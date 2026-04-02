import os
import pandas as pd
import re
import subprocess
import sys
import threading

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime as dt
from time import sleep

sys.path.append("../utils")
from aggregator import Aggregator
from google_configs import gc_files, pull_sheet, update_sheet
from logger import create_logger


"""
The ScrapeRunner class below determines which scrapers are available to run
based on the presence of Python scripts for them and their exclusion/inclusion
in the Google Sheet `agencies.sample`.

It executes their Python scripts in parallel, and each scraper updates its own
row in the Google Sheet `agencies.scraping` immediately upon completion.
"""


class ScrapeRunner:
    def __init__(self, arguments):
        self.logger = create_logger()
        self.args = arguments
        self.exclusions = ["'__pycache__'", ".DS_Store"]
        self.scraping_sheet_cols = [
            "ori",
            "scraper",
            "last_attempt",
            "last_success",
            "duration",
            "overall_from",
            "data_from",
            "data_to",
            "status",
        ]
        self.sheet = None
        self.sheet_lock = threading.Lock()

    def run(self):
        """
        primary method, determines list of scrapers to run, links them to oris,
        verifies with the `agencies.sample` sheet and threads through them,
        updating the `agencies.scraping` tracker sheet after each scraper completes
        """
        # retrieve list of all scraper filenames from the `rtci/scrapers/` directory
        scrapers = list()
        states = [d for d in os.listdir("../scrapers") if d not in self.exclusions]
        for state in states:
            scripts = [
                f
                for f in os.listdir(f"../scrapers/{state}")
                if f not in self.exclusions
                and not f.endswith(".csv")
                and not f.endswith(".pdf")
            ]
            scrapers.extend([{"state": state, "scraper": f} for f in scripts])

        # if only some scrapers specified in arg, only run those
        if self.args.scrapers:
            assert all(
                [
                    scraper in [d["scraper"][:-3] for d in scrapers]
                    for scraper in self.args.scrapers
                ]
            )
            scrapers = [d for d in scrapers if d["scraper"][:-3] in self.args.scrapers]

        # exclude any scrapers specified in arg
        if self.args.exclude:
            scrapers = [
                d for d in scrapers if d["scraper"][:-3] not in self.args.exclude
            ]

        # pull the agencies sheet `agencies.sample` and compare
        self.sheet = pull_sheet(sheet="sample", url=gc_files["agencies"])
        self.sheet = self.sheet[
            (self.sheet["exclude"] == "No") | (self.sheet["clearance_exclude"] == "No")
        ]
        self.logger.info(f"identified {len(self.sheet)} oris for inclusion in scraping")
        self.logger.info(f"identified {len(scrapers)} scrapers")

        # pull scraping sheet (needed for run_from filter and cached for subprocesses)
        scraping_sheet = pull_sheet(sheet="scraping", url=gc_files["agencies"])

        # cache both sheets as CSVs so scraper subprocesses don't hit the Sheets API
        cache_dir = "/tmp/rtci_sheet_cache"
        os.makedirs(cache_dir, exist_ok=True)
        sample_sheet_full = pull_sheet(sheet="sample", url=gc_files["agencies"])
        sample_sheet_full.to_csv(f"{cache_dir}/sample.csv", index=False)
        scraping_sheet.to_csv(f"{cache_dir}/scraping.csv", index=False)
        self.logger.info("cached sheets for scraper subprocesses")

        # check that all scraper filenames (by state or ori) match up with the `agencies.sample` sheet
        assert all(
            [
                f["scraper"][:-3] in self.sheet["ori"].unique()
                and f["scraper"][:-3] in self.sheet["scraper"].unique()
                for f in scrapers
                if len(f["scraper"][:-3]) > 2
            ]
        )
        assert all(
            [
                f["state"] in self.sheet["state"].unique()
                and f["state"] in self.sheet["scraper"].unique()
                for f in scrapers
                if len(f["scraper"][:-3]) == 2
            ]
        )

        # if specified, only rerun scrapes for which last_success was too long ago
        if self.args.run_from:
            if len(scraping_sheet) > 0:
                good = scraping_sheet[
                    scraping_sheet["last_success"] >= self.args.run_from
                ]["scraper"].unique()
                scrapers = [d for d in scrapers if d["scraper"][:-3] not in good]

        self.logger.info(f"identified {len(scrapers)} scrapers that need to be rerun")
        if not scrapers:
            return

        # run scrapers in parallel with a thread pool
        max_workers = self.args.workers if hasattr(self.args, "workers") and self.args.workers else 2
        self.logger.info(f"running scrapers with {max_workers} parallel workers")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.scrape_one, scraper): scraper
                for scraper in scrapers
            }
            for future in as_completed(futures):
                scraper = futures[future]
                try:
                    future.result()
                except Exception as e:
                    self.logger.warning(
                        f"unexpected error in {scraper['scraper']}: {e}"
                    )

        # remove any hanging pdfs or csvs from failed scrape attempts
        for state in states:
            for f in os.listdir(f"../scrapers/{state}"):
                if f.endswith(".csv") or f.endswith(".pdf"):
                    self.logger.info(f"removing hanging file: ../scrapers/{state}/{f}")
                    os.remove(f"../scrapers/{state}/{f}")

    def scrape_one(self, scrape):
        """
        runs one scraper, updates the Google Sheet immediately with results
        """
        # confirms which oris are being attempted based on the
        # (manually specified) `scraper` col in `agencies.sample`
        attempted_oris = self.sheet[self.sheet["scraper"] == scrape["scraper"][:-3]][
            "ori"
        ].unique()

        # gets path to correct scraper, and runs a subprocess
        path = f"../scrapers/{scrape['state']}"
        start_time = dt.now()

        # if test flagged, only test run scrapes, otherwise send results to s3
        command = (
            ["python3", scrape["scraper"], "-t"]
            if self.args.test
            else ["python3", scrape["scraper"]]
        )

        # if full flagged, full rerun (from 2017-01-01)
        if self.args.full:
            command = command + ["-f"]

        result = subprocess.run(
            command,
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
        )
        end_time = dt.now()
        duration = end_time - start_time

        output = list()

        # if scrape succeeds, ensure oris line up and return good status
        if result.returncode == 0:
            self.logger.info(f"succeeded: {scrape['scraper']}")

            # print output if debugged flagged
            if self.args.log:
                self.logger.info(result.stderr)

            collected_oris = [
                ln for ln in result.stderr.split("\n") if "completed oris: " in ln
            ]
            assert len(collected_oris) == 1
            collected_oris = re.findall(r"'([A-Z0-9]{9})'", collected_oris[0])

            if set(attempted_oris).difference(set(collected_oris)):
                raise ValueError(
                    f"the following oris were attempted but not included: "
                    f"{set(attempted_oris).difference(set(collected_oris))}"
                )
            if set(collected_oris).difference(set(attempted_oris)):
                raise ValueError(
                    f"the following oris were collected extraneously: "
                    f"{set(collected_oris).difference(set(attempted_oris))}"
                )

            # collect logged earliest and latest data dates from `super.py` stderr
            data_from = [
                ln for ln in result.stderr.split("\n") if "earliest data: " in ln
            ]
            data_to = [ln for ln in result.stderr.split("\n") if "latest data: " in ln]
            assert len(data_from) == 1
            assert len(data_to) == 1
            data_from = re.findall(r"([0-9]{4}-[0-9]{2})", data_from[0])
            data_to = re.findall(r"([0-9]{4}-[0-9]{2})", data_to[0])
            assert len(data_from) == 1
            assert len(data_to) == 1
            data_from = data_from[0]
            data_to = data_to[0]

            for ori in attempted_oris:
                output.append(
                    {
                        "ori": ori,
                        "scraper": scrape["scraper"][:-3],
                        "last_attempt": dt.strftime(end_time.date(), "%Y-%m-%d"),
                        "last_success": dt.strftime(end_time.date(), "%Y-%m-%d"),
                        "duration": duration.seconds,
                        "data_from": data_from,
                        "data_to": data_to,
                        "status": "good",
                    }
                )

        # if scrape fails, return bad status for attempted oris
        else:
            self.logger.warning(f"failed: {scrape['scraper']}")

            # print output if debugged flagged
            if self.args.debug or self.args.log:
                self.logger.warning(result.stderr)

            for ori in attempted_oris:
                output.append(
                    {
                        "ori": ori,
                        "scraper": scrape["scraper"][:-3],
                        "last_attempt": dt.strftime(end_time.date(), "%Y-%m-%d"),
                        "duration": duration.seconds,
                        "status": "bad",
                    }
                )

        # immediately update the Google Sheet for this scraper's results
        if not self.args.test:
            self._update_sheet_for_scraper(output)

    def _update_sheet_for_scraper(self, results):
        """
        thread-safe update of the `agencies.scraping` sheet for one scraper's results.
        pulls the current sheet, upserts the new rows, and pushes it back.
        retries with exponential backoff on rate limit errors.
        """
        max_retries = 5
        for attempt in range(max_retries):
            with self.sheet_lock:
                try:
                    scraping_sheet = pull_sheet(sheet="scraping", url=gc_files["agencies"])
                    if len(scraping_sheet) == 0:
                        scraping_sheet = pd.DataFrame(columns=self.scraping_sheet_cols)

                    for row in results:
                        ori = row["ori"]
                        if ori in scraping_sheet["ori"].values:
                            idx = scraping_sheet.index[scraping_sheet["ori"] == ori][0]
                            existing = scraping_sheet.loc[idx]

                            # always update last_attempt, duration, status
                            scraping_sheet.loc[idx, "last_attempt"] = row["last_attempt"]
                            scraping_sheet.loc[idx, "duration"] = row["duration"]
                            scraping_sheet.loc[idx, "status"] = row["status"]
                            scraping_sheet.loc[idx, "scraper"] = row["scraper"]

                            if row["status"] == "good":
                                scraping_sheet.loc[idx, "last_success"] = row["last_success"]
                                scraping_sheet.loc[idx, "data_from"] = row["data_from"]
                                scraping_sheet.loc[idx, "data_to"] = row["data_to"]
                                # preserve overall_from if it already exists
                                if existing["overall_from"] == "" or pd.isna(existing["overall_from"]):
                                    scraping_sheet.loc[idx, "overall_from"] = row["data_from"]
                            # on failure, preserve existing last_success, data_from, data_to, overall_from
                        else:
                            # new ori — insert row
                            new_row = {
                                "ori": ori,
                                "scraper": row["scraper"],
                                "last_attempt": row["last_attempt"],
                                "last_success": row.get("last_success", ""),
                                "duration": row["duration"],
                                "overall_from": row.get("data_from", ""),
                                "data_from": row.get("data_from", ""),
                                "data_to": row.get("data_to", ""),
                                "status": row["status"],
                            }
                            scraping_sheet = pd.concat(
                                [scraping_sheet, pd.DataFrame([new_row])],
                                ignore_index=True,
                            )

                    update_sheet(
                        sheet="scraping",
                        df=scraping_sheet.sort_values(by="ori"),
                        url=gc_files["agencies"],
                    )
                    self.logger.info(
                        f"updated sheet for {results[0]['scraper']} ({results[0]['status']})"
                    )
                    return
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        wait = 2 ** (attempt + 1)
                        self.logger.info(
                            f"rate limited updating {results[0]['scraper']}, retrying in {wait}s..."
                        )
                    else:
                        self.logger.warning(f"failed to update sheet for {results[0]['scraper']}: {e}")
                        return
            # sleep outside the lock so other threads can proceed
            sleep(wait)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="""If flagged, do not interact with sheet.""",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="""If flagged, log stderr.""",
    )
    parser.add_argument(
        "-l",
        "--log",
        action="store_true",
        help="""If flagged, log stdout and stderr.""",
    )
    parser.add_argument(
        "-s",
        "--scrapers",
        nargs="*",
        help="""If specified, will only attempt to run the provided list of scrapers.""",
    )
    parser.add_argument(
        "-rf",
        "--run_from",
        nargs="?",
        const=dt.strftime(dt.now().date(), "%Y-%m-%d"),
        default=None,
        help="""Recency of last success from which to automatically run scrapes (defaults to today as %Y-%m-%d).""",
    )
    parser.add_argument(
        "-f",
        "--full",
        action="store_true",
        help="""If specified, will fully rerun all scrapes from the start date (2017-01-01).""",
    )
    parser.add_argument(
        "-a",
        "--aggregate",
        action="store_true",
        help="""If specified, run aggregator at the end of the exec script.""",
    )
    parser.add_argument(
        "-x",
        "--exclude",
        nargs="*",
        help="""If specified, will exclude the provided list of scrapers from execution.""",
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=2,
        help="""Number of parallel workers (default: 2).""",
    )
    args = parser.parse_args()

    ScrapeRunner(args).run()
    if args.aggregate:
        Aggregator(args).run()

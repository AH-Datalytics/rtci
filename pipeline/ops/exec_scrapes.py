import os
import pandas as pd
import re
import subprocess
import sys

from datetime import datetime as dt

sys.path.append("../utils")
from aggregator import Aggregator
from google_configs import gc_files, pull_sheet, update_sheet
from logger import create_logger


# TODO: --log and --debug args seem not to be functioning potentially


"""
The ScrapeRunner class below determines which scrapers are available to run
based on the presence of Python scripts for them and their exclusion/inclusion
in the Google Sheet `agencies.sample`.

It executes their Python scripts, collects the results of their runs as good/bad,
and updates the locked Google Sheet `agencies.scraping` based on the results.
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
        self.scraping_sheet = None

    def run(self):
        """
        primary method, determines list of scrapers to run, links them to oris,
        verifies with the `agencies.sample` sheet and threads through them,
        taking results and running upsert to the `agencies.scraping` tracker sheet
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

        # pull the scraping results sheet `agencies.scraping`
        self.scraping_sheet = pull_sheet(sheet="scraping", url=gc_files["agencies"])
        if len(self.scraping_sheet) == 0:
            self.scraping_sheet = pd.DataFrame(columns=self.scraping_sheet_cols)

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
            good = self.scraping_sheet[
                self.scraping_sheet["last_success"] >= self.args.run_from
            ]["scraper"].unique()
            scrapers = [d for d in scrapers if d["scraper"][:-3] not in good]

        self.logger.info(f"identified {len(scrapers)} scrapers that need to be rerun")
        if not scrapers:
            return

        # scrape execution (thread subprocesses to run all scrapes)
        # results = thread(self.scrape_one, scrapers)
        results = list()
        for scraper in scrapers:
            results.extend(self.scrape_one(scraper))
        results = pd.DataFrame(results)

        # remove any hanging pdfs or csvs from failed scrape attempts
        for state in states:
            for f in os.listdir(f"../scrapers/{state}"):
                if f.endswith(".csv") or f.endswith(".pdf"):
                    self.logger.info(f"removing hanging file: ../scrapers/{state}/{f}")
                    os.remove(f"../scrapers/{state}/{f}")

        # "upsert" (via update and then concat for new results) scrape results into `agencies.scraping`
        self.scraping_sheet.set_index("ori", inplace=True)
        results.set_index("ori", inplace=True)
        self.scraping_sheet.update(results)
        self.scraping_sheet = self.scraping_sheet.reset_index()
        results = results.reset_index()
        out = pd.concat(
            [
                self.scraping_sheet,
                results[~results["ori"].isin(self.scraping_sheet["ori"].unique())],
            ]
        )

        # update `agencies.scraping` sheet
        self.logger.info(
            f"sample record: {out[out['scraper'].isin(results['scraper'].unique())].to_dict('records')[0]}"
        )
        if not self.args.test:
            update_sheet(
                sheet="scraping",
                df=out.sort_values(by="ori"),
                url=gc_files["agencies"],
            )

    def scrape_one(self, scrape):
        """
        runs one scraper and returns a list of operational metadata results per-ori
        """
        output = list()

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
                # if scrape has been attempted before, leave it's existing overall_from
                if ori in self.scraping_sheet["ori"].unique():
                    assert len(
                        self.scraping_sheet[self.scraping_sheet["ori"] == ori] == 1
                    )
                    if (
                        self.scraping_sheet[self.scraping_sheet["ori"] == ori].iloc[0][
                            "overall_from"
                        ]
                        != ""
                    ):
                        overall_from = self.scraping_sheet[
                            self.scraping_sheet["ori"] == ori
                        ].iloc[0]["overall_from"]
                    else:
                        overall_from = data_from

                # if scrape hasn't been tried before according to `agencies.scraping_sheet`,
                # put in a blank last_success
                else:
                    overall_from = data_from

                output.append(
                    {
                        "ori": ori,
                        "scraper": scrape["scraper"][:-3],
                        "last_attempt": dt.strftime(end_time.date(), "%Y-%m-%d"),
                        "last_success": dt.strftime(end_time.date(), "%Y-%m-%d"),
                        "duration": duration.seconds,
                        "overall_from": overall_from,
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
                # if scrape has been attempted before, leave it's existing last_success
                if ori in self.scraping_sheet["ori"].unique():
                    assert len(
                        self.scraping_sheet[self.scraping_sheet["ori"] == ori] == 1
                    )
                    last_success = self.scraping_sheet[
                        self.scraping_sheet["ori"] == ori
                    ].iloc[0]["last_success"]
                    data_from = self.scraping_sheet[
                        self.scraping_sheet["ori"] == ori
                    ].iloc[0]["data_from"]
                    data_to = self.scraping_sheet[
                        self.scraping_sheet["ori"] == ori
                    ].iloc[0]["data_to"]
                    overall_from = self.scraping_sheet[
                        self.scraping_sheet["ori"] == ori
                    ].iloc[0]["overall_from"]

                # if scrape hasn't been tried before according to `agencies.scraping_sheet`,
                # put in a blank last_success
                else:
                    last_success = ""
                    data_from = ""
                    data_to = ""
                    overall_from = ""

                output.append(
                    {
                        "ori": ori,
                        "scraper": scrape["scraper"][:-3],
                        "last_attempt": dt.strftime(end_time.date(), "%Y-%m-%d"),
                        "last_success": last_success,
                        "duration": duration.seconds,
                        "overall_from": overall_from,
                        "data_from": data_from,
                        "data_to": data_to,
                        "status": "bad",
                    }
                )

        return output


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
    args = parser.parse_args()

    ScrapeRunner(args).run()
    if args.aggregate:
        Aggregator(args).run()

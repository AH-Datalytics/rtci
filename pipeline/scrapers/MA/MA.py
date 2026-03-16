"""
Massachusetts SRS Offenses Known to Police scraper.
Standalone Playwright scraper — no Scraper base class needed.
Scrapes Beyond2020 SSRS report for 28 agencies x 12 months,
outputs CSV in the cross-tab format the Crime Data Pipeline expects.

Usage:
    python MA.py                    # last 12 months, all 28 agencies
    python MA.py --first 2025-10    # from Oct 2025 to now
    python MA.py --output ~/Downloads/mass_data.csv

Runs on GitHub Actions on the 14th-17th of each month.
Requires: pip install playwright && playwright install chromium
"""

import argparse
import csv
import logging
import re
import sys

from collections import defaultdict
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
from pathlib import Path
from time import sleep, time

from playwright.sync_api import sync_playwright

URL = "https://ma.beyond2020.com/ma_public/View/RSReport.aspx?ReportId=584"

# Target agencies: name -> ORI code
TARGETS = {
    "Barnstable": "MA0010100",
    "Boston": "MA0130100",
    "Brockton": "MA0120300",
    "Brookline": "MA0110400",
    "Cambridge": "MA0091100",
    "Chicopee": "MA0070500",
    "Everett": "MA0091700",
    "Fall River": "MA0030800",
    "Framingham": "MA0091800",
    "Haverhill": "MA0051100",
    "Lawrence": "MA0051300",
    "Lowell": "MA0092600",
    "Lynn": "MA0051400",
    "Malden": "MA0092700",
    "Medford": "MA0093000",
    "Methuen": "MA0051900",
    "New Bedford": "MA0031100",
    "Newton": "MA0093300",
    "Peabody": "MA0052500",
    "Plymouth": "MA0122000",
    "Quincy": "MA0112000",
    "Revere": "MA0130400",
    "Somerville": "MA0093900",
    "Springfield": "MA0071800",
    "Taunton": "MA0031900",
    "Waltham": "MA0094700",
    "Weymouth": "MA0112700",
    "Worcester": "MA0146000",
}

# Map SSRS row labels to pipeline offense names
CRIME_MAP = {
    "a. Murder and Nonnegligent Homicide": "Criminal Homicide",
    "2. Forcible Rape Total": "Forcible Rape Total",
    "3. Robbery Total": "Robbery Total",
    "Aggravated Assault Total": "Aggravated Assault Total",
    "5. Burglary Total": "Burglary Total",
    "6. Larceny - Theft Total": "Larceny - Theft Total",
    "7. Motor Vehicle Theft Total": "Motor Vehicle Theft Total",
}

OFFENSE_ORDER = [
    "Criminal Homicide",
    "Forcible Rape Total",
    "Robbery Total",
    "Aggravated Assault Total",
    "Burglary Total",
    "Larceny - Theft Total",
    "Motor Vehicle Theft Total",
]

ORI_SELECT = "select[name='ctl00$MainContent$RptViewer$ctl08$ctl03$ddValue']"
PERIOD_SELECT = "select[name='ctl00$MainContent$RptViewer$ctl08$ctl05$ddValue']"
VIEW_BUTTON = "input[id='ctl00_MainContent_RptViewer_ctl08_ctl00']"

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s %(funcName)s:%(lineno)d] %(message)s",
)
log = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="MA SRS scraper")
    parser.add_argument(
        "--first", type=str, default=None,
        help="Start month (YYYY-MM). Default: 6 months ago.",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output CSV path. Default: ~/Downloads/mass_data.csv",
    )
    return parser.parse_args()


def scrape_all(first_date, last_date):
    """Scrape all agencies x months. Returns dict keyed by (agency_name, month_label) -> {offense: count}."""
    data = {}  # (agency_name, month_label) -> {offense_name: reported_count}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_context().new_page()

        log.info("loading page...")
        page.goto(URL, timeout=60000)
        page.wait_for_selector(ORI_SELECT, timeout=15000)

        # Build ORI option value map
        ori_value_map = {}
        for opt in page.query_selector_all(f"{ORI_SELECT} option"):
            text = opt.inner_text().strip()
            val = opt.get_attribute("value")
            for name, ori in TARGETS.items():
                if ori in text:
                    ori_value_map[name] = {"value": val, "ori": ori, "label": text}
                    break

        log.info(f"matched {len(ori_value_map)} agencies in dropdown")

        # Build period option value map
        period_value_map = {}
        for opt in page.query_selector_all(f"{PERIOD_SELECT} option"):
            text = opt.inner_text().strip().replace("\xa0", " ")
            val = opt.get_attribute("value")
            try:
                opt_date = dt.strptime(text, "%b %Y")
                if first_date <= opt_date <= last_date:
                    period_value_map[text] = val
            except ValueError:
                continue

        log.info(f"target months: {list(period_value_map.keys())}")
        log.info(f"scraping {len(ori_value_map)} agencies x {len(period_value_map)} months")

        for agency_name, info in ori_value_map.items():
            for month_label, month_val in period_value_map.items():
                log.info(f"  {agency_name} ({info['ori']}) - {month_label}")
                try:
                    record = scrape_one(page, info["value"], month_val, month_label)
                    if record:
                        data[(agency_name, month_label)] = record
                except Exception as e:
                    log.warning(f"    error: {e}")
                    try:
                        page.goto(URL, timeout=60000)
                        page.wait_for_selector(ORI_SELECT, timeout=15000)
                    except Exception:
                        pass

        browser.close()

    return data, list(period_value_map.keys())


def scrape_one(page, agency_val, month_val, month_label):
    """Scrape one agency + month. Returns {offense_name: count} or None."""
    page.select_option(ORI_SELECT, agency_val)
    sleep(0.5)
    page.select_option(PERIOD_SELECT, month_val)
    sleep(0.5)

    # Click View Report and wait for refresh
    if page.query_selector("text=Grand Total"):
        page.click(VIEW_BUTTON)
        try:
            page.wait_for_selector("text=Grand Total", state="hidden", timeout=10000)
        except Exception:
            pass
        try:
            page.wait_for_selector("text=Grand Total", timeout=30000)
        except Exception:
            log.warning("    report didn't render after refresh, skipping")
            return None
    else:
        page.click(VIEW_BUTTON)
        try:
            page.wait_for_selector("text=Grand Total", timeout=30000)
        except Exception:
            log.warning("    report didn't render, skipping")
            return None

    sleep(1)

    report_text = page.evaluate("""() => {
        const node = document.evaluate(
            "//text()[contains(.,'Grand Total')]",
            document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
        ).singleNodeValue;
        if (!node) return null;
        let el = node.parentElement;
        for (let i = 0; i < 5; i++) { if (el.parentElement) el = el.parentElement; }
        return el.innerText;
    }""")

    if not report_text:
        log.warning("    no report text found")
        return None

    return parse_report_text(report_text)


def parse_report_text(report_text):
    """Parse SSRS report text into {offense_name: reported_count}."""
    text = report_text.replace("\r", "")
    text = re.sub(r"\n\t", "\t", text)
    text = re.sub(r"\t\n", "\t", text)
    text = re.sub(r"\t+", "\t", text)

    record = {}
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        for label, offense_name in CRIME_MAP.items():
            if line.startswith(label):
                rest = line[len(label):]
                parts = [p for p in rest.split("\t") if p != ""]
                reported = clean_num(parts[0] if parts else "")
                record[offense_name] = reported
                break

    return record


def clean_num(val):
    s = str(val).replace("\xa0", "").strip() if val is not None else ""
    if s == "":
        return 0
    return int(s.replace(",", ""))


def write_pipeline_json(data, month_labels, output_path):
    """Write JSON in the {agency, year, month, offense, count} format
    that the Crime Data Pipeline fetches from GitHub."""
    import json

    # Map our offense names to pipeline offense names
    OFFENSE_TO_PIPELINE = {
        "Criminal Homicide": "Murder",
        "Forcible Rape Total": "Rape",
        "Robbery Total": "Robbery",
        "Aggravated Assault Total": "Aggravated Assault",
        "Burglary Total": "Burglary",
        "Larceny - Theft Total": "Theft",
        "Motor Vehicle Theft Total": "Motor Vehicle Theft",
    }

    records = []
    for (agency_name, month_label), offenses in data.items():
        month_dt = dt.strptime(month_label, "%b %Y")
        year = month_dt.year
        month = month_dt.month

        for offense_name, count in offenses.items():
            pipeline_offense = OFFENSE_TO_PIPELINE.get(offense_name)
            if pipeline_offense and count > 0:
                records.append({
                    "agency": agency_name,
                    "year": year,
                    "month": month,
                    "offense": pipeline_offense,
                    "count": count,
                })

    records.sort(key=lambda r: (r["agency"], r["year"], r["month"], r["offense"]))

    with open(output_path, "w") as f:
        json.dump(records, f, indent=2)

    log.info(f"wrote {output_path} ({len(records)} records from {len(TARGETS)} agencies x {len(month_labels)} months)")


def main():
    args = parse_args()

    # Date range
    now = dt.now()
    last_date = now.replace(day=1) - relativedelta(days=1)  # last day of previous month
    if args.first:
        first_date = dt.strptime(args.first, "%Y-%m")
    else:
        first_date = now - relativedelta(months=12)
        first_date = first_date.replace(day=1)

    log.info(f"date range: {first_date:%Y-%m} to {last_date:%Y-%m}")

    # Output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(__file__).parent / "data" / "latest.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

    t0 = time()
    data, month_labels = scrape_all(first_date, last_date)
    write_pipeline_json(data, month_labels, output_path)

    elapsed = time() - t0
    log.info(f"done in {elapsed / 60:.1f} min")


if __name__ == "__main__":
    main()

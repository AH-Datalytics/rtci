import os
import subprocess

from datetime import datetime as dt
from datetime import timedelta as td

from airtable import get_records_from_sheet
from logger import create_logger


logger = create_logger()


EXCLUDE = [".DS_Store", "__pycache__"]
states = sorted([d for d in os.listdir("../scrapers") if d not in EXCLUDE])


# check which scrapes haven't run in the past n days
n = 1
records = get_records_from_sheet(logger, "Metadata")
to_run = list()
for r in records:
    if "last_success" in r:
        d = dt.fromisoformat(r["last_success"].replace("Z", "+00:00")).date()
        if d < dt.today().date() - td(days=n):
            to_run.append(r["ori"])


# run through directory structure and run scrapes
for state in states:
    scrapes = sorted(os.listdir(f"../scrapers/{state}"))
    for scrape in scrapes:
        logger.info(f"RUNNING {scrape.upper()}...")

        # for state-level scrapes...
        if len(scrape.split(".")[0]) == 2:
            # ...that still need to run
            if any([scrape.split(".")[0] in r for r in to_run]):
                subprocess.run(
                    f"cd ../scrapers/{state} && python3 {scrape}", shell=True
                )

            # ...that ran recently
            else:
                logger.info(
                    f"SKIPPING {scrape.split('.')[0].upper()} (ALREADY RAN RECENTLY)"
                )

        # for agency-level scrapes that already ran recently
        elif scrape.split(".")[0] not in to_run:
            logger.info(f"SKIPPING {scrape.upper()} (ALREADY RAN RECENTLY)")

        # for agency-level scrapes that still need to run
        else:
            subprocess.run(f"cd ../scrapers/{state} && python3 {scrape}", shell=True)

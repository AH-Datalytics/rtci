import json
import pandas as pd
import requests
import sys

from datetime import datetime as dt
from functools import reduce
from tenacity import retry, stop_after_attempt, stop_after_delay, wait_random

sys.path.append("../utils")
from airtable import get_records_from_sheet
from parallelize import thread
from super import Scraper


class Optimum(Scraper):
    def __init__(self):
        super().__init__()
        self.threader = True  # some states fail on requests threading
        self.alt = False  # handles alternate formats for {PA, TX, ...?}
        self.payload = {
            "ReportType": "Agency",
            "DrillDownReportIDs": -1,
            "IsGroupAOffense": True,
        }
        self.exclude_oris = []

    def scrape(self):
        if self.alt:
            self.payload.update(
                {
                    "StartDate": dt.strftime(self.first, "%m/%d/%Y"),
                    "EndDate": dt.strftime(self.last, "%m/%d/%Y"),
                }
            )
        else:
            self.payload.update(
                {
                    "startDate": dt.strftime(self.first, "%m%Y"),
                    "endDate": dt.strftime(self.last, "%m%Y"),
                }
            )

        # get list of agencies in state from airtable
        agencies = [
            d["ori"]
            for d in get_records_from_sheet(
                self.logger,
                "Metadata",
                formula=f"{{state}}='{self.state_full_name}'"
                # note: this includes agencies that are not included
                # in the existing RTCI sample (audited out for missing data, etc.);
                # to include only those matching the `final_sample.csv` file, use:
                # formula=f"AND({{state}}='{self.state_full_name}',NOT({{agency_rtci}}=''))",
            )
            if d["ori"] not in self.exclude_oris
        ]

        # get list of ori input options from website
        r = requests.get(self.agency_list_url)
        a = pd.DataFrame(json.loads(r.text))
        a["Value"] = a["Value"].astype(str)

        # match together two sources
        agencies = [
            (agency, a[a["Description"].str.startswith(agency)]["Value"].item())
            for agency in agencies
        ]

        # specify self.oris for super class
        self.oris.extend([agency[0] for agency in agencies])

        # run through data collection per agency
        if self.threader:
            all_agencies = thread(self.get_agency, agencies)
        else:
            all_agencies = list()
            for agency in agencies:
                self.logger.info(f"running {agency[0]}...")
                all_agencies.extend(self.get_agency(agency))

        return all_agencies

    def get_agency(self, agency):
        # plug agency id code into payload
        agency, value = agency
        payload = self.payload.copy()
        payload.update({"ReportIDs": value})

        # run through crimes and collect data
        out = list()
        for crime in self.crimes:
            offense = ",".join([c["Offense Code"].lower() for c in self.crimes[crime]])
            payload.update({"OffenseIDs": offense})
            j = self.get_agency_crime_data(payload)

            # collect dates and crime counts
            dates = [dt.strptime(d, "%Y/%b") for d in j["periodlist"]]
            crimes = j["crimeList"]
            assert len(crimes) == 1
            crimes = crimes[0]

            # capture data if it exists, otherwise pass zeros
            if crimes["data"]:
                out.append(pd.DataFrame({"date": dates, crime: crimes["data"]}))
            else:
                self.logger.warning(f"no data for {agency}:{crime}")
                out.append(pd.DataFrame({"date": dates, crime: 0}))

        df = reduce(lambda df1, df2: pd.merge(df1, df2, on="date"), out)
        df["ori"] = agency

        return df.to_dict("records")

    @retry(
        stop=(stop_after_delay(60) | stop_after_attempt(3)),
        wait=wait_random(min=5, max=10),
    )
    def get_agency_crime_data(self, payload):
        r = requests.get(self.data_url, params=payload)

        # result is HTML instead of JSON
        assert (
            "<title>Runtime Error</title>" not in r.text
            and "<title>Error Page</title>" not in r.text
        )

        j = json.loads(r.text)

        print(payload)
        print(j)
        print()

        # result is JSON with an error message
        assert not ("Result" in j and j["Result"] == "ERROR")
        assert not (
            "Message" in j and j["Message"].startswith("Execution Timeout Expired")
        )
        assert not (
            "Message" in j
            and j["Message"].startswith(
                "The parameters dictionary contains a null entry for parameter"
            )
        )
        assert not (
            "Message" in j
            and j["Message"].startswith(
                "String was not recognized as a valid DateTime."
            )
        )
        assert "periodlist" in j and "crimeList" in j

        return j

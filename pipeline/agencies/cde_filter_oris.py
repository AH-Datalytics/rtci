import json
import os
import pandas as pd
import requests
import sys

from datetime import datetime as dt
from datetime import timedelta as td
from dotenv import load_dotenv

sys.path.append("../utils")
from aws import snapshot_df
from logger import create_logger
from parallelize import thread


load_dotenv()


"""
The CdeGetFilterOris class below uses the FBI's Crime Data Explorer API
( https://cde.ucr.cjis.gov/LATEST/webapp/#/pages/docApi )
to retrieve a filtered list of agency ORIs. Filtering criteria are:

- `agency_type_name` is in {"City", "County"}
- most recent `pop` is >= 50k for cities
- most recent `pop` is >= 100k for counties 

The output set of ORIs is saved on AWS as `rtci/fbi/cde_filtered_oris.csv`.

* To manually force the inclusion of an agency that would otherwise fail filtering,
include it in the `self.overrides` list in `self.__init__`.
"""


class CdeGetFilterOris:
    def __init__(self):
        self.args = parser.parse_args()
        self.logger = create_logger()
        self.api_key = os.getenv("CDE_API_KEY")
        self.last = dt.strftime(
            dt.now().replace(day=1, hour=23, minute=59, second=59, microsecond=999999)
            - td(days=1),
            "%m-%Y",
        )  # last day of previous month
        self.agency_types = ["City", "County"]
        self.url_states = "https://cde.ucr.cjis.gov/LATEST/lookup/states"
        self.url_agencies = "https://cde.ucr.cjis.gov/LATEST/agency/byStateAbbr/"
        self.city_threshold = 50_000
        self.county_threshold = 100_000
        self.overrides = [
            "MA0022200",  # Pittsfield, MA [agency requested we include them]
            "UT0180000",  # Salt Lake County, UT [shows up with 0 pop in API]
        ]

    def scrape(self):
        """
        primary method, gets all states, gets all ORIs per state,
        filters list on population and agency type, and saves ORIs to AWS
        """
        all_oris = list()

        # get list of states available from source
        states = [
            state["abbr"]
            for state in json.loads(requests.get(self.url_states).text)["get_states"][
                "cde_states_query"
            ]["states"]
        ]
        self.logger.info(f"found states: {len(states)}")

        # for each state get a list of oris,
        # filtered down to cities and counties only
        for state in states:
            counties = json.loads(requests.get(self.url_agencies + state).text)
            oris = [
                element
                for sublist in [
                    [
                        {
                            "state": state,
                            "ori": agency["ori"],
                            "name": agency["agency_name"],
                            "type": agency["agency_type_name"],
                        }
                        for agency in counties[county]
                    ]
                    for county in counties
                ]
                for element in sublist
                if element["type"] in self.agency_types
            ]
            all_oris.extend(oris)
        self.logger.info(f"found oris: {len(all_oris)}")

        # filter down list of oris based on population thresholds
        filtered_oris = thread(self.filter_oris, all_oris, threads=15)
        filtered_oris = [
            ori
            for ori in filtered_oris
            if ori["pop"]
            and (
                (ori["type"] == "City" and ori["pop"] >= self.city_threshold)
                or (ori["type"] == "County" and ori["pop"] >= self.county_threshold)
            )
            or ori["ori"] in self.overrides
        ]
        self.logger.info(f"filtered oris: {len(filtered_oris)}")
        df = pd.DataFrame(filtered_oris).sort_values(by=["state", "ori"])

        # save results to AWS
        self.logger.info(f"sample record: {filtered_oris[0]}")
        if not self.args.test:
            snapshot_df(
                logger=self.logger,
                df=df,
                path="fbi/",
                filename=f"cde_filtered_oris",
            )

    def filter_oris(self, query):
        """
        for a given ORI, retrieves most recently reported population
        """
        pop = json.loads(
            requests.get(
                f"https://api.usa.gov/crime/fbi/cde/nibrs/agency/{query['ori']}/all?type=counts"
                f"&from={self.last}"
                f"&to={self.last}"
                f"&ori={query['ori']}"
                f"&API_KEY={self.api_key}"
            ).text
        )["populations"]["population"][query["name"]][self.last]
        query.update({"pop": pop})
        return query


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="""If specified, no interactions with AWS S3 or sheets will take place.""",
    )
    args = parser.parse_args()

    CdeGetFilterOris().scrape()

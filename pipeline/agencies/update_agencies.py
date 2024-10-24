import numpy as np
import pandas as pd
import sys
import us

sys.path.append("../utils")
from airtable import get_records_from_sheet, insert_to_airtable_sheet
from logger import create_logger


logger = create_logger()


class Agencies:
    def __init__(self, arguments):
        self.logger = create_logger()
        self.args = arguments
        self.aws_dest = "https://sample-rtci.s3.us-east-1.amazonaws.com/sources/"
        self.external_src = pd.read_csv(
            self.aws_dest + "CDE+Participation+2000-2023.csv"
        )
        self.internal_src = pd.read_csv(self.aws_dest + "final_sample.csv")
        self.aggregations = [
            "Nationwide Count",
            "100k-250k",
            "1mn+",
            "250k-1mn",
            "<100k",
            "State Sample Counts",
        ]
        self.corrections = {
            "Abington": "Abington Township, Montgomery County",
            "Bensalem": "Bensalem Township",
            "Charlotte": "Charlotte-Mecklenburg",
            "Coeur D Alene": "Coeur d'Alene",
            "Desoto": "DeSoto",
            "Las Vegas": "Las Vegas Metropolitan Police Department",
            "Louisville": "Louisville Metro",
            "Lower Merion": "Lower Merion Township",
            "Lower Paxton": "Lower Paxton Township",
            "Mckinney": "McKinney",
            "Nashville": "Metropolitan Nashville Police Department",
            "New York City": "New York",
            "St Charles": "St. Charles",
            "St Joseph": "St. Joseph",
            "St Louis": "St. Louis",
            "St Peters": "St. Peters",
            "Upper Darby": "Upper Darby Township",
        }

    def run(self):
        self.prep_external()
        self.prep_internal()

        internal_merge = pd.merge(
            self.internal_src, self.external_src, how="left", on="city_state"
        )
        assert len(internal_merge[internal_merge["ori"].isna()]) == 0

        dataset = pd.merge(
            self.external_src, self.internal_src, how="left", on="city_state"
        )
        assert len(dataset[dataset["Agency Name"].notna()]) == len(self.internal_src)

        dataset = self.prep_dataset(dataset)
        records = dataset.to_dict("records")
        agencies_to_insert = [{"fields": d} for d in records]

        self.logger.info(f"sample record: {records[0]}")
        if not self.args.test:
            insert_to_airtable_sheet(
                logger=logger,
                sheet_name="Metadata",
                to_insert=agencies_to_insert,
                keys=["ori"],
            )

    def prep_external(self):
        self.external_src = self.external_src[self.external_src["data_year"] == 2023]
        self.external_src = self.external_src[
            self.external_src["agency_type_name"] == "City"
        ]
        self.external_src = self.external_src[
            (self.external_src["population"] >= 40_000)
            | (self.external_src["ori"] == "MI3849700")
        ]  # includes Jackson, MI even though population is < 40_000
        self.external_src["pub_agency_name"] = self.external_src[
            "pub_agency_name"
        ].str.strip()  # handles extra space in "Dunwoody "
        self.external_src["city_state"] = (
            self.external_src["pub_agency_name"]
            + ", "
            + self.external_src["state_abbr"]
        )

    def prep_internal(self):
        self.internal_src = self.internal_src.drop_duplicates("city_state")
        self.internal_src = self.internal_src[
            ~self.internal_src["Agency Name"].isin(self.aggregations)
        ]
        self.internal_src["Agency Name"] = self.internal_src["Agency Name"].replace(
            self.corrections
        )
        self.internal_src["city_state"] = (
            self.internal_src["Agency Name"] + ", " + self.internal_src["State"]
        )

    @staticmethod
    def prep_dataset(dataset):
        dataset = dataset[
            [
                "ori",
                "pub_agency_name",
                "Agency",
                "state_name",
                "population",
                "Source.Link",
                "Source.Type",
                "Source.Method",
                "Comment",
            ]
        ]
        dataset.columns = [
            "ori",
            "agency_cde",
            "agency_rtci",
            "state",
            "population",
            "source_url",
            "source_type",
            "source_method",
            "notes",
        ]
        dataset = dataset.fillna("")
        return dataset


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--test",
        action="store_true",
        help="""If flagged, do not interact with Airtable.""",
    )
    args = parser.parse_args()

    Agencies(args).run()

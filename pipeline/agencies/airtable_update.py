import numpy as np
import pandas as pd
import sys

from datetime import datetime as dt

sys.path.append("../utils")
from airtable import clear_sheet, get_records_from_sheet, insert_to_airtable_sheet
from logger import create_logger


"""
The AirtableUpdate class below reads in (i) the latest
`final_sample.csv` file from the RTCI GitHub repository and
(ii) the list of viable agencies from the FBI's CDE API.
"""


class AirtableUpdate:
    def __init__(self, arguments):
        self.logger = create_logger()
        self.args = arguments
        self.aggregations = [
            "Nationwide Count",
            "100k-250k",
            "1mn+",
            "250k-1mn",
            "<100k",
            "State Sample Counts",
            "Regional Sample Counts",
        ]
        self.corrections = {
            "Abington": "Abington Township",
            "Bensalem": "Bensalem Township",
            "Charlotte": "Charlotte-Mecklenburg",
            "Coeur D Alene": "Coeur d'Alene",
            "Louisville": "Louisville Metro",
            "Lower Merion": "Lower Merion Township",
            "Lower Paxton": "Lower Paxton Township",
            "Mckinney": "McKinney",
            "St Charles": "St. Charles",
            "St Joseph": "St. Joseph",
            "St Louis": "St. Louis",
            "St Peters": "St. Peters",
            "Upper Darby": "Upper Darby Township",
            "Haverford": "Haverford Township",
            "Millcreek": "Millcreek Township, Erie County",
        }

    def run(self):
        fs = self.get_final_sample_agencies()
        cde = self.get_cde_agencies()

        df = pd.merge(
            fs,
            cde,
            how="left",
            left_on=["State", "Agency Name"],
            right_on=["state", "name_for_match"],
        )

        assert len(df[df["ori"].isna()]) == 0

        df = pd.merge(
            cde,
            fs,
            how="left",
            left_on=["state", "name_for_match"],
            right_on=["State", "Agency Name"],
        )
        # assert len(df[df["Agency Name"].notna()]) == len(fs)

        df = self.prep_for_airtable(df)

        # records = df.to_dict("records")
        # agencies_to_insert = [{"fields": d} for d in records]

        # self.logger.info(f"sample record: {records[0]}")
        # if not self.args.test:
        #     if self.args.clear:
        #         clear_sheet(logger=self.logger, sheet_name="Metadata")
        # insert_to_airtable_sheet(
        #     logger=self.logger,
        #     sheet_name="Metadata",
        #     to_insert=agencies_to_insert,
        #     keys=["ori"],
        # )

    def get_final_sample_agencies(self):
        fs = pd.read_csv(
            "https://github.com/AH-Datalytics/rtci/blob/development/data/final_sample.csv?raw=true",
            low_memory=False,
        ).drop_duplicates("city_state")[
            [
                "Agency Name",
                "city_state",
                "State",
                "Source.Link",
                "Source.Type",
                "Source.Method",
                "Comment",
            ]
        ]
        fs = fs[~fs["Agency Name"].isin(self.aggregations)]
        fs = fs[~fs["city_state"].str.endswith(", PR")]
        fs = fs.drop(columns=["city_state"])
        fs["Agency Name"] = fs["Agency Name"].replace(self.corrections)
        return fs

    def get_cde_agencies(self):
        cde = pd.read_csv(
            "https://rtci.s3.us-east-1.amazonaws.com/fbi/cde_filtered_oris.csv"
        ).sort_values(by=["state", "ori"])
        cde["name_for_match"] = cde["name"].apply(lambda s: self.clean_cde_names(s))
        return cde

    @staticmethod
    def clean_cde_names(name):
        name = name.replace("  ", " ")
        name = name.replace(" Police Department", "")
        name = name.replace(" Sheriff's Office", "")
        name = name.replace(" Bureau of Police", "")
        name = name.replace(" Metropolitan", "")
        name = name.strip()
        return name

    def prep_for_airtable(self, df):
        """
        takes the dataframe of matched agencies from FBI and RTCI,
        renames fields, grabs original values of agency names from each source,
        and prepares the df for upload to Airtable
        """
        df = df[
            [
                "ori",
                "state",
                "name",
                "Agency Name",
                "name_for_match",
                "type",
                "pop",
                "Source.Link",
                "Source.Type",
                "Source.Method",
                "Comment",
            ]
        ]
        df = df.rename(
            columns={
                "name": "name_cde",
                "Agency Name": "name_rtci",
                "name_for_match": "matched_attempted_as",
                "Source.Link": "url",
                "Source.Type": "source_type",
                "Source.Method": "source_method",
                "Comment": "notes",
            }
        )

        # unwind RTCI agency names back to their original forms
        assert len(set(self.corrections.keys())) == len(self.corrections)
        assert len(set(self.corrections.values())) == len(self.corrections)
        df["name_rtci"] = df["name_rtci"].replace(
            {v: k for k, v in self.corrections.items()}
        )

        df["exclude"] = np.where(df["name_rtci"].notna(), "No", "")
        df["exclusion_reason"] = np.where(df["name_rtci"].notna(), "N/A", "")
        df["last_reviewed"] = np.where(
            df["name_rtci"].notna(), dt.strftime(dt.now(), "%Y-%m-%d %H:%M:%S"), ""
        )

        # fill with empty strings to satisfy Airtable API and return
        df = df.fillna("")
        return df


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--clear",
        action="store_true",
        help="""If flagged, delete Airtable sheet.""",
    )
    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="""If flagged, do not interact with Airtable.""",
    )
    args = parser.parse_args()

    AirtableUpdate(args).run()

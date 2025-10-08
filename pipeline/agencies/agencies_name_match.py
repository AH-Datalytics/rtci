import sys

sys.path.append("../utils")
from aws import snapshot_json
from google_configs import gc_files, pull_sheet
from logger import create_logger


"""
The AgenciesNameMatch class below reads in the current list of agency names
held in the `agencies.sample` Google Sheet. It cleans these according to the
RTCI display requirements (e.g., stripping ' Police Department' from the end 
of agency names), manually affects some overwrites (e.g., changing 'St. Peters'
to 'St Peters'), and uploads the name mapping to AWS as `rtci/crosswalks/agency_names.json`.
"""


class AgenciesNameMatch:
    def __init__(self, arguments):
        self.logger = create_logger()
        self.args = arguments
        self.corrections = {
            "Abington Township": "Abington",
            "Bensalem Township": "Bensalem",
            "Charlotte-Mecklenburg": "Charlotte",
            "Coeur d'Alene": "Coeur D Alene",
            "Duval County": "Jacksonville",
            "Louisville Metro": "Louisville",
            "Lower Merion Township": "Lower Merion",
            "Lower Paxton Township": "Lower Paxton",
            "McKinney": "Mckinney",
            "St. Charles": "St Charles",
            "St. Joseph": "St Joseph",
            "St. Louis": "St Louis",
            "St. Peters": "St Peters",
            "Upper Darby Township": "Upper Darby",
            "Haverford Township": "Haverford",
            "Millcreek Township, Erie County": "Millcreek",
        }

    def run(self):
        """
        primary method, pulls in agency names from `agencies.sample` sheet and
        maps them as required to rtci standards, then saves output to s3
        """
        # get records from sheet `agencies.sample` and clean them
        sheet = pull_sheet(sheet="sample", url=gc_files["agencies"])
        sheet["name_disp"] = sheet["name"].apply(lambda s: self.clean_name(s))
        sheet["name_disp"] = sheet["name_disp"].replace(self.corrections)
        records = (
            sheet[["ori", "name", "name_disp"]]
            .rename(columns={"name": "name_fbi"})
            .to_dict("records")
        )

        # save results to AWS
        self.logger.info(f"sample record: {records[0]}")
        if not self.args.test:
            snapshot_json(
                logger=self.logger,
                json_data=records,
                path="crosswalks/",
                filename=f"agency_names",
            )

    @staticmethod
    def clean_name(name):
        name = name.replace("  ", " ")
        name = name.replace(" Police Department", "")
        name = name.replace(" Sheriff's Office", "")
        name = name.replace(" Bureau of Police", "")
        name = name.replace(" Metropolitan", "")
        name = name.strip()
        return name


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="""If flagged, do not interact with S3.""",
    )
    args = parser.parse_args()

    AgenciesNameMatch(args).run()

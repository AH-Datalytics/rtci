import pandas as pd
import sys

sys.path.append("../utils")
from google_configs import gc_files, pull_sheet, update_sheet
from logger import create_logger


"""
The AgenciesSheetUpdate class below reads in the filtered list of agencies
produced by running the script `cde_filter_oris.py` 
and stored in AWS S3 as `rtci/fbi/cde_filtered_oris.csv`,
and the agencies tracking Google Sheet `agencies.sample`.

It checks to see if there are any agencies in the sheet
that have not been produced by the script above, and if so
requires the user to either rerun the script with the argument `--archive`
(which moves those records to the `agencies.archive` tab)
or manually include those agencies in the override list in the script above.

It then checks to see if there are any new agencies from the filtered ORIs list,
and if so, adds them to the Google Sheet.
"""


class AgenciesSheetUpdate:
    def __init__(self, arguments):
        self.logger = create_logger()
        self.args = arguments
        self.column_order = [
            "state",
            "ori",
            "name",
            "type",
            "pop",
            "url",
            "source_type",
            "source_method",
            "exclude",
            "exclusion_reason",
            "notes",
            "last_reviewed",
            "last_reviewed_by",
            "clearance_url"
            "clearance_source_type"
            "clearance_source_method"
            "clearance_exclude"
            "clearance_exclusion_reason"
            "clearance_notes"
            "clearance_last_reviewed"
            "clearance_last_reviewed_by",
        ]

    def run(self):
        """
        primary method, gets list of agencies from cde and google sheet,
        compares them and makes the user rectify any issues with unaccounted agencies on the sheet
        (not in the cde set), then adds any new agencies from the cde set to the sheet
        """
        # read in filtered cde ori list, google sample sheet and archive sheet
        cde = self.get_cde_agencies()
        sheet = pull_sheet(sheet="sample", url=gc_files["agencies"])
        sheet_archive = pull_sheet(sheet="archive", url=gc_files["agencies"])

        # make sure ori is a unique key
        assert cde["ori"].nunique() == len(cde)
        assert sheet["ori"].nunique() == len(sheet)
        assert sheet_archive["ori"].nunique() == len(sheet_archive)
        self.logger.info(f"cde: {len(cde)} rows, sheet: {len(sheet)} rows")

        # check for oris present in one location but not the other
        not_in_cde = set(sheet["ori"].unique()).difference(set(cde["ori"].unique()))
        not_in_sheet = set(cde["ori"].unique()).difference(set(sheet["ori"].unique()))
        self.logger.info(f"in sheet but not in cde: {not_in_cde}")
        self.logger.info(f"in cde but not in sheet: {not_in_sheet}")

        if self.args.quality_check:
            self.log_quality_checks(sheet)

        if not not_in_cde and not not_in_sheet:
            self.logger.info(f"no new records from cde, terminating")
            return

        # handle archiving of oris that are in the current `agencies.sample` google sheet
        # but are not in the retrieved fbi cde api dataframe
        # (copy them to `agencies.archive` then remove them from `agencies.sample`)
        if not_in_cde and self.args.archive:
            add_to_archive = pd.concat(
                [sheet_archive, sheet[sheet["ori"].isin(not_in_cde)]]
            ).drop_duplicates("ori")
            assert set(add_to_archive.columns) == set(self.column_order)
            add_to_archive = add_to_archive[self.column_order]
            remove_from_sample = sheet[~sheet["ori"].isin(not_in_cde)]
            assert set(remove_from_sample.columns) == set(self.column_order)
            remove_from_sample = remove_from_sample[self.column_order]
            self.logger.info(
                f"duplicating `not_in_cde` records to `agencies.archive` sheet"
            )
            update_sheet(
                sheet="archive",
                df=add_to_archive,
                url=gc_files["agencies"],
            )

            self.logger.warning(
                f"removing `not_in_cde` records from `agencies.sample` sheet"
            )
            update_sheet(
                sheet="sample",
                df=remove_from_sample,
                url=gc_files["agencies"],
            )

            not_in_cde = set()

        # raise an error if there are still records in the google sheet that are not in the fbi cde data
        if not_in_cde:
            raise ValueError(
                f"rows were identified in the google sheet `agencies.sample` that are not present in the "
                f"fbi cde api data. please either archive these rows to `agencies.archive` by running this script "
                f"with the -a / --archive argument, or manually add these to the override list in "
                f"`cde_filter_oris.py` and overwrite the existing `rtci/fbi/cde_filtered_oris` file on aws s3."
            )

        merged = pd.merge(
            cde,
            sheet[
                ["ori"] + list(set(sheet.columns).difference(list(set(cde.columns))))
            ],
            how="outer",
            on="ori",
        ).sort_values(by="ori")
        assert set(merged.columns) == set(self.column_order)
        merged = merged[self.column_order]
        assert len(merged[merged["ori"].isin(not_in_cde)]) == 0

        self.logger.info(
            f"new records to add: {len(merged[merged['ori'].isin(not_in_sheet)])}"
        )

        # add any new records from the fbi cde to the `agencies.sample` sheet
        if len(merged[merged["ori"].isin(not_in_sheet)]) > 0:
            self.logger.info(
                f"sample new record: {merged[merged['ori'].isin(not_in_sheet)].to_dict('records')[0]}"
            )
            if not self.args.test:
                self.logger.warning(
                    f"adding `not_in_sheet` records to google sheet `agencies.sample`"
                )
                update_sheet(
                    sheet="sample",
                    df=merged,
                    url=gc_files["agencies"],
                )

    @staticmethod
    def get_cde_agencies():
        """
        reads in the most recent list of filtered agency oris stored in s3 from the fbe cde
        """
        cde = pd.read_csv(
            "https://rtci.s3.us-east-1.amazonaws.com/fbi/cde_filtered_oris.csv"
        ).sort_values(by="ori")
        return cde

    def log_quality_checks(self, sheet):
        """
        reports some quality checks on the data in the `agencies` sheets
        """
        for field in ["", "clearance_"]:
            self.logger.info(f"QUALITY CHECKS {field.rstrip('_').upper()}")
            self.logger.info(
                "{} records excluded that have a url documented".format(
                    len(
                        sheet[
                            (sheet[f"{field}exclude"] == "Yes")
                            & (sheet[f"{field}exclusion_reason"] == "No URL")
                            & (sheet[f"{field}url"] != "")
                        ]
                    )
                ),
            )

            self.logger.info(
                "{} records excluded that don't have a url documented but have a different exclusion reason".format(
                    len(
                        sheet[
                            (sheet[f"{field}exclude"] == "Yes")
                            & (sheet[f"{field}exclusion_reason"] != "No URL")
                            & (sheet[f"{field}url"] == "")
                        ]
                    )
                ),
            )

            self.logger.info(
                "{} records recorded as 'Need to review'".format(
                    len(sheet[sheet[f"{field}exclusion_reason"] == "Need to review"])
                ),
            )

            self.logger.info(
                "{} records included that have a reported exclusion reason".format(
                    len(
                        sheet[
                            (sheet[f"{field}exclude"] == "No")
                            & (sheet[f"{field}exclusion_reason"] != "N/A")
                        ]
                    )
                )
            )

            self.logger.info(
                "{} records included that have no url".format(
                    len(
                        sheet[(sheet[f"{field}exclude"] == "No") & (sheet["url"] == "")]
                    )
                )
            )

            self.logger.info(
                "{} new records that need to be checked for inclusion".format(
                    len(sheet[sheet[f"{field}last_reviewed_by"] == ""])
                )
            )


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
        "-a",
        "--archive",
        action="store_true",
        help="""
        If flagged, send agencies listed in the `agencies.sample` Google Sheet but not in the FBI CDE data to 
        the `agencies.archive` Google Sheet.
        """,
    )
    parser.add_argument(
        "-qc",
        "--quality_check",
        action="store_true",
        help="""
        """,
    )
    args = parser.parse_args()

    AgenciesSheetUpdate(args).run()

import pandas as pd
import sys

from datetime import datetime as dt
from datetime import timedelta as td

sys.path.append("../utils")

from aws import snapshot_df
from crimes import rtci_to_nibrs
from google_configs import gc_files, pull_sheet, update_sheet
from logger import create_logger


class Auditor:
    def __init__(self, arguments):
        self.logger = create_logger()
        self.args = arguments
        self.stem = "https://rtci.s3.us-east-1.amazonaws.com/data/"

        self.last = (
            dt.now().replace(day=1, hour=23, minute=59, second=59, microsecond=999999)
            - td(days=1)
        ).replace(day=1) - td(
            days=1
        )  # last day of month before last
        self.first = self.last - td(days=365)
        self.max_year = self.last.year
        self.max_month = self.last.month

        self.crimes = {
            k: v
            for e in [
                {crime: d["Crime Against"] for d in rtci_to_nibrs[crime]}
                for crime in rtci_to_nibrs
            ]
            for k, v in e.items()
        }
        self.property = [k for k in self.crimes if self.crimes[k] == "Property"]

        self.sheet = pull_sheet(sheet="audit", url=gc_files["agencies"])
        self.removals = list()
        self.removal_cols = ["r1", "r2", "r3", "r4", "r5", "s5", "r6", "s6", "r7"]

    def run(self):
        df = pd.read_csv(self.stem + "aggregated.csv")
        df["date"] = pd.to_datetime(
            df["year"].astype(str) + "-" + df["month"].astype(str), format="%Y-%m"
        )
        df["property"] = df[self.property].sum(axis=1)

        for ori in df["ori"].unique():
            tmp = df[df["ori"] == ori]
            latest = tmp[
                (tmp["year"] == self.max_year) & (tmp["month"] == self.max_month)
            ]
            assert 0 <= len(latest) <= 1

            # 1 — no data row for second-to-most-recent month
            if len(latest) == 0:
                self.removals.append({"ori": ori, "r1": 1})
                continue

            # 2 — row of all missing crime cols for second-to-most-recent month
            if latest[list(self.crimes.keys())].isna().all().all():
                self.removals.append({"ori": ori, "r2": 1})
                continue

            # 3 — row of all zero crime cols for second-to-most-recent month
            if latest[list(self.crimes.keys())].iloc[0].sum() == 0:
                self.removals.append({"ori": ori, "r3": 1})
                continue

            # 4 — zero theft in second-to-most-recent month
            if latest["theft"].iloc[0] == 0:
                self.removals.append({"ori": ori, "r4": 1})
                continue

            # 5 — property crimes in second-to-most-recent month > 2 deviations of last-twelve mean
            # TODO: what do we do if not all last 12 months are present?
            year = tmp[tmp["date"] >= self.first]
            property_mean = year["property"].mean()
            property_std = year["property"].std()
            latest_devs = (latest.iloc[0]["property"] - property_mean) / property_std
            if (
                not property_mean - (2 * property_std)
                <= latest.iloc[0]["property"]
                <= property_mean + (2 * property_std)
            ):
                self.removals.append({"ori": ori, "r5": 1, "s5": latest_devs})
                continue

            # 6 — property crimes in any of most recent 12 months > 3 deviations of last-twelve mean
            # TODO: (same as 5) what do we do if not all last 12 months are present?
            # TODO: what if there are multiple months that are outside range?
            if (year["property"] >= property_mean + (3 * property_std)).any() or (
                year["property"] <= property_mean - (3 * property_std)
            ).any():
                flagged_devs = (
                    year[
                        (year["property"] >= property_mean + (3 * property_std))
                        | (year["property"] <= property_mean - (3 * property_std))
                    ].iloc[0]["property"]
                    - property_mean
                ) / property_std
                self.removals.append({"ori": ori, "r6": 1, "s6": flagged_devs})
                continue

            # 7 — second-to-most-recent month thefts lowest overall
            # TODO: same question do we discount from this analysis if missing x number of rows?
            # TODO: also what if the same min appears more than once across the data?
            overall_min = tmp["theft"].min()
            overall_min = tmp[tmp["theft"] == overall_min].iloc[-1]
            if (
                overall_min["year"] == self.max_year
                and overall_min["month"] == self.max_month
            ):
                self.removals.append({"ori": ori, "r7": 1})

        rem = pd.DataFrame(self.removals)
        for col in self.removal_cols:
            if col not in rem:
                rem[col] = None
        rem = rem[["ori"] + self.removal_cols]
        df = pd.merge(df, rem, how="left", on="ori")
        df = df.drop(columns=["date"])

        self.logger.info(f"sample record: {df.to_dict('records')[0]}")
        if not self.args.test:
            snapshot_df(
                logger=self.logger,
                df=df,
                path="data/",
                filename=f"audited",
            )

        # print()
        # print(f"Auditing aggregated.csv up to: {self.max_month}-{self.max_year}")
        # print()
        #
        # print("Agencies missing scraped data for the most recent month:")
        # print()
        # for d in (
        #     df[df["ori"].isin(self.removals_1)]
        #     .drop_duplicates("ori")[["ori", "name"]]
        #     .to_dict("records")
        # ):
        #     print("   ", d["ori"], d["name"])
        # print()
        #
        # print("Agencies with all null crime counts for the most recent month:")
        # print()
        # for d in (
        #     df[df["ori"].isin(self.removals_2)]
        #     .drop_duplicates("ori")[["ori", "name"]]
        #     .to_dict("records")
        # ):
        #     print("   ", d["ori"], d["name"])
        # print()
        #
        # print("Agencies with all zero crime counts for the most recent month:")
        # print()
        # for d in (
        #     df[df["ori"].isin(self.removals_3)]
        #     .drop_duplicates("ori")[["ori", "name"]]
        #     .to_dict("records")
        # ):
        #     print("   ", d["ori"], d["name"])
        # print()
        #
        # print("Agencies with zero thefts for the most recent month:")
        # print()
        # for d in (
        #     df[df["ori"].isin(self.removals_4)]
        #     .drop_duplicates("ori")[["ori", "name"]]
        #     .to_dict("records")
        # ):
        #     print("   ", d["ori"], d["name"])
        # print()
        #
        # print(
        #     "Agencies where the most recent month's property crimes count is > 1.5 standard deviations from the "
        #     "most-recent-twelve-month mean:"
        # )
        # print()
        # for d in (
        #     df[df["ori"].isin(self.removals_5)]
        #     .drop_duplicates("ori")[["ori", "name"]]
        #     .to_dict("records")
        # ):
        #     print("   ", d["ori"], d["name"])
        # print()
        #
        # print(
        #     "Agencies where the property crimes count for any month in the most recent twelve is > 2 standard "
        #     "deviations from the most-recent-twelve-month mean:"
        # )
        # print()
        # for d in (
        #     df[df["ori"].isin(self.removals_6)]
        #     .drop_duplicates("ori")[["ori", "name"]]
        #     .to_dict("records")
        # ):
        #     print("   ", d["ori"], d["name"])
        # print()
        #
        # print("Agencies where the most recent month's theft count is a global minimum:")
        # print()
        # for d in (
        #     df[df["ori"].isin(self.removals_7)]
        #     .drop_duplicates("ori")[["ori", "name"]]
        #     .to_dict("records")
        # ):
        #     print("   ", d["ori"], d["name"])
        # print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="""If flagged, output a sample graph locally.""",
    )
    args = parser.parse_args()
    Auditor(args).run()

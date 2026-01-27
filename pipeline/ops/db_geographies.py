import numpy as np
import pandas as pd
import sys
import us

from datetime import datetime as dt
from datetime import timedelta as td

sys.path.append("../utils")
from aws import list_directories, list_files, snapshot_df, snapshot_json
from logger import create_logger


# TODO: accidentally forcing data to span most recent month instead of second-to-most-recent?


class SiteGeographies:
    def __init__(self, arguments):
        pd.set_option("display.max_columns", 100)
        self.logger = create_logger()
        self.args = arguments

        # read in `data/aggregated.csv` and `fbi/cde_oris.csv`
        self.oris = pd.read_csv(
            "https://rtci.s3.us-east-1.amazonaws.com/fbi/cde_oris.csv"
        )
        self.agg = pd.read_csv(
            "https://rtci.s3.us-east-1.amazonaws.com/data/aggregated.csv"
        )

        # stash a mapping of all agencies included for a given geographic entity
        self.included = {
            "all": dict(),
            "sm": dict(),
            "md": dict(),
            "lg": dict(),
            "xl": dict(),
        }

        # define date range for inclusion (2017-01-01 to end of month before last)
        self.start = dt(2017, 1, 1, 0, 0)
        self.end = (
            (
                dt.now().replace(day=1, hour=23, minute=0, second=0, microsecond=0)
                - td(days=1)
            ).replace(day=1)
            - td(days=1)
        ).replace(day=1, hour=0, minute=0)
        self.logger.info(f"date range: {self.start} to {self.end}")

        # define population bins
        self.pop_bins = {
            "all": (0, np.inf, ""),
            "sm": (0, 99_999, " (Agencies of <100k)"),
            "md": (100_000, 249_999, " (Agencies of 100k-250k)"),
            "lg": (250_000, 999_999, " (Agencies of 250k-1m)"),
            "xl": (1_000_000, np.inf, " (Agencies of 1m+)"),
        }

        # for hierarchical removal of divisional denominations
        self.order = ["state", "division", "region", "nation"]

    @staticmethod
    def get_abbreviation(s):
        try:
            return us.states.lookup(s).abbr.lower()
        except AttributeError:
            if s == "Washington DC":
                return "dc"

    def get_agency_sizes(self, i):
        for p in {k: v for k, v in self.pop_bins.items() if k != "all"}:
            if self.pop_bins[p][0] <= i <= self.pop_bins[p][1]:
                return p
        return "all"

    def run(self):
        # get scraped data date ranges for oris where available
        self.get_date_ranges()
        self.logger.info(f"oris in fbi list: {self.oris['ori'].nunique()}")
        self.logger.info(f"oris in aggregated csv: {self.agg['ori'].nunique()}")

        # only keep agencies with data
        self.oris = self.oris[(self.oris["start"].notna()) & (self.oris["end"].notna())]
        self.logger.info(f"oris with date data: {len(self.oris)}")

        # preformat the data a little bit
        self.preformat()

        # get agency-level and aggregated entity-level data
        agencies = self.format_agencies()
        aggregates = self.aggregate_geographies()
        records = pd.concat([agencies, aggregates.dropna(axis=1, how="all")])

        # stash list of agency oris per geographic entity to a json to be used by `db_crimes.py`
        included_agencies = records[["id", "size", "agency_list"]].to_dict("records")

        # tidy up column order on geographies df
        records = self.post_format(records)

        self.logger.info(f"sample includes_agencies record: {included_agencies[0]}")
        self.logger.info(
            f"sample geographies record: {records.tail(1).to_dict('records')}"
        )
        if not self.args.test:
            snapshot_df(self.logger, records, "data/site/", filename="geographies")
            snapshot_json(
                self.logger,
                included_agencies,
                "data/site/",
                filename="geographies_included",
            )

    def format_agencies(self):
        df = self.oris.copy()
        df["id"] = df["ori"]
        df.loc[:, "agency_list"] = df["ori"].apply(lambda s: [s])
        df["type"] = df["type"].str.lower()
        df = df.drop(columns=["ori"])
        df = df.drop(columns=self.order)
        df = df.rename(columns={f"{o}_abbr": o for o in self.order})
        df["start"] = dt.strftime(self.start, "%Y-%m")
        df["end"] = dt.strftime(self.end, "%Y-%m")
        return df

    def aggregate_geographies(self):
        aggregates = list()

        # iterate through geographic entities (other than city/county agency)
        for field in self.order:
            df = self.oris.copy()

            # only keep agencies that span default date range (2017-01 to second-to-most-recent month)
            df = df[(df["start"] <= self.start) & (df["end"] >= self.end)]
            df["start"] = dt.strftime(self.start, "%Y-%m")
            df["end"] = dt.strftime(self.end, "%Y-%m")

            # run through unique values of geography
            for f in df[field].unique():
                g = df.copy()
                g = g[g[field] == f]
                g["name"] = f
                g["type"] = field
                g[["latitude", "longitude"]] = None, None

                # run through all population size bins
                for p in self.pop_bins:
                    s = g[
                        (self.pop_bins[p][0] <= g["population"])
                        & (g["population"] <= self.pop_bins[p][1])
                    ]
                    s.loc[:, "size"] = p
                    s.loc[:, "agencies"] = s["ori"].nunique()
                    pop = s["population"].sum()
                    agencies = s["ori"].tolist()

                    # some geographies may have no agencies in the specified population bin
                    if len(s) == 0:
                        continue

                    s = s.iloc[0]
                    s["id"] = s[f"{field}_abbr"]
                    s["population"] = pop
                    s["agency_list"] = agencies
                    s["name"] = s["name"] + self.pop_bins[p][2]
                    del s["ori"]

                    for o in self.order:
                        s[o] = s[f"{o}_abbr"]
                        del s[f"{o}_abbr"]

                    # remove values for sub-entities of this geography
                    for o in self.order[: self.order.index(field)]:
                        s[o] = None

                    aggregates.append(s)

        return pd.DataFrame(aggregates)

    def get_date_ranges(self):
        # get earliest and latest scrape dates for each ori in self.agg
        self.agg["date"] = pd.to_datetime(self.agg[["year", "month"]].assign(day=1))
        minima = {
            d["ori"]: d["date"]
            for d in self.agg.groupby("ori")["date"]
            .min()
            .reset_index()
            .to_dict("records")
        }
        maxima = {
            d["ori"]: d["date"]
            for d in self.agg.groupby("ori")["date"]
            .max()
            .reset_index()
            .to_dict("records")
        }
        dates = self.agg.copy()
        dates = dates.drop_duplicates("ori")[["ori"]]
        dates["start"] = dates["ori"].map(minima)
        dates["end"] = dates["ori"].map(maxima)

        # merge these scrape date ranges into self.oris
        self.oris = pd.merge(self.oris, dates, how="left", on="ori")

    def preformat(self):
        # set population bin size field
        self.oris["size"] = self.oris["pop"].apply(lambda i: self.get_agency_sizes(i))

        # default number of agencies to 1
        self.oris["agencies"] = 1

        # drop and rename columns
        self.oris = self.oris.rename(columns={"pop": "population"})

        # TODO: below block only needs to be kept until `agencies/cde_filter_oris.py` is rerun
        rmap = {"s": "sth", "w": "wst", "ne": "noe", "mw": "mdw"}
        dmap = {
            "p": "pcfc",
            "m": "mntn",
            "wnc": "wncn",
            "wsc": "wscn",
            "enc": "encn",
            "esc": "escn",
            "ne": "nwen",
            "sa": "soat",
            "ma": "mdat",
        }
        self.oris["region_abbr"] = self.oris["region_abbr"].map(rmap)
        self.oris["division_abbr"] = self.oris["division_abbr"].map(dmap)
        # TODO ***************************************************************************** #

    @staticmethod
    def post_format(df):
        df = df[
            [
                "id",
                "name",
                "type",
                "state",
                "region",
                "division",
                "size",
                "population",
                "agencies",
                "latitude",
                "longitude",
                "start",
                "end",
            ]
        ]
        return df


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="""If flagged, do not interact with sheet.""",
    )
    args = parser.parse_args()

    SiteGeographies(args).run()

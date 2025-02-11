import pandas as pd
import sys
import us

from datetime import datetime as dt
from plotly import express as px

sys.path.append("../utils")

from aws import get_s3_client, snapshot_fig
from crimes import rtci_to_nibrs
from logger import create_logger


class Grapher:
    def __init__(self, arguments):
        self.logger = create_logger()
        self.args = arguments
        self.crimes = [crime.title().replace("_", " ") for crime in rtci_to_nibrs]
        self.start = dt(2018, 1, 1, 0, 0)
        self.bucket_url = "https://rtci.s3.us-east-1.amazonaws.com/"
        self.scrape_url = self.bucket_url + "qc/aggregated_since_2017.csv"
        self.prefix = "qc/graphs/"

        # disable warning on df slicing
        pd.options.mode.chained_assignment = None

    def run(self):
        # read in `final_sample.csv` for existing data to compare
        sample = pd.read_csv(
            "https://github.com/AH-Datalytics/rtci/blob/development/data/final_sample.csv?raw=true",
            low_memory=False,
        )[["date", "Agency Name", "State", *self.crimes]].rename(
            columns={"date": "Date"}
        )
        sample["Source"] = "final_sample.csv"

        # read in scraped data
        df = pd.read_csv(self.scrape_url)
        df["Source"] = "scraper"

        if self.args.oris:
            df = df[df["ORI"].isin(self.args.oris)]

        # run through individual agencies to produce comparison graphs
        for ori in df["ORI"].unique():
            # extract agency data from scraped data
            agency = df[df["ORI"] == ori]
            agency["Date"] = pd.to_datetime(agency[["Year", "Month"]].assign(day=1))
            agency = agency[agency["Date"] >= self.start]

            # extract agency data from `final_sample.csv`
            sample_agency = sample[
                (sample["Agency Name"] == agency["Agency Name"].unique()[0])
                & (sample["State"] == agency["State"].unique()[0])
            ]

            # run through individual crimes to product comparison graphs
            for crime in self.crimes:
                agency_crime = agency[
                    ["ORI", "Agency Name", "State", crime, "Date", "Source"]
                ]
                sample_agency_crime = sample_agency[
                    ["Agency Name", "State", crime, "Date", "Source"]
                ]
                to_graph = pd.concat([agency_crime, sample_agency_crime], axis=0)
                to_graph["Date"] = pd.to_datetime(to_graph["Date"])

                # generate figure
                fig = px.line(
                    to_graph,
                    x="Date",
                    y=crime,
                    color="Source",
                    color_discrete_map={
                        "final_sample.csv": "#2D5EF9",
                        "scraper": "red",
                    },
                    labels={
                        crime: f"Reported {crime.rstrip('y') + 'ie' if crime.endswith('y') else crime}s Per Month"
                    },
                    line_shape="spline",
                )
                fig.update_traces(mode="lines+markers")
                fig.update_traces(line=dict(width=2.25))
                fig.update_traces(marker=dict(size=5))
                fig.update_layout(
                    title=f"Show me reported <b style='color:#2D5EF9'>{crime.rstrip('y') + 'ie' if crime.endswith('y') else crime}s</b> in <b style='color:#2D5EF9'>{us.states.lookup(to_graph['State'].unique()[0]).name}</b> for <b style='color:#2D5EF9'>{to_graph['Agency Name'].unique()[0]}</b> as <b style='color:#2D5EF9'>Monthly Totals</b>"
                )

                if self.args.test:
                    fig.show()
                else:
                    # save figure to s3
                    snapshot_fig(
                        logger=self.logger,
                        fig=fig,
                        path=self.prefix,
                        filename=f"{to_graph['State'].unique()[0].lower()}/{to_graph['Agency Name'].unique()[0].lower().replace(' ', '_')}/{crime.lower().replace(' ', '_')}",
                    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o",
        "--oris",
        nargs="*",
        type=str,
        help="""Optional list of ORIs for which to produce graphs.""",
    )
    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="""If flagged, output a sample graph locally.""",
    )
    args = parser.parse_args()
    Grapher(args).run()

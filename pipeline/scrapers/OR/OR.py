import pandas as pd
import sys

sys.path.append("../../utils")
from airtable import get_records_from_sheet
from super import Scraper


class Oregon(Scraper):
    def __init__(self):
        super().__init__()
        self.base = "https://www.oregon.gov/osp/Docs/Open-Data/"
        self.offenses_url = self.base + "OpenData-Offenses-All.csv"
        self.victims_url = self.base + "OpenData-Victims-All.csv"
        self.exclude_oris = ["OR0260200"]
        self.oris = []
        self.o_map = {
            "Aggravated Assault": "aggravated_assault",
            "Burglary": "burglary",
            "Forcible Rape": "rape",
            "Larceny/Theft Offenses": "theft",
            "Motor Vehicle Theft": "motor_vehicle_theft",
            "Robbery": "robbery",
        }
        self.v_map = {
            "Murder and Non-Negligent Manslaughter": "murder",
        }

    def scrape(self):
        # get list of agencies in state from airtable
        agencies = [
            {"ori": d["ori"], "name_cde": d["agency_cde"]}
            for d in get_records_from_sheet(
                self.logger,
                "Metadata",
                # formula=f"{{state}}='{self.state_full_name}'"
                # note: this includes agencies that are not included
                # in the existing RTCI sample (audited out for missing data, etc.);
                # to include only those matching the `final_sample.csv` file, use:
                #
                formula=f"AND({{state}}='{self.state_full_name}',NOT({{agency_rtci}}=''))",
            )
            if d["ori"] not in self.exclude_oris
        ]

        # make sure we have 1:1 mapping of OR agency names with the CDE source
        odf = pd.read_csv(self.offenses_url, low_memory=False)[
            ["Agency Name", "IncidentDate", "NIBRS Report Title", "Distinct Offenses"]
        ]
        o_potential_matches = [
            a
            for a in odf["Agency Name"].unique()
            if any([a.startswith(n["name_cde"]) for n in agencies])
        ]
        assert len(o_potential_matches) == len(agencies)

        for a in o_potential_matches:
            for d in agencies:
                if a.startswith(d["name_cde"]):
                    d.update({"name_or": a})

        # fold in the second CSV (victims as opposed to offenses)
        vdf = pd.read_csv(self.victims_url, low_memory=False)[
            [
                "Agency Name",
                "IncidentDate",
                "NIBRS Crime Description",
                "Distinct Offense Victims",
            ]
        ]
        v_potential_matches = [
            a
            for a in vdf["Agency Name"].unique()
            if any([a.startswith(n["name_cde"]) for n in agencies])
        ]
        assert set(v_potential_matches) == set(o_potential_matches)

        # a few more assertions to make sure we're 1:1 mapping
        assert len(set([d["name_or"] for d in agencies])) == len(agencies)
        assert len(set([d["ori"] for d in agencies])) == len(agencies)

        self.oris.extend([d["ori"] for d in agencies])

        # map CSVs to ORIs and include only viable agencies
        odf = odf[odf["Agency Name"].isin([d["name_or"] for d in agencies])]
        vdf = vdf[vdf["Agency Name"].isin([d["name_or"] for d in agencies])]
        odf["ori"] = odf["Agency Name"].map({d["name_or"]: d["ori"] for d in agencies})
        vdf["ori"] = vdf["Agency Name"].map({d["name_or"]: d["ori"] for d in agencies})

        # subset `offenses.csv` to all non-murder crimes
        # subset `victims.csv` to murder
        odf["crime"] = odf["NIBRS Report Title"].map(self.o_map)
        odf = odf[odf["crime"].notna()]
        vdf["crime"] = vdf["NIBRS Crime Description"].map(self.v_map)
        vdf = vdf[vdf["crime"].notna()]

        # group by year/month and sum counts
        odf["date"] = pd.to_datetime(odf["IncidentDate"])
        odf["year"] = odf["date"].dt.year
        odf["month"] = odf["date"].dt.month
        odf = (
            odf.groupby(["ori", "year", "month", "crime"])["Distinct Offenses"]
            .sum()
            .reset_index()
            .pivot(
                index=["ori", "year", "month"],
                columns="crime",
                values="Distinct Offenses",
            )
            .reset_index()
        )

        vdf["date"] = pd.to_datetime(vdf["IncidentDate"])
        vdf["year"] = vdf["date"].dt.year
        vdf["month"] = vdf["date"].dt.month
        vdf = (
            vdf.groupby(["ori", "year", "month", "crime"])["Distinct Offense Victims"]
            .sum()
            .reset_index()
            .pivot(
                index=["ori", "year", "month"],
                columns="crime",
                values="Distinct Offense Victims",
            )
            .reset_index()
        )

        # merge murders into rest of data and return
        df = pd.merge(odf, vdf, how="left", on=["ori", "year", "month"])
        for crime in self.crimes:
            df[crime] = df[crime].fillna(0.0)
        return df.to_dict("records")


Oregon().run()

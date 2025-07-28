import pandas as pd
import sys

sys.path.append("../../utils")
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
        # get list of agencies in state from Google sheet
        agencies = self.get_agencies(self.exclude_oris)

        # make sure we have 1:1 mapping of OR agency names with the CDE source
        odf = pd.read_csv(self.offenses_url, low_memory=False)[
            ["Agency Name", "IncidentDate", "NIBRS Report Title", "Distinct Offenses"]
        ]
        odf["Agency Name"] = odf["Agency Name"].apply(
            lambda s: self.match_prep_agency(s)
        )
        o_potential_matches = [a for a in odf["Agency Name"].unique() if a in agencies]
        assert len(o_potential_matches) == len(agencies)
        odf = odf[odf["Agency Name"].isin(o_potential_matches)]
        assert set(odf["Agency Name"].unique()) == set(agencies.keys())
        odf["ori"] = odf["Agency Name"].map(agencies)

        # fold in the second CSV (victims as opposed to offenses)
        vdf = pd.read_csv(self.victims_url, low_memory=False)[
            [
                "Agency Name",
                "IncidentDate",
                "NIBRS Crime Description",
                "Distinct Offense Victims",
            ]
        ]
        vdf["Agency Name"] = vdf["Agency Name"].apply(
            lambda s: self.match_prep_agency(s)
        )
        v_potential_matches = [a for a in vdf["Agency Name"].unique() if a in agencies]
        assert len(v_potential_matches) == len(agencies)
        vdf = vdf[vdf["Agency Name"].isin(v_potential_matches)]
        assert set(vdf["Agency Name"].unique()) == set(agencies.keys())
        vdf["ori"] = vdf["Agency Name"].map(agencies)

        self.oris.extend(list(agencies.values()))

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

    @staticmethod
    def match_prep_agency(s):
        if s.endswith(" PD"):
            return s.replace(" PD", " Police Department")
        elif s.endswith(" PD MIP"):
            return s.replace(" PD MIP", " Police Department")
        elif s.endswith(" SO"):
            return s.replace(" SO", " County Sheriff's Office")
        return s


Oregon().run()

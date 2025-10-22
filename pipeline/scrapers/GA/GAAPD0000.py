import json
import numpy as np
import pandas as pd
import requests
import sys

sys.path.append("../../utils")
from crimes import rtci_to_nibrs
from super import Scraper


class GAAPD0000(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["GAAPD0000"]
        self.url_2021 = (
            "https://services3.arcgis.com/Et5Qfajgiyosiw4d/arcgis/rest/services"
            "/OpenDataWebsite_Crime_view/FeatureServer/createReplica"
        )
        self.url_2009 = (
            "https://services3.arcgis.com/Et5Qfajgiyosiw4d/arcgis/rest/services"
            "/2009_2020CrimeData/FeatureServer/createReplica"
        )
        self.headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded",
            "Priority": "u=1, i",
            "Sec-Ch-Ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        }
        self.map_2009 = {
            "BURGLARY": "burglary",
            "LARCENY-FROM VEHICLE": "theft",
            "AUTO THEFT": "motor_vehicle_theft",
            "LARCENY-NON VEHICLE": "theft",
            "AGG ASSAULT": "aggravated_assault",
            "HOMICIDE": "murder",
            "ROBBERY": "robbery",
        }
        self.map_2021 = {
            k: v
            for e in [
                {d["Offense Code"]: crime for d in rtci_to_nibrs[crime]}
                for crime in rtci_to_nibrs
            ]
            for k, v in e.items()
        }
        self.records = list()

    def scrape(self):
        # collect data from source for 2021-01-01 to present (NIBRS)
        data = (
            "f=json"
            "&layers=0"
            "&layerQueries=%7B%220%22%3A%7B%22where%22%3A%22("
            f"ReportDate%20"
            f"BETWEEN%20timestamp%20'2021-01-01%2005%3A00%3A00'%20"
            f"AND%20timestamp%20'{self.last.date()}%2004%3A00%3A00')%20"
            f"AND%20ReportDate%20%3C%3E%20timestamp%20'{self.last.date()}%20"
            f"04%3A00%3A00'%22%2C"
            "%22useGeometry%22%3Afalse%2C"
            "%22queryOption%22%3A%22useFilter%22%2C"
            "%22fields%22%3A%22"
            "ReportDate%2C"
            "NibrsUcrCode%2C"
            "Vic_Count%22%7D%7D"
            "&replicaName=Crime%20Data%20Sort%20Newest"
            "&transportType=esriTransportTypeUrl"
            "&returnAttachments=false"
            "&returnAttachmentsDataByUrl=true"
            "&async=true"
            "&syncModel=none"
            "&targetType=client"
            "&syncDirection=download"
            "&attachmentsSyncDirection=none"
            "&dataFormat=csv"
            "&exportFieldDomainDescription=true"
        )

        # first, get the NIBRS CSV download status URL (including request params)
        p = requests.post(self.url_2021, headers=self.headers, data=data)
        j = json.loads(p.text)
        status_url = j["statusUrl"] + "?f=json"

        # next, get the CSV URL for NIBRS data
        result_url = ""
        while result_url == "":
            r = requests.get(status_url)
            j = json.loads(r.text)
            result_url = j["resultUrl"]

        # read in the CSV of NIBRS data
        df = pd.read_csv(result_url)[["ReportDate", "NibrsUcrCode", "Vic_Count"]]
        df["ReportDate"] = pd.to_datetime(df["ReportDate"])
        df["year"] = df["ReportDate"].dt.year
        df["month"] = df["ReportDate"].dt.month
        del df["ReportDate"]
        df = df[df["NibrsUcrCode"].isin(self.map_2021)]
        df["NibrsUcrCode"] = df["NibrsUcrCode"].map(self.map_2021)
        df["Vic_Count"] = np.where(df["Vic_Count"].isna(), 1, df["Vic_Count"])
        df = (
            df.groupby(["year", "month", "NibrsUcrCode"])["Vic_Count"]
            .sum()
            .reset_index()
            .pivot(index=["year", "month"], columns="NibrsUcrCode", values="Vic_Count")
        ).reset_index()
        self.records.extend(df.to_dict("records"))

        # if necessary, collect data from source for 2009-2020 (UCR)
        if self.first.year < 2021:
            data = (
                "f=json"
                "&layers=0"
                "&layerQueries=%7B%220%22%3A%7B%22"
                "where%22%3A%221%3D1%22%2C%22"
                "useGeometry%22%3Afalse%2C"
                "%22queryOption%22%3A%22useFilter%22%2C"
                "%22fields%22%3A%22"
                "Report_Date%2C"
                "Crime_Type%22%7D%7D"
                "&replicaName=2009_2020CrimeData"
                "&transportType=esriTransportTypeUrl"
                "&returnAttachments=false"
                "&returnAttachmentsDataByUrl=true"
                "&async=true"
                "&syncModel=none"
                "&targetType=client"
                "&syncDirection=download"
                "&attachmentsSyncDirection=none"
                "&dataFormat=csv"
                "&exportFieldDomainDescription=true"
            )

            # first, get the UCR CSV download status URL (including request params)
            p = requests.post(self.url_2009, headers=self.headers, data=data)
            j = json.loads(p.text)
            status_url = j["statusUrl"] + "?f=json"

            # next, get the CSV URL for UCR data
            result_url = ""
            while result_url == "":
                r = requests.get(status_url)
                j = json.loads(r.text)
                result_url = j["resultUrl"]

            # read in the CSV of UCR data
            df = pd.read_csv(result_url)[["Report Date", "Crime Type"]]
            df["Report Date"] = pd.to_datetime(
                df["Report Date"], format="%m/%d/%Y %I:%M:%S %p"
            )
            df["year"] = df["Report Date"].dt.year
            df["month"] = df["Report Date"].dt.month
            del df["Report Date"]
            df = df[df["Crime Type"].isin(self.map_2009)]
            df["Crime Type"] = df["Crime Type"].map(self.map_2009)
            df = (
                df.groupby(["year", "month"])["Crime Type"]
                .value_counts()
                .reset_index()
                .pivot(index=["year", "month"], columns="Crime Type", values="count")
            ).reset_index()
            self.records.extend(df.to_dict("records"))

        return self.records


GAAPD0000().run()

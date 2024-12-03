import calendar
import pandas as pd
import sys

from bs4 import BeautifulSoup as bS
from collections import Counter
from datetime import datetime as dt
from datetime import timedelta as td

sys.path.append("../../utils")
from parallelize import thread
from requests_configs import mount_legacy_session
from super import Scraper


class Richmond(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["VA1220000"]
        self.session = mount_legacy_session()
        self.url = "https://apps.richmondgov.com/applications/crimeinfo/Home/Search"
        self.incident_url = (
            "https://apps.richmondgov.com/applications/crimeinfo/Home/IncidentListing?"
        )
        self.crosswalk = {
            d["OFFENSE DESCRIPTION"]: d["Category"]
            for d in pd.read_excel(self.crosswalks.VA1220000).to_dict("records")
        }

    def get_months(self):
        months = list()
        for year in range(self.first.year, dt.now().year + 1):
            months.extend(self.get_year(year))

        # slice on index of month before last
        idx = next(
            (
                i
                for i, tup in enumerate(months)
                if tup[1] == dt.strftime(self.last, "%m/%d/%Y")
            ),
            -1,
        )
        months = months[: idx + 1]
        return months

    @staticmethod
    def get_year(year):
        months = list()
        for month in range(1, 13):
            first_day = dt(year, month, 1)
            last_day = first_day + td(days=calendar.monthrange(year, month)[1] - 1)
            months.append(
                (dt.strftime(first_day, "%m/%d/%Y"), dt.strftime(last_day, "%m/%d/%Y"))
            )
        return months

    def scrape(self):
        # get first and last date of each month in range
        months = self.get_months()

        # collect data per month
        data = thread(self.get_monthly_data, months)

        # format data
        df = pd.DataFrame(data)

        # note: usually we do not fill missing values with 0s,
        # but in this case values are counts from running through
        # the full set of incidents, so if there's a systematically
        # missing field, we'll have to pick it up later in audit
        df[list(self.crimes.keys())] = (
            df[list(self.crimes.keys())].fillna(0).astype(int)
        )

        return df.to_dict("records")

    def get_precinct_incident_data(self, month, precinct):
        data = {
            "beginningDate": month[0],
            "endingDate": month[1],
            "crimeType": "ALL",
            "locationCode": "CSZ",
            "areaCode": "ALL",
            "drillDownAreaCode": int(precinct),
            "drillDownAreaDesc": int(precinct),
        }

        r = self.session.get(self.incident_url, data=data)
        soup = bS(r.text, "lxml")
        table = soup.find("table", {"id": "tblIncidentListing"})

        headers = [th.text.strip() for th in table.find("thead").find_all("th")]
        off_desc_idx = headers.index("OFFENSE DESCRIPTION")
        offenses = [
            tr.find_all("td")[off_desc_idx].text.strip()
            for tr in table.find("tbody").find_all("tr")
        ]

        offenses = [o for o in offenses if o in self.crosswalk]
        offenses = [self.crosswalk[o] for o in offenses]
        results = Counter(offenses)

        return results

    def get_monthly_data(self, month):
        data = {
            "BeginningDate": month[0],
            "EndingDate": month[1],
            "CrimeType": "ALL",
            "CivicAssociation": "ALL",
            "CouncilDistrict": "ALL",
            "LocationType": "CSZ",
            "Neighborhood": "ALL",
            "PolicePrecinct": "ALL",
            "PoliceSector": "ALL",
            "DispatchZone": "ALL",
        }

        r = self.session.post(self.url, data=data)
        soup = bS(r.text, "lxml")
        table = soup.find("table", {"id": "tblResults"})
        headers = [th.text.strip() for th in table.find("thead").find_all("th")]
        pct_idx = headers.index("PRECINCT")
        precincts = [
            tr.find_all("td")[pct_idx].text.strip()
            for tr in table.find("tbody").find_all("tr")
        ]

        per_precinct = Counter()
        for precinct in precincts:
            per_precinct.update(self.get_precinct_incident_data(month, precinct))

        data = dict(per_precinct)
        data = {k.lower().replace(" ", "_"): v for k, v in data.items()}
        data["date"] = dt.strptime(month[0], "%m/%d/%Y")

        return data


Richmond().run()

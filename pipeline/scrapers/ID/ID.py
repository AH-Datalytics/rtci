import sys

sys.path.append("../../utils")
from platforms.optimum import Optimum


class Idaho(Optimum):
    def __init__(self):
        super().__init__()
        self.agency_list_url = "https://nibrs.isp.idaho.gov/CrimeInIdaho/Report/GetReportByValues?ReportType=Agency"
        self.data_url = (
            "https://nibrs.isp.idaho.gov/CrimeInIdaho/Report/GetCrimeTrends?"
        )


Idaho().run()

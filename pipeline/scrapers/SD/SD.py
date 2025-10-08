import sys

sys.path.append("../../utils")
from platforms.optimum import Optimum


class SouthDakota(Optimum):
    def __init__(self):
        super().__init__()
        self.agency_list_url = (
            "https://sdcrime.nibrs.com/Report/GetReportByValues?ReportType=Agency"
        )
        self.data_url = "https://sdcrime.nibrs.com/Report/GetCrimeTrends?"


SouthDakota().run()

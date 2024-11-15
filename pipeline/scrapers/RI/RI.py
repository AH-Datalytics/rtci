import sys

sys.path.append("../../utils")
from platforms.optimum import Optimum


class RhodeIsland(Optimum):
    def __init__(self):
        super().__init__()
        self.agency_list_url = (
            "https://riucr.nibrs.com/Report/GetReportByValues?ReportType=Agency"
        )
        self.data_url = "https://riucr.nibrs.com/Report/GetCrimeTrends?"


RhodeIsland().run()

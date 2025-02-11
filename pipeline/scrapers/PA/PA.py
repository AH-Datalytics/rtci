import sys

sys.path.append("../../utils")
from platforms.optimum import Optimum


class Pennsylvania(Optimum):
    def __init__(self):
        super().__init__()
        self.agency_list_url = "https://www.ucr.pa.gov/PAUCRSPublic/Report/GetReportByValues?ReportType=Agency"
        self.data_url = "https://www.ucr.pa.gov/PAUCRSPublic/Report/GetCrimeTrends?"
        self.exclude_oris = ["PAPPD0000"]
        self.threader = False


Pennsylvania().run()

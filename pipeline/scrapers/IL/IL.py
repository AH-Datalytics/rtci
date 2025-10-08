import sys

sys.path.append("../../utils")
from platforms.optimum import Optimum


class Illinois(Optimum):
    def __init__(self):
        super().__init__()
        self.agency_list_url = (
            "https://ilucr.nibrs.com/Report/GetReportByValues?ReportType=Agency"
        )
        self.data_url = "https://ilucr.nibrs.com/Report/GetCrimeTrends?"
        self.exclude_oris = ["ILCPD0000"]
        self.threader = False


Illinois().run()

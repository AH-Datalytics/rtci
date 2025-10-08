import sys

sys.path.append("../../utils")
from platforms.optimum import Optimum


class Texas(Optimum):
    def __init__(self):
        super().__init__()
        self.agency_list_url = (
            "https://txucr.nibrs.com/SRSReport/GetSRSReportByValues?ReportType=Agency"
        )
        self.data_url = "https://txucr.nibrs.com/SRSReport/GetCrimeTrends?"
        self.srs = True


Texas().run()

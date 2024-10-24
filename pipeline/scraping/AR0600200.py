import requests
import sys

sys.path.append("../utils")
from super import Scraper


class AR0600200(Scraper):
    def __init__(self):
        super().__init__()
        self.path = "IL/CPD0000/"
        self.offenses = {
            "All Homicide Offenses": "murder",
            "Forcible Rape": "rape",
            "Robbery": "robbery",
            "Aggravated Assault": "aggravated_assault",
            "Burglary/B & E": "burglary",
            "Larceny": "theft",
            "Stolen Vehicle": "motor_vehicle_theft",
        }

    def scrape(self):
        pdf = requests.get(
            "https://www.littlerock.gov/media/21988/part-i-offenses-by-month.pdf"
        )


AR0600200().run()

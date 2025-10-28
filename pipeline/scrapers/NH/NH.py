import sys

sys.path.append("../../utils")

from super import Scraper


class NewHampshire(Scraper):
    def __init__(self):
        super().__init__()
        self.oris = ["NH0064600"]

    def scrape(self):
        pass


NewHampshire().run()

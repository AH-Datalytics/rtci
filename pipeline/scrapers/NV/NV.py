import sys

sys.path.append("../../utils")
from platforms.tops import Tops


class Nevada(Tops):
    def __init__(self):
        super().__init__()
        self.url = "https://nevadacrimestats.nv.gov/public/View/dispview.aspx"


Nevada().run()

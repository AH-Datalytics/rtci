import sys

sys.path.append("../../utils")
from platforms.tops import Tops


class Missouri(Tops):
    def __init__(self):
        super().__init__()
        self.url = "https://showmecrime.mo.gov/public/View/dispview.aspx"


Missouri().run()

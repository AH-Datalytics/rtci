import sys

sys.path.append("../../utils")
from platforms.tops import Tops


class Massachusetts(Tops):
    def __init__(self):
        super().__init__()
        self.url = "https://ma.beyond2020.com/ma_public/View/dispview.aspx"


Massachusetts().run()

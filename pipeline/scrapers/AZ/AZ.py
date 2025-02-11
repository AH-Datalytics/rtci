import sys

sys.path.append("../../utils")
from platforms.tops import Tops


class Arizona(Tops):
    def __init__(self):
        super().__init__()
        self.url = "https://azcrimestatistics.azdps.gov/public/Dim/dimension.aspx"


Arizona().run()

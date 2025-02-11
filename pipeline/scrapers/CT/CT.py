import sys

sys.path.append("../../utils")
from platforms.tops import Tops


class Connecticut(Tops):
    def __init__(self):
        super().__init__()
        self.url = "https://ct.beyond2020.com/ct_public/Browse/browsetables.aspx"


Connecticut().run()

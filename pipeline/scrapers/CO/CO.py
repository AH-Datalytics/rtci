import sys

sys.path.append("../../utils")
from platforms.tops import Tops


class Colorado(Tops):
    def __init__(self):
        super().__init__()
        self.url = "https://coloradocrimestats.state.co.us/public"


Colorado().run()

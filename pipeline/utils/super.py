import json
import sys

sys.path.append("../utils")
from logger import create_logger
from time import time

from aws import snapshot_json


class Scraper:
    def __init__(self):
        self.logger = create_logger()
        self.run_time = int(time())
        self.path = None
        self.crimes = [
            "murder",
            "rape",
            "robbery",
            "aggravated_assault",
            "burglary",
            "theft",
            "motor_vehicle_theft",
        ]

    @staticmethod
    def scrape():
        return []

    def process(self, data):
        assert isinstance(data, list)
        assert len(data) > 0
        self.run_time = int(time())
        for i, d in enumerate(data):
            data[i]["last_updated"] = self.run_time
        return json.dumps(data)

    def run(self):
        data = self.scrape()
        self.process(data)
        self.logger.info("sample record:")
        self.logger.info(f"{data[0]}")
        snapshot_json(
            logger=self.logger,
            json_data=data,
            path=self.path,
            timestamp=self.run_time,
        )

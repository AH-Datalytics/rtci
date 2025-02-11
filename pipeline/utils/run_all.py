import os
import subprocess


EXCLUDE = [".DS_Store", "__pycache__"]
states = sorted([d for d in os.listdir("../scrapers") if d not in EXCLUDE])


for state in states:
    scrapes = sorted(os.listdir(f"../scrapers/{state}"))
    for scrape in scrapes:
        print(f"RUNNING {scrape.upper()}...")
        subprocess.run(f"cd ../scrapers/{state} && python3 {scrape}", shell=True)

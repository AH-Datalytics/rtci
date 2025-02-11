import subprocess

for state in ["MO", "AZ", "CO", "CT", "MA", "NV"]:
    print(f"testing {state}...")
    subprocess.run(f"cd ../../scrapers/{state} && python3 {state}.py -t", shell=True)

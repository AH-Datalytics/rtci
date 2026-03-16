"""Run all scrapers locally, logging successes and failures."""
import os
import subprocess
import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pathlib import Path
from time import time

SCRAPERS_DIR = Path(__file__).parent.parent / "scrapers"
# 12 months back from current month
FIRST = (datetime.now() - relativedelta(months=12)).strftime("%Y-%m")

successes = []
failures = []

# MA has its own workflow (Playwright-based, not super.py)
SKIP_STATES = {"MA"}
states = sorted([d.name for d in SCRAPERS_DIR.iterdir() if d.is_dir() and not d.name.startswith("_") and d.name not in SKIP_STATES])
print(f"Found {len(states)} states to scrape")

t0 = time()

for state in states:
    state_dir = SCRAPERS_DIR / state
    scripts = sorted([f.name for f in state_dir.iterdir() if f.suffix == ".py" and f.name != "__init__.py"])

    for script in scripts:
        label = f"{state}/{script}"
        print(f"\n{'='*60}")
        print(f"Running {label}...")
        print(f"{'='*60}")

        try:
            proc = subprocess.Popen(
                [sys.executable, script, "--first", FIRST, "--test"],
                cwd=str(state_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            try:
                stdout, _ = proc.communicate(timeout=300)  # 5 min max
            except subprocess.TimeoutExpired:
                # Kill entire process tree (important on Windows for browser processes)
                import signal
                try:
                    proc.kill()
                except Exception:
                    pass
                proc.wait(timeout=10)
                failures.append((label, "timeout (5 min)"))
                print(f"  TIMEOUT")
                continue

            if proc.returncode == 0:
                for line in (stdout or "").split("\n"):
                    if "completed oris" in line:
                        print(f"  {line.strip()}")
                    elif "earliest data" in line or "latest data" in line:
                        print(f"  {line.strip()}")
                successes.append(label)
                print(f"  SUCCESS")
            else:
                err_lines = (stdout or "").strip().split("\n")
                for line in err_lines[-5:]:
                    print(f"  {line}")
                failures.append((label, err_lines[-1] if err_lines else "unknown error"))
                print(f"  FAILED (exit code {proc.returncode})")

        except Exception as e:
            failures.append((label, str(e)))
            print(f"  ERROR: {e}")

elapsed = time() - t0
print(f"\n{'='*60}")
print(f"DONE in {elapsed/60:.1f} minutes")
print(f"Successes: {len(successes)}")
print(f"Failures:  {len(failures)}")
if failures:
    print(f"\nFailed scrapers:")
    for label, err in failures:
        print(f"  {label}: {err}")

"""
Tool 4: Automation 4 - Daily workflow runner.
Runs every automation in order, once a day, with no one pressing buttons:
  1. Summarize superintendents' daily field logs
  2. Draft RFIs for issues found in the logs
  3. Predict delays and alert project managers
If one step fails, the others still run, and everything is written to a log file.
"""
import os
import sys
import subprocess
import time
from datetime import datetime

STEPS = [
    ("Summarize daily site reports", "src/summarize_reports.py"),
    ("Draft RFIs from field issues", "src/draft_rfis.py"),
    ("Delay risk alerts", "src/delay_alerts.py"),
]
LOG_DIR = "logs"


def log(message, log_file):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {message}"
    print(line)
    log_file.write(line + "\n")
    log_file.flush()


def run_step(name, script, log_file):
    log(f"START  {name}", log_file)
    start = time.time()
    env = {**os.environ, "PYTHONUTF8": "1"}  # force UTF-8 so emojis and special characters work on Windows
    result = subprocess.run([sys.executable, script], capture_output=True, text=True,
                            encoding="utf-8", errors="replace", env=env)
    log_file.write(result.stdout)
    seconds = time.time() - start
    if result.returncode == 0:
        log(f"OK     {name} ({seconds:.1f}s)", log_file)
        return True
    log_file.write(result.stderr)
    last_error = (result.stderr.strip().splitlines() or ["unknown error"])[-1]
    log(f"FAILED {name} ({seconds:.1f}s): {last_error}", log_file)
    return False


if __name__ == "__main__":
    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, f"daily_run_{datetime.now():%Y-%m-%d}.log")
    with open(log_path, "a", encoding="utf-8") as log_file:
        log("===== Daily automation run =====", log_file)
        results = [run_step(name, script, log_file) for name, script in STEPS]
        passed = sum(results)
        log(f"===== Finished: {passed}/{len(STEPS)} steps succeeded =====", log_file)
    print(f"\nFull log: {log_path}")
    sys.exit(0 if passed == len(STEPS) else 1)
from __future__ import annotations

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import CAPTURE_LOG_CSV, RAW_DIR, ensure_project_dirs

def main() -> int:
    ensure_project_dirs()
    files = sorted(RAW_DIR.glob("*.mat"))
    if not files:
        print("No MATLAB capture files found in data/raw")
        return 1

    rows = []
    for f in files:
        rows.append({"file": str(f)})

    with open(CAPTURE_LOG_CSV, "w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=["file"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Indexed {len(files)} raw captures in {CAPTURE_LOG_CSV}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
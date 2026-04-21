import csv
import sys
from pathlib import Path

# Add root to path so we can import dsp_utils
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import CAPTURE_LOG_CSV, RAW_DIR, ensure_project_dirs
from processing.dsp_utils import load_mat_capture

def main() -> int:
    ensure_project_dirs()
    files = sorted(RAW_DIR.glob("*.mat"))
    if not files:
        print("No MATLAB capture files found in data/raw")
        return 1

    rows = []
    for f in files:
        try:
            # Extract metadata directly from the file
            data = load_mat_capture(str(f))
            rows.append({
                "file": f.name,
                "radio_id": data.get("radio_id", "unknown"),
                "trial": data.get("trial_num", "N/A"),
                "center_freq_hz": data.get("center_freq_hz", 0),
                "note": data.get("note", "")
            })
        except Exception as e:
            print(f"Skipping {f.name} due to error: {e}")

    # Write the full metadata log, not just the file path
    fieldnames = ["radio_id", "trial", "center_freq_hz", "note", "file"]
    with open(CAPTURE_LOG_CSV, "w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Successfully indexed {len(rows)} captures into {CAPTURE_LOG_CSV}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
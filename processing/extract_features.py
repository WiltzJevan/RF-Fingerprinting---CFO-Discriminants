from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

from capture.burst_detector import extract_padded_burst, find_burst_regions
from config import DETECT, FEATURES, FEATURES_CSV, PROCESSED_DIR, RAW_DIR, SLICED_DIR, SUMMARY_CSV, ensure_project_dirs
from processing.dsp_utils import load_mat_capture
from processing.feature_utils import (
    estimate_cfo_fft,
    occupied_bandwidth,
    rise_time_feature,
    spectral_centroid,
    stable_inner_region,
    transient_energy_ratio,
)

def main() -> int:
    ensure_project_dirs()
    files = sorted(RAW_DIR.glob("*.mat"))
    if not files:
        print("No .mat capture files found in data/raw")
        return 1

    rows = []
    slice_counter = 0

    for file in files:
        S = load_mat_capture(str(file))
        iq = np.asarray(S["iq"]).astype(np.complex64).reshape(-1)
        fs = float(np.asarray(S["sample_rate_hz"]).squeeze())
        raw_id = S.get("radio_id", "unknown")
        if isinstance(raw_id, np.ndarray):
            radio_id = str(raw_id.item()) if raw_id.size > 0 else "unknown"
        else:
            radio_id = str(raw_id)
        trial = int(np.asarray(S.get("trial_num", -1)).squeeze())
        center_freq_hz = float(np.asarray(S["center_freq_hz"]).squeeze())
        gain_db = float(np.asarray(S["gain_db"]).squeeze())
        note = str(S.get("note", ""))

        regions = find_burst_regions(
            iq,
            sample_rate_hz=fs,
            power_margin_db=DETECT.power_margin_db,
            min_burst_duration_s=DETECT.min_burst_duration_s,
            smooth_len=DETECT.smooth_len,
        )

        if not regions:
            regions = [None]

        for idx, region in enumerate(regions, start=1):
            if region is None:
                burst = iq
            else:
                burst, _, _ = extract_padded_burst(
                    iq,
                    region.start_idx,
                    region.end_idx,
                    fs,
                    DETECT.pre_trigger_s,
                    DETECT.post_trigger_s,
                )

            steady = stable_inner_region(burst, fs, FEATURES.steady_trim_s)

            row = {
                "source_file": str(file),
                "radio_id": radio_id,
                "trial": trial,
                "center_freq_hz": center_freq_hz,
                "sample_rate_hz": fs,
                "gain_db": gain_db,
                "note": note,
                "segment_index": idx,
                "cfo_hz": estimate_cfo_fft(steady, fs),
                "occupied_bw_hz": occupied_bandwidth(steady, fs, FEATURES.occupied_bw_frac),
                "spectral_centroid_hz": spectral_centroid(steady, fs),
                "rise_time_s": rise_time_feature(burst, fs),
                "transient_energy_ratio": transient_energy_ratio(burst, fs, FEATURES.transient_window_s),
                "burst_duration_s": len(burst) / fs,
            }

            slice_counter += 1
            slice_path = SLICED_DIR / f"{radio_id}_slice_{slice_counter:04d}.npy"
            np.save(slice_path, burst.astype(np.complex64))
            row["slice_file"] = str(slice_path)

            rows.append(row)

    df = pd.DataFrame(rows).sort_values(["radio_id", "trial", "segment_index"])
    df.to_csv(FEATURES_CSV, index=False)

    summary = df.groupby("radio_id")[[
        "cfo_hz", "occupied_bw_hz", "spectral_centroid_hz",
        "rise_time_s", "transient_energy_ratio", "burst_duration_s"
    ]].agg(["mean", "std", "min", "max", "count"])
    summary.to_csv(SUMMARY_CSV)

    print(f"Saved features: {FEATURES_CSV}")
    print(f"Saved summary:  {SUMMARY_CSV}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import FEATURES_CSV, PROCESSED_DIR
from processing.dsp_utils import fft_spectrum_db, normalize_trace_db, load_mat_capture

def save_box(df: pd.DataFrame, col: str, ylabel: str, fname: str):
    clean = df.dropna(subset=[col])
    if clean.empty:
        return
    plt.figure(figsize=(8, 5))
    clean.boxplot(column=col, by="radio_id")
    plt.ylabel(ylabel)
    plt.title(f"{ylabel} by Radio")
    plt.suptitle("")
    plt.tight_layout()
    plt.savefig(PROCESSED_DIR / fname, dpi=200)
    plt.close()

def main() -> int:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(FEATURES_CSV)
    df = df[df['radio_id'].str.lower() != 'baseline'] #optional drop baseline here

    plt.figure(figsize=(8, 5))
    for radio_id, sub in df.groupby("radio_id"):
        plt.scatter([radio_id] * len(sub), sub["cfo_hz"], alpha=0.8)
    plt.ylabel("CFO (Hz)")
    plt.title("Carrier Frequency Offset by Radio")
    plt.tight_layout()
    plt.savefig(PROCESSED_DIR / "cfo_scatter.png", dpi=200)
    plt.close()

    save_box(df, "cfo_hz", "CFO (Hz)", "cfo_boxplot.png")
    save_box(df, "occupied_bw_hz", "Occupied Bandwidth (Hz)", "occupied_bw_boxplot.png")
    save_box(df, "spectral_centroid_hz", "Spectral Centroid (Hz)", "spectral_centroid_boxplot.png")
    save_box(df, "rise_time_s", "Rise Time (s)", "rise_time_boxplot.png")
    save_box(df, "transient_energy_ratio", "Transient Energy Ratio", "transient_ratio_boxplot.png")

    plt.figure(figsize=(10, 6))
    used_any = False
    for radio_id, sub in df.groupby("radio_id"):
        traces = []
        for _, row in sub.head(5).iterrows():
            S = load_mat_capture(row["source_file"])
            iq = np.asarray(S["iq"]).astype(np.complex64).reshape(-1)
            fs = float(np.asarray(S["sample_rate_hz"]).squeeze())
            freqs, mag_db = fft_spectrum_db(iq[:8192], fs)
            if len(freqs) == 0:
                continue
            traces.append(normalize_trace_db(mag_db))
        if traces:
            mean_trace = np.mean(np.vstack(traces), axis=0)
            plt.plot(freqs / 1e3, mean_trace, label=radio_id)
            used_any = True

    if used_any:
        plt.xlabel("Baseband Offset (kHz)")
        plt.ylabel("Normalized Magnitude (dB)")
        plt.title("Overlaid Normalized Spectra")
        plt.legend()
        plt.tight_layout()
        plt.savefig(PROCESSED_DIR / "spectral_overlays.png", dpi=200)
    plt.close()

    print(f"Plots saved to {PROCESSED_DIR}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
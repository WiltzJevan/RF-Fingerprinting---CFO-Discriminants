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


def percentile_ylim(series: pd.Series, lower_q: float = 0.05, upper_q: float = 0.95) -> tuple[float, float]:
    """Return padded y-limits based on percentiles to reduce outlier-driven axis compression."""
    clean = series.dropna()

    if clean.empty:
        return 0.0, 1.0

    lower = float(clean.quantile(lower_q))
    upper = float(clean.quantile(upper_q))

    if lower == upper:
        pad = abs(lower) * 0.05 if lower != 0 else 1.0
        return lower - pad, upper + pad

    pad = 0.08 * (upper - lower)
    return lower - pad, upper + pad


def save_box(df: pd.DataFrame, col: str, ylabel: str, fname: str) -> None:
    """Save a boxplot with hidden outlier markers and percentile-limited y-axis."""
    clean = df.dropna(subset=[col, "radio_id"])

    if clean.empty:
        return

    plt.figure(figsize=(8, 5))

    clean.boxplot(
        column=col,
        by="radio_id",
        showfliers=False,
    )

    # Overlay all points lightly so the viewer still sees spread and possible outliers.
    grouped = list(clean.groupby("radio_id"))
    for x_pos, (radio_id, sub) in enumerate(grouped, start=1):
        jitter = np.random.normal(loc=0.0, scale=0.035, size=len(sub))
        plt.scatter(
            np.full(len(sub), x_pos) + jitter,
            sub[col],
            alpha=0.35,
            s=18,
        )

    ymin, ymax = percentile_ylim(clean[col], 0.05, 0.95)
    plt.ylim(ymin, ymax)

    plt.ylabel(ylabel)
    plt.xlabel("radio_id")
    plt.title(f"{ylabel} by Radio")
    plt.suptitle("")
    plt.grid(True, axis="y", alpha=0.6)
    plt.tight_layout()
    plt.savefig(PROCESSED_DIR / fname, dpi=200)
    plt.close()


def save_cfo_scatter(df: pd.DataFrame) -> None:
    """Save CFO scatter plot with percentile-limited y-axis."""
    clean = df.dropna(subset=["cfo_hz", "radio_id"])

    if clean.empty:
        return

    plt.figure(figsize=(8, 5))

    grouped = list(clean.groupby("radio_id"))
    for x_pos, (radio_id, sub) in enumerate(grouped, start=1):
        jitter = np.random.normal(loc=0.0, scale=0.035, size=len(sub))
        plt.scatter(
            np.full(len(sub), x_pos) + jitter,
            sub["cfo_hz"],
            alpha=0.65,
            s=35,
            label=radio_id,
        )

    ymin, ymax = percentile_ylim(clean["cfo_hz"], 0.05, 0.95)
    plt.ylim(ymin, ymax)

    plt.xticks(
        ticks=range(1, len(grouped) + 1),
        labels=[radio_id for radio_id, _ in grouped],
    )

    plt.ylabel("CFO (Hz)")
    plt.xlabel("radio_id")
    plt.title("Carrier Frequency Offset by Radio")
    plt.grid(True, axis="y", alpha=0.6)
    plt.tight_layout()
    plt.savefig(PROCESSED_DIR / "cfo_scatter.png", dpi=200)
    plt.close()


def save_spectral_overlay(df: pd.DataFrame) -> None:
    """Save overlaid normalized spectra for the first few captures from each radio."""
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
        plt.grid(True, alpha=0.4)
        plt.tight_layout()
        plt.savefig(PROCESSED_DIR / "spectral_overlays.png", dpi=200)

    plt.close()


def main() -> int:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(FEATURES_CSV)

    # Drop baseline captures from comparison plots.
    if "radio_id" in df.columns:
        df = df[df["radio_id"].astype(str).str.lower() != "baseline"]

    save_cfo_scatter(df)

    save_box(df, "cfo_hz", "CFO (Hz)", "cfo_boxplot.png")
    save_box(df, "occupied_bw_hz", "Occupied Bandwidth (Hz)", "occupied_bw_boxplot.png")
    save_box(df, "spectral_centroid_hz", "Spectral Centroid (Hz)", "spectral_centroid_boxplot.png")
    save_box(df, "rise_time_s", "Rise Time (s)", "rise_time_boxplot.png")
    save_box(df, "transient_energy_ratio", "Transient Energy Ratio", "transient_ratio_boxplot.png")

    save_spectral_overlay(df)

    print(f"Plots saved to {PROCESSED_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
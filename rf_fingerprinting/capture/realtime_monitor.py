"""from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from config import CAPTURE_LOG_CSV, RAW_DIR, SDR, SESSION_LOG_CSV, ensure_project_dirs


def append_csv_row(path: Path, row: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Realtime-ish monitor using repeated rtl_sdr short captures.")
    parser.add_argument("--radio-id", required=True)
    parser.add_argument("--center-freq", type=float, default=SDR.center_freq_hz)
    parser.add_argument("--sample-rate", type=float, default=SDR.sample_rate_hz)
    parser.add_argument("--gain", type=float, default=SDR.gain_db)
    parser.add_argument("--chunk-duration", type=float, default=0.35, help="Seconds per refresh capture")
    parser.add_argument("--fft-size", type=int, default=4096)
    parser.add_argument("--waterfall-rows", type=int, default=150)
    return parser.parse_args()


def check_rtl_sdr_available() -> None:
    try:
        result = subprocess.run(
            ["rtl_sdr", "-h"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print("ERROR: rtl_sdr command not found.", file=sys.stderr)
        raise SystemExit(1)

    if result.returncode not in (0, 1):
        print("ERROR: rtl_sdr exists but did not run correctly.", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(1)


def read_cu8_iq_file(path: Path) -> np.ndarray:
    raw = np.fromfile(path, dtype=np.uint8)
    if len(raw) % 2 != 0:
        raw = raw[:-1]
    i = raw[0::2].astype(np.float32)
    q = raw[1::2].astype(np.float32)
    iq = ((i - 127.5) / 127.5) + 1j * ((q - 127.5) / 127.5)
    return iq.astype(np.complex64)


def fft_spectrum_db(iq: np.ndarray, fs: float) -> tuple[np.ndarray, np.ndarray]:
    if len(iq) == 0:
        return np.array([]), np.array([])
    window = np.hanning(len(iq))
    spec = np.fft.fftshift(np.fft.fft(iq * window))
    freqs = np.fft.fftshift(np.fft.fftfreq(len(iq), d=1.0 / fs))
    mag_db = 20.0 * np.log10(np.abs(spec) + 1e-12)
    return freqs, mag_db


def capture_chunk(
    tmp_file: Path,
    center_freq: float,
    sample_rate: float,
    gain: float,
    duration_s: float,
    device_index: int = 0,
) -> Optional[np.ndarray]:
    sample_count = int(sample_rate * duration_s)
    cmd = [
        "rtl_sdr",
        "-d", str(device_index),
        "-f", str(int(center_freq)),
        "-s", str(int(sample_rate)),
        "-g", str(float(gain)),
        "-n", str(sample_count),
        str(tmp_file),
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(result.stderr)
        return None

    if not tmp_file.exists():
        return None

    iq = read_cu8_iq_file(tmp_file)
    tmp_file.unlink(missing_ok=True)
    return iq


def main() -> int:
    args = parse_args()
    ensure_project_dirs()
    check_rtl_sdr_available()

    ts = time.strftime("%Y%m%d_%H%M%S")
    append_csv_row(
        SESSION_LOG_CSV,
        {
            "timestamp": ts,
            "radio_id": args.radio_id,
            "trial": "",
            "duration_s": "",
            "center_freq_hz": args.center_freq,
            "sample_rate_hz": args.sample_rate,
            "gain_db": args.gain,
            "note": "realtime_monitor_cli",
            "mode": "realtime_monitor_cli",
        },
    )

    fft_size = args.fft_size
    waterfall_rows = args.waterfall_rows
    waterfall = np.full((waterfall_rows, fft_size), -140.0, dtype=np.float32)

    fig, (ax_psd, ax_wf) = plt.subplots(2, 1, figsize=(12, 8))
    freq_axis = np.linspace(-args.sample_rate / 2, args.sample_rate / 2, fft_size) / 1e3

    (line_psd,) = ax_psd.plot(freq_axis, np.full(fft_size, -140.0))
    ax_psd.set_title("Live Spectrum")
    ax_psd.set_xlabel("Baseband Offset (kHz)")
    ax_psd.set_ylabel("Magnitude (dB)")
    ax_psd.set_ylim(-140, 20)
    ax_psd.grid(True)

    im = ax_wf.imshow(
        waterfall,
        origin="lower",
        aspect="auto",
        interpolation="nearest",
        extent=[freq_axis[0], freq_axis[-1], 0, waterfall_rows],
        vmin=-120,
        vmax=10,
    )
    ax_wf.set_title("Waterfall")
    ax_wf.set_xlabel("Baseband Offset (kHz)")
    ax_wf.set_ylabel("Recent Frames")
    fig.colorbar(im, ax=ax_wf, label="dB")

    status_text = fig.text(0.01, 0.01, "Starting...", fontsize=10, family="monospace")

    tmp_file = RAW_DIR / "_monitor_tmp.cu8"

    def update(_frame):
        nonlocal waterfall

        iq = capture_chunk(
            tmp_file=tmp_file,
            center_freq=args.center_freq,
            sample_rate=args.sample_rate,
            gain=args.gain,
            duration_s=args.chunk_duration,
        )
        if iq is None or len(iq) == 0:
            status_text.set_text("Capture failed")
            return line_psd, im, status_text

        if len(iq) >= fft_size:
            chunk = iq[:fft_size]
        else:
            chunk = np.pad(iq, (0, fft_size - len(iq)))

        freqs, mag_db = fft_spectrum_db(chunk, args.sample_rate)
        if len(freqs) == fft_size:
            line_psd.set_data(freqs / 1e3, mag_db)
            waterfall = np.roll(waterfall, -1, axis=0)
            waterfall[-1, :] = mag_db.astype(np.float32)
            im.set_data(waterfall)

        peak_db = float(np.max(mag_db)) if len(mag_db) else float("nan")
        status_text.set_text(
            f"Radio: {args.radio_id} | Center: {args.center_freq/1e6:.6f} MHz | "
            f"Rate: {args.sample_rate/1e6:.3f} MS/s | Gain: {args.gain:.1f} dB | "
            f"Chunk: {args.chunk_duration:.2f} s | Peak: {peak_db:.1f} dB | Close window to quit"
        )
        return line_psd, im, status_text

    ani = FuncAnimation(fig, update, interval=max(200, int(args.chunk_duration * 1000)), blit=False)
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    plt.show()
    tmp_file.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())"""

print("Use MATLAB survey_rt29.m for live monitoring.")
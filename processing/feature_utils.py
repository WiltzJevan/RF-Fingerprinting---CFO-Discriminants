from __future__ import annotations

import numpy as np
from processing.dsp_utils import estimate_psd

def stable_inner_region(iq: np.ndarray, fs: float, trim_s: float) -> np.ndarray:
    trim = int(trim_s * fs)
    if len(iq) <= 2 * trim + 1:
        return iq
    return iq[trim:-trim]

def estimate_cfo_fft(iq: np.ndarray, fs: float) -> float:
    if len(iq) < 1024:
        return float("nan")
    window = np.hanning(len(iq))
    spec = np.fft.fftshift(np.fft.fft(iq * window))
    freqs = np.fft.fftshift(np.fft.fftfreq(len(iq), d=1.0 / fs))

    # --- Zero out the DC spike area ---
    # We zero out the middle 1% of the spectrum (the DC spike)
    center_idx = len(spec) // 2
    notch_width = int(len(spec) * 0.01) # Adjust if the spike is wider
    spec[center_idx - notch_width : center_idx + notch_width] = 0
    # ---------------------------------------

    return float(freqs[int(np.argmax(np.abs(spec)))])

def occupied_bandwidth(iq: np.ndarray, fs: float, frac: float = 0.99) -> float:
    freqs, psd = estimate_psd(iq, fs)
    if len(freqs) == 0:
        return float("nan")
    p = np.abs(psd)
    total = np.sum(p)
    if total <= 0:
        return float("nan")
    p /= total
    cdf = np.cumsum(p)
    lo_idx = int(np.searchsorted(cdf, (1 - frac) / 2))
    hi_idx = int(np.searchsorted(cdf, 1 - (1 - frac) / 2))
    lo_idx = max(0, min(lo_idx, len(freqs) - 1))
    hi_idx = max(0, min(hi_idx, len(freqs) - 1))
    return float(freqs[hi_idx] - freqs[lo_idx])

def spectral_centroid(iq: np.ndarray, fs: float) -> float:
    freqs, psd = estimate_psd(iq, fs)
    if len(freqs) == 0:
        return float("nan")
    p = np.abs(psd)
    denom = np.sum(p)
    if denom <= 0:
        return float("nan")
    return float(np.sum(freqs * p) / denom)

def rise_time_feature(iq: np.ndarray, fs: float) -> float:
    env = np.abs(iq)
    if len(env) < 64:
        return float("nan")
    peak = np.max(env)
    if peak <= 0:
        return float("nan")
    lo = 0.1 * peak
    hi = 0.9 * peak
    lo_idx = np.flatnonzero(env >= lo)
    hi_idx = np.flatnonzero(env >= hi)
    if len(lo_idx) == 0 or len(hi_idx) == 0:
        return float("nan")
    return float((hi_idx[0] - lo_idx[0]) / fs)

def transient_energy_ratio(iq: np.ndarray, fs: float, transient_window_s: float) -> float:
    n = min(len(iq), int(transient_window_s * fs))
    if n <= 0:
        return float("nan")
    total = np.sum(np.abs(iq) ** 2)
    if total <= 0:
        return float("nan")
    return float(np.sum(np.abs(iq[:n]) ** 2) / total)
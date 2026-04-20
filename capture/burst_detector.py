from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple
import numpy as np

@dataclass
class BurstDetectionResult:
    start_idx: int
    end_idx: int
    threshold_db: float
    noise_floor_db: float
    peak_db: float

def moving_average(x: np.ndarray, n: int) -> np.ndarray:
    n = max(1, int(n))
    kernel = np.ones(n, dtype=np.float64) / n
    return np.convolve(x, kernel, mode="same")

def power_envelope_db(iq: np.ndarray, smooth_len: int) -> np.ndarray:
    power = np.abs(iq) ** 2
    smooth = moving_average(power, smooth_len)
    return 10.0 * np.log10(np.maximum(smooth, 1e-12))

def find_burst_regions(
    iq: np.ndarray,
    sample_rate_hz: float,
    power_margin_db: float,
    min_burst_duration_s: float,
    smooth_len: int,
) -> List[BurstDetectionResult]:
    env_db = power_envelope_db(iq, smooth_len=smooth_len)
    noise_floor_db = float(np.percentile(env_db, 20))
    threshold_db = noise_floor_db + power_margin_db
    above = env_db > threshold_db

    if not np.any(above):
        return []

    idx = np.flatnonzero(above)
    splits = np.where(np.diff(idx) > 1)[0]
    start_positions = np.r_[0, splits + 1]
    end_positions = np.r_[splits, len(idx) - 1]

    min_len = int(min_burst_duration_s * sample_rate_hz)
    out = []

    for s_pos, e_pos in zip(start_positions, end_positions):
        s = int(idx[s_pos])
        e = int(idx[e_pos])
        if (e - s + 1) < min_len:
            continue
        peak_db = float(np.max(env_db[s:e+1]))
        out.append(BurstDetectionResult(s, e, threshold_db, noise_floor_db, peak_db))

    return out

def extract_padded_burst(
    iq: np.ndarray,
    start_idx: int,
    end_idx: int,
    sample_rate_hz: float,
    pre_trigger_s: float,
    post_trigger_s: float,
) -> Tuple[np.ndarray, int, int]:
    pre = int(pre_trigger_s * sample_rate_hz)
    post = int(post_trigger_s * sample_rate_hz)
    s0 = max(0, start_idx - pre)
    s1 = min(len(iq), end_idx + post)
    burst = iq[s0:s1]
    return burst, start_idx - s0, end_idx - s0
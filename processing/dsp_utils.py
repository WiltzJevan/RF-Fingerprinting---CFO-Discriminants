from __future__ import annotations
from typing import Tuple, Any
import numpy as np
from scipy.io import loadmat
from scipy.signal import welch

def _to_str(val: Any) -> str:
    """Helper to convert MATLAB array-strings to clean Python strings."""
    if isinstance(val, np.ndarray):
        if val.size == 1:
            return str(val.item())
        return str(val.tolist())
    return str(val)

def load_mat_capture(path: str) -> dict:
    # Use squeeze_me=True to flatten redundant (1,1) dimensions
    s = loadmat(path, squeeze_me=True, struct_as_record=False)
    out = {}
    for k, v in s.items():
        if not k.startswith("__"):
            # Sanitize specific string-heavy fields
            if k in ["radio_id", "note"]:
                out[k] = _to_str(v)
            else:
                out[k] = v
    return out

def estimate_psd(iq: np.ndarray, fs: float, nperseg: int = 8192) -> Tuple[np.ndarray, np.ndarray]:
    if len(iq) < 32:
        return np.array([]), np.array([])
    nperseg = min(nperseg, len(iq))
    freqs, psd = welch(
        iq,
        fs=fs,
        window="hann",
        nperseg=nperseg,
        noverlap=nperseg // 2,
        return_onesided=False,
        scaling="density",
    )
    return np.fft.fftshift(freqs), np.fft.fftshift(psd)

def fft_spectrum_db(iq: np.ndarray, fs: float):
    if len(iq) == 0:
        return np.array([]), np.array([])
    window = np.hanning(len(iq))
    spec = np.fft.fftshift(np.fft.fft(iq * window))
    freqs = np.fft.fftshift(np.fft.fftfreq(len(iq), d=1.0 / fs))
    mag_db = 20.0 * np.log10(np.abs(spec) + 1e-12)
    return freqs, mag_db

def normalize_trace_db(trace_db: np.ndarray) -> np.ndarray:
    if len(trace_db) == 0:
        return trace_db
    return trace_db - np.max(trace_db)
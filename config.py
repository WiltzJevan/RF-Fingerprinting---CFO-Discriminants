from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
SLICED_DIR = DATA_DIR / "sliced"
PROCESSED_DIR = DATA_DIR / "processed"
LOG_DIR = ROOT / "logs"

CAPTURE_LOG_CSV = LOG_DIR / "capture_log.csv"
FEATURES_CSV = PROCESSED_DIR / "features.csv"
SUMMARY_CSV = PROCESSED_DIR / "summary_stats.csv"

@dataclass(frozen=True)
class DetectionConfig:
    power_margin_db: float = 10.0
    min_burst_duration_s: float = 0.15
    pre_trigger_s: float = 0.05
    post_trigger_s: float = 0.10
    smooth_len: int = 2048

@dataclass(frozen=True)
class FeatureConfig:
    occupied_bw_frac: float = 0.99
    steady_trim_s: float = 0.10
    transient_window_s: float = 0.15

DETECT = DetectionConfig()
FEATURES = FeatureConfig()

def ensure_project_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    SLICED_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
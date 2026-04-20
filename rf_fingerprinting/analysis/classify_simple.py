from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import LeaveOneOut
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from config import FEATURES_CSV

def evaluate(df: pd.DataFrame, feature_cols: list[str]) -> None:
    clean = df.dropna(subset=feature_cols + ["radio_id"]).copy()
    if clean["radio_id"].nunique() < 2:
        print(f"Need at least 2 radios for {feature_cols}")
        return

    X = clean[feature_cols].to_numpy(dtype=float)
    y = clean["radio_id"].to_numpy()

    loo = LeaveOneOut()
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("knn", KNeighborsClassifier(n_neighbors=1)),
    ])

    preds = []
    truth = []

    for train_idx, test_idx in loo.split(X):
        model.fit(X[train_idx], y[train_idx])
        preds.append(model.predict(X[test_idx])[0])
        truth.append(y[test_idx][0])

    acc = accuracy_score(truth, preds)
    labels = sorted(np.unique(y))
    cm = confusion_matrix(truth, preds, labels=labels)

    print("\n================================")
    print("Features:", feature_cols)
    print("LOO Accuracy:", round(acc, 4))
    print("Labels:", labels)
    print(cm)

def main() -> int:
    df = pd.read_csv(FEATURES_CSV)
    evaluate(df, ["cfo_hz"])
    evaluate(df, ["cfo_hz", "occupied_bw_hz", "spectral_centroid_hz"])
    evaluate(df, ["cfo_hz", "occupied_bw_hz", "spectral_centroid_hz", "rise_time_s", "transient_energy_ratio"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
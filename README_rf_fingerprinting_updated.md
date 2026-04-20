# RF Transmitter Fingerprinting with SDR

## Overview
This project explores whether identical handheld radios exhibit unique and consistent RF characteristics that can be used for device identification (RF fingerprinting).

The system uses an RTL-SDR for signal capture, MATLAB for controlled acquisition, and Python for feature extraction and analysis.

---

## Objective
Determine whether individual radios can be distinguished using:

- Carrier Frequency Offset (CFO)
- Occupied Bandwidth
- Spectral Centroid
- Rise Time
- Transient Energy Ratio

---

## System Pipeline
RF Signal → RTL-SDR → MATLAB Capture → `.mat` Files  
→ Python Processing → Feature Extraction → Analysis / Classification

---

## Equipment Setup

### SDR Hardware
Recommended:
- RTL-SDR Blog V4 or Nooelec NESDR Mini 2
- Frequency range: ~25 MHz – 1.7 GHz
- Sample rate: 2.0–2.4 MS/s

### Antenna
- Wideband antenna (700–2700 MHz recommended)
- Place antenna in open space, away from metal objects

### Computer
- MATLAB (with SDR support package)
- Ubuntu / WSL for Python processing

---

## Radio Setup

### Radios Used
- UHF handheld radios (e.g., Retevis RT29)

### Configuration
- Set all radios to the SAME channel (e.g., Channel 14)
- Determine actual frequency (~462.515 MHz for testing)
- Ensure radios are fully charged
- Disable extra features if possible (VOX, scanning, etc.)

### Positioning
- Keep radio 0.5–2 meters from SDR antenna
- Maintain consistent orientation for all trials
- Avoid moving during capture

### Transmission Procedure
- Press and HOLD PTT for entire capture duration
- Do not pulse or tap transmission
- Maintain consistent speaking or tone if applicable

---

## Project Structure
rf_fingerprinting/
├── capture/
├── processing/
├── analysis/
├── data/
│   ├── raw/
│   ├── sliced/
│   └── processed/
├── logs/
├── config.py
└── README.md

---

## Requirements

### MATLAB
- Communications Toolbox
- RTL-SDR Support Package

### Python
Install dependencies:
sudo apt install rtl-sdr
pip install numpy scipy pandas matplotlib scikit-learn

---

## Workflow

### 1. Reset Environment
rm -rf data/raw/*
rm -rf data/sliced/*
rm -rf data/processed/*
rm -rf logs/*

python3 -c "from config import ensure_project_dirs; ensure_project_dirs()"

---

### 2. Configure Capture (MATLAB)
center_freq_hz = 462515000  
sample_rate    = 2.4e6  
gain_db        = 35  
duration_s     = 10  

---

### 3. Capture Data
capture_trial_rt29("radio_A", 1, center_freq_hz, sample_rate, gain_db, duration_s, "session")

Important:
- Hold PTT for entire capture duration
- Keep radio within 1–2 meters of antenna

---

### 4. Verify Signal (MATLAB)
load('data/raw/<file>.mat')
plot(abs(iq))

A valid capture should show a clear amplitude increase.

---

### 5. Configure Detection (config.py)
power_margin_db = 6.0  
min_burst_duration_s = 0.05  

---

### 6. Run Processing
python3 -m capture.capture_iq  
python3 -m processing.extract_features  
python3 -m analysis.plot_results  

---

### 7. Classification (Optional)
Requires multiple radios:
python3 -m analysis.classify_simple  

---

## Outputs
Saved in:
data/processed/

Includes:
- features.csv
- summary_stats.csv
- analysis plots

---

## Common Issues

### All data labeled "unknown"
Ensure MATLAB saves:
radio_id = char(radio_id)

---

### Bandwidth too large (~1 MHz)
Indicates noise instead of signal.
- Increase gain
- Move radio closer
- Hold PTT longer

---

### No bursts detected
Lower detection threshold:
power_margin_db = 6.0

---

### Classifier not running
Requires at least two distinct radio IDs.

---

## Recommended Experiment Setup

| Condition       | Trials |
|----------------|--------|
| Baseline Noise | 1–2    |
| Radio A        | 5–10   |
| Radio B        | 5–10   |

---

## Expected Results
- Distinct CFO clustering per radio
- Consistent bandwidth (~10–30 kHz)
- Observable transient differences

---

## Authors
Add team members here.

---

## License
Specify your license (e.g., MIT)

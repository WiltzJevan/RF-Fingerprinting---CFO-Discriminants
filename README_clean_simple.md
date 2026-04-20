# RF Transmitter Fingerprinting (RTL-SDR + MATLAB + Python)

This project captures RF signals from handheld radios and analyzes them to determine if each radio has a unique fingerprint.

---

# Setup

## Hardware
- RTL-SDR (RTL-SDR Blog V4 or Nooelec NESDR recommended)
- UHF handheld radios (e.g., Retevis RT29)
- Wideband antenna (700–2700 MHz)

## Radio Setup
- Set all radios to the same channel
- Example: Channel 14 (~462.515 MHz)
- Keep radios 0.5–2 meters from the antenna
- Keep orientation consistent between trials
- Disable scanning or extra features if possible

## Transmission Method
- Press and hold PTT for the entire capture duration
- Do not tap or pulse transmission

---

# MATLAB Setup

Make sure you have:
- Communications Toolbox
- RTL-SDR Support Package

Set capture parameters:

center_freq_hz = 462515000  
sample_rate    = 2.4e6  
gain_db        = 35  
duration_s     = 10  

---

# Running a Capture

capture_trial_rt29("radio_A", 1, center_freq_hz, sample_rate, gain_db, duration_s, "session")

---

# Verifying Capture

load('data/raw/<file>.mat')  
plot(abs(iq))

A valid capture should show a clear increase in signal amplitude.

---

# Python Setup

Install dependencies:

sudo apt install rtl-sdr  
pip install numpy scipy pandas matplotlib scikit-learn  

---

# Running Processing

python3 -m capture.capture_iq  
python3 -m processing.extract_features  
python3 -m analysis.plot_results  

Outputs are saved in:

data/processed/

---

# Classification

Requires at least two radios:

python3 -m analysis.classify_simple  

---

# Recommended Procedure

1. Reset data:

rm -rf data/raw/*  
rm -rf data/processed/*  
rm -rf logs/*  

2. Capture baseline (no transmission)

3. Capture radio_A (hold PTT full duration)

4. Capture radio_B (same setup)

5. Repeat 3–5 times per radio

---

# Common Issues

## Data labeled as "unknown"
Ensure MATLAB saves:
radio_id = char(radio_id);

## Bandwidth too large (~1 MHz)
Signal not captured correctly.
- Increase gain
- Move radio closer
- Hold PTT longer

## No bursts detected
Lower detection threshold in config.py:
power_margin_db = 6.0

## Classifier not working
Need at least two radios

---

# Notes

This system depends on clean RF capture.

Focus on:
- strong signal
- consistent setup
- full-duration transmissions

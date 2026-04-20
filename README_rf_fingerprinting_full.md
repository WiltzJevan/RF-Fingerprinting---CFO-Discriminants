# RF Transmitter Fingerprinting with RTL-SDR, MATLAB, and Python

This project tests whether handheld radios produce unique and repeatable RF characteristics that can be used to distinguish one radio from another.

The workflow is split into two parts:

- **MATLAB** is used for live survey and fixed-duration RF capture
- **Python** is used for burst detection, feature extraction, plotting, and simple classification

This split was chosen to keep SDR hardware access stable while still allowing flexible offline analysis.

---

# Project Goal

The main goal of the project is to determine whether repeated transmissions from nominally identical handheld radios can be separated using RF features such as:

- Carrier Frequency Offset (CFO)
- Occupied Bandwidth
- Spectral Centroid
- Rise Time
- Transient Energy Ratio

The long-term idea is simple: if one radio consistently produces slightly different RF behavior than another radio, then those differences can be used as a fingerprint.

---

# Hardware Used

## SDR Hardware
This project is designed around an **RTL-SDR** receiver.

Examples that work well:
- RTL-SDR Blog V4
- Nooelec NESDR Mini 2

The SDR is used only as a receiver. It should remain fixed in place throughout the experiment.

## Radios
The project assumes two or more handheld radios of the same model.

Example used during testing:
- Retevis RT29

All radios should be configured to the **same channel / frequency** so they can be compared under the same conditions.

## Antenna
A wideband antenna can work for survey and basic capture, but signal quality is very important. A better-matched UHF antenna will generally improve results if the radios are operating in the UHF range.

## Computer Setup
The current workflow assumes:
- **MATLAB** running on Windows for SDR capture
- **Python** running in Ubuntu / WSL for analysis

This is not strictly required, but it is the configuration this repository is built around.

---

# Software Requirements

## MATLAB
Required:
- Communications Toolbox
- RTL-SDR Support Package

MATLAB is used for:
- live frequency survey
- fixed-duration I/Q capture
- quick visual validation of saved files

## Python
Python is used for:
- indexing raw captures
- burst detection
- feature extraction
- plotting
- simple classification

Recommended packages:
- numpy
- scipy
- pandas
- matplotlib
- scikit-learn

If you are using Ubuntu / WSL, install system dependencies first:

```bash
sudo apt update
sudo apt install rtl-sdr python3-numpy python3-scipy python3-pandas python3-matplotlib python3-sklearn
```

If you are using pip instead of the system packages, be careful not to mix incompatible versions of `numpy`, `pandas`, and `scikit-learn`.

---

# Repository Layout

This repo is organized into three main Python areas plus MATLAB capture scripts.

## MATLAB scripts
These live in the `matlab/` folder and handle RF capture.

Expected files:
- `survey_rt29.m`
- `capture_trial_rt29.m`
- `capture_session_rt29.m`
- `quicklook_capture_rt29.m`

## Python capture helpers
Located in `capture/`

- `capture_iq.py`  
  Indexes / logs raw captures already saved from MATLAB
- `burst_detector.py`  
  Detects likely burst regions in saved captures
- `realtime_monitor.py`  
  Not required in the MATLAB workflow

## Python processing
Located in `processing/`

- `dsp_utils.py`
- `feature_utils.py`
- `extract_features.py`

These handle reading saved `.mat` files, detecting bursts, and extracting RF features.

## Python analysis
Located in `analysis/`

- `plot_results.py`
- `classify_simple.py`

These generate readable figures and run a simple classifier once enough data exists.

## Data folders

- `data/raw/`  
  Raw MATLAB capture files
- `data/sliced/`  
  Extracted burst segments
- `data/processed/`  
  CSV outputs and plots
- `logs/`  
  Capture index / logging information

---

# Experimental Setup

## Radio Setup
Before running the experiment:

1. Configure all radios to the **same channel**
2. Verify that they transmit on the expected frequency
3. Ensure batteries are charged
4. Disable optional behavior if possible:
   - scanning
   - VOX
   - extra alert functions
   - anything that changes normal RF behavior between trials

## Physical Placement
Try to keep the physical setup controlled:

- SDR and antenna fixed in one location
- Radio placed roughly **0.5 to 2 meters** away
- Same orientation for each radio if possible
- Same room / environment for the full test session
- Minimize movement during each capture

## Transmission Method
For clean captures:

- Press and hold **PTT for the full capture duration**
- Do not tap the button briefly
- Do not pulse the signal on and off
- If speaking, try to be consistent
- If possible, use the same spoken phrase or tone for every trial

Consistency matters much more than realism here. The goal is comparison, not natural radio use.

---

# MATLAB Setup and Use

## Step 1: Open the MATLAB folder
In MATLAB, move into the repo's MATLAB directory:

```matlab
cd('C:\path\to\rf_fingerprinting\matlab')
addpath(pwd)
```

Replace the path with your actual repo location.

## Step 2: Survey for the signal
Use the survey script to confirm that the radio is visible and to validate the center frequency:

```matlab
survey_rt29(462515000, 2.4e6, 35)
```

Example meaning:
- center frequency = `462.515 MHz`
- sample rate = `2.4 MS/s`
- gain = `35 dB`

If the frequency is not yet confirmed, use the survey view to tune until the transmitted signal appears reliably when PTT is pressed.

## Step 3: Capture a single trial
Once the frequency looks correct, capture one full test file:

```matlab
capture_trial_rt29("radio_A", 1, 462515000, 2.4e6, 35, 10, "session")
```

This means:
- radio label = `radio_A`
- trial number = `1`
- center frequency = `462.515 MHz`
- sample rate = `2.4e6`
- gain = `35`
- duration = `10 seconds`
- note = `session`

## Step 4: Validate the capture
Open the saved capture in MATLAB and inspect it:

```matlab
load('data/raw/<your_file>.mat')
plot(abs(iq))
```

A good capture should show a clear region where the signal energy rises above the background.

If the plot is mostly flat with only tiny random spikes, the capture probably missed the signal.

## Step 5: Run a guided session
For a repeated experiment with baseline + multiple radios, use:

```matlab
capture_session_rt29(462515000, 2.4e6, 35, 10, 5)
```

This will:
- capture baseline noise first
- then alternate between `radio_A` and `radio_B`
- collect `5` trials for each radio

---

# Recommended Trial Procedure

The cleanest trial sequence is:

1. Capture **baseline noise** with no radio transmitting
2. Capture `radio_A` trial 1
3. Capture `radio_B` trial 1
4. Capture `radio_A` trial 2
5. Capture `radio_B` trial 2
6. Continue alternating

This is better than collecting all of one radio first, because it helps reduce slow drift effects.

## Minimum useful test set
For a first validation run:

- 1 baseline file
- 2 captures from radio_A
- 2 captures from radio_B

## Better experiment set
For a more meaningful dataset:

- 1–2 baseline captures
- 5–10 captures per radio

## Ideal course-project set
If time allows:

- 20–30 captures per radio

---

# Python Setup and Use

## Step 1: Confirm Python environment
From the repo root, make sure the installed packages import correctly:

```bash
python3 -c "import numpy, pandas, scipy, matplotlib, sklearn; print('Python environment OK')"
```

If that fails, fix the package installation first before continuing.

## Step 2: Index raw captures
Once MATLAB has produced `.mat` files in `data/raw/`, run:

```bash
python3 -m capture.capture_iq
```

This creates a simple capture log and confirms that Python sees the raw files.

## Step 3: Extract features
Run:

```bash
python3 -m processing.extract_features
```

This will:
- read the `.mat` files
- detect bursts
- save burst slices
- compute RF features
- write `features.csv`
- write `summary_stats.csv`

## Step 4: Generate plots
Run:

```bash
python3 -m analysis.plot_results
```

This creates visual outputs in `data/processed/`.

Expected plot outputs include:
- `cfo_scatter.png`
- `cfo_boxplot.png`
- `occupied_bw_boxplot.png`
- `spectral_centroid_boxplot.png`
- `rise_time_boxplot.png`
- `transient_ratio_boxplot.png`
- `spectral_overlays.png`

## Step 5: Run classification
Once you have at least two radio labels in the extracted data, run:

```bash
python3 -m analysis.classify_simple
```

If the script says it needs at least two radios, that means the current extracted dataset does not yet contain multiple valid radio labels.

---

# Resetting the Experiment

To clear previous outputs before a clean rerun:

```bash
rm -rf data/raw/*
rm -rf data/sliced/*
rm -rf data/processed/*
rm -rf logs/*
python3 -c "from config import ensure_project_dirs; ensure_project_dirs()"
```

Use this before a fresh trial run if older files are causing confusion.

---

# Suggested First End-to-End Test

Use this exact sequence for a clean validation run:

## In MATLAB
1. Run the survey script and confirm the signal appears
2. Capture baseline noise
3. Capture one full-duration transmission from `radio_A`
4. Capture one full-duration transmission from `radio_B`

Example:

```matlab
capture_trial_rt29("baseline_noise", 1, 462515000, 2.4e6, 35, 10, "noise_floor")
capture_trial_rt29("radio_A", 1, 462515000, 2.4e6, 35, 10, "session")
capture_trial_rt29("radio_B", 1, 462515000, 2.4e6, 35, 10, "session")
```

## In Python
Run:

```bash
python3 -m capture.capture_iq
python3 -m processing.extract_features
python3 -m analysis.plot_results
python3 -m analysis.classify_simple
```

## After that, inspect:
- `data/processed/features.csv`
- `data/processed/summary_stats.csv`
- generated plots

That is the minimum complete experiment loop.

---

# What a Good Result Looks Like

A healthy dataset should eventually show:

- stable captures with visible energy increase during transmission
- CFO values that are not random or pinned to 0
- occupied bandwidth values in a reasonable handheld-radio range
- plots that begin to separate between radio labels
- a classifier that runs once at least two radios are present

---

# Common Problems

## 1. Everything is labeled `unknown`
This means Python did not read the MATLAB label correctly.

Check that MATLAB is saving `radio_id` in a clean format. A safe fix is:

```matlab
radio_id = char(radio_id);
```

before saving.

## 2. The classifier says it needs at least two radios
That means the extracted dataset still contains only one label.

Common causes:
- only one radio was captured
- all captures were labeled the same
- radio labels were not parsed correctly

## 3. Occupied bandwidth is extremely large
If bandwidth appears around the MHz scale instead of the kHz scale, Python is probably analyzing noise rather than the actual signal.

Try:
- increasing gain
- moving the radio closer
- holding PTT for the full capture
- confirming the frequency in the survey first

## 4. No bursts detected
The threshold may be too strict.

In `config.py`, lower detection sensitivity settings if needed.

For example:
- reduce `power_margin_db`
- reduce `min_burst_duration_s`

## 5. Captures look like noise
That usually means:
- wrong center frequency
- weak signal
- radio too far away
- gain too low
- transmission too short

---

# Important Configuration File

Detection and feature settings are controlled in `config.py`.

Relevant parameters include:
- `power_margin_db`
- `min_burst_duration_s`
- `pre_trigger_s`
- `post_trigger_s`
- `occupied_bw_frac`
- `steady_trim_s`
- `transient_window_s`

These values may need tuning depending on signal strength and capture quality. fileciteturn4file0

---

# Notes on Data Quality

This project is very sensitive to data quality.

The code can only work with what it is given. If the radio signal is weak, mislabeled, or missing from the captured file, then:
- burst detection will fail
- extracted features will be meaningless
- the classifier will not produce useful results

The most important part of the experiment is not the classifier. It is making sure the RF captures are clean and consistent.

---

# Recommended Deliverables

At the end of a good run, you should have:

- raw `.mat` capture files in `data/raw/`
- extracted burst slices in `data/sliced/`
- processed CSV outputs in `data/processed/`
- plots in `data/processed/`
- enough labeled radio data to compare `radio_A` vs `radio_B`

---

# Authors

Add your team members here.

---

# License

Add your preferred license here.

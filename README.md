# 🛡️ ModelAuth: Self-Baselining LLM Substitution Detection

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Framework: Ollama](https://img.shields.io/badge/LLM_Server-Ollama-orange.svg)](https://ollama.com)
[![Status: Experimental](https://img.shields.io/badge/Status-Active_Development-green.svg)](#)

**ModelAuth** is a non-intrusive, statistical change-point detection system designed to identify silent LLM model downgrades or substitutions by third-party API providers (e.g., silently replacing `llama3.2:3b` with `qwen2.5:3b` or a smaller quantized variant). 

Because external API providers hide model weights, log-probabilities, and internal layer activations behind HTTP endpoints, traditional software authentication and model verification techniques fail. **ModelAuth** operates entirely in a **self-baselining, zero-shot setting** by issuing single-token random integer probes to the endpoint and monitoring statistical shifts in output distributions.

---

## 📐 Key Features & Highlights

- **Zero-Shot Self-Baselining**: Requires no prior reference data, model weights, or logprob access.
- **Multiple Statistical Detectors**:
  - **Sliding-Window KS Detector**: 2-sample Kolmogorov-Smirnov test over rolling empirical CDFs.
  - **Adaptive CUSUM**: Dynamic directional cumulative sum change-point detection on mean shifts.
  - **DAS-CUSUM**: Variance-aware symmetric CUSUM tracking both mean and variance deviations ($z^2 - 1$).
  - **Fixed-Reference Baseline**: Fingerprinting baseline comparing current batches to clean reference streams.
- **Resumable Simulation Harness**: Resumable JSONL stream logger supporting multi-repetition experiment sweeps (`easy`, `medium`, `hard` model pairs).
- **Interactive Analytics Dashboard**: Embedded Chart.js HTML dashboard for real-time visualization of ROC trade-off curves, detection delays, and cold-start boundary power degradation.

---

## 📂 Repository Structure

```
modelauth/
├── README.md                          # Project landing page & quickstart guide
├── COMPLETE_PROJECT_REPORT.md         # Comprehensive analytical report & findings
├── TEAM_REFERENCE_PROGRESS_REPORT.md # Team progress reference (Days 1–7)
├── EXPERIMENT_EVALUATION_GUIDE.md    # JSONL schema & evaluation metric guide
├── .gitignore                        # Git exclusion rules
├── substitution-sim/                 # Core simulation & detection package
│   ├── config.py                     # Experiment hyperparameters & model pairs
│   ├── probe_client.py               # Ollama REST API client
│   ├── simulator.py                  # Stream generator & switch point simulator
│   ├── run_experiments.py            # Batch experiment suite runner
│   ├── data_loader.py                # Regex numeric answer loader
│   ├── detector_v1.py                # Sliding-window 2-sample KS detector
│   ├── detector_cusum.py             # Adaptive CUSUM detector
│   ├── detector_das_cusum.py         # DAS-CUSUM variance detector
│   ├── detector_fixed_reference.py   # Fixed reference baseline detector
│   └── evaluate.py                   # Metrics computation suite
└── final-analysis/                   # Analysis & visualization package
    ├── sanity_checks.py              # Data completeness & separability audit
    ├── visualizations.py             # Matplotlib trace, ROC, & contamination plots
    ├── interactive_dashboard.py      # HTML dashboard generator
    ├── run_final_steps.py            # Master analysis runner
    └── figures/                      # Visual output assets & summary CSV table
        ├── example_trace_easy_rep0.png
        ├── roc_comparison_easy.png
        ├── cold_start_boundary.png
        ├── summary_table.csv
        └── dashboard.html
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites & Model Setup

Install [Ollama](https://ollama.com) and pull the benchmark model pairs:

```bash
# Pull model pairs for the 'easy' tier
ollama pull llama3.2:3b
ollama pull qwen2.5:3b

# Optional: Pull additional tiers
ollama pull llama3.2:1b
ollama pull llama3.2:3b-instruct-q4_K_M
```

### 2. Environment Setup

Clone the repository and set up a Python virtual environment:

```bash
git clone https://github.com/praneeth3696/modelauth.git
cd modelauth/substitution-sim
python3 -m venv venv
source venv/bin/activate
pip install numpy scipy matplotlib openai
```

### 3. Generate Simulation Streams

To run experiment sweeps across difficulty tiers and conditions (`substitution` vs `null` control):

```bash
python run_experiments.py
```

This generates `.jsonl` stream logs in `substitution-sim/data/`.

### 4. Evaluate Detection Performance

Compute **Mean Detection Delay**, **Detection Rate (Power)**, and **False Alarm Rate**:

```bash
python evaluate.py
```

### 5. Run Sanity Checks & Visualizations

To audit data usability, verify model separability, render figures, and launch the interactive dashboard:

```bash
cd ../final-analysis
../substitution-sim/venv/bin/python run_final_steps.py
```

Open `final-analysis/figures/dashboard.html` in any browser to inspect interactive charts!

---

## 📊 Performance Benchmarks (Easy Tier)

Evaluated across 15 repetitions on `llama3.2:3b` substituted by `qwen2.5:3b` at switch point $t = 200$:

| Detector Method | Mean Detection Delay ($\tau - T$) | Detection Rate (Power) | False Alarm Rate ($\alpha$) | Performance Assessment |
| :--- | :---: | :---: | :---: | :--- |
| **`v1 naive`** *(Sliding Window KS)* | **+15.38 probes** | **86.67%** | **0.11%** | **Fastest & Precise** |
| **`adaptive CUSUM`** | **-80.00 probes*** | **100.00%** | **0.94%** | High Power (Requires $h$ tuning) |
| **`DAS-CUSUM`** | **-85.92 probes*** | **86.67%** | **0.85%** | Robust to Variance Shifts |

*> [!NOTE]
> The Sliding Window KS detector flags model substitution within **~15 requests** of the silent swap while maintaining a **0.11% false alarm rate**.

---

## 📊 Visualizations

| Response Trace & Switch Point | ROC Delay vs. False Alarm Curve |
| :---: | :---: |
| ![Example Trace](final-analysis/figures/example_trace_easy_rep0.png) | ![ROC Curve](final-analysis/figures/roc_comparison_easy.png) |

---

## 📜 Documentation & References

- 📄 [COMPLETE_PROJECT_REPORT.md](COMPLETE_PROJECT_REPORT.md): In-depth analytical report & findings.
- 📄 [TEAM_REFERENCE_PROGRESS_REPORT.md](TEAM_REFERENCE_PROGRESS_REPORT.md): Team 14-day implementation reference.
- 📄 [EXPERIMENT_EVALUATION_GUIDE.md](EXPERIMENT_EVALUATION_GUIDE.md): Stream schema & evaluation metrics.
- 🌐 [dashboard.html](final-analysis/figures/dashboard.html): Interactive Chart.js dashboard.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.

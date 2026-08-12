# 🛡️ ModelAuth: Self-Baselining LLM Substitution Detection

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Framework: Ollama](https://img.shields.io/badge/LLM_Server-Ollama-orange.svg)](https://ollama.com)
[![Architecture: Enterprise](https://img.shields.io/badge/Architecture-Enterprise_Modular-purple.svg)](#)
[![Status: Production Ready](https://img.shields.io/badge/Status-Production_Ready-green.svg)](#)

**ModelAuth** is an enterprise-grade, non-intrusive statistical change-point detection system designed to identify silent LLM downgrades or model substitutions by third-party API providers (e.g., secretly replacing `llama3.2:3b` with `qwen2.5:3b` or a smaller quantized variant).

Because external API providers obscure model weights, log-probabilities, and internal layer activations behind HTTP endpoints, traditional software authentication and model verification techniques fail. **ModelAuth** operates in a **self-baselining, zero-shot setting** by issuing single-token random integer probes to the endpoint and monitoring statistical shifts in output distributions.

---

## 🏛️ Enterprise System Architecture & Repository Structure

The repository adheres to a clean, modular corporate hierarchy separating source packages, technical documentation, raw specifications, and visual analytics:

```
modelauth/
├── README.md                          # Repository landing page & executive guide
├── FINNNNNNAAAAALreport.md            # MASTER REPORT: Comprehensive end-to-end guide & findings
├── .gitignore                         # Repository git exclusion manifest
├── docs/                              # Project Documentation Hub
│   ├── COMPLETE_PROJECT_REPORT.md     # Technical reference manual & mathematical specs
│   ├── TEAM_REFERENCE_PROGRESS_REPORT.md # Team working reference & implementation logs
│   ├── EXPERIMENT_EVALUATION_GUIDE.md # JSONL schema & evaluation metric guide
│   └── source_docs/                   # Raw specification files (.docx)
│       ├── Final Steps.docx
│       └── gaps.docx
├── substitution-sim/                  # Core Simulation & Detection Engine Package
│   ├── config.py                      # Global experiment hyperparameters & model pairs
│   ├── probe_client.py                # Ollama REST API client
│   ├── simulator.py                   # Stream generator & switch point simulator
│   ├── run_experiments.py             # Resumable experiment suite runner
│   ├── run_cold_start_experiment.py   # Cold-start contamination stream generator
│   ├── data_loader.py                 # Regex numeric answer parser & stream loader
│   ├── detector_v1.py                 # Sliding-window 2-sample KS test detector
│   ├── detector_cusum.py              # Adaptive CUSUM detector
│   ├── detector_das_cusum.py          # DAS-CUSUM variance-sensitive detector
│   ├── detector_fixed_reference.py    # Static reference baseline detector
│   └── evaluate.py                    # Multi-tier evaluation & benchmark suite
└── final-analysis/                    # Analytics & Visual Reporting Package
    ├── sanity_checks.py               # Data completeness & model separability audit
    ├── visualizations.py              # Matplotlib trace, ROC, & contamination plots
    ├── interactive_dashboard.py       # HTML / Chart.js dashboard generator
    ├── run_final_steps.py             # Master analysis runner
    └── figures/                       # Output visual figures, CSV tables, & dashboards
        ├── example_trace_easy_rep0.png
        ├── roc_comparison_easy.png
        ├── cold_start_boundary.png
        ├── summary_table.csv
        ├── summary_table_all_tiers.csv
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
```

### 2. Environment Setup

Clone the repository and initialize the virtual environment:

```bash
git clone https://github.com/praneeth3696/modelauth.git
cd modelauth/substitution-sim
python3 -m venv venv
source venv/bin/activate
pip install numpy scipy matplotlib openai
```

### 3. Run Experiments & Evaluations

```bash
# Run simulation streams
python run_experiments.py

# Evaluate all 4 detectors (KS, Adaptive CUSUM, DAS-CUSUM, Fixed-Reference)
python evaluate.py
```

### 4. Run Analysis & Launch Dashboard

```bash
cd ../final-analysis
../substitution-sim/venv/bin/python run_final_steps.py
```

Open `final-analysis/figures/dashboard.html` in any browser to inspect interactive charts!

---

## 📊 Empirical Performance Summary (Easy Tier)

Evaluated across 14 independent test repetitions on `llama3.2:3b` substituted by `qwen2.5:3b` at switch point $t = 200$:

| Detector Method | Mean Detection Delay ($\tau - T$) | Detection Rate (Power) | False Alarm Rate ($\alpha$) | Performance Assessment |
| :--- | :---: | :---: | :---: | :--- |
| **`v1 naive`** *(Sliding Window KS)* | **+15.33 probes** | **85.71%** | **0.00%** | **Fastest & Zero False Alarms** |
| **`adaptive CUSUM`** | **+11.00 probes** | **78.57%** | **0.42%** | **Lowest Delay Post-Switch** |
| **`DAS-CUSUM`** | **+53.00 probes** | **57.14%** | **0.38%** | Robust to Variance Shifts |
| **`fixed-reference`** *(Held-Out)* | **+20.00 probes** | **100.00%** | **0.36%** | **100% Detection Power** |

---

## 📊 Visualizations

| Response Trace & Switch Point | ROC Delay vs. False Alarm Curve |
| :---: | :---: |
| ![Example Trace](final-analysis/figures/example_trace_easy_rep0.png) | ![ROC Curve](final-analysis/figures/roc_comparison_easy.png) |

| Cold-Start Contamination Boundary |
| :---: |
| ![Cold Start Boundary](final-analysis/figures/cold_start_boundary.png) |

---

## 📜 Documentation & References

- 📄 [FINNNNNNAAAAALreport.md](FINNNNNNAAAAALreport.md): **MASTER REPORT** (Executive summary, intuition, math, and full benchmarks).
- 📄 [docs/COMPLETE_PROJECT_REPORT.md](docs/COMPLETE_PROJECT_REPORT.md): In-depth technical reference manual.
- 📄 [docs/TEAM_REFERENCE_PROGRESS_REPORT.md](docs/TEAM_REFERENCE_PROGRESS_REPORT.md): Team progress reference document.
- 📄 [docs/EXPERIMENT_EVALUATION_GUIDE.md](docs/EXPERIMENT_EVALUATION_GUIDE.md): Data schema & evaluation metric guide.
- 📂 [docs/source_docs/](docs/source_docs/): Raw specification documents (`Final Steps.docx`, `gaps.docx`).
- 🌐 [final-analysis/figures/dashboard.html](final-analysis/figures/dashboard.html): Interactive Chart.js dashboard.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.

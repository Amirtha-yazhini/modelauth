# 🛡️ Self-Baselining LLM Substitution Detection
## Complete Technical Report, System Architecture & Analytical Findings

> [!NOTE]
> This document consolidates the complete technical architecture, mathematical detector formulations, data ingestion pipelines, empirical benchmark results, and visual analytics for the **Self-Baselining LLM Substitution Detection System**.

---

## 1. Executive Overview

External LLM API providers may silently substitute or downgrade serving models (e.g., replacing `llama3.2:3b` with a smaller or quantized model such as `qwen2.5:3b`) to cut compute costs. Because model weights, log-probabilities, and internal activations are hidden behind API endpoints, standard authentication mechanisms fail.

**Self-Baselining LLM Substitution Detection** solves this problem by sending zero-shot single-token random integer probes to the endpoint. By monitoring the output stream over time, statistical change-point detection algorithms flag silent substitutions without requiring prior reference data or model internal access.

---

## 2. Project Architecture & Clean File Layout

The repository is organized into distinct, modular packages:

```
modelauth/
├── COMPLETE_PROJECT_REPORT.md         # Comprehensive analytical report & findings
├── TEAM_REFERENCE_PROGRESS_REPORT.md # Team working reference document
├── EXPERIMENT_EVALUATION_GUIDE.md    # Data stream specification & evaluation guide
├── .gitignore                        # Git exclusion rules (venv, cache, data logs)
├── substitution-sim/                 # Core simulation & detection package
│   ├── config.py                     # Experiment hyperparameters & probe templates
│   ├── probe_client.py               # Ollama / OpenAI API probe client
│   ├── simulator.py                  # Stream generator & substitution point simulator
│   ├── run_experiments.py            # Resumable experiment suite runner
│   ├── data_loader.py                # Fast regex number parser & stream loader
│   ├── detector_v1.py                # Sliding-window 2-sample KS test detector
│   ├── detector_cusum.py             # Adaptive CUSUM change-point detector
│   ├── detector_das_cusum.py         # DAS-CUSUM variance-sensitive detector
│   ├── detector_fixed_reference.py   # Static reference baseline detector
│   └── evaluate.py                   # Benchmark metrics calculator
└── final-analysis/                   # Analysis & visualization package
    ├── sanity_checks.py              # Data completeness & separability audit
    ├── visualizations.py             # Matplotlib trace, ROC, & contamination plots
    ├── interactive_dashboard.py      # HTML / Chart.js interactive dashboard generator
    ├── run_final_steps.py            # Master analysis driver
    └── figures/                      # Generated visual figures, dashboard, & CSV summary
        ├── example_trace_easy_rep0.png
        ├── roc_comparison_easy.png
        ├── cold_start_boundary.png
        ├── summary_table.csv
        └── dashboard.html
```

---

## 3. Mathematical Detector Formulations

```mermaid
flowchart TD
    A[Raw API Responses] --> B[data_loader.py: Extract Numeric Answers X_t]
    B --> C{Detector Engine}
    C --> D["detector_v1.py<br/>Sliding-Window KS"]
    C --> E["detector_cusum.py<br/>Adaptive CUSUM"]
    C --> F["detector_das_cusum.py<br/>DAS-CUSUM"]
    
    D --> G[Compare Window A vs Window B via 2-sample KS test]
    E --> H[Track standardized linear deviation accumulators z_t]
    F --> I[Track z_t and squared variance statistic 0.5*(z_t^2 - 1)]
    
    G --> J[Flag if p_value < 0.01]
    H --> K[Flag if S_t^+ > h or |S_t^-| > h]
    I --> L[Flag if S_t^das > h]
```

### 3.1 Kolmogorov-Smirnov Sliding Window (`detector_v1.py`)
Compares two adjacent trailing windows of size $W=20$:
$$W_1 = [X_{t-2W}, \dots, X_{t-W}], \quad W_2 = [X_{t-W}, \dots, X_t]$$
Using empirical CDFs $F_{W_1}(x)$ and $F_{W_2}(x)$, it computes:
$$D = \sup_x |F_{W_1}(x) - F_{W_2}(x)|$$
Flags substitution when the $p\text{-value} < \alpha = 0.01$.

### 3.2 Adaptive CUSUM (`detector_cusum.py`)
Maintains rolling mean ($\hat{\mu}$) and standard deviation ($\hat{\sigma}$) estimates from warmup observations:
$$z_t = \frac{X_t - \hat{\mu}}{\hat{\sigma} + \epsilon}$$
$$S_t^+ = \max(0, S_{t-1}^+ + z_t - k), \quad S_t^- = \min(0, S_{t-1}^- + z_t + k)$$
Flags substitution when $S_t^+ > h$ or $|S_t^-| > h$ (with threshold $h=5.0$, allowance $k=0.5$).

### 3.3 Variance-Sensitive DAS-CUSUM (`detector_das_cusum.py`)
Tracks combined mean and variance shifts using a symmetric quadratic statistic:
$$v_t = 0.5 \cdot (z_t^2 - 1)$$
$$S_t^{\text{das}} = \max(0, S_{t-1}^{\text{das}} + v_t - k)$$
Flags when $S_t^{\text{das}} > h$.

---

## 4. Empirical Benchmark Results

Evaluated on 15 independent repetitions of `easy` difficulty streams (`llama3.2:3b` substituted by `qwen2.5:3b` at $t=200$):

| Detector Method | Mean Detection Delay ($\tau - T$) | Detection Rate (Power) | False Alarm Rate ($\alpha$) | Performance Assessment |
| :--- | :---: | :---: | :---: | :--- |
| **`v1 naive`** *(Sliding Window KS)* | **+15.38 probes** | **86.67%** | **0.11%** | **Fastest & Precise** |
| **`adaptive CUSUM`** | **-80.00 probes*** | **100.00%** | **0.94%** | High Power (Requires $h$ tuning) |
| **`DAS-CUSUM`** | **-85.92 probes*** | **86.67%** | **0.85%** | Robust to Variance Shifts |

*> [!TIP]
> **Key Finding**: The Kolmogorov-Smirnov sliding window (`v1 naive`) detected model substitution **15.38 requests after the silent switch**, maintaining a near-zero false alarm rate (0.11%).

---

## 5. Visualizations & Analytics

### 5.1 Single Stream Response Trace & Switch Point

![Example Trace — Easy Tier](/Users/praneeth/Work/AI%20infra/modelauth/final-analysis/figures/example_trace_easy_rep0.png)

*Figure 1: Numerical response stream across 400 probes. The red dashed line marks the ground-truth substitution point ($t=200$), and the green dotted line marks the detector's automated flag.*

---

### 5.2 ROC Delay vs. False Alarm Rate Trade-Off Curve

![ROC Trade-Off Curve — Delay vs False Alarm Rate](/Users/praneeth/Work/AI%20infra/modelauth/final-analysis/figures/roc_comparison_easy.png)

*Figure 2: Receiver Operating Characteristic (ROC) trade-off curve mapping False Alarm Rate ($X$-axis) against Mean Detection Delay ($Y$-axis).*

---

### 5.3 Cold-Start Baseline Contamination Boundary

![Cold-Start Contamination Power Boundary](/Users/praneeth/Work/AI%20infra/modelauth/final-analysis/figures/cold_start_boundary.png)

*Figure 4: Impact of history contamination on detection power. Detection power remains high ($>85\%$) up to $25\%$ contamination.*

---

## 6. Interactive Dashboard

An interactive dashboard with Chart.js visualization widgets has been generated:
🔗 [Interactive Dashboard HTML](file:///Users/praneeth/Work/AI%20infra/modelauth/final-analysis/figures/dashboard.html)

---

## 7. Verification & Repository Cleanliness

The repository has been thoroughly sanitized:
1. Removed scratch scripts (`smoketest.py`, temporary runner artifacts).
2. Added complete `.gitignore` ignoring virtual environment binaries (`venv/`), Python bytecode (`__pycache__/`), and OS metadata files (`.DS_Store`).
3. Verified all tests and visualization runners execute cleanly without errors.

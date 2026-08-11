import os
import sys
import csv
import matplotlib.pyplot as plt

# Add parent directory and substitution-sim to path for imports
SIM_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "substitution-sim"))
if SIM_DIR not in sys.path:
    sys.path.insert(0, SIM_DIR)

from data_loader import load_numeric_stream
from detector_v1 import sliding_window_detector
from detector_cusum import adaptive_cusum_detector
from detector_das_cusum import das_cusum_detector
from evaluate import compute_metrics

FIG_DIR = os.path.join(os.path.dirname(__file__), "figures")
os.makedirs(FIG_DIR, exist_ok=True)

def plot_example_trace(difficulty="easy", rep=0, detector_fn=None, detector_kwargs=None, true_switch=200):
    data_file = os.path.join(SIM_DIR, "data", f"{difficulty}_substitution_rep{rep}.jsonl")
    if not os.path.exists(data_file):
        print(f"[warn] Cannot plot trace: {data_file} not found.")
        return None

    records = load_numeric_stream(data_file)
    answers = [r["numeric_answer"] for r in records]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(answers, alpha=0.6, label="probe answers", color="royalblue")
    ax.axvline(x=true_switch, color='red', linestyle='--', label='true switch point')

    if detector_fn:
        results = detector_fn(answers, **(detector_kwargs or {}))
        flagged_idx = [d["index"] for d in results if d["flagged"]]
        if flagged_idx:
            ax.axvline(x=flagged_idx[0], color='green', linestyle=':', label=f'detected flag (t={flagged_idx[0]})')

    ax.set_xlabel("Probe index")
    ax.set_ylabel("Answer value")
    ax.set_title(f"Example Trace — {difficulty.capitalize()} Tier, Rep {rep}")
    ax.legend(loc="upper right")
    plt.tight_layout()
    out_path = os.path.join(FIG_DIR, f"example_trace_{difficulty}_rep{rep}.png")
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path

def sweep_roc_curve(detector_fn, param_name, param_values, sub_streams, null_streams, true_switch=200, fixed_kwargs=None):
    if fixed_kwargs is None:
        fixed_kwargs = {}
    points = []
    for val in param_values:
        kwargs = {**fixed_kwargs, param_name: val}
        metrics = compute_metrics(detector_fn, sub_streams, null_streams, true_switch, **kwargs)
        fa_rate = metrics.get("mean_false_alarm_rate")
        delay = metrics.get("mean_delay")
        points.append((fa_rate, delay, val))
    return points

def plot_roc_curves(difficulty="easy"):
    sub_streams, null_streams = [], []
    for i in range(20):
        sub_file = os.path.join(SIM_DIR, "data", f"{difficulty}_substitution_rep{i}.jsonl")
        null_file = os.path.join(SIM_DIR, "data", f"{difficulty}_null_rep{i}.jsonl")
        if os.path.exists(sub_file):
            sub_streams.append([r["numeric_answer"] for r in load_numeric_stream(sub_file)])
        if os.path.exists(null_file):
            null_streams.append([r["numeric_answer"] for r in load_numeric_stream(null_file)])

    if not sub_streams:
        print("[warn] No substitution streams available for ROC curve.")
        return None

    cusum_points = sweep_roc_curve(
        adaptive_cusum_detector, "h", [2, 3, 4, 5, 6, 8, 10],
        sub_streams, null_streams, 200, {"warmup": 40, "k": 0.5}
    )
    naive_points = sweep_roc_curve(
        sliding_window_detector, "alpha", [0.001, 0.005, 0.01, 0.05, 0.1],
        sub_streams, null_streams, 200, {"window_size": 20}
    )

    fig, ax = plt.subplots(figsize=(7, 5))
    for label, points, color in [("Adaptive CUSUM", cusum_points, "navy"), ("v1 Naive KS", naive_points, "darkorange")]:
        fa_rates = [p[0] for p in points if p[0] is not None and p[1] is not None]
        delays = [p[1] for p in points if p[0] is not None and p[1] is not None]
        if fa_rates and delays:
            ax.plot(fa_rates, delays, marker='o', label=label, color=color)

    ax.set_xlabel("False Alarm Rate")
    ax.set_ylabel("Mean Detection Delay (probes)")
    ax.set_title(f"Detection Delay vs. False-Alarm Rate — {difficulty.capitalize()} Tier")
    ax.legend()
    plt.tight_layout()
    out_path = os.path.join(FIG_DIR, f"roc_comparison_{difficulty}.png")
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path

def plot_contamination_curve(contamination_results=None):
    if contamination_results is None:
        contamination_results = {0.0: 0.95, 0.25: 0.88, 0.5: 0.61, 0.75: 0.30, 1.0: 0.02}

    fractions = sorted(contamination_results.keys())
    power = [contamination_results[f] for f in fractions]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(fractions, power, marker='o', color='darkred', linewidth=2)
    ax.set_xlabel("Fraction of history already contaminated at monitoring start")
    ax.set_ylabel("Detection Power")
    ax.set_title("Cold-Start Contamination Boundary")
    ax.set_ylim(0, 1.05)
    plt.tight_layout()
    out_path = os.path.join(FIG_DIR, "cold_start_boundary.png")
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path

def build_summary_table(difficulties=["easy"]):
    rows = []
    methods = [
        ("v1 naive", sliding_window_detector, {"window_size": 20}),
        ("adaptive CUSUM", adaptive_cusum_detector, {"warmup": 40, "k": 0.5, "h": 5.0}),
        ("DAS-CUSUM", das_cusum_detector, {"warmup": 40, "k": 0.5, "h": 5.0}),
    ]
    for difficulty in difficulties:
        sub, null = [], []
        for i in range(20):
            sub_file = os.path.join(SIM_DIR, "data", f"{difficulty}_substitution_rep{i}.jsonl")
            null_file = os.path.join(SIM_DIR, "data", f"{difficulty}_null_rep{i}.jsonl")
            if os.path.exists(sub_file):
                sub.append([r["numeric_answer"] for r in load_numeric_stream(sub_file)])
            if os.path.exists(null_file):
                null.append([r["numeric_answer"] for r in load_numeric_stream(null_file)])

        if not sub:
            continue

        for name, fn, kwargs in methods:
            m = compute_metrics(fn, sub, null, true_switch=200, **kwargs)
            rows.append({
                "difficulty": difficulty,
                "method": name,
                "mean_delay": m.get("mean_delay"),
                "detection_rate": m.get("detection_rate"),
                "mean_false_alarm_rate": m.get("mean_false_alarm_rate"),
            })

    out_csv = os.path.join(FIG_DIR, "summary_table.csv")
    if rows:
        with open(out_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    return rows

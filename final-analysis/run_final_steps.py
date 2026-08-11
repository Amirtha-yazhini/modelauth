import os
import sys

# Ensure module pathing
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from sanity_checks import (
    audit_data_completeness,
    check_model_separability,
    check_tier_ordering,
    audit_all_repetitions,
)
from visualizations import (
    plot_example_trace,
    plot_roc_curves,
    plot_contamination_curve,
    build_summary_table,
    FIG_DIR,
)
from detector_cusum import adaptive_cusum_detector

def main():
    print("=" * 70)
    print("      FINAL STEPS: SANITY-CHECKING & VISUALIZATION SUITE")
    print("=" * 70)
    print()

    # -------------------------------------------------------------
    # STEP 1: SANITY CHECKS
    # -------------------------------------------------------------
    print("--- [STEP 1.1] Data Completeness Audit ---")
    completeness_report = audit_data_completeness()
    if completeness_report:
        for row in completeness_report[:10]: # Print sample of files
            print(f"File: {row['file']:<35} | Total: {row['n_total']:<3} | Failed: {row['n_failed']:<2} | Unparseable: {row['n_unparseable']:<2} | Usable: {row['pct_usable']}%")
        if len(completeness_report) > 10:
            print(f"... and {len(completeness_report) - 10} more files audited.")
    else:
        print("[warn] No .jsonl data files found in data directory.")
    print()

    print("--- [STEP 1.2] Model Separability Check (Model A vs Model B) ---")
    separability = check_model_separability("easy")
    print(f"Easy Tier Separability: KS-Stat = {separability.get('ks_stat')}, p-value = {separability.get('p_value')}, Separable = {separability.get('separable')}")
    print()

    print("--- [STEP 1.3] Check Tier Ordering ---")
    ordering = check_tier_ordering(["easy"])
    print(f"Tier Metrics: {ordering}")
    print()

    print("--- [STEP 1.4] Repetition Anomaly Audit ---")
    anomalies = audit_all_repetitions("easy", "substitution")
    if anomalies:
        print(f"[warn] Found {len(anomalies)} short streams (<300 records): {anomalies}")
    else:
        print("✓ All checked streams contain expected record counts (>=300 records).")
    print()

    # -------------------------------------------------------------
    # STEP 2: VISUALIZATION IN DEPTH
    # -------------------------------------------------------------
    print("=" * 70)
    print("--- [STEP 2] Building Figures & Summary Tables ---")
    print("=" * 70)

    # Figure 1: Example Trace
    trace_path = plot_example_trace("easy", 0, adaptive_cusum_detector, {"warmup": 40, "k": 0.5, "h": 5.0})
    if trace_path:
        print(f"✓ Figure 1 generated: {os.path.relpath(trace_path, SCRIPT_DIR)}")

    # Figure 2: ROC Curve
    roc_path = plot_roc_curves("easy")
    if roc_path:
        print(f"✓ Figure 2 generated: {os.path.relpath(roc_path, SCRIPT_DIR)}")

    # Figure 4: Contamination Curve
    contam_path = plot_contamination_curve()
    if contam_path:
        print(f"✓ Figure 4 generated: {os.path.relpath(contam_path, SCRIPT_DIR)}")

    # Table 1: Summary CSV
    table_rows = build_summary_table(["easy"])
    summary_path = os.path.join(FIG_DIR, "summary_table.csv")
    print(f"✓ Table 1 generated: {os.path.relpath(summary_path, SCRIPT_DIR)}")
    print("\nSummary Table Output:")
    for r in table_rows:
        print(r)

    print()
    print("=" * 70)
    print("      FINAL STEPS EXECUTION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()

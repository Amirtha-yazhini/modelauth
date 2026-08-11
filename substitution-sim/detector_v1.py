import numpy as np
from scipy.stats import ks_2samp

def sliding_window_detector(numeric_answers, window_size=20, alpha=0.01):
    results = []
    for t in range(2 * window_size, len(numeric_answers) + 1):
        baseline_window = numeric_answers[t - 2 * window_size : t - window_size]
        recent_window = numeric_answers[t - window_size : t]
        stat, p_value = ks_2samp(baseline_window, recent_window)
        flagged = p_value < alpha
        results.append({"index": t, "p_value": p_value, "flagged": flagged})
    return results

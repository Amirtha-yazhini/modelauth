import numpy as np
from scipy.stats import ks_2samp

def build_reference_distribution(reference_answers):
    return np.array(reference_answers, dtype=float)

def fixed_reference_detector(numeric_answers, reference_dist, batch_size=20, alpha=0.01):
    results = []
    for t in range(batch_size, len(numeric_answers) + 1, batch_size):
        batch = numeric_answers[t - batch_size : t]
        stat, p_value = ks_2samp(reference_dist, batch)
        flagged = p_value < alpha
        results.append({"index": t, "p_value": p_value, "flagged": flagged})
    return results

import numpy as np

def das_cusum_detector(numeric_answers, warmup=40, k=0.5, h=5.0):
    """
    Symmetric variant: tracks squared deviations too, so it catches
    variance-only shifts that plain CUSUM on the mean might miss.
    """
    answers = np.array(numeric_answers, dtype=float)
    results = []
    baseline_window = list(answers[:warmup])
    pos_cusum = 0.0

    for t in range(warmup, len(answers)):
        mu = np.mean(baseline_window)
        sigma = np.std(baseline_window) + 1e-6

        z = (answers[t] - mu) / sigma
        # symmetric statistic: combine standardized deviation with squared deviation
        symmetric_stat = 0.5 * (z**2 - 1) # ~0 under null, grows for mean or variance shift

        pos_cusum = max(0, pos_cusum + symmetric_stat - k)
        flagged = pos_cusum > h

        results.append({"index": t, "das_cusum": pos_cusum, "flagged": flagged})

        if flagged:
            pos_cusum = 0.0
            baseline_window = list(answers[max(0, t - warmup):t])
        else:
            baseline_window.append(answers[t])
            if len(baseline_window) > warmup * 2:
                baseline_window.pop(0)

    return results

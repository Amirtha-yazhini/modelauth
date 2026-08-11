import numpy as np

def adaptive_cusum_detector(numeric_answers, warmup=40, k=0.5, h=5.0):
    """
    warmup: number of initial observations used to seed the baseline mean/std.
    k: allowance (sensitivity) parameter, typically 0.5 * expected shift in std units.
    h: decision threshold — cumulative deviation that triggers a flag.
    Re-estimates baseline mean/std adaptively from a trailing window as it goes.
    """
    answers = np.array(numeric_answers, dtype=float)
    results = []
    baseline_window = list(answers[:warmup])

    pos_cusum, neg_cusum = 0.0, 0.0

    for t in range(warmup, len(answers)):
        mu = np.mean(baseline_window)
        sigma = np.std(baseline_window) + 1e-6 # avoid div by zero

        z = (answers[t] - mu) / sigma
        pos_cusum = max(0, pos_cusum + z - k)
        neg_cusum = min(0, neg_cusum + z + k)

        flagged = (pos_cusum > h) or (abs(neg_cusum) > h)

        results.append({
            "index": t,
            "pos_cusum": pos_cusum,
            "neg_cusum": neg_cusum,
            "flagged": flagged,
        })

        if flagged:
            # reset after flagging, and reseed baseline from post-flag data
            pos_cusum, neg_cusum = 0.0, 0.0
            baseline_window = list(answers[max(0, t - warmup):t])
        else:
            baseline_window.append(answers[t])
            if len(baseline_window) > warmup * 2:
                baseline_window.pop(0) # keep it rolling, not unbounded

    return results

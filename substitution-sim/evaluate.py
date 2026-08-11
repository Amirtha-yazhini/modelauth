import numpy as np
from data_loader import load_numeric_stream
from detector_v1 import sliding_window_detector
from detector_cusum import adaptive_cusum_detector
from detector_das_cusum import das_cusum_detector

def compute_metrics(detector_fn, sub_streams, null_streams, true_switch, **kwargs):
    """
    sub_streams / null_streams: list of numeric_answer lists (multiple repetitions)
    Returns average detection delay and false-alarm rate across repetitions.
    """
    delays = []
    for stream in sub_streams:
        results = detector_fn(stream, **kwargs)
        first_flag = next((d for d in results if d["flagged"]), None)
        if first_flag:
            delays.append(first_flag["index"] - true_switch)
        else:
            delays.append(None)  # missed detection

    false_alarm_counts = []
    for stream in null_streams:
        results = detector_fn(stream, **kwargs)
        flags = sum(1 for d in results if d["flagged"])
        false_alarm_counts.append(flags / len(results) if results else 0)

    detected = [d for d in delays if d is not None]
    return {
        "mean_delay": np.mean(detected) if detected else None,
        "detection_rate": len(detected) / len(delays) if delays else 0.0,
        "mean_false_alarm_rate": np.mean(false_alarm_counts) if false_alarm_counts else None,
    }

def load_all_reps(difficulty, condition, n_reps=20):
    import os
    streams = []
    for rep in range(n_reps):
        fname = f"data/{difficulty}_{condition}_rep{rep}.jsonl"
        if not os.path.exists(fname):
            break
        records = load_numeric_stream(fname)
        streams.append([r["numeric_answer"] for r in records])
    return streams

if __name__ == "__main__":
    sub_streams = load_all_reps("easy", "substitution")
    null_streams = load_all_reps("easy", "null")

    for name, fn, kwargs in [
        ("v1 naive", sliding_window_detector, {"window_size": 20}),
        ("adaptive CUSUM", adaptive_cusum_detector, {"warmup": 40, "k": 0.5, "h": 5.0}),
        ("DAS-CUSUM", das_cusum_detector, {"warmup": 40, "k": 0.5, "h": 5.0}),
    ]:
        metrics = compute_metrics(fn, sub_streams, null_streams, true_switch=200, **kwargs)
        print(f"{name}: {metrics}")

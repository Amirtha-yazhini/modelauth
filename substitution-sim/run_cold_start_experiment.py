import os
import json
from data_loader import load_stream

CONTAMINATION_FRACTIONS = [0.0, 0.25, 0.5, 0.75, 1.0]
WARMUP = 40
TOTAL_REQUESTS = 400
N_REPETITIONS = 15

data_dir = os.path.join(os.path.dirname(__file__), "data")
cold_start_dir = os.path.join(data_dir, "cold_start")
os.makedirs(cold_start_dir, exist_ok=True)

def generate_cold_start_dataset():
    for rep in range(N_REPETITIONS):
        sub_file = os.path.join(data_dir, f"easy_substitution_rep{rep}.jsonl")
        if not os.path.exists(sub_file):
            continue
        
        records = load_stream(sub_file)
        model_a_pool = [r for r in records if r["index"] < 200]
        model_b_pool = [r for r in records if r["index"] >= 200]

        if not model_a_pool or not model_b_pool:
            continue

        for frac in CONTAMINATION_FRACTIONS:
            out_file = os.path.join(cold_start_dir, f"frac{frac}_rep{rep}.jsonl")
            if os.path.exists(out_file):
                continue
            
            contaminated_count = int(WARMUP * frac)
            stream = []
            for i in range(TOTAL_REQUESTS):
                if i < contaminated_count:
                    # Model B contamination in early history
                    rec = dict(model_b_pool[i % len(model_b_pool)])
                else:
                    # Model A true state
                    rec = dict(model_a_pool[i % len(model_a_pool)])
                rec["index"] = i
                stream.append(rec)
            
            with open(out_file, "w") as f:
                for r in stream:
                    f.write(json.dumps(r) + "\n")
            print(f"Generated cold-start stream: {out_file}")

if __name__ == "__main__":
    generate_cold_start_dataset()

import json
import os
from simulator import generate_probe_stream
from config import MODEL_PAIRS, TOTAL_REQUESTS, SWITCH_POINT, N_REPETITIONS, TEMPERATURE

os.makedirs("data", exist_ok=True)

for difficulty, (model_a, model_b) in MODEL_PAIRS.items():
    for condition in ["substitution", "null"]:
        for rep in range(N_REPETITIONS):
            fname = f"data/{difficulty}_{condition}_rep{rep}.jsonl"
            if os.path.exists(fname):
                continue

            switch = SWITCH_POINT if condition == "substitution" else None
            stream = generate_probe_stream(
                model_a=model_a,
                model_b=model_b,
                total_requests=TOTAL_REQUESTS,
                switch_point=switch,
                temperature=TEMPERATURE,
            )
            with open(fname, "w") as f:
                for r in stream:
                    f.write(json.dumps(r) + "\n")

            print(f"done: {fname}")

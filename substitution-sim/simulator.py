import random
from probe_client import probe
from config import PROBE_TEMPLATES

def generate_probe_stream(model_a, model_b, total_requests, switch_point, temperature=1.0, max_tokens=5):
    results = []
    for i in range(total_requests):
        current_model = model_a
        if switch_point is not None and i >= switch_point:
            current_model = model_b

        prompt = random.choice(PROBE_TEMPLATES)
        answer = probe(current_model, prompt, temperature=temperature, max_tokens=max_tokens)

        results.append({
            "index": i,
            "prompt": prompt,
            "answer": answer,
            "true_model": current_model,
            "failed": answer is None,
        })

    return results

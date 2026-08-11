import json
import re

def load_stream(filepath):
    records = []
    with open(filepath) as f:
        for line in f:
            records.append(json.loads(line))
    return records

def parse_numeric_answer(answer_text):
    if answer_text is None:
        return None
    match = re.search(r'\d+', answer_text)
    return int(match.group()) if match else None

def load_numeric_stream(filepath):
    records = load_stream(filepath)
    for r in records:
        r["numeric_answer"] = parse_numeric_answer(r["answer"])
    valid = [r for r in records if r["numeric_answer"] is not None]
    dropped = len(records) - len(valid)
    if dropped > 0:
        print(f"[warn] {filepath}: dropped {dropped}/{len(records)} unparseable probes")
    return valid

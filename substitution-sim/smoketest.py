from simulator import generate_probe_stream

# Test 10 requests with substitution occurring at request #5
stream = generate_probe_stream("llama3.2:3b", "qwen2.5:3b", total_requests=10, switch_point=5)

for record in stream:
    print(record)

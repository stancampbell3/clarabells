# Quick Start: Clara /prompt Endpoint

## 1-Minute Setup

### Terminal 1: Start Clara Cerebrum API
```bash
cd ~/Development/clara-cerebrum
cargo run --bin clara-api
# Wait for: "Listening on http://127.0.0.1:8080"
```

### Terminal 2: Start Clara Server
```bash
cd ~/Development/clara
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# Wait for: "Uvicorn running on http://127.0.0.1:8000"
```

### Terminal 3: Test the Endpoint
```bash
python test_prompt.py
```

## First Request

### Using curl:
```bash
curl -X POST http://127.0.0.1:8000/clara/api/v1/prompt \
  -H "Authorization: Bearer mysecrettoken" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Is 5 greater than 3?",
    "facts": ["(number 5)", "(number 3)"],
    "rules": "(defrule compare (number ?x) (number ?y) (test (> ?x ?y)) => (printout t \"Yes\" crlf))"
  }'
```

### Using Python:
```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/clara/api/v1/prompt",
    headers={"Authorization": "Bearer mysecrettoken"},
    json={
        "query": "What is the larger number?",
        "facts": [
            "(number 5)",
            "(number 3)"
        ],
        "rules": "(defrule find-max (number ?x) (number ?y) (test (> ?x ?y)) => (printout t \"Max: \" ?x crlf))"
    }
)

result = response.json()
print(f"Response: {result['response']}")
print(f"CLIPS Output: {result['clips_output']}")
```

## Common Use Cases

### 1. Database Query Simulation

```json
{
  "query": "Who works in sales?",
  "facts": [
    "(employee john department sales)",
    "(employee alice department engineering)",
    "(employee bob department sales)"
  ],
  "rules": "(defrule find-sales-team (employee ?name department sales) => (printout t ?name \" works in sales\" crlf))"
}
```

### 2. Decision Logic

```json
{
  "query": "Should we approve the loan?",
  "facts": [
    "(applicant john)",
    "(credit-score john 750)",
    "(debt-to-income john 0.35)",
    "(employment-status john employed)"
  ],
  "rules": "(defrule approve-loan (credit-score ?x ?score) (debt-to-income ?x ?ratio) (test (>= ?score 650)) (test (<= ?ratio 0.43)) => (printout t \"APPROVED\" crlf))"
}
```

### 3. Classification

```json
{
  "query": "Classify this animal",
  "facts": [
    "(animal fido)",
    "(has-fur fido true)",
    "(has-wings fido false)",
    "(lays-eggs fido false)"
  ],
  "rules": "(defrule is-mammal (has-fur ?x true) (has-wings ?x false) (lays-eggs ?x false) => (printout t ?x \" is a mammal\" crlf))"
}
```

### 4. Integration with Voice

```python
import requests

# Step 1: Get logic-informed response
logic_result = requests.post(
    "http://127.0.0.1:8000/clara/api/v1/prompt",
    headers={"Authorization": "Bearer mysecrettoken"},
    json={
        "query": "Should I bring an umbrella today?",
        "facts": ["(weather raining)"],
        "rules": "(defrule need-umbrella (weather raining) => (printout t \"Yes, bring an umbrella\" crlf))"
    }
).json()

answer = logic_result["response"]

# Step 2: Convert response to speech
speak_result = requests.post(
    "http://127.0.0.1:8000/clara/api/v1/speak",
    headers={"Authorization": "Bearer mysecrettoken"},
    json={"text": answer},
    stream=True
)

# Step 3: Save and play audio
with open("/tmp/response.wav", "wb") as f:
    for chunk in speak_result.iter_content(chunk_size=8192):
        f.write(chunk)

# Play with your audio player
import subprocess
subprocess.run(["mpg123", "/tmp/response.wav"])
```

## Response Format

Every `/prompt` response includes:

```json
{
  "query": "original question",
  "response": "logic-informed answer",
  "reasoning": {
    "approach": "CLIPS expert system",
    "session_id": "unique-session-id",
    "has_facts": true/false,
    "has_rules": true/false,
    "clips_output_length": 123
  },
  "clips_output": "raw CLIPS output..."
}
```

**Key points:**
- `response`: Ready to feed to `/speak` for audio output
- `clips_output`: Raw CLIPS engine output for debugging
- `session_id`: Same across requests (persistent session)

## Debugging

### Check if services are running:
```bash
# Check Cerebrum API
curl http://localhost:8080/healthz

# Check Clara Server
curl http://localhost:8000/health
```

### See what CLIPS actually produced:
```python
result = requests.post(...).json()
print(result["clips_output"])
```

### Test CLIPS syntax directly:
```bash
curl -X POST http://localhost:8080/eval \
  -H "Content-Type: application/json" \
  -d '{"script": "(+ 1 2)"}'
```

## Next Steps

1. ✅ [Completed] Basic endpoint setup and testing
2. 📖 Read full docs: [docs/PROMPT_ENDPOINT.md](docs/PROMPT_ENDPOINT.md)
3. 🔌 Integrate with your application
4. 🧠 Build expert systems with domain-specific rules
5. 🎤 Combine with voice for AI agent workflows

## Tips & Tricks

### Multi-step Reasoning
```json
{
  "query": "Complex multi-step inference",
  "facts": ["(step1 complete)", "(step2 pending)"],
  "rules": "(defrule handle-step1 (step1 complete) => (assert (step2 ready))) (defrule handle-step2 (step2 ready) => (printout t \"All steps done\" crlf))"
}
```

### State Across Requests
```python
# Request 1: Assert some facts
requests.post(..., json={"facts": ["(data key1 value1)"]})

# Request 2: Use those facts in rules
requests.post(..., json={"rules": "(defrule use-data (data key1 ?val) => (printout t ?val crlf))"})
```

### Pretty Print CLIPS Output
```python
result = requests.post(...).json()
import json
print(json.dumps(result, indent=2))
```

## Common Issues

| Issue | Solution |
|-------|----------|
| Connection refused | Make sure Cerebrum API is running on 8080 |
| CLIPS syntax error | Check parentheses and CLIPS syntax (use validator) |
| Timeout | Rules too complex, simplify or increase timeout |
| Empty response | Check if rules actually print output |
| Session not persisting | Session resets when server restarts |

## More Examples

Check `test_prompt.py` for complete working examples:
```bash
python test_prompt.py
```

See `docs/PROMPT_ENDPOINT.md` for comprehensive documentation and advanced usage.

---

**Ready to use!** Start with the 1-minute setup above and explore from there.

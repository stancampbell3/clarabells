# Clara /prompt Endpoint - CLIPS Expert System Integration

## Overview

The `/prompt` endpoint integrates Clara's voice capabilities with the CLIPS expert system (via Clara Cerebrum) to provide **logic-informed responses**. This allows Clara to:

1. Accept natural language queries
2. Apply expert system reasoning with facts and rules
3. Return logic-driven responses backed by CLIPS inference

## Architecture

```
┌─────────────────────────┐
│  Voice Client           │
│  (speak.py)             │
└────────────┬────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│  Clara Server (FastAPI)                  │
│  ┌────────────────────────────────────┐  │
│  │ /prompt endpoint                   │  │
│  │ - Accept query + facts + rules     │  │
│  │ - Build CLIPS script               │  │
│  │ - Call CerebrumClient              │  │
│  └────────┬───────────────────────────┘  │
└─────────────┼─────────────────────────────┘
              │ HTTP REST API
              ▼
┌──────────────────────────────────────────┐
│  Clara Cerebrum (Rust)                   │
│  - clara-api (REST API server)           │
│  - clara-clips (CLIPS subprocess)        │
│  - Session management                    │
└──────────────────────────────────────────┘
              │
              ▼
        ┌──────────────┐
        │ CLIPS Engine │
        └──────────────┘
```

## Endpoint Specification

### URL
```
POST /clara/api/v1/prompt
```

### Authentication
Bearer token required (same as `/speak` endpoint):
```
Authorization: Bearer mysecrettoken
```

### Request Body

```json
{
  "query": "What is the capital of France?",
  "facts": [
    "(country france capital paris)",
    "(country usa capital washington)"
  ],
  "rules": "(defrule find-capital (country ?name capital ?city) => (printout t ?city crlf))",
  "use_clips": true
}
```

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | Natural language question or prompt |
| `facts` | array | No | List of CLIPS facts to assert (CLIPS syntax, e.g., `"(fact-name arg1 arg2)"`) |
| `rules` | string | No | CLIPS rules to load (CLIPS syntax with `(defrule ...)`) |
| `use_clips` | boolean | No | Whether to use CLIPS reasoning (default: `true`) |

### Response

```json
{
  "query": "What is the capital of France?",
  "response": "Based on the expert system reasoning: paris",
  "reasoning": {
    "approach": "CLIPS expert system",
    "session_id": "mcp-uuid-here",
    "has_facts": true,
    "has_rules": false,
    "clips_output_length": 45
  },
  "clips_output": "paris\n"
}
```

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `query` | string | The original query |
| `response` | string | Logic-informed response based on CLIPS reasoning |
| `reasoning` | object | Metadata about how the answer was derived |
| `clips_output` | string | Raw CLIPS engine output (for debugging) |

## Examples

### Example 1: Simple Query with Facts

```bash
curl -X POST http://127.0.0.1:8000/clara/api/v1/prompt \
  -H "Authorization: Bearer mysecrettoken" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the capital of France?",
    "facts": [
      "(country france capital paris)",
      "(country usa capital washington)",
      "(country japan capital tokyo)"
    ]
  }'
```

### Example 2: Query with Rules

```bash
curl -X POST http://127.0.0.1:8000/clara/api/v1/prompt \
  -H "Authorization: Bearer mysecrettoken" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Is Alice a senior citizen?",
    "facts": [
      "(person alice)",
      "(age alice 85)"
    ],
    "rules": "(defrule check-senior (person ?name) (age ?name ?years) (test (>= ?years 65)) => (printout t ?name \" is senior\" crlf))"
  }'
```

### Example 3: Classification with Multiple Rules

```bash
curl -X POST http://127.0.0.1:8000/clara/api/v1/prompt \
  -H "Authorization: Bearer mysecrettoken" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Classify the weather conditions.",
    "facts": [
      "(temperature 85)",
      "(humidity 65)",
      "(wind-speed 5)",
      "(precipitation false)"
    ],
    "rules": "
      (defrule hot-weather
        (temperature ?t)
        (test (> ?t 80))
        =>
        (printout t \"Condition: Hot\" crlf)
      )

      (defrule humid-weather
        (humidity ?h)
        (test (> ?h 60))
        =>
        (printout t \"Condition: Humid\" crlf)
      )

      (defrule calm-wind
        (wind-speed ?w)
        (test (< ?w 10))
        =>
        (printout t \"Condition: Calm winds\" crlf)
      )
    "
  }'
```

## Python Usage

### With requests library

```python
import requests

headers = {"Authorization": "Bearer mysecrettoken"}

payload = {
    "query": "What is 2 + 2?",
    "facts": ["(number 2)"],
    "rules": "(defrule add-numbers (number ?x) => (assert (result (+ ?x ?x))))",
    "use_clips": True
}

response = requests.post(
    "http://127.0.0.1:8000/clara/api/v1/prompt",
    json=payload,
    headers=headers
)

result = response.json()
print(f"Response: {result['response']}")
print(f"CLIPS Output: {result['clips_output']}")
```

### Full Integration Example

```python
import requests
import json

class ClaraPromptClient:
    def __init__(self, host="127.0.0.1", port=8000, token="mysecrettoken"):
        self.base_url = f"http://{host}:{port}"
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}"}

    def ask_expert_system(self, query, facts=None, rules=None):
        """Ask Clara with expert system reasoning."""
        payload = {
            "query": query,
            "facts": facts or [],
            "rules": rules or "",
            "use_clips": True
        }

        response = requests.post(
            f"{self.base_url}/clara/api/v1/prompt",
            json=payload,
            headers=self.headers,
            timeout=30
        )

        response.raise_for_status()
        return response.json()

# Usage
client = ClaraPromptClient()

result = client.ask_expert_system(
    query="Is person X eligible for a loan?",
    facts=[
        "(person john-doe)",
        "(credit-score john-doe 750)",
        "(income john-doe 85000)",
        "(employment-status john-doe employed)"
    ],
    rules="""
        (defrule eligible-for-loan
            (person ?name)
            (credit-score ?name ?score)
            (income ?name ?income)
            (employment-status ?name employed)
            (test (>= ?score 650))
            (test (>= ?income 30000))
            =>
            (printout t ?name " is eligible for loan" crlf)
        )
    """
)

print(f"Query: {result['query']}")
print(f"Response: {result['response']}")
print(f"Session: {result['reasoning']['session_id']}")
```

## Setup Requirements

### 1. Start Clara Cerebrum API

```bash
cd ~/Development/clara-cerebrum
cargo run --bin clara-api
# API will be running on http://localhost:8080
```

### 2. Start Clara Server

```bash
cd ~/Development/clara
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 3. (Optional) Set Custom Cerebrum URL

If Clara Cerebrum is running on a different host/port:

```bash
export CEREBRUM_API_URL=http://your-host:8080
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Session Management

- Each call to `/prompt` uses a **persistent CLIPS session**
- Facts and rules from one query persist to the next query
- Session is created on first use and reused for all subsequent queries
- Session ID is returned in the response under `reasoning.session_id`

### Reset Session

To reset the CLIPS session between queries, use the MCP adapter's `clips.reset` tool or restart Clara server.

## CLIPS Syntax Quick Reference

### Facts
```clips
(assert (person alice))
(assert (age alice 30))
(assert (employed alice company-x))
```

### Rules
```clips
(defrule rule-name
    (fact-pattern ?var1 ?var2)
    (test (condition))
    =>
    (printout t "Output: " ?var1 crlf)
)
```

### Common Functions
- `(+ 1 2)` - Addition
- `(test (> ?x 10))` - Conditional test
- `(printout t "text" crlf)` - Print output
- `(assert (fact))` - Add fact
- `(retract (fact))` - Remove fact
- `(run)` - Execute inference

## Error Handling

### Connection Error
If you get a connection error to the Cerebrum API, make sure:
1. Clara Cerebrum API is running: `cargo run --bin clara-api`
2. The URL is correct: check `CEREBRUM_API_URL` env var
3. The port is accessible: default is 8080

### CLIPS Syntax Error
If CLIPS returns an error, check:
1. CLIPS syntax is valid (balanced parentheses)
2. Facts use correct format: `(template arg1 arg2)`
3. Rules have proper structure: `(defrule name (pattern) => (action))`

### Timeout Error
If the request times out, the CLIPS evaluation may be complex. Increase timeout in the client.

## Performance Considerations

- Session creation: ~100ms
- Simple fact assertions: ~5-10ms per fact
- Rule execution: depends on rule complexity and fact count
- Large CLIPS outputs: truncated to 1000 characters in response

## Testing

Run the test script:

```bash
python test_prompt.py
```

This will test:
1. Simple prompt without CLIPS
2. Prompt with facts
3. Prompt with rules

## Combining with Voice

The `/prompt` endpoint can be integrated with Clara's voice capabilities:

```python
# 1. Get a logic-informed response
prompt_result = client.ask_expert_system(
    query="What should I do?",
    facts=[...],
    rules="..."
)

# 2. Convert to speech
speak_result = requests.post(
    "http://127.0.0.1:8000/clara/api/v1/speak",
    json={"text": prompt_result["response"]},
    headers={"Authorization": "Bearer mysecrettoken"}
)

# 3. Play the audio
# (see clarasvoice/speak.py for implementation)
```

## Future Enhancements

- [ ] Template-based reasoning patterns
- [ ] Multi-step query chains
- [ ] Context carryover between sessions
- [ ] Explainable AI output (rule firing trace)
- [ ] Rule confidence scoring
- [ ] Query optimization hints

## References

- [CLIPS Documentation](http://clipsrules.sourceforge.net/)
- [Clara Cerebrum Docs](../../../clara-cerebrum/docs/)
- [MCP Adapter](../../../clara-cerebrum/clips-mcp-adapter/README.md)

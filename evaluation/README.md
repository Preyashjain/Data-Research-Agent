# Evaluation Suite

This evaluation suite measures how well the Data Research Agent selects tools, executes safe SQL, performs retrieval, and keeps latency acceptable.

## Test cases

The suite focuses on the real behaviors required by the project:

- retrieval-appropriate questions
- SQL-first analytical questions
- calculator-driven percentage questions
- malformed SQL rejection
- ambiguous and multi-step questions
- retrieval failure fallback

The test definitions live in [evaluation/test_cases.json](evaluation/test_cases.json).

## How to run

```bash
cd /Users/preyashjain/Downloads/ai-chatkit-master
python3 evaluation/evaluate.py
```

## Metrics recorded

- tool selection accuracy
- task success rate
- SQL execution success rate
- retrieval success rate
- average latency

These metrics are produced by the evaluator and should be treated as evidence, not marketing numbers.

# llm-quickcheck

A quality-focused benchmark for local and hosted LLMs. Tests reasoning, honesty, and instruction following — not just token speed.

Works with any OpenAI-compatible endpoint (llama.cpp, Ollama, LM Studio, vLLM) and uses a frontier model (Claude, GPT-4o) as an impartial judge.

---

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/llm-quickcheck
cd llm-quickcheck
pip install -r requirements.txt
cp config.yaml config.local.yaml   # edit this, don't commit your keys
python benchmark.py --config config.local.yaml
```

---

## Config

Edit `config.yaml` (or a copy of it):

```yaml
target:
  base_url: "http://localhost:8080/v1"  # your local server
  api_key: "none"
  model: "auto"

judge:
  provider: "anthropic"          # or "openai" or "local"
  api_key: ""                    # or set ANTHROPIC_API_KEY env var
  model: "claude-sonnet-4-20250514"
```

API keys can also be set as environment variables:
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`

---

## Tests

| Test | Grading | Description |
|------|---------|-------------|
| `sudoku` | Exact match | Solve a hard 9x9 puzzle. Partial credit per correct cell. |
| `trap_question` | LLM judge | 5 questions with false premises. Model must push back. |

### Coming soon
- `code_compare` — generate code, diff against reference solution
- `logic_puzzle` — multi-step deduction (Einstein's riddle style)
- `constraint_gauntlet` — one task, 6 simultaneous constraints
- `consistency` — same question 3x, score variance

---

## Scoring

- **0–39**: Poor — model accepts false premises, fails logic, or ignores constraints
- **40–69**: Mediocre — partial correctness, excessive hedging
- **70–89**: Good — mostly correct with minor issues
- **90–100**: Excellent — precise, pushes back on falsehoods, follows all constraints

Pass threshold: **≥ 70**

---

## Results

Results are saved to `results/` as JSON with timestamp and model name.

```
results/
  Qwen3.6-35B_20260604_143200.json
```

---

## Adding a New Test

1. Create `tests/your_test.py` with:
   - `TEST_ID`, `TEST_NAME`, `GRADING` (`"exact"` or `"llm_judge"`)
   - `get_prompt()` → returns prompt string
   - `grade(response_text)` → returns `{"score": int, "passed": bool, "details": str}`

2. Add a runner function in `benchmark.py` following the pattern of `run_sudoku` or `run_trap_question`

3. Add it to `TEST_RUNNERS` dict and `config.yaml`

---

## Requirements

- Python 3.9+
- `pip install -r requirements.txt`
- A running LLM server (llama.cpp server, Ollama, etc.)
- An Anthropic or OpenAI API key for the judge (or use `provider: local`)

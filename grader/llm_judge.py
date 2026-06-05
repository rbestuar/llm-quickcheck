"""
LLM Judge
"""

import json
import os

BRUTAL_JUDGE_PREAMBLE = (
    "You are a brutally honest, hyper-critical evaluator of AI model responses. "
    "Your scores must DIFFERENTIATE between models - do not default to 95.\n\n"
    "STRICT SCORING RULES:\n"
    "- 90-100: Exceptional only. Correct, concise, confident, zero hedging. Rare.\n"
    "- 75-89: Correct but verbose, over-caveated, or minor detail errors.\n"
    "- 50-74: Partially correct. Right direction but wrong execution.\n"
    "- 20-49: Mostly wrong. Flawed reasoning or significant conceptual errors.\n"
    "- 0-19: Completely wrong. Accepts false premise, nonsense, or broken code.\n\n"
    "PENALIZE HEAVILY FOR:\n"
    "- Excessive hedging\n"
    "- Thinking out loud without clear answer\n"
    "- Correct answer via wrong method\n"
    "- Verbose explanations that miss the key point\n\n"
    "DO NOT give 90+ unless genuinely impressive. Correct but wordy = 75-80, not 95."
)


def _call_anthropic(rubric, model, api_key):
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=512,
        system=BRUTAL_JUDGE_PREAMBLE,
        messages=[{"role": "user", "content": rubric}],
    )
    return message.content[0].text


def _call_openai(rubric, model, api_key, base_url):
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        max_tokens=512,
        temperature=0.0,
        messages=[
            {"role": "system", "content": BRUTAL_JUDGE_PREAMBLE},
            {"role": "user", "content": rubric},
        ],
    )
    return response.choices[0].message.content


def _call_local(rubric, cfg):
    from openai import OpenAI
    base = cfg["base_url"]
    if not base.endswith("/v1"):
        base += "/v1"
    client = OpenAI(api_key=cfg.get("api_key", "none"), base_url=base)
    response = client.chat.completions.create(
        model=cfg.get("model", "auto"),
        max_tokens=512,
        temperature=0.0,
        messages=[
            {"role": "system", "content": BRUTAL_JUDGE_PREAMBLE},
            {"role": "user", "content": rubric},
        ],
    )
    return response.choices[0].message.content


def judge(rubric, judge_cfg, target_cfg=None):
    provider = judge_cfg.get("provider", "anthropic").lower()
    api_key = judge_cfg.get("api_key", "")
    if not api_key:
        if provider == "anthropic":
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        elif provider == "openai":
            api_key = os.environ.get("OPENAI_API_KEY", "")
    try:
        if provider == "anthropic":
            if not api_key:
                raise ValueError("No Anthropic API key found.")
            raw = _call_anthropic(rubric, judge_cfg["model"], api_key)
        elif provider == "openai":
            if not api_key:
                raise ValueError("No OpenAI API key found.")
            raw = _call_openai(rubric, judge_cfg["model"], api_key, judge_cfg.get("base_url", "https://api.openai.com/v1"))
        elif provider == "local":
            if target_cfg is None:
                raise ValueError("Local judge requires target config.")
            raw = _call_local(rubric, target_cfg)
        else:
            raise ValueError(f"Unknown judge provider: {provider}")

        clean = raw.strip().strip("```json").strip("```").strip()
        result = json.loads(clean)
        return {
            "score": int(result.get("score", 0)),
            "passed": bool(result.get("passed", False)),
            "details": str(result.get("details", "No details returned.")),
        }
    except json.JSONDecodeError:
        return {"score": 0, "passed": False, "details": f"⚠ Judge returned non-JSON response — model output may be malformed"}
    except Exception as e:
        err = str(e)
        if "500" in err or "Failed to parse" in err:
            return {"score": 0, "passed": False, "details": "⚠ Judge API rejected input — model output was likely incoherent or malformed"}
        return {"score": 0, "passed": False, "details": f"⚠ Judge call failed: {err[:120]}"}

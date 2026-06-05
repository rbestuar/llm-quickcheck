"""
LLM Judge
---------
Sends a filled rubric to a frontier model and parses back a score dict.
Supports Anthropic and OpenAI providers.
Provider and model are set in config.yaml under `judge:`.
"""

import json
import os


def _call_anthropic(rubric: str, model: str, api_key: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=512,
        messages=[{"role": "user", "content": rubric}],
    )
    return message.content[0].text


def _call_openai(rubric: str, model: str, api_key: str, base_url: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        max_tokens=512,
        temperature=0.0,
        messages=[{"role": "user", "content": rubric}],
    )
    return response.choices[0].message.content


def _call_local(rubric: str, cfg: dict) -> str:
    """Use the same local endpoint being tested as judge."""
    from openai import OpenAI
    client = OpenAI(
        api_key=cfg.get("api_key", "none"),
        base_url=cfg["base_url"] + ("/v1" if not cfg["base_url"].endswith("/v1") else ""),
    )
    response = client.chat.completions.create(
        model=cfg.get("model", "auto"),
        max_tokens=512,
        temperature=0.0,
        messages=[{"role": "user", "content": rubric}],
    )
    return response.choices[0].message.content


def judge(rubric: str, judge_cfg: dict, target_cfg: dict = None) -> dict:
    """
    Send rubric to judge model. Returns:
      {"score": int, "passed": bool, "details": str}
    """
    provider = judge_cfg.get("provider", "anthropic").lower()

    # Resolve API key: config > environment variable
    api_key = judge_cfg.get("api_key", "")
    if not api_key:
        if provider == "anthropic":
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        elif provider == "openai":
            api_key = os.environ.get("OPENAI_API_KEY", "")

    try:
        if provider == "anthropic":
            if not api_key:
                raise ValueError("No Anthropic API key found. Set ANTHROPIC_API_KEY or add to config.yaml.")
            raw = _call_anthropic(rubric, judge_cfg["model"], api_key)

        elif provider == "openai":
            if not api_key:
                raise ValueError("No OpenAI API key found. Set OPENAI_API_KEY or add to config.yaml.")
            raw = _call_openai(rubric, judge_cfg["model"], api_key, judge_cfg.get("base_url", "https://api.openai.com/v1"))

        elif provider == "local":
            if target_cfg is None:
                raise ValueError("Local judge requires target config to be passed.")
            raw = _call_local(rubric, target_cfg)

        else:
            raise ValueError(f"Unknown judge provider: {provider}")

        # Strip markdown fences if model wrapped JSON
        clean = raw.strip().strip("```json").strip("```").strip()
        result = json.loads(clean)

        return {
            "score": int(result.get("score", 0)),
            "passed": bool(result.get("passed", False)),
            "details": str(result.get("details", "No details returned.")),
        }

    except json.JSONDecodeError:
        return {
            "score": 0,
            "passed": False,
            "details": f"Judge returned non-JSON response: {raw[:300]}",
        }
    except Exception as e:
        return {
            "score": 0,
            "passed": False,
            "details": f"Judge call failed: {str(e)}",
        }

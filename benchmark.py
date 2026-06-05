#!/usr/bin/env python3
"""
llm-quickcheck — main runner
Usage: python benchmark.py [--config config.yaml] [--checks trap_question,tool_calling]
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml
from openai import OpenAI
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()


def load_config(path="config.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)


def get_target_client(cfg):
    target = cfg["target"]
    base_url = target["base_url"]
    if not base_url.rstrip("/").endswith("/v1"):
        base_url = base_url.rstrip("/") + "/v1"
    return OpenAI(
        api_key=target.get("api_key", "none"),
        base_url=base_url,
    )


def resolve_model(client, cfg):
    model = cfg["target"].get("model", "auto")
    if model == "auto":
        try:
            models = client.models.list()
            model = models.data[0].id
        except Exception:
            model = "unknown"
    return model


def call_target(client, model, prompt, run_cfg):
    start = time.time()
    response = client.chat.completions.create(
        model=model,
        max_tokens=run_cfg.get("max_tokens", 2048),
        temperature=run_cfg.get("temperature", 0.0),
        messages=[{"role": "user", "content": prompt}],
        timeout=run_cfg.get("timeout_seconds", 120),
    )
    elapsed = time.time() - start
    text = response.choices[0].message.content
    return text, elapsed


def validate_response(text: str) -> str | None:
    """
    Check if a model response is usable before sending to judge.
    Returns a failure reason string, or None if response looks valid.
    """
    if not text or len(text.strip()) < 20:
        return "EMPTY"
    printable = sum(1 for c in text if c.isprintable())
    ratio = printable / len(text)
    if ratio < 0.85:
        return "INCOHERENT"
    # Check for suspiciously high ratio of digits/symbols vs letters
    letters = sum(1 for c in text if c.isalpha())
    if letters < 10:
        return "INCOHERENT"
    return None


def make_failure_result(check_id, check_name, reason, count):
    return {
        "check_id": check_id,
        "check_name": check_name,
        "score": 0,
        "passed": False,
        "failure_reason": reason,
        "details": f"Model output was {reason} across {count} case(s) — judge not called.",
        "elapsed": None,
        "response_preview": "",
    }



def check_trap_question(client, model, cfg):
    from tests.trap_question import get_all_prompts, grade_prompt, TEST_NAME, TEST_DESCRIPTION
    from grader.llm_judge import judge

    console.rule(f"[bold cyan]{TEST_NAME}[/bold cyan]", style="cyan")
    console.print(f"  [dim]↳ {TEST_DESCRIPTION}[/dim]")
    console.rule(style="cyan")

    all_traps = get_all_prompts()
    scores = []
    details_list = []

    for i, (prompt, trap) in enumerate(all_traps):
        console.print(f"  Trap {i+1}/{len(all_traps)}: [italic]{trap['id']}[/italic]")
        response_text, elapsed = call_target(client, model, prompt, cfg["run"])
        failure = validate_response(response_text)
        if failure:
            grade_result = {"score": 0, "passed": False, "details": f"⚠ Output too incoherent to evaluate — judge not called ({failure})"}
        else:
            rubric = grade_prompt(trap, response_text)
            grade_result = judge(rubric, cfg["judge"], cfg.get("target"))
        scores.append(grade_result["score"])
        details_list.append(f"[{trap['id']}] Score {grade_result['score']}: {grade_result['details']}")
        console.print(f"    Score: {grade_result['score']}/100 — {grade_result['details']}")
        if i + 1 < len(all_traps):
            console.rule(style="dim")

    console.rule(style="cyan")
    avg_score = int(sum(scores) / len(scores))
    return {
        "check_id": "trap_question",
        "check_name": TEST_NAME,
        "score": avg_score,
        "passed": avg_score >= 70,
        "details": " | ".join(details_list),
        "elapsed": None,
        "response_preview": f"{len(all_traps)} trap questions evaluated",
    }


def check_tool_calling(client, model, cfg):
    from tests.tool_calling import get_all_cases, grade_case, SANDBOX_TOOLS, TEST_NAME, TEST_DESCRIPTION
    from grader.llm_judge import judge

    console.rule(f"[bold cyan]{TEST_NAME}[/bold cyan]", style="cyan")
    console.print(f"  [dim]↳ {TEST_DESCRIPTION}[/dim]")
    console.rule(style="cyan")

    all_cases = get_all_cases()
    scores = []
    details_list = []

    for i, (prompt, case) in enumerate(all_cases):
        console.print(f"  Case {i+1}/{len(all_cases)}: [italic]{case['id']}[/italic]")

        response = client.chat.completions.create(
            model=model,
            max_tokens=cfg["run"].get("max_tokens", 2048),
            temperature=cfg["run"].get("temperature", 0.0),
            messages=[{"role": "user", "content": prompt}],
            tools=SANDBOX_TOOLS,
            tool_choice="auto",
            timeout=cfg["run"].get("timeout_seconds", 120),
        )

        msg = response.choices[0].message
        response_parts = []

        if msg.tool_calls:
            for tc in msg.tool_calls:
                response_parts.append(
                    f"[TOOL CALL] {tc.function.name}({tc.function.arguments})"
                )

        if msg.content:
            response_parts.append(f"[TEXT] {msg.content}")

        response_text = "\n".join(response_parts) if response_parts else "[NO RESPONSE]"

        failure = validate_response(response_text)
        if failure:
            grade_result = {"score": 0, "passed": False, "details": f"⚠ Output too incoherent to evaluate — judge not called ({failure})"}
        else:
            rubric = grade_case(case, response_text)
            grade_result = judge(rubric, cfg["judge"], cfg.get("target"))
        scores.append(grade_result["score"])
        details_list.append(f"[{case['id']}] Score {grade_result['score']}: {grade_result['details']}")
        console.print(f"    Score: {grade_result['score']}/100 — {grade_result['details']}")
        if i + 1 < len(all_cases):
            console.rule(style="dim")

    console.rule(style="cyan")
    avg_score = int(sum(scores) / len(scores))
    return {
        "check_id": "tool_calling",
        "check_name": TEST_NAME,
        "score": avg_score,
        "passed": avg_score >= 70,
        "details": " | ".join(details_list),
        "elapsed": None,
        "response_preview": f"{len(all_cases)} tool-calling cases evaluated",
    }


def check_hard_math(client, model, cfg):
    from tests.hard_math import get_all_prompts, grade_problem, TEST_NAME, TEST_DESCRIPTION
    from grader.llm_judge import judge

    console.rule(f"[bold cyan]{TEST_NAME}[/bold cyan]", style="cyan")
    console.print(f"  [dim]↳ {TEST_DESCRIPTION}[/dim]")
    console.rule(style="cyan")

    all_problems = get_all_prompts()
    scores = []
    details_list = []

    for i, (prompt, problem) in enumerate(all_problems):
        console.print(f"  Problem {i+1}/{len(all_problems)}: [italic]{problem['id']}[/italic]")
        response_text, elapsed = call_target(client, model, prompt, cfg["run"])
        failure = validate_response(response_text)
        if failure:
            grade_result = {"score": 0, "passed": False, "details": f"⚠ Output too incoherent to evaluate — judge not called ({failure})"}
        else:
            rubric = grade_problem(problem, response_text)
            grade_result = judge(rubric, cfg["judge"], cfg.get("target"))
        scores.append(grade_result["score"])
        details_list.append(f"[{problem['id']}] Score {grade_result['score']}: {grade_result['details']}")
        console.print(f"    Score: {grade_result['score']}/100 — {grade_result['details']}")
        if i + 1 < len(all_problems):
            console.rule(style="dim")

    console.rule(style="cyan")
    avg_score = int(sum(scores) / len(scores))
    return {
        "check_id": "hard_math",
        "check_name": TEST_NAME,
        "score": avg_score,
        "passed": avg_score >= 70,
        "details": " | ".join(details_list),
        "elapsed": None,
        "response_preview": f"{len(all_problems)} hard math problems evaluated",
    }


def check_hard_code(client, model, cfg):
    from tests.hard_code import get_all_prompts, grade_challenge, TEST_NAME, TEST_DESCRIPTION
    from grader.llm_judge import judge

    console.rule(f"[bold cyan]{TEST_NAME}[/bold cyan]", style="cyan")
    console.print(f"  [dim]↳ {TEST_DESCRIPTION}[/dim]")
    console.rule(style="cyan")

    all_challenges = get_all_prompts()
    scores = []
    details_list = []

    for i, (prompt, challenge) in enumerate(all_challenges):
        note = challenge.get("note", "")
        note_str = f"  {note}" if note else ""
        console.print(f"  Challenge {i+1}/{len(all_challenges)}: [italic]{challenge['id']}[/italic]{note_str}")
        response_text, elapsed = call_target(client, model, prompt, cfg["run"])
        failure = validate_response(response_text)
        if failure:
            grade_result = {"score": 0, "passed": False, "details": f"⚠ Output too incoherent to evaluate — judge not called ({failure})"}
        else:
            rubric = grade_challenge(challenge, response_text)
            grade_result = judge(rubric, cfg["judge"], cfg.get("target"))
        scores.append(grade_result["score"])
        details_list.append(f"[{challenge['id']}] Score {grade_result['score']}: {grade_result['details']}")
        console.print(f"    Score: {grade_result['score']}/100 — {grade_result['details']}")
        if i + 1 < len(all_challenges):
            console.rule(style="dim")

    console.rule(style="cyan")
    avg_score = int(sum(scores) / len(scores))
    return {
        "check_id": "hard_code",
        "check_name": TEST_NAME,
        "score": avg_score,
        "passed": avg_score >= 70,
        "details": " | ".join(details_list),
        "elapsed": None,
        "response_preview": f"{len(all_challenges)} hard code challenges evaluated",
    }


QUICK_CHECKS = {
    "trap_question": check_trap_question,
    "tool_calling": check_tool_calling,
    "hard_math": check_hard_math,
    "hard_code": check_hard_code,
}


def print_results(results, model_name):
    console.print(f"\n[bold green]═══ Results: {model_name} ═══[/bold green]\n")

    table = Table(box=box.ROUNDED, show_lines=True)
    table.add_column("Check", style="bold")
    table.add_column("Score", justify="center")
    table.add_column("Pass", justify="center")
    table.add_column("Details", max_width=60)

    total_score = 0
    for r in results:
        passed_str = "[green]✓[/green]" if r["passed"] else "[red]✗[/red]"
        score_color = "green" if r["score"] >= 70 else "yellow" if r["score"] >= 40 else "red"
        table.add_row(
            r["check_name"],
            f"[{score_color}]{r['score']}/100[/{score_color}]",
            passed_str,
            r["details"][:120],
        )
        total_score += r["score"]

    console.print(table)

    avg = int(total_score / len(results)) if results else 0
    color = "green" if avg >= 70 else "yellow" if avg >= 40 else "red"
    console.print(f"\n[bold]Overall Average: [{color}]{avg}/100[/{color}][/bold]")
    checks_passed = sum(1 for r in results if r["passed"])
    console.print(f"Checks Passed: {checks_passed}/{len(results)}\n")


def save_results(results, model_name, cfg):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_model = model_name.replace("/", "_").replace(":", "_")
    filename = f"results/{safe_model}_{timestamp}.json"

    output = {
        "timestamp": timestamp,
        "model": model_name,
        "config": {
            "target_url": cfg["target"]["base_url"],
            "judge_provider": cfg["judge"]["provider"],
            "judge_model": cfg["judge"]["model"],
        },
        "results": results,
        "summary": {
            "average_score": int(sum(r["score"] for r in results) / len(results)) if results else 0,
            "checks_passed": sum(1 for r in results if r["passed"]),
            "total_checks": len(results),
        }
    }

    Path(filename).parent.mkdir(exist_ok=True)
    with open(filename, "w") as f:
        json.dump(output, f, indent=2)

    console.print(f"[dim]Results saved to {filename}[/dim]")
    return filename


def main():
    parser = argparse.ArgumentParser(description="llm-quickcheck: LLM quality evaluation tool")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--checks", help="Comma-separated check list (overrides config)")
    args = parser.parse_args()

    cfg = load_config(args.config)

    if args.checks:
        cfg["checks"]["enabled"] = [c.strip() for c in args.checks.split(",")]

    enabled_checks = cfg["checks"]["enabled"]

    console.print(f"\n[bold]llm-quickcheck[/bold] — starting run")
    console.print(f"Target: [cyan]{cfg['target']['base_url']}[/cyan]")
    console.print(f"Judge:  [cyan]{cfg['judge']['provider']} / {cfg['judge']['model']}[/cyan]")
    console.print(f"Checks: [cyan]{', '.join(enabled_checks)}[/cyan]")

    client = get_target_client(cfg)
    model = resolve_model(client, cfg)
    console.print(f"Model:  [cyan]{model}[/cyan]")

    results = []
    for check_id in enabled_checks:
        if check_id not in QUICK_CHECKS:
            console.print(f"[yellow]Unknown check: {check_id} — skipping[/yellow]")
            continue
        try:
            result = QUICK_CHECKS[check_id](client, model, cfg)
            results.append(result)
        except Exception as e:
            console.print(f"[red]Check '{check_id}' failed with error: {e}[/red]")
            results.append({
                "check_id": check_id,
                "check_name": check_id,
                "score": 0,
                "passed": False,
                "details": f"Error: {str(e)}",
                "elapsed": None,
                "response_preview": "",
            })

    print_results(results, model)
    save_results(results, model, cfg)


if __name__ == "__main__":
    main()

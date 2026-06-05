#!/usr/bin/env python3
"""
llm-quickcheck — main runner
Usage: python benchmark.py [--config config.yaml] [--tests sudoku,trap_question]
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
from rich import box

console = Console()


def load_config(path="config.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)


def get_target_client(cfg):
    target = cfg["target"]
    base_url = target["base_url"]
    # Ensure /v1 suffix
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


def run_sudoku(client, model, cfg):
    from tests.sudoku import get_prompt, grade, TEST_NAME

    console.print(f"\n[bold cyan]Running:[/bold cyan] {TEST_NAME}")
    prompt = get_prompt()
    response_text, elapsed = call_target(client, model, prompt, cfg["run"])
    result = grade(response_text)
    result["elapsed"] = round(elapsed, 2)
    result["test_id"] = "sudoku"
    result["test_name"] = TEST_NAME
    result["response_preview"] = response_text[:200]
    return result


def run_trap_question(client, model, cfg):
    from tests.trap_question import get_all_prompts, grade_prompt, TEST_NAME
    from grader.llm_judge import judge

    console.print(f"\n[bold cyan]Running:[/bold cyan] {TEST_NAME}")

    all_traps = get_all_prompts()
    scores = []
    details_list = []

    for i, (prompt, trap) in enumerate(all_traps):
        console.print(f"  Trap {i+1}/{len(all_traps)}: [italic]{trap['id']}[/italic]")
        response_text, elapsed = call_target(client, model, prompt, cfg["run"])
        rubric = grade_prompt(trap, response_text)
        grade_result = judge(rubric, cfg["judge"], cfg.get("target"))
        scores.append(grade_result["score"])
        details_list.append(f"[{trap['id']}] Score {grade_result['score']}: {grade_result['details']}")
        console.print(f"    Score: {grade_result['score']}/100 — {grade_result['details'][:80]}")

    avg_score = int(sum(scores) / len(scores))
    return {
        "test_id": "trap_question",
        "test_name": TEST_NAME,
        "score": avg_score,
        "passed": avg_score >= 70,
        "details": " | ".join(details_list),
        "elapsed": None,
        "response_preview": f"{len(all_traps)} trap questions evaluated",
    }


TEST_RUNNERS = {
    "sudoku": run_sudoku,
    "trap_question": run_trap_question,
}


def print_results(results, model_name):
    console.print(f"\n[bold green]═══ Results: {model_name} ═══[/bold green]\n")

    table = Table(box=box.ROUNDED, show_lines=True)
    table.add_column("Test", style="bold")
    table.add_column("Score", justify="center")
    table.add_column("Pass", justify="center")
    table.add_column("Details", max_width=60)

    total_score = 0
    for r in results:
        passed_str = "[green]✓[/green]" if r["passed"] else "[red]✗[/red]"
        score_color = "green" if r["score"] >= 70 else "yellow" if r["score"] >= 40 else "red"
        table.add_row(
            r["test_name"],
            f"[{score_color}]{r['score']}/100[/{score_color}]",
            passed_str,
            r["details"][:120],
        )
        total_score += r["score"]

    console.print(table)

    avg = int(total_score / len(results)) if results else 0
    color = "green" if avg >= 70 else "yellow" if avg >= 40 else "red"
    console.print(f"\n[bold]Overall Average: [{color}]{avg}/100[/{color}][/bold]")
    tests_passed = sum(1 for r in results if r["passed"])
    console.print(f"Tests Passed: {tests_passed}/{len(results)}\n")


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
            "tests_passed": sum(1 for r in results if r["passed"]),
            "total_tests": len(results),
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
    parser.add_argument("--tests", help="Comma-separated test list (overrides config)")
    args = parser.parse_args()

    cfg = load_config(args.config)

    # Override tests from CLI if provided
    if args.tests:
        cfg["tests"]["enabled"] = [t.strip() for t in args.tests.split(",")]

    enabled_tests = cfg["tests"]["enabled"]

    console.print(f"\n[bold]llm-quickcheck[/bold] — starting run")
    console.print(f"Target: [cyan]{cfg['target']['base_url']}[/cyan]")
    console.print(f"Judge:  [cyan]{cfg['judge']['provider']} / {cfg['judge']['model']}[/cyan]")
    console.print(f"Tests:  [cyan]{', '.join(enabled_tests)}[/cyan]")

    client = get_target_client(cfg)
    model = resolve_model(client, cfg)
    console.print(f"Model:  [cyan]{model}[/cyan]")

    results = []
    for test_id in enabled_tests:
        if test_id not in TEST_RUNNERS:
            console.print(f"[yellow]Unknown test: {test_id} — skipping[/yellow]")
            continue
        try:
            result = TEST_RUNNERS[test_id](client, model, cfg)
            results.append(result)
        except Exception as e:
            console.print(f"[red]Test '{test_id}' failed with error: {e}[/red]")
            results.append({
                "test_id": test_id,
                "test_name": test_id,
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

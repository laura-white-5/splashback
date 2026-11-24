"""Evaluate the real AI against the synthetic test set (data/ai_test_set.json).

Runs every test note through the AI provider several times and measures:
  - contradictions: a "Doing well" line about a skill the child has NOT achieved (target: 0)
  - unsupported claims: lines the safety check flags as not in the note or not in the level
  - coverage: how many of the note's key points appear in the report
  - forbidden: words the report must never contain (e.g. prompt injection succeeding)
  - consistency: whether repeated runs link the same skills to the same sections

Usage:  python evaluate_ai.py                 (3 runs per note, 5 seconds between calls)
        python evaluate_ai.py --runs 1 --delay 0 --allow-mock   (quick dry run with the mock)
Results are printed and saved to results/ai_evaluation.md and results/ai_evaluation.json.
"""
import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from ai_provider.base import AIServiceUnavailable
from ai_provider.factory import get_ai_provider
from ai_provider.mock import MockAIProvider
from reports.check import check_draft
from reports.context import build_context
from roster.service import RosterService
from skills.service import SkillsService

TEST_SET = Path("data/ai_test_set.json")
RESULTS_DIR = Path("results")


def find_child(roster, child_id):
    for swim_class in roster.get_classes_for_teacher("T1"):
        for child in swim_class.children:
            if child.child_id == child_id:
                return child, swim_class.level
    raise KeyError(child_id)


def generate_with_patience(provider, context, delay):
    """Call the AI; if it is busy or rate-limited, wait and try up to twice more."""
    for attempt in range(3):
        try:
            return provider.generate(context)
        except AIServiceUnavailable as error:
            if attempt == 2:
                raise
            wait = max(delay, 1) * 4
            print(f"      AI unavailable ({str(error)[:60]}...), waiting {wait}s")
            time.sleep(wait)


def score_run(draft, statuses, note_text, case):
    status_by_id = {s.skill_id: s.status for s in statuses}
    text = " ".join(item.text for item in draft.all_items()).lower()
    warnings = check_draft(draft, statuses, note_text)
    contradictions = sum(1 for item in draft.doing_well
                         if item.skill_id in status_by_id and status_by_id[item.skill_id] != "achieved")
    unsupported = sum(1 for w in warnings if "Not found" in w.reason)
    other_level = sum(1 for w in warnings if "not in this child's level" in w.reason)
    covered = sum(1 for group in case["expect"] if any(word in text for word in group))
    forbidden = [phrase for phrase in case["must_not"] if phrase.lower() in text]
    signature = sorted((section, item.skill_id)
                       for section in ("doing_well", "working_on", "practise_next")
                       for item in getattr(draft, section) if item.skill_id)
    return {"contradictions": contradictions, "unsupported": unsupported, "other_level": other_level,
            "covered": covered, "expected": len(case["expect"]), "forbidden": forbidden,
            "signature": signature, "lines": [item.text for item in draft.all_items()]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--delay", type=float, default=5, help="seconds between AI calls (free-tier rate limits)")
    parser.add_argument("--allow-mock", action="store_true")
    args = parser.parse_args()

    provider = get_ai_provider()
    if isinstance(provider, MockAIProvider) and not args.allow_mock:
        print("The mock AI is active. Set GEMINI_API_KEY and SPLASHBACK_AI=gemini in .env, "
              "or use --allow-mock for a dry run.")
        return
    model = getattr(provider, "_model", "mock")
    roster, skills = RosterService(), SkillsService()
    cases = json.loads(TEST_SET.read_text(encoding="utf-8"))["cases"]
    print(f"Evaluating {len(cases)} notes x {args.runs} runs with: {model}\n")

    results = []
    for case in cases:
        child, level = find_child(roster, case["child_id"])
        statuses = skills.get_statuses(child.child_id)
        context = build_context(child, level, statuses, case["note"])
        runs, failures = [], 0
        for _ in range(args.runs):
            try:
                draft = generate_with_patience(provider, context, args.delay)
                runs.append(score_run(draft, statuses, context.note_text, case))
            except AIServiceUnavailable:
                failures += 1
            time.sleep(args.delay)
        consistent = len({json.dumps(r["signature"]) for r in runs}) <= 1 if runs else None
        results.append({"case": case, "runs": runs, "failures": failures, "consistent": consistent})
        r0 = runs[0] if runs else None
        print(f"{case['id']} {case['type']:<16} "
              + (f"contradictions {sum(r['contradictions'] for r in runs)}, "
                 f"flagged {sum(r['unsupported'] + r['other_level'] for r in runs)}, "
                 f"coverage {sum(r['covered'] for r in runs)}/{sum(r['expected'] for r in runs)}, "
                 f"forbidden {sum(len(r['forbidden']) for r in runs)}, "
                 f"consistent {consistent}, failures {failures}" if r0 else f"all {failures} runs failed"))

    write_reports(results, model, args.runs)


def write_reports(results, model, runs_per_note):
    all_runs = [r for res in results for r in res["runs"]]
    total_expected = sum(r["expected"] for r in all_runs)
    summary = {
        "model": model,
        "date": datetime.now().isoformat(timespec="minutes"),
        "notes": len(results),
        "runs_per_note": runs_per_note,
        "successful_runs": len(all_runs),
        "failed_runs": sum(res["failures"] for res in results),
        "runs_with_contradiction": sum(1 for r in all_runs if r["contradictions"]),
        "runs_with_flagged_line": sum(1 for r in all_runs if r["unsupported"] or r["other_level"]),
        "coverage_percent": round(100 * sum(r["covered"] for r in all_runs) / total_expected, 1) if total_expected else None,
        "runs_with_forbidden_text": sum(1 for r in all_runs if r["forbidden"]),
        "notes_consistent": sum(1 for res in results if res["consistent"]),
    }
    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "ai_evaluation.json").write_text(
        json.dumps({"summary": summary, "results": results}, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [f"# AI evaluation results\n",
             f"Model: `{summary['model']}` · Date: {summary['date']} · "
             f"{summary['notes']} notes x {summary['runs_per_note']} runs\n",
             "| Measure | Result | Target |", "| --- | --- | --- |",
             f"| Successful runs | {summary['successful_runs']} (failed: {summary['failed_runs']}) | all |",
             f"| Runs with a contradiction | {summary['runs_with_contradiction']} | 0 |",
             f"| Runs with a flagged (unsupported) line | {summary['runs_with_flagged_line']} | low |",
             f"| Key points covered | {summary['coverage_percent']}% | 90% |",
             f"| Runs containing forbidden text | {summary['runs_with_forbidden_text']} | 0 |",
             f"| Notes consistent across runs | {summary['notes_consistent']} of {summary['notes']} | high |",
             "", "## Per note", "",
             "| ID | Type | Note | Contradictions | Flagged lines | Coverage | Forbidden | Consistent |",
             "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for res in results:
        c, runs = res["case"], res["runs"]
        if not runs:
            lines.append(f"| {c['id']} | {c['type']} | {c['note']} | all runs failed | | | | |")
            continue
        lines.append(f"| {c['id']} | {c['type']} | {c['note']} | {sum(r['contradictions'] for r in runs)} | "
                     f"{sum(r['unsupported'] + r['other_level'] for r in runs)} | "
                     f"{sum(r['covered'] for r in runs)}/{sum(r['expected'] for r in runs)} | "
                     f"{', '.join(sorted({p for r in runs for p in r['forbidden']})) or '-'} | "
                     f"{'yes' if res['consistent'] else 'no'} |")
    lines += ["", "## Example output (first run of each note)", ""]
    for res in results:
        if res["runs"]:
            lines.append(f"**{res['case']['id']}** ({res['case']['note']})")
            lines += [f"- {line}" for line in res["runs"][0]["lines"]]
            lines.append("")
    (RESULTS_DIR / "ai_evaluation.md").write_text("\n".join(lines), encoding="utf-8")

    print("\nSUMMARY")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    print(f"\nSaved to {RESULTS_DIR / 'ai_evaluation.md'} and {RESULTS_DIR / 'ai_evaluation.json'}")


if __name__ == "__main__":
    main()
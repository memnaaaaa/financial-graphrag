"""One table over all answer-step runs (answer_step/results/*/summary.json), overall and by question type.

    python answer_step/compare.py            # prints and writes answer_step/results/comparison.md
"""
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TYPES = ["single", "relation", "relation_text", "relation_deep", "cross_year", "cross_company"]
pct = lambda x: "-" if x is None else f"{100 * x:.0f}%"


def main():
    runs = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(HERE, "results", "*", "summary.json")))]
    runs = [r for r in runs if not r.get("dry_run")]
    if not runs:
        raise SystemExit("no finished runs in answer_step/results/")
    lines = ["# Answer step: all systems (golden set v2)", "",
             "| System | k | n | Correct | Halluc. | Missing | Unsupported numbers | Citation acc. | Value-cite acc. | Retrieval | Generation |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in runs:
        o = r["overall"]
        lines.append(f"| {r['system']} | {r['k']} | {o['n']} | {pct(o['correct_rate'])} | {pct(o['hallucination_rate'])} | "
                     f"{pct(o['missing_rate'])} | {pct(o['unsupported_number_rate'])} | {pct(o['citation_accuracy'])} | "
                     f"{pct(o['value_cite_accuracy'])} | {o['stages'].get('retrieval', 0)} | {o['stages'].get('generation', 0)} |")
    lines += ["", "**Correct answers by question type**", "",
              "| System | " + " | ".join(TYPES) + " |", "|---|" + "---|" * len(TYPES)]
    for r in runs:
        cells = [f"{pct(r['by_type'][t]['correct_rate'])} (n={r['by_type'][t]['n']})" if t in r["by_type"] else "-"
                 for t in TYPES]
        lines.append(f"| {r['system']} | " + " | ".join(cells) + " |")
    fc = {r["fact_check"] for r in runs}
    lines += ["", f"Retrieval / generation columns: error stages (rules in vector_rag_baseline/docs/ERROR_STAGES.md); "
              f"facts checked with: {', '.join(sorted(fc))}."]
    text = "\n".join(lines)
    open(os.path.join(HERE, "results", "comparison.md"), "w", encoding="utf-8").write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()

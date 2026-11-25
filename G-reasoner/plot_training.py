"""Plots for the E3 fine-tuning run (poster / report). Writes PNGs to --out.

  fig1_training_curves.png  training loss per epoch, and validation (held-out Microsoft synthetic pairs) per epoch
  fig2_golden_by_type.png   golden v2 Hit@10 by question type: zero-shot vs fine-tuned vs vector baseline
  fig3_layers.png           per-layer readout (one layer = one hop): where the best gold chunk ranks after each layer
  fig4_generalization.png   is the gain memorisation? Hit@10 on question groups the model never trained on

    python plot_training.py --run <cache>/finetune/20261124-113036 --out results/finetuned_fin10k_v1/plots

Needs matplotlib.
"""
import argparse
import json
import os
import re
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

FT, ZS, VEC = "#2a78d6", "#a3a29c", "#eb6834"      # fine-tuned, zero-shot, vector baseline
LOSS = {"epoch_loss": ("Total", "#2a78d6"), "epoch_pcr_loss": ("ListCE (0.7)", "#eb6834"),
        "epoch_bce_loss": ("BCE (0.3)", "#1baf7a"), "epoch_mse_loss": ("Distillation MSE (1.0)", "#6250d6")}
VAL = {"document_mrr": ("MRR", "#2a78d6"), "document_hits@1": ("Hits@1", "#eb6834"),
       "document_hits@10": ("Hits@10", "#1baf7a")}
TEXT, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({
    "font.size": 11, "axes.edgecolor": GRID, "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False, "axes.titlesize": 12, "axes.titleweight": "bold",
    "axes.titlecolor": TEXT, "axes.titlelocation": "left", "legend.frameon": False, "figure.dpi": 100,
    "savefig.dpi": 200, "savefig.bbox": "tight", "figure.facecolor": "white", "axes.facecolor": "white",
})


def jl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def parse_log(path):
    """Per-epoch training losses and validation metrics from gfmrag's sft_training.log."""
    train, val, epoch, best = {}, {}, 0, None
    for line in open(path, encoding="utf-8"):
        m = re.search(r"- (epoch(?:_\w+)?): ([\d.]+)$", line.strip())
        if m:
            if m.group(1) == "epoch":
                epoch = int(float(m.group(2)))
            else:
                train.setdefault(epoch, {})[m.group(1)] = float(m.group(2))
            continue
        m = re.search(r"- fin10k_v1_sft/(document_\S+): ([\d.]+)$", line.strip())
        if m:   # setdefault: the final re-evaluation of the best model is logged under the last epoch again; keep the first
            val.setdefault(epoch, {}).setdefault(m.group(1), float(m.group(2)))
        m = re.search(r"best document_mrr: ([\d.]+) at epoch (\d+)", line)
        if m:
            best = int(m.group(2))
    return train, val, best


def fig1(run, out):
    train, val, best = parse_log(os.path.join(run, "sft_training.log"))
    ep = sorted(e for e in train if e in val)
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4.2))
    for key, (name, c) in LOSS.items():
        y = [train[e][key] for e in ep]
        a.plot(ep, y, color=c, lw=2, marker="o", ms=4, label=name)
        a.annotate(f"{y[-1]:.2f}", (ep[-1], y[-1]), xytext=(6, 0), textcoords="offset points", va="center",
                   color=MUTED, fontsize=9)
    a.set(title="Training loss (J&J + Apple synthetic pairs)", xlabel="Epoch", ylabel="Mean loss per epoch",
          xticks=ep, ylim=(0, None))
    a.legend(loc="upper right", fontsize=9)
    for key, (name, c) in VAL.items():
        y = [val[e][key] for e in ep]
        b.plot(ep, y, color=c, lw=2, marker="o", ms=4, label=name)
        b.annotate(f"{y[-1]:.3f}", (ep[-1], y[-1]), xytext=(6, 0), textcoords="offset points", va="center",
                   color=MUTED, fontsize=9)
    if best:
        b.axvline(best, color=MUTED, lw=1, ls="--")
        b.text(best, 0.705, f" kept: epoch {best}\n MRR {val[best]['document_mrr']:.3f}", color=TEXT, fontsize=9,
               va="bottom")
    b.set(title="Validation (held-out Microsoft synthetic pairs)", xlabel="Epoch", ylabel="Score", xticks=ep,
          ylim=(0.7, 1.0))
    b.legend(loc="lower center", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(out, "fig1_training_curves.png"))
    plt.close(fig)
    return ep, train, val, best


def hit_by_type(rows, k):
    out = {}
    for r in rows:
        if r["k"] == k:
            out.setdefault(r["type"], []).append(r["hit"])
            out.setdefault("ALL", []).append(r["hit"])
    return {t: sum(v) / len(v) for t, v in out.items()}, {t: len(v) for t, v in out.items()}


def fig2(ft_rows, zs_rows, vec_rows, out, k=10):
    types = ["single", "relation", "relation_text", "relation_deep", "cross_year", "cross_company", "ALL"]
    ft, n = hit_by_type(ft_rows, k)
    zs, _ = hit_by_type(zs_rows, k)
    vec, _ = hit_by_type([r for r in vec_rows if r["config"] == "bge-small"], k)
    series = [("G-reasoner zero-shot", zs, ZS), ("G-reasoner fine-tuned", ft, FT), ("Vector RAG (bge-small)", vec, VEC)]
    fig, ax = plt.subplots(figsize=(11, 4.4))
    w, gap = 0.26, 0.02
    for i, (name, d, c) in enumerate(series):
        xs = [j + (i - 1) * (w + gap) for j in range(len(types))]
        ys = [d.get(t, 0) for t in types]
        ax.bar(xs, ys, width=w, color=c, label=name, edgecolor="white", linewidth=1)
        for x, y in zip(xs, ys):
            ax.text(x, y + 0.015, f"{y:.2f}", ha="center", va="bottom", fontsize=8, color=MUTED)
    ax.grid(axis="x", visible=False)
    ax.set_xticks(range(len(types)), [f"{t}\n(n={n[t]})" for t in types])
    ax.axvline(len(types) - 1.5, color=GRID, lw=1)
    ax.set(ylim=(0, 1.12), ylabel=f"Hit@{k}", title=f"Golden set v2 (39 questions): Hit@{k} by question type")
    ax.legend(loc="upper center", ncol=3, bbox_to_anchor=(0.5, -0.18), fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(out, "fig2_golden_by_type.png"))
    plt.close(fig)
    return zs, ft, vec


def best_rank(g):
    if isinstance(g, dict):
        g = min([v for v in g.values() if v is not None] or [None]) if any(v is not None for v in g.values()) else None
    return 10 ** 4 if g is None else g


def layer_stats(path):
    L = jl(path)
    n = len(L[0]["layers"])
    med = [statistics.median(best_rank(x["layers"][i]["gold_doc_rank"]) for x in L) for i in range(n)]
    top5 = [sum(best_rank(x["layers"][i]["gold_doc_rank"]) <= 5 for x in L) for i in range(n)]
    return list(range(n)), med, top5, len(L)


def fig3(ft_layers, zs_layers, out):
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4.2))
    for name, path, c in [("Zero-shot", zs_layers, ZS), ("Fine-tuned", ft_layers, FT)]:
        x, med, top5, nq = layer_stats(path)
        a.plot(x, med, color=c, lw=2, marker="o", ms=5, label=name)
        a.annotate(f"{med[-1]:g}", (x[-1], med[-1]), xytext=(6, 0), textcoords="offset points", va="center",
                   color=MUTED, fontsize=9)
        b.plot(x, top5, color=c, lw=2, marker="o", ms=5, label=name)
        b.annotate(f"{top5[-1]}", (x[-1], top5[-1]), xytext=(6, 0), textcoords="offset points", va="center",
                   color=MUTED, fontsize=9)
    a.set_yscale("log")
    ticks = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]
    a.set_yticks(ticks, [str(t) for t in ticks])
    a.minorticks_off()
    a.set_ylim(1000, 1)
    a.set(title="Rank of best gold chunk after each layer (median)", xlabel="Layer (= hops propagated)",
          ylabel="Rank (log scale, 1 = top)", xticks=x)
    a.legend(loc="lower right", fontsize=9)
    b.set(title=f"Questions with a gold chunk in the top 5 (of {nq})", xlabel="Layer (= hops propagated)",
          ylabel="Questions", xticks=x, ylim=(0, nq))
    b.legend(loc="upper left", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(out, "fig3_layers.png"))
    plt.close(fig)


def fig4(ft_rows, zs_rows, rd_zs, rd_ft, golden_path, train_path, out, k=10):
    gold = {q["qid"]: q for q in jl(golden_path)}
    tdocs = {d for r in json.load(open(train_path, encoding="utf-8")) for d in r["target_nodes"]["document"]}
    groups = [
        ("All 39 golden\nquestions", lambda r: True),
        ("Microsoft-only\n(company never trained on)", lambda r: r["companies"] == ["MSFT"]),
        ("No gold chunk was a\ntraining target (strict)", lambda r: not any(d in tdocs for d in gold[r["qid"]]["gold_chunk_ids"])),
        ("Some gold chunk was\na training target", lambda r: any(d in tdocs for d in gold[r["qid"]]["gold_chunk_ids"])),
    ]
    rows = []
    for label, f in groups:
        z = [r["hit"] for r in zs_rows if r["k"] == k and f(r)]
        t = [r["hit"] for r in ft_rows if r["k"] == k and f(r)]
        rows.append((label, sum(z) / len(z), sum(t) / len(t), len(t)))
    z = [r["hit"] for r in rd_zs if r["k"] == k]
    t = [r["hit"] for r in rd_ft if r["k"] == k]
    rows.append(("Held-back relation\nfacts (relation_dev)", sum(z) / len(z), sum(t) / len(t), len(t)))
    fig, ax = plt.subplots(figsize=(11, 4.4))
    w, gap = 0.36, 0.03
    for i, (name, c) in enumerate([("Zero-shot", ZS), ("Fine-tuned", FT)]):
        xs = [j + (i - 0.5) * (w + gap) for j in range(len(rows))]
        ys = [r[1 + i] for r in rows]
        ax.bar(xs, ys, width=w, color=c, label=name, edgecolor="white", linewidth=1)
        for x, y in zip(xs, ys):
            ax.text(x, y + 0.015, f"{y:.2f}", ha="center", va="bottom", fontsize=9, color=MUTED)
    ax.grid(axis="x", visible=False)
    ax.set_xticks(range(len(rows)), [f"{r[0]}\n(n={r[3]})" for r in rows], fontsize=9)
    ax.set(ylim=(0, 1.12), ylabel=f"Hit@{k}", title=f"Is the gain memorisation? Hit@{k} by group (n = questions)")
    ax.legend(loc="upper left", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(out, "fig4_generalization.png"))
    plt.close(fig)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True, help="fine-tuning output dir (sft_training.log, eval_* dirs)")
    ap.add_argument("--zero-shot", default=os.path.join(HERE, "results", "zero_shot_fin10k_v1"))
    ap.add_argument("--vector", default=os.path.join(REPO, "vector_rag_baseline", "results", "v2_all_baselines",
                                                       "per_question_all.jsonl"))
    ap.add_argument("--golden", default=os.path.join(REPO, "vector_rag_baseline", "data", "questions_v2.jsonl"))
    ap.add_argument("--train", default=os.path.join(HERE, "synthetic", "fin10k_v1", "train.json"))
    ap.add_argument("--out", default=os.path.join(HERE, "results", "finetuned_fin10k_v1", "plots"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    ft_rows = jl(os.path.join(a.run, "eval_golden_v2", "per_question.jsonl"))
    zs_rows = jl(os.path.join(a.zero_shot, "per_question.jsonl"))
    ep, train, val, best = fig1(a.run, a.out)
    print("epochs", ep, "best", best, "val MRR", [val[e]["document_mrr"] for e in ep])
    zs, ft, vec = fig2(ft_rows, zs_rows, jl(a.vector), a.out)
    print("Hit@10 ALL: zero-shot", round(zs["ALL"], 2), "fine-tuned", round(ft["ALL"], 2), "vector", round(vec["ALL"], 2))
    fig3(os.path.join(a.run, "eval_golden_v2", "layers.jsonl"), os.path.join(a.zero_shot, "layers.jsonl"), a.out)
    rows = fig4(ft_rows, zs_rows, jl(os.path.join(a.run, "eval_relation_dev_zero-shot", "per_question.jsonl")),
                jl(os.path.join(a.run, "eval_relation_dev_fine-tuned", "per_question.jsonl")), a.golden, a.train, a.out)
    for r in rows:
        print(" ", r[0].replace("\n", " "), f"n={r[3]} {r[1]:.2f} -> {r[2]:.2f}")
    print("wrote", sorted(os.listdir(a.out)), "to", a.out)


if __name__ == "__main__":
    main()

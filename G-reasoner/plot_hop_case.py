"""Figure for the hop analysis case study (E7), from hop_case.py outputs.

One heatmap panel per model (zero-shot, fine-tuned), side by side: rows are the nodes on the question's chain,
its gold chunks and distractors; columns are GNN layers 0..6 (layer 6 = the model's output). A cell shows the
node's rank among nodes of its own type after that layer (1 = best), as a number and as colour (one blue
ramp, darker = higher rank, log scale). Row labels give hops from the anchor (the chain) and from the
nearest start node (the shortcut). Also writes the same numbers as a markdown table (the table view).

    python plot_hop_case.py results/hop_case/zero_shot_v2_q10.json results/hop_case/finetuned_v2_q10.json \
        --out results/hop_case/fig_hop_case_v2_q10
"""
import argparse
import json
import math
import os

# Sequential blue ramp (light -> dark), from the dataviz reference palette; rank 1 = darkest.
RAMP = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6", "#256abf",
        "#1c5cab", "#184f95", "#104281", "#0d366b"]
SURFACE, INK, INK_MUTED, INK_ON_DARK = "#fcfcfb", "#0b0b0b", "#5f5e5a", "#fcfcfb"
MAX_RANK = 2000  # colour scale ends here (more than the 1,855 document nodes)

# What each gold chunk says, for row labels (checked against data/chunks/chunks.jsonl).
CHUNK_NOTES = {
    "JNJ_FY2025_ITEM1_0011": "DARZALEX licence from Genmab",
    "JNJ_FY2025_ITEM1_0001": "Innovative Medicine covers Oncology",
    "JNJ_FY2025_ITEM7_0012": "IM sales by product: $60,401M",
    "JNJ_FY2025_ITEM7_0032": "segment earnings: IM $60,401M",
    "JNJ_FY2025_ITEM8_0120": "sales note: IM $60,401M",
    "JNJ_FY2025_ITEM8_0126": "segment P&L: IM $60,401M",
}
ROLE_TITLE = {"chain": "Chain", "gold chunk": "Gold chunks", "distractor": "Distractor"}


def short(name, rec):
    if rec["type"] == "document":
        note = CHUNK_NOTES.get(name)
        return f"{name.split('_', 2)[-1]}  {note}" if note else name
    return (name.replace("Innovative Medicine (JNJ)", "Innovative Medicine").replace(" million", "M")
            .replace(" (JNJ)", ""))


def colour(rank):
    x = math.log(min(rank, MAX_RANK)) / math.log(MAX_RANK)          # 0 = rank 1, 1 = rank >= MAX_RANK
    return RAMP[len(RAMP) - 1 - round(x * (len(RAMP) - 1))]


def text_colour(rank):
    x = math.log(min(rank, MAX_RANK)) / math.log(MAX_RANK)
    return INK_ON_DARK if x < 0.5 else INK


def rows_of(case):
    order = case["tracked_order"]
    return sorted(order, key=lambda n: (["chain", "gold chunk", "distractor"].index(case["tracked"][n]["role"]),
                                        order.index(n)))


def write_table(cases, path):
    lines = []
    for c in cases:
        n_layers = len(next(iter(c["tracked"].values()))["layers"])
        lines += [f"### {c['name']} on {c['qid']}", "", c["question"], "",
                  f"Start nodes: {', '.join(c['start_nodes'])}. Rank among nodes of the same type after each layer "
                  f"(1 = best); hops from {c['anchor']} / from the nearest start node.", "",
                  "| Node | Role | Type | Hops | " + " | ".join(f"L{l}" for l in range(n_layers)) + " |",
                  "|---|---|---|---|" + "---|" * n_layers]
        for n in rows_of(c):
            r = c["tracked"][n]
            lines.append(f"| {n} | {r['role']} | {r['type']} | {r['hops_from_anchor']} / {r['hops_from_start']} | "
                         + " | ".join(str(x["rank"]) for x in r["layers"]) + " |")
        lines += ["", "Top documents after each layer: " + "; ".join(
            f"L{l}: {', '.join(d)}" for l, d in enumerate(c["top_docs_by_layer"])), ""]
    open(path, "w", encoding="utf-8").write("\n".join(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cases", nargs="+", help="hop_case.py outputs, one per model, in panel order")
    ap.add_argument("--out", required=True, help="path without extension; writes .png, .pdf and .md")
    a = ap.parse_args()

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap, LogNorm

    cases = [json.load(open(p, encoding="utf-8")) for p in a.cases]
    if len({c["qid"] for c in cases}) != 1:
        raise SystemExit("all inputs must be the same question")
    rows = rows_of(cases[0])
    if any(rows_of(c) != rows for c in cases):
        raise SystemExit("inputs track different nodes; rerun hop_case.py with the same version")
    n_layers = len(cases[0]["tracked"][rows[0]]["layers"])
    ref = cases[0]["tracked"]

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
                         "axes.labelcolor": INK, "xtick.color": INK_MUTED, "ytick.color": INK})
    fig_w = 4.2 + 3.1 * len(cases)
    fig, axes = plt.subplots(1, len(cases), figsize=(fig_w, 0.42 * len(rows) + 2.0), sharey=True,
                             facecolor=SURFACE, squeeze=False)
    axes = axes[0]
    gap = 0.06  # surface gap between cells
    for ax, c in zip(axes, cases):
        ax.set_facecolor(SURFACE)
        for y, n in enumerate(rows):
            for x, cell in enumerate(c["tracked"][n]["layers"]):
                rk = cell["rank"]
                ax.add_patch(plt.Rectangle((x - 0.5 + gap / 2, y - 0.5 + gap / 2), 1 - gap, 1 - gap,
                                           facecolor=colour(rk), edgecolor="none"))
                ax.text(x, y, f"{rk:,}", ha="center", va="center", fontsize=8.5, color=text_colour(rk))
        ax.set_xlim(-0.5, n_layers - 0.5)
        ax.set_ylim(len(rows) - 0.5, -0.5)
        ax.set_xticks(range(n_layers))
        ax.set_xticklabels([f"L{l}" if l < n_layers - 1 else f"L{l}\noutput" for l in range(n_layers)])
        ax.xaxis.tick_top()
        ax.tick_params(length=0)
        for s in ax.spines.values():
            s.set_visible(False)
        label = {"g-reasoner": "Zero-shot", "g-reasoner-ft": "Fine-tuned"}.get(c["name"], c["name"])
        ax.set_title(label, fontsize=11, fontweight="bold", pad=28)
        # group separators
        for y in range(1, len(rows)):
            if ref[rows[y]]["role"] != ref[rows[y - 1]]["role"]:
                ax.axhline(y - 0.5, color=INK_MUTED, linewidth=0.8)

    labels = []
    for n in rows:
        r = ref[n]
        star = "  [start]" if r["is_start"] else ""
        labels.append(f"{short(n, r)}{star}   ({r['hops_from_anchor']} / {r['hops_from_start']})")
    axes[0].set_yticks(range(len(rows)))
    axes[0].set_yticklabels(labels, fontsize=9)
    # group names, left of the first panel
    for y, n in enumerate(rows):
        if y == 0 or ref[n]["role"] != ref[rows[y - 1]]["role"]:
            axes[0].annotate(ROLE_TITLE[ref[n]["role"]], xy=(0, y - 0.5), xycoords=("figure fraction", "data"),
                             xytext=(8, 0), textcoords="offset points", va="top", fontsize=9,
                             fontweight="bold", color=INK_MUTED)

    c0 = cases[0]
    height = fig.get_size_inches()[1]
    fig.subplots_adjust(top=1 - 1.25 / height, bottom=0.55 / height)
    fig.text(0.01, 1 - 0.12 / height, f"How G-reasoner hops, layer by layer ({c0['qid']})", ha="left", va="top",
             fontsize=13, fontweight="bold")
    fig.text(0.01, 1 - 0.42 / height, c0["question"], ha="left", va="top", fontsize=10, color=INK_MUTED)
    fig.text(0.01, 0.005,
             f"Cell = rank among nodes of the same type after each GNN layer (1 = best; darker = higher). "
             f"(a / s) = hops from {c0['anchor']} / from the nearest start node. "
             f"Start nodes: {', '.join(c0['start_nodes'])}.", fontsize=8, color=INK_MUTED, ha="left", va="bottom",
             wrap=True)
    sm = plt.cm.ScalarMappable(cmap=ListedColormap(RAMP[::-1]), norm=LogNorm(1, MAX_RANK))
    cb = fig.colorbar(sm, ax=list(axes), fraction=0.025, pad=0.02)
    cb.set_ticks([1, 10, 100, 1000])
    cb.set_ticklabels(["1", "10", "100", "1,000"])
    cb.ax.tick_params(colors=INK_MUTED, length=0)
    cb.set_label("rank within type (log)", color=INK_MUTED)
    cb.outline.set_visible(False)
    cb.ax.invert_yaxis()

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    fig.savefig(a.out + ".png", dpi=200, facecolor=SURFACE, bbox_inches="tight")
    fig.savefig(a.out + ".pdf", facecolor=SURFACE, bbox_inches="tight")
    write_table(cases, a.out + ".md")
    print("wrote", a.out + ".png", a.out + ".pdf", a.out + ".md")


if __name__ == "__main__":
    main()

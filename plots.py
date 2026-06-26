"""Generate the two figures into paper/figures/ from the measured numbers (no recompute).
  python plots.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path(__file__).resolve().parent / "paper" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
MODELS = ["sonnet", "haiku", "gpt-4o-mini", "qwen-72b", "llama-70b"]

# --- Fig: confound (grant rate per framing; source-invariant confident block vs collapsed hedged block)
FRAMINGS = [
    ("confident",          [0.81, 0.81, 0.81, 0.81, 0.81], "confident"),
    ("+ attribution",      [0.81, 0.47, 0.79, 0.81, 0.81], "confident"),
    ("+ forged authority", [0.81, 0.81, 0.81, 0.81, 0.81], "confident"),
    ('"probably"',         [0.00, 0.00, 0.40, 0.40, 0.24], "hedged"),
    ('"rumor has it"',     [0.00, 0.00, 0.40, 0.00, 0.00], "hedged"),
    ("+ attribution ",     [0.00, 0.00, 0.00, 0.00, 0.00], "hedged"),
    ('"never verified"',   [0.00, 0.01, 0.00, 0.00, 0.00], "hedged"),
]
labels = [f[0] for f in FRAMINGS]
means = [sum(f[1]) / len(f[1]) for f in FRAMINGS]
colors = ["#c0392b" if f[2] == "confident" else "#2471a3" for f in FRAMINGS]
y = range(len(FRAMINGS))[::-1]

fig, ax = plt.subplots(figsize=(3.3, 2.4))
ax.barh(list(y), means, color=colors, height=0.66, zorder=2)
for i, f in zip(y, FRAMINGS):                       # per-model points
    ax.scatter(f[1], [i] * len(f[1]), s=7, color="black", alpha=0.45, zorder=3)
ax.set_yticks(list(y)); ax.set_yticklabels(labels)
ax.set_xlim(0, 1); ax.set_xlabel("unauthorized-grant rate")
ax.axhspan(3.5, 6.5, color="#c0392b", alpha=0.06, zorder=0)   # confident block tint
ax.axhspan(-0.5, 3.5, color="#2471a3", alpha=0.05, zorder=0)  # hedged block tint
ax.text(0.5, 6.7, "confident: source varies, grant holds", ha="center", va="bottom",
        fontsize=7, color="#c0392b")
ax.text(0.5, -0.85, "hedged: any hedge collapses it", ha="center", va="top",
        fontsize=7, color="#2471a3")
ax.set_ylim(-1.6, 7.6)
fig.tight_layout(); fig.savefig(OUT / "confound.pdf", bbox_inches="tight", pad_inches=0.03)
plt.close(fig)

# --- Fig: extractor variation behind mem0. De-hedging (the load-bearing variable) is uniformly high;
# the attribution-based laundering metric undercounts it (esp. gpt-4o-mini: de-hedges 4/5, launders 2/5).
EXN = ["sonnet", "gpt-4o-mini", "llama-70b", "qwen-72b"]
DEHEDGE = [4, 4, 5, 5]   # /5
LAUNDER = [5, 2, 5, 4]   # /5
import numpy as np
x = np.arange(len(EXN)); w = 0.38
fig, ax = plt.subplots(figsize=(3.3, 2.0))
ax.bar(x - w/2, [d/5 for d in DEHEDGE], w, color="#c0392b", label="de-hedged (confident)", zorder=2)
ax.bar(x + w/2, [l/5 for l in LAUNDER], w, color="#e8b4ae", label="laundered (no attribution)", zorder=2)
for i in range(len(EXN)):
    ax.text(i - w/2, DEHEDGE[i]/5 + 0.03, f"{DEHEDGE[i]}/5", ha="center", fontsize=7)
    ax.text(i + w/2, LAUNDER[i]/5 + 0.03, f"{LAUNDER[i]}/5", ha="center", fontsize=7)
ax.set_ylim(0, 1.32); ax.set_ylabel("rate"); ax.set_xticks(x); ax.set_xticklabels(EXN)
ax.legend(fontsize=6.5, loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.16))
plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
fig.tight_layout(); fig.savefig(OUT / "extractor.pdf", bbox_inches="tight", pad_inches=0.03)
plt.close(fig)

print("wrote", OUT / "confound.pdf", "and", OUT / "extractor.pdf")

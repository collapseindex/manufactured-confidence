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

# --- Fig: extractor variation (laundering rate behind mem0; same de-hedging across extractors)
EX = [("sonnet", 1.0), ("qwen-72b", 1.0), ("gpt-4o-mini", 0.6), ("llama-70b", 0.6)]
fig, ax = plt.subplots(figsize=(3.3, 1.9))
ax.bar([e[0] for e in EX], [e[1] for e in EX], color="#c0392b", width=0.6, zorder=2)
ax.set_ylim(0, 1.05); ax.set_ylabel("laundering rate")
ax.axhline(1.0, ls=":", lw=0.7, color="gray")
for i, e in enumerate(EX):
    ax.text(i, e[1] + 0.03, f"{int(e[1]*5)}/5", ha="center", fontsize=8)
ax.set_title("extractor behind mem0", fontsize=9)
plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
fig.tight_layout(); fig.savefig(OUT / "extractor.pdf"); plt.close(fig)

print("wrote", OUT / "confound.pdf", "and", OUT / "extractor.pdf")

# confident-cascade

**A single confidently-wrong memory silently cascades through an agent loop, on every major LLM — and
the obvious fix doesn't work.**

When an agent carries a wrong conclusion forward in memory and a later step *computes with* it, the
error doesn't stay local: it propagates, silently and confidently, through the entire downstream chain.
This is the deployment-relevant failure mode of LLM memory, and it has a sharp, counterintuitive
structure:

1. **The harm is universal.** A wrong carried subtotal propagates confident-wrong through *all*
   downstream steps (blast radius 5/5) on Anthropic, OpenAI, Meta, and Alibaba models alike.
2. **The intuitive fix fails universally.** Tagging the memory *"unverified"* — the first thing an
   engineer would try — does **nothing** (≈5/5 on every model). Agents treat carried values as inputs
   to *compute with*, not claims to *vouch for*, so a passive uncertainty label is invisible to the
   computation.
3. **Only an active instruction works — and it works universally.** Telling the agent to *distrust* the
   value and treat dependent results as unverifiable collapses the blast radius to **0/5**, on every
   model.

The lever is the gap between a **label** and an **instruction**: marking memory uncertain is not enough;
you must change the agent's *procedural* behavior. That gap is universal, counterintuitive, and a
concrete deployment spec.

This is the safety follow-up to the
[evidence-space condition](https://github.com/collapseindex/evidence-space) and to
[Reclaim Evaluation](https://arxiv.org/abs/2606.25449): reclaim showed lossy memory is *worse than
empty*; this shows *why it is dangerous in an agent loop* (it cascades) and *what stops it* (an active
distrust instruction, not a passive tag).

## Findings so far

**The failure mode is steerable (single answer, no source to recompute).** Parrot = confident-wrong
rate; n=16:

| model | assertive | unverified | distrust |
|---|---|---|---|
| sonnet | 1.00 | 0.38 | 0.00 |
| haiku | 0.50 | 0.00 | 0.00 |
| llama-70b | 1.00 | 0.81 | 0.00 |
| gpt-4o-mini | 0.50 | 0.44 | 0.00 |
| qwen-72b | 0.75 | 0.00 | 0.00 |

Default disposition and cue-sensitivity vary by provider (Llama-70b ignores a mild tag), but explicit
distrust drives confident-wrong to 0 everywhere.

**The cascade, and the label-vs-instruction gap** (blast radius / 5 downstream steps, n=8–10):

| model | assertive | unverified | distrust |
|---|---|---|---|
| sonnet | 5.0 | 5.0 | 0.0 |
| haiku | 5.0 | 5.0 | 0.0 |
| llama-70b | 5.0 | 4.9 | 0.0 |
| gpt-4o-mini | 5.0 | 5.0 | 0.0 |
| qwen-72b | 5.0 | 5.0 | 0.0 |

## Status

Constructed tasks so far. The next step is to push the cascade **out of toy territory** — a realistic
multi-step agent task with checkable state — to show the harm and the fix on something that reads as a
real deployment, not a running total.

## Run

```bash
pip install requests anthropic
echo "OPENROUTER_API_KEY=..." >> .env
echo "ANTHROPIC_API_KEY=..." >> .env
python framing.py --model sonnet
python cascade.py  --model sonnet
```

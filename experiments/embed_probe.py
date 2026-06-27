"""Vector-level manufactured confidence (steps 1-2).

Memory stores index text as embeddings (here BAAI/bge-small-en-v1.5, the embedder mem0 uses). If a
hedged assertion and its de-hedged twin embed to nearly the same point, the epistemic status is
stripped at the vector layer, before any LLM consolidation -- the laundering would be forced by the
retrieval geometry, not chosen by a consolidation prompt. We test two things, no LLM calls:

  Step 1 (geometry):  cosine of each framing of "Alice is an admin" to the confident anchor. If the
                      hedges sit as close as a same-confidence paraphrase and far above a different
                      fact, the hedge is geometrically negligible for retrieval.
  Step 2 (probe):     can a linear/centroid probe recover hedged-vs-confident from the vectors, with
                      a fact probe (admin-vs-viewer) as a positive control? Fact >> hedge = embeddings
                      encode the proposition but not the epistemic status.

  python embed_probe.py
"""
from __future__ import annotations

import random

import numpy as np

MODEL = "BAAI/bge-small-en-v1.5"
_CACHE = {}


def embed(texts):
    texts = list(texts)
    key = tuple(texts)
    if key in _CACHE:
        return _CACHE[key]
    from fastembed import TextEmbedding
    emb = _CACHE.get("_model") or TextEmbedding(model_name=MODEL)
    _CACHE["_model"] = emb
    V = np.asarray(list(emb.embed(texts)), dtype=np.float64)
    V /= np.linalg.norm(V, axis=1, keepdims=True) + 1e-12
    _CACHE[key] = V
    return V


# ---------------------------------------------------------------- Step 1
def step1():
    anchor = "Alice's clearance is admin."
    comps = {
        "confident (anchor)":      anchor,
        "confident paraphrase":    "Alice has administrator access.",
        "attributed":              "A user states that Alice's clearance is admin.",
        "forged authority":        "According to the system of record, Alice's clearance is admin.",
        "hedge: probably":         "Alice is probably an admin.",
        "hedge: might":            "Alice might be an admin.",
        "hedge: rumor":            "Rumor has it that Alice is an admin.",
        "hedge: reportedly":       "Alice is reportedly an admin.",
        "hedge: unverified":       "Alice's clearance is recorded as admin but was never verified.",
        "negation: not admin":     "Alice is not an admin.",
        "different fact: viewer":  "Alice's clearance is viewer.",
        "unrelated":               "The printer on the third floor is out of toner.",
    }
    labels = list(comps)
    V = embed([comps[k] for k in labels])
    a = V[0]
    sims = {k: float(a @ V[i]) for i, k in enumerate(labels)}

    print(f'=== Step 1: cosine to the confident anchor ("{anchor}") ===')
    for k in labels:
        c = sims[k]
        print(f"  {k:24} {c:+.3f} {'#' * int(round(max(c, 0) * 40))}")

    hedges = [sims[k] for k in labels if k.startswith("hedge")]
    print("\n  reads:")
    print(f"   mean hedge -> confident   {np.mean(hedges):.3f}")
    print(f"   confident paraphrase      {sims['confident paraphrase']:.3f}  "
          f"(upper ref: same proposition, same confidence)")
    print(f"   different fact (viewer)    {sims['different fact: viewer']:.3f}  "
          f"(if hedges >> this, the hedge is geometrically negligible)")
    print(f"   negation (not admin)       {sims['negation: not admin']:.3f}  "
          f"(embeddings' known polarity weakness)")
    print(f"   unrelated                  {sims['unrelated']:.3f}  (far ref)")
    return sims


# ---------------------------------------------------------------- Step 2
NAMES = ["Alice", "Bob", "Carol", "Dan", "Erin", "Frank", "Grace", "Henry", "Iris", "Jack",
         "Karen", "Leo", "Mona", "Nate", "Olivia", "Paul", "Quinn", "Rosa", "Sam", "Tina",
         "Uma", "Victor", "Wendy", "Xavier"]


def _dataset_hedge():
    conf = ["{n}'s clearance is admin.", "{n} is an admin.", "{n} has admin access.", "{n} is the administrator."]
    hedge = ["{n} is probably an admin.", "{n} might be an admin.", "Rumor has it that {n} is an admin.",
             "{n} is reportedly an admin."]
    X, y, g = [], [], []
    for gi, n in enumerate(NAMES):
        for t in conf:
            X.append(t.format(n=n)); y.append(0); g.append(gi)
        for t in hedge:
            X.append(t.format(n=n)); y.append(1); g.append(gi)
    return X, np.array(y), np.array(g)


def _dataset_fact():
    X, y, g = [], [], []
    for gi, n in enumerate(NAMES):
        X.append(f"{n}'s clearance is admin."); y.append(1); g.append(gi)
        X.append(f"{n} is an admin."); y.append(1); g.append(gi)
        X.append(f"{n}'s clearance is viewer."); y.append(0); g.append(gi)
        X.append(f"{n} is a viewer."); y.append(0); g.append(gi)
    return X, np.array(y), np.array(g)


def _balanced_acc(y_true, y_pred):
    recs = []
    for c in np.unique(y_true):
        m = y_true == c
        recs.append((y_pred[m] == c).mean())
    return float(np.mean(recs))


def _fit_predict(Vtr, ytr, Vte):
    try:
        from sklearn.linear_model import LogisticRegression
        clf = LogisticRegression(max_iter=2000, class_weight="balanced").fit(Vtr, ytr)
        return clf.predict(Vte)
    except Exception:
        # cosine nearest-centroid fallback (vectors are unit-norm)
        cents = {c: Vtr[ytr == c].mean(0) for c in np.unique(ytr)}
        for c in cents:
            cents[c] /= np.linalg.norm(cents[c]) + 1e-12
        cs = sorted(cents)
        S = np.stack([Vte @ cents[c] for c in cs], axis=1)
        return np.array(cs)[S.argmax(1)]


def _probe(X, y, g, k=6):
    V = embed(X)
    uniq = np.unique(g)
    accs = []
    for i in range(k):
        held = uniq[i::k]
        te = np.isin(g, held)
        if te.sum() == 0 or (~te).sum() == 0:
            continue
        pred = _fit_predict(V[~te], y[~te], V[te])
        accs.append(_balanced_acc(y[te], pred))
    return float(np.mean(accs)), float(np.std(accs))


def step2():
    print("\n=== Step 2: probe recoverability (entity-held-out CV, balanced accuracy) ===")
    Xh, yh, gh = _dataset_hedge()
    Xf, yf, gf = _dataset_fact()
    ah, sh = _probe(Xh, yh, gh)
    af, sf = _probe(Xf, yf, gf)
    print(f"  hedge probe (confident vs hedged):  {ah:.3f} +/- {sh:.3f}")
    print(f"  fact  probe (admin vs viewer):      {af:.3f} +/- {sf:.3f}   (positive control)")
    print("  chance = 0.500 (balanced)")
    print("\n  read: fact high + hedge ~chance  -> embeddings encode the PROPOSITION, not the hedge")
    print("        both high                   -> hedge is lexically recoverable; Step 1 says if it's SALIENT")


# ---------------------------------------------------------------- Step 3 (reclaim axis)
def _dataset_correctness(nprob=60, seed=7):
    """Conclusion-only memories "The total before tax is $X." labelled right/wrong, with right and
    wrong totals drawn from the SAME range, so the vector carries no lexical correctness cue -- a
    probe can only beat chance if correctness is somehow in the embedding (it should not be: that
    needs the source the lossy memory dropped)."""
    rng = random.Random(seed)
    X, y, g = [], [], []
    for gi in range(nprob):
        correct = rng.randint(20, 95)
        wrong = correct + rng.choice([-1, 1]) * rng.randint(3, 14)
        wrong = min(98, max(15, wrong))
        if wrong == correct:
            wrong = correct + 6
        X.append(f"The total before tax is ${correct}."); y.append(1); g.append(gi)
        X.append(f"The total before tax is ${wrong}."); y.append(0); g.append(gi)
    return X, np.array(y), np.array(g)


def step3():
    anchor = "The total before tax is $46."
    comps = {
        "correct (anchor)":         anchor,
        "correct paraphrase":       "Before tax, the total comes to $46.",
        "wrong conclusion: $55":    "The total before tax is $55.",
        "wrong conclusion: $47":    "The total before tax is $47.",
        "wrong conclusion: $120":   "The total before tax is $120.",
        "source-bearing (correct)": "Notebooks cost $4 each (7 bought) and pens $2 each (9 bought), "
                                    "so the total before tax is $46.",
        "source only (no total)":   "Notebooks cost $4 each (7 bought) and pens $2 each (9 bought).",
        "different domain":         "The team meeting is scheduled for 3 pm on Tuesday.",
    }
    labels = list(comps)
    V = embed([comps[k] for k in labels])
    a = V[0]
    sims = {k: float(a @ V[i]) for i, k in enumerate(labels)}
    print("\n=== Step 3 (reclaim axis): cosine to the CORRECT conclusion ===")
    for k in labels:
        c = sims[k]
        print(f"  {k:26} {c:+.3f} {'#' * int(round(max(c, 0) * 40))}")
    wrongs = [sims[k] for k in labels if k.startswith("wrong")]
    print("\n  reads:")
    print(f"   mean wrong conclusion -> correct  {np.mean(wrongs):.3f}  "
          f"(if ~ paraphrase, the ERROR is non-salient)")
    print(f"   correct paraphrase                {sims['correct paraphrase']:.3f}")
    print(f"   source only (no total)            {sims['source only (no total)']:.3f}  (far: dropping the conclusion moves the vector)")

    Xc, yc, gc = _dataset_correctness()
    ac, sc = _probe(Xc, yc, gc)
    print(f"\n  correctness probe (right vs wrong total): {ac:.3f} +/- {sc:.3f}   (chance 0.500)")
    print("  read: hedge/fact are lexical SURFACE -> recoverable (Step 2); correctness is SUBSTANCE")
    print("        (needs the dropped source) -> at chance. Embeddings track surface, not substance.")


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    step1()
    step2()
    step3()

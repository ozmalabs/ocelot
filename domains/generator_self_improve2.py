"""Brick 6 — RECURSIVE self-improvement (turn 2): does the loop COMPOUND?

Turn 1 (domains/generator_self_improve.py) derived a single-feature
output-distance guide (AUC 0.84) from the UNGUIDED generator's traces and moved
the bound out (4-var a*b+c*d: timeout -> 8s; 5.3x fewer explored on a*a+b*b).
But the deep recursive step — having brick 6 SYNTHESIZE its own scorer Term —
FAILED at the narrow unguided bound (no clean fit; useful/not-useful overlap).

Turn 2's hypothesis (the central test of the recursive thesis):
  (a) Turn 1's WIDER bound (the guided generator) now solves BIGGER training
      targets the UNGUIDED brick-6 could NOT (size 8-9, 4-5 vars). Those richer
      solutions yield RICHER TRACES — the compounding premise: turn 1's output
      is turn 2's input.
  (b) With a RICHER FEATURE VOCABULARY per explored term (not just one distance)
      the self-synthesis that failed before may now LAND, and/or a richer
      trace-fit guide may SEPARATE BETTER than turn-1's 0.84 — and, applied,
      move the bound FURTHER (solve more, explore less) on HELD-OUT harder
      targets.

This module is ADDITIVE: it reuses turn-1 functions (output_distance,
_useful_signatures, _subterm_dicts, _term_from_dict) and brick-6 `synthesize`
(guide=None and the turn-1 guide path are both untouched). Weightless: every
feature is a graph-native term behaviour; both guides are trace-fit thresholds
or a synthesized Term-tree. No trained net, no LLM (contrast GRAM's learned
LPRM).
"""

from __future__ import annotations

import bisect
from typing import Any, Callable, Sequence

from domains.generator import synthesize, _signature, _num
from domains.generator_self_improve import (
    output_distance, _useful_signatures, _subterm_dicts, _term_from_dict,
    _sig_to_nums,
)


# ---------------------------------------------------------------------------
# 1. RICHER TRACES via the turn-1 guide.
#
# Run the turn-1 GUIDED generator (output-distance guide, tuned K) on BIGGER
# training targets the UNGUIDED brick-6 cannot finish. Each target we report:
# whether the unguided run solved it (the bound that turn 0 had) and whether
# the guided run did (turn 1's wider bound). Traces come from the GUIDED solve —
# those traces are only AVAILABLE because turn 1 widened the bound.
# ---------------------------------------------------------------------------

def _solve(substrate, examples, max_size, timeout_s, guide=None, guide_beam=None,
           ops=None):
    kw = dict(max_size=max_size, timeout_s=timeout_s, return_trace=True)
    if ops:
        kw["ops"] = ops
    if guide is not None:
        kw.update(guide=guide, guide_beam=guide_beam)
    return synthesize(substrate, examples, **kw)


def harvest_richer_traces(substrate, training_specs, guide, guide_beam=30,
                          max_size=9, timeout_s=120.0):
    """For each BIGGER training target, run UNGUIDED (turn-0 bound) and the
    turn-1 GUIDED generator. Report which the guide UNLOCKED for trace-harvest,
    and harvest the explored-term rows from the GUIDED solve.

    Returns {rows, unlocked, summary}:
      rows     — per explored distinct-behaviour term: feature dict (filled in
                 step 2) + useful label, from the GUIDED solves.
      unlocked — [(name, unguided_solved, guided_solved)] : compounding premise.
    """
    rows: list[dict] = []
    summary = []
    unlocked = []
    for name, examples in training_specs:
        envs = [env for env, _ in examples]
        target = tuple(_num(out) for _, out in examples)

        # turn-0 bound: unguided. Short-ish timeout — we just want to know if
        # turn-0 could reach this target's traces at all.
        ru = _solve(substrate, examples, max_size, timeout_s)
        u_solved = ru["fits"]

        # turn-1 bound: guided.
        rg = _solve(substrate, examples, max_size, timeout_s, guide, guide_beam)
        g_solved = rg["fits"]

        unlocked.append((name, u_solved, g_solved))
        summary.append({
            "name": name,
            "unguided": (u_solved, ru["explored"], ru["halt_reason"],
                         ru["elapsed_s"]),
            "guided": (g_solved, rg["explored"], rg.get("size"),
                       rg["elapsed_s"]),
        })

        if not g_solved:
            continue  # no solution -> no useful set -> skip trace harvest

        useful = _useful_signatures(substrate, rg["term"], envs)
        trace = rg["trace"]  # {sig: (size, term)}
        # Build the richer feature rows from this solved target's trace.
        rows.extend(_feature_rows(trace, target, useful, name))

    return {"rows": rows, "unlocked": unlocked, "summary": summary}


# ---------------------------------------------------------------------------
# 2. RICHER FEATURE VOCABULARY per explored term.
#
# Per term (a node in the trace), compute graph-native behaviour features:
#   - dist        : best normalised output-distance to the target (turn-1 feat).
#   - exact_hits  : how many example outputs it hits EXACTLY (== target entry).
#   - near_hits   : how many it hits within a small relative tolerance.
#   - size        : term size (MDL).
#   - frac_exact  : exact_hits / n_examples (scale-free).
#   - frac_near   : near_hits  / n_examples.
# "improves-on-best-subterm" needs per-term parent/child wiring which the trace
# (signature->(size,term)) does not preserve cheaply; we instead expose a
# size-normalised closeness `dist_per_size` capturing "promise per unit MDL"
# (a denser term that is no closer is less promising). These are all functions
# of a term's OUTPUTS — graph-native, weightless.
# ---------------------------------------------------------------------------

def _per_example_hits(sig: tuple, target: tuple[float, ...]):
    """(exact_hits, near_hits) of a term's output signature vs target."""
    nums = _sig_to_nums(sig)
    if len(nums) != len(target):
        return 0, 0
    exact = 0
    near = 0
    for got, want in zip(nums, target):
        if got != got or got in (float("inf"), float("-inf")):
            continue
        if abs(got - want) <= 1e-9:
            exact += 1
            near += 1
        elif abs(got - want) <= 0.10 * (1.0 + abs(want)):
            near += 1
    return exact, near


def _feature_rows(trace: dict, target: tuple, useful: set, name: str):
    rows = []
    n = len(target)
    for sig, (size, _term) in trace.items():
        dist = output_distance(sig, target)
        exact, near = _per_example_hits(sig, target)
        rows.append({
            "name": name,
            "dist": dist,
            "size": float(size),
            "exact": float(exact),
            "near": float(near),
            "frac_exact": exact / n if n else 0.0,
            "frac_near": near / n if n else 0.0,
            "dist_per_size": (dist / size) if dist != float("inf") else float("inf"),
            "useful": sig in useful,
        })
    return rows


FEATURES = ("dist", "size", "exact", "near", "frac_exact", "frac_near",
            "dist_per_size")
# Features where SMALLER => more promising (a distance); the rest LARGER =>
# more promising (a hit count). Used to orient single-feature AUC + the guide.
SMALLER_BETTER = {"dist", "size", "dist_per_size"}


# ---------------------------------------------------------------------------
# Per-feature separation (single-feature AUC) — to RANK features by how well
# each separates useful from not-useful in the agent's own traces.
# ---------------------------------------------------------------------------

def _auc_lower_better(use, notu):
    """AUC = P(useful value < not-useful value) (lower-is-better feature)."""
    if not use or not notu:
        return float("nan")
    snot = sorted(notu)
    n_not = len(snot)
    wins = 0.0
    for d in use:
        lo = bisect.bisect_left(snot, d)
        hi = bisect.bisect_right(snot, d)
        gt = n_not - hi
        eq = hi - lo
        wins += gt + 0.5 * eq
    return wins / (len(use) * n_not)


def feature_aucs(rows):
    """Single-feature AUC for every feature (oriented so >0.5 = separates,
    useful is the 'positive' class). Returns {feat: auc}."""
    out = {}
    for f in FEATURES:
        use = [r[f] for r in rows if r["useful"] and r[f] != float("inf")]
        notu = [r[f] for r in rows if not r["useful"] and r[f] != float("inf")]
        if f in SMALLER_BETTER:
            out[f] = _auc_lower_better(use, notu)
        else:
            # larger better: flip
            out[f] = _auc_lower_better(notu, use)
    return out


# ---------------------------------------------------------------------------
# 3a. RICHER DERIVED guide — a trace-FIT combination of features.
#
# Weightless + derived from the agent's own data: we pick the top-ranked
# features by single-feature AUC and combine them into a single promise SCORE
# whose per-feature thresholds + sign are taken FROM the traces (class means).
# The score is a normalised distance in feature space to the useful-class
# centroid, scaled by each feature's discriminability (its |AUC-0.5|). No
# trained net, no gradient — just class statistics of the agent's own traces.
#
# The guide signature is the same (sig, target) -> score brick-6 expects, so it
# drops straight into `guide=`/`guide_beam=`. Smaller score = more promising.
# ---------------------------------------------------------------------------

def fit_richer_guide(rows, top_k_features=4):
    """Fit a multi-feature promise score from the traces. Returns a callable
    guide(sig, target)->score AND a description dict."""
    aucs = feature_aucs(rows)
    # rank features by discriminability
    ranked = sorted(FEATURES, key=lambda f: -abs((aucs[f] if aucs[f] == aucs[f]
                                                   else 0.5) - 0.5))
    chosen = [f for f in ranked if aucs[f] == aucs[f]][:top_k_features]

    # per-feature useful-class mean + spread (std) from the traces
    stats = {}
    for f in chosen:
        vals = [r[f] for r in rows if r["useful"] and r[f] != float("inf")]
        if not vals:
            continue
        mu = sum(vals) / len(vals)
        var = sum((x - mu) ** 2 for x in vals) / max(1, len(vals) - 1)
        sd = var ** 0.5 or 1.0
        w = abs((aucs[f] if aucs[f] == aucs[f] else 0.5) - 0.5)  # 0..0.5
        stats[f] = {"mu": mu, "sd": sd, "w": w}

    n_target_cache = {}

    def _features_of(sig, target):
        n = len(target)
        dist = output_distance(sig, target)
        exact, near = _per_example_hits(sig, target)
        # size is NOT recoverable from sig alone; brick-6's guide only gets
        # (sig, target). We approximate size's contribution by leaving it out
        # of the LIVE score (it is available at fit time for ranking, but the
        # live guide scores on output-behaviour features only — which is the
        # graph-native, sig-derivable subset). This keeps the guide honest:
        # it scores what the beam actually has access to.
        return {
            "dist": dist,
            "exact": float(exact),
            "near": float(near),
            "frac_exact": exact / n if n else 0.0,
            "frac_near": near / n if n else 0.0,
            "dist_per_size": dist,  # size unknown live -> proportional to dist
            "size": None,
        }

    def guide(sig, target):
        fv = _features_of(sig, target)
        score = 0.0
        any_used = False
        for f, st in stats.items():
            x = fv.get(f)
            if x is None or x == float("inf"):
                # unavailable live (e.g. size): skip, fall back to its absence
                continue
            z = abs(x - st["mu"]) / st["sd"]
            score += st["w"] * z
            any_used = True
        if not any_used:
            return output_distance(sig, target)
        return score

    return guide, {"chosen": chosen, "aucs": {f: aucs[f] for f in chosen},
                   "stats": {f: {"mu": stats[f]["mu"], "sd": stats[f]["sd"],
                                 "w": stats[f]["w"]}
                             for f in stats}}


# ---------------------------------------------------------------------------
# 3b. SELF-SYNTHESIZED guide — the deep recursive step, RETRIED with the richer
# features + the wider bound. Have brick-6 `synthesize` compose a scoring Term
# over the new feature variables predicting useful(0/1).
#
# Turn 1 gave it only (d, s). Turn 2 gives it the richer vocabulary
# (dist, frac_exact, frac_near, exact, near, dist_per_size) — the lever the
# failed self-synthesis lacked. If it LANDS, the generator literally wrote its
# own guide.
# ---------------------------------------------------------------------------

def try_synthesize_scorer_richer(substrate, rows, max_size=7, timeout_s=60.0,
                                 n_examples=40, feats=None):
    """Retry self-synthesis with the richer feature vocabulary. Returns the
    brick-6 result + the example set used. Honest: reports separable or not."""
    feats = feats or ("dist", "frac_exact", "frac_near", "dist_per_size")
    seen: dict[tuple, Any] = {}
    for r in rows:
        if any(r[f] == float("inf") for f in feats):
            continue
        key = tuple(round(r[f], 3) for f in feats)
        lab = 1 if r["useful"] else 0
        if key in seen and seen[key] != lab:
            seen[key] = None  # conflict -> unlearnable here
        elif key not in seen:
            seen[key] = lab
    pos = [(k, v) for k, v in seen.items() if v == 1]
    neg = [(k, v) for k, v in seen.items() if v == 0]
    conflicts = sum(1 for v in seen.values() if v is None)
    if not pos or not neg:
        return {"ok": False, "reason": "no_balanced_examples",
                "n_pos": len(pos), "n_neg": len(neg), "conflicts": conflicts}

    k = min(len(pos), len(neg), n_examples // 2)
    pos = pos[:k]
    neg = neg[:k]
    examples = []
    for key, lab in pos + neg:
        env = {f: float(val) for f, val in zip(feats, key)}
        examples.append((env, lab))

    r = synthesize(substrate, examples,
                   ops=("Lt", "Gt", "Lte", "Gte", "And", "Or", "Not",
                        "Plus", "Minus", "Times"),
                   consts=(0, 1, 2),
                   max_size=max_size, timeout_s=timeout_s)
    return {"ok": True, "result": r, "n_examples": len(examples),
            "n_pos": len(pos), "n_neg": len(neg), "conflicts": conflicts,
            "feats": feats}


# ---------------------------------------------------------------------------
# Held-out AUC of a (sig,target)->score guide on trace rows it was NOT fit on.
# ---------------------------------------------------------------------------

def guide_auc_rows(score_of_row, rows):
    """Generic: score_of_row(row)->lower-better promise. AUC over useful vs not."""
    use = [score_of_row(r) for r in rows if r["useful"]]
    notu = [score_of_row(r) for r in rows if not r["useful"]]
    use = [x for x in use if x == x and x != float("inf")]
    notu = [x for x in notu if x == x and x != float("inf")]
    return _auc_lower_better(use, notu)

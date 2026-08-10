"""Brick 6 — RECURSIVE self-improvement (turn 1): the generator improves its
OWN combinatorial search by deriving a search-guidance heuristic from its OWN
traces, weightlessly.

This is the generator pointed at its own bottleneck. Brick 6's unguided search
is size-ordered + observational-equivalence pruned, but UNGUIDED: at each size
it carries EVERY distinct behaviour forward, so the explored/distinct count
grows combinatorially (a*a+b*b: ~400k explored / ~40s). The search itself is
the bottleneck.

The fix is NOT a bigger machine, a trained net, or an LLM ranker (GRAM's
learned LPRM). It is a guide the agent DERIVES from its own search experience:
  - Run the unguided synthesizer on TRAINING targets it can already solve.
  - For each solved target, the SOLUTION and all its sub-terms (descendants)
    are the USEFUL terms; every other explored distinct-behaviour term is
    NOT-useful.
  - Record each explored term's candidate FEATURE: its output-distance to the
    target (plus size). VALIDATE whether the distance SEPARATES useful from
    not-useful (do useful terms sit closer to the target?). If it separates,
    the agent has LEARNED — from its own traces, no weights — that
    "closeness-to-target predicts solution-membership". That validated
    distance becomes the guide steering the beam (domains/generator.py's
    `guide` + `guide_beam`).

OPTIONAL: ask brick 6 ITSELF to synthesize a scoring Term-tree (features ->
useful 0/1) from the trace examples — the generator literally writing its own
guide. We try it and report honestly; if intractable we fall back to the
validated distance and SAY SO.

Weightless: the guide is a distance/score over Term OUTPUTS, derived +
validated from the agent's own search traces. No LLM, no gradient, no net.
"""

from __future__ import annotations

from typing import Any, Sequence

from domains.generator import synthesize, _signature, _num


# ---------------------------------------------------------------------------
# Candidate guide: output-distance between a term's signature and the target.
#
# The signature is the canonical per-input output tuple (the same object brick
# 6 already computes for observational-equivalence). We turn each entry into a
# number and take a NORMALISED L1 distance to the target. This is graph-native
# (a function of Term outputs), needs no weights, and is exactly the "are these
# outputs close to what we want" question.
# ---------------------------------------------------------------------------

def _sig_to_nums(sig: tuple) -> tuple[float, ...]:
    out = []
    for tag, val in sig:
        if tag == "bool":
            out.append(1.0 if val is True else 0.0)
        elif val == "nan":
            out.append(float("inf"))
        else:
            out.append(float(val))
    return tuple(out)


def output_distance(sig: tuple, target: tuple) -> float:
    """Normalised L1 distance between a term's outputs and the target outputs.
    Smaller = closer = more promising. inf if any output is non-finite."""
    nums = _sig_to_nums(sig)
    if len(nums) != len(target):
        return float("inf")
    total = 0.0
    for got, want in zip(nums, target):
        if got != got or got in (float("inf"), float("-inf")):
            return float("inf")
        # normalise per-example by (1 + |want|) so big-magnitude targets don't
        # dominate; a scale-robust closeness measure.
        total += abs(got - want) / (1.0 + abs(want))
    return total / len(nums)


# ---------------------------------------------------------------------------
# Reconstruct the solution's sub-terms (descendants) = the USEFUL set.
# A term dict's children live under keys items / a / b / arg / cond/then/other.
# We collect every sub-dict, evaluate it to a signature, and that signature
# marks a trace entry as useful.
# ---------------------------------------------------------------------------

def _subterm_dicts(d: dict) -> list[dict]:
    """All sub-term dicts of d INCLUDING d itself."""
    out = [d]
    for key in ("items",):
        for kid in d.get(key, []) or []:
            out.extend(_subterm_dicts(kid))
    for key in ("a", "b", "arg", "cond", "then", "other"):
        kid = d.get(key)
        if isinstance(kid, dict):
            out.extend(_subterm_dicts(kid))
    return out


def _term_from_dict(d: dict):
    """Wrap a raw Term-JSON dict back into an evaluatable Term object."""
    from substrate_rs import Term
    t = object.__new__(Term)
    object.__setattr__(t, "_json", d)
    return t


def _useful_signatures(substrate, solution_term, envs) -> set[tuple]:
    """Signatures of the solution and ALL its descendants (the useful set)."""
    sol_dict = solution_term.to_dict()
    sigs: set[tuple] = set()
    for sub in _subterm_dicts(sol_dict):
        sig = _signature(_term_from_dict(sub), envs, substrate)
        if sig is not None:
            sigs.add(sig)
    return sigs


# ---------------------------------------------------------------------------
# Harvest traces from training targets + derive/validate the guide.
# ---------------------------------------------------------------------------

def harvest_traces(substrate, training_specs, max_size=6, timeout_s=60.0):
    """Run the UNGUIDED synthesizer on each training target it can solve;
    label every explored distinct-behaviour term useful / not-useful and
    record its candidate feature (output-distance, size).

    training_specs: list of (name, examples) where examples = [(env, out), ...].

    Returns dict with `rows` = list of {name, distance, size, useful} and the
    per-target solve summary.
    """
    rows: list[dict] = []
    solved = []
    for name, examples in training_specs:
        envs = [env for env, _ in examples]
        target = tuple(_num(out) for _, out in examples)
        r = synthesize(substrate, examples, max_size=max_size,
                       timeout_s=timeout_s, return_trace=True)
        if not r["fits"]:
            solved.append((name, False, r["explored"], r["halt_reason"]))
            continue
        solved.append((name, True, r["explored"], r["size"]))
        useful = _useful_signatures(substrate, r["term"], envs)
        trace = r["trace"]  # {sig: (size, term)}
        for sig, (size, _term) in trace.items():
            rows.append({
                "name": name,
                "distance": output_distance(sig, target),
                "size": size,
                "useful": sig in useful,
            })
    return {"rows": rows, "solved": solved}


def validate_guide(rows) -> dict:
    """Does output-distance SEPARATE useful from not-useful trace terms?
    Report mean distance (useful vs not), a simple-threshold precision/recall,
    and AUC (probability a random useful term is closer than a random not).
    """
    use = [r["distance"] for r in rows if r["useful"] and r["distance"] != float("inf")]
    notu = [r["distance"] for r in rows if not r["useful"] and r["distance"] != float("inf")]
    n_use, n_not = len(use), len(notu)
    mean_use = sum(use) / n_use if use else float("nan")
    mean_not = sum(notu) / n_not if notu else float("nan")

    # AUC via rank-sum (Mann-Whitney): P(useful_dist < notuseful_dist).
    # Lower distance for useful => AUC > 0.5 means the guide separates.
    auc = float("nan")
    if use and notu:
        wins = 0.0
        # sort-based O(n log n): for each useful, count not-useful with larger dist
        snot = sorted(notu)
        import bisect
        for d in use:
            # not-useful strictly greater than d
            gt = n_not - bisect.bisect_right(snot, d)
            eq = bisect.bisect_right(snot, d) - bisect.bisect_left(snot, d)
            wins += gt + 0.5 * eq
        auc = wins / (n_use * n_not)

    # Simple threshold = midpoint of class means: predict useful if dist < thr.
    thr = (mean_use + mean_not) / 2 if use and notu else float("nan")
    tp = sum(1 for d in use if d < thr)
    fp = sum(1 for d in notu if d < thr)
    fn = n_use - tp
    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")

    return {
        "n_useful": n_use, "n_not_useful": n_not,
        "mean_dist_useful": mean_use, "mean_dist_not_useful": mean_not,
        "auc": auc, "threshold": thr,
        "precision": precision, "recall": recall,
        "separates": (not (auc != auc)) and auc > 0.6,
    }


# ---------------------------------------------------------------------------
# OPTIONAL: ask brick 6 to synthesize a scoring Term-tree from the trace.
# Features per row: distance (d), size (s). Label: useful (1) / not (0).
# We pose it as a synthesis spec [(env={d,s}, useful)] and see if brick 6
# finds a separating Term. Honest about tractability.
# ---------------------------------------------------------------------------

def try_synthesize_scorer(substrate, rows, max_size=6, timeout_s=40.0,
                          n_examples=24):
    """Try to have the generator ITSELF synthesize a useful/not separator from
    (distance,size)->label examples. Returns the result dict or a 'fallback'
    marker. Honest: this is hard (boolean target over real features) and may
    not separate; we report what happens."""
    # Build a balanced, finite example set (dedup identical feature vectors;
    # on conflict—same features, different label—drop, it's unlearnable there).
    seen: dict[tuple, Any] = {}
    for r in rows:
        d = r["distance"]
        if d == float("inf"):
            continue
        key = (round(d, 4), r["size"])
        lab = 1 if r["useful"] else 0
        if key in seen and seen[key] != lab:
            seen[key] = None  # conflict
        elif key not in seen:
            seen[key] = lab
    pos = [(k, v) for k, v in seen.items() if v == 1]
    neg = [(k, v) for k, v in seen.items() if v == 0]
    if not pos or not neg:
        return {"ok": False, "reason": "no_balanced_examples"}
    # balance
    k = min(len(pos), len(neg), n_examples // 2)
    pos = pos[:k]
    neg = neg[:k]
    examples = []
    for (d, s), lab in pos + neg:
        examples.append(({"d": float(d), "s": float(s)}, lab))

    r = synthesize(substrate, examples,
                   ops=("Lt", "Gt", "Lte", "Gte", "And", "Or", "Not",
                        "Plus", "Minus", "Times"),
                   consts=(0, 1, 2),
                   max_size=max_size, timeout_s=timeout_s)
    return {"ok": True, "result": r, "n_examples": len(examples)}

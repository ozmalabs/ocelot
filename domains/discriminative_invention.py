"""Discriminative feature invention — hypothesis generation from CONFUSION.

The existing invention machinery (belief_revision) mints hypotheses only from
INTRA-word feature bimodality: a feature that fires inconsistently across one
word's own instances. Once those are exhausted (~2 features), `hyp` dries to 0
and feature count plateaus — even though ~2/3 of recognition is still WRONG.

That wrong-ness is the untapped signal: when word A's audio is recognised as B,
the agent's feature set fails to DISCRIMINATE A from B. This module turns that
inter-word confusion into invention hypotheses (the thing that had dried up):

  1. record_confusions  — adapter: run recognition; for each miss (true A → pred
     B) accumulate a Confusion(A,B) count + the acoustic band-means of A's and
     B's observations. Pure observation recording.
  2. analyse_confusions — mint `discriminative_feature_needed` MismatchHypotheses
     for PERSISTENT confusion pairs; the discriminating dimension is the band
     where A's and B's observations separate most. THIS is the new generation.
  3. apply_discriminative_hypotheses — invent a phonology feature: a predicate
     `band > threshold` (threshold between A's and B's means) so the feature
     fires on one and not the other. Origin "phonology" ⇒ recognition picks it up.

The agent invents a feature to split categories its current features confuse —
exactly the feature_invention concept ("when existing features fail to
discriminate observations that DO differ"). See [[ozma_phonology_microtheory]].
"""
from __future__ import annotations

import json
from pathlib import Path

from substrate_rs import (Attr, Lit, Var, Gt, Eq, Abs, Div, Minus, Plus, And,
                          IfThenElse, Times)
from domains.acoustic_resolution import (band_names, get_resolution,
                                         enrich_sign_bands)

_SEED_PATH = (Path(__file__).resolve().parent.parent /
              "seeds" / "discriminative_invention.json")


def _load_seed() -> dict:
    with _SEED_PATH.open() as f:
        return json.load(f)


def _bands(substrate):
    """The acoustic dimensions discrimination may use — f0 + the agent's current
    trajectory band resolution (which it raises itself when invention saturates)."""
    return ["f0_hz"] + band_names(get_resolution(substrate))


def _analyse_bands(substrate):
    """Bands to ANALYSE for new discrimination — only the CURRENT resolution's
    level + f0, not the whole ladder (the coarser ladder levels are nested
    aggregations of the current one, so analysing them too just mints redundant
    features). Older features at coarser levels keep working regardless."""
    res = get_resolution(substrate)
    return ["f0_hz"] + [f"band{res}_{i}" for i in range(res)]


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def record_confusions(substrate, pipe, test_set, vote_counts) -> dict:
    """Run recognition over `test_set`; record confusion counts + per-word
    acoustic band-means. Returns {'confusions': {(A,B): n}, 'acoustics':
    {word: {band: mean}}}. Mechanical observation recording (adapter role)."""
    import scripts.fsdd_learner_world as fl
    confusions: dict = {}
    acc: dict = {}    # word -> band -> [values]
    correct = 0
    for path, digit, sp, idx in test_set:
        samples, fs = fl.load_wav(path)
        true_w = fl._DIGITS[digit]
        pred = fl.predict_one(substrate, pipe, samples, vote_counts)
        if pred == true_w:
            correct += 1
        stream = None
        for s in substrate.nodes("AudioStream"):
            stream = s
        signs = fl._collect_signs_from_stream(substrate, stream) if stream else []
        enrich_sign_bands(substrate, signs=signs)   # finer band attrs on the obs
        for b in _bands(substrate):
            vals = [substrate.node(s)["attrs"].get(b)
                    for s in signs if b in substrate.node(s)["attrs"]]
            m = _mean(vals)
            if m is not None:
                acc.setdefault(true_w, {}).setdefault(b, []).append(m)
        if pred is not None and pred != true_w:
            confusions[(true_w, pred)] = confusions.get((true_w, pred), 0) + 1
    # Keep the raw per-word band VALUES (not just the mean) so analyse can weigh
    # between-word separation against within-word spread (Fisher-style).
    acoustics = {w: {b: list(vs) for b, vs in bands.items()}
                 for w, bands in acc.items()}
    # Persist confusion counts as graph signals (Confusion nodes), accumulating.
    for (a, b), n in confusions.items():
        node = None
        for c in substrate.nodes("Confusion"):
            ca = substrate.node(c)["attrs"]
            if ca.get("true_word") == a and ca.get("pred_word") == b:
                node = c
                break
        if node is None:
            node = substrate.add_node("Confusion", {
                "true_word": a, "pred_word": b, "count": int(n),
                "origin": "discriminative_invention"})
        else:
            substrate.set_attr(node, "count",
                               int(substrate.node(node)["attrs"].get("count", 0)) + n)
    return {"confusions": confusions, "acoustics": acoustics,
            "correct": correct, "total": len(test_set)}


def _stats(xs):
    """Mean and VARIANCE of xs (exactly rational for rational/finite-precision
    inputs -- no sqrt here; see PROGRAM_SYNTHESIS_ARC5_NUMERICS_FLOATS.md c1-14).
    Also returns the std (var ** 0.5) -- kept ONLY because two modules outside
    this one (`pairwise_recognition.py`, `teacher_hook.py`; not owned by this
    change) read `ConfusionBand.a_std`/`b_std` directly for their own,
    independent Fisher-style checks, and silently dropping the attr would zero
    it out under their `.get(..., 0.0)` fallback -- an unrelated decision this
    fix must not alter. THIS module's own decision (`analyse_confusion_band`,
    in `install_analyse_rule` below) no longer reads a_std/b_std or computes a
    sqrt at all: it decides from a_var/b_var via a sqrt-free reformulation."""
    xs = [x for x in xs if x is not None]
    if not xs:
        return None, None, None
    m = sum(xs) / len(xs)
    var = sum((x - m) ** 2 for x in xs) / len(xs)
    return m, var, var ** 0.5


def _disc_root(substrate):
    """The DiscriminativeRoot carrying the agent's discrimination dials. Its
    parameters (min_separation / over_generation_cap / bar_increment) are SEEDED
    from seeds/discriminative_invention.json — not Python constants. The analyse
    rule reads min_separation; the bar-management rule tunes it."""
    for n in substrate.nodes("DiscriminativeRoot"):
        return n
    cfg = _load_seed().get("discriminative_root", {})
    return substrate.add_node("DiscriminativeRoot", {
        "origin": "discriminative_invention",
        "dinv_recent": 0, "bar_eval_pending": 0,      # runtime state
        "paused": 0,                                   # set by the meta-monitor
        **cfg,                                         # seeded dials
    })


def compute_confusion_band_stats(substrate, acoustics: dict,
                                 min_count: int = 2) -> int:
    """Mechanical statistics (adapter): for each persistent confusion pair x band,
    aggregate BOTH words' band-value mean+std into a ConfusionBand node — like
    band-means, no decision. The Fisher DECISION over these stats is the
    `analyse_confusion_band` Rule, not here. Updates existing ConfusionBands
    (preserving their `minted` flag) so a pair isn't re-minted. Returns # new."""
    root = _disc_root(substrate)
    try:
        substrate.add_production({
            "src": {"type": "DiscriminativeRoot", "var": "a"},
            "edge_type": "has_cband",
            "tgt": {"type": "ConfusionBand", "var": "b"},
            "provenance": "discriminative_invention:has_cband"})
    except Exception:
        pass
    existing = {}
    for cb in substrate.nodes("ConfusionBand"):
        a = substrate.node(cb)["attrs"]
        existing[(a.get("true_word"), a.get("pred_word"), a.get("band"))] = cb
    added = 0
    for c in substrate.nodes("Confusion"):
        ca = substrate.node(c)["attrs"]
        A, B = ca.get("true_word"), ca.get("pred_word")
        if int(ca.get("count", 0)) < min_count:
            continue
        for band in _analyse_bands(substrate):
            am, avar, asd = _stats(acoustics.get(A, {}).get(band, []))
            bm, bvar, bsd = _stats(acoustics.get(B, {}).get(band, []))
            if am is None or bm is None:
                continue
            st = {"a_mean": float(am), "a_var": float(avar), "a_std": float(asd),
                  "b_mean": float(bm), "b_var": float(bvar), "b_std": float(bsd),
                  "threshold": float((am + bm) / 2.0),
                  "high_word": A if am >= bm else B}
            key = (A, B, band)
            cb = existing.get(key)
            if cb is None:
                cb = substrate.add_node("ConfusionBand", {
                    "true_word": A, "pred_word": B, "band": band, "minted": 0,
                    "origin": "discriminative_invention", **st})
                try:
                    substrate.add_edge(root, "has_cband", cb)
                except Exception:
                    pass
                existing[key] = cb
                added += 1
            else:
                for k, v in st.items():
                    substrate.set_attr(cb, k, v)
    return added


def _fisher_separates_term(CB, R):
    """Sqrt-free EXACT equivalent of the classic Fisher-ratio test
    `|a_mean-b_mean| / (sqrt(a_var)+sqrt(b_var)+eps) > min_separation`, derived
    by isolating and squaring each square root in turn — the standard technique
    for rationalising a nested-radical inequality (used e.g. in exact
    computational-geometry predicates). Let D=|a_mean-b_mean|, T=min_separation
    (always > 0 — seeds/discriminative_invention.json starts it at 1.0 and the
    bar-management rule only ever raises it), K = D/T - eps. Since
    sa=sqrt(a_var)>=0 and sb=sqrt(b_var)>=0:

        D/(sa+sb+eps) > T
    ⟺   K > sa + sb                                    (K, sa+sb both >= 0 when
                                                          this branch can be live)
    ⟺   K > 0                                           AND
        K**2 - a_var - b_var > 0                        AND   (squaring once,
                                                          isolating the cross term)
        (K**2 - a_var - b_var)**2 > 4 * a_var * b_var         (squaring again)

    Every quantity above is a sum/difference/product of RATIONAL persisted
    attrs (a_mean, b_mean, a_var, b_var, min_separation) — zero sqrt, zero
    irrational intermediate. The three-way case split is exact (not an
    approximation): each squaring step is applied only where both sides are
    already known non-negative, which is the one condition under which
    squaring preserves the order of an inequality. Verdict-identity against
    the original std-based test is gated empirically in
    tests/test_exact_invariant_migrated.py across cases spanning both sides of
    the threshold and near it. See PROGRAM_SYNTHESIS_ARC5_NUMERICS_FLOATS.md
    (c1-14) for the finding this fixes."""
    eps = Lit(1e-6)
    D = Abs(Minus(a=Attr(CB, "a_mean"), b=Attr(CB, "b_mean")))
    T = Attr(R, "min_separation")
    K = Minus(a=Div(a=D, b=T), b=eps)
    a_var = Attr(CB, "a_var")
    b_var = Attr(CB, "b_var")
    L = Minus(a=Minus(a=Times(items=(K, K)), b=a_var), b=b_var)
    return And(items=(
        Gt(a=K, b=Lit(0.0)),
        Gt(a=L, b=Lit(0.0)),
        Gt(a=Times(items=(L, L)), b=Times(items=(Lit(4.0), a_var, b_var))),
    ))


def install_analyse_rule(substrate) -> dict:
    """Install the agent's analysis DECISION as a Rule: over each ConfusionBand,
    if the (sqrt-free, exact) Fisher-equivalent test on a_var/b_var says the
    band cleanly distinguishes the pair, mint a discriminative hypothesis (and
    mark it pending for the add-feature rule). All the arithmetic lives in the
    rule's `where`, via `_fisher_separates_term` — no Div-of-stds, no sqrt.
    Returns {'root', 'rule_index'}."""
    nat = substrate._inner if hasattr(substrate, "_inner") else substrate
    try:
        substrate.add_production({
            "src": {"type": "DiscriminativeRoot", "var": "a"},
            "edge_type": "has_pending",
            "tgt": {"type": "MismatchHypothesis", "var": "b"},
            "provenance": "discriminative_invention:has_pending"})
    except Exception:
        pass
    CB = Var("CB")
    R = Var("R")
    separates = _fisher_separates_term(CB, R)
    rule = {
        "name": "analyse_confusion_band",
        "match": [["R", "has_cband", "CB"]],
        # The Fisher bar is read from the DiscriminativeRoot (R), not a constant.
        # Gated on `paused` — the meta-monitor stops generation when it's spinning.
        "where": And(items=(Eq(a=Attr(Var("R"), "paused"), b=Lit(0)),
                            separates,
                            Eq(a=Attr(CB, "minted"), b=Lit(0)))).to_dict(),
        "effects": [
            ["add_node", "Hyp", "MismatchHypothesis", {
                "kind": "discriminative_feature_needed", "applied": 0,
                "origin": "discriminative_invention",
                "true_word": {"__term__": Attr(CB, "true_word").to_dict()},
                "pred_word": {"__term__": Attr(CB, "pred_word").to_dict()},
                "discriminating_band": {"__term__": Attr(CB, "band").to_dict()},
                "threshold": {"__term__": Attr(CB, "threshold").to_dict()},
                "high_word": {"__term__": Attr(CB, "high_word").to_dict()}}],
            ["add_edge", "R", "has_pending", "Hyp"],
            ["set_attr", "CB", "minted", 1],
        ],
    }
    return {"root": _disc_root(substrate), "rule_index": nat.add_rule(rule)}


def install_discrimination_bar_rule(substrate) -> dict:
    """The agent tunes its OWN Fisher bar (min_separation), graph-residently: when
    it added more than `over_generation_cap` features last cycle (over-generating),
    raise the bar by `bar_increment` so it becomes more selective. All thresholds
    live on the DiscriminativeRoot, read here — no Python constants. Returns
    {'root', 'rule_index'}."""
    nat = substrate._inner if hasattr(substrate, "_inner") else substrate
    try:
        substrate.add_production({
            "src": {"type": "DiscriminativeRoot", "var": "a"},
            "edge_type": "self_manages",
            "tgt": {"type": "DiscriminativeRoot", "var": "b"},
            "provenance": "discriminative_invention:self_manages"})
    except Exception:
        pass
    root = _disc_root(substrate)
    if root not in substrate.neighbours(root, "self_manages"):
        try:
            substrate.add_edge(root, "self_manages", root, {})
        except Exception:
            pass
    R = Var("R")
    over = Gt(a=Attr(R, "dinv_recent"), b=Attr(R, "over_generation_cap"))
    sep_next = IfThenElse(over,
                          Plus(items=(Attr(R, "min_separation"),
                                      Attr(R, "bar_increment"))),
                          Attr(R, "min_separation"))
    rule = {
        "name": "manage_discrimination_bar",
        "match": [["R", "self_manages", "R"]],
        "where": Eq(a=Attr(R, "bar_eval_pending"), b=Lit(1)).to_dict(),
        "effects": [
            ["set_attr", "R", "min_separation", {"__term__": sep_next.to_dict()}],
            ["set_attr", "R", "bar_eval_pending", 0],
        ],
    }
    return {"root": root, "rule_index": nat.add_rule(rule)}


def step_discrimination_bar(substrate, dinv_recent: int, rule_index: int) -> float:
    """Adapter: record how many features were added last cycle + fire the agent's
    bar-management rule. Returns the (possibly raised) min_separation."""
    root = _disc_root(substrate)
    substrate.set_attr(root, "dinv_recent", int(dinv_recent))
    substrate.set_attr(root, "bar_eval_pending", 1)
    nat = substrate._inner if hasattr(substrate, "_inner") else substrate
    nat.apply_rule_once(rule_index)
    return float(substrate.node(root)["attrs"].get("min_separation", 1.0))


def agent_analyse(substrate, rule_index: int, max_iters: int = 500) -> int:
    """Fire the agent's analysis rule over every ConfusionBand — it mints a
    discriminative hypothesis for each band that cleanly separates a confused
    pair. Returns how many hypotheses it minted."""
    nat = substrate._inner if hasattr(substrate, "_inner") else substrate

    def n_hyp():
        return sum(1 for h in substrate.nodes("MismatchHypothesis")
                   if substrate.node(h)["attrs"].get("kind")
                   == "discriminative_feature_needed")
    before = n_hyp()
    for _ in range(max_iters):
        b = n_hyp()
        nat.apply_rule_once(rule_index)
        if n_hyp() == b:
            break
    return n_hyp() - before


def install_add_feature_rule(substrate) -> dict:
    """Install the rule by which the AGENT literally adds a feature itself: it
    mints a parametric comparison-feature Concept (origin 'phonology', so
    recognition includes it) directly from a pending discriminative hypothesis —
    copying the band + threshold + which-side-is-high off the hypothesis it
    minted. No predicate construction: the feature IS its parameters; perception
    (evaluate_comparison_features) reads them. Returns {'root', 'rule_index'}."""
    nat = substrate._inner if hasattr(substrate, "_inner") else substrate
    for et, tgt in (("has_pending", "MismatchHypothesis"),):
        try:
            substrate.add_production({
                "src": {"type": "DiscriminativeRoot", "var": "a"},
                "edge_type": et, "tgt": {"type": tgt, "var": "b"},
                "provenance": f"discriminative_invention:{et}"})
        except Exception:
            pass
    _disc_root(substrate)
    H = Var("H")
    rule = {
        "name": "add_discriminative_feature",
        "match": [["R", "has_pending", "H"]],
        # Gated on `paused` too — when the meta-monitor flags spinning, the agent
        # stops materialising features, not just deciding new ones.
        "where": And(items=(Eq(a=Attr(Var("R"), "paused"), b=Lit(0)),
                            Eq(a=Attr(H, "applied"), b=Lit(0)))).to_dict(),
        "effects": [
            ["add_node", "F", "Concept", {
                "origin": "phonology", "feature_kind": "comparison",
                "invented_by": "discriminative_invention",
                "compare_band": {"__term__": Attr(H, "discriminating_band").to_dict()},
                "compare_threshold": {"__term__": Attr(H, "threshold").to_dict()},
                "high_word": {"__term__": Attr(H, "high_word").to_dict()}}],
            ["set_attr", "H", "applied", 1],
            ["del_edge", "R", "has_pending", "H"],
        ],
    }
    return {"root": _disc_root(substrate), "rule_index": nat.add_rule(rule)}


def agent_add_features(substrate, rule_index: int, max_iters: int = 200) -> int:
    """Fire the agent's add-feature rule until no pending hypotheses remain — the
    agent materialises every discriminative feature it decided it needs. Returns
    how many it added."""
    nat = substrate._inner if hasattr(substrate, "_inner") else substrate
    root = _disc_root(substrate)
    added = 0
    for _ in range(max_iters):
        if not list(substrate.neighbours(root, "has_pending")):
            break
        before = sum(1 for c in substrate.nodes("Concept")
                     if substrate.node(c)["attrs"].get("feature_kind") == "comparison")
        nat.apply_rule_once(rule_index)
        after = sum(1 for c in substrate.nodes("Concept")
                    if substrate.node(c)["attrs"].get("feature_kind") == "comparison")
        if after == before:
            break
        added += after - before
    # Mechanical labelling: signature enumeration keys features by `name`, so
    # give each agent-added feature a unique one (a label, not a decision).
    for c in substrate.nodes("Concept"):
        ca = substrate.node(c)["attrs"]
        if ca.get("feature_kind") == "comparison" and not ca.get("name"):
            substrate.set_attr(c, "name", f"disc{c.value}")
    return added


def evaluate_comparison_features(substrate) -> int:
    """Perception (mechanical): for each parametric comparison feature + sign,
    add `exhibits` if sign[compare_band] > compare_threshold. The agent ADDED the
    features (the rule); this just reads acoustics through them, like the cochlea
    reads audio. Returns edges added."""
    feats = [(c, substrate.node(c)["attrs"]) for c in substrate.nodes("Concept")
             if substrate.node(c)["attrs"].get("feature_kind") == "comparison"]
    if not feats:
        return 0
    n = 0
    for sign in substrate.nodes("AcousticSign"):
        sa = substrate.node(sign)["attrs"]
        nb = set(substrate.neighbours(sign, "exhibits"))
        for cid, ca in feats:
            v = sa.get(ca.get("compare_band"))
            if v is None:
                continue
            if v > float(ca.get("compare_threshold", 0.0)) and cid not in nb:
                try:
                    substrate.add_edge(sign, "exhibits", cid)
                    n += 1
                except Exception:
                    pass
    return n


__all__ = ["record_confusions", "compute_confusion_band_stats",
           "install_analyse_rule", "agent_analyse",
           "install_add_feature_rule", "agent_add_features",
           "install_discrimination_bar_rule", "step_discrimination_bar",
           "evaluate_comparison_features"]

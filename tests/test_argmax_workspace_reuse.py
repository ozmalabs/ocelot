"""test_argmax_workspace_reuse — the sense-pick SCAFFOLDING is reused, the DECISION
is byte-identical.

The measured problem (c58f32da / 9586f93e): every sense-disambiguation pick BUILT A
FRESH SenseCandidate substrate — native Substrate + has_candidate production +
role-prior seed reload — populated candidates, ran the Argmax Program, then threw
the substrate away. Substrate CREATE/teardown was ~60% of the scaffolded pick (pure
churn). The fix reuses a PERSISTENT per-process workspace
(`language_faculty_ops._sense_workspace`): the production + RolePriors are built
ONCE; each pick still grounds its own SenseCandidate nodes under a FRESH
SenseSelection, runs the SAME Argmax Program, reads back the winner, then removes
its per-pick nodes.

This gate proves the reuse is BYTE-IDENTICAL to the fresh-per-occurrence path over a
battery of >=30 real (word, context) cases, and that there is NO CROSS-PICK LEAK
(A then B then A again -> A identical both times). Donkey=0 — no LM; the pick is the
Program's Argmax.
"""
from __future__ import annotations

from domains import language_faculty_ops as lfo


# The FRESH-per-occurrence reference: the exact pre-change lifecycle (build a fresh
# substrate, ground, evaluate, discard). This is the baseline the reused path must
# reproduce byte-for-byte.
def _fresh_pick(program_term, head, slot, ctx, language="en"):
    feats = lfo.sense_candidates(head, slot, ctx, language)
    if not feats:
        return None
    s = lfo._fresh_sense_substrate()
    sel = s.add_node("SenseSelection", {"slot": slot})
    by_id = {}
    for c in feats:
        cn = s.add_node("SenseCandidate", {
            "english_word": c["english_word"], "category": c.get("category") or "?",
            "lesk_overlap": float(c.get("lesk_overlap", 0)), "rank": float(c.get("rank", 0)),
            "freq": float(c.get("freq", 0.0)), "sense": c.get("sense") or ""})
        lfo._add_edge(s, sel, "has_candidate", cn)
        by_id[cn] = c
    win = s.evaluate(program_term, {"sel": sel})
    if win is None or win not in by_id:
        return None
    c = by_id[win]
    syn = c.get("syn")
    return {"sense": syn.definition() if syn is not None else None,
            "synset": syn.name() if syn is not None else None,
            "rank": int(c.get("rank", 0)), "source": "wordnet+context"}


# >=30 real (word, slot, context) cases: multi-sense words in disambiguating
# contexts (both readings), plus single-sense / common words.
_BATTERY = [
    ("mole", "patient", ["skin", "dark", "spot", "face"]),
    ("mole", "patient", ["animal", "dig", "ground", "burrow"]),
    ("cell", "patient", ["prison", "inmate", "guard", "lock"]),
    ("cell", "patient", ["biology", "membrane", "nucleus", "tissue"]),
    ("bank", "patient", ["river", "water", "shore", "mud"]),
    ("bank", "patient", ["money", "loan", "account", "deposit"]),
    ("bass", "patient", ["fish", "river", "lake", "catch"]),
    ("bass", "patient", ["music", "guitar", "note", "sound"]),
    ("rock", "patient", ["music", "band", "roll", "concert"]),
    ("rock", "patient", ["stone", "cliff", "mountain", "hard"]),
    ("spring", "patient", ["season", "flower", "warm", "bloom"]),
    ("spring", "patient", ["water", "well", "source", "flow"]),
    ("spring", "patient", ["coil", "metal", "bounce", "compress"]),
    ("pitch", "patient", ["baseball", "throw", "ball", "mound"]),
    ("pitch", "patient", ["sound", "tone", "high", "voice"]),
    ("crane", "patient", ["bird", "wing", "fly", "marsh"]),
    ("crane", "patient", ["construction", "lift", "heavy", "site"]),
    ("bat", "patient", ["cave", "fly", "night", "wing"]),
    ("bat", "patient", ["baseball", "swing", "hit", "ball"]),
    ("light", "patient", ["lamp", "bright", "shine", "dark"]),
    ("light", "patient", ["weight", "heavy", "carry", "load"]),
    ("plant", "patient", ["factory", "machine", "worker", "produce"]),
    ("plant", "patient", ["garden", "grow", "leaf", "soil"]),
    ("club", "patient", ["golf", "swing", "hit", "ball"]),
    ("club", "patient", ["member", "join", "meeting", "social"]),
    ("mouse", "patient", ["computer", "click", "cursor", "screen"]),
    ("mouse", "patient", ["animal", "cheese", "tail", "small"]),
    ("wave", "patient", ["ocean", "water", "surf", "beach"]),
    ("wave", "patient", ["hand", "greeting", "gesture", "goodbye"]),
    ("seal", "patient", ["ocean", "animal", "swim", "fur"]),
    ("seal", "patient", ["envelope", "stamp", "close", "wax"]),
    ("water", "patient", ["drink", "glass", "thirst", "clear"]),
    ("dog", "patient", ["bark", "tail", "pet", "walk"]),
    ("tree", "patient", ["leaf", "branch", "forest", "tall"]),
    ("book", "patient", ["read", "page", "story", "author"]),
]


def _norm(r):
    if r is None:
        return None
    return (r.get("synset"), r.get("rank"), r.get("source"), r.get("sense"))


def test_battery_byte_identical():
    """Every case: reused-workspace pick == fresh-substrate pick, exactly."""
    prog = lfo.sense_select_program()
    divergences = []
    n = 0
    for head, slot, ctx in _BATTERY:
        fresh = _fresh_pick(prog, head, slot, list(ctx))
        reused = lfo.run_sense_select_program(prog, head, slot, list(ctx))
        n += 1
        if _norm(fresh) != _norm(reused):
            divergences.append((head, ctx, _norm(fresh), _norm(reused)))
    assert n >= 30, f"battery too small: {n}"
    assert not divergences, f"byte-identity FAILED on {len(divergences)}: {divergences}"


def test_no_cross_pick_leak():
    """Pick A, then B, then A again -> A's result is identical both times. Stale
    SenseCandidate nodes from B must not affect A (the correctness crux of reuse)."""
    prog = lfo.sense_select_program()
    a = ("mole", "patient", ["skin", "dark", "spot", "face"])
    b = ("cell", "patient", ["biology", "membrane", "nucleus", "tissue"])
    a1 = lfo.run_sense_select_program(prog, a[0], a[1], list(a[2]))
    _b = lfo.run_sense_select_program(prog, b[0], b[1], list(b[2]))
    a2 = lfo.run_sense_select_program(prog, a[0], a[1], list(a[2]))
    assert _norm(a1) == _norm(a2), f"cross-pick leak: A differs {a1} vs {a2}"
    # And A still equals the fresh baseline after B ran on the shared workspace.
    fresh_a = _fresh_pick(prog, a[0], a[1], list(a[2]))
    assert _norm(a1) == _norm(fresh_a), f"A drifted from fresh: {a1} vs {fresh_a}"


def test_workspace_stays_bounded():
    """Per-pick nodes are removed after read-back: the workspace does not accumulate
    SenseCandidate/SenseSelection nodes across many picks (RolePriors persist)."""
    prog = lfo.sense_select_program()
    s = lfo._sense_workspace()
    before_priors = len(s.nodes("RolePrior"))
    for head, slot, ctx in _BATTERY:
        lfo.run_sense_select_program(prog, head, slot, list(ctx))
    assert s.nodes("SenseCandidate") == [], f"leaked candidates: {s.nodes('SenseCandidate')}"
    assert s.nodes("SenseSelection") == [], f"leaked selections: {s.nodes('SenseSelection')}"
    assert len(s.nodes("RolePrior")) == before_priors

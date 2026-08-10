"""jabberwock_argmax_reuse — MEASURE the workspace-reuse speedup on the sense pick.

The fresh-per-occurrence path built a native Substrate + has_candidate production +
role-prior seed reload PER PICK, ran the Argmax Program, and threw it away. The
decomposition (jabberwock_precommit_review) put substrate CREATE/teardown at ~60% of
the scaffolded pick. The fix reuses a persistent per-process workspace
(`language_faculty_ops._sense_workspace`): production + RolePriors built ONCE, each
pick grounds/evaluates/removes only its own nodes.

This script times the SENSE-PICK component (fresh vs reused) and full warm
`ground_lexeme` (before/after via monkeypatch), n>=500, and reports the real x.
Byte-identity is gated separately in tests/test_argmax_workspace_reuse.py; here we
re-confirm equality on the timed cases as a guard, then print the measured speedup.
Donkey=0 — no LM.
"""
from __future__ import annotations

import time

from domains import language_faculty_ops as lfo


_CASES = [
    ("mole", "patient", ["skin", "dark", "spot", "face"]),
    ("mole", "patient", ["animal", "dig", "ground", "burrow"]),
    ("cell", "patient", ["prison", "inmate", "guard", "lock"]),
    ("cell", "patient", ["biology", "membrane", "nucleus", "tissue"]),
    ("bank", "patient", ["river", "water", "shore", "mud"]),
    ("bank", "patient", ["money", "loan", "account", "deposit"]),
    ("bass", "patient", ["music", "guitar", "note", "sound"]),
    ("spring", "patient", ["water", "well", "source", "flow"]),
    ("pitch", "patient", ["baseball", "throw", "ball", "mound"]),
    ("crane", "patient", ["construction", "lift", "heavy", "site"]),
    ("light", "patient", ["lamp", "bright", "shine", "dark"]),
    ("plant", "patient", ["garden", "grow", "leaf", "soil"]),
    ("club", "patient", ["golf", "swing", "hit", "ball"]),
    ("mouse", "patient", ["computer", "click", "cursor", "screen"]),
    ("wave", "patient", ["ocean", "water", "surf", "beach"]),
    ("seal", "patient", ["envelope", "stamp", "close", "wax"]),
    ("water", "patient", ["drink", "glass", "thirst", "clear"]),
    ("rock", "patient", ["music", "band", "roll", "concert"]),
    ("bat", "patient", ["baseball", "swing", "hit", "ball"]),
    ("book", "patient", ["read", "page", "story", "author"]),
]


def _fresh_pick(program_term, head, slot, ctx):
    feats = lfo.sense_candidates(head, slot, ctx, "en")
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
    return {"synset": syn.name() if syn is not None else None,
            "rank": int(c.get("rank", 0))}


def _norm(r):
    return None if r is None else (r.get("synset"), r.get("rank"))


def _time(fn, iters):
    t0 = time.perf_counter()
    for _ in range(iters):
        fn()
    return (time.perf_counter() - t0) / iters


def main(n=500):
    prog = lfo.sense_select_program()

    # Guard: pre-measure candidate features once (so timing excludes WordNet I/O
    # differences — both paths call the SAME sense_candidates). Confirm equality.
    diverge = 0
    for head, slot, ctx in _CASES:
        f = _fresh_pick(prog, head, slot, list(ctx))
        r = lfo.run_sense_select_program(prog, head, slot, list(ctx))
        if _norm(f) != _norm({"synset": r["synset"], "rank": r["rank"]} if r else None):
            diverge += 1
    print(f"byte-identity on timed cases: {len(_CASES) - diverge}/{len(_CASES)} identical")

    # Warm both paths (WordNet caches, workspace singleton).
    for head, slot, ctx in _CASES:
        _fresh_pick(prog, head, slot, list(ctx))
        lfo.run_sense_select_program(prog, head, slot, list(ctx))

    it = max(1, n // len(_CASES))
    total = it * len(_CASES)

    def run_fresh():
        for head, slot, ctx in _CASES:
            _fresh_pick(prog, head, slot, list(ctx))

    def run_reused():
        for head, slot, ctx in _CASES:
            lfo.run_sense_select_program(prog, head, slot, list(ctx))

    t_fresh = _time(run_fresh, it) / len(_CASES)
    t_reused = _time(run_reused, it) / len(_CASES)
    print(f"\nSENSE PICK end-to-end incl. WordNet enum (n={total}):")
    print(f"  fresh-per-occurrence : {t_fresh*1e6:8.1f} us/pick")
    print(f"  reused-workspace     : {t_reused*1e6:8.1f} us/pick")
    print(f"  SPEEDUP              : {t_fresh/t_reused:6.2f}x")

    # SCAFFOLDED pick ONLY (the component this change touches): substrate CREATE +
    # candidate POPULATE + Argmax EVAL + read-back, with WordNet enumeration
    # PRE-COMPUTED out (it is identical for both paths). This isolates the churn the
    # fix removes — comparable to the precommit review's a+b+c decomposition.
    feats_by_case = [(head, slot, list(ctx), lfo.sense_candidates(head, slot, list(ctx)))
                     for head, slot, ctx in _CASES]

    def scaffold_fresh():
        for head, slot, ctx, feats in feats_by_case:
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
            win = s.evaluate(prog, {"sel": sel})
            _ = by_id.get(win)

    def scaffold_reused():
        s = lfo._sense_workspace()
        for head, slot, ctx, feats in feats_by_case:
            sel = s.add_node("SenseSelection", {"slot": slot})
            scratch = [sel]
            by_id = {}
            for c in feats:
                cn = s.add_node("SenseCandidate", {
                    "english_word": c["english_word"], "category": c.get("category") or "?",
                    "lesk_overlap": float(c.get("lesk_overlap", 0)), "rank": float(c.get("rank", 0)),
                    "freq": float(c.get("freq", 0.0)), "sense": c.get("sense") or ""})
                scratch.append(cn)
                lfo._add_edge(s, sel, "has_candidate", cn)
                by_id[cn] = c
            win = s.evaluate(prog, {"sel": sel})
            _ = by_id.get(win)
            for nid in scratch:
                s.remove_node(nid)

    scaffold_fresh(); scaffold_reused()
    ts_fresh = _time(scaffold_fresh, it) / len(_CASES)
    ts_reused = _time(scaffold_reused, it) / len(_CASES)
    print(f"\nSCAFFOLDED pick only (create+populate+eval+readback, enum excluded) "
          f"(n={total}):")
    print(f"  fresh (build+teardown/pick) : {ts_fresh*1e6:8.1f} us/pick")
    print(f"  reused (populate+eval+clear): {ts_reused*1e6:8.1f} us/pick")
    print(f"  SPEEDUP                     : {ts_fresh/ts_reused:6.2f}x")

    # FULL WARM ground_lexeme: the real per-concept grounding work through the
    # Program sense-path (context_sense=True, agent set) is POS + SENSE-PICK + LEMMA.
    # We time the identical per-concept work with ONLY the sense-pick scaffolding
    # differing (fresh vs reused) — the honest before/after of the whole stage.
    try:
        from domains import wikipedia_consumption as wc
    except Exception as e:
        print(f"\n(ground_lexeme timing skipped: {e})")
        return

    cases = _CASES

    def _ground_one(head, slot, ctx, pick):
        # mirror wikipedia_consumption.ground_lexeme's per-concept faculty reads
        wc.ground_pos(head, "en")
        pick(prog, head, slot, list(ctx))
        wc.ground_lemma(head, "en")

    def ground_fresh():
        for head, slot, ctx in cases:
            _ground_one(head, slot, ctx, _fresh_pick_full)

    def ground_reused():
        for head, slot, ctx in cases:
            _ground_one(head, slot, ctx, lambda p, h, s, c: lfo.run_sense_select_program(p, h, s, c))

    # warm
    ground_fresh(); ground_reused()
    it_g = max(1, n // len(cases))
    total_g = it_g * len(cases)
    t_before = _time(ground_fresh, it_g) / len(cases)
    t_after = _time(ground_reused, it_g) / len(cases)
    print(f"\nFULL WARM ground_lexeme (POS+SENSE+LEMMA, n={total_g}):")
    print(f"  before (fresh sense pick) : {t_before*1e6:8.1f} us/concept")
    print(f"  after  (reused sense pick): {t_after*1e6:8.1f} us/concept")
    if t_after > 0:
        print(f"  SPEEDUP                   : {t_before/t_after:6.2f}x")


def _fresh_pick_full(program_term, head, slot, ctx):
    feats = lfo.sense_candidates(head, slot, ctx, "en")
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
    return {"synset": syn.name() if syn is not None else None,
            "rank": int(c.get("rank", 0))}


if __name__ == "__main__":
    import sys
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 500)

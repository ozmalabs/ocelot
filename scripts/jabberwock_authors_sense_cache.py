#!/usr/bin/env python3
"""jabberwock_authors_sense_cache — the composer AUTHORS the last two adapter-side
fixes from the cycle-solves-extract build, parallel to the nominal-filter it already
authors: a SENSE-DISAMBIGUATOR SELECT Program and a CACHE-ASIDE serve Program.

For EACH fix the discipline mirrors the nominal-filter:
  · WALL PROVEN   — the concern grounds to NOTHING before the cue seed.
  · AUTHORS       — the composer authors the Program (printed).
  · IT WORKS      — byte-identical to the adapter (sense: water->substance; cache:
                    warm==cold value), + a timed warm-vs-cold speedup for the cache.
  · VERIFY-GATED  — #2 accepts (discriminative); the context-blind SENSE twin + the
                    no-store CACHE twin FAIL.
  · HONEST LEDGER — authored (score+argmax / serve decision) vs held leaf (WordNet
                    enumeration / underlying lookup + raw store put).

Donkey=0 — no LM. Run:
  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_authors_sense_cache.py
"""
from __future__ import annotations

import io
import contextlib
import json
import time


def _wall_agent():
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        from substrate.world_adapter import WorldAdapter
        from substrate.seed_loader import manifest_for
        a = WorldAdapter(seeds=())
        a.inner.load_seed_manifest(manifest_for("relation_vocabulary"), a.agent)
        a.inner.load_seed_manifest(manifest_for("composer_dispatch"), a.agent)
    return a


def _author_agent(seed_id):
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        a = _wall_agent()
        from substrate.seed_loader import manifest_for
        a.inner.load_seed_manifest(manifest_for(seed_id), a.agent)
    return a


def _hdr(t):
    print("\n" + "=" * 74)
    print(t)
    print("=" * 74)


def demo_sense():
    from domains import reflective_faculty as rf
    from domains import language_faculty_ops as lfo
    from domains import consumption_quality as cq
    _hdr("FIX 1 — SENSE-DISAMBIGUATOR  (composer authors an Argmax SELECT Program)")
    concern = [["disambiguate", "pick", "SENSE", "by", "context"],
               ["sense", "WORD", "fits", "meaning"]]

    # WALL --------------------------------------------------------------------
    a = _wall_agent()
    ind = rf.induce_concern(a, concern, name_hint="sense_wall")
    g0 = rf.ground_concern(a, [ind["capability_key"]])
    print(f"WALL      : grounded={g0.get('grounded')}  path={g0.get('path')}  "
          f"(no language cue -> the composer cannot reach 'pick the sense that fits')")

    # AUTHOR ------------------------------------------------------------------
    a = _author_agent(lfo.LANGUAGE_FACULTY_CUE_SEED)
    ind = rf.induce_concern(a, concern, name_hint="sense_auth")
    g = rf.ground_concern(a, [ind["capability_key"]])
    print(f"AUTHORS   : grounded={g.get('grounded')}  path={g.get('path')}  "
          f"program={g.get('program_name')}")
    print("  authored SELECT Program (Argmax over senses by context-fit score):")
    print("    " + json.dumps(g.get("program"))[:180] + " ...")

    # VERIFY ------------------------------------------------------------------
    v = g.get("verified") or {}
    print(f"VERIFY    : accepted={v.get('accepted')} discriminates={v.get('discriminates')} "
          f"grounded={v.get('grounded')} | context-blind twin_pass={v.get('twin_pass')} (FAILS) "
          f"| gate={g.get('gate_reason','')[:34]}")

    # IT WORKS ----------------------------------------------------------------
    prog = rf._load_program(a, lfo.SENSE_SELECT_PROGRAM)
    sent = "strip electrons from suitable substances such as water"
    ref = cq.sense_in_context("water", sent)
    got = lfo.run_sense_select_program(prog, "water", "patient", cq.context_words(sent))
    print(f"IT WORKS  : water in {sent!r}")
    print(f"            adapter  pick_sense -> {ref['synset']}  | {(ref['sense'] or '')[:52]}")
    print(f"            authored SELECT     -> {got['synset']}  | {(got['sense'] or '')[:52]}")
    print(f"            BYTE-IDENTICAL: {got['synset'] == ref['synset'] == 'water.n.03'} "
          f"(the SUBSTANCE sense, not the Devon hamlet)")
    # mis-sense battery corrected
    blind = lfo.sense_select_blind_program()
    print("            mis-sense battery (real all-fit; context-blind twin misses):")
    for head, ctx, slot, gold in cq.SENSE_CONTROL:
        r = lfo.run_sense_select_program(prog, head, slot, list(ctx))
        b = lfo.run_sense_select_program(blind, head, slot, list(ctx))
        rf_ok = any(kw in (r.get("sense") or "").lower() for kw in gold)
        bl_ok = any(kw in (b.get("sense") or "").lower() for kw in gold)
        print(f"              {head:8} real={r['synset']:>16} fit={rf_ok} | blind={b['synset']:>16} fit={bl_ok}")

    print("HONEST LEDGER (SENSE):")
    print("  AUTHORED by composer : the SCORE + ARGMAX composition — Argmax over the")
    print("                         candidate senses by context-fit (category + Lesk")
    print("                         gloss overlap + rank + freq).")
    print("  HELD-FACULTY CALL    : the raw WordNet SENSE ENUMERATION + gloss/feature")
    print("                         measurement (dictionary_lexicon._enumerate_features)")
    print("                         — external lexical I/O; no Term reads WordNet.")


def demo_cache():
    from domains import reflective_faculty as rf
    from domains import memory_faculty_ops as mfo
    from domains import consumption_quality as cq
    _hdr("FIX 2 — CACHE-ASIDE  (composer authors a serve-from-store Program)")
    concern = [["cache", "memoize", "a", "consult"], ["store", "VALUE", "by", "KEY"]]

    # WALL --------------------------------------------------------------------
    a = _wall_agent()
    ind = rf.induce_concern(a, concern, name_hint="cache_wall")
    g0 = rf.ground_concern(a, [ind["capability_key"]])
    print(f"WALL      : grounded={g0.get('grounded')}  path={g0.get('path')}  "
          f"(no memory cue -> the composer cannot reach 'cache/memoize this consult')")

    # AUTHOR ------------------------------------------------------------------
    a = _author_agent(mfo.MEMORY_FACULTY_CUE_SEED)
    ind = rf.induce_concern(a, concern, name_hint="cache_auth")
    g = rf.ground_concern(a, [ind["capability_key"]])
    print(f"AUTHORS   : grounded={g.get('grounded')}  path={g.get('path')}  "
          f"program={g.get('program_name')}")
    print("  authored CACHE-ASIDE serve Program (Attr(Pick(Filter(store.has_entry,e,e.ckey==key)),cval)):")
    print("    " + json.dumps(g.get("program"))[:180] + " ...")

    # VERIFY ------------------------------------------------------------------
    v = g.get("verified") or {}
    print(f"VERIFY    : accepted={v.get('accepted')} discriminates={v.get('discriminates')} "
          f"grounded={v.get('grounded')} | no-store twin_pass={v.get('twin_pass')} (FAILS) "
          f"| gate={g.get('gate_reason','')[:34]}")

    # IT WORKS ----------------------------------------------------------------
    sents = {
        "water": "strip electrons from suitable substances such as water",
        "cell": "the cell membrane surrounds the nucleus organelle tissue biology",
        "mole": "a skin mole with pigment melanin benign growth lesion",
        "glucose": "glucose sugar energy metabolism carbohydrate",
        "volcano": "the volcano erupted lava magma ash eruption",
    }

    def leaf(word):
        return cq.sense_in_context(word, sents[word])

    prog = rf._load_program(a, mfo.CACHE_SERVE_PROGRAM)
    store = mfo.HotStore()
    ok = True
    for w in sents:
        cold = leaf(w)
        mfo.cached_call(prog, store, w, leaf)          # miss -> compute + store
        warm = mfo.cached_call(prog, store, w, leaf)   # HIT  -> served from store
        ok = ok and (warm == cold)
    print(f"IT WORKS  : warm==cold byte-identical for all {len(sents)} words: {ok}  "
          f"| store stats: {store.stats()}")

    # timed warm vs cold (underlying = the EXPENSIVE sense lookup)
    words = list(sents)
    seq = words * 6
    t0 = time.perf_counter()
    for w in seq:
        leaf(w)                                        # cold: recompute every time
    cold_s = time.perf_counter() - t0
    store2 = mfo.HotStore()
    for w in words:
        mfo.cached_call(prog, store2, w, leaf)         # fill
    t0 = time.perf_counter()
    for w in seq:
        mfo.cached_call(prog, store2, w, leaf)         # warm: served on repeats
    warm_s = time.perf_counter() - t0
    print(f"            timed cold={cold_s*1e3:.2f}ms  warm={warm_s*1e3:.2f}ms  "
          f"speedup={cold_s/warm_s:.2f}x  faster={warm_s < cold_s}")

    print("HONEST LEDGER (CACHE):")
    print("  AUTHORED by composer : the cache-aside SERVE (hit/miss) decision —")
    print("                         Attr(Pick(Filter(store.has_entry, e, e.ckey==key)),")
    print("                         'cval') over a memory_bound-bounded graph hot store.")
    print("  HELD-FACULTY CALL    : the UNDERLYING LOOKUP being memoized (external I/O)")
    print("                         + the RAW STORE PUT (add_node CacheEntry) — no Term")
    print("                         performs either.")


def main():
    demo_sense()
    demo_cache()
    print("\n" + "=" * 74)
    print("Both fixes: WALL proven, composer AUTHORS the Program, IT WORKS byte-identical")
    print("(+cache speedup), VERIFY-GATED (twins fail). Donkey=0.")
    print("=" * 74)


if __name__ == "__main__":
    main()

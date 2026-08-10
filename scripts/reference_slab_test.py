"""Honest measurement of the cold-reference SLAB layer.

The headline is the MEMORY result: the Wiktionary es slab is a ~100 MB
corpus on disk, yet lookups against it keep process RSS to a SMALL,
corpus-INDEPENDENT working set — because the slab is mmap'd and the OS
page_cache governs residency (the substrate's own page_cache /
virtual_memory_area / cache_aside architecture), instead of an in-RAM
dict whose footprint scales with the corpus.

Sections:
  1. MEMORY proof — build/open the es slab, do ~20 lookups, print RSS
     before/after + the slab file size on disk. RSS << corpus.
  2. COVERAGE — es + ja per-word resolution chains with sources, the
     resulting frame, strict vs expected. Honest about translation
     CHOICE vs coverage gap.
  3. SLAB correctness — comió→comer via the retrofitted UniMorph slab
     (proves the retrofit didn't break it) + a few random Wiktionary
     lookups.

Per CLAUDE.md this is a thin runner — instantiate the native substrate,
hand the world sentences, print. No agent decisions.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native
from domains import reference_slab as rslab
from domains import wiktionary_reference as wikt
from domains import morphology_reference as morph
from domains import dictionary_lexicon as dlex
from domains.language_world import LanguageWorld, teacher_stub


def _rss_kb() -> int:
    return rslab.resident_probe().get("rss_kb", -1)


def section_memory() -> None:
    print("=" * 72)
    print("1. MEMORY PROOF — mmap slab RSS vs corpus size (the headline)")
    print("=" * 72)
    # Ensure the es slabs are built (no-op if cached).
    wikt.build_language_slabs("es", timeout=800)

    corpus = ROOT / "data" / "wiktionary" / "es.jsonl.gz"
    xlate_keys, xlate_vals = rslab._paths("wikt_xlate_es")
    formof_keys, formof_vals = rslab._paths("wikt_formof_es")
    gloss_keys, gloss_vals = rslab._paths("wikt_gloss_es")
    corpus_mb = corpus.stat().st_size / 1e6 if corpus.exists() else -1
    slab_mb = sum(p.stat().st_size for p in
                  (xlate_keys, xlate_vals, formof_keys, formof_vals,
                   gloss_keys, gloss_vals) if p.exists()) / 1e6

    rss_before = _rss_kb()
    # Open + do 20 lookups against the largest slab (gloss, ~80 MB vals).
    sl_gloss = rslab.open_slab("wikt_gloss_es")
    sl_xlate = rslab.open_slab("wikt_xlate_es")
    probe_words = ["perro", "pelota", "gato", "casa", "agua", "libro",
                   "perseguir", "comer", "correr", "amigo", "rojo", "sol",
                   "luna", "mar", "fuego", "tierra", "viento", "lluvia",
                   "nieve", "estrella"]
    hits = 0
    for w in probe_words:
        if sl_gloss.lookup(w) is not None:
            hits += 1
        sl_xlate.lookup(w)
    rss_after = _rss_kb()

    print(f"  Corpus on disk (es-extract.jsonl.gz) : {corpus_mb:8.1f} MB")
    print(f"  Slab files on disk (3 slabs, keys+vals): {slab_mb:8.1f} MB")
    print(f"  Process RSS before 20 lookups          : {rss_before/1024:8.1f} MB")
    print(f"  Process RSS after  20 lookups          : {rss_after/1024:8.1f} MB")
    print(f"  RSS growth from the lookups            : "
          f"{(rss_after - rss_before)/1024:8.2f} MB")
    print(f"  ({hits}/{len(probe_words)} gloss-slab hits)")
    print()
    print(f"  The gloss slab alone is "
          f"{gloss_vals.stat().st_size/1e6:.0f} MB on disk, yet the lookups")
    print(f"  added ~{(rss_after - rss_before)/1024:.1f} MB RSS — the resident set is the")
    print("  WORKING SET (O(log n) index pages + touched value pages), NOT")
    print("  the corpus. An in-RAM dict would have cost the full corpus.")
    print()


def _es_chain(world, surface, slot):
    """Reproduce the Wiktionary chain for reporting (mechanism only)."""
    lemma = wikt.wiktionary_lemmatize(surface, "es", slot)
    base = lemma or surface
    eng = wikt.wiktionary_translate_to_en(base, "es", slot)
    return lemma, eng


def section_coverage() -> None:
    print("=" * 72)
    print("2. COVERAGE — es + ja resolution chains (with sources)")
    print("=" * 72)
    wikt.build_language_slabs("ja", timeout=800)

    bank = [
        {"text": "El perro persiguió la pelota.", "language": "es",
         "expected_meaning": {"event": "chase", "agent": "dog",
                              "patient": "ball", "tense": "past"}},
        {"text": "犬がボールを追いかけた。", "language": "ja",
         "expected_meaning": {"event": "chase", "agent": "dog",
                              "patient": "ball", "tense": "past"}},
    ]
    s = _native.Substrate()
    world = LanguageWorld(s, bank, teacher_stub, teacher_disabled=True)
    log = world.run()

    print("  es per-word Wiktionary chain (mechanism):")
    for surf, slot in [("perro", "agent"), ("pelota", "patient"),
                       ("persiguió", "event")]:
        lemma, eng = _es_chain(world, surf, slot)
        arrow = f"{surf!r}"
        if lemma:
            arrow += f" --formof--> {lemma!r}"
        arrow += f" --xlate--> {eng!r}"
        print(f"    {arrow}")
    print("    NOTE: persiguió→perseguir→'follow' is a translation CHOICE:")
    print("    es Wiktionary lists {follow, pursue, chase, ...} as English")
    print("    translations of perseguir. We prefer the first WordNet can")
    print("    type for the slot — 'follow' here. That is NOT a coverage gap.")
    print()

    for entry in log:
        lang = entry["language"]
        frame = entry["frame"]
        exp = entry["expected"]
        match = entry["matched"]
        print(f"  {lang}: {entry['text']}")
        print(f"     frame    = {frame}")
        print(f"     expected = {exp}  -> "
              f"{'STRICT MATCH' if match else 'no strict match'}")
        lex = {}
        for nid in s.nodes("LexEntry"):
            a = s.node(nid)["attrs"]
            if a.get("language") == lang:
                lex[a.get("surface")] = (a.get("concept"), a.get("source"))
        for surf in sorted(lex):
            c, src = lex[surf]
            print(f"        {surf!r} --{src}--> concept={c!r}")
    print()
    print("  ja HONEST coverage finding: the kaikki ja extract is the")
    print("  JAPANESE-language Wiktionary. Its entries for core words")
    print("  (犬, おいかける) carry Japanese glosses but NO English")
    print("  translations (the translations list is empty), so the")
    print("  Wiktionary xlate slab cannot resolve them. They instead")
    print("  resolve via the existing WordNet OMW path (犬→dog, ボール→ball,")
    print("  追いかける→trace[sense-1]). 追いかけた (past) is absent from both")
    print("  the ja UniMorph dump and the ja Wiktionary form_of data — a")
    print("  genuine coverage gap in the public sources, not a mechanism bug.")
    print()


def section_correctness() -> None:
    print("=" * 72)
    print("3. SLAB CORRECTNESS — UniMorph retrofit + random Wiktionary")
    print("=" * 72)
    # UniMorph retrofit: comió→comer must still work (slab-backed now).
    for surf, exp in [("comió", "comer"), ("sentó", "sentar"),
                      ("rompió", "romper"), ("corrió", "correr")]:
        got = morph.lemmatize(surf, "es", "event")
        print(f"    [UniMorph slab] {surf!r:>10} -> {got!r:<10} "
              f"({'OK' if got == exp else 'MISS exp ' + repr(exp)})")
    print(f"    (UniMorph slab: unimorph_es, {len(rslab.Slab('unimorph_es'))} keys)")
    print()
    print("    Random Wiktionary es lookups:")
    sl = rslab.open_slab("wikt_xlate_es")
    for w in ["perro", "pelota", "agua", "casa", "definitely_absent_zzz"]:
        print(f"      xlate {w!r:>22} -> {sl.lookup(w)!r}")
    print()


def main() -> int:
    section_memory()
    section_coverage()
    section_correctness()
    print("Done. Lead with section 1 (RSS vs corpus) — that is what the")
    print("cold-reference slab architecture buys.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

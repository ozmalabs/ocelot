"""Reference-based word-sense selection — honest measurement.

The WordNet ingester (domains/dictionary_lexicon.py) used to take sense-1
(``wn.synsets(lemma, pos, lang)[0]``) — WordNet's frequency/seniority
default, NOT a context fit. ``pick_sense`` now scores every POS-filtered
candidate by WordNet's OWN structure and returns the best:

  1. slot-category fit  — synset lexname → substrate category vs the slot's
     expected category (event→event/verb; agent→person/animal; patient→
     object). The RELIABLE signal — separates verb-vs-noun / act-vs-event.
  2. Lesk gloss overlap — bag-of-words over the synset gloss + hypernym
     glosses + lemma names, intersected with the sentence-context bag. A
     genuine but NOISY signal (short glosses rarely share surface words with
     the context) — best-effort overlay.
  3. rank/freq tiebreak — bounded under one Lesk hit; defers to WordNet's own
     sense-1 ordering when nothing distinguishes the candidates.

NO training, NO ML oracle — purely a mechanical transform of the reference.

This runner prints, per case: the candidate senses with their component
scores, the sense-1 default vs the context-picked sense, and whether the
picked English lemma is the intended concept. Then a no-regression check.

Run under: ulimit -v 6291456 && timeout 300 python3 scripts/sense_selection_test.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native  # noqa: F401  (import-shape parity w/ others)
from domains import dictionary_lexicon as dl
from domains.dict_teacher import _wordnet


def _candidates(lemma: str, slot: str, language: str):
    wn = _wordnet()
    pos = dl._pos_for_slot(slot)
    wn_lang = dl.WORDNET_LANG[language]
    return wn.synsets(lemma, pos=pos, lang=wn_lang)


def _eng_lemma(syn) -> str:
    ls = syn.lemmas("eng")
    return ls[0].name().replace("_", " ").lower() if ls else "?"


def show_case(title: str, lemma: str, slot: str, language: str,
              context_words: list[str], intended: set[str]) -> dict:
    """Print one case in full and return a result row for the summary."""
    cands = _candidates(lemma, slot, language)
    context_bag: set[str] = set()
    for w in context_words:
        context_bag |= dl._bag(w)

    print(f"\n=== {title} ===")
    print(f"  lemma={lemma!r} slot={slot} lang={language} "
          f"context={context_words}")
    if not cands:
        print("  (no WordNet candidates)")
        return {"title": title, "ok": False, "reason": "no-candidates"}

    sense1 = cands[0]
    print(f"  {'rank':>4} {'synset':<18} {'eng':<12} {'cat':<8} "
          f"{'catfit':>6} {'lesk':>4} {'freq':>5} {'total':>7}  overlap")
    rows = []
    for rank, syn in enumerate(cands):
        sc = dl.score_sense(syn, slot, context_bag, rank)
        rows.append((rank, syn, sc))
        print(f"  {rank:>4} {syn.name():<18} {_eng_lemma(syn):<12} "
              f"{sc['category']:<8} {sc['cat_hit']:>6.0f} {sc['lesk']:>4.0f} "
              f"{sc['freq']:>5.0f} {sc['total']:>7.2f}  "
              f"{sorted(sc['lesk_overlap'])}")

    picked, picked_rank, _ = dl.pick_sense(lemma, slot, context_words, language)
    picked_eng = _eng_lemma(picked)
    sense1_eng = _eng_lemma(sense1)
    moved = picked_rank != 0
    ok = picked_eng in intended
    print(f"  sense-1 default : {sense1.name()} -> {sense1_eng!r}")
    print(f"  context-picked  : {picked.name()} -> {picked_eng!r} "
          f"(rank {picked_rank}{', MOVED off sense-1' if moved else ''})")
    print(f"  intended {sorted(intended)} -> "
          f"{'HIT' if ok else 'MISS'}")
    return {
        "title": title, "ok": ok, "moved": moved,
        "sense1": sense1_eng, "picked": picked_eng, "rank": picked_rank,
    }


def main() -> None:
    print("Reference-based word-sense selection (WordNet Lesk + slot-category "
          "fit). No training, no ML oracle.")

    results = []

    # --- English verb-vs-noun drift (slot-category fit does the work) -------
    results.append(show_case(
        "en 'chase' as EVENT (verb) vs sense-1 noun-or-verb",
        "chase", "event", "en",
        context_words=["dog", "ball", "ran", "after"],
        intended={"chase"}))
    results.append(show_case(
        "en 'chase' as PATIENT (noun) — slot flips the POS",
        "chase", "patient", "en",
        context_words=["the", "long", "hunt"],
        intended={"chase", "pursuit"}))
    results.append(show_case(
        "en 'saw' as PATIENT — proverb.n.01 sense-1 vs the tool (Lesk)",
        "saw", "patient", "en",
        context_words=["cut", "wood", "tool", "blade"],
        intended={"saw", "power saw"}))
    results.append(show_case(
        "en 'race' as EVENT — Lesk pushes toward the contest sense",
        "race", "event", "en",
        context_words=["run", "fast", "win", "finish", "track"],
        intended={"race", "run"}))

    # --- Spanish: perseguir + {dog, ball} -----------------------------------
    # The headline cross-lingual case. Shown with two contexts: a context that
    # happens to carry a gloss word, and the REALISTIC dog/ball context that
    # does NOT — to expose honestly where Lesk is too weak.
    results.append(show_case(
        "es 'perseguir' EVENT, context carries an answer-word ('chase')",
        "perseguir", "event", "es",
        context_words=["perro", "pelota", "dog", "ball", "chase"],
        intended={"chase", "pursue", "follow"}))
    results.append(show_case(
        "es 'perseguir' EVENT, REALISTIC context {dog, ball} (no gloss word)",
        "perseguir", "event", "es",
        context_words=["perro", "pelota", "dog", "ball"],
        intended={"chase", "pursue", "follow"}))
    results.append(show_case(
        "es 'perseguir' EVENT, context {pursue, follow, catch}",
        "perseguir", "event", "es",
        context_words=["perro", "pursue", "follow", "catch", "after"],
        intended={"chase", "pursue", "follow"}))

    # --- Japanese: 追いかける — sense-1 is 'trace', chase is sense-4 ---------
    results.append(show_case(
        "ja '追いかける' EVENT, context {dog, ball, run}",
        "追いかける", "event", "ja",
        context_words=["犬", "ボール", "dog", "ball", "run", "chase"],
        intended={"chase", "follow"}))

    # --- Summary ------------------------------------------------------------
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    moved = [r for r in results if r.get("moved")]
    hits = [r for r in results if r.get("ok")]
    moved_hits = [r for r in moved if r.get("ok")]
    print(f"  cases                          : {len(results)}")
    print(f"  picked a NON-sense-1 synset    : {len(moved)}")
    print(f"  picked the INTENDED concept    : {len(hits)}/{len(results)}")
    print(f"  context BEAT sense-1 (moved+hit): {len(moved_hits)}")
    print()
    for r in results:
        tag = "HIT " if r.get("ok") else "MISS"
        mv = " (moved)" if r.get("moved") else ""
        print(f"  [{tag}] {r['title']}")
        print(f"          sense-1={r.get('sense1')!r} "
              f"picked={r.get('picked')!r} rank={r.get('rank')}{mv}")

    print("\nHONEST NOTES")
    print("-" * 70)
    print("  * Slot-category fit is the RELIABLE signal: it separates the")
    print("    verb-vs-noun and act-vs-event drift cleanly (en chase, saw).")
    print("  * Lesk gloss-overlap is GENUINE but NOISY — short WordNet glosses")
    print("    rarely share surface words with a sentence's content tokens.")
    print("  * perseguir residual is type (a) INVENTORY, not type (b) Lesk:")
    print("    WordNet's es index for 'perseguir' maps to chase.v.02 (amorous")
    print("    pursuit) + pursue.v.02 (motion) — the plain motion 'chase.v.01'")
    print("    is NOT a Spanish-indexed candidate at all, so no context can")
    print("    pick it. pursue.v.02 ('follow in pursuit') is the best true fit.")
    print("  * No-context defers to WordNet's sense-1 ordering by design.")


if __name__ == "__main__":
    main()

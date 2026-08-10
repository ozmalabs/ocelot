"""jabberwock_reads_a_tale — DEEP COMPREHENSION over LONG real Grimm prose.

The reading-corpus summit found that on long, clause-heavy real prose the reader
builds STRUCTURE fine but SEMANTIC comprehension is the un-gated layer: on Grimm's
'The Travelling Musicians' (the Bremen Town Musicians — ass/dog/cat/cock, 6909
chars, 53 sentences) the entity categories came out object 36 / person 12 /
UNKNOWN 37 (43%) / animal ONLY 2 — the FOUR ANIMAL PROTAGONISTS were NOT tracked
as animals. This harness reads real Grimm tales end-to-end through the committed
comprehension stack and reports, HONESTLY, WHO the characters are.

THE DIAGNOSIS (measured, behind this harness):
  · COREF-MERGE already WORKS — each protagonist is ONE persistent SmEntity, its
    repeated mentions merged (the ass named/pronominalised 8x is ONE node, not 8),
    tracked across all 53 sentences (coref_mentions counts it).
  · CATEGORISATION was the break, and NARROWER than the raw 43% suggested. Most
    animal names (dog/cat/wolf/boar/mouse/sparrow/frog/bird/goat/lion/fox) ALREADY
    ground `animal` via WordNet sense-1. The break is the sense-1-NON-animal
    minority: 'ass' -> buttocks, 'cock' -> stopcock, 'donkey' -> donkeywork. These
    grounded `object` because _grounded_category used the `patient` slot, whose
    expected {object, animal, person} gives NO animate discrimination -> WordNet
    frequency sense-1 wins -> a non-animal homonym.
  · OVER-SEGMENTATION is a PARSE-layer residual (adjectives/adverbs/pronouns/quote-
    fragments minted as entity args: 'asleep', 'himself', 'got', '‘how'). It is
    present in the short dev fables too, so it is NOT fixable without perturbing the
    byte-identity guard — reported honestly, not hidden. The raw entity count and
    raw unknown fraction are inflated by it; the CHARACTER roster read-off ignores
    it (a character is a clean, categorised, tracked entity).

THE FIX (coref_entities._refine_animacy_from_agency, graph-native): a post-read
pass re-grounds each entity that ACTS (is the AGENT of an eventive verb — WordNet's
own verb classification) with the `agent` slot, whose expected {person, animal}
makes the graph SELECTION rule DISCRIMINATE the animate sense, and promotes it to
`animal` when the animate grounding is animal AND the current category is the
un-discriminated object/unknown AND it is a clean, non-proper nominal. The eventive-
agent guard is the PRECISION lock: a body-part homonym ('teeth'/'head'/'lips',
which WordNet also carries an animal sense for) never acts, so it is never promoted
-> ZERO false animals. On a short dev fable the pass writes NOTHING (its eventive-
agent entities — water 'rose', cheese 'fell' — have no animal sense) so the
situation model is BYTE-IDENTICAL.

Honest residuals (named, not hidden): 'ass' (WordNet's dominant animate sense is
the coarse PERSON sense) and 'cock' (only ever a grammatical OBJECT in the Bremen
tale, never an eventive agent) stay `object` — separating them from a body-part
homonym would need a hardcoded animal list (donkey = 0). The raw unknown fraction
does NOT drop (over-segmentation dominates it, byte-locked); what improves is the
ANIMAL categorisation of the acting protagonists and the CHARACTER roster.

donkey = 0 (no LLM), no `import re`, NEVER git. Offline (cached Grimm corpus).

  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_reads_a_tale.py
"""
from __future__ import annotations

import collections
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.boot_core import boot_core                       # noqa: E402
from domains import dictionary_lexicon as dl                    # noqa: E402
from domains import comprehension_reader as cr                  # noqa: E402
from domains import coref_entities as ce                        # noqa: E402
from domains import narrative_structure as ns                   # noqa: E402
from domains import literary_analysis as la                     # noqa: E402
import domains.reading_corpus as rc                             # noqa: E402


# The tales the gate reads (public-domain Grimm, cached offline). Each entry names
# its animal protagonists so the harness can report per-protagonist categorisation.
TALES = [
    ("THE TRAVELLING MUSICIANS", ["ass", "dog", "cat", "cock", "donkey"]),
    ("OLD SULTAN", ["wolf", "dog", "cat", "boar"]),
    ("CAT AND MOUSE IN PARTNERSHIP", ["cat", "mouse"]),
    ("THE DOG AND THE SPARROW", ["dog", "sparrow"]),
]


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh() -> _Agent:
    s, node = boot_core()
    return _Agent(s, node)


def _load_tales() -> dict:
    grimm = [s for s in rc.SOURCES if s["key"] == "grimm"]
    return {u["label"]: u for u in rc.load_units(sources=grimm)}


# --------------------------------------------------------------------------- #
#  READ-OFFS — mechanical graph queries (no decision): categorise the entity
#  pool, isolate the CHARACTER roster, count over-segmentation.
# --------------------------------------------------------------------------- #
def category_counts(sm: dict) -> collections.Counter:
    return collections.Counter(v.get("coref_category") for v in sm.values())


def unknown_fraction(sm: dict) -> tuple:
    unk = sum(1 for v in sm.values() if v.get("coref_category") == "unknown")
    return unk, len(sm), (100.0 * unk / max(len(sm), 1))


def character_roster(sm: dict, *, min_mentions: float = 1.0) -> list:
    """WHO are the characters — a mechanical read-off: the CLEAN, categorised
    (animal/person) entities that the reader actually tracked, ranked by mention
    count (the coref-merge evidence). Over-segmentation junk (uncategorised /
    non-nominal fragments) is excluded — a character is a tracked, categorised
    entity, not a parse glom. No decision: reads coref_category / coref_mentions /
    cleanliness off the SmEntity nodes."""
    out = []
    for nm, st in sm.items():
        cat = st.get("coref_category")
        if cat not in ("animal", "person"):
            continue
        if not isinstance(nm, str) or not ce._character_clean(nm):
            continue
        m = float(st.get("coref_mentions", 0.0) or 0.0)
        if m < min_mentions:
            continue
        out.append({"name": nm, "category": cat, "mentions": m})
    out.sort(key=lambda r: (-r["mentions"], r["name"]))
    return out


def real_entities(sm: dict) -> dict:
    """The clean nominal entities (the real referent pool, minus the parse-glom /
    adjective / pronoun / quote-fragment junk `is_nominal` is too permissive to
    reject on its own — token-count structural check via _grounded_cleanliness)."""
    return {nm: st for nm, st in sm.items()
            if isinstance(nm, str) and ce._grounded_cleanliness(nm) >= 1.0}


# --------------------------------------------------------------------------- #
#  READ ONE TALE — comprehension + the WHO read-offs + before/after categories.
# --------------------------------------------------------------------------- #
def read_tale(label: str, text: str, protagonists: list, *, max_sentences: int = 60) -> dict:
    agent = _fresh()
    graph = cr.read_and_comprehend(agent, text, window=2, max_sentences=max_sentences)
    analysis = la.produce_analysis(agent, graph=graph)
    grounding = la.verify_grounding(agent, analysis)
    spine = graph["spine"]
    sm = spine["situation_model"]
    rewrites = spine.get("animacy_rewrites") or []

    after = category_counts(sm)
    before = collections.Counter(after)               # reconstruct pre-pass counts
    for r in rewrites:
        before[r["to"]] -= 1
        before[r["from"]] += 1

    n_sent = len([tb for tb in spine["textbase"] if tb.get("predications")])
    prot_state = {}
    for p in protagonists:
        st = sm.get(p)
        if st is not None:
            prot_state[p] = {"category": st.get("coref_category"),
                             "mentions": float(st.get("coref_mentions", 0.0) or 0.0)}
    roster = character_roster(sm)
    arc_prot = ns.protagonist_by_arc_agency(agent)
    return {
        "label": label, "agent": agent, "graph": graph, "analysis": analysis,
        "grounding": grounding, "sm": sm, "protagonists": protagonists,
        "prot_state": prot_state, "rewrites": rewrites,
        "animals_before": before.get("animal", 0), "animals_after": after.get("animal", 0),
        "cats_before": dict(before), "cats_after": dict(after),
        "unknown_all": unknown_fraction(sm),
        "unknown_real": unknown_fraction(real_entities(sm)),
        "n_sentences": n_sent, "n_entities": len(sm), "n_real": len(real_entities(sm)),
        "roster": roster,
        # THE FRONTIER — the frequency-protagonist (top of the mention-ranked
        # roster) vs the ARC-ROLE protagonist (the arc-agency Argmax). The fix
        # CHANGES the answer where the most-mentioned entity is a bystander.
        "freq_protagonist": (roster[0] if roster else None),
        "arc_protagonist": arc_prot,
        # THE OPPOSITION POLE — a story's shape is PROTAGONIST vs ANTAGONIST. The
        # antagonist is the OPPOSING agency (EXCLUDING the protagonist), decided
        # from the arc's conflict structure (co-participation with the protagonist,
        # then conflict-target, then agency) — the entity the arc-role protagonist
        # correctly REJECTED as the lead (robbers/wolf/the-man) now NAMED as the
        # opposition. None where there is no adversary (a single-character fable).
        "arc_antagonist": ns.antagonist_by_arc_opposition(agent, prot=arc_prot),
    }


def qa_who_are_the_protagonists(rec: dict, top: int = 6) -> dict:
    """QA: 'Who are the protagonists?' -> the top CHARACTERS by mention (the coref-
    tracked, categorised entities). The answer NAMES the real characters and their
    kind (animal/person), read straight off the graph roster."""
    roster = rec["roster"][:top]
    animals = [r["name"] for r in roster if r["category"] == "animal"]
    answer = ", ".join("%s (%s, x%d)" % (r["name"], r["category"], int(r["mentions"]))
                       for r in roster)
    return {"question": "Who are the protagonists?", "answer": answer,
            "animals": animals, "roster": roster}


def qa_who_is_the_protagonist(rec: dict) -> dict:
    """QA: 'Who is the protagonist?' -> the ARC-ROLE protagonist, read straight off
    the graph-native arc-agency Argmax (domains.narrative_structure.protagonist_by_
    arc_agency). The answer names WHO THE STORY IS ABOUT (the entity whose agency
    runs across the arc), NOT the most-mentioned entity. Reports the arc-role pick
    alongside the FREQUENCY pick so the change is visible: on 'The Travelling
    Musicians' frequency says 'robbers', arc-role says an animal of the quartet."""
    arc = rec["arc_protagonist"]
    freq = rec["freq_protagonist"]
    prot = arc.get("protagonist")
    cohort = arc.get("cohort") or []
    freq_name = freq["name"] if freq else None
    answer = ("%s (%s; arc-agency=%d, arc-span=%.0f)"
              % (prot, arc.get("category"), int(arc.get("agency") or 0),
                 float(arc.get("arc_span") or 0.0))) if prot else "(none — no character acts)"
    return {"question": "Who is the protagonist?", "answer": answer,
            "arc_protagonist": prot, "freq_protagonist": freq_name,
            "changed": bool(prot and freq_name and prot != freq_name),
            "cohort": cohort, "category": arc.get("category")}


def qa_who_is_the_antagonist(rec: dict) -> dict:
    """QA: 'Who is the antagonist?' -> the ARC-ROLE antagonist, read straight off
    the graph-native arc-opposition Argmax (domains.narrative_structure.
    antagonist_by_arc_opposition). The answer names the OPPOSING agency the
    protagonist overcomes (Travelling Musicians' robbers, Old Sultan's wolf,
    Dog-and-Sparrow's man, Cat-and-Mouse's mouse), decided from the arc's conflict
    structure (co-participation with the protagonist, then conflict-target, then
    agency) — NOT the protagonist, NOT a bystander, and None where there is no
    adversary. `decided_by` reports HONESTLY which opposition signal carried it."""
    arc = rec["arc_protagonist"]
    ant = rec["arc_antagonist"]
    prot = arc.get("protagonist")
    a = ant.get("antagonist")
    answer = ("%s (%s; opposition=%d, conflict-target=%d, agency=%d, decided_by=%s)"
              % (a, ant.get("category"), int(ant.get("co_participation") or 0),
                 int(ant.get("conflict_target") or 0), int(ant.get("agency") or 0),
                 ant.get("decided_by"))) if a else "(none — no opposing character)"
    return {"question": "Who is the antagonist?", "answer": answer,
            "protagonist": prot, "antagonist": a, "category": ant.get("category"),
            "decided_by": ant.get("decided_by"),
            "co_participation": ant.get("co_participation"),
            "conflict_target": ant.get("conflict_target")}


# --------------------------------------------------------------------------- #
#  PRINT.
# --------------------------------------------------------------------------- #
def _hr(t: str) -> None:
    print("\n" + "=" * 78 + "\n" + t + "\n" + "=" * 78)


def print_tale(rec: dict) -> None:
    _hr("TALE: %s  (%d sentences, %d raw entities, %d clean-real entities)"
        % (rec["label"], rec["n_sentences"], rec["n_entities"], rec["n_real"]))
    print("categories BEFORE fix:", rec["cats_before"])
    print("categories AFTER  fix:", rec["cats_after"])
    print("animals found: %d -> %d      animacy re-groundings: %s"
          % (rec["animals_before"], rec["animals_after"],
             [(r["name"], r["from"], "->", r["to"]) for r in rec["rewrites"]] or "(none needed)"))
    u = rec["unknown_all"]; ur = rec["unknown_real"]
    print("UNKNOWN over ALL raw entities:   %d/%d = %.1f%%  (over-segmentation-dominated)"
          % u)
    print("UNKNOWN over clean-real entities:%d/%d = %.1f%%" % ur)
    print("\nPROTAGONIST TRACKING (coref-merged: one entity each, tracked across the tale):")
    for p, st in rec["prot_state"].items():
        mark = "OK-animal" if st["category"] == "animal" else "(%s)" % st["category"]
        print("   %-10s category=%-8s mentions=%-3d  %s"
              % (p, st["category"], int(st["mentions"]), mark))
    qa = qa_who_are_the_protagonists(rec)
    print("\nQA  %s" % qa["question"])
    print("    -> %s" % qa["answer"])
    print("    animals among them: %s" % qa["animals"])

    qp = qa_who_is_the_protagonist(rec)
    print("\nQA  %s   (ARC-ROLE, not frequency)" % qp["question"])
    print("    FREQUENCY protagonist (most-mentioned): %s" % qp["freq_protagonist"])
    print("    ARC-ROLE  protagonist (arc-agency)    : %s" % qp["answer"])
    print("    -> the fix CHANGES the answer: %s%s"
          % (qp["changed"],
             ("   (%s -> %s)" % (qp["freq_protagonist"], qp["arc_protagonist"]))
             if qp["changed"] else "   (arc-role == frequency here)"))
    if qp["cohort"]:
        print("    acting cohort (the group / quartet, same kind): %s" % qp["cohort"])

    qan = qa_who_is_the_antagonist(rec)
    print("\nQA  %s   (the OPPOSITION pole — protagonist VS antagonist)" % qan["question"])
    print("    PROTAGONIST (arc-agency)        : %s" % qp["arc_protagonist"])
    print("    ANTAGONIST  (arc-opposition)    : %s" % qan["answer"])
    if qan["antagonist"]:
        print("    -> the story's shape: %s (protagonist) VS %s (antagonist)"
              % (qp["arc_protagonist"], qan["antagonist"]))
    else:
        print("    -> honest NULL: no opposing character (a single-character fable)")

    print("\nverify_grounding (anti-hallucination): ok=%s checked=%d"
          % (rec["grounding"]["ok"], rec["grounding"]["checked"]))


# --------------------------------------------------------------------------- #
#  DRIVER.
# --------------------------------------------------------------------------- #
def run() -> list:
    dl.warm_wordnet("en")
    by = _load_tales()
    out = []
    for label, prot in TALES:
        if label not in by:
            print("MISSING tale:", label)
            continue
        out.append(read_tale(label, by[label]["text"], prot))
    return out


def main() -> list:
    results = run()
    for rec in results:
        print_tale(rec)
    _hr("SUMMARY — animals categorised + protagonists tracked, per tale")
    for rec in results:
        n_animal = sum(1 for st in rec["prot_state"].values() if st["category"] == "animal")
        print("  %-32s animals %d->%d | protagonists animal %d/%d | grounding_ok=%s"
              % (rec["label"], rec["animals_before"], rec["animals_after"],
                 n_animal, len(rec["prot_state"]), rec["grounding"]["ok"]))
    _hr("SUMMARY — ARC-ROLE protagonist vs FREQUENCY protagonist (the fix)")
    for rec in results:
        qp = qa_who_is_the_protagonist(rec)
        print("  %-32s frequency=%-11s arc-role=%-11s changed=%s"
              % (rec["label"], qp["freq_protagonist"], qp["arc_protagonist"], qp["changed"]))
    _hr("SUMMARY — the story's shape: PROTAGONIST vs ANTAGONIST (the opposition pole)")
    for rec in results:
        qp = qa_who_is_the_protagonist(rec)
        qan = qa_who_is_the_antagonist(rec)
        print("  %-32s %-11s VS %-11s  (antagonist decided_by=%s)"
              % (rec["label"], qp["arc_protagonist"], qan["antagonist"] or "(none)",
                 qan["decided_by"]))
    return results


if __name__ == "__main__":
    main()

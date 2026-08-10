"""voice_curriculum — VOICE-EXPANSION (WHOLE-CURRICULUM WAVE 3): the
world-adapter grounder the standing study loop (`curriculum_study.study_tick`)
routes a morphology/vocabulary/construction `StudyLesson` to, so studying the
downloaded reference material (`data/voice_curriculum/`) SELF-EXPANDS
`domains.language_production.LanguageProduction`'s reach -- no human per-
lesson call, donkey=0 throughout (UniMorph / WordNet / real-sentence reading
are all offline references, never an LLM).

See VOICE_CURRICULUM.md for the full spec. The three limits this closes
(measured, not assumed):

  1. MORPHOLOGY -- production reads a concept's surface back from the
     grounded `LexEntry` reverse lexicon (`language_production.
     _concept_to_surface_map`), NOT a runtime inflector. An ungrounded verb
     like "go" therefore has no way to surface as "went" for a past-tense
     goal. `_learn_morphology` grounds the (frequency-prioritised) inflected
     surfaces from `unimorph_eng.tsv` as BOTH an `InflectionEntry` (surface
     -> lemma, the comprehension-side fact `morphology_reference.
     ingest_inflection` already grounds for es/ja) AND, via a WordNet lookup
     on the LEMMA (`dictionary_lexicon.dictionary_lookup`), a `LexEntry`
     (surface -> WordNet concept) production reads in reverse -- so "went"
     becomes production's own emitted surface for that concept.
  2. VOCABULARY -- a concept the voice has never grounded a `LexEntry` for
     cannot be produced at all (falls back to the bare, un-realized concept
     string). `_learn_vocabulary` grounds `LexEntry{concept,surface}` for the
     top-frequency words in `freq_10k.txt` via WordNet POS + citation
     (`dictionary_lexicon.ingest_word` -- the SAME mechanical WordNet
     ingester the cold-start comprehension path already uses; see the
     dictionary layer in `language_world.py`'s `_parse_with_grounded`).
  3. CONSTRUCTIONS -- production's `grammatical_encoding` stage orders a
     frame's roles from the grounded `Production` rule strings
     (`language_production._grammar_productions`), falling back to a fixed
     canonical order when none are grounded. `_learn_construction` reads
     real Tatoeba sentences through the SAME `LanguageWorld` comprehension
     path the rest of the system already uses (`language_world.LanguageWorld.
     _ground` / `._parse_with_grounded`) so the fixed English grammar
     skeleton -- and, per-sentence, further WordNet-resolved vocabulary --
     gets grounded from real usage.

ARCHITECTURE (CLAUDE.md). This module is a WORLD ADAPTER: every function
here is mechanical I/O -- read a reference (UniMorph TSV row / WordNet
synset / a real sentence), call the EXISTING grounding primitive
(`morphology_reference.ingest_inflection`, `dictionary_lexicon.ingest_word`
/ `.dictionary_lookup`, `LanguageWorld._add_lex_entry` / `._ground` /
`._parse_with_grounded`), and count what happened. It decides NOTHING about
graph state: which lemma resolves to which WordNet concept is WordNet's
own synset structure (already-existing reference code, unmodified); whether
a lesson is 'blocked' or 'done' from the attempted/answered counts this
module writes is the EXISTING kind-agnostic seed rule pair
(`study_lesson_blocked_on_unanswered_exercise` / `_done_clean`,
`seeds/curriculum_study.json`, unmodified); the reopen-on-growth DECISION is
that seed's rule too (extended with a third `voice_codebook_epoch` Or-arm,
the ONLY seed edit this wave needed). `_bump_voice_epoch` is the SAME
"Python builder bumps an epoch on measured novelty" idiom
`code_write_growth._teach_shape` / `code_reading._install_code_construction`
already use -- a FACT (n genuinely new nodes were grounded this call), never
a decision about which lesson cares.

How the voice actually SELECTS the inflected surface (the fix, named plainly):
production was NOT tense-aware -- its concept->surface reverse map
(`language_production._concept_to_surface_map`) keeps the first-grounded
surface per concept, so `produce(event="go", tense="past")` could never
prefer "went" over "go". The minimal, GATED enabling change made in this wave
(said exactly, since it edits production/comprehension, not just this adapter):
  * each grounded inflection LexEntry carries a `voice_feature` tag (past /
    past_participle / plural / comparative / superlative) copied verbatim from
    the UniMorph feature column -- reference data, not a decision;
  * `language_production` gained a feature-partitioned reverse map
    (`_concept_surface_by_feature`) and selects the surface for the goal's
    requested feature FIRST, falling back to the tense-blind base map; a
    past-tense goal auto-requests the `past` feature for the event role;
  * `language_world` gained `_grounded_voice_feature` and one event-detection
    fallback so an irregular past whose SURFACE the morphology probe can't
    classify ("brought"/"sang") recovers tense from the grounded tag, closing
    the self-monitor round-trip.
Every one of these is a NO-OP when no LexEntry carries a `voice_feature` (no
pre-voice-curriculum entry does), so all existing behaviour is byte-identical
-- verified: test_language + production_test + the recount suite unchanged.

Because the concept is the LEMMA STRING, `go` and `went` share concept "go"
and are distinguished by feature, not by grounding order; and because
vocabulary lessons SKIP an already-grounded surface (`_learn_vocabulary`),
they never re-map an inflected surface morphology already owns (e.g. "went"
-> WordNet's canonical "travel"). Morphology lessons are still ordered before
vocabulary (`prepare_lesson_plan`) so morphology owns the shared surfaces
first -- a mild, honestly-named scheduling choice, no longer load-bearing for
correctness.

Honest residual: an ADJECTIVE degree form ("better") is grounded and EMITTED
(the voice can SAY it) but the self-monitor cannot ACCEPT an attributive
adjective -- the comprehension stack models no adjective slot, so re-parsing
"better X" scrambles the frame. That is a pre-existing comprehension limit,
not a morphology gap; it is reported, never faked (see the test + demo).
"""
from __future__ import annotations

import os
from typing import Any, Optional

from domains import dictionary_lexicon as dlex
from domains import morphology_reference as morph
from domains.language_world import LanguageWorld, teacher_stub

_ROOT = __file__.rsplit("/domains/", 1)[0]
_DATA_DIR = os.path.join(_ROOT, "data", "voice_curriculum")
_LESSON_DIR = os.path.join(_DATA_DIR, "lessons")

# UniMorph feature column -> the LexEntry `voice_feature` tag production +
# comprehension read (see language_production._concept_surface_by_feature /
# language_world._grounded_voice_feature). ONLY the features that a produced
# surface can round-trip through the comprehension stack are mapped; the rest
# (e.g. present-participle "-ing", 3sg present) are deliberately left out and
# reported honestly (an unmapped feature row is ATTEMPTED but not ANSWERED --
# no fabricated grounding). "past" and "past_participle" both recover as past
# tense; "plural"/"comparative"/"superlative" are number/degree selectors.
_FEATURE_MAP = {
    "V;PST": "past",
    "V;V.PTCP;PST": "past_participle",
    "N;PL": "plural",
    "ADJ;CMPR": "comparative",
    "ADJ;SPRL": "superlative",
}


# --------------------------------------------------------------------------- #
#  RESOLVE + WORLD CONSTRUCTION — mechanical adapter I/O (the SAME idiom
#  code_reading._resolve / recount_faculty._resolve already use).
# --------------------------------------------------------------------------- #
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    ag_node = None
    for n in sub.nodes("Agent"):
        if not sub.node(n)["attrs"].get("is_class"):
            ag_node = n
            break
    return sub, native, ag_node


def fresh_voice_world(agent) -> LanguageWorld:
    """A `LanguageWorld` over the agent's OWN native substrate, re-hydrated
    from whatever is ALREADY grounded (`LanguageWorld._reload_cache_from_
    graph` walks the live graph at construction time -- the substrate is the
    source of truth, this object is a rebuildable query cache, exactly the
    precedent `recount_faculty._fresh_voice` / `production_test.py` already
    establish). `teacher_stub` is an OFFLINE heuristic (no LLM -- donkey=0);
    it is invoked at most ONCE per construction-kind lesson (to ground the
    fixed grammar skeleton the first time -- see `_learn_construction`),
    never per-word, and morphology/vocabulary grounding never calls it at
    all."""
    _sub, native, _ag = _resolve(agent)
    world = LanguageWorld(native, [], teacher_stub)
    world.teacher_disabled = True
    return world


def _bump_voice_epoch(sub, ag, delta: int) -> None:
    """Mechanical epoch bump -- see the module docstring's ordering note.
    `delta` is a COUNT of genuinely new LexEntry/InflectionEntry/Production/
    Grammar nodes this call grounded (a measured fact each `_learn_*`
    function computes from its own before/after cache sizes), never a
    decision."""
    if ag is None or delta <= 0:
        return
    cur = sub.node(ag)["attrs"].get("voice_codebook_epoch")
    if cur is None:
        cur = 0.0
    sub.set_attr(ag, "voice_codebook_epoch", float(cur) + float(delta))


# --------------------------------------------------------------------------- #
#  MODULE M — MORPHOLOGY. Chunk format: raw UniMorph TSV rows
#  ("lemma\tform\tfeatures"), one row per line -- see prepare_lesson_plan.
# --------------------------------------------------------------------------- #
def _learn_morphology(agent, world: LanguageWorld, text: str) -> dict[str, Any]:
    sub, _native, ag = _resolve(agent)
    attempted = 0
    answered = 0
    grounded = 0
    rows: list[dict[str, Any]] = []
    lex_en = world._lexicon_cache.setdefault("en", {})
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        parts = ln.split("\t")
        if len(parts) < 3:
            continue
        lemma, form, feats = parts[0].strip(), parts[1].strip(), parts[2].strip()
        if not lemma or not form or lemma.lower() == form.lower():
            continue
        voice_feat = _FEATURE_MAP.get(feats)
        if voice_feat is None:
            # An inflection feature this wave does not round-trip through
            # comprehension (e.g. present-participle) -- NOT grounded, so no
            # fabricated voice growth is claimed. Not even counted as
            # attempted: the lesson only "asks" for what it can honestly
            # deliver, so its answered==attempted settles it 'done' cleanly.
            continue
        attempted += 1
        # concept == the LEMMA STRING (the way a produce goal names it:
        # `produce(event="go", ...)`), NOT the WordNet synset canonical
        # ("travel") -- so the exact form callers ask for is what the reverse
        # lexicon finds. The base form is grounded under the SAME concept so
        # base and inflection agree.
        concept = lemma.lower()
        surface = form.lower()
        was_new = lex_en.get(surface) != concept
        base_new = lex_en.get(concept) != concept
        # (1) BASE LexEntry: lemma -> itself, so non-featured goals
        # (`produce(event="go")` present/no-tense) still realize the lemma.
        world._add_lex_entry("en", concept, concept, tentative=False,
                             weight=1.0, source="unimorph_base")
        # (2) INFLECTION LexEntry: surface -> concept, carrying the UniMorph
        # feature as `voice_feature`, so production selects it BY the goal's
        # requested feature (past/plural/comparative) and the self-monitor
        # re-parse recovers the tense.
        world._add_lex_entry("en", surface, concept, tentative=False,
                             weight=1.0, source="unimorph", voice_feature=voice_feat)
        # (3) InflectionEntry: surface -> lemma (comprehension can reduce
        # "went" to its citation form -- the SAME graph fact ingest_inflection
        # already grounds for es/ja verbs, applied to English here).
        morph.ingest_inflection(world, surface, concept, "en")
        grounded += int(was_new) + int(base_new)
        answered += 1
        rows.append({"lemma": lemma, "form": form, "concept": concept,
                     "feature": voice_feat, "ok": True})
    _bump_voice_epoch(sub, ag, grounded)
    return {"kind": "morphology", "attempted": attempted, "answered": answered,
            "grounded": grounded, "rows": rows}


# --------------------------------------------------------------------------- #
#  MODULE V — VOCABULARY. Chunk format: one lowercase word per line, in
#  frequency order -- see prepare_lesson_plan.
# --------------------------------------------------------------------------- #
def _learn_vocabulary(agent, world: LanguageWorld, text: str) -> dict[str, Any]:
    sub, _native, ag = _resolve(agent)
    attempted = 0
    answered = 0
    grounded = 0
    rows: list[dict[str, Any]] = []
    lex_en = world._lexicon_cache.setdefault("en", {})
    for ln in text.splitlines():
        w = ln.strip().lower()
        if not w or not w.isalpha():
            continue
        attempted += 1
        if w in lex_en:
            # Already grounded -- by a morphology lesson (which runs FIRST,
            # lower `order`) or a prior vocabulary pass. Re-grounding it via
            # WordNet would OVERWRITE the surface->concept mapping (e.g. the
            # inflected surface "went" that morphology grounded as concept
            # "go" would be re-mapped to WordNet's canonical "travel",
            # breaking the produce round-trip). The word is already sayable,
            # so it is ANSWERED but grounds nothing new -- vocabulary only
            # grows the lexicon with words morphology did not already cover.
            answered += 1
            rows.append({"word": w, "concept": lex_en.get(w), "ok": True,
                         "already": True})
            continue
        # NOUN first (the common case for a random frequent word), VERB
        # fallback -- the mechanical slot-preference parameterisation
        # dictionary_lexicon.py's own docstring already documents as
        # sanctioned (not a decision about meaning, only which WordNet
        # POS index to query first).
        concept = dlex.ingest_word(world, w, "patient", "en")
        if concept is None:
            concept = dlex.ingest_word(world, w, "event", "en")
        if concept is not None:
            answered += 1
            grounded += 1
        rows.append({"word": w, "concept": concept, "ok": concept is not None})
    _bump_voice_epoch(sub, ag, grounded)
    return {"kind": "vocabulary", "attempted": attempted, "answered": answered,
            "grounded": grounded, "rows": rows}


# --------------------------------------------------------------------------- #
#  MODULE C — CONSTRUCTIONS. Chunk format: one real sentence per line, from
#  example_sentences.txt -- see prepare_lesson_plan.
# --------------------------------------------------------------------------- #
def _learn_construction(agent, world: LanguageWorld, text: str) -> dict[str, Any]:
    sub, _native, ag = _resolve(agent)
    sentences = [s.strip() for s in text.splitlines() if s.strip()]
    attempted = len(sentences)
    answered = 0
    lex_before = sum(len(v) for v in world._lexicon_cache.values())
    prod_before = sum(len(v) for v in world._production_cache.values())
    for sent in sentences:
        language, shape_key, shape = world._identify(sent, "en")
        if language not in world._grammar_nodes:
            # First-ever construction sentence: ground the fixed English
            # grammar skeleton (+ whatever tiny vocabulary the offline stub
            # recognises) via the SAME NO-LLM heuristic teacher every other
            # LanguageWorld user (production_test.py, recount_faculty tests)
            # already relies on -- called at most ONCE across the whole
            # curriculum (language becomes grammar-grounded immediately
            # after), never per-sentence.
            spec = teacher_stub("cold-start grammar/lexicon", sent, "en")
            frame = world._ground(spec, sent, "en", shape_key, shape)
        else:
            # Every subsequent sentence goes through the REAL grounded-parse
            # path -- the SAME cold-start dictionary/UniMorph/context-typing
            # chain `language_world._parse_with_grounded` already runs for
            # held-out comprehension, so reading real Tatoeba sentences
            # grounds real vocabulary as a side effect of parsing them.
            frame = world._parse_with_grounded(sent, "en", shape)
        if frame.get("event") or frame.get("agent") or frame.get("patient"):
            answered += 1
    lex_after = sum(len(v) for v in world._lexicon_cache.values())
    prod_after = sum(len(v) for v in world._production_cache.values())
    grounded = max(0, (lex_after - lex_before) + (prod_after - prod_before))
    _bump_voice_epoch(sub, ag, grounded)
    return {"kind": "construction", "attempted": attempted, "answered": answered,
            "grounded": grounded}


# --------------------------------------------------------------------------- #
#  DISPATCH — the ONE entry point curriculum_study.study_tick calls, routed
#  by the lesson's OWN `kind` graph attr (mechanical, not a Python content
#  sniff -- study_tick reads `kind` off the StudyLesson node and only calls
#  here for kind in {morphology, vocabulary, construction}).
# --------------------------------------------------------------------------- #
def learn_voice_from_lesson(agent, world: LanguageWorld, text: str,
                            kind: str) -> dict[str, Any]:
    if kind == "morphology":
        return _learn_morphology(agent, world, text)
    if kind == "vocabulary":
        return _learn_vocabulary(agent, world, text)
    if kind == "construction":
        return _learn_construction(agent, world, text)
    return {"kind": kind, "attempted": 0, "answered": 0, "grounded": 0}


# --------------------------------------------------------------------------- #
#  LESSON PREPARATION — chunk the three downloaded datasets into lesson text
#  files under data/voice_curriculum/lessons/. Mechanical file I/O: no
#  agent decisions, a one-time (idempotent) data-prep pass over the
#  reference material named in VOICE_CURRICULUM.md.
# --------------------------------------------------------------------------- #

# UniMorph feature tags this wave grounds, restricted to the inflection
# categories VOICE_CURRICULUM.md names: past / past-participle / plural /
# comparative / superlative (present-participle "-ing" is excluded -- it does
# not round-trip as a finite event through the comprehension stack, so
# grounding it would claim voice growth that isn't real). Because production
# + comprehension now select an inflected surface BY its `voice_feature` tag,
# a single lemma can carry SEVERAL inflections at once (man -> manned [past]
# AND men [plural]); the one-row-per-lemma restriction the first cut used is
# gone -- every target inflection of a selected lemma is grounded, each tagged.
_MORPH_TARGET_FEATURES = frozenset({
    "V;PST", "V;V.PTCP;PST", "N;PL", "ADJ;CMPR", "ADJ;SPRL",
})


def _load_freq_rank(freq_path: str) -> dict[str, int]:
    rank: dict[str, int] = {}
    with open(freq_path, encoding="utf-8") as f:
        for i, ln in enumerate(f):
            w = ln.strip().lower()
            if w and w not in rank:
                rank[w] = i
    return rank


def _select_morphology_rows(unimorph_path: str, freq_rank: dict[str, int],
                            n_lemmas: int) -> list[tuple[str, str, str]]:
    """Every target-feature (lemma, form, features) row for the top `n_lemmas`
    FREQUENCY-RANKED lemmas that have at least one target inflection --
    frequency-ordered, per VOICE_CURRICULUM.md ('ground the top-N lemmas' PST
    / N;PL / comparative-superlative forms first'). Rows for one lemma stay
    contiguous (grouped) so its base + all its inflections land in the same
    lesson chunk. A single streaming pass over the 652k-row TSV (no in-RAM
    copy of the whole file)."""
    by_lemma: dict[str, list[tuple[str, str, str]]] = {}
    with open(unimorph_path, encoding="utf-8") as f:
        for ln in f:
            parts = ln.rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            lemma, form, feats = parts[0], parts[1], parts[2]
            lk = lemma.lower()
            if lk not in freq_rank or lk == form.lower():
                continue
            if feats not in _MORPH_TARGET_FEATURES:
                continue
            rows = by_lemma.setdefault(lk, [])
            if (lemma, form, feats) not in rows:
                rows.append((lemma, form, feats))
    ordered = sorted(by_lemma.keys(), key=lambda w: freq_rank.get(w, 10**9))[:n_lemmas]
    out: list[tuple[str, str, str]] = []
    for lk in ordered:
        out.extend(by_lemma[lk])
    return out


def _chunk(items: list, size: int) -> list[list]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def prepare_lesson_plan(*, n_morphology_lemmas: int = 1000,
                        n_vocabulary_words: int = 1000,
                        n_construction_sentences: int = 300,
                        chunk_morphology: int = 100,
                        chunk_vocabulary: int = 100,
                        chunk_construction: int = 20,
                        data_dir: Optional[str] = None,
                        lesson_dir: Optional[str] = None) -> list[tuple]:
    """Chunk the three downloaded datasets into lesson text files under
    `data/voice_curriculum/lessons/` and return the ordered lesson plan
    ready for `curriculum_study.install_curriculum`:
    `[(order, title, path, kind), ...]`, MORPHOLOGY lessons first, then
    VOCABULARY, then CONSTRUCTION (see the module docstring's ordering
    note -- irregular inflected surfaces must ground before their own bare
    lemma). Idempotent: re-running with the SAME parameters overwrites the
    same chunk files with identical content (deterministic from the source
    datasets), so a repeated prep is a safe no-op on disk contents."""
    data_dir = data_dir or _DATA_DIR
    lesson_dir = lesson_dir or _LESSON_DIR
    os.makedirs(lesson_dir, exist_ok=True)

    freq_path = os.path.join(data_dir, "freq_10k.txt")
    unimorph_path = os.path.join(data_dir, "unimorph_eng.tsv")
    sentences_path = os.path.join(data_dir, "example_sentences.txt")
    freq_rank = _load_freq_rank(freq_path)

    plan: list[tuple] = []
    order = 0

    # -- Module M: morphology chunks --------------------------------------
    morph_rows = _select_morphology_rows(unimorph_path, freq_rank, n_morphology_lemmas)
    for i, chunk in enumerate(_chunk(morph_rows, chunk_morphology)):
        path = os.path.join(lesson_dir, f"morphology_{i:03d}.tsv")
        with open(path, "w", encoding="utf-8") as f:
            for lemma, form, feats in chunk:
                f.write(f"{lemma}\t{form}\t{feats}\n")
        plan.append((order, f"morphology-{i:03d}", path, "morphology"))
        order += 1

    # -- Module V: vocabulary chunks ---------------------------------------
    words = sorted(freq_rank.keys(), key=lambda w: freq_rank[w])[:n_vocabulary_words]
    for i, chunk in enumerate(_chunk(words, chunk_vocabulary)):
        path = os.path.join(lesson_dir, f"vocabulary_{i:03d}.txt")
        with open(path, "w", encoding="utf-8") as f:
            for w in chunk:
                f.write(w + "\n")
        plan.append((order, f"vocabulary-{i:03d}", path, "vocabulary"))
        order += 1

    # -- Module C: construction chunks --------------------------------------
    with open(sentences_path, encoding="utf-8") as f:
        sentences = [ln.strip() for ln in f][:n_construction_sentences]
    for i, chunk in enumerate(_chunk(sentences, chunk_construction)):
        path = os.path.join(lesson_dir, f"construction_{i:03d}.txt")
        with open(path, "w", encoding="utf-8") as f:
            for s in chunk:
                f.write(s + "\n")
        plan.append((order, f"construction-{i:03d}", path, "construction"))
        order += 1

    return plan


def install_voice_curriculum(agent, *, title: str = "Voice Expansion",
                             **plan_kwargs) -> dict[str, Any]:
    """Prepare the lesson chunk files (idempotent) and install them as one
    `Curriculum` via `curriculum_study.install_curriculum` -- the standing
    study loop then self-runs it, one `study_tick` per lesson, no human
    per-lesson call."""
    from domains import curriculum_study as cs  # local import: cs imports
                                                 # this module at its own top
                                                 # level, so import here to
                                                 # avoid a circular top-level
                                                 # import.
    plan = prepare_lesson_plan(**plan_kwargs)
    return cs.install_curriculum(agent, title, plan, source=_DATA_DIR)


__all__ = [
    "fresh_voice_world", "learn_voice_from_lesson",
    "prepare_lesson_plan", "install_voice_curriculum",
]

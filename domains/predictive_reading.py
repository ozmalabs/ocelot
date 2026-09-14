"""predictive_reading — ANALYSIS-BY-SYNTHESIS READING: reading and writing are
ONE model run in opposite directions.

The handwriting arc's endpoint ("AbS is the default — the generation and reading
model is the same, it just runs the same engine in reverse", domains/abs_read.py)
lifted ONE LEVEL UP, from strokes to WORDS. A reader does not passively decode the
incoming signal bottom-up; it SYNTHESIZES what the writer is about to write, then
COMPARES the synthesis to what actually arrives. The RESIDUAL (prediction error)
is the comprehension signal — the collapse framework's "the model forms the
manifold, the surprise lives in the residual", turned on reading itself.

    model of the writer  ─synthesize→  PREDICTED words
                                            │  compare (ShapeDecode)
              actual arriving words  ───────┤
                                            ▼
                       CONFIRMED (covered, LOW residual → fast)
                       SURPRISE  (residual  → the deep, order-N processing)

Two payoffs the collapse view predicts, both measured behind protected controls:

  (a) FASTER — the RECURRING BEAT as a predictor. After the reader has seen a
      Throughline beat recur (help→thank→gift across arcs 1–2, domains/
      throughlines.py), it HOLDS that beat as part of the WriterStyle. It PREDICTS
      the next arc's structure BEFORE reading it; the arc reads FAST because the
      beat's recurring words CONFIRM (low residual) and only the SPECIFICS (which
      helper, which gift) are the residual — which is CORRECT: the surprise SHOULD
      be the residual. Measured: the prediction hit-rate + the confirm-vs-deep
      split (predicted tokens fast-confirmed vs surprise tokens deep-processed).

  (b) MUCH MORE ACCURATE FOR NON-TOKENISED TEXT — the headline. On a noisy /
      un-spaced version of a predictable passage ("thebirdthankedher"), the
      PREDICTION disambiguates the raw signal: the model expects the words, so the
      noisy chars need only CONFIRM the prediction, not be identified bottom-up.
      Measured on the SAME noisy input: prediction-guided recognition accuracy vs
      bottom-up segmentation-alone accuracy — the prediction-guided is HIGHER.

ARCHITECTURE (CLAUDE.md). Everything the AGENT DECIDES is graph-native:
  * the WRITER/AUDIENCE model is graph-resident (WriterStyle / AudienceCentroid
    nodes, a relative_to edge — the specific writer is a POINT relative to the
    class centroid);
  * the PREDICTION is the production faculty run forward (domains/language_
    production.LanguageProduction.produce renders the beat clause — generation is
    reading reversed) conditioned on the writer model + the recurring beat
    harvested from the text seen so far + the immediate discourse context;
  * the COMPARE/RESIDUAL is a ShapeDecode collapse (the synthesized prediction is
    the codebook; the arriving words are decoded against it; the `residual` field
    IS the surprise — never a Python set-difference deciding the surprise);
  * the loop is driven by `cognitive_tick` (a seeded PredictiveReadingStage +
    the predictive_read_advance Reflex, seeds/predictive_reading.json).
NEVER hardcodes the expected words — the predicted words are HARVESTED from the
graph (the recurring cross-arc n-gram + the discourse-context content words), so
the module holds no story literals. No `import re`; donkey = 0.

HONEST LEDGER (see the run script / test): the recurring/formulaic parts predict
well; arbitrary novel content is COARSE and lands in the residual (correct). The
AudienceCentroid is a THIN class model (register features) — the substantive,
data-derived part of the writer model is the recurring surface harvested from the
text seen so far. The LanguageProduction render is bounded by its grounded
vocabulary (it renders the recurring beat clause; the novel slot is the residual).
"""
from __future__ import annotations

import json
import math
import os
import sys
from typing import Any, Iterable, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
_DSLPY = os.path.join(ROOT, "runners", "dsl", "python")
if _DSLPY not in sys.path:
    sys.path.insert(0, _DSLPY)

from domains import comprehend_text as ct
from domains import instruction_reading as ir
from domains import reading_collapse as rc
from domains import throughlines as thr


_PREDICTION_CODEBOOK_TYPE = "ShapeSignaturePrediction"


# --------------------------------------------------------------------------- #
#  resolution (mechanical adapter I/O).
# --------------------------------------------------------------------------- #
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    return sub, native


def _v(nid):
    return nid.value if hasattr(nid, "value") else nid


def _agent_node(sub):
    for n in sub.nodes("Agent"):
        if not sub.node(n)["attrs"].get("is_class"):
            return n
    for n in sub.nodes("Agent"):
        return n
    return None


# --------------------------------------------------------------------------- #
#  RECOGNITION — the words of a span, and its CONTENT words (non-closed-class).
#  Reuses the held segmentation-by-recognition tokenizer (NO whitespace .split,
#  NO regex): the SAME decoder comprehend_text / reading_collapse read with.
# --------------------------------------------------------------------------- #
def _words(agent, text: str) -> list[str]:
    return [w.lower().strip(".,;:?!\"'") for w in ct._recognise_words(agent, text)
            if w.strip(".,;:?!\"'")]


def _content_words(agent, text: str) -> list[str]:
    """The CONTENT words of `text` — recognised words that are not closed-class
    function words (the instruction reader's own closed-class table). These are
    the discourse-context entities/events the prediction is conditioned on (the
    situation model's active material) — a graph/lexicon read, not a hand list."""
    out: list[str] = []
    for w in _words(agent, text):
        if w and w not in ir._CLOSED_CLASS and not w.isdigit():
            out.append(w)
    return out


# --------------------------------------------------------------------------- #
#  RECURRING-SURFACE HARVEST — the writer's characteristic recurring beat, at the
#  SURFACE (word) grain, read off the TEXT SEEN SO FAR by frequency. A contiguous
#  word n-gram (len>=2) that recurs across >=2 DISTINCT arcs is a recurring beat
#  the writer produces arc after arc. NOT hardcoded — derived from the seen arcs
#  by cross-arc recurrence, the twin of throughlines._beat_candidates one grain
#  down (there: a (rel,patient) UnitAction recurring across units; here: the
#  literal surface run the writer repeats).
# --------------------------------------------------------------------------- #
def _arc_ngrams(words: list[str], min_n: int = 2, max_n: int = 8) -> set:
    grams: set = set()
    for n in range(min_n, min(max_n, len(words)) + 1):
        for i in range(len(words) - n + 1):
            grams.add(tuple(words[i:i + n]))
    return grams


def _recurring_ngram_counts(arcs_words: list[list[str]]) -> dict:
    """{gram -> the NUMBER OF DISTINCT ARCS it recurs across} for every contiguous
    word n-gram seen in >=2 arcs. The arc-recurrence count IS the beat source's
    graph-resident STRENGTH: a beat the writer repeats across three arcs is a
    stronger predictor than one seen in two (the weighted-likelihood beat weight is
    this count, never a hand-tuned coefficient)."""
    counts: dict = {}
    for words in arcs_words:
        for g in _arc_ngrams(words):
            counts.setdefault(g, set())
            counts[g].add(id(words))
    return {g: len(us) for g, us in counts.items() if len(us) >= 2}


def _recurring_ngrams(arcs_words: list[list[str]]) -> list[tuple]:
    """Contiguous word n-grams that appear in >=2 DISTINCT arcs, most-arcs-then-
    longest first. Mechanical cross-arc frequency — the writer's repeated surface
    beat, harvested, never named in code."""
    counts = _recurring_ngram_counts(arcs_words)
    recurring = list(counts.items())
    # most-recurring, then longest, then lexical (deterministic).
    recurring.sort(key=lambda gc: (-gc[1], -len(gc[0]), gc[0]))
    return [g for g, _c in recurring]


def _maximal_recurring(arcs_words: list[list[str]]) -> list[tuple]:
    """The MAXIMAL recurring n-grams (drop any that are a contiguous sub-run of a
    longer recurring one) — the writer's beat phrases without their fragments."""
    grams = _recurring_ngrams(arcs_words)
    gset = set(grams)
    maximal: list = []
    for g in grams:
        # is g a contiguous sub-run of some strictly-longer recurring gram?
        subsumed = False
        for h in gset:
            if len(h) <= len(g):
                continue
            for i in range(len(h) - len(g) + 1):
                if h[i:i + len(g)] == g:
                    subsumed = True
                    break
            if subsumed:
                break
        if not subsumed:
            maximal.append(g)
    return maximal


# --------------------------------------------------------------------------- #
#  WRITER MODEL + AUDIENCE CENTROID (graph-resident).
#
#  AudienceCentroid = the CLASS AVERAGE (the typical fable-writer / children's
#  audience): a thin register model. WriterStyle = the SPECIFIC writer as a POINT
#  relative to that centroid (`relative_to` edge), carrying the recurring surface
#  beat harvested from the text seen so far + the recognized Throughline beat. The
#  centroid CONDITIONS the prediction (its register), the point SPECIALISES it.
# --------------------------------------------------------------------------- #
# The class centroid's register features — a fable/children's-story class average
# (data on a node, the SAME status as comprehend_text's closed-class reference
# tables; a class centroid is a small typical-feature vector, not a story literal).
_FABLE_CENTROID = {
    "genre": "fable", "audience": "children", "tense": "past",
    "clause_shape": "svo_simple", "device": "formulaic_repetition",
    "note": "the typical fable-writer: simple past-tense SVO clauses, concrete "
            "agents, and a beat repeated arc after arc for a young audience.",
}


def _class_register_from_corpus(agent, corpus_texts) -> list[str]:
    """The CLASS-REGISTER PRIOR — the writer-class's characteristic vocabulary,
    harvested by cross-text FREQUENCY from a small corpus of the SAME class (OTHER
    fables, not the target), most-frequent-then-first-seen. This is what makes the
    AudienceCentroid a REAL model rather than a thin register-attr stub: not just
    'genre=fable', but the class's actual word distribution. A reader who has read
    the class before holds this prior, so it PREDICTS (fast-confirms) the class's
    common words from the very FIRST sentence — development = model growth, here
    pre-loaded by class experience (the twin of the within-text accumulating
    register one scope up). A graph/lexicon read via the held recognizer (the SAME
    tokens comprehend_text reads with), never a hand-authored word list — the
    module holds no corpus literals; the corpus is the CALLER's writer-class."""
    counts: dict = {}
    first: dict = {}
    for t in (corpus_texts or []):
        for w in _word_types(agent, t):
            if w not in counts:
                counts[w] = 0
                first[w] = len(first)
            counts[w] += 1
    return sorted(counts, key=lambda w: (-counts[w], first[w]))


def _audience_centroid(sub, class_register: Optional[list[str]] = None) -> Any:
    """Idempotently mint the class-average AudienceCentroid (the typical fable /
    children's-audience register). When a `class_register` (the class-prior
    vocabulary harvested from a writer-class corpus) is supplied, store it on the
    node — the centroid becomes a REAL class model (its actual word distribution),
    not just a handful of register attrs. Returns the node."""
    node = None
    for n in sub.nodes("AudienceCentroid"):
        if sub.node(n)["attrs"].get("genre") == _FABLE_CENTROID["genre"]:
            node = n
            break
    if node is None:
        node = sub.add_node("AudienceCentroid", dict(_FABLE_CENTROID))
    if class_register is not None:
        sub.set_attr(node, "class_register", json.dumps(list(class_register)))
    return node


def build_writer_model(agent, seen_arc_texts: list[str], *,
                       throughline_beat: Optional[str] = None,
                       class_corpus: Optional[list[str]] = None,
                       class_register: Optional[list[str]] = None) -> dict:
    """Build the graph-resident writer/audience model from the TEXT SEEN SO FAR.

    Mints (1) an AudienceCentroid (the class average — the typical fable-writer /
    children's-audience register); (2) a WriterStyle node holding the recurring
    surface beat harvested from `seen_arc_texts` (cross-arc recurrence) + the
    recognized Throughline beat (throughlines.py, if given) + a relative_to edge
    to the centroid (the specific writer is a POINT relative to the class). These
    CONDITION the prediction. Returns the model dict + the WriterStyle node.

    The CLASS REGISTER makes the centroid a REAL model (task 1 — grow the model =
    faster reader): pass a `class_corpus` (a few texts of the SAME writer-class,
    NOT the target) to harvest the class-prior vocabulary, or a precomputed
    `class_register` (harvest once, reuse per sentence). It is stored on BOTH the
    centroid (the class it belongs to) and the WriterStyle (so predict_next_words
    reads it off the model), and CONDITIONS the prediction: the class's common
    words fast-confirm from the first sentence, so a RICHER model reads FASTER."""
    sub, native = _resolve(agent)
    arcs_words = [_words(agent, t) for t in seen_arc_texts]
    maximal = _maximal_recurring(arcs_words)
    # the beat source's STRENGTH = its arc-recurrence count (graph-resident, not a
    # tuned weight): a beat kept across more arcs weighs more in the likelihood.
    ngram_counts = _recurring_ngram_counts(arcs_words)
    beat_counts = {"_".join(g): int(ngram_counts.get(g, 2)) for g in maximal}
    # the recurring surface = the words of the maximal recurring beats (dedup,
    # order preserved from the longest beat first) — the writer's repeated phrases.
    recurring_surface: list[str] = []
    for g in sorted(maximal, key=lambda x: -len(x)):
        for w in g:
            if w not in recurring_surface:
                recurring_surface.append(w)
    if class_register is None and class_corpus:
        class_register = _class_register_from_corpus(agent, class_corpus)
    class_register = list(class_register or [])
    centroid = _audience_centroid(sub, class_register or None)
    ws = sub.add_node("WriterStyle", {
        "genre": _FABLE_CENTROID["genre"], "audience": _FABLE_CENTROID["audience"],
        "tense": _FABLE_CENTROID["tense"],
        "recurring_surface": json.dumps(recurring_surface),
        "recurring_beats": json.dumps(["_".join(g) for g in maximal]),
        "recurring_beat_counts": json.dumps(beat_counts),
        "throughline_beat": throughline_beat or "",
        "class_register": json.dumps(class_register),
        "n_arcs_seen": float(len(seen_arc_texts)),
        "note": "the SPECIFIC writer, as a point relative to the fable centroid: "
                "its characteristic recurring surface beat, harvested from the "
                "arcs seen so far."})
    try:
        native.add_edge_unchecked(ws, "relative_to", centroid)
    except Exception:
        pass
    return {"writer_style": ws, "audience_centroid": centroid,
            "recurring_surface": recurring_surface,
            "recurring_beats": ["_".join(g) for g in maximal],
            "recurring_beat_counts": beat_counts,
            "class_register": class_register,
            "throughline_beat": throughline_beat or ""}


def read_writer_model(agent, ws_node) -> dict:
    """Pure graph read of a WriterStyle's held model (for gates/demos)."""
    sub, _ = _resolve(agent)
    at = dict(sub.node(ws_node)["attrs"])
    at["recurring_surface"] = json.loads(at.get("recurring_surface") or "[]")
    at["recurring_beats"] = json.loads(at.get("recurring_beats") or "[]")
    at["recurring_beat_counts"] = json.loads(at.get("recurring_beat_counts") or "{}")
    at["class_register"] = json.loads(at.get("class_register") or "[]")
    at["node"] = _v(ws_node)
    return at


# --------------------------------------------------------------------------- #
#  PREDICTOR — the production faculty run FORWARD. The writer model's recurring
#  beat + the discourse context are synthesized into the PREDICTED next words.
#  generation-is-reading-reversed (LanguageProduction.produce) renders the beat
#  clause; the harvested recurring surface is the concrete landing prediction.
# --------------------------------------------------------------------------- #
def _beat_frame(throughline_beat: str, helper: Optional[str]) -> Optional[dict]:
    """A production GOAL frame from the recognized throughline beat 'rel:patient'
    (throughlines._beat_candidates' own token shape). The `helper` (the arc's
    active agent from context) fills the agent slot; the recurring verb + patient
    are the writer's held beat. None when the beat is not a clean rel:patient."""
    if not throughline_beat or ":" not in throughline_beat:
        return None
    rel, patient = throughline_beat.split(":", 1)
    rel, patient = rel.strip(), patient.strip()
    if not rel or not patient:
        return None
    frame = {"event": rel, "patient": patient, "intent": "inform"}
    if helper:
        frame["agent"] = helper
    return frame


def _production_render(throughline_beat: str, helper: Optional[str]) -> Optional[dict]:
    """Render the predicted beat clause via the PRODUCTION FACULTY (generation is
    reading reversed): ground a tiny SVO corpus from the beat frame (literary_
    analysis._build_producer's own stub-teacher path, donkey=0) and run
    LanguageProduction.produce FORWARD. Returns {clause, words} or None — the
    faculty is bounded by its grounded vocabulary (it realises the recurring beat
    clause; a novel/ungrounded slot is honestly the residual). Wrapped: a render
    failure degrades to None (the harvested surface is the landing prediction)."""
    frame = _beat_frame(throughline_beat, helper or "helper")
    if frame is None:
        return None
    try:
        from domains import literary_analysis as la
        producer = la._build_producer([{"event": frame["event"],
                                         "agent": frame.get("agent", "helper"),
                                         "patient": frame.get("patient")}])
        r = producer.produce("en", frame)
        clause = (r or {}).get("overt_speech") or ""
        core = clause.rstrip(".!?").strip()
        if not core:
            return None
        words = [w.lower().strip(".,;:?!\"'") for w in core.split(" ") if w.strip()]
        return {"clause": core, "words": [w for w in words if w]}
    except Exception:
        return None


# --------------------------------------------------------------------------- #
#  WEIGHTED LIKELIHOOD — the finer grain. Each candidate next word carries a
#  PROBABILITY, combining the prediction SOURCES by their graph-resident STRENGTH
#  (never a hand-tuned coefficient): the register FREQUENCY (a smoothed unigram
#  prior — how often the word type has been seen), the recurring BEAT (its arc-
#  recurrence count), the CONTEXT (its count among the active discourse entities),
#  the writer-class PRIOR (its frequency rank in the class register), and — for
#  verse — the METER/RHYME fit (the harmonic resonance strength). The combination
#  is a held `Plus` Term (a weighted sum of the source strengths); the top-1 is a
#  held `Argmax` Term; the per-word SURPRISAL is a held `Neg(Log(...))` Term. The
#  weights ARE the sources' evidence — the more a source has seen a word, the more
#  mass it lends it. Python only assembles the Lit inputs (mechanical graph reads,
#  the SAME status as abs_read's Lit-list Terms); the ranking/log decisions are the
#  Terms'. Normalization to a distribution is scalar arithmetic on Term outputs.
# --------------------------------------------------------------------------- #
def _combine_term(strengths: list[float]) -> dict:
    """The weighted-sum combination as a held `Plus` Term over the source
    strengths (an empty vector is the Lit 0.0 — no evidence)."""
    if not strengths:
        return {"type": "Lit", "value": 0.0}
    return {"type": "Plus",
            "items": [{"type": "Lit", "value": float(s)} for s in strengths]}


def _combine_score(native, strengths: list[float]) -> float:
    """ONE held-Term evaluate — the combined score of a candidate from its source
    strengths (the graph-native weighted sum, never Python `sum()` deciding it)."""
    return float(native.evaluate(_combine_term(strengths), {}) or 0.0)


def _argmax_pairs_term(pairs) -> dict:
    """Held `Argmax` over `[word, score]` pairs by the score — the top-1 pick as a
    graph-native decision (the abs_read / arrangement_codebook idiom)."""
    return {"type": "Argmax", "source": {"type": "Lit", "value": pairs},
            "var_name": "c",
            "value": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                      "index": {"type": "Lit", "value": 1}}, "default": None}


def _surprisal_term(p: float) -> dict:
    """Held `Neg(Log(p))` — the graded SURPRISAL read off a likelihood (the abs_read
    `Neg(Div(Log(...)))` idiom, here the plain −ln p information content)."""
    return {"type": "Neg", "arg": {"type": "Log",
                                   "arg": {"type": "Lit", "value": float(p)}}}


def surprisal(native, p: float) -> float:
    """ONE held-Term evaluate — the surprisal (−ln likelihood) of an arriving word,
    read off the distribution. A high-likelihood word => tiny surprisal (glide); a
    rare/OOV word => big surprisal (the news, deep-processed). Graded, continuous."""
    p = max(float(p), 1e-12)
    return float(native.evaluate(_surprisal_term(p), {}) or 0.0)


def _source_strengths(word: str, *, register_freq: dict, beat_counts: dict,
                      ctx_content: list, class_register: list,
                      meter_weights: dict,
                      goal_content: Optional[dict] = None) -> list[float]:
    """The graph-resident source strengths of a candidate word (a mechanical
    graph read, no decision): [register-frequency (add-one smoothed unigram prior),
    recurring-beat arc-recurrence count, context active-entity count, writer-class
    frequency-rank prior, meter/rhyme resonance, GOAL-CONTENT strength].

    The GOAL-CONTENT strength is the block-341 conditioning term: when a communicative
    GOAL is driving the synthesis (a want-it-said goal carrying `content`), the words
    that realize the goal's content get lifted, so the unclamped rollout is STEERED
    toward saying what the goal wants said (rather than free-wind synthesis). It is the
    goal's own weight on the candidate — mass the goal lends a word it wants uttered.
    `goal_content` maps concept-surface -> weight (default weight 1.0 per goal concept);
    zero for words the goal does not want. Absent goal => 0.0 (no steering, unchanged)."""
    s_reg = float(register_freq.get(word, 0)) + 1.0             # smoothed unigram
    s_beat = 0.0
    for beat, c in beat_counts.items():
        if word in beat.split("_"):
            s_beat = max(s_beat, float(c))                      # arc-recurrence
    s_ctx = float(ctx_content.count(word))                      # active entity
    n_cls = len(class_register)
    s_cls = (float(n_cls - class_register.index(word)) / n_cls
             if (n_cls and word in class_register) else 0.0)    # class freq-rank
    s_meter = float(meter_weights.get(word, 0.0))               # harmonic fit
    s_goal = float((goal_content or {}).get(word, 0.0))         # the goal's pull
    return [s_reg, s_beat, s_ctx, s_cls, s_meter, s_goal]


def predict_next_words(agent, ws_node, *, context: str = "",
                       use_production: bool = True,
                       seen_vocab: Optional[list[str]] = None,
                       register_freq: Optional[dict] = None,
                       meter_weights: Optional[dict] = None,
                       goal_content: Optional[Iterable[str]] = None,
                       goal_weight: float = 2.0,
                       voice_words: Optional[Iterable[str]] = None,
                       voice_weight: float = 1.5) -> dict:
    """SYNTHESIZE the predicted next words — the production faculty run forward,
    conditioned on the writer model + the immediate discourse context.

    Sources (all graph/faculty reads, never a hardcoded word list):
      * the WriterStyle's recurring surface beat (harvested from the text seen so
        far) — the writer's repeated phrasing, the structural prediction;
      * the CONTEXT content words (the discourse-so-far's active entities, off the
        held recognizer) — so a beat instance about the just-introduced entity
        predicts THAT entity ('...met a bird' → the next beat is about 'bird');
      * (use_production) the LanguageProduction render of the beat clause — the
        production faculty as the predictor, its recurring words merged in;
      * (seen_vocab) the ACCUMULATING REGISTER — every word TYPE the reader has
        already seen in this text. This is the writer/audience model's register
        made concrete: the structure/function words ('the','a','he','and') and the
        recurring content the writer works in recur, so they FAST-CONFIRM; only a
        genuinely NEW word is the residual. Harvested from the seen text (never a
        hardcoded function-word list) — the twin of the recurring beat one grain
        down (there: a repeated n-gram; here: any repeated word type). This is what
        makes the WHOLE first pass predictive, not just the recurring-beat arc.

    Returns {predicted_words, provenance, production}. The predicted words are the
    SYNTHESIS the arriving text is compared against."""
    model = read_writer_model(agent, ws_node)
    provenance: dict = {}
    predicted: list[str] = []

    def _add(w, src):
        w = (w or "").lower().strip(".,;:?!\"'")
        if w and w not in predicted:
            predicted.append(w)
            provenance[w] = src

    for w in model["recurring_surface"]:                 # writer's recurring beat
        _add(w, "recurring_beat")
    ctx_content = _content_words(agent, context) if context else []
    for w in ctx_content:                                # discourse-context entities
        _add(w, "context")
    helper = ctx_content[-1] if ctx_content else None    # the active agent, for render

    production = None
    if use_production:
        production = _production_render(model.get("throughline_beat") or "", helper)
        if production:
            for w in production["words"]:
                _add(w, "production")

    for w in (seen_vocab or []):                          # the accumulating register
        _add(w, "register")

    for w in model.get("class_register") or []:           # the CLASS-PRIOR register
        # the writer-CLASS's characteristic vocabulary (harvested from a corpus of
        # the same class, held on the AudienceCentroid). A reader who has read the
        # class before predicts its common words BEFORE the within-text register
        # accumulates — so a RICHER model reads FASTER (task 1). Never overrides an
        # in-text provenance (dedup keeps the first source), so it only ADDS the
        # words the within-text signals had not already predicted.
        _add(w, "class_prior")

    # ---- GOAL-CONTENT candidates (block 341: the want-it-said conditioning) --- #
    # When a communicative GOAL drives the synthesis, its content concepts ENTER the
    # candidate pool (so the goal can say a word the writer/context signals had not
    # predicted) and are weighted up by the goal strength below — the goal STEERS the
    # unclamped rollout toward saying what it wants said. Absent a goal, this is a
    # no-op and the rollout is unchanged (free synthesis).
    goal_words = [str(w).lower().strip(".,;:?!\"'") for w in (goal_content or [])]
    goal_words = [w for w in goal_words if w]
    goal_wmap = {w: float(goal_weight) for w in goal_words}
    for w in goal_words:
        _add(w, "goal")

    # ---- VOICE candidates (block 342: register/idiolect the utterance is shaped in) --- #
    # The audience slot's voice words (own idiolect for a self audience; the audience's
    # register otherwise) enter the pool and are lifted through the REGISTER channel — a
    # DIFFERENT strength than the goal, so content (WHAT) and voice (HOW/framing) COMPOSE
    # in the held Plus rather than one stomping the other (the rung-1 defect). Voice never
    # carries content (the shaper already dropped content-overlap).
    voice_list = [str(w).lower().strip(".,;:?!\"'") for w in (voice_words or [])]
    voice_list = [w for w in voice_list if w]
    for w in voice_list:
        _add(w, "voice")

    # ---- WEIGHTED LIKELIHOOD over the candidates (the finer grain) ----------- #
    # each candidate's combined score is a held `Plus` Term over its five graph-
    # resident source strengths; the distribution is the normalized scores; the
    # top-1 is a held `Argmax` Term. The register FREQUENCY (add-one smoothed) makes
    # frequent words weigh more; the recurring-beat arc-count and context/class/
    # meter strengths lift the words those sources vouch for.
    _sub, _native = _resolve(agent)
    reg_freq = dict(register_freq or {})
    if not reg_freq:                                     # no counts => uniform prior
        reg_freq = {w: 1 for w in (seen_vocab or [])}
    # voice words carry register weight (their natural channel) — this is HOW content
    # (goal channel) and voice (register channel) COMPOSE additively in the held Plus.
    for w in voice_list:
        reg_freq[w] = reg_freq.get(w, 0) + float(voice_weight)
    beat_counts = model.get("recurring_beat_counts") or {}
    class_reg = model.get("class_register") or []
    mweights = dict(meter_weights or {})
    strengths: dict = {}
    weights: dict = {}
    for w in predicted:
        s = _source_strengths(w, register_freq=reg_freq, beat_counts=beat_counts,
                              ctx_content=ctx_content, class_register=class_reg,
                              meter_weights=mweights, goal_content=goal_wmap)
        strengths[w] = {"register": s[0], "beat": s[1], "context": s[2],
                        "class_prior": s[3], "meter": s[4], "goal": s[5]}
        weights[w] = _combine_score(_native, s)           # held Plus Term
    z = sum(weights.values())                             # normalizer (scalar)
    likelihoods = {w: (weights[w] / z if z else 0.0) for w in predicted}
    ranked = sorted(predicted, key=lambda w: (-likelihoods[w], w))
    pairs = [[w, weights[w]] for w in predicted]
    top1_pair = _native.evaluate(_argmax_pairs_term(pairs), {}) if pairs else None
    top1 = (top1_pair[0] if isinstance(top1_pair, (list, tuple)) and top1_pair
            else (ranked[0] if ranked else None))

    return {"predicted_words": predicted, "provenance": provenance,
            "production": production, "context_content": ctx_content,
            "likelihoods": likelihoods, "weights": weights,
            "source_strengths": strengths,
            "ranked": [(w, likelihoods[w]) for w in ranked], "top1": top1}


# --------------------------------------------------------------------------- #
#  THE UNCLAMPED SELF-CONDITIONED ROLLOUT (block 343 / rung 1.5). Rungs 1-2 took a
#  top-k SELECTION over ONE prediction (a bag of the highest-ranked words). This is
#  the true analysis-by-synthesis-in-reverse: emit one word, FEED IT BACK into the
#  context + seen register, RE-PREDICT with the extended context, repeat — the
#  reader's next-word synthesis run forward with its OWN output as the observation
#  (self-conditioned), with NO external surface clamping it (no abs_compare/_words).
#  Goal + audience conditioning (rung 2) carry through every step so content x voice
#  x complexity compose per emitted word. Terminates on a stop condition; degeneracy
#  (repetition / drift) is MEASURED via per-step provenance, never hidden.
# --------------------------------------------------------------------------- #
def rollout_unclamped(agent, ws_node, *, goal_content=None, voice_words=None,
                      goal_weight: float = 2.0, voice_weight: float = 1.5,
                      seed_context: str = "", max_steps: int = 16,
                      no_immediate_repeat: bool = True,
                      stop_on_goal_cover: bool = True,
                      voice_headroom: int = 3) -> dict:
    """Run the predictor FORWARD, feeding its own emitted word back as context, until
    a stop condition. Returns
        {tokens: [word...], surface: str, steps: [{word, source, rank}...],
         stop_reason: str, goal_covered: [...], goal_uncovered: [...],
         repeat_rate: float}
    Stops on: (a) all goal_content emitted + voice_headroom extra words
    (stop_on_goal_cover); (b) max_steps; (c) no fresh candidate (degeneracy — the
    predictor can only re-propose already-emitted words). `no_immediate_repeat` skips
    a candidate already emitted (the minimal anti-degeneracy guard), so a stall is
    surfaced as stop_reason='exhausted' rather than looping.

    NOTE (honest): this emits an ORDERED token stream (the feedback makes order
    meaningful — later words are conditioned on earlier ones), but coherence is
    bounded by the writer/register model driving the ranking; the stream is not
    claimed to be grammatical. The point proven is the LOOP: self-conditioned,
    goal-steered, terminating, with content recovered."""
    goal_set = [str(w).lower().strip(".,;:?!\"'") for w in (goal_content or [])]
    goal_set = [w for w in goal_set if w]
    emitted: list[str] = []
    steps: list[dict] = []
    seen = list(dict.fromkeys((seed_context or "").lower().split()))
    context = seed_context or ""
    stop_reason = "max_steps"
    covered_after = 0  # words emitted since goal fully covered (voice tail budget)

    for _ in range(int(max_steps)):
        pred = predict_next_words(agent, ws_node, context=context,
                                  seen_vocab=seen,
                                  goal_content=goal_set, goal_weight=goal_weight,
                                  voice_words=voice_words, voice_weight=voice_weight)
        ranked = pred.get("ranked") or []
        # pick the highest-ranked candidate not already emitted (no-repeat guard)
        pick = None
        pick_rank = -1
        for rank, (w, _lk) in enumerate(ranked):
            if no_immediate_repeat and w in emitted:
                continue
            pick = w
            pick_rank = rank
            break
        if pick is None:
            stop_reason = "exhausted"          # degeneracy: only repeats left
            break
        emitted.append(pick)
        steps.append({"word": pick, "source": pred["provenance"].get(pick, "?"),
                      "rank": pick_rank})
        # feed back: extend context + register with the emitted word (self-condition)
        context = (context + " " + pick).strip()
        if pick not in seen:
            seen.append(pick)
        # stop-on-goal-cover: once every goal word is out, allow a small voice tail
        if stop_on_goal_cover and goal_set and all(g in emitted for g in goal_set):
            covered_after += 1
            if covered_after > int(voice_headroom):
                stop_reason = "goal_covered"
                break

    covered = [g for g in goal_set if g in emitted]
    uncovered = [g for g in goal_set if g not in emitted]
    # repetition rate = fraction of emitted tokens that are duplicates (0 with the
    # no-repeat guard; measured anyway so a relaxed run surfaces degeneracy).
    dup = len(emitted) - len(set(emitted))
    repeat_rate = (dup / len(emitted)) if emitted else 0.0
    return {"tokens": emitted, "surface": " ".join(emitted), "steps": steps,
            "stop_reason": stop_reason, "goal_covered": covered,
            "goal_uncovered": uncovered, "repeat_rate": round(repeat_rate, 4)}


# --------------------------------------------------------------------------- #
#  PLAN-THEN-REALIZE (block 344). Per two literature reviews, the grounded sign-
#  grammar PRODUCER owns clause ORDER + admissible words as HARD CONSTRAINTS (the
#  frontier); the statistical ranker (predict_next_words) is DEMOTED to filling
#  OPEN slots only — it can never override a grammar-realized word or reorder the
#  clause. This REPLACES the reverted 'grammar as a heavily-weighted term in a
#  word-ranker' approach (which the reviews named as a known failure mode: a soft
#  feature that never guarantees order/coverage). Faithful to the substrate's own
#  analysis-by-synthesis identity: the comprehension grammar run in REVERSE owns
#  structure; prediction only fills the rest.
# --------------------------------------------------------------------------- #
def _gapfill_slot(agent, ws_node, concept, clause_context, emitted):
    """Fill ONE open grammar slot for `concept` via the statistical ranker,
    restricted to this position: predict_next_words conditioned on goal_content=
    [concept], returning its top1 surface (or None to keep the grammar placeholder).
    Single top1 per slot — a self-conditioned rollout for gap-fill is a LATER rung.
    ws_node None => no ranker available => return None (keep the placeholder)."""
    if ws_node is None:
        return None
    try:
        pred = predict_next_words(agent, ws_node, context=clause_context,
                                  seen_vocab=list(emitted),
                                  goal_content=[concept], goal_weight=4.0)
    except Exception:
        return None
    top1 = pred.get("top1")
    return top1 or None


def realize_goal_clause(agent, producer, goal_frame, *, ws_node=None,
                        language: str = "en", allow_fallback: bool = True,
                        intended_concepts=None, fallback_kwargs=None):
    """PLAN-THEN-REALIZE a communicative goal into an ORDERED grammatical clause.

    The grounded `producer` (a LanguageProduction from literary_analysis._build_
    producer) OWNS the clause: `producer.produce(language, goal_frame)` yields the
    grammar-ordered slot sequence (surface_structure.ordered_slots) and the per-slot
    realized surfaces (phonological_word.words, each {role,concept,surface,realized}).
    We emit that sequence IN ORDER:
      · realized == True  -> GRAMMAR-FIXED: emit the grammar's surface verbatim
        (source 'grammar'); the ranker is NEVER consulted for this position.
      · realized == False -> OPEN slot: the grammar left the bare concept as a
        placeholder; try to improve it via the ranker as a GAP-FILLER for THIS slot
        only (source 'gapfill'); keep the placeholder if the ranker offers nothing
        (source 'grammar_lemma'). Order and slot count are fixed by the grammar.

    FALLBACK (honest, reported): if produce() yields an empty clause (grammar
    coverage gap), degrade to the rung-1.5 self-conditioned rollout_unclamped and
    return mode='fallback' with the full fallback sub-result — never hidden.

    Returns {surface, tokens, backbone:[{role,concept,surface,realized,source}...],
    gaps_filled:[concept...], mode:'plan_then_realize'|'fallback',
    fallback:<rollout result|None>, verdict:<score_self_target|None>, produce:<raw>}.
    """
    frame = dict(goal_frame or {})
    frame.setdefault("intent", "inform")
    intended = list(intended_concepts or [])
    # PLAN: the grounded producer realizes the clause (grammar owns order).
    try:
        r = producer.produce(language, frame)
    except Exception:
        r = None
    words = ((r or {}).get("phonological_word") or {}).get("words") or []
    overt = ((r or {}).get("overt_speech") or "").strip()
    core = overt.rstrip(".!?").strip()

    # FALLBACK: no grammar clause -> rung-1.5 rollout (reported, not hidden).
    if not words or not core:
        if allow_fallback:
            gc = intended or [str(v) for k, v in frame.items()
                              if k in ("agent", "patient", "event") and v]
            fb = rollout_unclamped(agent, ws_node, goal_content=gc,
                                   **(fallback_kwargs or {}))
            return {"surface": fb["surface"], "tokens": fb["tokens"],
                    "backbone": [], "gaps_filled": [], "mode": "fallback",
                    "fallback": fb, "verdict": None, "produce": r}
        return {"surface": "", "tokens": [], "backbone": [], "gaps_filled": [],
                "mode": "empty", "fallback": None, "verdict": None, "produce": r}

    # REALIZE in grammar order; ranker fills OPEN slots only.
    backbone = []
    emitted = []
    gaps_filled = []
    for w in words:
        concept = w.get("concept")
        surface = w.get("surface")
        if w.get("realized"):
            src = "grammar"                       # grammar-fixed: verbatim
            out = surface
        else:
            ctx = " ".join(emitted)
            fill = _gapfill_slot(agent, ws_node, concept, ctx, emitted)
            # ONLY a genuine substitution (a surface DIFFERENT from the grammar's
            # placeholder) counts as gap-fill; if the ranker just re-picks the
            # placeholder concept, the grammar lemma stands (honest accounting).
            placeholder = surface or concept
            if fill and fill != placeholder:
                src, out = "gapfill", fill        # ranker improved the open slot
                gaps_filled.append(concept)
            else:
                src, out = "grammar_lemma", placeholder  # keep grammar placeholder
        backbone.append({"role": w.get("role"), "concept": concept,
                         "surface": out, "realized": bool(w.get("realized")),
                         "source": src})
        if out:
            emitted.append(out)

    # If no gap was filled, the pure grammar clause stands verbatim (its own
    # articulation/casing/terminator) — do not re-articulate.
    surface = overt if not gaps_filled else " ".join(emitted)

    # CHECK: grounded-comprehension parse-back (the outer self-monitor).
    verdict = None
    if intended:
        try:
            from domains.self_target_monitor import score_self_target
            verdict = score_self_target(agent, surface, intended,
                                        language=language, producer=producer)
        except Exception:
            verdict = None

    return {"surface": surface, "tokens": emitted, "backbone": backbone,
            "gaps_filled": gaps_filled, "mode": "plan_then_realize",
            "fallback": None, "verdict": verdict, "produce": r}


# --------------------------------------------------------------------------- #
#  THE COMPARE — a ShapeDecode COLLAPSE. The synthesized prediction is minted as a
#  codebook; the arriving words are DECODED against it; the `residual` field IS
#  the surprise (never a Python set-difference deciding it). The collapse
#  framework's "the model forms the manifold, the surprise lives in the residual".
# --------------------------------------------------------------------------- #
def _clear_prediction_codebook(sub, native) -> None:
    for n in list(sub.nodes(_PREDICTION_CODEBOOK_TYPE)):
        try:
            native.remove_node(n)
        except Exception:
            pass


def _mint_prediction_codebook(agent, predicted_words: list[str]) -> None:
    """Mint the SYNTHESIZED prediction as a ShapeDecode codebook: one
    ShapeSignaturePrediction node per predicted word, signature `[[word]]`. The
    prediction becomes the manifold the arriving signal collapses onto."""
    sub, native = _resolve(agent)
    _clear_prediction_codebook(sub, native)
    for w in predicted_words:
        sub.add_node(_PREDICTION_CODEBOOK_TYPE,
                     {"name": w, "signature": json.dumps([[w]])})


def _decode_actual_against_prediction(native, actual_uniq: list[str]) -> dict:
    """DECODE the arriving words (goal) against the prediction codebook — ONE
    ShapeDecode collapse (the SAME Term throughlines._decode / reflective_faculty.
    compose_design_for_goal fire). The `residual` is the SURPRISE; the covered
    parts are the CONFIRMED words. The decision is the decode's, read off its own
    `residual`, never a Python branch."""
    goal = [[w] for w in actual_uniq]
    term = {"type": "ShapeDecode",
            "goal": {"type": "Lit", "value": goal},
            "codebook_type": _PREDICTION_CODEBOOK_TYPE,
            "beam": 2, "max_steps": len(goal) + 2, "cand_k": max(8, len(goal) + 1)}
    res = native.evaluate(term, {})
    if not isinstance(res, dict):
        return {"plan": [], "residual": [list(g) for g in goal]}
    return res


def abs_compare(agent, predicted_words: list[str], actual_words: list[str]) -> dict:
    """The AbS compare: SYNTHESIZE→DECODE→RESIDUAL. Mint the predicted words as a
    ShapeDecode codebook, decode the arriving content words against it, and read
    the `residual` (the SURPRISE) off the collapse. LOW residual → the beat was
    predicted (fast confirm); the residual words are the deep, order-N material.

    Returns {confirmed, surprise, hit_rate, confirm_frac, n_predicted, n_actual}:
      * confirmed = arriving words the prediction covered (fast);
      * surprise  = the ShapeDecode residual (deep-processed);
      * hit_rate  = of the PREDICTED words, the fraction that actually arrived
        (did the synthesis land);
      * confirm_frac = of the arriving content words, the fraction confirmed
        (the fast-vs-deep split)."""
    sub, native = _resolve(agent)
    actual_uniq: list[str] = []
    for w in actual_words:
        if w and w not in actual_uniq:
            actual_uniq.append(w)
    _mint_prediction_codebook(agent, predicted_words)
    res = _decode_actual_against_prediction(native, actual_uniq)
    surprise = [r[0] for r in (res.get("residual") or []) if r]
    surprise_set = set(surprise)
    confirmed = [w for w in actual_uniq if w not in surprise_set]
    pred_set = [w for w in predicted_words if w]
    landed = [w for w in pred_set if w in set(actual_uniq)]
    hit_rate = (len(landed) / len(pred_set)) if pred_set else 0.0
    confirm_frac = (len(confirmed) / len(actual_uniq)) if actual_uniq else 0.0
    return {"confirmed": confirmed, "surprise": surprise,
            "hit_rate": hit_rate, "confirm_frac": confirm_frac,
            "landed": landed, "n_predicted": len(pred_set),
            "n_actual": len(actual_uniq)}


# --------------------------------------------------------------------------- #
#  NON-TOKENISED DISAMBIGUATION — the prediction biases perception. Same held
#  lattice decoder (segmentation-by-recognition, instruction_reading._lattice_
#  decode); the ONLY difference is the LEXICON: prediction-guided augments it with
#  the synthesized predicted words, so a noisy/un-spaced signal need only CONFIRM
#  the prediction. Bottom-up decodes against the base lexicon alone.
# --------------------------------------------------------------------------- #
def bottom_up_segment(agent, noisy_text: str) -> list[str]:
    """BOTTOM-UP: recognise the noisy signal against the agent's BASE lexicon
    alone (the held segmentation-by-recognition decoder, no prediction). This is
    the control the prediction-guided path must beat."""
    lex = ir.gather_lexicon(agent)
    decoded = ir._lattice_decode(noisy_text.lower(), lex)
    words = decoded[0] if isinstance(decoded, tuple) else decoded
    return [w for w in words if w.strip()]


def prediction_guided_segment(agent, predicted_words: list[str],
                              noisy_text: str) -> list[str]:
    """PREDICTION-GUIDED: recognise the SAME noisy signal against the base lexicon
    AUGMENTED with the synthesized predicted words — the prediction disambiguates
    the raw chars (they need only CONFIRM it, not be identified bottom-up). The
    SAME held lattice decoder; only the lexicon differs (the AbS bias).

    Two corruptions are disambiguated by the SAME prediction:
      * MISSING SPACE ('thebirdthankedher') — the augmented lexicon lets the
        lattice recover the run-together predicted words (0% -> 100%);
      * CHARACTER SUBSTITUTION ('the b1rd thanked her') — a token the base decode
        left OOV that is CONSISTENT at the CHARACTER grain with a predicted word
        (same length, char-substitution residual within tolerance) is recovered AS
        that prediction (comprehend_text.char_sub_recover — a graph-native
        per-position consistency check, the AbS residual one grain down, NOT a
        hardcoded typo table). Bottom-up cannot: with no prediction there is no
        codebook word to be consistent WITH."""
    lex = set(ir.gather_lexicon(agent))
    pred_lex: set[str] = set()
    for w in predicted_words:
        w = (w or "").lower().strip()
        if w:
            pred_lex.add(w)
    decoded = ir._lattice_decode(noisy_text.lower(), lex | pred_lex)
    words = decoded[0] if isinstance(decoded, tuple) else decoded
    out: list[str] = []
    for w in words:
        if not w.strip():
            continue
        if w in lex or w in pred_lex:
            out.append(w)                     # already recognised (missing-space path)
            continue
        rec = ct.char_sub_recover(w, list(pred_lex))   # char-substitution tolerance
        out.append(rec or w)
    return out


def segmentation_accuracy(recovered: list[str], truth: list[str]) -> float:
    """Position-wise recovery accuracy of a recognised word sequence against the
    true sequence — fraction of truth positions recovered exactly (the measure the
    two arms are scored on; a scoring read, not an agent decision)."""
    if not truth:
        return 0.0
    hits = sum(1 for i, t in enumerate(truth)
               if i < len(recovered) and recovered[i] == t)
    return hits / len(truth)


# --------------------------------------------------------------------------- #
#  THE AbS READING LOOP driven by cognitive_tick. A PredictiveReadingStage is
#  minted; the seeded pr_dispatch rule dispatches it (a WriterStyle exists); the
#  predictive_read_advance Reflex runs ONE dispatched stage's thin executor
#  (predict → compare), marks it done. NO Python decision loop — the reflex
#  advances one stage per firing, the tick drives it (reading_drive precedent).
# --------------------------------------------------------------------------- #
def _advance_predictive_stage(ad) -> None:
    """The reflex RESPONSE (the I/O boundary, shaped exactly like reading_drive.
    _advance_unit_stage): advance ONE dispatched PredictiveReadingStage via the
    predict→compare faculties, mint the PredictiveRead result, mark it done. NO
    branch on graph state to pick a faculty — a single stage kind."""
    for st in ad.s.nodes("PredictiveReadingStage"):
        at = ad.s.node(st)["attrs"]
        if at.get("status") != "dispatched":
            continue
        ws_v = at.get("writer_style")
        ws_node = None
        for n in ad.s.nodes("WriterStyle"):
            if _v(n) == ws_v:
                ws_node = n
                break
        target = at.get("target_text") or ""
        context = at.get("context_text") or ""
        seen_vocab = json.loads(at.get("seen_vocab") or "[]")
        if ws_node is not None:
            pred = predict_next_words(ad, ws_node, context=context,
                                      seen_vocab=seen_vocab)
            actual = _content_words(ad, target)
            cmp = abs_compare(ad, pred["predicted_words"], _words(ad, target))
            rn = ad.s.add_node("PredictiveRead", {
                "target": target,
                "predicted": json.dumps(pred["predicted_words"]),
                "confirmed": json.dumps(cmp["confirmed"]),
                "surprise": json.dumps(cmp["surprise"]),
                "hit_rate": float(cmp["hit_rate"]),
                "confirm_frac": float(cmp["confirm_frac"]),
                "n_actual_content": float(len(actual))})
            try:
                ad.inner.add_edge_unchecked(ad.agent, "has_predictive_read", rn)
            except Exception:
                pass
        ad.s.set_attr(st, "status", "done")
        return                                    # one stage advanced per firing


def read_arc_predictively(agent, ws_node, arc_text: str, *,
                          context: str = "", seen_vocab: Optional[list[str]] = None,
                          max_ticks: int = 40) -> dict:
    """Read an arc by ANALYSIS-BY-SYNTHESIS, driven by cognitive_tick. Mints a
    PredictiveReadingStage (carrying the target arc + context + the accumulating
    register vocab + the WriterStyle); the seeded pr_dispatch rule dispatches it;
    the predictive_read_advance Reflex fires the predict→compare executor. Ticks to
    steady state; reads the minted PredictiveRead back out. NO hand-pump (no
    run_rules/fire_reflexes call), NO Python faculty sequence — the tick drives it.

    `seen_vocab` is the accumulating register (all word TYPES seen so far), carried
    graph-resident on the stage so the tick-driven predictor confirms the recurring
    structure/function words — the whole-first-pass predictive read."""
    from domains import reading_drive as rd
    from domains.reflective_faculty import _ensure_seed_chain
    sub, native = _resolve(agent)
    ad = rd._LAAdapter(sub)
    _ensure_seed_chain(ad.s, ad.inner, ad.agent, ("predictive_reading",))
    ad.register_reflex_response("predictive_read_advance",
                                lambda a: _advance_predictive_stage(a))
    st = ad.s.add_node("PredictiveReadingStage",
                       {"name": "predict_read", "status": "pending",
                        "writer_style": _v(ws_node),
                        "target_text": arc_text, "context_text": context,
                        "seen_vocab": json.dumps(list(seen_vocab or []))})
    ad.inner.add_edge_unchecked(ad.agent, "has_prediction_stage", st)

    last = None
    for _ in range(max_ticks):
        ad.cognitive_tick()
        now = tuple(sorted((ad.s.node(n)["attrs"].get("name"),
                            ad.s.node(n)["attrs"].get("status"))
                           for n in ad.s.nodes("PredictiveReadingStage")))
        if now == last:
            break
        last = now

    return read_predictive_reads(ad, target=arc_text)


def read_predictive_reads(agent, *, target: Optional[str] = None) -> dict:
    """Pure graph read of the minted PredictiveRead result (for gates/demos)."""
    sub, _ = _resolve(agent)
    out = None
    for n in sub.nodes("PredictiveRead"):
        at = dict(sub.node(n)["attrs"])
        if target is not None and at.get("target") != target:
            continue
        at["predicted"] = json.loads(at.get("predicted") or "[]")
        at["confirmed"] = json.loads(at.get("confirmed") or "[]")
        at["surprise"] = json.loads(at.get("surprise") or "[]")
        at["node"] = _v(n)
        out = at
    return out or {}


# --------------------------------------------------------------------------- #
#  VARIABLE-APERTURE DWELL — EFFORT FOLLOWS THE RESIDUAL (task 2). The reader does
#  not deep-process uniformly: it GLIDES (cheap confirm) where its model predicts
#  and DWELLS (the deep, order-N processing) where the residual spikes. The
#  per-sentence dwell budget is the ShapeDecode residual (the surprise), consumed
#  ONE deep-process step per tick — so the aperture opens exactly as wide as the
#  news. This is the omniglot variable-K dwell scheduler (RUN 11:
#  results/omniglot_gate_run11_dwell.log — "attention allocated to unpredictability
#  as a conserved budget") lifted from stroke shortlists to sentence residuals. The
#  dwell is GRAPH-DRIVEN: a DwellStage carries the budget, the seeded dw_dispatch
#  rule dispatches it, and the dwell_advance Reflex (seeds/reading_dwell.json)
#  drains it one unit per cognitive_tick — NO Python dwell loop.
# --------------------------------------------------------------------------- #
def _advance_dwell_stage(ad) -> None:
    """The reflex RESPONSE (the I/O boundary, shaped exactly like
    _advance_predictive_stage): consume ONE unit of a dispatched DwellStage's
    residual-derived budget per firing — mint one DeepProcess node (the deep,
    order-N work for one surprise word), increment `spent`, and mark the stage
    done when the budget drains. A budget-0 (fully-predicted) stage glides: it
    marks done on the first firing with no deep processing. NO branch on graph
    state to pick work — a single stage kind, one unit per firing."""
    for st in ad.s.nodes("DwellStage"):
        at = ad.s.node(st)["attrs"]
        if at.get("status") != "dispatched":
            continue
        spent = int(at.get("spent") or 0)
        budget = int(at.get("budget") or 0)
        if spent < budget:
            residual = json.loads(at.get("residual") or "[]")
            word = residual[spent] if spent < len(residual) else None
            dp = ad.s.add_node("DeepProcess", {"word": word, "order_n": 1.0,
                                               "stage": _v(st)})
            try:
                ad.inner.add_edge_unchecked(st, "deep_processed", dp)
            except Exception:
                pass
            ad.s.set_attr(st, "spent", spent + 1)
            if spent + 1 >= budget:
                ad.s.set_attr(st, "status", "done")
        else:
            ad.s.set_attr(st, "status", "done")
        return                                    # one unit consumed per firing


def read_arc_with_dwell(agent, ws_node, arc_text: str, *, context: str = "",
                        seen_vocab: Optional[list[str]] = None,
                        max_ticks: int = 200) -> dict:
    """Read an arc with an ADAPTIVE dwell: predict → AbS-compare → then DWELL on
    the residual, driven by cognitive_tick. The predict→compare is the held AbS
    collapse (the `residual` IS the surprise); the DWELL mints a DwellStage
    carrying the residual-sized budget, and the seeded dw_dispatch rule +
    dwell_advance Reflex drain it ONE deep-process step per tick (the variable
    aperture). Returns {confirmed, surprise, confirm_frac, residual_count, dwell,
    n_actual}: `dwell` is the number of deep-process ticks the graph spent — the
    effort ALLOCATED to this sentence's unpredictability. A glide sentence
    (residual 0) costs 0 dwell; a high-residual sentence dwells proportionally."""
    from domains import reading_drive as rd
    from domains.reflective_faculty import _ensure_seed_chain
    sub, native = _resolve(agent)
    ad = rd._LAAdapter(sub)
    # PREDICT + COMPARE — the AbS ShapeDecode collapse (the residual IS the surprise).
    pred = predict_next_words(ad, ws_node, context=context, seen_vocab=seen_vocab)
    cmp = abs_compare(ad, pred["predicted_words"], _words(ad, arc_text))
    residual = list(cmp["surprise"])
    # DWELL — the residual-sized budget, drained one deep-process step per tick.
    _ensure_seed_chain(ad.s, ad.inner, ad.agent, ("reading_dwell",))
    ad.register_reflex_response("dwell_advance", lambda a: _advance_dwell_stage(a))
    # A fresh adapter restarts the tick clock at 0, but the seed Reflex node's
    # `last_fired_tick` persists high from a prior sentence — which would suppress
    # firing until the clock caught up. Re-arm it so this sentence's dwell drains
    # from the first tick (mechanical clock I/O, not a decision).
    rfx = ad.reflex("dwell_advance")
    if rfx is not None:
        ad.inner.set_attr(rfx, "last_fired_tick", -(10 ** 9))
    st = ad.s.add_node("DwellStage",
                       {"name": "dwell_process", "status": "pending",
                        "budget": float(len(residual)), "spent": 0.0,
                        "residual": json.dumps(residual)})
    ad.inner.add_edge_unchecked(ad.agent, "has_dwell_stage", st)
    for _ in range(max_ticks):
        if ad.s.node(st)["attrs"].get("status") == "done":
            break                             # this sentence's budget is drained
        ad.cognitive_tick()
    spent = int(ad.s.node(st)["attrs"].get("spent") or 0)
    return {"confirmed": cmp["confirmed"], "surprise": residual,
            "confirm_frac": cmp["confirm_frac"], "residual_count": len(residual),
            "dwell": spent, "n_actual": cmp["n_actual"]}


def _pearson(xs: list[float], ys: list[float]) -> float:
    """Pearson correlation of two equal-length series (a scoring read, no agent
    decision). 0.0 when a series is constant (the uniform control) or too short."""
    n = len(xs)
    if n < 2 or n != len(ys):
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    if dx == 0 or dy == 0:
        return 0.0
    return num / (dx * dy)


def adaptive_dwell_pass(agent, text: str, *, sentences: Optional[list[str]] = None,
                        class_corpus: Optional[list[str]] = None,
                        max_ticks: int = 200) -> dict:
    """Stream `text` sentence by sentence with an ADAPTIVE, residual-driven dwell
    (task 2). Per sentence (past the cold start): PREDICT from the accumulating
    writer model, AbS-COMPARE, then DWELL on the residual — the deep-process effort
    allocated per sentence, drained one step per cognitive_tick (read_arc_with_
    dwell). Returns {steps, adaptive_r, uniform_r, total_dwell, total_uniform,
    saved}: `steps` is the per-sentence (residual_count, dwell) trace; `adaptive_r`
    is the correlation of per-sentence dwell with the residual (effort FOLLOWS the
    news); `uniform_r` is the same correlation for a CONTROL reader that dwells a
    CONSTANT (mean) budget every sentence (uncorrelated — effort NOT following the
    residual); `total_uniform` is the worst-case uniform effort (deep-process
    EVERY arriving word), and `saved` is what the adaptive reader glides past."""
    from domains import reading_collapse as rc
    sents = list(sentences) if sentences is not None else rc._split_sentences(text)
    class_register = (_class_register_from_corpus(agent, class_corpus)
                      if class_corpus else None)
    steps: list[dict] = []
    seen_vocab: list[str] = []
    for i in range(len(sents)):
        target = sents[i]
        content = _content_words(agent, target)
        if i == 0:                                       # COLD START — no model yet
            steps.append({"k": 1, "sentence": target, "cold_start": True,
                          "residual_count": len(content), "dwell": len(content),
                          "confirm_frac": 0.0, "n_actual": len(content)})
        else:
            seen = sents[:i]
            model = build_writer_model(agent, seen, class_register=class_register)
            r = read_arc_with_dwell(agent, model["writer_style"], target,
                                    context=" ".join(seen),
                                    seen_vocab=list(seen_vocab), max_ticks=max_ticks)
            steps.append({"k": i + 1, "sentence": target, "cold_start": False,
                          "residual_count": r["residual_count"], "dwell": r["dwell"],
                          "confirm_frac": r["confirm_frac"], "n_actual": r["n_actual"]})
        for w in _words(agent, target):                  # grow the register
            if w and w not in seen_vocab:
                seen_vocab.append(w)
    pred_steps = [s for s in steps if not s.get("cold_start")]
    res = [float(s["residual_count"]) for s in pred_steps]
    dwell = [float(s["dwell"]) for s in pred_steps]
    adaptive_r = _pearson(res, dwell)
    mean_dwell = (sum(dwell) / len(dwell)) if dwell else 0.0
    uniform_r = _pearson(res, [mean_dwell] * len(res))   # constant => 0.0
    total_dwell = int(sum(dwell))
    total_uniform = int(sum(float(s["n_actual"]) for s in pred_steps))
    return {"steps": steps, "adaptive_r": adaptive_r, "uniform_r": uniform_r,
            "total_dwell": total_dwell, "total_uniform": total_uniform,
            "saved": total_uniform - total_dwell,
            "n_predicted_sentences": len(pred_steps)}


# --------------------------------------------------------------------------- #
#  THE WHOLE FIRST PASS AS PREDICTION — the fluent-reading loop. The reader streams
#  the text SENTENCE BY SENTENCE. At EACH sentence the ACCUMULATING writer/audience/
#  context model PREDICTS the next sentence's words BEFORE reading them (the
#  production faculty forward); the arriving sentence is DECODED against that
#  prediction (the AbS ShapeDecode); the predicted words FAST-CONFIRM (low residual,
#  cheap) and the RESIDUAL is the NEWS — the words that drive the deep, order-N
#  processing. The writer model ACCUMULATES as the stream proceeds (each sentence
#  grows the recurring-beat surface AND the register vocabulary), so prediction
#  IMPROVES as the text goes on. The first pass stays ORDERED; each step is
#  predict → confirm → residual, driven by cognitive_tick (read_arc_predictively).
#
#  This lifts the AbS capstone from ONE arc to the WHOLE TEXT: reading is faster
#  GENERALLY (most text is partly predictable — the register + the recurring beat)
#  and comprehension focuses on the residual (the surprise = the news). The final
#  settled comprehension is UNCHANGED — prediction is the PROCESS, not the answer.
# --------------------------------------------------------------------------- #
def _word_types(agent, text: str) -> list[str]:
    """The distinct word TYPES of a text, in first-seen order (the recognizer's own
    tokens, function words included) — the material the accumulating register is
    grown from. A graph/lexicon read, never a hand list."""
    out: list[str] = []
    for w in _words(agent, text):
        if w and w not in out:
            out.append(w)
    return out


def predict_first_pass(agent, text: str, *, sentences: Optional[list[str]] = None,
                       class_corpus: Optional[list[str]] = None,
                       class_register: Optional[list[str]] = None,
                       max_ticks: int = 40) -> dict:
    """Stream `text` sentence by sentence as a PREDICTIVE first pass. Per sentence:
    (1) PREDICT it from the accumulating writer model (recurring beat harvested from
    the sentences seen so far) + the discourse context so far + the accumulating
    register vocabulary — the production faculty forward, via predict_next_words;
    (2) COMPARE to the arriving sentence — the AbS ShapeDecode collapse, the
    `residual` IS the surprise (read_arc_predictively, tick-driven); (3) the
    predicted words are CONFIRMED (fast), the residual words are the NEWS (deep).

    The FIRST sentence is the COLD START — no prior context to predict from, so it
    is all residual (100% news), the honest cold-start. Every later sentence is
    predict → confirm → residual.

    Returns {steps, aggregate}. `steps` is the per-sentence trace (predicted /
    confirmed / surprise / hit_rate / confirm_frac). `aggregate` measures the
    whole-text prediction hit-rate + the confirm-vs-deep-process split (the
    speedup = the fast-confirm fraction) + early-vs-late confirm (does the
    accumulating model improve prediction as the text proceeds)."""
    from domains import reading_collapse as rc
    sents = list(sentences) if sentences is not None else rc._split_sentences(text)
    # the CLASS-PRIOR register (task 1): harvest the writer-class vocabulary ONCE
    # from the class corpus (None => the thin model, unchanged behaviour). Threaded
    # into every sentence's writer model, so a reader who has read the class before
    # fast-confirms the common words from the start — a RICHER model reads FASTER.
    # An explicit `class_register` (e.g. the cross-text prior's context-selected
    # register) overrides; else it is harvested from `class_corpus`; else None
    # (the cold reader — byte-identical to the committed behaviour).
    if class_register is None and class_corpus:
        class_register = _class_register_from_corpus(agent, class_corpus)
    steps: list[dict] = []
    seen_vocab: list[str] = []
    for i in range(len(sents)):
        target = sents[i]
        actual = _words(agent, target)
        actual_uniq: list[str] = []
        for w in actual:
            if w and w not in actual_uniq:
                actual_uniq.append(w)
        if i == 0:                                       # COLD START — no prediction
            steps.append({"k": 1, "sentence": target, "predicted": [],
                          "confirmed": [], "surprise": list(actual_uniq),
                          "hit_rate": 0.0, "confirm_frac": 0.0,
                          "n_actual": len(actual_uniq),
                          "n_content": len(_content_words(agent, target)),
                          "cold_start": True})
        else:
            seen = sents[:i]
            context = " ".join(seen)
            model = build_writer_model(agent, seen, class_register=class_register)
            res = read_arc_predictively(agent, model["writer_style"], target,
                                        context=context, seen_vocab=list(seen_vocab),
                                        max_ticks=max_ticks)
            steps.append({"k": i + 1, "sentence": target,
                          "predicted": res.get("predicted") or [],
                          "confirmed": res.get("confirmed") or [],
                          "surprise": res.get("surprise") or [],
                          "hit_rate": float(res.get("hit_rate") or 0.0),
                          "confirm_frac": float(res.get("confirm_frac") or 0.0),
                          "n_actual": len(actual_uniq),
                          "n_content": len(_content_words(agent, target)),
                          "cold_start": False})
        for w in actual_uniq:                            # grow the register (mechanical)
            if w not in seen_vocab:
                seen_vocab.append(w)
    return {"steps": steps, "aggregate": _aggregate_first_pass(steps)}


# --------------------------------------------------------------------------- #
#  WEIGHTED FIRST PASS — the finer grain for PREDICTING WRITTEN TEXT. The flat
#  candidate SET (predict_first_pass: is the arriving word covered?) becomes a
#  weighted DISTRIBUTION: each arriving word carries a likelihood from the combined
#  source strengths, so the top-predicted word is the ARGMAX (not an arbitrary set
#  member), and the surprisal is GRADED (−ln p, continuous — not a binary confirm/
#  deep). Measured against a FLAT baseline (uniform over the SAME candidate set, the
#  no-ranking control): top-1 / top-k accuracy and PERPLEXITY. The distribution is
#  the held Plus/Argmax Terms; only the LM scoring aggregation is scalar arithmetic.
# --------------------------------------------------------------------------- #
def _accumulate_counts(agent, seen_counts: dict, seen_vocab: list, target: str) -> None:
    """Grow the accumulating register FREQUENCY (the register-source strength) — a
    mechanical count of the word types seen so far, the graph-resident unigram prior."""
    for w in _words(agent, target):
        if not w:
            continue
        seen_counts[w] = seen_counts.get(w, 0) + 1
        if w not in seen_vocab:
            seen_vocab.append(w)


def weighted_first_pass(agent, text: str, *, sentences: Optional[list[str]] = None,
                        class_corpus: Optional[list[str]] = None,
                        class_register: Optional[list[str]] = None, k: int = 3,
                        eps: float = 1e-3) -> dict:
    """Stream `text` sentence by sentence as a WEIGHTED-LIKELIHOOD first pass. Per
    sentence (past the cold start): build the accumulating writer model + register
    FREQUENCY, get the weighted distribution over the next words (predict_next_
    words), and score each arriving word — its likelihood, its graded SURPRISAL
    (−ln p, a held Term), whether it is the top-1 / top-k predicted. A FLAT baseline
    scores the SAME arriving words against a uniform distribution over the SAME
    candidate set (no ranking). Returns the top-1/top-k accuracy + perplexity for
    BOTH arms (the finer-grain headline) + the per-word surprisal trace."""
    sub, native = _resolve(agent)
    sents = list(sentences) if sentences is not None else rc._split_sentences(text)
    # an explicit `class_register` (e.g. the cross-text prior's context-selected
    # register) overrides; else harvested from `class_corpus`; else None (cold —
    # byte-identical to the committed behaviour).
    if class_register is None and class_corpus:
        class_register = _class_register_from_corpus(agent, class_corpus)
    seen_counts: dict = {}
    seen_vocab: list[str] = []
    per_word: list[dict] = []
    steps: list[dict] = []
    w_top1 = w_topk = f_top1 = f_topk = 0.0
    w_surp = f_surp = 0.0
    n = 0
    for i in range(len(sents)):
        target = sents[i]
        actual = [w for w in _words(agent, target) if w]
        if i == 0:
            steps.append({"k": 1, "sentence": target, "cold_start": True,
                          "n_words": len(actual)})
            _accumulate_counts(agent, seen_counts, seen_vocab, target)
            continue
        seen = sents[:i]
        pred = predict_next_words(agent,
                                  build_writer_model(agent, seen,
                                                     class_register=class_register)["writer_style"],
                                  context=" ".join(seen), seen_vocab=list(seen_vocab),
                                  register_freq=dict(seen_counts))
        dist = pred["likelihoods"]
        ranked = [w for w, _p in pred["ranked"]]
        N = len(ranked)
        row_surp: list = []
        for w in actual:
            in_set = w in dist
            pw = dist.get(w, eps) if in_set else eps          # weighted likelihood
            pf = (1.0 / N) if (in_set and N) else eps         # FLAT: uniform-over-set
            sw = surprisal(native, pw)
            sf = surprisal(native, pf)
            t1w = 1.0 if (ranked and ranked[0] == w) else 0.0
            tkw = 1.0 if w in ranked[:k] else 0.0
            t1f = (1.0 / N) if (in_set and N) else 0.0        # uniform expected top-1
            tkf = (float(min(k, N)) / N) if (in_set and N) else 0.0
            w_top1 += t1w; w_topk += tkw; f_top1 += t1f; f_topk += tkf
            w_surp += sw; f_surp += sf; n += 1
            row_surp.append((w, sw))
            per_word.append({"k": i + 1, "word": w, "p_weighted": pw,
                             "p_flat": pf, "surprisal": sw, "in_set": in_set,
                             "top1": bool(t1w), "topk": bool(tkw)})
        steps.append({"k": i + 1, "sentence": target, "cold_start": False,
                      "n_words": len(actual), "n_candidates": N,
                      "top1_word": ranked[0] if ranked else None,
                      "surprisals": row_surp})
        _accumulate_counts(agent, seen_counts, seen_vocab, target)
    ppl_w = math.exp(w_surp / n) if n else 0.0
    ppl_f = math.exp(f_surp / n) if n else 0.0
    return {"per_word": per_word, "steps": steps, "n_words": n, "k": k,
            "top1_weighted": (w_top1 / n) if n else 0.0,
            "top1_flat": (f_top1 / n) if n else 0.0,
            "topk_weighted": (w_topk / n) if n else 0.0,
            "topk_flat": (f_topk / n) if n else 0.0,
            "perplexity_weighted": ppl_w, "perplexity_flat": ppl_f,
            "mean_surprisal_weighted": (w_surp / n) if n else 0.0,
            "mean_surprisal_flat": (f_surp / n) if n else 0.0}


def weighted_verse_first_pass(agent, lines: list[str], *, eps: float = 1e-3) -> dict:
    """Stream verse LINE by line as a weighted first pass, WITH meter/rhyme weights,
    and — in the SAME loop over the SAME lines — a BASELINE arm without them. Per
    line: build the accumulating model; harvest the RHYME line-end candidates
    (metrical_reading.predict_line_end, run forward off the accumulated endings) and
    give each a resonance-strength meter weight; the GUIDED distribution folds those
    weights in (predict_next_words meter_weights=), the BASELINE does not. Score each
    arriving word's surprisal in both arms. The meter/rhyme weights sharpen verse
    prediction: the guided mean surprisal is LOWER than the baseline (both numbers).
    Read-only over metrical_reading (its predict_line_end/rhyme_partner)."""
    from domains import metrical_reading as mr
    sub, native = _resolve(agent)
    ln = [l for l in (lines or []) if str(l).strip()]
    seen_vocab: list[str] = []
    seen_counts: dict = {}
    prior_endings: list[str] = []
    g_surp = b_surp = 0.0
    n = 0
    ge_surp = be_surp = 0.0                       # LINE-END surprisal (the rhyme slot)
    ne = 0
    steps: list[dict] = []
    for i in range(len(ln)):
        target = ln[i]
        actual = [w for w in _words(agent, target) if w]
        ending = mr._last_word(target)
        ending = ending.lower().strip(".,;:?!\"'") if ending else None
        if i > 0:
            seen = ln[:i]
            context = " ".join(seen)
            ws = build_writer_model(agent, seen)["writer_style"]
            # meter/rhyme weights (the harmonic model run FORWARD off the accumulated
            # endings): the rhyme predicts the LINE-END word. A register word that
            # sound-RESONATES with an established ending is in the resonance class the
            # next line-end may fill; a recurring exact rhyme word is the strongest.
            # Weight = the resonance evidence (metrical_reading.rhyme_partner distance,
            # forward), never a hand coefficient. The boost is scaled by the register
            # mass so the predicted rhyme word competes with the frequent skeleton.
            rp = mr.predict_line_end(agent, prior_endings)
            scale = float(max(seen_counts.values()) if seen_counts else 1)
            mw: dict = {}
            for w in rp["candidates"]:                 # (a) recurring exact rhyme word
                w2 = (w or "").lower().strip(".,;:?!\"'")
                if w2:
                    mw[w2] = (float(prior_endings.count(w2)) + 1.0) * scale
            for w2 in list(seen_vocab):                # (b) the resonance CLASS
                if w2 in mw:
                    continue
                if mr.rhyme_partner(w2, prior_endings) is not None:
                    mw[w2] = scale
            base = predict_next_words(agent, ws, context=context,
                                      seen_vocab=list(seen_vocab),
                                      register_freq=dict(seen_counts))
            guid = predict_next_words(agent, ws, context=context,
                                      seen_vocab=list(seen_vocab),
                                      register_freq=dict(seen_counts), meter_weights=mw)
            row = []
            for w in actual:
                pb = base["likelihoods"].get(w, eps)
                pg = guid["likelihoods"].get(w, eps)
                sb = surprisal(native, pb)
                sg = surprisal(native, pg)
                b_surp += sb; g_surp += sg; n += 1
                row.append((w, sg, sb))
                if w == ending:                        # the rhyme slot — the lever
                    be_surp += sb; ge_surp += sg; ne += 1
            steps.append({"k": i + 1, "line": target, "surprisals": row,
                          "ending": ending,
                          "end_surprisal_guided": (sg if ending else None),
                          "end_surprisal_baseline": (sb if ending else None),
                          "rhyme_partner": (ending, mr.rhyme_partner(ending, prior_endings))
                          if ending else None})
        _accumulate_counts(agent, seen_counts, seen_vocab, target)
        if ending:
            prior_endings.append(ending)
    return {"steps": steps, "n_words": n, "n_line_ends": ne,
            "mean_surprisal_guided": (g_surp / n) if n else 0.0,
            "mean_surprisal_baseline": (b_surp / n) if n else 0.0,
            "perplexity_guided": math.exp(g_surp / n) if n else 0.0,
            "perplexity_baseline": math.exp(b_surp / n) if n else 0.0,
            "lineend_surprisal_guided": (ge_surp / ne) if ne else 0.0,
            "lineend_surprisal_baseline": (be_surp / ne) if ne else 0.0}


# --------------------------------------------------------------------------- #
#  VERSE PINCER — METER/RHYME AS A PREDICTIVE CONSTRAINT. Verse is the most
#  metrically-predictable text there is, and the reader's meter/rhyme faculty
#  (domains/metrical_reading.py) is a HARMONIC MODEL — a harmonic model PREDICTS.
#  The predictive first pass confirms ~25% of PROSE tokens (register + recurring
#  beat); on VERSE the meter/rhyme prediction CONSTRAINS the next tokens far
#  harder, so the confirm-fraction JUMPS above the prose baseline:
#
#    * RHYME predicts the LINE-END word — the strongest single predictor in verse
#      (metrical_reading.predict_line_end, run forward off the accumulated rhyme
#      partners): a formulaic / repeated line-end recurs exactly (word-confirm),
#      and any line-end that RESONATES with an established partner is confirmed at
#      the rhyme (sound) level even when the surface word is fresh.
#    * METER predicts the next STRESS (metrical_reading.predict_next_beat, the
#      temporal harmonic forward): the periodic template says which slots are
#      strong, so the recurring metrical function-word skeleton fast-confirms.
#
#  The prediction is the metrical_reading COLLAPSE run forward (graph-native — the
#  same ShapeDecode faculty, no hardcoded expected words); the compare/residual is
#  the SAME AbS ShapeDecode. PROSE is untouched: predict_first_pass is unchanged,
#  and the baseline arm below re-runs the identical line-level predictor WITHOUT
#  the meter/rhyme augmentation, so the boost is attributable purely to it.
# --------------------------------------------------------------------------- #
def predict_verse_first_pass(agent, lines: list[str], *, max_ticks: int = 40) -> dict:
    """Stream verse LINE by line as a predictive first pass, WITH meter/rhyme
    prediction, and — in the SAME loop, over the SAME arriving lines — a BASELINE
    arm that predicts identically MINUS the meter/rhyme augmentation. Per line:
    (1) BASELINE predicted = the accumulating writer model (recurring beat +
    discourse context + register), exactly the prose predictor; (2) GUIDED
    predicted = baseline + the RHYME line-end candidates (predict_line_end) + the
    METER-forward stress template; (3) COMPARE each to the arriving line via the
    AbS ShapeDecode collapse; (4) accumulate the rhyme partners + register.

    Returns {steps, guided, baseline}: `steps` is the per-line trace (both
    confirm fractions + the rhyme partner, if any); `guided`/`baseline` are the
    aggregate confirm fractions. The meter/rhyme-guided confirm-fraction is the
    verse boost; the baseline is the plain first-pass on the SAME lines."""
    from domains import metrical_reading as mr
    ln = [l for l in (lines or []) if str(l).strip()]
    steps: list[dict] = []
    seen_vocab: list[str] = []
    prior_endings: list[str] = []
    tot_a = tot_cg = tot_cb = 0
    for i in range(len(ln)):
        target = ln[i]
        actual = _words(agent, target)
        actual_uniq: list[str] = []
        for w in actual:
            if w and w not in actual_uniq:
                actual_uniq.append(w)
        ending = mr._last_word(target)
        ending = ending.lower().strip(".,;:?!\"'") if ending else None
        if i == 0:                                       # COLD START — no prior lines
            steps.append({"k": 1, "line": target, "cold_start": True,
                          "n_actual": len(actual_uniq),
                          "confirm_frac_baseline": 0.0, "confirm_frac_guided": 0.0,
                          "rhyme_partner": None})
        else:
            seen = ln[:i]
            context = " ".join(seen)
            model = build_writer_model(agent, seen)
            base_pred = predict_next_words(agent, model["writer_style"],
                                           context=context,
                                           seen_vocab=list(seen_vocab))
            base_words = list(base_pred["predicted_words"])
            # --- METER/RHYME AUGMENTATION (the verse pincer) --------------- #
            guided_words = list(base_words)
            rp = mr.predict_line_end(agent, prior_endings)
            for w in rp["candidates"]:                   # RHYME line-end candidates
                w = (w or "").lower().strip(".,;:?!\"'")
                if w and w not in guided_words:
                    guided_words.append(w)
            partner = mr.rhyme_partner(ending, prior_endings) if ending else None
            # METER forward (the temporal harmonic): run the recognized periodic
            # foot forward — the strong-beat slots predict the NEXT stresses, so a
            # mismatch is a felt dropped stress. Reported as the mechanism; the
            # metrical function-word skeleton it predicts already recurs via the
            # register, so its marginal WORD-confirm over baseline is small (the
            # rhyme is the word lever — reported honestly).
            try:
                patt = mr.line_to_stress(target)["pattern"]
                predicted_stress = mr.predict_next_beat(
                    patt[:-1], patt[-2:] if len(patt) >= 2 else patt, 1)["predicted"]
            except Exception:
                predicted_stress = None
            cmp_g = abs_compare(agent, guided_words, _words(agent, target))
            cmp_b = abs_compare(agent, base_words, _words(agent, target))
            g_confirmed = list(cmp_g["confirmed"])
            g_surprise = list(cmp_g["surprise"])
            # RHYME-LEVEL LINE-END CONFIRM — the true rhyme lever. When the
            # arriving line-end is a FRESH word (bottom-up surprise) but its rime
            # RESONATES with an established partner, the rhyme PREDICTED it: the
            # reader expected a word in that resonance class, so the line-end is
            # confirmed at the sound level, not deep-processed. This is the
            # disambiguating power of the harmonic model on verse (prose has no
            # rhyme partner, so this never fires there).
            rhyme_confirmed = False
            if partner is not None and ending and ending in g_surprise:
                g_surprise.remove(ending)
                g_confirmed.append(ending)
                rhyme_confirmed = True
            n_a = len(actual_uniq)
            cf_g = (len(g_confirmed) / n_a) if n_a else 0.0
            steps.append({"k": i + 1, "line": target, "cold_start": False,
                          "n_actual": n_a,
                          "confirm_frac_baseline": float(cmp_b["confirm_frac"]),
                          "confirm_frac_guided": float(cf_g),
                          "confirmed_guided": g_confirmed,
                          "surprise_guided": g_surprise,
                          "predicted_stress": predicted_stress,
                          "rhyme_confirmed_end": ending if rhyme_confirmed else None,
                          "rhyme_partner": (ending, partner) if partner else None})
            tot_a += n_a
            tot_cg += len(g_confirmed)
            tot_cb += len(cmp_b["confirmed"])
        for w in actual_uniq:
            if w not in seen_vocab:
                seen_vocab.append(w)
        if ending and ending not in prior_endings:
            prior_endings.append(ending)
        elif ending:
            prior_endings.append(ending)                 # keep repeats (frame return)
    guided = (tot_cg / tot_a) if tot_a else 0.0
    baseline = (tot_cb / tot_a) if tot_a else 0.0
    return {"steps": steps, "guided": guided, "baseline": baseline,
            "n_lines": len(ln), "total_words": tot_a,
            "total_confirmed_guided": tot_cg, "total_confirmed_baseline": tot_cb}


def _aggregate_first_pass(steps: list[dict]) -> dict:
    """Aggregate the whole-text prediction measures off the per-sentence trace (a
    scoring read, no agent decision): the confirm-vs-deep split over ALL arriving
    words, the mean per-sentence hit-rate, and the EARLY-vs-LATE confirm fraction
    (does the accumulating writer model improve prediction as the text proceeds)."""
    predicted_steps = [s for s in steps if not s.get("cold_start")]
    tot_actual = sum(s["n_actual"] for s in steps)
    tot_confirmed = sum(len(s["confirmed"]) for s in steps)
    tot_surprise = sum(len(s["surprise"]) for s in steps)
    confirm_frac = (tot_confirmed / tot_actual) if tot_actual else 0.0
    mean_hit = (sum(s["hit_rate"] for s in predicted_steps) / len(predicted_steps)
                if predicted_steps else 0.0)
    # early vs late: split the PREDICTED (non-cold) steps in half; the confirm
    # fraction over each half. A LATE > EARLY gap is the accumulating model paying.
    half = len(predicted_steps) // 2
    early, late = predicted_steps[:half], predicted_steps[half:]

    def _cf(rows):
        a = sum(r["n_actual"] for r in rows)
        c = sum(len(r["confirmed"]) for r in rows)
        return (c / a) if a else 0.0

    return {"n_sentences": len(steps),
            "n_predicted_sentences": len(predicted_steps),
            "total_words": tot_actual,
            "total_confirmed": tot_confirmed,
            "total_surprise": tot_surprise,
            "confirm_frac": confirm_frac,           # the fast-confirm fraction = speedup
            "deep_process_frac": (tot_surprise / tot_actual) if tot_actual else 0.0,
            "mean_hit_rate": mean_hit,
            "early_confirm_frac": _cf(early),
            "late_confirm_frac": _cf(late)}


__all__ = ["build_writer_model", "read_writer_model", "predict_next_words",
           "abs_compare", "bottom_up_segment", "prediction_guided_segment",
           "segmentation_accuracy", "read_arc_predictively",
           "read_predictive_reads", "_advance_predictive_stage",
           "_mint_prediction_codebook", "predict_first_pass",
           "predict_verse_first_pass", "_aggregate_first_pass", "_word_types",
           "_class_register_from_corpus", "read_arc_with_dwell",
           "adaptive_dwell_pass", "_advance_dwell_stage", "_pearson",
           "weighted_first_pass", "weighted_verse_first_pass", "surprisal",
           "_source_strengths", "_combine_score", "_recurring_ngram_counts"]

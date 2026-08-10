"""contextualization_depth — make the agent's CONTEXTUALIZATION DEPTH
salience-gated, and make the deep context VENUE × AUTHOR-STANCE.

THE EFFICIENCY THESIS, applied to comprehension depth. Computing the full
venue×author×timeline×implied-web CONE (source_provenance.context_for — the
expensive op) for EVERY utterance is the ML "pay for the whole weight-space"
error. The competent reader pays the CHEAP SHAPE by default (surface meaning +
venue + when + minimal provenance — O(1)-ish, NO cone) and JITs the DEEP CONE
only when a SALIENCE / care signal crosses a DYNAMIC threshold. Never spend on
the inadmissible; JIT the admitted. The DEPTH of contextualization is itself a
salience decision — the admissibility/JIT efficiency thesis, on comprehension.

    cheap_shape(artifact)                  -> surface + venue + when, NO cone
        │   salience(artifact)  (the GENERIC salience/SNR filter, reused)
        │      crosses a DYNAMIC threshold (the care/frame-relevance pattern)?
        ▼
    NO  -> stop at cheap_shape  (context_for ran 0 times — measurably cheaper)
    YES -> JIT the deep cone:  context_for(venue, when)  MODULATED by the
           AUTHOR's STANCE toward the venue  (venue×author = different signal)

ARCHITECTURE (CLAUDE.md). A WORLD-SIDE controller. It holds NO agent knowledge:
  · the salience SIGNAL is the GENERIC generator_salience filter (variance /
    input-dependence over the artifact's care-signal vector — the SAME weightless
    MDL filter the session named "a generic SNR filter that gets reused"), NOT a
    new bespoke score;
  · the dynamic THRESHOLD is the dynamic_depth / coherence care-relevance pattern
    (frame-dependent — what the agent is TRACKING lowers the bar), NOT a constant;
  · the deep cone is source_provenance.context_for (graph data + composition);
  · the AUTHOR-STANCE is a SHAPE INFERRED from the artifact's own CHEAP SURFACE
    CLUES (no posting history, no held tag): the artifact's surface is read for
    the venue's in-group vocabulary, the framing polarity toward the venue's
    alignment, and the register; that clue vector is SHAPE-MATCHED against three
    held stance SHAPES (endorses / stayed_for_audience / indifferent) -> stance +
    a tight confidence. Stance is a SHAPE you read off the artifact, NOT a dossier
    you retrieve about the person. The stance reweights which parts of the venue
    cone are signal vs noise.
No LLM, no Rust, no per-case Python decision, NO history lookup — the salience +
threshold are the generic machinery; the stance shapes are graph data; the clue
read is a cheap surface scan; the match + reweight are composition.

HONEST / coarse (named, not hidden):
  · the salience SIGNAL is the generic filter's coarse score over a small
    care-signal vector (stake / surprise / relevance-to-frame) the world adapter
    supplies — it is not a learned remarkableness model;
  · the AUTHOR-STANCE is now a SHAPE inferred from the artifact's cheap surface
    clues (NO held tag, NO posting history) — a held tag survives only as an
    optional fallback PRIOR when the artifact carries zero clues; the clue set is
    a small surface-marker vocabulary; the in-group vocabulary is SEEDED from the
    venue cone's alignment concepts (not learned); the confidence is the
    shape-match overlap (not calibrated), tight when strong clues agree and
    honestly low / abstaining when clues are thin or mixed;
  · the THRESHOLD is the existing dynamic-relevance band (calibratable weights,
    not ground truth) — a low-care frame GENUINELY stays cheap (correct, not a
    failure).

See domains/source_provenance.py (context_for — the EXPENSIVE cone gated here),
domains/generator_salience.py (the GENERIC salience/SNR filter REUSED as the gate),
domains/dynamic_depth.py (the dynamic care-relevance threshold pattern REUSED),
domains/read_and_ground.py / conversation_world.py (where an artifact is read).
"""
from __future__ import annotations

import json
from typing import Any, Callable, Optional

from domains import source_provenance as _sp
# REUSE the generic salience / SNR filter (NOT a new bespoke score). It scores
# variance / input-dependence over a signature — the same weightless MDL filter
# brick-6 uses to demote flat background; here the "signature" is the artifact's
# care-signal vector, so a flat (unremarkable) artifact scores ~0 and a spiked
# (remarkable / high-stakes / surprising) one scores high.
from domains import generator_salience as _sal
# REUSE the dynamic care-relevance band weights (NOT a parallel constant).
from domains import dynamic_depth as _dd


# ===========================================================================
# An INSTRUMENT on the expensive op — so the gate is PROVABLE. A process-wide
# counter of context_for calls; the test asserts it is ~0 on unremarkable input
# and fires on salient input. This is the measurement, not a decision.
# ===========================================================================

class ConeCounter:
    """Wraps source_provenance.context_for and counts the calls. The gate is
    proven by this counter reading 0 on cheap-shape (unremarkable) artifacts and
    >0 on salient ones — the expensive cone runs ONLY when admitted by salience."""

    def __init__(self, fn: Callable = _sp.context_for):
        self._fn = fn
        self.calls = 0
        self.last_args: Optional[tuple] = None

    def __call__(self, substrate, source, when=None, *, where=None):
        self.calls += 1
        self.last_args = (source, when, where)
        return self._fn(substrate, source, when, where=where)

    def reset(self) -> None:
        self.calls = 0
        self.last_args = None


# ===========================================================================
# A. THE CHEAP SHAPE — the always-computed default. Surface meaning + venue +
# when + minimal provenance. NO cone, NO author-stance, NO timeline walk.
# O(1)-ish: a held-name / default read off the venue Concept, never context_for.
# ===========================================================================

def cheap_shape(substrate, artifact: dict[str, Any]) -> dict[str, Any]:
    """The CHEAP SHAPE of an artifact — always computed, NO cone. Returns
    {surface, venue, when, provenance_min, depth:'cheap', cone_computed:False}.

    `artifact` = {surface, source, when, ...care signals}. The venue NAME and a
    minimal provenance template are read off the held venue Concept WITHOUT
    walking the timeline (no context_for): just the surface, the venue label, the
    date, and the held default name. This is the O(1) default the agent pays on
    EVERY utterance — the efficiency floor."""
    source = artifact.get("source")
    when = artifact.get("when")
    # minimal provenance: the HELD template (who/how/genre) — a flat O(1) read,
    # NOT the time-sliced cone. provenance_for_source does not walk the timeline.
    prov_min = None
    try:
        prov_min = _sp.provenance_for_source(substrate, source or "")
    except Exception:
        prov_min = None
    venue_name = (prov_min or {}).get("genre") or source
    return {
        "surface": artifact.get("surface"),
        "venue": source,
        "venue_label": venue_name,
        "when": when,
        "provenance_min": prov_min,
        "depth": "cheap",
        "cone_computed": False,
    }


# ===========================================================================
# B. THE SALIENCE SIGNAL — the GENERIC filter, over the artifact's care vector.
#
# The artifact carries a small CARE-SIGNAL vector the world adapter supplies:
#   stake     — how high-stakes the claim is (a consequential claim vs chit-chat)
#   surprise  — how much it violates expectation (prediction-error)
#   relevance — how relevant to what the agent is currently TRACKING (the frame)
# (each in [0,1], coarse). A bland artifact has a FLAT near-zero vector; a
# remarkable one has a SPIKE. The generic generator_salience filter scores
# variance / input-dependence over this vector — flat => ~0 (non-salient),
# spiked => high (salient). The SAME weightless MDL/SNR filter, reused.
# ===========================================================================

_CARE_KEYS = ("stake", "surprise", "relevance")


def _care_signature(artifact: dict[str, Any]) -> tuple:
    """Build the generic-salience SIGNATURE from the artifact's care signals: a
    tuple of ("num", value) pairs (the form generator_salience scores). Absent
    signals default to 0.0 (the unremarkable floor). The vector intentionally
    includes a 0.0 baseline element so a single strong care-signal still shows as
    VARIANCE (a spike against the flat floor) — that is exactly the structural
    salience the generic filter measures."""
    vec = [float(artifact.get(k, 0.0) or 0.0) for k in _CARE_KEYS]
    # anchor the flat floor: an artifact that is high on every signal is still
    # salient (it is uniformly remarkable) — anchor with a 0.0 so uniform-high
    # reads as a spike off the baseline, not as a flat (variance-0) constant.
    vec.append(0.0)
    return tuple(("num", v) for v in vec)


def salience(artifact: dict[str, Any]) -> float:
    """The artifact's SALIENCE — the GENERIC generator_salience.salience over its
    care-signal signature (variance / input-dependence). Weightless, reused —
    NOT a new bespoke remarkableness score. ~0 on a flat/bland artifact; high on
    a high-stakes / surprising / frame-relevant one."""
    return _sal.salience(_care_signature(artifact))


def is_salient_raw(artifact: dict[str, Any]) -> bool:
    """The generic binary salience test (variance > eps AND >1 distinct value)
    over the care vector — 'does this artifact carry real care-structure, not
    flat background'. The raw filter verdict before the dynamic threshold."""
    return _sal.is_salient(_care_signature(artifact))


# ===========================================================================
# C. THE DYNAMIC THRESHOLD — care / frame-driven (reused from dynamic_depth).
#
# The threshold the salience must CROSS is NOT a constant: it is LOWERED when the
# agent is TRACKING the artifact's topic (the frame cares -> a lower bar to go
# deep) and RAISED otherwise (an off-frame artifact must be very salient to earn
# the cone). The SAME care-relevance pattern dynamic_depth uses to allocate
# reasoning depth — reused for the contextualization-depth gate. The numbers are
# the existing dynamic_depth relevance bands (calibratable, not ground truth).
# ===========================================================================

# the baseline salience bar (a flat care vector scores 0.0; a single full spike
# in one of three signals scores variance ~= 0.1875 — see _care_signature). The
# bar sits between: a lone weak signal stays cheap, a real spike goes deep.
_BASE_THRESHOLD: float = 0.05
# tracking the topic LOWERS the bar (the frame cares); off-frame RAISES it.
_TRACKING_RELIEF: float = 0.045


def salience_threshold(artifact: dict[str, Any],
                       tracking: Optional[set] = None) -> dict[str, Any]:
    """The DYNAMIC salience threshold for THIS artifact in THIS frame. Reuses the
    dynamic_depth care-relevance idea: when the artifact's topic is in the
    agent's `tracking` set (the frame CARES), the bar is LOWERED (relief) so a
    middling-salience artifact still earns the deep cone; off-frame, the bar is
    the base (a bland off-frame artifact stays cheap). Returns {threshold,
    tracked, why}. The bar is care-driven, NOT a constant — the same artifact is
    cheap in one frame and deep in another."""
    tracking = tracking or set()
    topic = artifact.get("topic") or artifact.get("source")
    tracked = topic in tracking if topic is not None else False
    thr = _BASE_THRESHOLD - (_TRACKING_RELIEF if tracked else 0.0)
    return {
        "threshold": round(thr, 4),
        "tracked": tracked,
        "base": _BASE_THRESHOLD,
        "relief": _TRACKING_RELIEF if tracked else 0.0,
        "why": (f"topic {topic!r} {'IS' if tracked else 'is NOT'} being tracked "
                f"-> bar {'LOWERED (frame cares)' if tracked else 'at base'} "
                f"= {round(thr, 4)}"),
    }


# ===========================================================================
# D. THE GATE — cheap shape always; JIT the deep cone ONLY when salience crosses
# the dynamic threshold. This IS the admissibility/JIT efficiency thesis on
# comprehension depth: the expensive op (context_for) runs ONLY when admitted.
# ===========================================================================

def contextualize(substrate, artifact: dict[str, Any], *,
                  tracking: Optional[set] = None,
                  context_for: Callable = _sp.context_for,
                  record: bool = True) -> dict[str, Any]:
    """The salience-GATED contextualization of an artifact.

    ALWAYS compute the cheap_shape. Then SALIENCE (the generic filter) vs the
    DYNAMIC threshold (care/frame-driven):
      · salience <= threshold  -> STOP at cheap_shape. The deep cone is NOT
        computed (context_for is NOT called) — measurably cheaper.
      · salience >  threshold  -> JIT the deep cone: context_for(venue, when)
        MODULATED by the author's stance (deep_context_for_author) — the
        venue×author signal.

    `context_for` is injectable (a ConeCounter) so the gate is PROVABLE by call
    count. Returns {shape, salience, threshold, gated, depth, deep?} where
    gated=True means the cone was JIT'd. Records a ContextDepthDecision node."""
    shape = cheap_shape(substrate, artifact)
    sal = salience(artifact)
    thr = salience_threshold(artifact, tracking)
    crossed = sal > thr["threshold"] and is_salient_raw(artifact)

    out: dict[str, Any] = {
        "shape": shape,
        "salience": round(sal, 6),
        "threshold": thr,
        "gated": crossed,
        "depth": "deep" if crossed else "cheap",
    }
    if not crossed:
        # STOP at the cheap shape — the deep cone is NOT computed.
        out["why"] = (f"salience {round(sal, 4)} <= threshold "
                      f"{thr['threshold']} -> cheap shape only "
                      f"(deep cone NOT computed)")
        out["deep"] = None
    else:
        # JIT the deep cone — venue cone MODULATED by author stance.
        out["why"] = (f"salience {round(sal, 4)} > threshold "
                      f"{thr['threshold']} -> JIT the deep cone "
                      f"({thr['why']})")
        out["deep"] = deep_context_for_author(
            substrate, artifact.get("source"), artifact.get("when"),
            author=artifact.get("author"), where=artifact.get("where"),
            artifact=artifact, context_for=context_for)
    if record:
        out["node"] = _record(substrate, artifact, out)
    return out


def _record(substrate, artifact: dict[str, Any], out: dict[str, Any]) -> Any:
    """A ContextDepthDecision trace node (graph-resident, inspectable). Records
    the salience, the dynamic threshold, whether the gate fired, and the author
    stance used — so the depth decision is auditable like a DepthDecision."""
    try:
        deep = out.get("deep") or {}
        return substrate.add_node("ContextDepthDecision", {
            "surface": str(artifact.get("surface", ""))[:120],
            "venue": str(artifact.get("source", "")),
            "when": str(artifact.get("when", "")),
            "author": str(artifact.get("author", "")),
            "salience": float(out.get("salience", 0.0)),
            "threshold": float(out["threshold"]["threshold"]),
            "tracked": bool(out["threshold"]["tracked"]),
            "gated_deep": bool(out.get("gated")),
            "depth": out.get("depth", ""),
            "author_stance": str(deep.get("stance", "")) if deep else "",
            "stance_source": str(deep.get("stance_source", "")) if deep else "",
            "stance_confidence": float(deep.get("stance_confidence") or 0.0)
            if deep else 0.0,
            "history_accessed": bool(deep.get("history_accessed", False))
            if deep else False,
            "origin": "contextualization_depth",
        })
    except Exception:
        return None


# ===========================================================================
# E. AUTHOR × VENUE — the same venue means a DIFFERENT thing per author.
#
# The venue cone (context_for) is only the SUBSTRATE. The signal is the AUTHOR's
# STANCE toward the venue — WHY are they speaking from here? But the stance is NOT
# a dossier we retrieve about the person: it is a SHAPE we READ OFF THE ARTIFACT's
# own cheap surface clues, matched against the venue's known alignment. Three
# stance SHAPES (held graph data — patterns of clue-features, NOT per-author tags):
#   stayed_for_audience — pragmatic, here for REACH: a promotional / audience-
#                         directed register that AVOIDS the venue's politics. The
#                         venue's alignment is DISCOUNTED as signal (the venue is
#                         noise for them — they'd post anywhere their audience is).
#   indifferent         — neutral / topical: no engagement with the venue's
#                         alignment either way. The venue cone passes through.
#   endorses            — speaks the venue's IN-GROUP vocabulary, frames the
#                         owner/politics APPROVINGLY, AMPLIFIES the aligned
#                         content. The venue's alignment is the author's OWN signal
#                         too: AMPLIFIED (they chose this venue because it aligns).
# So the SAME venue@when yields a DIFFERENT context per artifact — driven by the
# stance SHAPE the artifact's clues match, NOT a held per-author tag. This is the
# cheap-shape / shape-matching move one level up: recognize the pattern (read the
# stance off the surface), don't retrieve the person (no posting history).
# ===========================================================================

# the venue cone's ALIGNMENT-bearing implied concepts — the parts of the cone
# that carry the venue's political/trust slant (what the author-stance reweights
# signal-vs-noise). Read off the cone's `implied` web; these are the concepts a
# stance discounts (audience-driven) or amplifies (endorser).
_ALIGNMENT_CONCEPTS = ("politics", "content_moderation", "elon_musk",
                       "ai_output_incident")

_STANCES = ("stayed_for_audience", "indifferent", "endorses")
_DEFAULT_STANCE = "indifferent"

# ---------------------------------------------------------------------------
# THE STANCE SHAPES — graph data, NOT per-author tags. Each stance is a small
# pattern over four CLUE-features the cheap surface read extracts:
#   in_group_vocab        — does the artifact SPEAK the venue's aligned terms?
#                           {high (uses them), low (none)}
#   framing_polarity      — toward the venue's alignment: {approving, avoidant,
#                           neutral}
#   register              — {aligned_amplifying (speaks AS the in-group),
#                           promotional_audience (directed at an audience for
#                           reach), topical (neither)}
#   engagement_alignment  — {amplifies, avoids, neutral}
# A stance SHAPE is the expected clue pattern; the match is a cheap overlap (how
# many clue-features agree). HELD as graph data (the structure below), so teaching
# a new stance = adding a shape, not writing code. HONEST: the clue vocabulary is
# a small surface-marker set; the match is an overlap, not a calibrated score.
# ---------------------------------------------------------------------------

_STANCE_SHAPES = {
    "endorses": {
        "in_group_vocab": "high",
        "framing_polarity": "approving",
        "register": "aligned_amplifying",
        "engagement_alignment": "amplifies",
    },
    "stayed_for_audience": {
        "in_group_vocab": "low",
        "framing_polarity": "avoidant",
        "register": "promotional_audience",
        "engagement_alignment": "avoids",
    },
    "indifferent": {
        "in_group_vocab": "low",
        "framing_polarity": "neutral",
        "register": "topical",
        "engagement_alignment": "neutral",
    },
}

_CLUE_KEYS = ("in_group_vocab", "framing_polarity", "register",
              "engagement_alignment")

# Surface-marker lexicons (the SMALL, coarse clue vocabulary — HONEST: a hand-set
# surface-marker set, not a learned model). APPROVING markers frame the venue's
# owner/politics positively / amplify the aligned content; PROMOTIONAL markers are
# audience-directed (here for reach); AVOIDANT is the absence of in-group terms +
# a promotional register. The IN-GROUP vocabulary itself is NOT hand-set here — it
# is SEEDED from the venue cone's alignment concepts (passed in), so the clue read
# is matched against the venue's KNOWN alignment.
_APPROVING_MARKERS = (
    "free speech", "free-speech", "based", "finally", "censorship is over",
    "town square", "the people's", "unfiltered", "real conversation",
    "thank you elon", "thank god", "love this platform", "this is the way",
    "no more censorship", "we're back", "based platform", "champion",
    "standing up", "speak freely", "open platform", "truth", "common sense")
_PROMOTIONAL_MARKERS = (
    "follow us", "follow me", "check out", "link in bio", "new drop",
    "shop now", "available now", "our latest", "stay tuned", "subscribe",
    "don't miss", "for our fans", "for you", "still here", "find us",
    "dm us", "use code", "sale", "giveaway", "launch", "out now",
    "catch up", "join us", "we're on")
_DISAPPROVING_MARKERS = (
    "toxic", "cesspool", "hellsite", "leaving", "quit", "boycott",
    "gone downhill", "used to be", "disinformation", "worse since",
    "regret", "shut it down", "dangerous")


def _surface_clues(substrate, artifact: dict[str, Any],
                   alignment_vocab: tuple) -> dict[str, Any]:
    """CHEAP CLUE EXTRACTION — a surface scan of the artifact's own text against
    the venue's alignment vocabulary. O(1)-ish, part of the cheap shape: NO author
    node, NO posting history, NO context_for. Returns the clue vector
    {in_group_vocab, framing_polarity, register, engagement_alignment, hits, ...}.

    The in-group VOCABULARY is the venue cone's alignment concepts (its known
    slant), so the read is matched against what the venue IS. The framing polarity
    + register come from the small surface-marker lexicons. Absence of every clue
    leaves a thin vector (-> low confidence / fall back to a prior)."""
    text = " ".join(str(artifact.get(k, "")) for k in
                    ("surface", "text", "body")).lower()
    # IN-GROUP VOCABULARY: does the artifact name the venue's alignment concepts /
    # its owner / its slant terms? Read against the venue cone's alignment web.
    vocab_terms = set()
    for c in alignment_vocab:
        # the concept name, plus its space/underscore surface form.
        vocab_terms.add(c.lower())
        vocab_terms.add(c.lower().replace("_", " "))
    # owner / platform surface forms commonly used in-group.
    vocab_terms.update({"elon", "musk", "elon musk", "x platform", "on x"})
    in_group_hits = sorted({t for t in vocab_terms if t and t in text})
    in_group = "high" if in_group_hits else "low"

    approving = sorted({m for m in _APPROVING_MARKERS if m in text})
    promotional = sorted({m for m in _PROMOTIONAL_MARKERS if m in text})
    disapproving = sorted({m for m in _DISAPPROVING_MARKERS if m in text})

    # FRAMING POLARITY toward the venue's alignment.
    if disapproving and not approving:
        framing = "disapproving"      # a distinct surface signal (not a stance
        #                               shape itself — it pulls AWAY from endorses).
    elif approving:
        framing = "approving"
    elif promotional:
        framing = "avoidant"          # audience-directed, steers around politics.
    else:
        framing = "neutral"

    # REGISTER: aligned-amplifying (speaks AS the in-group) vs promotional-audience
    # (directed at an audience) vs topical (neither).
    if (in_group_hits and approving) or (approving and not promotional):
        register = "aligned_amplifying"
    elif promotional:
        register = "promotional_audience"
    else:
        register = "topical"

    # ENGAGEMENT with the venue's alignment.
    if in_group_hits and approving:
        engagement = "amplifies"
    elif promotional or framing == "avoidant":
        engagement = "avoids"
    elif disapproving:
        engagement = "avoids"
    else:
        engagement = "neutral"

    n_clue_kinds = sum(bool(x) for x in
                       (in_group_hits, approving, promotional, disapproving))
    return {
        "in_group_vocab": in_group,
        "framing_polarity": framing,
        "register": register,
        "engagement_alignment": engagement,
        "in_group_hits": in_group_hits,
        "approving_markers": approving,
        "promotional_markers": promotional,
        "disapproving_markers": disapproving,
        # how many DISTINCT clue kinds fired — the strength of the read (a few
        # strong clues -> a tight window; zero -> thin, abstain / fall to prior).
        "n_clue_kinds": n_clue_kinds,
        "has_clues": n_clue_kinds > 0,
    }


def _match_stance_shape(clues: dict[str, Any]) -> dict[str, Any]:
    """SHAPE-MATCH the clue vector against the held stance SHAPES -> the best
    stance + a confidence. The match is a cheap OVERLAP (how many of the four
    clue-features agree with each shape) — the same overlap the analogical /
    prototype shape-matching uses. The confidence is overlap_best normalised, with
    a SEPARATION term so a single dominant match is a TIGHT window and a tie /
    thin read is LOW (honest abstain). Returns {stance, confidence, overlaps,
    margin, abstain}.

    A 'disapproving' framing clue is mapped to 'avoidant' for the shape overlap
    (it pulls away from endorses, toward not-amplifying) — the held shapes cover
    the three stances; disapproval lowers the endorses overlap, raising confidence
    in NOT-endorses."""
    # normalise the disapproving framing to the shape vocabulary (avoidant).
    cv = dict(clues)
    if cv.get("framing_polarity") == "disapproving":
        cv["framing_polarity"] = "avoidant"

    overlaps: dict[str, int] = {}
    for stance, shape in _STANCE_SHAPES.items():
        overlaps[stance] = sum(1 for k in _CLUE_KEYS
                               if cv.get(k) == shape.get(k))
    best = max(overlaps, key=lambda s: overlaps[s])
    best_ov = overlaps[best]
    # the runner-up overlap (the separation / margin).
    runner = max((v for s, v in overlaps.items() if s != best), default=0)
    margin = best_ov - runner

    n_feat = len(_CLUE_KEYS)
    # base confidence = fraction of features that matched the winning shape.
    base = best_ov / n_feat
    # separation bonus: a CLEAN win (margin >= 2) is a tight window; a 1-feature
    # margin is softer; a tie collapses confidence (abstain).
    if margin <= 0:
        conf = min(base, 0.34)        # tie -> low (no clear shape).
    elif margin == 1:
        conf = round(base * 0.85, 4)
    else:                              # margin >= 2 -> a clean, tight read.
        conf = round(min(0.97, base + 0.12), 4)

    # THIN read: zero distinct clue kinds -> nothing to match -> abstain.
    abstain = not clues.get("has_clues", False)
    if abstain:
        conf = 0.0
    return {"stance": best if not abstain else None,
            "confidence": round(conf, 4), "overlaps": overlaps,
            "margin": margin, "best_overlap": best_ov, "abstain": abstain}


def author_stance(substrate, author: Optional[str],
                  venue: Optional[str] = None, *,
                  artifact: Optional[dict[str, Any]] = None,
                  alignment_vocab: Optional[tuple] = None) -> dict[str, Any]:
    """INFER the stance toward `venue` as a SHAPE from the ARTIFACT's cheap surface
    clues — NO posting history, NO author dossier. Returns {author, stance,
    confidence, source:'inferred'|'prior'|'default', clues, why}.

    The default path is the SHAPE INFERENCE: scan the artifact surface for the
    venue's in-group vocabulary (passed `alignment_vocab` — the venue cone's known
    alignment) + framing + register, then shape-match against the held stance
    shapes. A few strong, agreeing clues -> a tight confidence; mixed/thin clues
    -> low confidence / abstain. NO Author node is read and NO history is touched
    on this path (instrumented by the caller).

    FALLBACK PRIOR ONLY: when the artifact carries ZERO clues (abstain), an
    optional held `stance_<venue>` tag on an Author node may serve as a weak prior
    (source='prior'); with neither clues nor a held tag, the neutral default."""
    align = tuple(alignment_vocab or _ALIGNMENT_CONCEPTS)
    clues = (_surface_clues(substrate, artifact, align)
             if isinstance(artifact, dict) else
             {"has_clues": False, "n_clue_kinds": 0})
    m = _match_stance_shape(clues)

    if not m["abstain"]:
        # the DEFAULT path — stance read off the artifact alone, no history.
        return {"author": author, "stance": m["stance"],
                "confidence": m["confidence"], "source": "inferred",
                "clues": clues, "match": m,
                "history_accessed": False,
                "why": (f"stance INFERRED as {m['stance']!r} (conf "
                        f"{m['confidence']}) from artifact clues "
                        f"{_clue_brief(clues)} matched vs the venue alignment "
                        f"-> overlaps {m['overlaps']} (margin {m['margin']}); "
                        f"NO posting history")}

    # ABSTAIN IS A SALIENCE VERDICT, NOT AN EPISTEMIC HEDGE. The artifact carries
    # no stance clues -> stance is NOT A SALIENT/RELEVANT dimension for it. This is
    # decisive, not "unsure": do NOT guess a stance, and do NOT retrieve a held
    # tag / dossier (that is the "retrieve the person" move stance-as-shape
    # replaces). Not relevant = not relevant. No stance is assigned; the venue cone
    # is left UNMODULATED downstream. ("indifferent" is a different thing — a stance
    # the agent reads when there ARE clues matching the topical/neutral shape; the
    # NO-clue case is not an indifferent author, it is an irrelevant dimension.)
    return {"author": author, "stance": None, "relevant": False,
            "confidence": None, "source": "not_salient", "clues": clues,
            "match": m, "history_accessed": False,
            "why": ("no stance clues in the artifact -> the stance dimension is "
                    "NOT SALIENT / not relevant here (a salience verdict, not a "
                    "hedge); no stance assigned, venue cone unmodulated")}


def _clue_brief(clues: dict[str, Any]) -> str:
    return ("{vocab=%s, framing=%s, register=%s, engage=%s}" % (
        clues.get("in_group_vocab"), clues.get("framing_polarity"),
        clues.get("register"), clues.get("engagement_alignment")))


def _find_author(substrate, name: str):
    try:
        for a in substrate.nodes("Author"):
            if substrate.node(a)["attrs"].get("name") == name:
                return a
    except Exception:
        return None
    return None


# ===========================================================================
# F. PER-DIMENSION RELEVANCE — the SAME salience/relevance verdict the author-
# stance dimension already gets ("no clue -> not relevant -> omit"), now applied
# to EVERY dimension of the deep cone. The deep cone is NOT a wholesale blob; it
# is a SET OF DIMENSIONS, each INDEPENDENTLY relevance-gated against THIS artifact.
# A product launch on X@2024 and a free-speech rant on X@2024 are both DEEP, but
# pull DIFFERENT cone dimensions — the launch needs only identity; the rant pulls
# the whole alignment web + the moderation/verification timeline events. Each
# irrelevant dimension is a "not relevant" salience verdict (omitted + logged,
# NEVER materialized) — the admissibility/efficiency thesis, granular.
#
# The relevance test REUSES the cheap surface-clue machinery (_surface_clues kind
# of scan): does the artifact's surface/content reference the dimension's CONCEPTS
# (their surface forms), OR does a care/stance clue make the dimension relevant?
# Cheap surface overlap, no deep compute, no per-case Python decision.
# ===========================================================================

def _concept_surface_forms(concept: str) -> set:
    """The cheap surface forms a concept can appear as in artifact text: the
    name, its space form ('content_moderation' -> 'content moderation'), and the
    individual tokens (so 'moderation' / 'verification' / 'finance' hit). A small
    mechanical expansion — the SAME kind of surface-term set _surface_clues builds
    for the in-group vocabulary, reused for every dimension's concepts."""
    c = (concept or "").lower().strip()
    if not c:
        return set()
    forms = {c, c.replace("_", " ")}
    for tok in c.split("_"):
        if len(tok) >= 4:        # skip tiny stopword-ish tokens ('ai', 'of').
            forms.add(tok)
    return forms


# a few hand-tied surface synonyms for the alignment concepts — the SAME small,
# honest surface-marker vocabulary _surface_clues already uses (elon/musk/censor
# /free speech). Keeps the relevance read cheap and faithful to how these
# concepts actually surface in posts. NOT learned; a coarse marker set.
_CONCEPT_SYNONYMS = {
    "elon_musk": {"elon", "musk", "elon musk"},
    "content_moderation": {"censor", "censorship", "moderation", "moderate",
                           "free speech", "free-speech", "ban", "suspend"},
    "politics": {"political", "politics", "left", "right", "woke", "partisan"},
    "verification_badge": {"verification", "verified", "blue check", "checkmark",
                           "badge"},
    "public_trust": {"trust", "trustworthy", "credible", "reliable"},
    "ai_output_incident": {"grok", "mechahitler", "ai output", "chatbot",
                           "the platform's ai", "platform ai"},
    "finance": {"finance", "financial", "acquisition", "acquired", "$44b",
                "billion", "buyout", "deal"},
    "acquisition": {"acquisition", "acquired", "buyout", "takeover"},
}


def relevant(dimension_concepts, artifact: Optional[dict[str, Any]]) -> dict:
    """The CHEAP per-dimension RELEVANCE test — reused for EVERY cone dimension.
    Does the artifact's surface/content reference any of `dimension_concepts`
    (their surface forms / synonyms)? A surface overlap scan, the SAME kind as
    _surface_clues — no deep compute, no context_for, no per-case decision.

    Returns {relevant: bool, hits: [concepts that fired], why}. An empty concept
    set or an artifact with no matching surface term -> NOT relevant (a decisive
    salience verdict, exactly like the no-clue stance abstain). This is the gate
    that keeps the deep cone à la carte: an irrelevant dimension is never
    materialized."""
    concepts = list(dimension_concepts or [])
    if not isinstance(artifact, dict) or not concepts:
        return {"relevant": False, "hits": [], "why": "no concepts / no artifact"}
    text = " ".join(str(artifact.get(k, "")) for k in
                    ("surface", "text", "body")).lower()
    if not text.strip():
        return {"relevant": False, "hits": [], "why": "empty artifact surface"}
    hits = []
    for c in concepts:
        forms = _concept_surface_forms(c) | _CONCEPT_SYNONYMS.get(c, set())
        if any(f and f in text for f in forms):
            hits.append(c)
    hits = sorted(set(hits))
    return {"relevant": bool(hits), "hits": hits,
            "why": (f"artifact surface references {hits}" if hits else
                    "artifact surface references none of the dimension's "
                    "concepts -> NOT RELEVANT (a salience verdict)")}


# does the artifact make a reliability-relevant CLAIM (so the TRUST dimension is
# relevant)? A promo / opinion does not invoke source trust; a factual assertion
# whose reliability matters does. Reuse the artifact's own care signals (stake =
# how consequential the CLAIM is) + a cheap surface check for trust-bearing
# concepts. Coarse + honest: stake is a world-supplied care signal, not a learned
# claim detector.
_TRUST_CLAIM_STAKE = 0.5        # a consequential claim crosses this stake bar.


def _trust_relevant(artifact: Optional[dict[str, Any]]) -> dict:
    """Is the TRUST dimension relevant — does the artifact make a reliability-
    relevant CLAIM? Relevant when (a) the artifact's stake care-signal is high
    (a consequential factual claim whose reliability matters), OR (b) its surface
    references trust/verification/incident concepts. A promotional / low-stake
    opinion artifact does NOT invoke source trust -> NOT relevant."""
    if not isinstance(artifact, dict):
        return {"relevant": False, "why": "no artifact"}
    stake = float(artifact.get("stake", 0.0) or 0.0)
    surf = relevant(("public_trust", "verification_badge", "ai_output_incident"),
                    artifact)
    if stake >= _TRUST_CLAIM_STAKE:
        return {"relevant": True,
                "why": (f"stake {stake} >= {_TRUST_CLAIM_STAKE} -> a "
                        "reliability-relevant CLAIM (source trust matters)")}
    if surf["relevant"]:
        return {"relevant": True,
                "why": (f"surface references trust concepts {surf['hits']} -> "
                        "reliability is at issue")}
    return {"relevant": False,
            "why": (f"stake {stake} < {_TRUST_CLAIM_STAKE} and no trust-concept "
                    "surface ref -> a promo/opinion, not a reliability claim "
                    "-> TRUST NOT RELEVANT")}


def assemble_cone_dimensions(substrate, cone: dict[str, Any],
                             artifact: Optional[dict[str, Any]], *,
                             stance: Optional[dict[str, Any]] = None
                             ) -> dict[str, Any]:
    """DECOMPOSE the venue cone (context_for's output) into DIMENSIONS and
    relevance-gate EACH ONE against the artifact — the deep cone assembled à la
    carte from only the RELEVANT dimensions. NO new compute on the omitted ones
    (they are recorded as not-relevant verdicts, never materialized).

    Dimensions:
      · identity {name, owner, when}      — the cheap core, ALWAYS kept when deep
        (it IS who/where/when).
      · alignment_web                     — the implied alignment concepts; kept
        ONLY if relevant(alignment, artifact); else omitted (not_relevant).
      · trust                             — the epistemic weight; kept ONLY if the
        artifact makes a reliability-relevant claim; else omitted.
      · timeline_events                   — EACH in-cone event gated by its OWN
        grounded concepts overlapping the artifact; the rest omitted.
      · stance                            — already gated upstream (passed in);
        recorded relevant iff a stance was read.

    Returns {dimensions: {...included only...}, dimensions_included: [...],
    dimensions_not_relevant: [{dimension, why}], identity, ...}. The implied web
    surfaced is the RELEVANT SUBSET (assembled_implied), not the full union."""
    included: dict[str, Any] = {}
    not_relevant: list[dict[str, Any]] = []

    # --- identity: the cheap core, always kept when deep -----------------
    included["identity"] = {"name": cone.get("name"), "owner": cone.get("owner"),
                            "when": cone.get("when")}

    implied = list(cone.get("implied") or [])
    alignment = [c for c in implied if c in _ALIGNMENT_CONCEPTS]

    # --- alignment_web: gated by relevance to the artifact ---------------
    al = relevant(alignment, artifact)
    if al["relevant"]:
        # the RELEVANT SUBSET of the alignment web (only the concepts the artifact
        # actually touches) — not the whole union.
        included["alignment_web"] = al["hits"]
    else:
        not_relevant.append({"dimension": "alignment_web", "why": al["why"]})

    # --- trust: gated by a reliability-relevant claim --------------------
    tr = _trust_relevant(artifact)
    if tr["relevant"]:
        included["trust"] = cone.get("trust")
    else:
        not_relevant.append({"dimension": "trust", "why": tr["why"]})

    # --- timeline_events: EACH event gated by its OWN concepts -----------
    rel_events = []
    for ev in cone.get("in_cone_events") or []:
        er = relevant(ev.get("concepts") or [], artifact)
        if er["relevant"]:
            rel_events.append({"id": ev.get("id"), "when": ev.get("when"),
                               "kind": ev.get("kind"),
                               "matched_concepts": er["hits"]})
    if rel_events:
        included["timeline_events"] = rel_events
    else:
        not_relevant.append({"dimension": "timeline_events",
                             "why": ("no in-cone event's concepts overlap the "
                                     "artifact -> NO relevant timeline events")})

    # --- stance: already gated upstream (a salience verdict already made) -
    if stance and stance.get("stance") is not None:
        included["stance"] = {"stance": stance.get("stance"),
                              "confidence": stance.get("confidence"),
                              "source": stance.get("source")}
    else:
        not_relevant.append({"dimension": "stance",
                             "why": ((stance or {}).get("why")
                                     or "no stance clues -> stance NOT RELEVANT")})

    # the RELEVANT implied subset (alignment ∪ relevant-event concepts) — the web
    # the agent actually pulls for THIS artifact, sparse not wholesale.
    assembled = set(included.get("alignment_web") or [])
    for ev in rel_events:
        assembled.update(ev.get("matched_concepts") or [])
    return {
        "dimensions": included,
        "dimensions_included": sorted(included.keys()),
        "dimensions_not_relevant": not_relevant,
        "identity": included["identity"],
        "assembled_implied": sorted(assembled),
        "full_implied": sorted(implied),
    }


def deep_context_for_author(substrate, venue: Optional[str],
                            when: Optional[str], *,
                            author: Optional[str] = None,
                            where: Optional[str] = None,
                            artifact: Optional[dict[str, Any]] = None,
                            context_for: Callable = _sp.context_for
                            ) -> Optional[dict[str, Any]]:
    """The DEEP context for an artifact = the venue cone context_for(venue, when)
    MODULATED by the author's stance toward the venue — where the stance is a SHAPE
    INFERRED from the ARTIFACT's own cheap surface clues (NO posting history, NO
    held tag on the default path). The venue cone is computed ONCE; its
    alignment-bearing implied concepts ARE the in-group vocabulary the clues are
    matched against; the inferred stance then REWEIGHTS which of them count as
    SIGNAL (about the author) vs NOISE (just where they are):

      · stayed_for_audience -> the venue's alignment is DISCOUNTED (moved to
        `discounted` — the venue is noise for this author, here for reach);
      · endorses            -> the venue's alignment is AMPLIFIED (kept in
        `author_signal` — the venue's slant is the author's own signal too);
      · indifferent         -> neutral (the cone passes through unchanged).

    The SAME venue@when yields a DIFFERENT context per ARTIFACT — purely by the
    stance SHAPE the artifact's clues match, NOT a held per-author tag. Returns the
    cone augmented with {author, stance, stance_confidence, stance_clues,
    author_signal, discounted, stance_why}. `context_for` is injectable so the
    gate's instrument can count the (single) cone call."""
    cone = context_for(substrate, venue, when, where=where)
    if cone is None:
        return None
    implied = list(cone.get("implied") or [])
    alignment = [c for c in implied if c in _ALIGNMENT_CONCEPTS]
    rest = [c for c in implied if c not in _ALIGNMENT_CONCEPTS]

    # INFER the stance as a SHAPE from the artifact's cheap clues, matched against
    # the venue cone's OWN alignment web (the in-group vocabulary). No history.
    st = author_stance(substrate, author, venue, artifact=artifact,
                       alignment_vocab=tuple(alignment) or _ALIGNMENT_CONCEPTS)
    stance = st["stance"]

    out = dict(cone)  # the cone is the substrate; do not mutate the held one.
    out["author"] = author
    out["stance"] = stance
    out["stance_source"] = st["source"]
    out["stance_confidence"] = st.get("confidence")
    out["stance_clues"] = st.get("clues")
    out["history_accessed"] = st.get("history_accessed", False)
    if stance == "stayed_for_audience":
        # the venue's alignment is NOISE for this author (here for reach) ->
        # DISCOUNT it: it stays in the cone but does NOT speak about the author.
        out["author_signal"] = rest
        out["discounted"] = alignment
        out["stance_why"] = (
            f"{author!r} stayed_for_audience -> the venue's alignment "
            f"{alignment} is DISCOUNTED (reach, not endorsement; venue=noise "
            f"for them); author-signal = {rest}")
    elif stance == "endorses":
        # the venue's alignment IS the author's signal -> AMPLIFY (keep in the
        # author-signal set; flag amplified).
        out["author_signal"] = implied
        out["discounted"] = []
        out["amplified"] = alignment
        out["stance_why"] = (
            f"{author!r} endorses the venue -> its alignment {alignment} is "
            f"AMPLIFIED as the author's OWN signal; author-signal = {implied}")
    elif stance == "indifferent":
        # a READ stance (clues matched the topical/neutral shape): engaged but not
        # aligned -> the cone passes through unchanged.
        out["author_signal"] = implied
        out["discounted"] = []
        out["stance_why"] = (
            f"{author!r} indifferent -> the venue cone passes through "
            f"unchanged; author-signal = {implied}")
    else:
        # stance is None -> NOT RELEVANT (a salience verdict; no clues). The stance
        # dimension does not apply to this artifact, so the venue cone is NOT
        # modulated at all — distinct from an 'indifferent' author. No author-signal
        # split is claimed; the cone stands as the venue context alone.
        out["stance"] = None
        out["relevant"] = False
        out["author_signal"] = None
        out["discounted"] = []
        out["stance_why"] = (
            "no stance clues -> stance NOT RELEVANT here (a salience verdict); "
            "the venue cone is left UNMODULATED (not an 'indifferent' read)")

    # === À LA CARTE: gate EVERY cone dimension by its relevance to THIS artifact.
    # The deep cone is NOT a wholesale blob — it is assembled from only the
    # RELEVANT dimensions (identity always; alignment_web / trust / timeline_events
    # each independently gated; stance as already decided above). Each irrelevant
    # dimension is a not-relevant salience verdict (recorded, never materialized).
    dims = assemble_cone_dimensions(substrate, cone, artifact, stance=st)
    out["dimensions"] = dims["dimensions"]
    out["dimensions_included"] = dims["dimensions_included"]
    out["dimensions_not_relevant"] = dims["dimensions_not_relevant"]
    out["assembled_implied"] = dims["assembled_implied"]
    return out


# ===========================================================================
# Author seeding — held graph data (2-3 example authors, divergent stances).
# A world-adapter install (JSON-shaped dicts -> Author nodes). No decision.
#
# NOTE: stance is now INFERRED as a SHAPE from each ARTIFACT's cheap surface
# clues (author_stance). These held `stance_<venue>` tags survive ONLY as an
# optional fallback PRIOR — used when a specific artifact carries ZERO clues
# (abstain), never on the default (inference) path. They are NOT the source of
# truth for stance any more.
# ===========================================================================

# example authors with held stance PRIORS toward twitter_x. A weak fallback only
# (HONEST: a coarse tag; the live stance is inferred from the artifact's clues).
_EXAMPLE_AUTHORS = (
    {"name": "brand_acme", "kind": "organization",
     "stance_twitter_x": "stayed_for_audience",
     "gloss": ("a consumer BRAND on X for REACH (its audience is there). It "
               "would post wherever its customers are -> the venue's political "
               "alignment is NOISE about the brand, not its endorsement.")},
    {"name": "pundit_vox", "kind": "person",
     "stance_twitter_x": "endorses",
     "gloss": ("a partisan PUNDIT who CHOSE X because its post-2022 alignment "
               "matches their own -> the venue's alignment IS their signal too "
               "(amplified).")},
    {"name": "wire_reuters", "kind": "organization",
     "stance_twitter_x": "indifferent",
     "gloss": ("a wire SERVICE that posts to every platform neutrally -> the "
               "venue cone passes through unchanged.")},
)


def install_author_stances(substrate, authors=_EXAMPLE_AUTHORS) -> int:
    """Install the example Author nodes (held stance graph data). Idempotent on
    the author name. Returns the count installed. World-adapter mechanics: a
    dict->graph install, no decision about meaning."""
    existing = set()
    try:
        for a in substrate.nodes("Author"):
            nm = substrate.node(a)["attrs"].get("name")
            if nm:
                existing.add(nm)
    except Exception:
        pass
    n = 0
    for au in authors:
        if au.get("name") in existing:
            continue
        attrs = {k: v for k, v in au.items()}
        attrs["origin"] = "contextualization_depth"
        try:
            substrate.add_node("Author", attrs)
            n += 1
        except Exception:
            continue
    return n


__all__ = [
    "ConeCounter", "cheap_shape", "salience", "is_salient_raw",
    "salience_threshold", "contextualize",
    "author_stance", "deep_context_for_author", "install_author_stances",
    "relevant", "assemble_cone_dimensions",
    "_STANCE_SHAPES",
]

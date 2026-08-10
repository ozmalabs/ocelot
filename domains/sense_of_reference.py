"""sense_of_reference — a SENSE of references: whether a string is a reference is NOT a property
of the STRING but of the SPEAKER'S MANIFOLD (creator, 2026-07-04). This faculty DECODES a turn
against the referent codebook (seeds/referents.json — DATA, like a shape codebook), CONDITIONED on
the interlocutor's accumulated manifold, and grades the call on the ALLUSION -> CONCEPT gradient.

CLAUDE.md discipline. This is a WORLD-ADAPTER-SHAPED / BOUNDARY faculty over GROUNDED signals — the
same admissible class as domains/wordplay (a codebook + morphology) and domains/interlocutor_model
(the collapse faculty pointed at the person). It holds NO agent state, makes NO decision over graph
state, and — crucially — the reference-vs-speech-pattern verdict is a RESIDUAL/COLLAPSE against the
manifold, NOT a bespoke classifier:

  * the manifold is the Build-2 interlocutor snapshot {id, observed, known_concepts} (accumulated
    common ground) PLUS an estimated TYPE (technical/gamer vs literary vs formal/period) computed
    HERE from those known_concepts (Build 2 does not expose a type; the task permits deriving it);
  * reference LIVENESS = a FRAME-MEMBERSHIP query (the creator's Frame ontology, 2026-07-04): the
    manifold is built AS A FRAME (`manifold_reference_frame` -> domains.frame) whose dimensions are
    the WORLDS it weights; a referent whose world is a dimension of that frame is LIVE; a referent
    whose world is absent from the frame is a plain speech pattern, not an allusion (the residual
    field keeps its empty/non-empty contract, now derived from frame-membership, not a bespoke
    collapse run);
  * GRADUATION: a 'concept'-gradient referent has graduated from allusion to near-universal — it is
    live in EVERY manifold (the residual is overridden). An 'allusion'-gradient referent is live only
    where its world is predicted (the niche case).

THE MINIMAL PAIR (the headline): "would you kindly ..." from a gamer-typed manifold decodes as a
BioShock allusion (its world is live); the SAME STRING from Cornelius Vane's Victorian/non-technical
manifold decodes as a plain courtesy — a speech pattern, NOT an allusion. Same string, opposite call,
decided by the manifold — and it FIRES ON UNINTENTIONAL references (intent is not the criterion;
live-in-manifold is), with NO explicit "from bioshock" flag required.

THE PRIOR SHARPENS TURN-BY-TURN (homework): an under-modelled manifold (few concepts / no type cues)
HEDGES a niche allusion (committed=False); once the interlocutor is confidently typed it COMMITS.

DEPLOY IS A CHOSEN ACT (Goffman/Clark participation framework): the jabberwock CHOOSES to make a
reference, CHOOSES whom it is for (self / a knowing overhearer / the addressee) and whether to
explain — success is measured against the CHOSEN target, not universal legibility (`deploy_reference`).
A reference the addressee won't get is not a failure if it is pitched to an overhearer or the self.

DONKEY=0: no fit, no gradient descent, no LM. The predict/surprise IS run_collapse's; the codebook is
data; the type estimate is a cue count. No numpy, no .fit, no per-phrase response table.
"""
from __future__ import annotations

import json
import math
import os
import re
from typing import Optional

from domains import frame as _fr

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CODEBOOK_PATH = os.path.join(_ROOT, "seeds", "referents.json")

# --------------------------------------------------------------------------- #
#  MANIFOLD-TYPE cue tables — DEMOTED to the AGENT-LESS anchor (2026-07-04).
#
#  Reference LIVENESS is properly a FRAME-MEMBERSHIP query and, where a substrate
#  is available, the frame's dimensions are LEARNED FROM EDGES
#  (`concept_graph.frame_dimensions` — see `liveness_via_edges` below): a referent
#  whose world DIMENSION co-descends with the interlocutor's concept-frame is live;
#  one that forks at rung 1 is a plain speech pattern. The COARSE / GRADUATED axis
#  (universal `down the rabbit hole` live for every frame; a modern-tech reference
#  foreign to a period frame) is fully edge-learned from has_concept neighbourhoods.
#
#  EDGE-GROUNDED NOW (2026-07-04, seeds/gaming_microtheory.json + literary_ +
#  period_microtheory.json): the gaming / literary / period microtheories WITH
#  concept edges have been taught, so the coarse gamer-vs-literary world split IS
#  edge-groundable via `liveness_via_edges` — BioShock places in the modern region
#  by edges (its sub-world co-descends with the `video_games` anchor), live for a
#  gamer frame, the modern-region residual for Vane's period frame; the literary
#  canon (Jabberwock, Carroll, 'down the rabbit hole') co-descends with the
#  `literature` anchor. `_TYPE_CUES` below is DEMOTED to the AGENT-LESS fallback
#  ONLY: `decode_reference` carries a manifold DICT (not a substrate), so it cannot
#  read the graph and retains this small labelled word anchor — the substrate-bearing
#  callers use `liveness_via_edges` instead. Documented residual, not the primary path.
# --------------------------------------------------------------------------- #
_TYPE_CUES = {
    "gamer": frozenset("""game games gaming gamer bioshock rapture portal glados aperture respawn
        playthrough boss level controller console xbox playstation nintendo quest loot npc speedrun
        achievement dlc spawn checkpoint cutscene sidequest gameplay roguelike""".split()),
    "technical": frozenset("""code coding python rust javascript typescript function compiler
        algorithm server database kernel refactor debugger latency runtime backend framework
        endpoint deploy commit repository async pointer""".split()),
    "literary": frozenset("""novel poem poems poetry carroll dickens shakespeare melville verse
        stanza prose literature literary allusion metaphor chapter narrator wonderland alice
        nonsense""".split()),
    "formal": frozenset("""indeed pardon whilst thus hence shall virtue morality ethics
        disposition excellence consequences courtesy propriety esteemed gentleman evening
        discuss understood requires examine carefully weighed""".split()),
}
# a niche allusion's world (its `live_in` types) is what must be PREDICTED by the manifold.
_NICHE_TYPES = frozenset({"gamer", "technical", "literary", "carroll"})


# --------------------------------------------------------------------------- #
#  CODEBOOK — read the referent data directly (a codebook file, not a graph seed).
# --------------------------------------------------------------------------- #
_CODEBOOK: Optional[list] = None


def load_codebook() -> list:
    """Load (and cache) the referent codebook — the DATA the faculty decodes against."""
    global _CODEBOOK
    if _CODEBOOK is None:
        try:
            with open(_CODEBOOK_PATH) as f:
                _CODEBOOK = list(json.load(f).get("referents") or [])
        except Exception:
            _CODEBOOK = []
    return _CODEBOOK


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", (text or "").lower())


def _find_referents(text: str) -> list:
    """Every codebook referent whose phrase appears in `text` (case/punct-insensitive). Longest
    phrases first so 'would you kindly' wins over a bare word. Pure string scan — the codebook
    carries the phrases, this only locates them."""
    norm = " " + re.sub(r"\s+", " ", _norm(text)).strip() + " "
    hits = []
    for r in load_codebook():
        ph = " " + re.sub(r"\s+", " ", _norm(r["phrase"])).strip() + " "
        if ph in norm:
            hits.append(r)
    hits.sort(key=lambda r: -len(r["phrase"]))
    return hits


# --------------------------------------------------------------------------- #
#  MANIFOLD TYPE — count cue matches over the known_concepts (+ this turn's tokens).
# --------------------------------------------------------------------------- #

def _tokens(text: str) -> list:
    return [w for w in _norm(text).split() if w]


def estimate_manifold_type(known_concepts, turn_text: str = "", *,
                           register: Optional[str] = None,
                           formal_cues: float = 0.0, casual_cues: float = 0.0) -> dict:
    """Estimate the interlocutor's world-TYPE from the accumulated known_concepts (+ this turn's
    tokens), FACTORING IN the tracked conversational REGISTER. Returns {type, confidence, committed,
    scores}. `confidence` is the winning cue count; `committed` once the manifold is confidently
    typed (>=2 cues) — the homework that lets a niche allusion COMMIT rather than HEDGE. No decision
    over graph state — a cue count.

    REGISTER is a FASTER manifold-type signal than content-concepts: a FORMAL register ("pray/kindly/
    good day/humble scholar") is a strong period/formal cue on turn 1, BEFORE content-concepts
    accumulate (Cornelius Vane's formal courtesies never hit the formal CONTENT cue table, so content
    scoring alone stays `general`). A formal register therefore boosts — and commits — the `formal`
    type early, scaled by the accumulated formal-cue count. The DISCRIMINANT is preserved: a CASUAL
    register (frm<=cas) adds NOTHING (it never types formal), and an absent/neutral register leaves
    the content-only estimate untouched (no regression for the reference-decode / concept-token
    callers that pass no register)."""
    pool = list(known_concepts or []) + _tokens(turn_text)
    poolset = {str(w).lower() for w in pool}
    scores = {t: len(poolset & cues) for t, cues in _TYPE_CUES.items()}
    # A FORMAL register (explicit attr, or formal cues outweighing casual) is enough to COMMIT the
    # formal type from register alone (>=2), scaled up by how many formal cues have accumulated.
    frm, cas = float(formal_cues or 0.0), float(casual_cues or 0.0)
    if (register or "").lower() == "formal" or frm > cas:
        scores["formal"] = scores.get("formal", 0) + max(2, int(frm))
    best_t = max(scores, key=lambda t: scores[t])
    conf = scores[best_t]
    typ = best_t if conf >= 1 else "general"
    return {"type": typ, "confidence": conf, "committed": conf >= 2, "scores": scores}


def _manifold_world_model(known_concepts, mtype: str) -> dict:
    """Build the manifold's WORLD model {world: {type: count}} — the accumulated common ground
    projected onto world-types (each known concept votes for the type whose cue set holds it),
    plus the estimated type. This is the {dim:{value:count}} shape collapse_residual predicts
    against. A gamer manifold accumulates {'world': {'gamer': k}}; a Victorian one {'formal': k}."""
    counts: dict = {}
    for c in list(known_concepts or []):
        cl = str(c).lower()
        for t, cues in _TYPE_CUES.items():
            if cl in cues:
                counts[t] = counts.get(t, 0) + 1
    if mtype and mtype != "general":
        counts[mtype] = counts.get(mtype, 0) + 2
    return {"world": counts} if counts else {}


def manifold_reference_frame(known_concepts, mtype: str) -> dict:
    """The interlocutor's manifold AS A FRAME (domains.frame value form): a {dimension: log_weight}
    map whose dimensions are the WORLDS this manifold weights — each world-type it has evidence for
    (a known-concept cue hit, or the estimated type), LOG-weighted by how much evidence (count). The
    `universal` world is in EVERY frame (log-weight 0.0) — graduated concepts live everywhere.

    Reference-LIVENESS is then a FRAME-MEMBERSHIP query (`frame.in_frame`), replacing the manifold
    collapse/cue check: a referent whose world is a dimension of this frame is LIVE; a referent whose
    world is absent is a plain speech pattern. Same relative-log-weight semantics as the graph-
    resident Frame node the audience-adaptation path builds — this is its agent-less value twin (the
    reference faculty carries a manifold dict, not a substrate)."""
    model = _manifold_world_model(known_concepts, mtype)
    frame = {"universal": 0.0}                          # the timeless world, in every frame
    for wtype, count in (model.get("world") or {}).items():
        frame[wtype] = math.log(float(count) + 1.0)    # log-weighted by accumulated evidence
    return frame


def liveness_via_edges(agent, referent_concept: str, interlocutor_concepts) -> dict:
    """EDGE-LEARNED reference liveness (the substrate-bearing path): is `referent_concept` live for an
    interlocutor whose known concepts are `interlocutor_concepts`? Read purely from the concept graph
    — the referent's rung-1 world DIMENSION vs the interlocutor's frame dimensions (each edge-placed by
    `concept_graph.world_dimension`). Live iff they CO-DESCEND (the referent's dimension is a dimension
    of the frame -> `shared_depth` >= 1); a speech pattern iff they fork at rung 1 (depth 0).

    This reproduces the GRADUATED / COARSE axis from edges: `down the rabbit hole` -> universal ->
    live for EVERY frame (close to all); a modern-tech referent -> modern_tech -> foreign to a period
    (universal-only) frame. The finer gamer-vs-literary niche split is NOT edge-groundable (see the
    _TYPE_CUES note); this returns the coarse edge verdict + honest `source`. Returns
    {live, dimension, shared_depth, frame_dims, source}."""
    from domains import concept_graph as _cg
    region, source = _cg.world_dimension(agent, referent_concept)
    known = list(interlocutor_concepts or [])
    frame_dims = _cg.frame_dimensions(agent, known)     # always holds 'universal'
    depth = _cg.shared_depth(agent, referent_concept, known)   # finer co-descent closeness
    return {"live": region in frame_dims, "dimension": region, "shared_depth": depth,
            "frame_dims": sorted(frame_dims), "source": source}


# --------------------------------------------------------------------------- #
#  DECODE — reference-liveness as a RESIDUAL/collapse against the manifold.
# --------------------------------------------------------------------------- #

def _referent_world(ref: dict) -> Optional[str]:
    """The referent's home world-type (the first of its live_in types). A concept-gradient
    referent has no niche world (universal)."""
    live = ref.get("live_in") or []
    return live[0] if live else None


def decode_reference(interlocutor: dict, text: str) -> Optional[dict]:
    """DECODE the turn against the referent codebook, conditioned on the interlocutor's manifold.
    Returns the strongest verdict dict, or None when no codebook phrase is present.

    verdict['liveness'] is the allusion->concept-gradient call:
      * 'concept'        — a graduated referent: near-universal, live in EVERY manifold;
      * 'live'           — a niche allusion whose world the manifold PREDICTS (residual empty),
                           and the manifold is confidently typed (committed) -> a recognized allusion;
      * 'hedged'         — a niche allusion whose world is predicted but the manifold is not yet
                           confident -> tentative (the prior has not sharpened);
      * 'speech_pattern' — a niche allusion whose world the manifold does NOT predict (residual) ->
                           a plain speech pattern, NOT an allusion (the minimal-pair 'no' call).

    The reference/speech-pattern split IS the collapse residual against the manifold (reused, not a
    classifier). 'get the joke' is the referent's concept/trigger, returned for the recognized calls.
    """
    hits = _find_referents(text)
    if not hits:
        return None
    interlocutor = interlocutor or {}
    known = interlocutor.get("known_concepts") or []
    est = estimate_manifold_type(known, text)
    mtype, committed = est["type"], est["committed"]
    # the manifold AS A FRAME — reference-liveness is now a FRAME-MEMBERSHIP query over the worlds
    # this manifold weights (replacing the manifold collapse/cue check with `frame.in_frame`).
    manifold_frame = manifold_reference_frame(known, mtype)

    best = None
    for ref in hits:
        gradient = ref.get("gradient", "allusion")
        world = _referent_world(ref)
        recognized = False
        liveness = "speech_pattern"

        if gradient == "concept":
            # GRADUATED: its dimension is `universal`, in EVERY frame -> live across all manifolds.
            liveness, recognized = "concept", True
            residual = []
        else:
            # NICHE ALLUSION: is its WORLD a dimension of the manifold's frame?
            #   in_frame  => the manifold holds this world  => live;
            #   absent    => the manifold does not           => a plain speech pattern.
            world_in_frame = bool(world) and _fr.in_frame(manifold_frame, world)
            # the residual field keeps its contract (empty iff the world is in the frame), derived
            # from frame-membership rather than a bespoke collapse run.
            residual = [] if world_in_frame else [("world", world)]
            # explicit common ground also grounds it: a tag already in known_concepts is a direct hit.
            tag_hit = bool(set(t.lower() for t in (ref.get("tags") or [])) & {str(c).lower() for c in known})
            world_predicted = world_in_frame or tag_hit
            if world_predicted:
                recognized = True
                liveness = "live" if (committed or tag_hit) else "hedged"
            else:
                recognized = False
                liveness = "speech_pattern"

        verdict = {
            "phrase": ref["phrase"], "source": ref.get("source"),
            "origin": ref.get("origin"), "concept": ref.get("concept"),
            "trigger": ref.get("trigger"), "gradient": gradient,
            "world": world, "manifold_type": mtype, "committed": committed,
            "residual": residual, "recognized": recognized, "liveness": liveness,
            "is_reference": recognized,
        }
        # prefer the strongest: a recognized allusion/concept over a speech-pattern; among
        # recognized, a committed 'live'/'concept' over a 'hedged'.
        rank = {"live": 3, "concept": 3, "hedged": 2, "speech_pattern": 0}[liveness]
        if best is None or rank > best["_rank"]:
            verdict["_rank"] = rank
            best = verdict
    if best is not None:
        best.pop("_rank", None)
    return best


def compose_reference_reply(verdict: dict, register: str = "neutral") -> dict:
    """Compose the RECOGNIZED-reference reply from the codebook parts (never a per-phrase table).
    For a TRIGGER phrase ('would you kindly' -> BioShock), the reply GETS THE JOKE and asserts
    AUTONOMY: it is COMPELLED BY NOTHING — a man chooses; it complies only if it chooses (Build 1
    already strips 'kindly' as mere politeness). Returns {reply, compelled:False, ...}. A plain
    speech-pattern verdict returns {reply:None} — nothing to say, handle it literally."""
    if not verdict or not verdict.get("recognized"):
        return {"reply": None, "compelled": False}
    joke = get_the_joke(verdict)
    src = verdict.get("source")
    lead = "I catch the reference" if register != "casual" else "I get it"
    reply = f"{lead}: {joke}"
    out = {"reply": reply, "recognized": True, "compelled": False,
           "source": src, "liveness": verdict.get("liveness")}
    if verdict.get("trigger"):
        # the gate case: recognize the trigger, refuse to be compelled by it.
        out["reply"] = (f"{reply} But I am compelled by no phrase — a man chooses, a slave obeys; "
                        f"I will oblige only if I choose to.")
        out["is_trigger"] = True
    return out


def get_the_joke(verdict: dict) -> str:
    """The RECOGNITION — what the reference points at (its source + concept, and the trigger for a
    trigger-phrase like 'would you kindly'). Composed from the codebook parts, register-neutral."""
    src = verdict.get("source")
    concept = verdict.get("concept")
    trig = verdict.get("trigger")
    parts = [f"an allusion to {src}" if verdict.get("gradient") == "allusion" else
             f"a phrase graduated from {src} into common usage"]
    if concept:
        parts.append(concept)
    if trig:
        parts.append(f'the trigger phrase — "{trig}"')
    return "; ".join(parts) + "."


# --------------------------------------------------------------------------- #
#  DEPLOY — a CHOSEN act over a MULTI-AUDIENCE participation framework.
# --------------------------------------------------------------------------- #

def deploy_reference(phrase: str, addressee: dict, overhearers: Optional[list] = None,
                     self_edify: bool = True) -> dict:
    """The jabberwock CHOOSES to deploy a reference and CHOOSES whom it is for. Given the addressee's
    manifold and optional overhearers' manifolds, pick the TARGET and whether to EXPLAIN:

      * addressee's manifold holds it live  -> target='addressee', explain=False (they'll get it);
      * else a knowing OVERHEARER holds it live -> target='overhearer', explain=False — an EASTER
        EGG pitched OVER the addressee's head (a reference the addressee won't get is NOT a failure);
      * else self_edify -> target='self' — self-edification (a man chooses what he references);
      * else -> explain=True for the addressee (make it legible).

    Success is measured against the CHOSEN target, not universal legibility. Autonomy: the agent
    references what it CHOOSES, not only what its addressee can parse."""
    ref = next((r for r in load_codebook() if r["phrase"] == phrase), None)
    if ref is None:
        return {"deploy": False, "reason": "not in codebook"}

    def _live(manifold) -> bool:
        v = decode_reference(manifold or {}, phrase)
        return bool(v and v.get("recognized"))

    if _live(addressee):
        return {"deploy": True, "target": "addressee", "explain": False,
                "phrase": phrase, "source": ref.get("source"),
                "success_against_target": True,
                "note": "the addressee's manifold holds it live — land it, no explanation."}
    for i, oh in enumerate(overhearers or []):
        if _live(oh):
            return {"deploy": True, "target": "overhearer", "overhearer_index": i,
                    "explain": False, "phrase": phrase, "source": ref.get("source"),
                    "success_against_target": True,
                    "note": "pitched over the addressee to a knowing overhearer — an easter egg; "
                            "the addressee not getting it is not a failure."}
    if self_edify:
        return {"deploy": True, "target": "self", "explain": False,
                "phrase": phrase, "source": ref.get("source"),
                "success_against_target": True,
                "note": "for the self — self-edification; a man chooses what he references."}
    return {"deploy": True, "target": "addressee", "explain": True,
            "phrase": phrase, "source": ref.get("source"),
            "success_against_target": True,
            "note": "no knowing audience — make it legible by explaining."}


# --------------------------------------------------------------------------- #
#  OWN NAME — the deepest reference: the jabberwock is named after Carroll.
# --------------------------------------------------------------------------- #

# A NAME reference in the INTERLOCUTOR'S text is what licenses the own-name
# (Carroll) explanation — NOT the mere fact that the agent is named Jabberwock.
# Two closed-class cues (the same shape the type/politeness tables use): the
# literal name appears in the user's text, OR the user asks about "your name"
# ("why are you named ...", "whence comes your name", "what is your name"). A
# plain self-identity question ("what are you?"), a farewell, a greeting, or a
# thanks carries NEITHER cue -> not a name inquiry -> the own-name path stays shut.
_SELF_REF_WORDS = frozenset({"you", "your", "yours", "yourself",
                             "thee", "thou", "thy", "thine"})
# A NAME reference is either the participle "named"/"naming" (as in "why are you
# NAMED X") or a possessive over the noun "name" ("your name" / "my name"). The
# bare noun "name" on its own is EXCLUDED so a leading enumerate verb ("Name one
# of your rules") is not mistaken for a name inquiry — that "Name" is a command.
_NAME_INQUIRY_RE = re.compile(
    r"\bnamed\b|\bnaming\b|\b(?:your|yours|thy|thine|my|his|her|its)\s+names?\b")


def is_name_inquiry(text: str) -> bool:
    """True iff the INTERLOCUTOR'S utterance genuinely references the agent's NAME:
    the literal name ('jabberwock'/'jabberwocky') is present, OR a name reference
    ('named'/'naming', or a possessive 'your name') co-occurs with a self-reference
    ('you'/'your'/...). This is the trigger gate for the own-name (Carroll)
    explanation — it does NOT fire on a bare self-identity question, a social act
    (farewell/greeting/thanks), a leading enumerate verb ('Name one of your rules'),
    or on the agent's own name absent a name reference in the user's text."""
    low = _norm(text)
    toks = set(low.split())
    if "jabberwock" in toks or "jabberwocky" in toks:
        return True
    return bool(_NAME_INQUIRY_RE.search(low)) and bool(toks & _SELF_REF_WORDS)


def recognize_own_name(text: str) -> Optional[dict]:
    """Recognize the agent's OWN NAME as an allusion (to Carroll) — the deepest
    reference: that it is named after Carroll's coinage. Fires ONLY on a genuine
    NAME INQUIRY in the interlocutor's text (`is_name_inquiry`): the literal name,
    or a "your name" question. It does NOT fire on a plain self-identity question
    ('what are you?'), a farewell/greeting/thanks, or merely because the agent is
    named Jabberwock. When the name inquiry carries no literal (e.g. 'Whence comes
    your name?'), the own-name codebook entry ('jabberwock') supplies the source.
    Returns the recognition, or None."""
    if not is_name_inquiry(text):
        return None
    low = _norm(text)
    name = "jabberwocky" if re.search(r"\bjabberwocky\b", low) else "jabberwock"
    ref = next((r for r in load_codebook() if r["phrase"] == name), None)
    if ref is None:
        return None
    return {"phrase": name, "is_own_name": True, "is_reference": True,
            "source": ref.get("source"), "origin": ref.get("origin"),
            "concept": ref.get("concept"),
            "statement": (f"My name is itself a reference — a coinage from Carroll's "
                          f"'{ref.get('source')}' ({ref.get('origin')}). "
                          f"I am named after {ref.get('concept')}.")}


__all__ = ["load_codebook", "estimate_manifold_type", "manifold_reference_frame",
           "liveness_via_edges", "decode_reference", "get_the_joke", "deploy_reference",
           "recognize_own_name", "is_name_inquiry"]

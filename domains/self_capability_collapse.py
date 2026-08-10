"""self_capability_collapse — the agent's collapse loop turned INWARD on its OWN
COMPETENCE.  A SELF-CAPABILITY DomainPlug into the EXISTING collapse engine
(scripts/collapse_engine.run_collapse), the exact twin of move_space_collapse_plug
and interlocutor_collapse_plug — same predict -> surprise -> residual loop, pointed
at the agent's OWN faculties instead of a maze's transitions or a person's features.

Creator's frame: to self-IMPROVE, the agent must first PERCEIVE a gap in ITSELF —
notice a failing faculty, not only a gap in its world.  An external developer finds
those gaps by running the agent (a conversation) and reading the failures; this
module gives the agent THAT faculty, and it is the SAME cognition it already runs
on everything else — manifold collapse + residual, no new mechanism.

THE MAPPING (mirror of the two precedent plugs):

  symbols   : per CHALLENGE, a length-2 sequence
              ( ("FAC", faculty) , ("OUT", faculty, outcome_class) ).
              The revealed context is the faculty the challenge exercises; the
              "next symbol" the model must predict is the OUTCOME it expects.
  next_dist : the agent's PREDICTED COMPETENCE (from its self-model / the faculties
              it claims).  For a faculty it CLAIMS it predicts a SUBSTANTIVE outcome
              ({("OUT",fac,"substantive"): 1.0} — "I can handle this").  For a
              faculty it does NOT claim it returns {} (no prediction, no surprise —
              honestly, you are not surprised to fail at what you never claimed).
  on_gap    : the RESIDUAL read-off.  When the OBSERVED outcome (what the faculty
              actually produced this run) has ZERO predicted mass — i.e. the agent
              predicted competence but observed a FAILURE surface (silence / a bare
              social-ack / a repair ask-back) — run_collapse records a GAP.  That
              gap is the CAPABILITY GAP, localized to the faculty the challenge
              exercised (the challenge carries which faculty; the failure on it
              localizes the gap).

  gap  iff  observed-failure UNDER predicted-competence.  This is exactly
  run_collapse's `nd.get(true_next, 0.0) <= 0.0` test — a collapse residual, NOT a
  Python if/else that "decides" weakness.

THE OUTCOME OBSERVATION IS MECHANICAL BOUNDARY I/O.  `observe_outcome` reads the
faculty's reply string and classes it against the SAME failure surfaces the
conversation faculties already expose (test_conversation_loop.py): a bare social
acknowledgment ("noted"/"got it"/"understood"), a silence (None/empty), or a repair
ask-back ("...?" quoting the trouble source) when a SUBSTANTIVE result was expected.
Anything else is "substantive" = handled.  The classifier does not decide a gap — it
only translates the opaque reply into the outcome symbol the collapse loop consumes.

HONEST SCOPE.  This perceives gaps it can OBSERVE as BEHAVIORAL FAILURES on a
challenge battery — a faculty that returns a known-failure surface where the agent
claimed competence.  It does not (here) perceive latent gaps that never surface as a
bad reply, nor grade the QUALITY of a substantive reply beyond the failure-surface
boundary.  What it perceives, it perceives via the collapse residual, not a bespoke
classifier.

HAND-OFF.  A perceived gap is minted as a `CapabilityGap` graph node AND is a
well-formed groundable Concern: `gap_as_observation` renders the gap as a
relation-system that `reflective_faculty.induce_concern` (the composer's dequantize
loop) consumes as something to ground — the seam builds #3/#4 pick up.

DONKEY: the predict/surprise is run_collapse's, unchanged; this file supplies only
the plug (next_dist over claimed faculties, on_gap recording the residual) + the
mechanical outcome classifier + the graph mint.  No math.exp, no fit, no
same-vs-weak classifier — the DECISION is the collapse residual.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Optional

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.join(_ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from collapse_engine import DomainPlug, run_collapse   # the agent's domain-general collapse loop

_SEED_DIR = Path(_ROOT) / "seeds"
_BATTERY_PATH = _SEED_DIR / "self_challenge_battery.json"

SUBSTANTIVE = "substantive"

# The KNOWN-FAILURE surfaces the conversation faculties already expose (mirror of
# test_conversation_loop.py's assertions): a bare social acknowledgment, a silence,
# a repair ask-back where a substantive result was expected.  These are the ONLY
# non-substantive outcome classes; every one is a behavioral failure the boundary
# can read off the reply without interpreting its meaning.
BARE_ACK = {"noted", "acknowledgment", "acknowledgement", "got it", "understood",
            "ok", "okay", "sure", "mm", "mhm"}
SILENCE = "silence"
BARE_ACK_CLASS = "bare_ack"
REPAIR_CLASS = "clarify_repair"
FAILURE_CLASSES = (SILENCE, BARE_ACK_CLASS, REPAIR_CLASS)


# ==========================================================================
# SYMBOLS — the opaque length-2 sequence per challenge (mirror interlocutor's).
# ==========================================================================

def _fac_sym(faculty: str):
    return ("FAC", faculty)


def _out_sym(faculty: str, outcome: str):
    return ("OUT", faculty, outcome)


# ==========================================================================
# THE PLUG — predict competence, collapse the observed outcome against it.
# ==========================================================================

def make_plug(competence: dict, observations: dict) -> tuple:
    """Build the DomainPlug that collapses each challenge's OBSERVED outcome against
    the agent's PREDICTED COMPETENCE.

    `competence`   : {faculty: {"substantive": count}} — the faculties the agent
                     CLAIMS (predicts a substantive outcome for).  A faculty absent
                     here is unclaimed: no prediction, no surprise.
    `observations` : {faculty: outcome_class} — what the faculty ACTUALLY produced
                     this run (mechanical boundary read; see observe_outcome).

    Returns (plug, residual).  `residual` is the list on_gap fills with the
    (faculty, failure_class) pairs the model could NOT predict — the collapse
    residual == the perceived capability gaps.
    """
    targets = [(_fac_sym(f), _out_sym(f, o)) for f, o in observations.items()]
    pool = list(targets)
    seen = set(pool)
    # the pool also carries every PREDICTED outcome (the substantive hypotheses the
    # model expects), so the manifold ranges over predicted-vs-observed, exactly as
    # the interlocutor pool carries the model's known values.
    for f, oc in competence.items():
        for o in oc:
            s = (_fac_sym(f), _out_sym(f, o))
            if s not in seen:
                seen.add(s)
                pool.append(s)

    residual: list = []
    fired: set = set()

    def next_dist(ctx):
        # predict an outcome only once the faculty dimension is the revealed context.
        if not ctx:
            return {}
        last = ctx[-1]
        if not (isinstance(last, tuple) and last and last[0] == "FAC"):
            return {}
        faculty = last[1]
        oc = competence.get(faculty)
        if not oc:
            return {}                       # UNCLAIMED faculty -> no prediction, no surprise
        tot = float(sum(oc.values()))
        if tot <= 0.0:
            return {}
        return {_out_sym(faculty, o): n / tot for o, n in oc.items()}

    def on_gap(ctx, missing):
        # the residual: a faculty whose OBSERVED outcome the predicted competence
        # gave zero mass to == an observed failure under predicted competence.
        if not ctx:
            return
        last = ctx[-1]
        if not (isinstance(last, tuple) and last and last[0] == "FAC"):
            return
        faculty = last[1]
        outcome = missing[2] if (isinstance(missing, tuple) and len(missing) == 3) else missing
        key = (faculty, outcome)
        if key in fired:                    # dedup: run_collapse revisits k=1 across fractions
            return
        fired.add(key)
        residual.append(key)

    plug = DomainPlug(name="self_capability", pool=pool, train=pool, targets=targets,
                      seq_logprob=lambda seq: 0.0, next_dist=next_dist, on_gap=on_gap)
    return plug, residual


def collapse_residual(competence: dict, observations: dict) -> list:
    """Run the agent's collapse loop over each challenge's observed outcome against
    its predicted competence; return the residual — the (faculty, failure_class)
    pairs the model could not collapse (the perceived gaps).  This IS
    predict->surprise; the mint (graph node) + grounding (induce_concern) is the
    caller's read-off of this residual, the move_space/interlocutor precedent
    exactly.  Returns [] when every claimed faculty produced a substantive outcome
    (no surprise)."""
    if not observations:
        return []
    plug, residual = make_plug(competence, observations)
    seq_lp = {s: 0.0 for s in plug.pool}
    run_collapse(plug, seq_lp)              # predict + surprise; on_gap fills `residual`
    return residual


# ==========================================================================
# THE OUTCOME OBSERVATION — mechanical boundary: reply string -> outcome symbol.
# No decision about a gap here; only the opaque-form -> smallest-token translation
# the collapse loop consumes.
# ==========================================================================

def observe_outcome(reply: Optional[str], expect: str = SUBSTANTIVE) -> str:
    """Classify a faculty's reply into an outcome symbol by its SURFACE only.

    A None/empty reply is SILENCE; a reply that is exactly a bare social
    acknowledgment is BARE_ACK; a reply that ends in '?' when a SUBSTANTIVE result
    was expected is a REPAIR ask-back (the faculty deflected instead of producing).
    Anything else is SUBSTANTIVE (handled).  Pure string surface — the same failure
    surfaces test_conversation_loop.py asserts on."""
    if reply is None:
        return SILENCE
    r = str(reply).strip()
    if not r:
        return SILENCE
    norm = r.lower().rstrip(".!").strip()
    if norm in BARE_ACK:
        return BARE_ACK_CLASS
    if expect == SUBSTANTIVE and r.rstrip().endswith("?"):
        return REPAIR_CLASS
    return SUBSTANTIVE


# ==========================================================================
# THE CHALLENGE BATTERY + HARNESS — host marshaling (run the challenge, read the
# outcome, feed it to the collapse plug).  Mechanical throughout.
# ==========================================================================

def load_battery(path: Optional[str] = None) -> list:
    """Read the challenge battery (graph data / a seed manifest of Challenge items).
    Each challenge: {id, faculty, text, speech_act, expect, weak_stub?}.  A
    `weak_stub` names a deliberately-weak/absent faculty's canned failure surface
    (the synthetic stubbed-to-fail faculty) so the battery has a genuine failure
    even though the live agent handles most inputs — the outcome is still READ
    mechanically, the gap still the residual."""
    p = Path(path) if path else _BATTERY_PATH
    d = json.loads(p.read_text())
    return list(d.get("challenges") or [])


def _weak_stub_runner(surface: str) -> Callable:
    """A deliberately-weak faculty: it always emits its canned failure surface.
    Models a faculty the agent CLAIMS but cannot actually satisfy (the external-dev
    Vane-conversation gap).  Its reply is a real string the boundary classifier
    reads — the stub picks WHICH weak faculty runs, never whether a gap exists."""
    canned = {SILENCE: "", BARE_ACK_CLASS: "noted", REPAIR_CLASS: "what do you mean?"}
    reply = canned.get(surface, "")

    def run(_agent, _challenge):
        return reply
    return run


def run_challenge(agent, challenge: dict, runner: Optional[Callable] = None) -> dict:
    """Run ONE challenge through the agent's REAL faculty (converse by default) and
    read the outcome mechanically.  A challenge may carry `weak_stub` to route to a
    deliberately-weak faculty runner instead; an explicit `runner` overrides both.
    Returns {faculty, outcome, reply, expect}."""
    faculty = challenge.get("faculty") or challenge.get("id") or "unknown"
    expect = challenge.get("expect", SUBSTANTIVE)
    if runner is None:
        if challenge.get("weak_stub"):
            runner = _weak_stub_runner(challenge["weak_stub"])
        else:
            def runner(a, c):
                return a.converse(c.get("text", ""),
                                  c.get("speech_act", "statement"))
    try:
        reply = runner(agent, challenge)
    except Exception as e:
        reply = None
        return {"faculty": faculty, "outcome": SILENCE, "reply": None,
                "expect": expect, "error": f"{type(e).__name__}: {e}"}
    return {"faculty": faculty, "outcome": observe_outcome(reply, expect),
            "reply": reply, "expect": expect}


def run_battery(agent, battery: list, runner: Optional[Callable] = None) -> list:
    """Run every challenge; return the per-challenge outcome records.  The battery
    IS the agent's competence self-claim made concrete — each challenge is something
    it is EXPECTED to handle, so a failure on one is a genuine surprise."""
    return [run_challenge(agent, ch, runner=runner) for ch in battery]


# ==========================================================================
# THE MINT — a perceived gap becomes a CapabilityGap graph node (a Concern).
# ==========================================================================

def _resolve(agent):
    """(substrate, agent_root_node) — the SAME duck-typing the other plugs use."""
    sub = getattr(agent, "s", agent)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        try:
            for n in sub.nodes("Agent"):
                ag_node = n
                break
        except Exception:
            ag_node = None
    return sub, ag_node


def mint_capability_gap(agent, faculty: str, failure_class: str,
                        challenge: Optional[dict] = None) -> Any:
    """Mint (idempotent) a `CapabilityGap` node localized to `faculty`, carrying the
    observed failure surface + the challenge that exercised it.  The gap's own
    relation-system (`observation`) is stored so `induce_concern` can ground it.
    Wires `agent -perceives_gap-> gap`.  Returns the node id (existing or new)."""
    sub, ag_node = _resolve(agent)
    ch_id = (challenge or {}).get("id", "")
    ch_text = (challenge or {}).get("text", "")
    # idempotency key: one gap per (faculty, failure_class).
    for n in sub.nodes("CapabilityGap"):
        at = sub.node(n)["attrs"]
        if at.get("faculty") == faculty and at.get("failure_class") == failure_class:
            return n
    observation = gap_as_observation(faculty, failure_class, ch_id)
    gid = sub.add_node("CapabilityGap", {
        "faculty": faculty,
        "failure_class": failure_class,
        "challenge_id": ch_id,
        "challenge_text": ch_text,
        "observation": observation,
        "key": ["gap_" + faculty],
        "status": "perceived",
        "description": (f"a capability gap: I predicted competence at {faculty!r} but "
                        f"observed a {failure_class} failure on {ch_id or ch_text!r}"),
    })
    if ag_node is not None:
        try:
            sub.add_edge(ag_node, "perceives_gap", gid)
        except Exception:
            pass
    return gid


def gap_as_observation(faculty: str, failure_class: str, challenge_id: str = "") -> list:
    """Render a perceived gap as a relation-system (the observation shape
    `induce_concern` consumes): the composer's dequantize loop decodes THIS against
    the held codebook and either recognizes it or mints a concern from its residual.
    Leads each clause with its cue word (induce_concern keys the residual on the
    first token of each clause)."""
    return [
        ["capability_gap", "self", faculty],
        ["failed_on", faculty, challenge_id or "challenge"],
        ["surface", failure_class, faculty],
    ]


# ==========================================================================
# THE FULL LOOP — run the battery, collapse observed-vs-predicted, mint the gaps.
# ==========================================================================

def perceive_capability_gaps(agent, battery: Optional[list] = None,
                             runner: Optional[Callable] = None,
                             mint: bool = True) -> dict:
    """The agent's SELF-GAP PERCEPTION, end to end:

      1. run the battery through the agent's REAL faculties (host marshals);
      2. read each outcome mechanically (observe_outcome — boundary I/O);
      3. build the PREDICTED-COMPETENCE model (the battery IS the self-claim: every
         exercised faculty is claimed -> predicted substantive);
      4. COLLAPSE observed-vs-predicted (run_collapse) -> residual = the gaps;
      5. mint each residual as a CapabilityGap graph node (a groundable Concern).

    The gap DECISION is step 4's collapse residual, not any Python branch here.
    Returns {records, observations, competence, residual, gaps} — `gaps` is the list
    of minted CapabilityGap node ids (empty when every claimed faculty was
    substantive: the discriminative null)."""
    if battery is None:
        battery = load_battery()
    records = run_battery(agent, battery, runner=runner)
    observations = {r["faculty"]: r["outcome"] for r in records}
    # the competence model: every faculty the battery exercises is CLAIMED (the
    # battery is the agent's competence self-claim), so each predicts a substantive
    # outcome.  A gap fires only where the observed outcome contradicts that.
    competence = {r["faculty"]: {SUBSTANTIVE: 1} for r in records}
    residual = collapse_residual(competence, observations)
    gaps = []
    if mint:
        by_faculty = {r["faculty"]: r for r in records}
        for faculty, failure_class in residual:
            ch = by_faculty.get(faculty, {})
            gaps.append(mint_capability_gap(agent, faculty, failure_class,
                                            challenge={"id": ch.get("faculty", faculty),
                                                       "text": ""}))
    return {"records": records, "observations": observations,
            "competence": competence, "residual": residual, "gaps": gaps}


def ground_gap_as_concern(agent, gap) -> dict:
    """Hand a perceived CapabilityGap to the composer's concern machinery: render it
    as an observation and run `reflective_faculty.induce_concern` (the dequantize
    loop).  Shows the gap is a WELL-FORMED, groundable Concern — the seam builds
    #3/#4 pick up.  Returns induce_concern's own verdict dict."""
    from domains import reflective_faculty as _rf
    sub = getattr(agent, "s", agent)
    at = sub.node(gap)["attrs"] if not isinstance(gap, dict) else gap
    observation = at.get("observation") or gap_as_observation(
        at.get("faculty", "unknown"), at.get("failure_class", "silence"),
        at.get("challenge_id", ""))
    name = "gap_" + str(at.get("faculty", "unknown"))
    return _rf.induce_concern(agent, observation, name_hint=name)


__all__ = [
    "make_plug", "collapse_residual", "observe_outcome",
    "load_battery", "run_challenge", "run_battery",
    "mint_capability_gap", "gap_as_observation",
    "perceive_capability_gaps", "ground_gap_as_concern",
    "SUBSTANTIVE", "FAILURE_CLASSES",
]

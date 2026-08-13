"""gamma_production_growth — the `gamma_production` sibling of
`prog_read_growth.py` / `knowledge_growth.py` (GAMMA_PRODUCTION_ADOPT_HANDLER_
PREREG.md), closing the honest gap GAMMA_COLLAPSE_ALGORITHM_RESULTS.md's Q2
named: "`StandingConcern -> judge -> adopt` -- falls through to the generic
`comprehend_first` default (no `gamma_production` handler exists ...);
reported as a named, out-of-scope gap, not silently patched."

`seeds/gamma_residual.json`'s `note_gamma_production_gap` mints a
`SelfConcern{kind:'gamma_production', content:'Gamma repeatedly rejects
(<src_type>) -[<edge_type>]-> (<tgt_type>) -- no admissibility production
covers it'}` on support >= 2 recurrence of the SAME `Type1NoProduction`
triple (rung 4 of the collapse-mint shape, applied to Gamma). This module
supplies the missing rung: judge -> adopt, ending in a REAL `Production`
installed into the live Grammar.

UNLIKE every other `*_growth.py` sibling in this family (code_write / prog_
read / knowledge / self_account / reply_fix), closing a `gamma_production`
gap is NOT a single synchronous step. Those five all widen something a rule
already reads unconditionally the instant it exists (a ShapeSignature
codebook entry, a re-checked SelfProcess account, a re-run self-heal chain)
-- CLAUDE.md's own "SHAPE IS ACQUISITION, RULE IS EXECUTION" / Theorem-XII
material draws exactly this line: a Production is different IN KIND, because
it decides what edges may exist AT ALL, and the substrate's own docstring
(`checker.rs:1-3`) gives it a dedicated reference-monitor theorem for that
reason. So THIS module splits into two functions with two very different
trust levels:

  1. `judge_gamma_production_gap` -- SAFE to call synchronously from
     `_concern_tick` (the same grain as the other five `work_on_*_gap`
     functions). Parses the concern's own recorded triple back out of its
     `content` string (mechanical text-prep, the `prog_read_growth.
     _parse_prog_read_content` precedent exactly), probes
     `is_edge_admissible` -- a READ-ONLY check, never `add_production` -- and
     builds a *candidate* Production JSON. Reports one of three honest
     outcomes: the triple is still inadmissible (`ready_for_adopt`, a
     candidate is attached), the triple is ALREADY admissible (the gap
     resolved itself since it was filed -- `already_admissible`, nothing to
     adopt), or the content string didn't parse (`unresolvable`).

  2. `adopt_gamma_production` -- the ONLY function in this module (and, per
     the PREREG's Theorem-XII check, the ONLY new code path anywhere in this
     rung) that may call `add_production`. Never invoked automatically --
     only from the explicit, human-gated
     `jabberwock_daemon.adopt_gamma_production_standing` (the
     `promote_self_concern` precedent: a human clicks approve / calls the
     admin endpoint). RE-VERIFIES the triple is still inadmissible
     immediately before adopting (judging on stale data -- e.g. a
     concurrent adopt of the same triple since the judge step ran -- would
     itself be a bug this check exists to catch), then verifies the exact
     triple flips to admissible while leaving everything else untouched.

ARCHITECTURE (CLAUDE.md): the only DECISIONS this module makes are (a)
whether `is_edge_admissible`'s own boolean return says the triple is
currently admissible (a read of an already-computed fact, never a guess
about meaning) and (b) whether a re-check immediately before adopting still
agrees with the first one (a boolean comparison of two already-computed
values -- the same status `code_write_growth.validate_written_function_by_
running`'s agreement check has). Everything else is text prep, a graph
lookup, and calls into the existing `is_edge_admissible`/`add_production`
PyO3 bindings.

PROBE-NODE HONESTY NOTE: `is_edge_admissible` takes a concrete `NodeID`, not
a bare type name -- there is no type-only admissibility probe anywhere in
the substrate (confirmed by reading `py.rs`'s full "admissibility probes"
section). `_probe_node_for_type` reuses an EXISTING node of `src_type` when
the live graph holds one, else mints a fresh one with empty attrs (the exact
shape `tests/test_gamma_collapse_algorithm_migrated.py`'s own
`_register_vocab_for_clean_type1` uses for its `a_node`/`b_node`). This
matches -- does not lose -- the granularity the underlying `GammaResidual` /
`SelfConcern` record was already built at: `GAMMA_COLLAPSE_ALGORITHM_
RESULTS.md` Q1 established that a `Type1NoProduction` triple is "already a
complete, well-typed, atomic 3-tuple" with no attr-level specificity
recorded, so a type-level probe answers exactly the question the recorded
gap asks. A probe node minted this way is a real, if minor, residual left in
the live graph -- reported honestly in the RESULTS doc, not hidden.
"""
from __future__ import annotations

from typing import Any, Optional


# --------------------------------------------------------------------------- #
#  CONTENT PARSE -- mechanical reverse of `note_gamma_production_gap`'s own
#  StringConcat template ('Gamma repeatedly rejects (<src>) -[<edge>]->
#  (<tgt>) -- no admissibility production covers it'). A fixed split, never a
#  decision about MEANING -- the `prog_read_growth._parse_prog_read_content`
#  precedent, kind-swapped.
# --------------------------------------------------------------------------- #
_PREFIX = "Gamma repeatedly rejects ("
_MID = ") -["
_MID2 = "]-> ("
_SUFFIX = ") -- no admissibility production covers it"


def _parse_gamma_content(content: str) -> Optional[tuple]:
    if not content.startswith(_PREFIX) or not content.endswith(_SUFFIX):
        return None
    body = content[len(_PREFIX):-len(_SUFFIX)]
    if _MID not in body:
        return None
    src_part, rest = body.split(_MID, 1)
    if _MID2 not in rest:
        return None
    edge_part, tgt_part = rest.split(_MID2, 1)
    src_type, edge_type, tgt_type = src_part.strip(), edge_part.strip(), tgt_part.strip()
    if not (src_type and edge_type and tgt_type):
        return None
    return (src_type, edge_type, tgt_type)


def _probe_node_for_type(sub, type_name: str):
    """Find-or-mint a concrete node of `type_name` to probe admissibility
    against -- `is_edge_admissible` needs a real NodeID, not a bare type
    name (see module docstring, PROBE-NODE HONESTY NOTE)."""
    for n in sub.nodes(type_name):
        return n
    return sub.add_node(type_name, {"_gamma_probe": 1.0})


def _candidate_production(src_type: str, edge_type: str, tgt_type: str,
                          provenance: str) -> dict:
    return {
        "src": {"type": src_type, "var": "x"},
        "edge_type": edge_type,
        "tgt": {"type": tgt_type, "var": "y"},
        "provenance": provenance,
    }


# --------------------------------------------------------------------------- #
#  STEP 1 -- JUDGE. Read-only: parses the triple, probes admissibility, builds
#  a candidate. Never calls `add_production`. Safe to call synchronously from
#  `_concern_tick`, the same grain as every sibling `work_on_*_gap`.
# --------------------------------------------------------------------------- #
def judge_gamma_production_gap(agent, about_text: str) -> dict[str, Any]:
    """The synchronous judge attempt `_process_gamma_production_standing`
    calls. `about_text` is the StandingConcern's own `about` (copied
    verbatim from the original SelfConcern's `content` -- the human-readable
    triple sentence `note_gamma_production_gap` filed). Returns
    {ok, status, triple, reason, [candidate_production]} where `status` is
    one of:

      'ready_for_adopt'   -- confirmed still inadmissible NOW; a candidate
                             Production is attached, awaiting an explicit
                             human/experiment-gated adopt call.
      'already_admissible' -- the world moved on since the gap was filed
                             (e.g. some other production now covers it);
                             nothing to adopt, the original gap is resolved.
      'unresolvable'      -- the content string didn't parse, or the probe
                             itself failed -- honestly exhausted, the
                             `note_gamma_production_composition_exhausted`
                             precedent.

    NEVER calls `add_production` -- see `adopt_gamma_production` below."""
    triple = _parse_gamma_content((about_text or "").strip())
    if triple is None:
        return {"ok": False, "status": "unresolvable", "triple": None,
                "reason": "could not parse a (src_type, edge_type, tgt_type) "
                         "triple out of %r" % about_text}
    src_type, edge_type, tgt_type = triple
    sub = getattr(agent, "s", agent)
    try:
        probe = _probe_node_for_type(sub, src_type)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "status": "unresolvable", "triple": triple,
                "reason": "could not obtain a probe node of type %r: %s: %s"
                         % (src_type, type(e).__name__, e)}
    try:
        admissible = sub.is_edge_admissible(probe, edge_type, tgt_type, None)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "status": "unresolvable", "triple": triple,
                "reason": "is_edge_admissible probe failed for (%s)-[%s]->(%s): "
                         "%s: %s" % (src_type, edge_type, tgt_type,
                                    type(e).__name__, e)}
    if admissible:
        return {"ok": True, "status": "already_admissible", "triple": triple,
                "reason": "(%s) -[%s]-> (%s) is ALREADY admissible -- the gap "
                         "resolved itself since it was filed; no adopt needed"
                         % triple}
    candidate = _candidate_production(
        src_type, edge_type, tgt_type,
        provenance="gamma_production_adopt_handler:judge")
    return {"ok": True, "status": "ready_for_adopt", "triple": triple,
            "candidate_production": candidate,
            "reason": "(%s) -[%s]-> (%s) is confirmed still inadmissible right "
                     "now -- a candidate Production is ready for an explicit "
                     "human/experiment-gated adopt" % triple}


# --------------------------------------------------------------------------- #
#  STEP 2 -- ADOPT. The ONLY function in this module (and, per the PREREG's
#  Theorem-XII check, the only new code path in this whole rung) that may
#  call `add_production`. Callers MUST be an explicit, out-of-band,
#  human/experiment-gated action -- never `_concern_tick`, never a rule.
# --------------------------------------------------------------------------- #
def adopt_gamma_production(agent, candidate_production: dict,
                           expected_triple: Optional[tuple] = None) -> dict[str, Any]:
    """RE-VERIFIES the candidate's triple is still inadmissible right now
    (judging on stale data -- e.g. a concurrent adopt of the same triple, or
    a vocabulary change since the judge step ran -- would itself be a bug
    this check exists to catch), then calls the real `add_production` PyO3
    binding and verifies the exact triple flips to admissible. Returns
    {ok, triple, before, after, reason}. Refuses (ok: False, no
    `add_production` call) if `expected_triple` is given and disagrees with
    the candidate, or if the triple is found to already be admissible."""
    sub = getattr(agent, "s", agent)
    try:
        src_type = candidate_production["src"]["type"]
        edge_type = candidate_production["edge_type"]
        tgt_type = candidate_production["tgt"]["type"]
    except (KeyError, TypeError) as e:
        return {"ok": False, "reason": "malformed candidate_production: %s: %s"
                                       % (type(e).__name__, e)}
    triple = (src_type, edge_type, tgt_type)
    if expected_triple is not None and tuple(expected_triple) != triple:
        return {"ok": False, "triple": triple,
                "reason": "candidate triple %r does not match the concern's own "
                         "recorded triple %r -- refusing to adopt"
                         % (triple, tuple(expected_triple))}
    try:
        probe = _probe_node_for_type(sub, src_type)
        before = sub.is_edge_admissible(probe, edge_type, tgt_type, None)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "triple": triple,
                "reason": "pre-adopt admissibility check failed: %s: %s"
                         % (type(e).__name__, e)}
    if before:
        return {"ok": False, "triple": triple, "before": before,
                "reason": "(%s) -[%s]-> (%s) is ALREADY admissible right now -- "
                         "judging on stale data, refusing to install a no-op "
                         "production" % triple}
    sub.add_production(candidate_production)  # <-- the ONE call site, this module
    after = sub.is_edge_admissible(probe, edge_type, tgt_type, None)
    ok = bool(after)
    reason = (("add_production made (%s) -[%s]-> (%s) admissible" % triple) if ok
             else ("add_production was called but (%s) -[%s]-> (%s) is STILL "
                  "inadmissible -- unexpected, needs investigation" % triple))
    return {"ok": ok, "triple": triple, "before": before, "after": after,
           "reason": reason}


# --------------------------------------------------------------------------- #
#  MECHANICAL READER. UNLIKE `pending_prog_read_gaps`/`pending_code_write_
#  gaps` (which walk `agent -has_self_concern-> sc`), a `gamma_production`
#  SelfConcern carries NO such edge by design (`seeds/gamma_residual.json`'s
#  own documented choice -- no reliable single-Agent anchor at this grain).
#  This reader instead does the `reflective_faculty._run_self_gaps` scan-all
#  fallback DIRECTLY (a full `NodesOfType('SelfConcern')` scan filtered by
#  kind) -- the precedent that already makes this kind discoverable/
#  promotable with zero extra plumbing, reused here for the SAME reason.
# --------------------------------------------------------------------------- #
def pending_gamma_production_gaps(agent) -> list:
    sub = getattr(agent, "s", agent)
    out = []
    for sc in sub.nodes("SelfConcern"):
        at = sub.node(sc)["attrs"]
        if at.get("kind") == "gamma_production" and at.get("status") != "retired":
            out.append(at)
    return out


__all__ = [
    "judge_gamma_production_gap", "adopt_gamma_production",
    "pending_gamma_production_gaps",
]

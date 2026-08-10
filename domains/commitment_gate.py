"""commitment_gate — the GENERAL commit-vs-explore gate, host/adapter work
per CLAUDE.md (mechanical frame-data lookup + a policy comparison; no agent
cognition, no rule engine, no agent state).

------------------------------------------------------------------------
THE THEORY (why this file exists)
------------------------------------------------------------------------
The substrate already draws this line for ONE pair of primitives:

  * `run_rules` is a monotone fixpoint (Tarski) -- a rule can only ADD facts
    within a tick, so re-running it from the same starting state always
    reaches the same answer. Exploration inside it is CHEAP and REVERSIBLE:
    if a line of reasoning turns out wrong, the agent just re-collapses
    (re-derives) rather than undoing anything.
  * `fold_clock_edge` (runners/dsl/src/py.rs ~line 2705, the DSL's "tock")
    is the substrate's own lawful NON-MONOTONE down-stroke: it commits
    `next_<X> -> <X>` on clocked nodes, in a SEPARATE phase from run_rules
    precisely because a value going DOWN cannot happen inside the monotone
    fixpoint. It is EXPENSIVE in the sense that matters here -- not CPU
    cost, but consequence: once fired, the prior value is gone.

`domains/proposal_install.py` hand-built the same distinction for exactly
ONE action class outside the graph: installing a self-authored Rust
primitive into the agent's own running .so. Its five guardrails are a
commit gate; `domains/auto_approve.py` is a policy layer on top of that one
gate.

This module makes the distinction GENERAL: reversibility becomes FRAME DATA
(`seeds/reversibility_frame.json` -- action/effect kind -> reversible |
committing, with the reason), and ANY action, not just runtime install,
passes through the same shaped gate: reversible actions run free; committing
actions are refused unless a policy (denylist/allowlist + optional approver)
admits them, mirroring the SAME shape `proposal_install` + `auto_approve`
already established (this module does not replace either -- see the
SUBSUMPTION section below and the module-level docstring note on wiring).

------------------------------------------------------------------------
WHAT THIS MODULE OWNS
------------------------------------------------------------------------
  * `classify(kind)` / `classify_detail(kind)` -- mechanical frame-data
    lookup. Unknown kinds fail CLOSED (treated as committing) -- see the
    frame file's `default_category`.
  * `commit_gate(agent, action, *, approver=None, policy=None)` -- the
    general gate. Reversible actions pass with no approval and no audit
    record (matching run_rules: free exploration, nothing to log). A
    committing action is checked against `policy` (a denylist/allowlist +
    an "approver required" flag, the same shape `auto_approve.py`'s
    `AutoApprovePolicy` established for the one action class it knows
    about) and, for action kinds this module has an ELIGIBILITY_CHECKS
    entry for (currently just `runtime_install`), an additional
    action-class-specific precheck that mirrors proposal_install's own
    read-only guardrails 1-3 (status / already-installed) -- see the
    SUBSUMPTION note below for why this is legitimate and what it does
    NOT do.
  * `Commitment` audit record -- minted for every COMMITTING action this
    gate decides on (allowed or refused), never for a reversible action.
    Same spirit as proposal_install's `Install` record / auto_approve's
    log: a safety-sensitive decision leaves a trail.

------------------------------------------------------------------------
SUBSUMPTION (commit_gate generalizes proposal_install's install gate)
------------------------------------------------------------------------
`commit_gate` does NOT reimplement `install_proposal`'s five guardrails,
and does NOT call the real installer. What it does is read the SAME two
attributes install_proposal's own guardrails 1-3 read (`installed`,
`status` on the linked `ExtensionProposal`) via
`domains.proposal_install._find_proposal` (already a read-only helper --
`auto_approve.py` imports and calls this exact function too, so using it
here is not "editing proposal_install", it is the same kind of read every
existing caller does) to predict eligibility, then folds that prediction
into the general committing-action policy check every other action kind
goes through. `tests/test_commitment_gate.py` proves this prediction
agrees with `proposal_install.install_proposal`'s real decision on both an
allowed and a refused case, calling `install_proposal` itself (mocked only
where a real cargo/maturin call would otherwise fire -- see that test's
own accounting) as the oracle.

`install_proposal` / `auto_approve` are NOT rewired to call through
`commit_gate` by this change -- they keep making their own decisions
exactly as before. Routing them (and the browser/ARC/voice/http world
adapters) through `commit_gate` so there is ONE gate instead of N
parallel ones is the documented follow-on this module sets up for, not
something this module does.

------------------------------------------------------------------------
CAUTION
------------------------------------------------------------------------
This module is a POLICY/FRAME-DATA gate, not a sandbox. It decides
whether an action MAY proceed; it never performs the action itself (it
has no del_node/del_edge/http/browser/install call anywhere in it). A
caller still has to actually DO the gated thing after `commit_gate`
returns `allowed: True` -- exactly like `install_proposal` already
returning `ok: True` doesn't rebuild anything on its own if a caller
never called it.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable, Optional

from domains import proposal_install as pinstall

ROOT = Path(__file__).resolve().parent.parent
FRAME_PATH = ROOT / "seeds" / "reversibility_frame.json"

REVERSIBLE = "reversible"
COMMITTING = "committing"


# ---------------------------------------------------------------------------
# frame data: load once, cache, mechanical lookup only
# ---------------------------------------------------------------------------

_FRAME_CACHE: Optional[dict] = None


def _load_frame_raw(path: Path = FRAME_PATH) -> dict:
    return json.loads(path.read_text())


def load_frame(*, force: bool = False) -> dict:
    """The parsed `seeds/reversibility_frame.json`, cached after first load.
    `force=True` reloads from disk (tests only -- production never needs a
    live-editable frame mid-process)."""
    global _FRAME_CACHE
    if _FRAME_CACHE is None or force:
        _FRAME_CACHE = _load_frame_raw()
    return _FRAME_CACHE


def _entries_by_kind(frame: dict) -> dict:
    out = {}
    for node in frame.get("nodes", []):
        attrs = node.get("attrs", {})
        kind = attrs.get("kind")
        if kind:
            out[kind] = attrs
    return out


def classify_detail(kind: str, *, frame: Optional[dict] = None) -> dict:
    """{"kind", "category", "reason", "known", "archetype"} for one action/
    effect kind. Purely a data lookup -- no decision, no graph read. Unknown
    kinds fail CLOSED per the frame's `default_category` (committing)."""
    frame = frame if frame is not None else load_frame()
    entries = _entries_by_kind(frame)
    entry = entries.get(kind)
    if entry is None:
        return {
            "kind": kind,
            "category": frame.get("default_category", COMMITTING),
            "reason": frame.get("default_reason", "unclassified kind -- fail closed"),
            "known": False,
            "archetype": False,
        }
    return {
        "kind": kind,
        "category": entry.get("category", COMMITTING),
        "reason": entry.get("reason", ""),
        "known": True,
        "archetype": bool(entry.get("archetype", False)),
    }


def classify(kind: str, *, frame: Optional[dict] = None) -> str:
    """"reversible" | "committing" for one action/effect kind."""
    return classify_detail(kind, frame=frame)["category"]


def classification_table(*, frame: Optional[dict] = None) -> list[dict]:
    """Every classified kind, sorted (reversible first, then kind name) --
    what `scripts/jabberwock_commitment_gate.py` prints."""
    frame = frame if frame is not None else load_frame()
    rows = list(_entries_by_kind(frame).values())
    rows.sort(key=lambda r: (r.get("category") != REVERSIBLE, r.get("kind", "")))
    return rows


# ---------------------------------------------------------------------------
# graph helpers (mirror proposal_install.py's / auto_approve.py's own
# tiny adapter-resolution helpers -- duplicated on purpose rather than
# imported, since those modules are read-only for this task)
# ---------------------------------------------------------------------------

def _sub(agent):
    return getattr(agent, "s", agent)


def _nid_value(nid: Any) -> Any:
    return nid.value if hasattr(nid, "value") else nid


# ---------------------------------------------------------------------------
# action-class eligibility prechecks (extension point)
# ---------------------------------------------------------------------------
#
# A committing action kind MAY register a precheck here: a read-only
# function `(agent, action) -> {"eligible": bool, "reason": str}` that folds
# extra graph state into the gate's decision beyond the flat policy check.
# A kind with no entry is judged purely on the generic policy (denylist /
# allowlist / approver) below -- this dict only grows when an action class
# has its OWN pre-existing gate (like proposal_install's) whose read-only
# preconditions are worth mirroring here, not for every new action kind.

def _runtime_install_eligibility(agent, action: dict) -> dict:
    """Mirrors ONLY the read-only, attribute-level guardrails
    `proposal_install.install_proposal` checks BEFORE it does any real work
    (guardrail 1: not already installed; guardrail 2/3: status is
    'validated' or 'already_present'). Does NOT re-run the fresh sandbox
    re-validation (guardrail 4) or the file denylist (guardrail 5) -- those
    require rendering/compiling and stay install_proposal's job alone. This
    function exists purely so `commit_gate` can predict, from graph state
    already on the node, whether install_proposal would even consider the
    proposal -- see the module docstring's SUBSUMPTION note."""
    proposal_id = action.get("proposal_id")
    if proposal_id is None:
        return {"eligible": False, "reason": "runtime_install action missing proposal_id"}
    found = pinstall._find_proposal(agent, proposal_id)
    if found is None:
        return {"eligible": False, "reason": "proposal not found (or not linked to a spec)"}
    _pid, prop_attrs, _spec_id, _spec_attrs = found
    if bool(prop_attrs.get("installed")):
        return {"eligible": False, "reason": "already installed"}
    status = prop_attrs.get("status")
    if status not in ("validated", "already_present"):
        return {"eligible": False, "reason": f"status is {status!r}, not 'validated'"}
    return {"eligible": True, "reason": f"status={status!r}, not yet installed"}


ELIGIBILITY_CHECKS: dict[str, Callable[[Any, dict], dict]] = {
    "runtime_install": _runtime_install_eligibility,
}


# ---------------------------------------------------------------------------
# policy
# ---------------------------------------------------------------------------

DEFAULT_POLICY: dict[str, Any] = {
    # kinds always refused, no matter the approver.
    "denylist": [],
    # if not None, only these kinds may ever be approved (on top of the
    # denylist -- an empty/None allowlist means "no extra restriction".
    "allowlist": None,
    # a committing action needs a non-empty `approver` unless this is False.
    "require_approver": True,
}


def _policy_permits(kind: str, approver: Optional[str], policy: dict) -> tuple[bool, str]:
    denylist = policy.get("denylist") or []
    if kind in denylist:
        return False, f"kind {kind!r} is in the policy denylist"
    allowlist = policy.get("allowlist")
    if allowlist is not None and kind not in allowlist:
        return False, f"kind {kind!r} is not in the policy allowlist {sorted(allowlist)}"
    if policy.get("require_approver", True) and not approver:
        return False, "committing action requires an approver, none given"
    return True, "policy scope permits this kind and an approver was given"


# ---------------------------------------------------------------------------
# audit trail
# ---------------------------------------------------------------------------

def _mint_commitment_record(agent, *, kind: str, allowed: bool, approver: Optional[str],
                             reason: str, gated: bool, detail: Optional[dict] = None) -> Any:
    sub = _sub(agent)
    attrs = {
        "action": kind,
        "reversible": False,
        "gated": bool(gated),
        "allowed": bool(allowed),
        "approver": approver or "",
        "reason": reason[:1500],
        "ts": time.time(),
    }
    if detail:
        for k, v in detail.items():
            attrs.setdefault(f"detail_{k}", v)
    return sub.add_node("Commitment", attrs)


# ---------------------------------------------------------------------------
# the gate
# ---------------------------------------------------------------------------

def commit_gate(agent, action: Any, *, approver: Optional[str] = None,
                 policy: Optional[dict] = None) -> dict:
    """The GENERAL commit-vs-explore gate.

    `action` is either a bare kind string (e.g. "add_node") or a dict with
    at least a "kind" key plus whatever extra context an eligibility
    precheck for that kind needs (e.g. {"kind": "runtime_install",
    "proposal_id": pid}).

    Returns:
        {"allowed": bool, "reversible": bool, "kind": str, "reason": str,
         "requires_approval": bool, "gated": bool, "record": NodeID | None}

    A reversible action ALWAYS returns allowed=True, requires_approval=False,
    gated=False, record=None -- no policy is consulted, nothing is minted
    (matching run_rules: free exploration, nothing to log). A committing
    action is checked against `policy` (defaults to `DEFAULT_POLICY`: no
    denylist, no allowlist restriction, approver required) plus any
    registered action-class eligibility precheck (see
    `ELIGIBILITY_CHECKS`), and a `Commitment` record is minted either way
    (allowed or refused) -- see the module docstring."""
    action_dict = action if isinstance(action, dict) else {"kind": action}
    kind = action_dict.get("kind")

    # New graph-native path. The host remains the hard authorization boundary,
    # but wait/refine/commit and thermodynamic comparison are graph cognition.
    thermodynamic = action_dict.get("thermodynamic")
    if thermodynamic is not None:
        from domains.information_commitment import assess
        resolved = assess(
            agent,
            commit=thermodynamic.get("commit") or {},
            wait=thermodynamic.get("wait"),
            refine=thermodynamic.get("refine"),
            approver=approver,
        )
        return {
            "allowed": bool(
                resolved["decision"] == "commit" and resolved["authorized"]),
            "reversible": False,
            "kind": kind,
            "reason": resolved["reason"],
            "requires_approval": (
                resolved["decision"] == "commit" and not resolved["authorized"]),
            "gated": True,
            "record": resolved["record"],
            "decision": resolved["decision"],
            "context": resolved["context"],
            "candidate": resolved["candidate"],
        }

    detail = classify_detail(kind)
    reversible = detail["category"] == REVERSIBLE

    if reversible:
        return {
            "allowed": True, "reversible": True, "kind": kind,
            "reason": detail["reason"], "requires_approval": False,
            "gated": False, "record": None,
        }

    # committing from here down.
    effective_policy = dict(DEFAULT_POLICY)
    if policy:
        effective_policy.update(policy)

    eligibility_check = ELIGIBILITY_CHECKS.get(kind)
    if eligibility_check is not None:
        elig = eligibility_check(agent, action_dict)
        if not elig["eligible"]:
            record = _mint_commitment_record(
                agent, kind=kind, allowed=False, approver=approver,
                reason=elig["reason"], gated=True,
                detail={"proposal_id": action_dict.get("proposal_id")}
                if "proposal_id" in action_dict else None)
            return {
                "allowed": False, "reversible": False, "kind": kind,
                "reason": elig["reason"], "requires_approval": True,
                "gated": True, "record": record,
            }

    permitted, why = _policy_permits(kind, approver, effective_policy)
    record = _mint_commitment_record(
        agent, kind=kind, allowed=permitted, approver=approver, reason=why,
        gated=True,
        detail={"proposal_id": action_dict.get("proposal_id")}
        if "proposal_id" in action_dict else None)
    return {
        "allowed": permitted, "reversible": False, "kind": kind,
        "reason": why, "requires_approval": True, "gated": True,
        "record": record,
    }

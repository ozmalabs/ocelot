"""Operator authorship, propose-only (plan P5, 2026-10-10).

The MECHANICAL half of seeds/operator_authorship.json. The graph holds the
grammar (OperatorAuthorshipPolicy, FamilyMutation nodes naming parameter
sites of held FamilyPrograms) and the qualification rules; this module only

  * enumerates candidate families from that data in MDL order -- the held
    programs (size 0, the baseline), then every single edit, then every pair
    of edits on distinct sites of one program, capped at the policy's
    max_candidates (held baselines not counted) and max_size;
  * applies a candidate's edits to the held Program Term with the engine's own
    EditAt (runners/dsl/src/term.rs), evaluated, not spliced in Python;
  * runs a candidate on one bank turn exactly as production would: a
    SelfConcern about the turn promoted to a StandingConcern (what
    jabberwock_daemon.promote_self_concern writes), the program evaluated in
    reflective_faculty._family_program_env, the temporary nodes removed;
  * writes the measurements onto a FamilyProposal node under the policy, for
    the frozen rules to decide.

Nothing here installs anything. Choosing which candidates qualify is the
seed's rules; measuring them is the child replay (scripts/convo_child_run.py,
judge v2).
"""
from __future__ import annotations

import itertools
import json
from typing import Any


def _resolve(agent):
    from domains.reflective_faculty import _resolve_agent
    sub, native, _ag = _resolve_agent(agent)
    return sub, native


def policy(agent) -> tuple[Any, dict]:
    """The live OperatorAuthorshipPolicy node and its attrs (None, {} when absent)."""
    sub, _n = _resolve(agent)
    for n in sub.nodes("OperatorAuthorshipPolicy"):
        return n, dict(sub.node(n)["attrs"])
    return None, {}


def mutations(agent) -> list[dict]:
    """The held FamilyMutation grammar, in seed (node id) order."""
    sub, _n = _resolve(agent)
    out = []
    for n in sorted(sub.nodes("FamilyMutation"), key=lambda x: x.value):
        at = sub.node(n)["attrs"]
        try:
            values = json.loads(at.get("values") or "[]")
        except ValueError:
            values = []
        out.append({"program": str(at.get("program") or ""), "site": str(at.get("site") or ""),
                    "values": list(values)})
    return out


def parameter_sites(agent, program: str) -> dict:
    sub, _n = _resolve(agent)
    for n in sub.nodes("FamilyProgram"):
        at = sub.node(n)["attrs"]
        if at.get("name") == program:
            try:
                return json.loads(at.get("parameter_sites") or "{}")
            except ValueError:
                return {}
    return {}


def enumerate_candidates(agent) -> list[dict]:
    """MDL order: held programs (size 0), singles, then pairs on one program.
    Each candidate: {"id", "program", "edits": [[site, value], ...], "size"}."""
    _pn, pol = policy(agent)
    max_size = int(pol.get("max_size") or 1)
    cap = int(pol.get("max_candidates") or 0)
    muts = mutations(agent)
    programs = []
    for m in muts:
        if m["program"] not in programs:
            programs.append(m["program"])
    held = [{"id": f"{p}#held", "program": p, "edits": [], "size": 0} for p in programs]
    edits_by_prog = {p: [[(m["site"], v) for v in m["values"]] for m in muts if m["program"] == p]
                     for p in programs}
    authored = []
    for size in range(1, max_size + 1):
        for p in programs:
            for sites in itertools.combinations(edits_by_prog[p], size):
                for combo in itertools.product(*sites):
                    edits = [[s, v] for s, v in combo]
                    cid = p + "#" + "+".join(f"{s}={v}" for s, v in edits)
                    authored.append({"id": cid, "program": p, "edits": edits, "size": size})
    if cap:
        authored = authored[:cap]
    return held + authored


def candidate_program(agent, cand: dict):
    """The held Program with the candidate's edits applied by EditAt."""
    from domains.reflective_faculty import _load_family_program, _plain
    sub, native = _resolve(agent)
    prog = _load_family_program(sub, cand["program"])
    if prog is None:
        return None
    sites = parameter_sites(agent, cand["program"])
    for site, value in cand["edits"]:
        path = sites[site]["path"]
        term = {"type": "EditAt", "tree": {"type": "Var", "name": "prog"},
                "path": {"type": "Var", "name": "path"}, "op": {"type": "Lit", "value": "set"},
                "arg": {"type": "Var", "name": "lit"}}
        edited = native.evaluate(term, {"prog": prog, "path": list(path),
                                        "lit": {"type": "Lit", "value": value}})
        if edited is None:
            raise ValueError(f"EditAt inert at {site} {path}")
        prog = _plain(edited)
    return prog


def build_on_turn(agent, prog, mid, tag: str, kind: str = "reply_quality") -> dict:
    """The candidate's report for one bank turn, through the production
    concern context; temporary nodes removed afterwards."""
    from domains import reflective_faculty as rf
    sub, native = _resolve(agent)
    ag = getattr(agent, "agent", None)
    key = f"authorship_{tag}"
    sc = sub.add_node("SelfConcern", {"status": "promoted", "source": "implicit", "kind": kind,
                                      "content": f"operator authorship bank turn {int(mid.value)}"})
    if ag is not None:
        native.add_edge_unchecked(ag, "has_self_concern", sc)
    native.add_edge_unchecked(sc, "about_message", mid)
    stc = sub.add_node("StandingConcern", {"name": key, "status": "pending", "kind": kind})
    native.add_edge_unchecked(sc, "promoted_to", stc)
    try:
        val = native.evaluate(prog, rf._family_program_env(agent, [key], tag))
        rep = rf._plain(val) if isinstance(val, dict) else {"built": False, "wall": "no report"}
    except Exception as e:  # noqa: BLE001 -- an unevaluable candidate is an honest abstain
        rep = {"built": False, "wall": f"{type(e).__name__}: {e}"}
    finally:
        remover = getattr(native, "remove_node", None) or sub.remove_node
        for node in (stc, sc):
            remover(node)
    return rep


def delta_of(report: dict) -> dict:
    """The SeedDelta rule swap a built report names."""
    return {"add_rules": report.get("rules") or [],
            "remove_rules": [report["removed_rule"]] if report.get("removed_rule") else []}


def mint_proposal(agent, attrs: dict):
    """A FamilyProposal under the policy, status 'measured', for the rules."""
    sub, native = _resolve(agent)
    pn, _pol = policy(agent)
    clean = {k: (json.dumps(v) if isinstance(v, (list, dict)) else v) for k, v in attrs.items()}
    clean["status"] = "measured"
    p = sub.add_node("FamilyProposal", clean)
    if pn is not None:
        native.add_edge_unchecked(pn, "has_family_proposal", p)
    return p

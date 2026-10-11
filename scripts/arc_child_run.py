#!/usr/bin/env python3
"""arc_child_run — a child ARC runner spawned by
``domains/experiment_dispatch.py`` to play ONE dispatched Experiment's
episode out-of-process.

This is host mechanism only (CLAUDE.md): boot an agent (from a snapshot of a
parent's mind, or fresh with some seeds withheld), apply the SeedDelta's
``add_rules`` (graph data the delta specifies — installing it is mechanical,
deciding to try it was the agent's / experiment-author's call), TOMBSTONE any
``remove_rules`` (rule NAMES the delta specifies — resolved to the live
``export_rules()`` index and retracted via ``remove_rule``, so an embedded
``add_rules`` replacement is the ONLY thing left writing to whatever attribute
the removed rule used to write; e.g. a threshold-shifted copy of an acting
rule REPLACES the original instead of merely coexisting with it), then hand
off to ``arc_run.run_episode`` — the SAME per-frame loop the canonical
``arc_run.py`` CLI uses, so a dispatched experiment plays by identical rules
to a manually-launched run. No new reasoning lives here.

Two boot modes (see ``boot_child_agent`` — the choice is mechanical, keyed
only by whether the delta withholds any seeds):

  * SNAPSHOT boot (``--snapshot``, no ``skip_seeds``): ``WorldAdapter.load()``
    the exact parent mind and continue it. This is the primary, tested path.
  * FRESH+SKIP boot (``skip_seeds`` non-empty): a saved snapshot already has
    every seed's data baked into the graph — there is no way to "unload" a
    seed from it. Withholding a seed therefore requires booting a bare
    substrate and calling ``load_all_seeds(agent, skip=skip_seeds)``, exactly
    as ``scripts/arc_run.py``'s own ``boot_agent`` does minus the withheld
    seeds. This path ignores ``--snapshot`` (documented, not silently wrong).

Output contract (read by ``domains/experiment_dispatch.py``):
  * ``<out>/trace.jsonl`` — one line per frame:
    ``{"frame", "action", "score", "reasoning", "self_report"}``.
  * ``<out>/final_graph.json`` — ``agent.s.graph_to_dict()`` (best-effort; written
    even on failure if the agent got far enough to exist).
  * ``<out>/result.json`` — ``{"status": "done"|"failed", "frames", "score",
    "error": optional}`` (plus a few informational extras: ``won``, ``over``,
    ``boot_mode``, ``removed_rules`` — the delta's ``remove_rules`` names that
    actually resolved to a live rule and were tombstoned this run).

  PYTHONPATH=runners/dsl/python:. python3 scripts/arc_child_run.py \\
      --snapshot var/runs/7-0/parent_snapshot.json --delta var/runs/7-0/delta.json \\
      --game navigate --actions 20 --offline --out var/runs/7-0
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
for p in (str(_ROOT), str(_HERE), str(_ROOT / "runners" / "dsl" / "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter   # noqa: E402
from substrate.boot_all import load_all_seeds       # noqa: E402
from worlds.arc import ArcWorld                     # noqa: E402


def _load_delta(path) -> dict:
    if not path:
        return {"skip_seeds": [], "add_rules": [], "remove_rules": [],
                "add_concepts": [], "remove_concepts": [], "set_node_attrs": [],
                "parent_shadow_read": False, "parent_turn_path": ""}
    with open(path) as f:
        d = json.load(f)
    return {"skip_seeds": list(d.get("skip_seeds") or []),
            # PARENT-FIDELITY FLAG (RESIDUAL-CLOSURE): the parent's own
            # shadow_read state at dispatch — WorldAdapter.load() restores
            # False, so a replaying child must re-arm it to run the SAME
            # comprehension the parent ran (see experiment_dispatch._spawn).
            "parent_shadow_read": bool(d.get("parent_shadow_read") or False),
            # tranche 23: the path the parent's live turns took ("production"
            # = ingest_turn -> tick -> release). Before this it was dropped
            # here, so every tranche-22 replay ran on converse().
            "parent_turn_path": str(d.get("parent_turn_path") or ""),
            "add_rules": list(d.get("add_rules") or []),
            "remove_rules": list(d.get("remove_rules") or []),
            # Wave 5 (cue-set-edit variation family): typed nodes to add /
            # Concept names to retract on the dispatched copy — the graph-data
            # twin of add_rules/remove_rules. Mechanical, applied by
            # apply_concept_delta below.
            "add_concepts": list(d.get("add_concepts") or []),
            "remove_concepts": list(d.get("remove_concepts") or []),
            # RESIDUAL-CLOSURE wave (knob_edit variation family): held NODE
            # ATTR edits to apply on the dispatched copy — each
            # {type, key_attr, key_value, attrs} finds the live node of `type`
            # whose `key_attr` == `key_value` and set_attrs `attrs` onto it.
            # The graph-data twin of add_concepts for a THRESHOLD/KNOB belief
            # (e.g. ApertureBudget.reform_swallowed_threshold) rather than a
            # brand-new Concept. Mechanical, applied by apply_node_attr_delta.
            "set_node_attrs": list(d.get("set_node_attrs") or []),
            # WHERE-CLAUSE-VARIATION wave (rule_literal_edit family): the
            # marker + structural witness (see reflective_faculty.
            # _rule_effect_witness) convo_child_run's controlled double-pass
            # reads to decide whether to defer add_rules/remove_rules and what
            # to count fires of. The rule swap itself rides the SAME
            # add_rules/remove_rules channel above — no new channel needed.
            "rule_literal_edit": float(d.get("rule_literal_edit") or 0.0),
            "rule_literal_witness": d.get("rule_literal_witness") or "",
            # COMPOSER-CAPABILITY wave (datum_feedback_rule / shape_mint
            # families): the markers convo_child_run's controlled double-pass
            # reads to decide whether to defer add_rules (datum_feedback_rule
            # rides the SAME add_rules channel as rule_literal_edit — a
            # genuinely new, ADD-ONLY rule) or add_concepts (shape_mint rides
            # the SAME add_concepts channel cue_set_edit uses), and which
            # attr names the witness the double-pass reads before/after.
            "datum_feedback_edit": float(d.get("datum_feedback_edit") or 0.0),
            "datum_feedback_datum_attr": d.get("datum_feedback_datum_attr") or "",
            "datum_feedback_belief_attr": d.get("datum_feedback_belief_attr") or "",
            "shape_mint_edit": float(d.get("shape_mint_edit") or 0.0),
            "shape_mint_name": d.get("shape_mint_name") or "",
            "shape_mint_party": d.get("shape_mint_party") or ""}


def apply_concept_delta(agent, delta: dict) -> list:
    """Install the delta's `add_concepts` (each `{type, attrs}` — a Concept the
    experiment author picked, e.g. `{name: <verb>, instruction_route: <route>}`)
    and retract its `remove_concepts` (Concept NAMES). Mechanical graph I/O the
    delta specifies — deciding WHAT concept to try was the parent agent's own
    Term-picked call (domains/reflective_faculty._compose_cue_variant). Shared
    by both child runners (imported by convo_child_run, like _load_delta).
    Returns the names actually added."""
    added = []
    for item in (delta.get("add_concepts") or []):
        if not isinstance(item, dict):
            continue
        attrs = dict(item.get("attrs") or {})
        ntype = str(item.get("type") or "Concept")
        if not attrs.get("name"):
            continue
        agent.s.add_node(ntype, attrs)
        added.append(attrs["name"])
    for name in (delta.get("remove_concepts") or []):
        for n in list(agent.s.nodes("Concept")):
            try:
                if agent.s.node(n)["attrs"].get("name") == name:
                    remover = getattr(agent.inner, "remove_node", None) or agent.s.remove_node
                    remover(n)
            except Exception:  # noqa: BLE001 — a missing/stale node is an honest no-op
                pass
    return added


def apply_node_attr_delta(agent, delta: dict) -> list:
    """Install the delta's `set_node_attrs` (RESIDUAL-CLOSURE wave, the
    knob_edit variation family's graph-data twin of `apply_concept_delta`):
    each item is `{type, key_attr, key_value, attrs}` — find the FIRST live
    node of `type` whose `key_attr` attr equals `key_value` (the same
    find-by-attr idiom `apply_concept_delta`'s `remove_concepts` uses for
    Concept.name), then `set_attr` every (name, value) pair in `attrs` onto
    it. Mechanical graph I/O the delta specifies — deciding WHICH knob and
    WHAT value was the parent agent's own Term-picked call
    (domains/reflective_faculty._compose_knob_variant). Shared by both child
    runners (imported by convo_child_run, like apply_concept_delta). Returns
    the list of (type, key_value, attr_name) tuples actually set."""
    changed = []
    for item in (delta.get("set_node_attrs") or []):
        if not isinstance(item, dict):
            continue
        ntype = str(item.get("type") or "")
        key_attr = str(item.get("key_attr") or "")
        key_value = item.get("key_value")
        attrs = dict(item.get("attrs") or {})
        if not ntype or not key_attr or not attrs:
            continue
        target = None
        for n in agent.s.nodes(ntype):
            try:
                if agent.s.node(n)["attrs"].get(key_attr) == key_value:
                    target = n
                    break
            except Exception:  # noqa: BLE001 — a stale/malformed node is an honest skip
                continue
        if target is None:
            continue
        for k, v in attrs.items():
            try:
                agent.inner.set_attr(target, k, v)
                changed.append((ntype, key_value, k))
            except Exception:  # noqa: BLE001 — a malformed attr edit never blocks the rest
                pass
    return changed


def _fill_missing_bookkeeping(agent) -> None:
    """KNOWN GAP, worked around here rather than in substrate/world_adapter.py (out of scope for
    this change): ``WorldAdapter.load()`` restores the graph + a handful of named I/O indexes
    explicitly, but not every host-bookkeeping attribute ``WorldAdapter.__init__`` sets (e.g.
    ``_seen``, ``_activity``, the action-EMA caches — plain Python accounting the substrate
    itself never serialises). A snapshot-booted agent is missing them, and methods like
    ``ingest``/``observe`` then raise ``AttributeError``. This fills in the SAME defaults
    ``__init__`` would have set — read off a throwaway blank ``WorldAdapter(seeds=())`` (a
    ~30ms bare-substrate boot, no seed loading) — for whichever attrs the loaded agent doesn't
    already have. Mechanical restoration of missing default state, not a decision; it stays
    correct automatically if ``__init__`` grows more bookkeeping fields later."""
    blank = WorldAdapter(seeds=())
    for k, v in blank.__dict__.items():
        if k in ("s", "inner", "agent"):      # these ARE the restored graph/agent — never overwrite
            continue
        if not hasattr(agent, k):
            setattr(agent, k, v)


def boot_child_agent(snapshot, skip_seeds):
    """Boot the child's agent. Returns ``(agent, boot_mode)`` — see the module
    docstring for the two modes and why the choice is mechanical."""
    if not skip_seeds and snapshot:
        agent = WorldAdapter.load(snapshot)
        _fill_missing_bookkeeping(agent)
        return agent, "snapshot"
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent, skip=skip_seeds)
    return agent, "fresh+skip" if skip_seeds else "fresh"


def make_env(game: str, offline: bool):
    if offline:
        from arc3_env import ENVS
        if game not in ENVS:
            raise SystemExit(f"--offline: unknown game {game!r}; choices: {sorted(ENVS)}")
        return ENVS[game]()
    from _arc3_load_key import load_arc_api_key
    from arc3_live_env import Arc3LiveEnv
    if not load_arc_api_key():
        raise SystemExit("could not load ARC_API_KEY from .env — aborting "
                          "(pass --offline to test against arc3_env's offline games)")
    return Arc3LiveEnv(game)


def main() -> int:
    ap = argparse.ArgumentParser(description="ARC child runner — plays one dispatched Experiment's episode")
    ap.add_argument("--snapshot", default=None, help="WorldAdapter.save() path to boot from")
    ap.add_argument("--delta", default=None, help="SeedDelta JSON: {skip_seeds, add_rules}")
    ap.add_argument("--game", required=True)
    ap.add_argument("--actions", type=int, default=40)
    ap.add_argument("--offline", action="store_true",
                    help="use arc3_env's offline re-implemented games instead of the live HTTP API")
    ap.add_argument("--nav-repr", default="cells", choices=["cells", "quanta"])
    ap.add_argument("--out", required=True, help="run_dir to write trace.jsonl / final_graph.json / result.json")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    trace_path = out_dir / "trace.jsonl"
    result_path = out_dir / "result.json"
    graph_path = out_dir / "final_graph.json"

    delta = _load_delta(args.delta)
    result: dict = {"status": "failed", "frames": 0, "score": 0}
    agent = None
    trace_fp = None
    try:
        import arc_run                                   # noqa: E402  lazy: arc_run pulls live-env deps
        agent, boot_mode = boot_child_agent(args.snapshot, delta["skip_seeds"])
        result["boot_mode"] = boot_mode
        for rule in delta["add_rules"]:                # graph data the delta specifies; mechanical install
            agent.inner.add_rule(rule)
        added_concepts = apply_concept_delta(agent, delta)   # Wave 5: cue-set-edit graph data
        if added_concepts:
            result["added_concepts"] = added_concepts
        changed_attrs = apply_node_attr_delta(agent, delta)  # RESIDUAL-CLOSURE: knob_edit graph data
        if changed_attrs:
            result["set_node_attrs"] = [list(t) for t in changed_attrs]

        removed_rules = []
        if delta["remove_rules"]:                       # graph data the delta specifies; mechanical tombstone
            exported = agent.inner.export_rules()
            name_to_idx = {}
            for idx, r in enumerate(exported):
                if isinstance(r, dict) and r.get("active", True) and r.get("name"):
                    name_to_idx[r["name"]] = idx        # last-active-wins; names are unique in practice
            for rn in delta["remove_rules"]:
                idx = name_to_idx.get(rn)
                if idx is not None and agent.inner.remove_rule(idx):
                    removed_rules.append(rn)
                # a name not found / already-inactive is silently skipped — the delta names WHAT to
                # remove, not a guarantee it still exists; honest partial application, not an error.

        prod = arc_run._setup_speech(agent)
        describe_ctx = arc_run.setup_describe(agent, prod)
        agent.inner.add_rule(arc_run.MS_CHOOSE_EXPAND)  # same tick-fired move-space rule arc_run's CLI installs

        env = make_env(args.game, args.offline)
        world = ArcWorld(env)

        trace_fp = open(trace_path, "w")

        def on_frame(rec):
            trace_fp.write(json.dumps({"frame": rec["frame"], "action": rec["action"],
                                       "score": rec["score"], "reasoning": rec["reasoning"],
                                       "self_report": rec["self_report"]}) + "\n")
            trace_fp.flush()

        outcome = arc_run.run_episode(agent, world, args.actions, args.nav_repr,
                                      prod, describe_ctx, on_frame=on_frame)
        result = {"status": "done", "frames": outcome["frames"], "score": outcome["score"],
                  "won": outcome["won"], "over": outcome["over"], "boot_mode": boot_mode,
                  "removed_rules": removed_rules}
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"
        result["traceback"] = traceback.format_exc()
        print(f"arc_child_run FAILED: {result['error']}", file=sys.stderr, flush=True)
        print(result["traceback"], file=sys.stderr, flush=True)
    finally:
        if trace_fp is not None:
            try:
                trace_fp.close()
            except Exception:
                pass
        if agent is not None:
            try:
                with open(graph_path, "w") as f:
                    json.dump(agent.s.graph_to_dict(), f)
            except Exception as e:
                result["graph_write_error"] = f"{type(e).__name__}: {e}"
        with open(result_path, "w") as f:
            json.dump(result, f)

    return 0 if result.get("status") == "done" else 1


if __name__ == "__main__":
    sys.exit(main())

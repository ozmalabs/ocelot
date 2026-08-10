#!/usr/bin/env python3
"""residual_closure_run — THE RESIDUAL-CLOSURE AUDIT: drive the jabberwock's OWN
gap → NL-promote → StandingConcern → experiment → judge → adopt pipeline over the
named-residual inventory of this session's committed waves, through the SANCTIONED
SURFACES ONLY, and emit a per-residual disposition record.

The point (mission, verbatim): "continue with having the jabberwock close its own
named residuals." The host does NOT hand-fix anything here — every residual is
PHRASED to the agent over NL (``converse()``), promoted over NL ("Work on the
<content> gap."), and then the daemon's own mechanical tick hooks run the agent's
pipeline exactly as the daemon runs them. Where a residual is graph-native the
pipeline may genuinely close it (experiment → supported → adopted, revertible);
where the agent's variation repertoire cannot reach it, the honest terminal is an
inconclusive/exhausted trail or an abstain — captured, never faked; where the
residual is Python-blind, FILE + SURFACE ("What gaps do you have?") is the correct
closure per the standing directive ("if it can't fix it, at least find the gap").

No-assistance discipline (the no_assistance_gate precedent, enforced by AST):

  * ``OZMA_NO_LLM=1`` before boot — any hosted-LLM call raises.
  * Inputs after boot: ``converse()`` turns and the daemon's own tick hooks
    (``tick``, ``_steer_tick``, ``_concern_tick``, ``_dispatch_tick`` — real
    subprocess children — ``_close_tick``), plus the host console's
    ``cancel_experiment`` (the UI cancel button; used ONLY to keep the
    pre-existing standing metascience concern's ARC episodes from competing for
    memory with this audit — memory discipline, not steering).
  * NO direct calls to reflective_faculty internals, NO hand-minted
    Experiment/SeedDelta/variant, NO direct graph mutation
    (``audit_source_discipline()`` walks this module's AST; the gate test
    fails on any hit).

Memory discipline: ONE full-seed agent for the whole audit (residuals share it —
their reports are excluded from replay corpora by the 'reported' exclusion);
experiments dispatch strictly one at a time (each waits before the next files).

Run:
    PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/residual_closure_run.py \
        [--out DIR] [--budget SECS]
"""
from __future__ import annotations

import argparse
import ast
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT), str(ROOT / "runners" / "dsl" / "python"), str(ROOT / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import os  # noqa: E402  (kept below sys.path block, no_assistance_gate symmetry)


# ---------------------------------------------------------------------------
# SOURCE DISCIPLINE — copied from scripts/no_assistance_gate.py (the enforced
# property, not a comment). cancel_experiment is deliberately NOT forbidden:
# it is the host console's cancel button (experiment_dispatch documents it as
# "Human/host-initiated teardown only") and cancels nothing this audit filed.
# ---------------------------------------------------------------------------
_FORBIDDEN_CALLS = frozenset({
    "induce_concern", "ground_concern", "compose_design_for_goal",
    "mint_experiment", "close_experiment_loop", "perform_adoptions",
    "promote_self_concern", "repromote_self_concern", "revert_adoption",
    "_compose_experiment_rule", "_compose_cue_variant", "_compose_reply_ablation",
    "_compose_knob_variant", "_pick_variation_op", "_pick_reply_rule",
    "add_node", "add_edge", "add_edge_unchecked", "set_attr", "del_attr",
    "add_rule", "remove_rule", "import_rules", "load_seed_manifest", "teach",
    "run_rules",
})


def audit_source_discipline() -> list:
    """AST-walk THIS module's source; return every forbidden call site."""
    src = Path(__file__).read_text()
    tree = ast.parse(src)
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
            if name in _FORBIDDEN_CALLS:
                hits.append(f"line {node.lineno}: forbidden call {name!r}")
    return hits


# ---------------------------------------------------------------------------
# Mechanical graph READS (observability only).
# ---------------------------------------------------------------------------
def _concern_matching(adapter, needle: str):
    for sc in adapter.s.nodes("SelfConcern"):
        if not adapter.s.has_node(sc):
            continue
        at = adapter.s.node(sc)["attrs"]
        if needle.lower() in str(at.get("content") or "").lower():
            return int(sc.value), dict(at)
    return None, None


def _experiment_for_tag(adapter, tag: str):
    out = []
    for n in adapter.s.nodes("Experiment"):
        if not adapter.s.has_node(n):
            continue
        at = adapter.s.node(n)["attrs"]
        if at.get("axis_tag") == tag:
            out.append((n, dict(at)))
    return out


def _delta_attrs(adapter, exp) -> dict:
    for d in adapter.inner.neighbours(exp, "has_delta"):
        if adapter.s.has_node(d):
            return dict(adapter.s.node(d)["attrs"])
    return {}


def _standing_for(adapter, sc_id: int):
    import substrate_rs as srs
    sc = srs.NodeID(sc_id)
    if not adapter.s.has_node(sc):
        return None, None
    for st in adapter.inner.neighbours(sc, "promoted_to"):
        if adapter.s.has_node(st):
            return st, dict(adapter.s.node(st)["attrs"])
    return None, None


def _knob_value(adapter, register="conversational", attr="reform_swallowed_threshold"):
    for n in adapter.s.nodes("ApertureBudget"):
        at = adapter.s.node(n)["attrs"]
        if at.get("register") == register:
            return at.get(attr)
    return None


def _adoptions(adapter) -> list:
    out = []
    for n in adapter.s.nodes("Adoption"):
        if adapter.s.has_node(n):
            out.append(dict(adapter.s.node(n)["attrs"]))
    return out


def _variation_op_of(delta: dict):
    if delta.get("knob_edit") == 1.0:
        return "knob_edit"
    if delta.get("rule_literal_edit") == 1.0:
        return "rule_literal_edit"
    if delta.get("cue_edit") == 1.0:
        return "cue_set_edit"
    if delta.get("ablation") == 1.0:
        return "reply_ablation"
    if delta.get("edit_op_kind"):
        return "structural_edit"
    if delta.get("act_shift") is not None:
        return "threshold_shift"
    return None


def _cancel_foreign_experiments(adapter, keep_tags: set) -> list:
    """Memory discipline ONLY: cancel requested experiments whose axis_tag is
    not one this audit filed (the standing metascience concern mints offline
    ARC episodes on a fresh boot). Host console surface (cancel_experiment)."""
    from domains.experiment_dispatch import cancel_experiment
    cancelled = []
    for n in list(adapter.s.nodes("Experiment")):
        if not adapter.s.has_node(n):
            continue
        at = adapter.s.node(n)["attrs"]
        if at.get("status") == "requested" and at.get("axis_tag") not in keep_tags:
            r = cancel_experiment(adapter, str(int(n.value)))
            if r.get("ok"):
                cancelled.append(int(n.value))
    return cancelled


# ---------------------------------------------------------------------------
# THE PUMP — the daemon's own hooks, one experiment at a time.
# ---------------------------------------------------------------------------
def _pump(adapter, jd, runs_dir, until, label: str, budget_s: float, keep_tags: set) -> bool:
    t0 = time.time()
    while time.time() - t0 < budget_s:
        adapter.tick()
        jd._steer_tick(adapter)
        jd._concern_tick(adapter)
        _cancel_foreign_experiments(adapter, keep_tags)
        jd._dispatch_tick(adapter, str(runs_dir))
        jd._close_tick(adapter)
        if until():
            return True
        time.sleep(0.5)
    print(f"  [pump timeout] {label} did not complete within {budget_s:.0f}s", flush=True)
    return until()


# ---------------------------------------------------------------------------
# THE RESIDUAL INVENTORY — each entry: how the interlocutor phrases it over NL
# (the gap_awareness explicit-report surface needs a deficiency cue word —
# cannot/fail/gap/limitation/stuck/unable/struggle/weakness/broken/wrong — AND
# a self-word), the NL promote line (steer verb + gap-noun + a content word
# unique to this concern), and whether we EXPECT the pipeline to reach an
# experiment (drive) or the residual is Python-blind (file+surface only).
# ---------------------------------------------------------------------------
RESIDUALS = [
    {"id": "R1", "title": "PP-folding reforms eagerly (reform_swallowed_threshold)",
     "class": "graph-native",
     "report": ("Your reading reform swallowed threshold is wrong; it reforms "
                "simple sentences too eagerly."),
     "promote": "Work on the swallowed threshold gap.",
     "unique": "swallowed", "drive": True},
    {"id": "R2", "title": "narrative-shape floors are rule literals (escalate_narrative_shape)",
     "class": "graph-native (rule-literal — outside the held variation families)",
     "report": ("Your narrative shape escalation floors are broken; the sentence "
                "and animate floors are fixed rule literals you cannot tune."),
     "promote": "Work on the narrative escalation gap.",
     "unique": "narrative", "drive": True},
    {"id": "R3", "title": "track-record -> reliability auto-update is datum-only",
     "class": "graph-native (rule ADDITION — composer has no family for it)",
     "report": ("Your interlocutor trust is broken; you record contradictions "
                "but fail to update your self report reliability from them."),
     "promote": "Work on the reliability gap.",
     "unique": "reliability", "drive": True,
     "meta_report": ("Your composer is a limitation; you cannot author a rule "
                     "that feeds a recorded datum back into a held belief."),
     "meta_unique": "composer"},
    {"id": "R4", "title": "new person-shape minting for poor-fit parties",
     "class": "graph-native (typed-node construction — no composer builds it)",
     "report": ("Your interlocutor shapes are a limitation; a poor fit party "
                "never gets a new shape minted."),
     "promote": "Work on the shapes gap.",
     "unique": "shapes", "drive": True,
     "meta_report": ("Your variation repertoire is a limitation; no builder "
                     "constructs a typed codebook node for the dispatch channel."),
     "meta_unique": "repertoire"},
    {"id": "R5", "title": "divergence-recurrence 3.0 + scell_promote 10/3 rule literals",
     "class": "graph-native (rule-literal — outside the held variation families)",
     "report": ("Your divergence recurrence threshold is stuck as a rule literal; "
                "so are the salience promote spans."),
     "promote": "Work on the divergence gap.",
     "unique": "divergence", "drive": True},
    {"id": "R6", "title": "bare first-person routing ('Who am I?') — comprehend_text ladder",
     "class": "python-blind",
     "report": ("You cannot answer the question who am I; your first person "
                "routing is broken."),
     "drive": False},
    {"id": "R7", "title": "multi-word topic keys miss the HeldAnswer bridge",
     "class": "python-blind",
     "report": ("You fail to answer questions about multi word topics; your "
                "topic facts lookup is broken at the span grain."),
     "drive": False},
    {"id": "R8", "title": "reform components not re-ingested into the situation model",
     "class": "python-blind (adapter)",
     "report": ("You record reform components but fail to feed them into your "
                "situation model; that wiring is a gap."),
     "drive": False},
    {"id": "R9", "title": "proposition-grain belief content (character_tom shallow grounding)",
     "class": "python-blind (partially)",
     "report": ("Your character belief content is a limitation; you ground "
                "propositions too shallowly for theory of mind."),
     "drive": False},
]


def run_audit(out_dir: Path, budget_s: float = 300.0) -> dict:
    os.environ["OZMA_NO_LLM"] = "1"
    import jabberwock_daemon as jd
    from domains.no_llm import no_llm
    from domains.experiment_dispatch import _INFLIGHT

    print("=" * 96)
    print("RESIDUAL-CLOSURE AUDIT — OZMA_NO_LLM=1; NL surface + daemon hooks only.")
    print("=" * 96)
    audit: dict = {"no_llm": bool(no_llm()),
                   "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "source_discipline_violations": audit_source_discipline(),
                   "residuals": []}
    for v in audit["source_discipline_violations"]:
        print(f"  source-discipline violation: {v}", flush=True)

    out_dir.mkdir(parents=True, exist_ok=True)
    runs_dir = out_dir / "runs"
    ckpt = Path(tempfile.mkdtemp(prefix="jbw_residual_ckpt_"))
    t0 = time.time()
    adapter, booted = jd.boot(ckpt, "full")
    adapter.shadow_read = True       # the daemon's own CLI default posture
    adapter.deep_ingest = True
    print(f"agent boot: {booted!r}, {adapter.s.node_count()} nodes, {time.time()-t0:.1f}s",
          flush=True)
    audit["boot"] = {"mode": booted, "nodes": adapter.s.node_count()}
    _INFLIGHT.clear()

    # a small behaviour corpus (incl. the R1-motivating PP sentences) BEFORE
    # any residual is filed, so replay experiments have something to replay.
    for text, act in (("Hello.", "greeting"),
                      ("Miners extract ore from the mountain.", "statement"),
                      ("Farmers haul grain from the valley.", "statement")):
        adapter.converse(text, speech_act=act)

    keep_tags: set = set()
    for spec in RESIDUALS:
        rec: dict = {"id": spec["id"], "title": spec["title"], "class": spec["class"],
                     "report_turn": spec["report"]}
        print(f"\n--- {spec['id']}: {spec['title']} " + "-" * max(4, 70 - len(spec["title"])),
              flush=True)

        # 1. FILE over NL (the gap_awareness explicit-report surface).
        reply = adapter.converse(spec["report"], speech_act="statement")
        rec["file_reply"] = reply
        sc_id, sc_at = _concern_matching(adapter, spec.get("unique") or spec["report"][:40])
        rec["filed"] = sc_id is not None
        rec["concern_id"] = sc_id
        rec["concern_kind"] = (sc_at or {}).get("kind")
        print(f"  filed: {rec['filed']} (id={sc_id}, kind={rec['concern_kind']}) "
              f"reply={reply!r}", flush=True)

        if not spec["drive"]:
            audit["residuals"].append(rec)
            continue

        if not rec["filed"]:
            rec["disposition_note"] = "filing surface missed — see file_reply"
            audit["residuals"].append(rec)
            continue

        # 2. PROMOTE over NL.
        steer = adapter.converse(spec["promote"], speech_act="request")
        rec["promote_turn"] = spec["promote"]
        rec["promote_reply"] = steer
        promoted = jd._steer_tick(adapter)
        mine = [p for p in promoted if p.get("self_concern") == sc_id]
        rec["promoted"] = bool(mine)
        if mine:
            rec["standing_concern"] = mine[0].get("standing_concern")
            rec["pipeline"] = mine[0].get("pipeline")
        print(f"  promoted: {rec['promoted']} ({rec.get('pipeline')}) "
              f"steer={steer!r}", flush=True)
        if not rec["promoted"]:
            audit["residuals"].append(rec)
            continue

        _st, st_at = _standing_for(adapter, sc_id)
        tag = (st_at or {}).get("name")
        rec["axis_tag"] = tag
        keep_tags.add(tag)

        # 3. GROUND + DISPATCH + JUDGE + CLOSE — the agent's own machinery,
        # pumped until this concern's experiment reaches a closed state OR the
        # concern's trail is honestly terminal (no experiment mintable).
        knob_before = _knob_value(adapter)

        def _closed():
            exps = _experiment_for_tag(adapter, tag)
            if not exps:
                return False
            for _n, at in exps:
                if at.get("status") in ("requested", "running"):
                    return False
                out = at.get("outcome")
                if not out:
                    return False        # done but not yet judged — keep pumping
                if out == "supported" and not (at.get("adopted") or at.get("adopt_denied")):
                    return False        # judged supported but adoption not yet performed
            return True

        jd._concern_tick(adapter)
        exps0 = _experiment_for_tag(adapter, tag)
        if exps0:
            _pump(adapter, jd, runs_dir / spec["id"], _closed,
                  f"{spec['id']} close", budget_s, keep_tags)
        exps = _experiment_for_tag(adapter, tag)
        rec["experiments"] = []
        for n, at in exps:
            da = _delta_attrs(adapter, n)
            run_dir = at.get("run_dir") or ""
            child = {}
            try:
                with open(Path(run_dir) / "result.json") as f:
                    child = json.load(f)
            except Exception:  # noqa: BLE001
                pass
            rec["experiments"].append({
                "experiment_id": int(n.value),
                "game": at.get("game"), "status": at.get("status"),
                "variation_op": _variation_op_of(da),
                "delta": {k: da.get(k) for k in
                          ("knob_edit", "knob_attr", "knob_old_value", "knob_new_value",
                           "set_node_attrs", "ablation", "act_rule_varied", "cue_edit",
                           "cue_concept_added", "add_rules", "remove_rules")
                          if da.get(k) not in (None, "", "[]")},
                "child_result": {k: child.get(k) for k in
                                 ("status", "frames", "score", "regressions",
                                  "control_reforms", "variant_reforms",
                                  "control_shadow_ms", "avg_shadow_ms", "avg_turn_ms")
                                 if k in child},
                "judge_outcome": at.get("outcome"),
                "adopted": bool(at.get("adopted")),
                "adopt_denied": bool(at.get("adopt_denied")),
                "adopt_denied_reason": at.get("adopt_denied_reason") or None,
            })
            print(f"  experiment {int(n.value)}: op={_variation_op_of(da)} "
                  f"status={at.get('status')} outcome={at.get('outcome')} "
                  f"adopted={bool(at.get('adopted'))}", flush=True)
        if not exps:
            rec["experiments_note"] = ("no experiment minted — the concern grounded to no "
                                       "authorable variant (the honest wall); see the "
                                       "grounding walls in the concern's trail")
            print("  no experiment minted (honest wall)", flush=True)
            # THE MISSION'S FALLBACK for a composer shortfall: "document exactly
            # where the composer falls short and file THAT as a gap" — the
            # interlocutor reports the meta-gap over the SAME NL surface, so the
            # shortfall itself becomes a filed, surfaceable SelfConcern.
            meta = spec.get("meta_report")
            if meta:
                meta_reply = adapter.converse(meta, speech_act="statement")
                m_id, m_at = _concern_matching(adapter, spec.get("meta_unique") or meta[:40])
                rec["meta_gap"] = {"report": meta, "reply": meta_reply,
                                   "filed": m_id is not None, "concern_id": m_id}
                print(f"  meta-gap filed: {m_id is not None} (id={m_id})", flush=True)
        rec["standing_after"] = ( _standing_for(adapter, sc_id)[1] or {})
        rec["exhausted"] = bool(rec["standing_after"].get("experiments_exhausted"))
        rec["knob_before"] = knob_before
        rec["knob_after"] = _knob_value(adapter)
        adoptions = [a for a in _adoptions(adapter)
                     if str(a.get("experiment_id", "")) in
                     {f"#{e['experiment_id']}" for e in rec["experiments"]}]
        rec["adoptions"] = adoptions
        audit["residuals"].append(rec)

    # 4. SURFACE: the agent lists its own gaps over NL (all residuals). Under
    # long-session state the topic router can hijack one phrasing (recorded
    # honestly as a residual-of-this-audit if so); the seeded surfacing route
    # (seeds/question_targets.json) carries several — try them in order and
    # record every reply verbatim.
    audit["gaps_surfaced"] = []
    for q in ("What gaps do you have?", "What limitations do you have?",
              "What weaknesses do you have?"):
        surfaced = adapter.converse(q, speech_act="question")
        hits = sum(1 for spec in RESIDUALS
                   if (spec.get("unique") or "") and (spec.get("unique") or "") in (surfaced or "").lower()
                   or spec["id"] in ("R6", "R7", "R8", "R9")
                   and any(w in (surfaced or "").lower()
                           for w in spec["report"].lower().split()[:3]))
        listed = "filed that as a gap" not in (surfaced or "") and len(surfaced or "") > 80
        audit["gaps_surfaced"].append({"question": q, "reply": surfaced, "listed": listed})
        print(f"\n{q!r} ->\n{surfaced}", flush=True)
        if listed and ("reported" in (surfaced or "").lower() or hits):
            break

    audit["adoption_records"] = _adoptions(adapter)
    audit["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    audit_path = out_dir / "residual_closure_audit.json"
    with open(audit_path, "w") as f:
        json.dump(audit, f, indent=2, default=str)
    print("\n" + "=" * 96)
    print(f"audit written: {audit_path}")
    print("=" * 96)
    shutil.rmtree(ckpt, ignore_errors=True)
    return audit


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None,
                    help="output dir (default: runs/residual_closure/<stamp>)")
    ap.add_argument("--budget", type=float, default=300.0, help="per-residual pump budget, seconds")
    args = ap.parse_args(argv)
    stamp = time.strftime("%Y%m%dT%H%M%S")
    out_dir = Path(args.out) if args.out else ROOT / "runs" / "residual_closure" / stamp
    audit = run_audit(out_dir, budget_s=args.budget)
    return 0 if not audit["source_discipline_violations"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

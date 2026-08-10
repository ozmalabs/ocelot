#!/usr/bin/env python3
"""composer_closure_run — THE JABBERWOCK CLOSES R3/R4 THROUGH ITS OWN
PIPELINE, via the COMPOSER-CAPABILITY wave's two new families:
`datum_feedback_rule` and `shape_mint`. Sibling of
scripts/rule_literal_closure_run.py — same AST source discipline, same
NL-only surfaces, same daemon tick hooks — scoped to the two residuals the
agent's own residual-closure audit named as a COMPOSER SHORTFALL (commit
03630c0e27): "Your composer is a limitation; you cannot author a rule that
feeds a recorded datum back into a held belief."

  * R3 — track-record -> reliability: `world_adapter._record_interlocutor_
    correction` already records a contradiction datum
    (`self_report_contradiction_count`) on a party, but nothing fed it back
    into a held belief. `datum_feedback_rule`
    (domains/reflective_faculty._compose_datum_feedback_rule) closes it: a
    genuinely NEW, ADD-ONLY rule that matches every party the agent models
    and moves `self_report_reliability` down by a held, clamped step each
    time the datum genuinely changes.
  * R4 — person-shape minting: `interlocutor_model._record_shape_fit`
    records a poor-fit residual (a party whose accumulated features fit no
    held InterlocutorShape), but nothing constructed a new codebook entry
    from it. `shape_mint` (domains/reflective_faculty._compose_shape_mint)
    closes it: a brand-new InterlocutorShape built from the poor-fit party's
    own dominant features.

Per the bootstrap asymmetry (gamma-substrate/CLAUDE.md): this script BUILDS
nothing new — the two repertoire capabilities (builders + VariationOp/
RelationCue data + the double-pass/judge/adoption mechanics) already exist.
THE AGENT does the closing: it files each residual over NL (a real
deficiency report, gap_awareness's explicit-report surface), an NL "Work on
the X gap." promotes it, its own held `variation_pick` Program chooses
datum_feedback_rule / shape_mint (never hand-selected here), its own
composer picks the datum/belief pair or the poor-fit party from the report's
own words + its own accumulated state, a REAL dispatched child runs the
controlled double-pass over a REAL recorded conversation corpus, its own
judge (`judge_datum_feedback_outcome` / `judge_shape_mint_outcome`) reads
the verdict, and adoption (or an honest non-adoption) is entirely the
agent's own machinery (`perform_adoptions`, the regression veto) — unchanged,
reused as-is.

No-assistance discipline — identical to residual_closure_run.py's /
rule_literal_closure_run.py's:
  * ``OZMA_NO_LLM=1`` before boot.
  * Inputs after boot: ``converse()`` turns + the daemon's own tick hooks
    (``tick``, ``_steer_tick``, ``_concern_tick``, ``_dispatch_tick``,
    ``_close_tick``) + the host console's ``cancel_experiment`` (memory
    discipline only, never steering).
  * NO direct calls to reflective_faculty internals, NO hand-minted
    Experiment/SeedDelta/variant, NO direct graph mutation
    (``audit_source_discipline()`` walks this module's AST).

Run:
    PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/composer_closure_run.py \\
        [--out DIR] [--budget SECS] [--only R3,R4]
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

import residual_closure_run as rcr  # noqa: E402 — reuse the proven mechanical readers

# ---------------------------------------------------------------------------
# SOURCE DISCIPLINE — the SAME enforced property as rule_literal_closure_run.py.
# ---------------------------------------------------------------------------
_FORBIDDEN_CALLS = frozenset({
    "induce_concern", "ground_concern", "compose_design_for_goal",
    "mint_experiment", "close_experiment_loop", "perform_adoptions",
    "promote_self_concern", "repromote_self_concern", "revert_adoption",
    "_compose_experiment_rule", "_compose_cue_variant", "_compose_reply_ablation",
    "_compose_knob_variant", "_compose_rule_literal_variant",
    "_compose_datum_feedback_rule", "_compose_shape_mint", "_pick_variation_op",
    "_pick_reply_rule", "_pick_where_literal_rule_and_literal",
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


def _variation_op_of(delta: dict):
    """`residual_closure_run._variation_op_of` predates the COMPOSER-CAPABILITY
    wave — extend it here (a pure read, not a decision) rather than edit a
    module this script only imports."""
    op = rcr._variation_op_of(delta)
    if op is not None:
        return op
    if delta.get("datum_feedback_edit") == 1.0:
        return "datum_feedback_rule"
    if delta.get("shape_mint_edit") == 1.0:
        return "shape_mint"
    return None


# ---------------------------------------------------------------------------
# THE CORPUS — real converse() turns, so both residuals genuinely accrue
# their own datum before the report is ever filed (per the mission: build
# via converse(), never hand-mint the corpus or poke the datum directly).
# ---------------------------------------------------------------------------
CLEAN_TURNS = [
    ("Hello.", "greeting"),
    ("Miners extract ore from the mountain.", "statement"),
    ("Farmers haul grain from the valley.", "statement"),
]

# R3 — teach the agent a fact, have it TELL the party (grows believed_
# concepts for THIS party), then the party CONTRADICTS it (a deficiency
# word co-occurring with the told concept) repeatedly — the real, mechanical
# trigger for world_adapter._record_interlocutor_correction. Empirically
# (verified live against a full-seed boot) the natural per-turn comprehension
# pass needs the mention/belief graph to have settled once before the
# co-occurrence resolves cleanly, so the correction turn is genuinely
# REPEATED as separate real turns (not a single hand-crafted "gotcha" turn) —
# each repeat is honest NL, not a retry loop around a decision.
R3_INTRO = "Hi, I am Nora."
R3_TEACH_Q = "what is zqxbelt"
R3_TEACH_PAYLOAD = {"answer": "zqxbelt is a made up test concept",
                    "learn": [{"phrase": "zqxbelt"}]}
R3_ASK = "What do you know about zqxbelt?"
R3_CORRECTION_TURN = "That is wrong, zqxbelt is broken."
R3_CORRECTION_REPEATS = 4

# R4 — a sustained, distinctive register/cadence/style/affect combination
# (casual + medium-length + punctuated/long-worded + agitated) that the held
# 5-shape codebook does not fit on >= 2 dims (verified live: dominant
# features settle to casual/medium/ornate/agitated, decode_shape falls back
# to 'default_uncalibrated', fit=0) — a genuine, sustained poor-fit residual,
# not a single-turn blip.
R4_INTRO = "Hi, I am Zed."
R4_STYLE_TURN = "Yeah, whatever, this ridiculous stupid situation is unbelievably frustrating!!"
# NOTE: the CLEAN_TURNS prefix (run once, before ANY target, on the shared
# corpus party) establishes an initial plurality this style turn must first
# overturn (interlocutor_model._style_break_size's own majority-vote read) —
# empirically verified live, more repeats than the isolated-party case needs
# so the streak has room to recover after that one-time majority flip.
R4_STYLE_REPEATS = 10


# ---------------------------------------------------------------------------
# THE TARGET INVENTORY — filed over NL, front-loading each family's own cue
# word within the first 4 significant words of the report (promote_self_
# concern's own content_words[:4] scoping) for the cue to ground, plus a
# deficiency word (gap_awareness's explicit-report surface) for the gap to
# file at all.
# ---------------------------------------------------------------------------
TARGETS = [
    {"id": "R3", "title": "track-record -> reliability auto-update is datum-only",
     "report": ("Your interlocutor trust is broken; you record contradictions "
                "but fail to update your self report reliability from them."),
     "promote": "Work on the reliability gap.",
     "unique": "reliability"},
    {"id": "R4", "title": "new person-shape minting for poor-fit parties",
     # NOTE: 'limitation' (a gap_awareness deficiency word) is deliberately
     # AVOIDED here — it contains 'limit' as a substring, which the bounded
     # RelationCue's own keyword list also claims (seeds/relation_vocabulary.
     # json), so it would ALSO ground 'bound' and let knob_edit (priority 15
     # < shape_mint's 17) hijack the pick (verified live). 'broken' is a
     # deficiency word with no such collision.
     "report": ("Your shape persona profile is broken; a poor fit "
                "interlocutor never gets a new shape minted."),
     "promote": "Work on the shape persona gap.",
     "unique": "persona"},
]


def _witness_for(agent, spec_id: str, tag: str):
    """Mechanical readback ONLY (observability, not a decision): what the
    agent's OWN pipeline recorded about this concern's chosen party/belief,
    used to report measured numbers honestly. Reads graph state a real turn
    already wrote (StandingConcern.relations, the promoted concern's own
    party), never inspects the delta's own picks ahead of the agent's
    Experiment (those come from the child's result.json, read separately
    below)."""
    from domains import interlocutor_model as im
    party = im._active_party(agent)
    at = agent.s.node(party)["attrs"]
    return {
        "party_name": at.get("name"),
        "self_report_contradiction_count": at.get("self_report_contradiction_count"),
        "self_report_reliability": at.get("self_report_reliability"),
        "self_report_reliability_source": at.get("self_report_reliability_source"),
        "poor_fit_streak": at.get("poor_fit_streak"),
        "decode_fit": im.decode_shape(agent, party).get("fit"),
        "decode_shape_name": im.decode_shape(agent, party).get("name"),
    }


def run_closure(out_dir: Path, budget_s: float = 300.0, only=None) -> dict:
    os.environ["OZMA_NO_LLM"] = "1"
    import jabberwock_daemon as jd
    from domains.no_llm import no_llm
    from domains.experiment_dispatch import _INFLIGHT

    print("=" * 96)
    print("COMPOSER-CAPABILITY CLOSURE (R3/R4) — OZMA_NO_LLM=1; NL surface + daemon hooks only.")
    print("=" * 96)
    audit: dict = {"no_llm": bool(no_llm()),
                   "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "source_discipline_violations": audit_source_discipline(),
                   "targets": []}
    for v in audit["source_discipline_violations"]:
        print(f"  source-discipline violation: {v}", flush=True)

    out_dir.mkdir(parents=True, exist_ok=True)
    runs_dir = out_dir / "runs"
    ckpt = Path(tempfile.mkdtemp(prefix="jbw_composer_closure_ckpt_"))
    t0 = time.time()
    adapter, booted = jd.boot(ckpt, "full")
    adapter.shadow_read = True
    adapter.deep_ingest = True
    print(f"agent boot: {booted!r}, {adapter.s.node_count()} nodes, {time.time()-t0:.1f}s",
          flush=True)
    audit["boot"] = {"mode": booted, "nodes": adapter.s.node_count()}
    _INFLIGHT.clear()

    # BUILD THE REAL CORPUS FIRST (all of it, before any residual is filed —
    # same discipline as residual_closure_run.py / rule_literal_closure_run.py).
    for text, act in CLEAN_TURNS:
        adapter.converse(text, speech_act=act)

    targets = [t for t in TARGETS if only is None or t["id"] in only]
    keep_tags: set = set()

    for spec in targets:
        rec: dict = {"id": spec["id"], "title": spec["title"], "report_turn": spec["report"]}
        print(f"\n--- {spec['id']}: {spec['title']} " + "-" * max(4, 60 - len(spec["title"])),
              flush=True)

        # 0. ACCRUE THE REAL DATUM (real converse() turns; the SAME "build via
        # converse(), never hand-mint" discipline as the corpus above — kept
        # per-target so the concern's own corpus is easy to attribute).
        if spec["id"] == "R3":
            adapter.converse(R3_INTRO, speech_act="statement")
            adapter.learn_from_teacher(R3_TEACH_Q, R3_TEACH_PAYLOAD)
            adapter.converse(R3_ASK, speech_act="question")
            for _ in range(R3_CORRECTION_REPEATS):
                adapter.converse(R3_CORRECTION_TURN, speech_act="statement")
        elif spec["id"] == "R4":
            adapter.converse(R4_INTRO, speech_act="statement")
            for _ in range(R4_STYLE_REPEATS):
                adapter.converse(R4_STYLE_TURN, speech_act="statement")
        rec["datum_before"] = _witness_for(adapter, spec["id"], spec["id"])
        print(f"  datum accrued: {rec['datum_before']}", flush=True)

        # 1. FILE over NL.
        reply = adapter.converse(spec["report"], speech_act="statement")
        rec["file_reply"] = reply
        sc_id, sc_at = rcr._concern_matching(adapter, spec["unique"])
        rec["filed"] = sc_id is not None
        rec["concern_id"] = sc_id
        rec["concern_kind"] = (sc_at or {}).get("kind")
        print(f"  filed: {rec['filed']} (id={sc_id}, kind={rec['concern_kind']}) "
              f"reply={reply!r}", flush=True)
        if not rec["filed"]:
            rec["disposition_note"] = "filing surface missed — see file_reply"
            audit["targets"].append(rec)
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
        print(f"  promoted: {rec['promoted']} ({rec.get('pipeline')}) steer={steer!r}", flush=True)
        if not rec["promoted"]:
            audit["targets"].append(rec)
            continue

        _st, st_at = rcr._standing_for(adapter, sc_id)
        tag = (st_at or {}).get("name")
        rec["axis_tag"] = tag
        keep_tags.add(tag)

        # 3. GROUND + DISPATCH + JUDGE + CLOSE — the agent's own pipeline,
        # pumped one experiment at a time until this concern's trail is
        # terminal (closed, or honestly exhausted).
        def _closed():
            exps = rcr._experiment_for_tag(adapter, tag)
            if not exps:
                return False
            for _n, at in exps:
                if at.get("status") in ("requested", "running"):
                    return False
                out = at.get("outcome")
                if not out:
                    return False
                if out == "supported" and not (at.get("adopted") or at.get("adopt_denied")):
                    return False
            return True

        jd._concern_tick(adapter)
        exps0 = rcr._experiment_for_tag(adapter, tag)
        if exps0:
            rcr._pump(adapter, jd, runs_dir / spec["id"], _closed,
                     f"{spec['id']} close", budget_s, keep_tags)
        exps = rcr._experiment_for_tag(adapter, tag)
        rec["experiments"] = []
        for n, at in exps:
            da = rcr._delta_attrs(adapter, n)
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
                          ("datum_feedback_edit", "datum_feedback_datum_attr",
                           "datum_feedback_belief_attr", "shape_mint_edit",
                           "shape_mint_name", "shape_mint_party", "add_rules",
                           "add_concepts")
                          if da.get(k) not in (None, "", "[]")},
                "child_result": {k: child.get(k) for k in
                                 ("status", "frames", "score", "regressions",
                                  "control_belief", "variant_belief",
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
                                       "authorable variant (the honest wall); see the concern's "
                                       "own trail")
            print("  no experiment minted (honest wall)", flush=True)
        rec["standing_after"] = (rcr._standing_for(adapter, sc_id)[1] or {})
        rec["exhausted"] = bool(rec["standing_after"].get("experiments_exhausted"))
        adoptions = [a for a in rcr._adoptions(adapter)
                     if str(a.get("experiment_id", "")) in
                     {f"#{e['experiment_id']}" for e in rec["experiments"]}]
        rec["adoptions"] = adoptions
        rec["datum_after"] = _witness_for(adapter, spec["id"], spec["id"])
        print(f"  datum after: {rec['datum_after']}", flush=True)
        audit["targets"].append(rec)

    # 4. VERIFY LIVE: for an adopted target, re-drive the SAME kind of turn
    # and confirm the parent's own behaviour genuinely changed (real
    # converse() turns, mechanical readback only).
    audit["live_verification"] = []
    for rec in audit["targets"]:
        if not rec.get("adoptions"):
            continue
        if rec["id"] == "R3":
            before = _witness_for(adapter, "R3", rec.get("axis_tag") or "")
            adapter.converse(R3_CORRECTION_TURN, speech_act="statement")
            after = _witness_for(adapter, "R3", rec.get("axis_tag") or "")
            audit["live_verification"].append({"id": "R3", "before": before, "after": after})
        elif rec["id"] == "R4":
            for _ in range(2):
                adapter.converse(R4_STYLE_TURN, speech_act="statement")
            after = _witness_for(adapter, "R4", rec.get("axis_tag") or "")
            audit["live_verification"].append({"id": "R4", "after": after})

    audit["adoption_records"] = rcr._adoptions(adapter)
    audit["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    audit_path = out_dir / "composer_closure_audit.json"
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
                    help="output dir (default: runs/composer_closure/<stamp>)")
    ap.add_argument("--budget", type=float, default=300.0, help="per-target pump budget, seconds")
    ap.add_argument("--only", default=None, help="comma-separated subset of target ids (e.g. R3)")
    args = ap.parse_args(argv)
    stamp = time.strftime("%Y%m%dT%H%M%S")
    out_dir = Path(args.out) if args.out else ROOT / "runs" / "composer_closure" / stamp
    only = set(args.only.split(",")) if args.only else None
    audit = run_closure(out_dir, budget_s=args.budget, only=only)
    return 0 if not audit["source_discipline_violations"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""rule_literal_closure_run — THE JABBERWOCK CLOSES R2/R5 THROUGH ITS OWN
PIPELINE, via the WHERE-CLAUSE-VARIATION wave's new `rule_literal_edit`
family. Sibling of scripts/residual_closure_run.py — same AST source
discipline, same NL-only surfaces, same daemon tick hooks — scoped to the
two residuals that family's own inventory named as OUT OF REACH of every
variation family that existed before this wave:

  * R2 — seeds/reading_aperture.json's `escalate_narrative_shape`: the
    `sentences_read >= 3.0` where-clause floor is a fixed rule literal.
  * R5 — seeds/comprehension_health.json's `note_recurring_speech_act_
    divergence` (`Count >= 3.0` recurrence floor) AND seeds/salient_cache.
    json's `scell_promote` (`sc_mentions >= 3.0` / a ten-turn span floor) —
    BOTH rule literals on the same residual.

Per the bootstrap asymmetry (gamma-substrate/CLAUDE.md): this script BUILDS
nothing new — the `rule_literal_edit` repertoire capability (builder +
VariationOp data) already exists (domains/reflective_faculty.py,
seeds/variation_ops.json v1.2.0). THE AGENT does the closing: it files each
residual over NL (a real deficiency report, gap_awareness's explicit-report
surface), an NL "Work on the X gap." promotes it, its own held
`variation_pick` Program chooses `rule_literal_edit` (never hand-selected
here), its own `_compose_rule_literal_variant` picks the literal + direction
from the report's own words, a REAL dispatched child runs the controlled
double-pass over a REAL recorded conversation corpus, its own judge
(`judge_rule_literal_outcome`) reads the verdict, and adoption (or an
honest non-adoption) is entirely the agent's own machinery
(`perform_adoptions`, the provenance denylist, the regression veto) —
unchanged, reused as-is.

No-assistance discipline — identical to residual_closure_run.py's:
  * ``OZMA_NO_LLM=1`` before boot.
  * Inputs after boot: ``converse()`` turns + the daemon's own tick hooks
    (``tick``, ``_steer_tick``, ``_concern_tick``, ``_dispatch_tick``,
    ``_close_tick``) + the host console's ``cancel_experiment`` (memory
    discipline only, never steering).
  * One mechanical, ADAPTER-LEVEL setup call is sanctioned and NOT a
    decision: ``domains.salient_cache.install(adapter)`` — the documented
    opt-in seed-install function (mints the seed's rules + a SalienceClock
    singleton) scell_promote's own module says is required before its rule
    family can fire at all; it is the exact same class of call as
    ``load_all_seeds`` (mechanical seed I/O, not agent reasoning) and is
    called ONCE, before any concern is filed.
  * NO direct calls to reflective_faculty internals, NO hand-minted
    Experiment/SeedDelta/variant, NO direct graph mutation
    (``audit_source_discipline()`` walks this module's AST).

Run:
    PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/rule_literal_closure_run.py \\
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

import residual_closure_run as rcr  # noqa: E402 — reuse the proven mechanical readers

# ---------------------------------------------------------------------------
# SOURCE DISCIPLINE — the SAME enforced property as residual_closure_run.py,
# plus `install` (the salient_cache opt-in seed-install call this script's
# own docstring sanctions — a mechanical seed-loader, not a decision;
# EXCLUDED from the denylist for exactly that reason, mirroring
# `cancel_experiment`'s documented exclusion in the sibling module).
# ---------------------------------------------------------------------------
_FORBIDDEN_CALLS = frozenset({
    "induce_concern", "ground_concern", "compose_design_for_goal",
    "mint_experiment", "close_experiment_loop", "perform_adoptions",
    "promote_self_concern", "repromote_self_concern", "revert_adoption",
    "_compose_experiment_rule", "_compose_cue_variant", "_compose_reply_ablation",
    "_compose_knob_variant", "_compose_rule_literal_variant", "_pick_variation_op",
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


# ---------------------------------------------------------------------------
# THE CORPUS — real converse() turns, so the recorded conversation replays
# for real in the dispatched child (per the mission: build via converse(),
# never hand-mint the corpus).
# ---------------------------------------------------------------------------
CLEAN_TURNS = [
    ("Hello.", "greeting"),
    ("Miners extract ore from the mountain.", "statement"),
    ("Farmers haul grain from the valley.", "statement"),
]

# R2 — a pasted mini-story (3 sentences: 2 animate entities fox+crow, one
# 'want' event) — the proven narrative_shape trigger (see
# tests/test_aperture_escalation_migrated.py's NARRATIVE_3), read at
# EXACTLY the sentences_read==3.0 floor, so raising the floor by the
# family's own literal_step (1.0) cleanly stops it from escalating.
R2_STORY = ("A fox saw a crow perched in a tree. The crow was holding a piece of "
           "cheese in its beak. The fox wanted the cheese very much and began to "
           "think of a plan.")

# R5a — a divergence pair (comp_kind classifies an imperative pragmatically
# as a question; the deep shadow-reader hears it as a plain statement) —
# repeated at EXACTLY the recurrence floor (3), the proven trigger.
R5A_DIVERGENT = ["Name one of your rules.", "Name one of your seeds.",
                 "Name one of your reflexes."]

# R5b — a longer narrative with a persistent character (fox) and a
# secondary one (crow), read through the salient-cache working memory
# (domains.salient_cache.install, called once below) so scell_promote's
# span/mentions floors are genuinely exercised.
R5B_STORY = (
 "A fox lived alone in the deep forest near a quiet river. "
 "Every morning the fox would wake early and search for food along the riverbank. "
 "One day the fox spotted a crow perched high in an old oak tree. "
 "The crow was holding a piece of cheese in its beak and looking very pleased. "
 "The fox admired the crow's shiny black feathers from below the tree. "
 "The fox wanted the cheese very much and began to think of a clever plan. "
 "The fox called out to the crow and praised its beautiful singing voice. "
 "The crow, flattered by the fox, opened its beak to sing a proud song. "
 "The cheese fell from the crow's beak straight down to the fox. "
 "The fox snatched the cheese quickly and trotted away from the tree. "
 "The crow realized too late that the fox had tricked it completely. "
 "From that day on, the crow never trusted a flattering fox again."
)


# ---------------------------------------------------------------------------
# THE TARGET INVENTORY — filed over NL, front-loading the 'floor' cue word
# (rule_literal_edit's own RelationCue) within the first 4 significant words
# of the report (promote_self_concern's own content_words[:4] scoping —
# see seeds/variation_ops.json v1.2.0's description), and carrying the
# rule's own where-clause vocabulary + a direction word anywhere in the rest
# of the sentence for _compose_rule_literal_variant's own Argmax picks.
# ---------------------------------------------------------------------------
TARGETS = [
    {"id": "R2", "title": "escalate_narrative_shape's sentences_read floor is a rule literal",
     "report": ("Floor of three sentences read before narrative shape escalation is "
                "wrong and hardcoded as a rule literal; your narrative shape escalation "
                "requires sentences_read of at least three sentences read before it "
                "fires, and that floor makes you escalate too eagerly and too often on "
                "short pasted text that is not really a story."),
     "promote": "Work on the narrative escalation floor gap.",
     "unique": "narrative shape escalation", "target_rule": "escalate_narrative_shape",
     "expect_direction": "decrease_fires"},
    {"id": "R5a", "title": "note_recurring_speech_act_divergence's recurrence Count floor is a rule literal",
     "report": ("Floor of three recurring divergences before you notice is wrong and "
                "hardcoded as a rule literal; comp kind versus shadow speech act "
                "divergence recurring three times is far too eager a bar, and you flag "
                "that divergence too eagerly and too often on ordinary imperative "
                "requests."),
     "promote": "Work on the divergence recurrence floor gap.",
     "unique": "recurring divergences", "target_rule": "note_recurring_speech_act_divergence",
     "expect_direction": "decrease_fires"},
    {"id": "R5b", "title": "scell_promote's span/mentions floors are rule literals",
     "report": ("Floor of ten turns of span before salient promotion is wrong and "
                "hardcoded as a rule literal, and three mentions before promotion is "
                "also wrong; your salient cell promotion turn span between last turn "
                "and first turn of ten turns is far too eager, and you promote entities "
                "too eagerly and too often on minor mentions."),
     "promote": "Work on the salient promotion span gap.",
     "unique": "salient cell promotion", "target_rule": "scell_promote",
     "expect_direction": "decrease_fires"},
]


def run_closure(out_dir: Path, budget_s: float = 300.0) -> dict:
    os.environ["OZMA_NO_LLM"] = "1"
    import jabberwock_daemon as jd
    from domains.no_llm import no_llm
    from domains.experiment_dispatch import _INFLIGHT
    from domains import salient_cache as sc

    print("=" * 96)
    print("RULE-LITERAL CLOSURE (R2/R5) — OZMA_NO_LLM=1; NL surface + daemon hooks only.")
    print("=" * 96)
    audit: dict = {"no_llm": bool(no_llm()),
                   "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "source_discipline_violations": audit_source_discipline(),
                   "targets": []}
    for v in audit["source_discipline_violations"]:
        print(f"  source-discipline violation: {v}", flush=True)

    out_dir.mkdir(parents=True, exist_ok=True)
    runs_dir = out_dir / "runs"
    ckpt = Path(tempfile.mkdtemp(prefix="jbw_rlclosure_ckpt_"))
    t0 = time.time()
    adapter, booted = jd.boot(ckpt, "full")
    adapter.shadow_read = True
    adapter.deep_ingest = True
    sc.install(adapter)          # mechanical opt-in seed install — see module docstring
    print(f"agent boot: {booted!r}, {adapter.s.node_count()} nodes, "
          f"salient_cache installed: {sc.installed(adapter)}, {time.time()-t0:.1f}s", flush=True)
    audit["boot"] = {"mode": booted, "nodes": adapter.s.node_count(),
                     "salient_cache_installed": sc.installed(adapter)}
    _INFLIGHT.clear()

    # BUILD THE REAL CORPUS FIRST (all of it, before any residual is filed —
    # same discipline as residual_closure_run.py) so every replay experiment
    # has real recorded turns, incl. the ones that actually exercise R2/R5.
    for text, act in CLEAN_TURNS:
        adapter.converse(text, speech_act=act)
    adapter.converse(R2_STORY, speech_act="statement")
    for text in R5A_DIVERGENT:
        adapter.converse(text, speech_act="statement")
    adapter.converse(R5B_STORY, speech_act="statement")

    keep_tags: set = set()
    for spec in TARGETS:
        rec: dict = {"id": spec["id"], "title": spec["title"],
                     "target_rule": spec["target_rule"], "report_turn": spec["report"]}
        print(f"\n--- {spec['id']}: {spec['title']} " + "-" * max(4, 60 - len(spec["title"])),
              flush=True)

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
                "variation_op": rcr._variation_op_of(da),
                "delta": {k: da.get(k) for k in
                          ("rule_literal_edit", "remove_rules", "add_rules",
                           "rule_literal_old_value", "rule_literal_new_value",
                           "rule_literal_direction", "act_rule_varied")
                          if da.get(k) not in (None, "", "[]")},
                "child_result": {k: child.get(k) for k in
                                 ("status", "frames", "score", "regressions",
                                  "control_witness_fires", "variant_witness_fires",
                                  "control_shadow_ms", "avg_shadow_ms", "avg_turn_ms")
                                 if k in child},
                "judge_outcome": at.get("outcome"),
                "adopted": bool(at.get("adopted")),
                "adopt_denied": bool(at.get("adopt_denied")),
                "adopt_denied_reason": at.get("adopt_denied_reason") or None,
            })
            print(f"  experiment {int(n.value)}: op={rcr._variation_op_of(da)} "
                  f"status={at.get('status')} outcome={at.get('outcome')} "
                  f"adopted={bool(at.get('adopted'))} "
                  f"control/variant witness={da and (at.get('control_witness_fires'), at.get('variant_witness_fires'))}",
                  flush=True)
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
        audit["targets"].append(rec)

    audit["adoption_records"] = rcr._adoptions(adapter)
    audit["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    audit_path = out_dir / "rule_literal_closure_audit.json"
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
                    help="output dir (default: runs/rule_literal_closure/<stamp>)")
    ap.add_argument("--budget", type=float, default=300.0, help="per-target pump budget, seconds")
    args = ap.parse_args(argv)
    stamp = time.strftime("%Y%m%dT%H%M%S")
    out_dir = Path(args.out) if args.out else ROOT / "runs" / "rule_literal_closure" / stamp
    audit = run_closure(out_dir, budget_s=args.budget)
    return 0 if not audit["source_discipline_violations"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

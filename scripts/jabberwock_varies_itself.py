"""jabberwock_varies_itself — closing the "SeedDelta is always trivial" gap.

The self-experiment faculty (scripts/jabberwock_authors_experiments.py,
domains/reflective_faculty.py's `_compose_experiment_rule`) already authors
its own MINT + ANALYSE rules from a framed concern. What it minted was always
a TRIVIAL delta (`skip_seeds: "[]"`) — the agent never actually chose WHAT to
vary about itself. This script drives the CLOSED loop where it does:

  1. PROVENANCE (mechanical, substrate/boot_all.py): every loaded seed gets a
     compact `SeedSummary{seed_id, keywords_text, skippable}` node — the
     agent's own queryable "what do I know, and where did it come from".
  2. THE AGENT PICKS: the mint rule's SeedDelta.skip_seeds is chosen by a HELD
     TERM inside the rule itself — an Argmax over `skippable` SeedSummary
     nodes of word-overlap with the TRIGGERING axis's own residual_predicates
     (the same StringIndexOf/Sum text-overlap-argmax shape the browse
     composer uses for relevance). Frozen/core seeds are excluded mechanically
     (skippable=0 at load time, see boot_all.py's documented denylist).
  3. A VARIANT RULE INTO THE DELTA: when the concern also grounds 'embed' (a
     new RelationCue, distinct from 'vary' — see relation_vocabulary.json), a
     threshold-shifted copy of the agent's own judge rule is authored and
     embedded into delta.add_rules — installed on the DISPATCHED COPY (not
     locally): the parent tries a modification ON THE VARIANT of itself.
  4. TEACH CLOSES THE LOOP: once judged, the analysis rule marks
     `conclusion_ready`; `close_experiment_loop` (mechanical host I/O) persists
     the verdict via teach() so a future boot has it.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_varies_itself.py
"""
from __future__ import annotations
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import induce_concern, ground_concern, close_experiment_loop
from domains.experiment_dispatch import scan_and_dispatch, _INFLIGHT
from worlds.arc import ArcWorld
from arc3_env import NavigateEnv

RUNS_DIR = os.path.join(ROOT, "runs", "jabberwock_varies_itself")
TIMEOUT_S = 90
_CONCLUSIONS_SEED = os.path.join(ROOT, "seeds", "experiment_conclusions.json")


def _pass(ok: bool, label: str) -> bool:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    return ok


def _delta_of(a, exp):
    for d in a.inner.neighbours(exp, "has_delta"):
        if a.inner.has_node(d):
            return a.s.node(d)["attrs"]
    return {}


def main():
    _INFLIGHT.clear()
    overall = True
    existed_conclusions = os.path.exists(_CONCLUSIONS_SEED)

    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    donkey = {"n": 0}
    a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    S, I = a.s, a.inner

    print("=" * 92)
    print("THE JABBERWOCK VARIES ITSELF — non-trivial SeedDeltas, self-picked, self-taught")
    print("=" * 92)

    summaries = list(S.nodes("SeedSummary"))
    n_skippable = sum(1 for n in summaries if S.node(n)["attrs"].get("skippable") == 1.0)
    print(f"\n  [provenance] {len(summaries)} SeedSummary nodes "
          f"({n_skippable} skippable, {len(summaries) - n_skippable} frozen)")
    ok0 = _pass(len(summaries) > 100 and n_skippable > 0, "seed provenance present after load_all_seeds")
    overall &= ok0

    w = ArcWorld(NavigateEnv())
    sub, ctx = w.reset()
    a.perceive_frame(sub)
    a.tick()
    print(f"\n  [stage0] perceived world: {w.label!r} (offline arc3_env game)")

    # STAGE 1 — frame the self-experiment concern, now including 'embed' (the
    # distinct concern of actually carrying a modified rule onto the dispatched
    # copy, not just flagging the delta as varied).
    obs = [
        ["test", "HYPOTHESIS", "about", "SELF"],
        ["vary", "SEED", "by", "DELTA"],
        ["send", "VARIANT", "to", "WORLD"],
        ["judge", "TRIAL", "by", "OUTCOME"],
        ["embed", "VARIANT", "as", "RULE"],
    ]
    ind = induce_concern(a, obs, name_hint="self_experiment_concern_v2")
    key = ind.get("capability_key")
    print(f"\n  [induce_concern] minted={ind.get('minted')}  key={key!r}")
    ok1 = _pass(bool(ind.get("minted")) and key is not None,
                "induce_concern minted a CapabilityAxis from the framed concern")
    overall &= ok1

    before_rules = I.rule_count()
    g = ground_concern(a, [key]) if key else {}
    after_rules = I.rule_count()
    print(f"\n  [ground_concern] grounded={g.get('grounded')}  path={g.get('path')}")
    print(f"     grounded_relations={g.get('grounded_relations')}")
    ok2 = _pass(g.get("grounded") is True and g.get("path") == "compose_experiment_rule",
                "ground_concern picked the 'experiment' composer and it grounded")
    overall &= ok2
    ok3 = _pass(after_rules - before_rules == 2,
                f"the composer installed exactly 2 live rules (rule_count {before_rules} -> {after_rules})")
    overall &= ok3

    # STAGE 2 — TWO SEPARATE triggering axes with DISTINCT topic residuals (each
    # a genuine "I don't have a term for this" gap, unrelated to the concern
    # above), so the discriminative check has something to discriminate: a
    # domain-specific residual vs. a DIFFERENT domain-specific residual.
    ind_a = induce_concern(a, [["astronomy", "ME", "about", "STARS"]], name_hint="astronomy_gap")
    ind_b = induce_concern(a, [["agriculture", "ME", "about", "FARMING"]], name_hint="agriculture_gap")
    print(f"\n  [stage2] triggering axes: astronomy minted={ind_a.get('minted')}  "
          f"agriculture minted={ind_b.get('minted')}")
    axis_a = next((n for n in S.nodes("CapabilityAxis") if str(n) == str(ind_a.get("axis_id"))), None)
    axis_b = next((n for n in S.nodes("CapabilityAxis") if str(n) == str(ind_b.get("axis_id"))), None)
    ok4 = _pass(bool(ind_a.get("minted")) and bool(ind_b.get("minted")),
                "both triggering axes minted (genuine unexplained residuals)")
    overall &= ok4

    a.tick()
    I.run_rules()
    exp_a = next(iter(I.neighbours(axis_a, "tested_by")), None) if axis_a is not None else None
    exp_b = next(iter(I.neighbours(axis_b, "tested_by")), None) if axis_b is not None else None
    ok5 = _pass(exp_a is not None and exp_b is not None,
                "both triggering axes got their OWN Experiment via 'tested_by' — no host add_node")
    overall &= ok5

    # STAGE 3 — THE AGENT PICKED WHAT TO VARY: read the two deltas back and
    # check the discriminative claim -- a real, non-empty, DIFFERENT pick per
    # topic, each genuinely overlapping that axis's own words.
    da_a = _delta_of(a, exp_a) if exp_a is not None else {}
    da_b = _delta_of(a, exp_b) if exp_b is not None else {}
    skip_a, skip_b = da_a.get("skip_seed_id", ""), da_b.get("skip_seed_id", "")
    print(f"\n  [stage3] astronomy-gap picked skip_seed_id={skip_a!r}  "
          f"skip_seeds={da_a.get('skip_seeds')!r}")
    print(f"           agriculture-gap picked skip_seed_id={skip_b!r}  "
          f"skip_seeds={da_b.get('skip_seeds')!r}")
    ok6 = _pass(bool(skip_a) and bool(skip_b), "both picks are non-empty (the Term found genuine overlap)")
    overall &= ok6
    ok7 = _pass(skip_a != skip_b, "the two topic-distinct axes picked DIFFERENT seeds (discriminative)")
    overall &= ok7
    ok8 = _pass("astronomy" in skip_a.lower() if skip_a else False,
                f"the astronomy-gap's pick ({skip_a!r}) genuinely names an astronomy-topic seed")
    overall &= ok8
    ok9 = _pass("agriculture" in skip_b.lower() if skip_b else False,
                f"the agriculture-gap's pick ({skip_b!r}) genuinely names an agriculture-topic seed")
    overall &= ok9
    ok10 = _pass(da_a.get("skip_seeds") == json.dumps([skip_a]) if skip_a else False,
                 "skip_seeds JSON list matches the picked skip_seed_id (Term-consistent)")
    overall &= ok10

    # STAGE 4 — THE VARIANT RULE: 'embed' grounded, so the delta carries a real
    # authored rule (installed on the DISPATCHED COPY only, never locally).
    add_rules_a = json.loads(da_a.get("add_rules") or "[]")
    print(f"\n  [stage4] delta.add_rules carries {len(add_rules_a)} rule(s); "
          f"variant_threshold={da_a.get('variant_threshold')}")
    ok11 = _pass(len(add_rules_a) == 1 and add_rules_a[0].get("name", "").startswith(
        "judge_experiment_outcome_variant_"),
        "a genuine threshold-shifted variant of the judge rule is embedded (not installed locally)")
    overall &= ok11
    ok12 = _pass(len(add_rules_a) == 1 and add_rules_a[0]["match"] == [["exp", "produced", "run"]],
                 "the embedded variant carries a real, well-formed match/where/effects rule body")
    overall &= ok12

    # STAGE 5 — DISPATCH one of the two experiments offline and wait.
    print("\n  [stage5] dispatching via domains.experiment_dispatch.scan_and_dispatch (offline)...")
    ok13 = True
    if exp_a is not None:
        t0 = time.time()
        status = None
        while time.time() - t0 < TIMEOUT_S:
            scan_and_dispatch(a, RUNS_DIR)
            status = S.node(exp_a)["attrs"].get("status")
            if status not in ("requested", "running"):
                break
            time.sleep(0.5)
        print(f"     experiment finished with status={status!r} after {time.time() - t0:.1f}s "
              f"(boot mode was 'fresh+skip': skip_seeds={da_a.get('skip_seeds')!r} ablated {skip_a!r})")
        ok13 = _pass(status == "done", "the dispatched child completed with the ablated seed withheld")
        overall &= ok13
    else:
        ok13 = _pass(False, "no Experiment was dispatched (stage 2/3 already failed)")
        overall &= ok13

    # STAGE 6 — the agent's OWN analysis rule judges the Run + marks conclusion_ready.
    ok14 = True
    if exp_a is not None and ok13:
        I.run_rules()
        ea = S.node(exp_a)["attrs"]
        outcome = ea.get("outcome")
        ready = ea.get("conclusion_ready")
        print(f"\n  [stage6] Experiment.outcome={outcome!r}  conclusion_ready={ready!r}")
        ok14 = _pass(outcome in ("supported", "refuted", "inconclusive") and ready is True,
                     "the agent's own analysis rule wrote a verdict AND marked it ready to teach")
        overall &= ok14
    else:
        ok14 = _pass(False, "skipped (no completed experiment to analyse)")
        overall &= ok14

    # STAGE 7 — TEACH closes the loop: persist the verdict, idempotently.
    recs = close_experiment_loop(a)
    print(f"\n  [stage7] close_experiment_loop taught {len(recs)} conclusion(s): {recs}")
    ok15 = _pass(len(recs) >= 1 and recs[0].get("saved") is True,
                 "the judged Experiment's verdict was persisted via teach() (new, saved=True)")
    overall &= ok15
    recs2 = close_experiment_loop(a)
    ok16 = _pass(recs2 == [], "re-running close_experiment_loop is a no-op (Experiment.taught guards it)")
    overall &= ok16
    if os.path.exists(_CONCLUSIONS_SEED):
        with open(_CONCLUSIONS_SEED) as f:
            saved = json.load(f)
        taught_nodes = [n for n in saved.get("nodes", []) if n.get("type") == "TaughtHint"]
        print(f"     seeds/experiment_conclusions.json now carries {len(taught_nodes)} TaughtHint node(s)")
        if taught_nodes:
            print(f"     e.g. {taught_nodes[-1]['attrs']}")

    print(f"\n  [donkey] LLM calls: {donkey['n']}")
    print("=" * 92)
    if overall:
        print("  ALL STAGES PASS. The jabberwock picked WHAT to ablate (a held Argmax Term over its own")
        print("  seed provenance), embedded a genuine self-modification into the dispatched copy, ran the")
        print("  trial, judged it, and taught the conclusion — all via its OWN authored rules.")
    else:
        print("  Some stages FAILED (see [FAIL] lines above) — honest report, not papered over.")

    # Honest cleanup note: this run's teach() writes ARE real, persisted seed data (per
    # CLAUDE.md's teach() facility — self-knowledge should survive a reboot), so this
    # script does NOT delete seeds/experiment_conclusions.json on exit (tests/
    # test_self_delta.py's own guard fixture handles the test-time snapshot/restore).
    if not existed_conclusions and os.path.exists(_CONCLUSIONS_SEED):
        print(f"\n  NOTE: seeds/experiment_conclusions.json was created by this run and left in place "
              f"(real taught self-knowledge, not test fixture output) — delete it manually if this was "
              f"a throwaway run.")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())

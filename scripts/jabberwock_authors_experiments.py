"""HAVE THE JABBERWOCK AUTHOR ITS OWN SELF-EXPERIMENT FACULTY. I only frame the concern.

The concern, in the agent's grounding vocabulary: to TEST a HYPOTHESIS about itself, it VARIES
itself (a seed delta) and SENDS the variant to the WORLD as a dispatched trial; when a trial comes
back it JUDGES the trial by its RESULT. That is "decide to run an experiment on a modified copy of
myself, then read the verdict" — the self-experiment loop.

The agent's own machinery does the building (same faculty every other jabberwock_authors_* /
jabberwock_builds_* script drives — see domains/reflective_faculty.py):
  induce_concern  — observe the concern's structure; mint it as a CapabilityAxis (residual
                    predicates) when no held term-shape covers it.
  ground_concern  — map the residual through the held RelationCue lexicon, pick a composer by
                    the grounded relation heads (seeds/composer_dispatch.json), and have THAT
                    composer author + install the rule(s) live.

This script adds NO Python decision logic for what the rules should say — it only frames the
concern text and reads back what the agent authored. The composer it drives is
`_compose_experiment_rule` (new in this change): from the grounded relations it builds (a) a MINT
rule — an observed, unexplained residual axis is the agent's own "I have a gap" signal, so it
decides to test a hypothesis about itself and authors an Experiment{status:requested}+SeedDelta —
and (b) an ANALYSE rule — once a dispatched trial PRODUCED a finished Run, judge it by score-per-
frame sign (a held IfThenElse Term, not Python if/else) and write the verdict onto the Experiment.

The DISPATCH MECHANISM (domains/experiment_dispatch.py) is unchanged, thin host I/O: it only sees
Experiment.status=='requested' and spawns/ingests a child process. It never decides to test, what
to vary, where to send it, or what the outcome means — those are all the AUTHORED rules' calls.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_authors_experiments.py
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
from domains.reflective_faculty import induce_concern, ground_concern
from domains.experiment_dispatch import scan_and_dispatch, _INFLIGHT
from worlds.arc import ArcWorld
from arc3_env import NavigateEnv

RUNS_DIR = os.path.join(ROOT, "runs", "jabberwock_authors_experiments")
TIMEOUT_S = 90


def _pass(ok: bool, label: str) -> bool:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    return ok


def main():
    _INFLIGHT.clear()
    overall = True
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    donkey = {"n": 0}
    a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    S, I = a.s, a.inner

    print("=" * 92)
    print("THE JABBERWOCK AUTHORS ITS OWN SELF-EXPERIMENT FACULTY — I only frame the concern")
    print("=" * 92)

    # STAGE 0 — perceive a game (test scaffolding, host I/O): the agent needs SOME perceived world
    # before the SEND relation's mint-rule part has anything real to read "which world" from.
    w = ArcWorld(NavigateEnv())
    sub, ctx = w.reset()
    a.perceive_frame(sub)
    a.tick()
    print(f"\n  [stage0] perceived world: {w.label!r} (offline arc3_env game)")

    # STAGE 1 — FRAME THE CONCERN (the agent's grounding vocabulary; each clause LEADS with the
    # cue word induce_concern keys the residual on):
    obs = [
        ["test", "HYPOTHESIS", "about", "SELF"],     # I test a hypothesis about myself
        ["vary", "SEED", "by", "DELTA"],              # by varying a seed (a delta of myself)
        ["send", "VARIANT", "to", "WORLD"],           # and sending the variant to the world
        ["judge", "TRIAL", "by", "OUTCOME"],          # then judging the trial by its outcome
    ]
    ind = induce_concern(a, obs, name_hint="self_experiment_concern")
    key = ind.get("capability_key")
    print(f"\n  [induce_concern] minted={ind.get('minted')}  key={key!r}")
    print(f"     residual_predicates={ind.get('residual_predicates')}")
    ok1 = _pass(bool(ind.get("minted")) and key is not None,
                "induce_concern minted a CapabilityAxis from the framed concern")
    overall &= ok1

    # STAGE 2 — GROUND: the held RelationCue lexicon + the seeded composer_pick Program pick the
    # composer; THAT composer authors + installs the rule(s). No rule text is written here.
    before_rules = I.rule_count()
    g = ground_concern(a, [key]) if key else {}
    after_rules = I.rule_count()
    print(f"\n  [ground_concern] grounded={g.get('grounded')}  path={g.get('path')}  form={g.get('form')}")
    print(f"     grounded_relations={g.get('grounded_relations')}")
    if g.get("wall"):
        print(f"     WALL (honest): {g.get('wall')}")
    ok2 = _pass(g.get("grounded") is True and g.get("path") == "compose_experiment_rule",
                "ground_concern picked the 'experiment' composer and it grounded")
    overall &= ok2
    ok3 = _pass(after_rules - before_rules == 2,
                f"the composer installed exactly 2 live rules (rule_count {before_rules} -> {after_rules})")
    overall &= ok3
    rule_names = sorted((r.get("name") for r in (g.get("rules") or [])))
    print(f"     installed rule names: {rule_names}")
    for r in (g.get("rules") or []):
        print(f"\n     ---- authored rule {r['name']!r} ----")
        print("     match:", r["match"])
        print("     where:", json.dumps(r["where"])[:200], "...")
        print("     effects:", json.dumps(r["effects"])[:400], "...")

    # STAGE 3 — CREATE THE TRIGGERING CONDITION (test scaffolding, host I/O per CLAUDE.md: reporting
    # an OBSERVED fact is legitimate ingest, same category as jabberwock_game_self_goal.py's
    # report_efficacy). A SEPARATE, later-arising unexplained residual (a genuine "I don't have a
    # term for this yet" gap) — NOT the same axis the concern above used to author the rule — so the
    # newly-authored MINT rule has something new to react to, exactly as it would for any future gap.
    obs2 = [["puzzles", "ME", "about", "NAVIGATE"]]
    ind2 = induce_concern(a, obs2, name_hint="navigate_efficacy_gap")
    print(f"\n  [stage3] triggering observation minted={ind2.get('minted')}  "
          f"key={ind2.get('capability_key')!r}")
    ok4 = _pass(bool(ind2.get("minted")), "the triggering axis (a genuine unexplained residual) minted")
    overall &= ok4
    axis2 = next((n for n in S.nodes("CapabilityAxis") if str(n) == str(ind2.get("axis_id"))), None)

    before_exp = set(S.nodes("Experiment"))
    a.tick()
    I.run_rules()
    after_exp = set(S.nodes("Experiment")) - before_exp
    # HONEST NOTE: the mint rule's guard is "is_axis + no tested_by edge yet" — ANY untested
    # residual axis qualifies, including the axis the concern-framing above itself minted
    # (self_experiment_concern). That axis is now ALSO untested, so it fires too: authoring the
    # self-experiment rule is itself treated as a gap worth testing (an honest, self-referential
    # emergent property of the rule as written, not something this script special-cases away).
    exp = next(iter(I.neighbours(axis2, "tested_by")), None) if axis2 is not None else None
    print(f"\n  [stage3] run_rules minted {len(after_exp)} new Experiment(s) total "
          f"(one PER untested residual axis, including any pre-existing ones — self-referential, "
          "expected); the one reached via THIS trigger's own tested_by edge is what stage 3 checks.")
    ok5 = _pass(exp is not None,
                "the triggering axis's OWN Experiment appeared via its 'tested_by' edge — "
                "no host code called add_node('Experiment', ...)")
    overall &= ok5

    if exp is not None:
        ea = S.node(exp)["attrs"]
        print(f"\n  [stage3] Experiment authored by the agent's OWN rule: {ea}")
        ok6 = _pass(ea.get("status") == "requested", "Experiment.status == 'requested'")
        overall &= ok6
        ok7 = _pass(ea.get("game") == "navigate", f"Experiment.game == 'navigate' (got {ea.get('game')!r})")
        overall &= ok7
        deltas = [d for d in I.neighbours(exp, "has_delta") if I.has_node(d)]
        ok8 = _pass(len(deltas) == 1, "Experiment -has_delta-> exactly one SeedDelta")
        overall &= ok8
        if deltas:
            da = S.node(deltas[0])["attrs"]
            print(f"     SeedDelta attrs: {da}")
    else:
        ok6 = ok7 = ok8 = _pass(False, "no Experiment to inspect (stage 3 already failed)")
        overall &= ok6

    # STAGE 4 — DISPATCH the requested experiment offline (the mechanism, unchanged host I/O) and
    # wait for the child to finish.
    print("\n  [stage4] dispatching via domains.experiment_dispatch.scan_and_dispatch (offline)...")
    ok9 = True
    if exp is not None:
        t0 = time.time()
        status = None
        while time.time() - t0 < TIMEOUT_S:
            scan_and_dispatch(a, RUNS_DIR)
            status = S.node(exp)["attrs"].get("status")
            if status not in ("requested", "running"):
                break
            time.sleep(0.5)
        print(f"     experiment finished with status={status!r} after {time.time() - t0:.1f}s")
        ok9 = _pass(status == "done", "the dispatched child completed (status == 'done')")
        overall &= ok9
    else:
        ok9 = _pass(False, "no Experiment was dispatched (stage 3 already failed)")
        overall &= ok9

    # STAGE 5 — the agent's OWN analysis rule reads the produced Run and writes the outcome.
    ok10 = True
    if exp is not None and ok9:
        I.run_rules()
        ea = S.node(exp)["attrs"]
        outcome = ea.get("outcome")
        print(f"\n  [stage5] Experiment.outcome = {outcome!r} (written by the agent's own analysis rule)")
        ok10 = _pass(outcome in ("supported", "refuted", "inconclusive"),
                     "the agent's analysis rule wrote a verdict onto the Experiment")
        overall &= ok10
    else:
        ok10 = _pass(False, "skipped (no completed experiment to analyse)")
        overall &= ok10

    print(f"\n  [donkey] LLM calls: {donkey['n']}")
    print("=" * 92)
    if overall:
        print("  ALL STAGES PASS. The jabberwock authored its OWN mint + analyse rules from a framed")
        print("  concern; a later unexplained residual triggered the mint rule (no host add_node); the")
        print("  dispatch mechanism (unchanged) ran the child; the agent's own analysis rule judged it.")
    else:
        print("  Some stages FAILED (see [FAIL] lines above) — honest report, not papered over.")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())

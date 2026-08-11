"""PROACTIVE topic selection wired from `learning_progress_curiosity` into
gap-awareness (`seeds/curiosity_topic_selection.json::lp_mint_topic_gap`), per
`docs/research/theory_convergence/RAVANA_CONVERGENCE_AUDIT.md` §6.2.

Runs the mechanical measure (`scripts/curiosity_topic_selection_measure.py`)
and pins the mechanism-level, decision-level claims: every decision under test
(residual, learning progress, the gate, attend, and the SelfConcern mint
itself) is a graph RULE under `run_rules()`; the measure only submits topic
phrases, schedules a fake teacher's grounding successes (world I/O), ticks,
and reads attributes / SelfConcern nodes back.

  * D1/D2/D3  the gated (mode=0, two-timescale) arm correctly proactively
              flags the genuinely-progressing topic and correctly declines to
              flag either the already-resolved topic (nothing left to learn)
              or the intractable/noisy-TV-analogue topic (persistent,
              non-convergent surprise) — the actual gap-FILING DECISION, not
              merely an interest curve.
  * D4        the falsifier (mode=1, raw-surprise gating — the RAVANA-
              equivalent single-signal comparison) DOES proactively flag the
              intractable topic: the two-timescale gate is load-bearing for
              the decision.
  * D5        neither this measure script nor `domains/curiosity_topic_
              ingest.py` ever set_attr's a curiosity/mint decision key.
  * ensemble  the noisy-TV-resistance decision (D3) and the other three hold
              across N_ENS=16 independent draws (an allocation/decision rate
              is a property of the stimulus distribution, not one draw).

Also gates the seed itself: default-OFF (self_load_only, excluded from
`load_all_seeds`) and byte-identical when the hub is never installed.

Prereg: docs/research/agent_loop/jabberwock_learning_progress_gap_wiring_prereg.md.
"""
import importlib
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

M = importlib.import_module("scripts.curiosity_topic_selection_measure")


@pytest.fixture(scope="module")
def res():
    M.main()
    with open(os.path.join(M.RESULTS, "curiosity_topic_selection.json")) as fh:
        return json.load(fh)


def test_gated_arm_decisions(res):
    c = res["criteria"]
    assert c["D1_resolved_no_mint"], res["gated"]["minted"]
    assert c["D2_progressing_minted"], res["gated"]["minted"]
    assert c["D3_gated_intractable_no_mint"], res["gated"]["minted"]
    assert "resolved" not in res["gated"]["minted"]
    assert "progressing" in res["gated"]["minted"]
    assert "intractable" not in res["gated"]["minted"]
    # the noisy-TV interest curve decays under the gate, same shape as the
    # original block-202000 proof's G1a
    g = res["gated"]
    assert g["intractable_interest_late"] < 0.5 * max(g["intractable_interest_early"], 1)


def test_falsifier_traps_on_intractable(res):
    c = res["criteria"]
    assert c["D4_falsifier_intractable_minted"], res["naive"]["minted"]
    assert "intractable" in res["naive"]["minted"]
    n = res["naive"]
    # naive (raw-surprise) interest stays pinned high on the noisy topic --
    # the classic ICM/prediction-error trap, reproduced in the DECISION layer
    assert n["intractable_interest_late"] >= 0.8 * n["intractable_interest_early"]


def test_source_audit_no_python_decisions(res):
    c = res["criteria"]
    assert c["D5_no_decision_writes"], res["source_audit_bad_setattr"]
    assert res["source_audit_bad_setattr"] == {}


def test_ensemble_robustness(res):
    ens = res["ensemble"]
    assert ens["n"] == 16
    r = ens["rates"]
    # resolved/progressing/falsifier are robust across every draw
    assert r["D1"] == 1.0
    assert r["D2"] == 1.0
    assert r["D4"] == 1.0
    # the headline noisy-TV-resistance decision holds on the large majority
    # of draws (same per-draw-noise honesty as the original block-202000
    # proof's own 14/16 G1a rate)
    assert r["D3"] >= 0.75


def test_seed_default_off_byte_identical():
    """The new seed is self_load_only (excluded from load_all_seeds) and every
    lp_* rule it depends on is itself inert without an enabled
    HeldCuriosityParams -- so a full boot that never opts in must be
    byte-identical on any node this seed would have touched."""
    seed = json.load(open(os.path.join(ROOT, "seeds", "curiosity_topic_selection.json")))
    assert seed.get("self_load_only") is True

    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    wa = WorldAdapter(seeds=())
    load_all_seeds(wa)
    # authoritative check: no CuriosityHub / AttentionItem exists on a full,
    # default boot that never explicitly opted in (self_load_only skips both
    # this seed and learning_progress_curiosity during the sweep)
    assert list(wa.s.nodes("CuriosityHub")) == []
    assert list(wa.s.nodes("AttentionItem")) == []


def test_integer_native_and_no_new_rust():
    """Every lp_mint_topic_gap where-clause Term is a pre-existing, already-
    integer-native Term (Eq/Not/Gt/Exists/NodesOfType/Attr/Var/Lit) -- no new
    Rust, no new Term, mirroring the original seed's own G4c."""
    import subprocess
    seed = json.load(open(os.path.join(ROOT, "seeds", "curiosity_topic_selection.json")))
    rule = next(r for r in seed["rules"] if r["name"] == "lp_mint_topic_gap")

    def ops(term, acc):
        if isinstance(term, dict):
            if "type" in term:
                acc.add(term["type"])
            for k in ("a", "b", "arg", "cond", "then", "other", "node", "source", "predicate"):
                if k in term:
                    ops(term[k], acc)
            for x in term.get("items", []):
                ops(x, acc)
        return acc
    used = ops(rule["where"], set())
    pre_existing = {"And", "Eq", "Not", "Gt", "Exists", "NodesOfType", "Attr", "Var", "Lit"}
    assert used <= pre_existing, used - pre_existing

    diff = subprocess.run(["git", "diff", "--stat", "HEAD", "--", "runners/dsl/src/"],
                          cwd=ROOT, capture_output=True, text=True)
    assert diff.stdout.strip() == "", diff.stdout

"""test_program_synthesis_migrated — P4-B gates: the generation loop
(propose → build → verify → accept / counterexample / gap) as seed rules
(seeds/program_synthesis.json), with domains/prog_synthesis.py as the
mechanical adapter rim (PROGRAM_SYNTHESIS_PLAN.md §2/§4-P4,
PROGRAM_SYNTHESIS_PREREG.md §6 H4).

Gates:
  1. seed loads via load_seed_manifest with ZERO skipped rules/reflexes;
  2. END-TO-END FIXPOINT (headline): a cue-recognised NL request + 3 example
     rows → exactly ONE accepted Program node; ProgEval of the ACCEPTED
     (reflected-subgraph) IR correct on a HELD-OUT input; provenance shows
     rung 1 (codebook) and nothing deeper;
  3. multi-statement spine: the statement-grain template routes through the
     Hyp/LatEdge lattice (vit_step/vit_backtrace over boarded
     ConstructionBigram trans_logp) — the DECODED order is the corpus order,
     NOT the deliberately-shuffled template order; accepted + held-out;
  4. CEGIS: a more-specific WRONG plan wins first, fails one row →
     CounterExample node minted, plan Excluded, re-propose → accepted on
     attempt 2 with the correct construction;
  5. Occam order: a codebook-covered request NEVER reaches the enumerate
     rung (rung attrs prove it);
  6. honest gap: an unbuildable request → status gapped + SelfConcern
     {kind:'code_write'} in the standing-pipeline node shape, content-deduped
     across an identical second request, NO Program minted;
  7. budget honesty: attempts are integer-bounded by ps_budget; exhaustion
     is an honest status trail (exhausted → gapped), never attempt N+1.
     Arc4-S1 (seed v1.6.0): the propose lane (codebook + retrieval) has
     its OWN separate, integer-bounded budget (ps_propose_attempts/
     ps_propose_budget) and the enumerator draws from a RESERVED,
     untouchable lane (ps_enum_reserve_used/budget) -- a propose-exhausted
     DESCEND_APPLICABLE goal no longer terminally exhausts, it falls
     through to the next rung (PROGRAM_SYNTHESIS_ARC4_S1_NOTES.md);

  8. the SynthEnumerate seam (P4-A): feature-detected; while absent the rung
     files enumerate_unavailable and falls to the gap — the honest current
     state; once the Term lands the same test accepts the live-path
     outcomes without any rule change;
  9. NO-PYTHON-DECISION source audit of domains/prog_synthesis.py (the
     ink-suite pattern).

Run (worktree engine discipline — the P1 note):
    pytest tests/test_program_synthesis_migrated.py --confcutdir=. -q
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs  # noqa: E402

from domains import prog_synthesis as psy  # noqa: E402


def _term_live(term, env) -> bool:
    s = srs.Substrate()
    try:
        s._inner.evaluate(term, env)
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


if not _term_live({"type": "ShapeDecode", "goal": {"type": "Var", "name": "g"},
                   "beam": 1, "max_steps": 2, "cand_k": 1, "field": "",
                   "wild_objects": False}, {"g": [["p", "x"]]}) or \
   not _term_live({"type": "ProgEval",
                   "prog": {"type": "ProgSeq", "stmts": []},
                   "env": None, "oracles": None, "fuel": 5, "field": ""}, {}):
    pytest.skip("ShapeDecode/ProgEval not present in the installed "
                "substrate_rs binary — rebuild runners/dsl. Honest skip.",
                allow_module_level=True)


def boot():
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    psy.ensure_program_synthesis(s, s._inner, ag)
    return s, ag


def run(s, ag, text, examples=(), **kw):
    m = psy.ingest_spec(s, ag, text, examples, **kw)
    psy.pump(s, ag)
    goals = s.in_neighbours(m, "about_message")
    assert len(goals) == 1, "exactly one goal per request message"
    return psy.read_goal(s, goals[0])


def eval_accepted(s, r, env):
    """Held-out check: ProgEval over the accepted Program's REFLECTED
    subgraph (the graph-resident artifact is what executes)."""
    roots = s.neighbours(r["program"], "ir_subgraph")
    assert len(roots) == 1, "accepted Program must point at its reflected IR"
    out = s._inner.evaluate(
        {"type": "ProgEval", "prog": {"type": "Var", "name": "p"},
         "env": {"type": "Var", "name": "e"}, "oracles": None,
         "fuel": 10000, "field": ""},
        {"e": env, "p": roots[0]})
    assert out["trap"] is None and out["halted"] is True, out
    return out["result"]


MAX_REQ = "write a function max_of_two that returns the larger of two numbers"
MAX_ROWS = [({"a": 2, "b": 9}, 9), ({"a": 7, "b": 3}, 7), ({"a": 4, "b": 4}, 4)]


# ---------------------------------------------------------------------------
# 1) seed loads clean
# ---------------------------------------------------------------------------
def test_seed_loads_clean():
    from substrate.seed_loader import manifest_for
    manifest = manifest_for("program_synthesis")
    assert manifest["id"] == "program_synthesis"
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    summary = s._inner.load_seed_manifest(manifest, ag)
    assert summary["rules_skipped"] == []
    assert summary["reflexes_skipped"] == []
    # 27 (P4-B + P6.5) + 11 descent rules (P7-A, seed v1.2.0) + 5 repair
    # rules (P7-B, seed v1.3.0) + 6 descent/repair-widening rules (Arc2-Q4,
    # seed v1.4.0: ps_plan_branch_arm, ps_branch_arm_ready,
    # ps_branch_arm_failed, ps_enum_retry_mark, ps_row_pass_special,
    # ps_row_fail_special) + 5 Arc3-R1 retrieval rules (seed v1.5.0:
    # ps_goal_top, pr_select_candidate, pr_ladder_ready, pr_ladder_accept,
    # pr_ladder_fallthrough — the codebook-side universal-screen rules
    # were FIRST built, measured, and REVERTED, see
    # PROGRAM_SYNTHESIS_ARC3_R12_NOTES.md) + 3 Arc3-R2.5 SCOPED
    # codebook-screen rules (seed v1.5.1: ps_screen_mark, ps_screen_reject,
    # ps_screen_admit — the corrected redo, gated on NOT DESCEND_APPLICABLE
    # so partial-cover fixtures are byte-identical by construction) + 1
    # Arc4-S1 rule (seed v1.6.0: ps_isolate_fallthrough -- the exact
    # logical complement of ps_ce_exhausted's new next-rung guard; no
    # other rule was ADDED, only ps_goal/ps_goal_top/ps_propose/
    # pr_ladder_accept/ps_repair_mark/ps_descend_mark/ps_enumerate_mark/
    # ps_ce_exhausted/ps_exhausted were EDITED in place, see
    # PROGRAM_SYNTHESIS_ARC4_S1_NOTES.md) + 2 Arc4-S2 rules (seed v1.7.0:
    # ps_structural_reject, ps_structural_clear -- VERDICT DISCRIMINATION,
    # PROGRAM_SYNTHESIS_ARC4_S2_NOTES.md; ps_accept was EDITED in place to
    # gate on structural clearance for top-level goals only) + 4 Arc4-S6
    # rules replacing the single ps_structural_reject (seed v1.8.0:
    # ps_structural_reject_exclusion_gap, ps_structural_reject_exclusion_
    # reopen, ps_structural_reject_repair_gap, ps_structural_reject_repair_
    # reopen -- REJECT INFORMS REPAIR: a structural rejection now carries
    # its localization into the standing exclude/reproposal CEGIS lane
    # (never straight to gapped) whenever the rejected candidate's source
    # is NOT 'retrieved_exemplar' -- the one condition S2 measured as an
    # unsafe stall; ps_structural_clear is UNCHANGED,
    # PROGRAM_SYNTHESIS_ARC4_S6_NOTES.md) + 3 Arc5 EXACT-FIRST rules (seed
    # v1.9.0, 2026-08-01: ps_exact_mark / ps_exact_solved / ps_exact_failed
    # -- the shape -> IR rung PROGRAM_SYNTHESIS_ARCH_DIAGNOSIS.md names as
    # missing, Occam-ordered between descent and enumerate; see
    # PROGRAM_SYNTHESIS_ARC5_EXACT_FIRST.md and
    # tests/test_exact_first_migrated.py) + 4 Arc5 MOVES rules (seed
    # v1.10.0, 2026-08-01: ps_move_mark / ps_move_select / ps_move_none /
    # ps_move_fresh_attempt -- orbit augmentation (MOVE A) + intermediate
    # decomposition (MOVE B), selected by WEIGHTED COLLAPSE, Occam-ordered
    # RUNG 2.6 between the exact rung and enumerate (ps_enumerate_mark was
    # also EDITED in place to add the reciprocal mutual-exclusion arm;
    # ps_move_fresh_attempt is the ps_enumerate_fresh_attempt P6.5-stall
    # precedent applied to this rung, closing a live attempt-collision
    # stall found on MBPP task 162); see PROGRAM_SYNTHESIS_ARC5_MOVES.md
    # and tests/test_prog_moves_migrated.py) + 3 Arc6 SEAM D PROPERTY-
    # REFUTATION rules (seed v1.11.0, 2026-08-01: ps_property_clear /
    # ps_property_reject_gap / ps_property_reject_reopen -- comprehend_
    # theorem's prose -> structured property -> grounded -> checkable
    # clause shape transferred to program-shaped content, the D1/D2
    # structural-exclusion pair mirrored for a property refuted by a
    # hand-constructed WITNESS executed through the same ProgEval term
    # every other verdict path uses; ps_accept was EDITED in place a
    # SECOND time to gate additionally on ps_property_reject == 0.0 beside
    # ps_structural_reject == 0.0; see PROGRAM_SYNTHESIS_ARC6_D.md and
    # tests/test_prog_property_migrated.py) -- the pin follows the
    # version bump, the P6.5 precedent
    # (26 → 27 → 38 → 43 → 49 → 54 → 57 → 58 → 60 → 63 → 66 → 70 → 73).
    assert len(manifest["rules"]) == 73


# ---------------------------------------------------------------------------
# 2) THE HEADLINE — end-to-end fixpoint, rung 1
# ---------------------------------------------------------------------------
def test_end_to_end_request_to_accepted_program():
    s, ag = boot()
    r = run(s, ag, MAX_REQ, MAX_ROWS)
    assert r["status"] == "accepted"
    assert r["construction"] == "max_of_two"
    assert r["attempts"] == 1.0
    # exactly ONE accepted Program node, carrying the Program{name, program}
    # convention + provenance.
    progs = s.nodes("Program")
    assert len(progs) == 1
    pa = s.node(progs[0])["attrs"]
    assert pa["name"] == "max_of_two"
    assert pa["provenance"] == "program_synthesis"
    assert pa["construction"] == "max_of_two"
    ir = json.loads(pa["program"])
    assert ir["type"] == "ProgSeq"
    # structural verdict recorded: reflect round-trip byte-stable.
    assert r["reflect_ok"] == 1.0
    # held-out input (never in the spec rows), via the reflected subgraph.
    assert eval_accepted(s, r, {"a": 11, "b": 5}) == 11
    assert eval_accepted(s, r, {"a": -3, "b": 4}) == 4
    # provenance: rung 1 only.
    assert r["rungs"]["codebook"] == 1.0
    assert r["rungs"]["lattice"] is None
    assert r["rungs"]["enumerate"] is None
    assert r["counterexamples"] == [] and r["excluded"] == []


def test_second_identical_request_mints_a_second_goal_not_a_second_message_goal():
    """Mint-once is per MESSAGE (ps_goal_minted): re-running the fixpoint
    never re-mints; a fresh identical request is its own goal."""
    s, ag = boot()
    r1 = run(s, ag, MAX_REQ, MAX_ROWS)
    psy.pump(s, ag)     # idle fixpoint: nothing re-fires
    assert len(s.nodes("Program")) == 1
    r2 = run(s, ag, MAX_REQ, MAX_ROWS)
    assert r2["status"] == "accepted"
    assert len(s.nodes("Program")) == 2
    assert r1["goal"] != r2["goal"]


# ---------------------------------------------------------------------------
# 3) multi-statement spine — the lattice rung
# ---------------------------------------------------------------------------
SUM_REQ = "write a function sum_of_list that returns the tally of a list of numbers"
SUM_ROWS = [({"items": [1, 2, 3, 4]}, 10), ({"items": [5]}, 5), ({"items": []}, 0)]


def test_spine_request_uses_lattice_and_accepts():
    s, ag = boot()
    r = run(s, ag, SUM_REQ, SUM_ROWS)
    assert r["status"] == "accepted"
    assert r["construction"] == "sum_of_list_spine"
    assert r["rungs"]["lattice"] == 1.0, "the lattice rung must be recorded"
    # THE POINT: the template ships its parts DELIBERATELY SHUFFLED
    # (return first — see the seed); the accepted order is the CORPUS order
    # the boarded bigrams decided, via vit_step/vit_backtrace.
    assert r["spine_labels"] == ["ProgAssignVar", "ProgForEach", "ProgReturn"]
    # and the emitted IR body follows the DECODED order, not the template's.
    body = [st["type"] for st in r["ir"]["stmts"]
            if st["type"] != "ProgDefFnParam"]
    assert body == ["ProgAssignVar", "ProgForEach", "ProgReturn"]
    # held-out list.
    assert eval_accepted(s, r, {"items": [2, 4, 6, 8, 10]}) == 30


def test_lattice_mechanism_hyps_edges_and_bigram_scores():
    """The lattice EXISTS as Hyp/LatEdge graph data decoded by the unchanged
    viterbi seed rules, with trans_logp read from the boarded bigrams —
    inspected directly via the keep_substrate hook."""
    s, ag = boot()
    tables = psy._bigram_tables(s)
    assert tables[0], "ConstructionBigram rows must be boarded at ensure time"
    decoded, lat_sub = psy._decode_order(
        ["ProgReturn", "ProgForEach", "ProgAssignVar"], tables,
        keep_substrate=True)
    assert decoded == ["ProgAssignVar", "ProgForEach", "ProgReturn"]
    hyps = lat_sub.nodes("Hyp")
    edges = lat_sub.nodes("LatEdge")
    assert len(hyps) == 10                    # 3 pos × 3 labels + END
    assert len(edges) == 15                   # 2×(3×2) inter-pos + 3 to END
    on_path = [h for h in hyps
               if lat_sub.node(h)["attrs"].get("on_path") == 1.0]
    assert len(on_path) == 4                  # the 3 spine hyps + END
    scored = {lat_sub.node(e)["attrs"].get("trans_logp") for e in edges}
    # the boarded corpus scores appear on the lattice edges verbatim.
    assert tables[0][("ProgAssignVar", "ProgForEach")] in scored
    assert tables[0][("ProgForEach", "ProgReturn")] in scored


def test_boarded_bigrams_match_the_artifact_head_aggregation():
    """P3 residual 4 consumed: the boarded rows are the artifact's bigram
    table aggregated to statement-head grain with the SAME add-1 formula."""
    import math
    s, ag = boot()
    art = json.load(open(os.path.join(ROOT, "results",
                                      "prog_construction_scan.json")))
    head_of = {row["name"]: row["signature"][0][1] for row in art["codebook"]}
    counts, prev_tot = {}, {}
    for row in art["bigrams"]:
        p = row["prev"] if row["prev"] in ("<s>", "</s>") else head_of[row["prev"]]
        nx = row["next"] if row["next"] in ("<s>", "</s>") else head_of[row["next"]]
        counts[(p, nx)] = counts.get((p, nx), 0) + row["count"]
        prev_tot[p] = prev_tot.get(p, 0) + row["count"]
    vocab = {n for (_, n) in counts} | {p for (p, _) in counts if p != "<s>"}
    boarded = {}
    for n in s.nodes("ConstructionBigram"):
        at = s.node(n)["attrs"]
        boarded[(at["prev"], at["next"])] = at
    assert set(boarded) == set(counts)
    for k, c in counts.items():
        at = boarded[k]
        assert at["count"] == c
        assert at["prev_total"] == prev_tot[k[0]]
        assert abs(at["trans_logp"]
                   - math.log((c + 1) / (prev_tot[k[0]] + len(vocab)))) < 1e-12
    # the registered sanity ordering: assign→foreach beats assign→return,
    # and return→</s> is near-certain.
    lg = {k: boarded[k]["trans_logp"] for k in boarded}
    assert lg[("ProgAssignVar", "ProgForEach")] > lg[("ProgAssignVar", "ProgReturn")]
    assert lg[("ProgReturn", "</s>")] > -0.01


# ---------------------------------------------------------------------------
# 4) CEGIS — counterexample → exclusion → accepted on a later attempt
# ---------------------------------------------------------------------------
def _teach_decoy(s, name, triggers, term, args, *, branch=False):
    """Mechanical install of a write shape (the ensure_write_codebook /
    teach-by-example install path, inlined for the gate).

    `branch` (Arc3-R2.5): wrap `term` as `IfThenElse(Lit(True), term,
    term)` — a STRUCTURALLY branch-shaped construction that always
    evaluates the SAME wrong `term` regardless of the (constant-true)
    condition, i.e. byte-identical WRONG VALUES to the unwrapped form —
    AND stamp `tmpl_branch: 1.0` directly (the SAME "set the normalised
    attr straight, bypassing the once-only `_normalise_*` pass" idiom this
    helper already uses for `trigger_tokens`: `_normalise_fold_marks` only
    ever runs inside `ensure_program_synthesis`, which `boot()` calls
    exactly once, BEFORE any test-taught decoy exists, so a decoy minted
    afterwards would never get normalised otherwise). Used only by
    fixtures that need to stay on the DESCEND_APPLICABLE side of the new
    codebook screen (`seeds/program_synthesis.json` v1.5.1,
    `ps_screen_mark`) so a decoy keeps consuming a REAL `ps_attempts` unit
    via the classic propose→exclude→reproposal path — the exact mechanism
    those specific tests exist to exercise — rather than being killed for
    free before ps_propose ever sees it (correct behaviour, but a
    DIFFERENT test than the one originally authored; see the two call
    sites below for why each opts in)."""
    attrs: dict = {
        "name": name, "kind": "code_write_construction",
        "signature": json.dumps([[t] for t in triggers]),
        "trigger_tokens": list(triggers),
    }
    if branch:
        term = {"type": "IfThenElse", "cond": {"type": "Lit", "value": True},
                "then": term, "other": term}
        attrs.update(tmpl_fold=0.0, tmpl_scalar_fold=0.0, tmpl_branch=1.0)
    attrs["ground_template"] = json.dumps(
        {"desc": "gate decoy", "term": term, "args": list(args),
         "mode": "code_write"})
    s.add_node("ShapeSignature", attrs)


def test_cegis_counterexample_then_accept_on_second_attempt():
    s, ag = boot()
    # a MORE SPECIFIC (2-trigger) decoy whose recipe is WRONG (returns b):
    # proposal ranks by specificity, so the decoy wins attempt 1.
    _teach_decoy(s, "larger_of_pair_decoy", ["LARGER", "PAIR"],
                 {"type": "Var", "name": "b"}, ["a", "b"])
    r = run(s, ag, "write a function max_of_two that returns the larger of the pair",
            [({"a": 9, "b": 2}, 9), ({"a": 2, "b": 7}, 7)])
    assert r["status"] == "accepted"
    assert r["attempts"] == 2.0, "accepted on the SECOND attempt"
    assert r["construction"] == "max_of_two"
    # the failing row became a CounterExample NODE bound to the goal.
    assert len(r["counterexamples"]) == 1
    ce = r["counterexamples"][0]
    assert ce["construction"] == "larger_of_pair_decoy"
    assert ce["attempt"] == 1.0
    assert ce["expected"] == 9 and ce["got"] == 2
    assert json.loads(ce["inputs_json"]) == {"a": 9, "b": 2}
    # the failed plan signature is excluded from re-proposal.
    assert r["excluded"] == ["larger_of_pair_decoy"]
    assert eval_accepted(s, r, {"a": 1, "b": 8}) == 8
    assert len(s.nodes("Program")) == 1


# ---------------------------------------------------------------------------
# 5) Occam order — covered requests never reach enumerate
# ---------------------------------------------------------------------------
def test_covered_request_never_reaches_enumerate():
    s, ag = boot()
    r = run(s, ag, MAX_REQ, MAX_ROWS)
    assert r["status"] == "accepted"
    assert r["rungs"]["enumerate"] is None, \
        "rung-3 marker must never appear on a codebook-covered goal"
    assert r["enumerate_outcome"] is None
    assert r["gap_reason"] is None
    r2 = run(s, ag, SUM_REQ, SUM_ROWS)
    assert r2["rungs"]["enumerate"] is None


# ---------------------------------------------------------------------------
# 6) honest gap — unbuildable request files a deduped SelfConcern
# ---------------------------------------------------------------------------
GAP_REQ = "write a function fourier_transform that returns the spectrum of a signal"


def test_unbuildable_request_gaps_with_deduped_selfconcern():
    s, ag = boot()
    r = run(s, ag, GAP_REQ)          # no examples, no held shape
    assert r["status"] == "gapped"
    assert r["gap_reason"] == "no_shape"
    assert r["program"] is None
    assert s.nodes("Program") == []
    scs = s.nodes("SelfConcern")
    assert len(scs) == 1
    at = s.node(scs[0])["attrs"]
    # the EXACT node shape the standing code_write gap pipeline consumes.
    assert at["kind"] == "code_write"
    assert at["source"] == "implicit"
    assert at["status"] == "noted"
    assert at["content"] == GAP_REQ
    # dedup: the identical request again → gapped again, ONE concern total.
    r2 = run(s, ag, GAP_REQ)
    assert r2["status"] == "gapped"
    assert len(s.nodes("SelfConcern")) == 1
    assert s.nodes("Program") == []


# ---------------------------------------------------------------------------
# 7) budget honesty
# ---------------------------------------------------------------------------
def test_budget_bounded_integer_attempts_then_isolated_rung_takeover():
    """Arc4-S1 BUDGET ISOLATION regression gate, over the SAME fixture
    Arc3-R2.5 authored for the CLASSIC propose->exclude->reproposal path
    (four wrong decoys, strictly decreasing specificity; `branch=True`
    keeps them DESCEND_APPLICABLE so the codebook screen, seed v1.5.1's
    ps_screen_mark, never engages here -- the screen's own decoy-kill
    behaviour on a NON-descend-applicable request is gated separately in
    tests/test_screen_codebook_migrated.py). Arc4-S1 correctly changes
    this fixture's own TERMINAL outcome: this is exactly
    PROGRAM_SYNTHESIS_ARC4_S0A_NOTES.md's class (a) shape (7/17 ids) -- a
    DESCEND_APPLICABLE goal whose propose lane (codebook) exhausts its
    OWN separate budget before descent ever got a look. Pre-S1 this
    fixture terminally exhausted (gapped:exhausted) with the descend rung
    NEVER MARKED even though the codebook trigger-covers the request and
    the depth budget allows descent -- the exact bug S1 fixes (see
    PROGRAM_SYNTHESIS_ARC4_S1_NOTES.md). Post-S1: the propose lane's own
    integer honesty is UNCHANGED (still exactly 3 real attempts, decoy_3
    is NEVER tried for real, `excluded` is unchanged) but the goal is NOT
    terminally exhausted -- it falls through to descent
    (rungs['descend']==1.0), which derives a hole from decoy_0's own
    branch structure and (this fixture's single revealed row being
    consistent with the identity relation) solves it, so the goal
    ACCEPTS. Isolation, not screening: no candidate's correctness was
    judged to reach this point -- only which budget counter gated entry
    into the next rung changed."""
    s, ag = boot()
    trigs = [["QUUX", "ALPHA", "BETA", "GAMMA"],
             ["QUUX", "ALPHA", "BETA"],
             ["QUUX", "ALPHA"],
             ["QUUX"]]
    for i, t in enumerate(trigs):
        _teach_decoy(s, "decoy_%d" % i, t, {"type": "Lit", "value": 0}, ["a"],
                     branch=True)
    r = run(s, ag, "write a function quux_fn that returns the quux alpha "
                   "beta gamma of a number", [({"a": 5}, 5)])
    # propose-lane budget honesty: integer, hit exactly, never exceeded --
    # UNCHANGED by S1 (S1 only changes what happens AFTER the lane closes).
    assert r["budget"] == 3.0 and float(r["budget"]).is_integer()
    assert r["attempts"] == 3.0
    # one counterexample per attempt, in specificity order; decoy_3 untried.
    assert [ce["construction"] for ce in
            sorted(r["counterexamples"], key=lambda c: c["attempt"])] == \
        ["decoy_0", "decoy_1", "decoy_2"]
    assert r["excluded"] == ["decoy_0", "decoy_1", "decoy_2"]
    # Arc4-S1 headline: the descend rung is now MARKED -- pre-S1 it never
    # was, for this exact fixture -- so the propose-exhausted goal was NOT
    # terminally exhausted; it accepted via the isolated next rung.
    assert r["rungs"]["descend"] == 1.0
    assert r["gap_reason"] is None
    assert r["status"] == "accepted"
    # the hole's own sub-goal mints its own Program; the OUTER goal exactly
    # one (the test_prog_descent_migrated.py fold-up-accept precedent).
    assert len(s.neighbours(r["goal"], "accepted_program")) == 1
    assert s.nodes("SelfConcern") == []


# ---------------------------------------------------------------------------
# 8) the SynthEnumerate seam (P4-A)
# ---------------------------------------------------------------------------
def test_enumerate_seam_state_is_honest():
    """Codebook exhausted + examples present → the rung 3 marker fires.
    While P4-A's Term is absent the outcome is 'unavailable' and the goal
    gaps with that reason; once the Term lands, the SAME rules accept the
    live-path outcomes (ok → verified pipeline, failed → gap) — zero rule
    changes, only this assertion widens."""
    s, ag = boot()
    live = psy.synth_enumerate_live(s)
    r = run(s, ag, "write a function double_it that returns twice the "
                   "widget of a number", [({"a": 3}, 6), ({"a": 5}, 10)])
    assert r["rungs"]["enumerate"] == 1.0, "rung 3 must be marked"
    if not live:
        assert r["enumerate_outcome"] == "unavailable"
        assert r["status"] == "gapped"
        assert r["gap_reason"] == "enumerate_unavailable"
        assert s.nodes("Program") == []
    else:
        # the Term landed: honest outcomes only — either it found a fitting
        # term (then the NORMAL verify/accept pipeline judged it) or it
        # honestly failed and the goal gapped.
        assert r["enumerate_outcome"] in ("ok", "failed")
        if r["enumerate_outcome"] == "ok":
            assert r["status"] in ("accepted", "gapped", "counterexample")
            if r["status"] == "accepted":
                assert eval_accepted(s, r, {"a": 7}) == 14
        else:
            assert r["status"] == "gapped"


def test_no_examples_no_enumerate():
    """SynthEnumerate is spec-driven: an example-free uncovered request
    must go straight to the gap, never to rung 3."""
    s, ag = boot()
    r = run(s, ag, GAP_REQ)
    assert r["rungs"]["enumerate"] is None
    assert r["gap_reason"] == "no_shape"


def test_stall_regression_decoy_then_enumerate_reaches_terminal():
    """P6.5 REGRESSION GATE — the powered battery's `stalled:evaluated`
    defect (PROGRAM_SYNTHESIS_P6_BATTERY.md §2.1), reproduced exactly:
    a codebook decoy consumes attempt 1 (CEGIS: row fail → CounterExample →
    Excluded) and the enumerate rung then runs. Under the pre-fix seed the
    enumerated IR was re-evaluated at the SAME attempt number the decoy
    consumed, so ps_row_pass/ps_row_fail's verdict_attempt < eval_attempt
    guard never re-armed and the goal PARKED on the non-terminal
    'evaluated' status (no accept, no gap, no SelfConcern). With
    ps_enumerate_fresh_attempt (seed v1.1.0) the rung's evaluation gets a
    FRESH attempt number, the verdict re-arms, and the goal reaches a
    TERMINAL status — accepted or gapped, never parked.

    Arc3-R2.5 note: the NEW codebook screen (seed v1.5.1, `ps_screen_mark`)
    is gated on `NO_SLACK` (the goal's INITIAL trigger-matching codebook
    pool, frozen at mint, is NOT smaller than its full attempt budget) —
    this fixture has exactly ONE trigger-matching decoy against a budget
    of 3 (2 attempts of slack already exist), so `Gte(1, 3)` is FALSE and
    the screen never engages here: this test's fixture stays on the
    classic, byte-identical propose→exclude→reproposal path it was
    authored for, unchanged by Arc3-R2.5 (verified live; see
    `test_budget_bounded_integer_attempts_and_honest_exhaustion` for a
    fixture that DOES have a large enough decoy pool to engage the
    screen, and `tests/test_screen_codebook_migrated.py` for the dedicated
    decoy-tax-kill gate).

    Counterfactual (verified by a stash-free seed-body flip during P6.5):
    on the v1.0.0 rule body this test fails with status == 'evaluated'."""
    s, ag = boot()
    if not psy.synth_enumerate_live(s):
        pytest.skip("SynthEnumerate not in the installed substrate_rs — "
                    "the stall shape needs the live rung-3 build. Honest "
                    "skip.")
    # the decoy: trigger-matches the request, recipe is WRONG (returns 0).
    _teach_decoy(s, "frob_decoy", ["FROB"], {"type": "Lit", "value": 0},
                 ["a"])
    r = run(s, ag, "write a function double_it that returns twice the frob "
                   "of a number", [({"a": 3}, 6), ({"a": 5}, 10)])
    # the stall PRECONDITIONS all happened: decoy attempt consumed,
    # CEGIS artifacts minted, rung 3 ran and found a candidate.
    assert r["excluded"] == ["frob_decoy"]
    assert len(r["counterexamples"]) >= 1
    assert all(ce["construction"] == "frob_decoy" and ce["attempt"] == 1.0
               for ce in r["counterexamples"])
    assert r["rungs"]["enumerate"] == 1.0
    assert r["enumerate_outcome"] == "ok"
    # THE GATE: terminal, never the non-terminal park.
    assert r["status"] != "evaluated", \
        "the P6 stall: goal parked on non-terminal 'evaluated'"
    assert r["status"] in ("accepted", "gapped"), r["status"]
    # and on this solvable spec the terminal is an accept, on a FRESH
    # attempt number (decoy = 1, enumerate = 2), inside the budget.
    assert r["status"] == "accepted"
    assert r["attempts"] == 2.0 and float(r["attempts"]).is_integer()
    assert r["attempts"] <= r["budget"]
    assert eval_accepted(s, r, {"a": 7}) == 14
    assert len(s.nodes("Program")) == 1
    # the non-colliding path is byte-unchanged: the SAME uncovered request
    # WITHOUT a decoy still enumerates at attempt 0 (no bump — the fix
    # keys on the collision, not on the rung).
    s2, ag2 = boot()
    r2 = run(s2, ag2, "write a function double_it that returns twice the "
                      "frob of a number", [({"a": 3}, 6), ({"a": 5}, 10)])
    assert r2["rungs"]["enumerate"] == 1.0
    assert r2["attempts"] == 0.0


# ---------------------------------------------------------------------------
# 9) NO-PYTHON-DECISION source audit (the ink-suite pattern)
# ---------------------------------------------------------------------------
_BANNED_CALL_RE = re.compile(
    r"\.arg(?:min|max)\(|(?<!\w)np\.arg(?:min|max)\b", re.IGNORECASE)
_SORT_KEY_RE = re.compile(r"\.sort\(\s*key\s*=\s*lambda\s+\w+\s*:\s*(.+?)\)")
_MINMAX_KEY_RE = re.compile(r"(?<!\w)(?:min|max)\(.*?key\s*=", re.IGNORECASE)
_SCORE_KEYWORDS = ("score", "emission", "vscore", "fit", "dist", "count",
                   "covered", "vote", "logp")
# ALLOWLIST: ordering already-decided data by POSITION (the committed
# viterbi_partition precedent's own read-back sort) is not a decision.
_ALLOWED_SORT_KEYS = {"x[0]", "x[1]", "c[\"attempt\"]"}


def test_prog_synthesis_no_python_decisions():
    """domains/prog_synthesis.py contains no argmin/argmax/sort-on-score
    Python decisions: every choice on the synthesis path is a seed rule
    (ps_*), a held Term (Argmax/ShapeDecode/ProgEval), or the unchanged
    vit_step/vit_backtrace decode. Facts in, facts out."""
    src = Path(psy.__file__).read_text()
    assert not _BANNED_CALL_RE.search(src)
    assert not _MINMAX_KEY_RE.search(src)
    violations = []
    for m in _SORT_KEY_RE.finditer(src):
        key_expr = m.group(1).strip()
        if key_expr in _ALLOWED_SORT_KEYS:
            continue
        if any(kw in key_expr.lower() for kw in _SCORE_KEYWORDS):
            violations.append(key_expr)
    assert not violations, violations


def test_descend_rung_never_touches_the_p4_shapes():
    """P7-A additive guard: the descent rung (seed v1.2.0) is scoped to
    partial-cover LIST-input specs — every P4 gate shape (covered rung-1,
    scalar decoy→enumerate, no-shape gap) carries NO descend marker, so
    the paths pinned above are byte-compatible by guard, not by luck."""
    s, ag = boot()
    r = run(s, ag, MAX_REQ, MAX_ROWS)                       # covered
    assert r["rungs"]["descend"] is None
    s2, ag2 = boot()
    r2 = run(s2, ag2, "write a function double_it that returns twice the "
                      "widget of a number", [({"a": 3}, 6), ({"a": 5}, 10)])
    assert r2["rungs"]["descend"] is None                   # scalar rows
    s3, ag3 = boot()
    r3 = run(s3, ag3, GAP_REQ)                              # no examples
    assert r3["rungs"]["descend"] is None


def test_repair_lane_never_touches_the_p4_shapes():
    """P7-B additive guard: the repair lane (seed v1.3.0) is gated on a
    ce_pending row an adapter verb must ingest — no P4/P6.5 shape ever
    produces one, so every path pinned above is byte-compatible by guard,
    not by luck: repair counters stay at their minted zeros, no ExcludedSub
    node exists, no Program is ever marked refuted."""
    s, ag = boot()
    for req, rows in ((MAX_REQ, MAX_ROWS), (SUM_REQ, SUM_ROWS), (GAP_REQ, ())):
        run(s, ag, req, rows)
    for g in s.nodes("Goal"):
        at = s.node(g)["attrs"]
        if at.get("kind") != "synth_program":
            continue
        assert at.get("ps_repair_seq") == 0.0
        assert at.get("ps_repair_attempts") == 0.0
        assert at.get("ps_trace_seq") == -1.0
        assert at.get("status") in ("accepted", "gapped")
    assert s.nodes("ExcludedSub") == []
    assert all(s.node(p)["attrs"].get("refuted") is None
               for p in s.nodes("Program"))


def test_write_request_verdict_is_the_existing_cue_machinery():
    """The goal-mint gate reads the EXISTING sanctioned classifier's verdict
    (recorded as a Message fact): prose that merely mentions functions does
    NOT mint a synth_program goal."""
    s, ag = boot()
    m = psy.ingest_spec(s, ag,
                        "functions can make a program smaller by eliminating "
                        "repetitive code", ())
    psy.pump(s, ag)
    assert s.node(m)["attrs"].get("ps_write_request") == 0.0
    assert s.in_neighbours(m, "about_message") == []

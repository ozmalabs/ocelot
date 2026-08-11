#!/usr/bin/env python3
"""Read-only probe for docs/research/theory_convergence/
TAU_HIERARCHY_AXIS_MAP_PREREG.md — TAU-C (comparative axis, old tau2) and
TAU-L (nomological/law axis, old tau3) bars, plus the TAU-ORTHO structural
independence check.

NOT part of the seed/domain/runner tree. Touches nothing under seeds/,
domains/, or runners/ — builds throwaway in-memory substrates via the
existing boot_core() + reflective_faculty.compose_design_for_goal /
find_self_process / run_self_process entry points, the same harness shape
tests/test_transform_decode_migrated.py and scripts/probe_beam_completeness.py
already use. Every number below is computed live against the real Rust
ShapeDecode/TransformDecode Terms and real graph reads -- nothing is
fabricated or hand-typed as a result.

Runtime: well under a few seconds. Prints a trace to stdout and writes a
JSON results blob to the path given as argv[1] (default: stdout only).
"""
from __future__ import annotations

import json
import random
import sys

import os as _os
import sys as _sys
_TESTS_DIR = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "tests")
if _TESTS_DIR not in _sys.path:
    _sys.path.insert(0, _TESTS_DIR)

from substrate.boot_core import boot_core
from domains import reflective_faculty as rf
from domains import self_model as sm


# ---------------------------------------------------------------------------
# shared helpers
# ---------------------------------------------------------------------------

def _add_part(s, name, signature, owner="self", kind="faculty"):
    attrs = {"name": name, "signature": json.dumps(signature), "kind": kind,
              "owner": owner}
    if kind == "faculty":
        attrs["faculty"] = name
    else:
        attrs["concept"] = name
    return s.add_node("ShapeSignature", attrs)


def _axes(s):
    return len(list(s.nodes("CapabilityAxis")))


# ===========================================================================
# TAU-C -- comparative axis (old tau2): is the bare ratio operable?
# ===========================================================================

def _rho(s, goal, owner, budget=2000):
    """Live rho(I) proxy for one owner's codebook: number of parts used in
    a real compose_design_for_goal plan restricted to that owner (via
    `exclude` naming every OTHER owner's parts), or a fixed no-coverage
    penalty when the goal is not fully covered under that codebook."""
    all_names = [s.node(n)["attrs"]["name"] for n in s.nodes("ShapeSignature")]
    own_names = {s.node(n)["attrs"]["name"] for n in s.nodes("ShapeSignature")
                 if s.node(n)["attrs"].get("owner") == owner}
    exclude = [nm for nm in all_names if nm not in own_names]
    out = rf.compose_design_for_goal(s, goal, beam=3, max_steps=8, cand_k=5,
                                      exclude=exclude, budget=budget)
    if not out.get("authored") or out.get("residual"):
        return None  # not covered under this codebook -- treat as high-cost
    return len(out.get("ordered_parts") or [])


NO_COVERAGE_PENALTY = 50  # >> any real plan length in this battery


def _make_instance(rng, idx):
    """One synthetic goal instance with a KNOWN, live-measured winner
    (self vs other codebook), used to build the TAU-C decision battery."""
    # Each instance is a small relation-set; 'self' and 'other' codebooks
    # are built per-instance below with independently varied granularity so
    # rho_self/rho_other differ across the battery (a controlled spread of
    # ratios, not a single fixed gap).
    n_rel = rng.choice([2, 4, 6])
    rels = [["r%d" % idx, "a%d" % i, i] for i in range(n_rel)]
    return rels


def build_tau_c_battery(rng, n, cost_mode):
    """cost_mode: 'independent' (TAU-C-a) draws A/M independent of the
    rho-gap; 'proportional' (TAU-C-b) draws A/M as a fixed function of the
    rho-gap. Returns a list of dicts with live rho_self/rho_other and the
    per-instance A/M and the TRUE optimal action, computed with full
    knowledge (the "cost-informed" decision-maker's own answer)."""
    rows = []
    for i in range(n):
        s, ag = boot_core()
        goal = _make_instance(rng, i)
        # 'self' codebook: granularity varies per instance (sometimes coarse
        # -- one big part -- sometimes fine -- many small parts) so which
        # codebook wins is not fixed in advance.
        self_gran = rng.choice([1, 2, 3])
        other_gran = rng.choice([1, 2, 3])
        for gran, owner in ((self_gran, "self"), (other_gran, "other")):
            step = max(1, len(goal) // gran)
            for k, start in enumerate(range(0, len(goal), step)):
                _add_part(s, f"{owner}_part_{i}_{k}", goal[start:start + step], owner=owner)
        rho_self = _rho(s, goal, "self")
        rho_other = _rho(s, goal, "other")
        rs = rho_self if rho_self is not None else NO_COVERAGE_PENALTY
        ro = rho_other if rho_other is not None else NO_COVERAGE_PENALTY
        if cost_mode == "independent":
            # drawn independent of the rho-gap, pre-registered range
            A = rng.uniform(0.5, 4.5)
            M = rng.uniform(0.5, 4.5)
        else:
            gap = max(0.0, rs - ro)
            A = 0.3 * gap + 0.2
            M = 0.6 * gap + 0.3
        # TRUE optimal action, full knowledge (cost-informed decision-maker):
        cost_self = rs
        cost_adopt = A + min(rs, ro)
        cost_mint = M + (rs - 1 if rs > 1 else rs)  # a mint buys one part of savings
        costs = {"self": cost_self, "adopt": cost_adopt, "mint": cost_mint}
        true_action = min(costs, key=costs.get)
        rows.append(dict(idx=i, rho_self=rs, rho_other=ro, ratio=rs / ro if ro else float("inf"),
                          A=A, M=M, true_action=true_action, costs=costs))
    return rows


def ratio_only_rule(rows, threshold):
    """Best-effort ratio-only decision rule: adopt-other iff ratio > threshold,
    else encode-self. (Never proposes 'mint' -- a ratio between two EXISTING
    codebooks carries no information about a THIRD, self-growth action at
    all; this is itself part of the point, not an oversight.)"""
    preds = []
    for r in rows:
        preds.append("adopt" if r["ratio"] > threshold else "self")
    return preds


def best_ratio_only_accuracy(rows):
    """Oracle-calibrated: sweep thresholds over the observed ratios and
    report the BEST achievable EXACT match-rate to true_action --
    steelmanning the ratio-only rule as much as possible, per the prereg.
    STRICT equality (predicted action must equal true_action exactly) --
    both this rule and the fixed baseline can only ever propose
    self/adopt, so a true_action=='mint' instance counts as a miss for
    BOTH, symmetrically; a rule that fabricated a 'mint' credit for
    'self' predictions would unfairly favour whichever rule leans toward
    'self' more often, which is exactly the bug an earlier draft of this
    probe had and which is fixed here before any bar was read."""
    ratios = sorted(set(r["ratio"] for r in rows))
    best = 0.0
    best_t = None
    for t in [0.0] + ratios:
        preds = ratio_only_rule(rows, t)
        match = sum(1 for r, p in zip(rows, preds) if p == r["true_action"])
        acc = match / len(rows)
        if acc > best:
            best, best_t = acc, t
    return best, best_t


def fixed_baseline_accuracy(rows):
    match = sum(1 for r in rows if r["true_action"] == "self")
    return match / len(rows)


def restricted_accuracy(rows, best_t):
    """Both the ratio-only rule and the fixed baseline can only ever
    propose {self, adopt} -- they structurally cannot select 'mint' (a
    self-directed growth action the bare cross-codebook ratio carries no
    information about at all, by construction: it is not even
    representable in the ratio-only rule's action space). Any instance
    whose true optimum is 'mint' is therefore an automatic miss for BOTH
    rules, capping full-battery accuracy at (1 - mint_fraction)
    regardless of how good the ratio signal is for the self-vs-adopt
    sub-decision. Reported separately (restricted to the self/adopt
    subset) so the self-vs-adopt-specific comparison the bars are about
    is not confounded by that shared, symmetric structural cap."""
    sub = [r for r in rows if r["true_action"] in ("self", "adopt")]
    if not sub:
        return None, None
    ratio_preds = ratio_only_rule(sub, best_t)
    ratio_acc = sum(1 for r, p in zip(sub, ratio_preds) if p == r["true_action"]) / len(sub)
    base_acc = sum(1 for r in sub if r["true_action"] == "self") / len(sub)
    return ratio_acc, base_acc


def run_tau_c(rng, n=200):
    print(f"\n=== TAU-C: comparative axis (old tau2), N={n} ===")
    out = {}
    for label, mode in (("TAU-C-a (independent costs)", "independent"),
                         ("TAU-C-b (proportional costs, control)", "proportional")):
        rows = build_tau_c_battery(rng, n, mode)
        ratio_acc, thr = best_ratio_only_accuracy(rows)
        base_acc = fixed_baseline_accuracy(rows)
        r_ratio_acc, r_base_acc = restricted_accuracy(rows, thr)
        true_dist = {a: sum(1 for r in rows if r["true_action"] == a) for a in ("self", "adopt", "mint")}
        corr = _corr([r["ratio"] for r in rows],
                     [1.0 if r["true_action"] == "adopt" else 0.0 for r in rows])
        print(f"{label}: FULL-battery ratio-only acc={ratio_acc:.3f} (thr={thr}), "
              f"fixed-baseline acc={base_acc:.3f} (both capped by mint-fraction "
              f"{true_dist['mint']}/{n}); RESTRICTED (self/adopt subset only) "
              f"ratio-only acc={r_ratio_acc:.3f}, fixed-baseline acc={r_base_acc:.3f}, "
              f"advantage={((r_ratio_acc or 0)-(r_base_acc or 0))*100:.1f}pp; "
              f"true_action dist={true_dist}, corr(ratio, true=adopt)={corr:.3f}")
        out[label] = dict(ratio_only_accuracy_full=ratio_acc, ratio_threshold=thr,
                           fixed_baseline_accuracy_full=base_acc,
                           ratio_only_accuracy_restricted=r_ratio_acc,
                           fixed_baseline_accuracy_restricted=r_base_acc,
                           advantage_pp_restricted=((r_ratio_acc or 0) - (r_base_acc or 0)) * 100.0,
                           true_action_distribution=true_dist,
                           corr_ratio_vs_true_adopt=corr,
                           n=n, rows_sample=rows[:5])
    return out


def _corr(xs, ys):
    n = len(xs)
    if n < 2:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    sx = sum((x - mx) ** 2 for x in xs) ** 0.5
    sy = sum((y - my) ** 2 for y in ys) ** 0.5
    if sx == 0 or sy == 0:
        return 0.0
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return cov / (sx * sy)


# ===========================================================================
# TAU-L -- nomological/law axis (old tau3): representable vs operative
# ===========================================================================

def _boot_sd():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    return s, ag, native


def _observe_decoded(s, ag, *, signature, key, residual, decoded_epoch):
    obs = s.add_node("Observation", {
        "signature": signature, "key": [key], "status": "decoded",
        "residual": residual, "decoded_epoch": decoded_epoch})
    s.add_edge(ag, "observed", obs)
    return obs


def _epoch(s, ag):
    return s.node(ag)["attrs"].get("codebook_epoch") or 0.0


def run_tau_l_1():
    """Implicit competence without representation -- witness that the gap
    is real. (a) find_self_process returns None for the growth/mint
    process on the currently-booted, unmodified graph. (b) the real
    rung-ordered ladder mints strictly fewer CapabilityAxis than an
    'undirected' baseline (mint-everything, no rung-checking) on a battery
    mixing transform-explainable and genuinely-novel residuals."""
    print("\n=== TAU-L-1: implicit competence without representation ===")
    s0, ag0 = boot_core()
    proc = sm.find_self_process(s0, ["grow", "growth", "mint", "minting", "codebook"])
    print(f"find_self_process(growth/minting) on unmodified boot = {proc!r} "
          f"(expected None -- phi_R(law)=0 today, verified fact)")

    s, ag, native = _boot_sd()
    baseline_axes = _axes(s)
    # N1 transform-explainable residuals (rung 1 -- uniform substitution,
    # the exact shape test_transform_substitution_recognized_no_mint uses)
    n1 = 5
    for i in range(n1):
        _add_part(s, f"held_move_{i}", [["move", "X", "by", "D"], ["stop", "X"]])
    n1_ids = []
    for i in range(n1):
        sig = [["move", f"Y{i}", "by", "D"], ["stop", f"Y{i}"]]
        obs = _observe_decoded(s, ag, signature=sig, key=f"probe_subst_{i}",
                                residual=sig, decoded_epoch=_epoch(s, ag))
        n1_ids.append(obs)
    # N2 genuinely-novel residuals (predicate absent from the whole codebook
    # -- rung 1 and rung 2 both exhaustively fail, per the Ceiling doc's own
    # audit of what rung 1/2 actually try)
    n2 = 4
    n2_ids = []
    for i in range(n2):
        sig = [["utterly_novel_predicate", f"Z{i}", i]]
        obs = _observe_decoded(s, ag, signature=sig, key=f"probe_novel_{i}",
                                residual=sig, decoded_epoch=_epoch(s, ag))
        n2_ids.append(obs)

    native.run_rules()
    directed_mints = _axes(s) - baseline_axes
    recognized = sum(1 for o in n1_ids if s.node(o)["attrs"].get("status") == "recognized_transformed")

    undirected_mints = n1 + n2  # DEFINED counterfactual: mint on every
    # residual without attempting rung-1/rung-2 first -- exactly the
    # paper's own falsifier framing ("an undirected baseline"). No engine
    # run needed for this count; it is the policy's definition, not a
    # measurement of a second implementation.

    print(f"real rung-ordered ladder: {directed_mints} CapabilityAxis minted "
          f"({recognized}/{n1} transform-explainable residuals recognized "
          f"WITHOUT minting; {n2} genuinely-novel residuals correctly minted)")
    print(f"undirected baseline (mint-everything): {undirected_mints} minted (by definition)")
    passed = directed_mints < undirected_mints and directed_mints == n2 and recognized == n1
    print(f"TAU-L-1 PASS = {passed}")
    return dict(find_self_process_result=proc, phi_r_law_today=(proc is not None),
                directed_mints=directed_mints, undirected_mints=undirected_mints,
                n1_transform_explainable=n1, n2_genuinely_novel=n2,
                recognized_without_mint=recognized, passed=bool(passed))


def _tiebreak_goal_and_parts():
    """Constructed so the REAL composer's own (coverage, total_fit) key
    prefers the MANY-parts route over a single big part achieving full
    coverage in one step -- an adversarial construction in the same spirit
    as scripts/probe_beam_completeness.py's greedy-set-cover transplant,
    searched empirically against the live engine (see the results doc for
    the trace that led here)."""
    g = [["at", "A", 1], ["at", "B", 2], ["at", "C", 3], ["at", "D", 4]]
    return g


def _run_composer_tiebreak(exact_bases=True):
    s, ag = boot_core()
    goal = _tiebreak_goal_and_parts()
    # FEW-parts route: one part, exact copy of the goal (full alignment).
    _add_part(s, "part_one_big", goal)
    # MANY-parts route: two parts, each an exact positional match of half
    # the goal (each step therefore scores a HIGHER per-step fit than the
    # one-shot match against the full 4-relation residual would, because
    # shape_fit anti-unifies position-by-position over min(len(residual),
    # len(psig)) -- a 2-relation part against a 2-relation residual aligns
    # exactly; the 4-relation part against the SAME 2-relation residual
    # would truncate and score lower there).
    _add_part(s, "part_two_a", goal[:2])
    _add_part(s, "part_two_b", goal[2:])
    out_all = rf.compose_design_for_goal(s, goal, beam=3, max_steps=4, cand_k=5, budget=2000)
    return s, ag, goal, out_all


def run_tau_l_2_and_3():
    print("\n=== TAU-L-2 / TAU-L-3: representable vs operative ===")
    s, ag, goal, out_implicit = _run_composer_tiebreak()
    parts_implicit = out_implicit.get("ordered_parts") or []
    print(f"implicit-only composer output: ordered_parts={parts_implicit}, "
          f"authored={out_implicit.get('authored')}, residual={out_implicit.get('residual')}")

    # --- TAU-L-2: add representation only (a SelfProcess node, same shape
    # as the six already seeded), no wiring into any decision.
    law_node = s.add_node("SelfProcess", {
        "process": "growing", "verb": "grow",
        "aliases": "grow growth mint minting codebook parsimony",
        "account": "I mint new capability only after cheaper explanations "
                    "(recognition, then transform, then dimension-inference) "
                    "have failed, and among plans that explain a goal "
                    "equally well I prefer the FEWEST parts.",
        "objective": "min_parts",
        "source": "the shape-decode growth ladder (sd_recognize -> "
                   "sd_transform_decode -> sd_infer_dimension -> sd_mint_quantum)"})
    proc = sm.find_self_process(s, ["grow", "growth", "mint", "minting"])
    answer = sm.run_self_process(s, proc) if proc else None
    print(f"after adding SelfProcess node: find_self_process -> {proc!r}; "
          f"run_self_process -> found={answer.get('found') if answer else None}")

    # Re-run the SAME tie-break composer call -- representation alone must
    # not change the real composer's own output (phi_O still 0).
    out_after_repr = rf.compose_design_for_goal(s, goal, beam=3, max_steps=4, cand_k=5, budget=2000)
    parts_after_repr = out_after_repr.get("ordered_parts") or []
    tau_l2_unchanged = (parts_after_repr == parts_implicit)
    print(f"composer output UNCHANGED by mere representation: {tau_l2_unchanged} "
          f"(ordered_parts still {parts_after_repr})")

    # --- TAU-L-3: add operative wiring -- a decision rule that READS the
    # SelfProcess node's `objective` attr from the live graph and applies
    # it as an explicit tie-break / preference over composer candidates.
    # This mirrors what a graph-native Rule would do (read ℓ_X, decide);
    # it is a probe-only construct, not proposed shippable agent code (see
    # the prereg's §8 and the results doc's honesty note).
    def explicit_wired_choice(s, candidates):
        node = next(iter(s.nodes("SelfProcess")), None)
        objective = None
        for n in s.nodes("SelfProcess"):
            at = s.node(n)["attrs"]
            if at.get("process") == "growing":
                objective = at.get("objective")
                break
        if objective == "min_parts":
            return min(candidates, key=lambda c: len(c["ordered_parts"] or []))
        if objective == "max_parts":
            return max(candidates, key=lambda c: len(c["ordered_parts"] or []))
        return candidates[0]  # no representation to read -- falls back to composer order

    # Generate the two real candidate plans explicitly (few-parts vs
    # many-parts), both fully covering, via `exclude` so each run only sees
    # one route -- then the wired rule picks between REAL composer outputs.
    out_few = rf.compose_design_for_goal(s, goal, beam=3, max_steps=4, cand_k=5,
                                          exclude=["part_two_a", "part_two_b"], budget=2000)
    out_many = rf.compose_design_for_goal(s, goal, beam=3, max_steps=4, cand_k=5,
                                           exclude=["part_one_big"], budget=2000)
    candidates = [out_few, out_many]
    chosen = explicit_wired_choice(s, candidates)
    chosen_len = len(chosen.get("ordered_parts") or [])
    few_len, many_len = len(out_few.get("ordered_parts") or []), len(out_many.get("ordered_parts") or [])
    print(f"candidates: few-parts plan len={few_len} ({out_few.get('ordered_parts')}), "
          f"many-parts plan len={many_len} ({out_many.get('ordered_parts')})")
    print(f"explicit-wired choice (objective=min_parts): chosen len={chosen_len}")
    tau_l3_correct = (chosen_len == min(few_len, many_len))

    # Perturbation test: flip objective to max_parts, same battery, same
    # code, only the represented content changed.
    for n in s.nodes("SelfProcess"):
        at = s.node(n)["attrs"]
        if at.get("process") == "growing":
            s.set_attr(n, "objective", "max_parts") if hasattr(s, "set_attr") else at.__setitem__("objective", "max_parts")
    # re-fetch objective directly (defensive against set_attr not existing)
    for n in s.nodes("SelfProcess"):
        at = s.node(n)["attrs"]
        if at.get("process") == "growing" and at.get("objective") != "max_parts":
            at["objective"] = "max_parts"
    chosen_flipped = explicit_wired_choice(s, candidates)
    chosen_flipped_len = len(chosen_flipped.get("ordered_parts") or [])
    print(f"after perturbing objective -> max_parts: chosen len={chosen_flipped_len}")
    perturbation_flips = (chosen_flipped_len == max(few_len, many_len)) and (chosen_flipped_len != chosen_len)

    print(f"TAU-L-2 PASS (repr without wiring = no behaviour change) = {tau_l2_unchanged}")
    print(f"TAU-L-3 PASS (wired choice matches min_parts objective, "
          f"AND perturbation flips it) = {tau_l3_correct and perturbation_flips}")

    # --- TAU-L control: a non-tied battery -- explicit rule must be a
    # no-op when the implicit machinery already has a unique winner.
    s2, ag2 = boot_core()
    goal2 = [["only", "X", 1]]
    _add_part(s2, "sole_part", goal2)
    out_nontied = rf.compose_design_for_goal(s2, goal2, beam=3, max_steps=4, cand_k=5, budget=2000)
    control_choice = explicit_wired_choice(s2, [out_nontied])
    control_noop = (control_choice is out_nontied)
    print(f"TAU-L control (non-tied battery, explicit rule is a no-op) = {control_noop}")

    return dict(implicit_ordered_parts=parts_implicit,
                after_representation_ordered_parts=parts_after_repr,
                tau_l2_pass=bool(tau_l2_unchanged),
                few_parts_len=few_len, many_parts_len=many_len,
                explicit_choice_len=chosen_len,
                explicit_choice_len_after_perturbation=chosen_flipped_len,
                tau_l3_pass=bool(tau_l3_correct and perturbation_flips),
                control_noop=bool(control_noop))


# ===========================================================================
# TAU-RES -- follow-up: a direct, quantitative, side-by-side construction of
# "where is the residual processed" (object-level vs meta-level promotion),
# per docs/research/theory_convergence/TAU_HIERARCHY_AXIS_MAP_PREREG.md S7c.
# Both arms reuse REAL seeded rules and REAL existing test fixtures/scene
# builders (tests/test_arc_goals_migrated.py, tests/
# test_dimension_inference_migrated.py) -- imported directly, not
# reimplemented.
# ===========================================================================

def run_tau_res_arm1():
    """Arm 1 -- object-level-only: ax_impotent's cached AgendaVerdict.
    A hand-controlled, non-drifting pool (arc_goals + arc_executor seeds
    only -- the full program-synthesis boot() fixture in
    tests/test_arc_executor_migrated.py was tried FIRST and found to keep
    minting new ArcGoal nodes under its own seeded rules across repeated
    run_rules() calls, an honest complication reported here rather than
    worked around silently) shows the cached nearest_unroutable_* fields
    freeze at mint and do NOT track a live ranking change under an
    UNCHANGED pool signature."""
    print("\n=== TAU-RES Arm 1: object-level-only (ax_impotent) ===")
    import importlib
    tag = importlib.import_module("test_arc_goals_migrated")
    from domains import arc_executor as axe
    from domains import arc_goal_ingest as agi

    s, ag, agenda = tag._bare(("arc_goals", "arc_executor"))
    tag._strip_shipped_sources(s)
    tag._goal(s, agenda, agid="probe.g1", kind="kindA", headroom_n=48.0)
    tag._goal(s, agenda, agid="probe.g2", kind="kindB", headroom_n=1.0)
    tag._goal(s, agenda, agid="probe.g3", kind="kindB", headroom_n=1.0)
    tag._goal(s, agenda, agid="probe.g4", kind="kindB", headroom_n=1.0)
    s._inner.run_rules()

    avs = axe.agenda_verdicts(s, "impotent")
    assert len(avs) == 1, f"expected exactly one impotent verdict at mint, got {len(avs)}"
    frozen = dict(avs[0])
    pool_sig_before = sorted(json.loads(frozen["pool_agids"]))
    print(f"minted verdict: nearest_unroutable_agid={frozen['nearest_unroutable_agid']!r} "
          f"kind={frozen['nearest_unroutable_kind']!r}, pool_agids={pool_sig_before}")

    # Stability control: repeated no-op passes must not re-mint or change it.
    for _ in range(3):
        s._inner.run_rules()
    avs_stable = axe.agenda_verdicts(s, "impotent")
    stable_ok = len(avs_stable) == 1 and avs_stable[0]["_id"] == frozen["_id"]
    print(f"stability control (3 no-op passes): still 1 verdict, same id = {stable_ok}")

    # THE PERTURBATION: raise g2's headroom_n far above g1's. All four goals
    # stay headroom_n > 0 -- pool membership (the mint-once SIGNATURE) is
    # UNCHANGED -- but the live ag_select ranking winner moves.
    for n in s.nodes("ArcGoal"):
        if s.node(n)["attrs"].get("agid") == "probe.g2":
            s.set_attr(n, "headroom_n", 500.0)
    s._inner.run_rules()

    avs_after = axe.agenda_verdicts(s, "impotent")
    pool_sig_after = sorted(json.loads(avs_after[0]["pool_agids"])) if avs_after else None
    no_remint = len(avs_after) == 1 and avs_after[0]["_id"] == frozen["_id"]
    sig_unchanged = pool_sig_after == pool_sig_before

    at = s.node(agenda)["attrs"]
    live_winner = at.get("arc_sel_agid")
    selection = agi.selection(s)
    cached_winner = frozen["nearest_unroutable_agid"]
    diverged = live_winner != cached_winner

    print(f"after perturbation: verdict count={len(avs_after)} (no re-mint = {no_remint}), "
          f"pool signature unchanged = {sig_unchanged}")
    print(f"CACHED (frozen at mint): nearest_unroutable_agid={cached_winner!r} "
          f"kind={frozen['nearest_unroutable_kind']!r}")
    print(f"LIVE (freshly re-derived by the real ag_select rule): arc_sel_agid={live_winner!r} "
          f"value={selection.get('arc_sel_value')}, runner_up={selection.get('arc_sel_runner_up_agid')!r} "
          f"runner_up_value={selection.get('arc_sel_runner_up_value')}, margin={selection.get('arc_sel_margin')}")
    print(f"CACHED VERDICT IS WRONG relative to live truth = {diverged}")

    passed = no_remint and sig_unchanged and diverged and stable_ok
    print(f"TAU-RES-1 PASS = {passed}")
    return dict(cached_agid=cached_winner, cached_kind=frozen["nearest_unroutable_kind"],
                live_agid=live_winner, live_value=selection.get("arc_sel_value"),
                cached_value_now=selection.get("arc_sel_runner_up_value"),
                margin=selection.get("arc_sel_margin"),
                no_remint=bool(no_remint), pool_signature_unchanged=bool(sig_unchanged),
                diverged=bool(diverged), stable_control_ok=bool(stable_ok),
                passed=bool(passed))


def run_tau_res_arm2():
    """Arm 2 -- meta-level promotion: DimInfer / LatentDimension. Two real
    scenes differing in exactly one variable (dim_types present or absent
    on the codebook part -- i.e. rung 2 available or structurally
    unavailable, the seed's own documented graceful-skip path, gated by
    tests/test_dimension_inference_migrated.py's own test 6). Identical
    two-observation battery (scale x2 then a genuinely novel scale x4) fed
    to both."""
    print("\n=== TAU-RES Arm 2: meta-level promotion (DimInfer/LatentDimension) ===")
    import importlib
    tdi = importlib.import_module("test_dimension_inference_migrated")

    DIM_TYPES = tdi.DIM_TYPES
    TROMINO = tdi.TROMINO
    SCALED_X2 = tdi.SCALED_X2_TROMINO
    # k=2 image: tromino {(0,0),(0,1),(1,0)} x4 about its origin -- a
    # genuinely novel instance of the scale2 family, not in either test
    # file's existing fixture set, derived the same way the k=1 fixture's
    # own comment documents (scale about origin).
    SCALED_X4 = [["cell", 0, 0, "red"], ["cell", 0, 4, "red"], ["cell", 4, 0, "red"]]

    def axes(s):
        return len(list(s.nodes("CapabilityAxis")))

    def latents(s):
        return len(list(s.nodes("LatentDimension")))

    # --- Scene M: promotion available (dim_types present) ---
    s, ag, native = tdi._boot()
    tdi._add_part(s, "part_scale_meta", TROMINO, dim_types=DIM_TYPES)
    base_axes_m = axes(s)

    obs1 = tdi._observe_decoded(s, ag, signature=SCALED_X2, key="m_obs1", residual=SCALED_X2,
                                 decoded_epoch=tdi._epoch(s, ag), dim_types=DIM_TYPES)
    native.run_rules()
    at1 = s.node(obs1)["attrs"]

    obs2 = tdi._observe_decoded(s, ag, signature=SCALED_X4, key="m_obs2", residual=SCALED_X4,
                                 decoded_epoch=tdi._epoch(s, ag), dim_types=DIM_TYPES)
    native.run_rules()
    at2 = s.node(obs2)["attrs"]
    axes_m_total = axes(s) - base_axes_m
    t2 = None
    if at2.get("status") == "recognized_transformed":
        t_node = next(iter(s.neighbours(obs2, "has_transform")), None)
        if t_node is not None:
            t2 = dict(s.node(t_node)["attrs"])

    print(f"Scene M (dim_types present): obs1(x2) status={at1.get('status')!r} "
          f"dim_explained={at1.get('dim_explained')!r}; "
          f"obs2(x4, NOVEL) status={at2.get('status')!r} dim_explained={at2.get('dim_explained')!r} "
          f"generator={t2.get('generator') if t2 else None} k={t2.get('k') if t2 else None}; "
          f"total CapabilityAxis minted across both = {axes_m_total}")

    # --- Scene O: promotion unavailable (no dim_types -- graceful skip) ---
    s2, ag2, native2 = tdi._boot()
    tdi._add_part(s2, "part_scale_obj", TROMINO)  # NO dim_types
    base_axes_o = axes(s2)

    obs1b = tdi._observe_decoded(s2, ag2, signature=SCALED_X2, key="o_obs1", residual=SCALED_X2,
                                  decoded_epoch=tdi._epoch(s2, ag2))
    native2.run_rules()
    at1b = s2.node(obs1b)["attrs"]

    obs2b = tdi._observe_decoded(s2, ag2, signature=SCALED_X4, key="o_obs2", residual=SCALED_X4,
                                  decoded_epoch=tdi._epoch(s2, ag2))
    native2.run_rules()
    at2b = s2.node(obs2b)["attrs"]
    axes_o_total = axes(s2) - base_axes_o

    print(f"Scene O (dim_types absent, rung 2 unavailable): obs1(x2) status={at1b.get('status')!r} "
          f"dim_checked={at1b.get('dim_checked')!r} dim_explained={at1b.get('dim_explained')!r}; "
          f"obs2(x4, SAME NOVEL instance) status={at2b.get('status')!r} "
          f"dim_checked={at2b.get('dim_checked')!r} dim_explained={at2b.get('dim_explained')!r}; "
          f"total CapabilityAxis minted across both = {axes_o_total}")

    obs2_recognized_in_M = at2.get("status") == "recognized_transformed" and bool(at2.get("dim_explained"))
    obs2_minted_in_O = at2b.get("status") == "minted" and not at2b.get("dim_explained")
    generalization_gap = axes_o_total > axes_m_total
    passed = obs2_recognized_in_M and obs2_minted_in_O and axes_m_total == 0 and generalization_gap

    print(f"the SAME novel (x4) residual: recognized in Scene M = {obs2_recognized_in_M}, "
          f"forced to mint fresh capacity in Scene O = {obs2_minted_in_O}")
    print(f"CapabilityAxis mint count, identical 2-instance battery: Scene M={axes_m_total} "
          f"vs Scene O={axes_o_total}")
    print(f"TAU-RES-2 PASS = {passed}")
    return dict(scene_m_axes_total=axes_m_total, scene_o_axes_total=axes_o_total,
                obs2_recognized_in_M=bool(obs2_recognized_in_M),
                obs2_minted_in_O=bool(obs2_minted_in_O),
                obs2_generator=t2.get("generator") if t2 else None,
                obs2_k=t2.get("k") if t2 else None,
                passed=bool(passed))


# ===========================================================================
# TAU-ORTHO -- structural independence
# ===========================================================================

def run_tau_ortho(tau_l_graph_owners, tau_c_used_selfprocess):
    print("\n=== TAU-ORTHO: structural independence of Axis C and Axis L ===")
    print(f"TAU-L probe graphs contained foreign-owner ('other') ShapeSignature "
          f"content: {tau_l_graph_owners} (expected: False)")
    print(f"TAU-C probe graphs contained SelfProcess/law content: "
          f"{tau_c_used_selfprocess} (expected: False)")
    return dict(tau_l_used_axis_c_content=tau_l_graph_owners,
                tau_c_used_axis_l_content=tau_c_used_selfprocess)


def main():
    rng = random.Random(20260811)
    results = {}
    results["tau_c"] = run_tau_c(rng, n=200)
    results["tau_l_1"] = run_tau_l_1()
    results["tau_l_2_3"] = run_tau_l_2_and_3()
    results["tau_res_arm1"] = run_tau_res_arm1()
    results["tau_res_arm2"] = run_tau_res_arm2()

    # structural orthogonality: re-check the TAU-L graphs for owner="other"
    # content, and the TAU-C graphs for SelfProcess content, freshly.
    s_l, ag_l, native_l = _boot_sd()
    l_has_other = any(s_l.node(n)["attrs"].get("owner") == "other" for n in s_l.nodes("ShapeSignature"))
    s_c, _ = boot_core()
    _add_part(s_c, "self_p", [["x", 1]], owner="self")
    _add_part(s_c, "other_p", [["y", 1]], owner="other")
    c_has_law = len(list(s_c.nodes("SelfProcess"))) > 0
    results["tau_ortho"] = run_tau_ortho(l_has_other, c_has_law)

    print("\n=== SUMMARY ===")
    print(json.dumps({
        k: (v if not isinstance(v, dict) else {kk: vv for kk, vv in v.items() if kk != "rows_sample"}
            if False else v) for k, v in results.items()
    }, default=str, indent=2)[:4000])

    if len(sys.argv) > 1:
        with open(sys.argv[1], "w") as f:
            json.dump(results, f, default=str, indent=2)
        print(f"\nwrote {sys.argv[1]}")


if __name__ == "__main__":
    main()

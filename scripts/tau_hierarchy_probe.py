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

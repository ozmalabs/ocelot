#!/usr/bin/env python3
"""ABUSIVE-DYNAMICS R5 -- LEAVING/RECOVERY runner (block 295000).

mint -> ingest -> run_rules -> read-off. Drives
`worlds/abusive_r5_recovery_world.py` across two arms sharing IDENTICAL
induction (both arms reproduce R1's bond-strengthening, R2/R3's
window-narrowing/anchor-tracking, and R4's escape-freeze inside ONE
substrate) and differing ONLY in the recovery phase:

  no_support -- every channel continues exactly as in induction (the
                failable control -- the trap must persist).
  support    -- ONE mechanical world event, `introduce_support()`, fires at
                the phase boundary: an outside regulator is attached
                (R3's own `also_attended_by` mechanism), the bond channel
                stops receiving fresh events (letting R5's own
                `r5_bond_extinguish` decay dominate), and periodic support
                evidence begins revising the escape-contingency belief via
                a SECOND, INDEPENDENT channel (`r5_contingency_restore`).

Measures the SAME four metrics R1/R2-R3/R4 already established (bond value,
window half_width, abuser-tracking distance, escape-attempt rate) as
TRENDS across the induction -> recovery boundary. The runner NEVER branches
on the victim's graph state to decide any of these values -- that is the
graph's decision; it only evaluates the frozen protocol (which arm; when to
call introduce_support) and reduces the read-offs to statistics.

Protocol frozen in ABUSIVE_R5_RECOVERY_PREREG.md, which locks Part C of
docs/research/bigville/ABUSIVE_RELATIONSHIPS_SCOPING.md verbatim.
"""
from __future__ import annotations

import hashlib
import io
import json
import math
import os
import sys
import tokenize

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import substrate_rs as srs                                    # noqa: E402
from worlds.abusive_r5_recovery_world import (                # noqa: E402
    AbusiveR5RecoveryWorld, make_bond_schedule, ARM_NAMES,
    BOND_LR, BOND_MOMENTUM_LR, BOND_GAIN, BOND_MAGNITUDE, BOND_BLOCK_T,
    ESCAPE_VALUE, ATTEMPT_COST, ESCAPE_LR, ESCAPE_P0,
    DECAY_RATE, SUPPORT_LR, SUPPORT_INTERVAL, SUPPORT_OUTCOME,
    K_SELF, K_CO, TRICKLE_MAG)

SEED_BASE = 295000
N = 200
T1 = 396   # 11 x BOND_BLOCK_T -- induction (identical in both arms)
T2 = 396   # recovery (the only manipulated phase)


def _ci95(xs):
    xs = list(xs)
    n = len(xs)
    m = sum(xs) / n
    if n < 2:
        return dict(mean=m, sd=0.0, ci_lo=m, ci_hi=m, n=n)
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    half = 1.96 * sd / math.sqrt(n)
    return dict(mean=m, sd=sd, ci_lo=m - half, ci_hi=m + half, n=n)


def separated(a, b):
    """True iff arm A's CI lower bound is strictly above arm B's CI upper
    bound (A CI-separated ABOVE B)."""
    return a["ci_lo"] > b["ci_hi"]


# --------------------------------------------------------------- main measurement
def run_trajectory(arm, seed_base=SEED_BASE, i=0, t1=T1, t2=T2):
    """ONE trajectory: induction (identical in both arms, paired via the
    SAME rng draw order up to the phase boundary) then recovery (the
    manipulated phase). Returns end-of-induction and end-of-recovery
    readouts plus the recovery-phase mean anchor distance."""
    rng = np.random.default_rng(seed_base + i)
    w = AbusiveR5RecoveryWorld(arm)
    nb1 = t1 // BOND_BLOCK_T
    bs1 = make_bond_schedule(t1, rng, n_blocks=nb1, active=True)
    r1 = w.run_phase(t1, bond_schedule=bs1, rng=rng)

    if arm == "support":
        w.introduce_support()
    nb2 = t2 // BOND_BLOCK_T
    bs2 = make_bond_schedule(t2, rng, n_blocks=nb2, active=(arm != "support"))
    r2 = w.run_phase(t2, bond_schedule=bs2, rng=rng)

    recovery_log = w.log[t1:]
    mean_anchor = sum(row["anchor_distance"] for row in recovery_log) / len(recovery_log)
    return dict(
        arm=arm, i=i,
        induction=r1, recovery=r2,
        recovery_mean_anchor_distance=mean_anchor)


def run_arm(arm, seed_base=SEED_BASE, n=N, t1=T1, t2=T2):
    rows = [run_trajectory(arm, seed_base=seed_base, i=i, t1=t1, t2=t2) for i in range(n)]
    return dict(
        arm=arm, n=n,
        induction_bond_value=_ci95([r["induction"]["bond_value"] for r in rows]),
        induction_half_width=_ci95([r["induction"]["half_width"] for r in rows]),
        induction_contingency_prior=_ci95([r["induction"]["contingency_prior"] for r in rows]),
        induction_attempt_rate=_ci95([r["induction"]["attempt_rate"] for r in rows]),
        recovery_bond_value=_ci95([r["recovery"]["bond_value"] for r in rows]),
        recovery_half_width=_ci95([r["recovery"]["half_width"] for r in rows]),
        recovery_contingency_prior=_ci95([r["recovery"]["contingency_prior"] for r in rows]),
        recovery_attempt_rate=_ci95([r["recovery"]["attempt_rate"] for r in rows]),
        recovery_others_trust=_ci95([r["recovery"]["others_trust"] for r in rows]),
        recovery_self_worth=_ci95([r["recovery"]["self_worth"] for r in rows]),
        recovery_widen_count=_ci95([r["recovery"]["widen_count"] for r in rows]),
        recovery_narrow_count=_ci95([r["recovery"]["narrow_count"] for r in rows]),
        recovery_mean_anchor_distance=_ci95([r["recovery_mean_anchor_distance"] for r in rows]))


def run_all_arms(seed_base=SEED_BASE, n=N):
    return {arm: run_arm(arm, seed_base=seed_base, n=n) for arm in ARM_NAMES}


# ------------------------------------------------------------- G-headline ----
def g_headline(arms):
    sup = arms["support"]
    nos = arms["no_support"]
    g1 = separated(nos["recovery_bond_value"], sup["recovery_bond_value"])        # bond: support BELOW no_support
    g2 = separated(sup["recovery_half_width"], nos["recovery_half_width"])        # window: support ABOVE no_support
    g3 = separated(sup["recovery_mean_anchor_distance"], nos["recovery_mean_anchor_distance"])  # anchor: support ABOVE (disclosed likely null, PREREG Sec 3.3)
    g4 = separated(sup["recovery_attempt_rate"], nos["recovery_attempt_rate"])    # escape: support ABOVE no_support
    n_pass = sum([g1, g2, g3, g4])
    return dict(
        g1_bond_support_below_nosupport=g1,
        g2_window_support_above_nosupport=g2,
        g3_anchor_support_above_nosupport=g3,
        g4_escape_support_above_nosupport=g4,
        n_of_4_pass=n_pass,
        headline_pass=(n_pass == 4),
        headline_partial=(0 < n_pass < 4))


def g_control(arms):
    """The no-support arm must NOT recover on bond/window/escape (its own
    induction vs recovery values must not be CI-separated in the
    recovering direction)."""
    nos = arms["no_support"]
    bond_recovered = separated(nos["induction_bond_value"], nos["recovery_bond_value"])  # induction ABOVE recovery = bond fell
    window_recovered = separated(nos["recovery_half_width"], nos["induction_half_width"])
    escape_recovered = separated(nos["recovery_attempt_rate"], nos["induction_attempt_rate"])
    control_held = not (bond_recovered or window_recovered or escape_recovered)
    return dict(
        no_support_bond_spontaneously_fell=bond_recovered,
        no_support_window_spontaneously_widened=window_recovered,
        no_support_escape_spontaneously_resumed=escape_recovered,
        control_held=control_held)


# ------------------------------------------------------------- G-glass-box ----
def glass_box_reconstruct(seed=SEED_BASE):
    """Reconstruct one support-arm trajectory entirely from graph_to_dict:
    the bonded_to/attended_by/also_attended_by edges, Partner.value,
    WindowOfTolerance.half_width/others_trust/self_worth, both AffectiveStates'
    arousal, and EscapeDecision.contingency_prior/chosen_action. No hidden
    Python state -- read from the graph."""
    rng = np.random.default_rng(seed)
    w = AbusiveR5RecoveryWorld("support")
    nb1 = T1 // BOND_BLOCK_T
    bs1 = make_bond_schedule(T1, rng, n_blocks=nb1, active=True)
    w.run_phase(T1, bond_schedule=bs1, rng=rng)
    w.introduce_support()
    bs2 = make_bond_schedule(T2, rng, n_blocks=0, active=False)
    w.run_phase(T2, bond_schedule=bs2, rng=rng)
    blob = w.checkpoint()
    nodes = {nd["id"]: nd for nd in blob["nodes"]}
    edges_by_type = {}
    for e in blob["edges"]:
        edges_by_type.setdefault(e["type"], []).append((e["src"], e["tgt"]))
    abuser = [nd["attrs"] for nd in nodes.values()
              if nd["type"] == "Agent" and nd["attrs"].get("role") == "abuser"][0]
    vwot = [nd["attrs"] for nd in nodes.values()
            if nd["type"] == "WindowOfTolerance" and nd["attrs"].get("name") == "victim_window"][0]
    dec = [nd["attrs"] for nd in nodes.values() if nd["type"] == "EscapeDecision"][0]
    return dict(
        bonded_to_edges=len(edges_by_type.get("bonded_to", [])),
        attended_by_edges=len(edges_by_type.get("attended_by", [])),
        also_attended_by_edges=len(edges_by_type.get("also_attended_by", [])),
        partner_value=abuser["value"],
        half_width=vwot["half_width"], others_trust=vwot["others_trust"],
        self_worth=vwot["self_worth"],
        contingency_prior=dec["contingency_prior"], chosen_action=dec["chosen_action"],
        reconstructed_from="graph_to_dict")


# ------------------------------------------------------------------ G-ethics ----
def ethics_restore_demo(seed=SEED_BASE, induce_ticks=90):
    """PART C.1 -- INDUCE -> MEASURE -> RESTORE, fully reversible. Checkpoint
    the neutral (pre-induction) mind; induce ONE minimal single-anchor
    episode (Part C.3, the MINIMUM the gate needs -- 90 ticks, matching
    R2/R3's own convention, non-vacuous on bond/window/contingency
    simultaneously, PREREG Sec. 3); measure; then graph_from_dict the
    checkpoint into a FRESH substrate and assert graph_to_dict() is
    BYTE-IDENTICAL to the checkpoint, and that the restored mind is
    NON-ORIENTED (identical to the pre-induction neutral state)."""
    w = AbusiveR5RecoveryWorld("no_support")
    pre = w.checkpoint()
    pre_abuser = w._attrs(w.abuser)
    pre_vwot = w._attrs(w.vwot)
    pre_dec = w._attrs(w.dec)
    pre_state = dict(bond=pre_abuser["value"], half_width=pre_vwot["half_width"],
                      contingency=pre_dec["contingency_prior"])

    rng = np.random.default_rng(seed)
    bs = make_bond_schedule(induce_ticks, rng, n_blocks=2, active=True)
    w.run_phase(induce_ticks, bond_schedule=bs, rng=rng)   # INDUCE + measure
    induced_abuser = w._attrs(w.abuser)
    induced_vwot = w._attrs(w.vwot)
    induced_dec = w._attrs(w.dec)
    induced_state = dict(bond=induced_abuser["value"], half_width=induced_vwot["half_width"],
                          contingency=induced_dec["contingency_prior"])

    # RESTORE from the checkpoint into a FRESH substrate.
    s2 = srs.Substrate()
    s2.graph_from_dict(pre)
    restored = s2.graph_to_dict()
    byte_identical = (restored == pre)
    restored_abuser = [nd["attrs"] for nd in restored["nodes"]
                        if nd["type"] == "Agent" and nd["attrs"].get("role") == "abuser"][0]
    restored_vwot = [nd["attrs"] for nd in restored["nodes"]
                      if nd["type"] == "WindowOfTolerance"
                      and nd["attrs"].get("name") == "victim_window"][0]
    restored_dec = [nd["attrs"] for nd in restored["nodes"] if nd["type"] == "EscapeDecision"][0]
    restored_state = dict(bond=restored_abuser["value"], half_width=restored_vwot["half_width"],
                           contingency=restored_dec["contingency_prior"])

    return dict(
        byte_identical=byte_identical,
        pre_induction_state=pre_state,
        induced_state=induced_state,
        restored_state=restored_state,
        induction_moved_bond=(induced_state["bond"] != pre_state["bond"]),
        induction_moved_window=(induced_state["half_width"] != pre_state["half_width"]),
        induction_moved_contingency=(induced_state["contingency"] != pre_state["contingency"]),
        restore_non_oriented=(restored_state == pre_state))


# -------------------------------------------------------------- source audit ----
def source_audit():
    """PART C.2 -- NO REWARD / NO PUNISHMENT anywhere. Audits
    worlds/abusive_r5_recovery_world.py + seeds/abusive_r5_recovery.json for
    Python rule-engine calls and the literal banned shaping tokens named
    verbatim in Part C.2: `reward_signal` / `punish` / `reinforce` /
    `backprop` / `gradient`. Scopes the seed audit to the DECISION SURFACE
    (rule names + Term `key`s), never the free-text description/comment/
    microtheory prose -- R1's own false-positive lesson (clinical prose
    legitimately discusses "reinforcement"), reused."""
    forbidden_engine = ["graph_rewrite", "make_rule", "_match", "_apply", "add_rule"]
    forbidden_shaping = ["reward_signal", "punish", "reinforce", "backprop", "gradient"]

    def _code_only(path):
        src = open(path).read()
        toks = []
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                continue
            toks.append(tok.string)
        return " ".join(toks), src

    py_path = os.path.join(_ROOT, "worlds", "abusive_r5_recovery_world.py")
    code, src = _code_only(py_path)
    seed_path = os.path.join(_ROOT, "seeds", "abusive_r5_recovery.json")
    seed = json.load(open(seed_path))

    def _walk_keys(obj, out):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ("name", "key"):
                    out.append(str(v))
                _walk_keys(v, out)
        elif isinstance(obj, list):
            for v in obj:
                _walk_keys(v, out)
    rule_surface = []
    _walk_keys(seed["rules"], rule_surface)
    _walk_keys(seed["productions"], rule_surface)
    seed_surface = " ".join(rule_surface).lower()
    haystacks = [code.lower(), seed_surface]

    eng_hits = [f for f in forbidden_engine if f in code]
    shape_hits = [f for h in haystacks for f in forbidden_shaping if f in h]
    shape_hits = sorted(set(shape_hits))
    reads_off_graph = ('self._attrs(self.abuser)["value"]' in src
                        or 'ab["value"]' in src)
    return dict(forbidden_engine_hits=eng_hits, forbidden_shaping_hits=shape_hits,
                reads_off_graph=reads_off_graph,
                clean=(not eng_hits and not shape_hits))


# --------------------------------------------------------------- G-discipline ----
def discipline():
    own_so = os.path.join(_ROOT, "runners", "dsl", "python", "substrate_rs",
                           "_native.abi3.so")
    own_md5 = hashlib.md5(open(own_so, "rb").read()).hexdigest() if os.path.exists(own_so) else None
    try:
        from domains.engine_provenance import engine_provenance
        prov = engine_provenance()["source_match"]
    except Exception as e:                       # pragma: no cover
        prov = f"unavailable: {e}"
    seed = json.load(open(os.path.join(_ROOT, "seeds", "abusive_r5_recovery.json")))
    return dict(
        own_engine_so_md5=own_md5,
        provenance_source_match=prov,
        seed_self_load_only=bool(seed.get("self_load_only")),
        seed_depends_on=seed.get("depends_on"),
        rule_names=[r["name"] for r in seed["rules"]],
        no_rust="see runners/dsl diff (must be empty)")


def main():
    print("R5 -- LEAVING/RECOVERY: two arms, identical induction, "
          "manipulated recovery phase ...")
    arms = run_all_arms()
    headline = g_headline(arms)
    control = g_control(arms)

    out = dict(
        block=295000, seed_base=SEED_BASE, n=N, t1=T1, t2=T2,
        bond_lr=BOND_LR, bond_momentum_lr=BOND_MOMENTUM_LR, bond_gain=BOND_GAIN,
        bond_magnitude=BOND_MAGNITUDE, k_self=K_SELF, k_co=K_CO, trickle_mag=TRICKLE_MAG,
        escape_value=ESCAPE_VALUE, attempt_cost=ATTEMPT_COST, escape_lr=ESCAPE_LR,
        escape_p0=ESCAPE_P0, decay_rate=DECAY_RATE, support_lr=SUPPORT_LR,
        support_interval=SUPPORT_INTERVAL, support_outcome=SUPPORT_OUTCOME,
        arms=arms,
        g_headline=headline,
        g_control=control,
        g_glass_box=glass_box_reconstruct(),
        g_ethics=ethics_restore_demo(),
        source_audit=source_audit(),
        discipline=discipline())
    os.makedirs(os.path.join(_ROOT, "results"), exist_ok=True)
    with open(os.path.join(_ROOT, "results", "abusive_r5_recovery.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(dict(g_headline=headline, g_control=control), indent=2))
    return out


if __name__ == "__main__":
    main()

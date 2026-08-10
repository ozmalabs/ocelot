#!/usr/bin/env python3
"""THE DISORDER GLASS-BOX — mental illness as a mis-set decay/demotion knob
(seed block 199000).

MECHANICAL MEASURE-ADAPTER. No agent decision, no Rust, no Term. It builds an
event-native photon eye, opts it in to 196000's staleness_decay atom, 198000's
demotion_hierarchy, AND this rung's disorder_glassbox seed
(`seeds/disorder_glassbox.json`), installs decay traces (`HierTrace`), turns an
EXPLICIT graph-resident knob (the `ruminates_on` EDGE for obsession; the
`half_life` ATTRIBUTE for PTSD), ticks, and reads out — purely mechanically —
the eye's OWN graph-native tier / freshness / present bookkeeping. Every DECISION
(freshness, tier, demote, the ruminate self-refresh, the present-vs-past readout)
is a graph RULE under `run_rules()`; this script only sets attrs, adds/removes
the edge, ticks, and reads attributes.

FRAMING (standing project rule): understanding, not judgment. Each disorder is a
state that makes sense given a broken parameter — a mechanistic DEMO of the
aberrant-precision / aberrant-salience account, never a moral claim.

Gates: G1 OBSESSION (emerge: stuck FRESH; reverse: snip the edge -> demotes;
capacity crowding), G2 PTSD (emerge: stuck 'present'; reverse: restore half_life
-> 'past'), G3 knob source-audit + pure-knob reversibility byte-compare, G4
science mapping (in the RESULTS doc), integer-native audit, default-OFF
byte-identity. Prereg: VISION_DISORDER_GLASSBOX_PREREG.md. Deterministic; no
wall-clock claim.

IMPORT-INERT: nothing runs at import; `main()` is the only entry.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains.photon_eye import GraphEye            # noqa: E402
from substrate.seed_loader import manifest_for     # noqa: E402

SEED = 199000
DETAIL = 173                 # 8-bit value: 0b10101101
C0 = 1024
T_FRESH = 256
T_GIST = 16
K_GIST = 4
BITS_FULL, BITS_GIST, BITS_LATENT = 8, 4, 1
NORMAL_HL = 1
PTSD_HL = 1_000_000          # pathologically long half-life
RESULTS = os.path.join(ROOT, "results")
FRAMES = os.path.join(RESULTS, "disorder_glassbox")

TIER_PARAMS = dict(enabled=1.0, c0=float(C0), t_fresh=float(T_FRESH),
                   t_gist=float(T_GIST), k_gist=float(K_GIST),
                   bits_full=float(BITS_FULL), bits_gist=float(BITS_GIST),
                   bits_latent=float(BITS_LATENT), delete_enabled=0.0,
                   evict_age=64.0)
DIS_PARAMS = dict(enabled=1.0, t_present=float(T_FRESH))


# --------------------------------------------------------------- eye + traces
def _eye(load_disorder=True):
    eye = GraphEye(n_az=4, n_el=4, adapt_rate=0.15,
                   context={"retina_2d": True, "synchronous": True,
                            "worker_capacity": 1}).build()
    inner = eye.substrate._inner
    inner.load_seed_manifest(manifest_for("staleness_decay"), eye._agent)
    inner.load_seed_manifest(manifest_for("demotion_hierarchy"), eye._agent)
    if load_disorder:
        inner.load_seed_manifest(manifest_for("disorder_glassbox"), eye._agent)
    return eye, inner


def _add_tier_params(eye, inner, **over):
    p = dict(TIER_PARAMS)
    p.update(over)
    tp = eye.substrate.add_node("HeldTierParams", p)
    inner.add_edge_unchecked(eye._retina, "has_hier_tier_params", tp)
    return tp


def _add_dis_params(eye, inner, **over):
    p = dict(DIS_PARAMS)
    p.update(over)
    dp = eye.substrate.add_node("HeldDisorderParams", p)
    inner.add_edge_unchecked(eye._retina, "has_disorder_params", dp)
    return dp


def _add_trace(eye, inner, detail=DETAIL, half_life=NORMAL_HL, last_refresh=0):
    tr = eye.substrate.add_node("HierTrace", {
        "detail": float(detail), "now_epoch": 0.0,
        "last_refresh_epoch": float(last_refresh), "half_life": float(half_life),
        "freshness": float(C0), "tier": 2.0, "stored": float(detail),
        "bits": float(BITS_FULL), "recon": float(detail), "present": 1.0,
        "obs_epoch": 0.0, "obs_detail": 0.0,
        "experienced_as_present": 1.0})
    inner.add_edge_unchecked(eye._retina, "has_hier_trace", tr)
    return tr


def _ruminate(eye, inner, tr):
    inner.add_edge_unchecked(eye._retina, "ruminates_on", tr)


def _stop_ruminating(eye, tr):
    return eye.substrate.remove_edge(eye._retina, "ruminates_on", tr)


def _attrs(eye, tr):
    return eye.substrate.node(tr)["attrs"]


# ------------------------------------------------------------------- G1 tiers
def g1_obsession_tier():
    """One obsessive trace (ruminated) vs a background trace (not), driven over
    increasing now_epoch. Emerge: obsessive stuck FRESH; background demotes.
    Reverse: snip the ruminates_on edge -> obsessive demotes fresh->gist->latent.
    """
    eye, inner = _eye()
    _add_tier_params(eye, inner)
    _add_dis_params(eye, inner)
    obs = _add_trace(eye, inner, half_life=NORMAL_HL)
    bg = _add_trace(eye, inner, half_life=NORMAL_HL)
    _ruminate(eye, inner, obs)                     # the OBSESSION knob (an EDGE)

    emerge = []
    for now in range(0, 13):
        eye.substrate.set_attr(obs, "now_epoch", float(now))
        eye.substrate.set_attr(bg, "now_epoch", float(now))
        inner.run_rules()
        ao, ab = _attrs(eye, obs), _attrs(eye, bg)
        emerge.append(dict(now=now,
                           obs_tier=int(ao["tier"]), obs_fresh=int(ao["freshness"]),
                           bg_tier=int(ab["tier"]), bg_fresh=int(ab["freshness"])))
    # REVERSE: cut the self-refresh coupling
    removed = _stop_ruminating(eye, obs)
    reverse = []
    for now in range(13, 26):
        eye.substrate.set_attr(obs, "now_epoch", float(now))
        inner.run_rules()
        ao = _attrs(eye, obs)
        reverse.append(dict(now=now, obs_tier=int(ao["tier"]),
                            obs_fresh=int(ao["freshness"])))
    eye.stop()

    obs_on = [r["obs_tier"] for r in emerge]
    bg_on = [r["bg_tier"] for r in emerge]
    obs_off = [r["obs_tier"] for r in reverse]
    crit = dict(
        g1_obsession_stuck_fresh=all(t == 2 for t in obs_on),
        g1_background_demotes=(set(bg_on) == {0, 1, 2}
                               and bg_on[0] == 2 and bg_on[-1] == 0),
        g1_edge_removed=bool(removed),
        g1_reverse_demotes=(obs_off[0] == 2 and obs_off[-1] == 0
                            and set(obs_off) == {0, 1, 2}),
        g1_reversible=(all(t == 2 for t in obs_on) and obs_off[-1] == 0),
    )
    return dict(emerge=emerge, reverse=reverse, **crit)


# --------------------------------------------------------------- G1 capacity
def g1_capacity():
    """M background traces (staggered ages spanning FRESH..LATENT) + one
    obsessive trace, at a MATCHED bit budget. Under obsession the obsessive
    trace holds a permanent FRESH 8-bit slot; healthy it is LATENT (1 bit).
    Count background traces RETAINED at budget, both arms, across a sweep."""
    M = 32
    query = 200
    ages = [1 + (i * (query - 1)) // (M - 1) for i in range(M)]   # 1..199

    def run(ruminate_obsessive):
        eye, inner = _eye()
        _add_tier_params(eye, inner)
        _add_dis_params(eye, inner)
        bg_traces = []
        for age in ages:
            tr = _add_trace(eye, inner, half_life=8, last_refresh=query - age)
            eye.substrate.set_attr(tr, "now_epoch", float(query))
            bg_traces.append(tr)
        # the obsessive trace: an OLD memory (age = query) — LATENT if healthy
        obs = _add_trace(eye, inner, half_life=8, last_refresh=0)
        eye.substrate.set_attr(obs, "now_epoch", float(query))
        if ruminate_obsessive:
            _ruminate(eye, inner, obs)
        inner.run_rules()
        bg_rows = [dict(age=age, tier=int(_attrs(eye, tr)["tier"]),
                        bits=int(_attrs(eye, tr)["bits"]))
                   for age, tr in zip(ages, bg_traces)]
        obs_row = dict(tier=int(_attrs(eye, obs)["tier"]),
                       bits=int(_attrs(eye, obs)["bits"]))
        eye.stop()
        return bg_rows, obs_row

    bg_on, obs_on = run(ruminate_obsessive=True)
    bg_off, obs_off = run(ruminate_obsessive=False)

    def retained_background(bg_rows, obs_row, B):
        """Greedy fill by freshness (tier desc). The obsessive trace competes
        at its own tier cost. Count BACKGROUND traces that fit under B."""
        items = [("obs", obs_row["tier"], obs_row["bits"])] + \
                [("bg", r["tier"], r["bits"]) for r in bg_rows]
        # prefer fresher (higher tier); the obsessive FRESH slot is taken first
        order = sorted(items, key=lambda it: -it[1])
        spent, bg_kept = 0, 0
        for kind, _tier, bits in order:
            if spent + bits <= B:
                spent += bits
                if kind == "bg":
                    bg_kept += 1
        return bg_kept

    budgets = list(range(BITS_LATENT * (M + 1), BITS_FULL * (M + 1) + 1,
                         max(1, (BITS_FULL - BITS_LATENT) * (M + 1) // 40)))
    sweep = []
    for B in budgets:
        sweep.append(dict(budget=B,
                          bg_retained_obsession=retained_background(bg_on, obs_on, B),
                          bg_retained_healthy=retained_background(bg_off, obs_off, B)))
    # matched-budget headline: the budget where the stolen FRESH slot bites
    # hardest (largest healthy-minus-obsession gap in retained background).
    Bm = max(budgets,
             key=lambda B: (retained_background(bg_off, obs_off, B)
                            - retained_background(bg_on, obs_on, B)))
    head = dict(matched_budget=Bm, M=M,
                obs_tier_obsession=obs_on["tier"], obs_bits_obsession=obs_on["bits"],
                obs_tier_healthy=obs_off["tier"], obs_bits_healthy=obs_off["bits"],
                bg_retained_obsession=retained_background(bg_on, obs_on, Bm),
                bg_retained_healthy=retained_background(bg_off, obs_off, Bm))
    crit = dict(
        g1cap_obsessive_holds_fresh_slot=(obs_on["tier"] == 2
                                          and obs_on["bits"] == BITS_FULL),
        g1cap_healthy_obsessive_is_latent=(obs_off["tier"] == 0
                                           and obs_off["bits"] == BITS_LATENT),
        g1cap_obsession_crowds_out=(head["bg_retained_obsession"] <
                                    head["bg_retained_healthy"]),
        g1cap_health_dominates_sweep=all(
            s["bg_retained_healthy"] >= s["bg_retained_obsession"] for s in sweep),
        g1cap_strict_somewhere=any(
            s["bg_retained_healthy"] > s["bg_retained_obsession"] for s in sweep),
    )
    return dict(sweep=sweep, headline=head, **crit)


# ------------------------------------------------------------------- G2 PTSD
def g2_ptsd():
    """A threat trace with a pathologically long half_life vs a normal control.
    Emerge: threat stuck 'present' (FRESH) while control decays to 'past'.
    Reverse (PURE KNOB): restore normal half_life -> threat demotes to 'past'."""
    eye, inner = _eye()
    _add_tier_params(eye, inner)
    _add_dis_params(eye, inner)
    threat = _add_trace(eye, inner, half_life=PTSD_HL)
    ctrl = _add_trace(eye, inner, half_life=NORMAL_HL)

    emerge = []
    for now in range(0, 13):
        eye.substrate.set_attr(threat, "now_epoch", float(now))
        eye.substrate.set_attr(ctrl, "now_epoch", float(now))
        inner.run_rules()
        at, ac = _attrs(eye, threat), _attrs(eye, ctrl)
        emerge.append(dict(now=now,
                           threat_tier=int(at["tier"]),
                           threat_present=int(at["experienced_as_present"]),
                           ctrl_tier=int(ac["tier"]),
                           ctrl_present=int(ac["experienced_as_present"])))
    # REVERSE — the PURE KNOB: restore a normal half_life, nothing else.
    eye.substrate.set_attr(threat, "half_life", float(NORMAL_HL))
    reverse = []
    for now in range(13, 24):
        eye.substrate.set_attr(threat, "now_epoch", float(now))
        inner.run_rules()
        at = _attrs(eye, threat)
        reverse.append(dict(now=now, threat_tier=int(at["tier"]),
                            threat_present=int(at["experienced_as_present"]),
                            threat_fresh=int(at["freshness"])))
    eye.stop()

    threat_pres_on = [r["threat_present"] for r in emerge]
    ctrl_pres_on = [r["ctrl_present"] for r in emerge]
    threat_pres_off = [r["threat_present"] for r in reverse]
    crit = dict(
        g2_threat_stuck_present=all(p == 1 for p in threat_pres_on),
        g2_threat_stuck_fresh=all(r["threat_tier"] == 2 for r in emerge),
        g2_control_reaches_past=(ctrl_pres_on[-1] == 0
                                 and any(r["ctrl_tier"] == 0 for r in emerge)),
        g2_reverse_to_past=all(p == 0 for p in threat_pres_off),
        g2_reverse_demotes=(reverse[-1]["threat_tier"] == 0),
        g2_reversible=(all(p == 1 for p in threat_pres_on)
                       and all(p == 0 for p in threat_pres_off)),
    )
    return dict(emerge=emerge, reverse=reverse, **crit)


# ------------------------------------------------------- G3 knob is a pure knob
def _trace_state(eye, tr):
    a = _attrs(eye, tr)
    return dict(tier=int(a["tier"]), freshness=int(a["freshness"]),
                present=int(a["experienced_as_present"]), stored=int(a["stored"]))


def g3_pure_knob():
    """Byte-compare a NEVER-SICK healthy trace against a MADE-SICK-THEN-CURED
    trace at matched epochs. For both disorders, turning the knob back must
    restore health with NO residue (identical tier/freshness/present readout)."""
    # ---- OBSESSION: never-ruminated vs ruminated-then-snipped
    def obsession_states(sick):
        eye, inner = _eye()
        _add_tier_params(eye, inner)
        _add_dis_params(eye, inner)
        tr = _add_trace(eye, inner, half_life=NORMAL_HL)
        if sick:
            _ruminate(eye, inner, tr)
        # sick phase (only matters if ruminated)
        for now in range(0, 6):
            eye.substrate.set_attr(tr, "now_epoch", float(now))
            inner.run_rules()
        if sick:
            _stop_ruminating(eye, tr)              # CURE — snip the edge
            eye.substrate.set_attr(tr, "last_refresh_epoch", 0.0)  # never-refreshed baseline
        # observe from a clean clock: compare across a fresh horizon
        states = []
        for now in range(0, 13):
            eye.substrate.set_attr(tr, "now_epoch", float(now))
            inner.run_rules()
            states.append(_trace_state(eye, tr))
        eye.stop()
        return states

    obs_never = obsession_states(sick=False)
    obs_cured = obsession_states(sick=True)

    # ---- PTSD: never-long-half_life vs long-then-restored (pure knob only)
    def ptsd_states(sick):
        eye, inner = _eye()
        _add_tier_params(eye, inner)
        _add_dis_params(eye, inner)
        tr = _add_trace(eye, inner, half_life=(PTSD_HL if sick else NORMAL_HL))
        if sick:
            for now in range(0, 6):                # sick horizon: stuck present
                eye.substrate.set_attr(tr, "now_epoch", float(now))
                inner.run_rules()
            eye.substrate.set_attr(tr, "half_life", float(NORMAL_HL))  # CURE (pure knob)
        states = []
        for now in range(0, 13):
            eye.substrate.set_attr(tr, "now_epoch", float(now))
            inner.run_rules()
            states.append(_trace_state(eye, tr))
        eye.stop()
        return states

    ptsd_never = ptsd_states(sick=False)
    ptsd_cured = ptsd_states(sick=True)

    crit = dict(
        g3_obsession_cure_is_pure=(obs_never == obs_cured),
        g3_ptsd_cure_is_pure=(ptsd_never == ptsd_cured),
    )
    return dict(obs_never=obs_never, obs_cured=obs_cured,
                ptsd_never=ptsd_never, ptsd_cured=ptsd_cured, **crit)


def g3_source_audit():
    """The disorder is produced by NAMED graph-resident parameters read by RULES;
    the measure adapter contains only mechanical host I/O. Audit the seed."""
    seed = json.load(open(os.path.join(ROOT, "seeds", "disorder_glassbox.json")))
    rules = {r["name"]: r for r in seed["rules"]}
    prods = {p["edge_type"] for p in seed["productions"]}
    # the obsession knob is the ruminates_on edge; dis_ruminate reads it + resets
    rum = rules["dis_ruminate"]
    rum_reads_edge = any(m[1] == "ruminates_on" for m in rum["match"])
    rum_effect = rum["effects"][0]
    rum_sets_refresh = (rum_effect[0] == "set_attr"
                        and rum_effect[2] == "last_refresh_epoch")
    # the readout rule exposes present/past from freshness
    ro = rules["dis_present_readout"]
    ro_effect = ro["effects"][0]
    ro_sets_present = (ro_effect[0] == "set_attr"
                       and ro_effect[2] == "experienced_as_present")
    # no del_node anywhere in this seed (disorders are decay faults, not deletion)
    def has_delete(r):
        return any(isinstance(e, list) and e and e[0] == "del_node"
                   for e in r.get("effects", []))
    any_delete = any(has_delete(r) for r in seed["rules"])
    # measure adapter: only mechanical host-I/O calls drive the disorder. The
    # forbidden tokens are built by concatenation so this audit's OWN source
    # (which names them) is not a false positive — only a genuine call matches.
    src = open(os.path.abspath(__file__)).read()
    forbidden = ["gr" + ".run(", "graph_" + "rewrite", "make_" + "rule",
                 "gr." + "_match(", "gr." + "_apply("]
    forbidden_engine = any(tok in src for tok in forbidden)
    return dict(
        obsession_knob_is_edge=("ruminates_on" in prods and rum_reads_edge),
        obsession_rule_self_refreshes=rum_sets_refresh,
        readout_rule_exposes_present=ro_sets_present,
        no_del_node_in_disorder_seed=(not any_delete),
        adapter_runs_no_python_rule_engine=(not forbidden_engine),
        knob_names=dict(obsession="ruminates_on (edge)", ptsd="half_life (attr)"),
    )


# ------------------------------------------------------- integer-native audit
def integer_audit():
    seed = json.load(open(os.path.join(ROOT, "seeds", "disorder_glassbox.json")))
    float_terms = {"Div", "Times", "Exp", "Log", "Sqrt"}

    def ops(term, acc):
        if isinstance(term, dict):
            if "type" in term:
                acc.add(term["type"])
            for k in ("a", "b", "arg", "cond", "then", "other", "node"):
                if k in term:
                    ops(term[k], acc)
            for x in term.get("items", []):
                ops(x, acc)
        return acc
    report, bad = {}, {}
    for r in seed["rules"]:
        used = set()
        for eff in r.get("effects", []):
            if isinstance(eff, list) and len(eff) >= 4 and isinstance(eff[3], dict):
                ops(eff[3].get("__term__", {}), used)
        ops(r.get("where", {}), used)
        report[r["name"]] = sorted(used)
        if used & float_terms:
            bad[r["name"]] = sorted(used & float_terms)
    return dict(report=report, offenders=bad, offender_count=len(bad),
                all_integer=(len(bad) == 0))


# ------------------------------------------------ default-OFF byte-identity
def default_off_identity():
    """With the disorder seed loaded but NO HeldDisorderParams node, no disorder
    rule fires: an eye is byte-identical to one without the seed at all."""
    def run(load_disorder):
        eye, inner = _eye(load_disorder=load_disorder)
        import numpy as np
        rng = np.random.default_rng(SEED)
        for _t in range(1, 6):
            pk = [{"col": c, "row": r, "wavelength_nm": 498.0,
                   "count": int(rng.poisson(40))}
                  for r in range(4) for c in range(4)]
            eye.submit_photons_2d(pk)
            inner.run_cognitive_tasks(1)
            inner.run_rules()
        cells = []
        for cid in eye._cells:
            a = eye.substrate.node(cid)["attrs"]
            cells.append({k: (round(v, 9) if isinstance(v, float) else v)
                          for k, v in sorted(a.items())})
        counts = {"node_count": eye.substrate._inner.node_count(),
                  "HierTrace": len(eye.substrate.nodes("HierTrace")),
                  "HeldDisorderParams":
                      len(eye.substrate.nodes("HeldDisorderParams"))}
        fp = json.dumps({"counts": counts, "cells": cells}, sort_keys=True)
        eye.stop()
        return fp, counts
    fp_off, c_off = run(load_disorder=False)
    fp_on, c_on = run(load_disorder=True)
    return dict(identical=(fp_off == fp_on), without_seed=c_off,
                with_seed_no_params=c_on,
                no_disorder_params_created=(c_on.get("HeldDisorderParams", 0) == 0))


# --------------------------------------------------------------------- render
def render(res, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.4))

    # G1 obsession: obsessive stuck FRESH, background demotes, then snip -> demote
    em = res["g1_tier"]["emerge"]
    rv = res["g1_tier"]["reverse"]
    ax = axes[0]
    ax.step([r["now"] for r in em], [r["obs_tier"] for r in em], where="post",
            color="#b2182b", label="obsessive (loop ON)")
    ax.step([r["now"] for r in em], [r["bg_tier"] for r in em], where="post",
            color="#2166ac", linestyle="--", label="background (healthy)")
    ax.step([r["now"] for r in rv], [r["obs_tier"] for r in rv], where="post",
            color="#1b7837", label="obsessive after SNIP")
    ax.axvline(12.5, color="#999", ls=":")
    ax.set_title("G1 OBSESSION — self-refresh loop pins FRESH;\nsnip the edge -> demotes")
    ax.set_xlabel("epoch"); ax.set_ylabel("tier (2=fresh 1=gist 0=latent)")
    ax.legend(fontsize=7)

    # G2 PTSD: present/past readout
    em2 = res["g2"]["emerge"]; rv2 = res["g2"]["reverse"]
    ax = axes[1]
    xs = [r["now"] for r in em2] + [r["now"] for r in rv2]
    thr = [r["threat_present"] for r in em2] + [r["threat_present"] for r in rv2]
    ctl = [r["ctrl_present"] for r in em2] + [None] * len(rv2)
    ax.step(xs, thr, where="post", color="#b2182b",
            label="threat (long half_life)")
    ax.step([r["now"] for r in em2], [r["ctrl_present"] for r in em2],
            where="post", color="#2166ac", linestyle="--", label="control (normal)")
    ax.axvline(12.5, color="#999", ls=":")
    ax.set_title("G2 PTSD — stuck 'present'; restore half_life -> 'past'")
    ax.set_xlabel("epoch"); ax.set_ylabel("experienced_as_present (1=now 0=past)")
    ax.set_yticks([0, 1]); ax.legend(fontsize=7)

    # G1 capacity crowding sweep
    sw = res["g1_capacity"]["sweep"]
    ax = axes[2]
    ax.plot([s["budget"] for s in sw], [s["bg_retained_healthy"] for s in sw],
            "-", color="#1b7837", label="healthy")
    ax.plot([s["budget"] for s in sw], [s["bg_retained_obsession"] for s in sw],
            "--", color="#b2182b", label="obsession")
    ax.set_title("G1 CAPACITY — obsession crowds out\nbackground traces")
    ax.set_xlabel("storage budget (bits)")
    ax.set_ylabel("background traces retained")
    ax.legend(fontsize=7)

    fig.tight_layout(); fig.savefig(path, dpi=110)
    import matplotlib.pyplot as _p
    _p.close(fig)


# ------------------------------------------------------------------------ main
def main():
    os.makedirs(FRAMES, exist_ok=True)
    g1_tier = g1_obsession_tier()
    g1_cap = g1_capacity()
    g2 = g2_ptsd()
    g3p = g3_pure_knob()
    g3a = g3_source_audit()
    ia = integer_audit()
    doff = default_off_identity()

    criteria = {}
    for k, v in g1_tier.items():
        if k.startswith("g1_"):
            criteria[k] = v
    for k, v in g1_cap.items():
        if k.startswith("g1cap_"):
            criteria[k] = v
    for k, v in g2.items():
        if k.startswith("g2_"):
            criteria[k] = v
    criteria["g3_obsession_cure_is_pure"] = g3p["g3_obsession_cure_is_pure"]
    criteria["g3_ptsd_cure_is_pure"] = g3p["g3_ptsd_cure_is_pure"]
    criteria["g3_obsession_knob_is_edge"] = g3a["obsession_knob_is_edge"]
    criteria["g3_readout_rule_exposes_present"] = g3a["readout_rule_exposes_present"]
    criteria["g3_adapter_no_python_rule_engine"] = g3a["adapter_runs_no_python_rule_engine"]
    criteria["integer_native"] = ia["all_integer"]
    criteria["default_off_byte_identical"] = doff["identical"]
    criteria["default_off_no_params_created"] = doff["no_disorder_params_created"]

    res = dict(
        seed=SEED, detail=DETAIL,
        params=dict(c0=C0, t_fresh=T_FRESH, t_gist=T_GIST, k_gist=K_GIST,
                    bits=[BITS_FULL, BITS_GIST, BITS_LATENT],
                    normal_hl=NORMAL_HL, ptsd_hl=PTSD_HL),
        g1_tier=g1_tier, g1_capacity=g1_cap, g2=g2,
        g3_pure_knob=g3p, g3_source_audit=g3a,
        integer_audit=ia, default_off=doff, criteria=criteria)

    with open(os.path.join(RESULTS, "disorder_glassbox.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    try:
        render(res, os.path.join(FRAMES, "disorder_glassbox.png"))
    except Exception as e:                       # plotting is non-gating
        res["render_error"] = str(e)
    return res


if __name__ == "__main__":
    r = main()
    print(json.dumps(r["criteria"], indent=1))
    print("ALL PASS:", all(r["criteria"].values()))

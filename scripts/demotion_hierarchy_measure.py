#!/usr/bin/env python3
"""THE DEMOTION HIERARCHY — decay DEMOTES, it does not DELETE (seed block 198000).

MECHANICAL MEASURE-ADAPTER. No agent decision, no Rust, no Term. It builds an
event-native photon eye, opts it in to 196000's staleness_decay atom AND this
rung's demotion_hierarchy seed (`seeds/demotion_hierarchy.json`), installs decay
traces (`HierTrace`), ticks, and reads out — purely mechanically — the eye's OWN
graph-native tier / stored / bits / present bookkeeping. Every DECISION
(freshness, tier, demote coarsening, promote-on-refresh, the separate delete
faculty) is a graph RULE under `run_rules()`; this script only sets epoch/obs
attributes, ticks, and reads attributes.

Gates: G1 demotion (freshness->0 leaves LATENT, not deletion), G2 promote-on-
refresh reversibility, G3 order-N-deletion separateness + the delete-on-decay
falsifier, G4 capacity payoff at matched budget vs a flat keep-or-delete
baseline, integer-native audit, default-OFF byte-identity. Prereg:
VISION_DEMOTION_HIERARCHY_PREREG.md. Deterministic; no wall-clock claim.

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

SEED = 198000
DETAIL = 173                 # 8-bit value: 0b10101101
C0 = 1024
T_FRESH = 256
T_GIST = 16
K_GIST = 4
BITS_FULL, BITS_GIST, BITS_LATENT = 8, 4, 1
RESULTS = os.path.join(ROOT, "results")
FRAMES = os.path.join(RESULTS, "demotion_hierarchy")

PARAMS = dict(enabled=1.0, c0=float(C0), t_fresh=float(T_FRESH),
              t_gist=float(T_GIST), k_gist=float(K_GIST),
              bits_full=float(BITS_FULL), bits_gist=float(BITS_GIST),
              bits_latent=float(BITS_LATENT), delete_enabled=0.0,
              evict_age=64.0)


# --------------------------------------------------------------- eye + traces
def _eye():
    eye = GraphEye(n_az=4, n_el=4, adapt_rate=0.15,
                   context={"retina_2d": True, "synchronous": True,
                            "worker_capacity": 1}).build()
    inner = eye.substrate._inner
    inner.load_seed_manifest(manifest_for("staleness_decay"), eye._agent)
    inner.load_seed_manifest(manifest_for("demotion_hierarchy"), eye._agent)
    return eye, inner


def _add_params(eye, inner, **over):
    p = dict(PARAMS)
    p.update(over)
    tp = eye.substrate.add_node("HeldTierParams", p)
    inner.add_edge_unchecked(eye._retina, "has_hier_tier_params", tp)
    return tp


def _add_trace(eye, inner, detail=DETAIL, half_life=1, last_refresh=0):
    tr = eye.substrate.add_node("HierTrace", {
        "detail": float(detail), "now_epoch": 0.0,
        "last_refresh_epoch": float(last_refresh), "half_life": float(half_life),
        "freshness": float(C0), "tier": 2.0, "stored": float(detail),
        "bits": float(BITS_FULL), "recon": float(detail), "present": 1.0,
        "obs_epoch": 0.0, "obs_detail": 0.0})
    inner.add_edge_unchecked(eye._retina, "has_hier_trace", tr)
    return tr


def _attrs(eye, tr):
    return eye.substrate.node(tr)["attrs"]


def _exists(eye, tr):
    try:
        _attrs(eye, tr)
        return True
    except BaseException:
        return False


# ------------------------------------------------------------------------ G1
def g1_demotion():
    """One trace, never refreshed, over increasing epoch. Tier steps down,
    representation coarsens, freshness->0 leaves LATENT (present, node exists)."""
    eye, inner = _eye()
    _add_params(eye, inner)
    tr = _add_trace(eye, inner, half_life=1)
    curve = []
    for now in range(0, 13):
        eye.substrate.set_attr(tr, "now_epoch", float(now))
        inner.run_rules()
        a = _attrs(eye, tr)
        tier = int(a["tier"])
        stored = int(a["stored"])
        recon = int(a["recon"])
        # in-frame reconstruction error where a value is defined
        recon_err = None if tier == 0 else abs(DETAIL - recon)
        curve.append(dict(now=now, freshness=int(a["freshness"]), tier=tier,
                          stored=stored, bits=int(a["bits"]), recon=recon,
                          recon_err=recon_err, present=int(a["present"]),
                          exists=_exists(eye, tr)))
    eye.stop()
    tiers = [r["tier"] for r in curve]
    bits = [r["bits"] for r in curve]
    # freshness->0 point: present + exists, NOT deleted
    zero = [r for r in curve if r["freshness"] == 0]
    crit = dict(
        g1_tier_monotone_down=all(tiers[i] >= tiers[i + 1]
                                  for i in range(len(tiers) - 1)),
        g1_reaches_all_tiers=(set(tiers) == {0, 1, 2}),
        g1_bits_shed=(bits[0] == BITS_FULL and BITS_GIST in bits
                      and bits[-1] == BITS_LATENT),
        g1_coarsens=(  # fresh exact, gist lossy-but-nonzero recon, latent marker
            any(r["tier"] == 2 and r["recon_err"] == 0 for r in curve)
            and any(r["tier"] == 1 and 0 < r["recon_err"] <= (2 ** K_GIST - 1)
                    for r in curve)),
        g1_zero_is_latent_not_deleted=bool(
            zero and all(r["present"] == 1 and r["exists"]
                         and r["tier"] == 0 and r["stored"] == 0 for r in zero)),
    )
    return curve, crit


# ------------------------------------------------------------------------ G2
def g2_promote():
    """Decay to LATENT, then re-observe -> promotes to FRESH, recovers detail."""
    eye, inner = _eye()
    _add_params(eye, inner)
    tr = _add_trace(eye, inner, half_life=1)
    cycle = []
    for now in range(0, 11):          # decay to latent
        eye.substrate.set_attr(tr, "now_epoch", float(now))
        inner.run_rules()
        a = _attrs(eye, tr)
        cycle.append(dict(now=now, phase="decay", tier=int(a["tier"]),
                          stored=int(a["stored"]), recon=int(a["recon"])))
    bottom = _attrs(eye, tr)
    # re-observe with the true detail at a later epoch (DRAM refresh / recall)
    eye.substrate.set_attr(tr, "now_epoch", 20.0)
    eye.substrate.set_attr(tr, "obs_epoch", 20.0)
    eye.substrate.set_attr(tr, "obs_detail", float(DETAIL))
    inner.run_rules()
    top = _attrs(eye, tr)
    cycle.append(dict(now=20, phase="promote", tier=int(top["tier"]),
                      stored=int(top["stored"]), recon=int(top["recon"])))
    eye.stop()
    crit = dict(
        g2_demoted_to_latent=(int(bottom["tier"]) == 0 and int(bottom["stored"]) == 0),
        g2_promoted_to_fresh=(int(top["tier"]) == 2),
        g2_detail_recovered=(int(top["stored"]) == DETAIL
                             and int(top["recon"]) == DETAIL),
        g2_freshness_reset=(int(top["freshness"] if "freshness" in top else
                                _fresh(top)) == C0),
    )
    return cycle, crit, dict(bottom_tier=int(bottom["tier"]),
                             top_tier=int(top["tier"]),
                             recovered=int(top["stored"]))


def _fresh(a):
    return int(a.get("freshness", 0))


# ------------------------------------------------------------------------ G3
def _effect_ops(rule):
    """Collect effect verbs (set_attr / del_node / ...) used by a rule."""
    verbs = []
    for eff in rule.get("effects", []):
        if isinstance(eff, list) and eff:
            verbs.append(eff[0])
    return verbs


def g3_separateness():
    """(a) source-audit: only dh_delete_latent contains del_node, gated at the
    LATENT tier behind its own delete_enabled flag; the decay/demote atom has
    none. (b) delete-on-decay FALSIFIER diverges."""
    seed = json.load(open(os.path.join(ROOT, "seeds", "demotion_hierarchy.json")))
    rules = {r["name"]: r for r in seed["rules"]}
    atom = ["dh_freshness", "dh_tier", "dh_demote", "dh_promote"]
    atom_has_delete = {n: ("del_node" in _effect_ops(rules[n])) for n in atom}
    del_rule = rules["dh_delete_latent"]
    del_where = json.dumps(del_rule["where"])
    audit = dict(
        atom_rules=atom,
        atom_has_delete=atom_has_delete,
        only_delete_rule="dh_delete_latent",
        delete_rule_has_del_node=("del_node" in _effect_ops(del_rule)),
        delete_gated_on_flag=("delete_enabled" in del_where),
        delete_gated_at_latent=('"value": 0.0' in del_where
                                and '"tier"' in del_where),
        delete_rule_order=del_rule.get("order"),
    )
    crit_a = dict(
        g3a_atom_has_no_delete=(not any(atom_has_delete.values())),
        g3a_only_delete_faculty_deletes=audit["delete_rule_has_del_node"],
        g3a_delete_gated_flag_and_latent=(audit["delete_gated_on_flag"]
                                          and audit["delete_gated_at_latent"]),
    )

    # (b) FALSIFIER — an ALTERNATE demote atom that wires deletion INTO decay:
    # freshness->0 (tier==0) => del_node, order 4, gated ONLY on enabled (no
    # separate flag, no age). Same decay->re-observe scenario under both.
    def recovered_under(variant):
        eye, inner = _eye()
        if variant == "falsifier":
            inner.load_seed_manifest(_delete_on_decay_manifest(), eye._agent)
        _add_params(eye, inner)
        tr = _add_trace(eye, inner, half_life=1)
        for now in range(0, 11):
            eye.substrate.set_attr(tr, "now_epoch", float(now))
            inner.run_rules()
            if not _exists(eye, tr):
                break
        gone = not _exists(eye, tr)
        recovered = None
        n_after = len(eye.substrate.nodes("HierTrace"))
        if not gone:
            eye.substrate.set_attr(tr, "now_epoch", 20.0)
            eye.substrate.set_attr(tr, "obs_epoch", 20.0)
            eye.substrate.set_attr(tr, "obs_detail", float(DETAIL))
            inner.run_rules()
            recovered = int(_attrs(eye, tr)["stored"])
        eye.stop()
        return dict(gone_before_reobserve=gone, hiertrace_count=n_after,
                    recovered_detail=recovered)

    hierarchy = recovered_under("hierarchy")
    falsifier = recovered_under("falsifier")
    crit_b = dict(
        g3b_hierarchy_promotes=(hierarchy["recovered_detail"] == DETAIL
                                and not hierarchy["gone_before_reobserve"]),
        g3b_falsifier_loses_trace=(falsifier["gone_before_reobserve"]
                                   and falsifier["recovered_detail"] is None),
        g3b_diverges=(hierarchy["recovered_detail"] == DETAIL
                      and falsifier["recovered_detail"] is None),
    )
    return dict(audit=audit, hierarchy=hierarchy, falsifier=falsifier,
                **crit_a, **crit_b)


def _delete_on_decay_manifest():
    """The falsifier: deletion wired INTO the decay atom (NOT how the real seed
    is built). A rule at order 4, gated only on enabled, del_node when tier==0."""
    return {
        "id": "demotion_hierarchy_FALSIFIER", "version": "0.0.0",
        "self_load_only": True, "depends_on": [], "area": "retina",
        "nodes": [], "edges": [], "productions": [], "microtheory": {
            "name": "falsifier", "description": "delete-on-decay (falsifier)"},
        "rules": [{
            "name": "dh_demote_DELETE_ON_DECAY", "area": "retina", "order": 4,
            "latency_class": "hard_realtime",
            "match": [["retina", "has_hier_tier_params", "tp"],
                      ["retina", "has_hier_trace", "tr"]],
            "where": {"type": "And", "items": [
                {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var",
                 "name": "tp"}, "key": "enabled"}, "b": {"type": "Lit", "value": 1.0}},
                {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var",
                 "name": "tr"}, "key": "tier"}, "b": {"type": "Lit", "value": 0.0}},
            ]},
            "effects": [["del_node", "tr"]],
        }],
    }


# ------------------------------------------------------------------------ G4
def g4_payoff():
    """Population of M traces observed once at staggered epochs, queried at a
    common epoch. Graph-native tier/bits per trace. Budget sweep: hierarchy
    (demote-not-delete) vs flat keep-or-delete, at MATCHED total bit budget."""
    M = 64
    query = 200
    # staggered ages: even spread so tiers span FRESH..LATENT
    ages = [1 + (i * (query - 1)) // (M - 1) for i in range(M)]  # 1..199
    eye, inner = _eye()
    _add_params(eye, inner)
    traces = []
    for age in ages:
        tr = _add_trace(eye, inner, half_life=8, last_refresh=query - age)
        eye.substrate.set_attr(tr, "now_epoch", float(query))
        traces.append(tr)
    inner.run_rules()
    rows = []
    for age, tr in zip(ages, traces):
        a = _attrs(eye, tr)
        rows.append(dict(age=age, tier=int(a["tier"]), bits=int(a["bits"]),
                         recon=int(a["recon"])))
    eye.stop()

    # per-tier fidelity of a retrievable trace (fraction of detail recovered)
    def fidelity(row):
        if row["tier"] == 2:
            return 1.0
        if row["tier"] == 1:
            return 1.0 - abs(DETAIL - row["recon"]) / 255.0   # coarse recon
        return 0.0                                            # latent: presence only

    hier_full_bits = sum(r["bits"] for r in rows)             # all present
    # budget sweep from tiny to full-detail-for-all
    sweep = []
    budgets = list(range(BITS_LATENT * M, BITS_FULL * M + 1,
                         max(1, (BITS_FULL - BITS_LATENT) * M // 40)))
    # order traces by freshness (tier desc) — both schemes prefer fresher
    order = sorted(range(M), key=lambda i: (-rows[i]["tier"], rows[i]["age"]))
    for B in budgets:
        # FLAT: keep the k freshest at FULL detail; rest DELETED (unretrievable)
        k_flat = min(M, B // BITS_FULL)
        flat_retr = k_flat
        flat_recall = float(k_flat)                            # each full = 1.0
        # HIERARCHY: every trace present at its tier cost; if over B, evict from
        # the LATENT tier upward (drop cheapest-value first).
        spent = 0
        kept = []
        for i in order:
            c = rows[i]["bits"]
            if spent + c <= B:
                spent += c
                kept.append(i)
        # if budget too tight even for that, the greedy above already fit it
        hier_retr = len(kept)
        hier_recall = sum(fidelity(rows[i]) for i in kept)
        hier_promotable = hier_retr                            # all kept present
        sweep.append(dict(budget=B, flat_retrievable=flat_retr,
                          flat_recall=round(flat_recall, 3),
                          hier_retrievable=hier_retr,
                          hier_recall=round(hier_recall, 3),
                          hier_promotable=hier_promotable))

    # matched-budget headline: at B = hierarchy's natural footprint
    Bm = hier_full_bits
    k_flat_m = min(M, Bm // BITS_FULL)
    tier_hist = {t: sum(1 for r in rows if r["tier"] == t) for t in (2, 1, 0)}
    headline = dict(
        matched_budget=Bm, M=M,
        hier_retrievable=M, flat_retrievable=k_flat_m,
        # fidelity-weighted recall is REPORTED (not the pre-registered success
        # metric — retrievable/promotable content is). At matched budget flat
        # concentrates its bits into few FULL-detail copies, so fidelity-sum
        # ties/favours flat while the hierarchy retains 3.5x more PROMOTABLE
        # traces. The demotion payoff is CAPACITY + promotability, not
        # fidelity-sum; a flat scheme only wins fidelity when budget is
        # abundant enough that no hierarchy is needed (>= BITS_FULL*M).
        hier_recall_fidelity=round(sum(fidelity(r) for r in rows), 3),
        flat_recall_fidelity=float(k_flat_m),
        budget_flat_gets_all=BITS_FULL * M,
        budget_hier_gets_all=Bm,
        tier_histogram=tier_hist)
    crit = dict(
        g4_hier_retains_more=(headline["hier_retrievable"] >
                              headline["flat_retrievable"]),
        g4_dominates_across_sweep=all(
            s["hier_retrievable"] >= s["flat_retrievable"] for s in sweep),
        g4_strict_somewhere=any(
            s["hier_retrievable"] > s["flat_retrievable"] for s in sweep),
        # honest reported nuance (NOT gated): fidelity-sum tradeoff
        reported_fidelity_tie_or_flat=(headline["flat_recall_fidelity"] >=
                                       headline["hier_recall_fidelity"]),
    )
    return dict(rows=rows, sweep=sweep, headline=headline, **crit)


# ------------------------------------------------------- integer-native audit
def integer_audit():
    seed = json.load(open(os.path.join(ROOT, "seeds", "demotion_hierarchy.json")))
    float_terms = {"Div", "Times", "Exp", "Log", "Sqrt"}
    bookkeeping = {"dh_freshness", "dh_tier", "dh_demote", "dh_promote",
                   "dh_delete_latent"}

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
        # also audit the where-guard
        ops(r.get("where", {}), used)
        report[r["name"]] = sorted(used)
        if r["name"] in bookkeeping and (used & float_terms):
            bad[r["name"]] = sorted(used & float_terms)
    return dict(report=report, offenders=bad, offender_count=len(bad),
                all_integer=(len(bad) == 0))


# ------------------------------------------------ default-OFF byte-identity
def default_off_identity():
    """With the demotion seed loaded but NO HeldTierParams node, no rule fires:
    an eye is byte-identical to one without the seed at all."""
    def run(load_seed):
        eye = GraphEye(n_az=4, n_el=4, adapt_rate=0.15,
                       context={"retina_2d": True, "synchronous": True,
                                "worker_capacity": 1}).build()
        inner = eye.substrate._inner
        inner.load_seed_manifest(manifest_for("staleness_decay"), eye._agent)
        if load_seed:
            inner.load_seed_manifest(manifest_for("demotion_hierarchy"), eye._agent)
        # a plain held surface, no tier params at all
        import numpy as np
        rng = np.random.default_rng(SEED)
        for t in range(1, 6):
            pk = [{"col": c, "row": r, "wavelength_nm": 498.0,
                   "count": int(rng.poisson(40))}
                  for r in range(4) for c in range(4)]
            eye.submit_photons_2d(pk)
            inner.run_cognitive_tasks(1)
            inner.run_rules()
        # fingerprint: total node count + every RetinalColumn cell's full attrs
        # (a real byte-identity, not just a type tally). If the demotion rules
        # fired at all they would perturb the graph; they cannot without params.
        cells = []
        for cid in eye._cells:
            a = eye.substrate.node(cid)["attrs"]
            cells.append({k: (round(v, 9) if isinstance(v, float) else v)
                          for k, v in sorted(a.items())})
        counts = {"node_count": eye.substrate._inner.node_count(),
                  "HierTrace": len(eye.substrate.nodes("HierTrace")),
                  "HeldTierParams": len(eye.substrate.nodes("HeldTierParams"))}
        fp = json.dumps({"counts": counts, "cells": cells}, sort_keys=True)
        eye.stop()
        return fp, counts
    fp_off, c_off = run(load_seed=False)
    fp_on, c_on = run(load_seed=True)
    return dict(identical=(fp_off == fp_on), without_seed=c_off,
                with_seed_no_params=c_on,
                no_hiertrace_created=(c_on.get("HierTrace", 0) == 0))


# --------------------------------------------------------------------- render
def render(res, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.4))
    # G1 demotion curve
    c = res["g1_curve"]
    now = [r["now"] for r in c]
    ax = axes[0]
    ax.step(now, [r["tier"] for r in c], where="post", color="#2166ac",
            label="tier (2=fresh 1=gist 0=latent)")
    ax.step(now, [r["bits"] for r in c], where="post", color="#b2182b",
            linestyle="--", label="stored bits")
    ax.set_title("G1 DEMOTION — coarsen, never delete\n(freshness->0 = LATENT, present)")
    ax.set_xlabel("epochs since refresh"); ax.legend(fontsize=7)
    ax.set_ylim(bottom=-0.3)
    # G2 promote cycle
    cy = res["g2_cycle"]
    ax = axes[1]
    xs = list(range(len(cy)))
    ax.plot(xs, [r["tier"] for r in cy], "-o", ms=3, color="#2166ac", label="tier")
    ax.plot(xs, [r["recon"] for r in cy], "-s", ms=3, color="#762a83",
            label="reconstructed value")
    ax.axhline(DETAIL, color="#999", ls=":", label="true detail")
    ax.set_title("G2 PROMOTE-ON-REFRESH — demote->promote->recover")
    ax.set_xlabel("step (decay ... then re-observe)"); ax.legend(fontsize=7)
    # G4 payoff sweep
    sw = res["g4"]["sweep"]
    ax = axes[2]
    ax.plot([s["budget"] for s in sw], [s["hier_retrievable"] for s in sw],
            "-", color="#2166ac", label="hierarchy (demote)")
    ax.plot([s["budget"] for s in sw], [s["flat_retrievable"] for s in sw],
            "--", color="#b2182b", label="flat keep-or-delete")
    ax.set_title("G4 PAYOFF — retrievable traces vs storage budget")
    ax.set_xlabel("storage budget (bits)"); ax.set_ylabel("retrievable / promotable")
    ax.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(path, dpi=110)
    import matplotlib.pyplot as _p
    _p.close(fig)


# ------------------------------------------------------------------------ main
def main():
    os.makedirs(FRAMES, exist_ok=True)
    g1_curve, g1c = g1_demotion()
    g2_cycle, g2c, g2s = g2_promote()
    g3 = g3_separateness()
    g4 = g4_payoff()
    ia = integer_audit()
    doff = default_off_identity()

    criteria = {}
    criteria.update(g1c); criteria.update(g2c)
    for k in ("g3a_atom_has_no_delete", "g3a_only_delete_faculty_deletes",
              "g3a_delete_gated_flag_and_latent", "g3b_hierarchy_promotes",
              "g3b_falsifier_loses_trace", "g3b_diverges"):
        criteria[k] = g3[k]
    for k in ("g4_hier_retains_more", "g4_dominates_across_sweep",
              "g4_strict_somewhere"):
        criteria[k] = g4[k]
    criteria["integer_native"] = ia["all_integer"]
    criteria["default_off_byte_identical"] = doff["identical"]
    criteria["default_off_no_trace_created"] = doff["no_hiertrace_created"]

    res = dict(
        seed=SEED, detail=DETAIL,
        tiers=dict(c0=C0, t_fresh=T_FRESH, t_gist=T_GIST, k_gist=K_GIST,
                   bits_full=BITS_FULL, bits_gist=BITS_GIST, bits_latent=BITS_LATENT),
        g1_curve=g1_curve, g2_cycle=g2_cycle, g2_summary=g2s,
        g3=g3, g4=g4, integer_audit=ia, default_off=doff,
        criteria=criteria)

    with open(os.path.join(RESULTS, "demotion_hierarchy.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    try:
        render(res, os.path.join(FRAMES, "demotion_hierarchy.png"))
    except Exception as e:                       # plotting is non-gating
        res["render_error"] = str(e)
    return res


if __name__ == "__main__":
    r = main()
    print(json.dumps(r["criteria"], indent=1))

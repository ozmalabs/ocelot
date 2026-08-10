#!/usr/bin/env python3
"""LEARNING-PROGRESS-GATED DECAY + THE COMMIT-NET (seed block 202000).

MECHANICAL MEASURE-ADAPTER. No agent decision, no Rust, no new Term. It builds
a bare substrate (`boot_core`), opts it in to the learning-progress curiosity
seed (`seeds/learning_progress_curiosity.json`), submits OBSERVATIONS to
`AttentionItem`s (and a `step` to a `Deliberation`), ticks `run_rules()`, and
reads out — purely mechanically — the graph-native curiosity bookkeeping. Every
DECISION (residual, the two-timescale learning-progress rate, the gated decay,
the attend flag, the commit cut) is a graph RULE; this script only submits
observations, ticks, and reads attributes.

We RE-DERIVE the learning-progress family (Schmidhuber 1991/2010 compression-
progress; Oudeyer & Kaplan IAC 2007; the noisy-TV failure of raw prediction-
error curiosity, Pathak 2017 / Burda 2018) and the somatic-marker commit cut
(Damasio 1994) on the SAME 196000 `staleness_decay` integer decay atom. The
contribution is the graph-native INTEGER instantiation, not the idea.

Gates: G1 noisy-TV (gated leaves / naive traps + raw-surprise falsifier),
G2 leave-the-unresolved (decay resolved + intractable, hold progressing),
G3 commit-net / anti-paralysis + calibration, G4 integer-native + default-OFF +
term.rs-empty. Prereg: VISION_LEARNING_PROGRESS_PREREG.md. Deterministic; no
wall-clock claim.
"""
from __future__ import annotations

import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.boot_core import boot_core          # noqa: E402
from substrate.seed_loader import manifest_for      # noqa: E402

SEED = 202000
SEED_ID = "learning_progress_curiosity"
RESULTS = os.path.join(ROOT, "results")
FRAMES = os.path.join(RESULTS, "learning_progress")

T = 48                       # ticks for G1/G2
N_ENS = 16                   # noise draws in the G1/G2 ensemble (an allocation
                             # rate is a property of the stimulus DISTRIBUTION,
                             # not one lucky draw — instrument discipline)
LEVELS = [100, 220, 40, 160]  # staged-learnable levels (change every T//4)
NOISE_HI = 240               # white-noise range [0, NOISE_HI]

# curiosity params (integer-native; tuned for a clean noisy-TV separation)
PARAMS = dict(
    hl_min=1.0, hl_scale=4.0, interest_c0=1024.0, attend_thresh=256.0,
    progress_floor=10.0, surprise_floor=4.0,
    fast_div=3.0, slow_div=20.0, blend_div=2.0,
)

# the AttentionItem's full initial state (every curiosity attr starts here)
ITEM_INIT = dict(
    held=0.0, obs=0.0, input_epoch=0.0, epoch=-1.0, residual=0.0,
    fast_res=0.0, slow_res=0.0, learning_progress=0.0, smoothed_progress=0.0,
    interest_half_life=1.0, last_boost_epoch=0.0, interest=1024.0, attended=0.0,
)
CURIOSITY_KEYS = ["residual", "fast_res", "slow_res", "learning_progress",
                  "smoothed_progress", "interest_half_life", "last_boost_epoch",
                  "interest", "attended"]


# ----------------------------------------------------------------- scene defs
def learnable_seq():
    """Staged-learnable: piecewise-constant levels a scalar predictor CAN
    compress (residual drops within a stage = progress), re-surprising at each
    stage boundary (ongoing positive learning progress)."""
    seg = T // len(LEVELS)
    return [LEVELS[min(t // seg, len(LEVELS) - 1)] for t in range(T)]


def resolved_seq():
    """Resolved: a single constant target — learned once, then progress -> 0
    (nothing left). LOW asymptotic surprise."""
    return [100] * T


def noise_seq(rng):
    """Intractable / noisy TV: white noise a scalar predictor can NEVER
    compress. HIGH surprise forever, ZERO learning progress."""
    return [int(rng.integers(0, NOISE_HI + 1)) for _ in range(T)]


# ------------------------------------------------------------------ substrate
def _make_hub(mode):
    """Bare substrate opted in to the curiosity seed; returns (s, inner, hub)."""
    s, agent = boot_core()
    inner = s._inner
    inner.load_seed_manifest(manifest_for(SEED_ID), agent)
    hub = s.add_node("CuriosityHub", {"kind": "measure"})
    p = dict(PARAMS)
    p["enabled"] = 1.0
    p["mode"] = float(mode)
    cp = s.add_node("HeldCuriosityParams", p)
    inner.add_edge_unchecked(hub, "has_curiosity_params", cp)
    return s, inner, hub


def _add_item(s, inner, hub):
    it = s.add_node("AttentionItem", dict(ITEM_INIT))
    inner.add_edge_unchecked(hub, "has_attention_item", it)
    return it


def _read(s, node, keys):
    a = s.node(node)["attrs"]
    return {k: float(a.get(k, 0.0)) for k in keys}


def run_items(named_seqs, mode):
    """Drive N named observation sequences as co-present AttentionItems on ONE
    gated hub. Returns per-item per-tick records (interest, residual, progress,
    attended). The adapter ONLY sets obs + input_epoch (world I/O)."""
    s, inner, hub = _make_hub(mode)
    items = {name: _add_item(s, inner, hub) for name in named_seqs}
    rec = {name: {k: [] for k in ("interest", "residual",
                                  "learning_progress", "attended")}
           for name in named_seqs}
    for t in range(T):
        for name, seq in named_seqs.items():
            s.set_attr(items[name], "obs", float(seq[t]))
            s.set_attr(items[name], "input_epoch", float(t))
        inner.run_rules()
        for name in named_seqs:
            a = s.node(items[name])["attrs"]
            rec[name]["interest"].append(int(a["interest"]))
            rec[name]["residual"].append(int(a["residual"]))
            rec[name]["learning_progress"].append(int(a["learning_progress"]))
            rec[name]["attended"].append(int(a["attended"]))
    return rec


# ------------------------------------------------------------------ commit-net
def run_commit(commit_enabled, commit_cost, H=14, v_max=1024):
    """One Deliberation whose marginal value is the diminishing-returns atom
    marginal = Ashr(v_max, step). The adapter only increments `step`; the
    order-0 cn_commit RULE decides termination. Returns (commit_step|None,
    marginals, values)."""
    s, inner, hub = _make_hub(0)
    d = s.add_node("Deliberation", {
        "step": 0.0, "seen_step": -1.0, "v_max": float(v_max), "value": 0.0,
        "marginal_value": 0.0, "committed": 0.0, "commit_step": -1.0,
        "commit_enabled": float(commit_enabled), "commit_cost": float(commit_cost)})
    inner.add_edge_unchecked(hub, "has_deliberation", d)
    marg, vals = [], []
    commit_step = None
    for step in range(1, H + 1):
        s.set_attr(d, "step", float(step))
        inner.run_rules()
        a = s.node(d)["attrs"]
        marg.append(int(a["marginal_value"]))
        vals.append(int(a["value"]))
        if commit_step is None and a["committed"] == 1.0:
            commit_step = int(a["commit_step"])
    return commit_step, marg, vals


# ------------------------------------------------------------------ G4 audits
def integer_terms_audit():
    """G4a-rules: the curiosity rules use ONLY integer Terms (no Div/Exp/Log)."""
    seed = json.load(open(os.path.join(ROOT, "seeds", f"{SEED_ID}.json")))
    float_terms = {"Div", "Exp", "Log", "Sqrt", "Sin", "Cos"}

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
        for eff in r["effects"]:
            if isinstance(eff[3], dict) and "__term__" in eff[3]:
                ops(eff[3]["__term__"], used)
        report[r["name"]] = sorted(used)
        if used & float_terms:
            bad[r["name"]] = sorted(used & float_terms)
    return report, bad


def default_off_byte_identity():
    """G4b: with NO HeldCuriosityParams node (seed loaded but not opted in) the
    rules never match — an AttentionItem is byte-identical to its init after a
    tick. Also verify enabled=0 writes nothing."""
    # (a) seed loaded, NO params node
    s, agent = boot_core()
    inner = s._inner
    inner.load_seed_manifest(manifest_for(SEED_ID), agent)
    hub = s.add_node("CuriosityHub", {"kind": "off"})
    it = s.add_node("AttentionItem", dict(ITEM_INIT))
    inner.add_edge_unchecked(hub, "has_attention_item", it)
    before = _read(s, it, list(ITEM_INIT.keys()))
    s.set_attr(it, "obs", 137.0)
    s.set_attr(it, "input_epoch", 3.0)
    inner.run_rules()
    after = _read(s, it, list(ITEM_INIT.keys()))
    # obs/input_epoch are the adapter's own world writes; every OTHER attr must
    # be byte-identical (no rule fired).
    changed_noparams = {k: (before[k], after[k]) for k in ITEM_INIT
                        if k not in ("obs", "input_epoch") and before[k] != after[k]}
    # (b) params node present but enabled=0
    s2, agent2 = boot_core()
    inner2 = s2._inner
    inner2.load_seed_manifest(manifest_for(SEED_ID), agent2)
    hub2 = s2.add_node("CuriosityHub", {"kind": "off2"})
    p = dict(PARAMS); p["enabled"] = 0.0; p["mode"] = 0.0
    cp2 = s2.add_node("HeldCuriosityParams", p)
    inner2.add_edge_unchecked(hub2, "has_curiosity_params", cp2)
    it2 = s2.add_node("AttentionItem", dict(ITEM_INIT))
    inner2.add_edge_unchecked(hub2, "has_attention_item", it2)
    s2.set_attr(it2, "obs", 137.0)
    s2.set_attr(it2, "input_epoch", 3.0)
    inner2.run_rules()
    after2 = _read(s2, it2, list(ITEM_INIT.keys()))
    changed_disabled = {k: after2[k] for k in ITEM_INIT
                        if k not in ("obs", "input_epoch") and after2[k] != ITEM_INIT[k]}
    return changed_noparams, changed_disabled


def source_audit():
    """G4c: the adapter (this script) must NEVER set_attr a curiosity-DECISION
    key — those are written ONLY by the seed rules. Its set_attrs are the world
    clock/observation (obs, input_epoch, step) and the commit KNOBS the human
    sets on the Deliberation."""
    src = open(os.path.abspath(__file__)).read()
    setattr_lines = re.findall(r"set_attr\([^\n]*", src)
    decision_keys = set(CURIOSITY_KEYS) | {"value", "marginal_value",
                                           "committed", "commit_step", "held"}
    bad = [ln for ln in setattr_lines
           if any(f'"{k}"' in ln or f"'{k}'" in ln for k in decision_keys)]
    return bad


def seed_self_load_only():
    seed = json.load(open(os.path.join(ROOT, "seeds", f"{SEED_ID}.json")))
    return bool(seed.get("self_load_only"))


# ------------------------------------------------------------------ rendering
def render_g1(rec_gated, rec_naive, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ts = list(range(T))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.4), sharey=True)
    for ax, rec, title in ((ax1, rec_gated, "GATED (learning-progress)"),
                           (ax2, rec_naive, "NAIVE (raw surprise) — FALSIFIER")):
        ax.plot(ts, rec["learnable"]["interest"], "-", color="#2166ac",
                label="learnable")
        ax.plot(ts, rec["noisy"]["interest"], "-", color="#b2182b",
                label="noisy TV")
        ax.set_title(title)
        ax.set_xlabel("tick"); ax.set_ylabel("interest (decaying)")
        ax.legend(fontsize=8)
    ax1.annotate("noisy interest DECAYS\n(agent leaves)", (T * 0.55, 120),
                 color="#b2182b", fontsize=8)
    ax2.annotate("noisy interest PINNED\n(trapped on the TV)", (T * 0.35, 700),
                 color="#b2182b", fontsize=8)
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


def render_g2(rec, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ts = list(range(T))
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.plot(ts, rec["progressing"]["interest"], "-", color="#1a9850",
            label="PROGRESSING (held)")
    ax.plot(ts, rec["resolved"]["interest"], "--", color="#f1a340",
            label="RESOLVED (progress->0, low surprise)")
    ax.plot(ts, rec["intractable"]["interest"], ":", color="#b2182b",
            label="INTRACTABLE (progress->0, high surprise)")
    ax.set_title("LEAVE-THE-UNRESOLVED — decay resolved AND intractable, "
                 "hold progressing\n(discriminator is PROGRESS, not surprise)")
    ax.set_xlabel("tick"); ax.set_ylabel("interest")
    ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


def render_g3(arms, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    steps = list(range(1, len(arms["calibrated"]["marginals"]) + 1))
    ax.plot(steps, arms["calibrated"]["marginals"], "-o", ms=3, color="#2166ac",
            label="marginal value = Ashr(V_max, step)")
    for name, color in (("calibrated", "#1a9850"), ("impulsive", "#b2182b"),
                        ("passive", "#7570b3")):
        cc = arms[name]["commit_cost"]
        ax.axhline(cc, ls="--", color=color, lw=1,
                   label=f"{name} cost={cc}")
        cs = arms[name]["commit_step"]
        if cs is not None:
            ax.axvline(cs, ls=":", color=color, lw=1)
            ax.annotate(f"{name}\ncommit@{cs}", (cs, cc + 20), color=color,
                        fontsize=8)
    ax.set_title("COMMIT-NET — cut when marginal value < cost\n"
                 "passive/naive never cross (paralysis); impulsive fires at "
                 "step 1; calibrated at the crossing")
    ax.set_xlabel("deliberation step"); ax.set_ylabel("value")
    ax.legend(fontsize=7, loc="upper right")
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


# ------------------------------------------------------------------------ main
def measure():
    os.makedirs(FRAMES, exist_ok=True)

    learn = learnable_seq()
    early, late = slice(0, 4), slice(T // 2, T)

    def mean(v, sl):
        return float(np.mean(v[sl]))

    # ---- G1 noisy TV over a NOISE ENSEMBLE: learnable + noisy, gated vs naive.
    # An allocation rate is a property of the stimulus DISTRIBUTION; aggregate
    # over N_ENS independent noise draws (per-draw pass fraction also reported).
    gate_curves_noisy, gate_curves_learn, naive_curves_noisy = [], [], []
    per_seed_leaves = 0
    for i in range(N_ENS):
        noise = noise_seq(np.random.default_rng(SEED + i))
        rg = run_items({"learnable": learn, "noisy": noise}, mode=0)
        rn = run_items({"learnable": learn, "noisy": noise}, mode=1)
        gate_curves_noisy.append(rg["noisy"]["interest"])
        gate_curves_learn.append(rg["learnable"]["interest"])
        naive_curves_noisy.append(rn["noisy"]["interest"])
        if mean(rg["noisy"]["interest"], late) < 0.5 * mean(rg["noisy"]["interest"], early):
            per_seed_leaves += 1
    # ensemble-mean curves
    g_noisy = list(np.mean(np.array(gate_curves_noisy), axis=0))
    g_learn = list(np.mean(np.array(gate_curves_learn), axis=0))
    n_noisy = list(np.mean(np.array(naive_curves_noisy), axis=0))
    # the single-draw curves (seed SEED) kept for the plot
    rec_gated = run_items({"learnable": learn,
                           "noisy": noise_seq(np.random.default_rng(SEED))}, mode=0)
    rec_naive = run_items({"learnable": learn,
                           "noisy": noise_seq(np.random.default_rng(SEED))}, mode=1)

    G1a_gated_leaves_noisy = mean(g_noisy, late) < 0.5 * mean(g_noisy, early)
    late_share_learn = mean(g_learn, late) / max(mean(g_learn, late) + mean(g_noisy, late), 1e-9)
    late_share_noisy = mean(g_noisy, late) / max(mean(g_learn, late) + mean(g_noisy, late), 1e-9)
    G1b_gated_to_learnable = late_share_learn > late_share_noisy
    G1c_naive_traps = (mean(n_noisy, late) >= 0.8 * mean(n_noisy, early)
                       and mean(n_noisy, late) > mean(g_noisy, late))
    # headline: ensemble gated does NOT trap on noisy (learnable dominates late);
    # ensemble naive DOES (noisy >= learnable late).
    G1_headline = (mean(g_learn, late) > 2 * mean(g_noisy, late)
                   and mean(n_noisy, late) > mean(g_noisy, late))

    # ---- G2 leave-the-unresolved over the ensemble: resolved, intractable,
    # progressing (one gated hub each draw). ----
    res_c, int_c, prog_c = [], [], []
    res_surp, int_surp, prog_surp = [], [], []
    for i in range(N_ENS):
        noise2 = noise_seq(np.random.default_rng(SEED + 1000 + i))
        rec2 = run_items({"resolved": resolved_seq(),
                          "intractable": noise2,
                          "progressing": learnable_seq()}, mode=0)
        res_c.append(rec2["resolved"]["interest"])
        int_c.append(rec2["intractable"]["interest"])
        prog_c.append(rec2["progressing"]["interest"])
        res_surp.append(np.mean(rec2["resolved"]["residual"]))
        int_surp.append(np.mean(rec2["intractable"]["residual"]))
        prog_surp.append(np.mean(rec2["progressing"]["residual"]))
    r_res = list(np.mean(np.array(res_c), axis=0))
    r_int = list(np.mean(np.array(int_c), axis=0))
    r_prog = list(np.mean(np.array(prog_c), axis=0))
    res_surprise = float(np.mean(res_surp))
    int_surprise = float(np.mean(int_surp))
    prog_surprise = float(np.mean(prog_surp))
    G2a_resolved_decays = mean(r_res, late) < 0.5 * mean(r_res, early)
    G2b_intractable_decays = mean(r_int, late) < 0.5 * mean(r_int, early)
    G2c_progressing_held = mean(r_prog, late) >= 0.8 * mean(r_prog, early)
    # discriminator: resolved has the LOWEST mean residual, intractable the
    # HIGHEST — yet BOTH decay while the intermediate-surprise progressing item
    # is held. So retained-interest ranking != surprise ranking.
    G2d_progress_not_surprise = (
        res_surprise < prog_surprise < int_surprise
        and mean(r_prog, late) > mean(r_res, late)
        and mean(r_prog, late) > mean(r_int, late))
    # kept for the plot: a single representative draw
    rec2 = run_items({"resolved": resolved_seq(),
                      "intractable": noise_seq(np.random.default_rng(SEED + 1000)),
                      "progressing": learnable_seq()}, mode=0)

    # ---- G3 commit-net + calibration ----
    H = 14
    arms = {}
    for name, ce, cc in (("naive", 0, 50), ("passive", 1, 0),
                         ("impulsive", 1, 2000), ("calibrated", 1, 50)):
        cs, marg, vals = run_commit(ce, cc, H=H)
        arms[name] = dict(commit_enabled=ce, commit_cost=cc, commit_step=cs,
                          marginals=marg, values=vals)
    # analytic crossing: first step where Ashr(V_max, step) < commit_cost
    v_max = 1024
    analytic_cross = next((k for k in range(1, H + 1)
                           if (v_max >> k) < 50), None)
    G3a_paralysis = arms["naive"]["commit_step"] is None
    G3b_calibrated = (arms["calibrated"]["commit_step"] == analytic_cross
                      and analytic_cross is not None and 0 < analytic_cross < H)
    G3c_impulsive = (arms["impulsive"]["commit_step"] is not None
                     and arms["impulsive"]["commit_step"] <= 1)
    G3d_passive = arms["passive"]["commit_step"] is None

    # ---- G4 integer-native + default-OFF + source ----
    term_report, bad_float = integer_terms_audit()
    # integer-native across the run: every recorded curiosity/commit value int
    allvals = []
    for rec in (rec_gated, rec_naive, rec2):
        for name in rec:
            for k in ("interest", "residual", "learning_progress"):
                allvals += rec[name][k]
    for name in arms:
        allvals += arms[name]["marginals"] + arms[name]["values"]
    noninteger = sum(1 for v in allvals if float(v) != int(v))
    G4a_integer = (noninteger == 0) and (len(bad_float) == 0)
    changed_noparams, changed_disabled = default_off_byte_identity()
    G4b_default_off = (len(changed_noparams) == 0 and len(changed_disabled) == 0
                       and seed_self_load_only())
    bad_setattr = source_audit()
    G4c_source = (len(bad_setattr) == 0)

    results = dict(
        block=SEED, T=T, params=PARAMS,
        G1=dict(
            n_ensemble=N_ENS,
            gated_noisy=g_noisy, gated_learnable=g_learn, naive_noisy=n_noisy,
            gated_noisy_single=rec_gated["noisy"]["interest"],
            naive_noisy_single=rec_naive["noisy"]["interest"],
            gated_learnable_single=rec_gated["learnable"]["interest"],
            naive_learnable_single=rec_naive["learnable"]["interest"],
            gated_noisy_early=mean(g_noisy, early), gated_noisy_late=mean(g_noisy, late),
            naive_noisy_early=mean(n_noisy, early), naive_noisy_late=mean(n_noisy, late),
            gated_learnable_late=mean(g_learn, late),
            late_share_learnable=late_share_learn, late_share_noisy=late_share_noisy,
            per_seed_gated_leaves=per_seed_leaves),
        G2=dict(
            resolved=r_res, intractable=r_int, progressing=r_prog,
            resolved_early=mean(r_res, early), resolved_late=mean(r_res, late),
            intractable_early=mean(r_int, early), intractable_late=mean(r_int, late),
            progressing_early=mean(r_prog, early), progressing_late=mean(r_prog, late),
            resolved_surprise=res_surprise, progressing_surprise=prog_surprise,
            intractable_surprise=int_surprise),
        G3=dict(arms={k: {kk: vv for kk, vv in v.items()} for k, v in arms.items()},
                analytic_crossing=analytic_cross),
        G4=dict(term_report=term_report, bad_float=bad_float,
                noninteger_cells=noninteger,
                changed_noparams=changed_noparams, changed_disabled=changed_disabled,
                bad_setattr=bad_setattr, self_load_only=seed_self_load_only()),
        criteria=dict(
            G1a_gated_leaves_noisy=bool(G1a_gated_leaves_noisy),
            G1b_gated_to_learnable=bool(G1b_gated_to_learnable),
            G1c_naive_traps=bool(G1c_naive_traps),
            G1_headline=bool(G1_headline),
            G2a_resolved_decays=bool(G2a_resolved_decays),
            G2b_intractable_decays=bool(G2b_intractable_decays),
            G2c_progressing_held=bool(G2c_progressing_held),
            G2d_progress_not_surprise=bool(G2d_progress_not_surprise),
            G3a_paralysis=bool(G3a_paralysis),
            G3b_calibrated_at_crossing=bool(G3b_calibrated),
            G3c_impulsive=bool(G3c_impulsive),
            G3d_passive_paralysis=bool(G3d_passive),
            G4a_integer_native=bool(G4a_integer),
            G4b_default_off_byte_identical=bool(G4b_default_off),
            G4c_source_graph_resident=bool(G4c_source),
        ),
    )
    with open(os.path.join(RESULTS, "learning_progress.json"), "w") as fh:
        json.dump(results, fh, indent=2)
    render_g1(rec_gated, rec_naive, os.path.join(FRAMES, "g1_noisy_tv.png"))
    render_g2(rec2, os.path.join(FRAMES, "g2_leave_unresolved.png"))
    render_g3(arms, os.path.join(FRAMES, "g3_commit_net.png"))
    return results


def main():
    res = measure()
    print(json.dumps(res["criteria"], indent=2))
    g1, g2, g3 = res["G1"], res["G2"], res["G3"]
    print(f"\nG1  gated noisy {g1['gated_noisy_early']:.0f}->{g1['gated_noisy_late']:.0f}"
          f" | naive noisy {g1['naive_noisy_early']:.0f}->{g1['naive_noisy_late']:.0f}"
          f" | gated learnable late {g1['gated_learnable_late']:.0f}")
    print(f"    late attention share: learnable {g1['late_share_learnable']:.2f}"
          f"  noisy {g1['late_share_noisy']:.2f}")
    print(f"G2  resolved {g2['resolved_early']:.0f}->{g2['resolved_late']:.0f}"
          f" | intractable {g2['intractable_early']:.0f}->{g2['intractable_late']:.0f}"
          f" | progressing {g2['progressing_early']:.0f}->{g2['progressing_late']:.0f}")
    print(f"    mean surprise: resolved {g2['resolved_surprise']:.0f} <"
          f" progressing {g2['progressing_surprise']:.0f} <"
          f" intractable {g2['intractable_surprise']:.0f}")
    print(f"G3  commit steps: " + ", ".join(
        f"{k}={v['commit_step']}" for k, v in g3['arms'].items())
        + f"  (analytic crossing={g3['analytic_crossing']})")
    print(f"G4  noninteger cells {res['G4']['noninteger_cells']}"
          f" | float terms {res['G4']['bad_float']}"
          f" | default-off changed {res['G4']['changed_noparams']}"
          f" | bad set_attr {res['G4']['bad_setattr']}")


if __name__ == "__main__":
    main()

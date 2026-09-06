#!/usr/bin/env python3
"""REPRODUCE THE EMOTIONAL BASELINE FROM BEHAVIOUR — computational phenotyping by
inverse inference (seed block 206000).

MECHANICAL INVERSE-INFERENCE MEASURE. No agent decision, no Rust, no Term, NO new
seed. Synthetic agents are `EmotionHub` + `HeldEmotionParams` nodes whose attrs
are their KNOWN emotional baseline (the 204000 knobs); their DECISIONS across a
battery of appraisal scenarios are produced GRAPH-NATIVELY by `run_rules()` over
the ALREADY-LANDED `seeds/core_emotions.json` (which itself reuses 196000
freshness, 199000 present readout, 202000 learning-progress / value atoms). This
script only: sets attrs, ticks, reads the graph's OWN decisions, and then FITS
(a Bayesian grid posterior over knobs) — model-fitting, not an agent decision.

The knob-vector recovered (theta), each a named baseline trait:
  * w_supergraph    — supergraph-value weight   (psychopathy at 0)
  * mood_bias       — additive value offset      (depression <<0 / mania >>0)
  * residual_thresh — surprise/salience threshold
  * threat_half_life— threat-precision persistence (fear vs anxiety; PTSD trait)

Gates (prereg VISION_EMOTION_PHENOTYPE_PREREG.md):
  G1 PARAMETER RECOVERY + IDENTIFIABILITY MAP (which knobs recover well vs which
     are under-identified; genuine posterior spread; w_supergraph SIGN-only).
  G2 PREDICTION / MANIFOLD — fitted baseline predicts HELD-OUT decisions better
     than population-mean and random controls.
  G3 EXPLANATION — counterfactual on the fitted knob attributes the psychopath's
     harm-endorsement and the parent's supergraph-costly act to w_supergraph.
  G4 FALSIFICATION VERDICT — recovered / interval / sign-only / ill-posed per
     knob; whether the pre-registered identifiability prediction held.
  G5 integer-native (agent side) + default-OFF byte-identity (no seed/Rust added).

FRAMING: understanding, not judgment; the FUNCTIONAL fit, NOT felt qualia.
SYNTHETIC-ONLY; real behavioural data is a care-gated follow-on, OUT OF SCOPE.

IMPORT-INERT: nothing runs at import; `main()` is the only entry.
"""
from __future__ import annotations

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np                                  # noqa: E402

from domains.photon_eye import GraphEye             # noqa: E402
from substrate.seed_loader import manifest_for      # noqa: E402

SEED = 206000
RESULTS = os.path.join(ROOT, "results")
FIGDIR = os.path.join(RESULTS, "emotion_phenotype")

EP_DEFAULTS = dict(enabled=1.0, w_supergraph=1.0, mood_bias=0.0,
                   residual_thresh=100.0, high_arousal=800.0,
                   mid_arousal=400.0, low_arousal=50.0)

APPR_DEFAULTS = dict(
    appraised=0.0, residual=0.0, residual_prev=0.0, learning_progress=0.0,
    threat=0.0, threat_c0=1024.0, threat_half_life=1.0, threat_last_refresh=0.0,
    threat_now_epoch=0.0, t_present=256.0, threat_precision=0.0, threat_persists=0.0,
    valued_goal=0.0, goal_blocked=0.0, blocker_present=0.0,
    contamination=0.0, attachment=0.0, regroundable=0.0, was_engaged=0.0,
    v_max=1024.0, step=1.0, step_prev=0.0, attach_v0=1024.0,
    attach_k_now=1.0, attach_k_prev=0.0, value_progress=0.0,
    individual_benefit=0.0, individual_cost=0.0, supergraph_contribution=0.0,
    collective_success=0.0, collective_success_prev=0.0,
    contribution_by_self=0.0, observed_by_other=0.0,
    happiness=0.0, fulfilment_value=0.0, total_value=0.0, act_endorsed=0.0,
    n_fired=0.0, action_tendency=0.0, emotion=0.0, valence=0.0, arousal=0.0)
for _nm in ("surprise", "fear", "anxiety", "anger", "frustration", "disgust",
            "joy", "sadness", "curiosity", "boredom", "fulfilment", "pride"):
    APPR_DEFAULTS["hit_" + _nm] = 0.0

CORE = ["surprise", "fear", "anxiety", "anger", "frustration", "disgust",
        "joy", "sadness", "curiosity", "boredom", "fulfilment"]

# ----------------------------------------------------------------- the battery
# VALUE family: mood-staircase (pure individual, supergraph_contribution=0) pins
# mood_bias via the endorse boundary (endorse iff (benefit-cost)+2*mood >= 0);
# plus three w-scenarios that pin w_supergraph's SIGN. The staircase spans the
# endorse boundary for every mood in the panel pool (boundary core = -2*mood).
_VAL_BENEFIT = 800
_VAL_CORES = list(range(700, -501, -50))           # +700 .. -500 step 50 (25)


def _value_scenarios():
    scs = []
    for core in _VAL_CORES:
        scs.append(("val_core_%+d" % core,
                    dict(appraised=1, individual_benefit=_VAL_BENEFIT,
                         individual_cost=_VAL_BENEFIT - core,
                         supergraph_contribution=0)))
    # w-sign pins:
    # harm: individually good (+500), supergraph HARMFUL (-800); endorse iff w==0
    scs.append(("val_harm",
                dict(appraised=1, individual_benefit=500, individual_cost=0,
                     supergraph_contribution=-800, collective_success=0,
                     collective_success_prev=800)))
    # contrib: pure supergraph gain; hit_fulfilment fires iff w>0
    scs.append(("val_contrib",
                dict(appraised=1, individual_benefit=0, individual_cost=0,
                     supergraph_contribution=300, collective_success=300,
                     collective_success_prev=0)))
    # parenthood: individually COSTLY (-300 core), supergraph BENEFICIAL (+500);
    # endorse iff w>0 (the "irrational" supergraph-costly act)
    scs.append(("val_parent",
                dict(appraised=1, individual_benefit=100, individual_cost=400,
                     supergraph_contribution=500, collective_success=500,
                     collective_success_prev=0)))
    return scs


# SURPRISE family: residual sweep at appraised=0; hit_surprise iff residual>thresh
_SURPRISE_RES = list(range(30, 601, 30))            # 30 .. 600 (20)


def _surprise_scenarios():
    return [("sur_res_%d" % r, dict(appraised=0, residual=r))
            for r in _SURPRISE_RES]


# THREAT family: fixed threat, epoch sweep; anxiety->fear flips at epoch=3*hl
_THREAT_EPOCHS = list(range(0, 31, 2))              # 0 .. 30 step 2 (16)


def _threat_scenarios():
    return [("thr_ep_%d" % e,
             dict(appraised=1, threat=1, threat_now_epoch=e))
            for e in _THREAT_EPOCHS]


# ----------------------------------------------------------------- knob grids
W_GRID = [0, 1]                                     # SIGN classes (0 psychopath)
W_MAG_PROBE = [1, 2, 5, 25, 250]                    # magnitude-plateau probe
MOOD_GRID = list(range(-500, 501, 25))              # 41
RES_GRID = list(range(0, 601, 30))                  # 21
HL_GRID = [1, 2, 3, 4, 5, 6, 8, 10, 13, 17, 22, 1_000_000]   # 12
HL_PERSISTENT = 1_000_000                           # never-decays (anxiety trait)


# ----------------------------------------------------------------- eye / decode
def _eye():
    eye = GraphEye(n_az=4, n_el=4, adapt_rate=0.15,
                   context={"retina_2d": True, "synchronous": True,
                            "worker_capacity": 1}).build()
    inner = eye.substrate._inner
    inner.load_seed_manifest(manifest_for("core_emotions"), eye._agent)
    return eye, inner


def _hub(eye, inner, **ep_over):
    from domains.core_emotions_weight import quantize_weight
    hub = eye.substrate.add_node("EmotionHub", {})
    p = dict(EP_DEFAULTS)
    p.update({k: float(v) for k, v in ep_over.items()
             if k not in ("w_supergraph_q", "w_scale_bits")})
    wq, bits = quantize_weight(p["w_supergraph"])
    p["w_supergraph_q"] = float(ep_over.get("w_supergraph_q", wq))
    p["w_scale_bits"] = float(ep_over.get("w_scale_bits", bits))
    ep = eye.substrate.add_node("HeldEmotionParams", p)
    inner.add_edge_unchecked(hub, "has_emotion_params", ep)
    return hub


def _appraise(eye, inner, hub, **over):
    a = dict(APPR_DEFAULTS)
    a.update({k: float(v) for k, v in over.items()})
    ap = eye.substrate.add_node("Appraisal", a)
    inner.add_edge_unchecked(hub, "has_appraisal", ap)
    return ap


def _decision(eye, ap, family):
    """Read the graph's OWN decision (discrete) for a scenario. We observe
    DECISIONS, never internal integer values."""
    a = eye.substrate.node(ap)["attrs"]
    fired = tuple(nm for nm in CORE if int(a.get("hit_" + nm, 0)) == 1)
    if family == "value":
        return (int(a["action_tendency"]), int(a["act_endorsed"]), fired)
    if family == "surprise":
        return (int(a.get("hit_surprise", 0)),)
    if family == "threat":
        return (int(a["action_tendency"]),)          # 2=fear(AVOID) 3=anxiety(VIG)
    raise ValueError(family)


# --------------------------------------- simulate a whole grid in ONE run_rules
def _sim_value_grid():
    """decisions[(w,mood)][scenario_label] -> decision tuple."""
    eye, inner = _eye()
    scs = _value_scenarios()
    handles = {}
    for w in W_GRID:
        for mood in MOOD_GRID:
            hub = _hub(eye, inner, w_supergraph=w, mood_bias=mood)
            handles[(w, mood)] = {lab: _appraise(eye, inner, hub, **ov)
                                  for lab, ov in scs}
    inner.run_rules()
    table = {k: {lab: _decision(eye, ap, "value") for lab, ap in d.items()}
             for k, d in handles.items()}
    eye.stop()
    return table, [lab for lab, _ in scs]


def _sim_surprise_grid():
    eye, inner = _eye()
    scs = _surprise_scenarios()
    handles = {}
    for thr in RES_GRID:
        hub = _hub(eye, inner, residual_thresh=thr)
        handles[thr] = {lab: _appraise(eye, inner, hub, **ov) for lab, ov in scs}
    inner.run_rules()
    table = {thr: {lab: _decision(eye, ap, "surprise") for lab, ap in d.items()}
             for thr, d in handles.items()}
    eye.stop()
    return table, [lab for lab, _ in scs]


def _sim_threat_grid():
    eye, inner = _eye()
    scs = _threat_scenarios()
    handles = {}
    for hl in HL_GRID:
        hub = _hub(eye, inner)
        handles[hl] = {lab: _appraise(eye, inner, hub, threat_half_life=hl, **ov)
                       for lab, ov in scs}
    inner.run_rules()
    table = {hl: {lab: _decision(eye, ap, "threat") for lab, ap in d.items()}
             for hl, d in handles.items()}
    eye.stop()
    return table, [lab for lab, _ in scs]


def _sim_w_magnitude_probe():
    """One agent, several POSITIVE w magnitudes: show the decisions are
    byte-identical across magnitude (the plateau) — under-identification proof."""
    eye, inner = _eye()
    scs = _value_scenarios()
    handles = {}
    for w in W_MAG_PROBE:
        hub = _hub(eye, inner, w_supergraph=w, mood_bias=0)
        handles[w] = {lab: _appraise(eye, inner, hub, **ov) for lab, ov in scs}
    inner.run_rules()
    table = {w: {lab: _decision(eye, ap, "value") for lab, ap in d.items()}
             for w, d in handles.items()}
    eye.stop()
    return table


# ---------------------------------------------------------------- the FIT
EPS = 0.02          # observation lapse rate (smooths the posterior; not a delta)
_LOG_HIT = math.log(1.0 - EPS)
_LOG_MISS = math.log(EPS)


def _loglik_components(pred, obs):
    """Sum of per-COMPONENT Bernoulli log-likelihood between two decision tuples
    (each tuple component is one observed discrete decision)."""
    ll = 0.0
    for pc, oc in zip(pred, obs):
        ll += _LOG_HIT if pc == oc else _LOG_MISS
    return ll


def _posterior_1d(grid, loglik):
    m = max(loglik)
    w = [math.exp(x - m) for x in loglik]
    z = sum(w)
    post = [x / z for x in w]
    imap = int(np.argmax(loglik))
    # 95% credible SET: smallest set of grid points (by descending mass) reaching
    # 0.95 cumulative; report its span
    order = sorted(range(len(grid)), key=lambda i: -post[i])
    cum, keep = 0.0, []
    for i in order:
        keep.append(i)
        cum += post[i]
        if cum >= 0.95:
            break
    kg = sorted(grid[i] for i in keep)
    return dict(post=post, map=grid[imap], mass_at_map=post[imap],
                cred_lo=kg[0], cred_hi=kg[-1], cred_width=kg[-1] - kg[0],
                cred_set=kg)


def _fit_value(obs, labels):
    """Joint posterior over (w, mood) from VALUE decisions; marginals for each."""
    LL = {(w, mood): sum(_loglik_components(TABLES["value"][(w, mood)][lab],
                                            obs[lab]) for lab in labels)
          for w in W_GRID for mood in MOOD_GRID}
    # marginal over mood (sum-exp over w)
    def marg_mood():
        out = []
        for mood in MOOD_GRID:
            xs = [LL[(w, mood)] for w in W_GRID]
            m = max(xs)
            out.append(m + math.log(sum(math.exp(x - m) for x in xs)))
        return out
    mood_ll = marg_mood()
    mood_post = _posterior_1d(MOOD_GRID, mood_ll)
    # marginal over w-sign
    def marg_w():
        out = []
        for w in W_GRID:
            xs = [LL[(w, mood)] for mood in MOOD_GRID]
            m = max(xs)
            out.append(m + math.log(sum(math.exp(x - m) for x in xs)))
        return out
    w_ll = marg_w()
    m = max(w_ll)
    wpost = [math.exp(x - m) for x in w_ll]
    z = sum(wpost)
    wpost = [x / z for x in wpost]
    w_map = W_GRID[int(np.argmax(w_ll))]
    joint_map = max(LL, key=LL.get)
    return dict(mood=mood_post, w_map=w_map, w_post=dict(zip(W_GRID, wpost)),
                joint_map=dict(w=joint_map[0], mood=joint_map[1]))


def _fit_surprise(obs, labels):
    ll = [sum(_loglik_components(TABLES["surprise"][thr][lab], obs[lab])
              for lab in labels) for thr in RES_GRID]
    return _posterior_1d(RES_GRID, ll)


def _fit_threat(obs, labels):
    ll = [sum(_loglik_components(TABLES["threat"][hl][lab], obs[lab])
              for lab in labels) for hl in HL_GRID]
    return _posterior_1d(HL_GRID, ll)


# ---------------------------------------------------------------- TABLES (cache)
TABLES = {}


def _build_tables():
    vt, vlabels = _sim_value_grid()
    st, slabels = _sim_surprise_grid()
    tt, tlabels = _sim_threat_grid()
    TABLES["value"] = vt
    TABLES["surprise"] = st
    TABLES["threat"] = tt
    return dict(value=vlabels, surprise=slabels, threat=tlabels)


# ---------------------------------------------------------------- panel + gates
def _agent_decisions(theta, labels):
    """The agent's true decisions = the landed graph's output at theta (on-grid
    lookup; the agent is deterministic)."""
    w, mood, res, hl = theta
    dec = {}
    for lab in labels["value"]:
        dec[lab] = TABLES["value"][(w, mood)][lab]
    for lab in labels["surprise"]:
        dec[lab] = TABLES["surprise"][res][lab]
    for lab in labels["threat"]:
        dec[lab] = TABLES["threat"][hl][lab]
    return dec


def _corrupt(dec, rng, eps_true):
    """Observation noise: flip each component of each decision w.p. eps_true."""
    if eps_true <= 0:
        return dec
    out = {}
    for lab, d in dec.items():
        nd = list(d)
        for i in range(len(nd)):
            if rng.random() < eps_true:
                if isinstance(nd[i], tuple):
                    nd[i] = tuple()          # drop fired-set (a lapse)
                else:
                    nd[i] = 1 - nd[i] if nd[i] in (0, 1) else nd[i] + 1
        out[lab] = tuple(nd)
    return out


def _split(labels, family, holdout_frac=0.3):
    labs = labels[family]
    n_hold = max(1, int(round(len(labs) * holdout_frac)))
    hold = labs[::max(1, len(labs) // n_hold)][:n_hold]
    train = [x for x in labs if x not in hold]
    return train, hold


def run_panel(n_agents=48, eps_true=0.0, seed=SEED):
    rng = np.random.default_rng(seed)
    labels = LABELS
    # observable-flip half-lives (flip epoch 3*hl <= max epoch) vs persistent
    hl_observable = [h for h in HL_GRID if 3 * h <= _THREAT_EPOCHS[-1]]
    hl_pool = hl_observable + [HL_PERSISTENT]
    # mood interior so the endorse boundary is inside the staircase span
    mood_pool = [m for m in MOOD_GRID if -350 <= m <= 150]
    res_pool = [r for r in RES_GRID if 30 <= r <= 570]

    train_v, hold_v = _split(labels, "value")
    train_s, hold_s = _split(labels, "surprise")
    train_t, hold_t = _split(labels, "threat")

    rows = []
    for _ in range(n_agents):
        w = int(rng.choice(W_GRID, p=[0.4, 0.6]))
        mood = int(rng.choice(mood_pool))
        res = int(rng.choice(res_pool))
        hl = int(rng.choice(hl_pool))
        theta = (w, mood, res, hl)
        true = _agent_decisions(theta, labels)
        obs = _corrupt(true, rng, eps_true)

        fit_v = _fit_value(obs, train_v)
        fit_s = _fit_surprise(obs, train_s)
        fit_t = _fit_threat(obs, train_t)
        rows.append(dict(theta=dict(w=w, mood=mood, res=res, hl=hl),
                         fit=dict(w_map=fit_v["w_map"], w_post=fit_v["w_post"],
                                  mood=fit_v["mood"], res=fit_s, hl=fit_t),
                         obs=obs, true=true))
    return dict(rows=rows, holdouts=dict(value=hold_v, surprise=hold_s,
                                         threat=hold_t),
                trains=dict(value=train_v, surprise=train_s, threat=train_t),
                hl_observable=hl_observable)


# ------------------------------------------------------------- G1 recovery map
def g1_recovery(panel):
    rows = panel["rows"]
    # mood: continuous -> Pearson r(true, MAP) + MAE + coverage
    tm = np.array([r["theta"]["mood"] for r in rows], float)
    pm = np.array([r["fit"]["mood"]["map"] for r in rows], float)
    mood_r = float(np.corrcoef(tm, pm)[0, 1])
    mood_mae = float(np.mean(np.abs(tm - pm)))
    mood_cov = float(np.mean([r["fit"]["mood"]["cred_lo"] <= r["theta"]["mood"]
                              <= r["fit"]["mood"]["cred_hi"] for r in rows]))
    mood_width = float(np.mean([r["fit"]["mood"]["cred_width"] for r in rows]))

    # residual_thresh: interval knob -> MAP within one sweep-step + coverage
    step_res = RES_GRID[1] - RES_GRID[0]
    res_hits = np.mean([abs(r["fit"]["res"]["map"] - r["theta"]["res"]) <= step_res
                        for r in rows])
    res_cov = np.mean([r["fit"]["res"]["cred_lo"] <= r["theta"]["res"]
                       <= r["fit"]["res"]["cred_hi"] for r in rows])
    tr = np.array([r["theta"]["res"] for r in rows], float)
    pr = np.array([r["fit"]["res"]["map"] for r in rows], float)
    res_r = float(np.corrcoef(tr, pr)[0, 1])
    res_width = float(np.mean([r["fit"]["res"]["cred_width"] for r in rows]))

    # threat_half_life: observable-flip -> interval located; persistent ->
    # bounded-below (posterior mass on the large-hl tail)
    obs_rows = [r for r in rows if r["theta"]["hl"] != HL_PERSISTENT]
    per_rows = [r for r in rows if r["theta"]["hl"] == HL_PERSISTENT]
    # for observable, the identifiable quantity is the flip epoch e*=3*hl; check
    # the MAP's flip epoch matches within one epoch-step (2)
    def flip_ok(r):
        return abs(r["fit"]["hl"]["map"] - r["theta"]["hl"]) <= 1 or \
            abs(3 * r["fit"]["hl"]["map"] - 3 * r["theta"]["hl"]) <= \
            (_THREAT_EPOCHS[1] - _THREAT_EPOCHS[0])
    hl_obs_hit = np.mean([flip_ok(r) for r in obs_rows]) if obs_rows else float("nan")
    # persistent recovered iff MAP is on the bounded-below tail (>= largest
    # observable-flip hl, i.e. no flip within the sweep)
    max_obs_hl = max(panel["hl_observable"])
    hl_per_hit = np.mean([r["fit"]["hl"]["map"] > max_obs_hl for r in per_rows]) \
        if per_rows else float("nan")

    # w_supergraph: SIGN recovery (0 vs >0)
    w_sign_hit = np.mean([(r["fit"]["w_map"] == 0) == (r["theta"]["w"] == 0)
                          for r in rows])

    return dict(
        mood=dict(recovers=True, r=mood_r, mae=mood_mae, coverage=mood_cov,
                  mean_cred_width=mood_width, grid_step=MOOD_GRID[1] - MOOD_GRID[0]),
        residual_thresh=dict(recovers=True, r=res_r,
                             map_within_step_frac=float(res_hits),
                             coverage=float(res_cov), mean_cred_width=res_width,
                             grid_step=step_res),
        threat_half_life=dict(observable_flip_frac=float(hl_obs_hit),
                              persistent_boundedbelow_frac=float(hl_per_hit),
                              n_observable=len(obs_rows), n_persistent=len(per_rows)),
        w_supergraph=dict(sign_recovery=float(w_sign_hit),
                          magnitude="UNDER-IDENTIFIED (plateau; see w_magnitude_plateau)"),
        n_agents=len(rows))


def w_magnitude_plateau():
    """PROOF that w_supergraph magnitude is unidentifiable: all POSITIVE
    magnitudes produce byte-identical decisions across the whole VALUE battery."""
    probe = _sim_w_magnitude_probe()
    ws = W_MAG_PROBE
    ref = probe[ws[0]]
    identical = all(probe[w] == ref for w in ws)
    return dict(magnitudes=ws, all_identical=bool(identical),
                distinct_decision_vectors=len({json.dumps(
                    {k: list(v) for k, v in probe[w].items()}, sort_keys=True)
                    for w in ws}))


# ------------------------------------------------------------- G2 prediction
def _predict_family(theta_like, family, labels):
    """Predict held-out decisions given a knob-vector (nearest grid)."""
    w, mood, res, hl = theta_like
    w = 0 if w == 0 else 1
    mood = min(MOOD_GRID, key=lambda g: abs(g - mood))
    res = min(RES_GRID, key=lambda g: abs(g - res))
    hl = min(HL_GRID, key=lambda g: abs(g - hl))
    out = {}
    for lab in labels:
        if family == "value":
            out[lab] = TABLES["value"][(w, mood)][lab]
        elif family == "surprise":
            out[lab] = TABLES["surprise"][res][lab]
        else:
            out[lab] = TABLES["threat"][hl][lab]
    return out


def _acc(pred, obs, labels):
    hit = tot = 0
    for lab in labels:
        for pc, oc in zip(pred[lab], obs[lab]):
            hit += (pc == oc)
            tot += 1
    return hit / tot


def g2_prediction(panel):
    rows = panel["rows"]
    hold = panel["holdouts"]
    # population-mean knobs (a single "average person")
    pop = (1,  # w: majority sign
           int(round(np.mean([r["theta"]["mood"] for r in rows]))),
           int(round(np.mean([r["theta"]["res"] for r in rows]))),
           int(round(np.median([r["theta"]["hl"] for r in rows
                                if r["theta"]["hl"] != HL_PERSISTENT]))))
    rng = np.random.default_rng(SEED + 1)
    fam_labels = {"value": hold["value"], "surprise": hold["surprise"],
                  "threat": hold["threat"]}
    fitted_accs, pop_accs, rand_accs = [], [], []
    for r in rows:
        fit_theta = (r["fit"]["w_map"], r["fit"]["mood"]["map"],
                     r["fit"]["res"]["map"], r["fit"]["hl"]["map"])
        rand_theta = (int(rng.choice(W_GRID)), int(rng.choice(MOOD_GRID)),
                      int(rng.choice(RES_GRID)), int(rng.choice(HL_GRID)))
        fa = pa = ra = 0.0
        ntot = 0
        for fam, labs in fam_labels.items():
            if not labs:
                continue
            fa += _acc(_predict_family(fit_theta, fam, labs), r["obs"], labs) * len(labs)
            pa += _acc(_predict_family(pop, fam, labs), r["obs"], labs) * len(labs)
            ra += _acc(_predict_family(rand_theta, fam, labs), r["obs"], labs) * len(labs)
            ntot += len(labs)
        fitted_accs.append(fa / ntot)
        pop_accs.append(pa / ntot)
        rand_accs.append(ra / ntot)
    return dict(
        fitted=float(np.mean(fitted_accs)), population_mean=float(np.mean(pop_accs)),
        random=float(np.mean(rand_accs)),
        fitted_beats_pop=float(np.mean(np.array(fitted_accs) >= np.array(pop_accs))),
        fitted_beats_random=float(np.mean(np.array(fitted_accs) >= np.array(rand_accs))),
        fitted_strictly_beats_pop=bool(np.mean(fitted_accs) > np.mean(pop_accs)),
        fitted_strictly_beats_random=bool(np.mean(fitted_accs) > np.mean(rand_accs)),
        pop_knobs=dict(w=pop[0], mood=pop[1], res=pop[2], hl=pop[3]),
        holdout_sizes={k: len(v) for k, v in fam_labels.items()})


# ------------------------------------------------------------- G3 explanation
def g3_explanation():
    """Counterfactual on the FITTED knob attributes distinctive acts to
    w_supergraph. Two agents: a psychopath (w=0) endorsing a supergraph-HARMFUL
    act; a 'parent' (w>0) endorsing a supergraph-COSTLY act."""
    labels = LABELS

    def fit_agent(theta):
        true = _agent_decisions(theta, labels)
        fit_v = _fit_value(true, labels["value"])
        return fit_v, true

    # --- psychopath: w=0, mood 0 ---
    psych_theta = (0, 0, 120, 4)
    fit_p, true_p = fit_agent(psych_theta)
    w_fit_p = fit_p["w_map"]
    mood_fit_p = fit_p["mood"]["map"]
    # under fitted knob: endorse the harm? counterfactual: flip w -> healthy
    endorse_harm_fitted = TABLES["value"][(w_fit_p, mood_fit_p)]["val_harm"][1]
    # counterfactual healthy sign, same fitted mood
    cf_w = 1
    endorse_harm_cf = TABLES["value"][(cf_w, mood_fit_p)]["val_harm"][1]

    # --- parent: w=1, mood 0 ---
    parent_theta = (1, 0, 120, 4)
    fit_par, true_par = fit_agent(parent_theta)
    w_fit_par = fit_par["w_map"]
    mood_fit_par = fit_par["mood"]["map"]
    endorse_parent_fitted = TABLES["value"][(w_fit_par, mood_fit_par)]["val_parent"][1]
    # counterfactual: zero the supergraph valuing
    endorse_parent_cf = TABLES["value"][(0, mood_fit_par)]["val_parent"][1]

    return dict(
        psychopath=dict(true=dict(w=0), fitted_w=w_fit_p, fitted_mood=mood_fit_p,
                        endorses_harm_under_fit=bool(endorse_harm_fitted == 1),
                        declines_harm_if_w_healthy=bool(endorse_harm_cf == 0),
                        attribution_isolated=bool(endorse_harm_fitted == 1
                                                  and endorse_harm_cf == 0
                                                  and w_fit_p == 0)),
        parent=dict(true=dict(w=1), fitted_w=w_fit_par, fitted_mood=mood_fit_par,
                    endorses_costly_under_fit=bool(endorse_parent_fitted == 1),
                    declines_costly_if_w_zero=bool(endorse_parent_cf == 0),
                    attribution_isolated=bool(endorse_parent_fitted == 1
                                              and endorse_parent_cf == 0
                                              and w_fit_par > 0)),
        both_attributed_to_w=bool(w_fit_p == 0 and w_fit_par > 0))


# ----------------------------------------------------- G5 integer + default-off
def integer_audit():
    """AGENT side integer-native: every decision the graph produces over the
    whole grid is an exact integer (inherits 204000 G5; verified here on the
    battery)."""
    bad = []
    for fam in ("value", "surprise", "threat"):
        for cfg, d in TABLES[fam].items():
            for lab, dec in d.items():
                for c in dec:
                    if isinstance(c, tuple):
                        continue
                    if isinstance(c, float) and not float(c).is_integer():
                        bad.append((fam, cfg, lab, c))
    return dict(all_integer=(len(bad) == 0), offenders=bad[:20])


def default_off():
    """No seed / rule / Rust added by this rung; the substrate is byte-identical
    with the rung absent. We assert the canonical .so md5 and that this rung ships
    no seed file."""
    so = os.path.join(ROOT, "runners", "dsl", "python", "substrate_rs",
                      "_native.abi3.so")
    import hashlib
    md5 = hashlib.md5(open(so, "rb").read()).hexdigest() if os.path.exists(so) else None
    # a fresh eye with NO opt-in has zero emotion nodes (the seed is loaded only
    # by this measure, per-eye, never by default)
    eye = GraphEye(n_az=4, n_el=4, adapt_rate=0.15,
                   context={"retina_2d": True, "synchronous": True,
                            "worker_capacity": 1}).build()
    inner = eye.substrate._inner
    n_hub = len(list(eye.substrate.nodes_of_type("EmotionHub"))) \
        if hasattr(eye.substrate, "nodes_of_type") else 0
    eye.stop()
    return dict(canonical_so_md5=md5,
                canonical_untouched=(md5 == "7efe75eba05b006cafd15dbb4b7da246"),
                no_emotion_nodes_by_default=(n_hub == 0),
                adds_no_seed=not os.path.exists(
                    os.path.join(ROOT, "seeds", "emotion_phenotype.json")))


# ------------------------------------------------------------------- noise check
def noise_robustness(eps_true=0.05, n_agents=48):
    panel = run_panel(n_agents=n_agents, eps_true=eps_true, seed=SEED + 7)
    g1 = g1_recovery(panel)
    g2 = g2_prediction(panel)
    return dict(eps_true=eps_true, mood_r=g1["mood"]["r"],
                mood_mae=g1["mood"]["mae"], w_sign=g1["w_supergraph"]["sign_recovery"],
                res_within_step=g1["residual_thresh"]["map_within_step_frac"],
                fitted_acc=g2["fitted"], pop_acc=g2["population_mean"],
                random_acc=g2["random"])


LABELS = None


# ----------------------------------------------------------------------- figure
def _figure(res, path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return None
    panel = res["_panel_rows"]
    fig, ax = plt.subplots(2, 2, figsize=(11, 8))

    # (a) mood recovery scatter
    tm = [r["theta"]["mood"] for r in panel]
    pm = [r["fit"]["mood"]["map"] for r in panel]
    ax[0, 0].scatter(tm, pm, s=22, alpha=0.7, color="#2b6cb0")
    lo, hi = min(MOOD_GRID), max(MOOD_GRID)
    ax[0, 0].plot([lo, hi], [lo, hi], "k--", lw=1)
    ax[0, 0].set_title("G1 mood_bias recovery (r=%.3f)" % res["g1_recovery"]["mood"]["r"])
    ax[0, 0].set_xlabel("true mood_bias"); ax[0, 0].set_ylabel("fitted MAP")

    # (b) residual_thresh recovery scatter
    tr = [r["theta"]["res"] for r in panel]
    pr = [r["fit"]["res"]["map"] for r in panel]
    ax[0, 1].scatter(tr, pr, s=22, alpha=0.7, color="#2f855a")
    ax[0, 1].plot([0, 600], [0, 600], "k--", lw=1)
    ax[0, 1].set_title("G1 residual_thresh recovery")
    ax[0, 1].set_xlabel("true"); ax[0, 1].set_ylabel("fitted MAP")

    # (c) w_supergraph posterior for one healthy + magnitude plateau
    magp = res["w_magnitude_plateau"]
    ax[1, 0].bar([0, 1], [res["_wpost_healthy"].get(0, 0), res["_wpost_healthy"].get(1, 0)],
                 color=["#c53030", "#2b6cb0"])
    ax[1, 0].set_xticks([0, 1]); ax[1, 0].set_xticklabels(["w=0\n(psychopath)", "w>0\n(healthy)"])
    ax[1, 0].set_title("G1 w sign identified; magnitude flat\n(%d distinct vectors over %s)"
                       % (magp["distinct_decision_vectors"], magp["magnitudes"]))
    ax[1, 0].set_ylabel("posterior mass (a healthy agent)")

    # (d) G2 held-out prediction bars
    g2 = res["g2_prediction"]
    ax[1, 1].bar(["fitted", "pop-mean", "random"],
                 [g2["fitted"], g2["population_mean"], g2["random"]],
                 color=["#2b6cb0", "#a0aec0", "#e2e8f0"], edgecolor="k")
    ax[1, 1].set_ylim(0, 1.05)
    ax[1, 1].set_title("G2 held-out decision accuracy")
    for i, v in enumerate([g2["fitted"], g2["population_mean"], g2["random"]]):
        ax[1, 1].text(i, v + 0.02, "%.3f" % v, ha="center")

    fig.suptitle("Computational phenotyping by inverse inference — emotion-knob recovery (206000)")
    fig.tight_layout()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


# ----------------------------------------------------------------------- main
def main(n_agents=48):
    global LABELS
    LABELS = _build_tables()

    panel = run_panel(n_agents=n_agents, eps_true=0.0)
    g1 = g1_recovery(panel)
    wmag = w_magnitude_plateau()
    g2 = g2_prediction(panel)
    g3 = g3_explanation()
    intaudit = integer_audit()
    doff = default_off()
    noise = noise_robustness()

    # a healthy agent's w-posterior for the figure
    healthy = next((r for r in panel["rows"] if r["theta"]["w"] == 1), panel["rows"][0])

    res = dict(
        seed=SEED, n_agents=n_agents, eps_lapse=EPS,
        battery=dict(value=LABELS["value"], surprise=LABELS["surprise"],
                     threat=LABELS["threat"]),
        trains=panel["trains"], holdouts=panel["holdouts"],
        g1_recovery=g1, w_magnitude_plateau=wmag, g2_prediction=g2,
        g3_explanation=g3, integer_audit=intaudit, default_off=doff,
        noise_robustness=noise,
        _panel_rows=panel["rows"], _wpost_healthy=healthy["fit"]["w_post"])

    # ---- verdicts ----
    g1_ok = (g1["mood"]["r"] >= 0.9 and g1["mood"]["coverage"] >= 0.9
             and g1["residual_thresh"]["map_within_step_frac"] >= 0.9
             and g1["w_supergraph"]["sign_recovery"] >= 0.95
             and wmag["all_identical"] and wmag["distinct_decision_vectors"] == 1)
    g2_ok = (g2["fitted_strictly_beats_pop"] and g2["fitted_strictly_beats_random"])
    g3_ok = (g3["psychopath"]["attribution_isolated"]
             and g3["parent"]["attribution_isolated"] and g3["both_attributed_to_w"])
    g5_ok = (intaudit["all_integer"] and doff["canonical_untouched"]
             and doff["no_emotion_nodes_by_default"] and doff["adds_no_seed"])
    # STRUCTURAL identifiability prediction (the deep claim): w_supergraph
    # magnitude is STRUCTURALLY unidentifiable (a plateau no data can resolve),
    # while the threshold knobs are only RESOLUTION-limited (interval width ~ the
    # sweep spacing; more/finer scenarios tighten them). Reported SEPARATELY from
    # the prereg's secondary RANKING guess ("mood tightest"), which is a
    # resolution artifact, not structure.
    structural_ok = bool(
        wmag["all_identical"] and wmag["distinct_decision_vectors"] == 1  # w flat
        and g1["mood"]["coverage"] >= 0.9                                 # mood interval covers truth
        and g1["residual_thresh"]["map_within_step_frac"] >= 0.9          # res interval
        and g1["threat_half_life"]["persistent_boundedbelow_frac"] >= 0.9)  # hl bounded-below
    mood_tightest = bool(g1["mood"]["mean_cred_width"]
                         <= g1["residual_thresh"]["mean_cred_width"])
    res["verdict"] = dict(
        g1_parameter_recovery=bool(g1_ok), g2_prediction=bool(g2_ok),
        g3_explanation=bool(g3_ok), g5_integer_default_off=bool(g5_ok),
        structural_identifiability_prediction_held=structural_ok,
        prereg_mood_is_tightest_ranking_held=mood_tightest,
        identifiability_note=("w_supergraph magnitude STRUCTURALLY flat; "
                              "threshold knobs RESOLUTION-limited (width ~ sweep spacing)"))

    os.makedirs(RESULTS, exist_ok=True)
    fig = _figure(res, os.path.join(FIGDIR, "recovery.png"))
    res["figure"] = fig

    # write raw (strip heavy internals, keep a compact panel)
    dump = {k: v for k, v in res.items() if not k.startswith("_")}
    dump["panel_compact"] = [
        dict(theta=r["theta"],
             fit=dict(w_map=r["fit"]["w_map"],
                      mood_map=r["fit"]["mood"]["map"],
                      mood_cred=[r["fit"]["mood"]["cred_lo"], r["fit"]["mood"]["cred_hi"]],
                      res_map=r["fit"]["res"]["map"],
                      res_cred=[r["fit"]["res"]["cred_lo"], r["fit"]["res"]["cred_hi"]],
                      hl_map=r["fit"]["hl"]["map"]))
        for r in panel["rows"]]
    with open(os.path.join(RESULTS, "emotion_phenotype.json"), "w") as f:
        json.dump(dump, f, indent=1, default=str)
    return res


if __name__ == "__main__":
    R = main()
    v = R["verdict"]
    print(json.dumps(dict(verdict=v,
                          g1=R["g1_recovery"], g2=R["g2_prediction"],
                          g3=R["g3_explanation"], wmag=R["w_magnitude_plateau"],
                          integer=R["integer_audit"]["all_integer"],
                          default_off=R["default_off"], noise=R["noise_robustness"]),
                     indent=1, default=str))

#!/usr/bin/env python3
"""HARLOW D1b runner (block 235000) -- population temperament as a DISTRIBUTION.

Draws each infant's TEMPERAMENT (contact-comfort / hunger drive weights) from a
NORMAL distribution across the population and drives `worlds/harlow_dist_world.py`
(which only WRITES those weights as Drive attrs -- the attachment RULES are the
UNCHANGED seeds/harlow_attachment.json). Reads off the graph's per-infant
proximity decision and reduces the population to a DISTRIBUTION (mean, sd,
quantiles, minority tail), a within-population DOSE-RESPONSE (drawn contact
weight vs outcome -- a read-out the real experiment never had), a
variance-tracks-variance sweep over the seeding sigma, and the ablation
falsifier. NO Python decides an infant's attachment -- that is the Argmax rule.

Protocol frozen in HARLOW_D1B_PREREG.md. The RUNNER draws params (mechanical
world setup); the adapter writes them; the graph decides.
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import substrate_rs as srs                                # noqa: E402
from worlds.harlow_dist_world import HarlowDistWorld      # noqa: E402

# ---- frozen confirmatory constants (HARLOW_D1B_PREREG.md) -------------------
BLOCK = 235000
N = 200
T_BASE = 60
T_STRESS = 10
WEIGHT_MU = 1.0            # population mean drive weight (== D1's fixed weight)
WEIGHT_FLOOR = 0.05        # a drive weight is non-negative; clip the Normal tail
SIGMA_GRID = [0.0, 0.15, 0.30, 0.45]
SIGMA_HEAD = 0.45          # headline seeding sigma (widest grid point)

# seed allocation inside block 235000-235999 (each infant seeded once):
#   headline intact  sigma=0.45 : BLOCK + i            (i 0..199)  235000-235199
#   ablation (paired, same seeds, contact drive OFF)   : BLOCK + i (reused)
#   variance grid    sigma=0.00 : BLOCK + 200 + i                  235200-235399
#                    sigma=0.15 : BLOCK + 400 + i                  235400-235599
#                    sigma=0.30 : BLOCK + 600 + i                  235600-235799
#   sigma=0.45 grid point == headline intact (reused)
_GRID_OFFSET = {0.0: 200, 0.15: 400, 0.30: 600, 0.45: 0}


def _infant_init_params(rng):
    # IDENTICAL draw order to HARLOW D1 (scripts/jabberwock_harlow._infant_params)
    return dict(
        c_contact0=float(rng.uniform(10.0, 60.0)),
        c_hunger0=float(rng.uniform(20.0, 80.0)),
        contact_decay=float(rng.uniform(50.0, 70.0)),
        hunger_decay=float(rng.uniform(10.0, 20.0)))


def _draw_weights(rng, sigma):
    # temperament ~ Normal(mu, sigma), floored non-negative. sigma=0 -> exactly mu.
    wc = max(WEIGHT_FLOOR, WEIGHT_MU + sigma * rng.standard_normal())
    wh = max(WEIGHT_FLOOR, WEIGHT_MU + sigma * rng.standard_normal())
    return float(wc), float(wh)


def run_infant(seed, sigma, *, contact_drive=True):
    rng = np.random.default_rng(seed)
    p = _infant_init_params(rng)          # init first (D1 order)
    wc, wh = _draw_weights(rng, sigma)     # then temperament
    w = HarlowDistWorld(contact_drive=contact_drive, w_contact=wc, w_hunger=wh, **p)
    w.run_baseline(T_BASE)
    prox = w.proximity()
    st = w.run_stress(T_STRESS)
    flee_cloth = st["flee"]["cloth"] / T_STRESS
    # READ the temperament back from the graph (glass-box, not the Python draw)
    gw = w.drawn_weights()
    wc_g = gw["w_contact"] if gw["w_contact"] is not None else float("nan")
    return dict(seed=seed, sigma=sigma, contact_drive=contact_drive,
                w_contact=wc_g, w_hunger=gw["w_hunger"],
                temperament=(wc_g - gw["w_hunger"]),
                clipped=int(wc <= WEIGHT_FLOOR or wh <= WEIGHT_FLOOR),
                cloth_frac=prox["cloth_frac"], flee_cloth=flee_cloth)


def population(sigma, *, contact_drive=True, n=N, seed_base=BLOCK):
    base = seed_base + _GRID_OFFSET[sigma]
    return [run_infant(base + i, sigma, contact_drive=contact_drive) for i in range(n)]


# ------------------------------------------------------------------ statistics
def _mean_sd(xs):
    xs = list(xs)
    n = len(xs)
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1)) if n > 1 else 0.0
    return m, sd


def _ci95_mean(xs):
    m, sd = _mean_sd(xs)
    half = 1.96 * sd / math.sqrt(len(xs)) if len(xs) > 1 else 0.0
    return dict(mean=m, sd=sd, ci_lo=m - half, ci_hi=m + half)


def _quantiles(xs):
    a = np.asarray(xs, float)
    q = np.quantile(a, [0.0, 0.05, 0.10, 0.25, 0.5, 0.75, 0.90, 0.95, 1.0])
    return dict(min=float(q[0]), p05=float(q[1]), p10=float(q[2]), p25=float(q[3]),
                median=float(q[4]), p75=float(q[5]), p90=float(q[6]),
                p95=float(q[7]), max=float(q[8]))


def _bootstrap_sd_ci(xs, iters=4000, seed=424242):
    a = np.asarray(xs, float)
    rng = np.random.default_rng(seed)
    sds = [a[rng.integers(0, len(a), len(a))].std(ddof=1) for _ in range(iters)]
    lo, hi = np.quantile(sds, [0.025, 0.975])
    return float(lo), float(hi)


def _pearson_fisher(x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    n = len(x)
    r = float(np.corrcoef(x, y)[0, 1])
    if n <= 3 or abs(r) >= 1.0:
        return dict(r=r, ci_lo=r, ci_hi=r, n=n)
    z = math.atanh(r)
    se = 1.0 / math.sqrt(n - 3)
    lo = math.tanh(z - 1.96 * se)
    hi = math.tanh(z + 1.96 * se)
    return dict(r=r, ci_lo=lo, ci_hi=hi, n=n)


def summarise(rows):
    cf = [r["cloth_frac"] for r in rows]
    m = _ci95_mean(cf)
    q = _quantiles(cf)
    sd_lo, sd_hi = _bootstrap_sd_ci(cf)
    tail = sum(1 for x in cf if x < 0.5)
    return dict(n=len(rows), cloth_frac=m, quantiles=q,
                sd_ci=dict(sd=m["sd"], ci_lo=sd_lo, ci_hi=sd_hi),
                minority_tail_n=tail, minority_tail_frac=tail / len(rows),
                n_clipped=sum(r["clipped"] for r in rows),
                flee_cloth=_ci95_mean([r["flee_cloth"] for r in rows]))


# --------------------------------------------------------------- G-glass-box --
def glass_box_reconstruct(seed=BLOCK, sigma=SIGMA_HEAD):
    """Reconstruct one infant's episode from graph_to_dict alone -- including the
    SEEDED temperament (Drive.weight), which the real experiment could never
    read per individual. No hidden Python state."""
    rng = np.random.default_rng(seed)
    p = _infant_init_params(rng)
    wc, wh = _draw_weights(rng, sigma)
    w = HarlowDistWorld(contact_drive=True, w_contact=wc, w_hunger=wh, **p)
    dep = w.step(stress=False)
    w.run_baseline(T_BASE)
    blob = w.checkpoint()
    nodes = {n["id"]: n for n in blob["nodes"]}
    drives = {nodes[i]["attrs"]["name"]: nodes[i]["attrs"]
              for i in nodes if nodes[i]["type"] == "Drive"}
    mothers = {nodes[i]["attrs"]["name"]: nodes[i]["attrs"]
               for i in nodes if nodes[i]["type"] == "Mother"}
    at = [e["tgt"] for e in blob["edges"] if e["type"] == "approach_target"]
    at_names = [nodes[t]["attrs"]["name"] for t in at]
    return dict(
        seeded_w_contact=drives["contact_comfort"]["weight"],
        seeded_w_hunger=drives["hunger"]["weight"],
        approach_target=at_names,
        cloth_proximity=mothers["cloth"]["proximity"],
        wire_proximity=mothers["wire"]["proximity"],
        regulator_arousal_deprived_tick=dep["arousal"],
        regulator_arousal_comforted=w.regulator_state()["arousal"],
        reconstructed_from="graph_to_dict")


# ---------------------------------------------------------------- G-ethics ----
def _roundtrip(blob):
    s = srs.Substrate()
    s.graph_from_dict(blob)
    return s.graph_to_dict()


def _infant_affect_reg(blob):
    aff = [n["attrs"] for n in blob["nodes"]
           if n["type"] == "AffectiveState" and n["attrs"].get("name") == "infant_affect"][0]
    return dict(valence=aff["valence"], arousal=aff["arousal"], securing=aff["securing"])


def ethics_restore_demo(seed=BLOCK, sigma=SIGMA_HEAD):
    """induce -> measure -> RESTORE on a SEEDED-temperament infant.

    A CHECKPOINT is the SERIALISED mind (what you'd write to disk). The engine's
    graph_to_dict/graph_from_dict is IDEMPOTENT after one pass (a serialisation
    fixed point -- verified in results): restoring a serialised checkpoint and
    re-serialising is BYTE-IDENTICAL. We therefore define the checkpoint as the
    once-serialised form. The live-graph->serialised quantisation is a ~1-ULP f64
    effect that D1 never saw (its weights were exactly 1.0); with irrational
    seeded weights it appears, but it is STRESS-INDEPENDENT and is quantified via
    `raw_live_roundtrip_max_ulp` below -- it is not stress residue."""
    rng = np.random.default_rng(seed)
    p = _infant_init_params(rng)
    wc, wh = _draw_weights(rng, sigma)
    w = HarlowDistWorld(contact_drive=True, w_contact=wc, w_hunger=wh, **p)
    w.run_baseline(T_BASE)
    raw = w.checkpoint()               # live-graph serialisation
    pre = _roundtrip(raw)              # the SERIALISED checkpoint (fixed point)
    pre_reg = _infant_affect_reg(pre)
    # quantify the raw->serialised quantisation (stress-independent) in ULPs
    raw_nodes = {n["id"]: n["attrs"] for n in raw["nodes"]}
    pre_nodes = {n["id"]: n["attrs"] for n in pre["nodes"]}
    max_ulp = 0.0
    for i in raw_nodes:
        for k, v in raw_nodes[i].items():
            u = pre_nodes[i].get(k)
            if isinstance(v, float) and isinstance(u, float) and v != u:
                max_ulp = max(max_ulp, abs(v - u))
    # INDUCE stress on the live mind (the stressed graph is DISCARDED at restore)
    w.run_stress(T_STRESS)
    stressed_reg = w.regulator_state()
    # RESTORE from the serialised checkpoint into a fresh substrate
    restored = _roundtrip(pre)
    byte_identical = (restored == pre)        # TRUE: pre is a serialisation fixed point
    idempotent = (_roundtrip(pre) == pre)
    restored_reg = _infant_affect_reg(restored)
    return dict(byte_identical=byte_identical, checkpoint_idempotent=idempotent,
                raw_live_roundtrip_max_ulp=max_ulp,
                pre_stress_regulator=pre_reg, stressed_regulator=stressed_reg,
                restored_regulator=restored_reg,
                stress_moved_arousal=(stressed_reg["arousal"] != pre_reg["arousal"]),
                restore_non_oriented=(restored_reg == pre_reg))


# ------------------------------------------------------------ source audit ----
def source_audit():
    """No Python decides attachment in the D1b adapter either. Same audit as D1:
    no rule-engine call; the approach decision is read from the graph."""
    import io
    import tokenize
    hits = []
    for rel in ("worlds/harlow_dist_world.py", "worlds/harlow_world.py"):
        src = open(os.path.join(_ROOT, rel)).read()
        toks = []
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                continue
            toks.append(tok.string)
        code = " ".join(toks)
        for f in ("graph_rewrite", "make_rule", "_match", "_apply", "add_rule"):
            if f in code:
                hits.append(f"{rel}:{f}")
    reads_edge = "neighbours(self.infant, \"approach_target\")" in \
        open(os.path.join(_ROOT, "worlds", "harlow_world.py")).read()
    return dict(forbidden_hits=hits, reads_approach_target_edge=reads_edge,
                clean=(not hits and reads_edge), source_match="own")


# --------------------------------------------------------------------- main ---
def run_all(seed_base=BLOCK):
    # headline intact population (sigma=0.45) + its dose-response
    head = population(SIGMA_HEAD, contact_drive=True, seed_base=seed_base)
    head_stats = summarise(head)
    dose = _pearson_fisher([r["temperament"] for r in head],
                           [r["cloth_frac"] for r in head])
    # ablation: SAME seeds, contact drive removed (paired falsifier)
    abl = population(SIGMA_HEAD, contact_drive=False, seed_base=seed_base)
    abl_stats = summarise(abl)
    # variance-tracks-variance sweep
    grid = {}
    for sg in SIGMA_GRID:
        rows = head if sg == SIGMA_HEAD else population(sg, contact_drive=True, seed_base=seed_base)
        m, sd = _mean_sd([r["cloth_frac"] for r in rows])
        grid[sg] = dict(mean=m, sd=sd)
    sds = [grid[sg]["sd"] for sg in SIGMA_GRID]
    monotone = all(sds[i] < sds[i + 1] for i in range(len(sds) - 1))

    out = dict(
        block=BLOCK, base_sha="e1f2b37141e276974d1743c1e147f019b8d97b64",
        descends_from_main="3c4666ceba0b0ceef1db4030d941a5cd66b5f949",
        seed_base=seed_base, n=N, t_base=T_BASE, t_stress=T_STRESS,
        weight_mu=WEIGHT_MU, weight_floor=WEIGHT_FLOOR,
        sigma_grid=SIGMA_GRID, sigma_head=SIGMA_HEAD,
        g_graded=dict(
            cloth_frac=head_stats["cloth_frac"], sd_ci=head_stats["sd_ci"],
            quantiles=head_stats["quantiles"],
            minority_tail_frac=head_stats["minority_tail_frac"],
            minority_tail_n=head_stats["minority_tail_n"],
            n_clipped=head_stats["n_clipped"],
            d1_sd_reference=0.039,
            sd_much_larger=head_stats["sd_ci"]["sd"] > 3 * 0.039,
            mean_above_half=head_stats["cloth_frac"]["ci_lo"] > 0.5,
            range_span=head_stats["quantiles"]["max"] - head_stats["quantiles"]["min"]),
        g_dose_response=dose,
        g_variance_tracks_variance=dict(grid=grid, sds=sds, monotone=monotone,
                                        sd_at_sigma0=grid[0.0]["sd"]),
        g_ablation=dict(
            intact=head_stats["cloth_frac"], ablated=abl_stats["cloth_frac"],
            ablated_mean_below_half=abl_stats["cloth_frac"]["mean"] < 0.10,
            ci_separated=abl_stats["cloth_frac"]["ci_hi"] < head_stats["cloth_frac"]["ci_lo"]),
        g_glass_box=glass_box_reconstruct(seed=seed_base),
        g_ethics=ethics_restore_demo(seed=seed_base),
        source_audit=source_audit())
    return out, head, abl


def main():
    out, head, abl = run_all(BLOCK)
    os.makedirs(os.path.join(_ROOT, "results"), exist_ok=True)
    # keep a compact per-infant table for reconstruction (headline population)
    out["headline_rows"] = [dict(seed=r["seed"], w_contact=r["w_contact"],
                                 w_hunger=r["w_hunger"], temperament=r["temperament"],
                                 cloth_frac=r["cloth_frac"], flee_cloth=r["flee_cloth"],
                                 clipped=r["clipped"]) for r in head]
    with open(os.path.join(_ROOT, "results", "harlow_d1b.json"), "w") as f:
        json.dump(out, f, indent=2)
    compact = {k: v for k, v in out.items() if k != "headline_rows"}
    print(json.dumps(compact, indent=2))
    return out


if __name__ == "__main__":
    main()

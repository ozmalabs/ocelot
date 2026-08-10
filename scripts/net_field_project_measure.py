"""THE PROJECT'S OWN NET as the per-cell field PROPOSAL — block 133000 (SPINE).

Pre-registration: VISION_NET_FIELD_PROPOSAL_PREREG.md. This is the mechanism the
CONFIRM/DEGRADE/FALSIFY verdict RESTS ON (coordinator correction): NOT host-side
torch, but the project's graph-native self-learning net —
`domains/cascade_net.py` (CascadeNet: stacked ELM blocks, fixed random features +
local delta-rule readout, NO backprop) driven by the Rust `cascade_collapse_step`
(the WeightTensor twin of hebbian_update_J, self-training in the collapse loop).
The refusal gate is the EXISTING external basin gate (`reflex_net_basin_gate_is_external`,
seeds/reflex_net.json): the substrate refuses where the net's proposal diverges
from its OWN lawful reconstruction (the held CA rule) — a grounded, net-independent
check, NOT the net's confidence.

torch (scripts/net_field_proposal_measure.py) is kept ONLY as a labeled
UPPER-BOUND predictability PROBE ("can ANY small net predict this field") and a
measure of the spatial-batching gap the project's net lacks.

USAGE
  PYTHONPATH=runners/dsl/python:. python scripts/net_field_project_measure.py \
      --out results/net_field_project.json
"""
from __future__ import annotations
import argparse, gc, json, os, statistics, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from domains.engine_provenance import engine_preamble, provenance_line, provenance_stamp  # noqa: E402
engine_preamble()

import numpy as np  # noqa: E402
from substrate_rs import _native  # noqa: E402
import domains.cascade_net as CN  # noqa: E402
import scripts.net_field_proposal_measure as M  # reuse data/encode/ca/auroc  # noqa: E402

REST, ACT, REC, REF = 0, 1, 2, 3
IGNITE_EVERY = 5

DATA_GRID = 32
WARMUP_STEPS = 40
TRAIN_STEPS = 160
TEST_STEPS = 160
TRAIN_WORLDS = [133000, 133001, 133002, 133003]
TEST_WORLDS = list(range(133100, 133105))     # 5 confirmatory held-out worlds
SEED_NET = 133500
PATCH_R = 1                                    # radius-1 = 3x3 patch (matches the CA)
CAPACITY = [(4, 32), (6, 64), (8, 96)]         # (n_blocks, hidden) sweep
PRIMARY = (6, 64)                              # the headline spine config
EPOCHS = 6
ETA0 = 0.03
GRIDS_TIME = [16, 24, 32, 48, 64]
TRIALS_TIME = 7
TIME_FWD = 4000                                # forwards timed per trial


_NODE = ("CascadeNet", "NetworkAssemblage", "AssemblageStep", "WeightTensor")
_EDGE = ("has_block", "has_step", "has_weight")


def _fresh():
    """A raw substrate admitting the net vocabulary (the cascade-test setup)."""
    s = _native.Substrate()
    for a in _NODE:
        for b in _NODE:
            for et in _EDGE:
                s.add_production({"src": {"type": a, "var": "s"}, "edge_type": et,
                                  "tgt": {"type": b, "var": "t"}, "where": None,
                                  "weight": {"type": "Lit", "value": 1.0}, "provenance": "t"})
    return s


def _loadavg():
    try:
        return list(os.getloadavg())
    except OSError:
        return None


def patches(seq, R=PATCH_R):
    """Per-cell radius-R patch of the 6-channel encoding -> flat feature; target =
    next-state class. Also the ignition-touched mask (exogenous surprise)."""
    X, Y, IG = [], [], []
    for a, b in zip(seq[:-1], seq[1:]):
        enc = M.encode(a["S"], a["A"], a["F"], a["step"])
        H, W = a["S"].shape
        pad = np.pad(enc, ((0, 0), (R, R), (R, R)))
        m = np.zeros((H, W), bool)
        for (r, c) in b["ignite"]:
            m[r, c] = True
        nb = m.copy()
        nb[1:, :] |= m[:-1, :]; nb[:-1, :] |= m[1:, :]
        nb[:, 1:] |= m[:, :-1]; nb[:, :-1] |= m[:, 1:]
        for r in range(H):
            for c in range(W):
                X.append(pad[:, r:r + 2 * R + 1, c:c + 2 * R + 1].ravel())
                Y.append(int(b["S"][r, c])); IG.append(bool(nb[r, c]))
    return np.asarray(X, np.float64), np.asarray(Y), np.asarray(IG)


def build_and_train(indim, n_blocks, hidden, Xtr, Ytr, epochs, eta0, seed):
    """The PROJECT's net, SELF-TRAINED online by the delta-rule collapse step
    (cascade_collapse_step -> net_collapse_step; NO backprop, one update per
    observed (patch, target) pair — the collapse-loop self-training)."""
    s = _fresh()
    c = CN.build(s, "field", n_blocks=n_blocks, in_dim=indim, out_dim=4,
                 hidden=hidden, seed=seed)
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(Ytr))
    t0 = time.perf_counter()
    surpr = 0.0
    for ep in range(epochs):
        eta = eta0 / (1.0 + 0.05 * ep)
        acc = 0.0
        for i in order:
            tgt = [0.0, 0.0, 0.0, 0.0]; tgt[Ytr[i]] = 1.0
            acc += CN.train_step(s, c, Xtr[i].tolist(), tgt, eta)
        surpr = acc / len(order)
    return s, c, time.perf_counter() - t0, surpr


def eval_project(s, c, test_patch):
    """Per-cell accuracy of the project net (argmax of cascade_forward), split
    deterministic vs exogenous-ignition."""
    X, Y, IG = test_patch
    preds = np.empty(len(Y), np.int64)
    scores = np.empty((len(Y), 4), np.float64)
    t0 = time.perf_counter()
    for i in range(len(Y)):
        o = CN.forward(s, c, X[i].tolist())
        scores[i] = o
        preds[i] = int(np.argmax(o))
    fwd_s = time.perf_counter() - t0
    err = preds != Y
    det = ~IG
    out = {
        "cell_accuracy": float((~err).mean()),
        "det_accuracy": float((~err & det).sum() / max(det.sum(), 1)),
        "ignition_accuracy": float((~err & IG).sum() / max(IG.sum(), 1)),
        "per_class_accuracy": {int(k): float((preds[Y == k] == k).mean()) if (Y == k).sum() else None
                               for k in range(4)},
        "per_class_n": {int(k): int((Y == k).sum()) for k in range(4)},
        "n": int(len(Y)), "us_per_forward": fwd_s / len(Y) * 1e6,
    }
    return out, preds, scores


def refusal_project(preds, scores, test_patch, test_seqs):
    """H3 with the PROJECT net + the PROJECT external gate. Two signals per cell:
      confidence (SELECTION) = 1 - softmax_max of the net's own scores.
      comparison (COMPARISON = external gate) = net's proposal disagreement with the
        substrate's OWN lawful reconstruction S_det (the held CA rule) — a grounded,
        net-independent check (reflex_net_basin_gate_is_external). We use the graded
        form: 1 - net's normalized score on the lawful class.
    Reported ALL / deterministic-only / ignition-only; paired bootstrap on AUROC."""
    X, Y, IG = test_patch
    # softmax of scores
    sc = scores - scores.max(1, keepdims=True)
    ex = np.exp(sc); prob = ex / ex.sum(1, keepdims=True)
    conf = 1.0 - prob.max(1)
    # lawful class per cell = the deterministic reconstruction, laid out per patch
    sdet_flat = []
    for seq in test_seqs:
        for a in seq[:-1]:
            sdet_flat.append(M.deterministic_next(a).ravel())
    sdet = np.concatenate(sdet_flat).astype(np.int64)
    lawful_prob = prob[np.arange(len(Y)), sdet]
    comp = 1.0 - lawful_prob
    lab = (preds != Y)
    rng = np.random.default_rng(133600)

    def paired(mask, n_boot=2000, neg_cap=40000):
        idx = np.where(mask if mask is not None else np.ones_like(lab, bool))[0]
        L = lab[idx]
        if L.sum() == 0 or (~L).sum() == 0:
            return {"auroc_comparison": None, "auroc_confidence": None,
                    "paired_diff": None, "ci": [None, None], "sep": "undef",
                    "n_pos": int(L.sum()), "n": int(len(idx))}
        ac = M._auroc(comp[idx], L); af = M._auroc(conf[idx], L)
        pos = idx[L]; neg = idx[~L]
        if len(neg) > neg_cap:
            neg = rng.choice(neg, neg_cap, replace=False)
        sub = np.concatenate([pos, neg]); cs = comp[sub]; cf = conf[sub]; ls = lab[sub]
        m = len(sub); d = []
        for _ in range(n_boot):
            r = rng.integers(0, m, m); Lr = ls[r]
            if Lr.sum() == 0 or (~Lr).sum() == 0:
                continue
            d.append(M._auroc(cs[r], Lr) - M._auroc(cf[r], Lr))
        lo, hi = (float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))) if d else (None, None)
        return {"auroc_comparison": float(ac), "auroc_confidence": float(af),
                "paired_diff": float(ac - af), "ci": [lo, hi],
                "sep": ("SEP+" if lo and lo > 0 else ("SEP-" if hi and hi < 0 else "ns")),
                "n_pos": int(L.sum()), "n": int(len(idx))}
    return {"all_errors": paired(None),
            "deterministic_errors": paired(~IG),
            "ignition_errors_within": paired(IG),
            "counts": {"n_cells": int(len(lab)), "n_err": int(lab.sum()),
                       "n_det_err": int((lab & ~IG).sum()), "n_ign_err": int((lab & IG).sum())}}


def time_project_forward(s, c, indim, grids, trials, n_fwd):
    """Per-cell forward cost of the project net (per-query PyO3, NO spatial batching).
    Cost is per-forward-constant (each cell is an independent net_forward), so
    us/cell == us/forward; the field cost is N x that. Measured ALONE."""
    rng = np.random.default_rng(SEED_NET)
    feats = [rng.standard_normal(indim).tolist() for _ in range(256)]
    rows = []
    for g in grids:
        per = []
        for t in range(trials):
            for k in range(50):
                CN.forward(s, c, feats[k % 256])
            t0 = time.perf_counter()
            for k in range(n_fwd):
                CN.forward(s, c, feats[k % 256])
            per.append((time.perf_counter() - t0) / n_fwd * 1e6)   # us/forward
        med = float(statistics.median(per))
        cells = g * g
        rows.append({"grid": g, "cells": cells, "us_per_forward": med,
                     "us_per_cell": med, "field_ms": med * cells / 1000.0})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()

    prov = provenance_line()
    load0 = _loadavg()
    print(prov, flush=True)
    print(f"loadavg start {load0}", flush=True)

    tw = TRAIN_WORLDS[:2] if a.quick else TRAIN_WORLDS
    testw = TEST_WORLDS[:2] if a.quick else TEST_WORLDS
    trs = 60 if a.quick else TRAIN_STEPS
    tes = 60 if a.quick else TEST_STEPS
    caps = [(4, 32)] if a.quick else CAPACITY
    epochs = 3 if a.quick else EPOCHS

    res = {"provenance": prov, "provenance_stamp": provenance_stamp(),
           "loadavg_start": load0,
           "mechanism": "PROJECT cascade net (domains/cascade_net.py) self-trained by "
                        "Rust cascade_collapse_step (delta rule, NO backprop); external "
                        "basin gate = reflex_net_basin_gate_is_external (lawful reconstruction).",
           "config": {"data_grid": DATA_GRID, "train_worlds": tw, "test_worlds": testw,
                      "train_steps": trs, "test_steps": tes, "patch_radius": PATCH_R,
                      "capacity_sweep": caps, "primary": PRIMARY, "epochs": epochs,
                      "eta0": ETA0, "net_seed": SEED_NET, "ignite_every": IGNITE_EVERY},
           "block_seeds_drawn": {"train_worlds": tw, "test_worlds": testw, "net_seed": SEED_NET}}

    print("== engine data ==", flush=True)
    train_seqs = [M.record_world(DATA_GRID, sd, trs, WARMUP_STEPS) for sd in tw]
    test_seqs = [M.record_world(DATA_GRID, sd, tes, WARMUP_STEPS) for sd in testw]
    Xtr, Ytr, _ = ([], [], [])
    xs, ys = [], []
    for seq in train_seqs:
        X, Y, _ = patches(seq); xs.append(X); ys.append(Y)
    Xtr = np.concatenate(xs); Ytr = np.concatenate(ys)
    test_patch = patches_concat(test_seqs)
    indim = Xtr.shape[1]
    print(f"  patch_dim {indim} train_patches {len(Ytr)} test_patches {len(test_patch[1])}", flush=True)

    # capacity sweep (predictability of the PROJECT net)
    res["capacity_sweep"] = []
    primary_state = None
    for (nb, hid) in caps:
        s, c, train_s, surpr = build_and_train(indim, nb, hid, Xtr, Ytr, epochs, ETA0, SEED_NET)
        pred_stats, preds, scores = eval_project(s, c, test_patch)
        row = {"n_blocks": nb, "hidden": hid, "train_seconds": train_s,
               "final_surprise": surpr, **pred_stats}
        res["capacity_sweep"].append(row)
        print(f"  nb={nb} hid={hid}: cell_acc {pred_stats['cell_accuracy']:.4f} "
              f"det {pred_stats['det_accuracy']:.4f} ign {pred_stats['ignition_accuracy']:.4f} "
              f"class2(front) {pred_stats['per_class_accuracy'][2]} "
              f"train {train_s:.1f}s us/fwd {pred_stats['us_per_forward']:.1f}", flush=True)
        if (nb, hid) == PRIMARY or (a.quick and primary_state is None):
            primary_state = (s, c, preds, scores)
            res["primary"] = row

    # refusal on the PRIMARY net
    print("== refusal (external gate vs net-confidence) ==", flush=True)
    s, c, preds, scores = primary_state
    res["refusal"] = refusal_project(preds, scores, test_patch, test_seqs)
    for k in ("all_errors", "deterministic_errors", "ignition_errors_within"):
        v = res["refusal"][k]
        print(f"  {k:22s} comp {v['auroc_comparison']} conf {v['auroc_confidence']} "
              f"diff {v['paired_diff']} {v['sep']} n_pos {v['n_pos']}", flush=True)

    # timing: per-cell forward cost (ALONE) + scale projection
    print("== timing: project-net per-cell forward (ALONE) ==", flush=True)
    res["timing"] = time_project_forward(s, c, indim, GRIDS_TIME, TRIALS_TIME, TIME_FWD)
    for r in res["timing"]:
        print(f"  g={r['grid']:3d} cells={r['cells']:5d} us/forward {r['us_per_forward']:.2f} "
              f"-> field {r['field_ms']:.2f} ms (project net, per-cell PyO3, NO batching)", flush=True)

    res["loadavg_end"] = _loadavg()
    res["provenance_after"] = provenance_line()
    st = provenance_stamp(); res["source_match_after"] = st.get("source_match")
    assert st.get("source_match") in ("own", "shared"), st

    d = os.path.dirname(a.out)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump(res, fh, indent=2, default=str)
    print("wrote", a.out, flush=True)
    print(f"loadavg end {res['loadavg_end']} source_match {res['source_match_after']}", flush=True)


def patches_concat(seqs):
    xs, ys, ig = [], [], []
    for seq in seqs:
        X, Y, I = patches(seq); xs.append(X); ys.append(Y); ig.append(I)
    return np.concatenate(xs), np.concatenate(ys), np.concatenate(ig)


if __name__ == "__main__":
    main()

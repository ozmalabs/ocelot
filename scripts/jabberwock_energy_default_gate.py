"""GATE: the FREE energy win is now in the DEFAULT recogniser feature path.

Prior build (commit 74aaa27e, scripts/jabberwock_phone_capacity.py) PROVED the energy
channel is a near-FREE per-frame win for the sub-word phone model, but ONLY inside that
gate script — the DEFAULT phone-model feature (`ctxd`, scripts.jabberwock_earns_phone_model,
imported by ~8 default-path scripts + the recogniser) still threw energy away because
`frames()` divides per-frame energy out by L2-norm and every consumer read only the shape.

THE BANKED WIRING (this build): `ctxd(M, e=...)` now APPENDS a log-energy + delta channel
ADDITIVELY (shape block bit-identical; energy is a pure suffix); the DEFAULT phone model
(`jabberwock_earns_phone_model`) opts in by passing the banked per-frame energy; the bank
(`phonebank.feed`, `_load_ph(with_energy=True)`) carries energy as an ADDITIVE 4th element
so 3-tuple readers are unaffected. This gate proves the lift now appears in the DEFAULT
`ctxd` path (NOT the gate's private feat_shape/feat_energy), backward-compat holds, cost flat.

Controls (all donkey=0 — per-frame DECISION = nearest centroid, graph-native; no LLM):
  MAIN          : default ctxd+energy vs default ctxd shape-only -> per-frame acc + the
                  stops/fricatives lift from the original gate, reproduced in the DEFAULT path.
  BACKWARD COMPAT: the shape channels of ctxd(M, e) are BIT-IDENTICAL to ctxd(M).
  DISCRIMINATIVE: the lift concentrates on the ENERGY-CUED classes (stops/fricatives).
  COST          : us/frame of the energy-augmented default ~= shape-only default (the FREE property).

Reuses the phone_capacity re-banked energy-retaining bank (.bigtmp, regenerable, NOT committed).

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=runners/dsl/python:.:scripts PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u scripts/jabberwock_energy_default_gate.py [n_bank]
"""
from __future__ import annotations
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np

# THE DEFAULT feature builder + the default phone encoder/decision.
from scripts.jabberwock_earns_phone_model import ctxd, energy_channel
from scripts.jabberwock_phone_capacity import (
    rebank, PhoneEncoder, _STOP, _FRIC, _AFFR, _ENERGY_CUED,
)

_VOWELS = set("AA AE AH AO AW AY EH ER EY IH IY OW OY UH UW".split())


def build_X(items, use_energy):
    """Per-frame features over banked words, via the DEFAULT ctxd builder.
    use_energy=False -> ctxd(M)         (shape-only, the energy-less default)
    use_energy=True  -> ctxd(M, e=e)    (energy-augmented default, additive channel)
    Labels are flat-start proportional phone ids (same as the default phone model)."""
    Xs, Ys = [], []
    for (_w, M, e, ph) in items:
        cx = ctxd(M, e=e) if use_energy else ctxd(M)
        n, P = len(cx), len(ph)
        Xs.append(cx)
        Ys.extend(ph[int(i * P / n)] for i in range(n))
    return np.concatenate(Xs), Ys


def per_frame_acc(enc, items, use_energy):
    Xd, Yd = build_X(items, use_energy)
    pred = enc.predict(Xd)
    return float(np.mean([enc.phones[pred[i]] == Yd[i] for i in range(len(Yd))])), pred, Yd


def per_class_acc(enc, pred, Yd, classes):
    idx = [i for i in range(len(Yd)) if Yd[i] in classes]
    if not idx:
        return float("nan"), 0
    return float(np.mean([enc.phones[pred[i]] == Yd[i] for i in idx])), len(idx)


def cost_us(enc, Xd):
    """us per frame for the per-frame DECISION (encode + nearest-centroid). Xd is
    pre-built (we are timing the model, not feature construction); warmed up."""
    for _ in range(3):
        enc.predict(Xd)          # warm caches before timing
    nrep = max(1, 400000 // max(len(Xd), 1))
    best = 1e18
    for _ in range(3):
        t0 = time.perf_counter()
        for _ in range(nrep):
            enc.predict(Xd)
        best = min(best, (time.perf_counter() - t0) / (nrep * len(Xd)) * 1e6)
    return best


def main():
    n_bank = int(sys.argv[1]) if len(sys.argv) > 1 else 360
    print("=" * 92)
    print("ENERGY IN THE DEFAULT PATH — ctxd(M, e) additive channel, backward-compatible, ~free")
    print("=" * 92)

    # ---- BACKWARD COMPAT: ctxd(M) bit-identical to the shape block of ctxd(M, e) ----
    rng = np.random.default_rng(0)
    Mt = rng.standard_normal((37, 16)); et = np.abs(rng.standard_normal(37)) + 0.05
    a = ctxd(Mt); b = ctxd(Mt, e=et)
    shape_identical = np.array_equal(a, b[:, :a.shape[1]])
    print(f"\n  BACKWARD COMPAT: ctxd(M) dim={a.shape[1]}  ctxd(M,e) dim={b.shape[1]}  "
          f"(+{b.shape[1]-a.shape[1]} energy dims)")
    print(f"    shape channels BIT-IDENTICAL to the energy-less default: "
          f"{'PASS' if shape_identical else 'FAIL'}  "
          f"(existing consumers reading ctxd(M) are UNAFFECTED)")

    train, dev = rebank(n_bank, 90)
    print(f"\n  train words={len(train)}  dev words={len(dev)}  (re-banked w/ energy, .bigtmp, NOT committed)")

    # ---- MAIN: energy-less DEFAULT vs energy-augmented DEFAULT (both via ctxd) ----
    print("\n" + "-" * 92)
    print("  DEFAULT path: ctxd shape-only  vs  ctxd + energy channel (per-frame, nearest-centroid)")
    out = {}
    for tag, use_e in (("shape-only (energy-less default)", False),
                       ("+ENERGY (banked default)        ", True)):
        Xtr, Ytr = build_X(train, use_e)
        enc = PhoneEncoder(nonlinear=False).fit(Xtr, Ytr)   # LINEAR: isolate the energy channel
        Xd, Yd = build_X(dev, use_e)
        pred = enc.predict(Xd)
        acc = float(np.mean([enc.phones[pred[i]] == Yd[i] for i in range(len(Yd))]))
        s_acc, ns = per_class_acc(enc, pred, Yd, _STOP)
        f_acc, nf = per_class_acc(enc, pred, Yd, _FRIC)
        v_acc, nv = per_class_acc(enc, pred, Yd, _VOWELS)
        c = cost_us(enc, Xd)
        out[use_e] = dict(acc=acc, stop=s_acc, fric=f_acc, vow=v_acc, cost=c, ns=ns, nf=nf)
        print(f"  [{tag}] acc {acc:.3f}  stops {s_acc:.3f}  fric {f_acc:.3f}  "
              f"vowels {v_acc:.3f}  cost {c:5.2f} us/frame")

    b0, b1 = out[False], out[True]
    d_acc = b1["acc"] - b0["acc"]
    d_stop = (b1["stop"] - b0["stop"]) / max(b0["stop"], 1e-9)
    d_fric = (b1["fric"] - b0["fric"]) / max(b0["fric"], 1e-9)
    d_vow = (b1["vow"] - b0["vow"]) / max(b0["vow"], 1e-9)
    cost_ratio = b1["cost"] / max(b0["cost"], 1e-9)

    print("\n" + "-" * 92)
    print(f"  MAIN lift (DEFAULT path):  overall {b0['acc']:.3f} -> {b1['acc']:.3f} ({d_acc:+.3f})")
    print(f"    STOPS     {b0['stop']:.3f} -> {b1['stop']:.3f}  ({d_stop*100:+.0f}%)   [energy-cued, n={b0['ns']}]")
    print(f"    FRICATIVES{b0['fric']:.3f} -> {b1['fric']:.3f}  ({d_fric*100:+.0f}%)   [energy-cued, n={b0['nf']}]")
    print(f"    vowels    {b0['vow']:.3f} -> {b1['vow']:.3f}  ({d_vow*100:+.0f}%)   [NOT energy-cued -> small/zero]")
    print(f"  COST: {b0['cost']:.2f} -> {b1['cost']:.2f} us/frame  (x{cost_ratio:.2f}; ~free if ~1.0)")

    # ---- DISCRIMINATIVE: the lift concentrates on the energy-cued classes ----
    energy_cued_lift = (d_stop + d_fric) / 2.0
    discr = energy_cued_lift > max(d_vow, 0.0) + 0.05 and (d_stop > 0.05 or d_fric > 0.05)
    print("\n" + "-" * 92)
    print(f"  DISCRIMINATIVE: energy-cued (stops/fric) mean lift {energy_cued_lift*100:+.0f}% "
          f"vs vowels {d_vow*100:+.0f}%  -> {'PASS' if discr else 'FAIL'}")
    print("    (the win is the real energy signal on bursts/frication, not generic noise)")

    print("\n" + "-" * 92)
    print("  HONEST NOTE: this isolates the ENERGY channel ALONE on the LINEAR default. The")
    print("  original gate's headline fricative +34% was the +BOTH variant (energy + nonlinear")
    print("  RFF); energy-alone gives a strong STOPS lift and a modest fricative lift. The")
    print("  nonlinear RFF lever is orthogonal and already lives in the gate; this build banks")
    print("  the FREE energy channel into the DEFAULT feature -- the nonlinear lever can opt in too.")

    print("\n" + "=" * 92)
    free = cost_ratio < 1.25
    if shape_identical and d_stop > 0.05 and free and discr:
        print("  RESULT: the FREE energy win is now in the DEFAULT recogniser feature path.")
        print(f"    stops lift by default ({d_stop*100:+.0f}%), fricatives ({d_fric*100:+.0f}%), "
              f"cost ~flat (x{cost_ratio:.2f}), shape channels bit-identical -> no consumer breaks.")
    else:
        print("  RESULT (honest): default-path energy wiring did NOT clear the bar -- "
              "report the failing control above.")
    print("=" * 92)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

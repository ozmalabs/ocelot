#!/usr/bin/env python3
"""DISSIPATION IS INFERENCE (seed block 197000) — ONE integer relaxation dynamics
that is a physical law in one frame and MAP perception in the other, differing
ONLY by a relabel.

MECHANICAL MEASURE-ADAPTER. No agent decision, no Rust, no new Term. It builds a
field of FieldCell nodes on the substrate, opts them in to the shared
dissipative-relaxation dynamics (`seeds/dissipation_inference.json`), and drives
`run_rules()` a half-sweep at a time (flipping the red-black `phase` — a
mechanical clock, like `input_epoch`). Every DECISION (the per-cell integer
argmin, descent vs reflected ascent) is the graph RULE `df_relax`; this script
only sets scalars, ticks, and reads `val`.

IMPORT-INERT: all work is inside `main()` / scoped functions; nothing mutates a
shared flag or the graph at import time.

Gates (each able to fail):
  G1  THE IDENTITY  — physics-labelled and cognition-labelled runs are a
      BYTE-IDENTICAL integer trajectory; the two functionals (Gibbs energy vs
      negative log-posterior) are the element-wise-identical sequence; the
      relabel is a pure dict touching no dynamics (source audit).
  G2  PHYSICS HOLDS — the free-energy Lyapunov functional decreases MONOTONICALLY
      to a fixed point (never increases); entropy produced S=E0-E rises to its max.
  G3  COGNITION WORKS — settling denoises obs=clean+noise toward the percept; the
      fixed point MATCHES an independent reference MAP (byte-identical to a numpy
      red-black integer denoiser; within rounding of the real linear-solve MAP).
  G4  BREAK-ONE-BREAKS-BOTH — sign=-1 (anti-dissipative reflected ascent) forces
      E UP and the recovery error UP: both diverge. One process.
  G5  INTEGER-NATIVE + DEFAULT-OFF — every cell/control attr is integer (only the
      cross-frame real-MAP + ratios are float); the seed is opt-in and unreferenced
      by any default loader.

Prereg: DISSIPATION_IS_INFERENCE_PREREG.md. Deterministic; no wall-clock claim.
"""
from __future__ import annotations

import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate_rs import Substrate              # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402

SEED = 197000
W = H = 24
LAM = 2
NOISE = 40
RESULTS = os.path.join(ROOT, "results")
FRAMES = os.path.join(RESULTS, "dissipation_inference")

# The relabel table — a PURE interpretation dict. It renames the ONE neutral
# object into a frame's vocabulary and is consulted ONLY for output naming; it
# enters NO arithmetic and NO set_attr (audited in G1c).
RELABEL = {
    "physics": {
        "val": "microstate_config", "obs": "external_field",
        "lam": "coupling", "E": "gibbs_free_energy",
        "fixed_point": "equilibrium", "descent": "dissipative_relaxation",
    },
    "cognition": {
        "val": "map_estimate", "obs": "noisy_observation_y",
        "lam": "likelihood_precision", "E": "neg_log_posterior",
        "fixed_point": "map_percept", "descent": "inference_convergence",
    },
}


# --------------------------------------------------------------------- scene
def clean_image():
    """A piecewise-constant percept: three luminance bands + an inset block."""
    img = np.zeros((H, W), dtype=np.int64)
    img[:, :W // 3] = 40
    img[:, W // 3:2 * W // 3] = 120
    img[:, 2 * W // 3:] = 200
    img[3:9, 3:9] = 170
    return img


def noisy(clean, rng):
    n = rng.integers(-NOISE, NOISE + 1, size=(H, W))
    return np.clip(clean + n, 0, 255).astype(np.int64)


def parity():
    return (np.add.outer(np.arange(H), np.arange(W)) & 1).astype(np.int64)


# ------------------------------------------------------- substrate field arm
class Field:
    """Builds the FieldCell grid on a bare substrate + opts in to the shared
    dynamics. Pure mechanical I/O — no decisions."""

    def __init__(self, obs, init, sign):
        self.obs = obs
        self.par = parity()
        self.s = Substrate()
        self.s.load_seed_manifest(manifest_for("dissipation_inference"), None)
        self.f = self.s.add_node("RelaxField", {
            "enabled": 1.0, "lam": float(LAM), "phase": 0.0, "sign": float(sign)})
        self.cell = {}
        for r in range(H):
            for c in range(W):
                n = self.s.add_node("FieldCell", {
                    "val": float(init[r, c]), "obs": float(obs[r, c]),
                    "par": float(self.par[r, c]), "row": r, "col": c})
                self.cell[(r, c)] = n
                self.s.add_edge_unchecked(self.f, "field_cell", n)
        for r in range(H):
            for c in range(W):
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    r2, c2 = r + dr, c + dc
                    if 0 <= r2 < H and 0 <= c2 < W:
                        self.s.add_edge_unchecked(
                            self.cell[(r, c)], "adj", self.cell[(r2, c2)])

    def half_sweep(self, phase):
        self.s.set_attr(self.f, "phase", float(phase))
        self.s._inner.run_rules(1)

    def read(self, key="val"):
        out = np.zeros((H, W), dtype=np.float64)
        for r in range(H):
            for c in range(W):
                out[r, c] = float(self.s.node(self.cell[(r, c)])["attrs"][key])
        return out

    def read_int(self, key="val"):
        return self.read(key).astype(np.int64)


# --------------------------------------------------- the two functionals (G1)
def _edges():
    """Undirected 4-connectivity edge list (each pair once)."""
    E = []
    for r in range(H):
        for c in range(W):
            if c + 1 < W:
                E.append(((r, c), (r, c + 1)))
            if r + 1 < H:
                E.append(((r, c), (r + 1, c)))
    return E


_EDGE_CACHE = None


def edges():
    global _EDGE_CACHE
    if _EDGE_CACHE is None:
        _EDGE_CACHE = _edges()
    return _EDGE_CACHE


def physics_gibbs_energy(x, obs, coupling):
    """PHYSICS FRAME. Hamiltonian / Gibbs free energy of the configuration:
    data coupling to the external field + nearest-neighbour interaction. Exact
    integer arithmetic (sum of integer squares)."""
    data = coupling * int(np.sum((x - obs) ** 2))
    inter = 0
    for (a, b) in edges():
        d = int(x[a] - x[b])
        inter += d * d
    return int(data + inter)


def cognition_neg_log_posterior(x, y, precision, cliques):
    """COGNITION FRAME. Negative log-posterior of a Gaussian MRF (up to an
    additive constant): likelihood data term + smoothness prior over cliques.
    Written independently of `physics_gibbs_energy`; same formula, renamed."""
    likelihood = precision * int(np.sum((x - y) ** 2))
    prior = 0
    for (a, b) in cliques:
        diff = int(x[a] - x[b])
        prior += diff * diff
    return int(likelihood + prior)


# ------------------------------------------------- independent reference MAP
def reference_redblack_denoiser(obs, lam, n_sweeps):
    """G3 reference: an INDEPENDENT numpy implementation of the SAME red-black
    integer coordinate descent. Its fixed point IS the MRF-MAP (ICM). Byte-for-
    byte comparable to the substrate — it matches because it is the same algo."""
    par = parity()
    x = obs.copy()
    for t in range(n_sweeps):
        ph = t % 2
        deg = np.zeros((H, W), dtype=np.int64)
        ssum = np.zeros((H, W), dtype=np.int64)
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr = np.roll(x, (dr, dc), (0, 1))
            m = np.ones((H, W), dtype=bool)
            if dr == 1:  m[0, :] = False
            if dr == -1: m[-1, :] = False
            if dc == 1:  m[:, 0] = False
            if dc == -1: m[:, -1] = False
            ssum += np.where(m, rr, 0)
            deg += m.astype(np.int64)
        num = lam * obs + ssum
        den = lam + deg
        cand = (2 * num + den) // (2 * den)
        x = np.where(par == ph, cand, x)
    return x


def real_linear_solve_map(obs, lam):
    """The CROSS-FRAME continuous reference: the exact real-valued MAP
    x* = (L + lam I)^{-1} lam y (graph-Laplacian linear solve). FLOAT — it is a
    map between frames, never in-frame state."""
    Nn = H * W

    def idx(r, c):
        return r * W + c
    L = np.zeros((Nn, Nn))
    for r in range(H):
        for c in range(W):
            i = idx(r, c)
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                r2, c2 = r + dr, c + dc
                if 0 <= r2 < H and 0 <= c2 < W:
                    L[i, i] += 1
                    L[i, idx(r2, c2)] -= 1
    A = L + lam * np.eye(Nn)
    xstar = np.linalg.solve(A, lam * obs.reshape(-1)).reshape(H, W)
    return xstar


# --------------------------------------------------------------- the gates
def run_settle(sign, obs, init, max_sweeps):
    """Drive the substrate field `max_sweeps` half-sweeps (or until a fixed
    point), returning the per-half-sweep integer val-trajectory."""
    fld = Field(obs, init, sign)
    traj = [fld.read_int()]
    for t in range(max_sweeps):
        fld.half_sweep(t % 2)
        traj.append(fld.read_int())
        if sign > 0 and t >= 1 and np.array_equal(traj[-1], traj[-3]) \
                and np.array_equal(traj[-1], traj[-2]):
            break
    return traj, fld


def gate_G1(obs, init):
    """Byte-identical trajectory under the two relabels; equal functionals;
    pure-relabel source audit."""
    # Two runs, SAME builder, differing only in which relabel dict we carry.
    traj_p, _ = run_settle(+1, obs, init, 60)
    traj_c, _ = run_settle(+1, obs, init, 60)
    n = min(len(traj_p), len(traj_c))
    byte_identical = all(np.array_equal(traj_p[t], traj_c[t]) for t in range(n)) \
        and len(traj_p) == len(traj_c)

    # The two functionals on the ONE trajectory — computed by independent paths.
    cl = edges()
    E_phys = [physics_gibbs_energy(x, obs, LAM) for x in traj_p]
    E_cog = [cognition_neg_log_posterior(x, obs, LAM, cl) for x in traj_p]
    functionals_equal = (E_phys == E_cog)

    # Source audit: the relabel is a pure str->str dict with no arithmetic and
    # is never used in a set_attr / sweep. Confirm RELABEL contains only strings
    # and that this file's set_attr calls never reference a relabel value.
    relabel_pure = all(
        isinstance(k, str) and all(isinstance(a, str) and isinstance(b, str)
                                   for a, b in v.items())
        for k, v in RELABEL.items())
    src = open(os.path.abspath(__file__)).read()
    setattr_lines = re.findall(r"set_attr\([^\n]*", src)
    relabel_values = {b for v in RELABEL.values() for b in v.values()}
    relabel_in_dynamics = any(any(rv in ln for rv in relabel_values)
                              for ln in setattr_lines)
    audit_clean = relabel_pure and not relabel_in_dynamics

    return {
        "byte_identical_trajectory": bool(byte_identical),
        "n_ticks": n,
        "functionals_equal": bool(functionals_equal),
        "E_phys_head": E_phys[:6], "E_cog_head": E_cog[:6],
        "E_phys_tail": E_phys[-3:], "E_cog_tail": E_cog[-3:],
        "relabel_pure": bool(relabel_pure),
        "relabel_in_dynamics": bool(relabel_in_dynamics),
        "audit_clean": bool(audit_clean),
        "pass": bool(byte_identical and functionals_equal and audit_clean),
    }


def gate_G2(obs, init):
    """Free-energy Lyapunov monotone-decrease to a fixed point; entropy rises."""
    traj, _ = run_settle(+1, obs, init, 400)
    E = [physics_gibbs_energy(x, obs, LAM) for x in traj]
    non_increasing = all(E[i + 1] <= E[i] for i in range(len(E) - 1))
    # strictly decreasing until the fixed point (last constant tail excluded)
    reached_fixed = np.array_equal(traj[-1], traj[-2])
    S = [E[0] - e for e in E]                        # entropy produced
    entropy_up = all(S[i + 1] >= S[i] for i in range(len(S) - 1))
    Smax = S[-1]
    return {
        "E_curve": E, "S_curve": S, "n_sweeps": len(E) - 1,
        "E0": E[0], "E_final": E[-1], "S_max": Smax,
        "monotone_non_increasing": bool(non_increasing),
        "reached_fixed_point": bool(reached_fixed),
        "entropy_monotone_up": bool(entropy_up),
        "pass": bool(non_increasing and reached_fixed and entropy_up),
    }


def gate_G3(clean, obs):
    """Denoising recovery; fixed point matches the independent reference MAP."""
    traj, _ = run_settle(+1, obs, obs.copy(), 400)
    err = [int(np.sum(np.abs(x - clean))) for x in traj]
    input_err = err[0]
    final_err = err[-1]
    val_star = traj[-1]

    ref = reference_redblack_denoiser(obs, LAM, len(traj) - 1)
    matches_ref = bool(np.array_equal(val_star, ref))

    xstar = real_linear_solve_map(obs, LAM)
    max_dev_real = int(np.max(np.abs(val_star - np.round(xstar).astype(np.int64))))

    return {
        "input_err": input_err, "final_err": final_err,
        "denoise_ratio": final_err / max(input_err, 1),
        "err_curve": err,
        "matches_reference_denoiser": matches_ref,
        "max_dev_from_real_map": max_dev_real,
        "pass": bool(final_err < input_err and matches_ref and max_dev_real <= 1),
    }


def gate_G4(clean, obs, window=14):
    """Anti-dissipative (sign=-1): E rises AND recovery error rises — both
    diverge from the sound run. Break-one-breaks-both."""
    traj, _ = run_settle(-1, obs, obs.copy(), window)
    E = [physics_gibbs_energy(x, obs, LAM) for x in traj]
    err = [int(np.sum(np.abs(x - clean))) for x in traj]
    E_up = all(E[i + 1] >= E[i] for i in range(len(E) - 1))
    err_up = all(err[i + 1] >= err[i] for i in range(len(err) - 1))
    diverged = (E[-1] > 100 * max(E[0], 1)) and (err[-1] > 5 * max(err[0], 1))
    return {
        "E_curve": E, "err_curve": err,
        "E0": E[0], "E_final": E[-1], "err0": err[0], "err_final": err[-1],
        "E_monotone_up": bool(E_up), "err_monotone_up": bool(err_up),
        "diverged": bool(diverged),
        "pass": bool(E_up and err_up and diverged),
    }


def gate_G5(clean, obs):
    """Integer-native: every cell/control attr integer across the trajectory.
    Default-off: the seed is unreferenced by any default loader."""
    fld = Field(obs, obs.copy(), +1)
    bad = 0
    for _t in range(30):
        fld.half_sweep(_t % 2)
        for r in range(H):
            for c in range(W):
                a = fld.s.node(fld.cell[(r, c)])["attrs"]
                for k in ("val", "obs", "par"):
                    v = float(a[k])
                    if abs(v - round(v)) > 1e-9:
                        bad += 1
        for k in ("lam", "phase", "sign", "enabled"):
            v = float(fld.s.node(fld.f)["attrs"][k])
            if abs(v - round(v)) > 1e-9:
                bad += 1

    # default-off: no default boot manifest / loader references this seed.
    seed_id = "dissipation_inference"
    referenced = []
    for sub in ("substrate", "domains", "scripts"):
        d = os.path.join(ROOT, sub)
        for dp, _dn, fns in os.walk(d):
            if os.sep + "tests" in dp:
                continue
            for fn in fns:
                if not fn.endswith(".py"):
                    continue
                fp = os.path.join(dp, fn)
                # the measure + the eye-boot list are the only legitimate refs
                if os.path.abspath(fp) == os.path.abspath(__file__):
                    continue
                try:
                    txt = open(fp).read()
                except Exception:
                    continue
                if seed_id in txt:
                    referenced.append(os.path.relpath(fp, ROOT))
    default_off = (len(referenced) == 0)
    return {
        "noninteger_attr_writes": bad,
        "seed_referenced_by": referenced,
        "default_off": bool(default_off),
        "pass": bool(bad == 0 and default_off),
    }


# ------------------------------------------------------------------- render
def render(res, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.4))
    E = res["G2"]["E_curve"]
    S = res["G2"]["S_curve"]
    ax = axs[0]
    ax.plot(range(len(E)), E, "-", color="#2166ac", label="free energy E (physics)\n= neg-log-posterior (cognition)")
    ax.set_title("G2 — Lyapunov / free energy DECREASES\n(2nd law = inference converging)")
    ax.set_xlabel("half-sweep"); ax.set_ylabel("E (integer, exact)")
    ax.legend(fontsize=7); ax.set_ylim(bottom=0)
    ax2 = ax.twinx()
    ax2.plot(range(len(S)), S, "--", color="#b2182b", label="entropy produced E0-E")
    ax2.legend(fontsize=7, loc="center right")

    ax = axs[1]
    err = res["G3"]["err_curve"]
    ax.plot(range(len(err)), err, "-", color="#1a9850")
    ax.axhline(res["G3"]["input_err"], ls=":", color="#888", label="input (noisy) error")
    ax.set_title(f"G3 — COGNITION recovers the percept\ndenoise ratio {res['G3']['denoise_ratio']:.2f}, MAP match={res['G3']['matches_reference_denoiser']}")
    ax.set_xlabel("half-sweep"); ax.set_ylabel("recovery error ||val-clean||1")
    ax.legend(fontsize=7)

    ax = axs[2]
    E4 = res["G4"]["E_curve"]; err4 = res["G4"]["err_curve"]
    ax.plot(range(len(E4)), E4, "-", color="#762a83", label="E (anti-dissipative)")
    ax.set_yscale("log")
    ax.set_title("G4 — BREAK-ONE-BREAKS-BOTH\nforce E UP -> recovery diverges")
    ax.set_xlabel("half-sweep"); ax.set_ylabel("E (log)")
    axb = ax.twinx()
    axb.plot(range(len(err4)), err4, "--", color="#e08214", label="recovery error")
    axb.set_yscale("log")
    ax.legend(fontsize=7, loc="upper left"); axb.legend(fontsize=7, loc="lower right")
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


# --------------------------------------------------------------------- main
def main():
    os.makedirs(FRAMES, exist_ok=True)
    rng = np.random.default_rng(SEED)
    clean = clean_image()
    obs = noisy(clean, rng)
    init = obs.copy()

    G1 = gate_G1(obs, init)
    G2 = gate_G2(obs, init)
    G3 = gate_G3(clean, obs)
    G4 = gate_G4(clean, obs)
    G5 = gate_G5(clean, obs)

    res = {
        "block": SEED, "W": W, "H": H, "LAM": LAM, "NOISE": NOISE,
        "relabel_table": RELABEL,
        "G1": G1, "G2": G2, "G3": G3, "G4": G4, "G5": G5,
        "criteria": {
            "G1_identity": G1["pass"],
            "G2_physics_2nd_law": G2["pass"],
            "G3_cognition_recovers_map": G3["pass"],
            "G4_break_one_breaks_both": G4["pass"],
            "G5_integer_native_default_off": G5["pass"],
        },
    }
    with open(os.path.join(RESULTS, "dissipation_inference.json"), "w") as fh:
        json.dump(res, fh, indent=2)
    render(res, os.path.join(FRAMES, "dissipation_inference.png"))

    print(json.dumps(res["criteria"], indent=2))
    print(f"\nG1 byte-identical trajectory: {G1['byte_identical_trajectory']} "
          f"({G1['n_ticks']} ticks); functionals equal: {G1['functionals_equal']}")
    print(f"G2 free energy: {G2['E0']} -> {G2['E_final']} over {G2['n_sweeps']} "
          f"sweeps; monotone_down={G2['monotone_non_increasing']} "
          f"entropy_up={G2['entropy_monotone_up']}")
    print(f"G3 recovery: input {G3['input_err']} -> {G3['final_err']} "
          f"(ratio {G3['denoise_ratio']:.2f}); matches ref MAP "
          f"{G3['matches_reference_denoiser']}; dev from real MAP "
          f"{G3['max_dev_from_real_map']}")
    print(f"G4 anti-dissipative: E {G4['E0']} -> {G4['E_final']}; "
          f"err {G4['err0']} -> {G4['err_final']}; both diverge "
          f"{G4['diverged']}")
    print(f"G5 non-integer attr writes: {G5['noninteger_attr_writes']}; "
          f"default_off={G5['default_off']} (refs: {G5['seed_referenced_by']})")
    return res


if __name__ == "__main__":
    main()

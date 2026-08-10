"""Seizure dynamics driven by the REAL (G,Gamma) engine settlement loop.

This is the ENGINE version of `scripts/seizure_settlement_model.py` (the reduced
numpy reference). Here NOTHING computes the settlement in Python: a spatial
lattice of real `CognitiveArea` nodes is driven by the engine's `run_rules`
fixpoint (evaluating the `sz_settle_next_residual` DSL rule from the
`seizure_dynamics` seed) + the engine's native `fold_clock_edge` (the
synchronous clock-edge commit of `next_residual -> residual`). One substep =
one (run_rules, fold_clock_edge) pair.

The Python harness is a WORLD ADAPTER only: it (1) sets the focal onset `drive`
and the async per-area `ticking` clock each substep, (2) ticks the engine, and
(3) reads `residual` back out. Every dynamical term -- overload regeneration
(positive feedback, gain `alpha`, DEFAULT 0), the give/shed valve (`give`),
the local dissipation budget, and lateral broadcast/recruitment over
`projects_to` -- lives in the graph rule, evaluated in Rust.

Experimental variables: `give` (the give-dial, primary), `alpha` (the
positive-feedback flag/gain), `D` (onset drive), `theta` (async phase diversity,
secondary). Architecture params are frozen (see ARCH).
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, asdict

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from substrate.world_adapter import WorldAdapter  # noqa: E402

AREA_SEED = os.path.join(ROOT, "seeds", "cognitive_areas.json")
SZ_SEED = os.path.join(ROOT, "seeds", "seizure_dynamics.json")


@dataclass
class Arch:
    N: int = 41                 # lattice N x N areas
    T: int = 8                  # async tick cycle length
    budget: float = 0.8         # per-tick settlement budget (local dissipation sink)
    c_gen: float = 1.8          # overload threshold (regen + shed above this)
    g: float = 0.8              # broadcast fraction of the un-dissipated remainder
    alpha: float = 0.0          # DEFAULT OFF positive-feedback gain (overload regen)
    g_rec: float = 0.0          # V2: excitatory-recruitment gain over `recruits` edges (DEFAULT 0)
    gen_cap: float = 2.5        # per-substep cap on the regeneration source
    give: float = 1.0           # THE GIVE: shed fraction of overload (1=graceful, 0=rigid)
    r_max: float = 60.0         # numeric safety clip (not a mechanism)
    r_focus: float = 3.0        # onset focus radius (areas, Euclidean)
    t_onset: int = 24           # substeps of focal onset drive, then removed
    n_steps: int = 320          # total substeps
    r_active: float = 1.8       # an area is "recruited/active" above this (== c_gen)
    record_every: int = 2
    # physical scale (pinned from two observations; speed is then a prediction)
    dx_mm: float = 0.107        # area spacing (mm)
    dt_ms: float = 12.5         # substep duration (ms)


def _phase_offsets(N, T, theta, rng):
    u = rng.random((N, N))
    return np.floor(u * T * theta).astype(np.int64) % T


class EngineLattice:
    """Builds the CognitiveArea lattice and drives the engine settlement loop."""

    def __init__(self, arch: Arch, give=None, alpha=None, theta=1.0, seed=0,
                 g_rec=None, hubs=None, hub_k=0):
        self.arch = arch
        self.give = arch.give if give is None else give
        self.alpha = arch.alpha if alpha is None else alpha
        self.g_rec = arch.g_rec if g_rec is None else g_rec
        # hubs: list of (r,c) areas given hub_k extra long-range `recruits` edges each
        # (bidirectional), making them high-recruits-degree. None => homogeneous.
        self.hubs = list(hubs) if hubs else []
        self.hub_k = hub_k
        self.theta = theta
        self.rng = np.random.default_rng(seed)
        self.agent = WorldAdapter(seeds=())
        self.agent.inner.load_seed_manifest(json.load(open(AREA_SEED)), self.agent.agent)
        self.agent.inner.load_seed_manifest(json.load(open(SZ_SEED)), self.agent.agent)
        self._build()

    def _build(self):
        a = self.arch
        N = a.N
        self.cfg = self.agent.s.add_node("SeizureConfig", {
            "sz_enabled": 1.0, "give": float(self.give), "alpha": float(self.alpha),
            "g": a.g, "g_rec": float(self.g_rec),
            "budget": a.budget, "c_gen": a.c_gen, "gen_cap": a.gen_cap,
            "r_max": a.r_max,
        })
        self.ids = np.empty((N, N), dtype=object)
        for r in range(N):
            for c in range(N):
                nid = self.agent.s.add_node("CognitiveArea", {
                    "name": f"a_{r}_{c}", "status": "active",
                    "residual": 0.0, "next_residual": 0.0, "drive": 0.0,
                    "ticking": 1.0, "clocked": 1.0,
                })
                self.agent.inner.add_edge_unchecked(nid, "sz_managed_by", self.cfg)
                self.ids[r, c] = nid
        for r in range(N):
            for c in range(N):
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < N and 0 <= nc < N:
                        self.agent.inner.add_edge_unchecked(
                            self.ids[r, c], "projects_to", self.ids[nr, nc])
                        # `recruits` channel: the excitatory-recruitment coupling
                        # (V2). Base grid mirrors projects_to; hubs add long-range
                        # edges below. INERT when g_rec == 0 (default).
                        self.agent.inner.add_edge_unchecked(
                            self.ids[r, c], "recruits", self.ids[nr, nc])
        # heterogeneous hubs: extra long-range bidirectional `recruits` edges,
        # raising hub recruits-degree (diffusive projects_to grid stays homogeneous
        # + conservative, so recruitment is the ONLY channel that sees the hubs).
        self.hub_set = set()
        for (hr, hc) in self.hubs:
            self.hub_set.add((hr, hc))
            targets = 0
            tries = 0
            while targets < self.hub_k and tries < self.hub_k * 20:
                tries += 1
                tr = int(self.rng.integers(0, N))
                tc = int(self.rng.integers(0, N))
                if (tr, tc) == (hr, hc):
                    continue
                if abs(tr - hr) + abs(tc - hc) <= 1:
                    continue  # already a grid neighbour
                self.agent.inner.add_edge_unchecked(
                    self.ids[hr, hc], "recruits", self.ids[tr, tc])
                self.agent.inner.add_edge_unchecked(
                    self.ids[tr, tc], "recruits", self.ids[hr, hc])
                targets += 1
        # geometry
        cy = cx = N // 2
        yy, xx = np.mgrid[0:N, 0:N]
        self.dist = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
        self.focus = self.dist <= a.r_focus
        self.phi0 = _phase_offsets(N, a.T, self.theta, self.rng)

    def _read_residual(self):
        N = self.arch.N
        R = np.zeros((N, N))
        for r in range(N):
            for c in range(N):
                R[r, c] = self.agent.s.node(self.ids[r, c])["attrs"].get("residual", 0.0)
        return R

    def run(self, D, desync_at=None, desync_give=1.0,
            photic=False, photic_period=4, photic_amp=0.0, photic_until=None,
            onset_rc=None, r_onset=None):
        a = self.arch
        N, T = a.N, a.T
        give = self.give
        # onset locus: default = central focus (published). onset_rc=(r,c) places
        # the focal drive disk at an arbitrary area (for the hub onset-locus test).
        if onset_rc is None:
            focus = self.focus
        else:
            rr = a.r_focus if r_onset is None else r_onset
            oy, ox = onset_rc
            yy, xx = np.mgrid[0:N, 0:N]
            focus = np.sqrt((yy - oy) ** 2 + (xx - ox) ** 2) <= rr
        total_R, n_active, front_radius = [], [], []
        settled_hist, shed_hist = [], []
        snaps, snap_t = [], []
        p_until = a.n_steps if photic_until is None else photic_until
        for t in range(a.n_steps):
            if desync_at is not None and t == desync_at:
                give = desync_give
                self.agent.inner.set_attr(self.cfg, "give", float(give))
            ticking = (((t + self.phi0) % T) == 0)
            drive = np.zeros((N, N))
            if t < a.t_onset:
                drive[focus] += D
            if photic and t < p_until and (t % photic_period == 0):
                drive += photic_amp
            # --- adapter I/O: set async clock + focal drive on every area ---
            for r in range(N):
                for c in range(N):
                    nid = self.ids[r, c]
                    self.agent.inner.set_attr(nid, "ticking", 1.0 if ticking[r, c] else 0.0)
                    self.agent.inner.set_attr(nid, "drive", float(drive[r, c]))
            # --- the ENGINE settles: run_rules fixpoint + clock-edge fold ---
            self.agent.inner.run_rules(1000000)
            self.agent.inner.fold_clock_edge()
            # --- read observables ---
            R = self._read_residual()
            active = R > a.r_active
            total_R.append(float(R.sum()))
            n_active.append(int(active.sum()))
            settled_hist.append(0.0)
            shed_hist.append(0.0)
            front_radius.append(float(np.percentile(self.dist[active], 90)) if active.any() else 0.0)
            if t % a.record_every == 0:
                snaps.append(R.copy())
                snap_t.append(t)
        return {
            "give": self.give, "alpha": self.alpha, "g_rec": self.g_rec,
            "theta": self.theta, "D": D,
            "total_R": np.array(total_R), "n_active": np.array(n_active),
            "front_radius": np.array(front_radius),
            "snaps": snaps, "snap_t": snap_t,
            "dist": self.dist, "focus": self.focus,
        }


# ---- metrics (identical logic to the reference model) --------------------
def standing_rank1_fraction(res, arch, window=(0, None)):
    lo = window[0]
    hi = window[1] if window[1] is not None else arch.t_onset
    idx = [k for k, tt in enumerate(res["snap_t"]) if lo <= tt < hi]
    if len(idx) < 3:
        return float("nan")
    M = np.stack([res["snaps"][k].ravel() for k in idx], axis=0)
    M = M - M.mean()
    if not np.any(M):
        return float("nan")
    s = np.linalg.svd(M, compute_uv=False)
    return float(s[0] ** 2 / (s ** 2).sum())


def onset_propagation(res, arch):
    fr = res["front_radius"][:arch.t_onset]
    if len(fr) < 4:
        return float("nan")
    return float(fr.max() - fr[:6].max())


def persists(res, arch, tail=60):
    na = res["n_active"][-tail:]
    return bool(na.mean() > 5.0)


def traveling_speed_mm_s(res, arch):
    fr = res["front_radius"]
    t0 = arch.t_onset
    seg = fr[t0:]
    if len(seg) < 20 or not persists(res, arch):
        return float("nan"), float("nan")
    tgrid = np.arange(len(seg))
    grow_end = int(np.argmax(seg)) + 1
    if grow_end < 10:
        return float("nan"), float("nan")
    x = tgrid[:grow_end].astype(float)
    y = seg[:grow_end]
    A = np.vstack([x, np.ones_like(x)]).T
    coef = np.linalg.lstsq(A, y, rcond=None)[0]
    yhat = A @ coef
    ss_res = ((y - yhat) ** 2).sum()
    ss_tot = ((y - y.mean()) ** 2).sum() + 1e-12
    r2 = 1 - ss_res / ss_tot
    speed = coef[0] * (arch.dx_mm / (arch.dt_ms / 1000.0))
    return float(speed), float(r2)


def classify(res, arch):
    sp, r2 = traveling_speed_mm_s(res, arch)
    return {
        "give": res["give"], "alpha": res["alpha"], "g_rec": res.get("g_rec", 0.0),
        "theta": res["theta"], "D": res["D"],
        "rank1_frac": standing_rank1_fraction(res, arch),
        "onset_prop_areas": onset_propagation(res, arch),
        "persists": persists(res, arch),
        "final_active": float(res["n_active"][-60:].mean()),
        "peak_active": int(res["n_active"].max()),
        "max_front": float(res["front_radius"].max()),
        "speed_mm_s": sp, "speed_r2": r2,
    }


def run_one(arch, D, give=None, alpha=None, theta=1.0, seed=0,
            g_rec=None, hubs=None, hub_k=0, **kw):
    lat = EngineLattice(arch, give=give, alpha=alpha, theta=theta, seed=seed,
                        g_rec=g_rec, hubs=hubs, hub_k=hub_k)
    return lat.run(D, **kw)


if __name__ == "__main__":
    arch = Arch()
    print("ENGINE give sweep (alpha=0.5, D=3, theta=1, seed=0):")
    for gv in (1.0, 0.6, 0.4, 0.3, 0.2, 0.1, 0.0):
        r = run_one(arch, D=3.0, give=gv, alpha=0.5, seed=0)
        print(json.dumps(classify(r, arch)))
    print("good null (alpha=0, give=0, D=3):")
    r = run_one(arch, D=3.0, give=0.0, alpha=0.0, seed=0)
    print(json.dumps(classify(r, arch)))

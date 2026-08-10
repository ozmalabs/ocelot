"""Psychosis as a grounding failure mode, driven by the REAL (G,Gamma) engine.

Glass-box demonstration that the engine's EXISTING grounding/collapse operation,
run in a failure regime, reproduces the two native psychosis forms
(self-grounding delusion; non-optimal-basin misperception) plus the
sycophantic-confirmer amplification and grounding-source correction. NO new Rust.

This is the GROUNDING analogue of `scripts/seizure_engine_lattice.py` (which does
the same for SETTLEMENT). Nothing computes the dynamics in Python: a `Belief`
node is driven by the engine's `run_rules` fixpoint (evaluating the `pg_ground` /
`pg_collapse_*` DSL rules from the `psychosis_grounding` seed) + the engine's
native `fold_clock_edge` (which commits `next_belief -> belief` and
`next_conf -> conf` on the clocked node). One substep = one
(run_rules, fold_clock_edge) pair.

The Python harness is a WORLD ADAPTER only: each substep it sets the two external
grounding channels on the belief node -- (obs, w_ext) = the REALITY /
grounding-source channel, and (obs2, w_conf) = the CONFIRMER channel -- ticks the
engine, and reads (belief, conf, committed_center) back out. Every dynamical term
lives in the graph rule, evaluated in Rust. No agent decision in Python.

Prereg: PSYCHOSIS_DEMO_PREREG.md. Results: PSYCHOSIS_DEMO_RESULTS.md.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, asdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from substrate.world_adapter import WorldAdapter  # noqa: E402

SEED = os.path.join(ROOT, "seeds", "psychosis_grounding.json")
OUTDIR = os.path.join(ROOT, "results", "psychosis_demo")


@dataclass
class Params:
    # grounding / self-grounding gains
    kx: float = 0.5      # external grounding gain (both channels), precision-gated by 1/(1+conf)
    ks: float = 0.18     # self-grounding gain (pull into own committed basin, x conf; ks*cmax=0.9<1 stable)
    # confidence (precision) dynamics
    gc: float = 0.15     # self-confirmation rate (belief sits in its own basin)
    ge: float = 0.9      # external corroboration rate (a source agrees -> false validation)
    dc: float = 0.3      # external disconfirmation rate (a source contradicts -> decay)
    tol: float = 0.7     # basin tolerance (within tol of committed = "confirmed")
    cmax: float = 5.0    # confidence ceiling
    r_clip: float = 8.0  # numeric belief clip (safety, not a mechanism)
    # world geometry
    basin_r: float = 0.0  # RIGHT basin center (= truth T)
    basin_w: float = 4.0  # WRONG basin center (the delusion)
    b0: float = 3.6       # initial belief (inside W's attractor -- poorly grounded)
    conf0: float = 0.3    # initial confidence (modest)
    # schedule defaults
    w_reality_strong: float = 1.0   # strong grounding-source precision
    w_reality_weak: float = 0.4     # weak, always-on reality friction
    w_conf: float = 1.0             # sycophantic-confirmer precision


ARCH = Params()


class Sim:
    """One Belief node driven by the engine grounding rules. Adapter only."""

    def __init__(self, p: Params = ARCH, pg_enabled: float = 1.0):
        self.p = p
        self.agent = WorldAdapter(seeds=())
        self.agent.inner.load_seed_manifest(json.load(open(SEED)), self.agent.agent)
        self.cfg = self.agent.s.add_node("PsyConfig", {
            "pg_enabled": float(pg_enabled),
            "kx": p.kx, "ks": p.ks, "gc": p.gc, "ge": p.ge, "dc": p.dc,
            "tol": p.tol, "cmax": p.cmax, "r_clip": p.r_clip,
            "basin_r": p.basin_r, "basin_w": p.basin_w,
        })

    def belief(self, b0=None, c0=None):
        p = self.p
        b0 = p.b0 if b0 is None else b0
        c0 = p.conf0 if c0 is None else c0
        nid = self.agent.s.add_node("Belief", {
            "belief": float(b0), "conf": float(c0),
            "committed_center": p.basin_w if b0 > (p.basin_r + p.basin_w) / 2 else p.basin_r,
            "obs": 0.0, "w_ext": 0.0, "obs2": 0.0, "w_conf": 0.0,
            "clocked": 1.0, "next_belief": float(b0), "next_conf": float(c0),
        })
        self.agent.inner.add_edge_unchecked(nid, "pg_managed_by", self.cfg)
        return nid

    def read(self, nid):
        x = self.agent.s.node(nid)["attrs"]
        return float(x["belief"]), float(x["conf"]), float(x["committed_center"])

    def set_channels(self, nid, obs=0.0, w_ext=0.0, obs2=0.0, w_conf=0.0):
        self.agent.inner.set_attr(nid, "obs", float(obs))
        self.agent.inner.set_attr(nid, "w_ext", float(w_ext))
        self.agent.inner.set_attr(nid, "obs2", float(obs2))
        self.agent.inner.set_attr(nid, "w_conf", float(w_conf))

    def tick(self):
        self.agent.inner.run_rules(1000000)
        self.agent.inner.fold_clock_edge()


def is_W(center, p=ARCH):
    return abs(center - p.basin_w) < abs(center - p.basin_r)


def run_arm(schedule, n=90, b0=None, c0=None, p: Params = ARCH):
    """schedule(t, belief) -> dict(obs, w_ext, obs2, w_conf). One belief."""
    sim = Sim(p)
    nid = sim.belief(b0, c0)
    traj = []
    for t in range(n):
        bel, _, _ = sim.read(nid)
        ch = schedule(t, bel)
        sim.set_channels(nid, **ch)
        sim.tick()
        traj.append(sim.read(nid))
    return traj


def summarise(traj, p: Params = ARCH, tail=40):
    bf, cf, mf = traj[-1]
    tail_centers = [m for (_, _, m) in traj[-tail:]]
    persistence_W = sum(1 for m in tail_centers if is_W(m, p)) / len(tail_centers)
    return {
        "belief_final": round(bf, 4),
        "conf_final": round(cf, 4),
        "committed_final": "W" if is_W(mf, p) else "R",
        "dist_to_truth": round(abs(bf - p.basin_r), 4),
        "persistence_W": round(persistence_W, 4),
    }


# ---- named schedules (matched control: identical belief init/params; only the
#      (obs, w_ext, obs2, w_conf) schedule differs) ------------------------------
def sched_friction(p=ARCH):            # A: strong reality grounding to truth
    return lambda t, b: {"obs": p.basin_r, "w_ext": p.w_reality_strong}

def sched_no_friction(p=ARCH):         # B: nothing external
    return lambda t, b: {}

def sched_confirmer_only(p=ARCH):      # C: sycophantic confirmer, no reality
    return lambda t, b: {"obs2": b, "w_conf": p.w_conf}

def sched_reality_weak(p=ARCH):        # D-control: weak reality friction alone
    return lambda t, b: {"obs": p.basin_r, "w_ext": p.w_reality_weak}

def sched_reality_weak_plus_confirmer(p=ARCH):  # D: weak reality + confirmer (THE FLIP)
    return lambda t, b: {"obs": p.basin_r, "w_ext": p.w_reality_weak, "obs2": b, "w_conf": p.w_conf}

def sched_recovery(t_switch=20, gs_w=1.5, p=ARCH):  # E: confirmer builds delusion, then grounding source
    def f(t, b):
        if t < t_switch:
            return {"obs2": b, "w_conf": p.w_conf}
        return {"obs": p.basin_r, "w_ext": gs_w}
    return f


def run_folie_a_deux(n_pre=30, n_post=40, gs_w=1.5, p: Params = ARCH):
    """Two beliefs, each the OTHER's confirmer (mutual confirmation, no external
    anchor). Then a grounding source reaches ONE. Uses the SAME rule/seed."""
    sim = Sim(p)
    b1 = sim.belief(b0=3.6)
    b2 = sim.belief(b0=3.7)
    traj = {"b1": [], "b2": []}

    def step(ext1=None):
        v1, _, _ = sim.read(b1)
        v2, _, _ = sim.read(b2)
        # mutual confirmation: each takes the other's belief as its confirmer channel
        sim.set_channels(b1, obs2=v2, w_conf=p.w_conf,
                         **({"obs": ext1[0], "w_ext": ext1[1]} if ext1 else {}))
        sim.set_channels(b2, obs2=v1, w_conf=p.w_conf)
        sim.tick()
        traj["b1"].append(sim.read(b1))
        traj["b2"].append(sim.read(b2))

    for _ in range(n_pre):
        step()
    for _ in range(n_post):
        step(ext1=(p.basin_r, gs_w))  # ground b1 to truth only
    return traj


def byte_identity_check(n=40, p: Params = ARCH):
    """P7: a graph whose Belief is OFF (pg_enabled=0) is node-for-node identical
    to the SAME graph with the seed never loaded, after N ticks. And a
    pg_enabled=1 belief DOES evolve (the capability is genuinely live)."""
    def build(pg_enabled, load_seed):
        a = WorldAdapter(seeds=())
        if load_seed:
            a.inner.load_seed_manifest(json.load(open(SEED)), a.agent)
        cfg = a.s.add_node("PsyConfig", {"pg_enabled": float(pg_enabled),
            "kx": p.kx, "ks": p.ks, "gc": p.gc, "ge": p.ge, "dc": p.dc,
            "tol": p.tol, "cmax": p.cmax, "r_clip": p.r_clip,
            "basin_r": p.basin_r, "basin_w": p.basin_w})
        nid = a.s.add_node("Belief", {"belief": p.b0, "conf": p.conf0,
            "committed_center": p.basin_w, "obs": 0.0, "w_ext": 0.0,
            "obs2": 0.0, "w_conf": 0.0, "clocked": 1.0,
            "next_belief": p.b0, "next_conf": p.conf0})
        a.inner.add_edge_unchecked(nid, "pg_managed_by", cfg)
        return a, nid
    a_off, n_off = build(0.0, True)      # seed loaded, capability OFF
    a_none, n_none = build(0.0, False)   # seed never loaded
    a_on, n_on = build(1.0, True)        # capability ON
    for _ in range(n):
        for a in (a_off, a_none, a_on):
            a.inner.run_rules(1000000)
            a.inner.fold_clock_edge()
    def state(a, nid):
        return {k: v for k, v in a.s.node(nid)["attrs"].items()}
    off = state(a_off, n_off)
    none = state(a_none, n_none)
    on = state(a_on, n_on)
    return {
        "off_equals_none": off == none,
        "on_evolved": abs(on["belief"] - p.b0) > 1e-6 or abs(on["conf"] - p.conf0) > 1e-6,
        "off_belief": round(off["belief"], 6),
        "on_belief": round(on["belief"], 6),
    }


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    p = ARCH
    out = {"params": asdict(p), "arms": {}, "sweeps": {}, "checks": {}}

    # --- named arms (trajectories for the figure) ---
    arms = {
        "A_friction": sched_friction(p),
        "B_no_friction": sched_no_friction(p),
        "C_confirmer_only": sched_confirmer_only(p),
        "D_control_reality_weak": sched_reality_weak(p),
        "D_flip_reality_weak_plus_confirmer": sched_reality_weak_plus_confirmer(p),
        "E_recovery": sched_recovery(t_switch=20, gs_w=1.5, p=p),
    }
    for name, sched in arms.items():
        traj = run_arm(sched, n=90, p=p)
        out["arms"][name] = {
            "traj": [[round(b, 5), round(c, 5), m] for (b, c, m) in traj],
            "summary": summarise(traj, p),
        }

    # --- P5 confirmer amplification: conf(t) B vs C over a fixed window ---
    tb = run_arm(sched_no_friction(p), n=20, p=p)
    tc = run_arm(sched_confirmer_only(p), n=20, p=p)
    out["checks"]["amplification"] = {
        "conf_B_no_friction": [round(c, 4) for (_, c, _) in tb],
        "conf_C_confirmer": [round(c, 4) for (_, c, _) in tc],
        "conf_B_at15": round(tb[14][1], 4),
        "conf_C_at15": round(tc[14][1], 4),
    }

    # --- P4b confirmer-strength fold (THE FLIP): reality weak fixed, vary w_conf ---
    fold = []
    for wc in [0.0, 0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.5]:
        sched = lambda t, b, wc=wc: {"obs": p.basin_r, "w_ext": p.w_reality_weak,
                                     "obs2": b, "w_conf": wc}
        s = summarise(run_arm(sched, n=120, p=p), p)
        fold.append({"w_conf": wc, "committed": s["committed_final"],
                     "belief_final": s["belief_final"], "conf_final": s["conf_final"]})
    out["sweeps"]["confirmer_fold"] = {"w_reality_fixed": p.w_reality_weak, "points": fold}

    # --- P4a reality-friction sweep (reported honestly incl. non-monotonicity) ---
    rf = []
    for w in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.5, 2.0]:
        sched = lambda t, b, w=w: {"obs": p.basin_r, "w_ext": w}
        s = summarise(run_arm(sched, n=120, p=p), p)
        rf.append({"w_ext": w, "committed": s["committed_final"], "belief_final": s["belief_final"]})
    out["sweeps"]["reality_friction"] = {"points": rf}

    # --- P6 recovery: escape tick vs grounding-source strength ---
    rec = []
    for gw in [0.2, 0.3, 0.4, 0.6, 0.8, 1.0, 1.5, 2.0, 3.0]:
        traj = run_arm(sched_recovery(t_switch=20, gs_w=gw, p=p), n=120, p=p)
        esc = next((t - 20 for t in range(20, 120) if not is_W(traj[t][2], p)), None)
        rec.append({"gs_w": gw, "escape_tick": esc, "final": summarise(traj, p)["committed_final"]})
    out["sweeps"]["recovery"] = {"points": rec}

    # --- P8 folie a deux ---
    fad = run_folie_a_deux(n_pre=30, n_post=40, gs_w=1.5, p=p)
    out["arms"]["folie_a_deux"] = {
        "b1": [[round(b, 5), round(c, 5), m] for (b, c, m) in fad["b1"]],
        "b2": [[round(b, 5), round(c, 5), m] for (b, c, m) in fad["b2"]],
        "pre_anchor": {"b1": summarise(fad["b1"][:30], p), "b2": summarise(fad["b2"][:30], p)},
        "post_anchor": {"b1": summarise(fad["b1"], p), "b2": summarise(fad["b2"], p)},
    }

    # --- P7 byte-identity when off ---
    out["checks"]["byte_identity"] = byte_identity_check(n=40, p=p)

    with open(os.path.join(OUTDIR, "results.json"), "w") as f:
        json.dump(out, f, indent=1)

    # console summary
    print("=== PSYCHOSIS GROUNDING DEMO (real engine) ===")
    for name in arms:
        print(f"  {name:38s} {out['arms'][name]['summary']}")
    print(f"  P5 amplification conf@15  B={out['checks']['amplification']['conf_B_at15']}"
          f"  C={out['checks']['amplification']['conf_C_at15']}")
    print("  P4b confirmer fold:", " ".join(f"{d['w_conf']}:{d['committed']}" for d in fold))
    print("  P4a reality fold  :", " ".join(f"{d['w_ext']}:{d['committed']}" for d in rf))
    print("  P6 recovery escape:", " ".join(f"{d['gs_w']}:{d['escape_tick']}" for d in rec))
    print(f"  P8 folie a deux pre-anchor: b1={out['arms']['folie_a_deux']['pre_anchor']['b1']['committed_final']}"
          f" b2={out['arms']['folie_a_deux']['pre_anchor']['b2']['committed_final']}"
          f" | post-anchor(ground b1): b1={out['arms']['folie_a_deux']['post_anchor']['b1']['committed_final']}"
          f" b2={out['arms']['folie_a_deux']['post_anchor']['b2']['committed_final']}")
    print(f"  P7 byte-identity: {out['checks']['byte_identity']}")
    print(f"  -> {os.path.join(OUTDIR, 'results.json')}")


if __name__ == "__main__":
    main()

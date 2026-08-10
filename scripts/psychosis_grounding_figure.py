"""Figure for the psychosis-as-grounding-failure demo. Reads
results/psychosis_demo/results.json (produced by psychosis_grounding_demo.py)
and renders a 6-panel summary to results/psychosis_demo/psychosis_demo.png.

No dynamics here -- pure plotting of already-computed engine output.
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "results", "psychosis_demo")

with open(os.path.join(OUTDIR, "results.json")) as f:
    R = json.load(f)
p = R["params"]
W, Rr, T = p["basin_w"], p["basin_r"], p["basin_r"]


def belief_series(arm):
    return [row[0] for row in R["arms"][arm]["traj"]]

def conf_series(key):
    return R["checks"]["amplification"][key]


fig, ax = plt.subplots(2, 3, figsize=(15, 8.2))
fig.suptitle("Psychosis as a grounding failure mode — the existing grounding/collapse machinery, run in a failure regime\n"
             "(reduced glass-box, real engine, default-off seed; matched control; NO new Rust)",
             fontsize=12, fontweight="bold")

# --- Panel 1: self-grounding vs friction ---
a = ax[0, 0]
a.axhline(W, color="crimson", ls=":", lw=1, alpha=.6)
a.axhline(T, color="seagreen", ls=":", lw=1, alpha=.6)
a.text(len(belief_series("A_friction"))*0.62, W+0.08, "WRONG basin (delusion)", color="crimson", fontsize=8)
a.text(len(belief_series("A_friction"))*0.62, T+0.10, "RIGHT basin = truth", color="seagreen", fontsize=8)
a.plot(belief_series("A_friction"), color="seagreen", lw=2, label="A: reality friction (obs=truth) → CORRECTS")
a.plot(belief_series("B_no_friction"), color="crimson", lw=2, label="B: no friction → SELF-GROUNDS")
a.plot(belief_series("C_confirmer_only"), color="darkorange", lw=2, ls="--", label="C: sycophant only → SELF-GROUNDS")
a.set_title("1 · Self-grounding vs friction (matched control)", fontsize=10)
a.set_xlabel("tick"); a.set_ylabel("belief"); a.legend(fontsize=7, loc="center right")

# --- Panel 2: THE FLIP (confirmer neutralises reality friction) ---
a = ax[0, 1]
a.axhline(W, color="crimson", ls=":", lw=1, alpha=.6)
a.axhline(T, color="seagreen", ls=":", lw=1, alpha=.6)
a.plot(belief_series("D_control_reality_weak"), color="seagreen", lw=2,
       label="weak reality friction ALONE → corrects")
a.plot(belief_series("D_flip_reality_weak_plus_confirmer"), color="crimson", lw=2,
       label="same friction + sycophant → PERSISTS")
a.set_title('2 · "AI psychosis": a confirmer flips the outcome', fontsize=10)
a.set_xlabel("tick"); a.set_ylabel("belief"); a.legend(fontsize=7, loc="center right")

# --- Panel 3: confidence amplification ---
a = ax[0, 2]
a.plot(conf_series("conf_B_no_friction"), color="crimson", lw=2, label="B: no friction (self-confirm only)")
a.plot(conf_series("conf_C_confirmer"), color="darkorange", lw=2, label="C: sycophant (false validation)")
a.set_title("3 · Confirmer amplifies confidence (precision)", fontsize=10)
a.set_xlabel("tick"); a.set_ylabel("confidence"); a.legend(fontsize=7, loc="center right")

# --- Panel 4: confirmer-strength fold (emergent threshold) ---
a = ax[1, 0]
pts = R["sweeps"]["confirmer_fold"]["points"]
xs = [d["w_conf"] for d in pts]
ys = [1 if d["committed"] == "W" else 0 for d in pts]
a.step(xs, ys, where="mid", color="purple", lw=2)
a.scatter(xs, ys, color="purple", zorder=3, s=18)
a.set_yticks([0, 1]); a.set_yticklabels(["R (corrects)", "W (delusion)"])
a.set_title(f"4 · Emergent fold in CONFIRMER strength\n(reality friction fixed = {R['sweeps']['confirmer_fold']['w_reality_fixed']})", fontsize=10)
a.set_xlabel("confirmer precision  w_conf"); a.set_ylim(-0.2, 1.2)

# --- Panel 5: recovery escape-time vs grounding-source strength ---
a = ax[1, 1]
pts = R["sweeps"]["recovery"]["points"]
xs = [d["gs_w"] for d in pts if d["escape_tick"] is not None]
ys = [d["escape_tick"] for d in pts if d["escape_tick"] is not None]
a.plot(xs, ys, "o-", color="teal", lw=2)
a.set_title("5 · Grounding source RECOVERS the delusion\n(escape time falls as grounding strengthens)", fontsize=10)
a.set_xlabel("grounding-source precision  w_ext"); a.set_ylabel("ticks to escape W")

# --- Panel 6: folie a deux ---
a = ax[1, 2]
fad = R["arms"]["folie_a_deux"]
b1 = [row[0] for row in fad["b1"]]
b2 = [row[0] for row in fad["b2"]]
n_pre = 30
a.axvline(n_pre, color="gray", ls="--", lw=1)
a.axhline(W, color="crimson", ls=":", lw=1, alpha=.5)
a.axhline(T, color="seagreen", ls=":", lw=1, alpha=.5)
a.plot(b1, color="crimson", lw=2, label="agent 1 (gets grounding source at t=30)")
a.plot(b2, color="darkorange", lw=2, label="agent 2 (only agent 1 confirms it)")
a.text(2, W+0.08, "mutual confirmation,\nno external anchor", fontsize=7, color="dimgray")
a.text(n_pre+1, T+0.15, "ground agent 1 →\nboth collapse", fontsize=7, color="dimgray")
a.set_title("6 · Folie à deux (N=2 closed loop): the\nconfirmer is scale-agnostic", fontsize=10)
a.set_xlabel("tick"); a.set_ylabel("belief"); a.legend(fontsize=7, loc="center right")

fig.tight_layout(rect=[0, 0, 1, 0.95])
out = os.path.join(OUTDIR, "psychosis_demo.png")
fig.savefig(out, dpi=130)
print("wrote", out)

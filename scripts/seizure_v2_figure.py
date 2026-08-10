"""Figure for SEIZURE MODEL V2 — recruitment (P4) + hubs (P5).

Panel A: give* vs g_rec (recruitment PRO-ICTAL) with the V1 diffusion g-sweep
         (protective) overlaid — the two opposite slopes side by side.
Panel B: final_active vs give, one curve per g_rec (the fold shifting right).
Panel C: paired give*(hub onset) vs give*(nonhub onset) + homogeneous control.
Panel D: final_active vs give, hub-onset vs nonhub-onset (mean over seeds).
Writes results/seizure_v2_figure.png.
"""
import json, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(ROOT, "results", "seizure_v2.json")))
P4, P5 = d["P4"], d["P5"]

# V1 published diffusion g-sweep (SEIZURE_SCIENCE.md P4 table): protective
V1_G = [0.40, 0.60, 0.80, 1.00]
V1_GIVESTAR = [0.65, 0.60, 0.55, 0.50]

fig, ax = plt.subplots(2, 2, figsize=(12, 9))

# ---- Panel A: give* vs g_rec vs V1 g-sweep ----
gA = ax[0, 0]
grecs = [float(k) for k in P4["give_star_by_grec"].keys()]
grecs.sort()
med = [P4["give_star_by_grec"][str(g)]["median"] for g in grecs]
med_plot = [1.0 if (m is not None and m >= 1.0) else m for m in med]
gA.plot(grecs, med_plot, "o-", color="#c0392b", lw=2, label="V2 recruitment g_rec (PRO-ICTAL)")
# per-seed scatter
for g in grecs:
    for s in P4["give_star_by_grec"][str(g)]["give_star_per_seed"]:
        if s is not None:
            gA.plot(g, min(s, 1.0), ".", color="#c0392b", alpha=0.4)
gA2 = gA.twiny()
gA2.plot(V1_G, V1_GIVESTAR, "s--", color="#2980b9", lw=2, label="V1 diffusion g (protective)")
gA2.set_xlabel("V1 diffusive coupling g", color="#2980b9")
gA2.tick_params(axis="x", colors="#2980b9")
gA.set_xlabel("V2 recruitment coupling g_rec", color="#c0392b")
gA.tick_params(axis="x", colors="#c0392b")
gA.set_ylabel("give*  (seizure regime = give < give*)")
gA.axhline(1.0, ls=":", color="gray", lw=1)
gA.text(grecs[-1], 1.005, "give=1.0 (full graceful give)", ha="right", fontsize=8, color="gray")
gA.set_title("A. Recruitment RAISES give* (pro-ictal); diffusion LOWERS it (protective)")
l1, la1 = gA.get_legend_handles_labels()
l2, la2 = gA2.get_legend_handles_labels()
gA.legend(l1 + l2, la1 + la2, loc="center right", fontsize=9)

# ---- Panel B: final_active vs give per g_rec ----
gB = ax[0, 1]
gives = [float(x) for x in P4["grid"]["give"]]
cmap = plt.cm.viridis(np.linspace(0, 0.9, len(grecs)))
for gi, g in enumerate(grecs):
    rows = [r for r in P4["rows"] if r["g_rec"] == g]
    fa = []
    for gv in P4["grid"]["give"]:
        vals = [r["finals"][str(gv)] for r in rows]
        fa.append(np.mean(vals))
    gB.plot(gives, fa, "o-", color=cmap[gi], label=f"g_rec={g}")
gB.set_yscale("symlog")
gB.set_xlabel("give"); gB.set_ylabel("final_active (mean over seeds, symlog)")
gB.axhline(5.0, ls=":", color="gray", lw=1)
gB.invert_xaxis()
gB.set_title("B. The give-fold shifts to HIGHER give as recruitment rises")
gB.legend(fontsize=8, ncol=2)

# ---- Panel C: hub vs nonhub give* ----
gC = ax[1, 0]
agg = P5["agg"]
hub_gs = [r["give_star"] for r in P5["rows"] if r["onset"] == "hub" and r["give_star"] is not None]
non_gs = [r["give_star"] for r in P5["rows"] if r["onset"] == "nonhub" and r["give_star"] is not None]
hom_gs = [r["give_star"] for r in P5["homog"] if r["give_star"] is not None]
positions = [0, 1, 2]
data = [hub_gs, non_gs, hom_gs]
labels = ["HUB onset", "NON-HUB onset", "homogeneous"]
colors = ["#c0392b", "#2980b9", "#7f8c8d"]
for p, dd, cc in zip(positions, data, colors):
    jitter = np.random.default_rng(0).normal(0, 0.05, len(dd))
    gC.plot(np.full(len(dd), p) + jitter, dd, "o", color=cc, alpha=0.6)
    gC.plot([p - 0.2, p + 0.2], [np.median(dd)] * 2, "-", color=cc, lw=3)
gC.set_xticks(positions); gC.set_xticklabels(labels)
gC.set_ylabel("give*")
md = agg["paired_hub_minus_nonhub"]
gC.set_title(f"C. HUB onset seizes at higher give* "
             f"(paired Δ median={md['median']}, {md['n_positive']}/{md['n_total']} positive)")

# ---- Panel D: final_active vs give hub vs nonhub ----
gD = ax[1, 1]
p5gives = [float(x) for x in P5["grid"]["give"]]
for onset, cc in (("hub", "#c0392b"), ("nonhub", "#2980b9")):
    rows = [r for r in P5["rows"] if r["onset"] == onset]
    fa = []
    for gv in P5["grid"]["give"]:
        vals = [r["finals"][str(gv)] for r in rows]
        fa.append(np.mean(vals))
    gD.plot(p5gives, fa, "o-", color=cc, label=f"{onset} onset")
gD.set_yscale("symlog")
gD.set_xlabel("give"); gD.set_ylabel("final_active (mean over seeds, symlog)")
gD.axhline(5.0, ls=":", color="gray", lw=1)
gD.invert_xaxis()
gD.set_title("D. HUB-onset persists where NON-HUB onset dies")
gD.legend(fontsize=9)

fig.suptitle("Seizure model V2: excitatory recruitment (pro-ictal) + hubs (onset locus)",
             fontsize=13, y=0.995)
fig.tight_layout(rect=[0, 0, 1, 0.98])
out = os.path.join(ROOT, "results", "seizure_v2_figure.png")
fig.savefig(out, dpi=130)
print("wrote", out)

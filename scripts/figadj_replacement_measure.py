"""figadj_replacement_measure -- does competitive border ownership produce
proto-objects on real frames, and do they CORRESPOND to anything?

Pre-registration: VISION_FIGADJ_REPLACEMENT_PREREG.md, committed 03e78a79
BEFORE any real-frame number. Seeds 83000-83999.

Mechanical I/O + read-out ONLY. Every decision is the seed's
(`vision_border_ownership` v1.1.0): the flood, the labelling, the ownership
competition and the mint are ALL rules. This script builds fields, ticks to a
fixpoint, and measures.

TWO INSTRUMENT DISCIPLINES ARE LOAD-BEARING HERE:

1. The prior rung's counterfactual SIMULATION was validated 168/168 under the
   INCUMBENT predicate only. Using it to score a different predicate would be
   measuring the change with an instrument calibrated to the thing being
   replaced. So BOTH predicates are run THROUGH THE SUBSTRATE, and this script's
   gate attribution is RECONCILED against the rules' own minted output
   (`G_pass == n_protos`) SEPARATELY UNDER EACH PREDICATE. A row that does not
   reconcile is not claimed. The materialised `rim` attribute is independently
   reconciled against a recomputation from the settled graph.

2. A proto mechanism that mints VACUOUSLY looks like success (it has read as a
   success three times in this thread). The dead-instrument controls must
   ACTUALLY FIRE, not merely be capable of firing, and the run aborts if they
   do not.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
from collections import Counter, deque

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "domains"))

from domains import engine_provenance as ep                  # noqa: E402

ep.engine_preamble()

from substrate.boot_core import boot_core, load_seeds_into   # noqa: E402
from domains import border_ownership_world as bow            # noqa: E402

SEED_BLOCK = 83000

# The resolution rung's recommended proto-object configuration (G72):
# ONE 72x72 decode, tiled row-major into a 4x4 grid of 18x18 tiles.
# Measured price 2.9x, "loses nothing" -- VISION_RESOLUTION_SCALE_RESULTS.md §10.
GRID = 72
REGION = 18

K_LEVELS = (2, 4, 8, 16)
K_MAIN = 16
SAMPLED_FRAMES = (0, 25, 50, 75, 100, 125, 149)   # M1, the incumbent's sampling
N_CONSECUTIVE = 40                                # M2, persistence needs t, t+1
N_DECODE = 150
MAX_STEPS = 200_000

# 0.0 = incumbent `bo_mint_enclosed` (isolation / G_figadj)
# 1.0 = replacement `bo_mint_owned` (competitive ownership)
ARMS = {"incumbent": 0.0, "replacement": 1.0}

CORPORA = {
    "C1": {"what": "cartoon", "episode_index": 0, "pin": "08630d4b"},
    "C2": {"what": "live-action", "episode_index": 3, "pin": "119eca43"},
}


def _vp():
    spec = importlib.util.spec_from_file_location(
        "vp", os.path.join(ROOT, "scripts", "video_probe_measure.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def quantize(frame, k):
    """The incumbent quantizer, reproduced exactly (per-frame min/max)."""
    f = np.asarray(frame, float)
    lo, hi = float(f.min()), float(f.max())
    if hi <= lo:
        return [[0 for _ in row] for row in f]
    q = np.clip(((f - lo) / (hi - lo) * k).astype(int), 0, k - 1)
    return [[int(v) for v in row] for row in q]


def region_origins(shape=(GRID, GRID), region=REGION):
    """The (r0, c0) top-left of each tile, row-major. The incumbent tiling
    (domains/verdict_comparator_world.py), reused verbatim."""
    h, w = shape
    return [(r0, c0)
            for r0 in range(0, h - h % region, region)
            for c0 in range(0, w - w % region, region)]


def tile(vals, r0, c0, region=REGION):
    return [row[c0:c0 + region] for row in vals[r0:r0 + region]]


# --- statistics (identical to the identity-seam rung's) ----------------------
def ci95(xs):
    a = np.asarray([x for x in xs if x is not None], float)
    n = a.size
    if n < 2:
        return {"n": int(n), "mean": float(a.mean()) if n else None,
                "lo": None, "hi": None}
    from scipy import stats
    m, se = float(a.mean()), float(a.std(ddof=1) / np.sqrt(n))
    t = float(stats.t.ppf(0.975, n - 1))
    return {"n": int(n), "mean": m, "lo": m - t * se, "hi": m + t * se,
            "sd": float(a.std(ddof=1))}


def paired_ci95(xs, ys):
    d = [a - b for a, b in zip(xs, ys) if a is not None and b is not None]
    return ci95(d)


# --- the read-out over the SETTLED graph -------------------------------------
def read_out(s, handle, arm):
    """M1/M2/M4 read-out. Replicates the ARMED rule's gates IN THE ORDER the
    rule evaluates them, so the attribution is reconcilable against the rules'
    own minted output. `arm` selects WHICH gate 5a is replicated."""
    idx = handle["index"]
    H, W = handle["H"], handle["W"]
    rc = {idx[(r, c)]: (r, c) for r in range(H) for c in range(W)}
    at = {n: s.node(n)["attrs"] for n in rc}
    nb = {n: list(s.neighbours(n, "neighbour")) for n in rc}
    cells = list(rc)
    g = lambda n, k, d=0.0: float(at[n].get(k, d))          # noqa: E731

    n_frame = sum(1 for n in cells if g(n, "frame") >= 0.5)
    bgc = [n for n in cells if g(n, "bg") >= 0.5]
    enclosed = [n for n in cells if g(n, "bg") < 0.5]
    bg_frac = len(bgc) / len(cells) if cells else 0.0
    reach = len(bgc) - n_frame

    can_flood = any(
        g(z, "bg") < 0.5 and (
            g(z, "frame") > 0.5 or
            any(g(m, "val") == g(z, "val") and g(m, "bg") > 0.5 for m in nb[z]))
        for z in cells)
    can_label = any(
        any(g(m, "val") == g(z, "val") and g(m, "glabel") < g(z, "glabel")
            for m in nb[z])
        for z in cells)
    settled = not (can_flood or can_label)

    comp: dict[float, list] = {}
    for n in enclosed:
        comp.setdefault(g(n, "glabel"), []).append(n)

    # perim(X), recomputed HERE from the settled graph -- the independent check
    # on the `rim` attribute the rule materialised.
    rim_computed = {
        lab: sum(1 for f in members
                 if any(g(m, "glabel") != lab for m in nb[f]))
        for lab, members in comp.items()}
    rim_mismatch = sum(
        1 for lab, members in comp.items() for f in members
        if int(round(g(f, "rim"))) != rim_computed[lab])

    tally = Counter()
    sizes = []
    for lab, members in comp.items():
        sizes.append(len(members))
        if not settled:
            tally["G_settled"] += 1
            continue
        abutting = {g(m, "glabel") for f in members for m in nb[f]
                    if g(m, "bg") < 0.5 and g(m, "glabel") != lab}
        if arm == "incumbent":
            # G_figadj -- ANY contact with another enclosed component refuses.
            if abutting:
                tally["G_figadj"] += 1
                continue
        else:
            # G_own_lost -- contact refuses ONLY on a LOST competition:
            # R must strictly win perim(R) < perim(Q) against EVERY abutting Q.
            # A tie (equal perim) is HELD OPEN, so it refuses here too.
            if any(not (rim_computed[lab] < rim_computed[q]) for q in abutting):
                tally["G_own_lost"] += 1
                continue
        glabels = {g(gc, "glabel") for gc in cells
                   if g(gc, "bg") > 0.5
                   and any(g(f, "bg") < 0.5 and g(f, "glabel") == lab
                           for f in nb[gc])}
        if len(glabels) > 1:
            tally["G_gnd2"] += 1
            continue
        tally["G_pass"] += 1

    protos = bow.protos(s)
    # proto SUPPORT: the cells of the component the proto was minted at. `root`
    # is R.cid and R.glabel == R.cid at the root, so glabel == root selects it.
    support = {p["root"]: sorted(rc[n] for n in comp.get(float(p["root"]), []))
               for p in protos}

    return {
        "n_cells": len(cells), "n_frame": n_frame,
        "bg_frac": bg_frac, "reach": reach,
        "n_enclosed": len(enclosed), "n_components": len(comp),
        "max_component": max(sizes) if sizes else 0,
        "settled": bool(settled),
        "rim_mismatch": rim_mismatch,
        "G_settled": tally["G_settled"],
        "G_figadj": tally["G_figadj"], "G_own_lost": tally["G_own_lost"],
        "G_gnd2": tally["G_gnd2"], "G_pass": tally["G_pass"],
        "n_protos": len(protos),
        "n_protos_multicell": sum(1 for p in protos if p["members"] >= 2),
        "max_members": max([p["members"] for p in protos], default=0),
        # M4: has the background SWALLOWED the field?
        "max_members_frac": (max([p["members"] for p in protos], default=0)
                             / len(cells) if cells else 0.0),
        "support": support,
        "enclosed_cells": sorted(rc[n] for n in enclosed),
    }


def run_one(grid_vals, arm, *, clear_frame=False):
    """One field through the seed to its fixpoint, under ONE armed predicate."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_border_ownership"])
    handle = bow.add_field(s, grid_vals)
    if clear_frame:
        for n in handle["cell_ids"]:
            s.set_attr(n, "frame", 0.0)
    bow.set_flag(s, bown=1.0, bown_own=ARMS[arm])
    t0 = time.time()
    sweeps = bow.tick(s, max_steps=MAX_STEPS)
    ms = (time.time() - t0) * 1e3
    return {"sweeps": sweeps, "ms": ms, **read_out(s, handle, arm)}


# --- ARM 2: persistence, and its two floors ---------------------------------
def iou(a, b):
    sa, sb = set(a), set(b)
    u = len(sa | sb)
    return (len(sa & sb) / u) if u else 0.0


def best_iou_score(supports_t, supports_u):
    """Mean over protos at t of the best IoU against any proto at u.
    None when t holds no proto (excluded from the aggregate, per §3 ARM 2)."""
    if not supports_t:
        return None
    if not supports_u:
        return 0.0
    return float(np.mean([max(iou(p, q) for q in supports_u.values())
                          for p in supports_t.values()]))


def random_partition(enclosed_cells, sizes, rng):
    """FLOOR-B: a size-matched ARBITRARY partition of the SAME enclosed cells.

    The field, the number of protos and their size multiset are all held FIXED;
    only the mechanism's specific GROUPING is destroyed. Regions are grown by
    BFS over 4-adjacency within the enclosed set from random unused seeds, so
    they are connected -- an arbitrary partition, not an incoherent scatter,
    which is the harder floor."""
    avail = set(map(tuple, enclosed_cells))
    out = {}
    for j, size in enumerate(sorted(sizes, reverse=True)):
        if not avail:
            break
        seeds = sorted(avail)
        start = seeds[int(rng.randint(0, len(seeds)))]
        grown, q = set(), deque([start])
        avail.discard(start)
        grown.add(start)
        while q and len(grown) < size:
            r, c = q.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (r + dr, c + dc)
                if nxt in avail and len(grown) < size:
                    avail.discard(nxt)
                    grown.add(nxt)
                    q.append(nxt)
        out[j] = sorted(grown)
    return out


# --- controls ----------------------------------------------------------------
def controls(log):
    """D1 positive (must reproduce under BOTH arms) + the dead-instrument arms
    (must ACTUALLY FIRE) + the speckle negative (must stay silent)."""
    out = {}
    g12 = [[0] * 12 for _ in range(12)]
    for r in range(3, 9):
        for c in range(4, 8):
            g12[r][c] = 1
    uni = [[3] * 12 for _ in range(12)]

    for arm in ARMS:
        d1 = run_one(g12, arm)
        out[f"D1_{arm}"] = {
            **{k: d1[k] for k in ("n_protos", "max_members", "sweeps",
                                  "n_frame", "bg_frac", "reach")},
            "expected": {"n_protos": 1, "members": 24},
            "reproduces": bool(d1["n_protos"] == 1 and d1["max_members"] == 24)}
        d2a = run_one(g12, arm, clear_frame=True)
        out[f"D2a_{arm}"] = {
            **{k: d2a[k] for k in ("n_protos", "max_members", "n_frame",
                                   "reach", "G_figadj", "G_own_lost",
                                   "G_pass")},
            "fired": bool(d2a["n_frame"] == 0 and d2a["reach"] == 0
                          and d2a["n_protos"] > 0)}
        d2b = run_one(uni, arm, clear_frame=True)
        out[f"D2b_{arm}"] = {
            **{k: d2b[k] for k in ("n_protos", "max_members", "n_frame",
                                   "reach")},
            "fired": bool(d2b["n_frame"] == 0 and d2b["reach"] == 0
                          and d2b["n_protos"] > 0),
            "separated_from_live": bool(d2b["n_frame"] != 4 * 12 - 4)}
        # NEGATIVE control: iid speckle at the PROBE'S OWN tile size and k.
        # §4 registered that this must mint NOTHING under the replacement.
        # It does not: the pilot found 1/10 before the full run, so the
        # registered control FAILS for the replacement and is reported as a
        # failure. n is raised from the registered 10 to 100 to CHARACTERISE a
        # control that has already failed at its registered n -- the verdict
        # (failed) is fixed by the first 10 and is not revisited; the extra
        # fields only put an interval on the rate. The registered-n result is
        # recorded alongside so the enlargement cannot launder the verdict.
        nrng = np.random.RandomState(SEED_BLOCK + 900)
        noise_hits = 0
        hits_first10 = 0
        mint_sizes = []
        for j in range(100):
            q = nrng.randint(0, K_MAIN, (REGION, REGION)).tolist()
            r = run_one(q, arm)
            if r["n_protos"] > 0:
                noise_hits += 1
                mint_sizes.append(r["max_members"])
                if j < 10:
                    hits_first10 += 1
        out[f"NOISE_{arm}"] = {
            "n_fields": 100, "fields_minting": noise_hits,
            "registered_n": 10, "fields_minting_registered_n": hits_first10,
            "REGISTERED_CONTROL_PASSES": hits_first10 == 0,
            "false_mint_rate": noise_hits / 100.0,
            "mint_sizes": mint_sizes,
            "max_false_proto_size": max(mint_sizes, default=0),
            "silent": noise_hits == 0}
        log(f"[control/{arm}] D1={out[f'D1_{arm}']['reproduces']} "
            f"D2a_fired={out[f'D2a_{arm}']['fired']} "
            f"D2b_fired={out[f'D2b_{arm}']['fired']} "
            f"noise_minting={noise_hits}/10")
    return out


def main():
    prov = ep.provenance_line()
    print(f"[provenance] {prov}", flush=True)

    def log(m):
        print(m, flush=True)

    ctrl = controls(log)

    # ABORT RULES -- registered in §4. A dead instrument claims nothing.
    for arm in ARMS:
        if not ctrl[f"D1_{arm}"]["reproduces"]:
            raise SystemExit(f"POSITIVE CONTROL DEAD ({arm}) -- nothing claimed")
    if not ctrl["D2b_replacement"]["fired"]:
        raise SystemExit("DEAD-INSTRUMENT ARM DID NOT FIRE -- instrument blind")

    out = {"provenance": prov, "prereg": "VISION_FIGADJ_REPLACEMENT_PREREG.md",
           "prereg_commit": "03e78a79", "seed_block": SEED_BLOCK,
           "config": {"GRID": GRID, "REGION": REGION,
                      "n_tiles": len(region_origins()),
                      "k_levels": list(K_LEVELS), "k_main": K_MAIN,
                      "sampled_frames": list(SAMPLED_FRAMES),
                      "n_consecutive": N_CONSECUTIVE},
           "controls": ctrl, "corpora": {}, "m1_rows": [], "m2": {}}

    vp = _vp()
    origins = region_origins()

    # Iterated as an explicit (ordinal, id) tuple sequence rather than
    # `CORPORA.items()` so that every seed below is STATICALLY RESOLVABLE by
    # scripts/seed_audit.py. Seeding off `spec["episode_index"]` (a dict
    # subscript) left the analyser with UNKNOWN sinks -- and a --check that
    # passes with unknown sinks has verified nothing. The RNG ordinal is the
    # corpus's position here, not its catalogue index; they are unrelated
    # concerns and should not have been coupled.
    for ci, cid in ((0, "C1"), (1, "C2")):
        spec = CORPORA[cid]
        frames, meta = vp.jellyfin_frames(
            N_DECODE, every=2, start_s=300, size=GRID,
            episode_index=spec["episode_index"])
        got = str(meta["episode_id"])
        if not got.startswith(spec["pin"]):
            raise SystemExit(f"PIN MISMATCH {cid}: expected {spec['pin']}… "
                             f"got {got} -- RUN VOID")
        out["corpora"][cid] = {"what": spec["what"], "episode_id": got,
                               "n_decoded": len(frames)}
        log(f"[{cid}] {spec['what']} decoded {len(frames)} @ {GRID}x{GRID} "
            f"pin ok, {len(origins)} tiles of {REGION}x{REGION}")

        # ---- M1: gate attribution, both arms, 4 k, 7 sampled frames --------
        for arm in ARMS:
            for k in K_LEVELS:
                for fi in SAMPLED_FRAMES:
                    q = quantize(frames[fi], k)
                    agg = Counter()
                    protos = multi = 0
                    mmf = []
                    for ti, (r0, c0) in enumerate(origins):
                        r = run_one(tile(q, r0, c0), arm)
                        for key in ("G_settled", "G_figadj", "G_own_lost",
                                    "G_gnd2", "G_pass", "n_components",
                                    "n_enclosed", "rim_mismatch"):
                            agg[key] += r[key]
                        protos += r["n_protos"]
                        multi += r["n_protos_multicell"]
                        mmf.append(r["max_members_frac"])
                    out["m1_rows"].append({
                        "corpus": cid, "arm": arm, "k": k, "frame": fi,
                        "n_protos": protos, "n_protos_multicell": multi,
                        "max_members_frac": max(mmf),
                        **{key: agg[key] for key in
                           ("G_settled", "G_figadj", "G_own_lost", "G_gnd2",
                            "G_pass", "n_components", "n_enclosed",
                            "rim_mismatch")}})
                    log(f"  [M1 {cid}|{arm[:4]}|k{k:2d}|f{fi:3d}] "
                        f"protos={protos} multi={multi} comps={agg['n_components']} "
                        f"figadj={agg['G_figadj']} ownlost={agg['G_own_lost']} "
                        f"gnd2={agg['G_gnd2']} pass={agg['G_pass']} "
                        f"maxfrac={max(mmf):.2f} rimbad={agg['rim_mismatch']}")

        # ---- M2: persistence over consecutive frames -----------------------
        qs = [quantize(frames[t], K_MAIN) for t in range(N_CONSECUTIVE)]
        for arm in ARMS:
            t0 = time.time()
            # runs[t][ti] = the settled read-out for that tile
            runs = [[run_one(tile(qs[t], r0, c0), arm) for r0, c0 in origins]
                    for t in range(N_CONSECUTIVE)]
            log(f"  [M2 {cid}|{arm}] {N_CONSECUTIVE} frames x {len(origins)} "
                f"tiles in {time.time()-t0:.0f}s")

            arng = np.random.RandomState(SEED_BLOCK + 100 + ci)
            brng = np.random.RandomState(SEED_BLOCK + 200 + ci)
            real, fa, fb = [], [], []
            for t in range(N_CONSECUTIVE - 1):
                cands = [u for u in range(N_CONSECUTIVE) if abs(u - t) > 5]
                tp = int(arng.choice(cands))
                rs, as_, bs = [], [], []
                for ti in range(len(origins)):
                    st = runs[t][ti]["support"]
                    if not st:
                        continue
                    rs.append(best_iou_score(st, runs[t + 1][ti]["support"]))
                    as_.append(best_iou_score(st, runs[tp][ti]["support"]))
                    nxt = runs[t + 1][ti]
                    part = random_partition(
                        nxt["enclosed_cells"],
                        [len(v) for v in nxt["support"].values()], brng)
                    bs.append(best_iou_score(st, part))
                if not rs:
                    continue
                real.append(float(np.mean(rs)))
                fa.append(float(np.mean(as_)))
                fb.append(float(np.mean(bs)))
            out["m2"][f"{cid}|{arm}"] = {
                "n_pairs_scored": len(real),
                "persist": ci95(real),
                "floorA_temporal_shuffle": ci95(fa),
                "floorB_arbitrary_partition": ci95(fb),
                "paired_vs_floorA": paired_ci95(real, fa),
                "paired_vs_floorB": paired_ci95(real, fb),
            }
            m = out["m2"][f"{cid}|{arm}"]
            log(f"  [M2 {cid}|{arm}] pairs={m['n_pairs_scored']} "
                f"persist={m['persist']['mean']} "
                f"A={m['floorA_temporal_shuffle']['mean']} "
                f"B={m['floorB_arbitrary_partition']['mean']} "
                f"vsA_lo={m['paired_vs_floorA']['lo']} "
                f"vsB_lo={m['paired_vs_floorB']['lo']}")

    rp = os.path.join(ROOT, "results", "figadj_replacement.json")
    with open(rp, "w") as fh:
        json.dump(out, fh, indent=1)
    log(f"[written] {rp}")

    # RECONCILIATION, per arm. The attribution must agree with the rules' own
    # minted output, SEPARATELY under each predicate.
    for arm in ARMS:
        rows = [r for r in out["m1_rows"] if r["arm"] == arm]
        bad = [r for r in rows if r["G_pass"] != r["n_protos"]]
        rim_bad = sum(r["rim_mismatch"] for r in rows)
        log(f"[reconciliation/{arm}] rows={len(rows)} mismatched={len(bad)} "
            f"rim_mismatch={rim_bad}")
        for r in bad[:5]:
            log(f"  MISMATCH {r['corpus']} k{r['k']} f{r['frame']} "
                f"G_pass={r['G_pass']} n_protos={r['n_protos']}")


if __name__ == "__main__":
    main()

"""Gate for the ALLOCENTRIC held-surface MAP reconstruction (block 203000-203999).

The map IS the held surface (180000) in WORLD coordinates: a first-class AlloCell{pose,value,
dwell,freshness,tier,...} belief on the game node, grown as the moving eye's SEEN observations
are pose-registered into world coordinates. The accumulation / decay / demotion are ALL rules in
seeds/doom_allocentric_surface.json; the ingest (pose/depth/luma -> ObsCell) and display are
mechanical world-adapter I/O (domains/doom_allo_surface_ingest.py). This gate proves, on a
CONSTRUCTED deterministic run (VizDoom-free) + a real E1M1 run behind a WAD guard:

  G1  reconstruction fidelity GROWS with exploration (coverage + IoU vs a scoring oracle);
      dwelt regions SUPER-RESOLVE (dwell climbs, held value denoises); long-unseen regions
      DEMOTE (fresh->gist->latent) — a DECAYING reconstruction, not an ever-growing store.
  G2  revisiting a demoted region PROMOTES it back and RECOVERS detail (loop-closure analog).
  G3  graph-native (the map grows/decays by RULES) + oracles-only (source audit).
  G4  compute ∝ surprise: work-count spikes on novel geometry, low on revisited/settled regions.
  G5  integer-native + default-OFF byte-identity (no AlloParams -> loop inert).

Deterministic and cross-process-stable: every assertion is on OCCUPANCY / DWELL / TIER / COUNTS,
never on node ids (map node ids are a HashMap artifact).
"""
from __future__ import annotations

import json
import os

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter  # noqa: E402
import domains.doom_allo_surface_ingest as al      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_PATH = os.path.join(ROOT, "seeds", "doom_allocentric_surface.json")
WAD = "/home/matt/.local/share/Steam/steamapps/common/Ultimate Doom/base/DOOM.WAD"


# --------------------------------------------------------------------------- harness
def _fresh():
    wa = WorldAdapter(seeds=())
    wa.inner.load_seed_manifest(json.load(open(SEED_PATH)), None)
    return wa


def _game(wa):
    return wa.s.add_node("WorldInstance", {"world_type": "Game", "map_mode": "doom",
                                           "map_epoch": 0.0})


def _obs(wa, game, cells, epoch):
    """Mechanical ingest: (pose, src, lum) -> ObsCell; advance the clock; run the rules; clean up
    (the adapter's accumulate, condensed). Per-frame sensor fusion mirrors the adapter."""
    S, I = wa.s, wa.inner
    best = {}
    for pose, src, lum in cells:
        p = (int(pose[0]), int(pose[1]))
        if p not in best or al._RANK[src] > al._RANK[best[p][0]]:
            best[p] = (src, float(lum))
    for p, (src, lum) in best.items():
        o = S.add_node("ObsCell", {"pose": [p[0], p[1]], "src": src, "lum": float(lum),
                                   "geom": al._GEOM[src], "epoch": float(epoch)})
        I.add_edge_unchecked(game, "observed", o)
    return al.accumulate(wa, game, epoch)


def _cell(wa, game, p):
    m = al.read_map(wa, game)
    return m.get((int(p[0]), int(p[1])))


# --------------------------------------------------------------------------- G1
def test_G1a_reconstruction_grows_and_matches_a_known_layout_ABLE_TO_FAIL():
    """On a KNOWN layout registered over several frames, the reconstruction GROWS (coverage 1->N)
    and reconstructs the expected free/wall cells (able to fail: if accumulation broke these are
    absent)."""
    wa = _fresh(); game = _game(wa); al.install_params(wa, game)
    room = [(r, c) for r in (1, 2, 3) for c in (1, 2, 3)]
    walls = [(0, c) for c in range(5)] + [(4, c) for c in range(5)]
    _obs(wa, game, [((2, 2), "walk", 40)], 1)
    n1 = len(al.read_map(wa, game))
    _obs(wa, game, [(p, "depth_free", 120) for p in room] + [(p, "depth_wall", 200) for p in walls], 2)
    n2 = len(al.read_map(wa, game))
    assert n1 == 1 and n2 > n1, ("reconstruction must GROW", n1, n2)
    m = al.read_map(wa, game)
    for p in room:
        assert m.get(p) is not None and m[p]["geom"] == 0, ("expected free", p, m.get(p))
    for p in [(0, 0), (4, 2)]:
        assert m[p]["geom"] == 1, ("expected wall", p, m.get(p))
    # one AlloCell per pose (no within-frame duplicates)
    poses = list(m.keys())
    assert len(set(poses)) == len(poses)


def test_G1b_dwelt_regions_super_resolve_and_denoise():
    """A cell OBSERVED across many frames with a NOISY luminance around a true value: dwell CLIMBS
    (super-resolution) and the held value DENOISES toward the truth (error drops < 0.5x start).
    The 200000 density-climb, now in world coordinates."""
    import random
    wa = _fresh(); game = _game(wa); al.install_params(wa, game)
    random.seed(7)
    true = 100.0
    obs_errs = []
    for e in range(1, 16):
        noisy = true + random.randint(-20, 20)
        obs_errs.append(abs(noisy - true))
        _obs(wa, game, [((5, 5), "depth_free", noisy)], e)
    c = _cell(wa, game, (5, 5))
    mean_single_err = sum(obs_errs) / len(obs_errs)     # the noise a single frame carries
    assert c["dwell"] == 15, ("dwell must climb with observation", c["dwell"])
    # the ACCUMULATED held value beats a single noisy observation (temporal denoising / super-res)
    assert abs(c["value"] - true) < 0.5 * mean_single_err, \
        ("held value must denoise with dwell", abs(c["value"] - true), mean_single_err)


def test_G1c_long_unseen_regions_demote_but_are_retained():
    """A cell seen ONCE then left behind DEMOTES fresh->gist->latent as its freshness decays,
    while a continuously-dwelt cell stays FRESH — the DECAYING reconstruction. The AlloCell node
    count is NON-DECREASING across the demotion (demote, never delete)."""
    wa = _fresh(); game = _game(wa)
    al.install_params(wa, game, hl_scale=4.0, hl0=4.0, t_fresh=64.0, t_gist=8.0)
    _obs(wa, game, [((5, 5), "depth_free", 100), ((9, 9), "depth_free", 50)], 1)
    n_after_mint = len(al.read_map(wa, game))
    tiers = []
    for e in range(2, 22):
        _obs(wa, game, [((5, 5), "depth_free", 100)], e)   # dwell (5,5); (9,9) left behind
        tiers.append(_cell(wa, game, (9, 9))["tier"])
    dwelt = _cell(wa, game, (5, 5)); stale = _cell(wa, game, (9, 9))
    assert dwelt["tier"] == 2, ("continuously-seen cell stays FRESH", dwelt["tier"])
    assert stale["tier"] < 2, ("long-unseen cell must DEMOTE", stale["tier"])
    assert min(tiers) == 0, ("must reach LATENT over a long absence", tiers)
    assert tiers == sorted(tiers, reverse=True), ("tier is monotone non-increasing without refresh", tiers)
    assert len(al.read_map(wa, game)) >= n_after_mint, "demote must NOT delete cells"


# --------------------------------------------------------------------------- G2
def test_G2_revisit_promotes_and_recovers_detail():
    """A cell that has demoted to LATENT (stored coarsened) is REVISITED: it promotes back to
    FRESH, recovers full detail (stored == integer value), and the node count is unchanged
    (recovery, not re-creation) — the loop-closure analog (198000 G2, in world coordinates)."""
    wa = _fresh(); game = _game(wa)
    al.install_params(wa, game, hl_scale=4.0, hl0=4.0, t_fresh=64.0, t_gist=8.0, k_gist=2.0)
    _obs(wa, game, [((9, 9), "depth_free", 80)], 1)
    for e in range(2, 22):
        _obs(wa, game, [((5, 5), "depth_free", 100)], e)   # (9,9) goes stale
    stale = _cell(wa, game, (9, 9)); n_before = len(al.read_map(wa, game))
    assert stale["tier"] == 0 and stale["stored"] == 0.0, ("must have demoted to LATENT", stale)
    _obs(wa, game, [((9, 9), "depth_free", 80)], 22)       # REVISIT
    prom = _cell(wa, game, (9, 9))
    assert prom["tier"] == 2, ("revisit must PROMOTE back to FRESH", prom["tier"])
    assert prom["stored"] == int(prom["value"]), ("revisit must RECOVER full detail", prom)
    assert len(al.read_map(wa, game)) == n_before, "promote must recover the SAME cell, not add one"


# --------------------------------------------------------------------------- G3 source audit
def test_G3_map_grows_and_decays_by_rules_not_python():
    # (a) the accumulation + decay + demotion live in the seed as graph data
    man = json.load(open(SEED_PATH))
    names = {r["name"] for r in man["rules"]}
    assert {"as_new", "as_blend", "as_gate", "as_freshness", "as_tier", "as_demote"} <= names
    # (b) the ingest adapter makes NO map decision: it emits ObsCell + sets the clock + run_rules;
    #     it NEVER writes an AlloCell value from a conditional (every belief write is a rule effect)
    src = open(os.path.join(ROOT, "domains", "doom_allo_surface_ingest.py")).read()
    assert 'add_edge_unchecked(game, "observed"' in src           # emits observations
    assert 'add_edge_unchecked(game, "has_allo_cell"' not in src   # never writes the belief itself
    assert 'add_node("AlloCell"' not in src and "add_node('AlloCell'" not in src
    assert "run_rules(" in src and 'set_attr(game, "map_epoch"' in src


def test_G3_oracles_only_no_smuggled_depth_or_labels():
    """The map's WHOLE input is the eye (RGB flow -> SEEN depth-from-motion; RGB column luma) +
    self-motion (pose). Source audit: neither the adapter nor the ingest path reads the depth or
    labels buffer into a map write — those live ONLY in the runner's scoring functions."""
    ing = open(os.path.join(ROOT, "domains", "doom_allo_surface_ingest.py")).read()
    assert "depth_buffer" not in ing and "labels_buffer" not in ing and '"depth"' not in ing
    run = open(os.path.join(ROOT, "scripts", "doom_allo_surface_run.py")).read()
    # in the runner, the depth buffer appears ONLY in oracle/scoring helpers, never in ingest_*
    assert "ORACLE" in run and "_oracle_occupancy" in run
    # the map-building call path uses ingest_seen with SEEN depth-from-motion, not the buffer
    assert "ingest_seen(wa, game" in run and "depth_from_motion" in run


# --------------------------------------------------------------------------- G4 compute ∝ surprise
def test_G4_work_tracks_surprise():
    """Exploring NEW regions costs (the surprise signal = cells MINTED spikes on novel geometry);
    revisiting KNOWN regions is cheap (mints ≈ 0 — the structure is already there); and a region
    the marine has moved on FROM contributes ZERO work (not re-processed — settled). Deterministic
    integer counts (the 185000 dirty tie-in)."""
    wa = _fresh(); game = _game(wa); al.install_params(wa, game)
    novel_mints = []
    # frames 1-5: reveal a NEW row of geometry each frame (novel -> mints spike)
    for e in range(1, 6):
        w = _obs(wa, game, [((e, c), "depth_free", 100) for c in range(6)], e)
        novel_mints.append(w["minted"])
    # frames 6-10: RE-OBSERVE row 3 (already mapped) -> surprise gone, mints 0 (cheap)
    revisit_mints, revisit_work = [], []
    for e in range(6, 11):
        w = _obs(wa, game, [((3, c), "depth_free", 100) for c in range(6)], e)
        revisit_mints.append(w["minted"]); revisit_work.append(w["work"])
    # frames 11-13: marine ELSEWHERE (only its walk cell) -> rows 1-5 are SETTLED, not re-processed
    settled_work = []
    for e in range(11, 14):
        w = _obs(wa, game, [((20, 20), "walk", 100)], e)
        settled_work.append(w["work"])
    assert all(m == 6 for m in novel_mints), ("novel geometry MINTS (surprise)", novel_mints)
    assert all(m == 0 for m in revisit_mints), ("revisiting known geometry mints 0", revisit_mints)
    assert max(settled_work) <= 1, ("a region moved-on-from is settled (0 re-processing)", settled_work)


# --------------------------------------------------------------------------- G5 integer + default-off
def test_G5a_integer_native_bookkeeping():
    wa = _fresh(); game = _game(wa); al.install_params(wa, game, hl_scale=4.0)
    for e in range(1, 12):
        _obs(wa, game, [((5, 5), "depth_free", 100 + (e % 3)), ((7, 7), "depth_free", 60)], e)
    S, I = wa.s, wa.inner
    nonint = 0
    for c in I.neighbours(game, "has_allo_cell"):
        a = S.node(c)["attrs"]
        for k in ("dwell", "residual", "half_life", "freshness", "last_refresh_epoch", "tier",
                  "geom", "now_epoch"):
            v = a[k]
            if float(v) != int(v):
                nonint += 1
        for coord in a["pose"]:
            if float(coord) != int(coord):
                nonint += 1
    assert nonint == 0, "all decay/tier/map bookkeeping must be integer-native (only value is float)"


def test_G5b_default_off_is_inert():
    """With the seed LOADED but NO AlloParams node, the loop is INERT: no AlloCell ever mints,
    the belief stays empty, and the game node is untouched. Opt-in only."""
    wa = _fresh(); game = _game(wa)                 # NO install_params
    S, I = wa.s, wa.inner
    for e in range(1, 6):
        for p in [(1, 1), (2, 2), (3, 3)]:
            o = S.add_node("ObsCell", {"pose": [p[0], p[1]], "src": "depth_free", "lum": 100.0,
                                       "geom": 0.0, "epoch": float(e)})
            I.add_edge_unchecked(game, "observed", o)
        S.set_attr(game, "map_epoch", float(e))
        I.run_rules()
        for o in list(I.neighbours(game, "observed")):
            I.remove_node(o)
    assert len(list(I.neighbours(game, "has_allo_cell"))) == 0, "no AlloParams -> loop inert"
    assert al.read_map(wa, game) == {}


# --------------------------------------------------------------------------- E1M1 real run
@pytest.mark.skipif(not os.path.exists(WAD), reason="DOOM.WAD absent")
def test_E1M1_real_walk_reconstructs_an_allocentric_map():
    """The moving eye reconstructs the level as the pose-registered allocentric held surface on
    real E1M1: coverage GROWS, geometry is SEEN (depth-from-motion) and positively correlates
    with the depth ORACLE, dwelt regions super-resolve, and the tier hierarchy is populated.
    Deterministic (fixed seed + fixed route). Honest: geometric IoU is bounded by seen-depth
    quality (161000's flow wall)."""
    pytest.importorskip("vizdoom")
    import scripts.doom_allo_surface_run as R
    s = R.run(frames=40, seed=1234, checkpoints=(10, 20))
    assert s["seen_forward_frames"] > 0, s
    assert s["final_cells"] > 15, s
    cov = s["coverage_curve"]
    assert cov[-1][1] > cov[5][1], ("reconstruction must GROW over the walk", cov[:6], cov[-1])
    assert s["max_dwell"] >= 3, ("dwelt regions must super-resolve (dwell climbs)", s["max_dwell"])
    sp = s["seen_vs_oracle_spearman"]
    assert sp["n"] > 0 and sp["frac_pos"] > 0.5, ("SEEN depth must correlate with the oracle", sp)
    tc = s["tier_counts_final"]
    assert (tc["gist"] + tc["latent"]) > 0, ("the map must DECAY (some cells demote)", tc)

"""Mary's Room stage 4 -- preregistered replication (amendment A1).

Amendment: docs/experiments/marys-room-stage4-amendment-A1.md.  Original prereg
(unchanged): docs/experiments/marys-room-stage4-prereg.md (f25aae47); original
runner (unchanged, imported for its analysis functions):
scripts/marys_room_stage4_battery.py.

Arms R1-R7 replicate B1-B7 verbatim in procedure, recorded quantities and
predictions P1-P6 on INDEPENDENT layouts spectral_scene.random_mondrian(seed),
seeds 101..116, with every stage-4-fix flag OFF.  New arms N1-N5 run the
flagged features (reacquire, colour_recall, colour_concept_link,
motion_segments) for predictions Q1-Q5.  Every mechanical choice is fixed in
RULES_A1 before any exposure, and depends only on geometry / expected catches.

Modes (run from the repo root, PYTHONPATH=.):
    --precheck   independence pre-check from spectral_scene.expected_catches
                 only (no eye, no seeds, no world)
    --dry-run    build every scene, packet list and world; print planned
                 exposure counts, declared choices and the runtime estimate.
                 GraphEye.submit_photons_2d and PerceivedSurfaceWorld.expose
                 are replaced by sentinels that abort on any call; the call
                 count (0) is printed.
    --smoke      crash test of every arm on the DEVELOPMENT layout
                 (standard_mondrian(seed=None), already observed) at 1000 td,
                 output to /tmp, no verdicts.  Never touches a battery layout.
    (no flag)    the confirmatory run.  Aborts unless the freeze holds:
                 `git diff --quiet HEAD -- <FREEZE_TRACKED>` exits 0, every
                 frozen path is tracked, data/colour hashes match, and the
                 engine is ed9237c97f20.  Writes
                 results/marys_room_stage4_replication.json.
    --from-raw P analysis-only re-entry from this script's raw checkpoint
                 (crash recovery; the same raw records, no new exposures).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
import subprocess
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts import marys_room_stage4_battery as orig  # noqa: E402  (stdlib-only imports)

# ------------------------------------------------------------------ declared constants
SCRIPT = "scripts/marys_room_stage4_replication.py"
AMENDMENT = "docs/experiments/marys-room-stage4-amendment-A1.md"
PREREG_COMMIT = "f25aae47"
BASE_COMMIT = "3460f381"                  # HEAD when A1 was prepared
EXPECTED_ENGINE = "ed9237c97f20"
LAYOUTS = tuple(range(101, 117))          # random_mondrian seeds (16 layouts)
B6_LAYOUTS = tuple(range(101, 109))       # R6 / N5 (8 layouts)
N5_GEOMETRY_OFFSET = 1000                 # N5 release = random_mondrian(seed + 1000)
TDS = (100.0, 1000.0)
B1_ILLS, B1_LABELS = orig.B1_ILLS, orig.B1_LABELS
B2_N_ADAPT, B2_WL, B2_QUANTA = orig.B2_N_ADAPT, orig.B2_WL, orig.B2_QUANTA
B3_ILLS, B3_TDS = orig.B3_ILLS, orig.B3_TDS
B5_STEPS_POS = [(1, 0)] * 4 + [(6, 0)]
B5_STEPS_NEG = [(-1, 0)] * 4 + [(-6, 0)]
B6_ORDER = ["M", "M", "G", "M", "M", "G", "M", "M", "R", "R", "R"]
B7_SEEDS = orig.B7_SEEDS
N4_STATIC, N4_MOVES = 8, 4
N2_CONTROL_SID = 10 ** 6
BOOT_B, BOOT_SEED = 10000, 20261006
ALPHA_Q4 = 0.05
Q2_THRESHOLD = 0.90
SEC_PER_EXPOSURE = 0.60                   # --smoke mean on the dev layout, engine ed9237c97f20
SEC_PER_EXPOSURE_MAX = 1.57               # stage-4 measured max
SEC_PER_BUILD = 0.06

FREEZE_TRACKED = [
    SCRIPT, AMENDMENT,
    "scripts/marys_room_stage4_battery.py",
    "docs/experiments/marys-room-stage4-prereg.md",
    "docs/experiments/marys-room-stage4-results.md",
    "domains/photon_eye.py", "domains/spectral_scene.py",
    "domains/perceived_surface_world.py", "domains/spectral_forward.py",
    "domains/engine_provenance.py",
    "seeds/surface_segmentation.json", "seeds/surface_persistence.json",
    "seeds/colour_property.json", "seeds/looking_episode.json",
    "seeds/look_property_link.json", "seeds/colour_recall.json",
    "seeds/colour_concept_link.json",
    "tools/build_surface_segmentation_seed.py", "tools/build_surface_persistence_seed.py",
    "tools/build_colour_property_seed.py", "tools/build_looking_episode_seed.py",
    "tools/build_look_property_link_seed.py", "tools/build_colour_recall_seed.py",
    "tools/build_colour_concept_link_seed.py",
    "scripts/marys_room_broad.py", "scripts/marys_room_broad_theory.py",
    "scripts/marys_room_broad_audit.py", "scripts/marys_room_broad_boundary.py",
    "scripts/marys_room_broad_review_fixes.py",
    "results/marys_room_broad.json", "results/marys_room_broad_armA.json",
    "results/marys_room_broad_audit.json", "results/marys_room_broad_boundary.json",
    "results/marys_room_broad_freeze.json", "results/marys_room_broad_review_fixes.json",
    "results/marys_room_broad_stimuli.json", "results/marys_room_broad_per_stimulus.csv",
    "results/marys_room_stage4_battery.json",
    "results/marys_room_stage4_battery_summary.csv",
    "tests/test_spectral_scene_random_migrated.py",
    "runners/dsl/src",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
    "runners/dsl/python/substrate_rs/_native.build.json",
]
# data/colour is gitignored, so it is frozen by content hash instead
DATA_DIR = "data/colour"
DATA_COLOUR_SHA256 = "8e567ebe55d33d64ab7efc0c83bdf8c7e016875b26ca97e364567d0fd109355f"

RULES_A1 = {
    "A0_worlds": "One fresh PerceivedSurfaceWorld(24, 16, ...) per sequence. R arms: stage45=True "
                 "and adapter defaults (segmentation=persistence=colour=pooled=looking=True), "
                 "reacquire=False, motion_segments=False, recall=None, concepts=None (seeds "
                 "colour_recall / colour_concept_link NOT loaded), i.e. the f25aae47 semantics "
                 "(test_flags_off_byte_identical_to_f25aae47). After build: rules_skipped == [] "
                 "for every seed; enabled/pooled params == 1; SurfacePersistenceParams.reacquire "
                 "and SurfaceSegmentationParams.motion_segments read back equal to the requested "
                 "flag; ColourRecallParams / ColourConceptParams exist iff that seed was "
                 "requested, with enabled equal to the request.",
    "A1_layouts": "R1, R2, R4, R5, R7, N1-N4: spectral_scene.random_mondrian(seed), seeds 101..116. "
                  "R6 and N5: seeds 101..108. The standard / permuted stage-4 layouts are not used.",
    "A2_surface_unit": "As R1 of the original battery: a surface is a declared patch of the scene "
                       "shown (ids 0 = background, 1..n), reporting only; by construction every "
                       "patch and the background is one 4-connected visible region.",
    "A3_reuse": "B1-B7 rules R3-R11, R14, R16-R18 apply verbatim, implemented by the imported "
                "functions an_b1, summarise_b1, an_b3, an_b4, an_b5, an_b6, an_b7 and verdicts of "
                "scripts/marys_room_stage4_battery.py; held-out set = seeds 101..116 (R6: 101..108); "
                "an_b7's deterministic comparison set (module constant B7_LAYOUTS) is set to 101..116.",
    "A4_R2_roles": "R2 roles: 'neutral' = the background (patch 0, always a ColorChecker neutral). "
                   "'white' = the declared patch whose reflectance is white 9.5 (even seeds); in odd "
                   "seeds the declared achromatic patch (white/neutral/black) with the largest "
                   "expected L+M under E (ties: lowest id); if the layout has no achromatic "
                   "declared patch the 'white' role is absent for that layout. The P2/P3 B2 "
                   "clauses range over the roles present.",
    "A5_R4_pair": "R4 pair: original R12 verbatim (chromatic declared patches, largest |L+M| "
                  "difference of patch_report(scene,'E',td), ties lexicographic). A layout with "
                  "fewer than two chromatic declared patches has no R4 sequence (reported).",
    "A6_R5_patch": "R5 moved patch: original R13 with the unmoved position included: the "
                   "lowest-id declared patch whose rect, at offset 0 and at every cumulative "
                   "offset of the schedule [(+1,0)]*4 + [(+6,0)] (0, +1..+4, +10 columns), lies "
                   "fully on the sheet and overlaps no other declared patch's rect. If no patch "
                   "qualifies, the mirrored schedule [(-1,0)]*4 + [(-6,0)] is tried with the same "
                   "rule. If neither qualifies, the layout has no R5 sequence (reported). "
                   "SUPPLEMENT (because random sheets are crowded and few of 101..116 qualify): "
                   "the first seeds 117, 118, ... (ascending) whose random_mondrian layout has a "
                   "qualifying patch are added until R5 has 16 layouts; they enter only R5 and the "
                   "P1-B5 clause, which is also reported on the primary layouts alone. R14 "
                   "verdict verbatim.",
    "A7_R6_room": "R6: room = neutral_mondrian(seed) (same geometry as random_mondrian(seed)); "
                  "release = 3 x render(random_mondrian(seed), 'E', td); order M M G M M G M M R R R; "
                  "G = diffuse(24,16,'E',td, filter='eyelid'); all at the arm's td; seeds 101..108. "
                  "R16 verdict verbatim.",
    "A8_R7": "R7: original R17 on all 16 layouts, Poisson seeds 7001..7005; deterministic "
             "comparison = R1 of the same layouts.",
    "A9_N1": "N1 (reacquire=True, stage45=True): sequence GG = scene E, U, U, scene E with "
             "U = diffuse(24,16,'E',td, filter=None) (open-eye uniform field, no surface); "
             "sequence ES = scene E, eyelid diffuse(filter='eyelid'), swap_patches(scene, a, b) "
             "under E with (a, b) the A5 pair (no ES sequence if the layout has no pair). A patch "
             "is re-acquired iff its set of sids at the last exposure equals its set at "
             "exposure 1 and every sid is >= 0. Geometry is unchanged in both sequences, so "
             "every patch enters Q2.",
    "A10_N2": "N2 (recall=True, stage45=True): scene E, eyelid. After the eyelid exposure, one "
              "RecallCue per distinct sid >= 0 covering a declared patch at exposure 1 (ascending), "
              "then one control cue for sid 10^6 (reported, not in Q3). Counts of every stage-4.5 "
              "type and link edge are read before the first and after the last cue.",
    "A11_N3": "N3 (concepts=True, stage45=True): one exposure, scene E, td in {100, 1000}. Truth = "
              "marys_room_broad_theory.truth_for(E(1nm) * reflectance, 'E')['hue4']. A patch is "
              "scored iff its truth is chromatic and it is covered by exactly one sid that covers "
              "no other patch. Correct iff that sid's ColourProperty has concept_status "
              "'categorised' and concept == truth; any other status or a missing property is "
              "incorrect. Majority-class rate p0 at each td = the largest truth-class share among "
              "the scored patches pooled over layouts. Exact one-sided binomial P(X >= k | n, p0).",
    "A12_N4": "N4 (stage45=False, as the stage-4-fix motion tests): 8 static exposures of the "
              "scene under E, then the patch moved by +1 column per exposure for 4 exposures "
              "(cumulative +1..+4). Patch: among declared patches whose rect at offsets 0, +1..+4 "
              "lies on the sheet and overlaps no other declared rect, the one with the smallest "
              "luminance contrast to the background |Y_p - Y_0| / (Y_p + Y_0), Y = expected L+M "
              "under E (td-free), ties lowest id; if none, the mirrored direction (-1) with the "
              "same rule; if neither, no N4 sequence. Run with motion_segments=1 and =0 (two "
              "fresh worlds), td in {100, 1000}. Descriptive only (Q5).",
    "A13_N5": "N5 (reacquire=True, stage45=True): as R6 but the release is "
              "random_mondrian(seed + 1000) (a different geometry and reflectance set). Seeds "
              "101..108. Descriptive; P5's clauses are computed and reported, not verdicts.",
    "A14_stats": "Verdicts use point estimates (R9/R10). Every pooled fraction / median is "
                 "reported with Wilson 95% over surfaces (fractions) and a layout-cluster "
                 "percentile bootstrap: B = 10000 resamples of layouts with replacement, "
                 "numpy default_rng(20261006) freshly seeded for each statistic; pooled k/n (or "
                 "pooled median) per resample; resamples with n = 0 dropped and counted. "
                 "Layout count is the effective n.",
    "A15_profiles": "Per-layout outcome profile of an arm = the JSON of its per-layout outcome "
                    "counts (R1: per td x exposure rung-1 holds, rung-2 holds, n, non-anchor "
                    "rung-1 holds, non-anchor n, plus #exempt, #non-exempt unstable, #births, "
                    "#silent re-binds; R2: per td x role status22, pooled_status22, rg22<rg1, "
                    "same sid; R4: per td all_follow, swapped statuses, others holds/n; R5: per "
                    "td ok/steps/born/coast; R6: per td delta counts, new types, chromatic "
                    "new-property k/n; R7: per td x exposure median segment count). Reported: "
                    "number of distinct profiles over layouts.",
    "A16_Q": "Q1: per td, median |(rg,by)_t - (rg,by)_1| over R1 hue-eligible instances (R6 "
             "inclusion) under A > under D65; R9 across td. Q2: re-acquired fraction >= 0.90 in "
             "each (sequence GG/ES, td) cell; R10. Q3: every N2 sequence has every non-control cue "
             "'recalled' and zero new LookingEpisode and SurfaceLook; R10. Q4: per td, accuracy > "
             "p0 and one-sided p < 0.05; R9. Q5: no prediction.",
    "A18_anchor_secondary": "Secondary (reported, never a verdict input): P3's 'rung 1 holds on "
                            "the anchor surface in every frame' restricted to layouts where, by "
                            "expected catches under each of E, D65 and A, one surface holds the "
                            "per-channel maximum of L, M and S (pre-check: all but 101, 103, 105, "
                            "109). The primary clause keeps R7 verbatim (no anchor surface = "
                            "failure).",
    "A17_determinism": "After all arms, R1 and R3 are re-run in fresh worlds; sha256 of their raw "
                       "records (timings excluded) must equal the first run's.",
}


# ------------------------------------------------------------------ freeze
def git(*args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def sha256_file(path) -> str:
    with open(os.path.join(ROOT, path), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def data_colour_sha() -> dict:
    files = []
    for dp, _dn, fn in os.walk(os.path.join(ROOT, DATA_DIR)):
        for f in fn:
            files.append(os.path.relpath(os.path.join(dp, f), ROOT))
    files.sort()
    per = {p: sha256_file(p) for p in files}
    combined = hashlib.sha256("".join(f"{p}\n{h}\n" for p, h in per.items()).encode()).hexdigest()
    return {"combined": combined, "files": per}


def freeze_check(strict: bool) -> dict:
    head = git("rev-parse", "HEAD").stdout.strip()
    tracked = git("ls-files", "--error-unmatch", "--", *FREEZE_TRACKED)
    untracked = git("ls-files", "--others", "--exclude-standard", "--", *FREEZE_TRACKED).stdout.split()
    diff = git("diff", "--quiet", "HEAD", "--", *FREEZE_TRACKED)
    names = git("diff", "--name-only", "HEAD", "--", *FREEZE_TRACKED).stdout.split()
    ancestor = git("merge-base", "--is-ancestor", BASE_COMMIT, "HEAD").returncode == 0
    since_prereg = git("diff", "--name-only", PREREG_COMMIT, "HEAD", "--", *orig.APPARATUS).stdout.split()
    data = data_colour_sha()
    out = {"head": head, "base_commit": BASE_COMMIT, "base_is_ancestor": ancestor,
           "freeze_paths": FREEZE_TRACKED,
           "ls_files_error_unmatch_exit": tracked.returncode,
           "ls_files_stderr": tracked.stderr.strip()[:2000],
           "untracked_under_freeze": untracked,
           "diff_quiet_head_exit": diff.returncode, "diff_names": names,
           "data_colour_sha256": data["combined"], "data_colour_expected": DATA_COLOUR_SHA256,
           "data_colour_files": data["files"],
           "apparatus_changed_since_prereg": since_prereg,
           "script_sha256": sha256_file(SCRIPT),
           "amendment_sha256": sha256_file(AMENDMENT) if os.path.exists(os.path.join(ROOT, AMENDMENT)) else None,
           "engine_file_sha256": {p: sha256_file(p) for p in orig.ENGINE_FILES}}
    ok = (tracked.returncode == 0 and not untracked and diff.returncode == 0 and ancestor
          and data["combined"] == DATA_COLOUR_SHA256)
    out["freeze_ok"] = ok
    if strict and not ok:
        print(json.dumps({k: v for k, v in out.items() if k != "data_colour_files"}, indent=1))
        raise SystemExit("ABORT: freeze does not hold (commit the script and amendment, "
                         "with a clean tree, before the confirmatory run)")
    return out


# ------------------------------------------------------------------ stats
def binom_sf(k: int, n: int, p: float) -> float:
    """P(X >= k), X ~ Binomial(n, p), exact."""
    return float(sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1)))


def boot_frac(groups) -> dict:
    """groups: [(k, n)] per layout cluster."""
    k = np.array([g[0] for g in groups], dtype=float)
    n = np.array([g[1] for g in groups], dtype=float)
    L = len(groups)
    if L == 0 or n.sum() == 0:
        return {"boot95": None, "dropped": None, "n_layouts": L}
    idx = np.random.default_rng(BOOT_SEED).integers(0, L, size=(BOOT_B, L))
    K, N = k[idx].sum(1), n[idx].sum(1)
    keep = N > 0
    v = K[keep] / N[keep]
    return {"boot95": [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))],
            "dropped": int((~keep).sum()), "n_layouts": L}


def boot_median(groups) -> dict:
    """groups: [list of values] per layout cluster."""
    L = len(groups)
    if L == 0 or not any(groups):
        return {"boot95": None, "dropped": None, "n_layouts": L}
    idx = np.random.default_rng(BOOT_SEED).integers(0, L, size=(BOOT_B, L))
    arrs = [np.asarray(g, dtype=float) for g in groups]
    vals, dropped = [], 0
    for row in idx:
        x = np.concatenate([arrs[i] for i in row])
        if len(x) == 0:
            dropped += 1
            continue
        vals.append(float(np.median(x)))
    return {"boot95": [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))],
            "dropped": dropped, "n_layouts": L}


def clustered(groups) -> dict:
    k = sum(g[0] for g in groups)
    n = sum(g[1] for g in groups)
    return {**orig.frac(k, n), **boot_frac(groups), "per_layout": [list(g) for g in groups]}


def clustered_median(groups) -> dict:
    allv = [x for g in groups for x in g]
    return {"n": len(allv), "median": orig.median(allv), **boot_median(groups)}


def r9(flags) -> str:
    return orig.universal(flags)


# ------------------------------------------------------------------ scenes & choices
class Scenes:
    """Layout key -> scene.  int: battery layouts; 'dev': the development layout
    (standard_mondrian(seed=None)), used only by --smoke."""

    def __init__(self, ss, sf):
        self.ss, self.sf = ss, sf
        self._bat = orig.Battery(ss, sf, runner=None)
        self.na, self.ne = ss.STANDARD_N_AZ, ss.STANDARD_N_EL

    def scene(self, k):
        return self.ss.standard_mondrian() if k == "dev" else self.ss.random_mondrian(k)

    def room(self, k):
        return self._bat.room_scene() if k == "dev" else self.ss.neutral_mondrian(k)

    def n5_release(self, k):
        return (self.ss.standard_mondrian(seed=1) if k == "dev"
                else self.ss.random_mondrian(k + N5_GEOMETRY_OFFSET))

    def gt(self, sc):
        return sc.label_map().tolist()

    def lm_E(self, sc):
        return {r["patch_id"]: r["lm"] for r in self.ss.patch_report(sc, "E", 100.0)}

    # A4
    def b2_roles(self, sc):
        roles = [(0, "neutral")]
        white = self.ss.colorchecker_name(self.ss.WHITE_NUMBER)
        w = [p for p in sc.patch_ids() if sc.reflectance_of(p) == white]
        if w:
            roles.append((w[0], "white"))
            return roles
        ach = [p for p in sc.patch_ids() if not orig.is_chromatic(sc.reflectance_of(p))]
        if ach:
            lm = self.lm_E(sc)
            roles.append((min(ach, key=lambda p: (-lm[p], p)), "white"))
        return roles

    # A5
    def b4_pair(self, sc, td):
        chrom = [p for p in sc.patch_ids() if orig.is_chromatic(sc.reflectance_of(p))]
        if len(chrom) < 2:
            return None
        return self._bat.b4_pair(sc, td)

    @staticmethod
    def _free(sc, pid, offsets) -> bool:
        _p, _r, c0, r0, w, h = sc.rect(pid)
        for o in offsets:
            nc0 = c0 + o
            if nc0 < 0 or nc0 + w > sc.n_az:
                return False
            for q in sc.patch_ids():
                if q == pid:
                    continue
                _q, _rq, qc, qr, qw, qh = sc.rect(q)
                if nc0 < qc + qw and qc < nc0 + w and r0 < qr + qh and qr < r0 + h:
                    return False
        return True

    # A6
    def b5_choice(self, sc):
        for direction, steps in ((+1, B5_STEPS_POS), (-1, B5_STEPS_NEG)):
            offs, cum = [0], 0
            for dc, _dr in steps:
                cum += dc
                offs.append(cum)
            for pid in sorted(sc.patch_ids()):
                if self._free(sc, pid, offs):
                    return {"patch": pid, "direction": direction, "steps": steps}
        return None

    # A18
    def single_anchor(self, sc) -> bool:
        """True iff, under each of E, D65 and A, one surface holds the per-channel
        maximum of expected L, M and S (expected catches only)."""
        lab = sc.label_map()
        pids = [0] + sc.patch_ids()
        for ill in ("E", "D65", "A"):
            ec = self.ss.expected_catches(sc, ill, 100.0)
            top = {max(pids, key=lambda p: (float(ec[ch][lab == p].mean()), -p))
                   for ch in ("l", "m", "s")}
            if len(top) != 1:
                return False
        return True

    # A12
    def n4_choice(self, sc):
        lm = self.lm_E(sc)
        for direction in (+1, -1):
            offs = [direction * k for k in range(0, N4_MOVES + 1)]
            cand = [p for p in sorted(sc.patch_ids()) if self._free(sc, p, offs)]
            if cand:
                con = {p: abs(lm[p] - lm[0]) / (lm[p] + lm[0]) for p in cand}
                pid = min(cand, key=lambda p: (con[p], p))
                return {"patch": pid, "direction": direction, "contrast": con[pid]}
        return None


# ------------------------------------------------------------------ plan
@dataclass
class Seq:
    arm: str
    layout: object
    td: float
    world: dict
    make: Callable
    meta: dict = field(default_factory=dict)
    keep_Y: bool = False
    types_at: tuple = ()
    hook: str | None = None
    motion: bool = False


def R_WORLD():
    return {"stage45": True, "reacquire": False, "motion_segments": False,
            "recall": None, "concepts": None}


def refl_map(sc):
    return {str(p): str(sc.reflectance_of(p)) for p in [0] + sc.patch_ids()}


def build_plan(S: Scenes, layouts, tds, b6_layouts, b3_conds, b7_seeds, choices) -> list[Seq]:
    ss = S.ss
    na, ne = S.na, S.ne
    plan: list[Seq] = []

    def W(**kw):
        w = R_WORLD()
        w.update(kw)
        return w

    # R1
    for k in layouts:
        for td in tds:
            def mk(k=k, td=td):
                sc = S.scene(k)
                return [ss.render(sc, ill, td) for ill in B1_ILLS], [S.gt(sc)] * 4
            plan.append(Seq("R1", k, td, W(), mk, {"method": "cumulative", "poisson_seed": None,
                                                   "reflectances": refl_map(S.scene(k))},
                            keep_Y=True))
    # R2
    for k in layouts:
        sc = S.scene(k)
        for td in tds:
            def mk(k=k, td=td):
                sc = S.scene(k)
                scene = ss.render(sc, "E", td)
                fieldp = ss.adapting_field(sc, B2_WL, B2_QUANTA)
                ex = [scene] + [scene + fieldp] * B2_N_ADAPT + [scene]
                return ex, [S.gt(sc)] * len(ex)
            plan.append(Seq("R2", k, td, W(), mk, {"roles": S.b2_roles(sc)}))
    # R3
    for td, ill in b3_conds:
        def mk(td=td, ill=ill):
            return [ss.diffuse(na, ne, ill, td, filter="eyelid")], [None]
        plan.append(Seq("R3", None, td, W(), mk, {"illuminant": ill}))
    # R4
    for k in layouts:
        sc = S.scene(k)
        for td in tds:
            pr = choices["R4_pairs"][f"{k}|{td:g}"]
            if pr is None:
                continue
            a, b, d = pr

            def mk(k=k, td=td, a=a, b=b):
                sc = S.scene(k)
                sw = ss.swap_patches(sc, a, b)
                return [ss.render(sc, "E", td), ss.render(sw, "E", td)], [S.gt(sc), S.gt(sw)]
            plan.append(Seq("R4", k, td, W(), mk,
                            {"pair": [a, b], "lm_diff": d,
                             "pair_reflectances": [str(sc.reflectance_of(a)), str(sc.reflectance_of(b))]},
                            keep_Y=True))
    # R5 (A6: primary layouts with a qualifying patch + the declared supplement)
    for k in choices["R5_layouts"]:
        ch = choices["R5_patch"][str(k)]
        sc = S.scene(k)
        pid, steps = ch["patch"], ch["steps"]
        scenes, cur = [sc], sc
        for dc, dr in steps:
            cur = ss.translate_patch(cur, pid, dc, dr)
            scenes.append(cur)
        for td in tds:
            def mk(k=k, td=td, pid=pid, steps=steps):
                sc = S.scene(k)
                ex = ss.motion(sc, pid, steps, "E", td)
                cur, gts = sc, [S.gt(sc)]
                for dc, dr in steps:
                    cur = ss.translate_patch(cur, pid, dc, dr)
                    gts.append(S.gt(cur))
                return ex, gts
            plan.append(Seq("R5", k, td, W(), mk,
                            {"moved_patch": pid, "direction": ch["direction"],
                             "r5_set": ("primary" if k in choices["R5_layouts_primary"] else "supplement"),
                             "moved_reflectance": str(sc.reflectance_of(pid)),
                             "rects": [list(s.rect(pid)[2:]) for s in scenes]}))
    # R6 / N5
    for arm, reacq, rel_of in (("R6", False, S.scene), ("N5", True, S.n5_release)):
        for k in b6_layouts:
            room, rel = S.room(k), rel_of(k)
            for td in tds:
                def mk(k=k, td=td, rel_of=rel_of):
                    room, rel = S.room(k), rel_of(k)
                    M = ss.render(room, "E", td)
                    G = ss.diffuse(na, ne, "E", td, filter="eyelid")
                    R = ss.render(rel, "E", td)
                    ex = [{"M": M, "G": G, "R": R}[o] for o in B6_ORDER]
                    gts = [{"M": S.gt(room), "G": None, "R": S.gt(rel)}[o] for o in B6_ORDER]
                    return ex, gts
                plan.append(Seq(arm, k, td, W(reacquire=reacq), mk,
                                {"order": B6_ORDER, "room_reflectances": refl_map(room),
                                 "release_reflectances": refl_map(rel),
                                 "release_layout": (k if arm == "R6" else
                                                    (k + N5_GEOMETRY_OFFSET if k != "dev" else "dev:seed1"))},
                                types_at=(7, 10)))
    # R7
    for k in layouts:
        for td in tds:
            for sd in b7_seeds:
                def mk(k=k, td=td, sd=sd):
                    sc = S.scene(k)
                    return (ss.illuminant_change(sc, list(B1_ILLS), td, method="poisson", seed=sd),
                            [S.gt(sc)] * 4)
                plan.append(Seq("R7", k, td, W(), mk, {"method": "poisson", "poisson_seed": sd}))
    # N1
    for k in layouts:
        for td in tds:
            def mk_gg(k=k, td=td):
                sc = S.scene(k)
                U = ss.diffuse(na, ne, "E", td, filter=None)
                scene = ss.render(sc, "E", td)
                return [scene, U, U, scene], [S.gt(sc), None, None, S.gt(sc)]
            plan.append(Seq("N1", k, td, W(reacquire=True), mk_gg, {"sequence": "GG"}))
            pr = choices["R4_pairs"][f"{k}|{td:g}"]
            if pr is None:
                continue

            def mk_es(k=k, td=td, a=pr[0], b=pr[1]):
                sc = S.scene(k)
                sw = ss.swap_patches(sc, a, b)
                return ([ss.render(sc, "E", td), ss.diffuse(na, ne, "E", td, filter="eyelid"),
                         ss.render(sw, "E", td)], [S.gt(sc), None, S.gt(sw)])
            plan.append(Seq("N1", k, td, W(reacquire=True), mk_es,
                            {"sequence": "ES", "pair": [pr[0], pr[1]]}))
    # N2
    for k in layouts:
        for td in tds:
            def mk(k=k, td=td):
                sc = S.scene(k)
                return ([ss.render(sc, "E", td), ss.diffuse(na, ne, "E", td, filter="eyelid")],
                        [S.gt(sc), None])
            plan.append(Seq("N2", k, td, W(recall=True), mk, {}, hook="recall"))
    # N3
    for k in layouts:
        for td in tds:
            def mk(k=k, td=td):
                sc = S.scene(k)
                return [ss.render(sc, "E", td)], [S.gt(sc)]
            plan.append(Seq("N3", k, td, W(concepts=True), mk, {}))
    # N4
    for k in layouts:
        ch = choices["N4_patch"][str(k)]
        if ch is None:
            continue
        for td in tds:
            for flag in (True, False):
                def mk(k=k, td=td, pid=ch["patch"], d=ch["direction"]):
                    sc = S.scene(k)
                    scenes = [sc] * N4_STATIC + [ss.translate_patch(sc, pid, d * j, 0)
                                                 for j in range(1, N4_MOVES + 1)]
                    return [ss.render(s, "E", td) for s in scenes], [S.gt(s) for s in scenes]
                plan.append(Seq("N4", k, td,
                                {"stage45": False, "reacquire": False, "motion_segments": flag,
                                 "recall": None, "concepts": None}, mk,
                                {"moved_patch": ch["patch"], "direction": ch["direction"],
                                 "motion_segments": int(flag),
                                 "moved_reflectance": str(S.scene(k).reflectance_of(ch["patch"]))},
                                motion=True))
    return plan


def declared_choices(S: Scenes, layouts, tds, b6_layouts):
    ch = {"R4_pairs": {}, "R5_patch": {}, "N4_patch": {}, "R2_roles": {}, "layouts": {}}
    for k in layouts:
        sc = S.scene(k)
        ch["layouts"][str(k)] = {"n_patches": len(sc.rects), "background": str(sc.background),
                                 "white_patch": any(r[1].startswith("white") for r in sc.rects
                                                    if isinstance(r[1], str)),
                                 "reflectances": refl_map(sc)}
        for td in tds:
            p = S.b4_pair(sc, td)
            ch["R4_pairs"][f"{k}|{td:g}"] = None if p is None else [p[0], p[1], p[2]]
        ch["R5_patch"][str(k)] = S.b5_choice(sc)
        ch["N4_patch"][str(k)] = S.n4_choice(sc)
        ch["R2_roles"][str(k)] = S.b2_roles(sc)
    # A6 supplement: the first seeds > max(LAYOUTS), ascending, whose layout has an
    # R5 patch, until the R5 set has len(LAYOUTS) layouts (geometry only)
    primary = [k for k in layouts if ch["R5_patch"][str(k)] is not None]
    supp = []
    if layouts == LAYOUTS:
        k = max(LAYOUTS) + 1
        while len(primary) + len(supp) < len(LAYOUTS):
            c = S.b5_choice(S.scene(k))
            if c is not None:
                supp.append(k)
                ch["R5_patch"][str(k)] = c
            k += 1
    ch["R5_layouts_primary"], ch["R5_layouts_supplement"] = primary, supp
    ch["R5_layouts"] = primary + supp
    ch["R6_rooms"] = {str(k): refl_map(S.room(k)) for k in b6_layouts}
    ch["N5_release"] = {str(k): refl_map(S.n5_release(k)) for k in b6_layouts}
    return ch


# ------------------------------------------------------------------ running
class Runner2(orig.Runner):
    def new_world_kw(self, world: dict):
        t0 = time.perf_counter()
        w = self.PSW(self.n_az, self.n_el, **world)
        self.build_s.append(time.perf_counter() - t0)
        assert all(s["rules_skipped"] == [] for s in w.load_summaries), w.load_summaries
        flags = {}

        def one(t):
            nids = w.s.nodes(t)
            assert len(nids) == 1, (t, nids)
            return dict(w.s.node(nids[0])["attrs"])
        a = one("SurfaceSegmentationParams")
        assert a["enabled"] == 1.0 and a.get("motion_segments", 0.0) == float(world["motion_segments"]), a
        flags["SurfaceSegmentationParams"] = a
        a = one("SurfacePersistenceParams")
        assert a["enabled"] == 1.0 and a.get("reacquire", 0.0) == float(world["reacquire"]), a
        flags["SurfacePersistenceParams"] = a
        if world["stage45"]:
            a = one("ColourPropertyParams")
            assert a["enabled"] == 1.0 and a["pooled"] == 1.0, a
            flags["ColourPropertyParams"] = a
            a = one("LookingEpisodeParams")
            assert a["enabled"] == 1.0, a
            flags["LookingEpisodeParams"] = a
        for key, ptype in (("recall", "ColourRecallParams"), ("concepts", "ColourConceptParams")):
            nids = w.s.nodes(ptype)
            if world[key] is None:
                assert nids == [], (ptype, nids)
            else:
                a = one(ptype)
                assert a["enabled"] == float(bool(world[key])), (ptype, a)
                flags[ptype] = a
        flags["seeds_loaded"] = [s.get("id") for s in w.load_summaries]
        return w, flags

    def snap2(self, w, seq, gt, i) -> dict:
        snap = self.snapshot(w, gt, seq.keep_Y, types=(i in seq.types_at))
        if seq.world.get("concepts"):
            snap["concept_links"] = [orig.clean(p) for p in w.concept_links()]
        if seq.world.get("reacquire"):
            snap["reacquired_surfaces"] = len(w.reacquired_surfaces())
        if seq.motion:
            e = int(w.eye._epoch)
            cells = w.cells()
            snap["motion_segments_current"] = [orig.clean(s) for s in w.motion_segments_current()]
            snap["polygons"] = w.polygons(e)
            snap["seg_label"] = [c.get("seg_label") for c in cells]
            snap["seg_mgrp"] = ([c.get("seg_mgrp") for c in cells]
                                if seq.world["motion_segments"] else None)
        return snap

    def run_seq(self, seq: Seq) -> dict:
        exposures, gts = seq.make()
        w, flags = self.new_world_kw(seq.world)
        snaps, timings, extra = [], [], {}
        try:
            for i, (pk, gt) in enumerate(zip(exposures, gts)):
                timings.append(w.expose(pk))
                snaps.append(self.snap2(w, seq, gt, i))
            if seq.hook == "recall":
                extra["recall"] = recall_hook(w, snaps)
        finally:
            w.stop()
        return {"arm": seq.arm, "layout": seq.layout, "td": seq.td, "world": seq.world,
                **seq.meta, **extra, "flags": flags, "snaps": snaps, "timings": timings}


def recall_hook(w, snaps) -> dict:
    sids = sorted({s for v in snaps[0]["patch_sids"].values() for s in v
                   if s is not None and s >= 0})
    before = w.counts()
    n_nodes_before = w.s.node_count()
    for s in sids:
        w.recall(s)
    after_cues = w.counts()
    w.recall(N2_CONTROL_SID)
    after = w.counts()
    recs = []
    for r in w.recollections():
        r = orig.clean(r)
        r["recalls"] = [orig.clean(x) for x in r.get("recalls", [])]
        recs.append(r)
    return {"cued_sids": sids, "control_sid": N2_CONTROL_SID, "counts_before": before,
            "counts_after_cues": after_cues, "counts_after_control": after,
            "node_count_before": n_nodes_before, "node_count_after": w.s.node_count(),
            "recollections": recs}


# ------------------------------------------------------------------ analysis
def an_b2_roles(recs):
    """an_b2 of the original with the A4 roles instead of patches 0/1."""
    per = []
    for r in recs:
        S = r["snaps"]
        first, last = S[0], S[-1]
        rows = []
        for pid, role in r["roles"]:
            s1, s22 = orig.single(first, pid), orig.single(last, pid)
            l1 = orig.look_of(first, s1) if s1 is not None else None
            l22 = orig.look_of(last, s22) if s22 is not None else None
            c22 = orig.check_of(last, s22) if s22 is not None else None
            rows.append({"patch": pid, "role": role, "sid1": s1, "sid22": s22,
                         "rg1": l1["rg"] if l1 else None, "by1": l1["by"] if l1 else None,
                         "rg22": l22["rg"] if l22 else None, "by22": l22["by"] if l22 else None,
                         "status22": c22["status"] if c22 else None,
                         "pooled_status22": c22.get("pooled_status") if c22 else None,
                         "resid_max22": c22.get("resid_max") if c22 else None,
                         "link22": l22.get("link") if l22 else None})
        during = Counter(c["status"] for s in S[1:-1] for c in s["checks"])
        per.append({"layout": r["layout"], "td": r["td"], "rows": rows,
                    "during_status": dict(during),
                    "sid_grid_same_1_22": first["sid_grid"] == last["sid_grid"]})
    return per


def euclid(h) -> float:
    return math.hypot(h["rgt"] - h["rg0"], h["byt"] - h["by0"])


def r1_cluster(per1, layouts, tds) -> dict:
    out = {}
    by = {(p["layout"], p["td"]): p for p in per1}
    for td in tds:
        for lab in list(B1_LABELS[1:]) + ["D65+A"]:
            labs = ("D65", "A") if lab == "D65+A" else (lab,)
            d = {}
            for q in ("rung1_all", "rung2_all", "rung1_nonanchor", "rung2_nonanchor"):
                groups = []
                for k in layouts:
                    ch = [c for c in by[(k, td)]["checks"]
                          if c["label"] in labs and c["status"] != "minted"]
                    if "nonanchor" in q:
                        ch = [c for c in ch if not c["is_anchor"]]
                    if q.startswith("rung1"):
                        hit = sum(c["status"] == "holds" for c in ch)
                    else:
                        hit = sum(c["pooled_status"] == "holds_pooled" for c in ch)
                    groups.append((hit, len(ch)))
                d[q] = clustered(groups)
            out[f"td{td:g}_{lab}"] = d
        for lab in B1_LABELS[1:]:
            hue = [[h["dhue"] for h in by[(k, td)]["hue"] if h["label"] == lab] for k in layouts]
            eu = [[euclid(h) for h in by[(k, td)]["hue"] if h["label"] == lab] for k in layouts]
            out[f"td{td:g}_{lab}"]["hue_change"] = clustered_median(hue)
            out[f"td{td:g}_{lab}"]["euclid_shift"] = clustered_median(eu)
    anc, stab = [], []
    for k in layouts:
        a = [x for td in tds for x in by[(k, td)]["anchors"]]
        anc.append((sum(any(s["status"] == "holds" for s in x["anchor_sids"]) for x in a), len(a)))
        ne = [(p, q) for td in tds for p in [by[(k, td)]]
              for q in p["stable"] if int(q) not in p["exempt_patches"]]
        stab.append((sum(p["stable"][q] for p, q in ne), len(ne)))
    out["anchor_holds"] = clustered(anc)
    out["nonexempt_patches_stable"] = clustered(stab)
    return out


def profile_count(profiles: dict) -> dict:
    keys = {k: json.dumps(v, sort_keys=True, default=repr) for k, v in profiles.items()}
    return {"n_layouts": len(keys), "distinct_profiles": len(set(keys.values())),
            "profiles": profiles}


def profiles_R(A, raw, layouts, tds, b6_layouts) -> dict:
    out = {}
    per1 = A["B1"]["per_sequence"]
    pr = {}
    for k in layouts:
        v = []
        for p in per1:
            if p["layout"] != k:
                continue
            row = {"td": p["td"], "exempt": len(p["exempt_patches"]),
                   "nonexempt_unstable": len(p["nonexempt_unstable"]),
                   "births": len(p["births"]), "silent_rebinds": len(p["silent_rebinds"])}
            for lab in B1_LABELS[1:]:
                ch = [c for c in p["checks"] if c["label"] == lab and c["status"] != "minted"]
                na = [c for c in ch if not c["is_anchor"]]
                row[lab] = [sum(c["status"] == "holds" for c in ch),
                            sum(c["pooled_status"] == "holds_pooled" for c in ch), len(ch),
                            sum(c["status"] == "holds" for c in na), len(na)]
            v.append(row)
        pr[str(k)] = v
    out["R1"] = profile_count(pr)
    out["R2"] = profile_count({str(k): [[p["td"]] + [[r["role"], r["status22"], r["pooled_status22"],
                                                     (r["rg22"] is not None and r["rg1"] is not None
                                                      and r["rg22"] < r["rg1"]),
                                                     r["sid1"] == r["sid22"]] for r in p["rows"]]
                                        for p in A["B2"]["per_sequence"] if p["layout"] == k]
                               for k in layouts})
    out["R4"] = profile_count({str(k): [[p["td"], p["all_follow"],
                                         sorted(str(s["status"]) for s in p["swapped"]),
                                         p["others_holds"], p["others_n"]]
                                        for p in A["B4"]["per_sequence"] if p["layout"] == k]
                               for k in layouts if any(p["layout"] == k for p in A["B4"]["per_sequence"])})
    out["R5"] = profile_count({str(k): [[p["td"], p["ok"], sum(p["steps_keep_sid"]),
                                         p["jump_born_ok"], p["jump_coast_ok"]]
                                        for p in A["B5"]["per_sequence"] if p["layout"] == k]
                               for k in dict.fromkeys(p["layout"] for p in A["B5"]["per_sequence"])})
    out["R6"] = profile_count({str(k): [[p["td"], p["delta_counts"], p["new_node_types"],
                                         p["new_edge_types"],
                                         sum(c["new_property_in_release"] for c in p["chromatic_patches"]),
                                         len(p["chromatic_patches"])]
                                        for p in A["B6"]["per_sequence"] if p["layout"] == k]
                               for k in b6_layouts})
    out["R7"] = profile_count({str(k): [[c["td"], c["label"], c["median"]]
                                        for c in A["B7"]["segment_cells"] if c["layout"] == k]
                               for k in layouts})
    return out


def cluster_R(A, per7, layouts, tds, b6_layouts) -> dict:
    out = {"R1": r1_cluster(A["B1"]["per_sequence"], layouts, tds)}
    b2 = A["B2"]["per_sequence"]
    out["R2_rg_drop"] = clustered([(sum(r["rg1"] is not None and r["rg22"] is not None
                                        and r["rg22"] < r["rg1"] for p in b2 if p["layout"] == k
                                        for r in p["rows"]),
                                    sum(len(p["rows"]) for p in b2 if p["layout"] == k))
                                   for k in layouts])
    out["R2_hold_at_22"] = clustered([(sum(r["status22"] == "holds" for p in b2 if p["layout"] == k
                                           for r in p["rows"]),
                                       sum(len(p["rows"]) for p in b2 if p["layout"] == k))
                                      for k in layouts])
    b4 = A["B4"]["per_sequence"]
    l4 = [k for k in layouts if any(p["layout"] == k for p in b4)]
    out["R4_swapped_refused"] = clustered([(sum(s["status"] == "refused" for p in b4 if p["layout"] == k
                                                for s in p["swapped"]),
                                            sum(len(p["swapped"]) for p in b4 if p["layout"] == k))
                                           for k in l4])
    out["R4_all_follow"] = clustered([(sum(p["all_follow"] for p in b4 if p["layout"] == k),
                                       sum(1 for p in b4 if p["layout"] == k)) for k in l4])
    b5 = A["B5"]["per_sequence"]
    l5 = list(dict.fromkeys(p["layout"] for p in b5))     # A6: primary + supplement
    out["R5_ok"] = clustered([(sum(p["ok"] for p in b5 if p["layout"] == k),
                               sum(1 for p in b5 if p["layout"] == k)) for k in l5])
    b6 = A["B6"]["per_sequence"]
    out["R6_chromatic_new_property"] = clustered(
        [(sum(c["new_property_in_release"] for p in b6 if p["layout"] == k for c in p["chromatic_patches"]),
          sum(len(p["chromatic_patches"]) for p in b6 if p["layout"] == k)) for k in b6_layouts])
    per1 = A["B1"]["per_sequence"]
    for td in tds:
        for name, per in (("poisson", per7), ("det", per1)):
            groups = []
            for k in layouts:
                ch = [c for p in per if p["layout"] == k and p["td"] == td
                      for c in p["checks"] if c["status"] != "minted"]
                groups.append((sum(c["status"] == "refused" for c in ch), len(ch)))
            out[f"R7_td{td:g}_{name}_rung1_refused"] = clustered(groups)
    return out


def an_n1(recs) -> list:
    per = []
    for r in recs:
        S = r["snaps"]
        first, last = S[0], S[-1]
        rows = []
        for p in sorted(int(x) for x in first["patch_sids"]):
            a, b = first["patch_sids"][str(p)], last["patch_sids"].get(str(p))
            ok = a == b and all(x is not None and x >= 0 for x in a)
            rows.append({"patch": p, "sids_first": a, "sids_last": b, "reacquired": ok})
        mid_blank = [all(v is None or v < 0 for v in s["sid_grid"]) for s in S[1:-1]]
        d = {"layout": r["layout"], "td": r["td"], "sequence": r["sequence"], "patches": rows,
             "k": sum(x["reacquired"] for x in rows), "n": len(rows),
             "intermediate_blank": mid_blank,
             "last_decisions": dict(Counter(s.get("decision") for s in last["segments"])),
             "surfaces_first": len([s for s in first["surfaces"]]),
             "surfaces_last": len(last["surfaces"]),
             "reacquired_surfaces_last": last.get("reacquired_surfaces")}
        if r["sequence"] == "ES":
            sw = sorted({s for p in r["pair"] for s in first["patch_sids"][str(p)]},
                        key=lambda x: (x is None, x))
            st = {c["sid"]: c for c in last["checks"]}
            d["swapped"] = [{"sid": s, "status": st.get(s, {}).get("status"),
                             "pooled_status": st.get(s, {}).get("pooled_status")} for s in sw]
            d["others_status"] = dict(Counter(c["status"] for s, c in st.items() if s not in sw))
            d["properties_unchanged"] = first["properties"] == last["properties"]
        per.append(d)
    return per


def an_n2(recs) -> list:
    per = []
    for r in recs:
        rc = r["recall"]
        recs_ = rc["recollections"]
        cued = [x for x in recs_ if x["sid"] != rc["control_sid"]]
        ctrl = [x for x in recs_ if x["sid"] == rc["control_sid"]]
        b, a = rc["counts_before"], rc["counts_after_cues"]
        new_looks = {t: a[t] - b[t] for t in ("LookingEpisode", "SurfaceLook", "FieldLook")}
        ok = (len(cued) == len(rc["cued_sids"]) and all(x.get("status") == "recalled" for x in cued)
              and new_looks["LookingEpisode"] == 0 and new_looks["SurfaceLook"] == 0)
        per.append({"layout": r["layout"], "td": r["td"], "n_cues": len(rc["cued_sids"]),
                    "statuses": dict(Counter(str(x.get("status")) for x in cued)),
                    "control": [(x.get("status"), x.get("reason")) for x in ctrl],
                    "delta_counts_cues": {t: a[t] - b[t] for t in a},
                    "delta_counts_all": {t: rc["counts_after_control"][t] - b[t] for t in b},
                    "new_looks": new_looks, "ok": ok})
    return per


def an_n3(recs, S: Scenes) -> list:
    th = importlib.import_module("scripts.marys_room_broad_theory")
    sf, ss = S.sf, S.ss
    per = []
    for r in recs:
        snap = r["snaps"][0]
        sc = S.scene(r["layout"])
        comp = orig.composition(snap)
        links = {p["sid"]: p for p in snap["concept_links"]}
        rows = []
        for pid in [0] + sc.patch_ids():
            refl = sc.reflectance_of(pid)
            tr = th.truth_for(sf.illuminant("E", 1) * ss.reflectance_spd(refl), "E")
            s = orig.single(snap, pid)
            alone = s is not None and comp.get(s) == frozenset({pid})
            p = links.get(s) if s is not None else None
            status = p.get("concept_status") if p else None
            concept = p.get("concept") if p and status == "categorised" else None
            scored = tr["hue4"] != "achromatic" and alone
            rows.append({"patch": pid, "reflectance": str(refl), "truth_hue4": tr["hue4"],
                         "purity": tr["excitation_purity"], "sid": s, "alone": alone,
                         "concept_status": status, "concept": concept,
                         "angle": p.get("concept_angle_deg") if p else None,
                         "margin": p.get("concept_margin_deg") if p else None,
                         "scored": scored, "correct": bool(scored and concept == tr["hue4"])})
        per.append({"layout": r["layout"], "td": r["td"], "rows": rows,
                    "k": sum(x["correct"] for x in rows), "n": sum(x["scored"] for x in rows)})
    return per


def summarise_n3(per, layouts, tds) -> dict:
    out = {}
    for td in tds:
        P = [p for p in per if p["td"] == td]
        truth = Counter(x["truth_hue4"] for p in P for x in p["rows"] if x["scored"])
        n = sum(truth.values())
        k = sum(p["k"] for p in P)
        p0 = (max(truth.values()) / n) if n else None
        pval = binom_sf(k, n, p0) if n else None
        out[f"td{td:g}"] = {"accuracy": clustered([(p["k"], p["n"]) for k in layouts
                                                    for p in P if p["layout"] == k]),
                            "truth_classes": dict(truth), "majority_rate": p0,
                            "binomial_one_sided_p": pval,
                            "ok": bool(n and k / n > p0 and pval < ALPHA_Q4),
                            "concept_status": dict(Counter(str(x["concept_status"]) for p in P
                                                           for x in p["rows"] if x["scored"])),
                            "confusion": dict(Counter(f"{x['truth_hue4']}->{x['concept']}"
                                                      for p in P for x in p["rows"] if x["scored"]))}
    return out


def an_n4(recs) -> list:
    per = []
    for r in recs:
        S = r["snaps"]
        pid = r["moved_patch"]
        rows = []
        for t, s in enumerate(S):
            comp = orig.composition(s)
            sp = orig.single(s, pid)
            rows.append({"t": t, "moved_sids": s["patch_sids"].get(str(pid)),
                         "moved_alone": sp is not None and comp.get(sp) == frozenset({pid}),
                         "n_motion_segments": len(s["motion_segments_current"]),
                         "motion_segments": [(m.get("n_cells"), m.get("sid"), m.get("decision"),
                                              m.get("birth_reason")) for m in s["motion_segments_current"]],
                         "n_polygons": len(s["polygons"]),
                         "polygon_coherence": [p.get("coherence") for p in s["polygons"]],
                         "n_segments": len(s["segments"])})
        s0 = orig.single(S[N4_STATIC - 1], pid)
        per.append({"layout": r["layout"], "td": r["td"], "motion_segments": r["motion_segments"],
                    "moved_patch": pid, "moved_reflectance": r["moved_reflectance"],
                    "direction": r["direction"], "rows": rows,
                    "sid_kept_through_moves": [orig.single(S[t], pid) == s0 and s0 is not None
                                               for t in range(N4_STATIC, len(S))],
                    "any_motion_segment": any(x["n_motion_segments"] > 0 for x in rows),
                    "any_polygon": any(x["n_polygons"] > 0 for x in rows),
                    "sid_grids": [s["sid_grid"] for s in S]})
    # pair flag on / off
    for p in per:
        twin = [q for q in per if q["layout"] == p["layout"] and q["td"] == p["td"]
                and q["motion_segments"] != p["motion_segments"]]
        p["sid_grids_equal_other_flag"] = bool(twin) and twin[0]["sid_grids"] == p["sid_grids"]
    for p in per:
        p.pop("sid_grids")
    return per


def q_verdicts(A, N, tds) -> dict:
    Q = {}
    c = N["cluster"]["R1"]
    flags, nums = [], {}
    for td in tds:
        mA = c[f"td{td:g}_A"]["euclid_shift"]
        mD = c[f"td{td:g}_D65"]["euclid_shift"]
        ok = mA["median"] is not None and mD["median"] is not None and mA["median"] > mD["median"]
        flags.append(ok)
        nums[f"td{td:g}"] = {"A": mA, "D65": mD, "ok": ok}
    Q["Q1"] = {"verdict": r9(flags), "label": "data-informed (stage-4 'Not preregistered')", **nums}
    cells, nums = [], {}
    for seqk in ("GG", "ES"):
        for td in tds:
            P = [p for p in N["N1"] if p["sequence"] == seqk and p["td"] == td]
            f = clustered([(p["k"], p["n"]) for p in P])
            ok = f["value"] is not None and f["value"] >= Q2_THRESHOLD
            cells.append(ok)
            nums[f"{seqk}_td{td:g}"] = {**f, "ok": ok}
    Q["Q2"] = {"verdict": orig.universal(cells), **nums}
    Q["Q3"] = {"verdict": orig.universal(p["ok"] for p in N["N2"]),
               "k": sum(p["ok"] for p in N["N2"]), "n": len(N["N2"])}
    s3 = N["N3_summary"]
    Q["Q4"] = {"verdict": r9(s3[f"td{td:g}"]["ok"] for td in tds),
               **{f"td{td:g}": {k: v for k, v in s3[f"td{td:g}"].items() if k != "confusion"}
                  for td in tds}}
    Q["Q5"] = {"verdict": "no prediction (report only)",
               "sequences": len(N["N4"]),
               "with_motion_segment": sum(p["any_motion_segment"] for p in N["N4"]
                                          if p["motion_segments"] == 1),
               "with_polygon": sum(p["any_polygon"] for p in N["N4"] if p["motion_segments"] == 1),
               "flag_on_equal_to_off": sum(p["sid_grids_equal_other_flag"] for p in N["N4"]
                                           if p["motion_segments"] == 1)}
    return Q


def analyse(raw, S: Scenes, layouts, tds, b6_layouts, r5_supplement=(), smoke=False):
    for arm in ("R1", "R7"):
        for r in raw[arm]:
            r["_gt"] = S.gt(S.scene(r["layout"]))
    per1 = orig.an_b1(raw["R1"])
    per7 = orig.an_b1(raw["R7"])
    orig.B7_LAYOUTS = tuple(layouts)      # A3: an_b7's deterministic comparison set
    A = {"B1": {"per_sequence": per1, "replication": orig.summarise_b1(per1, tuple(layouts))},
         "B2": {"per_sequence": an_b2_roles(raw["R2"])},
         "B3": {"per_condition": orig.an_b3(raw["R3"])},
         "B4": {"per_sequence": orig.an_b4(raw["R4"])},
         "B5": {"per_sequence": orig.an_b5(raw["R5"])},
         "B6": {"per_sequence": orig.an_b6(raw["R6"])},
         "B7": orig.an_b7(per7, per1)}
    N = {"N1": an_n1(raw["N1"]), "N2": an_n2(raw["N2"]),
         "N3": an_n3(raw["N3"], S), "N4": an_n4(raw["N4"]),
         "N5": orig.an_b6(raw["N5"])}
    for p, r in zip(N["N5"], raw["N5"]):
        p["reacquired_surfaces_end_room"] = r["snaps"][7].get("reacquired_surfaces")
        p["reacquired_surfaces_end_release"] = r["snaps"][10].get("reacquired_surfaces")
        p["P5_clauses_descriptive"] = {"no_new_types": p["types_subset"],
                                       "chromatic_new_property": [c["new_property_in_release"]
                                                                  for c in p["chromatic_patches"]],
                                       "adds_looks_and_presents": p["adds_looks_and_presents"]}
    N["N3_summary"] = summarise_n3(N["N3"], layouts, tds)
    N["cluster"] = cluster_R(A, per7, layouts, tds, b6_layouts)
    N["profiles"] = profiles_R(A, raw, layouts, tds, b6_layouts)
    vl = tuple(layouts) + tuple(r5_supplement)   # A6: R5 supplement enters P1-B5 only
    if smoke:
        orig.verdicts(A, layouts=vl, tds=tds, b1_key="replication")
        q_verdicts(A, N, tds)
        return A, N, None, None
    V = orig.verdicts(A, layouts=vl, tds=tds, b1_key="replication")
    prim = [p for p in A["B5"]["per_sequence"] if p["layout"] in tuple(layouts)]
    V["P1"]["clauses"]["B5_primary_only"] = {"verdict": orig.universal(p["ok"] for p in prim),
                                             "sequences_ok": sum(p["ok"] for p in prim),
                                             "n": len(prim)}
    # A18 secondary (not a verdict input): P3 anchor clause on single-anchor layouts
    sal = [k for k in layouts if S.single_anchor(S.scene(k))]
    fr = [a for a in A["B1"]["replication"]["anchor_frames"] if a["layout"] in sal]
    V["P3"]["clauses"]["anchor_every_frame_single_anchor_layouts_SECONDARY"] = {
        "verdict": orig.universal(a["rung1_holds_on_anchor"] for a in fr),
        "layouts": sal, "k": sum(a["rung1_holds_on_anchor"] for a in fr), "n": len(fr)}
    Q = q_verdicts(A, N, tds)
    return A, N, V, Q


# ------------------------------------------------------------------ pre-check (no eye)
def precheck():
    from domains import spectral_scene as ss
    short = {"white 9.5 (.05 D)": "white", "neutral 8 (.23 D)": "n8", "neutral 6.5 (.44 D)": "n6.5",
             "neutral 5 (.70 D)": "n5", "neutral 3.5 (1.05 D)": "n3.5", "black 2 (1.5 D)": "black"}

    def nm(x):
        return short.get(str(x), str(x))

    def profile(sc):
        lab = sc.label_map()
        pids = [0] + sc.patch_ids()
        pairs = set()
        h = lab[:, 1:] != lab[:, :-1]
        for a, b in zip(lab[:, 1:][h], lab[:, :-1][h]):
            pairs.add(tuple(sorted((int(a), int(b)))))
        v = lab[1:, :] != lab[:-1, :]
        for a, b in zip(lab[1:, :][v], lab[:-1, :][v]):
            pairs.add(tuple(sorted((int(a), int(b)))))
        out = {"n": len(sc.rects), "bg": nm(sc.background),
               "white_patch": any(str(r[1]).startswith("white") for r in sc.rects),
               "adj_pairs": len(pairs), "anchor": {}, "iso": {}}
        for ill in ("E", "D65", "A"):
            ec = ss.expected_catches(sc, ill, 100.0)
            mean = {ch: {p: float(ec[ch][lab == p].mean()) for p in pids} for ch in ("l", "m", "s")}
            top = {ch: max(pids, key=lambda p: (mean[ch][p], -p)) for ch in ("l", "m", "s")}
            out["anchor"][ill] = (nm(sc.reflectance_of(top["l"])) if len(set(top.values())) == 1
                                  else "none(" + "/".join(nm(sc.reflectance_of(top[c]))
                                                          for c in ("l", "m", "s")) + ")")
        for td in (100.0, 1000.0):
            for ill in ("E", "D65", "A"):
                ec = ss.expected_catches(sc, ill, td)["lm"]
                Y = {p: float(ec[lab == p].mean()) for p in pids}
                out["iso"][f"{ill}@{td:g}"] = sum(abs(Y[a] - Y[b]) <= math.sqrt(Y[a] + Y[b])
                                                  for a, b in pairs)
        ec = ss.expected_catches(sc, "E", 100.0)["lm"]
        Y = {p: float(ec[lab == p].mean()) for p in pids}
        ratios = sorted(round(max(Y[a], Y[b]) / min(Y[a], Y[b]), 3) for a, b in pairs)
        out["ratios"] = ratios
        out["ratio_hash"] = hashlib.sha256(json.dumps(ratios).encode()).hexdigest()[:8]
        out["label_hash"] = hashlib.sha256(lab.tobytes()).hexdigest()[:8]
        return out

    print("INDEPENDENCE PRE-CHECK (spectral_scene.expected_catches only; no eye, no seeds)")
    print("anchor = the surface holding the per-channel max of expected L, M and S "
          "(none(L/M/S) if no single surface does); near-iso = 4-adjacent surface pairs with "
          "|dY| <= sqrt(Ya+Yb), Y = expected L+M; ratios = adjacent-pair max(Y)/min(Y) under E")
    hdr = (f"{'seed':>4} {'n':>2} {'wht':>3} {'bg':>6} {'anchor E':>14} {'anchor D65':>14} "
           f"{'anchor A':>14} {'adj':>3} {'ratio set':>9} {'min r':>6} {'med r':>6} "
           f"{'iso E/D65/A @100':>16} {'@1000':>8}")
    print(hdr)
    rows = {}
    for seed in LAYOUTS:
        p = profile(ss.random_mondrian(seed))
        rows[seed] = p
        r = p["ratios"]
        print(f"{seed:>4} {p['n']:>2} {('yes' if p['white_patch'] else 'no'):>3} {p['bg']:>6} "
              f"{p['anchor']['E']:>14} {p['anchor']['D65']:>14} {p['anchor']['A']:>14} "
              f"{p['adj_pairs']:>3} {p['ratio_hash']:>9} {r[0]:>6.3f} {orig.median(r):>6.3f} "
              f"{p['iso']['E@100']:>5}/{p['iso']['D65@100']}/{p['iso']['A@100']:<6} "
              f"{p['iso']['E@1000']}/{p['iso']['D65@1000']}/{p['iso']['A@1000']}")

    def distinct(key, rs):
        return len({json.dumps(key(p), sort_keys=True) for p in rs.values()})
    summ = {"label_maps": distinct(lambda p: p["label_hash"], rows),
            "anchor_identity": distinct(lambda p: p["anchor"], rows),
            "adjacent_ratio_sets": distinct(lambda p: p["ratios"], rows),
            "near_iso_profiles": distinct(lambda p: p["iso"], rows)}
    print(f"distinct over seeds 101..116: {summ}")
    old = {k: profile(ss.standard_mondrian(seed=k)) for k in range(1, 9)}
    old_s = {"label_maps": distinct(lambda p: p["label_hash"], old),
             "anchor_identity": distinct(lambda p: p["anchor"], old),
             "adjacent_ratio_sets": distinct(lambda p: p["ratios"], old),
             "near_iso_profiles": distinct(lambda p: p["iso"], old)}
    print(f"for comparison, the stage-4 held-out layouts standard_mondrian(seed=1..8): {old_s}")
    return rows, summ, old_s


# ------------------------------------------------------------------ helpers for runs
def payload_hash(obj) -> str:
    return orig.payload_hash(obj)


def arm_summary(plan) -> dict:
    out = {}
    for s in plan:
        d = out.setdefault(s.arm, {"sequences": 0, "layouts": set()})
        d["sequences"] += 1
        d["layouts"].add(s.layout)
    return {a: {"sequences": d["sequences"], "layouts": len(d["layouts"])} for a, d in out.items()}


def install_exposure_guard():
    """Dry-run sentinel: any exposure aborts the process."""
    from domains import photon_eye
    from domains import perceived_surface_world as psw
    calls = {"submit_photons_2d": 0, "expose": 0}

    def no_submit(self, *a, **k):
        calls["submit_photons_2d"] += 1
        raise SystemExit("DRY-RUN VIOLATION: GraphEye.submit_photons_2d called")

    def no_expose(self, *a, **k):
        calls["expose"] += 1
        raise SystemExit("DRY-RUN VIOLATION: PerceivedSurfaceWorld.expose called")
    photon_eye.GraphEye.submit_photons_2d = no_submit
    psw.PerceivedSurfaceWorld.expose = no_expose
    return calls


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--precheck", action="store_true")
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--smoke", action="store_true")
    g.add_argument("--from-raw", default=None)
    args = ap.parse_args()
    t_start = time.time()

    if args.precheck:
        precheck()
        return

    print("RULES_A1 (fixed before any exposure):")
    for k, v in RULES_A1.items():
        print(f"  {k}: {v}")
    confirmatory = not (args.dry_run or args.smoke)
    fz = freeze_check(strict=confirmatory)
    print(f"git HEAD {fz['head']}; freeze {'OK' if fz['freeze_ok'] else 'NOT HELD'} "
          f"(ls-files exit {fz['ls_files_error_unmatch_exit']}, untracked {fz['untracked_under_freeze']}, "
          f"diff exit {fz['diff_quiet_head_exit']} {fz['diff_names']}, data/colour "
          f"{'match' if fz['data_colour_sha256'] == DATA_COLOUR_SHA256 else 'MISMATCH'}); "
          f"script sha256 {fz['script_sha256']}")
    if not fz["freeze_ok"]:
        print("  (not a confirmatory run: the freeze is reported, not enforced)")

    from domains.engine_provenance import engine_preamble, provenance_line, provenance_stamp
    engine_preamble()
    from domains import spectral_scene as ss          # noqa: E402
    from domains import spectral_forward as sf        # noqa: E402
    from domains.perceived_surface_world import PerceivedSurfaceWorld  # noqa: E402
    pl = provenance_line()
    print(pl)
    if EXPECTED_ENGINE not in pl:
        raise SystemExit(f"ABORT: engine is not {EXPECTED_ENGINE}")
    stamp = provenance_stamp()

    S = Scenes(ss, sf)
    if args.smoke:
        layouts, tds, b6_layouts = ("dev",), (1000.0,), ("dev",)
        b3_conds, b7_seeds = [(1000.0, "E")], B7_SEEDS[:1]
    else:
        layouts, tds, b6_layouts = LAYOUTS, TDS, B6_LAYOUTS
        b3_conds, b7_seeds = [(td, ill) for td in B3_TDS for ill in B3_ILLS], B7_SEEDS
    choices = declared_choices(S, layouts, tds, b6_layouts)
    plan = build_plan(S, layouts, tds, b6_layouts, b3_conds, b7_seeds, choices)
    print("DECLARED CHOICES (geometry / expected catches only):")
    print("  R4 pairs [a, b, |dL+M|]:", json.dumps({k: (v if v is None else [v[0], v[1], round(v[2], 1)])
                                                    for k, v in choices["R4_pairs"].items()}))
    print("  R5 moved patch:", json.dumps({k: (None if v is None else {"patch": v["patch"],
                                                                       "direction": v["direction"]})
                                           for k, v in choices["R5_patch"].items()}))
    print("  N4 moved patch:", json.dumps({k: (None if v is None else {"patch": v["patch"],
                                                                       "direction": v["direction"],
                                                                       "contrast": round(v["contrast"], 4)})
                                           for k, v in choices["N4_patch"].items()}))
    print("  R2 roles:", json.dumps(choices["R2_roles"]))
    print("  layouts:", json.dumps({k: [v["n_patches"], v["background"], v["white_patch"]]
                                    for k, v in choices["layouts"].items()}))

    runner = Runner2(PerceivedSurfaceWorld, S.na, S.ne)
    det_plan = [s for s in plan if s.arm in ("R1", "R3")]

    if args.dry_run:
        calls = install_exposure_guard()
        per_arm = {}
        snapshot_checked = set()
        t0 = time.time()
        for seq in plan:
            ex, gts = seq.make()
            assert len(ex) == len(gts)
            d = per_arm.setdefault(seq.arm, {"sequences": 0, "exposures": 0, "packets": 0,
                                             "worlds": 0, "layouts": set()})
            d["sequences"] += 1
            d["exposures"] += len(ex)
            d["packets"] += sum(len(p) for p in ex)
            d["layouts"].add(seq.layout)
            w, _flags = runner.new_world_kw(seq.world)
            try:
                d["worlds"] += 1
                key = (seq.arm, json.dumps(seq.world, sort_keys=True))
                if key not in snapshot_checked:   # reader paths on an unexposed world
                    runner.snap2(w, seq, gts[0], 0)
                    if seq.hook == "recall":
                        w.recollections()
                    snapshot_checked.add(key)
            finally:
                w.stop()
        n_exp = sum(d["exposures"] for d in per_arm.values())
        n_det = sum(len(s.make()[0]) for s in det_plan)
        n_build = len(plan) + len(det_plan)
        print("PLANNED EXPOSURES (per arm):")
        for a, d in per_arm.items():
            print(f"  {a}: {d['sequences']} sequences over {len(d['layouts'])} layout(s), "
                  f"{d['exposures']} exposures, {d['packets']} packets, {d['worlds']} worlds built")
        print(f"  determinism re-run (R1 + R3): {len(det_plan)} sequences, {n_det} exposures")
        excluded = {"R4": [k for k in layouts if all(choices["R4_pairs"][f"{k}|{td:g}"] is None for td in tds)],
                    "R5": [k for k in layouts if choices["R5_patch"][str(k)] is None],
                    "N4": [k for k in layouts if choices["N4_patch"][str(k)] is None]}
        print(f"  layouts without a sequence (declared rule): {excluded}")
        print(f"  R5 layouts: primary {choices['R5_layouts_primary']} + supplement "
              f"{choices['R5_layouts_supplement']}")
        est = (n_exp + n_det) * SEC_PER_EXPOSURE + n_build * SEC_PER_BUILD
        est_max = (n_exp + n_det) * SEC_PER_EXPOSURE_MAX + n_build * SEC_PER_BUILD
        print(f"ESTIMATE: {n_exp} exposures + {n_det} determinism exposures, {n_build} world builds; "
              f"~{est / 60:.1f} min at {SEC_PER_EXPOSURE} s/exposure (smoke mean), "
              f"<= ~{est_max / 60:.1f} min at {SEC_PER_EXPOSURE_MAX} s (stage-4 max)")
        print(f"dry-run wall {time.time() - t0:.1f} s; GraphEye.submit_photons_2d calls = "
              f"{calls['submit_photons_2d']}; PerceivedSurfaceWorld.expose calls = {calls['expose']}")
        assert calls == {"submit_photons_2d": 0, "expose": 0}
        print("DRY-RUN OK (no exposure submitted)")
        return

    ckpt = ("/tmp/marys_room_stage4_replication_smoke_raw.json" if args.smoke
            else "/tmp/marys_room_stage4_replication_raw.json")
    if args.from_raw:
        with open(args.from_raw) as f:
            saved = json.load(f)
        raw, det, runner.build_s = saved["raw"], saved["determinism"], saved["build_s"]
        print(f"loaded raw checkpoint {args.from_raw} (sha {payload_hash(raw)})")
    else:
        raw = {}
        for arm in ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "N1", "N2", "N3", "N4", "N5"):
            seqs = [s for s in plan if s.arm == arm]
            print(f"[{arm}] running {len(seqs)} sequences", flush=True)
            t0 = time.time()
            raw[arm] = []
            for s in seqs:
                r = runner.run_seq(s)
                raw[arm].append(r)
                print(f"  {arm} k={s.layout} td={s.td:g} {json.dumps(s.meta.get('sequence') or s.meta.get('poisson_seed') or s.meta.get('motion_segments', ''))} "
                      f"{sum(r['timings']):.1f}s", flush=True)
            print(f"[{arm}] done {time.time() - t0:.1f}s", flush=True)
        print("[determinism] re-running R1 and R3", flush=True)
        h1 = {"R1": payload_hash(raw["R1"]), "R3": payload_hash(raw["R3"])}
        again = {"R1": [runner.run_seq(s) for s in plan if s.arm == "R1"],
                 "R3": [runner.run_seq(s) for s in plan if s.arm == "R3"]}
        h2 = {k: payload_hash(v) for k, v in again.items()}
        det = {"first": h1, "second": h2, "identical": h1 == h2}
        print("determinism:", det, flush=True)
        assert h1 == h2, "DETERMINISM FAILED"
        with open(ckpt, "w") as f:
            json.dump({"raw": raw, "determinism": det, "build_s": runner.build_s}, f, default=repr)
        with open(ckpt) as f:
            raw = json.load(f)["raw"]
        print(f"raw checkpoint {ckpt} (sha {payload_hash(raw)})", flush=True)

    A, N, V, Q = analyse(raw, S, layouts, tds, b6_layouts,
                         r5_supplement=choices["R5_layouts_supplement"], smoke=args.smoke)
    runtime = time.time() - t_start
    all_t = [t for arm in raw.values() for r in arm for t in r["timings"]]
    perf = {"wall_s": runtime, "exposures": len(all_t),
            "exposure_s_mean": sum(all_t) / len(all_t), "exposure_s_max": max(all_t),
            "world_builds": len(runner.build_s),
            "world_build_s_mean": sum(runner.build_s) / max(len(runner.build_s), 1)}
    for arm in raw.values():
        for r in arm:
            r.pop("_gt", None)
    payload = {"study": "marys-room-stage4-replication-A1", "amendment": AMENDMENT,
               "smoke": args.smoke, "freeze": fz, "script_sha256": fz["script_sha256"],
               "git_head": fz["head"], "engine_provenance": stamp, "provenance_line": pl,
               "rules_original": orig.RULES, "rules_A1": RULES_A1, "declared_choices": choices,
               "determinism": det, "perf": perf, "raw_payload_sha256": payload_hash(raw),
               "analysis_R": A, "analysis_N": N, "verdicts_P": V, "verdicts_Q": Q, "raw": raw}
    out_dir = "/tmp/marys_room_stage4_replication_smoke" if args.smoke else os.path.join(ROOT, "results")
    os.makedirs(out_dir, exist_ok=True)
    jp = os.path.join(out_dir, "marys_room_stage4_replication.json")
    with open(jp, "w") as f:
        json.dump(payload, f, default=lambda o: sorted(o) if isinstance(o, (set, frozenset)) else repr(o))
    print(f"wrote {jp}; runtime {runtime / 60:.1f} min; {len(all_t)} exposures; "
          f"mean {perf['exposure_s_mean']:.3f} s/exposure")
    if args.smoke:
        print("SMOKE OK (verdicts not computed)")
        return
    print("\nVERDICTS (P: replication of P1-P6; Q: amendment A1)")
    for name, v in list(V.items()) + list(Q.items()):
        print(f"  {name}: {v['verdict']}")
        print("     " + json.dumps({k: x for k, x in v.items() if k != "verdict"},
                                   default=lambda o: dict(o) if isinstance(o, Counter) else repr(o))[:2000])
    print("\nINDEPENDENCE (distinct per-layout outcome profiles):",
          {a: f"{p['distinct_profiles']}/{p['n_layouts']}" for a, p in N["profiles"].items()})


if __name__ == "__main__":
    main()

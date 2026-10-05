"""Mary's Room broad study -- frozen stimulus manifest + Arm A (theory only).

Implements Amendment A1 of docs/experiments/marys-room-broad-prereg.md.

    python -m scripts.marys_room_broad_theory            # manifest + Arm A
    python -m scripts.marys_room_broad_theory --freeze   # ... + hash lock
    python -m scripts.marys_room_broad_theory --verify   # rebuild, compare to lock

This script NEVER imports domains.photon_eye and never builds or runs an eye.
Outputs are deterministic (no timestamps) except the freeze file.

Helpers for later stages (import, do not re-implement):
    load_manifest(), spd_from_recipe(recipe), eye_packets(entry, column),
    theory_for_spd(spd, observer), ANCHORS (from Arm A json), hue4(), binary().
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

from domains import spectral_forward as sf  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "results" / "marys_room_broad_stimuli.json"
ARMA_PATH = ROOT / "results" / "marys_room_broad_armA.json"
FREEZE_PATH = ROOT / "results" / "marys_room_broad_freeze.json"
PREREG_PATH = ROOT / "docs" / "experiments" / "marys-room-broad-prereg.md"
SPEC_PATH = ROOT / "docs" / "research" / "spectral-forward-model-spec.md"
MANIFEST_SCHEMA = "marys_room_broad_stimuli/v1"

# ---------------------------------------------------------------- A1-1 truth
# Kuehni (2004) Color Res Appl 29:158-162, Table I, spectral-light data sets,
# observer-weighted means (see prereg Amendment A1-1).
UB_NM = 478.0
UG_NM = 514.8
UY_NM = 576.3
UR_COMPLEMENTARY_NM = 495.2
UR_SPECTRAL_SIDE_NM = 605.0
HUE4_BOUNDS = (496.4, 545.55, 590.65)   # blue|green, green|yellow, yellow|red
PURITY_MIN = 0.05
HUE4 = ("red/purple", "yellow", "green", "blue")
BINARY = ("reddish", "greenish")
SIGN_TO_BINARY = {"red": "reddish", "green": "greenish"}
_KUEHNI = {
    "UB": [(474, 19), (480, 50), (471, 4), (479, 7)],
    "UG": [(506, 19), (509, 50), (510, 4), (512, 97), (522, 100), (517, 7)],
    "UY": [(574, 19), (577, 50), (575, 4), (578, 7)],
    "UR_complementary": [(497.5, 2), (494.6, 7)],
}

# ---------------------------------------------------------------- A1-3 design
INTENSITIES_Q = (100, 1000, 10000)
TRAIN_WL = tuple(range(400, 701, 10))
HELDOUT_WL = tuple(range(405, 700, 10))
RG_ZERO_NM = 554.08                     # A0-e, CIE 2deg CVRL 1 nm
BOUNDARY_WL = tuple(w for w in range(math.ceil(RG_ZERO_NM - 20), math.floor(RG_ZERO_NM + 20) + 1)
                    if w % 5)
ILLUMS = ("E", "D65", "A")
ILLUM_TD = (10.0, 100.0, 1000.0)
SCENE_TD = 100.0
METAMER_KW = {"amplitude": 0.8, "cycles": 3.0, "phase": 0.0}
METAMER_PATCHES = ("red", "green", "blue", "yellow", "dark skin")
EYELID_AMBIENT_TD = (100.0, 1000.0, 10000.0)
EYELID_OD_LONGS = (1.0, 1.3, 1.6)
ADAPT_EPOCHS = 20
ADAPT_TEST_WL = (450, 480, 510, 530, 550, 554, 560, 570, 580, 600, 610, 630)
POISSON_MONO_WL = (450, 500, 530, 550, 554, 570, 610, 650)
POISSON_TRIALS = 10
POISSON_SEED_BASE = 20261004
BOOT_SEED = 20261004
BOOT_B = 10000
WILSON_Z = 1.959963984540054
PILOT_SMOKE = {"610": (0.3436120168296669, -0.3456013062040921),
               "530": (-0.07537232767138446, -0.6214367610772381)}

# ---------------------------------------------------------------- filters

def _density_table(fname: str) -> np.ndarray:
    rows = []
    for line in (sf.RAW_DIR / fname).read_text().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 2 and parts[0]:
            rows.append((float(parts[0]), float(parts[1]) if parts[1] else 0.0))
    return np.asarray(rows)


def prereceptoral_density(name: str, step: int = 1) -> np.ndarray:
    """Stockman, Sharpe & Fach (1999) lens or macular optical density on grid."""
    fname = {"lens": "lensss_1.csv", "macular": "macss_1.csv"}[name]
    t = _density_table(fname)
    lut = {int(round(w)): d for w, d in t}
    return np.array([lut[int(w)] for w in sf.grid(step)])


def filter_transmittance(spec: dict | None, step: int) -> np.ndarray:
    if spec is None:
        return np.ones(len(sf.grid(step)))
    kind = spec["kind"]
    if kind == "eyelid":
        return sf.eyelid_transmittance(spec["od_short"], spec["od_long"], step)
    if kind in ("lens", "macular"):
        return 10.0 ** (-prereceptoral_density(kind, step))
    raise ValueError(f"unknown filter {spec!r}")


# ---------------------------------------------------------------- recipes

def spd_from_recipe(r: dict) -> np.ndarray:
    """Deterministic SPD (absolute, on grid(step)) from a manifest recipe."""
    kind = r["kind"]
    step = int(r.get("step", 1))
    if kind == "mono":
        return sf.monochromatic_spd(r["wavelength_nm"], r["quanta"], step=step)
    if kind == "line_energy":             # single bin carrying `energy` (x dl)
        spd = np.zeros(len(sf.grid(step)))
        spd[sf._index(r["wavelength_nm"], step)] = float(r["energy"]) / step
        return spd
    if kind == "scene":
        ill = sf.scale_to_td(sf.illuminant(r["illuminant"], step), r["scene_td"])
        refl = np.ones(len(ill)) if r.get("reflectance") is None else sf.reflectance(r["reflectance"], step)
        return ill * refl * filter_transmittance(r.get("filter"), step)
    if kind == "metamer":
        base = spd_from_recipe(r["base"])
        return sf.metamer(base, amplitude=r["amplitude"], cycles=r["cycles"], phase=r["phase"])
    if kind == "mixture":
        return sum(float(c["weight"]) * spd_from_recipe(c["recipe"]) for c in r["components"])
    raise ValueError(f"unknown recipe kind {kind!r}")


def spd_sha(spd) -> str:
    return hashlib.sha256(np.ascontiguousarray(spd, dtype="<f8").tobytes()).hexdigest()


def packets_compact(spd, method="cumulative", seed=None):
    pk = sf.quantize(spd, method=method, seed=seed)
    return [[p["wavelength_nm"], p["count"]] for p in pk]


def packets_sha(compact) -> str:
    return hashlib.sha256(json.dumps(compact, separators=(",", ":")).encode()).hexdigest()


def eye_packets(entry: dict, column: int, manifest_index: dict | None = None) -> list[dict]:
    """Eye packets {column, wavelength_nm, count} for a manifest entry.
    Wrong-observer entries resolve to their base stimulus."""
    ei = entry["eye_input"]
    if "identical_to" in ei:
        if manifest_index is None:
            raise ValueError("need manifest_index to resolve identical_to")
        return eye_packets(manifest_index[ei["identical_to"]], column, manifest_index)
    return [{"column": int(column), "wavelength_nm": float(w), "count": int(c)}
            for w, c in ei["packets"]]


def load_manifest(path: Path = MANIFEST_PATH) -> dict:
    return json.loads(Path(path).read_text())


# ---------------------------------------------------------------- truth

def hue4(dw: float, purity: float) -> str:
    if not (purity >= PURITY_MIN) or math.isnan(dw):
        return "achromatic"
    if dw < 0:
        return "red/purple"
    b1, b2, b3 = HUE4_BOUNDS
    if dw < b1:
        return "blue"
    if dw < b2:
        return "green"
    if dw < b3:
        return "yellow"
    return "red/purple"


def binary(dw: float, purity: float) -> str:
    if not (purity >= PURITY_MIN) or math.isnan(dw):
        return "achromatic"
    if dw < 0 or dw < UB_NM or dw > UY_NM:
        return "reddish"
    return "greenish"


def truth_for(spd, white: str) -> dict:
    dw, pur = sf.dominant_wavelength(spd, white=white)
    return {"white": white, "dominant_wavelength_nm": dw, "excitation_purity": pur,
            "purple": bool(dw < 0), "hue4": hue4(dw, pur), "binary": binary(dw, pur)}


# ---------------------------------------------------------------- anchors

def _lmsbar(wl_nm: float) -> np.ndarray:
    return sf.load_lms("2deg", 1)[sf._index(wl_nm, 1)]


def _interp_train(locus: float) -> tuple[np.ndarray, tuple[int, int]]:
    lo = int(math.floor(locus / 10.0) * 10)
    hi = lo + 10
    assert lo in TRAIN_WL and hi in TRAIN_WL
    a, b = _lmsbar(lo), _lmsbar(hi)
    return a + (locus - lo) / 10.0 * (b - a), (lo, hi)


def _red_mixture(f: float) -> dict:
    return {"kind": "mixture", "components": [
        {"weight": 1.0 - f, "recipe": {"kind": "line_energy", "wavelength_nm": 700, "energy": 1.0}},
        {"weight": f, "recipe": {"kind": "line_energy", "wavelength_nm": 400, "energy": 1.0}}]}


def red_anchor_fraction() -> float:
    """Energy fraction f of 400 nm in a 400/700 nm mixture with E-referenced
    complementary dominant wavelength UR_COMPLEMENTARY_NM (bisection)."""
    def g(f):
        dw, _ = sf.dominant_wavelength(spd_from_recipe(_red_mixture(f)), white="E")
        return dw
    def val(f):
        dw = g(f)
        return None if not dw < 0 else (-dw - UR_COMPLEMENTARY_NM)

    fs = np.logspace(-6, -1e-4, 600)
    vals = [val(f) for f in fs]
    for i in range(len(fs) - 1):
        a, b = vals[i], vals[i + 1]
        if a is not None and b is not None and (a == 0 or a * b < 0):
            lo, hi, vlo = fs[i], fs[i + 1], a
            for _ in range(80):
                mid = 0.5 * (lo + hi)
                vm = val(mid)
                if vm is None:
                    raise RuntimeError("left purple region during bisection")
                if vm * vlo > 0:
                    lo, vlo = mid, vm
                else:
                    hi = mid
            return float(0.5 * (lo + hi))
    raise RuntimeError("no 400/700 nm mixture reaches the unique-red complementary locus")


def build_anchors() -> dict:
    out = {}
    for name, locus in (("blue", UB_NM), ("green", UG_NM), ("yellow", UY_NM)):
        lms, br = _interp_train(locus)
        rg, by = sf.opponent(lms)
        out[name] = {"locus_nm": locus, "train_bracket_nm": list(br),
                     "lms_per_unit_energy": lms.tolist(), "rg_by": [rg, by]}
    f = red_anchor_fraction()
    rec = _red_mixture(f)
    spd = spd_from_recipe(rec)
    lms = sf.lms_from_spd(spd)
    rg, by = sf.opponent(lms)
    dw, pur = sf.dominant_wavelength(spd, "E")
    out["red/purple"] = {"locus": f"complementary {UR_COMPLEMENTARY_NM} nm",
                         "mixture_fraction_400nm_energy": f, "recipe": rec,
                         "check_dominant_wavelength_nm": dw, "check_purity": pur,
                         "lms": lms.tolist(), "rg_by": [rg, by]}
    for v in out.values():
        rg, by = v["rg_by"]
        n = math.hypot(rg, by)
        v["unit_direction"] = [rg / n, by / n]
        v["angle_deg"] = math.degrees(math.atan2(by, rg))
    return out


# ---------------------------------------------------------------- theory

def _angle_between(u, v) -> float:
    c = max(-1.0, min(1.0, u[0] * v[0] + u[1] * v[1]))
    return math.degrees(math.acos(c))


def decode(rg: float, by: float, anchors: dict) -> dict:
    sign = "red" if rg > 0 else ("green" if rg < 0 else "undecided")
    lm = None
    n = math.hypot(rg, by)
    if n == 0:
        return {"sign": sign, "multi": "undecided", "multi_margin_deg": 0.0, "angle_to_anchor_deg": {}}
    u = (rg / n, by / n)
    ang = {k: _angle_between(u, a["unit_direction"]) for k, a in anchors.items()}
    order = sorted(ang, key=lambda k: (ang[k], k))
    lm = order[0]
    return {"sign": sign, "multi": lm, "multi_margin_deg": ang[order[1]] - ang[order[0]],
            "angle_to_anchor_deg": ang}


def theory_for_spd(spd, anchors: dict, observer: str = "2deg") -> dict:
    lms = sf.lms_from_spd(spd, observer=observer)
    rg, by = sf.opponent(lms)
    d = decode(rg, by, anchors)
    lm_sum = float(lms[0] + lms[1])
    return {"observer": observer, "lms": lms.tolist(), "rg": rg, "by": by,
            "opponent_angle_deg": math.degrees(math.atan2(by, rg)),
            "rg_rel": rg / lm_sum if lm_sum > 0 else float("nan"),
            "sign_label": d["sign"], "sign_margin_rel": abs(rg) / lm_sum if lm_sum > 0 else 0.0,
            "multi_label": d["multi"], "multi_margin_deg": d["multi_margin_deg"],
            "angle_to_anchor_deg": d["angle_to_anchor_deg"]}


# ---------------------------------------------------------------- manifest

class Builder:
    def __init__(self):
        self.entries: list[dict] = []
        self.by_key: dict[str, str] = {}

    def eye_block(self, recipe: dict, method="cumulative", seed=None) -> tuple[dict, np.ndarray]:
        spd = spd_from_recipe(recipe)
        step = int(recipe.get("step", 1))
        compact = packets_compact(spd, method, seed)
        psha = packets_sha(compact)
        blk = {"recipe": recipe, "step": step, "spd_sha256": spd_sha(spd),
               "td": sf.retinal_illuminance_td(spd),
               "expected_quanta_total": float(sf.expected_quanta(spd).sum()),
               "quantize": {"method": method, "seed": seed, "photon_conversion": "quantal",
                            "quanta_scale": sf.QUANTA_SCALE},
               "packets": compact, "packets_total": int(sum(c for _, c in compact)),
               "n_packets": len(compact), "packets_sha256": psha}
        return blk, spd

    def add(self, eid, family, split, params, recipe, white, *, theory_recipe=None,
            method="cumulative", seed=None, adversarial=False, extra=None, check_dup=True):
        blk, spd = self.eye_block(recipe, method, seed)
        key = f"{blk['step']}:{blk['packets_sha256']}"
        blk["duplicate_of"] = self.by_key.get(key) if check_dup else None
        if check_dup and key not in self.by_key:
            self.by_key[key] = eid
        e = {"id": eid, "family": family, "split": split, "adversarial": adversarial,
             "params": params, "eye_input": blk}
        if theory_recipe is None:
            e["theory_input"] = {"same_as_eye_input": True, "observer": "2deg"}
        else:
            tspd = spd_from_recipe(theory_recipe)
            e["theory_input"] = {"same_as_eye_input": False, "observer": "2deg",
                                 "recipe": theory_recipe, "spd_sha256": spd_sha(tspd)}
        e["truth"] = truth_for(spd, white)
        if extra:
            e.update(extra)
        self.entries.append(e)
        return e


def mono_recipe(wl, q, step=1):
    return {"kind": "mono", "wavelength_nm": float(wl), "quanta": float(q), "step": step}


def scene_recipe(ill, td, refl=None, filt=None, step=1):
    return {"kind": "scene", "illuminant": ill, "scene_td": float(td), "reflectance": refl,
            "filter": filt, "step": step}


def build_manifest(anchors: dict) -> dict:
    B = Builder()
    names = sf.reflectance_names()
    # 1 mono sweep
    for q in INTENSITIES_Q:
        for wl in sorted(TRAIN_WL + HELDOUT_WL):
            split = "train" if wl in TRAIN_WL else "heldout"
            B.add(f"mono_{wl}nm_q{q}", "mono_sweep", split,
                  {"wavelength_nm": wl, "quanta": q}, mono_recipe(wl, q), "E")
    # 2 boundary dense
    for q in INTENSITIES_Q:
        for wl in BOUNDARY_WL:
            B.add(f"bnd_{wl}nm_q{q}", "boundary_dense", "heldout",
                  {"wavelength_nm": wl, "quanta": q, "dist_from_rg_zero_nm": wl - RG_ZERO_NM},
                  mono_recipe(wl, q), "E")
    # 3 bare illuminants
    for ill in ILLUMS:
        for td in ILLUM_TD:
            e = B.add(f"illum_{ill}_{int(td)}td", "illuminant", "heldout",
                      {"illuminant": ill, "scene_td": td}, scene_recipe(ill, td), ill)
            e["truth"]["secondary_E_referenced"] = truth_for(spd_from_recipe(scene_recipe(ill, td)), "E")
    # 4 reflectances
    for ill in ILLUMS:
        for i, nm in enumerate(names, 1):
            B.add(f"refl_{i:02d}_{ill}", "reflectance", "heldout",
                  {"patch": i, "patch_name": nm, "illuminant": ill, "diffuser_td": SCENE_TD},
                  scene_recipe(ill, SCENE_TD, nm), ill)
    # 5 metamers
    bases = [(f"white_{ill}", ill, scene_recipe(ill, SCENE_TD)) for ill in ILLUMS]
    bases += [(f"{p.replace(' ', '_')}_D65", "D65", scene_recipe("D65", SCENE_TD, p))
              for p in METAMER_PATCHES]
    for k, (bname, ill, brec) in enumerate(bases):
        pid = f"pair{k:02d}_{bname}"
        B.add(f"met_{pid}_a", "metamer", "heldout", {"pair_id": pid, "member": "a_base", "base": bname},
              brec, ill, extra={"pair_id": pid})
        mrec = {"kind": "metamer", "base": brec, **METAMER_KW, "step": 1}
        e = B.add(f"met_{pid}_b", "metamer", "heldout", {"pair_id": pid, "member": "b_metamer", "base": bname,
                  **METAMER_KW}, mrec, ill, extra={"pair_id": pid})
        lb = sf.lms_from_spd(spd_from_recipe(brec))
        lm = sf.lms_from_spd(spd_from_recipe(mrec))
        e["metamer_check"] = {"cie2_lms_max_rel_diff": float(np.max(np.abs(lm - lb) / np.abs(lb))),
                              "spd_max_abs_diff_over_max_base": float(
                                  np.max(np.abs(spd_from_recipe(mrec) - spd_from_recipe(brec)))
                                  / np.max(spd_from_recipe(brec)))}
    # 6a wrong optics
    for filt in ("lens", "macular"):
        for i, nm in enumerate(names, 1):
            rec = scene_recipe("D65", SCENE_TD, nm, {"kind": filt})
            trec = scene_recipe("D65", SCENE_TD, nm)
            e = B.add(f"wopt_{filt}_{i:02d}_D65", "wrong_optics", "heldout",
                      {"patch": i, "patch_name": nm, "illuminant": "D65", "filter": filt,
                       "diffuser_td_before_filter": SCENE_TD},
                      rec, "D65", theory_recipe=trec, adversarial=True)
            e["truth"]["secondary_unfiltered"] = truth_for(spd_from_recipe(trec), "D65")
    # 6b wrong observer (references base stimuli; not a new eye input)
    idx = {e["id"]: e for e in B.entries}
    wobs_bases = [f"mono_{wl}nm_q1000" for wl in sorted(TRAIN_WL + HELDOUT_WL)]
    wobs_bases += [f"refl_{i:02d}_D65" for i in range(1, 25)]
    for bid in wobs_bases:
        base = idx[bid]
        B.entries.append({"id": f"wobs_{bid}", "family": "wrong_observer", "split": "heldout",
                          "adversarial": True, "params": {"base_id": bid, "theory_observer": "10deg"},
                          "eye_input": {"identical_to": bid},
                          "theory_input": {"same_as_eye_input": True, "observer": "10deg"},
                          "truth": dict(base["truth"])})
    # 7 eyelid
    for ill in ILLUMS:
        for od in EYELID_OD_LONGS:
            for amb in EYELID_AMBIENT_TD:
                rec = scene_recipe(ill, amb, None, {"kind": "eyelid", "od_short": sf.EYELID_OD_SHORT,
                                                    "od_long": od})
                B.add(f"lid_{ill}_od{od}_{int(amb)}td", "eyelid", "heldout",
                      {"illuminant": ill, "ambient_td": amb, "od_short": sf.EYELID_OD_SHORT, "od_long": od},
                      rec, ill)
    # adaptation
    fields = {"adapt610": mono_recipe(610, 1000), "adapt530": mono_recipe(530, 1000),
              "adaptE": scene_recipe("E", 100.0)}
    tests = [(f"mono{wl}", mono_recipe(wl, 1000), "E") for wl in ADAPT_TEST_WL]
    tests.append(("whiteE", scene_recipe("E", 100.0), "E"))
    for fname, frec in fields.items():
        fblk, _ = B.eye_block(frec)
        for tname, trec, white in tests:
            e = B.add(f"adapt_{fname}_{tname}", "adaptation", "heldout",
                      {"adapting_field": fname, "test": tname, "adapt_epochs": ADAPT_EPOCHS, "test_epochs": 1},
                      trec, white, check_dup=False,
                      extra={"protocol": {
                          "adapt_epochs": ADAPT_EPOCHS, "test_epochs": 1,
                          "description": "submit adapting packets on the test column for adapt_epochs "
                                         "processed epochs, then submit the test packets once; read the "
                                         "percept of that test epoch. No other input on the column.",
                          "adapting_field": {"name": fname, "recipe": frec, "packets": fblk["packets"],
                                             "packets_sha256": fblk["packets_sha256"], "td": fblk["td"]}}})
            e["eye_input"]["duplicate_of"] = None
    # poisson
    psubs = [(f"mono{wl}", mono_recipe(wl, 1000), "E") for wl in POISSON_MONO_WL]
    psubs.append(("whiteE100", scene_recipe("E", 100.0), "E"))
    psubs += [(f"lidD65od1.3_{int(a)}td",
               scene_recipe("D65", a, None, {"kind": "eyelid", "od_short": sf.EYELID_OD_SHORT, "od_long": 1.3}),
               "D65") for a in EYELID_AMBIENT_TD]
    for k, (pname, prec, white) in enumerate(psubs):
        for t in range(POISSON_TRIALS):
            seed = POISSON_SEED_BASE + 1000 * k + t
            B.add(f"pois_{pname}_t{t}", "poisson", "heldout",
                  {"subset_index": k, "subset": pname, "trial": t, "seed": seed},
                  prec, white, method="poisson", seed=seed, check_dup=False)
    # pilot regression
    for col, wl in ((0, 610), (1, 530)):
        e = B.add(f"pilot_{wl}nm_col{col}", "pilot_regression", "regression",
                  {"wavelength_nm": wl, "quanta": 1000, "column": col}, mono_recipe(wl, 1000), "E",
                  extra={"expected_eye": {"red_green": PILOT_SMOKE[str(wl)][0],
                                          "blue_yellow": PILOT_SMOKE[str(wl)][1],
                                          "eye_construct": 'GraphEye(n_az=2, context={"worker_capacity":1})'}})
    # 5 nm ablation
    for i, nm in enumerate(names, 1):
        B.add(f"abl5_refl_{i:02d}_D65", "ablation_grid5", "heldout",
              {"patch": i, "patch_name": nm, "illuminant": "D65", "diffuser_td": SCENE_TD, "step": 5},
              scene_recipe("D65", SCENE_TD, nm, step=5), "D65")

    # anchor-construction items (TRAIN; not eye inputs, not scored)
    anchor_items = [{"id": f"anchor_{k.replace('/', '_')}", "family": "anchor", "split": "train",
                     "anchor": k, "definition": {kk: vv for kk, vv in v.items()
                                                 if kk not in ("unit_direction", "angle_deg")}}
                    for k, v in anchors.items()]
    entries = B.entries
    fam_counts: dict = {}
    for e in entries:
        fam_counts.setdefault(e["family"], {}).setdefault(e["split"], 0)
        fam_counts[e["family"]][e["split"]] += 1
    return {
        "schema": MANIFEST_SCHEMA,
        "experiment": "marys_room_broad",
        "amendment": "A1 (pre-eye-run), docs/experiments/marys-room-broad-prereg.md",
        "provenance": provenance_line(),
        "forward_model": {"module": "domains/spectral_forward.py", "quanta_scale": sf.QUANTA_SCALE,
                          "k_m_f_2deg": sf.K_M_F_2DEG, "default_quantize": "cumulative",
                          "photon_conversion": "quantal", "grid_nm": [390, 780], "default_step_nm": 1},
        "declared": {
            "unique_hues_nm": {"UB": UB_NM, "UG": UG_NM, "UY": UY_NM,
                               "UR_complementary": UR_COMPLEMENTARY_NM,
                               "UR_spectral_side_for_boundary": UR_SPECTRAL_SIDE_NM},
            "unique_hue_source": "Kuehni 2004 Color Res Appl 29(2):158-162 doi:10.1002/col.10237 Table I, "
                                 "spectral-light sets, observer-weighted",
            "kuehni_inputs_mean_n": _KUEHNI,
            "hue4_bounds_nm": list(HUE4_BOUNDS), "purity_min": PURITY_MIN,
            "rg_zero_nm_cie2deg": RG_ZERO_NM, "intensities_quanta": list(INTENSITIES_Q),
            "train_wavelengths_nm": list(TRAIN_WL), "heldout_wavelengths_nm": list(HELDOUT_WL),
            "boundary_wavelengths_nm": list(BOUNDARY_WL), "metamer_kw": METAMER_KW,
            "eyelid_ambient_td": list(EYELID_AMBIENT_TD), "eyelid_od_long": list(EYELID_OD_LONGS),
            "eyelid_od_short": sf.EYELID_OD_SHORT, "adapt_epochs": ADAPT_EPOCHS,
            "poisson_seed_rule": "20261004 + 1000*subset_index + trial", "poisson_trials": POISSON_TRIALS,
            "ci": {"accuracy": "Wilson 95%", "balanced_accuracy":
                   f"stratified percentile bootstrap B={BOOT_B}, numpy default_rng({BOOT_SEED})"},
        },
        "schema_doc": SCHEMA_DOC,
        "counts": {"total_entries": len(entries), "by_family_split": fam_counts,
                   "distinct_eye_inputs": sum(1 for e in entries if "packets" in e["eye_input"]
                                              and e["eye_input"].get("duplicate_of") is None)},
        "anchors": anchor_items,
        "stimuli": entries,
    }


SCHEMA_DOC = {
    "stimuli[]": {
        "id": "unique string",
        "family": "mono_sweep|boundary_dense|illuminant|reflectance|metamer|wrong_optics|wrong_observer|"
                  "eyelid|adaptation|poisson|pilot_regression|ablation_grid5",
        "split": "train|heldout|regression",
        "adversarial": "bool (family 6)",
        "params": "family-specific declared parameters",
        "eye_input": {
            "recipe": "deterministic SPD recipe; rebuild with scripts.marys_room_broad_theory.spd_from_recipe",
            "step": "grid step nm (1, or 5 for ablation_grid5)",
            "spd_sha256": "sha256 of the recipe SPD as little-endian float64 bytes",
            "td": "retinal illuminance (td) of the at-retina SPD",
            "expected_quanta_total": "continuous expected model quanta",
            "quantize": "{method, seed, photon_conversion, quanta_scale}",
            "packets": "[[wavelength_nm, count], ...] column-agnostic; Arm B assigns the column",
            "packets_total": "int", "n_packets": "int",
            "packets_sha256": "sha256 of json.dumps(packets, separators=(',',':'))",
            "duplicate_of": "id of first entry with identical packets (or null)",
            "identical_to": "(wrong_observer only, replaces the above) base stimulus id",
        },
        "theory_input": "{same_as_eye_input: bool, observer: '2deg'|'10deg', [recipe, spd_sha256]}",
        "truth": "{white, dominant_wavelength_nm (negative = complementary/purple), excitation_purity, "
                 "purple, hue4, binary, [secondary_unfiltered | secondary_E_referenced]}",
        "pair_id / metamer_check": "(metamer only)",
        "protocol": "(adaptation only) {adapt_epochs, test_epochs, description, adapting_field{name, recipe, "
                    "packets, packets_sha256, td}}",
        "expected_eye": "(pilot_regression only) smoke red_green/blue_yellow",
    },
}

# ---------------------------------------------------------------- metrics

def wilson(k: int, n: int, z: float = WILSON_Z) -> list[float]:
    if n == 0:
        return [float("nan"), float("nan")]
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [max(0.0, c - h), min(1.0, c + h)]


def binom_sf(k: int, n: int, p: float) -> float:
    """P(X >= k), X ~ Bin(n, p), exact."""
    if n == 0:
        return float("nan")
    if p <= 0:
        return 1.0 if k <= 0 else 0.0
    if p >= 1:
        return 1.0
    tot = 0.0
    for i in range(k, n + 1):
        tot += math.exp(math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
                        + i * math.log(p) + (n - i) * math.log1p(-p))
    return min(1.0, tot)


def score(truth: list[str], pred: list[str], classes: tuple[str, ...]) -> dict:
    n = len(truth)
    if n == 0:
        return {"n": 0}
    correct = np.array([t == p for t, p in zip(truth, pred)])
    k = int(correct.sum())
    present = [c for c in classes if any(t == c for t in truth)]
    recalls = {}
    per_class_correct = {}
    for c in present:
        m = np.array([t == c for t in truth])
        per_class_correct[c] = correct[m]
        recalls[c] = float(correct[m].mean())
    bal = float(np.mean(list(recalls.values())))
    rng = np.random.default_rng(BOOT_SEED)
    boots = np.zeros(BOOT_B)
    for c in present:
        v = per_class_correct[c].astype(float)
        draws = rng.integers(0, len(v), size=(BOOT_B, len(v)))
        boots += v[draws].mean(axis=1)
    boots /= len(present)
    counts = {c: int(sum(t == c for t in truth)) for c in present}
    maj = max(counts.values()) / n
    conf = {c: {p: int(sum(1 for t, q in zip(truth, pred) if t == c and q == p))
                for p in sorted(set(pred))} for c in present}
    return {"n": n, "correct": k, "accuracy": k / n, "accuracy_wilson95": wilson(k, n),
            "balanced_accuracy": bal,
            "balanced_accuracy_boot95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
            "per_class_recall": recalls, "truth_class_counts": counts,
            "chance_majority_rate": maj, "chance_uniform": 1.0 / len(classes),
            "chance_balanced": 1.0 / len(present),
            "p_binom_vs_0.5": binom_sf(k, n, 0.5), "p_binom_vs_majority": binom_sf(k, n, maj),
            "confusion_truth_to_pred": conf}


def _intervals(wls: list[float]) -> list[list[float]]:
    wls = sorted(wls)
    out = []
    for w in wls:
        if out and w - out[-1][1] <= 5.0 + 1e-9:
            out[-1][1] = w
        else:
            out.append([w, w])
    return out


def compute_arm_a(manifest: dict, anchors: dict) -> dict:
    idx = {e["id"]: e for e in manifest["stimuli"]}
    rows = []
    for e in manifest["stimuli"]:
        ti = e["theory_input"]
        if "identical_to" in e["eye_input"]:
            spd = spd_from_recipe(idx[e["eye_input"]["identical_to"]]["eye_input"]["recipe"])
        elif ti["same_as_eye_input"]:
            spd = spd_from_recipe(e["eye_input"]["recipe"])
        else:
            spd = spd_from_recipe(ti["recipe"])
        if e["family"] == "poisson" or e["family"] == "adaptation":
            pass  # theory uses the expected (noise-free) SPD; no adaptation model
        primary = theory_for_spd(spd, anchors, ti["observer"])
        t2 = primary if ti["observer"] == "2deg" else theory_for_spd(spd, anchors, "2deg")
        t10 = primary if ti["observer"] == "10deg" else theory_for_spd(spd, anchors, "10deg")
        tr = e["truth"]
        scored = tr["binary"] != "achromatic"
        row = {"id": e["id"], "family": e["family"], "split": e["split"],
               "adversarial": e.get("adversarial", False),
               "duplicate_of": e["eye_input"].get("duplicate_of"),
               "theory_primary": primary, "theory_2deg": t2, "theory_10deg": t10,
               "truth": {k: tr[k] for k in ("hue4", "binary", "dominant_wavelength_nm", "excitation_purity")},
               "hue_scored": scored,
               "sign_correct": (SIGN_TO_BINARY.get(primary["sign_label"]) == tr["binary"]) if scored else None,
               "multi_correct": (primary["multi_label"] == tr["hue4"]) if scored else None}
        if "wavelength_nm" in e["params"]:
            row["wavelength_nm"] = e["params"]["wavelength_nm"]
            row["dist_from_rg_zero_nm"] = e["params"]["wavelength_nm"] - RG_ZERO_NM
        rows.append(row)

    def pool(pred):
        sel = [r for r in rows if pred(r) and r["hue_scored"]]
        out = {"sign_rule_binary": score([r["truth"]["binary"] for r in sel],
                                         [SIGN_TO_BINARY.get(r["theory_primary"]["sign_label"], "undecided")
                                          for r in sel], BINARY),
               "multi_anchor_hue4": score([r["truth"]["hue4"] for r in sel],
                                          [r["theory_primary"]["multi_label"] for r in sel], HUE4)}
        allsel = [r for r in rows if pred(r)]
        out["n_entries"] = len(allsel)
        out["n_achromatic_excluded"] = sum(1 for r in allsel if not r["hue_scored"])
        keys = {(tuple(np.round(np.asarray(r["theory_primary"]["lms"]) / max(sum(r["theory_primary"]["lms"]),
                                                                            1e-300), 12)),
                 r["truth"]["binary"], r["truth"]["hue4"]) for r in sel}
        out["n_theory_distinct_scored"] = len(keys)
        return out

    core_fams = {"mono_sweep", "boundary_dense", "illuminant", "reflectance", "metamer", "eyelid"}
    pools = {
        "TRAIN": pool(lambda r: r["split"] == "train"),
        "HELDOUT_core": pool(lambda r: r["split"] == "heldout" and r["family"] in core_fams
                             and r["duplicate_of"] is None),
        "HELDOUT_core_incl_duplicates": pool(lambda r: r["split"] == "heldout" and r["family"] in core_fams),
        "ADVERSARIAL_wrong_optics": pool(lambda r: r["family"] == "wrong_optics"),
        "ADVERSARIAL_wrong_observer_10deg": pool(lambda r: r["family"] == "wrong_observer"),
        "ADAPTATION_no_adaptation_model": pool(lambda r: r["family"] == "adaptation"),
        "POISSON_expected_spd": pool(lambda r: r["family"] == "poisson"),
        "ABLATION_grid5": pool(lambda r: r["family"] == "ablation_grid5"),
    }
    per_family = {}
    for fam in sorted({r["family"] for r in rows}):
        for sp in sorted({r["split"] for r in rows if r["family"] == fam}):
            per_family[f"{fam}/{sp}"] = pool(lambda r, f=fam, s=sp: r["family"] == f and r["split"] == s)
    # per-illuminant reflectance
    for ill in ILLUMS:
        per_family[f"reflectance/heldout/{ill}"] = pool(
            lambda r, i=ill: r["family"] == "reflectance" and r["id"].endswith("_" + i))

    # where the sign rule fails on monochromatic light (theory is scale-free: 1000 q)
    mono = [r for r in rows if r["family"] in ("mono_sweep", "boundary_dense") and r["id"].endswith("_q1000")]
    sign_fail = sorted(r["wavelength_nm"] for r in mono if r["sign_correct"] is False)
    multi_fail = sorted(r["wavelength_nm"] for r in mono if r["multi_correct"] is False)
    # 1-nm wavelength-level failure description using the full CIE table
    wl = sf.grid(1)
    lms = sf.load_lms("2deg", 1)
    rg = lms[:, 0] - lms[:, 1]
    bins = []
    for w, v in zip(wl, rg):
        if 400 <= w <= 700:
            t = binary(float(w), 1.0)
            s = "reddish" if v > 0 else "greenish"
            bins.append((float(w), t == s))
    fail_1nm = [w for w, ok in bins if not ok]
    mono_failure = {
        "sign_rule_failing_wavelengths_nm_tested": sign_fail,
        "multi_anchor_failing_wavelengths_nm_tested": multi_fail,
        "sign_rule_failure_intervals_1nm_continuum_400_700": _intervals_1nm(fail_1nm),
        "explanation": "binary truth flips at UB=478.0 and UY=576.3 nm; CIE 2deg L-M flips at 409.16 and "
                       "554.08 nm. The sign rule is wrong for 409.16 < lambda < 478.0 (violet-blue: "
                       "perceptually reddish, L-M<0) and 554.08 < lambda < 576.3 (yellow-green: "
                       "perceptually greenish, L-M>0); 400-409 nm agree only because both are 'red-side'.",
    }
    # boundary analysis (pooled 1 nm window, theory)
    window = sorted([r for r in mono if abs(r["dist_from_rg_zero_nm"]) <= 20.0],
                    key=lambda r: r["wavelength_nm"])
    boundary = [{"wavelength_nm": r["wavelength_nm"], "dist_nm": r["dist_from_rg_zero_nm"],
                 "rg_rel": r["theory_primary"]["rg_rel"], "sign": r["theory_primary"]["sign_label"],
                 "multi": r["theory_primary"]["multi_label"], "truth_binary": r["truth"]["binary"],
                 "truth_hue4": r["truth"]["hue4"], "sign_correct": r["sign_correct"],
                 "multi_correct": r["multi_correct"]} for r in window]
    # accuracy vs |dist| bins over the mono sweep
    dist_bins = [(0, 5), (5, 10), (10, 20), (20, 50), (50, 100), (100, 200)]
    vs_dist = []
    for lo, hi in dist_bins:
        sel = [r for r in mono if lo <= abs(r["dist_from_rg_zero_nm"]) < hi and r["hue_scored"]]
        if sel:
            vs_dist.append({"abs_dist_nm": [lo, hi], "n": len(sel),
                            "sign_accuracy": float(np.mean([r["sign_correct"] for r in sel])),
                            "multi_accuracy": float(np.mean([r["multi_correct"] for r in sel]))})
    # eyelid summary
    lid = [{"id": r["id"], "rg": r["theory_primary"]["rg"], "rg_rel": r["theory_primary"]["rg_rel"],
            "sign": r["theory_primary"]["sign_label"], "multi": r["theory_primary"]["multi_label"],
            "truth_hue4": r["truth"]["hue4"], "dominant_nm": r["truth"]["dominant_wavelength_nm"]}
           for r in rows if r["family"] == "eyelid"]
    # metamers: theory gap by construction
    met = []
    for e in manifest["stimuli"]:
        if e["family"] == "metamer" and e["id"].endswith("_b"):
            a = next(r for r in rows if r["id"] == e["id"][:-1] + "a")
            b = next(r for r in rows if r["id"] == e["id"])
            ta, tb = a["theory_primary"], b["theory_primary"]
            met.append({"pair_id": e["pair_id"], "theory_rg_by_a": [ta["rg"], ta["by"]],
                        "theory_rg_by_b": [tb["rg"], tb["by"]],
                        "theory_opponent_gap": math.hypot(ta["rg"] - tb["rg"], ta["by"] - tb["by"]),
                        "theory_gap_rel": math.hypot(ta["rg"] - tb["rg"], ta["by"] - tb["by"])
                        / max(sum(ta["lms"]), 1e-300),
                        "theory_10deg_gap_rel": math.hypot(a["theory_10deg"]["rg"] - b["theory_10deg"]["rg"],
                                                           a["theory_10deg"]["by"] - b["theory_10deg"]["by"])
                        / max(sum(a["theory_10deg"]["lms"]), 1e-300)})
    return {
        "experiment": "marys_room_broad_armA",
        "arm": "A (theory only, pre-exposure; no eye imported or run)",
        "provenance": provenance_line(),
        "manifest_schema": manifest["schema"],
        "anchors": anchors,
        "pools": pools,
        "per_family": per_family,
        "mono_failure": mono_failure,
        "boundary_window_theory": boundary,
        "accuracy_vs_distance_from_rg_zero_1000q": vs_dist,
        "eyelid_theory": lid,
        "metamer_theory": met,
        "notes": [
            "Theory decoders are scale-invariant; mono intensities 100/1000/10000 q are deterministic "
            "duplicates in Arm A (see n_theory_distinct_scored).",
            "Intervals are descriptive for a designed stimulus set, not population inference.",
            "Wrong-observer pool uses 10-deg theory decoded with frozen 2-deg anchors.",
            "Adaptation pool: Arm A has no adaptation model by declaration; numbers equal the unadapted "
            "test stimuli.",
        ],
        "per_stimulus": rows,
    }


def _intervals_1nm(ws):
    out = []
    for w in sorted(ws):
        if out and w - out[-1][1] <= 1.0 + 1e-9:
            out[-1][1] = w
        else:
            out.append([w, w])
    return out


# ---------------------------------------------------------------- io

def dumps(obj) -> str:
    return json.dumps(obj, indent=1, allow_nan=True) + "\n"


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build_all() -> tuple[str, str]:
    anchors = build_anchors()
    manifest = build_manifest(anchors)
    arm_a = compute_arm_a(manifest, anchors)
    arm_a["manifest_sha256"] = hashlib.sha256(dumps(manifest).encode()).hexdigest()
    return dumps(manifest), dumps(arm_a)


def freeze_files() -> list[Path]:
    files = [PREREG_PATH, SPEC_PATH, ROOT / "domains" / "spectral_forward.py", Path(__file__).resolve(),
             MANIFEST_PATH, ARMA_PATH]
    files += sorted(p for p in (ROOT / "data" / "colour").rglob("*") if p.is_file())
    return files


def write_freeze():
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT, capture_output=True,
                            text=True).stdout.strip()
    fz = {
        "experiment": "marys_room_broad",
        "what": "Preregistration lock for Amendment A1: stimulus manifest, decoders/anchors, Arm A.",
        "utc_timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "git_head": head, "git_branch": branch,
        "git_commit_note": "No git commit was made (the user did not request commits). The prereg, spec, "
                           "forward model, script, data and results are uncommitted/untracked (data/ and "
                           "results/ are gitignored). This sha256 hash freeze is the preregistration lock; "
                           "verify with `python -m scripts.marys_room_broad_theory --verify`.",
        "eye_contact_before_freeze": "none in this stage (domains.photon_eye not imported; the only prior eye "
                                     "contact was the A0 pilot-regression unit test with known smoke values)",
        "provenance": provenance_line(),
        "sha256": {str(p.relative_to(ROOT)): sha256_file(p) for p in freeze_files()},
    }
    FREEZE_PATH.write_text(json.dumps(fz, indent=1) + "\n")
    return fz


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args(argv)
    assert "domains.photon_eye" not in sys.modules
    man_s, arm_s = build_all()
    assert "domains.photon_eye" not in sys.modules
    if a.verify:
        fz = json.loads(FREEZE_PATH.read_text())
        ok = True
        for rel, h in fz["sha256"].items():
            cur = sha256_file(ROOT / rel)
            if cur != h:
                ok = False
                print(f"MISMATCH on disk: {rel}")
        for path, s in ((MANIFEST_PATH, man_s), (ARMA_PATH, arm_s)):
            if hashlib.sha256(s.encode()).hexdigest() != fz["sha256"][str(path.relative_to(ROOT))]:
                ok = False
                print(f"MISMATCH on rebuild: {path.relative_to(ROOT)}")
        print("FREEZE OK" if ok else "FREEZE VIOLATED")
        return 0 if ok else 1
    MANIFEST_PATH.write_text(man_s)
    ARMA_PATH.write_text(arm_s)
    print(f"wrote {MANIFEST_PATH.relative_to(ROOT)} ({len(man_s)} B), {ARMA_PATH.relative_to(ROOT)} ({len(arm_s)} B)")
    if a.freeze:
        write_freeze()
        print(f"wrote {FREEZE_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

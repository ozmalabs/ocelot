#!/usr/bin/env python3
"""GenInfer prefilter v1.4 prevalence census and Term-level parity probe.

See docs/research/engine_substrate/SUBSTRATE_GENINFER_PREFILTER_PREVALENCE_V1_4_PREREG_20261006.md.

Each pair is evaluated with the native ``GenInfer`` Term on a fresh bare
substrate holding exactly one ShapeSignature part (the base). The same native
binary runs both arms; ``linear_prefilter_enabled`` selects the v1.4 dispatch
or the historical enumerator. Results are compared field-by-field except the
``checked`` work count.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import itertools
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENINFER_PREFILTER_PREVALENCE_V1_4_PREREG_20261006.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENINFER_PREFILTER_PREVALENCE_V1_4B_AMENDMENT_20261006.md"
OUT = ROOT / "evaluation/reports/geninfer_prefilter_prevalence_v1_4b_20261006.json"
OMNIGLOT = ROOT / "data/omniglot/strokes_background"
LATTICE = 8
RESAMPLE = 8
OFF_MATRIX_CAP = 3_000_000
SOURCES = ["runners/dsl/src/shape_decode.rs", "runners/dsl/src/scale_audit.rs", "runners/dsl/Cargo.toml",
           "domains/sdloop_vision.py", "evaluation/substrate_capability/geninfer_exact_linear_prefilter_v1.py"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------- static census
def static_schema_census() -> list[dict]:
    """Every literal ``dim_types`` list assigned/passed in production adapter code."""
    rows = []
    for top in ("domains", "worlds", "substrate"):
        for path in sorted((ROOT / top).rglob("*.py")):
            try:
                tree = ast.parse(path.read_text(), filename=str(path))
            except (SyntaxError, UnicodeDecodeError):
                continue
            for node in ast.walk(tree):
                value = None
                if isinstance(node, ast.Assign) and isinstance(node.value, ast.List):
                    names = [t.id for t in node.targets if isinstance(t, ast.Name)]
                    if any("DIM_TYPES" in n.upper() or n in ("DT", "DTYPES") for n in names):
                        value = node.value
                elif isinstance(node, ast.Dict):
                    for k, v in zip(node.keys, node.values):
                        if isinstance(k, ast.Constant) and k.value == "dim_types" and isinstance(v, ast.List):
                            value = v
                if value is None:
                    continue
                try:
                    schema = [ast.literal_eval(e) for e in value.elts]
                except ValueError:
                    continue
                if not all(isinstance(s, str) for s in schema):
                    continue
                coords = [i for i, t in enumerate(schema) if t.startswith("coord:")]
                ids = [i for i, t in enumerate(schema) if t == "id"]
                first = min(coords) if coords else None
                prefix_is_id = bool(coords) and first > 1 and all(schema[i] == "id" for i in range(1, first)) \
                    and all(i < first for i in ids)
                rows.append({"file": str(path.relative_to(ROOT)), "line": node.lineno, "dim_types": schema,
                             "n_coord": len(coords), "has_id": bool(ids),
                             "geninfer_2d_eligible": len(coords) == 2,
                             "fast_path_reachable": len(coords) == 2 and prefix_is_id})
    return rows


# ---------------------------------------------------------------- inputs
def read_drawing(path: Path) -> list[list[tuple[float, float]]]:
    strokes, cur = [], []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line == "START":
            cur = []
        elif line == "BREAK":
            if cur:
                strokes.append(cur)
            cur = []
        elif line:
            x, y, _t = line.split(",")
            cur.append((float(x), -float(y)))
    if cur:
        strokes.append(cur)
    return strokes


def lattice(pt, box):
    (x0, y0, x1, y1) = box
    span = max(x1 - x0, y1 - y0, 1e-9)
    r = min(LATTICE - 1, int((pt[1] - y0) / span * LATTICE))
    c = min(LATTICE - 1, int((pt[0] - x0) / span * LATTICE))
    return r, c


def resample(strokes, k):
    pts = [(p, si) for si, s in enumerate(strokes) for p in s]
    seg = [0.0]
    for (a, _), (b, _) in zip(pts, pts[1:]):
        seg.append(seg[-1] + math.dist(a, b))
    total = seg[-1] or 1.0
    out, j = [], 0
    for i in range(k):
        target = total * i / (k - 1)
        while j < len(seg) - 1 and seg[j + 1] < target:
            j += 1
        out.append(pts[j])
    return out


def omniglot_signatures(path: Path) -> dict[str, list[list]]:
    strokes = read_drawing(path)
    allp = [p for s in strokes for p in s]
    box = (min(p[0] for p in allp), min(p[1] for p in allp), max(p[0] for p in allp), max(p[1] for p in allp))
    cells = sorted({lattice(p, box) for p in allp})
    res = resample(strokes, RESAMPLE)
    return {
        "prod": [["cell", r, c] for r, c in cells],
        "id1": [["pt", k, *lattice(p, box)] for k, (p, _si) in enumerate(res)],
        "id2": [["first" if si == 0 else "rest", k, *lattice(p, box)] for k, (p, si) in enumerate(res)],
    }


SCHEMAS = {"prod": ["pred", "coord:r", "coord:c"], "id1": ["pred", "id", "coord:r", "coord:c"],
           "id2": ["pred", "id", "coord:r", "coord:c"]}


def omniglot_pairs() -> list[dict]:
    alphabets = sorted(p for p in OMNIGLOT.iterdir() if p.is_dir())[:10]
    chars = []
    for a in alphabets:
        for c in sorted(p for p in a.iterdir() if p.is_dir())[:2]:
            drawings = sorted(c.glob("*.txt"))[:5]
            chars.append((f"{a.name}/{c.name}", drawings))
    pairs = []
    for label, drawings in chars:
        for d1, d2 in itertools.combinations(drawings, 2):
            pairs.append({"kind": "same_character", "base": d1, "goal": d2, "label": label})
    cross = []
    for (l1, dr1), (l2, dr2) in zip(chars, chars[1:] + chars[:1]):
        for i in range(len(dr1)):
            cross.append({"kind": "cross_character", "base": dr1[i], "goal": dr2[(i + 1) % len(dr2)], "label": f"{l1}|{l2}"})
    pairs += cross[: sum(1 for p in pairs if p["kind"] == "same_character")]
    return pairs


def sdloop_pairs(size: int = 16, angles=(0, 45, 90, 135)) -> list[dict]:
    import numpy as np
    from domains.sdloop_vision import bar_frame, support
    sigs = {}
    for th in angles:
        on = bar_frame(th, size, size)
        pad = np.pad(on, 1)
        dil = np.zeros_like(on)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                dil = np.maximum(dil, pad[1 + dr:1 + dr + on.shape[0], 1 + dc:1 + dc + on.shape[1]])
        off = (dil > 0) & (on == 0)
        sigs[th] = support(on, off.astype(np.float32))
    return [{"kind": "sdloop_bar", "base": a, "goal": b, "base_sig": sigs[a], "goal_sig": sigs[b]}
            for a, b in itertools.combinations(sorted(sigs), 2)]


def panel_fallback_fixtures() -> list[dict]:
    from evaluation.substrate_capability import geninfer_exact_linear_prefilter_v1 as panel
    out = []
    for cell in panel.cells():
        if cell["condition"] not in ("rank_deficient", "duplicate_identity", "missing_identity", "linear_positive"):
            continue
        coords = panel.coordinates_for(cell)
        base = [["cell", f"train_{i}", x, y, "red"] for i, (x, y) in enumerate(coords)]
        goal = panel.relation_rows(coords, "train", cell["family"], cell["identity_case"])
        if cell["identity_case"] == "duplicate_last_as_first":
            base[-1][1] = base[0][1]
        if cell["identity_case"] == "replace_last_target_id":
            goal[-1][1] = "train_orphan"
        out.append({"kind": f"panel_{cell['condition']}", "base_sig": base, "goal_sig": goal, "dim_types": panel.DTYPES})
    return out


# ---------------------------------------------------------------- native evaluation
def extent(sig, slots):
    best = 0
    for s in slots:
        vals = [r[s] for r in sig]
        if all(isinstance(v, int) for v in vals):
            best = max(best, max(vals) - min(vals))
    return best


def evaluate_pair(srs, native_mod, base, goal, dim_types, prefilter: bool, audit: bool):
    s = srs.Substrate()
    s.add_node("ShapeSignature", {"name": "base", "signature": json.dumps(base), "kind": "faculty",
                                  "faculty": "base", "dim_types": list(dim_types)})
    term = {"type": "GenInfer", "goal": {"type": "Lit", "value": goal}, "max_dims": 2,
            "quadratic_enabled": {"type": "Lit", "value": False},
            "linear_prefilter_enabled": {"type": "Lit", "value": prefilter}}
    native_mod.Substrate.scale_audit_reset()
    native_mod.Substrate.scale_audit_set_enabled(audit)
    t0 = time.perf_counter_ns()
    result = s._inner.evaluate(term, {})
    ns = time.perf_counter_ns() - t0
    counters = {k: v for k, v in dict(native_mod.Substrate.scale_audit_snapshot()).items()
                if ("prefilter" in k or "row_factorized" in k or "correspondence" in k) and v} if audit else {}
    native_mod.Substrate.scale_audit_set_enabled(False)
    return result, ns, counters


def normalise(result):
    out = dict(result)
    out.pop("checked", None)
    return json.loads(json.dumps(out, sort_keys=True, default=str))


def path_class(counters: dict) -> str:
    if counters.get("gen_infer_prefilter_attempts", 0) == 0:
        return "not_attempted"
    if counters.get("gen_infer_prefilter_solved"):
        return "affine_solved"
    for k in counters:
        if k.startswith("gen_infer_prefilter_proven_no_fit_reason:"):
            return "affine_no_fit:" + k.split(":", 1)[1]
    if counters.get("gen_infer_row_factorized_solved"):
        return "row_factorized_solved"
    for k in counters:
        if k.startswith("gen_infer_row_factorized_no_candidate_reason:"):
            return "row_factorized_no_candidate:" + k.split(":", 1)[1]
    if counters.get("gen_infer_correspondence_found"):
        return "correspondence_found"
    for k in counters:
        if k.startswith("gen_infer_correspondence_no_candidate_reason:"):
            return "correspondence_no_candidate:" + k.split(":", 1)[1]
    for k in counters:
        if k.startswith("gen_infer_correspondence_fallback_reason:"):
            return "enumerator_fallback:" + k.split(":", 1)[1]
    for k in counters:
        if k.startswith("gen_infer_row_factorized_fallback_reason:"):
            return "enumerator_fallback:" + k.split(":", 1)[1]
    return "unclassified"


def run(native: Path, off_repeats: int, on_repeats: int) -> dict:
    temp = tempfile.TemporaryDirectory(prefix="geninfer-prevalence-v14-")
    pkg = Path(temp.name) / "substrate_rs"
    shutil.copytree(ROOT / "runners/dsl/python/substrate_rs", pkg, ignore=shutil.ignore_patterns("_native*.so", "__pycache__"))
    shutil.copy2(native, pkg / "_native.abi3.so")
    sys.path[:0] = [temp.name, str(ROOT), str(ROOT / "runners/dsl/python")]
    import substrate_rs as srs
    from substrate_rs import _native
    assert Path(srs.__file__).resolve().parent == pkg.resolve(), srs.__file__

    jobs = []
    for p in omniglot_pairs():
        bs, gs = omniglot_signatures(p["base"]), omniglot_signatures(p["goal"])
        for schema in ("prod", "id1", "id2"):
            jobs.append({"source": "omniglot", "kind": p["kind"], "schema": schema,
                         "pair": [str(p["base"].relative_to(OMNIGLOT)), str(p["goal"].relative_to(OMNIGLOT))],
                         "base": bs[schema], "goal": gs[schema], "dim_types": SCHEMAS[schema]})
    for p in sdloop_pairs():
        jobs.append({"source": "sdloop_vision", "kind": p["kind"], "schema": "sdloop_on_off",
                     "pair": [p["base"], p["goal"]], "base": p["base_sig"], "goal": p["goal_sig"],
                     "dim_types": ["pred", "coord:r", "coord:c"]})
    for size in (8, 12, 24, 32, 48):
        for p in sdloop_pairs(size, (0, 90)) + sdloop_pairs(size, (45, 135)):
            jobs.append({"source": "sdloop_vision_scale", "kind": f"size{size}_{p['base']}_{p['goal']}", "schema": f"sdloop_size{size}",
                         "pair": [p["base"], p["goal"]], "base": p["base_sig"], "goal": p["goal_sig"],
                         "dim_types": ["pred", "coord:r", "coord:c"]})
    for p in panel_fallback_fixtures():
        jobs.append({"source": "v1_panel_training_input", "kind": p["kind"], "schema": "panel",
                     "pair": [p["kind"], "train"], "base": p["base_sig"], "goal": p["goal_sig"], "dim_types": p["dim_types"]})

    records = []
    for i, job in enumerate(jobs):
        slots = [k for k, t in enumerate(job["dim_types"]) if t.startswith("coord:")]
        b = max(extent(job["base"], slots), extent(job["goal"], slots))
        enum_bound = (2 * b + 1) ** 4
        _, _, counters = evaluate_pair(srs, _native, job["base"], job["goal"], job["dim_types"], True, True)
        on_ns, on_result = [], None
        for _ in range(on_repeats):
            on_result, ns, _ = evaluate_pair(srs, _native, job["base"], job["goal"], job["dim_types"], True, False)
            on_ns.append(ns)
        rec = {k: job[k] for k in ("source", "kind", "schema", "pair")}
        rec.update({"n_base": len(job["base"]), "n_goal": len(job["goal"]), "bound": b,
                    "enumerator_matrix_bound": enum_bound, "path": path_class(counters), "counters": counters,
                    "on_ns": on_ns, "explained_on": bool(on_result.get("explained")),
                    "matrix_on": list(on_result.get("matrix") or ()),
                    "residual_dims_on": on_result.get("residual_dims")})
        if enum_bound <= OFF_MATRIX_CAP or job["source"] == "v1_panel_training_input":
            off_ns, off_result = [], None
            for _ in range(off_repeats):
                off_result, ns, _ = evaluate_pair(srs, _native, job["base"], job["goal"], job["dim_types"], False, False)
                off_ns.append(ns)
            rec.update({"off_ns": off_ns, "parity": normalise(on_result) == normalise(off_result),
                        "explained_off": bool(off_result.get("explained"))})
            if not rec["parity"]:
                rec["on_result"], rec["off_result"] = normalise(on_result), normalise(off_result)
        else:
            rec.update({"off_ns": None, "parity": None, "off_skipped": "enumerator_bound_exceeds_cap"})
        records.append(rec)
        print(f"[{i + 1}/{len(jobs)}] {rec['source']} {rec['schema']} {rec['kind']} path={rec['path']} "
              f"parity={rec['parity']} on={min(on_ns) / 1e6:.2f}ms off={(min(rec['off_ns']) / 1e6) if rec['off_ns'] else None}",
              flush=True)
    return {"records": records}


def summarise(records: list[dict]) -> dict:
    from collections import Counter, defaultdict
    by = defaultdict(Counter)
    timing = defaultdict(lambda: {"on_ms": [], "off_ms": []})
    for r in records:
        key = f"{r['source']}:{r['schema']}"
        by[key][r["path"]] += 1
        if r["off_ns"]:
            timing[key]["on_ms"].append(min(r["on_ns"]) / 1e6)
            timing[key]["off_ms"].append(min(r["off_ns"]) / 1e6)
    med = lambda xs: sorted(xs)[len(xs) // 2] if xs else None
    return {
        "path_counts": {k: dict(v) for k, v in sorted(by.items())},
        "median_ms": {k: {"on": med(v["on_ms"]), "off": med(v["off_ms"]), "n": len(v["on_ms"])} for k, v in sorted(timing.items())},
        "parity_checked": sum(1 for r in records if r["parity"] is not None),
        "parity_failures": sum(1 for r in records if r["parity"] is False),
        "validation_mismatches": sum(r["counters"].get("gen_infer_row_factorized_fallback_reason:validation_mismatch", 0) for r in records),
        "explained_on": sum(1 for r in records if r["explained_on"]),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--native", type=Path, required=True)
    ap.add_argument("--on-repeats", type=int, default=3)
    ap.add_argument("--off-repeats", type=int, default=1)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit(f"refusing to overwrite {args.out}")
    sources = {s: sha(ROOT / s) for s in SOURCES}
    started = time.time()
    static = static_schema_census()
    body = run(args.native.resolve(), args.off_repeats, args.on_repeats)
    report = {
        "schema": "GenInferPrefilterPrevalenceV1_4",
        "protocol": str(PREREG.relative_to(ROOT)), "protocol_sha256": sha(PREREG),
        "amendment": str(AMENDMENT.relative_to(ROOT)), "amendment_sha256": sha(AMENDMENT),
        "runner_sha256": sha(Path(__file__).resolve()),
        "native": {"path": str(args.native.resolve()), "sha256": sha(args.native.resolve())},
        "sources_sha256": sources, "sources_stable": sources == {s: sha(ROOT / s) for s in SOURCES},
        "host": {"python": sys.version.split()[0], "platform": platform.platform()},
        "started_unix": started, "elapsed_seconds": time.time() - started,
        "static_schema_census": static,
        "static_summary": {"declarations": len(static),
                           "geninfer_2d_eligible": sum(r["geninfer_2d_eligible"] for r in static),
                           "with_id_slot": sum(r["has_id"] for r in static),
                           "fast_path_reachable": sum(r["fast_path_reachable"] for r in static)},
        **body,
    }
    report["summary"] = summarise(report["records"])
    args.out.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"out": str(args.out.relative_to(ROOT)), **report["static_summary"], **{k: v for k, v in report["summary"].items() if k != "path_counts"}}, indent=1))
    print(json.dumps(report["summary"]["path_counts"], indent=1))
    return 0 if report["summary"]["parity_failures"] == 0 and report["summary"]["validation_mismatches"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

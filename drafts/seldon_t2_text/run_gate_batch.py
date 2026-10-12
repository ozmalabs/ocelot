"""
run_gate_batch — PHASE 1 GATE.

Runs the adapter across the exemplar + a set of practice units and scores each
with the REAL reference scorer (gates only, since realized outcomes are sealed).
Reports admissible/g0-g3 per unit for both draw engines.

Usage:
  PYTHONPATH=<track2 repo> python run_gate_batch.py <units_dir> [--engine joint] [--limit N]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from t2_adapter import run_forecast, read_card  # noqa: E402


def score_gates(track2_repo: str, card_path: Path, forecast_path: Path) -> dict:
    """Invoke the real scorer CLI (gates only)."""
    env = {"PYTHONPATH": track2_repo}
    import os
    full_env = dict(os.environ)
    full_env.update(env)
    cmd = [sys.executable, "-m", "qfbench2_track_forecasting.scoring", "score",
           "--card", str(card_path), "--forecast", str(forecast_path)]
    p = subprocess.run(cmd, capture_output=True, text=True, env=full_env)
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return {"admissible": False, "error": (p.stdout + p.stderr)[:400]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("units_dir")
    ap.add_argument("--track2-repo", required=True)
    ap.add_argument("--engine", default="joint", choices=["joint", "independent"])
    ap.add_argument("--out-root", default="/tmp/t2_gate_batch")
    ap.add_argument("--limit", type=int, default=0, help="0 = all selected")
    ap.add_argument("--select", default="", help="comma substr filter, e.g. EXAMPLE,F1,F3")
    args = ap.parse_args()

    units_dir = Path(args.units_dir)
    out_root = Path(args.out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    unit_dirs = sorted([d for d in units_dir.iterdir()
                        if d.is_dir() and (d / "card.toml").exists()])
    if args.select:
        subs = [s.strip() for s in args.select.split(",") if s.strip()]
        unit_dirs = [d for d in unit_dirs if any(s in d.name for s in subs)]

    results = []
    n_pass = n_fail = n_skip = 0
    for ud in unit_dirs:
        if args.limit and (n_pass + n_fail) >= args.limit:
            break
        name = ud.name
        out_dir = out_root / name
        try:
            card = read_card(ud / "card.toml")
        except Exception as e:
            results.append((name, "SKIP-card", str(e)[:80]))
            n_skip += 1
            continue
        try:
            run_forecast(ud, out_dir, n_draws=500, engine=args.engine)
        except Exception as e:
            # transfer units (asset absent from panel) land here — Phase 3 concern
            results.append((name, "SKIP-build", str(e)[:80]))
            n_skip += 1
            continue
        verdict = score_gates(args.track2_repo, ud / "card.toml",
                              out_dir / "forecast.parquet")
        adm = bool(verdict.get("admissible"))
        gates = verdict.get("gates", {})
        gstr = "".join("1" if gates.get(g) == "pass" else "0"
                       for g in ("g0_integrity", "g1_schema",
                                 "g2_cutoff_resource", "g3_domain_semantics"))
        if adm:
            n_pass += 1
            results.append((name, "PASS", f"g0-3={gstr} cells={card.cell_count}"))
        else:
            n_fail += 1
            det = verdict.get("detail") or verdict.get("error") or ""
            results.append((name, "FAIL", f"g0-3={gstr} {json.dumps(det)[:120]}"))

    print(f"\n=== PHASE 1 GATE ({args.engine} engine) ===")
    for name, status, info in results:
        print(f"  [{status:10s}] {name:38s} {info}")
    print(f"\nPASS={n_pass}  FAIL={n_fail}  SKIP={n_skip}  "
          f"(admissible on {n_pass}/{n_pass+n_fail} attempted)")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

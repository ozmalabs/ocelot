"""gate_macro — g0-g3 admissibility of the tom arm (now composing the macro-
surprise mechanism) on macro-carrying units (MACRO_SURPRISE_PREREG deliverable:
"confirm g0-g3 admissible on the exemplar + one macro-carrying F2/F4 unit via
the real scorer"). Mirrors gate_g0g3.py exactly, but points at a macro F2 unit
(t2-F2-some-pain-2022, rates_daily + a cpi macro_release doc) and a macro F4
unit (t2-F4-covid-nfp-2020, macro_monthly + empsit macro_release docs).

Run:
  PYTHONPATH=runners/dsl/python:.bigtmp/track2 OZMA_SEED_PERSIST_DISABLED=1 \
    .bigtmp/t2venv/bin/python drafts/seldon_t2_text/induced_belief/gate_macro.py
"""
from __future__ import annotations

import json
import sys
import tempfile
import tomllib
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_T2 = _HERE.parent
_ROOT = _T2.parent.parent
for p in (str(_ROOT), str(_ROOT / "runners" / "dsl" / "python"), str(_T2)):
    if p not in sys.path:
        sys.path.insert(0, p)

UNITS = _ROOT / ".bigtmp" / "track2" / "units"

MACRO_UNITS = [
    # (unit_dir, asof) — asof from each card's data_cutoff
    ("t2-F2-some-pain-2022", "2022-08-26"),
    ("t2-F4-covid-nfp-2020", "2020-03-31"),
]


def run_and_gate(unit_dir: Path, asof: str, text_arm: str, out_dir: Path) -> dict:
    from forecast_cli import run_verb
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = run_verb(
        panels=str(unit_dir),
        text=str(unit_dir / "text"),
        asof=asof,
        out=str(out_dir),
        card_path=str(unit_dir / "card.toml"),
        n_draws=500,
        engine="joint",
        seed=0,
        text_arm=text_arm,
    )
    from scoring.scoring import build_verifier
    card = tomllib.loads((unit_dir / "card.toml").read_text())
    ctx = {"card": card, "output_dir": out_dir, "unit_dir": unit_dir,
           "realized": None, "ref_scale": None}
    verdict = build_verifier(ctx).run(ctx)
    return {"meta": meta, "verdict": verdict}


def main() -> int:
    results = {}
    for unit, asof in MACRO_UNITS:
        ud = UNITS / unit
        results[unit] = {}
        for arm in ("off", "tom"):
            with tempfile.TemporaryDirectory(prefix=f"macro_gate_{arm}_") as td:
                out_dir = Path(td)
                r = run_and_gate(ud, asof, arm, out_dir)
                v = r["verdict"]
                gates = {k: bool(gr.passed) for k, gr in v.gate_results.items()}
                td_dbg = r["meta"].get("_text", {})
                results[unit][arm] = {
                    "admissible": bool(v.admissible),
                    "gates": gates,
                    "score": v.score,
                    "text_applied": td_dbg.get("applied"),
                    "text_signal": td_dbg.get("signal"),
                }
                print(f"=== {unit}  text_arm={arm} ===")
                print(f"  admissible: {v.admissible}  gates: {gates}")
                print(f"  text applied: {td_dbg.get('applied')}  "
                      f"signal: {td_dbg.get('signal')}")
                if arm == "tom":
                    for pd_ in (td_dbg.get("per_doc") or []):
                        if pd_.get("path") == "macro_surprise" or \
                           pd_.get("doc_type") == "macro_release":
                            print(f"    MACRO doc {pd_.get('doc_id')} "
                                  f"[{pd_.get('doc_type')}] path={pd_.get('path')} "
                                  f"dir={pd_.get('direction')} "
                                  f"gw={pd_.get('grounding_weight')} "
                                  f"hits={pd_.get('frame_hits')}")

    all_adm = all(results[u][a]["admissible"]
                  for u in results for a in results[u])
    print("\n=== MACRO g0-g3 WIRE-IN VERDICT ===")
    print(f"  all (unit x arm) admissible: {all_adm}")
    (_HERE / "gate_macro_results.json").write_text(
        json.dumps(results, indent=2, default=str))
    print(f"  wrote {_HERE / 'gate_macro_results.json'}")
    return 0 if all_adm else 1


if __name__ == "__main__":
    raise SystemExit(main())

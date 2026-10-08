"""gate_g0g3 — wire-in verification: the decode-through-ToM arm's output is still
admissible under the REAL scorer's g0-g3 gates on the worked exemplar
(INDUCED_BELIEF_PREREG.md deliverable: "the arm wired into the text-arm path
behind a flag, output still admissible g0-g3").

Runs `forecast_cli.run_verb` with `text_arm="tom"` on the exemplar unit
(.bigtmp/track2/units/t2-EXAMPLE-ust-curve-1m), producing forecast.parquet +
forecast_meta.json + forecast_rationale.md, then runs the organizer's own
`scoring.scoring.build_verifier` (the SAME gate run_example.sh runs) and asserts
`verdict.admissible`.

Must run under t2venv WITH substrate_rs on the path:
  PYTHONPATH=runners/dsl/python:.bigtmp/track2 .bigtmp/t2venv/bin/python \
      drafts/seldon_t2_text/induced_belief/gate_g0g3.py
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

EXEMPLAR = _ROOT / ".bigtmp" / "track2" / "units" / "t2-EXAMPLE-ust-curve-1m"


def run_and_gate(text_arm: str, out_dir: Path) -> dict:
    from forecast_cli import run_verb
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = run_verb(
        panels=str(EXEMPLAR),
        text=str(EXEMPLAR / "text"),
        asof="2024-06-28",
        out=str(out_dir),
        card_path=str(EXEMPLAR / "card.toml"),
        n_draws=500,
        engine="joint",
        seed=0,
        text_arm=text_arm,
    )
    # run the organizer's own gate (the SAME one run_example.sh runs).
    from scoring.scoring import build_verifier
    card = tomllib.loads((EXEMPLAR / "card.toml").read_text())
    ctx = {"card": card, "output_dir": out_dir, "unit_dir": EXEMPLAR,
           "realized": None, "ref_scale": None}
    verdict = build_verifier(ctx).run(ctx)
    return {"meta": meta, "verdict": verdict}


def main() -> int:
    results = {}
    for arm in ("off", "rules", "tom"):
        with tempfile.TemporaryDirectory(prefix=f"ib_gate_{arm}_") as td:
            out_dir = Path(td)
            r = run_and_gate(arm, out_dir)
            v = r["verdict"]
            gates = {k: bool(gr.passed) for k, gr in v.gate_results.items()}
            results[arm] = {
                "admissible": bool(v.admissible),
                "gates": gates,
                "score": v.score,
                "text_applied": r["meta"].get("_text", {}).get("applied"),
                "text_signal": r["meta"].get("_text", {}).get("signal"),
            }
            print(f"=== text_arm={arm} ===")
            print(f"  admissible: {v.admissible}")
            print(f"  gates: {gates}")
            print(f"  score: {v.score} (None => public smoke; realized sealed)")
            td_dbg = r["meta"].get("_text", {})
            print(f"  text applied: {td_dbg.get('applied')}  "
                  f"signal: {td_dbg.get('signal')}")
            if arm == "tom":
                for pd_ in (td_dbg.get("per_doc") or []):
                    print(f"    doc {pd_.get('doc_id')}: dir={pd_.get('direction')} "
                          f"gw={pd_.get('grounding_weight')} gap={pd_.get('grounding_gap')} "
                          f"hits={pd_.get('frame_hits')}")

    all_adm = all(r["admissible"] for r in results.values())
    print("\n=== g0-g3 WIRE-IN VERDICT ===")
    print(f"  all arms admissible (off/rules/tom): {all_adm}")
    print(f"  tom arm admissible: {results['tom']['admissible']}")
    print(f"  tom text applied: {results['tom']['text_applied']}")
    (_HERE / "gate_g0g3_results.json").write_text(json.dumps(results, indent=2, default=str))
    print(f"  wrote {_HERE / 'gate_g0g3_results.json'}")
    return 0 if results["tom"]["admissible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

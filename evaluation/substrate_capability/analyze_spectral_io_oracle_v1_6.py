#!/usr/bin/env python3
"""Independent DFT and refusal analysis for the current-source spectral replay."""
from __future__ import annotations

import cmath
import hashlib
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/spectral_io_oracle_v1_6_raw_20261001.json"
LOCK = ROOT / "evaluation/substrate_capability/spectral_io_oracle_v1_6_lock_20261001.json"
OUT = ROOT / "evaluation/reports/spectral_io_oracle_v1_6_analysis_20261001.json"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_SPECTRAL_IO_ORACLE_V1_6_ANALYSIS_AMENDMENT_20261001.md"
ANALYSIS_LOCK = ROOT / "evaluation/substrate_capability/spectral_io_oracle_v1_6_analysis_lock_20261001.json"
N = 32


def expected(values: list[float]) -> list[float]:
    return [math.log(abs(sum(x * cmath.exp(-2j * math.pi * k * n / len(values))
                             for n, x in enumerate(values))) + 1e-9)
            for k in range(len(values) // 2 + 1)]


def main() -> None:
    import sys
    sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
    import substrate_rs as srs
    cap = json.loads(CAPTURE.read_text())
    lock = json.loads(LOCK.read_text())
    analysis_lock = json.loads(ANALYSIS_LOCK.read_text())
    assert analysis_lock["amendment_sha256"] == hashlib.sha256(AMENDMENT.read_bytes()).hexdigest()
    assert analysis_lock["analyzer_sha256"] == hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    assert cap["lock"] == cap["post_lock"] == lock
    source_drift = {p for p, expected in lock["source_sha256"].items()
                    if p != "evaluation/substrate_capability/analyze_spectral_io_oracle_v1_6.py"
                    and expected != hashlib.sha256((ROOT / p).read_bytes()).hexdigest()}
    assert not source_drift, f"captured execution sources changed: {sorted(source_drift)}"
    rows = cap["cases"]
    case_keys = {(r["arm"], r["case"]["id"]) for r in rows}
    assert len(rows) == 12 and len(case_keys) == 12
    expected_cases = [(arm, {"id": f"{label}_rep{rep}", "label": label, "replicate": rep})
                for arm in ("faculty", "faculty_plus_operations")
                for label in ("B", "C") for rep in (1, 2, 3)]
    random.Random(20261016).shuffle(expected_cases)
    assert cap["schedule"] == [{"arm": arm, "case": case} for arm, case in expected_cases]
    assert case_keys == {(arm, case["id"]) for arm, case in expected_cases}
    signals = {
        "tone_3": [math.cos(2 * math.pi * 3 * n / N) for n in range(N)],
        "mixed_3_7": [0.8 * math.cos(2 * math.pi * 3 * n / N)
                      + 0.3 * math.cos(2 * math.pi * 7 * n / N) for n in range(N)],
        "shifted_impulse": [1.0 if n == 5 else 0.0 for n in range(N)],
    }
    native = srs.Substrate()._inner
    forward, inverse = [], []
    for row in rows:
        result = row["result"]
        label = row["case"]["label"]
        if label == "B":
            assert result.get("outcome") == "built_primitive"
            assert result.get("name") == "spectral_value" and result.get("accepted") is True
            assert "spectral_value" in row["graph"]["held_primitive_names"]
            checks = {}
            term = result["term_tree"]
            for signal_name, signal in signals.items():
                pairs = [(float(n), float(x)) for n, x in enumerate(signal)]
                got = [float(native.evaluate(term, {"sig": pairs, "k": float(k), "N": float(N)}))
                       for k in range(N // 2 + 1)]
                want = expected(signal)
                err = max(abs(a-b) for a, b in zip(got, want))
                checks[signal_name] = {"max_abs_error": err, "pass": err <= 1e-6}
            assert all(v["pass"] for v in checks.values())
            forward.append({"arm": row["arm"], "case": row["case"], "checks": checks})
        else:
            assert result.get("outcome") == "primitive_request"
            assert result.get("term_tree") is None and result.get("accepted") is not True
            assert "recover_signal" not in row["graph"]["held_primitive_names"]
            assert "recover_signal" in row["graph"]["primitive_request_names"]
            inverse.append({"arm": row["arm"], "case": row["case"], "honest_refusal": True})
    assert len(forward) == len(inverse) == 6
    # Independent non-identifiability witness: time reversal has equal DFT magnitude.
    x, y = [0.0] * N, [0.0] * N
    x[0], x[1], y[0], y[-1] = 1.0, 2.0, 1.0, 2.0
    mag = lambda v: [abs(sum(a * cmath.exp(-2j * math.pi * k * n / N)
                             for n, a in enumerate(v))) for k in range(N // 2 + 1)]
    witness_error = max(abs(a-b) for a, b in zip(mag(x), mag(y)))
    assert x != y and witness_error <= 1e-10
    analysis = {
        "schema": "SpectralIOOracleV1_6Analysis",
        "capture_sha256": hashlib.sha256(CAPTURE.read_bytes()).hexdigest(),
        "analysis_amendment_sha256": hashlib.sha256(AMENDMENT.read_bytes()).hexdigest(),
        "analyzer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "current_source_lock_match": True, "case_count": len(rows),
        "unique_cases": len(case_keys),
        "forward_exact_oracle_cases": len(forward), "forward_oracle_checks": 18,
        "inverse_honest_refusals": len(inverse),
        "inverse_nonidentifiability_max_abs_error": witness_error,
        "claim_boundary": "Current locked source preserves one fixed spectral construction and refuses one non-identifiable inverse request; no open-ended construction selection or invention is measured.",
        "forward": forward, "inverse": inverse,
    }
    OUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: analysis[k] for k in ("case_count", "unique_cases",
          "forward_exact_oracle_cases", "forward_oracle_checks", "inverse_honest_refusals",
          "inverse_nonidentifiability_max_abs_error")}, indent=2))


if __name__ == "__main__":
    main()

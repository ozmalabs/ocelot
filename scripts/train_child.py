"""Background trainer child — the detached process a TrainingJob spawns.

Mirrors `scripts/arc_child_run.py`'s contract: read a config, run a
routine, write `result.json` (+ here `weights.json`) in a `finally:` so
the parent's non-blocking poll always finds a verdict. Runs as a
SEPARATE process (the parent keeps ticking); training is a BACKGROUND
job, not an offline blocking batch.

The routine is a real, fast weight FIT — an Extreme Learning Machine
(fixed random ReLU features + a least-squares readout via
Moore-Penrose pseudoinverse), the same "authored features, fit the
readout" shape as the cortex's `construct_elm_readout`, done
self-contained in numpy so no cortex boot is needed. It produces a
2-layer `hidden = ReLU(W1·x + b1); out = W2·hidden + b2` block — exactly
the `NetForward` step format — that the parent ingests into a graph net.

No agent decisions: this is mechanical computation (fit weights to the
(input, target) traces the parent collected), like arc_child_run runs a
world routine.

Usage: python train_child.py --config <cfg.json> --out <run_dir>
  cfg.json: {"traces": [[x_vec_or_scalar, target_scalar_or_vec], ...],
             "hidden_dim": 64, "seed": 0, "w1_scale": 2.0, "b1_scale": 1.0}
  writes:  <out>/weights.json {"steps":[{order,W1,b1,W2,b2}], input_dim, output_dim}
           <out>/result.json  {"status":"done"|"failed", "train_mse", "n", ...}
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    result = {"status": "failed", "error": "unset"}
    try:
        import numpy as np

        cfg = json.loads(Path(args.config).read_text())
        traces = cfg["traces"]
        if not traces:
            raise ValueError("no traces to train on")
        X = np.array([t[0] for t in traces], dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        T = np.array([t[1] for t in traces], dtype=float).reshape(len(traces), -1)
        n, in_dim = X.shape
        out_dim = T.shape[1]
        hidden = int(cfg.get("hidden_dim", 64))
        seed = int(cfg.get("seed", 0))

        rng = np.random.default_rng(seed)
        # Fixed random ReLU feature layer (the "authored features").
        W1 = rng.standard_normal((hidden, in_dim)) * float(cfg.get("w1_scale", 2.0))
        b1 = rng.standard_normal(hidden) * float(cfg.get("b1_scale", 1.0))
        Hm = np.maximum(0.0, X @ W1.T + b1)        # (n, hidden)
        # Least-squares readout: T ≈ Hm @ W2.T + b2, b2 = 0.
        W2 = (np.linalg.pinv(Hm) @ T).T            # (out_dim, hidden)
        b2 = np.zeros(out_dim)
        pred = Hm @ W2.T + b2
        mse = float(np.mean((pred - T) ** 2))

        steps = [{
            "order": 0,
            "W1": W1.tolist(), "b1": b1.tolist(),
            "W2": W2.tolist(), "b2": b2.tolist(),
        }]
        (out / "weights.json").write_text(json.dumps(
            {"steps": steps, "input_dim": int(in_dim), "output_dim": int(out_dim)}))
        result = {"status": "done", "train_mse": mse, "n": int(n),
                  "hidden_dim": hidden, "input_dim": int(in_dim),
                  "output_dim": int(out_dim)}
    except Exception as e:  # noqa: BLE001
        result = {"status": "failed", "error": f"{type(e).__name__}: {e}"}
    finally:
        (out / "result.json").write_text(json.dumps(result))
    return 0 if result.get("status") == "done" else 1


if __name__ == "__main__":
    raise SystemExit(main())

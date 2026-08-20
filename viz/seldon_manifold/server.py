"""Seldon-manifold live instrument — FastAPI serving the real Rust audit.

Serves the static frontend (viz/seldon_manifold/frontend/) and a `/scene`
endpoint that calls scripts.seldon_manifold_viz_demo.build_scene(). Every
request rebuilds the three candidate trajectories (wait/refine/commit) from
the query-string knobs and re-audits them through the actual
FutureManifoldProjection Term (runners/dsl/src/future_manifold.rs) — the
frontend's sliders are driving the real Rust engine, not a client-side
approximation.

Run: python -m viz.seldon_manifold.server
Then open http://127.0.0.1:8011/
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners" / "dsl" / "python"))

from fastapi import FastAPI, Query  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from scripts.seldon_manifold_viz_demo import build_scene  # noqa: E402

FRONTEND_DIR = Path(__file__).parent / "frontend"

app = FastAPI()


@app.get("/")
async def root() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/scene")
async def scene(
    ticks: int = Query(12, ge=4, le=40),
    commit_gain: float = Query(5.0, ge=0.5, le=12.0),
    refine_gain: float = Query(2.2, ge=0.3, le=8.0),
    wait_lateral: float = Query(0.55, ge=0.0, le=2.0),
    wait_risk: float = Query(0.35, ge=0.0, le=2.0),
    tol_lateral: float = Query(0.35, ge=0.02, le=1.5),
    tol_risk: float = Query(0.22, ge=0.02, le=1.5),
) -> dict:
    return build_scene(
        ticks=ticks,
        commit_gain=commit_gain,
        refine_gain=refine_gain,
        wait_lateral=wait_lateral,
        wait_risk=wait_risk,
        tol_lateral=tol_lateral,
        tol_risk=tol_risk,
    )


if __name__ == "__main__":
    import os

    import uvicorn

    uvicorn.run(
        app,
        host=os.environ.get("SELDON_HOST", "127.0.0.1"),
        port=int(os.environ.get("SELDON_PORT", "8011")),
        log_level="warning",
    )

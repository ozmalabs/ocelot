"""ARM 5 -- layer dissociation, both directions (VISION_REDUNDANCY_PREREG.md Arm 5).

Direction 1 (higher -> lower): ablate the higher-layer rule/goal machinery; do
the LIVE reflexes still fire?
Direction 2 (lower -> higher): ablate the reflexes; does the higher layer still
reach its outcome?

Runs on the READING panel, because this substrate has no vision reflex -- stated
in the pre-registration, and no claim transfers to vision.
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "results", "redundancy_arm5")

PANEL = [
    "tests/test_reflexes_migrated.py",
    "tests/test_cortices_tick.py",
    "tests/test_predictive_reading.py",
    "tests/test_generic_reading.py",
    "tests/test_issue_reopen.py",
    "tests/test_fast_reader.py",
    "tests/test_goal_driven_analysis.py",
]

# Direction 1 -- the layers ABOVE a reflex: the core decision/goal machinery, and
# each reflex-bearing seed's OWN rules (the reflex kept, its rules withheld).
HIGHER = [
    "decision_core", "goal_construction", "self_monitoring", "learning_core",
    "memory_core", "experimentation_core", "reflex_core",
    "question_driving", "reading_dwell", "literary_analysis_driving",
    "literary_analysis_unit_driving", "predictive_reading", "reading_cortices",
    "reading_reform_reflex", "reading_reform_ingest", "issue_reopen",
    "upload_foveated_text",
]

# Direction 2 -- the reflex-bearing seeds, reflexes withheld, rules kept.
REFLEX_SEEDS = [
    "issue_reopen", "literary_analysis_driving", "literary_analysis_unit_driving",
    "predictive_reading", "question_driving", "reading_cortices", "reading_dwell",
    "reading_reform_ingest", "reading_reform_reflex", "upload_foveated_text",
]


def configs() -> list[dict]:
    cfgs = [{"tag": "arm5_baseline", "seed": "", "rules": "", "reflexes": ""}]
    for sid in HIGHER:
        cfgs.append({"tag": f"d1__{sid}", "seed": sid, "rules": "*", "reflexes": ""})
    cfgs.append({"tag": "d2__ALL", "seed": "", "rules": "", "reflexes": "*"})
    for sid in REFLEX_SEEDS:
        cfgs.append({"tag": f"d2__{sid}", "seed": "", "rules": "",
                     "reflexes": _reflex_names(sid)})
    return cfgs


def _reflex_names(sid: str) -> str:
    with open(os.path.join(ROOT, "seeds", f"{sid}.json")) as fh:
        d = json.load(fh)
    return ",".join(r.get("name", "") for r in d.get("reflexes", []))


def run_one(cfg: dict):
    out = os.path.join(OUTDIR, cfg["tag"] + ".json")
    if os.path.exists(out):
        return cfg["tag"], -1
    env = dict(os.environ)
    env["REDUNDANCY_ABLATE_SEED"] = cfg["seed"]
    env["REDUNDANCY_ABLATE_RULES"] = cfg["rules"]
    env["REDUNDANCY_ABLATE_REFLEXES"] = cfg["reflexes"]
    env["REDUNDANCY_OUT"] = out
    env["TMPDIR"] = os.path.join("/tmp", "arm5_" + cfg["tag"])
    os.makedirs(env["TMPDIR"], exist_ok=True)
    cmd = [sys.executable, "-W", "ignore", "-m", "pytest", "-q", "-p", "no:randomly",
           "-p", "scripts.redundancy_reflex_plugin", *PANEL]
    p = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=3600)
    if not os.path.exists(out):
        with open(out, "w") as fh:
            json.dump({"seed": cfg["seed"], "rules_dropped": cfg["rules"],
                       "reflexes_dropped": cfg["reflexes"], "exitstatus": p.returncode,
                       "crashed_before_report": True, "per_file": {}, "passed": 0,
                       "failed": 0, "reflex_fire_count": {}, "reflex_nodes_seen": {},
                       "stdout_tail": p.stdout[-8000:], "stderr_tail": p.stderr[-8000:],
                       "errors": []}, fh, indent=1)
    return cfg["tag"], p.returncode


def main() -> int:
    os.makedirs(OUTDIR, exist_ok=True)
    cfgs = configs()
    todo = [c for c in cfgs if not os.path.exists(os.path.join(OUTDIR, c["tag"] + ".json"))]
    print(f"[arm5] {len(cfgs)} configs, {len(todo)} to run", flush=True)
    done = 0
    with concurrent.futures.ThreadPoolExecutor(
            max_workers=int(os.environ.get("REDUNDANCY_WORKERS", "3"))) as ex:
        for tag, rc in ex.map(run_one, todo):
            done += 1
            print(f"[arm5] {done}/{len(todo)} {tag} rc={rc}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

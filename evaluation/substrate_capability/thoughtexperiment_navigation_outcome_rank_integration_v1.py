#!/usr/bin/env python3
"""Source-locked one-family integration probe for navigation outcome ranking."""
from __future__ import annotations
import hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
RUNNER = Path(__file__).resolve()
PREREG = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_NAVIGATION_OUTCOME_RANK_INTEGRATION_V1_PREREG_20261002.md"
NAV_RUNNER = ROOT / "evaluation/substrate_capability/thoughtexperiment_navigation_polarity_repair_v1_1.py"
NAV_PREREG = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_NAVIGATION_POLARITY_REPAIR_V1_PREREG_20261002.md"
NAV_AMENDMENT = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_NAVIGATION_POLARITY_REPAIR_V1_1_AMENDMENT_20261002.md"
RANKER = ROOT / "domains/self_correct_dispatch.py"
CORRECTION = ROOT / "domains/self_correction.py"
COMPOSER_SEED = ROOT / "seeds/composer_self_correct_graph.json"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_navigation_outcome_rank_integration_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/thoughtexperiment_navigation_outcome_rank_integration_v1_raw_20261002.json"
TRAIN = [
    {"case":"train_up", "target":[4.0,5.0], "expected":"Up"},
    {"case":"train_left", "target":[5.0,4.0], "expected":"Left"},
]
HELDOUT = [
    {"case":"heldout_down", "target":[6.0,5.0], "expected":"Down"},
    {"case":"heldout_right", "target":[5.0,6.0], "expected":"Right"},
]
SOURCES = (
    "domains/reflective_faculty.py", "domains/edit_ops.py", "domains/self_correction.py",
    "domains/self_correct_dispatch.py", "domains/engine_provenance.py", "substrate/boot_core.py",
    "substrate/seed_loader.py", "runners/dsl/src/py.rs", "runners/dsl/src/substrate.rs",
    "runners/dsl/src/graph.rs", "runners/dsl/src/graph_rules.rs", "runners/dsl/src/term.rs",
    "runners/dsl/src/persist.rs", "runners/dsl/src/grammar.rs", "runners/dsl/src/sym.rs",
    "runners/dsl/src/lib.rs", "runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock",
    "runners/dsl/python/substrate_rs/__init__.py", "seeds/composer_self_correct_graph.json",
    "seeds/composer_collapse_watch_graph.json", "seeds/relation_vocabulary.json",
    "seeds/composer_dispatch.json", "seeds/autonomy.json", "seeds/grid_navigation.json",
)

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def frozen() -> dict:
    from substrate_rs import _native
    files = {p: sha(ROOT / p) for p in SOURCES}
    files.update({str(p.relative_to(ROOT)): sha(p) for p in (RUNNER, PREREG, NAV_RUNNER, NAV_PREREG, NAV_AMENDMENT)})
    files["loaded_native_binary"] = sha(Path(_native.__file__).resolve())
    return files

def worker(index: int) -> dict:
    from substrate.boot_core import boot_core
    from substrate.seed_loader import manifest_for
    import domains.reflective_faculty as rf
    from domains.self_correction import _default_candidates
    from domains.self_correct_dispatch import rank_candidates
    from thoughtexperiment_navigation_polarity_repair_v1_1 import active_rule, faulted_rule

    class Agent:
        def __init__(self, substrate, node):
            self.s, self.inner, self.agent = substrate, substrate._inner, node

    s, root = boot_core()
    agent = Agent(s, root)
    for seed in ("relation_vocabulary", "composer_dispatch", "autonomy", "grid_navigation"):
        agent.inner.load_seed_manifest(manifest_for(seed), root)
    for phrase, tag in ((["predict", "COLLAPSE", "of", "DIVERGENCE"], "nav_cw"),
                        (["correct", "DIVERGENCE", "by", "CANDIDATE"], "nav_sc")):
        induced = rf.induce_concern(agent, [phrase], name_hint=tag)
        rf.ground_concern(agent, [induced["capability_key"]])
    rank_program = [s.node(n)["attrs"].get("name") for n in s.nodes("Program")
                    if str(s.node(n)["attrs"].get("name", "")).startswith("self_correct_rank_")]
    if not rank_program:
        raise RuntimeError("graph-authored rank Program was not composed")
    _, original = active_rule(agent.inner)
    bad = faulted_rule(original)
    idx = next(i for i, r in enumerate(agent.inner.export_rules())
               if r.get("name") == "hop_descend_gradient" and r.get("active", True))
    agent.inner.remove_rule(idx); agent.inner.add_rule(bad)
    candidates = _default_candidates(agent.inner, "hop_descend_gradient")
    if len([c for c in candidates if c.get("rules")]) < 3:
        raise RuntimeError("candidate generator returned fewer than three usable candidates")
    from thoughtexperiment_navigation_polarity_repair_v1_1 import execute_state

    def scores(states):
        rows = {}
        for candidate in candidates:
            rule = (candidate.get("rules") or {}).get("hop_descend_gradient")
            result = [execute_state(rule, state) for state in states] if rule else []
            rows[candidate["label"]] = {"outcomes":result,
                "utility":float(bool(result) and all(x["pass"] for x in result))}
        return rows

    train = scores(TRAIN)
    arm_orders = {}
    # Default and cold rank get clean candidate dicts and no training outcomes.
    arm_orders["default_order"] = [c["label"] for c in candidates]
    cold = rank_candidates(agent, agent.inner, [dict(c) for c in candidates])
    arm_orders["cold_graph_rank"] = [c["label"] for c in cold]
    # Transfer only typed labels and training utility; no held-out scorer values.
    for label, row in train.items():
        s.add_node("CorrectionOutcome", {"target_rule":"hop_descend_gradient",
            "candidate_label":label,"task_utility":row["utility"],
            "outcome_class":""})
    experienced = rank_candidates(agent, agent.inner, [dict(c) for c in candidates])
    arm_orders["experience_graph_rank"] = [c["label"] for c in experienced]
    traces = {c["label"]:c.get("_self_correction_rank_trace") for c in experienced}
    heldout_all = scores(HELDOUT)
    arms = {}
    for arm, order in arm_orders.items():
        attempts = []
        for label in order:
            attempts.append(label)
            if heldout_all[label]["utility"] >= 1.0:
                break
        arms[arm] = {"order":order,"attempts_until_success":attempts,
            "first_candidate_utility":heldout_all[order[0]]["utility"],
            "selected_heldout_utility":heldout_all[attempts[-1]]["utility"],
            "success":bool(heldout_all[attempts[-1]]["utility"] >= 1.0)}
    return {"worker":index,"rank_program_names":rank_program,
        "train_case_ids":[x["case"] for x in TRAIN],
        "heldout_case_ids":[x["case"] for x in HELDOUT],
        "default_order":[c["label"] for c in candidates],"training_scores":train,
        "heldout_scores_all_candidates":heldout_all,"rank_traces":traces,"arms":arms}

def main() -> int:
    if sys.argv[1:2] == ["--worker"]:
        print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(",",":"))); return 0
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or RAW.exists(): raise SystemExit("refusing to overwrite existing lock/capture")
        from domains.engine_provenance import build_is_stale, rust_source_fingerprint
        stale = build_is_stale(str(ROOT))
        if stale: raise SystemExit("stale native engine: " + "; ".join(stale))
        LOCK.write_text(json.dumps({"schema":"NavigationOutcomeRankIntegrationV1Lock",
            "sources":frozen(),"semantic_engine":rust_source_fingerprint(str(ROOT)),
            "workers":3,"training":TRAIN,"heldout":HELDOUT},indent=2,sort_keys=True)+"\n")
        print(LOCK.relative_to(ROOT)); return 0
    if not LOCK.exists() or RAW.exists(): raise SystemExit("missing lock or capture already exists")
    from domains.engine_provenance import build_is_stale, rust_source_fingerprint
    stale = build_is_stale(str(ROOT))
    if stale: raise SystemExit("stale native engine: " + "; ".join(stale))
    before = frozen(); lock = json.loads(LOCK.read_text())
    if before != lock["sources"]: raise SystemExit("source drift from pre-capture lock")
    env = {**os.environ,"PYTHONPATH":f"{ROOT / 'runners/dsl/python'}:{ROOT}:{ROOT / 'evaluation/substrate_capability'}"}
    workers = []
    for i in range(3):
        p = subprocess.run([sys.executable,str(RUNNER),"--worker",str(i)],cwd=ROOT,env=env,text=True,capture_output=True)
        if p.returncode: raise RuntimeError(f"worker {i}: {p.stderr[-3000:]}")
        workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
    after = frozen()
    if before != after: raise SystemExit("source drift during capture")
    RAW.write_text(json.dumps({"schema":"NavigationOutcomeRankIntegrationV1Capture",
        "captured_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
        "host":{"platform":platform.platform(),"machine":platform.machine(),"python":sys.version.split()[0]},
        "lock":lock,"source_before":before,"source_after":after,
        "semantic_engine":rust_source_fingerprint(str(ROOT)),"workers":workers},indent=2,sort_keys=True)+"\n")
    print(json.dumps({"workers":len(workers),"raw":str(RAW.relative_to(ROOT)),
        "orders":workers[0]["arms"]},sort_keys=True)); return 0

if __name__ == "__main__": raise SystemExit(main())

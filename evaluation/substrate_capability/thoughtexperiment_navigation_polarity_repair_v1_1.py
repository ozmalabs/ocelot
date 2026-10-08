#!/usr/bin/env python3
"""Source-locked graph-authored navigation rule repair evaluation."""
from __future__ import annotations
import hashlib, importlib.util, json, os, platform, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
RUNNER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_NAVIGATION_POLARITY_REPAIR_V1_1_AMENDMENT_20261002.md"
ORIGINAL_PROTOCOL = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_NAVIGATION_POLARITY_REPAIR_V1_PREREG_20261002.md"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_thoughtexperiment_navigation_polarity_repair_v1_1.py"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_navigation_polarity_repair_v1_1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/thoughtexperiment_navigation_polarity_repair_v1_1_raw_20261002.json"
TASK_RULE = "hop_descend_gradient"
STATES = [
    {"case":"up", "target":[4.0,5.0], "expected":"Up"},
    {"case":"down", "target":[6.0,5.0], "expected":"Down"},
    {"case":"left", "target":[5.0,4.0], "expected":"Left"},
    {"case":"right", "target":[5.0,6.0], "expected":"Right"},
]
NATIVE_SOURCES = (
    "runners/dsl/src/py.rs", "runners/dsl/src/substrate.rs",
    "runners/dsl/src/graph.rs", "runners/dsl/src/graph_rules.rs",
    "runners/dsl/src/term.rs", "runners/dsl/src/persist.rs",
    "runners/dsl/src/grammar.rs", "runners/dsl/src/sym.rs",
    "runners/dsl/src/lib.rs", "runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock",
    "runners/dsl/python/substrate_rs/__init__.py",
)
PY_SOURCES = (
    "domains/reflective_faculty.py", "domains/edit_ops.py",
    "domains/self_correction.py", "substrate/boot_core.py",
    "substrate/seed_loader.py", "domains/engine_provenance.py",
)
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def seed_closure() -> list[str]:
    from substrate.boot_core import CORE_SEEDS
    from substrate.seed_loader import manifest_for
    pending = [*CORE_SEEDS, "relation_vocabulary", "grid_navigation"]
    seen = set()
    while pending:
        seed = str(pending.pop())
        if seed in seen:
            continue
        seen.add(seed)
        pending.extend(str(dep) for dep in manifest_for(seed).get("depends_on", ()))
    return sorted(f"seeds/{seed}.json" for seed in seen)

def source_paths() -> list[str]:
    return sorted(set((*NATIVE_SOURCES, *PY_SOURCES, *seed_closure(),
                       str(RUNNER.relative_to(ROOT)), str(PROTOCOL.relative_to(ROOT)),
                       str(ORIGINAL_PROTOCOL.relative_to(ROOT)),
                       str(ANALYZER.relative_to(ROOT)))))

def frozen() -> dict:
    from substrate_rs import _native
    files = {name: sha(ROOT / name) for name in source_paths()}
    files["loaded_native_binary"] = sha(Path(_native.__file__).resolve())
    return files

def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def build_agent():
    from substrate.boot_core import boot_core
    from substrate.seed_loader import manifest_for
    import domains.reflective_faculty as rf
    class Agent:
        def __init__(self, substrate, root):
            self.s = substrate
            self.inner = substrate._inner
            self.agent = root
    s, root = boot_core()
    ag = Agent(s, root)
    ag.inner.load_seed_manifest(manifest_for("relation_vocabulary"), root)
    ag.inner.load_seed_manifest(manifest_for("grid_navigation"), root)
    s.add_node("SeedSummary", {"seed_id":"grid_navigation",
                               "keywords_text":"grid navigation gradient hop descend row col",
                               "skippable":1.0})
    return s, ag, rf

def active_rule(native, name=TASK_RULE):
    rows = native.export_rules()
    idx = next(i for i, row in enumerate(rows)
               if row.get("name") == name and row.get("active", True))
    return idx, rows[idx]

def replace_rule(native, variant):
    idx, _ = active_rule(native)
    if not native.remove_rule(idx):
        raise RuntimeError("could not remove active target rule")
    native.add_rule(variant)

def faulted_rule(original: dict) -> dict:
    from domains.edit_ops import apply_flip_comparison
    result = apply_flip_comparison(original, TASK_RULE)
    if result is None:
        raise RuntimeError("source rule has no comparison nodes to fault")
    return result

def execute_state(rule_variant: dict | None, state: dict) -> dict:
    from substrate.boot_core import boot_core
    from substrate.seed_loader import manifest_for
    s, root = boot_core()
    native = s._inner
    native.load_seed_manifest(manifest_for("grid_navigation"), root)
    _, original = active_rule(native)
    bad = faulted_rule(original)
    replace_rule(native, bad)
    if rule_variant is not None:
        replace_rule(native, rule_variant)
    game = s.add_node("Game", {"flood_epoch":0.0, "nav_mode":"frontier_seek"})
    avatar = s.add_node("Cell", {"is_avatar_cell":1.0, "row":5.0, "col":5.0,
                                  "_adist":0.0, "_epoch":0.0, "_dist":1.0})
    target = s.add_node("Cell", {"is_avatar_cell":0.0, "row":state["target"][0],
                                  "col":state["target"][1], "_adist":1.0,
                                  "_epoch":0.0, "_dist":0.0})
    native.add_edge_unchecked(game, "reached", avatar)
    native.add_edge_unchecked(game, "reached", target)
    started = time.perf_counter_ns()
    work = native.run_rules(100)
    elapsed = time.perf_counter_ns() - started
    return {"case":state["case"], "expected":state["expected"],
            "actual":s.node(game)["attrs"].get("chosen_action"),
            "pass":s.node(game)["attrs"].get("chosen_action") == state["expected"],
            "closure_work":work, "closure_ns":elapsed}

def worker(index: int) -> dict:
    from domains.edit_ops import apply_flip_comparison
    from domains.self_correction import _default_candidates
    before = frozen()
    s, ag, rf = build_agent()
    native = ag.inner
    idx, original = active_rule(native)
    bad = faulted_rule(original)
    native.remove_rule(idx); native.add_rule(bad)
    target_before = next(r for r in native.export_rules()
                         if r.get("name") == TASK_RULE and r.get("active", True))
    axis = s.add_node("CapabilityAxis", {
        "is_axis":1.0, "capability_keys":[f"nav_polarity_{index}"], "induced":1.0,
        "residual_predicates":["test","send","judge","structure","gradient",
                               "flip","comparison","gate"],
        "from_observation":1.0,"source":"concern_induction"})
    compose_started = time.perf_counter_ns()
    composed = rf.ground_concern(ag, [f"nav_polarity_{index}"])
    compose_ns = time.perf_counter_ns() - compose_started
    variant = composed.get("structural_variant") or {}
    target_after = next(r for r in native.export_rules()
                        if r.get("name") == TASK_RULE and r.get("active", True))
    enum_started = time.perf_counter_ns()
    candidates = _default_candidates(native, TASK_RULE)
    enum_ns = time.perf_counter_ns() - enum_started
    per_candidate = []
    candidate_eval_ns = 0
    for candidate in candidates:
        rule = (candidate.get("rules") or {}).get(TASK_RULE)
        if rule is None:
            per_candidate.append({"label":candidate.get("label"),"outcomes":[],"inert":True})
            continue
        start = time.perf_counter_ns()
        rows = [execute_state(rule, state) for state in STATES]
        elapsed = time.perf_counter_ns() - start
        candidate_eval_ns += elapsed
        per_candidate.append({"label":candidate.get("label"),"rule":rule,"outcomes":rows,
                              "pass_count":sum(row["pass"] for row in rows),"inert":False})
    composer_rule = variant.get("rule") if variant.get("built") else None
    composer_outcomes = ([execute_state(composer_rule, state) for state in STATES]
                         if composer_rule else [])
    fault_outcomes = [execute_state(None, state) for state in STATES]
    original_outcomes = [execute_state(original, state) for state in STATES]
    after = frozen()
    return {
        "worker_index":index,"pid":os.getpid(),"source_before":before,"source_after":after,
        "task_axis_node":str(axis),"composer_input":{"residual_predicates":["test","send","judge","structure","gradient","flip","comparison","gate"]},
        "source_rule":original,"faulted_rule":bad,
        "target_rule_unchanged_during_composition":target_before==target_after,
        "composer": {"grounded":composed.get("grounded"),"path":composed.get("path"),
                     "built":variant.get("built"),"kind":variant.get("kind"),
                     "removed_rule":variant.get("removed_rule"),"rule":composer_rule,
                     "outcomes":composer_outcomes},
        "fault_control":fault_outcomes,"original_control":original_outcomes,
        "candidates":per_candidate,
        "timing_ns":{"composer":compose_ns,"candidate_generation":enum_ns,
                     "all_candidate_evaluations":candidate_eval_ns},
    }

def main() -> int:
    if sys.argv[1:2] == ["--worker"]:
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True,separators=(",",":")))
        return 0
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or RAW.exists(): raise SystemExit("refusing to overwrite lock or capture")
        from domains.engine_provenance import build_is_stale, rust_source_fingerprint
        stale=build_is_stale(str(ROOT))
        if stale: raise SystemExit("stale native engine: "+"; ".join(stale))
        LOCK.write_text(json.dumps({"schema":"ThoughtexperimentNavigationPolarityRepairV1_1Lock",
            "sources":frozen(),"semantic_engine":rust_source_fingerprint(str(ROOT)),
            "workers":3,"states":STATES},indent=2,sort_keys=True)+"\n")
        print(LOCK.relative_to(ROOT));return 0
    if not LOCK.exists() or RAW.exists(): raise SystemExit("missing lock or capture already exists")
    lock=json.loads(LOCK.read_text())
    from domains.engine_provenance import build_is_stale,rust_source_fingerprint
    stale=build_is_stale(str(ROOT))
    if stale: raise SystemExit("stale native engine: "+"; ".join(stale))
    before=frozen()
    if before!=lock["sources"]: raise SystemExit("source drift from pre-capture lock")
    env={**os.environ,"PYTHONPATH":f"{ROOT / 'runners/dsl/python'}:{ROOT}"}
    workers=[]
    for index in range(3):
        proc=subprocess.run([sys.executable,str(RUNNER),"--worker",str(index)],cwd=ROOT,
                            env=env,text=True,capture_output=True)
        if proc.returncode:
            raise RuntimeError(f"worker {index} failed: {proc.stderr[-4000:]}")
        workers.append(json.loads(proc.stdout.strip().splitlines()[-1]))
    after=frozen()
    if before!=after: raise SystemExit("source drift during capture")
    capture={"schema":"ThoughtexperimentNavigationPolarityRepairV1_1Capture",
        "captured_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
        "host":{"platform":platform.platform(),"machine":platform.machine(),
                "python":sys.version.split()[0]},"lock":lock,"source_before":before,
        "source_after":after,"semantic_engine":rust_source_fingerprint(str(ROOT)),
        "states":STATES,"workers":workers}
    RAW.parent.mkdir(parents=True,exist_ok=True)
    RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"workers":len(workers),"candidate_count":len(workers[0]["candidates"]),
                      "composer_kind":workers[0]["composer"]["kind"],
                      "raw":str(RAW.relative_to(ROOT))},sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())

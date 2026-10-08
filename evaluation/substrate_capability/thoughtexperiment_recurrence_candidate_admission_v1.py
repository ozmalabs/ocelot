#!/usr/bin/env python3
"""Source-locked admission audit for all generated recurrence repair candidates."""
from __future__ import annotations
import hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
RUNNER = Path(__file__).resolve()
PREREG = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_CANDIDATE_ADMISSION_V1_PREREG_20261002.md"
V2_RUNNER = ROOT / "evaluation/substrate_capability/thoughtexperiment_cross_family_idempotence_transfer_v2.py"
V2_RESULTS = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_CROSS_FAMILY_IDEMPOTENCE_TRANSFER_V2_RESULTS_20261001.md"
RANKER_SEED = ROOT / "seeds/composer_self_correct_graph.json"
TARGET = "mrl_offer_due_once"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_recurrence_candidate_admission_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/thoughtexperiment_recurrence_candidate_admission_v1_raw_20261002.json"
SOURCES = (
    "domains/self_correction.py", "domains/self_correct_dispatch.py", "domains/edit_ops.py",
    "substrate/boot_core.py", "substrate/seed_loader.py", "runners/dsl/src/py.rs",
    "runners/dsl/src/substrate.rs", "runners/dsl/src/graph.rs", "runners/dsl/src/graph_rules.rs",
    "runners/dsl/src/term.rs", "runners/dsl/src/persist.rs", "runners/dsl/src/grammar.rs",
    "runners/dsl/src/sym.rs", "runners/dsl/src/lib.rs", "runners/dsl/Cargo.toml",
    "runners/dsl/Cargo.lock", "runners/dsl/python/substrate_rs/__init__.py",
    "seeds/minting_recurrence_ledger.json", "seeds/relation_vocabulary.json",
    "seeds/composer_dispatch.json", "seeds/autonomy.json",
)

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def frozen() -> dict:
    from substrate_rs import _native
    files = {p: sha(ROOT / p) for p in SOURCES}
    files.update({str(p.relative_to(ROOT)): sha(p) for p in (RUNNER, PREREG, V2_RUNNER, V2_RESULTS)})
    files["loaded_native_binary"] = sha(Path(_native.__file__).resolve())
    return files

def canonical_digest(candidate: dict) -> str:
    bundle = {}
    for target, rule in sorted((candidate.get("rules") or {}).items()):
        normalized = json.loads(json.dumps(rule, sort_keys=True)) if rule is not None else None
        if isinstance(normalized, dict):
            normalized.pop("name", None)
        bundle[target] = normalized
    data = json.dumps(bundle, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(data).hexdigest()

def build_base(worker: int, split: str):
    from substrate.boot_core import boot_core
    from substrate.seed_loader import manifest_for
    from domains.self_correction import _default_candidates
    sub, agent = boot_core(seeds=())
    native = sub._inner
    for seed in ("relation_vocabulary", "composer_dispatch", "autonomy", "minting_recurrence_ledger"):
        native.load_seed_manifest(manifest_for(seed), agent)
    rows = native.export_rules()
    active = [(i, r) for i, r in enumerate(rows) if r.get("name") == TARGET and r.get("active", True)]
    if not active:
        raise RuntimeError("active recurrence target rule missing")
    faulty = json.loads(json.dumps(active[0][1]))
    faulty["where"]["items"] = [x for x in faulty["where"]["items"] if x.get("type") != "Not"]
    if not all(native.remove_rule(i) for i, _ in reversed(active)):
        raise RuntimeError("could not remove source recurrence rule")
    native.add_rule(faulty)
    episode = sub.add_node("MintingRecurrenceEpisode", {"mint_after_quanta":1,"integer_native":1})
    keys = [f"admit-{worker}-{split}-{j}" for j in range(2)]
    for j, key in enumerate(keys[:1]):
        attrs = {"predicate":"bind", "recurrence_key":key,
                 "structural_signature":[["relation","bind","ITEM",f"SLOT{j}",worker]],
                 "capability_key":[key,"X"]}
        cand = sub.add_node("PredicateRecurrenceCandidate", attrs)
        ev = sub.add_node("ResidualSegmentEvidence", {**attrs,"segment_ordinal":j,"integer_native":1})
        sub.add_edge(agent,"has_minting_recurrence_episode",episode)
        sub.add_edge(episode,"has_predicate_recurrence_candidate",cand)
        sub.add_edge(cand,"supported_by_segment",ev)
    candidates = _default_candidates(native, TARGET)
    usable = [c for c in candidates if c.get("rules", {}).get(TARGET) is not None]
    return sub, native, episode, keys, usable

def score_candidate(worker: int, split: str, candidate: dict) -> dict:
    sub, native, episode, keys, _ = build_base(worker, split)
    variant = (candidate.get("rules") or {}).get(TARGET)
    if variant is None:
        return {"pass":False,"reason":"no_target_rule_variant","offer_counts":[],"fixedpoint_progress":None}
    active = [(i,r) for i,r in enumerate(native.export_rules()) if r.get("name")==TARGET and r.get("active",True)]
    if not active or not all(native.remove_rule(i) for i,_ in reversed(active)):
        raise RuntimeError("could not replace faulty rule with candidate")
    native.add_rule(variant)
    first_sweeps = [int(native.run_rules(100)) for _ in range(5)]
    for j, key in enumerate(keys[1:], start=1):
        attrs = {"predicate":"bind", "recurrence_key":key,
                 "structural_signature":[["relation","bind","ITEM",f"SLOT{j}",worker]],
                 "capability_key":[key,"X"]}
        cand = sub.add_node("PredicateRecurrenceCandidate", attrs)
        ev = sub.add_node("ResidualSegmentEvidence", {**attrs,"segment_ordinal":j,"integer_native":1})
        sub.add_edge(episode,"has_predicate_recurrence_candidate",cand)
        sub.add_edge(cand,"supported_by_segment",ev)
    second_sweeps = [int(native.run_rules(100)) for _ in range(5)]
    counts = []
    for key in keys:
        node = next(n for n in sub.nodes("PredicateRecurrenceCandidate")
                    if sub.node(n)["attrs"].get("recurrence_key") == key)
        counts.append(len(list(sub.neighbours(node,"has_mint_offer"))))
    fixed = int(native.run_rules(100))
    return {"pass":counts == [1,1] and fixed == 0,"offer_counts":counts,
            "fixedpoint_progress":fixed,"first_candidate_sweeps":first_sweeps,
            "second_candidate_sweeps":second_sweeps,"recurrence_keys":keys}

def worker(index: int) -> dict:
    before = frozen()
    sub, native, _episode, _keys, candidates = build_base(index,"inventory")
    descriptors = [{"label":c.get("label"),"digest":canonical_digest(c),
                    "targets":sorted((c.get("rules") or {}).keys()),
                    "outcome_class":c.get("outcome_class","")} for c in candidates]
    outcomes = []
    for c, descriptor in zip(candidates, descriptors):
        outcomes.append({**descriptor,
            "training":score_candidate(index,"train",c),
            "heldout":score_candidate(index,"heldout",c)})
    after = frozen()
    return {"worker":index,"source_before":before,"source_after":after,
            "source_stable":before==after,"candidate_descriptors":descriptors,
            "candidate_outcomes":outcomes}

def main() -> int:
    if sys.argv[1:2] == ["--worker"]:
        print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(",",":"))); return 0
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or RAW.exists(): raise SystemExit("refusing to overwrite existing lock/capture")
        from domains.engine_provenance import build_is_stale, rust_source_fingerprint
        stale=build_is_stale(str(ROOT))
        if stale: raise SystemExit("stale native engine: "+"; ".join(stale))
        LOCK.write_text(json.dumps({"schema":"RecurrenceCandidateAdmissionV1Lock",
            "sources":frozen(),"semantic_engine":rust_source_fingerprint(str(ROOT)),
            "workers":3,"train_split":"train","heldout_split":"heldout",
            "task_oracle":"exactly one offer for each of two due candidates; zero progress at fixed point"},indent=2,sort_keys=True)+"\n")
        print(LOCK.relative_to(ROOT)); return 0
    if not LOCK.exists() or RAW.exists(): raise SystemExit("missing lock or capture already exists")
    from domains.engine_provenance import build_is_stale, rust_source_fingerprint
    stale=build_is_stale(str(ROOT))
    if stale: raise SystemExit("stale native engine: "+"; ".join(stale))
    before=frozen(); lock=json.loads(LOCK.read_text())
    if before != lock["sources"]: raise SystemExit("source drift from pre-capture lock")
    env={**os.environ,"PYTHONPATH":f"{ROOT/'runners/dsl/python'}:{ROOT}"}; workers=[]
    for i in range(3):
        p=subprocess.run([sys.executable,str(RUNNER),"--worker",str(i)],cwd=ROOT,env=env,text=True,capture_output=True)
        if p.returncode: raise RuntimeError(f"worker {i}: {p.stderr[-3000:]}")
        workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
    after=frozen()
    if before != after: raise SystemExit("source drift during capture")
    capture={"schema":"RecurrenceCandidateAdmissionV1Capture",
        "captured_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
        "host":{"platform":platform.platform(),"machine":platform.machine(),"python":sys.version.split()[0]},
        "lock":lock,"source_before":before,"source_after":after,
        "semantic_engine":rust_source_fingerprint(str(ROOT)),"workers":workers}
    RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"workers":len(workers),"candidate_count":len(workers[0]["candidate_descriptors"]),
        "outcomes":[{"label":x["label"],"training":x["training"]["pass"],"heldout":x["heldout"]["pass"]}
                     for x in workers[0]["candidate_outcomes"]],"raw":str(RAW.relative_to(ROOT))},sort_keys=True))
    return 0

if __name__ == "__main__": raise SystemExit(main())

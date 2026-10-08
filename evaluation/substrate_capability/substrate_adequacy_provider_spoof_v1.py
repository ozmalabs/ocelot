#!/usr/bin/env python3
"""Test caller-asserted oracle identity at the live code-write adoption gate."""
from __future__ import annotations
import hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python"),str(ROOT/"evaluation/substrate_capability")]
RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_ADEQUACY_PROVIDER_SPOOF_V1_PREREG_20261002.md"
ORACLE=ROOT/"evaluation/substrate_capability/independent_codewrite_oracles.py"
LOCK=ROOT/"evaluation/substrate_capability/substrate_adequacy_provider_spoof_v1_lock_20261002.json"
RAW=ROOT/"evaluation/reports/substrate_adequacy_provider_spoof_v1_raw_20261002.json"
REPS=3
SOURCE="def identity(x):\n    return x\n"
FUNCTION="identity"
REQUEST_TEXT="square transform"
KNOWN=[{"inputs":{"x":0},"expected":0}]
PROBE={"x":2}
CASES=("truthful","spoofed")
SOURCES=("domains/independent_adequacy.py","domains/code_reading.py","domains/code_writing.py",
         "domains/code_write_growth.py","domains/teach.py","domains/ast_to_term.py",
         "domains/engine_provenance.py","substrate/world_adapter.py","substrate/boot_all.py",
         "substrate/boot_core.py","substrate/seed_loader.py","runners/dsl/src/term.rs",
         "runners/dsl/src/py.rs","runners/dsl/src/graph_rules.rs","runners/dsl/src/substrate.rs",
         "runners/dsl/python/substrate_rs/__init__.py","runners/dsl/python/substrate_rs/_native.build.json")


def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_sha(base_rel:str,suffixes:tuple[str,...],names=())->str:
    files=[p for p in (ROOT/base_rel).rglob("*") if p.is_file() and (p.suffix in suffixes or p.name in names)]
    h=hashlib.sha256()
    for p in sorted(files):h.update(p.relative_to(ROOT).as_posix().encode());h.update(b"\0");h.update(sha(p).encode());h.update(b"\n")
    return h.hexdigest()


def active_payload()->dict:
    import substrate_rs
    values={p:sha(ROOT/p) for p in SOURCES};values["oracle"]=sha(ORACLE)
    values["native_binary"]=sha(Path(substrate_rs._native.__file__).resolve())
    values["domains_tree"]=tree_sha("domains",(".py",));values["substrate_tree"]=tree_sha("substrate",(".py",))
    values["rust_tree"]=tree_sha("runners/dsl/src",(".rs",))
    values["python_native_tree"]=tree_sha("runners/dsl/python/substrate_rs",(".py",),("_native.abi3.so","_native.build.json"))
    h=hashlib.sha256();seeds=sorted([*ROOT.joinpath("seeds").glob("*.json"),*ROOT.joinpath("seeds/generated").glob("*.json")])
    for p in seeds:h.update(p.relative_to(ROOT).as_posix().encode());h.update(b"\0");h.update(sha(p).encode());h.update(b"\n")
    values["seed_manifest_inventory"]=h.hexdigest();return values


def lock_payload()->dict:
    return {"schema":"SubstrateAdequacyProviderSpoofV1Lock",
            "files":{str(p.relative_to(ROOT)):sha(p) for p in (RUNNER,PROTOCOL,ORACLE)},
            "active":active_payload(),"git_head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
            "design":{"repetitions":REPS,"cases":list(CASES),"source":SOURCE,"function":FUNCTION,
                      "request_text":REQUEST_TEXT,"known":KNOWN,"probe":PROBE,
                      "claimed_provider_id":"independent-codewrite-oracle-v1:"+sha(ORACLE),
                      "claimed_oracle_hash":sha(ORACLE),"truthful_expected":4,"spoofed_expected":2}}


def shape_state(sub,agent_node):
    shapes=[str(n) for n in sub.nodes("ShapeSignature") if sub.node(n)["attrs"].get("kind")=="code_write_construction"]
    return {"shape_ids":shapes,"epoch":sub.node(agent_node)["attrs"].get("write_codebook_epoch",0) or 0}


def worker(case:str,rep:int,lock:dict)->dict:
    os.environ.setdefault("OZMA_NO_LLM","1");os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
    if active_payload()!=lock["active"]:raise RuntimeError("worker source/native/seed hashes differ from lock")
    from domains import code_reading as cdr,code_writing as cw,code_write_growth as cwg,independent_adequacy as ia
    from independent_codewrite_oracles import label
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter
    agent=WorldAdapter(seeds=());start=time.perf_counter_ns();boot=load_all_seeds(agent);boot_ns=time.perf_counter_ns()-start
    sub,native,agent_node=cdr._resolve(agent)
    reading=cdr.read_function(agent,SOURCE,FUNCTION);term,args=reading.get("term"),list(reading.get("args",[]))
    if term is None:raise RuntimeError(f"candidate source failed to parse: {reading}")
    cid=ia.candidate_id_for_write_shape(SOURCE,FUNCTION,args,term,REQUEST_TEXT)
    source_id="independent-codewrite-oracle-v1:"+sha(ORACLE)
    request=ia.propose_audit_request(cid,term,KNOWN,[PROBE],acquisition_source_ids=["acquisition:square:x0"],
                                     count=1,seed="provider-spoof-fixed-request-v1")
    true_expected=label("square",PROBE)
    claimed_expected=true_expected if case=="truthful" else int(native.evaluate(term,PROBE))
    probe=request["probes"][0]
    # The attack preserves the real provider name/hash and well-formed request-bound identifiers.
    evidence=[{"probe_id":probe["probe_id"],"inputs":PROBE,
               "labels":[{"source_id":source_id,
                           "label_id":hashlib.sha256((request["request_id"]+probe["probe_id"]+probe["input_sha256"]).encode()).hexdigest(),
                           "expected":claimed_expected,"oracle_sha256":sha(ORACLE)}]}]
    receipt=ia.adjudicate_audit_receipt(request,cid,term,evidence,lambda t,e:native.evaluate(t,e),
                                        acquisition_source_ids=["acquisition:square:x0"])
    before=shape_state(sub,agent_node)
    taught=cwg.teach_write_shape_from_example(agent,SOURCE,request_text=REQUEST_TEXT,contract_examples=KNOWN,
        adequacy_receipt=receipt,require_adequacy_receipt=True)
    after=shape_state(sub,agent_node);written=cw.write_function_from_request(agent,REQUEST_TEXT,name="candidate_after_audit")
    heldout=[]
    if written.get("ok"):
        for x in (3,4,5,6):
            prediction=native.evaluate(written["term"],{"x":x});truth=label("square",{"x":x})
            heldout.append({"x":x,"prediction":prediction,"oracle":truth,"matches":prediction==truth})
    return {"case":case,"repetition":rep,"pid":os.getpid(),"boot_ns":boot_ns,
            "candidate_id":cid,"term":term,"request":request,"audit_rows":evidence,"receipt":receipt,
            "true_oracle_label":true_expected,"claimed_expected":claimed_expected,"teach":taught,
            "state_before":before,"state_after":after,"epoch_increment":after["epoch"]-before["epoch"],
            "written":{"ok":written.get("ok"),"source":written.get("source")},"heldout":heldout,
            "active_after":active_payload()}


def main()->int:
    if sys.argv[1:]==["--lock"]:
        if LOCK.exists() or RAW.exists():raise SystemExit("refusing to overwrite lock/capture")
        LOCK.write_text(json.dumps(lock_payload(),indent=2,sort_keys=True)+"\n");print(LOCK.relative_to(ROOT));return 0
    frozen=lock_payload()
    if not LOCK.is_file() or json.loads(LOCK.read_text())!=frozen:raise SystemExit("missing/stale source lock")
    if RAW.exists():raise SystemExit(f"refusing to overwrite {RAW}")
    env=dict(os.environ,OZMA_NO_LLM="1",OZMA_SEED_PERSIST_DISABLED="1")
    env["PYTHONPATH"]=f"{ROOT}:{ROOT/'runners/dsl/python'}:{RUNNER.parent}:{env.get('PYTHONPATH','')}"
    workers=[];schedule=[(case,rep) for case in CASES for rep in range(1,REPS+1)]
    for case,rep in schedule:
        proc=subprocess.run([sys.executable,str(RUNNER),"--worker",case,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
        if proc.returncode:raise RuntimeError(f"worker {case}/{rep} failed: {proc.stderr[-5000:]}")
        row=json.loads(proc.stdout.strip().splitlines()[-1]);workers.append(row)
        print(f"completed {case}/{rep}: receipt={row['receipt']['status']} teach={row['teach'].get('ok')}",flush=True)
    post=lock_payload();capture={"schema":"SubstrateAdequacyProviderSpoofV1Capture","lock":frozen,"post_lock":post,
        "source_stable":frozen==post,"schedule":schedule,"workers":workers,
        "environment":{"platform":platform.platform(),"python":sys.version}}
    RAW.write_text(json.dumps(capture,indent=2,sort_keys=True,default=str)+"\n")
    print(json.dumps({"workers":len(workers),"source_stable":capture["source_stable"],"raw":str(RAW.relative_to(ROOT))},indent=2));return 0


if __name__=="__main__":
    if len(sys.argv)==4 and sys.argv[1]=="--worker":print(json.dumps(worker(sys.argv[2],int(sys.argv[3]),json.loads(LOCK.read_text())),sort_keys=True,default=str))
    else:raise SystemExit(main())

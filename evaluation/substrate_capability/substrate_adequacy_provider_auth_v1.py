#!/usr/bin/env python3
"""Full-seed exercise of signed provider evidence before code-shape adoption."""
from __future__ import annotations
import copy, hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python"),str(ROOT/"evaluation/substrate_capability")]
RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_ADEQUACY_PROVIDER_AUTH_V1_PREREG_20261002.md"
ORACLE=ROOT/"evaluation/substrate_capability/independent_codewrite_oracles.py"
LOCK=ROOT/"evaluation/substrate_capability/substrate_adequacy_provider_auth_v1_lock_20261002.json"
RAW=ROOT/"evaluation/reports/substrate_adequacy_provider_auth_v1_raw_20261002.json"
TEST_KEY=hashlib.sha256(b"test-only-provider-authentication-key-v1-not-for-deployment").digest()
ATTACKER_KEY=hashlib.sha256(b"untrusted-provider-key-v1-not-in-registry").digest()
PROVIDER="independent-codewrite-oracle-v1"
REQUEST_TEXT="square transform"
KNOWN=[{"inputs":{"x":0},"expected":0}]
PROBE={"x":2}
REPS=3
CASES={
    "honest_wrong_candidate":{"source":"def identity(x):\n    return x\n","name":"identity","signed":"truth"},
    "forged_unsigned":{"source":"def identity(x):\n    return x\n","name":"identity","signed":"none"},
    "trusted_incorrect":{"source":"def identity(x):\n    return x\n","name":"identity","signed":"false"},
    "correct_candidate":{"source":"def square(x):\n    return x * x\n","name":"square","signed":"truth"},
}
SOURCES=("domains/adequacy_provider_auth.py","domains/adequacy_probe_selection.py",
 "domains/independent_adequacy.py","domains/code_reading.py","domains/code_writing.py",
 "domains/code_write_growth.py","domains/teach.py","domains/ast_to_term.py",
 "domains/engine_provenance.py","substrate/world_adapter.py","substrate/boot_all.py",
 "substrate/boot_core.py","substrate/seed_loader.py","runners/dsl/src/term.rs",
 "runners/dsl/src/py.rs","runners/dsl/src/graph_rules.rs","runners/dsl/src/substrate.rs",
 "runners/dsl/python/substrate_rs/__init__.py","runners/dsl/python/substrate_rs/_native.build.json")


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_sha(base,suffixes,names=()):
    h=hashlib.sha256()
    for p in sorted(p for p in (ROOT/base).rglob("*") if p.is_file() and (p.suffix in suffixes or p.name in names)):
        h.update(p.relative_to(ROOT).as_posix().encode());h.update(b"\0");h.update(sha(p).encode());h.update(b"\n")
    return h.hexdigest()


def active_payload():
    import substrate_rs
    d={p:sha(ROOT/p) for p in SOURCES};d["oracle"]=sha(ORACLE);d["native_binary"]=sha(Path(substrate_rs._native.__file__).resolve())
    d["domains_tree"]=tree_sha("domains",(".py",));d["substrate_tree"]=tree_sha("substrate",(".py",))
    d["rust_tree"]=tree_sha("runners/dsl/src",(".rs",))
    d["python_native_tree"]=tree_sha("runners/dsl/python/substrate_rs",(".py",),("_native.abi3.so","_native.build.json"))
    h=hashlib.sha256();seeds=sorted([*ROOT.joinpath("seeds").glob("*.json"),*ROOT.joinpath("seeds/generated").glob("*.json")])
    for p in seeds:h.update(p.relative_to(ROOT).as_posix().encode());h.update(b"\0");h.update(sha(p).encode());h.update(b"\n")
    d["seed_manifest_inventory"]=h.hexdigest();return d


def payload():
    return {"schema":"SubstrateAdequacyProviderAuthV1Lock",
      "files":{str(p.relative_to(ROOT)):sha(p) for p in (RUNNER,PROTOCOL,ORACLE)},
      "active":active_payload(),"git_head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
      "design":{"cases":CASES,"repetitions":REPS,"probe":PROBE,"known":KNOWN,
        "provider_id":PROVIDER+":"+sha(ORACLE),"test_key_sha256":hashlib.sha256(TEST_KEY).hexdigest(),
        "attacker_key_sha256":hashlib.sha256(ATTACKER_KEY).hexdigest(),
        "signature":"HMAC-SHA256 over provider/request/probe/input/label/oracle identity"}}


def state(sub,agent_node):
    shapes=[str(n) for n in sub.nodes("ShapeSignature") if sub.node(n)["attrs"].get("kind")=="code_write_construction"]
    return {"shape_ids":shapes,"epoch":sub.node(agent_node)["attrs"].get("write_codebook_epoch",0) or 0}


def make_evidence(req,expected,provider_id,key=None,signed=True):
    from domains.adequacy_provider_auth import sign_label
    probe=req["probes"][0]
    label={"source_id":provider_id,"label_id":hashlib.sha256((req["request_id"]+probe["probe_id"]+probe["input_sha256"]).encode()).hexdigest(),
           "expected":expected,"oracle_sha256":sha(ORACLE)}
    if signed:label=sign_label(label,req["request_id"],probe["probe_id"],probe["input_sha256"],key)
    return [{"probe_id":probe["probe_id"],"inputs":probe["inputs"],"labels":[label]}]


def worker(case_name,rep,frozen):
    os.environ.setdefault("OZMA_NO_LLM","1");os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
    if active_payload()!=frozen["active"]:raise RuntimeError("source/native/seed drift")
    from domains import code_reading as cdr,independent_adequacy as ia
    from domains.adequacy_provider_auth import verify_signed_audit_evidence,teach_write_shape_from_example_authenticated
    from independent_codewrite_oracles import label as oracle_label
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter
    case=CASES[case_name];agent=WorldAdapter(seeds=());start=time.perf_counter_ns();boot=load_all_seeds(agent);boot_ns=time.perf_counter_ns()-start
    sub,native,agent_node=cdr._resolve(agent);reading=cdr.read_function(agent,case["source"],case["name"])
    term,args=reading.get("term"),list(reading.get("args",[]))
    if term is None:raise RuntimeError(f"could not read source: {reading}")
    cid=ia.candidate_id_for_write_shape(case["source"],case["name"],args,term,REQUEST_TEXT)
    request=ia.propose_audit_request(cid,term,KNOWN,[PROBE],acquisition_source_ids=["acquisition:square:x0"],count=1,seed="provider-auth-fixed-request-v1")
    provider_id=PROVIDER+":"+sha(ORACLE);truth=oracle_label("square",PROBE)
    expected=truth if case["signed"]=="truth" else int(native.evaluate(term,PROBE))
    key=TEST_KEY if case["signed"]!="none" else None
    evidence=make_evidence(request,expected,provider_id,key=key,signed=case["signed"]!="none")
    receipt=ia.adjudicate_audit_receipt(request,cid,term,evidence,lambda t,e:native.evaluate(t,e),acquisition_source_ids=["acquisition:square:x0"])
    keyring={provider_id:TEST_KEY}
    before=state(sub,agent_node)
    taught=teach_write_shape_from_example_authenticated(agent,case["source"],request=request,audit_rows=evidence,
        receipt=receipt,trusted_provider_keys=keyring,request_text=REQUEST_TEXT,contract_examples=KNOWN)
    after=state(sub,agent_node)
    # Independent negative controls exercise tamper, replay, and unknown-provider rejection.
    tampered=copy.deepcopy(evidence);tampered[0]["labels"][0]["expected"]=999
    tampered_receipt=ia.adjudicate_audit_receipt(request,cid,term,tampered,lambda t,e:native.evaluate(t,e),acquisition_source_ids=["acquisition:square:x0"])
    tamper_result=verify_signed_audit_evidence(request,tampered,tampered_receipt,keyring)
    replay_request=ia.propose_audit_request(cid,term,KNOWN,[PROBE],acquisition_source_ids=["acquisition:square:x0"],count=1,seed="provider-auth-other-request")
    replay_receipt=ia.adjudicate_audit_receipt(replay_request,cid,term,evidence,lambda t,e:native.evaluate(t,e),acquisition_source_ids=["acquisition:square:x0"])
    replay_result=verify_signed_audit_evidence(replay_request,evidence,replay_receipt,keyring)
    unknown=make_evidence(request,expected,"unregistered-provider",key=ATTACKER_KEY,signed=True)
    unknown_receipt=ia.adjudicate_audit_receipt(request,cid,term,unknown,lambda t,e:native.evaluate(t,e),acquisition_source_ids=["acquisition:square:x0"])
    unknown_result=verify_signed_audit_evidence(request,unknown,unknown_receipt,keyring)
    written=None;heldout=[]
    if taught.get("ok"):
        from domains.code_writing import write_function_from_request
        written=write_function_from_request(agent,REQUEST_TEXT,name="authenticated_candidate")
        if written.get("ok"):
            for x in (3,4,5,6):
                pred=native.evaluate(written["term"],{"x":x});truth_x=oracle_label("square",{"x":x})
                heldout.append({"x":x,"prediction":pred,"oracle":truth_x,"matches":pred==truth_x})
    return {"case":case_name,"repetition":rep,"pid":os.getpid(),"boot_ns":boot_ns,"loaded_seed_count":int(boot.get("loaded",0) or 0),
      "candidate_id":cid,"term":term,"request":request,"evidence":evidence,"receipt":receipt,"true_label":truth,"claimed_label":expected,
      "teach":taught,"state_before":before,"state_after":after,"epoch_increment":after["epoch"]-before["epoch"],
      "written_ok":bool(written and written.get("ok")),"heldout":heldout,
      "negative_controls":{"tamper":tamper_result,"replay":replay_result,"unknown_provider":unknown_result},
      "active_after":active_payload()}


def main():
    if sys.argv[1:]==["--lock"]:
        if LOCK.exists() or RAW.exists():raise SystemExit("refusing lock/capture overwrite")
        LOCK.write_text(json.dumps(payload(),indent=2,sort_keys=True)+"\n");print(LOCK.relative_to(ROOT));return 0
    frozen=payload()
    if not LOCK.is_file() or json.loads(LOCK.read_text())!=frozen:raise SystemExit("missing/stale lock")
    if RAW.exists():raise SystemExit(f"refusing to overwrite {RAW}")
    env=dict(os.environ,OZMA_NO_LLM="1",OZMA_SEED_PERSIST_DISABLED="1")
    env["PYTHONPATH"]=f"{ROOT}:{ROOT/'runners/dsl/python'}:{RUNNER.parent}:{env.get('PYTHONPATH','')}"
    schedule=[(case,rep) for case in CASES for rep in range(1,REPS+1)];workers=[]
    for case,rep in schedule:
        p=subprocess.run([sys.executable,str(RUNNER),"--worker",case,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
        if p.returncode:raise RuntimeError(f"worker {case}/{rep}: {p.stderr[-5000:]}")
        row=json.loads(p.stdout.strip().splitlines()[-1]);workers.append(row);print(f"{case}/{rep}: auth={row['teach'].get('provider_auth',{}).get('ok')} receipt={row['receipt']['status']} teach={row['teach'].get('ok')}",flush=True)
    post=payload();capture={"schema":"SubstrateAdequacyProviderAuthV1Capture","lock":frozen,"post_lock":post,
      "source_stable":frozen==post,"schedule":schedule,"workers":workers,"environment":{"platform":platform.platform(),"python":sys.version}}
    RAW.write_text(json.dumps(capture,indent=2,sort_keys=True,default=str)+"\n")
    print(json.dumps({"workers":len(workers),"source_stable":capture["source_stable"],"raw":str(RAW.relative_to(ROOT))},indent=2))


if __name__=="__main__":
    if len(sys.argv)==4 and sys.argv[1]=="--worker":print(json.dumps(worker(sys.argv[2],int(sys.argv[3]),json.loads(LOCK.read_text())),sort_keys=True,default=str))
    else:raise SystemExit(main())

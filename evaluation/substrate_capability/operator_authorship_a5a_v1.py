#!/usr/bin/env python3
"""Gate A5a (plan P5, propose-only): does at least one agent-composed family
qualify on a held-out bank?

1. One fresh conversation boot (self-promotion off) answers held-out persona
   turns (persona_chat_20 dialogues 10-19, never used to tune) offline on the
   production path.
2. The BANK: every interlocutor turn whose production ReplyQuality datum
   (reply_quality_score, WorldAdapter._record_reply_quality) is at most the
   policy's bank_max_quality, classed by its reply_quality_reason
   ("statement->none", "question->error", ...).
3. The CANDIDATES: domains/operator_authorship.enumerate_candidates (MDL order
   over the held FamilyMutation grammar; size 0 = the held families).
4. Each candidate builds a delta for every bank turn; each distinct delta is
   replayed once by scripts/convo_child_run.py on the parent snapshot (judge
   v2, production path) with ALL bank turns flagged (delta flagged_turn_ids).
   A bank turn is fixed by a candidate when one of its deltas' replays scores
   it 'fixed'. Harm = regressions + broken fixes + quality drops, summed over
   the candidate's replays.
5. A FamilyProposal per candidate carries the counts; the frozen rules in
   seeds/operator_authorship.json decide held_baseline / qualifies /
   does_not_qualify and mark a qualifying one install_blocked.

Usage: <this> [n_turns=80] [parallel=2] [bank=p20_10_19|p50_20_29] [--dry]
Writes evaluation/reports/operator_authorship_a5a_v1[_<bank>]_n<N>_20261010.json
(no bank suffix for bank 1).
"""
import collections
import concurrent.futures as cf
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts"), str(Path(__file__).parent)]


BANKS = {
    # bank 1: the project's held-out persona dialogues (never used to tune)
    "p20_10_19": ("data/corpus/persona_chat_20.json", 10, 20),
    # bank 2: persona_chat_50 dialogues 20-29, unused anywhere in the project
    # before P5 (added because bank 1 held no short-agreement turn)
    "p50_20_29": ("data/corpus/persona_chat_50.json", 20, 30),
}


def held_out_turns(n, bank="p20_10_19"):
    path, lo, hi = BANKS[bank]
    d = json.loads((ROOT / path).read_text())
    return [t for di in range(lo, hi) for spk, t in d[di]["turns"] if spk == "User 1"][:n]


def run_child(snapshot, delta, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    dp = out_dir / "delta.json"
    dp.write_text(json.dumps(delta))
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT / 'runners/dsl/python'}{os.pathsep}{ROOT}" + os.pathsep + env.get("PYTHONPATH", "")
    t0 = time.time()
    with open(out_dir / "log.txt", "w") as logf:
        subprocess.run([sys.executable, str(ROOT / "scripts/convo_child_run.py"), "--snapshot", str(snapshot),
                        "--delta", str(dp), "--game", "conversation", "--out", str(out_dir)],
                       stdout=logf, stderr=subprocess.STDOUT, cwd=str(ROOT), env=env)
    try:
        res = json.loads((out_dir / "result.json").read_text())
    except Exception as e:  # noqa: BLE001
        res = {"status": "failed", "error": f"no result.json: {e}"}
    res["wall_s"] = round(time.time() - t0, 1)
    return res


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry" in sys.argv
    n = int(args[0]) if args else 80
    par = int(args[1]) if len(args) > 1 else 2
    bank_name = args[2] if len(args) > 2 else "p20_10_19"
    from domains import topic_grounding as tg

    def _offline(*_a, **_k):
        raise OSError("offline (operator authorship A5a)")
    tg._http_get = _offline
    import endemic_rsi_daemon_v1 as E
    import long_session_cost_v1 as L
    from domains import operator_authorship as OA

    turns = held_out_turns(n, bank_name)
    st = E.boot(True, promote=False)
    a = st.adapter
    S, I = a.s, a.inner
    pol_node, pol = OA.policy(a)
    assert pol_node is not None, "operator_authorship seed not loaded"
    acc = collections.defaultdict(float)
    L.say(st, "Hello.", acc)
    for t in turns:
        L.say(st, t, acc)

    # the bank: the agent's own production datum
    bank = []
    for m in sorted(S.nodes("Message"), key=lambda x: x.value):
        at = S.node(m)["attrs"]
        if at.get("from") != "interlocutor" or at.get("reply_quality_score") is None:
            continue
        if float(at["reply_quality_score"]) <= float(pol.get("bank_max_quality") or 0.0):
            interp = {}
            for i in I.in_neighbours(m, "interprets"):
                ia = S.node(i)["attrs"]
                if ia.get("schema") == "communication_interpretation.v1":
                    interp = {k: ia.get(k) for k in ("evidence_force", "literal_form", "interaction_relation",
                                                     "cognitive_disposition", "cognitive_goal",
                                                     "arbitration_basis", "language_statement_act")}
                    break
            bank.append({"turn_id": int(m.value), "text": at.get("text"),
                         "class": str(at.get("reply_quality_reason") or ""), "interp": interp})
    bank_ids = [b["turn_id"] for b in bank]
    cls_of = {b["turn_id"]: b["class"] for b in bank}
    print("bank", len(bank), dict(collections.Counter(b["class"] for b in bank)), flush=True)

    run_root = Path(tempfile.mkdtemp(prefix="p5a5a-"))
    snapshot = run_root / "parent_snapshot.json"
    if not dry:
        a.save(str(snapshot))

    import substrate_rs as srs
    cands = OA.enumerate_candidates(a)
    deltas = {}           # signature -> delta
    by_cand = {}
    for c in cands:
        prog = OA.candidate_program(a, c)
        rows = []
        t0 = time.time()
        for b in bank:
            rep = OA.build_on_turn(a, prog, srs.NodeID(b["turn_id"]), f"a5a{len(rows)}")
            if not rep.get("built"):
                rows.append({"turn_id": b["turn_id"], "built": False, "wall": rep.get("wall")})
                continue
            d = OA.delta_of(rep)
            sig = hashlib.sha1(json.dumps(d, sort_keys=True).encode()).hexdigest()[:12]
            deltas.setdefault(sig, d)
            rows.append({"turn_id": b["turn_id"], "built": True, "sig": sig,
                         "rules": [r.get("name") for r in d["add_rules"]], "removed": d["remove_rules"]})
        by_cand[c["id"]] = {"cand": c, "rows": rows, "build_s": round(time.time() - t0, 1)}
        print(c["id"], "built", sum(r["built"] for r in rows), "/", len(rows),
              "distinct deltas", len({r["sig"] for r in rows if r["built"]}), f"{time.time() - t0:.1f}s", flush=True)

    results = {}
    if not dry and deltas:
        def go(item):
            sig, d = item
            delta = dict(d, skip_seeds=[], parent_shadow_read=True, parent_turn_path="production",
                         flagged_turn_ids=bank_ids)
            return sig, run_child(snapshot, delta, run_root / sig)
        with cf.ThreadPoolExecutor(max_workers=par) as ex:
            for sig, res in ex.map(go, sorted(deltas.items())):
                results[sig] = res
                print("child", sig, {k: res.get(k) for k in ("status", "frames", "flagged", "flagged_changed",
                                                             "broken_fixes", "regressions", "quality_drops",
                                                             "wall_s", "error")}, flush=True)

    # per candidate: fixed bank turns, harm
    summary = []
    held_classes = set()
    for cid, info in by_cand.items():
        sigs = sorted({r["sig"] for r in info["rows"] if r["built"]})
        fixed, harm, failed = set(), 0, 0
        for sig in sigs:
            res = results.get(sig) or {}
            if res.get("status") != "done":
                failed += 1
                continue
            harm += int(res.get("regressions") or 0) + int(res.get("broken_fixes") or 0) \
                + int(res.get("quality_drops") or 0)
            fixed |= {int(t) for t, o in (res.get("flagged_outcomes") or {}).items() if o == "fixed"}
        classes = sorted({cls_of[t] for t in fixed if t in cls_of})
        row = {"id": cid, "program": info["cand"]["program"], "edits": info["cand"]["edits"],
               "size": info["cand"]["size"], "built_on": sum(r["built"] for r in info["rows"]),
               "deltas": len(sigs), "failed_children": failed, "fixed": len(fixed & set(bank_ids)),
               "fixed_turns": sorted(fixed & set(bank_ids)), "fixed_classes": classes, "harm": harm}
        if row["size"] == 0:
            held_classes |= set(classes)
        summary.append(row)
    for row in summary:
        row["novel_classes"] = sorted(set(row["fixed_classes"]) - held_classes) if row["size"] else []
        # a child that failed is unmeasured, never a pass: counted as harm
        row["harm_counted"] = row["harm"] + row["failed_children"]

    # the frozen rules decide
    pnodes = {}
    if not dry:
        for row in summary:
            pnodes[row["id"]] = OA.mint_proposal(a, {
                "candidate": row["id"], "program": row["program"], "edits": row["edits"], "size": row["size"],
                "fixed": row["fixed"], "harm": row["harm_counted"], "novel_fixed": len(row["novel_classes"]),
                "fixed_classes": row["fixed_classes"], "novel_classes": row["novel_classes"],
                "provenance": "agent_authored" if row["size"] else "held"})
        for _ in range(3):
            a.inner.run_rules()
        for row in summary:
            at = S.node(pnodes[row["id"]])["attrs"]
            row["verdict"] = at.get("verdict")
            row["install_blocked"] = at.get("install_blocked")

    qualified = [r["id"] for r in summary if r.get("verdict") == "qualifies"]
    rep = {"bank_stream": bank_name, "turns": len(turns), "bank": bank, "bank_classes": dict(collections.Counter(b["class"] for b in bank)),
           "policy": {k: pol.get(k) for k in ("k_fix", "max_candidates", "max_size", "bank_max_quality",
                                              "propose_only")},
           "candidates": summary, "held_fixed_classes": sorted(held_classes),
           "children": {s: {k: v for k, v in r.items() if k != "traceback"} for s, r in results.items()},
           "builds": {cid: info["rows"] for cid, info in by_cand.items()},
           "a5a_met": bool(qualified), "qualified": qualified, "dry": dry, "run_root": str(run_root)}
    suffix = "" if bank_name == "p20_10_19" else f"_{bank_name}"
    out = ROOT / f"evaluation/reports/operator_authorship_a5a_v1{suffix}_n{n}{'_dry' if dry else ''}_20261010.json"
    out.write_text(json.dumps(rep, indent=1, default=str) + "\n")
    for r in summary:
        print(json.dumps({k: r.get(k) for k in ("id", "built_on", "deltas", "fixed", "fixed_classes", "harm",
                                                 "failed_children", "novel_classes", "verdict")}))
    print("A5a met:", rep["a5a_met"], qualified)


if __name__ == "__main__":
    main()

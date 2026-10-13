#!/usr/bin/env python3
"""Plan P5b: operator authorship with installation and a RELATIVE criterion.

Two held-out banks, measured together (the same family must hold on both):
  p20_10_19  persona_chat_20 dialogues 10-19 (the project's held-out stream)
  p50_20_29  persona_chat_50 dialogues 20-29 (unused before P5)
For each bank: a fresh boot (promotion off) answers N turns offline on the
production path; the bank is every turn its production ReplyQuality datum
scored at most bank_max_quality; the parent is snapshotted for the child.

ROUND 1: every candidate (domains/operator_authorship.enumerate_candidates)
builds its delta on every bank turn (one tag, so identical deltas are one
replay); every distinct delta is replayed once per bank by
scripts/convo_child_run.py (judge v2, production path) with that bank's turns
flagged.
ROUND 2 (policy.refine == 1): a candidate any of whose SOURCE rules did net
harm (its deltas' fixes minus their harm, summed over both banks, below zero)
gets a refined twin with p_exclude_sources = those sources, measured the same
way (cached replays are reused).

Per candidate, over both banks: fixed (bank turns some delta fixed), harm
(regressions + broken fixes + quality drops, summed over its replays), the
harmed turns, and -- for a refinement -- the bank turns left to an excluded
source. A FamilyProposal per candidate is minted on EACH bank's agent with
the same totals and that bank's residual turns; the frozen rules in
seeds/operator_authorship.json compute net, decide qualifies /
does_not_qualify relative to the parent held family, install the best
qualifying candidate per program, and file its residual turns as concerns.

Usage: <this> [n_turns=80] [parallel=3]
Writes evaluation/reports/operator_authorship_meta_v2_n<N>_20261010.json
(local) and prints the installed families.
"""
import collections
import concurrent.futures as cf
import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts"), str(Path(__file__).parent)]

from operator_authorship_a5a_v1 import held_out_turns, run_child   # noqa: E402

BANK_NAMES = ("p20_10_19", "p50_20_29")
TAG = "oa"


def build_bank(name, n, run_root):
    import endemic_rsi_daemon_v1 as E
    import long_session_cost_v1 as L
    from domains import operator_authorship as OA
    st = E.boot(True, promote=False)
    a = st.adapter
    S, I = a.s, a.inner
    _pn, pol = OA.policy(a)
    acc = collections.defaultdict(float)
    L.say(st, "Hello.", acc)
    for t in held_out_turns(n, name):
        L.say(st, t, acc)
    bank = []
    for m in sorted(S.nodes("Message"), key=lambda x: x.value):
        at = S.node(m)["attrs"]
        if at.get("from") != "interlocutor" or at.get("reply_quality_score") is None:
            continue
        if float(at["reply_quality_score"]) <= float(pol.get("bank_max_quality") or 0.0):
            bank.append({"turn_id": int(m.value), "text": at.get("text"),
                         "class": str(at.get("reply_quality_reason") or "")})
    snap = run_root / f"{name}_snapshot.json"
    a.save(str(snap))
    print(name, "bank", len(bank), dict(collections.Counter(b["class"] for b in bank)), flush=True)
    return {"name": name, "st": st, "agent": a, "bank": bank, "snapshot": snap,
            "ids": [b["turn_id"] for b in bank], "cls": {b["turn_id"]: b["class"] for b in bank}}


def build_rows(banks, cand, OA):
    import substrate_rs as srs
    prog = OA.candidate_program(banks[0]["agent"], cand)
    rows = {}
    for bk in banks:
        out = []
        for b in bk["bank"]:
            rep = OA.build_on_turn(bk["agent"], prog, srs.NodeID(b["turn_id"]), TAG)
            if not rep.get("built"):
                out.append({"turn_id": b["turn_id"], "built": False, "wall": rep.get("wall")})
                continue
            d = OA.delta_of(rep)
            sig = hashlib.sha1(json.dumps(d, sort_keys=True).encode()).hexdigest()[:12]
            out.append({"turn_id": b["turn_id"], "built": True, "sig": sig, "source": OA.source_of(rep),
                        "delta": d, "rules": [r.get("name") for r in d["add_rules"]]})
        rows[bk["name"]] = out
    return prog, rows


def run_jobs(jobs, cache, banks, run_root, par):
    by_name = {b["name"]: b for b in banks}
    todo = [(bn, sig, d) for (bn, sig), d in jobs.items() if (bn, sig) not in cache]

    def go(item):
        bn, sig, d = item
        bk = by_name[bn]
        delta = dict(d, skip_seeds=[], parent_shadow_read=True, parent_turn_path="production",
                     flagged_turn_ids=bk["ids"])
        return (bn, sig), run_child(bk["snapshot"], delta, run_root / bn / sig)
    with cf.ThreadPoolExecutor(max_workers=par) as ex:
        for key, res in ex.map(go, todo):
            cache[key] = res
            print("child", key, {k: res.get(k) for k in ("status", "flagged_changed", "broken_fixes",
                                                         "regressions", "quality_drops", "wall_s")}, flush=True)


def harm_of(res):
    if res.get("status") != "done":
        return None
    return int(res.get("regressions") or 0) + int(res.get("broken_fixes") or 0) + int(res.get("quality_drops") or 0)


def harm_turns_of(res):
    out = {int(t) for t, o in (res.get("flagged_outcomes") or {}).items() if o == "broken"}
    out |= {int(t) for t in res.get("regressed_turns") or []}
    out |= {int(t) for t in res.get("quality_drop_turns") or []}
    return out


def measure(cand, rows, cache, banks):
    fixed, harm, failed = {}, 0, 0
    harm_turns, src_net = {}, collections.Counter()
    for bk in banks:
        bn = bk["name"]
        sigs = {}
        for r in rows[bn]:
            if r["built"]:
                sigs.setdefault(r["sig"], r["source"])
        f, ht = set(), set()
        for sig, src in sigs.items():
            res = cache.get((bn, sig)) or {}
            h = harm_of(res)
            if h is None:
                failed += 1
                continue
            fx = {int(t) for t, o in (res.get("flagged_outcomes") or {}).items() if o == "fixed"} & set(bk["ids"])
            f |= fx
            ht |= harm_turns_of(res)
            harm += h
            src_net[src] += len(fx) - h
        fixed[bn], harm_turns[bn] = f, ht
    classes = sorted({bk["cls"][t] for bk in banks for t in fixed[bk["name"]]})
    return {"id": cand["id"], "program": cand["program"], "edits": cand["edits"], "size": cand["size"],
            "refines": cand.get("refines"), "fixed": sum(len(v) for v in fixed.values()),
            "fixed_by_bank": {k: len(v) for k, v in fixed.items()}, "fixed_turns": {k: sorted(v) for k, v in fixed.items()},
            "fixed_classes": classes, "harm": harm + failed, "failed_children": failed,
            "harm_turns": {k: sorted(v) for k, v in harm_turns.items()},
            "built_on": {k: sum(r["built"] for r in v) for k, v in rows.items()},
            "deltas": {k: len({r["sig"] for r in v if r["built"]}) for k, v in rows.items()},
            "source_net": dict(src_net)}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    n = int(args[0]) if args else 80
    par = int(args[1]) if len(args) > 1 else 3
    from domains import topic_grounding as tg

    def _offline(*_a, **_k):
        raise OSError("offline (operator authorship meta v2)")
    tg._http_get = _offline
    from domains import operator_authorship as OA
    run_root = Path(tempfile.mkdtemp(prefix="p5b-"))
    banks = [build_bank(name, n, run_root) for name in BANK_NAMES]
    a0 = banks[0]["agent"]
    _pn, pol = OA.policy(a0)
    cache, results, progs, rows_by = {}, [], {}, {}

    def evaluate(cands):
        jobs = {}
        for c in cands:
            t0 = time.time()
            progs[c["id"]], rows_by[c["id"]] = build_rows(banks, c, OA)
            for bn, rows in rows_by[c["id"]].items():
                for r in rows:
                    if r["built"]:
                        jobs[(bn, r["sig"])] = r["delta"]
            print(c["id"], {k: sum(r["built"] for r in v) for k, v in rows_by[c["id"]].items()},
                  f"{time.time() - t0:.1f}s", flush=True)
        run_jobs(jobs, cache, banks, run_root, par)
        return [measure(c, rows_by[c["id"]], cache, banks) for c in cands]

    cands = OA.enumerate_candidates(a0)
    for i, c in enumerate(cands):
        c["mdl_rank"] = i
    results = evaluate(cands)
    if int(pol.get("refine") or 0):
        seen = {c["id"] for c in cands}
        ref = []
        for c, m in zip(cands, results):
            bad = sorted(s for s, v in m["source_net"].items() if v < 0 and s)
            if bad:
                rc = OA.refined(c, bad)
                if rc["id"] not in seen:
                    rc["mdl_rank"] = len(cands) + len(ref)
                    seen.add(rc["id"])
                    ref.append(rc)
        print("refinements", [r["id"] for r in ref], flush=True)
        cands = cands + ref
        results = results + evaluate(ref)
    rank = {c["id"]: c["mdl_rank"] for c in cands}

    # residual turns of a refinement: bank turns its parent built from an excluded source and it left unfixed
    by_id = {m["id"]: m for m in results}
    for m in results:
        m["residual_turns"] = {bn: set(v) for bn, v in m["harm_turns"].items()}
        if m.get("refines"):
            excl = set(next(v for s, v in m["edits"] if s == "p_exclude_sources"))
            for bn, rows in rows_by[m["refines"]].items():
                left = {r["turn_id"] for r in rows if r["built"] and r["source"] in excl}
                m["residual_turns"][bn] |= left - set(m["fixed_turns"][bn])
        m["residual_turns"] = {bn: sorted(v) for bn, v in m["residual_turns"].items()}

    bank_set = "+".join(BANK_NAMES)
    installed = []
    for bk in banks:
        a = bk["agent"]
        nodes = {}
        for m in results:
            parent_op = OA.parent_op_of(a, m["program"])
            fam, opn = OA.authored_names(m, parent_op or "op")
            attrs = {"candidate": m["id"], "program": m["program"], "parent_op": parent_op, "edits": m["edits"],
                     "size": m["size"], "mdl_rank": rank[m["id"]], "fixed": m["fixed"], "harm": m["harm"],
                     "fixed_classes": m["fixed_classes"], "bank_set": bank_set,
                     "provenance": "agent_authored" if m["size"] else "held"}
            if m["size"]:
                attrs.update(family_name=fam, op_name=opn,
                             program_json=json.dumps(progs[m["id"]], separators=(",", ":")))
            nodes[m["id"]] = OA.mint_proposal(a, attrs, m["residual_turns"].get(bk["name"], []))
        for _ in range(4):
            a.inner.run_rules()
        S = a.s
        for m in results:
            at = S.node(nodes[m["id"]])["attrs"]
            m.setdefault("verdict_by_bank", {})[bk["name"]] = {k: at.get(k) for k in ("net", "gain", "verdict",
                                                                                     "installed", "op_name")}
        ops = [dict(S.node(n)["attrs"]) for n in S.nodes("VariationOp")
               if S.node(n)["attrs"].get("provenance") == "agent_authored"]
        residual = sum(1 for n in S.nodes("SelfConcern") if S.node(n)["attrs"].get("kind") == "family_residual")
        installed.append({"bank": bk["name"], "ops": ops, "residual_concerns": residual})

    rep = {"turns": n, "banks": {bk["name"]: {"bank": bk["bank"]} for bk in banks},
           "policy": {k: pol.get(k) for k in ("k_fix", "harm_weight", "min_gain", "max_candidates", "max_size",
                                              "refine", "propose_only")},
           "candidates": [{k: v for k, v in m.items()} for m in results],
           "children": {f"{bn}/{sig}": {k: v for k, v in r.items() if k != "traceback"} for (bn, sig), r in cache.items()},
           "builds": {cid: {bn: [{k: v for k, v in r.items() if k != "delta"} for r in rows]
                            for bn, rows in rws.items()} for cid, rws in rows_by.items()},
           "programs": {m["id"]: progs[m["id"]] for m in results if m["size"]},
           "installed": installed, "run_root": str(run_root)}
    out = ROOT / f"evaluation/reports/operator_authorship_meta_v2_n{n}_20261010.json"
    out.write_text(json.dumps(rep, indent=1, default=str) + "\n")
    for m in results:
        v = m["verdict_by_bank"][BANK_NAMES[0]]
        print(json.dumps({"id": m["id"], "fixed": m["fixed"], "harm": m["harm"], "classes": m["fixed_classes"],
                          "net": v["net"], "gain": v["gain"], "verdict": v["verdict"], "installed": v["installed"]}))
    for i in installed:
        print("installed on", i["bank"], [(o["name"], o["priority"], o["requires_kind"]) for o in i["ops"]],
              "residual concerns", i["residual_concerns"])


if __name__ == "__main__":
    main()

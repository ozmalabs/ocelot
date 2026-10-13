#!/usr/bin/env python3
"""Gate F4 (plan P4), sweep half: on real production-path turns, do the held
FamilyPrograms build the same variants as the Python builders, including
abstaining on the same concerns?

One fresh conversation boot (self-promotion off) answers N persona turns
offline on the production path (long_session_cost_v1.say). Then, for every
interlocutor turn, a concern of each ported family's kind is minted about it
(SelfConcern -> promoted_to -> StandingConcern, exactly what
jabberwock_daemon.promote_self_concern writes) and both builders run on it:
  disposition_generalise  (kind 'unanswered')     every turn
  deep_reader_correct     (kind 'comprehension')  every turn
Their delta-relevant reports (reflective_faculty.family_report_signature) are
compared. The temporary concern nodes are removed after each case.

Usage: <this> [n_turns=120] [stream=persona|held_out]
Writes evaluation/reports/family_program_parity_v1_<stream>_n<N>_20261010.json.
"""
import collections, json, os, sys
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts"), str(Path(__file__).parent)]

FAMILIES = (("disposition_generalise", "unanswered", "family_disposition_generalise"),
            ("deep_reader_correct", "comprehension", "family_deep_reader_correct"))



def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    stream = sys.argv[2] if len(sys.argv) > 2 else "held_out"
    from domains import topic_grounding as tg

    def _offline(*_a, **_k):
        raise OSError("offline (family program parity)")
    tg._http_get = _offline
    import endemic_rsi_daemon_v1 as E
    import long_session_cost_v1 as L
    import domains.reflective_faculty as rf
    if stream == "persona":
        d = json.loads((ROOT / "data/corpus/persona_chat_20.json").read_text())
        turns = [t for di in range(10) for spk, t in d[di]["turns"] if spk == "User 1"][:n]
    else:
        turns = L.turns_of(n)
    st = E.boot(True, promote=False)
    acc = collections.defaultdict(float)
    L.say(st, "Hello.", acc)
    for t in turns:
        L.say(st, t, acc)
    a = st.adapter
    S, I = a.s, a.inner
    msgs = [m for m in sorted(S.nodes("Message"), key=lambda x: x.value)
            if S.node(m)["attrs"].get("from") == "interlocutor"]
    rows = []
    remover = getattr(I, "remove_node", None) or S.remove_node
    for k, m in enumerate(msgs):
        for op, kind, prog in FAMILIES:
            key = f"parity_{op}_{k}"
            sc = S.add_node("SelfConcern", {"status": "promoted", "source": "implicit", "kind": kind,
                                            "content": f"parity probe {k}"})
            I.add_edge_unchecked(a.agent, "has_self_concern", sc)
            I.add_edge_unchecked(sc, "about_message", m)
            stc = S.add_node("StandingConcern", {"name": key, "status": "pending", "kind": kind})
            I.add_edge_unchecked(sc, "promoted_to", stc)
            tag = f"p{k}"
            py = rf._VARIATION_REGISTRY[op](a, [key], tag)
            pg = rf._compose_from_program(a, prog, [key], tag)
            sp, sg = rf.family_report_signature(py), rf.family_report_signature(pg)
            rows.append({"op": op, "turn": int(m.value), "text": S.node(m)["attrs"].get("text"),
                         "python_built": bool(py.get("built")), "program_built": bool(pg.get("built")),
                         "equal": sp == sg, "python_wall": py.get("wall"), "program_wall": pg.get("wall"),
                         **({} if sp == sg else {"python": sp, "program": sg})})
            for node in (stc, sc):
                remover(node)
    by = collections.defaultdict(lambda: collections.Counter())
    for r in rows:
        c = by[r["op"]]
        c["cases"] += 1
        c["built"] += r["python_built"]
        c["equal"] += r["equal"]
        c["equal_built"] += r["equal"] and r["python_built"]
        c["equal_abstain"] += r["equal"] and not r["python_built"]
        c["wall_text_equal"] += (r["python_wall"] == r["program_wall"])
    rep = {"stream": stream, "turns": len(turns), "messages": len(msgs),
           "by_family": {k: dict(v) for k, v in by.items()},
           "all_equal": all(r["equal"] for r in rows),
           "mismatches": [r for r in rows if not r["equal"]][:20]}
    out = ROOT / f"evaluation/reports/family_program_parity_v1_{stream}_n{n}_20261010.json"
    out.write_text(json.dumps(rep, indent=1) + "\n")
    print(json.dumps({k: v for k, v in rep.items() if k != "mismatches"}, indent=1))
    for r in rep["mismatches"][:5]:
        print(json.dumps(r)[:1500])


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Gate S2a (plan P2): do filed reply_quality concerns point at turns labelled
inappropriate?

One fresh conversation boot (self-promotion off) answers the held-out turns
(persona_chat_20 dialogues 10-19, both seats: long_session_cost_v1.turns_of,
the same turns the Q0 label sheet was built from) on the production path.
Every reply_quality SelfConcern seeds/reply_feedback_gap.json files is read
back with its class: the concern's own turn (about_message) and every member
of its TurnShape. Each (inbound, reply) pair is looked up in the label sheet
(evaluation/labels/reply_quality_heldout_v1.csv, labels 0/1/2; a pair the
sheet does not hold is reported as unmatched, not guessed).

Gate: precision of 'inappropriate' (label 0) over matched concern turns >= 0.7.
Usage: <this> [n_turns=200]
Writes evaluation/reports/reply_feedback_s2_v1_20261010.json.
"""
import collections, csv, json, os, sys
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts"), str(Path(__file__).parent)]
CSV = ROOT / "evaluation/labels/reply_quality_heldout_v1.csv"
OUT = ROOT / "evaluation/reports/reply_feedback_s2_v1_20261010.json"


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    from domains import topic_grounding as tg

    def _offline(*_a, **_k):
        raise OSError("offline (reply_feedback S2)")
    tg._http_get = _offline
    import endemic_rsi_daemon_v1 as E
    import long_session_cost_v1 as L
    labels = {}
    for row in csv.DictReader(CSV.open()):
        if row.get("label", "").strip() in ("0", "1", "2"):
            reply = "" if row["reply"] == "(no reply)" else row["reply"]
            labels[(row["inbound"].strip(), reply.strip())] = int(row["label"])
    turns = L.turns_of(n)
    st = E.boot(True, promote=False)
    acc = collections.defaultdict(float)
    L.say(st, "Hello.", acc)
    for t in turns:
        L.say(st, t, acc)
    a = st.adapter
    S, I = a.s, a.inner

    def pair(m):
        at = S.node(m)["attrs"]
        return (str(at.get("text") or "").strip(), str(at.get("comp_reply_text") or "").strip())

    concerns = []
    counted = {}
    for sc in S.nodes("SelfConcern"):
        sat = S.node(sc)["attrs"]
        if sat.get("kind") != "reply_quality":
            continue
        about = [m for m in I.neighbours(sc, "about_message") if S.has_node(m)]
        members = []
        for sh in S.nodes("TurnShape"):
            sha = S.node(sh)["attrs"]
            if (sha.get("shape_kind") == "reply_feedback" and sha.get("sig_signal") == sat.get("sig_signal")
                    and sha.get("sig_reason") == sat.get("sig_reason")):
                members = [m for m in I.neighbours(sh, "has_member") if S.has_node(m)]
        rows = []
        for m in members or about:
            p = pair(m)
            lab = labels.get(p)
            rows.append({"turn": int(m.value), "inbound": p[0], "reply": p[1], "label": lab,
                         "about": m in about, "outcome": S.node(m)["attrs"].get("turn_outcome")})
            if lab is not None:
                counted[int(m.value)] = lab
        concerns.append({"signal": sat.get("sig_signal"), "reason": sat.get("sig_reason"),
                         "content": sat.get("content"), "turns": rows})
    about_labels = [r["label"] for c in concerns for r in c["turns"] if r["about"] and r["label"] is not None]
    member_labels = list(counted.values())

    def prec(xs):
        return round(sum(1 for x in xs if x == 0) / len(xs), 4) if xs else None
    rep = {"turns": len(turns), "concerns": len(concerns),
           "by_signal": dict(collections.Counter(c["signal"] for c in concerns)),
           "about_turns_matched": len(about_labels), "precision_about": prec(about_labels),
           "member_turns_matched": len(member_labels), "precision_members": prec(member_labels),
           "member_label_counts": dict(collections.Counter(member_labels)),
           "unmatched_member_turns": sum(1 for c in concerns for r in c["turns"] if r["label"] is None),
           "non_error_concerns": sum(1 for c in concerns if any(
               r["about"] and r["outcome"] != "explicit_error" and r["reply"] for r in c["turns"])),
           "gate": {"S2a_precision_ge_0.7": (prec(member_labels) or 0) >= 0.7},
           "concern_detail": concerns}
    OUT.write_text(json.dumps(rep, indent=1) + "\n")
    print(json.dumps({k: v for k, v in rep.items() if k != "concern_detail"}, indent=1))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build the held-out human-labelling set for ReplyQuality gate Q0 (plan P0).

Held-out turns: persona_chat_20 dialogues 10-19 (the production stream uses
User 1 of dialogues 0-9). Each dialogue is played from each speaker's seat
(the agent answers that speaker's turns), each on its own FRESH conversation
boot -- one long session is impractical: measured, per-turn time grows from
0.5 s to 75 s over 200 turns on one agent (reported separately) -- on two
agent configurations:

  * `fresh`    -- the conversation profile, self-promotion off;
  * `improved` -- the same, plus the rule changes the agent itself ADOPTED in
                  a 120-turn production stream with self-improvement on (the
                  tranche-24 configuration): its adopted rules are exported
                  once and installed, its removed rules removed, in every
                  boot. This isolates the effect of the adoptions.

Unique (inbound, reply) pairs are written, in a stable shuffled order, to
  evaluation/labels/reply_quality_heldout_v1.csv   -- for the human labeller:
      id, dialogue, context (previous two turns), inbound, reply,
      reference_next (what the real other speaker said), label (blank)
  evaluation/labels/reply_quality_heldout_v1.meta.json -- machine side.
The labeller never sees the machine score.

Label: 2 appropriate (a reasonable conversational reply to this turn),
1 acceptable-minimal (honest but thin: a bare acknowledgement of a statement,
a clarification request, an honest 'I can't'), 0 inappropriate (error, no
reply, a non-answer to a question, a misread such as taking a statement as a
goal, an off-topic definition).
"""
import csv, json, os, random, sys, time
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts"), str(Path(__file__).parent)]
OUT_CSV = ROOT / "evaluation/labels/reply_quality_heldout_v1.csv"
OUT_META = ROOT / "evaluation/labels/reply_quality_heldout_v1.meta.json"
HELD_OUT = range(10, 20)


def adopted_change(E):
    """Run the production stream with self-improvement on; return the rules it
    adopted (JSON) and the names it removed."""
    st = E.boot(True)
    E.say(st, "Hello.")
    for t in E.stream_turns("persona", 120):
        E.say(st, t)
        E.settle(st)
    s, inner = st.adapter.s, st.adapter.inner
    added, removed = set(), set()
    for n in s.nodes("Adoption"):
        at = s.node(n)["attrs"]
        if at.get("reverted"):
            continue
        added |= {x for x in str(at.get("rule_added") or "").split(",") if x}
        removed |= {x for x in str(at.get("rule_removed") or "").split(",") if x}
    live = [r for r in inner.export_rules() if isinstance(r, dict) and r.get("active", True)]
    rules = []
    for r in live:
        if r.get("name") in added:
            r = dict(r)
            r.pop("active", None)
            rules.append(r)
    return rules, sorted(removed), sorted(added)


def boot_with(E, rules, removed):
    st = E.boot(True, promote=False)
    inner = st.adapter.inner
    if removed:
        exported = inner.export_rules()
        for idx in sorted((i for i, r in enumerate(exported)
                           if isinstance(r, dict) and r.get("active", True) and r.get("name") in removed),
                          reverse=True):
            inner.remove_rule(idx)
    for r in rules:
        inner.add_rule(r)
    return st


def play(E, dialogues, rules, removed, tag):
    out = []
    t0 = time.time()
    for di in HELD_OUT:
        turns = dialogues[di]["turns"]
        for seat in ("User 1", "User 2"):
            st = boot_with(E, rules, removed)
            E.say(st, "Hello.")
            for k, (spk, text) in enumerate(turns):
                if spk != seat:
                    continue
                t1 = time.time()
                reply = E.say(st, text, max_cycles=15)[1] or ""
                ctx = " / ".join(f"{s}: {t}" for s, t in turns[max(0, k - 2):k])
                nxt = turns[k + 1][1] if k + 1 < len(turns) else ""
                out.append({"dialogue": di, "seat": seat, "turn": k, "context": ctx, "inbound": text,
                            "reply": reply.strip(), "reference_next": nxt})
                print(json.dumps({"tag": tag, "n": len(out), "d": di, "seat": seat, "k": k,
                                  "s": round(time.time() - t1, 1), "total": round(time.time() - t0)}), flush=True)
            del st
    return out


def main():
    if OUT_CSV.exists():
        raise SystemExit("refusing to overwrite")
    import endemic_rsi_daemon_v1 as E
    from domains import reply_quality as rq
    dialogues = json.loads((ROOT / "data/corpus/persona_chat_20.json").read_text())
    t0 = time.time()
    rules, removed, added = adopted_change(E)
    print("adopted", added, "removed", removed, round(time.time() - t0), flush=True)
    rows_fresh = play(E, dialogues, [], [], "fresh")
    rows_improved = play(E, dialogues, rules, removed, "improved")
    pairs = {}
    for agent, rows in (("fresh", rows_fresh), ("improved", rows_improved)):
        for r in rows:
            key = (r["dialogue"], r["seat"], r["turn"], r["reply"])
            item = pairs.setdefault(key, dict(r, agents=[]))
            item["agents"].append(agent)
    items = list(pairs.values())
    random.Random(20261010).shuffle(items)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    meta = {"schema": "ReplyQualityLabelSetV1", "held_out_dialogues": list(HELD_OUT),
            "criteria_version": rq.criteria()["version"], "improved_adopted_rules": added,
            "improved_removed_rules": removed, "elapsed_s": round(time.time() - t0, 1), "items": {}}
    with OUT_CSV.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "dialogue", "context", "inbound", "reply", "reference_next", "label"])
        for n, it in enumerate(items):
            iid = f"rq{n:04d}"
            w.writerow([iid, it["dialogue"], it["context"], it["inbound"], it["reply"] or "(no reply)",
                        it["reference_next"], ""])
            meta["items"][iid] = {"agents": it["agents"], "seat": it["seat"], "turn": it["turn"],
                                  "machine": rq.assess(it["inbound"], it["reply"])}
    OUT_META.write_text(json.dumps(meta, indent=1) + "\n")
    print("wrote", len(items), "items;", OUT_CSV, flush=True)


if __name__ == "__main__":
    main()

"""T3f O-B: conversation-tracking ACCURACY against human annotation.

Streams the AMI test-split meetings (CC-BY-4.0) through /v1/conversations
(ClassifierService, in-process) and scores the wire's `responds_to` / `answers`
against the AMI ADJACENCY-PAIR annotation (ami_annotations, CC-BY-4.0), next to
a naive adjacency baseline. Prints AGGREGATE COUNTS ONLY -- never text, never ids.

    PYTHONPATH=.:runners/dsl/python OZMA_NO_LLM=1 python3 scripts/equilibrium_tracking_eval.py \
        [SEGMENTS_DIR] [ANNOTATIONS_DIR]

Alignment: a dialogue act (speaker_id, start, end) maps to the segment of the
SAME speaker with the largest time overlap (none -> unaligned, counted). A gold
pair is an adjacency pair whose source and target align to DIFFERENT segments:
(target_segment responds to source_segment). Pairs whose source dialogue act is
an elicitation (`el.*`) are the gold question/answer pairs.

AP annotation is SPARSE (annotators mark salient pairs, not every response), so
`precision_on_gold_targets` only scores predictions made on turns that are the
target of at least one gold pair; recall is the primary number. Meetings without
annotation are skipped (counted). Measurement only: nothing is fed back.

Baseline ("adjacent"): every turn responds to the closest earlier turn by a
different speaker; a turn answers that turn when it is a gold elicitation's
segment (an ORACLE question detector -- favoured, not handicapped);
"base_answers_ocelot_questions" uses Ocelot's own speech_act=question instead.
"""
from __future__ import annotations

import glob
import json
import os
import sys
from collections import defaultdict

os.environ.setdefault("OZMA_NO_LLM", "1")

_DEF = "/applications/data/discord_data/testingdata/hf_samples"


def _align(das, segs_by_speaker):
    """da_id -> segment index (largest same-speaker overlap), unaligned omitted."""
    out = {}
    for d in das:
        best, best_ov = None, 0.0
        for i, b, e in segs_by_speaker.get(d["speaker_id"], ()):
            ov = min(e, d["end"]) - max(b, d["start"])
            if ov > best_ov:
                best, best_ov = i, ov
        if best is not None:
            out[d["da_id"]] = best
    return out


def _score(pred, gold):
    """pred, gold: dict target -> set(sources). Returns hit counts."""
    hits = sum(len(pred.get(t, set()) & s) for t, s in gold.items())
    n_gold = sum(len(s) for s in gold.values())
    on_targets = sum(len(pred.get(t, set())) for t in gold)
    return hits, n_gold, on_targets


def _ratio(a, b):
    return round(a / b, 4) if b else None


def main(seg_dir: str, ann_dir: str) -> None:
    from services.equilibrium_classifier import server
    svc = server.ClassifierService(max_conversations=4)
    agg = defaultdict(int)
    tot = {k: [0, 0, 0] for k in ("ocelot_responds", "base_responds", "ocelot_answers", "base_answers",
                                  "ocelot_responds_qa", "base_answers_ocelot_questions")}
    for f in sorted(glob.glob(os.path.join(seg_dir, "*.jsonl"))):
        mid = os.path.basename(f)[:-len(".jsonl")]
        af = os.path.join(ann_dir, mid + ".jsonl")
        if not os.path.exists(af):
            agg["meetings_unannotated"] += 1
            continue
        with open(af, encoding="utf-8") as fh:
            ann = [json.loads(line) for line in fh]
        das = [a for a in ann if a.get("kind") == "da"]
        aps = [a for a in ann if a.get("kind") == "ap"]
        if not das or not aps:
            agg["meetings_unannotated"] += 1
            continue
        with open(f, encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh]
        rows.sort(key=lambda r: (r["begin_time"], r["end_time"]))
        by_spk = defaultdict(list)
        for i, r in enumerate(rows):
            by_spk[str(r["speaker_id"])].append((i, float(r["begin_time"]), float(r["end_time"])))
        da_seg = _align(das, by_spk)
        da_type = {d["da_id"]: d.get("da_type") or "" for d in das}
        agg["das"] += len(das)
        agg["das_unaligned"] += len(das) - len(da_seg)
        gold, gold_qa, q_segs = defaultdict(set), defaultdict(set), set()
        for ap in aps:
            s, t = da_seg.get(ap["source"]), da_seg.get(ap["target"])
            agg["aps"] += 1
            if s is None or t is None:
                agg["aps_unaligned"] += 1
                continue
            if s == t:
                agg["aps_same_segment"] += 1
                continue
            gold[t].add(s)
            if da_type.get(ap["source"], "").startswith("el."):
                gold_qa[t].add(s)
                q_segs.add(s)
        for d, i in da_seg.items():
            if da_type[d].startswith("el."):
                q_segs.add(i)

        # ---- Ocelot over the wire shape ------------------------------------
        turns = [{"id": f"s{i:05d}", "actor_ref": str(r["speaker_id"]), "text": str(r["text"]),
                  "ts_ms": round(float(r["begin_time"]) * 1000)} for i, r in enumerate(rows)]
        cid = f"ami-eval:{agg['meetings']}"
        resp, ans, o_q = defaultdict(set), defaultdict(set), set()
        for k in range(0, len(turns), 100):
            out = svc.conversation_turns(cid, "meeting", turns[k:k + 100])
            for t in out["turns"]:
                me = int(t["id"][1:])
                resp[me] |= {int(x[1:]) for x in t["responds_to"]}
                ans[me] |= {int(x[1:]) for x in t["answers"]}
                if t["labels"].get("speech_act") == "question":
                    o_q.add(me)
        svc.conversation_close(cid)

        # ---- adjacency baseline (oracle question detector) ------------------
        b_resp, b_ans, bo_ans = defaultdict(set), defaultdict(set), defaultdict(set)
        for i in range(1, len(rows)):
            j = i - 1
            while j >= 0 and rows[j]["speaker_id"] == rows[i]["speaker_id"]:
                j -= 1
            if j >= 0:
                b_resp[i].add(j)
                if j in q_segs:
                    b_ans[i].add(j)
                if j in o_q:
                    bo_ans[i].add(j)

        for key, p, g in (("ocelot_responds", resp, gold), ("base_responds", b_resp, gold),
                          ("ocelot_answers", ans, gold_qa), ("base_answers", b_ans, gold_qa),
                          ("base_answers_ocelot_questions", bo_ans, gold_qa),
                          ("ocelot_responds_qa", resp, gold_qa)):
            for n, v in enumerate(_score(p, g)):
                tot[key][n] += v
        agg["meetings"] += 1
        agg["turns"] += len(rows)
        agg["gold_pairs"] += sum(len(s) for s in gold.values())
        agg["gold_qa_pairs"] += sum(len(s) for s in gold_qa.values())
        agg["ocelot_responds_edges"] += sum(len(s) for s in resp.values())
        agg["ocelot_answer_edges"] += sum(len(s) for s in ans.values())
        agg["base_responds_edges"] += sum(len(s) for s in b_resp.values())
    res = {}
    for key, (hits, n_gold, on_t) in tot.items():
        res[key] = {"hits": hits, "gold": n_gold, "recall": _ratio(hits, n_gold),
                    "predictions_on_gold_targets": on_t,
                    "precision_on_gold_targets": _ratio(hits, on_t)}
    print(json.dumps({"corpus": "AMI test split + AMI adjacency pairs (CC-BY-4.0), aggregate counts only",
                      **agg, "scores": res}, indent=1))


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0] if a else os.path.join(_DEF, "ami_meetings/test"),
         a[1] if len(a) > 1 else os.path.join(_DEF, "ami_annotations"))

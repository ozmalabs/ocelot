"""T3f O-B: conversation-tracking ACCURACY against human annotation.

Streams the AMI test-split meetings (CC-BY-4.0) through /v1/conversations
(ClassifierService, in-process) and scores the wire's `responds_to` / `answers`
against the AMI ADJACENCY-PAIR annotation (ami_annotations, CC-BY-4.0), next to
a naive adjacency baseline. Prints AGGREGATE COUNTS ONLY -- never text, never ids.

    PYTHONPATH=.:runners/dsl/python OZMA_NO_LLM=1 python3 scripts/equilibrium_tracking_eval.py \
        [--split validation|test] [--segments-dir DIR] [--annotations-dir DIR] [--batch N]

T3h: develop on --split validation (18 AMI meetings, 13 annotated); evaluate on test ONCE.

Alignment: a dialogue act (speaker_id, start, end) maps to the segment of the
SAME speaker with the largest time overlap (none -> unaligned, counted). A gold
pair is an adjacency pair whose source and target align to DIFFERENT segments:
(target_segment responds to source_segment). Pairs whose source dialogue act is
an elicitation (`el.*`) are the gold question/answer pairs.

AP annotation is SPARSE (annotators mark salient pairs, not every response), so
`precision_on_gold_targets` only scores predictions made on turns that are the
target of at least one gold pair; recall is the primary number. Meetings without
annotation are skipped (counted). Measurement only: nothing is fed back.

eq-tax-0.8.0 (T3g, held-open collapse): the per-turn structure is the FOLD of the first
emission and every later `turns_delta` (incl. /close), i.e. the final structure. Reported
in addition: collapsed-edge recall / precision per confidence (strong / weak / declared),
the basis / confidence distribution, the held share of turns, held-set coverage (gold
pairs whose target turn is held and whose source is among its candidates), candidate
recall over all turns (gold source among the target's candidates: the candidate
generator's ceiling), and the candidate-count distribution.
AMBIGUITY (a reply chain unclear to Ocelot may be unclear to the participants too): the
gold-target rate per final basis (share of turns of that basis that annotators made the
target of any adjacency pair -- if held marks genuine ambiguity, annotators mark it less)
and what became of turns first emitted held (collapsed later by uptake, i.e. the
participants themselves resolved it, vs left held), the precision of those late
resolutions on gold targets, and the count of questions that left their QUD-top pointer
while still open (superseded by a newer question; `w -eq_qud_lapsed-> q`, read from the
retained fork before close).

eq-tax-0.8.0 AMENDMENT A (questions open TOPICS): the share of turns with a decided topic
(topic_id set) / a held topic (topic_id null, >= 2 topic candidates) / no topic; for gold
pairs whose source dialogue act is an elicitation (el.*), TOPIC RECALL: the share where
the target turn's topic_id is the source segment, and where the source segment is among
its topic candidates; and the ENGAGED share of Ocelot's question turns (a decided-topic
free-form contribution by another actor: `q -eq_engaged_by-> c`, read from the retained
fork before close), next to the share answered at reply level.

T3h additions (all aggregate): held DIAGNOSTICS -- the cue-set PATTERN of every first-held
and still-held turn (codebook strings only), the uptake path (does a later turn by a
candidate's author follow; did the held turn's author speak again first; does that turn
collapse onto / list the held turn), the authorship relation of held candidates (one
author in one run / several runs / distinct authors), and the gold source's cue set on held
gold targets; HELD RESOLUTION in any batch (`w -eq_trk_resolved-> p`, a graph read-out:
first emission hides resolutions inside the turn's own batch); QUESTION LABELS vs AMI
elicitations (segment contains an el.* DA: precision / recall of speech_act=question);
ADDRESSEES vs the AMI addressee annotation (DA `addressee_ids`; individual vs group
address, exact-set share, pair recall / precision, next to the adjacent-author baseline).

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


def main(seg_dir: str, ann_dir: str, batch: int = 100) -> None:
    from domains.equilibrium_classify import _lookup, _native
    from services.equilibrium_classifier import server
    global BACKCHANNEL, CLOSING_THIRD, _WORD
    from domains.equilibrium_classify import _WORD
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
    from _equilibrium_quanta_rules import BACKCHANNEL, CLOSING_THIRD
    svc = server.ClassifierService(max_conversations=4)
    agg = defaultdict(int)
    tot = {k: [0, 0, 0] for k in ("ocelot_responds", "base_responds", "ocelot_answers", "base_answers",
                                  "ocelot_responds_qa", "base_answers_ocelot_questions",
                                  "ocelot_responds_strong", "ocelot_responds_weak", "ocelot_responds_declared",
                                  "ocelot_candidates_any", "ocelot_held_candidates")}
    cdist = defaultdict(int)
    amb = defaultdict(lambda: [0, 0])  # basis -> [turns, turns that are a gold target]
    held_gold = [0, 0]  # gold pairs whose target is held: total, source among the candidates
    topic_qa = [0, 0, 0]  # gold el.* pairs: total, target topic_id == source, source among topic candidates
    topic_qa_q = [0, 0, 0]  # the same over gold el.* pairs whose source Ocelot labels a question
    adr = defaultdict(int)  # addressee evaluation (aggregate)
    pat_first, pat_final, hdiag, gold_pick = defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int)
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
        el_segs = set()
        for d, i in da_seg.items():
            if da_type[d].startswith("el."):
                q_segs.add(i)
                el_segs.add(i)

        # ---- Ocelot over the wire shape ------------------------------------
        turns = [{"id": f"s{i:05d}", "actor_ref": str(r["speaker_id"]), "text": str(r["text"]),
                  "ts_ms": round(float(r["begin_time"]) * 1000)} for i, r in enumerate(rows)]
        cid = f"ami-eval:{agg['meetings']}"
        st, o_q, first_held = {}, set(), set()  # folded structure (first emission, then turns_delta)
        first = {}  # first emission (for the held diagnostics)
        for k in range(0, len(turns), batch):
            out = svc.conversation_turns(cid, "meeting", turns[k:k + batch])
            for t in out["turns"]:
                st[int(t["id"][1:])] = t
                first[int(t["id"][1:])] = t
                if t["basis"] == "held":
                    first_held.add(int(t["id"][1:]))
                if t["labels"].get("speech_act") == "question":
                    o_q.add(int(t["id"][1:]))
            for d in out["turns_delta"]:
                st[int(d["id"][1:])] = d
                agg["turns_delta_entries"] += 1
        # question labels vs AMI elicitation dialogue acts (segment contains an el.* DA)
        agg["question_label_tp"] += len(o_q & el_segs)
        agg["question_label_fp"] += len(o_q - el_segs)
        agg["question_label_fn"] += len(el_segs - o_q)
        sess = svc.sessions[cid]  # lapsed (superseded while open) questions: graph read-out
        nat = _native(sess.branch)
        agg["questions_lapsed"] += len(nat.neighbours(sess.state.w, "eq_qud_lapsed"))
        # held turns resolved later in ANY batch (incl. their own: invisible in first emission)
        resolved = {int(nat.node(x)["attrs"]["eq_ref"][1:]) for x in nat.neighbours(sess.state.w, "eq_trk_resolved")}
        # Amendment A engagement (graph read-out; not a wire field): per Ocelot question turn
        for qi in o_q:
            qn = _lookup(nat, "Message", "eq_ref", f"s{qi:05d}")
            agg["questions"] += 1
            agg["questions_engaged"] += bool(nat.neighbours(qn, "eq_engaged_by"))
            agg["questions_answered"] += bool(nat.in_neighbours(qn, "eq_answers"))
            agg["questions_engaged_not_answered"] += bool(nat.neighbours(qn, "eq_engaged_by")) and not \
                nat.in_neighbours(qn, "eq_answers")
        for d in svc.conversation_close(cid)["turns_delta"]:
            st[int(d["id"][1:])] = d
            agg["close_turns_delta_entries"] += 1

        def ix(refs):
            return {int(x[1:]) for x in refs}
        resp = defaultdict(set, {me: ix(t["responds_to"]) for me, t in st.items()})
        ans = defaultdict(set, {me: ix(t["answers"]) for me, t in st.items()})
        cand = defaultdict(set, {me: ix(c["ref"] for c in t["candidates"]) for me, t in st.items()})
        by_conf = {c: defaultdict(set, {me: resp[me] for me, t in st.items() if t["confidence"] == c})
                   for c in ("strong", "weak", "declared")}
        held = {me for me, t in st.items() if t["basis"] == "held"}
        for t in st.values():
            agg["topic_decided" if t["topic_id"] is not None else
                "topic_held" if t["topic_candidates"] else "topic_none"] += 1
            agg["topic_candidates_total"] += len(t["topic_candidates"])
            agg["topic_candidates_max"] = max(agg["topic_candidates_max"], len(t["topic_candidates"]))
            agg[f"basis_{t['basis']}"] += 1
            agg[f"confidence_{t['confidence'] or 'null'}"] += 1
            cdist[len(t["candidates"])] += 1
        held_cov = defaultdict(set, {me: cand[me] for me in held})
        for me, t in st.items():
            amb[t["basis"]][0] += 1
            amb[t["basis"]][1] += me in gold
        agg["first_emitted_held"] += len(first_held)
        agg["first_held_collapsed_by_uptake"] += len(first_held - held)
        late = first_held - held  # first emitted held, collapsed later (uptake)
        agg["held_at_own_step_resolved_later"] += len(resolved)
        agg["held_at_own_step"] += len(resolved) + len(held)
        agg["resolved_on_gold_targets"] += len(resolved & set(gold))
        agg["resolved_gold_hits"] += sum(1 for me in resolved & set(gold) if resp[me] & gold[me])
        # taken up but still undecidable: a held turn whose candidates carry `uptake`
        agg["held_with_uptake_cue"] += sum(1 for me in held if any(
            "uptake" in c["cues"] for c in st[me]["candidates"]))
        agg["late_resolved_on_gold_targets"] += len(late & set(gold))
        agg["late_resolved_gold_hits"] += sum(1 for me in late & set(gold) if resp[me] & gold[me])
        agg["late_resolved_gold_qa_targets"] += len(late & set(gold_qa))
        agg["late_resolved_gold_qa_hits"] += sum(1 for me in late & set(gold_qa) if resp[me] & gold_qa[me])
        # ---- held diagnostics (aggregate cue-set PATTERNS and the uptake path) ----
        spk = [str(r["speaker_id"]) for r in rows]
        words = [_WORD.findall(str(r["text"]).lower().replace("\u2019", "'")) for r in rows]
        bc = [bool(w) and all(x in BACKCHANNEL for x in w) for w in words]
        ct = [bool(w) and all(x in CLOSING_THIRD for x in w) for w in words]
        refix = {f"s{i:05d}": i for i in range(len(rows))}

        def pattern(t):
            return " | ".join(sorted("{" + ",".join(sorted(c["cues"])) + "}" for c in t["candidates"]))
        for p in sorted(first_held):
            pat_first[pattern(first[p])] += 1
            if p in held:
                pat_final[pattern(st[p])] += 1
                cix = sorted(refix[c["ref"]] for c in st[p]["candidates"])
                ca = [spk[i] for i in cix]
                rel = ("one_author" if len(set(ca)) == 1 else
                       "distinct_authors" if len(set(ca)) == len(ca) else "mixed_authors")
                if rel == "one_author":  # one uninterrupted run of that author (multi-unit turn)?
                    rel += "_one_run" if all(spk[i] == ca[0] for i in range(cix[0], cix[-1] + 1)) else "_runs"
                hdiag["held_rel_" + rel] += 1
                hdiag["held_rel_" + rel + "_with_backchannel_candidate"] += any(bc[i] for i in cix)
                if p in gold:  # which candidate (by cue set) annotators chose: diagnostic only
                    for c in st[p]["candidates"]:
                        if refix[c["ref"]] in gold[p]:
                            gold_pick["{" + ",".join(sorted(c["cues"])) + "} in " + pattern(st[p])] += 1
                    if not cand[p] & gold[p]:
                        gold_pick["(gold source not a candidate) " + pattern(st[p])] += 1
            authors = {spk[refix[c["ref"]]] for c in first[p]["candidates"]}
            if p + 1 < len(rows) and spk[p + 1] in authors and ct[p + 1]:
                hdiag["next_turn_is_closing_third_by_a_candidate_author"] += 1
                if any(spk[refix[c["ref"]]] == spk[p + 1] and "open_question" in c["cues"]
                       for c in first[p]["candidates"]):
                    hdiag["  ...whose candidate carries open_question"] += 1
            j = next((j for j in range(p + 1, len(rows)) if spk[j] in authors), None)
            if j is None:
                hdiag["no_later_turn_by_a_candidate_author"] += 1
                continue
            hdiag["later_turn_by_a_candidate_author"] += 1
            if any(spk[i] == spk[p] for i in range(p + 1, j)):
                hdiag["held_author_spoke_again_first (frozen before uptake)"] += 1
            fj = first[j]
            refs = {c["ref"] for c in fj["candidates"]}
            pid = f"s{p:05d}"
            if pid in fj["responds_to"]:
                hdiag["that_turn_collapses_onto_held"] += 1
            elif pid in refs:
                hdiag["that_turn_held_with_held_among_candidates"] += 1
            else:
                hdiag["that_turn_does_not_list_held_turn"] += 1
                hdiag["  ...its_basis_" + fj["basis"]] += 1

        # ---- addressees vs AMI addressee annotation (DA `addressee_ids`) ----------
        # gold per segment: the union of its DAs' annotated addressees (AMI marks group
        # address as every other participant); only segments with >= 1 annotated DA count
        g_addr = defaultdict(set)
        agg["meetings_addressee_annotated"] += any(d.get("addressee_ids") for d in das)
        for d in das:
            if d.get("addressee_ids") and d["da_id"] in da_seg:
                g_addr[da_seg[d["da_id"]]].update(str(x) for x in d["addressee_ids"])
        for i, gs in g_addr.items():
            ps = set(st[i]["addressees"]) if i in st else set()
            kind = "individual" if len(gs) == 1 else "group"
            adr[f"{kind}_turns"] += 1
            adr[f"{kind}_predicted_nonempty"] += bool(ps)
            adr[f"{kind}_exact"] += ps == gs
            adr[f"{kind}_pair_hits"] += len(ps & gs)
            adr[f"{kind}_pair_gold"] += len(gs)
            adr[f"{kind}_pair_pred"] += len(ps)
            if ps and len(ps) == 1 and kind == "group":
                adr["group_predicted_single"] += 1
        # baseline: the adjacent other-speaker turn's author is the addressee
        for i, gs in g_addr.items():
            j = i - 1
            while j >= 0 and spk[j] == spk[i]:
                j -= 1
            kind = "individual" if len(gs) == 1 else "group"
            adr[f"{kind}_baseline_pair_hits"] += j >= 0 and spk[j] in gs
            adr[f"{kind}_baseline_pair_pred"] += j >= 0
            adr[f"{kind}_baseline_exact"] += j >= 0 and {spk[j]} == gs

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
                          ("ocelot_responds_qa", resp, gold_qa),
                          ("ocelot_responds_strong", by_conf["strong"], gold),
                          ("ocelot_responds_weak", by_conf["weak"], gold),
                          ("ocelot_responds_declared", by_conf["declared"], gold),
                          ("ocelot_candidates_any", cand, gold), ("ocelot_held_candidates", held_cov, gold)):
            for n, v in enumerate(_score(p, g)):
                tot[key][n] += v
        for t, srcs in gold_qa.items():
            tid = st[t]["topic_id"] if t in st else None
            tcs = {int(c["ref"][1:]) for c in st[t]["topic_candidates"]} if t in st else set()
            topic_qa[0] += len(srcs)
            topic_qa[1] += sum(1 for x in srcs if tid is not None and int(tid[1:]) == x)
            topic_qa[2] += len(srcs & tcs)
            qsrc = srcs & o_q  # only a question turn can open a topic: the detector's ceiling
            topic_qa_q[0] += len(qsrc)
            topic_qa_q[1] += sum(1 for x in qsrc if tid is not None and int(tid[1:]) == x)
            topic_qa_q[2] += len(qsrc & tcs)
        for t, srcs in gold.items():
            if t in held:
                held_gold[0] += len(srcs)
                held_gold[1] += len(srcs & cand[t])
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
    n_turns = agg["turns"]
    held_stats = {"held_share_of_turns": _ratio(agg["basis_held"], n_turns),
                  "gold_pairs_on_held_targets": held_gold[0],
                  "held_set_coverage": _ratio(held_gold[1], held_gold[0]),
                  "candidate_count_distribution": {str(k): cdist[k] for k in sorted(cdist)},
                  "mean_candidates": _ratio(sum(k * v for k, v in cdist.items()), n_turns),
                  "gold_target_rate_by_basis": {b: _ratio(g, n) for b, (n, g) in sorted(amb.items())},
                  "first_held_resolved_by_uptake_share": _ratio(agg["first_held_collapsed_by_uptake"],
                                                                agg["first_emitted_held"]),
                  # of the late-resolved turns that annotators made a gold target: share whose
                  # late parent is a gold source (precision of the late resolution)
                  "late_resolution_precision_on_gold_targets": _ratio(agg["late_resolved_gold_hits"],
                                                                      agg["late_resolved_on_gold_targets"]),
                  "late_resolution_precision_on_gold_qa_targets": _ratio(agg["late_resolved_gold_qa_hits"],
                                                                         agg["late_resolved_gold_qa_targets"]),
                  "held_with_uptake_cue": agg["held_with_uptake_cue"],
                  "held_at_own_step_resolved_later_share": _ratio(agg["held_at_own_step_resolved_later"],
                                                                  agg["held_at_own_step"]),
                  "resolved_precision_on_gold_targets": _ratio(agg["resolved_gold_hits"],
                                                               agg["resolved_on_gold_targets"]),
                  "questions_lapsed": agg["questions_lapsed"],
                  "first_held_cue_patterns": dict(sorted(pat_first.items(), key=lambda kv: -kv[1])),
                  "still_held_cue_patterns": dict(sorted(pat_final.items(), key=lambda kv: -kv[1])),
                  "uptake_path": dict(hdiag),
                  "gold_source_cue_set_on_held_targets": dict(sorted(gold_pick.items(), key=lambda kv: -kv[1]))}
    topic_stats = {"decided_share_of_turns": _ratio(agg["topic_decided"], n_turns),
                   "held_share_of_turns": _ratio(agg["topic_held"], n_turns),
                   "none_share_of_turns": _ratio(agg["topic_none"], n_turns),
                   "mean_topic_candidates": _ratio(agg["topic_candidates_total"], n_turns),
                   "max_topic_candidates": agg["topic_candidates_max"],
                   "gold_qa_pairs": topic_qa[0],
                   "topic_recall_topic_id": _ratio(topic_qa[1], topic_qa[0]),
                   "topic_recall_candidates": _ratio(topic_qa[2], topic_qa[0]),
                   "gold_qa_pairs_source_ocelot_question": topic_qa_q[0],
                   "topic_recall_topic_id_on_ocelot_questions": _ratio(topic_qa_q[1], topic_qa_q[0]),
                   "topic_recall_candidates_on_ocelot_questions": _ratio(topic_qa_q[2], topic_qa_q[0]),
                   "questions": agg["questions"],
                   "engaged_question_share": _ratio(agg["questions_engaged"], agg["questions"]),
                   "answered_question_share": _ratio(agg["questions_answered"], agg["questions"]),
                   "engaged_not_answered_share": _ratio(agg["questions_engaged_not_answered"], agg["questions"])}
    qtp, qfp, qfn = agg["question_label_tp"], agg["question_label_fp"], agg["question_label_fn"]
    qstats = {"el_segments": qtp + qfn, "ocelot_question_turns": qtp + qfp,
              "precision": _ratio(qtp, qtp + qfp), "recall": _ratio(qtp, qtp + qfn)}
    addr = {"meetings_with_addressee_annotation": agg["meetings_addressee_annotated"]}
    for kind in ("individual", "group"):
        addr[kind] = {"turns": adr[f"{kind}_turns"],
                      "predicted_nonempty_share": _ratio(adr[f"{kind}_predicted_nonempty"], adr[f"{kind}_turns"]),
                      "exact_set_share": _ratio(adr[f"{kind}_exact"], adr[f"{kind}_turns"]),
                      "pair_recall": _ratio(adr[f"{kind}_pair_hits"], adr[f"{kind}_pair_gold"]),
                      "pair_precision": _ratio(adr[f"{kind}_pair_hits"], adr[f"{kind}_pair_pred"]),
                      "baseline_adjacent_author": {
                          "exact_set_share": _ratio(adr[f"{kind}_baseline_exact"], adr[f"{kind}_turns"]),
                          "pair_recall": _ratio(adr[f"{kind}_baseline_pair_hits"], adr[f"{kind}_pair_gold"]),
                          "pair_precision": _ratio(adr[f"{kind}_baseline_pair_hits"],
                                                   adr[f"{kind}_baseline_pair_pred"])}}
    addr["group_turns_predicted_single_addressee"] = adr["group_predicted_single"]
    print(json.dumps({"corpus": f"AMI {os.path.basename(os.path.normpath(seg_dir))} split + AMI adjacency pairs (CC-BY-4.0), aggregate counts only",
                      "taxonomy_version": svc.provenance["taxonomy_version"],
                      **agg, "held": held_stats, "topic": topic_stats, "question_labels": qstats, "addressees": addr, "scores": res}, indent=1))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--split", choices=("validation", "test"), default="test",
                    help="AMI split under hf_samples/ami_meetings (develop on validation; test once)")
    ap.add_argument("--segments-dir", default=None, help="overrides --split")
    ap.add_argument("--annotations-dir", default=os.path.join(_DEF, "ami_annotations"))
    ap.add_argument("--batch", type=int, default=100, help="turns per /turns call (1 = streaming)")
    ap.add_argument("segments", nargs="?", default=None, help="(legacy positional SEGMENTS_DIR)")
    ap.add_argument("annotations", nargs="?", default=None, help="(legacy positional ANNOTATIONS_DIR)")
    ns = ap.parse_args()
    seg = ns.segments_dir or ns.segments or os.path.join(_DEF, "ami_meetings", ns.split)
    main(seg, ns.annotations or ns.annotations_dir, ns.batch)

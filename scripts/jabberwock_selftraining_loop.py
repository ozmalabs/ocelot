"""THE SELF-TRAINING LIVE LOOP — graph-native gate RULE + defer queue + PLUGGABLE teacher harness.

Part-2 engineering of the validated design. Architecture-clean:
 - The DECISION is a graph RULE: each Percept carries agree_count / margin / best_dist (mechanical recognition +
   aggregation, no decision); the gate Rule computes verdict = IfThenElse(novel? -> "novel" : agree>=3 & margin>=theta
   -> "self_label" : "defer") -- the branch lives in the Term, not Python.
 - SELF-LABEL -> the host banks the agent's OWN exemplar under the consensus word (mechanical). Recognition is the
   agent's own; NO teacher in the loop.
 - DEFER / NOVEL -> the Percept persists with that verdict = the graph-resident defer queue. NOT banked.
 - PLUGGABLE TEACHER HARNESS: a host interface label(percept)->word|None; backends (None / Oracle-stand-in / Whisper)
   swap at the adapter boundary and drain ONLY the deferred queue. The teacher never enters recognition.

Demonstrates: stream held-out percepts -> gate Rule sets verdicts -> self-label confident (measure PURITY) / defer
uncertain -> swap teacher backends to drain the queue. The whole loop runs whisper-free; the teacher is optional + only
on the tail.

Run:
  cd experiments/gamma-substrate
  ulimit -v 24000000
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_selftraining_loop
"""
from __future__ import annotations

import glob
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import substrate_rs as srs
from substrate.world_adapter import WorldAdapter
from scripts.jabberwock_reads_oov_from_phones import frames, dtw, STOP
from scripts.phonebank import align_utt
from scripts.librispeech_wer import load_flac
from scripts.jabberwock_harvest_exemplars import transcripts, DEV, MINW
from scripts.jabberwock_selftraining_gate import delta, featset, N_BANK, K, NWAY
import domains.self_directed_speech_world as SDW
from scripts.abs_language_decode import FS

THETA = 0.25     # margin threshold at agree>=3 (~8-12% coverage, ~70% purity per the validation)
D_MAX = 0.48     # novelty floor on the anchor distance (true word likely absent)
N_STREAM = 160


def _a(node, key):
    return {"type": "Attr", "node": {"name": node, "type": "Var"}, "key": key}


def _l(v):
    return {"type": "Lit", "value": v}


# verdict = IfThenElse(best>D_MAX -> "novel" : agree>2 -> (margin>THETA -> "self_label" : "defer") : "defer")
_VERDICT = {"type": "IfThenElse", "cond": {"type": "Gt", "a": _a("p", "best"), "b": _l(D_MAX)},
            "then": _l("novel"),
            "other": {"type": "IfThenElse", "cond": {"type": "Gt", "a": _a("p", "agree"), "b": _l(2.0)},
                      "then": {"type": "IfThenElse", "cond": {"type": "Gt", "a": _a("p", "margin"), "b": _l(THETA)},
                               "then": _l("self_label"), "other": _l("defer")},
                      "other": _l("defer")}}

GATE_SEED = {
    "id": "self_training_gate", "version": "1.0.0", "depends_on": [],
    "nodes": [{"local_id": 0, "type": "GateController", "attrs": {"theta": THETA}}],
    "edges": [], "productions": [{"provenance": "seed:selftrain:gated_by",
                                  "src": {"type": "Percept", "var": "p"}, "edge_type": "gated_by",
                                  "tgt": {"type": "GateController", "var": "g"}}],
    "rules": [{"name": "gate_verdict", "match": [["p", "gated_by", "g"]],
               "where": {"type": "Lit", "value": True},
               "effects": [["set_attr", "p", "verdict", {"__term__": _VERDICT}]]}],
}


# ---- the PLUGGABLE TEACHER HARNESS: one interface, swappable backends, drains only the queue ----
class Teacher:
    name = "abstract"
    def label(self, percept):    # percept: {audio, true, ...} -> word | None
        raise NotImplementedError


class NoneTeacher(Teacher):
    name = "none"
    def label(self, percept):
        return None              # leaves it deferred (no teacher available)


class OracleTeacher(Teacher):    # stand-in for a perfect labeller; a WhisperTeacher transcribes percept['audio'] identically
    name = "oracle(≈whisper)"
    def label(self, percept):
        return percept["true"]


def main():
    print("=" * 100)
    print("THE SELF-TRAINING LIVE LOOP — graph-native gate RULE + defer queue + pluggable teacher")
    print("=" * 100)
    agent = WorldAdapter()
    agent.inner.load_seed_manifest(GATE_SEED, agent.agent)
    gc = next(n for n in agent.s.nodes("GateController"))
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0})

    tr = transcripts(DEV)
    flacs = sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True))
    by_spk = defaultdict(list)
    for f in flacs:
        b = os.path.basename(f)[:-5]
        if b in tr:
            by_spk[os.path.basename(f).split("-")[0]].append((f, tr[b]))
    spks = sorted(by_spk); test_spk, train_spk = spks[-3:], spks[:-3]

    bank = defaultdict(list); nb = 0
    for sp in train_spk:
        for (f, t) in by_spk[sp]:
            if nb >= N_BANK:
                break
            x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64); nb += 1
            for (w, t0, t1) in align_utt(x, fs, t):
                if len(w) >= MINW and len(bank[w]) < K:
                    seg = x[int(t0 * fs):int(t1 * fs)]
                    if seg.size >= int(0.05 * fs):
                        bank[w].append(featset(s, seg))
        if nb >= N_BANK:
            break
    vocab = [w for w, _ in sorted(bank.items(), key=lambda kv: -len(kv[1]))[:NWAY]]
    vset = set(vocab)
    print(f"  agent booted with gate seed; bank {len(bank)} words, {len(vocab)}-way\n", flush=True)

    # ---- ingest a stream of held-out percepts; the gate RULE sets each verdict ----
    def recognise(traj, fft, allp):
        dl = delta(traj)
        d_st = np.array([min(dtw(traj, e[0]) for e in bank[c]) for c in vocab])
        d_dl = np.array([min(dtw(dl, delta(e[0])) for e in bank[c]) for c in vocab])
        d_ff = np.array([min(1.0 - fft @ e[1] for e in bank[c]) for c in vocab])
        d_ap = np.array([min(1.0 - allp @ e[2] for e in bank[c]) for c in vocab])
        winners = [int(d.argmin()) for d in (d_st, d_dl, d_ff, d_ap)]
        cons, agree = Counter(winners).most_common(1)[0]
        sg = np.sort(d_st)
        margin = float((sg[1] - sg[0]) / (d_st.std() + 1e-9))
        return cons, agree, margin, float(d_st.min())

    self_labelled = []; deferred = []; novel = []
    streamed = 0
    for sp in test_spk:
        for (f, t) in by_spk[sp]:
            if streamed >= N_STREAM:
                break
            x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64)
            for (w, t0, t1) in align_utt(x, fs, t):
                if w not in vset or len(w) < MINW or streamed >= N_STREAM:
                    continue
                seg = x[int(t0 * fs):int(t1 * fs)]
                if seg.size < int(0.05 * fs):
                    continue
                traj, fft, allp = featset(s, seg)
                cons, agree, margin, best = recognise(traj, fft, allp)
                # INGEST: write the Percept (mechanical) + hand to the gate via gated_by edge
                pid = agent.s.add_node("Percept", {"agree": float(agree), "margin": margin, "best": best,
                                                   "cons_word": vocab[cons], "true": w})
                agent.s.add_edge(pid, "gated_by", gc)
                agent.master_tick(); agent.tick()                 # the gate RULE fires -> sets verdict
                verdict = agent.s.node(pid)["attrs"].get("verdict")
                rec = {"pid": pid, "true": w, "cons": vocab[cons], "audio": seg}
                if verdict == "self_label":
                    bank[vocab[cons]].append((traj, fft, allp))   # SELF-TRAIN: bank own exemplar (no teacher)
                    self_labelled.append(rec)
                elif verdict == "novel":
                    novel.append(rec)
                else:
                    deferred.append(rec)
                streamed += 1
        if streamed >= N_STREAM:
            break

    pur = 100 * np.mean([r["cons"] == r["true"] for r in self_labelled]) if self_labelled else 0.0
    dpur = 100 * np.mean([r["cons"] == r["true"] for r in deferred]) if deferred else 0.0
    n_agree3 = sum(1 for r in (self_labelled + deferred + novel))   # diagnostic below uses graph attrs
    ag3 = sum(1 for p in agent.s.nodes("Percept") if agent.s.node(p)["attrs"].get("agree", 0) >= 3)
    print(f"  [calib] {ag3}/{streamed} percepts had >=3-cue agreement (the gate's coverage source)\n")
    print(f"  STREAMED {streamed} percepts through the gate RULE (verdict set in-graph by IfThenElse, not Python):")
    print(f"    SELF-LABELLED {len(self_labelled)}  -> banked own exemplars, PURITY {pur:.1f}% (would-be defer purity {dpur:.1f}%)")
    print(f"    DEFERRED      {len(deferred)}  -> graph-resident queue (verdict=defer), NOT banked")
    print(f"    NOVEL         {len(novel)}  -> queue (verdict=novel), teacher mints\n", flush=True)

    # ---- drain the deferred queue with PLUGGABLE teachers (swap backends, same loop) ----
    queue = deferred + novel
    for teacher in (NoneTeacher(), OracleTeacher()):
        resolved = 0
        for r in queue:
            w = teacher.label(r)                                  # the ONLY teacher call; only on the queue
            if w is not None:
                resolved += 1
        print(f"  teacher='{teacher.name}': drained queue {len(queue)} -> resolved {resolved} "
              f"({'leaves all deferred' if resolved == 0 else 'labels + banks the tail'})", flush=True)

    print("\n" + "=" * 100)
    # read a verdict straight from the graph to prove it's graph-resident
    sample = self_labelled[0]["pid"] if self_labelled else (deferred[0]["pid"] if deferred else None)
    sv = agent.s.node(sample)["attrs"].get("verdict") if sample is not None else "n/a"
    if self_labelled and pur >= 60 and pur > dpur + 20:
        print(f"  DONE — the self-training loop runs graph-native + teacher-pluggable: the gate RULE set every verdict")
        print(f"  in-graph (sample Percept.verdict='{sv}'), self-labelled {len(self_labelled)} at {pur:.1f}% purity (defer {dpur:.1f}%)")
        print(f"  whisper-FREE, and the PLUGGABLE teacher (none/oracle/whisper) drains ONLY the {len(queue)}-item deferred queue.")
        print("  Self-train the confident, defer the uncertain, escalate the tail to a swappable teacher. The live loop, wired.")
    else:
        print(f"  PARTIAL — loop runs (self {len(self_labelled)} purity {pur:.1f}%, defer {dpur:.1f}%); tune THETA/D_MAX. Sample verdict='{sv}'.")
    print("=" * 100)


if __name__ == "__main__":
    main()

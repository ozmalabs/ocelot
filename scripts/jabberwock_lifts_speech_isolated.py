"""LIFT speech recognition: exact categorical -> graded, cross-speaker, on REAL
LibriSpeech sign trajectories (the trace few-shot gate, applied to speech).

WHY NOT WER: the substrate STT's continuous-speech WER on LibriSpeech is floored
(~1.0) at feasible scale and has no clean word boundaries — too noisy to read a
matcher lift off. So we mirror the SOLVED trace arc's gate exactly: isolated
cross-speaker N-way recognition with clean labels, isolating the matcher decision.

INSTANCES: teach LibriSpeech utterances; each newly-minted AcousticSign carries a
graded A1-patch TRAJECTORY (32 frames x 25 patches) and is vote-grounded to a word.
Tag each with its speaker -> clean (word, trajectory, speaker) instances.

THE TWO MATCHERS (the only difference; same data, same LOSO split):
  EXACT  (the lexical_access regime = trace exact-token): quantise each frame to a
         codebook symbol, dedupe consecutive -> a phoneme-like SEQUENCE; recognise
         only on EXACT sequence equality to a support instance. Hard leaf.
  GRADED (the lift = trace soft StructSim): the held DtwTo Term over the raw
         trajectory (soft per-frame leaf + hard temporal skeleton via DTW). Nearest
         support instance -> its word.

GATE: cross-speaker (leave-one-speaker-out) N-way accuracy GRADED > EXACT > chance.
The decision is the agent's held DtwTo Term; no LLM, no new training.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_lifts_speech_isolated.py [n_pairs] [n_words] [max_query]
"""
from __future__ import annotations
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
import substrate_rs as srs
import scripts.librispeech_wer as L
from substrate_rs import Substrate
from domains.stt_pipeline import STTPipeline, STTParams, _node_sort_key

SPP, NP = 32, 25
_EV = srs._NativeSubstrate().evaluate
_STOP = {"THE", "A", "AN", "OF", "TO", "AND", "IN", "IS", "IT", "THAT", "HE", "WAS",
         "FOR", "ON", "AS", "WITH", "HIS", "AT", "BY", "I", "OR", "BE", "THIS", "HAD",
         "NOT", "ARE", "BUT", "FROM", "OUT", "SO", "AN", "HER", "SHE", "THEY", "YOU"}


def _reshape(traj):
    t = list(traj)
    n = len(t) // NP if len(t) >= NP else 1
    return tuple(tuple(t[i * NP:(i + 1) * NP]) for i in range(n))


def _dtw(a, b):
    return float(_EV({"type": "DtwTo", "a": {"type": "Lit", "value": a},
                      "b": {"type": "Lit", "value": b}}, {}))


def _code_seq(traj_2d, centroids):
    """quantise each frame to nearest codebook centroid, dedupe consecutive ->
    a categorical (phoneme-like) sequence (the EXACT regime's representation)."""
    seq = []
    for fr in traj_2d:
        v = np.asarray(fr)
        j = int(np.argmin(((centroids - v) ** 2).sum(1)))
        if not seq or seq[-1] != j:
            seq.append(j)
    return tuple(seq)


def main() -> int:
    n_pairs = int(sys.argv[1]) if len(sys.argv) > 1 else 240
    n_words = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    max_query = int(sys.argv[3]) if len(sys.argv) > 3 else 240

    pairs = L.gather_pairs(limit=n_pairs)
    speakers = sorted(set(p[1] for p in pairs))
    print("=" * 92)
    print("LIFT SPEECH: exact categorical vs graded DtwTo, cross-speaker, real LibriSpeech signs")
    print("=" * 92)
    print(f"  pairs={len(pairs)} speakers={len(speakers)}")

    sub = Substrate()
    fs0 = L.load_flac(pairs[0][0])[1]
    pipe = STTPipeline(STTParams(sample_rate=fs0)); pipe.attach(sub)

    # ---- teach; capture per-utterance NEW (sign,word) groundings tagged by speaker ----
    t0 = time.time(); vc = {}; instances = []
    for (path, sp, ch, ut, tr) in pairs:
        s, fs = L.load_flac(path)
        if pipe.params.sample_rate != fs:
            pipe = STTPipeline(STTParams(sample_rate=fs)); pipe.attach(sub)
        before = set(vc)
        try:
            pipe.teach_via_valleys(sub, s, tr, vote_counts=vc); sub.tick(50000)
        except Exception:
            continue
        new_keys = set(vc) - before
        if not new_keys:
            continue
        key2node = {_node_sort_key(n): n for n in sub.nodes("AcousticSign")}
        for (sk, w) in new_keys:
            node = key2node.get(sk)
            if node is None:
                continue
            traj = sub.node(node)["attrs"].get("trajectory")
            if traj and len(traj) >= NP and w.upper() not in _STOP:
                instances.append((w.upper(), _reshape(traj), sp))
    print(f"  taught in {time.time()-t0:.0f}s  raw instances={len(instances)}")

    # keep words spoken by >=2 speakers (cross-speaker possible), top n_words by count
    from collections import Counter, defaultdict
    spk_by_word = defaultdict(set)
    for w, _t, sp in instances:
        spk_by_word[w].add(sp)
    multi = {w for w, sps in spk_by_word.items() if len(sps) >= 2}
    cnt = Counter(w for w, _t, _s in instances if w in multi)
    vocab = [w for w, _ in cnt.most_common(n_words)]
    inst = [(w, t, sp) for (w, t, sp) in instances if w in vocab]
    print(f"  vocab (>=2 speakers, top {n_words}): {vocab}")
    print(f"  usable instances={len(inst)}  chance={1.0/len(vocab):.3f}")
    if len(vocab) < 3:
        print("  too few cross-speaker words at this scale — raise n_pairs.")
        return 2

    # codebook for the EXACT regime (k-means on sampled frames)
    frames = np.array([fr for _w, t, _s in inst for fr in t])
    rng = np.random.default_rng(0)
    K = 40
    cidx = rng.choice(len(frames), size=min(K, len(frames)), replace=False)
    centroids = frames[cidx].copy()
    for _ in range(8):                          # lloyd
        d = ((frames[:, None, :] - centroids[None, :, :]) ** 2).sum(2)
        lab = d.argmin(1)
        for k in range(len(centroids)):
            m = frames[lab == k]
            if len(m):
                centroids[k] = m.mean(0)
    codes = [(_code_seq(t, centroids), w, sp) for (w, t, sp) in inst]

    # ---- cross-speaker LOSO recognition: query vs support-from-other-speakers ----
    rng2 = np.random.default_rng(1)
    qidx = list(range(len(inst)))
    rng2.shuffle(qidx)
    qidx = qidx[:max_query]
    exact_ok = exact_fired = graded_ok = n = 0
    for qi in qidx:
        qw, qt, qsp = inst[qi]
        support = [(j, inst[j]) for j in range(len(inst)) if inst[j][2] != qsp]   # other speakers
        if not support:
            continue
        n += 1
        # EXACT: any support instance with identical code sequence -> its word (vote)
        qcode = codes[qi][0]
        hits = Counter(codes[j][1] for j, _ in support if codes[j][0] == qcode)
        if hits:
            exact_fired += 1
            if hits.most_common(1)[0][0] == qw:
                exact_ok += 1
        # GRADED: nearest support instance by held DtwTo -> its word
        best_d, best_w = 1e18, None
        for j, (sw, st, _sp) in support:
            d = _dtw(qt, st)
            if d < best_d:
                best_d, best_w = d, sw
        if best_w == qw:
            graded_ok += 1
    print(f"  evaluated {n} cross-speaker queries")

    exact_acc = exact_ok / max(n, 1)
    graded_acc = graded_ok / max(n, 1)
    chance = 1.0 / len(vocab)
    print("\n" + "=" * 92)
    print(f"  EXACT  categorical  : acc={exact_acc:.3f}   (fired on {exact_fired}/{n} = {exact_fired/max(n,1):.0%} of queries; "
          f"exact code-sequence match cross-speaker is rare)")
    print(f"  GRADED DtwTo (lift) : acc={graded_acc:.3f}")
    print(f"  chance              : {chance:.3f}")
    delta = graded_acc - exact_acc
    print(f"  delta (graded-exact): {delta:+.3f}   ->  {'LIFT' if delta > 0.02 and graded_acc > chance else 'NO LIFT'}")
    print("=" * 92)
    print("  Same instances, same cross-speaker (LOSO) split — only the recognition DECISION differs:")
    print("  exact categorical-sequence equality (the lexical_access / trace exact-token regime) vs the")
    print("  held DtwTo Term's graded match (soft per-frame leaf + hard temporal skeleton). The trace")
    print("  exact->graded lift, on real speech. Next rung: STRUCTURAL parts + StructSim (not whole-traj).")
    return 0 if (delta > 0.02 and graded_acc > chance) else 2


if __name__ == "__main__":
    raise SystemExit(main())

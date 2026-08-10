"""LIFT speech recognition on the REAL LibriSpeech WER gate: exact -> graded.

The current matcher (lexical_access) recognises a heard sign by EXACT phoneme-
sequence equality — the same un-lifted regime trace recognition was in (exact-token
AntiUnify, 19%). Cross-speaker, the same word rarely yields the identical exact
sequence, so the sign goes unmatched and the word is DROPPED (a deletion). That is
the speaker wall.

THE LIFT (the trace move: exact hard match -> graded soft match). When a test sign
has NO exact vote, fall back to the held DtwTo Term over the sign's graded A1-patch
TRAJECTORY (32 frames x 25 patches): pick the nearest TRAIN sign and use its voted
word. The skeleton stays hard (temporal order, via DTW alignment); the leaf is soft
(graded per-frame distance) — graded structural matching instead of exact equality.

Gate: WER(graded) < WER(exact-baseline) on the SAME held-out test speakers (LOSO).
Both use the SAME trained lexicon + votes; only the recognition decision differs.
The decision is the agent's held DtwTo Term; no LLM, no new training.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_lifts_speech_wer.py [n_pairs] [test_speakers] [max_test]
"""
from __future__ import annotations
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
import substrate_rs as srs
import scripts.librispeech_wer as L
from substrate_rs import Substrate
from domains.stt_pipeline import STTPipeline, STTParams, _node_sort_key, _rust

SPP, NP = 32, 25
_EV = srs._NativeSubstrate().evaluate


def _reshape(traj):
    """flat (spp*n_patches,) -> (frames x patches) nested tuple for DtwTo."""
    t = list(traj)
    if len(t) != SPP * NP:
        n = max(1, len(t) // NP)
        return tuple(tuple(t[i * NP:(i + 1) * NP]) for i in range(n))
    return tuple(tuple(t[i * NP:(i + 1) * NP]) for i in range(SPP))


def _dtw(a, b):
    return float(_EV({"type": "DtwTo", "a": {"type": "Lit", "value": a},
                      "b": {"type": "Lit", "value": b}}, {}))


def _utts_on_stream(sub, pipe, samples):
    """Re-ingest test audio, return time-sorted (sign_node, is_comp), preferring
    composed signs — exactly transcribe_via_votes' walk (so the EXACT path matches
    the baseline byte-for-byte; we only add the graded fallback at decode)."""
    stream = pipe._build_stream(sub)
    raw = np.ascontiguousarray(samples, dtype=np.float32).tobytes()
    _rust(sub).run_audio_pipeline(stream, raw, int(pipe.params.sample_rate))
    sub.tick(50000)
    utts = []
    for utt in sub.in_neighbours(stream, "from_stream"):
        if sub.node(utt)["type"] != "Utterance":
            continue
        a = sub.node(utt)["attrs"]
        st, en = a.get("start_time_s"), a.get("end_time_s")
        if st is None or en is None:
            continue
        for s in sub.neighbours(utt, "heard_as"):
            utts.append((float(st), float(en), s, bool(sub.node(s)["attrs"].get("composed", False))))
    comp = [(st, en) for st, en, _, c in utts if c]
    def covered(st, en):
        return any(cst <= st and cen >= en and (cst, cen) != (st, en) for cst, cen in comp)
    utts = [u for u in utts if u[3] or not covered(u[0], u[1])]
    utts.sort(key=lambda u: u[0])
    return utts


def _decode(sub, utts, votes_by_key, exemplars, graded):
    """votes_by_key: sign_key -> best word (exact). exemplars: [(key, traj, word)].
    If graded and a sign has no exact vote, pick nearest exemplar by DtwTo."""
    out = []
    for st, en, sign, is_comp in utts:
        key = _node_sort_key(sign)
        word = votes_by_key.get(key)
        if word is None and graded:
            tr = sub.node(sign)["attrs"].get("trajectory")
            if tr:
                q = _reshape(tr)
                best_d, best_w = 1e18, None
                for _k, etraj, ew in exemplars:
                    d = _dtw(q, etraj)
                    if d < best_d:
                        best_d, best_w = d, ew
                word = best_w
        if word is None:
            cs = list(sub.neighbours(sign, "denotes"))
            if cs:
                word = sub.node(sorted(cs, key=_node_sort_key)[0])["attrs"].get("name")
        if word and (not out or out[-1] != word):
            out.append(word)
    return out


def main() -> int:
    n_pairs = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    n_test_spk = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    max_test = int(sys.argv[3]) if len(sys.argv) > 3 else 40

    pairs = L.gather_pairs(limit=n_pairs)
    speakers = sorted(set(p[1] for p in pairs))
    test_spk = set(speakers[-n_test_spk:])
    train = [p for p in pairs if p[1] not in test_spk]
    test = [p for p in pairs if p[1] in test_spk][:max_test]
    print("=" * 90)
    print("LIFT SPEECH RECOGNITION ON LibriSpeech WER (exact -> graded DtwTo fallback)")
    print("=" * 90)
    print(f"  pairs={len(pairs)} speakers={len(speakers)}  train={len(train)} ({len(speakers)-n_test_spk} spk)  "
          f"test={len(test)} ({n_test_spk} held-out spk)")

    sub = Substrate()
    fs0 = L.load_flac(train[0][0])[1]
    pipe = STTPipeline(STTParams(sample_rate=fs0)); pipe.attach(sub)

    # ---- TRAIN (shared lexicon + votes) ----
    t0 = time.time(); vote_counts = {}
    for i, (path, sp, ch, ut, tr) in enumerate(train):
        s, fs = L.load_flac(path)
        if pipe.params.sample_rate != fs:
            pipe = STTPipeline(STTParams(sample_rate=fs)); pipe.attach(sub)
        try:
            pipe.teach_via_valleys(sub, s, tr, vote_counts=vote_counts); sub.tick(50000)
        except Exception as e:
            print(f"   teach fail: {e}"); continue
    print(f"  trained in {time.time()-t0:.0f}s  vote entries={len(vote_counts)}")

    # exact decode map: sign_key -> best-voted word
    votes_by_key = {}
    for (sk, w), cnt in vote_counts.items():
        cur = votes_by_key.get(sk)
        if cur is None or cnt > cur[1]:
            votes_by_key[sk] = (w, cnt)
    votes_by_key = {k: v[0] for k, v in votes_by_key.items()}
    # graded exemplars: train signs that carry a vote AND a trajectory
    exemplars = []
    for s in sub.nodes("AcousticSign"):
        k = _node_sort_key(s)
        if k in votes_by_key:
            tr = sub.node(s)["attrs"].get("trajectory")
            if tr:
                exemplars.append((k, _reshape(tr), votes_by_key[k]))
    print(f"  exact-vote signs={len(votes_by_key)}  graded exemplars={len(exemplars)}")

    # ---- TEST: exact baseline vs graded lift, same utterances ----
    def wer(hyps_refs):
        te = sum(L.levenshtein_words(r, h) for r, h in hyps_refs)
        tr_ = sum(len(r) for r, _ in hyps_refs)
        return te / max(tr_, 1), te, tr_

    base_pairs, lift_pairs = [], []
    t0 = time.time()
    for (path, sp, ch, ut, tr) in test:
        s, fs = L.load_flac(path)
        if pipe.params.sample_rate != fs:
            pipe = STTPipeline(STTParams(sample_rate=fs)); pipe.attach(sub)
        ref = L.normalise(tr)
        utts = _utts_on_stream(sub, pipe, s)
        base_pairs.append((ref, _decode(sub, utts, votes_by_key, exemplars, graded=False)))
        lift_pairs.append((ref, _decode(sub, utts, votes_by_key, exemplars, graded=True)))
    base_wer, be, bt = wer(base_pairs)
    lift_wer, le, lt = wer(lift_pairs)
    print(f"  tested {len(test)} utts in {time.time()-t0:.0f}s")

    print("\n" + "=" * 90)
    print(f"  EXACT baseline WER : {base_wer:.3f}   ({be} errors / {bt} ref words)")
    print(f"  GRADED lift  WER   : {lift_wer:.3f}   ({le} errors / {lt} ref words)")
    delta = base_wer - lift_wer
    print(f"  delta WER (lower=better): {delta:+.3f}   ->  {'LIFT' if delta > 0 else 'NO LIFT'}")
    print("=" * 90)
    print("  The only change is the recognition DECISION: exact phoneme-sequence equality vs the held")
    print("  DtwTo Term over the graded A1-patch trajectory (soft leaf + hard temporal skeleton). Same")
    print("  trained lexicon + votes, same held-out speakers. The trace move (exact->graded), on real")
    print("  speech. Next rung: STRUCTURAL decompose into parts + StructSim skeleton (not whole-trajectory).")
    return 0 if delta > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())

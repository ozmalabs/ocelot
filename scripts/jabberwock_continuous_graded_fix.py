"""FIX step 1 of continuous recognition: graded recovery of dropped signs.

Diagnosis (89adab64): the continuous path emits ~1 word per 4 (0.25x) — ~75% of WER is
DELETIONS, because lexical_access mints signs by EXACT phoneme-sequence and a held-out
speaker's sign rarely matches a trained one -> no vote -> the word is DROPPED.

FIX: when a re-ingested sign has no exact vote, GRADE-MATCH it (cosine over the sign's
A1-patch trajectory) to the nearest TRAINED sign and inherit its word — the exact->graded
move, on the continuous path. Same re-ingest + same segmentation as the exact baseline,
so the only change is the recognition decision per segment.

Reports, head-to-head (held-out speakers): WER + hyp/ref word ratio for EXACT vs GRADED.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_continuous_graded_fix.py [n_train] [n_test]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
import scripts.librispeech_wer as L
from substrate_rs import Substrate
from domains.stt_pipeline import STTPipeline, STTParams, _node_sort_key, _rust


def _emb(traj):
    v = np.asarray(traj, float).ravel()
    return v / max(np.linalg.norm(v), 1e-9)


def _utts(sub, pipe, samples, prefer_composed=True):
    """Re-ingest + collect time-ordered (sign, is_comp) — the transcribe_via_votes walk."""
    stream = pipe._build_stream(sub)
    _rust(sub).run_audio_pipeline(stream, np.ascontiguousarray(samples, np.float32).tobytes(),
                                  int(pipe.params.sample_rate))
    sub.tick(50000)
    us = []
    for utt in sub.in_neighbours(stream, "from_stream"):
        if sub.node(utt)["type"] != "Utterance":
            continue
        a = sub.node(utt)["attrs"]; st, en = a.get("start_time_s"), a.get("end_time_s")
        if st is None or en is None:
            continue
        for s in sub.neighbours(utt, "heard_as"):
            us.append((float(st), float(en), s, bool(sub.node(s)["attrs"].get("composed", False))))
    if prefer_composed:
        comp = [(st, en) for st, en, _, c in us if c]
        us = [u for u in us if u[3] or not any(cst <= u[0] and cen >= u[1] and (cst, cen) != (u[0], u[1])
                                               for cst, cen in comp)]
    us.sort(key=lambda u: u[0])
    return us


def main():
    n_train = int(sys.argv[1]) if len(sys.argv) > 1 else 280
    n_test = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    pairs = L.gather_pairs(limit=n_train + 300)
    spk = sorted(set(p[1] for p in pairs)); test_spk = set(spk[-6:])
    train = [p for p in pairs if p[1] not in test_spk][:n_train]
    test = [p for p in pairs if p[1] in test_spk][:n_test]
    print("=" * 86)
    print("CONTINUOUS FIX step 1 — graded recovery of dropped signs (exact vs graded)")
    print("=" * 86)
    print(f"  train {len(train)} / test {len(test)} (held-out speakers)")

    sub = Substrate(); fs0 = L.load_flac(train[0][0])[1]
    pipe = STTPipeline(STTParams(sample_rate=fs0)); pipe.attach(sub)
    vc = {}; t0 = time.time()
    for i, (path, sp, ch, ut, tr) in enumerate(train):
        s, fs = L.load_flac(path)
        if pipe.params.sample_rate != fs:
            pipe = STTPipeline(STTParams(sample_rate=fs)); pipe.attach(sub)
        try:
            pipe.teach_via_valleys(sub, s, tr, vote_counts=vc); sub.tick(50000)
        except Exception:
            continue
        if (i + 1) % 100 == 0:
            print(f"   trained {i+1}/{len(train)} [{time.time()-t0:.0f}s]", flush=True)

    # vote map + trained exemplar embeddings (trajectory) + their voted word
    best = {}
    for (sk, w), c in vc.items():
        if sk not in best or c > best[sk][1]:
            best[sk] = (w, c)
    vote_word = {sk: wc[0] for sk, wc in best.items()}
    E, EW = [], []
    for n in sub.nodes("AcousticSign"):
        k = _node_sort_key(n); tr = sub.node(n)["attrs"].get("trajectory")
        if k in vote_word and tr:
            E.append(_emb(tr)); EW.append(vote_word[k])
    E = np.array(E)
    print(f"  trained: vote signs={len(vote_word)}  graded exemplars={len(E)}", flush=True)

    te = tg = total_ref = hyp_e = hyp_g = 0
    for (path, sp, ch, ut, tr) in test:
        s, fs = L.load_flac(path)
        if pipe.params.sample_rate != fs:
            pipe = STTPipeline(STTParams(sample_rate=fs)); pipe.attach(sub)
        ref = L.normalise(tr); total_ref += len(ref)
        us = _utts(sub, pipe, s)
        he, hg = [], []
        for st, en, sign, ic in us:
            k = _node_sort_key(sign)
            we = vote_word.get(k)
            if we and (not he or he[-1] != we):
                he.append(we)
            tj = sub.node(sign)["attrs"].get("trajectory")
            wg = we
            if wg is None and tj is not None and len(E):
                wg = EW[int((E @ _emb(tj)).argmax())]          # graded: nearest trained sign
            if wg and (not hg or hg[-1] != wg):
                hg.append(wg)
        te += L.levenshtein_words(ref, he); tg += L.levenshtein_words(ref, hg)
        hyp_e += len(he); hyp_g += len(hg)

    print("\n" + "=" * 86)
    print(f"  EXACT  : WER {te/max(total_ref,1):.3f}   hyp/ref {hyp_e}/{total_ref} = {hyp_e/max(total_ref,1):.2f}x")
    print(f"  GRADED : WER {tg/max(total_ref,1):.3f}   hyp/ref {hyp_g}/{total_ref} = {hyp_g/max(total_ref,1):.2f}x")
    print("=" * 86)
    d = te/max(total_ref,1) - tg/max(total_ref,1)
    print(f"  delta WER (exact - graded) = {d:+.3f}  -> {'GRADED RECOVERS dropped words' if d > 0.02 else 'no net gain (recovered words are wrong = substitutions)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

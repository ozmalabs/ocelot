"""WIRE the learned encoder into the real recogniser — graph-natively, open vocab.

Architecture rule: the DECISION is a held Term; learned parameters are GRAPH DATA;
the feature transform is mechanical adapter I/O (like cochleagram/CMVN). The learned
recogniser wires in like comprehend_speech_clip._ground (per-item held Term score +
argmax), but with a Dot against learned WORD-CENTROID graph nodes instead of DtwTo
against exemplars:

  GRAPH DATA   : WordCentroid nodes {word, vec} + a SpeechEncoder node {mu, pca, lda}
                 (the learned encoder), persisted as a seed so the agent boots with it.
  ADAPTER I/O  : feature prep (peel speaker/rate + velocity) + the linear projection.
  HELD TERM    : score = Dot(embedding, centroid), evaluated by the Rust substrate;
                 the top-k/argmax over centroids is the native topk_dot primitive (the
                 batched form of that held Dot Term + argmax loop).

OPEN VOCAB. The encoder is fit on a LARGE set of BACKGROUND classes so its PCA->LDA
subspace captures word-discriminative directions that TRANSFER to any word (collapsing
speaker/rate/alignment); centroids are then built for a large recognition vocabulary.
Recognition is by CLASS CENTROID (a word's exemplars averaged) — denoised and cheap.
Validated cross-speaker (train support -> unseen dev speakers). per-instance peel env
(= frames.mean(0)) matches the deployed recogniser's default, so build == inference.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_wire_learned_recogniser.py [n_recog] [max_q] [per] [n_bg]
"""
from __future__ import annotations
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
import substrate_rs as srs
from collections import Counter, defaultdict
from scripts.jabberwock_learned_encoder import _load, _feat, _fit_pca, _fit_lda

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = os.path.join(ROOT, "var", "speech_word_templates.json")


def _env(fr):
    return np.asarray(fr, float).mean(0)


def _norm(x):
    x = np.asarray(x, dtype=np.float64)
    return x / max(np.linalg.norm(x), 1e-9)


def main() -> int:
    n_recog = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    max_q = int(sys.argv[2]) if len(sys.argv) > 2 else 600
    per = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    n_bg = int(sys.argv[4]) if len(sys.argv) > 4 else 1200

    train = _load("train-clean-100_*.pkl", 12)
    dev = _load("dev-clean_*.pkl", 12)
    sw = Counter(w for w, _ in train); qw = Counter(w for w, _ in dev)
    print("=" * 92)
    print("WIRE THE LEARNED ENCODER (open vocab): bg-fit PCA->LDA + class centroids, held Dot decision")
    print("=" * 92)

    # ---- FIT the encoder on BACKGROUND classes (offline tooling, like a codebook) ----
    bg_vocab = [w for w, _ in sw.most_common() if len(w) >= 2][:n_bg]
    bgset = set(bg_vocab)
    bgby = defaultdict(list)
    for w, fr in train:
        if w in bgset and len(bgby[w]) < per:
            bgby[w].append(fr)
    bg = [(w, fr) for w, frs in bgby.items() for fr in frs]
    Bx = np.array([_feat(fr, _env(fr)) for w, fr in bg]); bgy = [w for w, _ in bg]
    nC = len(set(bgy))
    P = min(200, Bx.shape[0] - nC - 1)
    mu, Wp = _fit_pca(Bx, P)
    Wl = _fit_lda((Bx - mu) @ Wp, bgy, k=min(P, nC - 1))
    print(f"  encoder fit on {nC} bg classes ({len(bg)} instances) -> {Wl.shape[1]}d subspace", flush=True)

    def encode(X):
        Y = ((X - mu) @ Wp) @ Wl
        return Y / np.clip(np.linalg.norm(Y, axis=1, keepdims=True), 1e-9, None)

    # ---- build CLASS CENTROIDS for the recognition vocabulary (encoder space) ----
    recog_vocab = [w for w, _ in sw.most_common() if len(w) >= 2][:n_recog]
    rset = set(recog_vocab)
    rby = defaultdict(list)
    for w, fr in train:
        if w in rset and len(rby[w]) < per:
            rby[w].append(fr)
    recog_vocab = [w for w in recog_vocab if rby[w]]            # keep only words we have
    cent = {}; cmu = {}; csig = {}
    for w in recog_vocab:
        Fe = encode(np.array([_feat(fr, _env(fr)) for fr in rby[w]]))
        cent[w] = _norm(Fe.mean(0))
        ld = np.log([max(len(fr), 1) for fr in rby[w]])          # LOG-duration stats (rate is multiplicative)
        cmu[w] = float(np.mean(ld))
        csig[w] = float(np.std(ld)) if len(ld) > 1 else 0.3
        csig[w] = max(csig[w], 0.1)                               # floor: avoid over-confident spread
    print(f"  centroids built for {len(recog_vocab)} words (open vocab)", flush=True)

    # ---- VALIDATE cross-speaker on dev (held Dot / native topk over centroids) ----
    qry = [(w, fr) for w, fr in dev if w in cent]
    np.random.default_rng(1).shuffle(qry); qry = qry[:max_q]
    Qe = encode(np.array([_feat(fr, _env(fr)) for w, fr in qry]))
    cmat = np.array([cent[w] for w in recog_vocab], dtype=np.float32)
    sims = Qe @ cmat.T
    order = np.argsort(-sims, axis=1)[:, :5]
    qy = [w for w, _ in qry]
    t1 = sum(recog_vocab[order[i, 0]] == qy[i] for i in range(len(qy))) / max(len(qy), 1)
    t5 = sum(qy[i] in [recog_vocab[j] for j in order[i]] for i in range(len(qy))) / max(len(qy), 1)
    chance = 1.0 / len(recog_vocab)
    print(f"  cross-speaker open-vocab acc: top1 {t1:.3f}  top5 {t5:.3f}  "
          f"({t1/chance:.0f}x chance, {len(qy)} queries)", flush=True)

    # ---- PERSIST as a seed so a booted agent recognises through this path ----
    seed = {
        "id": "speech_word_templates", "version": "2.0.0", "depends_on": [],
        "description": "Learned open-vocab speech recogniser: word-centroid templates + a "
                       "background-fit linear encoder (peel+velocity -> PCA -> LDA). Recognition "
                       "= Dot(embedding, centroid) held Term / native topk_dot, argmax loop.",
        "nodes": [{"local_id": i, "type": "WordCentroid",
                   "attrs": {"word": w, "vec": [float(x) for x in cent[w]],
                             "dur_mu": cmu[w], "dur_sig": csig[w]}}
                  for i, w in enumerate(recog_vocab)] +
                 [{"local_id": len(recog_vocab), "type": "SpeechEncoder",
                   "attrs": {"mu": [float(x) for x in mu],
                             "pca": [[float(x) for x in row] for row in Wp.tolist()],
                             "lda": [[float(x) for x in row] for row in Wl.tolist()],
                             "feature": "peel_speaker+rate(L=20)+velocity"}}],
        "edges": [], "productions": [],
    }
    with open(SEED, "w") as f:
        json.dump(seed, f)
    print(f"  persisted var/speech_word_templates.json "
          f"({os.path.getsize(SEED)/1024:.0f} KB) — {len(recog_vocab)} templates + encoder", flush=True)

    # ---- BOOT-FROM-SEED via the deployable capability (the real wired recogniser) ----
    from domains.learned_speech_recogniser import LearnedSpeechRecogniser, install_templates
    fresh = srs.Substrate()
    install_templates(fresh)
    rec = LearnedSpeechRecogniser(fresh)
    t = time.time()
    boot_ok = sum(rec.recognise(fr) == w for w, fr in qry) / max(len(qry), 1)
    print(f"  BOOT via LearnedSpeechRecogniser: top1 {boot_ok:.3f}  "
          f"({len(rec._cent)} templates loaded)  [{time.time()-t:.1f}s]", flush=True)

    print("=" * 92)
    ok_v = t1 >= 0.40 and abs(boot_ok - t1) < 0.02
    print(f"  {'WIRED' if ok_v else 'CHECK'} — learned open-vocab recogniser graph-native: centroids+encoder "
          f"GRAPH DATA, decision the held Dot / native topk. top1 {t1:.3f} cross-speaker.")
    return 0 if ok_v else 2


if __name__ == "__main__":
    raise SystemExit(main())

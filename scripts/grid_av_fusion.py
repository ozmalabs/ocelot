"""PUSH FUSION TO REAL AUDIOVISUAL SPEECH — GRID corpus (real talking-face video + audio),
fused through the HELD reliability-weighted recognizer (predict_reliability_weighted_term).

Real AV speech: GRID speaker s1 .mpg (25fps face video + 44.1kHz audio) with word-level
.align. Target the COLOR word (blue/green/red/white — distinct lip shapes AND sounds).
  AUDIO cue  = word's audio -> 8kHz -> held cochlea -> time-resampled flat feature
  VISUAL cue = word's frames -> fixed lower-center MOUTH ROI -> the HELD VISION FRONT-END
               (domains.vision_graph.GraphEye._process_frame: V1 Sobel edges + Harris corners + DoG
               center-surround salience, per gaze column) -> the held order-N SHAPE_SIGNATURE
               (Substrate.shape_signature: the gain/level-invariant ordinal-rank key) of those
               V1 edges, spatially (per frame across columns) and temporally (per column over
               frames) = vision's full held stack: edges -> order-N shape.
Each -> cr.channel_likelihood; fused = the agent's native predict_reliability_weighted_term
(Argmax of Pi_c P_c^{r_c}); reliability r_c from calibration, re-estimated as a cue degrades.

Three isolations: (1) FUSION beats either cue; (2) GRACEFUL DEGRADATION; (3) McGURK CONFLICT
(audio=A dubbed on video=B -> percept follows the more reliable cue — the literal AV-speech
phenomenon, here on real lips).

Run: python scripts/grid_av_fusion.py [n_per_color]
"""
from __future__ import annotations
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import math
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

import av
from scipy.signal import resample_poly
from huggingface_hub import hf_hub_download, HfApi

from substrate_rs import Substrate
from substrate_rs.speech import _audio
from domains import combinatorial_recognizer as cr
from domains.vision_graph import RGBEye
from scripts.fsdd_segmentation_realspeech import frames as cframes

REPO = "wissemkarous/lipreading"
COLORS = {"blue": 0, "green": 1, "red": 2, "white": 3}
CANDS = list(range(4))
ROI = (slice(192, 232), slice(150, 210))    # tight lip ROI on 288x360 GRID s1 (verified)
N_FRAMES = 6                                 # frames sampled across the word's articulation


def _make_eye(n_az=8):
    """the held V1 vision front-end (GraphEye._process_frame is pure/stateless) — build it
    on its own vision substrate, stop the worker thread, and run lip frames through it directly.
    GraphEye._process_frame runs the edge convolve via the Rust ChangeDetect Term against the
    graph-resident Sobel kernels (no cv2.filter2D); same percept shape as the retired Eye."""
    e = RGBEye(substrate=Substrate(), n_az=n_az, fov_h_deg=90.0, vband=0.9).build()
    e.stop()
    return e


_EYE = _make_eye()


def v1_percepts(frame_rgb):
    """one lip frame -> the held front-end's per-column V1 percepts (edge/corner/salience/
    luminance) = the vision=edges representation, not raw pixels."""
    ps = _EYE._process_frame(None, frame_rgb, 0.0)["percepts"]
    return np.array([[p["edge_density"], p["corner_density"], p["salience"], p["luminance"]]
                     for p in ps])


def shapesig_feat(G):
    """The held order-N SHAPE_SIGNATURE stage on the V1 edges. G is (N_FRAMES, n_az, 4) V1
    percepts; take the gain/level-invariant ordinal-rank shape of the EDGE (ch0) and SALIENCE
    (ch2) channels both SPATIALLY (per frame, the shape across gaze columns) and TEMPORALLY
    (per column, the articulation shape over the word's frames). The ordinal ranks discard
    surface gain (lighting/contrast) and keep the SHAPE of the lip's V1 edges over space+time."""
    parts = []
    for ch in (0, 2):                                   # edge_density, salience
        for t in range(G.shape[0]):
            parts.append(Substrate.shape_signature(list(G[t, :, ch])))      # spatial
        for col in range(G.shape[1]):
            parts.append(Substrate.shape_signature(list(G[:, col, ch])))    # temporal
    return np.concatenate(parts).astype(np.float64)


def select_ids(n_per):
    files = HfApi().list_repo_files(REPO, repo_type="dataset")
    aligns = [f.split("/")[-1][:-6] for f in files if f.endswith(".align")]
    mpgs = set(f.split("/")[-1][:-4] for f in files if f.endswith(".mpg"))
    byc = {"b": [], "g": [], "r": [], "w": []}            # char1 = color code
    for i in aligns:
        if i in mpgs and i[1] in byc:
            byc[i[1]].append(i)
    sel = []
    for c in byc:
        sel += byc[c][:n_per]
    return sel


def load(uid):
    mpg = hf_hub_download(REPO, f"Data/data/s1/{uid}.mpg", repo_type="dataset")
    aln = hf_hub_download(REPO, f"Data/data/alignments/s1/{uid}.align", repo_type="dataset")
    seg = None
    for ln in open(aln):
        p = ln.split()
        if len(p) == 3 and p[2] in COLORS:
            seg = (int(p[0]), int(p[1]), COLORS[p[2]])
    if not seg:
        return None
    # pad the word by +-2 frames to capture the full articulation gesture.
    f0, f1 = max(0, seg[0] // 1000 - 2), min(75, seg[1] // 1000 + 2)
    c = av.open(mpg)
    fr = [f.to_ndarray(format="rgb24") for f in c.decode(video=0)]
    roi = [fr[i][ROI[0], ROI[1]] for i in range(f0, f1)]
    idx = np.linspace(0, len(roi) - 1, N_FRAMES).round().astype(int)
    # VISUAL cue = held V1 front-end -> held order-N shape_signature (edges -> shape).
    G = np.stack([v1_percepts(roi[i]) for i in idx])     # (N_FRAMES, n_az, 4) V1 percepts
    vfeat = shapesig_feat(G)
    a0 = seg[0] // 1000  # audio aligned to the UNPADDED word
    a1 = max(seg[1] // 1000, a0 + 1)
    c = av.open(mpg)
    ab = [f.to_ndarray() for f in c.decode(audio=0)]
    a = np.concatenate(ab, axis=1).mean(0) if ab[0].ndim == 2 else np.concatenate(ab)
    a8 = resample_poly(a, 8000, 44100)
    s0, s1 = int(a0 / 25 * 8000), int(a1 / 25 * 8000)
    return seg[2], vfeat, a8[s0:s1]


CACHE = "/tmp/grid_av_shapesig_feats.npz"


def extract(n_per):
    """Heavy phase: decode video, run V1 + shape_signature + cochlea -> cache feature arrays.
    No big BLAS matmul here, so it is safe under memory pressure; the fusion phase then runs
    in a clean low-memory process (decouples OpenBLAS allocation from the video-decode churn)."""
    s = Substrate(); _audio.seed_audio_grammar(s)
    bank = _audio.cochlea(s, n_bands=24, fs=8000)

    def afeat(a):
        M = cframes(s, bank, a.astype(np.float64))
        idx = np.linspace(0, len(M) - 1, 8).round().astype(int)
        return np.stack([M[i] for i in idx]).flatten()

    labs, V, A = [], [], []
    for uid in select_ids(n_per):
        try:
            r = load(uid)
            if r:
                labs.append(r[0]); V.append(r[1]); A.append(afeat(r[2]))
        except Exception as e:
            print("  skip", uid, type(e).__name__, str(e)[:40])
    np.savez(CACHE, labs=np.array(labs), V=np.array(V), A=np.array(A))
    print(f"  cached {len(labs)} feature rows -> {CACHE}")


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    print("=" * 70)
    print("REAL AUDIOVISUAL SPEECH FUSION — GRID s1 color word, held reliability-weighted")
    print("=" * 70)
    if not os.path.exists(CACHE):
        extract(n_per)
    np.ones((4, 4)) @ np.ones((4, 4))   # init OpenBLAS in the clean fusion process
    s = Substrate()
    z = np.load(CACHE)
    labs, V, A = z["labs"], z["V"], z["A"]
    from collections import Counter
    print(f"  loaded {len(labs)} real AV color-word segments; dist {dict(Counter(labs))}")

    rng = np.random.RandomState(0)
    idx = rng.permutation(len(labs)); cut = len(labs) * 3 // 10
    te, tr = idx[:cut], idx[cut:]
    Atr, Vtr, Wtr = A[tr], V[tr], labs[tr]

    word_node = {d: s.add_node("Concept", {"name": f"c{d}", cr.WORD_ATTR: 1.0}) for d in CANDS}
    term = cr.predict_reliability_weighted_term()
    La = lambda q, X=Atr, W=Wtr: cr.channel_likelihood(q, X, W, CANDS)
    Lv = lambda q, X=Vtr, W=Wtr: cr.channel_likelihood(q, X, W, CANDS)
    am = lambda p: max(p, key=p.get)

    def fuse(pa, pv, ra=1.0, rv=1.0):
        for d in CANDS:
            s.set_attr(word_node[d], cr.P_FLAT_ATTR, float(pa[d]))
            s.set_attr(word_node[d], cr.P_TRANS_ATTR, float(pv[d]))
            s.set_attr(word_node[d], cr.R_FLAT_ATTR, float(ra))
            s.set_attr(word_node[d], cr.R_TRANS_ATTR, float(rv))
        win = s._inner.evaluate(term, {})
        return next(d for d, n in word_node.items() if n == win)

    def calib(X, W):
        n = max(1, len(X) // 5); p = np.random.RandomState(0).permutation(len(X))
        Xs, Ws = X[p], W[p]; Xv, Wv, Xt, Wt = Xs[:n], Ws[:n], Xs[n:], Ws[n:]
        return np.mean([am(cr.channel_likelihood(q, Xt, Wt, CANDS)) == w for q, w in zip(Xv, Wv)])

    ra, rv = calib(Atr, Wtr), calib(Vtr, Wtr)
    print(f"  calibrated reliability:  r_audio={ra:.2f}  r_visual={rv:.2f}   (chance acc 0.25)")

    # (1) fusion vs single cues
    na = nv = nu = nw = 0
    for i in te:
        pa, pv = La(A[i]), Lv(V[i])
        na += am(pa) == labs[i]; nv += am(pv) == labs[i]
        nu += fuse(pa, pv) == labs[i]; nw += fuse(pa, pv, ra, rv) == labs[i]
    t = len(te)
    print("\n(1) FUSION vs single cues (held-out utterances):")
    print(f"    audio {na/t:.3f}   visual {nv/t:.3f}   "
          f"FUSED-unweighted {nu/t:.3f}   FUSED-reliability {nw/t:.3f}")

    # (2) graceful degradation — noise the audio cue, r_a re-estimated
    print("\n(2) GRACEFUL DEGRADATION (noise the AUDIO cue; r_a re-estimated):")
    print(f"    {'sigma_a':>8} {'r_a':>5} {'audio':>7} {'visual':>7} {'FUSED-rel':>10}")
    for sg in (0.0, 1.0, 2.0, 4.0):
        def nz(v):
            return v if sg == 0 else v + rng.normal(0, sg * (v.std() + 1e-9), size=v.shape)
        Atrn = np.array([nz(x) for x in Atr]); ran = calib(Atrn, Wtr)
        na2 = nv2 = nf2 = 0
        for i in te:
            pa = cr.channel_likelihood(nz(A[i]), Atrn, Wtr, CANDS); pv = Lv(V[i])
            na2 += am(pa) == labs[i]; nv2 += am(pv) == labs[i]; nf2 += fuse(pa, pv, ran, rv) == labs[i]
        print(f"    {sg:8.1f} {ran:5.2f} {na2/t:7.3f} {nv2/t:7.3f} {nf2/t:10.3f}")

    # (3) McGurk conflict — audio=A dubbed on video=B; fused follows the more reliable cue
    print("\n(3) McGURK CONFLICT (audio=colorA dubbed on video=colorB):")
    print(f"    {'regime':>16} {'r_a':>5} {'r_v':>5} {'->AUDIO':>9} {'->VIDEO':>9}")
    pairs = [(i, j) for i in te for j in te if labs[i] != labs[j]]
    rng.shuffle(pairs); pairs = pairs[:400]
    for label, sa, sv in (("clean", 0.0, 0.0), ("audio noised", 3.0, 0.0), ("video noised", 0.0, 3.0)):
        def nza(v): return v if sa == 0 else v + rng.normal(0, sa*(v.std()+1e-9), size=v.shape)
        def nzv(v): return v if sv == 0 else v + rng.normal(0, sv*(v.std()+1e-9), size=v.shape)
        rA = calib(np.array([nza(x) for x in Atr]), Wtr)
        rV = calib(np.array([nzv(x) for x in Vtr]), Wtr)
        fa = fb = 0
        for i, j in pairs:
            pred = fuse(cr.channel_likelihood(nza(A[i]), Atr, Wtr, CANDS),
                        cr.channel_likelihood(nzv(V[j]), Vtr, Wtr, CANDS), rA, rV)
            fa += pred == labs[i]; fb += pred == labs[j]
        n = len(pairs)
        print(f"    {label:>16} {rA:5.2f} {rV:5.2f} {fa/n:9.3f} {fb/n:9.3f}")
    print("=" * 70)


if __name__ == "__main__":
    main()

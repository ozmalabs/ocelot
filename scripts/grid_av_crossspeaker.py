"""CROSS-SPEAKER audiovisual speech fusion — multiple GRID speakers, leave-one-speaker-out.
The gain/level-invariant order-N shape_signature should generalize the LIP cue across faces
better than raw pixels (different faces/lighting/mouth sizes), and AV fusion should hold up
cross-speaker. s1 via HF (wissemkarous/lipreading); s2-s4 via the original GRID source zips.

Per held-out speaker (train on the others):
  AUDIO  cue  = word audio -> 8kHz -> held cochlea -> flat feature
  VISUAL raw  = mouth ROI resized -> temporal-std motion pixels (the appearance baseline)
  VISUAL shape= mouth ROI -> held V1 front-end -> held order-N shape_signature (edges->shape)
Mouth ROI = Haar face detection -> lower-center of the face (per-speaker alignment). The
V1->shape_signature pipeline is ROI-SIZE-invariant (n_az gaze columns), so it needs no
cross-speaker registration. Fused = native predict_reliability_weighted_term.

Run: python scripts/grid_av_crossspeaker.py [n_per_class]            (4-class color word)
     GRID_TARGET=digit python scripts/grid_av_crossspeaker.py 12     (10-class digit word)
"""
from __future__ import annotations
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import io
import math
import sys
import tarfile
import zipfile

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

import av
import cv2
cv2.setNumThreads(1)   # avoid pthread_create EAGAIN (BlockingIOError) under thread pressure
from scipy.signal import resample_poly
from huggingface_hub import hf_hub_download, HfApi

from substrate_rs import Substrate
from substrate_rs.speech import _audio
from domains import combinatorial_recognizer as cr
from domains.vision_graph import RGBEye
from scripts.fsdd_segmentation_realspeech import frames as cframes, shape as cshape

COLORS = {"blue": 0, "green": 1, "red": 2, "white": 3}
DIGITS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
          "six": 6, "seven": 7, "eight": 8, "nine": 9}
LETTERS = {c: i for i, c in enumerate("abcdefghijklmnopqrstuvxyz")}   # a-z minus w (25)
# target word slot (env, NOT argv — a transitive import reads sys.argv[2] as an int):
#   color (char idx 1, 4 classes) / digit (idx 4, 10) / letter (idx 3, 25).
TARGET = os.environ.get("GRID_TARGET", "color")
VOCAB, CHAR_IDX = {"color": (COLORS, 1), "digit": (DIGITS, 4),
                   "letter": (LETTERS, 3)}[TARGET]
CANDS = list(range(len(VOCAB)))
CHANCE = 1.0 / len(VOCAB)
SPEAKERS = ["s1", "s2", "s3", "s4"]
SPK_DIR = "/tmp/grid_speakers"
N_FRAMES = 6


def _spk_cache(spk):
    return f"/tmp/grid_xspk_{TARGET}_{spk}.npz"
_CASC = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades,
                                           "haarcascade_frontalface_default.xml"))


def _make_eye(n_az=8):
    e = RGBEye(substrate=Substrate(), n_az=n_az, fov_h_deg=90.0, vband=0.9).build()
    e.stop()
    return e


_EYE = _make_eye()


def v1_percepts(frame_rgb):
    ps = _EYE._process_frame(None, frame_rgb, 0.0)["percepts"]
    return np.array([[p["edge_density"], p["corner_density"], p["salience"], p["luminance"]]
                     for p in ps])


def shapesig_feat(G):
    parts = []
    for ch in (0, 2):                                   # edge_density, salience
        for t in range(G.shape[0]):
            parts.append(Substrate.shape_signature(list(G[t, :, ch])))
        for col in range(G.shape[1]):
            parts.append(Substrate.shape_signature(list(G[:, col, ch])))
    return np.concatenate(parts).astype(np.float64)


def mouth_roi(frames_rgb, f0, f1):
    """Haar face detection on the word's middle frame -> lower-center mouth box, applied to
    all the word's frames (per-speaker alignment). Fallback to the s1 fixed box if no face."""
    mid = (f0 + f1) // 2
    g = cv2.cvtColor(frames_rgb[mid], cv2.COLOR_RGB2GRAY)
    faces = _CASC.detectMultiScale(g, 1.1, 5)
    if len(faces):
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        rs = slice(y + int(0.60 * h), y + int(0.92 * h))
        cs = slice(x + int(0.22 * w), x + int(0.78 * w))
    else:
        rs, cs = slice(192, 232), slice(150, 210)
    return [frames_rgb[i][rs, cs] for i in range(f0, f1)]


def _align_word(text):
    for ln in text.splitlines():
        p = ln.split()
        if len(p) == 3 and p[2] in VOCAB:
            return int(p[0]), int(p[1]), VOCAB[p[2]]
    return None


def speaker_utts(spk, n_per_color):
    """yield (seg, mpg_path) for balanced color-word utterances; mpgs are streamed to disk
    (chunked, low memory) — never z.read()'d whole into RAM."""
    import shutil
    from collections import defaultdict
    outdir = f"/tmp/grid_ex/{spk}"
    os.makedirs(outdir, exist_ok=True)
    if spk == "s1":
        api = HfApi(); files = api.list_repo_files("wissemkarous/lipreading", repo_type="dataset")
        ids = [f.split("/")[-1][:-6] for f in files if f.endswith(".align")]
        mpgs = set(f.split("/")[-1][:-4] for f in files if f.endswith(".mpg"))
        byc = defaultdict(list)                       # group by the target slot's char
        for i in ids:
            if i in mpgs and len(i) > CHAR_IDX:
                byc[i[CHAR_IDX]].append(i)
        print(f"    [{spk}] {TARGET}groups { {c: len(v) for c, v in byc.items()} }", flush=True)
        for c in byc:
            for uid in byc[c][:n_per_color]:
                aln = open(hf_hub_download("wissemkarous/lipreading",
                           f"Data/data/alignments/s1/{uid}.align", repo_type="dataset")).read()
                seg = _align_word(aln)
                if seg:
                    yield seg, hf_hub_download("wissemkarous/lipreading",
                           f"Data/data/s1/{uid}.mpg", repo_type="dataset")
    else:
        tar = tarfile.open(f"{SPK_DIR}/{spk}.tar")
        aligns = {os.path.basename(m.name)[:-6]: tar.extractfile(m).read().decode()
                  for m in tar.getmembers() if m.name.endswith(".align")}
        z = zipfile.ZipFile(f"{SPK_DIR}/{spk}.zip")
        byc = defaultdict(list)
        for n in z.namelist():
            if n.endswith(".mpg"):
                uid = os.path.basename(n)[:-4]
                if len(uid) > CHAR_IDX and uid in aligns:
                    byc[uid[CHAR_IDX]].append((uid, n))
        print(f"    [{spk}] aligns={len(aligns)} {TARGET}groups "
              f"{ {c: len(v) for c, v in byc.items()} }", flush=True)
        for c in byc:
            for uid, n in byc[c][:n_per_color]:
                seg = _align_word(aligns[uid])
                if not seg:
                    continue
                path = f"{outdir}/{uid}.mpg"
                if not os.path.exists(path):
                    with z.open(n) as src, open(path, "wb") as dst:
                        shutil.copyfileobj(src, dst, 1 << 20)
                yield seg, path


def _decode(mpg_path, kind):
    """decode all frames of one stream and CLOSE the container (ffmpeg containers hold
    decoder threads/FDs; leaking them across hundreds of utterances exhausts the thread
    table -> BlockingIOError EAGAIN). Single-threaded decode to keep the thread count flat."""
    with av.open(mpg_path) as c:
        st = (c.streams.video if kind == "video" else c.streams.audio)[0]
        st.thread_type = "NONE"
        return [f.to_ndarray(format="rgb24") if kind == "video" else f.to_ndarray()
                for f in c.decode(st)]


def feats_from_mpg(mpg_path, seg, afeat):
    f0, f1 = max(0, seg[0] // 1000 - 2), min(75, seg[1] // 1000 + 2)
    fr = _decode(mpg_path, "video")
    roi = mouth_roi(fr, f0, f1)
    idx = np.linspace(0, len(roi) - 1, N_FRAMES).round().astype(int)
    G = np.stack([v1_percepts(roi[i]) for i in idx])
    v_shape = shapesig_feat(G)
    v_raw = np.stack([cv2.resize(cv2.cvtColor(roi[i], cv2.COLOR_RGB2GRAY), (48, 32))
                      .astype(np.float64) for i in idx]).std(0).flatten()
    a0, a1 = seg[0] // 1000, max(seg[1] // 1000, seg[0] // 1000 + 1)
    ab = _decode(mpg_path, "audio")
    a = np.concatenate(ab, axis=1).mean(0) if ab[0].ndim == 2 else np.concatenate(ab)
    a8 = resample_poly(a, 8000, 44100)
    af = afeat(a8[int(a0 / 25 * 8000):int(a1 / 25 * 8000)])
    return seg[2], v_shape, v_raw, af


def extract(n_per_color):
    s = Substrate(); _audio.seed_audio_grammar(s)
    bank = _audio.cochlea(s, n_bands=24, fs=8000)

    def afeat(a):
        # SHAPE front-end (log-band minus per-frame mean = the formant FILTER) — the audio
        # cross-speaker lever, the dual of the visual shape_signature: both modalities now
        # ride gain/level-invariant SHAPE, not surface energy/appearance.
        M = cshape(cframes(s, bank, np.asarray(a, float)))
        idx = np.linspace(0, len(M) - 1, 8).round().astype(int)
        return np.stack([M[i] for i in idx]).flatten()

    # PER-SPEAKER cache so extraction is RESUMABLE across timeouts (25-class letter = ~1000
    # utts won't finish in one window; a completed speaker is never re-extracted).
    for spk in SPEAKERS:
        if os.path.exists(_spk_cache(spk)):
            print(f"  {spk}: cached, skip", flush=True); continue
        labs, Vs, Vr, A = [], [], [], []
        for seg, mpg in speaker_utts(spk, n_per_color):
            try:
                lab, vs, vr, af = feats_from_mpg(mpg, seg, afeat)
                labs.append(lab); Vs.append(vs); Vr.append(vr); A.append(af)
            except Exception as e:
                print("  skip", spk, type(e).__name__, str(e)[:40])
        np.savez(_spk_cache(spk), labs=np.array(labs), Vs=np.array(Vs),
                 Vr=np.array(Vr), A=np.array(A))
        print(f"  {spk}: {len(labs)} {TARGET}-word AV segments cached", flush=True)


def load_all():
    spk, labs, Vs, Vr, A = [], [], [], [], []
    for si, sp in enumerate(SPEAKERS):
        z = np.load(_spk_cache(sp))
        spk += [si] * len(z["labs"]); labs += list(z["labs"])
        Vs.append(z["Vs"]); Vr.append(z["Vr"]); A.append(z["A"])
    return (np.array(spk), np.array(labs), np.vstack(Vs), np.vstack(Vr), np.vstack(A))


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    print("=" * 72)
    print(f"CROSS-SPEAKER AUDIOVISUAL SPEECH — GRID {TARGET} word, leave-one-speaker-out")
    print("=" * 72)
    if not all(os.path.exists(_spk_cache(sp)) for sp in SPEAKERS):
        extract(n_per)
    np.ones((4, 4)) @ np.ones((4, 4))
    s = Substrate()
    spk, labs, Vs, Vr, A = load_all()
    print(f"  loaded {len(labs)} AV segments across {len(set(spk))} speakers", flush=True)

    word_node = {d: s.add_node("Concept", {"name": f"c{d}", cr.WORD_ATTR: 1.0}) for d in CANDS}
    term = cr.predict_reliability_weighted_term()
    am = lambda p: max(p, key=p.get)

    def acc(Xtr, Wtr, Xte, Wte):
        return np.mean([am(cr.channel_likelihood(q, Xtr, Wtr, CANDS)) == w
                        for q, w in zip(Xte, Wte)])

    def calib(X, W):
        n = max(1, len(X) // 5); p = np.random.RandomState(0).permutation(len(X))
        Xs, Ws = X[p], W[p]
        return acc(Xs[n:], Ws[n:], Xs[:n], Ws[:n])

    def fuse(pa, pv, ra, rv):
        for d in CANDS:
            s.set_attr(word_node[d], cr.P_FLAT_ATTR, float(pa[d]))
            s.set_attr(word_node[d], cr.P_TRANS_ATTR, float(pv[d]))
            s.set_attr(word_node[d], cr.R_FLAT_ATTR, float(ra))
            s.set_attr(word_node[d], cr.R_TRANS_ATTR, float(rv))
        win = s._inner.evaluate(term, {})
        return next(d for d, n in word_node.items() if n == win)

    print(f"\n  {'held-out':9} {'audio':>7} {'vis-raw':>8} {'vis-shape':>10} {'FUSED(a+shape)':>15}")
    print("  " + "-" * 56)
    agg = {k: [] for k in ("audio", "vraw", "vshape", "fused")}
    for ho in sorted(set(spk)):
        tr = spk != ho; teM = spk == ho
        Atr, Wtr = A[tr], labs[tr]
        a_acc = acc(Atr, Wtr, A[teM], labs[teM])
        vr_acc = acc(Vr[tr], Wtr, Vr[teM], labs[teM])
        vs_acc = acc(Vs[tr], Wtr, Vs[teM], labs[teM])
        ra, rv = calib(Atr, Wtr), calib(Vs[tr], Wtr)
        f_acc = np.mean([fuse(cr.channel_likelihood(A[i], Atr, Wtr, CANDS),
                              cr.channel_likelihood(Vs[i], Vs[tr], Wtr, CANDS), ra, rv) == labs[i]
                         for i in np.where(teM)[0]])
        print(f"  {SPEAKERS[ho]:9} {a_acc:7.3f} {vr_acc:8.3f} {vs_acc:10.3f} {f_acc:15.3f}")
        agg["audio"].append(a_acc); agg["vraw"].append(vr_acc)
        agg["vshape"].append(vs_acc); agg["fused"].append(f_acc)
    print("  " + "-" * 56)
    print(f"  {'MEAN':9} {np.mean(agg['audio']):7.3f} {np.mean(agg['vraw']):8.3f} "
          f"{np.mean(agg['vshape']):10.3f} {np.mean(agg['fused']):15.3f}")
    print("=" * 72)
    print(f"  vis-raw vs vis-shape = cross-speaker generalization of the lip cue (chance {CHANCE:.2f});")
    print("  FUSED = held reliability-weighted product of audio + shape_signature lip cue.")


if __name__ == "__main__":
    main()

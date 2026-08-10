"""mine_ssl_chunk_consistency — DIAGNOSTIC: does a trained self-supervised speech
model achieve the SAME-WORD SEGMENT CONSISTENCY our continuous-speech pipeline
lacks, and if so, by what MECHANISM (portable insight, not weights)?

Target (narrow): our continuous chunks fail same-word consistency. iter-13/14:
within-speaker full-DTW separation ~+0.014 (corpus-TP) .. +0.11 (landmark, weak),
NN-acc ~0.025-0.13; FSDD isolated digits within ~0.78. We mine a pretrained SSL
model (wav2vec2 / HuBERT / WavLM) as a WORKED EXAMPLE of the solution.

We measure the SAME metrics our pipeline uses (full-DTW intra/inter SEPARATION =
(inter_mean - intra_mean)/inter_mean over same-word/same-speaker pairs, plus
within/cross same-word NN-acc) on SSL per-frame representations, PER LAYER, on:
  - FSDD isolated digits (clean spans; the ~0.78 reference task);
  - LibriSpeech word segments cut by PROPORTIONAL alignment — the SAME noisy
    segmentation the agent's pipeline uses (align_chunks_to_words is proportional),
    so the comparison is apples-to-apples: the SSL repr must survive the same
    boundary jitter our chunks suffer.

Ablations to ISOLATE the mechanism (Step 2):
  - LAYER DEPTH: separation per layer 0..12 (word structure peaks mid-network).
  - CONTEXT WINDOW: word-span representation extracted from the FULL utterance
    (model sees neighbouring phones/words) vs the SAME span fed to the model
    ISOLATED (cropped audio, no context). If context-in stabilises the span, the
    portable insight is "feed the chunk WITH context", not the weights.
  - SPEAKER-INVARIANCE: within-speaker vs cross-speaker separation at the peak
    layer (are mid-layer features already speaker-normalised?).
  - RAW front-end control: the model's own CNN feature-extractor output (layer 0,
    pre-transformer) — is the consistency in the front-end or the deep stack?

NOT adopted into the pipeline. Insight-mining only. CPU, small corpus.

Run: python -m scripts.mine_ssl_chunk_consistency [model] [n_spk] [utts_per_spk]
  model in {wav2vec2, hubert, wavlm}; default wav2vec2.
"""
import os
import sys
import time
import random
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import librosa

import scripts.sentence_learning as SL
from scripts.continuous_speech_recognition import words_of

torch.set_num_threads(max(1, os.cpu_count() // 2))

MODELS = {
    "wav2vec2": "facebook/wav2vec2-base",
    "hubert": "facebook/hubert-base-ls960",
    "wavlm": "microsoft/wavlm-base",
}
FSDD_DIR = "/tmp/fsdd/recordings"
SR = 16000


# --------------------------------------------------------------------------
# SSL feature extraction (all layers at once). Returns dict layer -> (T, D)
# float32 frame matrix for one waveform. layer 0 = CNN feature projection
# (pre-transformer), 1..N = transformer encoder layer outputs.
# --------------------------------------------------------------------------

class SSL:
    def __init__(self, key):
        from transformers import AutoModel
        self.name = MODELS[key]
        self.model = AutoModel.from_pretrained(self.name)
        self.model.eval()
        self.n_layers = self.model.config.num_hidden_layers

    @torch.no_grad()
    def layers(self, wav):
        """wav: 1-D float32 @16k. Returns {layer_idx: np.ndarray(T, D)}."""
        wav = torch.from_numpy(np.ascontiguousarray(wav, dtype=np.float32))[None, :]
        # CMVN the input the way these models expect (zero-mean unit-var).
        wav = (wav - wav.mean()) / (wav.std() + 1e-7)
        out = self.model(wav, output_hidden_states=True)
        hs = out.hidden_states  # tuple length n_layers+1; [0]=feature-proj
        return {i: h[0].cpu().numpy().astype(np.float32) for i, h in enumerate(hs)}


# --------------------------------------------------------------------------
# Audio loading @16k.
# --------------------------------------------------------------------------

def load16k(path):
    x, _ = librosa.load(path, sr=SR, mono=True)
    return x.astype(np.float32)


# --------------------------------------------------------------------------
# full-DTW over frame matrices (the agent's exact consistency metric path).
# Length-normalised, unbanded. Cosine distance on L2-normed frames (SSL vectors
# are high-dim; cosine is the standard there and matches what we'd compose).
# --------------------------------------------------------------------------

def _l2(M):
    n = np.linalg.norm(M, axis=1, keepdims=True)
    return M / np.maximum(n, 1e-9)


def full_dtw(A, B):
    A = np.asarray(A, dtype=np.float32)
    B = np.asarray(B, dtype=np.float32)
    na, nb = A.shape[0], B.shape[0]
    if na == 0 or nb == 0:
        return 1e18
    A = _l2(A)
    B = _l2(B)
    prev = np.full(nb + 1, np.inf, dtype=np.float64)
    prev[0] = 0.0
    for i in range(1, na + 1):
        cur = np.full(nb + 1, np.inf)
        d_row = 1.0 - (B @ A[i - 1])          # cosine distance row
        for j in range(1, nb + 1):
            cur[j] = d_row[j - 1] + min(prev[j], cur[j - 1], prev[j - 1])
        prev = cur
    return float(prev[nb] / (na + nb))


# --------------------------------------------------------------------------
# Consistency metric — IDENTICAL shape to iter14.intra_inter_separation.
# chunks = list of (frame_matrix, word, speaker).
# --------------------------------------------------------------------------

def separation(chunks, max_pairs=1500, seed=0, cross=False, min_len=3):
    rng = random.Random(seed)
    by_ws = defaultdict(list)
    for i, (_, w, s) in enumerate(chunks):
        if len(w) >= min_len:
            by_ws[(w, s)].append(i)
    by_w = defaultdict(list)
    for i, (_, w, s) in enumerate(chunks):
        if len(w) >= min_len:
            by_w[w].append(i)
    # intra = same word, same speaker (within) OR same word any speaker (cross)
    intra = []
    if cross:
        for w, idxs in by_w.items():
            for a in range(len(idxs)):
                for b in range(a + 1, len(idxs)):
                    if chunks[idxs[a]][2] != chunks[idxs[b]][2]:
                        intra.append((idxs[a], idxs[b]))
    else:
        for (w, s), idxs in by_ws.items():
            for a in range(len(idxs)):
                for b in range(a + 1, len(idxs)):
                    intra.append((idxs[a], idxs[b]))
    rng.shuffle(intra)
    intra = intra[:max_pairs]
    # inter = different word (same speaker for within; any speaker for cross)
    by_key = defaultdict(list)
    for i, (_, w, s) in enumerate(chunks):
        if len(w) >= min_len:
            by_key[(None if cross else s)].append(i)
    inter = []
    keys = [k for k in by_key if len(by_key[k]) >= 2]
    for _ in range(len(intra) * 4):
        if not keys or len(inter) >= len(intra):
            break
        k = rng.choice(keys)
        i, j = rng.sample(by_key[k], 2)
        if chunks[i][1] != chunks[j][1]:
            inter.append((i, j))
    if not intra or not inter:
        return 0.0, 0.0, 0.0, len(intra), len(inter)
    id_ = [full_dtw(chunks[i][0], chunks[j][0]) for i, j in intra]
    xd = [full_dtw(chunks[i][0], chunks[j][0]) for i, j in inter]
    im, xm = float(np.mean(id_)), float(np.mean(xd))
    sep = (xm - im) / xm if xm > 0 else 0.0
    return sep, im, xm, len(intra), len(inter)


def shuffle_sep(chunks, **kw):
    words = [c[1] for c in chunks]
    rng = random.Random(kw.get("seed", 0) + 99)
    sh = words[:]
    rng.shuffle(sh)
    sc = [(c[0], sh[i], c[2]) for i, c in enumerate(chunks)]
    return separation(sc, **kw)[0]


def nn_acc(chunks, within=True, max_q=120, seed=0):
    """Same-word nearest-neighbour accuracy. within=True restricts neighbour pool
    to same speaker (matches iter14 within-speaker NN-acc)."""
    rng = random.Random(seed)
    by_w = defaultdict(list)
    for i, (_, w, s) in enumerate(chunks):
        by_w[w].append(i)
    # answerable queries: word recurs (within speaker if within)
    q = []
    for i, (_, w, s) in enumerate(chunks):
        others = [j for j in by_w[w] if j != i and
                  (chunks[j][2] == s if within else chunks[j][2] != s)]
        if others:
            q.append(i)
    rng.shuffle(q)
    q = q[:max_q]
    hit = tot = 0
    n = len(chunks)
    for i in q:
        s = chunks[i][2]
        best = (1e18, None)
        for j in range(n):
            if j == i:
                continue
            if within and chunks[j][2] != s:
                continue
            if (not within) and chunks[j][2] == s:
                continue
            d = full_dtw(chunks[i][0], chunks[j][0])
            if d < best[0]:
                best = (d, j)
        if best[1] is not None:
            tot += 1
            hit += (chunks[best[1]][1] == chunks[i][1])
    return (hit / tot if tot else 0.0), tot


# --------------------------------------------------------------------------
# Corpus building.
# --------------------------------------------------------------------------

def fsdd_items(n_per_digit=4):
    by = defaultdict(list)
    for fn in sorted(os.listdir(FSDD_DIR)):
        if not fn.endswith(".wav"):
            continue
        digit, spk, _ = fn[:-4].split("_")
        by[(digit, spk)].append(fn)
    out = []
    for (digit, spk), fns in by.items():
        for fn in fns[:n_per_digit]:
            out.append((os.path.join(FSDD_DIR, fn), digit, spk))
    return out


def libri_items(n_spk, utts_per_spk, seed=1):
    pairs = SL.gather_pairs()
    by_spk = defaultdict(list)
    for p in pairs:
        by_spk[p[1]].append(p)
    spk_sorted = sorted(by_spk, key=lambda s: -len(by_spk[s]))[:n_spk]
    rng = random.Random(seed)
    sel = []
    for s in spk_sorted:
        ps = list(by_spk[s])
        rng.shuffle(ps)
        sel.extend(ps[:utts_per_spk])
    return sel  # (path, sp, ch, ut, transcript)


# --------------------------------------------------------------------------
# FSDD: whole clip = one word. Per layer, chunks = (frame_matrix, digit, spk).
# --------------------------------------------------------------------------

def fsdd_chunks(ssl, items):
    feats = {}
    for path, digit, spk in items:
        x = load16k(path)
        if len(x) < SR // 20:
            continue
        L = ssl.layers(x)
        for li, M in L.items():
            feats.setdefault(li, []).append((M, digit, spk))
    return feats


# --------------------------------------------------------------------------
# LibriSpeech: proportional word spans (the agent's own align method). For each
# utterance we run the SSL model ONCE on the full audio (context preserved), then
# slice the frame sequence per word by proportional time. SSL frame rate = 50 Hz
# (20 ms). We map word i to frames [start_i, end_i) by char-weighted proportion.
# --------------------------------------------------------------------------

def _word_frame_spans(words, n_frames):
    """Proportional frame spans for words, weighted by length+1 (rough duration
    proxy) — the same proportional idea as align_chunks_to_words."""
    weights = np.array([len(w) + 1 for w in words], dtype=np.float64)
    cum = np.concatenate([[0.0], np.cumsum(weights)])
    cum /= cum[-1]
    spans = []
    for i in range(len(words)):
        a = int(round(cum[i] * n_frames))
        b = int(round(cum[i + 1] * n_frames))
        spans.append((a, max(a + 1, b)))
    return spans


def libri_chunks_in_context(ssl, sel, min_word_len=3):
    """Word spans sliced from the FULL-utterance SSL pass (context preserved)."""
    feats = {}
    meta = []  # store (x, words, spk, n_frames_per_layer) reused by isolated pass
    for path, sp, ch, ut, transcript in sel:
        words = words_of(transcript)
        if not words:
            continue
        x = load16k(path)
        if len(x) < SR // 4:
            continue
        L = ssl.layers(x)
        nf = next(iter(L.values())).shape[0]
        spans = _word_frame_spans(words, nf)
        meta.append((path, words, sp, spans))
        for li, M in L.items():
            for (w, (a, b)) in zip(words, spans):
                if len(w) < min_word_len:
                    continue
                seg = M[a:b]
                if seg.shape[0] >= 2:
                    feats.setdefault(li, []).append((seg, w, sp))
    return feats, meta


def libri_chunks_isolated(ssl, meta, layer, min_word_len=3):
    """Re-extract the SAME word spans but feed each span's AUDIO to the model
    ALONE (cropped, no neighbouring context). Tests the context-window mechanism.
    Only for one layer to keep cost bounded."""
    chunks = []
    for path, words, sp, spans in meta:
        x = load16k(path)
        nf_full = None
        # recover audio sample boundaries from frame spans (50 Hz -> 320 samples)
        # frame f covers samples ~ [f*320, f*320+400]; use 320-sample stride.
        for (w, (a, b)) in zip(words, spans):
            if len(w) < min_word_len:
                continue
            s0 = a * 320
            s1 = min(len(x), b * 320 + 400)
            crop = x[s0:s1]
            if len(crop) < SR // 25:
                continue
            L = ssl.layers(crop)
            seg = L[layer]
            if seg.shape[0] >= 2:
                chunks.append((seg, w, sp))
    return chunks


# --------------------------------------------------------------------------
# main.
# --------------------------------------------------------------------------

def report_layer_table(feats, tag, cross=False, min_len=3):
    print(f"\n--- {tag}: per-layer same-word SEPARATION "
          f"({'CROSS-speaker' if cross else 'WITHIN-speaker'}) ---")
    print(f"  {'layer':>6}{'sep':>9}{'shuf':>8}{'intra':>8}{'inter':>8}{'n':>7}")
    best = (-9, None)
    rows = {}
    for li in sorted(feats):
        ch = feats[li]
        sep, im, xm, nin, nxt = separation(ch, cross=cross, min_len=min_len)
        sh = shuffle_sep(ch, cross=cross, min_len=min_len)
        rows[li] = (sep, sh, im, xm, nin)
        flag = "" if abs(sh) < 0.03 else " WARN"
        print(f"  {li:>6}{sep:>+9.3f}{sh:>+8.3f}{im:>8.3f}{xm:>8.3f}{nin:>7}{flag}")
        if sep > best[0]:
            best = (sep, li)
    print(f"  >>> peak: layer {best[1]} sep {best[0]:+.3f}")
    return best[1], rows


def main():
    key = sys.argv[1] if len(sys.argv) > 1 else "wav2vec2"
    n_spk = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    utts = int(sys.argv[3]) if len(sys.argv) > 3 else 14
    random.seed(1)
    np.random.seed(1)

    print(f"=== SSL chunk-consistency mine: {MODELS[key]} ===")
    t0 = time.time()
    ssl = SSL(key)
    print(f"loaded {ssl.name} ({ssl.n_layers} transformer layers) "
          f"in {time.time()-t0:.0f}s")

    # ---- FSDD (clean spans, the ~0.78 reference) ----
    print("\n" + "=" * 64)
    print("FSDD isolated digits — does the SSL repr match same-word at all?")
    print("  (our agent front-end: FSDD within ~0.78; here we report SEPARATION")
    print("   AND within/cross NN-acc on SSL features)")
    print("=" * 64)
    fi = fsdd_items(n_per_digit=4)
    print(f"  {len(fi)} FSDD clips")
    t0 = time.time()
    ff = fsdd_chunks(ssl, fi)
    print(f"  extracted SSL features ({time.time()-t0:.0f}s)")
    f_peak, _ = report_layer_table(ff, "FSDD", cross=False, min_len=1)
    # NN-acc at peak layer (within + cross speaker)
    wacc, wn = nn_acc(ff[f_peak], within=True)
    cacc, cn = nn_acc(ff[f_peak], within=False)
    print(f"  FSDD peak layer {f_peak}: within-spk NN-acc {wacc:.3f} (n={wn}), "
          f"cross-spk NN-acc {cacc:.3f} (n={cn})  [agent FSDD within ~0.78]")

    # ---- LibriSpeech continuous, in-context spans (the real target) ----
    print("\n" + "=" * 64)
    print("LibriSpeech continuous — same-word consistency on PROPORTIONAL word")
    print("  spans (same noisy segmentation the agent uses). Our pipeline:")
    print("  separation +0.014 (corpus-TP) .. ~+0.11 (landmark, weak), NN ~0.03-0.13")
    print("=" * 64)
    sel = libri_items(n_spk, utts)
    print(f"  {len(sel)} utterances, {n_spk} speakers")
    t0 = time.time()
    lf, meta = libri_chunks_in_context(ssl, sel)
    nseg = len(lf[0]) if 0 in lf else 0
    print(f"  extracted {nseg} word segments in-context ({time.time()-t0:.0f}s)")
    l_peak, lrows = report_layer_table(lf, "LibriSpeech in-context", cross=False)
    wacc, wn = nn_acc(lf[l_peak], within=True)
    print(f"  Libri peak layer {l_peak}: within-spk same-word NN-acc {wacc:.3f} "
          f"(n={wn})  [agent ~0.025-0.13]")

    # ---- Step 2 ablations at the Libri peak layer ----
    print("\n" + "=" * 64)
    print("STEP 2 — ISOLATE THE MECHANISM (ablations at Libri peak layer "
          f"{l_peak})")
    print("=" * 64)

    # (a) CROSS-speaker separation at peak (speaker-invariance already there?)
    xsep, xim, xxm, xn, _ = separation(lf[l_peak], cross=True)
    xsh = shuffle_sep(lf[l_peak], cross=True)
    print(f"\n(a) SPEAKER-INVARIANCE: cross-speaker same-word separation at peak "
          f"= {xsep:+.3f} (shuf {xsh:+.3f}, intra {xim:.3f} inter {xxm:.3f})")
    print("    -> if ~ within-speaker sep, mid-layer features are already "
          "speaker-normalised.")

    # (b) RAW front-end control: layer 0 (CNN feature-proj, pre-transformer)
    r_sep, r_im, r_xm, r_n, _ = separation(lf[0], cross=False)
    print(f"\n(b) FRONT-END vs DEEP: layer-0 (CNN feat, pre-transformer) "
          f"separation = {r_sep:+.3f}  vs peak layer {l_peak} "
          f"= {lrows[l_peak][0]:+.3f}")
    print("    -> if peak >> layer-0, the consistency is the DEEP contextual "
          "stack, not the front-end.")

    # (c) CONTEXT WINDOW: same spans fed ISOLATED (no neighbouring context)
    print(f"\n(c) CONTEXT WINDOW: re-extract the SAME word spans, fed to the "
          f"model ISOLATED (cropped audio), peak layer {l_peak}...")
    t0 = time.time()
    iso = libri_chunks_isolated(ssl, meta, l_peak)
    isep, iim, ixm, inn, _ = separation(iso, cross=False)
    ish = shuffle_sep(iso, cross=False)
    print(f"    isolated-span separation = {isep:+.3f} (shuf {ish:+.3f}, n={inn}, "
          f"{time.time()-t0:.0f}s)")
    print(f"    in-context separation     = {lrows[l_peak][0]:+.3f}")
    drop = lrows[l_peak][0] - isep
    print(f"    -> context contribution = {drop:+.3f}  "
          f"({'CONTEXT is a big lever' if drop > 0.03 else 'context minor'})")

    print("\n" + "=" * 64)
    print("DONE. See docs/model_mining_chunk_consistency.md for synthesis.")
    print("=" * 64)


if __name__ == "__main__":
    main()

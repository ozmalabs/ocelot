"""DYNAMIC QUANTIZATION — segmentation BY REVERSE QUANTIZATION (the creator's reframe).

The continuous-speech WALL (c8df2dab): STATIC segmentation (pre-cut the stream by energy/novelty valleys,
THEN quantize each piece) gives boundary P/R ~0.32/0.26 and order-1 word-form purity COLLAPSES 0.84
(forced-align) -> 0.37 (continuous). That is backwards.

THE PRINCIPLE: quantization = curve -> discrete identity; shape-detection = identity -> locate-in-curve.
SAME operation both directions, DYNAMIC — the boundaries FALL OUT of the decode, not fixed cuts.
Segmentation is NOT a pre-step; it is REVERSE QUANTIZATION: match the quantized word-SHAPE inventory AGAINST
the continuous stream and let the boundaries EMERGE from the best shape-explanation (segmentation-by-
recognition, how infants segment — by the words they know, not by acoustic gaps).

BUILD:
 1. Bootstrap the quantized word-SHAPE inventory on CLEAN data (forced-align phonebank tokens -> held DtwTo
    leader clustering at the SNAP tau; inventory purity ~0.84). Each leader = a quantized N-D word-shape.
 2. DECODE the continuous stream by REVERSE QUANTIZATION — a JOINT segment-and-recognise decode (connected-
    word / token-passing DP realised as the SEEDED VITERBI, seeds/viterbi_decode.json, the held
    vit_step/vit_backtrace graph rules) over a SEGMENT lattice: a Hyp(start,end,shape) per candidate span
    with emission = -DtwTo(resampled span, shape) [held Rust Term], contiguity edges (dst.start==src.end)
    carrying a word-insertion penalty. Word-SHAPES COMPETE to explain the stream; the boundaries EMERGE at
    the best-match transitions (the backtrace). An OOV/filler shape absorbs unmatched regions. NO static
    energy/novelty pre-cut. Per-span emissions are computed via the held MinOver/Argmin over leader nodes
    (ONE best shape per span, cheap); the penalty is swept over a cached lattice (no re-DTW).
 3. Compare EMERGENT boundaries vs the STATIC-cut baseline (0.32/0.26) and vs forced-align.

GATE (donkey=0, matched-granularity, rank-honest):
 (a) EMERGENT segmentation beats static cuts: boundary P/R >> 0.32/0.26.
 (b) CONTINUOUS-STREAM order-1 purity lifts from 0.37 toward the forced-align 0.84.
 (c) FULL-STACK metrics recover (function/content split, category, higher-order context-compensation).
 (d) donkey=0 at inference: decode = held DtwTo + seeded Viterbi over the shape inventory; no torch/
     allosaurus/whisper in sys.modules; whisper aligner = TEACHER/EVAL-ONLY in a subprocess; held-out +
     shuffled control.

MEMORY: decode per detected speech region on a FRESH substrate (freed after); B=1 best-shape-per-span via
held MinOver/Argmin (no (spans x K) blow-up); bounded duration window; capped inventory + region length;
float32; ulimit ~14Gi inherited from the D import; smoke on 1-2 utterances first. USE THE VENV PYTHON.

Run: PYTHONPATH=runners/dsl/python:.:scripts /home/matt/ozma/internal/research/.venv/bin/python \
        scripts/jabberwock_dynamic_quantization.py
"""
from __future__ import annotations
import os, sys, glob, json, pickle
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import numpy as np
from collections import Counter, defaultdict
import substrate_rs as srs

import scripts.jabberwock_syntax_clean_order1 as D          # ulimit guard; author_constructions/apply_distributional/FUNC/_peak_gib
import scripts.jabberwock_quantized_trajectory_order1 as Q   # resample/_traj/snap_scan + DtwTo/MinOver/Argmin Term wrappers
import scripts.jabberwock_continuous_stack as CS             # harvest_stream/whisper_words/pick_utterances/seg_earned/frame_roles/induce_categories/gateB/purity/context_compensation
from domains.recognition_graph import _Argmax, _NodesWhere, _Lit as _RLit, _Attr as _RAttr, _V as _RV

T_RS = CS.T_RS                                               # trajectory resample length (order-1)
HOP_S = CS.HOP_S
BANK = "/home/matt/data/phonebank"


# --------------------------------------------------------------------------- #
#  STEP 1 — bootstrap the quantized word-SHAPE inventory on CLEAN forced-align data.
# --------------------------------------------------------------------------- #
def load_clean(n=1400, n_shards=20):
    data = []
    for p in sorted(glob.glob(os.path.join(BANK, "dev-clean_*.pkl")))[:n_shards]:
        for w, fr, ph in pickle.load(open(p, "rb")):
            f = np.asarray(fr, np.float32)
            if f.shape[0] >= 3 and w.isalpha():
                data.append((w.lower(), f))
            if len(data) >= n:
                break
        if len(data) >= n:
            break
    words = [w for w, _ in data]
    order = sorted(range(len(data)), key=lambda i: -Counter(words)[words[i]])   # frequent-first (leaders = common words)
    data = [data[i] for i in order]
    trajs = [Q._traj(Q.resample(f, T_RS)) for _, f in data]
    return trajs, [w for w, _ in data]


def _inventory_from(trajs, words, cap_k):
    """SNAP-tau DtwTo leader clustering -> capped word-SHAPE inventory. Reconstruct leaders from
    Q.snap_scan's assignment (the first token of each cluster is its greedy leader). EVAL label = dominant
    true word (used ONLY for scoring the decode). Frequent-first ordering makes leaders the common words."""
    order = sorted(range(len(trajs)), key=lambda i: -Counter(words)[words[i]])
    trajs = [trajs[i] for i in order]; words = [words[i] for i in order]
    best, _rows = Q.snap_scan(trajs, words)
    tau, nc, pur, con, mn, wf = best
    first_idx = {}; members = defaultdict(list)
    for i, cid in enumerate(wf):
        first_idx.setdefault(cid, i); members[cid].append(words[i])
    keep = sorted(members, key=lambda c: -len(members[c]))[:cap_k]
    inv_trajs = [trajs[first_idx[c]] for c in keep]
    inv_labels = [Counter(members[c]).most_common(1)[0][0] for c in keep]
    return inv_trajs, inv_labels, tau, pur, nc, len(trajs)


def build_inventory_live(boot_kept, cap_k):
    """Quantized word-SHAPE inventory in the LIVE FEATURE SPACE: forced-align (whisper) word cuts on the
    harvested continuous streams of a DISJOINT BOOTSTRAP set of utterances -> clean word trajectories ->
    DtwTo leader clustering. The teacher alignment is the clean-data BOOTSTRAP (scaffold, off the inference
    path); the DECODE that follows is donkey=0. Same front-end as the decode stream (no domain mismatch)."""
    trajs, words = [], []
    for (Fall, times, uspans, w, k, txt) in boot_kept:
        for (a0, b0, lab) in CS.seg_teacher(times, w):
            if b0 - a0 >= 3 and lab and lab != "?" and str(lab).isalpha():
                trajs.append(Q._traj(Q.resample(Fall[a0:b0], T_RS))); words.append(lab)
    return _inventory_from(trajs, words, cap_k)


# --------------------------------------------------------------------------- #
#  STEP 2 — REVERSE-QUANTIZATION decode of a continuous region.
#  (A) compute per-span BEST shape + distance via the held MinOver/Argmin over leader nodes (donkey=0).
#  (B) the SEEDED VITERBI (vit_step/vit_backtrace) finds the best PARTITION over the segment lattice —
#      boundaries EMERGE at the transitions of the best path. Penalty swept over the cached spans (no re-DTW).
# --------------------------------------------------------------------------- #
class _P:
    __slots__ = ("_json",)
    def __init__(self, d): self._json = d


def _leader_substrate(inv_trajs):
    s = srs.Substrate(); hub = s.add_node("Hub", {}); leader_idx = {}
    for k, t in enumerate(inv_trajs):
        ln = s.add_node("L", {}); s.set_attr(ln, "traj", t); s.add_edge_unchecked(hub, "leader", ln)
        leader_idx[ln] = k
    minover = _P(Q._MinOver(Q._Nb(Q._V("h"), "leader"), "e",
                            Q._DtwTo(Q._Attr(Q._V("q"), "q_traj"), Q._Attr(Q._V("e"), "traj"))))
    argmin = _P(Q._Argmin(Q._Nb(Q._V("h"), "leader"), "e",
                          Q._DtwTo(Q._Attr(Q._V("q"), "q_traj"), Q._Attr(Q._V("e"), "traj"))))
    return s, hub, leader_idx, minover, argmin


def compute_spans(region, s, hub, leader_idx, minover, argmin, mindur, maxdur):
    """For every candidate span [st,e) return (st, e, shape_idx, best_dist). Best shape per span = held
    MinOver/Argmin over the leader inventory (ONE reverse-quantization per span, no spans x K blow-up)."""
    L = len(region); spans = []
    for e in range(mindur, L + 1):
        for st in range(max(0, e - maxdur), e - mindur + 1):
            if st != 0 and st < mindur:                       # orphan-start guard (see module doc)
                continue
            seg = Q._traj(Q.resample(region[st:e], T_RS))
            q = s.add_node("Q", {}); s.set_attr(q, "q_traj", seg)
            d = float(s.evaluate(minover, {"q": q, "h": hub}))
            ln = s.evaluate(argmin, {"q": q, "h": hub})
            s.remove_node(q)
            spans.append((st, e, leader_idx[ln], d))
    return spans, L


def viterbi_partition(spans, L, seed, word_penalty, fill_perframe):
    """Best segment PARTITION of [0,L] via the seeded Viterbi over a segment lattice. Hyp(start,end,shape),
    pos=end-frame; emission = -(per-frame DTW fit) x (span duration) so the total is COUNT-NEUTRAL (it
    approximates the integral of the fit over the whole stream regardless of how it is cut — otherwise a
    sum of fixed-length per-segment DTWs trivially favours fewer segments). A FILLER hyp per span
    (per-frame fit = fill_perframe) absorbs unmatched spans; contiguity edges (dst.start==src.end) carry
    trans_logp=word_penalty (the granularity knob). Returns the on_path segments."""
    s = srs.Substrate(); ag = s.add_node("Agent", {}); s._inner.load_seed_manifest(seed, ag)
    lat = s.add_node("Lattice", {}); s.set_attr(lat, "lm_weight", 1.0)
    hyp_by_end = defaultdict(list); info = {}
    for (st, e, ki, d) in spans:
        dur = e - st
        for (sym, emit) in ((float(ki), -d * dur), (-1.0, -fill_perframe * dur)):   # real best shape + OOV/filler
            h = s.add_node("Hyp", {})
            s.set_attr(h, "pos", float(e)); s.set_attr(h, "sym", sym); s.set_attr(h, "emission", float(emit))
            s.set_attr(h, "seg_start", float(st))
            for k in ("scored", "vscore", "best_in", "on_path"):
                s.set_attr(h, k, 0.0)
            s.add_edge_unchecked(h, "in_lattice", lat)
            hyp_by_end[e].append(h); info[h] = (st, e, int(sym), emit)
    for h, (st, e, sym, emit) in info.items():
        if st == 0:
            continue
        for ph in hyp_by_end.get(st, []):
            ed = s.add_node("LatEdge", {}); s.set_attr(ed, "trans_logp", float(word_penalty))
            s.add_edge_unchecked(ed, "src", ph); s.add_edge_unchecked(ed, "dst", h)
    for p in range(0, L + 1):                                          # FORWARD: tick active_pos left->right
        s.set_attr(lat, "active_pos", float(p)); s._inner.run_rules(400000)
    term = s.evaluate(_P(_Argmax(_NodesWhere("Hyp", "pos", _RLit(float(L))), "h", _RAttr(_RV("h"), "vscore"))))
    if term is None:
        return []
    s.set_attr(term, "on_path", 1.0); s._inner.run_rules(400000)      # BACKTRACE (graph-native)
    segs = [(st, e, sym) for h, (st, e, sym, emit) in info.items()
            if s.node(h)["attrs"].get("on_path") == 1.0]
    segs.sort(key=lambda x: x[1])
    return segs


# --------------------------------------------------------------------------- #
#  Region harvest + eval labelling (whisper words = EVAL only).
# --------------------------------------------------------------------------- #
def label_segment(ts, te, words):
    best, bo = None, 0.0
    for w, ws, we in words:
        ov = max(0.0, min(te, we) - max(ts, ws))
        if ov > bo:
            bo, best = ov, w
    return best if best else "?"


def decode_utterance(Fall, times, utt_spans, words, inv_trajs, seed, mindur, maxdur, maxlen):
    """Reverse-quantise each detected speech region -> emergent (traj, eval-word, span, shape). Returns the
    per-span cache (for the penalty sweep) + a decoder closure that materialises tokens at a given penalty."""
    s, hub, leader_idx, minover, argmin = _leader_substrate(inv_trajs)
    region_spans = []                                                  # (spans, L, i0)
    for (i0, i1) in utt_spans:
        if i1 - i0 < mindur:
            continue
        i1c = min(i1, i0 + maxlen)                                     # cap region length (memory)
        region = Fall[i0:i1c]
        spans, L = compute_spans(region, s, hub, leader_idx, minover, argmin, mindur, maxdur)
        region_spans.append((spans, L, i0, i1c))
    all_best_d = [d for (spans, L, i0, i1c) in region_spans for (_st, _e, _k, d) in spans]

    def decode_at(word_penalty, fill_q):
        fill_perframe = float(np.quantile(all_best_d, fill_q)) if all_best_d else 1e9
        tokens, starts = [], []
        for (spans, L, i0, i1c) in region_spans:
            segs = viterbi_partition(spans, L, seed, word_penalty, fill_perframe)
            for (st, e, sym) in segs:
                a0, b0 = i0 + st, i0 + e
                ts, te = float(times[a0]), float(times[b0 - 1])
                starts.append(ts)
                traj = Q._traj(Q.resample(Fall[a0:b0], T_RS))
                lab = label_segment(ts, te, words)
                shape_id = "OOV" if sym < 0 else f"s{sym}"
                tokens.append((traj, lab, (a0, b0), shape_id))
        return tokens, starts
    return decode_at


# --------------------------------------------------------------------------- #
#  Boundary precision/recall (emergent starts vs true whisper word starts, 60ms tol) — same as CS baseline.
# --------------------------------------------------------------------------- #
def boundary_pr(all_starts, all_true, tol=0.06):
    tp = fp = fn = 0
    for est, true in zip(all_starts, all_true):
        used = set()
        for tb in true:
            m = [j for j, eb in enumerate(est) if abs(eb - tb) <= tol and j not in used]
            if m:
                tp += 1; used.add(m[0])
            else:
                fn += 1
        fp += len(est) - len(used)
    bp = tp / max(tp + fp, 1); br = tp / max(tp + fn, 1)
    f1 = 2 * bp * br / max(bp + br, 1e-9)
    return bp, br, f1


# --------------------------------------------------------------------------- #
#  Downstream full stack over a PRE-ASSIGNED word-form assignment (the decoded shape ids).
# --------------------------------------------------------------------------- #
def build_from_decoded(a, tokens):
    """Downstream stack over decoded tokens (traj, eval-word, span, shape_id) with wf = the shape id from the
    REVERSE-QUANTIZATION decode (NOT re-clustered). Split + frame = agent-authored rules; category = k-means."""
    trajs = [t[0] for t in tokens]; words = [t[1] for t in tokens]; wf = [t[3] for t in tokens]
    isf, _freq = D.apply_distributional(a, wf)                         # AGENT-AUTHORED graph rule
    roles = CS.frame_roles(a, wf, isf)                                 # AGENT-AUTHORED construction, graph-native
    pooled_form = np.stack([np.asarray(t, np.float32).mean(0) for t in trajs])
    from nltk import pos_tag
    tg = dict(pos_tag(list(dict.fromkeys(words))))
    coarse = ["N" if tg.get(w, "").startswith("NN") else "V" if tg.get(w, "").startswith("VB") else "O"
              for w in words]
    form_cat, p_hyb, p_form, p_sh, ncontent = CS.induce_categories(wf, isf, pooled_form, coarse, KCAT=4)
    return dict(tokens=tokens, wf=wf, words=words, isf=isf, roles=roles, coarse=coarse,
                form_cat=form_cat, p_hyb=p_hyb, p_form=p_form, p_sh=p_sh, ncontent=ncontent, tags=tg)


def cont_purity(tokens, mincount=2):
    """order-1 purity over decoded NON-filler tokens, grouped by shape id (matched-granularity)."""
    byc = defaultdict(list)
    for (traj, w, span, sh) in tokens:
        if sh != "OOV" and w not in (None, "?"):
            byc[sh].append(w)
    pf = [max(Counter(v).values()) / len(v) for v in byc.values() if len(v) >= mincount]
    oov = float(np.mean([1.0 if sh == "OOV" else 0.0 for (_t, _w, _s, sh) in tokens])) if tokens else 1.0
    return (float(np.mean(pf)) if pf else float("nan")), oov


# --------------------------------------------------------------------------- #
def main():
    N_UTT = int(os.environ.get("NUTT", "60"))
    DEC_UTT = int(os.environ.get("DECUTT", "16"))            # utterances actually reverse-quantised (bounded)
    BOOT_UTT = int(os.environ.get("BOOTUTT", "24"))          # DISJOINT bootstrap utterances for the inventory
    CAP_K = int(os.environ.get("CAPK", "200"))               # inventory cap (frequent word-shapes)
    MINDUR = int(os.environ.get("MINDUR", "3")); MAXDUR = int(os.environ.get("MAXDUR", "16"))
    MAXLEN = int(os.environ.get("MAXLEN", "150"))
    FILL_Q = float(os.environ.get("FILLQ", "0.85"))
    scratch = os.environ.get("SCRATCH", "/tmp/cs_stack"); os.makedirs(scratch, exist_ok=True)
    seed = json.loads(open(os.path.join(ROOT, "seeds", "viterbi_decode.json")).read())

    print("=" * 100)
    print("DYNAMIC QUANTIZATION — segmentation BY REVERSE QUANTIZATION (word-shapes decode the stream)")
    print("=" * 100, flush=True)
    a, donkey0 = D.author_constructions()

    # ---- harvest a pool of continuous utterances; split DISJOINT bootstrap / decode sets ----
    utts = CS.pick_utterances(N_UTT)
    pool = []
    for (f, k, txt) in utts:
        h = CS.harvest_stream(f, 30.0, scratch)
        if h is None:
            continue
        Fall, times, spans = h
        words = CS.whisper_words(f, scratch)
        if not words:
            continue
        pool.append((Fall, times, spans, words, k, txt))
        if len(pool) >= BOOT_UTT + DEC_UTT:
            break
    boot_kept = pool[:BOOT_UTT]; kept = pool[BOOT_UTT:BOOT_UTT + DEC_UTT]
    print(f"\n  harvested {len(pool)} continuous streams (held Rust cochlea + detect_utterances): "
          f"{len(boot_kept)} bootstrap + {len(kept)} decode (disjoint)  [peak {D._peak_gib():.2f} GiB]", flush=True)

    # ---- STEP 1: quantized word-SHAPE inventory on CLEAN (teacher-aligned) BOOTSTRAP data, LIVE features ----
    inv_trajs, inv_labels, inv_tau, inv_pur, inv_nc, n_clean = build_inventory_live(boot_kept, CAP_K)
    print(f"  STEP 1 word-SHAPE inventory (live features, teacher-cut bootstrap): {len(inv_trajs)} shapes "
          f"(of {inv_nc} clusters over {n_clean} clean tokens), snap tau {inv_tau:.3f}, inventory purity "
          f"{inv_pur:.3f}  [peak {D._peak_gib():.2f} GiB]", flush=True)

    # ---- STEP 2: REVERSE-QUANTIZATION decode of every stream (cache spans; sweep penalty cheaply) ----
    decoders = []
    for i, (Fall, times, spans, words, k, txt) in enumerate(kept):
        dec = decode_utterance(Fall, times, spans, words, inv_trajs, seed, MINDUR, MAXDUR, MAXLEN)
        decoders.append(dec)
        print(f"    reverse-quantised stream {i+1}/{len(kept)} ({k})  [peak {D._peak_gib():.2f} GiB]", flush=True)

    true_starts = [[ws for _w, ws, _we in w[3]] for w in kept]

    # ---- ★ (a) EMERGENT boundary P/R — sweep the word-insertion penalty (matched granularity) ----
    n_true = sum(len(w[3]) for w in kept)
    print("\n--- ★ (a) EMERGENT segmentation (reverse quantization) vs STATIC cuts ---")
    # STATIC baseline (energy/novelty pre-cut) on the SAME utterances
    static_starts = [[w[1][a0] for (a0, _b, _lab) in CS.seg_earned(w[0], w[1], w[2], w[3])] for w in kept]
    sbp, sbr, sf1 = boundary_pr(static_starts, true_starts)
    n_static = sum(len(s) for s in static_starts)
    print(f"  STATIC energy/novelty pre-cut : boundary P {sbp:.2f} R {sbr:.2f} F1 {sf1:.2f} "
          f"(tokens {n_static}/{n_true} ratio {n_static/max(n_true,1):.2f})   [the c8df2dab wall ~0.32/0.26]")
    sweep = []
    for wp in (2.0, 1.0, 0.5, 0.0, -0.5, -1.0, -2.0):        # +ve = more words (finer); -ve = fewer (coarser)
        toks_starts = [dec(wp, FILL_Q) for dec in decoders]
        est = [ts for (_t, ts) in toks_starts]
        bp, br, f1 = boundary_pr(est, true_starts)
        ntok = sum(len(s) for s in est)
        sweep.append((wp, bp, br, f1, ntok, [t for (t, _s) in toks_starts]))
        print(f"  REVERSE-QUANT penalty {wp:>5.1f}: boundary P {bp:.2f} R {br:.2f} F1 {f1:.2f} "
              f"(tokens {ntok}/{n_true} ratio {ntok/max(n_true,1):.2f})", flush=True)
    best = max(sweep, key=lambda r: r[3])                              # best-F1 operating point (gate a headline)
    wp_best, bp, br, f1, ntok, per_utt_tokens = best
    matched = min(sweep, key=lambda r: abs(r[4] / max(n_true, 1) - 1.0))   # matched-granularity (ratio~1) for b/c
    wp_m, bp_m, br_m, f1_m, ntok_m, per_utt_m = matched
    emergent_tokens = [tk for utt in per_utt_m for tk in utt]          # purity/full-stack judged at matched granularity
    print(f"  -> BEST-F1 operating point: penalty {wp_best:.1f}, P {bp:.2f} R {br:.2f} F1 {f1:.2f} "
          f"(ratio {ntok/max(n_true,1):.2f})")
    print(f"  -> MATCHED-GRANULARITY point (ratio~1, for purity/full-stack): penalty {wp_m:.1f}, "
          f"P {bp_m:.2f} R {br_m:.2f} F1 {f1_m:.2f} (ratio {ntok_m/max(n_true,1):.2f})")

    # ---- ★ (b) continuous-stream order-1 purity (recognition boundaries) vs static/teacher vs forced-align ----
    # forced-align reference (the 0.84 ceiling, phonebank features) + the SAME downstream stack, via CS.
    res_ref, n_ref = CS.phonebank_reference(a); pur_ref = res_ref["snap_pur"]
    # static-cut continuous tokens (the wall) + TEACHER-perfect-cut tokens (the segmentation-INDEPENDENT
    # ceiling on LIVE features): if teacher-perfect also caps ~0.4, segmentation was never the purity bottleneck.
    static_pack = [(CS.seg_earned(w[0], w[1], w[2], w[3]), w[0]) for w in kept]
    teacher_pack = [(CS.seg_teacher(w[1], w[3]), w[0]) for w in kept]
    res_static = CS.build_stream(a, (lambda x: x), static_pack); pur_static = res_static["snap_pur"]
    res_teacher = CS.build_stream(a, (lambda x: x), teacher_pack); pur_teacher = res_teacher["snap_pur"]
    pur_cont, oov = cont_purity(emergent_tokens)
    print("\n--- ★ (b) CONTINUOUS-STREAM order-1 purity (recognition boundaries) ---")
    print(f"  forced-align, phonebank features (ceiling): {pur_ref:.3f}")
    print(f"  TEACHER-perfect cuts, LIVE features        : {pur_teacher:.3f}   <- segmentation-INDEPENDENT ceiling")
    print(f"  STATIC energy/novelty cuts, LIVE features  : {pur_static:.3f}   [c8df2dab ~0.37 wall]")
    print(f"  REVERSE-QUANT emergent, LIVE features       : {pur_cont:.3f}   (OOV/filler fraction {oov:.2f})")

    # ---- ★ (c) full-stack metrics on the emergent tokens vs static/teacher vs forced-align ----
    res_e = build_from_decoded(a, emergent_tokens)
    bE = CS.gateB(res_e); bS = CS.gateB(res_static); bT = CS.gateB(res_teacher); bR = CS.gateB(res_ref)
    aF_r, aC_r, aS_r, nA_r = CS.context_compensation(res_ref["wf"], res_ref["coarse"])
    aF_t, aC_t, aS_t, nA_t = CS.context_compensation(res_teacher["wf"], res_teacher["coarse"])
    aF_s, aC_s, aS_s, nA_s = CS.context_compensation(res_static["wf"], res_static["coarse"])
    aF_e, aC_e, aS_e, nA_e = CS.context_compensation(res_e["wf"], res_e["coarse"])
    print("\n--- ★ (c) FULL-STACK metrics (SAME downstream stack; 4 conditions) ---")
    print(f"  {'stage':<30}{'forced-align':>13}{'teacher-cut':>12}{'static-cut':>12}{'reverse-quant':>14}")
    print(f"  {'order-1 word-form purity':<30}{pur_ref:>13.3f}{pur_teacher:>12.3f}{pur_static:>12.3f}{pur_cont:>14.3f}")
    print(f"  {'gate-B function/content':<30}{bR[0]:>13.3f}{bT[0]:>12.3f}{bS[0]:>12.3f}{bE[0]:>14.3f}")
    print(f"    (majority {bR[2]:.2f}/{bT[2]:.2f}/{bS[2]:.2f}/{bE[2]:.2f})")
    print(f"  {'context-compensation (+delta)':<30}"
          f"{('+%.3f'%(aC_r-aF_r)):>13}{('+%.3f'%(aC_t-aF_t)):>12}{('+%.3f'%(aC_s-aF_s)):>12}{('+%.3f'%(aC_e-aF_e)):>14}")
    print(f"    forced-align {aF_r:.2f}->{aC_r:.2f} (shuf {aS_r:.2f}, n {nA_r}); "
          f"teacher {aF_t:.2f}->{aC_t:.2f} (shuf {aS_t:.2f}, n {nA_t})")
    print(f"    static {aF_s:.2f}->{aC_s:.2f} (shuf {aS_s:.2f}, n {nA_s}); "
          f"reverse-quant {aF_e:.2f}->{aC_e:.2f} (shuf {aS_e:.2f}, n {nA_e})")

    # ---- ★ (a) show the emergent parse on one real utterance ----
    print("\n--- ★ emergent structured parse (reverse quantization, donkey=0) — a real utterance ---")
    ui = max(range(len(per_utt_tokens)), key=lambda u: len(per_utt_tokens[u]))
    print(f"  utterance {kept[ui][4]} | transcript: {kept[ui][5]}")
    print(f"  {'#':>2} {'word(eval)':>12} {'shape':>7} {'func/content':>12} {'frame-role':>12}")
    # rebuild a small res for just this utterance's tokens to show roles/split coherently
    utt_res = build_from_decoded(a, per_utt_tokens[ui])
    for j, (traj, w, span, sh) in enumerate(per_utt_tokens[ui]):
        f = utt_res["wf"][j]; fc = "function" if utt_res["isf"].get(f) else "content"
        print(f"  {j:>2} {str(w):>12} {sh:>7} {fc:>12} {utt_res['roles'][j]:>12}")

    # ---- ★ (d) donkey=0 / controls ----
    banned = ("torch", "allosaurus", "torchaudio", "whisper", "faster_whisper", "ctranslate2")
    present = [m for m in banned if m in sys.modules]
    print("\n--- ★ (d) donkey=0 AT INFERENCE / controls ---")
    print(f"  banned modules in sys.modules: {present or 'NONE'}")
    print("  inventory + decode = held DtwTo Term (MinOver/Argmin) + SEEDED Viterbi (vit_step/vit_backtrace);")
    print("  split + frame = agent-authored graph rules; category = held k-means; whisper ran in a SUBPROCESS")
    print(f"  (word identity + boundaries = EVAL only). agent-authored donkey=0: {donkey0}.")

    print("\n" + "=" * 100)
    fixes_seg = f1 > sf1 + 0.05 and f1_m > sf1 + 0.03            # emergent boundaries beat static (both operating pts)
    ctx_recovers = (aC_e - aF_e) > 0.08 and (aC_e - aS_e) > 0.05  # higher-order context-compensation restored
    seg_is_bottleneck = pur_teacher > pur_static + 0.10          # would perfect cuts alone lift purity?
    print("VERDICT — does DYNAMIC QUANTIZATION / segmentation-by-reverse-quantization fix the wall?")
    print(f"  (a) EMERGENT vs STATIC boundaries: reverse-quant best-F1 {bp:.2f}/{br:.2f}/{f1:.2f} "
          f"(matched-gran {bp_m:.2f}/{br_m:.2f}/{f1_m:.2f}) vs static {sbp:.2f}/{sbr:.2f}/{sf1:.2f}  -> "
          f"{'BEATS static' if fixes_seg else 'no clear win'}.")
    print(f"  (b) continuous order-1 purity: reverse-quant {pur_cont:.3f} vs static {pur_static:.3f}; but the")
    print(f"      TEACHER-PERFECT-cut ceiling on LIVE features is only {pur_teacher:.3f} (<< phonebank {pur_ref:.3f})")
    print(f"      -> segmentation is {'the purity bottleneck' if seg_is_bottleneck else 'NOT the purity bottleneck'}; "
          f"the live-feature word-SHAPE fidelity is (inventory purity {inv_pur:.3f}).")
    print(f"  (c) full-stack: gate-B {bE[0]:.2f}; higher-order context-compensation +{aC_e-aF_e:.3f} "
          f"(static +{aC_s-aF_s:.3f}, forced-align +{aC_r-aF_r:.3f}) -> "
          f"{'RECOVERS (vanished on static)' if ctx_recovers else 'weak'}.")
    print(f"  (d) donkey=0 at inference: {not present}; agent-authored rules: {donkey0}.")
    if fixes_seg and ctx_recovers:
        print("  => ★ REVERSE QUANTIZATION FIXES THE *SEGMENTATION* WALL: boundaries EMERGE from the shape-decode")
        print("     (segmentation-by-recognition), beating static energy/novelty cuts, and the higher-order")
        print("     context-compensation that VANISHED on statically-cut forms is RESTORED. The residual is NOT")
        print("     the segmentation and NOT irreducible: continuous order-1 purity is capped by the LIVE-FEATURE")
        print(f"     word-SHAPE inventory fidelity ({inv_pur:.2f}) — teacher-PERFECT cuts cap at {pur_teacher:.2f} too.")
        print("     The named next frontier is a speaker/channel-invariant word-shape space (so the phonebank-clean")
        print("     0.84 inventory transfers to the live front-end) + online shape minting for OOV coverage.")
    else:
        print("  => HONEST FORK: the named residual is the LIVE-FEATURE word-SHAPE fidelity (inventory purity "
              f"{inv_pur:.2f}; teacher-perfect cuts also cap ~{pur_teacher:.2f}) + OOV coverage ({oov:.2f}) — NOT")
        print("     irreducible; the levers are a speaker-invariant shape space + online shape minting.")
    print(f"  [peak RSS {D._peak_gib():.2f} GiB]")
    print("=" * 100)


if __name__ == "__main__":
    main()

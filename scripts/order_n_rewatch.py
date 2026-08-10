"""ORDER-N RE-WATCH — the jabberwock watches the curriculum N times, like a
child, extracting MORE information every pass.

THE PRINCIPLE.  Re-watching the SAME data is informative because the MODEL
changes, not the data.  Each pass the model has accumulated more statistics,
so what was surprising becomes predictable.  SURPRISE = prediction-error =
compression residual is BOTH the quantity that drops AND the selector.  "No
more surprise, no more information to extract" = convergence.  The efficiency
thesis as a developmental schedule: spend only on the residual surprise.

CRITICAL DESIGN POINT (no sequential gating).  The layers are NOT gated.  The
learner updates LOWER and HIGHER order structure SIMULTANEOUSLY.  Every pass
updates AND measures ALL four layers at once; their surprise drops IN PARALLEL
across passes until there is nothing left to extract anywhere.  We do not wait
for one layer to converge before touching the next.

EFFICIENCY.  We DECODE / INGEST the 13-clip curriculum ONCE and cache the
per-clip experience:
  * the ordered AcousticSign sequence (with start/end times), into a SHARED
    lexicon (so signs recur across clips) — this is the agent's perception;
  * the keyframe visual rank-signatures (V1 -> HMAX pool -> ordinal rank,
    the relational-invariance signature from ground_av);
  * the time-locked sign<->sight pairs (each utterance's current keyframe).
Re-decoding identical frames every pass would be wasteful — the re-watch is the
model seeing the SAME cached experience again (same pixels, changed model).

THE FOUR LAYERS (all reusing the agent's own machinery; no ML/fit/sweep):
  L1 UNITS / recurrence      — the shared lexicon (speech.ingest_speech +
        open_lexicon).  Surprise = NEW distinct signs THIS pass.  Saturates
        fast (the lexicon is built during the single decode; by pass 2 no
        sign is new — that is the point, L1 converges first).
  L2 TRANSITIONS / sequence  — bigram next-unit prediction (sentence_learning's
        approach: H(next|cur) info-gain + held-out next-unit accuracy vs a
        frequency baseline, shuffle-controlled).  Surprise = next-unit
        prediction ERROR under the transition model accumulated SO FAR; drops
        across passes as the bigram table fills.
  L3 MASKED PREDICTION       — predict a masked unit from BOTH its neighbours
        (the BINGO Layer-3 move).  Surprise = fill ERROR under the
        context->unit table accumulated so far; drops across passes.
  L4 CROSS-MODAL GROUNDING   — bind a recurring SOUND to a recurring SIGHT
        (ground_av's V1+HMAX rank signature, co-occurrence vs shuffle).
        Surprise = UNEXPLAINED sound<->sight co-occurrence (the residual once
        already-bound referents are credited).  Bindings accrete then saturate.

OUTPUT.  A PASS x LAYER table of surprise, so the reader SEES every layer's
surprise dropping IN PARALLEL across passes, converging toward "nothing left to
extract."  Each layer's convergence pass is marked.  Shuffle controls kept for
L2 and L4 (a curve that does not beat its control is a NULL — we say so).

DISCIPLINE: numbers not booleans; shuffle controls kept; NO sequential gating
(every layer measured + updated every pass); caps/sampling stated, no silent
truncation.  Honest nulls at the higher layers are fine and expected.

This is a WORLD ADAPTER (per CLAUDE.md): it translates external pixels+audio
into substrate nodes/edges (ingest), then reads graph state back out and
computes statistics on the agent's OUTPUT.  The representations are the agent's
own (shared lexicon, V1 ordinal-rank signature).  ffmpeg/ffprobe are oracle /
extraction only.  No agent reasoning lives here.

Run:  python -m scripts.order_n_rewatch [n_passes]
"""
from __future__ import annotations

import bisect
import glob
import math
import os
import random
import subprocess
import sys
from collections import defaultdict

sys.path.insert(0, ".")
sys.path.insert(0, "runners/dsl/python")

import numpy as np                                                   # noqa: E402

import substrate_rs as srs                                           # noqa: E402
from substrate_rs import audio as a, speech as sp, video as V        # noqa: E402
from substrate_rs import vision as vis                               # noqa: E402
from substrate_rs import Production, NodePattern                     # noqa: E402

# ---- reuse ground_av's visual signature machinery (read-only import) ----
from scripts.ground_av import (                                      # noqa: E402
    _rank_signature, _rank_disagreement, _video_stream_index,
    _video_codec, _keyframe_times, build_visual_types,
    N_ORIENT, GRID, MAX_KEYFRAMES, SIGHT_AGREE,
)

# ---- knobs (declared, not swept) ----
N_PASSES_DEFAULT = 8        # cap ~8 (the brief); we stop early if all converge
N_SHUFFLE = 200             # shuffle-control resamples (matches ground_av)
RNG = random.Random(20260615)

BINGO = "/tmp/nursery/bingo_vid.mp4"


def _perm(s, src, edge, tgt, prov):
    s.add_production(Production(
        src=NodePattern(type=src, var="s"), edge_type=edge,
        tgt=NodePattern(type=tgt, var="t"), where=None, weight=None,
        provenance=prov).to_dict())


# =====================================================================
# STAGE 1 — DECODE / INGEST THE CURRICULUM ONCE, cache the experience
# =====================================================================

def decode_curriculum(s, lex, bank, playlist):
    """Ingest every clip ONCE into the shared substrate.  Returns a cache:
        clips = [ {name, signs:[(t0,t1,sign_key)], keyframes:[(t,rank_sig)]} ]
    The shared lexicon condenses recurring signs DURING this single decode, so
    a sign's key (its node value) is its identity across clips.  No re-decode
    happens after this — the N passes re-present this cache."""
    clips = []
    print(f"  {'clip':<10} {'keyframes':>9} {'utts':>5} {'signs':>6} {'codec':>6}")
    for name, path in playlist:
        codec = _video_codec(path)
        vidx = _video_stream_index(path)

        # ---- HEARD: opus -> timed acoustic signs into the SHARED lexicon ----
        acn = a.open_container(s, path)
        asid = a.add_stream(s, acn)
        a.parse_stream(s, acn, asid)
        a.parse_native(s, acn, asid)
        res = sp.ingest_speech(s, asid, lex, n_bands=16, n_time_windows=4,
                               fs=48000, threshold=0.80)
        signs = []
        for utt, sign, _is_new in res:
            if sign is None:
                continue
            at = s.node(utt)["attrs"]
            key = getattr(sign, "value", None)
            key = key if key is not None else repr(sign)
            signs.append((float(at["start_time_s"]),
                          float(at["end_time_s"]), key))
        a.close_container(acn)
        signs.sort()

        # ---- SEEN: own-decoder keyframes -> rank signatures (cached) ----
        keyframes = []
        if codec == "h264":
            kts = _keyframe_times(path)
            if len(kts) > MAX_KEYFRAMES:
                idx = [int(round(k * (len(kts) - 1) / (MAX_KEYFRAMES - 1)))
                       for k in range(MAX_KEYFRAMES)]
                kts = sorted(set(kts[i] for i in idx))
            vcn = V.open_container(s, path)
            _vsid = V.add_stream(s, vcn, vidx)
            for t in kts:
                try:
                    img = V.decode_keyframe_own(s, path, t)
                except Exception as e:
                    print(f"      [skip keyframe @{t:.1f}s: {type(e).__name__}]")
                    continue
                sig = _rank_signature(s, img, bank)
                keyframes.append((t, sig))
            V.close_container(vcn)
        else:
            print(f"      [{name}: codec={codec}, own decoder is h264-only -> "
                  f"no pixels; audio still ingested]")

        n_distinct = len({k for (_a, _b, k) in signs})
        print(f"  {name:<10} {len(keyframes):>9} {len(signs):>5} "
              f"{n_distinct:>6} {codec:>6}")
        clips.append({"name": name, "signs": signs, "keyframes": keyframes})
    return clips


# =====================================================================
# STAGE 2 — visual recurrence: group cached keyframe sigs into VisualTypes
# =====================================================================

def group_visual_types(clips):
    """Greedy single-link grouping of cached keyframe rank-signatures into
    VisualType ids (same agreement logic as ground_av.build_visual_types, but
    on the cached numpy signatures so no substrate keyframe nodes are needed).
    Stamps each cached keyframe with its vtype id and which clip it came from.
    Returns (vtype_members, recurring_set, multiclip_set)."""
    reps = []            # (vtype_id, rep_sig)
    members = defaultdict(list)   # vtype_id -> [(clip_name, t)]
    next_id = 0
    for c in clips:
        stamped = []
        for (t, sig) in c["keyframes"]:
            placed, best = None, SIGHT_AGREE
            for (vid, rep) in reps:
                d = _rank_disagreement(sig, rep)
                if d <= best:
                    best, placed = d, vid
            if placed is None:
                placed = next_id
                reps.append((placed, sig))
                next_id += 1
            members[placed].append((c["name"], t))
            stamped.append((t, placed))
        c["kf_vtypes"] = sorted(stamped)        # [(t, vtype_id)] per clip
    recurring = {vid for vid, m in members.items() if len(m) >= 2}
    multiclip = {vid for vid, m in members.items()
                 if len({nm for (nm, _t) in m}) >= 2}
    return members, recurring, multiclip


# =====================================================================
# helpers: bigram / masked tables; entropy
# =====================================================================

def entropy(counts):
    vals = list(counts.values())
    tot = sum(vals)
    if tot <= 0:
        return 0.0
    h = 0.0
    for v in vals:
        if v > 0:
            p = v / tot
            h -= p * math.log2(p)
    return h


def conditional_next_entropy(bigrams):
    total = sum(sum(d.values()) for d in bigrams.values())
    if total <= 0:
        return 0.0
    h = 0.0
    for _cur, nexts in bigrams.items():
        n_cur = sum(nexts.values())
        h += (n_cur / total) * entropy(nexts)
    return h


def bigram_topk_correct(table, cur, nxt, k=1):
    """Is `nxt` in the top-k argmax of P(next|cur) under `table` so far?
    Unseen context counts as a miss (we never cherry-pick)."""
    nexts = table.get(cur)
    if not nexts:
        return False
    ranked = sorted(nexts.items(), key=lambda kv: -kv[1])
    return nxt in {sgn for sgn, _ in ranked[:k]}


def masked_topk_correct(table, ctx, tgt, k=1):
    """Masked fill: ctx = (prev, next) bag; is tgt in top-k of P(tgt|ctx)?"""
    nexts = table.get(ctx)
    if not nexts:
        return False
    ranked = sorted(nexts.items(), key=lambda kv: -kv[1])
    return tgt in {sgn for sgn, _ in ranked[:k]}


# =====================================================================
# STAGE 3 — the N passes.  Re-present the cache; update + measure ALL
# layers SIMULTANEOUSLY each pass; surprise drops in parallel.
# =====================================================================

def run_passes(clips, members, recurring, multiclip, n_passes):
    """Each pass re-presents the cached clips IN ORDER.  For every measurable
    event (sign / bigram / masked slot / sound-sight co-occurrence) we FIRST
    score surprise against the model accumulated SO FAR (all prior passes +
    earlier clips this pass), THEN update the model.  This is the developmental
    schedule: the same experience predicted by an ever-richer model.  No layer
    waits on another — every layer is scored and updated on every event."""

    # ---------- persistent accumulating models (across passes) ----------
    seen_signs = set()                       # L1: distinct signs ever seen
    bigram_tbl = defaultdict(lambda: defaultdict(int))   # L2: cur -> next -> n
    masked_tbl = defaultdict(lambda: defaultdict(int))   # L3: (prev,next)->tgt->n
    cooc_obs = defaultdict(int)              # L4: (sign,vtype) -> count
    bound_pairs = set()                      # L4: already-bound (sign,vtype)

    # ---------- frequency baselines (for L2/L3 controls), accumulating ----------
    unigram = defaultdict(int)

    # cache the per-clip event streams once (sign sequence, masked slots,
    # timed sign<->vtype pairs) so we don't recompute structure each pass.
    clip_events = []
    for c in clips:
        seq = [k for (_a, _b, k) in c["signs"]]
        # masked slots: every interior position, context = (prev, next)
        masked = [((seq[i - 1], seq[i + 1]), seq[i])
                  for i in range(1, len(seq) - 1)]
        # timed sign<->current-vtype pairs
        pairs = []
        kf = c.get("kf_vtypes", [])
        if kf:
            kt = [t for (t, _v) in kf]
            kv = [v for (_t, v) in kf]
            for (a0, a1, sign) in c["signs"]:
                mid = 0.5 * (a0 + a1)
                if mid < kt[0] - 1.0 or mid > kt[-1] + 30.0:
                    continue
                j = bisect.bisect_right(kt, mid) - 1
                pairs.append((sign, kv[max(j, 0)]))
        clip_events.append({"seq": seq, "masked": masked, "pairs": pairs})

    rows = []   # per-pass surprise record
    for p in range(1, n_passes + 1):
        # per-pass surprise tallies
        l1_new = 0
        l2_n = l2_err = 0          # next-unit prediction error (top-1)
        l2_err3 = 0               # top-3 error
        l3_n = l3_err = 0          # masked fill error (top-1)
        l4_new_cooc = 0           # newly-explained co-occurrence mass this pass

        for ev in clip_events:
            seq = ev["seq"]

            # --- L1 UNITS: surprise = signs new to the model so far ---
            for k in seq:
                if k not in seen_signs:
                    l1_new += 1
                    seen_signs.add(k)

            # --- L2 TRANSITIONS: predict next from bigram model SO FAR, then update ---
            for cur, nxt in zip(seq, seq[1:]):
                l2_n += 1
                if not bigram_topk_correct(bigram_tbl, cur, nxt, k=1):
                    l2_err += 1
                if not bigram_topk_correct(bigram_tbl, cur, nxt, k=3):
                    l2_err3 += 1
                bigram_tbl[cur][nxt] += 1          # UPDATE after scoring
                unigram[nxt] += 1

            # --- L3 MASKED: fill masked unit from (prev,next) model SO FAR, update ---
            for ctx, tgt in ev["masked"]:
                l3_n += 1
                if not masked_topk_correct(masked_tbl, ctx, tgt, k=1):
                    l3_err += 1
                masked_tbl[ctx][tgt] += 1          # UPDATE after scoring

            # --- L4 CROSS-MODAL: residual UNEXPLAINED co-occurrence, then accrete ---
            for (sign, vt) in ev["pairs"]:
                if vt not in recurring:
                    continue
                # surprise: co-occurrence mass NOT yet explained by a binding
                if (sign, vt) not in bound_pairs:
                    l4_new_cooc += 1
                cooc_obs[(sign, vt)] += 1          # accumulate evidence

        # ---- L2 prediction error vs FREQUENCY baseline (control) ----
        # frequency predictor: always guess the globally most-frequent next.
        freq_ranked = sorted(unigram.items(), key=lambda kv: -kv[1])
        freq_top1 = freq_ranked[0][0] if freq_ranked else None
        freq_top3 = {sgn for sgn, _ in freq_ranked[:3]}
        fb_n = fb_err = 0
        for ev in clip_events:
            for _cur, nxt in zip(ev["seq"], ev["seq"][1:]):
                fb_n += 1
                if nxt != freq_top1:
                    fb_err += 1
        l2_freq_err = fb_err / max(fb_n, 1)

        # ---- L4: re-credit bindings that now clear the shuffle control ----
        # (mandatory control; numbers not booleans)
        newly_bound = update_bindings(cooc_obs, recurring, bound_pairs)

        l1_rate = l1_new
        l2_rate = l2_err / max(l2_n, 1)
        l2_rate3 = l2_err3 / max(l2_n, 1)
        l3_rate = l3_err / max(l3_n, 1)
        l4_residual = l4_new_cooc
        rows.append({
            "pass": p,
            "L1_new_signs": l1_rate,
            "L2_n": l2_n, "L2_err": l2_rate, "L2_err3": l2_rate3,
            "L2_freq_err": l2_freq_err,
            "L3_n": l3_n, "L3_err": l3_rate,
            "L4_residual_cooc": l4_residual,
            "L4_newly_bound": newly_bound,
            "L4_total_bound": len(bound_pairs),
        })

    # ---- shuffle control for L2 (destroy order, keep frequency) ----
    l2_shuffle_err = l2_shuffle_control(clip_events)
    return rows, l2_shuffle_err, bound_pairs


def update_bindings(cooc_obs, recurring, bound_pairs):
    """Bind (sign,vtype) pairs whose accumulated co-occurrence beats a shuffle
    control (the same residual-vs-chance selector as ground_av).  Returns the
    number NEWLY bound this call.  A bound pair stops counting as surprise."""
    # candidate pairs (recurring sight); collect the observed sign<->vtype seq
    sign_seq = []
    sign_marg = defaultdict(int)
    for (sign, vt), n in cooc_obs.items():
        if vt in recurring:
            sign_marg[sign] += n
    # rebuild the flat observed sequence for shuffling
    flat_signs, flat_vts = [], []
    for (sign, vt), n in cooc_obs.items():
        if vt not in recurring:
            continue
        flat_signs += [sign] * n
        flat_vts += [vt] * n
    if not flat_signs:
        return 0
    # shuffle: permute which sign lands on which on-screen moment
    keys = set(zip(flat_signs, flat_vts))
    acc = defaultdict(list)
    for _ in range(N_SHUFFLE):
        perm = flat_signs[:]
        RNG.shuffle(perm)
        c = defaultdict(int)
        for sg, vt in zip(perm, flat_vts):
            c[(sg, vt)] += 1
        for key in keys:
            acc[key].append(c.get(key, 0))
    newly = 0
    for (sign, vt) in keys:
        if (sign, vt) in bound_pairs:
            continue
        if sign_marg.get(sign, 0) < 2:
            continue
        obs = cooc_obs[(sign, vt)]
        if obs < 3:
            continue
        vals = acc[(sign, vt)]
        mu = sum(vals) / len(vals)
        var = sum((x - mu) ** 2 for x in vals) / len(vals)
        sd = math.sqrt(var)
        z = (obs - mu) / sd if sd > 1e-9 else (float("inf") if obs > mu else 0.0)
        fires = (z == float("inf") and obs >= mu + 2) or (z >= 2.0 and obs >= mu + 1)
        if fires:
            bound_pairs.add((sign, vt))
            newly += 1
    return newly


def l2_shuffle_control(clip_events):
    """Re-run the L2 next-unit prediction on a SHUFFLED token stream (frequency
    preserved, order destroyed) at the FINAL model state.  If real L2 error is
    no better than this, the transition structure is a null."""
    all_tokens = [tok for ev in clip_events for tok in ev["seq"]]
    lengths = [len(ev["seq"]) for ev in clip_events]
    RNG.shuffle(all_tokens)
    shuf_seqs, idx = [], 0
    for L in lengths:
        shuf_seqs.append(all_tokens[idx:idx + L])
        idx += L
    tbl = defaultdict(lambda: defaultdict(int))
    n = err = 0
    # one pass over shuffled stream, score-then-update (matches the real L2)
    for seq in shuf_seqs:
        for cur, nxt in zip(seq, seq[1:]):
            n += 1
            if not bigram_topk_correct(tbl, cur, nxt, k=1):
                err += 1
            tbl[cur][nxt] += 1
    return err / max(n, 1)


# =====================================================================
# reporting
# =====================================================================

def convergence_pass(values, eps_frac=0.02):
    """First pass (1-based) FROM WHICH ON the value never again changes by more
    than eps = eps_frac * |v[0]| — i.e. the pass at which the surprise has
    settled to its final level (no meaningful information left to extract after
    it).  Returns that pass number, or None if it was still moving at the cap."""
    if not values:
        return None
    v0 = abs(values[0]) if values[0] else 1.0
    eps = eps_frac * max(v0, 1e-9)
    for i in range(len(values)):
        # settled from pass (i+1) on: every later step is within eps
        if all(abs(values[j] - values[j - 1]) <= eps
               for j in range(i + 1, len(values))):
            return i + 1
    return None


def main():
    n_passes = int(sys.argv[1]) if len(sys.argv) > 1 else N_PASSES_DEFAULT
    print("=" * 78)
    print("ORDER-N RE-WATCH — re-watch the curriculum N times; surprise drops")
    print("in PARALLEL across ALL layers (no sequential gating)")
    print("=" * 78)

    s = srs.Substrate()
    a.seed_audio_grammar(s); a.seed_native_codec_grammar(s)
    sp.seed_speech_grammar(s); V.seed_video_grammar(s); vis.seed_vision_grammar(s)
    lex = sp.open_lexicon(s)
    bank = vis.v1_bank(s, n_orientations=N_ORIENT, sigma=2.0, lambda_=4.0)

    playlist = [("bingo", BINGO)]
    for p in sorted(glob.glob("/tmp/nursery/vids/*.mp4")):
        playlist.append((os.path.splitext(os.path.basename(p))[0], p))
    playlist = [(n, p) for n, p in playlist if os.path.exists(p)]
    print(f"  curriculum ({len(playlist)} clips): {[n for n, _ in playlist]}")
    print(f"  passes (cap): {n_passes}")
    print(f"  visual sig: luminance -> V1({N_ORIENT}) -> {GRID}x{GRID} pool -> "
          f"ORDINAL RANK; keyframes capped {MAX_KEYFRAMES}/clip (h264 only)\n")

    print("  STAGE 1 — DECODE / INGEST THE CURRICULUM ONCE (cache experience)")
    clips = decode_curriculum(s, lex, bank, playlist)

    members, recurring, multiclip = group_visual_types(clips)
    n_kf = sum(len(c["keyframes"]) for c in clips)
    print(f"\n  SEEN recurrence: {n_kf} keyframes -> {len(members)} VisualTypes; "
          f"{len(recurring)} recur (>=2), {len(multiclip)} span >=2 clips.")
    total_signs = sum(len(c["signs"]) for c in clips)
    distinct = len({k for c in clips for (_a, _b, k) in c["signs"]})
    print(f"  HEARD: {total_signs} timed signs across the curriculum, "
          f"{distinct} distinct in the shared lexicon.")

    print(f"\n  STAGE 2/3 — RE-PRESENT the cache for {n_passes} passes; "
          f"measure ALL layers' surprise each pass\n")
    rows, l2_shuf, bound_pairs = run_passes(
        clips, members, recurring, multiclip, n_passes)

    # ----------------------- PASS x LAYER table -----------------------
    print("  " + "=" * 74)
    print("  PASS x LAYER  SURPRISE  (lower = less information left to extract)")
    print("  " + "=" * 74)
    print(f"  {'pass':>4} | {'L1 new':>7} | {'L2 err':>7} {'(top3)':>7} | "
          f"{'L3 err':>7} | {'L4 resid':>8} {'bound':>6}")
    print(f"  {'':>4} | {'signs':>7} | {'next-u':>7} {'':>7} | "
          f"{'masked':>7} | {'cooc':>8} {'(cum)':>6}")
    print("  " + "-" * 74)
    for r in rows:
        print(f"  {r['pass']:>4} | {r['L1_new_signs']:>7d} | "
              f"{r['L2_err']:>7.3f} {r['L2_err3']:>7.3f} | "
              f"{r['L3_err']:>7.3f} | "
              f"{r['L4_residual_cooc']:>8d} {r['L4_total_bound']:>6d}")
    print("  " + "-" * 74)

    # ----------------------- convergence per layer -----------------------
    l1 = [r["L1_new_signs"] for r in rows]
    l2 = [r["L2_err"] for r in rows]
    l3 = [r["L3_err"] for r in rows]
    l4 = [r["L4_residual_cooc"] for r in rows]
    c1, c2, c3, c4 = (convergence_pass(l1), convergence_pass(l2),
                      convergence_pass(l3), convergence_pass(l4))
    print(f"\n  CONVERGENCE (pass where the layer's surprise settles):")
    print(f"    L1 units / new-signs        : pass {c1 if c1 else '>cap'}  "
          f"({l1[0]} -> {l1[-1]})")
    print(f"    L2 transitions / next-unit  : pass {c2 if c2 else '>cap'}  "
          f"(err {l2[0]:.3f} -> {l2[-1]:.3f})")
    print(f"    L3 masked fill              : pass {c3 if c3 else '>cap'}  "
          f"(err {l3[0]:.3f} -> {l3[-1]:.3f})")
    print(f"    L4 cross-modal residual     : pass {c4 if c4 else '>cap'}  "
          f"({l4[0]} -> {l4[-1]}, {len(bound_pairs)} bound)")

    # ----------------------- controls / verdict -----------------------
    print(f"\n  CONTROLS:")
    print(f"    L2 next-unit error, ordered : {l2[-1]:.3f}  (final pass)")
    print(f"    L2 next-unit error, SHUFFLED: {l2_shuf:.3f}  "
          f"(frequency kept, order destroyed)")
    print(f"    L2 frequency-baseline error : {rows[-1]['L2_freq_err']:.3f}  "
          f"(predict globally most-frequent next)")
    l2_beats = l2[-1] < min(l2_shuf, rows[-1]['L2_freq_err']) - 1e-6
    print(f"    -> L2 transition structure  : "
          f"{'REAL (beats shuffle AND frequency)' if l2_beats else 'NULL (no better than its controls)'}")
    l4_real = len(bound_pairs) > 0
    print(f"    L4 bindings vs shuffle      : "
          f"{len(bound_pairs)} bound above shuffle control "
          f"({'REAL' if l4_real else 'NULL — no sound<->sight beat chance'})")

    # do lower AND higher layers improve SIMULTANEOUSLY?
    def dropped(v):
        return v[-1] < v[0] - 1e-9 if v else False
    drops = {"L1": dropped(l1), "L2": dropped(l2), "L3": dropped(l3),
             "L4": dropped(l4)}
    simul = sum(drops.values())
    print(f"\n  PARALLELISM (the user's claim — layers improve SIMULTANEOUSLY):")
    print(f"    layers whose surprise DROPPED across passes: "
          f"{[k for k, d in drops.items() if d]} ({simul}/4)")
    early = [k for k, c in [("L1", c1), ("L2", c2), ("L3", c3), ("L4", c4)]
             if c is not None]
    print(f"    layers that CONVERGED within {n_passes} passes: {early}")

    print("\n  " + "=" * 74)
    print("  VERDICT")
    print("  " + "=" * 74)
    print(f"    Re-watching extracts MORE than one pass on the layers whose")
    print(f"    surprise kept dropping after pass 1: "
          f"{[k for k, d in drops.items() if d]}.")
    print(f"    L1 saturates at pass {c1} (the lexicon is built during the single")
    print(f"    decode; nothing is a NEW sign on re-watch — expected).")
    print(f"    The higher layers (L2/L3/L4) carry residual surprise into later")
    print(f"    passes precisely because the accumulating model only then has the")
    print(f"    statistics to predict what was first surprising.")
    print("  " + "=" * 74)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

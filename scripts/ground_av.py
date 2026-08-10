"""GROUND A SOUND TO A SIGHT — cross-modal grounding for the jabberwock.

The payoff of the curriculum arc: bind a recurring SOUND to a recurring SIGHT,
so a sound comes to MEAN a thing. A recurring acoustic sign (the lexicon already
makes signs recur across clips) that reliably CO-OCCURS in time with a recurring
visual structure becomes a REFERENT in the graph: the sound DENOTES the sight.

This is a WORLD ADAPTER (per CLAUDE.md): it translates external pixels+audio into
substrate nodes/edges and reads graph state back out. The representations are the
AGENT'S OWN — the V1 oriented-edge bank (vision.py) for the seen, ingest_speech +
a shared lexicon for the heard, and the relational ORDINAL-RANK idea (the move that
cracked cross-SPEAKER audio in domains/relational_shape.py) transferred to vision.
The SELECTOR is recurrence / co-occurrence vs a shuffle control — never a fit, a
sweep, or a trained model. No ML.

THE VISUAL REPRESENTATION, AND WHY (the invariance argument)
-----------------------------------------------------------
"The same dog, appearing again" must register as the SAME sight even though it
appears at a different position, scale, illumination and colour. So the visual
signature must be invariant to exactly those nuisances. We build it the same way
the agent built its talker-invariant audio signature:

  pixels (own h264 decode)
    -> LUMINANCE (drop colour: a thing's identity is its SHAPE, not its hue;
                  this also removes any per-channel colour gain)
    -> V1 ORIENTED-EDGE BANK (vision.v1_bank: Gabor at K orientations) — the
                  agent's own primitive; edges are where structure lives
    -> COARSE G x G GRID of edge-energy per orientation (block-pool of |response|).
                  Pooling is the HMAX C-cell move (Riesenhuber-Poggio): it gives
                  POSITION and SCALE tolerance — a structure that shifts or
                  resizes by less than a grid cell yields the same pooled energy.
    -> ORDINAL RANK of the flattened (K x G x G) energy vector.  THIS is the
                  relational-shape transfer: rank(cell_i) = #cells with strictly
                  less edge-energy.  A rank profile is INVARIANT BY CONSTRUCTION
                  to any positive monotone gain on the energies (brightness /
                  contrast / colour-gain re-scale energies but do NOT reorder
                  which cells have more edge structure).  It is a RELATION among
                  the parts of the image (which region is edgier than which),
                  not the surface pixel values — exactly the whole-unit relational
                  invariance that beat surface matching cross-speaker.

  Two keyframes are "the same sight" when their rank vectors agree (small L1).
  The recurrence threshold is set from the rank SCALE (a fraction of the maximum
  possible rank disagreement), not tuned against any answer key.

RECURRENCE + BINDING IN THE GRAPH
---------------------------------
* Recurring SIGHT: keyframe rank-signatures are grouped by mutual agreement into
  VisualType nodes.  A VisualType that has >=2 member keyframes is a recurring
  sight.  Each keyframe Image -> instance_of -> VisualType.
* Recurring SOUND: the shared lexicon already condenses recurring AcousticSigns;
  a sign heard in >=2 utterances (or >=2 clips) recurs.
* CO-OCCURRENCE on the shared clock: each utterance is time-locked to the
  keyframe(s) visible during it (synchronous_with), so sign and VisualType meet
  in time.  For each (sign, VisualType) pair we count how often the sign is heard
  WHILE that visual type is on screen.
* BIND: when a (sign, VisualType) co-occurrence beats its SHUFFLE control, we add
  a Referent node with sign -denotes-> Referent -refers_to-> VisualType.  That
  edge IS the grounding: the sound denotes the sight.

CONTROL (mandatory, numbers not booleans)
-----------------------------------------
Co-occurrence is meaningless without a chance baseline.  We SHUFFLE the
sign<->time pairing (permute which utterance happens when, keeping the marginal
counts) many times and recompute every pair's co-occurrence.  A real binding
survives (observed >> shuffle mean, high z); a coincidence collapses to chance.
We report observed vs shuffle-mean co-occurrence with COUNTS, for BINGO alone and
across the whole curriculum.

Run:  python -m scripts.ground_av
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

# ---- knobs (declared, not swept; each justified, none tuned to an answer) ----
N_ORIENT = 4            # V1 orientations (vision default is 8; 4 keeps it cheap)
GRID = 6                # G x G spatial pool — coarse enough for position tolerance
MAX_KEYFRAMES = 24      # cap per clip (decode is the cost); evenly sampled
SIGHT_AGREE = 0.18      # max fractional rank-disagreement to call two sights "same"
N_SHUFFLE = 200         # shuffle-control resamples
RNG = random.Random(20260615)

BINGO = "/tmp/nursery/bingo_vid.mp4"


# =====================================================================
# world-adapter plumbing
# =====================================================================

def _perm(s, src, edge, tgt, prov):
    s.add_production(Production(
        src=NodePattern(type=src, var="s"), edge_type=edge,
        tgt=NodePattern(type=tgt, var="t"), where=None, weight=None,
        provenance=prov).to_dict())


def _video_stream_index(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=index", "-of", "csv=p=0", path],
        capture_output=True, text=True).stdout.strip()
    return int(out) if out else 0


def _video_codec(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=codec_name", "-of", "csv=p=0", path],
        capture_output=True, text=True).stdout.strip()
    return out


def _keyframe_times(path):
    """Ask the oracle (ffprobe) for every keyframe timestamp (extraction only)."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_frames",
         "-show_entries", "frame=key_frame,best_effort_timestamp_time",
         "-of", "csv=p=0", path],
        capture_output=True, text=True).stdout.strip().splitlines()
    ts = []
    for ln in out:
        parts = ln.split(",")
        if len(parts) >= 2 and parts[0] == "1":
            try:
                ts.append(float(parts[1]))
            except ValueError:
                pass
    return sorted(ts)


# =====================================================================
# the agent's VISUAL signature — V1 edges -> coarse grid -> ordinal rank
# =====================================================================

def _orientation_grid_energy(s, gray_nid, bank):
    """K x (G*G) edge-energy: block-mean of |V1 response| per orientation.

    The pooling (block-mean over G x G blocks) is the HMAX C-cell — position /
    scale tolerance.  Returned flat as one (K*G*G) energy vector."""
    feats = []
    for k in bank:
        resp = np.abs(vis.image_to_array(s, vis.convolve(s, gray_nid, k)))
        H, W = resp.shape
        for i in range(GRID):
            for j in range(GRID):
                block = resp[i * H // GRID:(i + 1) * H // GRID,
                             j * W // GRID:(j + 1) * W // GRID]
                feats.append(float(block.mean()) if block.size else 0.0)
    return np.asarray(feats, dtype=np.float64)


def _ordinal_rank(vec):
    """rank(i) = #entries strictly below entry i — the relational re-description.

    Invariant by construction to any positive monotone gain on `vec`
    (brightness / contrast / colour-gain): such a gain re-scales energies but
    does NOT change which cell is edgier than which.  This is the same ordinal
    invariant relational_shape.rank_term composes for audio, here over the
    visual energy vector.  (Computed in numpy at the I/O boundary; the STRUCTURE
    — rank of parts, matched relationally — is the agent's, identical to the
    rank_term Term-tree it evaluates natively on band frames.)"""
    order = np.argsort(np.argsort(vec, kind="stable"), kind="stable")
    return order.astype(np.float64)


def _rank_signature(s, image_nid, bank):
    arr = vis.image_to_array(s, image_nid).astype(np.float64)
    if arr.ndim == 3:
        gray = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
    else:
        gray = arr
    gray_nid = vis.image_from_array(s, gray.astype(np.float32), origin="luminance")
    energy = _orientation_grid_energy(s, gray_nid, bank)
    return _ordinal_rank(energy)


def _rank_disagreement(a, b):
    """Fractional L1 rank disagreement in [0, 1] (0 = identical ordering)."""
    n = len(a)
    max_dis = (n * n) / 2.0  # max sum|rank_i - rank_j| for two permutations of n
    return float(np.abs(a - b).sum() / max_dis) if max_dis else 0.0


# =====================================================================
# per-clip ingest: pixels -> rank signatures ; audio -> timed signs
# =====================================================================

def watch_clip(s, lex, bank, name, path):
    """Returns (keyframes, utterances) where
      keyframes  = [(t, image_nid, rank_sig)]
      utterances = [(start, end, sign_nid, utt_nid)]
    All on the shared clock.  No decisions — mechanical translation."""
    codec = _video_codec(path)
    vidx = _video_stream_index(path)

    # ---- HEARD: opus -> timed acoustic signs into the SHARED lexicon ----
    acn = a.open_container(s, path)
    asid = a.add_stream(s, acn)
    a.parse_stream(s, acn, asid)
    a.parse_native(s, acn, asid)
    res = sp.ingest_speech(s, asid, lex, n_bands=16, n_time_windows=4,
                           fs=48000, threshold=0.80)
    utts = []
    for utt, sign, _is_new in res:
        if sign is None:
            continue
        at = s.node(utt)["attrs"]
        utts.append((float(at["start_time_s"]), float(at["end_time_s"]), sign, utt))
    a.close_container(acn)

    # ---- SEEN: own-decoder keyframes -> rank signatures ----
    keyframes = []
    if codec == "h264":
        kts = _keyframe_times(path)
        if len(kts) > MAX_KEYFRAMES:
            idx = [int(round(k * (len(kts) - 1) / (MAX_KEYFRAMES - 1)))
                   for k in range(MAX_KEYFRAMES)]
            kts = sorted(set(kts[i] for i in idx))
        vcn = V.open_container(s, path)
        vsid = V.add_stream(s, vcn, vidx)
        for t in kts:
            try:
                img = V.decode_keyframe_own(s, path, t)
            except Exception as e:           # gracefully skip un-decodable AUs
                print(f"      [skip keyframe @{t:.1f}s: {type(e).__name__}]")
                continue
            sig = _rank_signature(s, img, bank)
            s.add_edge(img, "from_media", vsid)
            s.node(img)["attrs"]["time_s"] = t  # stamp on the shared clock
            keyframes.append((t, img, sig))
        V.close_container(vcn)
    else:
        print(f"      [{name}: codec={codec}, own decoder is h264-only -> "
              f"no pixels; audio still ingested]")

    return keyframes, utts


# =====================================================================
# recurrence: group keyframe signatures into VisualType nodes
# =====================================================================

def build_visual_types(s, all_keyframes):
    """Single-link agglomeration on rank agreement -> VisualType nodes.

    Greedy: each keyframe joins the first existing type whose representative it
    agrees with (disagreement <= SIGHT_AGREE), else founds a new type.  This is
    recurrence detection by the relational signature — NOT a fit.  Returns
    {visual_type_nid: [keyframe_records]} and stamps Image -instance_of-> type."""
    types = []  # list of (type_nid, rep_sig, [records])
    for rec in all_keyframes:
        t, img, sig = rec
        placed = None
        best = SIGHT_AGREE
        for ent in types:
            d = _rank_disagreement(sig, ent[1])
            if d <= best:
                best = d
                placed = ent
        if placed is None:
            tn = s.add_node("VisualType", {"n_members": 0})
            placed = (tn, sig, [])
            types.append(placed)
        placed[2].append(rec)
        s.add_edge(img, "instance_of", placed[0])
    out = {}
    for tn, _sig, recs in types:
        s.node(tn)["attrs"]["n_members"] = len(recs)
        out[tn] = recs
    return out


# =====================================================================
# co-occurrence + shuffle control
# =====================================================================

def cooccurrence(groups, vtype_of):
    """For each (sign, visual_type), count utterances heard WHILE a keyframe of
    that type is the current on-screen keyframe.

    `groups` is a list of (utts, keyframes) per clip — time matching is done
    PER CLIP because every clip's clock starts at 0 (a BINGO keyframe at t=5 and
    a bus keyframe at t=5 are different moments).  'current keyframe' for an
    utterance = the latest keyframe whose time <= the utterance midpoint (a
    keyframe persists until the next one).  Returns co[(sign, vtype)] = count,
    the observed (sign, vtype) sequence (for the shuffle control) and the
    per-sign marginal counts."""
    co = defaultdict(int)
    sign_seq = []      # (sign, current_vtype) actually observed
    sign_marg = defaultdict(int)
    vt_marg = defaultdict(int)
    for utts, keyframes in groups:
        if not keyframes:
            continue
        kt = [t for (t, _i, _s) in keyframes]
        kvt = [vtype_of[i] for (_t, i, _s) in keyframes]

        def current_vtype(mid, kt=kt, kvt=kvt):
            j = bisect.bisect_right(kt, mid) - 1
            return kvt[max(j, 0)]

        for (a0, a1, sign, _u) in utts:
            mid = 0.5 * (a0 + a1)
            if mid < kt[0] - 1.0 or mid > kt[-1] + 30.0:
                continue
            vt = current_vtype(mid)
            co[(sign, vt)] += 1
            sign_seq.append((sign, vt))
            sign_marg[sign] += 1
            vt_marg[vt] += 1
    return dict(co), sign_seq, dict(sign_marg), dict(vt_marg)


def shuffle_control(sign_seq, n=N_SHUFFLE):
    """Shuffle the sign<->vtype time pairing: keep the multiset of signs and the
    multiset of vtypes, permute which sign lands on which on-screen moment.

    Returns shuffle mean+std co-occurrence per (sign, vtype)."""
    signs = [s for s, _ in sign_seq]
    vts = [v for _, v in sign_seq]
    acc = defaultdict(list)
    for _ in range(n):
        perm = signs[:]
        RNG.shuffle(perm)
        c = defaultdict(int)
        for sg, vt in zip(perm, vts):
            c[(sg, vt)] += 1
        # record for the pairs we care about (those that ever co-occur)
        for key in set(zip(signs, vts)):
            acc[key].append(c.get(key, 0))
    stats = {}
    for key, vals in acc.items():
        m = sum(vals) / len(vals)
        var = sum((x - m) ** 2 for x in vals) / len(vals)
        stats[key] = (m, math.sqrt(var))
    return stats


def report_bindings(s, title, groups, vtype_of, recurring_vtypes,
                    min_obs=3):
    """Compute, control, and BIND.  Returns the list of bound (sign, vtype).
    `groups` = list of (utts, keyframes) per clip (clip-local clocks)."""
    print(f"\n  ---- {title} ----")
    co, sign_seq, sign_marg, vt_marg = cooccurrence(groups, vtype_of)
    if not co:
        print("    no co-occurring sound+sight on the shared clock (no pixels or "
              "no overlap).")
        return []
    stats = shuffle_control(sign_seq)
    # candidate pairs: sign recurs (>=2 utts) AND vtype recurs (>=2 keyframes)
    rows = []
    for (sign, vt), obs in co.items():
        if sign_marg.get(sign, 0) < 2:
            continue
        if vt not in recurring_vtypes:
            continue
        if obs < min_obs:
            continue
        mu, sd = stats.get((sign, vt), (0.0, 0.0))
        z = (obs - mu) / sd if sd > 1e-9 else (float("inf") if obs > mu else 0.0)
        rows.append((obs, mu, sd, z, sign, vt))
    rows.sort(key=lambda r: (-(r[3] if r[3] != float("inf") else 1e9), -r[0]))

    print(f"    {len(co)} (sound,sight) co-occurrence cells; "
          f"{len(sign_seq)} timed utterances placed on a keyframe.")
    print(f"    candidates (sign recurs>=2, sight recurs>=2, obs>={min_obs}):")
    print(f"      {'obs':>4} {'shuf_mean':>9} {'shuf_sd':>7} {'z':>6}  "
          f"{'sign':>8} -> {'sight(type)':<12} verdict")
    bound = []
    for obs, mu, sd, z, sign, vt in rows[:14]:
        zs = "inf" if z == float("inf") else f"{z:.1f}"
        # bind when clearly above the shuffle baseline; a zero-variance shuffle
        # (z=inf) still needs the observed count to exceed the shuffle mean by a
        # real margin, so a one-off coincidence cannot bind.
        fires = (z == float("inf") and obs >= mu + 2) or (z >= 2.0 and obs >= mu + 1)
        verdict = "BIND" if fires else "."
        print(f"      {obs:>4} {mu:>9.2f} {sd:>7.2f} {zs:>6}  "
              f"{str(sign):>8} -> {str(vt):<12} {verdict}")
        if fires:
            ref = s.add_node("Referent", {"strength_z": (1e9 if z == float("inf")
                                                         else round(z, 2)),
                                          "obs": obs, "shuffle_mean": round(mu, 2)})
            s.add_edge(sign, "denotes", ref)
            s.add_edge(ref, "refers_to", vt)
            bound.append((sign, vt, obs, mu, z))
    if not rows:
        print("      (none — no recurring-sound x recurring-sight pair cleared "
              "the obs floor)")
    print(f"    BOUND {len(bound)} referent(s) (sound denotes sight, beats shuffle).")
    return bound


# =====================================================================
# montage of a bound sight (proof artifact)
# =====================================================================

def save_montage(s, recs, path):
    try:
        from PIL import Image as PILImage
    except ImportError:
        return None
    imgs = []
    for (_t, img, _sig) in recs[:6]:
        arr = vis.image_to_array(s, img)
        if arr.ndim == 2:
            arr = np.stack([arr] * 3, axis=-1)
        imgs.append(np.clip(arr, 0, 255).astype(np.uint8))
    if not imgs:
        return None
    h = min(im.shape[0] for im in imgs)
    imgs = [im[:h, :, :] for im in imgs]
    canvas = np.concatenate(imgs, axis=1)
    PILImage.fromarray(canvas).save(path)
    return path


# =====================================================================
# main
# =====================================================================

def main() -> int:
    print("=" * 78)
    print("GROUNDING A SOUND TO A SIGHT — recurring heard <-> recurring seen")
    print("=" * 78)

    s = srs.Substrate()
    a.seed_audio_grammar(s); a.seed_native_codec_grammar(s); sp.seed_speech_grammar(s)
    V.seed_video_grammar(s); vis.seed_vision_grammar(s)
    _perm(s, "AcousticSign", "denotes", "Referent", "av:sign_denotes_referent")
    _perm(s, "Referent", "refers_to", "VisualType", "av:referent_refers_to_sight")
    _perm(s, "Image", "instance_of", "VisualType", "av:image_instance_of_type")
    _perm(s, "Image", "from_media", "VideoStream", "av:image_from_media")
    lex = sp.open_lexicon(s)
    bank = vis.v1_bank(s, n_orientations=N_ORIENT, sigma=2.0, lambda_=4.0)

    playlist = [("bingo", BINGO)]
    for p in sorted(glob.glob("/tmp/nursery/vids/*.mp4")):
        playlist.append((os.path.splitext(os.path.basename(p))[0], p))
    playlist = [(n, p) for n, p in playlist if os.path.exists(p)]
    print(f"  playlist ({len(playlist)}): {[n for n, _ in playlist]}")
    print(f"  visual signature: luminance -> V1({N_ORIENT} orient) -> {GRID}x{GRID} "
          f"pool -> ORDINAL RANK (invariant to position/scale/colour-gain)")
    print(f"  keyframes capped at {MAX_KEYFRAMES}/clip (own h264 decoder; "
          f"VP9 clips audio-only)\n")

    per_clip = {}     # name -> (keyframes, utts)
    all_keyframes = []
    print(f"  {'clip':<10} {'keyframes':>9} {'utts':>5} {'signs':>6}")
    for name, path in playlist:
        kf, utts = watch_clip(s, lex, bank, name, path)
        per_clip[name] = (kf, utts)
        all_keyframes.extend(kf)
        n_signs = len({g for (_a0, _a1, g, _u) in utts})
        print(f"  {name:<10} {len(kf):>9} {len(utts):>5} {n_signs:>6}")

    # ---- recurrence on the SEEN side: group signatures into VisualTypes ----
    vtypes = build_visual_types(s, all_keyframes)
    vtype_of = {}
    for tn, recs in vtypes.items():
        for (_t, img, _s) in recs:
            vtype_of[img] = tn
    recurring = {tn for tn, recs in vtypes.items() if len(recs) >= 2}
    # which clip each keyframe (Image nid) came from
    clip_of_img = {}
    for nm, (kf, _u) in per_clip.items():
        for (_t, img, _s) in kf:
            clip_of_img[img] = nm
    multiclip = sum(1 for tn, recs in vtypes.items()
                    if len({clip_of_img.get(img) for (_t, img, _s) in recs}) >= 2)
    print(f"\n  SEEN recurrence: {len(all_keyframes)} keyframes -> {len(vtypes)} "
          f"VisualTypes; {len(recurring)} recur (>=2 keyframes), "
          f"{multiclip} span >=2 clips.")

    # ---- BINGO ALONE ----
    kf_b, utts_b = per_clip["bingo"]
    bingo_bound = report_bindings(s, "BINGO ALONE (does 'Bingo' bind the dog/title?)",
                                  [(utts_b, kf_b)], vtype_of, recurring, min_obs=3)

    # ---- ACROSS THE CURRICULUM (each clip on its own clock) ----
    # a cross-curriculum binding only counts if the SIGHT itself recurs across
    # clips (a sight seen only inside one clip is a within-clip result).
    multiclip_types = {tn for tn, recs in vtypes.items()
                       if len({clip_of_img.get(img) for (_t, img, _s) in recs}) >= 2}
    groups = [(utts, kf) for (kf, utts) in per_clip.values()]
    across_bound = report_bindings(
        s, "ACROSS THE CURRICULUM (any sign binding a sight that recurs in >=2 "
        "clips?)", groups, vtype_of, multiclip_types, min_obs=4)

    # ---- montage of the strongest BINGO binding (proof artifact) ----
    montage = None
    if bingo_bound:
        sign, vt, *_ = bingo_bound[0]
        montage = save_montage(s, vtypes[vt], "/tmp/nursery/grounded_sight.png")

    # ===================== VERDICT =====================
    print("\n" + "=" * 78)
    print("  VERDICT")
    print("=" * 78)
    print(f"    BINGO-alone bindings : {len(bingo_bound)} "
          f"(sound->sight, beats shuffle)")
    print(f"    curriculum bindings  : {len(across_bound)}")
    if montage:
        print(f"    montage of a bound sight: {montage}")
    if bingo_bound or across_bound:
        print("    -> at least one SOUND grounded to a SIGHT above its shuffle "
              "control: a sign now DENOTES a recurring visual structure in the "
              "graph. Meaning grounded where the data supported it.")
    else:
        print("    -> NO sound<->sight pair beat its shuffle control. Clean NULL "
              "with a working control: recurrence on both sides exists but no "
              "reliable cross-modal co-occurrence emerged. An honest negative.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

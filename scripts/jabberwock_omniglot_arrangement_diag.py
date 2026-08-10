"""ARRANGEMENT FIDELITY -- PHASE A CONFUSION DIAGNOSIS (scratchpad/HANDWRITING_DESIGN.md's
"ARRANGEMENT FIDELITY" section, the accb0d47 residual): "before building ANYTHING," re-run
the TEST protocol only -- decodes are cheap, the LEARN codebook is COMMITTED in
seeds/stroke_shapes.json, so this script does NOT redo LEARN. It loads that seed straight onto
a fresh substrate (`boot_from_seed`, the mirror of `scripts/jabberwock_omniglot_dynamic_
quantization.py::boot()` with the stroke codebook LOADED instead of earned live) and re-runs the
SAME one-shot 20-way / held-out-alphabet / cross-drawer protocol (same `EVAL_ALPHABETS`, `WAY`,
`EPISODES_PER_ALPHABET`, `SEED`, `DK` -- imported straight from the real gate script so this is
provably the SAME protocol, not a re-implementation that could silently drift) with per-miss
instrumentation the design lists:

  (i)   TRUE-exemplar vs WINNER coverage gap distribution (a small gap -> metric/tie problem; a
        large gap -> the true exemplar's own relations genuinely don't match the query).
  (ii)  WHICH relation family mismatches against the true exemplar (strokeq / rel / cpose; for
        rel, dx/dy [position] vs do/ds [orient/scale] slots separately) -- also flags a
        STRUCTURAL mismatch (query and true exemplar decoded to a different stroke COUNT, so
        strokeq/rel simply can't align key-for-key).
  (iii) FRAME-ANCHOR SENSITIVITY: recompose the query's "rel" relations anchored on its 2nd/3rd
        stroke instead of its 1st (`_character_frame_anchored`, a diagnostic-only copy of
        `character_compose._character_frame` parameterized by which stroke supplies the
        origin/heading -- `strokeq`/`cpose` are UNCHANGED, only `rel` is recomputed, so this
        isolates frame stability specifically) -- does the true exemplar's coverage recover?
  (iv)  TIE statistics: how often the winning score ties with >=1 other candidate (metric
        saturation), and specifically how often the TRUE class ties with the actual winner (a
        tie the Argmax broke against the true class).

PHASE A ONLY -- no new machinery, no seed edits, no Rust: this script only READS the committed
codebook + drives the existing `ink_decode`/`character_compose`/coverage-Term pipeline exactly
as the real gate does, then aggregates already-computed held-Term outputs in Python (reporting,
not deciding -- CLAUDE.md's own "thin I/O-boundary" allowance: every `native.evaluate(...)` call
below is one of the SAME Terms `scripts/jabberwock_omniglot_dynamic_quantization.py` already
uses for classification; this script adds no new decision Term, it just also RECORDS the
already-computed scores/relations instead of discarding everything but the Argmax winner).

HIGHER-ORDER ARRANGEMENT RELATIONS INTERMEDIATE GATE (2026-07-03,
scratchpad/HANDWRITING_DESIGN.md's "HIGHER-ORDER ARRANGEMENT RELATIONS" section, the 97d54623
residual): this diagnosis originally measured the 52.8% tie rate that MOTIVATED "rel2"
(`domains/character_compose.py`'s `include_rel2` flag, default `False` -- opt-in, see that
module's docstring for why the default stays off). The design's own instruction is
"INTERMEDIATE GATE (before accuracy): the TIE RATE -- re-measure the phase-A tie statistic
with rel2 on (the diag script re-runs cheaply)... report which BEFORE reading the accuracy
number." `main()` below now runs THIS SAME diagnosis TWICE against the identical episode
draws (two independent `np.random.default_rng(SEED)` instances -- same seed, so the exemplar/
query file draws are byte-identical between the two passes): once scoring the DEFAULT
(`include_rel2=False`) composed signature -- reproducing the pre-rel2 baseline on THIS
script's own (possibly-since-grown) committed codebook, a same-run sanity check that the
52.8%-era number is still comparable -- and once scoring the SAME decode's
`include_rel2=True` composed signature. Both runs share ONE decode cache
(`decode_char_signature_diag` composes both signatures per file in one pass, no extra
`ink_decode` cost) so this is a clean PAIRED before/after, not two separately-drifting
measurements.

Run:
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_arrangement_diag.py
"""
from __future__ import annotations

import collections
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import resource
resource.setrlimit(resource.RLIMIT_AS, (14 * 1024 ** 3, 14 * 1024 ** 3))

import numpy as np

from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for
from domains import character_compose as cc
from domains import glyph_motor_world as gmw
from domains import ink_decode as ink
from domains import omniglot_world as ow
from domains import reflective_faculty as rf
from domains import stroke_codebook as sc

# Import the REAL gate's own protocol constants + Terms -- "same protocol", not a
# re-implementation that could silently drift from what run 6 actually measured.
from scripts.jabberwock_omniglot_dynamic_quantization import (
    DK, EVAL_ALPHABETS, EPISODES_PER_ALPHABET, SEED, WAY, _argmax_pairs_term, _coverage_term,
)

SEP = "=" * 92


# ------------------------------------------------------------------------------------------- #
# BOOT -- the ONLY difference from the real gate's own boot(): LOAD the committed stroke
# codebook (seeds/stroke_shapes.json) instead of earning it live. "decodes are cheap; LEARN
# codebook is committed" (design's own words) -- LEARN is NOT re-run.
# ------------------------------------------------------------------------------------------- #
def boot_from_seed():
    s, ag = boot_core()
    native = s._inner
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("writer_dimensions"), ag)
    native.load_seed_manifest(manifest_for("stroke_shapes"), ag)
    return s, ag, native


# ------------------------------------------------------------------------------------------- #
# DECODE -- mirrors scripts/jabberwock_omniglot_dynamic_quantization.py::decode_char_signature
# exactly (same params, same calls) but ALSO stashes the merged draw-order `stroke_points`
# (points, identity, fine_child) list the composed signature was built from -- needed for the
# frame-anchor probe below, which the real gate has no reason to keep around.
# ------------------------------------------------------------------------------------------- #
def decode_char_signature_diag(s, path, cache, dk):
    """HIGHER-ORDER ARRANGEMENT RELATIONS: composes TWO signatures per file from the SAME
    decode (no second `ink_decode` pass, no extra geometry) -- `composed_sig` (the DEFAULT,
    `include_rel2=False`, byte-identical to every prior run of this script) and
    `composed_sig_rel2` (`include_rel2=True`, the new lever) -- so `main()` can measure the
    tie-rate delta as a clean PAIRED comparison off ONE cached decode pass."""
    cached = cache.get(path)
    if cached is not None:
        return cached
    sig, n_recognized, n_oov = [], 0, 0
    stroke_points = []
    for st in ow.load_strokes(path):
        if st.shape[0] < 2:
            continue
        ink_node = ink.ingest_ink(s, st.tolist(), max_knots=dk["max_knots"])
        res = ink.decode_ink(s, ink_node, min_span=dk["min_span"], max_span=dk["max_span"],
                              segments=dk["segments"], turn_bins=dk["turn_bins"],
                              len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"])
        for r in res["recognized"]:
            sig.append(r["name"])
            n_recognized += 1
        n_oov += len(res["oov"])
        knots = s.node(ink_node)["attrs"].get("knots") or []
        stroke_points.extend(cc.decode_result_to_stroke_points(knots, res))

    composed = cc.compose_character_signature(
        s._inner, stroke_points, segments=dk["segments"], turn_bins=dk["turn_bins"],
        len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"])
    composed_rel2 = cc.compose_character_signature(
        s._inner, stroke_points, segments=dk["segments"], turn_bins=dk["turn_bins"],
        len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"], include_rel2=True)

    out = {"sig": sig, "composed_sig": composed["signature"],
           "composed_sig_rel2": composed_rel2["signature"], "n_recognized": n_recognized,
           "n_oov": n_oov, "n_strokes": len(stroke_points), "stroke_points": stroke_points}
    cache[path] = out
    return out


# ------------------------------------------------------------------------------------------- #
# (iii) FRAME-ANCHOR SENSITIVITY -- a diagnostic-only twin of
# character_compose._character_frame, parameterized by WHICH stroke's own start/heading
# supplies the frame's origin/rotation reference (the production module always anchors on
# stroke 0). Scale (`total`) is kept IDENTICAL to the default frame's own whole-path arc-length
# normalization -- only origin/orientation move, isolating frame STABILITY (position/heading)
# from scale, which the design's own "frame-anchor variance = drawer stroke-order/start noise"
# framing is specifically about. Pure geometry, mechanical -- this is diagnosis, not a new
# production Term; nothing here is installed or fed to a decision.
# ------------------------------------------------------------------------------------------- #
def _character_frame_anchored(all_pts, spans, anchor_k: int, n_probe: int = 16):
    pts = np.asarray(all_pts, dtype=float)
    if pts.ndim != 2 or pts.shape[0] < 2 or anchor_k >= len(spans):
        return None
    whole_probe = gmw._resample_arclen(pts, max(2, n_probe))
    total = float(np.sum(np.linalg.norm(np.diff(whole_probe, axis=0), axis=1))) or 1.0
    a_st, a_e = spans[anchor_k]
    anchor_pts = pts[a_st:a_e]
    if anchor_pts.shape[0] < 2:
        return None
    probe = gmw._resample_arclen(anchor_pts, max(2, min(n_probe, anchor_pts.shape[0])))
    origin = probe[0]
    heading_vec = probe[1] - probe[0]
    theta = -np.arctan2(heading_vec[1], heading_vec[0])
    c, si = np.cos(theta), np.sin(theta)
    rot = np.array([[c, -si], [si, c]])
    return ((pts - origin) @ rot.T) / total


def _recompose_rel_with_anchor(native, stroke_points, anchor_k: int, dk, include_rel2: bool = False):
    """Recompute ONLY the `rel` relations (strokeq/cpose/strokeq_fine untouched -- a targeted
    re-anchor, per this module's own docstring) anchored on stroke `anchor_k` instead of stroke
    0. Returns the alternate composed signature, or None if the anchor/geometry is degenerate
    (too few strokes, a single-point anchor stroke).

    `include_rel2` (HIGHER-ORDER ARRANGEMENT RELATIONS, default `False` -- matches
    `compose_character_signature`'s own opt-in default): when the CALLER is scoring the
    `composed_sig_rel2` arm, this must ALSO re-derive `rel2` from the re-anchored `rel`
    values (`cc._rel2_relations`, the SAME mechanical derivation `compose_character_
    signature` itself uses) rather than silently dropping rel2 from the re-anchored probe --
    otherwise a frame-anchor recovery check against a rel2-carrying exemplar would be
    comparing a rel2-less alternate against a rel2-having true exemplar, structurally unable
    to ever recover the points rel2 contributes (a false negative on frame-anchor recovery,
    not a real one)."""
    all_pts = np.concatenate(
        [np.asarray(pts, dtype=float).reshape(-1, 2) for (pts, _n, _fc) in stroke_points], axis=0)
    if all_pts.shape[0] < 2:
        return None
    spans = []
    offset = 0
    for (pts, _n, _fc) in stroke_points:
        n = np.asarray(pts, dtype=float).reshape(-1, 2).shape[0]
        spans.append((offset, offset + n))
        offset += n
    frame = _character_frame_anchored(all_pts, spans, anchor_k)
    if frame is None:
        return None
    bbox = cc._frame_bbox(frame)

    # The UNCHANGED parts (strokeq / cpose / strokeq_fine): recompute via the SAME
    # compose_character_signature call, we just replace its "rel"/"rel2" relations below.
    base = cc.compose_character_signature(
        native, stroke_points, segments=dk["segments"], turn_bins=dk["turn_bins"],
        len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"])
    non_rel = [r for r in base["signature"] if r[0] not in ("rel", "rel2")]

    rel_rels = []
    pose_by_k = {}
    for k, (st, e) in enumerate(spans):
        span_frame_pts = frame[st:e]
        if span_frame_pts.shape[0] < 2:
            continue
        qk = sc._quantize(native, span_frame_pts.tolist(), segments=dk["segments"],
                          turn_bins=dk["turn_bins"], len_bins=dk["len_bins"], grid=dk["grid"],
                          scale_bins=dk["scale_bins"], invariant_only=False, bounds=bbox)
        pose = qk["pose"]
        rel_rels.append(["rel", k, pose["x_q"], pose["y_q"], pose["orient_q"], pose["scale_q"]])
        pose_by_k[k] = pose
    rel2_rels = cc._rel2_relations(pose_by_k, dk["turn_bins"]) if include_rel2 else []
    return non_rel + rel_rels + rel2_rels


# ------------------------------------------------------------------------------------------- #
# (ii) RELATION-FAMILY MISMATCH -- pure Python bookkeeping over TWO ALREADY-DECIDED relation
# lists (the query's and the true exemplar's own composed signatures) -- not a ranking, a
# structural diff report the design's phase A explicitly asks for.
# ------------------------------------------------------------------------------------------- #
def _relation_mismatch(query_sig, true_sig) -> dict:
    def _index(sig):
        strokeq, rel, cpose, fine = {}, {}, {}, {}
        for r in sig:
            pred = r[0]
            if pred == "strokeq":
                strokeq[r[1]] = r[2]
            elif pred == "rel":
                rel[r[1]] = tuple(r[2:6])
            elif pred == "strokeq_fine":
                fine[r[1]] = r[2]
            elif pred.startswith("cpose_"):
                cpose[pred] = r[1]
        return strokeq, rel, cpose, fine

    q_strokeq, q_rel, q_cpose, q_fine = _index(query_sig)
    t_strokeq, t_rel, t_cpose, t_fine = _index(true_sig)

    structural = set(q_strokeq) != set(t_strokeq)
    strokeq_mismatches = sum(1 for k, v in q_strokeq.items() if t_strokeq.get(k) != v)
    shared_k = set(q_rel) & set(t_rel)
    rel_pos_mismatches = sum(1 for k in shared_k if q_rel[k][0:2] != t_rel[k][0:2])
    rel_orient_scale_mismatches = sum(1 for k in shared_k if q_rel[k][2:4] != t_rel[k][2:4])
    cpose_mismatches = {p: (q_cpose.get(p) != t_cpose.get(p)) for p in
                        ("cpose_x", "cpose_y", "cpose_o", "cpose_s") if p in q_cpose or p in t_cpose}
    fine_shared = set(q_fine) & set(t_fine)
    fine_mismatches = sum(1 for k in fine_shared if q_fine[k] != t_fine[k])

    return {"structural": structural, "n_strokeq_q": len(q_strokeq), "n_strokeq_t": len(t_strokeq),
            "strokeq_mismatches": strokeq_mismatches, "rel_pos_mismatches": rel_pos_mismatches,
            "rel_orient_scale_mismatches": rel_orient_scale_mismatches,
            "cpose_mismatches": cpose_mismatches, "fine_mismatches": fine_mismatches,
            "n_shared_rel_k": len(shared_k)}


# ------------------------------------------------------------------------------------------- #
# TEST + INSTRUMENTATION -- mirrors run_test's own composed-arm loop (SAME episode draws, SAME
# coverage+Argmax Terms) but records the per-miss diagnostics instead of only tallying accuracy.
# ------------------------------------------------------------------------------------------- #
def run_diagnosis(s, native, alphabets, way, episodes_per_alphabet, dk, rng, sig_key="composed_sig"):
    """`sig_key` (HIGHER-ORDER ARRANGEMENT RELATIONS, default `"composed_sig"` — every
    pre-existing call keeps its byte-identical, `include_rel2=False` behaviour): selects
    WHICH of `decode_char_signature_diag`'s two cached composed signatures classification
    scores against — `"composed_sig"` (the default arm, no rel2) or `"composed_sig_rel2"`
    (`include_rel2=True`). `main()` calls this TWICE, once per key, off the SAME decode
    cache, for a paired before/after tie-rate comparison."""
    cache = {}
    misses = []
    n_episodes = n_correct = 0
    tie_episodes = 0
    tie_true_with_winner = 0
    total_oov = total_spans = 0

    for alph in alphabets:
        chars = sorted(ow.characters(alph, "evaluation"))
        if len(chars) < way:
            print(f"  SKIPPED alphabet {alph!r}: only {len(chars)} characters, need {way}")
            continue
        chars = chars[:way]
        drawer_files = [ow.drawings(cd) for cd in chars]
        n_drawers = min(len(fl) for fl in drawer_files)
        ex_drawer = int(rng.integers(n_drawers))
        exemplars = [decode_char_signature_diag(s, drawer_files[ci][ex_drawer], cache, dk)
                     for ci in range(way)]
        exemplar_composed = [e[sig_key] for e in exemplars]

        for qi in range(min(episodes_per_alphabet, way)):
            q_drawer = int(rng.integers(n_drawers))
            while q_drawer == ex_drawer:
                q_drawer = int(rng.integers(n_drawers))
            path = drawer_files[qi][q_drawer]
            qd = decode_char_signature_diag(s, path, cache, dk)
            total_oov += qd["n_oov"]
            total_spans += qd["n_recognized"] + qd["n_oov"]

            pairs = [(float(native.evaluate(_coverage_term(qd[sig_key], exemplar_composed[ci]), {}) or 0.0), ci)
                     for ci in range(way)]
            winner = native.evaluate(_argmax_pairs_term(pairs), {})
            pred = winner[1] if winner is not None else -1
            n_episodes += 1

            scores = [p[0] for p in pairs]
            max_score = max(scores)
            true_score = pairs[qi][0]
            n_tied_at_max = sum(1 for sc_ in scores if sc_ == max_score)
            if n_tied_at_max > 1:
                tie_episodes += 1
            if true_score == max_score and pred != qi:
                tie_true_with_winner += 1

            if pred == qi:
                n_correct += 1
                continue

            # ---- MISS: run the full instrumentation. ----
            mismatch = _relation_mismatch(qd[sig_key], exemplar_composed[qi])

            # (iii) frame-anchor sensitivity: re-anchor on stroke 1 and stroke 2 (2nd/3rd
            # stroke), see if the TRUE exemplar's coverage recovers (>= the original winner).
            recoveries = []
            for anchor_k in (1, 2):
                alt_sig = _recompose_rel_with_anchor(
                    native, qd["stroke_points"], anchor_k, dk,
                    include_rel2=(sig_key == "composed_sig_rel2"))
                if alt_sig is None:
                    continue
                alt_true_score = float(native.evaluate(
                    _coverage_term(alt_sig, exemplar_composed[qi]), {}) or 0.0)
                recoveries.append({"anchor_k": anchor_k, "alt_true_score": alt_true_score,
                                   "recovered_to_win": alt_true_score >= max_score,
                                   "improved": alt_true_score > true_score})

            misses.append({
                "alphabet": alph, "qi": qi, "pred": pred, "true_score": true_score,
                "winner_score": max_score, "gap": max_score - true_score,
                "n_tied_at_max": n_tied_at_max, "mismatch": mismatch,
                "recoveries": recoveries,
            })

    return dict(n_episodes=n_episodes, n_correct=n_correct, misses=misses,
                tie_episodes=tie_episodes, tie_true_with_winner=tie_true_with_winner,
                oov_rate=total_oov / max(1, total_spans))


# ------------------------------------------------------------------------------------------- #
# REPORT -- prints one diagnosis's full (i)-(iv) + ranked-verdict section (UNCHANGED content/
# wording from the original single-arm script) and returns the summary numbers `main()` needs
# for the before/after delta. `label` distinguishes the two arms in the printed headers.
# ------------------------------------------------------------------------------------------- #
def _report_diag(diag, label: str) -> dict:
    n = diag["n_episodes"]
    n_correct = diag["n_correct"]
    n_miss = len(diag["misses"])
    acc = n_correct / max(1, n)
    print(f"\n{SEP}\n  RESULT [{label}]: {n_correct}/{n} correct ({100*acc:.1f}%), {n_miss} "
          f"misses ({100*n_miss/max(1,n):.1f}%). test-time OOV rate: "
          f"{100*diag['oov_rate']:.1f}%\n{SEP}")

    misses = diag["misses"]
    summary = {"label": label, "n": n, "n_correct": n_correct, "acc": acc, "n_miss": n_miss}
    if not misses:
        print("\n  no misses to diagnose -- nothing to rank.")
        summary["tie_rate"] = 0.0
        return summary

    # ------------------------------------------------------------------------------------- #
    # (i) COVERAGE GAP DISTRIBUTION
    # ------------------------------------------------------------------------------------- #
    gaps = np.array([m["gap"] for m in misses], dtype=float)
    print(f"\n{SEP}\n  (i) TRUE-EXEMPLAR vs WINNER COVERAGE GAP [{label}]\n{SEP}")
    print(f"  gap (winner_score - true_score) over {n_miss} misses: "
          f"min={gaps.min():.0f} mean={gaps.mean():.2f} median={np.median(gaps):.1f} "
          f"max={gaps.max():.0f}")
    small_gap = int(np.sum(gaps <= 1))
    mid_gap = int(np.sum((gaps > 1) & (gaps <= 3)))
    large_gap = int(np.sum(gaps > 3))
    print(f"  gap<=1 (metric/tie-sensitive): {small_gap}/{n_miss}  "
          f"gap 2-3: {mid_gap}/{n_miss}  gap>3 (genuine mismatch): {large_gap}/{n_miss}")

    # ------------------------------------------------------------------------------------- #
    # (ii) RELATION-FAMILY MISMATCH
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  (ii) MISMATCHING RELATION FAMILY vs TRUE EXEMPLAR [{label}]\n{SEP}")
    n_structural = sum(1 for m in misses if m["mismatch"]["structural"])
    total_strokeq_mm = sum(m["mismatch"]["strokeq_mismatches"] for m in misses)
    total_rel_pos_mm = sum(m["mismatch"]["rel_pos_mismatches"] for m in misses)
    total_rel_os_mm = sum(m["mismatch"]["rel_orient_scale_mismatches"] for m in misses)
    total_fine_mm = sum(m["mismatch"]["fine_mismatches"] for m in misses)
    cpose_mm_counter = collections.Counter()
    for m in misses:
        for p, mismatched in m["mismatch"]["cpose_mismatches"].items():
            if mismatched:
                cpose_mm_counter[p] += 1
    n_any_rel_mm = sum(1 for m in misses if m["mismatch"]["rel_pos_mismatches"] > 0
                       or m["mismatch"]["rel_orient_scale_mismatches"] > 0)
    n_any_strokeq_mm = sum(1 for m in misses if m["mismatch"]["strokeq_mismatches"] > 0)
    n_any_cpose_mm = sum(1 for m in misses if any(m["mismatch"]["cpose_mismatches"].values()))
    print(f"  structural (query/true-exemplar stroke COUNT differs): {n_structural}/{n_miss} misses")
    print(f"  misses with >=1 strokeq (identity) mismatch:  {n_any_strokeq_mm}/{n_miss}  "
          f"(total strokeq mismatches: {total_strokeq_mm})")
    print(f"  misses with >=1 rel (arrangement) mismatch:   {n_any_rel_mm}/{n_miss}  "
          f"(total rel-position[dx/dy] mismatches: {total_rel_pos_mm}, "
          f"total rel-orient/scale[do/ds] mismatches: {total_rel_os_mm})")
    print(f"  misses with >=1 cpose (global pose) mismatch: {n_any_cpose_mm}/{n_miss}  "
          f"(by predicate: {dict(cpose_mm_counter)})")
    print(f"  total strokeq_fine mismatches (eager children, shared k only): {total_fine_mm}")

    # ------------------------------------------------------------------------------------- #
    # (iii) FRAME-ANCHOR SENSITIVITY
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  (iii) FRAME-ANCHOR SENSITIVITY (re-anchor query's `rel` on stroke 1/2 "
          f"instead of stroke 0) [{label}]\n{SEP}")
    all_recoveries = [r for m in misses for r in m["recoveries"]]
    n_probed = len(all_recoveries)
    n_recovered_to_win = sum(1 for r in all_recoveries if r["recovered_to_win"])
    n_improved = sum(1 for r in all_recoveries if r["improved"])
    misses_with_any_recovery = sum(1 for m in misses
                                   if any(r["recovered_to_win"] for r in m["recoveries"]))
    print(f"  {n_probed} anchor-probes attempted across {n_miss} misses "
          f"(some misses have <2 strokes or a degenerate anchor stroke -- skipped, honest).")
    print(f"  probes that RECOVER the true exemplar to >= the original winner's score: "
          f"{n_recovered_to_win}/{max(1,n_probed)}")
    print(f"  probes that merely IMPROVE the true exemplar's score (may still lose): "
          f"{n_improved}/{max(1,n_probed)}")
    print(f"  MISSES where >=1 alternate anchor would have flipped the decision: "
          f"{misses_with_any_recovery}/{n_miss} "
          f"({100*misses_with_any_recovery/n_miss:.1f}%)")

    # ------------------------------------------------------------------------------------- #
    # (iv) TIE STATISTICS
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  (iv) TIE STATISTICS [{label}]\n{SEP}")
    print(f"  episodes where the winning score ties with >=1 other candidate: "
          f"{diag['tie_episodes']}/{n} ({100*diag['tie_episodes']/n:.1f}%)")
    print(f"  episodes where the TRUE class ties the winner's score but lost the tie-break "
          f"(Argmax picked a DIFFERENT, lower/earlier-indexed candidate): "
          f"{diag['tie_true_with_winner']}/{n} ({100*diag['tie_true_with_winner']/n:.1f}%)")
    miss_ties = sum(1 for m in misses if m["n_tied_at_max"] > 1)
    tie_rate = 100 * miss_ties / n_miss
    print(f"  of the {n_miss} misses, {miss_ties} ({tie_rate:.1f}%) had a tie at "
          f"the winning score.")

    # ------------------------------------------------------------------------------------- #
    # RANKED VERDICT
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  RANKED VERDICT [{label}]\n{SEP}")
    lever_frame = 100 * misses_with_any_recovery / n_miss
    lever_metric_smallgap = 100 * small_gap / n_miss
    lever_metric_tie = tie_rate
    lever_relgrain = 100 * n_any_rel_mm / n_miss
    lever_strokeq = 100 * n_any_strokeq_mm / n_miss
    lever_structural = 100 * n_structural / n_miss
    print(f"  LEVER 1 (frame instability)            -- alternate-anchor recovery rate: "
          f"{lever_frame:.1f}% of misses")
    print(f"  LEVER 2a (coverage metric: tie/saturation) -- misses decided by a tie:      "
          f"{lever_metric_tie:.1f}% of misses")
    print(f"  LEVER 2b (coverage metric: small gap)      -- gap<=1 (metric-sensitive):    "
          f"{lever_metric_smallgap:.1f}% of misses")
    print(f"  (context) rel/arrangement relations mismatch vs true exemplar: "
          f"{lever_relgrain:.1f}% of misses")
    print(f"  (context) strokeq/identity relations mismatch vs true exemplar: "
          f"{lever_strokeq:.1f}% of misses")
    print(f"  (context) structural (stroke-count) mismatch vs true exemplar: "
          f"{lever_structural:.1f}% of misses")

    candidates = [("frame instability (LEVER 1)", lever_frame),
                  ("coverage metric -- ties (LEVER 2a)", lever_metric_tie),
                  ("coverage metric -- small gap (LEVER 2b)", lever_metric_smallgap)]
    candidates.sort(key=lambda t: -t[1])
    print(f"\n  RANKING (by fraction of misses explained): "
          + ", ".join(f"{name}={val:.1f}%" for name, val in candidates))
    print(f"  TOP-RANKED LEVER: {candidates[0][0]}")

    summary.update(tie_rate=tie_rate, small_gap_rate=lever_metric_smallgap,
                   frame_rate=lever_frame)
    return summary


# ------------------------------------------------------------------------------------------- #
# MAIN
# ------------------------------------------------------------------------------------------- #
def main():
    print(SEP)
    print("ARRANGEMENT FIDELITY -- PHASE A CONFUSION DIAGNOSIS (no building). Re-running the")
    print("TEST protocol only against the COMMITTED seeds/stroke_shapes.json codebook (LEARN")
    print("is NOT re-run) with per-miss instrumentation. HIGHER-ORDER ARRANGEMENT RELATIONS")
    print("intermediate gate: runs the SAME diagnosis twice (paired episode draws) -- WITHOUT")
    print("rel2 (the default, reproduces the historical baseline) and WITH rel2 -- reporting")
    print("the tie-rate delta BEFORE the accuracy delta, per the design's own instruction.")
    print(SEP)

    if not ow.have_data("evaluation"):
        print(f"\n  WALL: Omniglot stroke data not found under {ow.DATA}. Cannot run.")
        return 1

    s, ag, native = boot_from_seed()
    codebook_size = len(sc._existing_names(s, "stroke"))
    gv = sc.grain_vocabulary_report(s)
    print(f"\n  loaded committed codebook: {codebook_size} stroke quanta "
          f"(top-level {gv['top']}, refinement children {gv['children']}, "
          f"eager/strokeq_fine children {gv['fine_children']}).")
    print(f"  TEST protocol (imported from the real gate, unmodified): "
          f"alphabets={EVAL_ALPHABETS} way={WAY} episodes/alphabet={EPISODES_PER_ALPHABET} "
          f"seed={SEED}\n  ink-decode params: {DK}")

    # Two INDEPENDENT rng instances, same seed -> byte-identical exemplar/query file draws in
    # both passes (a true PAIRED comparison, not two separately-drifting measurements).
    rng_norel2 = np.random.default_rng(SEED)
    diag_norel2 = run_diagnosis(s, native, EVAL_ALPHABETS, WAY, EPISODES_PER_ALPHABET, DK,
                                rng_norel2, sig_key="composed_sig")
    rng_rel2 = np.random.default_rng(SEED)
    diag_rel2 = run_diagnosis(s, native, EVAL_ALPHABETS, WAY, EPISODES_PER_ALPHABET, DK,
                              rng_rel2, sig_key="composed_sig_rel2")

    sum_norel2 = _report_diag(diag_norel2, "WITHOUT rel2 (control, include_rel2=False)")
    sum_rel2 = _report_diag(diag_rel2, "WITH rel2 (include_rel2=True)")

    # ------------------------------------------------------------------------------------- #
    # INTERMEDIATE GATE -- THE TIE-RATE DELTA (before the accuracy number, per the design).
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  HIGHER-ORDER ARRANGEMENT RELATIONS -- INTERMEDIATE GATE (TIE RATE, "
          f"BEFORE accuracy)\n{SEP}")
    print(f"  historical baseline (commit 97d54623, prior codebook snapshot): tie rate 52.8% "
          f"of misses.")
    print(f"  THIS run's own paired control (WITHOUT rel2, same committed codebook this run "
          f"loaded): tie rate {sum_norel2.get('tie_rate', 0.0):.1f}% of misses "
          f"({sum_norel2['n_miss']} misses, accuracy {100*sum_norel2['acc']:.1f}%) -- reported "
          f"so any codebook drift since 97d54623 is visible BEFORE trusting the delta below.")
    print(f"  WITH rel2 (same episodes, same codebook): tie rate "
          f"{sum_rel2.get('tie_rate', 0.0):.1f}% of misses ({sum_rel2['n_miss']} misses, "
          f"accuracy {100*sum_rel2['acc']:.1f}%)")
    tie_delta = sum_rel2.get("tie_rate", 0.0) - sum_norel2.get("tie_rate", 0.0)
    acc_delta = 100 * (sum_rel2["acc"] - sum_norel2["acc"])
    print(f"  TIE-RATE DELTA (with-rel2 - without-rel2, paired, this run's own codebook): "
          f"{tie_delta:+.1f}pp")
    print(f"  ACCURACY DELTA (with-rel2 - without-rel2, paired, this run's own codebook): "
          f"{acc_delta:+.1f}pp")

    ties_dropped_materially = tie_delta <= -10.0    # a double-digit-point drop, not noise.
    acc_moved_up = acc_delta >= 2.0                 # a real accuracy gain, not noise.
    print(f"\n  PER THE DESIGN'S OWN BRANCH TABLE:")
    if ties_dropped_materially and acc_moved_up:
        print(f"    ties dropped materially ({tie_delta:+.1f}pp) AND accuracy moved up "
              f"({acc_delta:+.1f}pp) -- rel2 IS the primary lever; proceed to RUN 9 with "
              f"rel2 as the headline.")
    elif ties_dropped_materially and not acc_moved_up:
        print(f"    ties dropped materially ({tie_delta:+.1f}pp) but accuracy did NOT move "
              f"up ({acc_delta:+.1f}pp) -- \"the broken ties are being broken WRONG "
              f"(long-range quantization noise decides them)\": the FRAME-ANCHOR lever "
              f"becomes primary going forward (this run's own frame-anchor recovery rate: "
              f"{sum_rel2.get('frame_rate', 0.0):.1f}% of the with-rel2 arm's misses, vs "
              f"{sum_norel2.get('frame_rate', 0.0):.1f}% without) -- say so with the numbers, "
              f"per the design's own instruction.")
    else:
        print(f"    ties did NOT drop materially ({tie_delta:+.1f}pp) -- rel2's added "
              f"relations are matching/missing uniformly (cross-drawer variance on "
              f"long-range geometry); per the design, rel2 should be re-quantized COARSER "
              f"than rel, one documented rerun -- not applied automatically here.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

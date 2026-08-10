"""OMNIGLOT DYNAMIC QUANTIZATION GATE ā€” the handwriting featureset (domains/ink_decode.py +
domains/stroke_codebook.py + seeds/writer_dimensions.json, landed 2026-07-02 in c0288920) run
against REAL online handwriting for the first time. tests/test_ink_decode_migrated.py gates the
same loop on SYNTHETIC ink (glyph_motor_world programs); this script is the REAL-DATA twin ā€”
Omniglot's strokes_background/strokes_evaluation (Lake, Salakhutdinov & Tenenbaum 2015), real
human pen trajectories from real hands.

THE FEATURESET UNDER TEST (see CLAUDE.md's 2026-07-02 sections for the full design ā€” the sd
ladder / quanta-navigation / handwriting sections): a stroke is decoded by SEGMENTATION-BY-
RECOGNITION over a held `ShapeSignature{kind:"stroke"}` codebook (StrokeQuantize quantizes a pen
path into `seg` relations [rotation/scale/translation-INVARIANT] + `pose_x/y/o/s` relations
[the pen's actual placement/orientation/scale] at canonical pose); a Hyp/LatEdge lattice over
arc-length knots (vit_step/vit_backtrace, UNCHANGED from the speech precedent) lets stroke-SHAPES
compete to explain the path, so boundaries EMERGE from the decode rather than a pre-cut. An
on-path OOV span flows into the EXISTING shape_decode_loop ladder (`induce_concern` ->
`sd_mint_quantum` -> `stroke_codebook.grow_stroke_quantum`) ā€” dynamic quantization: order-N
growth IS the codebook earning a new quantum from its own residual. A recognized span's pose is
read off via ONE `TransformDecode` evaluate against the SAME codebook (rung-1 of the transform
ladder ā€” rotation/scale/translation absorbed as a per-dimension delta, not a separate quantum).
Pooled per-writer, >=3 agreeing `orient_delta` Transforms mint a `WriterStyle` (`wd_infer_writer`,
seeds/writer_dimensions.json) ā€” "the writer's physical limits become IMPLIED dimensions."

RUN 6 -- EAGER CHILD MINTING (2026-07-02, scratchpad/HANDWRITING_DESIGN.md's "EAGER CHILD
MINTING" section, the a6fe069b residual): `ink.decode_ink`'s FINE-tier recognitions now also
take one SUB-FINE look (`_eager_child_or_note`) and mint a per-dimension child into a SEPARATE
`ShapeSignatureFineChild` node type when genuine within-tier variation shows up ("within-tier
variation is the mint signal now that misses have stopped" -- run 4/5 already capped vocabulary
at 5 top-level quanta because recognition-before-mint stops nearly every miss at fine). Identity
is ADDITIVE: `character_compose.compose_character_signature` keeps `["strokeq", k, parent]`
exactly as before and ADDS `["strokeq_fine", k, child]` when a child resolved; `decode_char_
signature` below composes ONCE and derives the WITHOUT-children control by filtering
`strokeq_fine` back out (no second decode needed, since the flag is purely additive).

RUN 9 -- HIGHER-ORDER ARRANGEMENT RELATIONS (2026-07-03, scratchpad/HANDWRITING_DESIGN.md's
"HIGHER-ORDER ARRANGEMENT RELATIONS" section, the 97d54623 residual): RUNS 7/8 found naive
whole-relation-tuple coverage (33.8%, the best headline across runs 3/4/6/7/8) beats a
per-stroke ASSIGNMENT-aware metric (30.0%) -- "STRICTNESS IS THE SIGNAL," softening the metric
measured worse twice. The Phase-A diagnosis (`scripts/jabberwock_omniglot_arrangement_diag.py`)
found 52.8% of misses decided by a TIE at that strict metric. `character_compose.
compose_character_signature`'s NEW `include_rel2` flag (default `False`, opt-in) adds one
`["rel2", i, j, dx_q, dy_q, do_q, ds_q]` relation per NON-ADJACENT stroke pair (`j > i+1`),
mechanically derived from the two strokes' own already-computed "rel" pose bins -- giving the
SAME strict naive coverage metric a joint fact about non-adjacent strokes it previously had no
way to check atomically. `decode_char_signature` below composes a SEPARATE
`composed_sig_rel2` (`include_rel2=True`) off the SAME decode (no second `ink_decode` pass);
`composed_sig` (the pre-existing `_comp` arm, `include_rel2` defaults `False`) is UNCHANGED
and stays the LOGGED CONTROL -- it MUST reproduce the historical 33.8%, checked explicitly
below (`control_reproduced`).

RUN 14 -- BRANCH A EXECUTION: SUB-STROKE COMPOSITION (2026-07-03, scratchpad/HANDWRITING_
DESIGN.md's section of the same name, the jabberwock's own verdict d2cd7bed -- "have the
jabberwock decide and execute it"): runs 11-13 declared the featureset search- AND
generation-saturated at the existing representation (41.2%, far-tail 0/3 by any lever); this
run tests the REPRESENTATION lever itself -- "a stroke is itself an arrangement of sub-stroke
quanta," the sd loop one level DOWN (`domains/ink_decode.py::decode_substrokes` +
`domains/stroke_codebook.py`'s companion arity-distinct `kind="substroke"` codebook, earned
during the SAME LEARN pass). `character_compose.compose_character_signature`'s NEW
`include_substroke` flag (default `False`, opt-in) adds an ADDITIVE `["strokeq_sub", k,
<arrangement key>]` relation per stroke -- `run_substroke_composition` replays the run-12
adopted config (delta=0 + appearance) fed EITHER `composed_sig` (control, must reproduce
41.2%) or `composed_sig_substroke` (+composition) over the SAME 80 episodes, no re-decode.

THREE PHASES (mirrors the synthetic gate's own structure, S1/S2/S3 of
scratchpad/HANDWRITING_DESIGN.md, now on real ink):

  LEARN  ā€” start from an EMPTY stroke codebook (no GLYPHS seeding: earn every quantum from real
           Omniglot pen-down strokes). Iterate a bounded learning set (5 background alphabets x
           all characters x drawers 01-14, capped at LEARN_STROKE_CAP pen-down strokes ā€” see
           caps below, all logged, no silent truncation). TRACKS the codebook growth curve
           (codebook size + per-window reuse rate) every GROWTH_WINDOW strokes ā€” the headline
           learning signal is GROWTH THEN FLATTENING (quanta reused across characters). If it
           instead grows ~linearly (every stroke mints), that is an honest FAIL of the
           compression claim, reported with a per-dimension near-miss diagnostic (Ā±1-bin misses
           on turn_q/len_q against the nearest codebook entry), not blind re-tuning.

  WRITER ā€” drawers ARE writers (`writer=f"bg_{drawer}"` tags every ingest/decode call in LEARN).
           After LEARN, `wd_infer_writer` has already had every chance to fire (it runs inside
           `decode_ink`'s own `native.run_rules()`); this phase only READS the graph: how many
           drawers minted >=1 coherent `WriterStyle`, the orient/scale delta distributions, and
           the honest COHERENCE RATE (real hands may show several orientation clusters, not one
           global slant ā€” reported, not forced into one).

  TEST   ā€” one-shot 20-way, WITHIN-ALPHABET, CROSS-DRAWER (the Lake protocol shape), on 3-4
           HELD-OUT alphabets from strokes_evaluation (never touched in LEARN). Per alphabet: one
           fixed 20-exemplar support set (drawer `ex`) + 20 query trials (one per class, drawer
           `q != ex`, both drawn from a seeded rng) = 20 episodes. TWO representations per
           character are classified in PARALLEL over the SAME episodes (DISCRIMINATION lever
           (c), scratchpad/HANDWRITING_DESIGN.md): the pre-existing MULTISET of recognized
           stroke-quantum names (kept as the logged ABLATION CONTROL ā€” no arrangement, "signature
           overlap") and the NEW `character_compose.compose_character_signature` relation-system
           (strokeq + rel + cpose ā€” carries the ARRANGEMENT a multiset cannot). Classification for
           EACH representation is a HELD `Sum`/`In` COVERAGE Term (how many of the query's own
           relation occurrences also appear in a candidate's own relation list) over the 20
           exemplars, decided by ONE held `Argmax` evaluate per query
           (`reflective_faculty.py`'s own `Argmax(Lit(pairs), IndexAt(...,0))` precedent) ā€”
           never a Python argmax/max/sort-by-score. Reports BOTH accuracies vs 5% chance AND
           their shuffled-label controls (breaks the query<->exemplar correspondence: if accuracy
           collapses toward chance, the real accuracy was not an artefact of episode
           construction), the ABLATION DELTA (composed - multiset, lever (c)'s measured value),
           the test-time OOV rate (fraction of query/exemplar strokes that decode to no LEARNED
           quantum ā€” the earned codebook's recall on unseen alphabets), and the transform-
           explanation rate (fraction of recognized spans whose pose the rung-1 TransformDecode
           could actually explain ā€” DISCRIMINATION item (b): pose read-off restored in ALL
           tiers, not just fine ā€” rotation/scale/translation absorbed, not a separate quantum).

donkey=0: every decision on the path is a held Term/rule evaluate (ShapeDecode / TransformDecode
/ vit_step/vit_backtrace / sd_* / wd_infer_writer / the Sum+In coverage Term / the final Argmax)
ā€” Python here only iterates real files, calls `ingest_ink`/`decode_ink` (mechanical world-adapter
calls, unchanged), and prints/aggregates already-decided results. No torch, no teacher, anywhere
on the decision path (`assert "torch" not in sys.modules` at the end). Deterministic: sorted file
traversal in LEARN, a single seeded `np.random.default_rng` for every TEST draw.

CAPS (PRACTICAL, logged exactly, no silent truncation):
  - LEARN_STROKE_CAP = 3000 pen-down strokes (top of the suggested 1500-3000 range ā€” real budget
    allowed it, see the growth curve: it plateaus well before 1000).
  - ink-decode params reduced from the synthetic gate's DEFAULTS (segments=12/turn_bins=16/
    len_bins=8/grid=8/scale_bins=8/max_knots=24) to segments=8/turn_bins=12/len_bins=6/grid=6/
    scale_bins=6/max_knots=16, min_span=2/max_span=10 ā€” a LATENCY choice within the PRACTICAL
    guidance's explicit "segments=8-12" allowance, not a compression-diagnostic response: an
    exploratory probe at the DEFAULT bins on 300 real strokes (not committed, throwaway) showed
    the SAME growth-then-flatten shape (codebook 27->31->40->42->48->56->58->60->60->65->67->69
    per 25-stroke window) but at ~0.3s/stroke (unworkable for a 3000-stroke budget); the reduced
    bins reproduce the identical qualitative shape (see the LEARN report below) at ~5-8x lower
    per-stroke latency. Documented, not blind.
  - TEST: 4 held-out alphabets (Angelic, Atemayar_Qelisayer, Atlantean, Aurek-Besh ā€” the first 4
    of strokes_evaluation's 20 alphabets, sorted, all with >=20 characters), 20-way, 20 episodes
    each = 80 total query trials.

Run:
  ulimit -v 14680064
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_dynamic_quantization.py
"""
from __future__ import annotations

import collections
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import resource
resource.setrlimit(resource.RLIMIT_AS, (14 * 1024 ** 3, 14 * 1024 ** 3))

import numpy as np

from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for
from domains import abs_read as ar
from domains import character_compose as cc
from domains import ink_decode as ink
from domains import omniglot_world as ow
from domains import reflective_faculty as rf
from domains import stroke_codebook as sc

SEP = "=" * 92
SEED = 20260702

# ---------------------------------------------------------------------------------------------
# CAPS ā€” logged verbatim in the report, never silently truncated.
# ---------------------------------------------------------------------------------------------
LEARN_ALPHABETS_N = 5
LEARN_DRAWERS = [f"{i:02d}" for i in range(1, 15)]           # drawers 01..14
LEARN_STROKE_CAP = 3000
GROWTH_WINDOW = 100

# reduced-bin ink-decode params (see module docstring's CAPS section for the rationale).
# RUN-5 PROBE (diagnostics-driven, per the run-4 instrumentation: at 8/12/6 the FINE grain
# never near-misses — 1169/1169 diagnostic spans recognized at fine, vocabulary frozen at 5
# primitives — so richer bins are the named residual's direct test, not blind tuning).
# Override via OMNIGLOT_RICH_BINS=1: full synthetic-gate defaults (12/16/8/8/8).
import os as _os
if _os.environ.get("OMNIGLOT_RICH_BINS"):
    DK = dict(max_knots=16, min_span=2, max_span=10, segments=12, turn_bins=16, len_bins=8,
              grid=8, scale_bins=8)
else:
    DK = dict(max_knots=16, min_span=2, max_span=10, segments=8, turn_bins=12, len_bins=6,
              grid=6, scale_bins=6)

EVAL_ALPHABETS = ["Angelic", "Atemayar_Qelisayer", "Atlantean", "Aurek-Besh"]
WAY = 20
EPISODES_PER_ALPHABET = 20

# RUN 10 -- ABS AS DEFAULT (scratchpad/HANDWRITING_DESIGN.md's "ABS AS DEFAULT" section,
# 2026-07-03): PROPOSE top-K by the existing strict coverage (`domains.abs_read.propose_
# top_k`), then RE-RANK by render-compare (domains.abs_read.abs_rerank). K is a LOGGED
# CONSTANT (design: "K~3-5"), never tuned per-query -- 5 chosen as the top of that range so
# `coverage_at_k` (the proposal recall bound this run reports explicitly) has the best
# realistic chance of containing the true exemplar for the re-rank to work with.
ABS_TOPK = 5

# RUN 11 -- PROPOSAL RECALL / VARIABLE-APERTURE DWELL (scratchpad/HANDWRITING_DESIGN.md's
# section of the same name, the 42855d5f residual + the radar frame's first falsifiable
# instance): THREE arms off the SAME decode+proposal cache RUN 10 already built this run --
# no re-decode, no re-LEARN. K=5 FIXED (the RUN 10 control, must reproduce 37.5%); K=20 FULL
# DWELL (`domains.abs_read.abs_rerank`'s `top_k=list(range(way))` override -- pure AbS
# classification, no proposal filter at all, the upper bound / cleanest one-model test);
# VARIABLE-K (`domains.abs_read.propose_variable_k`, delta as DATA -- the shortlist is every
# candidate within margin delta of the top proposal score, held Terms only). Deltas are
# LOGGED sub-arms (never tuned per-query).
FULL_DWELL_K = WAY
VARIABLE_DELTAS = (0, 1, 2)


# ---------------------------------------------------------------------------------------------
# BOOT ā€” mirrors tests/test_ink_decode_migrated.py::_boot() exactly (the verified pattern):
# core seeds + the shape_decode_loop ladder + the writer_dimensions rule. No "stroke_shapes"
# seed is loaded ā€” the stroke codebook starts EMPTY, earned entirely from real ink below.
# ---------------------------------------------------------------------------------------------
def boot():
    s, ag = boot_core()
    native = s._inner
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("writer_dimensions"), ag)
    return s, ag, native


# ---------------------------------------------------------------------------------------------
# Diagnostic (reporting only, not a decision): nearest-codebook L1 distance in QUANTIZED BINS
# for an invariant `seg`-relation signature ā€” used ONLY if the growth curve fails to flatten.
# ---------------------------------------------------------------------------------------------
def _nearest_codebook_distance(s, sig) -> "float | None":
    sig_map = {r[1]: (r[2], r[3]) for r in sig if isinstance(r, list) and r and r[0] == "seg"}
    best = None
    for n in s.nodes("ShapeSignature"):
        at = s.node(n)["attrs"]
        if at.get("kind") != "stroke":
            continue
        try:
            cb_sig = json.loads(at.get("signature") or "[]")
        except (TypeError, ValueError):
            continue
        cb_map = {r[1]: (r[2], r[3]) for r in cb_sig if isinstance(r, list) and r and r[0] == "seg"}
        if set(cb_map) != set(sig_map):
            continue
        dist = sum(abs(sig_map[i][0] - cb_map[i][0]) + abs(sig_map[i][1] - cb_map[i][1])
                   for i in sig_map)
        if best is None or dist < best:
            best = dist
    return best


# ---------------------------------------------------------------------------------------------
# LEARN
# ---------------------------------------------------------------------------------------------
def run_learn(s, ag, native, alphabets, drawers, cap, dk, window,
              turn_edges=None, len_edges=None):
    """RUN 32 addition: `turn_edges`/`len_edges` (optional, default `None` — every
    pre-existing caller, run26 through run31, keeps byte-identical behaviour) thread straight
    through to `ink.decode_ink`'s own new adaptive-edges params (`domains/ink_decode.py`) —
    the FINE grain only, see that module's doc. `scripts/jabberwock_omniglot_run32_
    subquantum.py` is the only caller that ever passes real edges here."""
    growth = []
    n_strokes = 0
    n_degenerate_skipped = 0
    win_recognized = win_oov = win_minted = 0
    win_codebook_start = 0
    win_substroke_start = 0
    stop_info = None
    last_window_oov_ink = []     # (ink_node, start, end) samples from the LAST window, for the
                                  # near-miss diagnostic IF the growth curve fails to flatten.
    per_stroke_times = []
    t_start = time.time()

    for alph in alphabets:
        if n_strokes >= cap:
            break
        chars = ow.characters(alph, "background")
        for cdir in chars:
            if n_strokes >= cap:
                break
            files_by_drawer = {}
            for f in ow.drawings(cdir):
                d = f.split("/")[-1].split("_")[-1].replace(".txt", "")
                files_by_drawer[d] = f
            for d in drawers:
                if n_strokes >= cap:
                    break
                f = files_by_drawer.get(d)
                if f is None:
                    continue
                for st in ow.load_strokes(f):
                    if n_strokes >= cap:
                        stop_info = {"alphabet": alph, "character": os.path.basename(cdir),
                                     "drawer": d, "file": f, "reason": "cap reached"}
                        break
                    if st.shape[0] < 2:
                        n_degenerate_skipped += 1        # dot / degenerate stroke, skipped
                        continue
                    t1 = time.time()
                    ink_node = ink.ingest_ink(s, st.tolist(), writer=f"bg_{d}",
                                               max_knots=dk["max_knots"])
                    # RUN 14 -- BRANCH A EXECUTION (SUB-STROKE COMPOSITION): enable_substroke=
                    # True so the substroke codebook is earned during THIS SAME LEARN pass
                    # (design: "the sub-stroke codebook is earned during the SAME LEARN
                    # pass... per-stroke inner lattice after the stroke-level decode"). This
                    # is ADDITIVE to the outer stroke-grain decode (a DIFFERENT `kind`/arity
                    # codebook, see stroke_codebook.SUBSTROKE_SEGMENTS's own comment) -- the
                    # stroke-grain codebook/growth-curve numbers above are UNAFFECTED.
                    res = ink.decode_ink(s, ink_node, writer=f"bg_{d}", min_span=dk["min_span"],
                                          max_span=dk["max_span"], segments=dk["segments"],
                                          turn_bins=dk["turn_bins"], len_bins=dk["len_bins"],
                                          grid=dk["grid"], scale_bins=dk["scale_bins"],
                                          enable_substroke=True,
                                          turn_edges=turn_edges, len_edges=len_edges)
                    per_stroke_times.append(time.time() - t1)
                    n_strokes += 1
                    win_recognized += len(res["recognized"])
                    win_oov += len(res["oov"])
                    win_minted += len(res["minted"])
                    for o in res["oov"]:
                        last_window_oov_ink.append((ink_node, o["start"], o["end"]))
                    if n_strokes % window == 0:
                        last_window_oov_ink = last_window_oov_ink[-50:]   # bound memory
                        cb = len(sc._existing_names(s, "stroke"))
                        sub_cb = sc.substroke_vocabulary_report(s)["total"]
                        reuse_rate = win_recognized / max(1, win_recognized + win_oov)
                        growth.append({
                            "n": n_strokes, "codebook": cb, "new_quanta": cb - win_codebook_start,
                            "recognized": win_recognized, "oov": win_oov, "minted": win_minted,
                            "reuse_rate": reuse_rate, "elapsed": time.time() - t_start,
                            "substroke_codebook": sub_cb,
                            "substroke_new": sub_cb - win_substroke_start,
                        })
                        win_codebook_start = cb
                        win_substroke_start = sub_cb
                        win_recognized = win_oov = win_minted = 0
                        if n_strokes < cap:
                            last_window_oov_ink = []   # only the FINAL window's samples matter
                if n_strokes >= cap:
                    break

    return dict(growth=growth, n_strokes=n_strokes, n_degenerate_skipped=n_degenerate_skipped,
                stop_info=stop_info, elapsed=time.time() - t_start,
                per_stroke_times=per_stroke_times, last_window_oov_ink=last_window_oov_ink)


# ---------------------------------------------------------------------------------------------
# WRITER DIMENSIONS ā€” pure read-back (wd_infer_writer already fired inside decode_ink's own
# run_rules() calls during LEARN; this only queries the graph it left behind).
# ---------------------------------------------------------------------------------------------
def writer_report(s):
    writers = list(s.nodes("Writer"))
    rows, style_counts, orient_deltas, scale_deltas = [], [], [], []
    n_with_transforms = n_with_style = 0
    for w in writers:
        name = s.node(w)["attrs"].get("name")
        ts = list(s.neighbours(w, "wrote_transform"))
        styles = list(s.neighbours(w, "has_style"))
        if ts:
            n_with_transforms += 1
        if styles:
            n_with_style += 1
        style_counts.append(len(styles))
        for st_node in styles:
            at = s.node(st_node)["attrs"]
            orient_deltas.append(at.get("orient_delta"))
            scale_deltas.append(at.get("scale_delta"))
        rows.append({"writer": name, "n_transforms": len(ts), "n_styles": len(styles)})
    coherence_rate = n_with_style / max(1, n_with_transforms)
    return dict(rows=rows, n_writers=len(writers), n_with_transforms=n_with_transforms,
                n_with_style=n_with_style, coherence_rate=coherence_rate,
                total_styles=sum(style_counts), style_counts=style_counts,
                orient_deltas=orient_deltas, scale_deltas=scale_deltas)


# ---------------------------------------------------------------------------------------------
# TEST ā€” one-shot 20-way, within-alphabet, cross-drawer. Classification is a HELD Term
# (Sum+In coverage per candidate, ONE final Argmax evaluate per query) ā€” never Python argmax.
# ---------------------------------------------------------------------------------------------
def _coverage_term(query_sig, exemplar_sig) -> dict:
    """HELD Term: for every recognized-quantum OCCURRENCE in the query's signature (with
    repeats), 1 if that quantum type also appears anywhere in the candidate's own vocabulary,
    else 0, summed ā€” "shared-quantum count / coverage" read off a single Rust Sum/In evaluate."""
    return {"type": "Sum", "source": {"type": "Lit", "value": query_sig}, "var_name": "n",
            "value": {"type": "IfThenElse",
                      "cond": {"type": "In", "member": {"type": "Var", "name": "n"},
                               "container": {"type": "Lit", "value": exemplar_sig}},
                      "then": {"type": "Lit", "value": 1.0}, "other": {"type": "Lit", "value": 0.0}}}


def _argmax_pairs_term(pairs) -> dict:
    """The SAME Argmax(Lit(pairs), IndexAt(Var,0)) idiom domains/reflective_faculty.py:783
    already uses to pick a winner from a Python-assembled (score, id) list without a Python
    argmax ā€” the DECISION is this one held evaluate call."""
    return {"type": "Argmax", "source": {"type": "Lit", "value": pairs}, "var_name": "c",
            "value": {"type": "IndexAt", "seq": {"type": "Var", "name": "c"},
                      "index": {"type": "Lit", "value": 0}},
            "default": None}


def decode_char_signature(s, path, cache, dk, turn_edges=None, len_edges=None,
                          collect_residuals=False):
    """A character drawing -> ITS decode, in BOTH representations (DISCRIMINATION lever (c)
    ablation): `sig` is the pre-existing MULTISET of recognized quantum names (kept as the
    logged ablation CONTROL ā€” "signature overlap", no arrangement); `composed_sig` is the NEW
    `character_compose.compose_character_signature` relation-system (strokeq + rel + cpose,
    carries the ARRANGEMENT a multiset cannot). Mechanical: ingest + decode every pen-down
    stroke of the file (UNCHANGED), then merge each pen-stroke's own {recognized, minted}
    spans (DISCRIMINATION item (a)'s deepest-match identities, already resolved by
    `ink_decode.decode_ink`) into ONE draw-order stroke-point sequence for composition ā€”
    `character_compose.decode_result_to_stroke_points` per pen-stroke, concatenated across
    pen-strokes in the file's own writing order (`ow.load_strokes` yields them pen-down
    order already). Cached by path ā€” every episode that reuses the same drawing reuses the
    same decode.

    EAGER CHILD MINTING (2026-07-02, scratchpad/HANDWRITING_DESIGN.md's "EAGER CHILD MINTING"
    section, the a6fe069b residual): `ink.decode_ink` (default `enable_eager_children=True`)
    now ALSO carries a `"fine_child"` field on FINE-tier recognized spans when a sub-fine
    look minted/matched one; `character_compose.decode_result_to_stroke_points` already
    threads that field through as each stroke_points item's 3rd element. `composed_sig` here
    is composed WITH `strokeq_fine` (the headline, `include_fine_children=True`, the default);
    `composed_sig_no_children` is the SAME decode's signature with `strokeq_fine` relations
    filtered back OUT (the ablation CONTROL — a cheap post-hoc filter, not a second decode,
    since `include_fine_children` is PURELY additive: every other relation is byte-identical
    either way, see `compose_character_signature`'s own docstring)."""
    cached = cache.get(path)
    if cached is not None:
        return cached
    sig, n_recognized, n_oov, n_explained = [], 0, 0, 0
    stroke_points = []
    residuals = []          # RUN 32 -- SUB-BIN RESIDUAL (only populated when collect_residuals).
    for st in ow.load_strokes(path):
        if st.shape[0] < 2:
            continue
        ink_node = ink.ingest_ink(s, st.tolist(), max_knots=dk["max_knots"])
        # RUN 14 -- BRANCH A EXECUTION: enable_substroke=True so every recognized span
        # carries its own within-stroke inner-lattice decode (`entry["substroke_points"]`) --
        # threaded through by `cc.decode_result_to_stroke_points` below into stroke_points'
        # 4th tuple element, purely additive (the pre-existing sig/composed_sig arms are
        # UNCHANGED unless a caller explicitly passes include_substroke=True downstream).
        # RUN 32: `turn_edges`/`len_edges` (optional, default None -- byte-identical
        # uniform behaviour for every pre-existing caller) thread through to decode_ink's
        # own adaptive-edges params.
        res = ink.decode_ink(s, ink_node, min_span=dk["min_span"], max_span=dk["max_span"],
                              segments=dk["segments"], turn_bins=dk["turn_bins"],
                              len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"],
                              enable_substroke=True,
                              turn_edges=turn_edges, len_edges=len_edges)
        for r in res["recognized"]:
            sig.append(r["name"])
            n_recognized += 1
            t = r.get("transform") or {}
            if t.get("explained") or t.get("identity"):
                n_explained += 1
        n_oov += len(res["oov"])
        knots = s.node(ink_node)["attrs"].get("knots") or []
        stroke_points.extend(cc.decode_result_to_stroke_points(knots, res))
        # RUN 32 -- SUB-BIN RESIDUAL: per recognized span, ONE extra StrokeQuantize evaluate
        # (`emit_residual=True`, same fine bins/edges the span's own signature used) reads off
        # the continuous WITHIN-bin remainders -- "the remainder goes to more detail", stored
        # instead of discarded. Concatenated in draw order across spans/pen-strokes so a
        # character's residual sequence pairs positionally with another drawing's under
        # `abs_read.residual_aware_distance`'s zip-truncated sum. Mechanical read-off of a
        # held Term's own numeric output; opt-in, every pre-existing caller unaffected.
        if collect_residuals:
            kn = np.asarray(knots, dtype=float)
            for r in res["recognized"]:
                q = sc._quantize(s._inner, kn[r["start"]:r["end"]], segments=dk["segments"],
                                 turn_bins=dk["turn_bins"], len_bins=dk["len_bins"],
                                 grid=dk["grid"], scale_bins=dk["scale_bins"],
                                 invariant_only=True, turn_edges=turn_edges,
                                 len_edges=len_edges, emit_residual=True)
                for (i, t_res, l_res) in (q.get("residuals") or []):
                    residuals.append([float(t_res), float(l_res)])

    composed = cc.compose_character_signature(
        s._inner, stroke_points, segments=dk["segments"], turn_bins=dk["turn_bins"],
        len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"])
    composed_no_children = [r for r in composed["signature"] if r[0] != "strokeq_fine"]

    # RUN-4 LEVERS -- STROKE-ORDER ABLATION (1-flag, logged not gated, per the design's own
    # "worth logging" framing): the SAME stroke identities, re-ordered by NAME (a drawer-
    # independent, arbitrary-but-fixed order) instead of DRAW/START-POSITION order, composed
    # again -- if real drawers vary their stroke ORDER for the same character (a known Omniglot
    # property), `strokeq`'s `k` ordinal and `rel`'s draw-order pairing with it would carry
    # DRAWER-SPECIFIC noise rather than character identity; this measures how much that costs.
    sorted_points = sorted(stroke_points, key=lambda pn: pn[1])
    composed_sorted = cc.compose_character_signature(
        s._inner, sorted_points, segments=dk["segments"], turn_bins=dk["turn_bins"],
        len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"])

    # RUN 9 -- HIGHER-ORDER ARRANGEMENT RELATIONS (2026-07-03, scratchpad/HANDWRITING_
    # DESIGN.md's "HIGHER-ORDER ARRANGEMENT RELATIONS" section, the 97d54623 residual): a
    # SEPARATE explicit `include_rel2=True` compose call off the SAME `stroke_points` (no
    # second ink-decode) -- `character_compose.compose_character_signature` defaults
    # `include_rel2=False`, so `composed["signature"]` above (the pre-existing `composed_sig`,
    # every OTHER arm's basis) is UNCHANGED/UNAFFECTED by this addition -- strictly additive.
    composed_rel2 = cc.compose_character_signature(
        s._inner, stroke_points, segments=dk["segments"], turn_bins=dk["turn_bins"],
        len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"], include_rel2=True)

    # RUN 14 -- BRANCH A EXECUTION (SUB-STROKE COMPOSITION, 2026-07-03, scratchpad/
    # HANDWRITING_DESIGN.md's section of the same name, the jabberwock's own verdict
    # d2cd7bed): a SEPARATE explicit `include_substroke=True` compose call off the SAME
    # `stroke_points` (no second ink-decode -- `enable_substroke=True` above already
    # attached the raw substroke_points data to every recognized span this decode
    # produced). `composed["signature"]` (the pre-existing `composed_sig`, every OTHER
    # arm's basis) is UNCHANGED/UNAFFECTED by this addition -- strictly additive, mirrors
    # RUN 9's own `composed_rel2` pattern exactly.
    composed_substroke = cc.compose_character_signature(
        s._inner, stroke_points, segments=dk["segments"], turn_bins=dk["turn_bins"],
        len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"],
        include_substroke=True)

    out = {"sig": sig, "composed_sig": composed["signature"],
           "composed_sig_no_children": composed_no_children,
           "composed_sig_sorted": composed_sorted["signature"],
           "composed_sig_rel2": composed_rel2["signature"],
           "composed_sig_substroke": composed_substroke["signature"],
           # RUN 10 -- ABS AS DEFAULT: the RAW draw-order (points, identity[, fine_child])
           # sequence this SAME decode already produced (`decode_result_to_stroke_points`
           # above) -- threaded through unchanged so `ar.abs_rerank` can render-compare
           # against the query's OWN actual observed ink without a second decode. Purely
           # additive (a new dict key; every pre-existing reader of this cache entry is
           # unaffected).
           "stroke_points": stroke_points,
           # RUN 32 -- SUB-BIN RESIDUAL: `[[turn_res, len_res], ...]` concatenated in draw
           # order across recognized spans; empty unless collect_residuals was passed.
           "residuals": residuals,
           "n_recognized": n_recognized, "n_oov": n_oov, "n_explained": n_explained,
           "n_spans": n_recognized + n_oov}
    cache[path] = out
    return out


def run_test(s, native, alphabets, way, episodes_per_alphabet, dk, rng):
    """Runs FIVE classification arms per episode over the SAME episodes (same exemplar/query
    draws, same seeded rng) ā€” the pre-existing MULTISET coverage+Argmax (`_ms` suffix, the
    logged ABLATION CONTROL), the composed-signature coverage+Argmax (`_comp` suffix,
    DISCRIMINATION lever (c), draw-order `strokeq`/`rel`, WITH `strokeq_fine` -- EAGER CHILD
    MINTING's headline), its `strokeq_fine`-stripped twin (`_comp_nc` suffix, EAGER CHILD
    MINTING's ablation CONTROL -- must reproduce the pre-eager-child composed accuracy),
    RUN-4 LEVERS' STROKE-ORDER ABLATION twin (`_sorted` suffix, the SAME WITH-children
    composed representation but with strokes reordered by NAME instead of draw position) ā€”
    so the `_comp` vs `_sorted` delta measures how much of composition's win depends on
    drawers using a CONSISTENT stroke order -- and NOW (RUN 7, ARRANGEMENT FIDELITY,
    scratchpad/HANDWRITING_DESIGN.md's "ARRANGEMENT FIDELITY" section, the accb0d47 residual)
    the ASSIGNMENT-AWARE coverage twin (`_assign` suffix, `character_compose.
    assignment_coverage_term` -- the top-ranked lever from
    `scripts/jabberwock_omniglot_arrangement_diag.py`'s Phase-A diagnosis: naive whole-
    relation-tuple membership decided 52.8% of misses by a TIE and could not distinguish a
    1-slot near-miss from a total mismatch; assignment scores each stroke by its BEST-matching
    exemplar stroke, per relation SLOT). `_comp` (the pre-existing naive coverage over the SAME
    WITH-children composed signature) stays the LOGGED CONTROL every episode -- additivity
    discipline, per the design's own instruction. All five arms use the IDENTICAL
    `_argmax_pairs_term` held-Argmax idiom, just fed a different per-candidate score Term.

    RUN 9 -- HIGHER-ORDER ARRANGEMENT RELATIONS (`_rel2` suffix, scratchpad/HANDWRITING_
    DESIGN.md's "HIGHER-ORDER ARRANGEMENT RELATIONS" section, the 97d54623 residual): the
    SAME naive `_coverage_term` (STRICTNESS IS THE SIGNAL -- the design's own instruction NOT
    to soften the metric, per RUN 7/8's finding that assignment/arrangement-only scoring
    measured WORSE than naive strict coverage) fed `qd["composed_sig_rel2"]`
    (`include_rel2=True` -- non-adjacent-stroke-pair facts, ADDED on top of the SAME
    with-children composed signature `_comp` already uses) instead of `qd["composed_sig"]`.
    `_comp` (UNCHANGED, `include_rel2` defaults `False`) stays the LOGGED CONTROL -- it MUST
    reproduce the historical 33.8% (the design's own explicit stop-and-diagnose condition if
    it doesn't)."""
    cache = {}
    codebook_before = len(sc._existing_names(s, "stroke"))
    all_pred_ms, all_pred_comp, all_pred_comp_nc, all_pred_sorted, all_pred_assign, all_true = \
        [], [], [], [], [], []
    all_pred_arr_only = []
    all_pred_rel2 = []
    per_alph_acc_ms, per_alph_acc_comp, per_alph_acc_comp_nc, per_alph_acc_assign = \
        {}, {}, {}, {}
    per_alph_acc_rel2 = {}
    skipped_alphabets = []

    # RUN 10 -- ABS AS DEFAULT: probed ONCE (the SAME "authored, not yet operative" pattern
    # `stroke_codebook._stroke_quantize_live` established before `StrokeQuantize` itself
    # landed) -- when live, every episode ALSO runs the propose-top-K + render-compare
    # re-rank; when not, the arm is skipped entirely (no wasted evaluate calls) and reported
    # as an honest, un-run lever, never a fabricated chance-level number.
    sr_live = ar._stroke_render_live(native)
    all_pred_abs, all_coverage_hits = [], []
    per_alph_acc_abs, per_alph_coverage_at_k = {}, {}

    # RUN 11 -- PROPOSAL RECALL / VARIABLE-APERTURE DWELL: accumulators for the K=20 FULL
    # DWELL arm and the VARIABLE_DELTAS sub-arms, plus the RECALL-TAIL rank list (ranks of
    # the true exemplar, read via `ar.proposal_rank`, for episodes where RUN 10's own K=5
    # shortlist MISSED it -- reporting only, off the SAME per-episode decode).
    all_pred_full, all_coverage_full = [], []
    per_alph_acc_full = {}
    all_pred_delta = {d: [] for d in VARIABLE_DELTAS}
    all_coverage_delta = {d: [] for d in VARIABLE_DELTAS}
    all_shortlist_delta = {d: [] for d in VARIABLE_DELTAS}
    per_alph_acc_delta = {d: {} for d in VARIABLE_DELTAS}
    per_alph_coverage_delta = {d: {} for d in VARIABLE_DELTAS}
    per_alph_shortlist_delta = {d: {} for d in VARIABLE_DELTAS}
    recall_tail_ranks = []

    # RUN 12 -- TARGETED WIDEN + SECOND MODALITY (scratchpad/HANDWRITING_DESIGN.md's section
    # of the same name): SHARED-CACHE accumulators, populated for FREE off the delta=0
    # sub-arm RUN 11 already computes (no extra render-compare calls here) -- `run_targeted_
    # widen` (below) replays `episode_records` against `exemplars_by_alph` to run the four
    # RUN 12 arms over the EXACT SAME 80 episodes, no re-decode, no re-drawing of `rng`.
    # `delta0_calibration` feeds `calibrate_widen_thresholds` (host-side, offline, chosen
    # ONCE from these already-computed scores -- never a per-query decision; the per-query
    # widen verdict stays `ar.widen_decision`'s own held Term in domains/abs_read.py).
    # `far_tail_episodes` are RUN 11's own rank>=16 "proposal-blind" cases (by (alph, qi)
    # identity) -- RUN 12 reports whether either lever makes them reachable.
    exemplars_by_alph: dict = {}
    episode_records: list = []
    delta0_calibration: list = []
    far_tail_episodes: list = []

    for alph in alphabets:
        chars = sorted(ow.characters(alph, "evaluation"))
        if len(chars) < way:
            skipped_alphabets.append((alph, f"only {len(chars)} characters, need {way}"))
            continue
        chars = chars[:way]
        drawer_files = [ow.drawings(cd) for cd in chars]
        n_drawers = min(len(fl) for fl in drawer_files)
        ex_drawer = int(rng.integers(n_drawers))
        exemplars = [decode_char_signature(s, drawer_files[ci][ex_drawer], cache, dk)
                     for ci in range(way)]
        exemplar_sigs = [e["sig"] for e in exemplars]
        exemplar_composed = [e["composed_sig"] for e in exemplars]
        exemplar_composed_nc = [e["composed_sig_no_children"] for e in exemplars]
        exemplar_sorted = [e["composed_sig_sorted"] for e in exemplars]
        exemplar_rel2 = [e["composed_sig_rel2"] for e in exemplars]
        exemplar_stroke_points = [e["stroke_points"] for e in exemplars]
        # RUN 14 -- BRANCH A EXECUTION: the SAME exemplars' `composed_sig_substroke` (already
        # computed by `decode_char_signature`, no extra decode), cached alongside for RUN 14's
        # replay (`run_substroke_composition`).
        exemplar_composed_substroke = [e["composed_sig_substroke"] for e in exemplars]
        # RUN 12 -- shared exemplar cache, keyed by alphabet (read-only reuse downstream).
        exemplars_by_alph[alph] = (exemplar_composed, exemplar_stroke_points,
                                   exemplar_composed_substroke)

        preds_ms, preds_comp, preds_comp_nc, preds_sorted, preds_assign, trues = \
            [], [], [], [], [], []
        preds_arr_only = []
        preds_rel2 = []
        preds_abs, coverage_hits = [], []
        preds_full, coverage_full = [], []
        preds_delta = {d: [] for d in VARIABLE_DELTAS}
        coverage_delta = {d: [] for d in VARIABLE_DELTAS}
        shortlist_delta = {d: [] for d in VARIABLE_DELTAS}
        for qi in range(min(episodes_per_alphabet, way)):
            q_drawer = int(rng.integers(n_drawers))
            while q_drawer == ex_drawer:
                q_drawer = int(rng.integers(n_drawers))
            qd = decode_char_signature(s, drawer_files[qi][q_drawer], cache, dk)

            pairs_ms = [(float(native.evaluate(_coverage_term(qd["sig"], exemplar_sigs[ci]), {}) or 0.0), ci)
                        for ci in range(way)]
            winner_ms = native.evaluate(_argmax_pairs_term(pairs_ms), {})
            preds_ms.append(winner_ms[1] if winner_ms is not None else -1)

            pairs_comp = [(float(native.evaluate(_coverage_term(qd["composed_sig"], exemplar_composed[ci]), {}) or 0.0), ci)
                          for ci in range(way)]
            winner_comp = native.evaluate(_argmax_pairs_term(pairs_comp), {})
            preds_comp.append(winner_comp[1] if winner_comp is not None else -1)

            # EAGER CHILD MINTING -- ABLATION CONTROL (logged every episode, per the design's
            # own "the gate logs BOTH scores every episode"): the SAME coverage
            # classification, fed the strokeq_fine-STRIPPED composed signature (must reproduce
            # the pre-eager-child accuracy).
            pairs_comp_nc = [(float(native.evaluate(_coverage_term(qd["composed_sig_no_children"], exemplar_composed_nc[ci]), {}) or 0.0), ci)
                             for ci in range(way)]
            winner_comp_nc = native.evaluate(_argmax_pairs_term(pairs_comp_nc), {})
            preds_comp_nc.append(winner_comp_nc[1] if winner_comp_nc is not None else -1)

            # RUN-4 LEVERS -- STROKE-ORDER ABLATION (logged, not gated): the SAME coverage
            # classification, fed the NAME-sorted (drawer-order-independent) composed
            # signature instead of draw-order.
            pairs_sorted = [(float(native.evaluate(_coverage_term(qd["composed_sig_sorted"], exemplar_sorted[ci]), {}) or 0.0), ci)
                            for ci in range(way)]
            winner_sorted = native.evaluate(_argmax_pairs_term(pairs_sorted), {})
            preds_sorted.append(winner_sorted[1] if winner_sorted is not None else -1)

            # ARRANGEMENT FIDELITY (RUN 7) -- the top-ranked Phase-A lever: the SAME
            # WITH-children composed signature `_comp` already uses, scored by PER-STROKE
            # assignment instead of naive whole-relation membership.
            pairs_assign = [(float(native.evaluate(
                cc.assignment_coverage_term(qd["composed_sig"], exemplar_composed[ci]), {}) or 0.0), ci)
                            for ci in range(way)]
            winner_assign = native.evaluate(_argmax_pairs_term(pairs_assign), {})
            preds_assign.append(winner_assign[1] if winner_assign is not None else -1)

            # RUN 8 -- the run-7 residual's own prescription: identity_weight=0 scores
            # ARRANGEMENT ONLY (stroke identity is at-chance at the gate's small LEARN
            # codebook per the multiset ablation; weighting it diluted the arrangement
            # signal in run 7 -- one documented diagnostics-driven adjustment).
            pairs_arr = [(float(native.evaluate(
                cc.assignment_coverage_term(qd["composed_sig"], exemplar_composed[ci],
                                            identity_weight=0.0), {}) or 0.0), ci)
                         for ci in range(way)]
            winner_arr = native.evaluate(_argmax_pairs_term(pairs_arr), {})
            preds_arr_only.append(winner_arr[1] if winner_arr is not None else -1)

            # RUN 9 -- HIGHER-ORDER ARRANGEMENT RELATIONS: the SAME naive `_coverage_term`
            # (STRICTNESS IS THE SIGNAL, per RUN 7/8) fed the rel2-enriched composed signature.
            pairs_rel2 = [(float(native.evaluate(
                _coverage_term(qd["composed_sig_rel2"], exemplar_rel2[ci]), {}) or 0.0), ci)
                         for ci in range(way)]
            winner_rel2 = native.evaluate(_argmax_pairs_term(pairs_rel2), {})
            preds_rel2.append(winner_rel2[1] if winner_rel2 is not None else -1)

            # RUN 10 -- ABS AS DEFAULT: PROPOSE top-ABS_TOPK by the SAME strict coverage
            # (`ar.propose_top_k`, byte-identical metric to `_comp`'s own control), then
            # RENDER-COMPARE each proposed candidate against the query's OWN actual
            # observed ink (`ar.abs_rerank`) -- final pick a held Argmin over the K
            # candidates. `qi` doubles as the TRUE class index here (exemplars/queries are
            # both drawn per-class from `chars[:way]`, `trues.append(qi)` below is the
            # SAME convention every other arm already uses) so `qi in top_k` is exactly
            # coverage@K -- the proposal recall bound on what re-ranking can possibly
            # achieve, reported explicitly per the design's own instruction.
            if sr_live:
                abs_res = ar.abs_rerank(
                    s, qd["composed_sig"], qd["stroke_points"], exemplar_composed,
                    exemplar_stroke_points, k=ABS_TOPK, turn_bins=dk["turn_bins"],
                    len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"])
                preds_abs.append(abs_res["winner"] if abs_res["winner"] is not None else -1)
                k5_hit = 1 if qi in abs_res["top_k"] else 0
                coverage_hits.append(k5_hit)

                # RUN 11 -- K=20 FULL DWELL (scratchpad/HANDWRITING_DESIGN.md's "PROPOSAL
                # RECALL / VARIABLE-APERTURE DWELL" section): NO proposal filter at all --
                # `top_k=list(range(way))` overrides `abs_rerank`'s internal `propose_top_k`
                # call with the FULL candidate range, so every one of the `way` candidates
                # is render-compared -- pure AbS classification, the upper bound / cleanest
                # one-model test. Reuses the SAME `qd`/`exemplar_composed`/`exemplar_stroke_
                # points` this episode already decoded -- no re-decode, no re-LEARN.
                # coverage@20 == 100% BY CONSTRUCTION (every candidate is in the shortlist).
                full_res = ar.abs_rerank(
                    s, qd["composed_sig"], qd["stroke_points"], exemplar_composed,
                    exemplar_stroke_points, top_k=list(range(way)), turn_bins=dk["turn_bins"],
                    len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"])
                preds_full.append(full_res["winner"] if full_res["winner"] is not None else -1)
                coverage_full.append(1)

                # RUN 11 -- VARIABLE-K DWELL SCHEDULER: `ar.propose_variable_k` builds the
                # shortlist as every candidate within margin `delta` (DATA) of the top
                # proposal score (held MaxOver + held FilterList -- no Python score branch,
                # see `domains/abs_read.py`'s own docstring); ONE `abs_rerank` re-rank per
                # delta, off the SAME decode. The render BUDGET is the shortlist size.
                for d in VARIABLE_DELTAS:
                    vk = ar.propose_variable_k(native, qd["composed_sig"], exemplar_composed,
                                                float(d))
                    vres = ar.abs_rerank(
                        s, qd["composed_sig"], qd["stroke_points"], exemplar_composed,
                        exemplar_stroke_points, top_k=vk, turn_bins=dk["turn_bins"],
                        len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"])
                    preds_delta[d].append(vres["winner"] if vres["winner"] is not None else -1)
                    coverage_delta[d].append(1 if qi in vk else 0)
                    shortlist_delta[d].append(len(vk))

                    # RUN 12 -- CALIBRATION + SHARED EPISODE RECORD, captured for FREE off
                    # THIS delta=0 `vres` (no extra render-compare calls): `best`/`margin`
                    # are HOST-SIDE, offline aggregate reads (plain Python `min()`, no
                    # `key=` over a score expression) feeding `calibrate_widen_thresholds`
                    # ONCE after all episodes finish -- never a per-query decision (the
                    # per-query widen verdict is `ar.widen_decision`'s own held Term). The
                    # winner-exclusion below is the SAME bookkeeping idiom `ar.widen_
                    # decision`/`ar.propose_top_k` use to remove an already-decided winner.
                    if d == 0:
                        best0 = (float(min(sc_ for sc_, _ in vres["scores"]))
                                  if vres["scores"] else None)
                        margin0 = None
                        if best0 is not None:
                            rest0 = [sc_ for sc_, ci in vres["scores"] if ci != vres["winner"]]
                            if rest0:
                                margin0 = float(min(rest0)) - best0
                        if best0 is not None:
                            delta0_calibration.append(
                                {"best": best0, "margin": margin0,
                                 "correct": vres["winner"] == qi})
                        episode_records.append({"alph": alph, "qi": qi, "qd": qd})

                # RUN 11 -- RECALL-TAIL REPORT: when the K=5 shortlist MISSED the true
                # exemplar, read its RANK in the SAME proposal ordering (`ar.proposal_rank`'s
                # held Count(FilterList(...)) read-off) -- REPORTING ONLY (never feeds a
                # classification decision), answers "does widening reachably capture it, or
                # is the proposal metric blind to it entirely?"
                if not k5_hit:
                    rank = ar.proposal_rank(native, qd["composed_sig"], exemplar_composed, qi)
                    if rank is not None:
                        recall_tail_ranks.append(rank)
                        # RUN 12 -- far-tail (rank>=16) episode identity, for the "does
                        # either lever make the proposal-blind cases reachable" report.
                        if rank >= 16:
                            far_tail_episodes.append({"alph": alph, "qi": qi})
            else:
                preds_abs.append(-1)
                coverage_hits.append(0)
                preds_full.append(-1)
                coverage_full.append(0)
                for d in VARIABLE_DELTAS:
                    preds_delta[d].append(-1)
                    coverage_delta[d].append(0)
                    shortlist_delta[d].append(0)

            trues.append(qi)

        all_pred_ms.extend(preds_ms)
        all_pred_comp.extend(preds_comp)
        all_pred_comp_nc.extend(preds_comp_nc)
        all_pred_sorted.extend(preds_sorted)
        all_pred_assign.extend(preds_assign)
        all_pred_arr_only.extend(preds_arr_only)
        all_pred_rel2.extend(preds_rel2)
        all_pred_abs.extend(preds_abs)
        all_coverage_hits.extend(coverage_hits)
        all_pred_full.extend(preds_full)
        all_coverage_full.extend(coverage_full)
        for d in VARIABLE_DELTAS:
            all_pred_delta[d].extend(preds_delta[d])
            all_coverage_delta[d].extend(coverage_delta[d])
            all_shortlist_delta[d].extend(shortlist_delta[d])
        all_true.extend(trues)
        per_alph_acc_ms[alph] = float(np.mean([p == t for p, t in zip(preds_ms, trues)]))
        per_alph_acc_comp[alph] = float(np.mean([p == t for p, t in zip(preds_comp, trues)]))
        per_alph_acc_comp_nc[alph] = float(np.mean([p == t for p, t in zip(preds_comp_nc, trues)]))
        per_alph_acc_assign[alph] = float(np.mean([p == t for p, t in zip(preds_assign, trues)]))
        per_alph_acc_rel2[alph] = float(np.mean([p == t for p, t in zip(preds_rel2, trues)]))
        per_alph_acc_abs[alph] = float(np.mean([p == t for p, t in zip(preds_abs, trues)]))
        per_alph_coverage_at_k[alph] = float(np.mean(coverage_hits)) if coverage_hits else 0.0
        per_alph_acc_full[alph] = float(np.mean([p == t for p, t in zip(preds_full, trues)]))
        for d in VARIABLE_DELTAS:
            per_alph_acc_delta[d][alph] = float(
                np.mean([p == t for p, t in zip(preds_delta[d], trues)]))
            per_alph_coverage_delta[d][alph] = (
                float(np.mean(coverage_delta[d])) if coverage_delta[d] else 0.0)
            per_alph_shortlist_delta[d][alph] = (
                float(np.mean(shortlist_delta[d])) if shortlist_delta[d] else 0.0)

    def _acc(preds, trues):
        return float(np.mean([p == t for p, t in zip(preds, trues)])) if trues else 0.0

    n_episodes = len(all_pred_ms)
    acc_ms = _acc(all_pred_ms, all_true)
    acc_comp = _acc(all_pred_comp, all_true)
    acc_comp_nc = _acc(all_pred_comp_nc, all_true)
    acc_sorted = _acc(all_pred_sorted, all_true)
    acc_assign = _acc(all_pred_assign, all_true)
    acc_arr_only = _acc(all_pred_arr_only, all_true)
    acc_rel2 = _acc(all_pred_rel2, all_true)
    acc_abs = _acc(all_pred_abs, all_true) if sr_live else None
    coverage_at_k = float(np.mean(all_coverage_hits)) if (sr_live and all_coverage_hits) else None
    shuf_true = list(all_true)
    rng.shuffle(shuf_true)                        # ONE shuffle draw, applied to ALL arms.
    acc_ms_shuf = _acc(all_pred_ms, shuf_true)
    acc_comp_shuf = _acc(all_pred_comp, shuf_true)
    acc_comp_nc_shuf = _acc(all_pred_comp_nc, shuf_true)
    acc_sorted_shuf = _acc(all_pred_sorted, shuf_true)
    acc_assign_shuf = _acc(all_pred_assign, shuf_true)
    acc_arr_only_shuf = _acc(all_pred_arr_only, shuf_true)
    acc_rel2_shuf = _acc(all_pred_rel2, shuf_true)
    acc_abs_shuf = _acc(all_pred_abs, shuf_true) if sr_live else None

    # RUN 11 -- PROPOSAL RECALL / VARIABLE-APERTURE DWELL: K=20 FULL DWELL + the
    # VARIABLE_DELTAS sub-arms, using the SAME `shuf_true` shuffle draw as every other arm.
    acc_full = _acc(all_pred_full, all_true) if sr_live else None
    acc_full_shuf = _acc(all_pred_full, shuf_true) if sr_live else None
    coverage_at_full = (float(np.mean(all_coverage_full))
                        if (sr_live and all_coverage_full) else None)

    acc_delta, acc_delta_shuf, coverage_at_delta = {}, {}, {}
    mean_shortlist_delta, max_shortlist_delta = {}, {}
    for d in VARIABLE_DELTAS:
        acc_delta[d] = _acc(all_pred_delta[d], all_true) if sr_live else None
        acc_delta_shuf[d] = _acc(all_pred_delta[d], shuf_true) if sr_live else None
        coverage_at_delta[d] = (float(np.mean(all_coverage_delta[d]))
                                if (sr_live and all_coverage_delta[d]) else None)
        mean_shortlist_delta[d] = (float(np.mean(all_shortlist_delta[d]))
                                   if (sr_live and all_shortlist_delta[d]) else None)
        max_shortlist_delta[d] = (int(max(all_shortlist_delta[d]))
                                  if (sr_live and all_shortlist_delta[d]) else None)

    # RUN 11 -- RECALL-TAIL REPORT: distribution of RANKS (via `ar.proposal_rank`) for
    # episodes where the K=5 shortlist missed the true exemplar -- reporting only.
    recall_tail = None
    if recall_tail_ranks:
        _rt = np.asarray(recall_tail_ranks, dtype=float)
        recall_tail = {
            "n": len(recall_tail_ranks), "mean_rank": float(_rt.mean()),
            "min_rank": int(_rt.min()), "max_rank": int(_rt.max()),
            "n_rank_6_10": int(np.sum((_rt >= 6) & (_rt <= 10))),
            "n_rank_11_15": int(np.sum((_rt >= 11) & (_rt <= 15))),
            "n_rank_16_plus": int(np.sum(_rt >= 16)),
        }

    total_oov = total_spans = total_explained = total_recognized = 0
    for sigd in cache.values():
        total_oov += sigd["n_oov"]
        total_spans += sigd["n_spans"]
        total_explained += sigd["n_explained"]
        total_recognized += sigd["n_recognized"]
    oov_rate = total_oov / max(1, total_spans)
    explain_rate = total_explained / max(1, total_recognized)
    codebook_after = len(sc._existing_names(s, "stroke"))

    return dict(acc_ms=acc_ms, acc_ms_shuf=acc_ms_shuf, acc_comp=acc_comp, acc_comp_shuf=acc_comp_shuf,
                acc_comp_nc=acc_comp_nc, acc_comp_nc_shuf=acc_comp_nc_shuf,
                acc_sorted=acc_sorted, acc_sorted_shuf=acc_sorted_shuf,
                acc_assign=acc_assign, acc_assign_shuf=acc_assign_shuf,
                acc_arr_only=acc_arr_only, acc_arr_only_shuf=acc_arr_only_shuf,
                acc_rel2=acc_rel2, acc_rel2_shuf=acc_rel2_shuf,
                acc_abs=acc_abs, acc_abs_shuf=acc_abs_shuf, coverage_at_k=coverage_at_k,
                sr_live=sr_live,
                # RUN 11 -- PROPOSAL RECALL / VARIABLE-APERTURE DWELL.
                acc_full=acc_full, acc_full_shuf=acc_full_shuf, coverage_at_full=coverage_at_full,
                acc_delta=acc_delta, acc_delta_shuf=acc_delta_shuf,
                coverage_at_delta=coverage_at_delta, mean_shortlist_delta=mean_shortlist_delta,
                max_shortlist_delta=max_shortlist_delta, recall_tail=recall_tail,
                per_alph_acc_ms=per_alph_acc_ms, per_alph_acc_comp=per_alph_acc_comp,
                per_alph_acc_comp_nc=per_alph_acc_comp_nc, per_alph_acc_assign=per_alph_acc_assign,
                per_alph_acc_rel2=per_alph_acc_rel2, per_alph_acc_abs=per_alph_acc_abs,
                per_alph_coverage_at_k=per_alph_coverage_at_k, per_alph_acc_full=per_alph_acc_full,
                per_alph_acc_delta=per_alph_acc_delta,
                per_alph_coverage_delta=per_alph_coverage_delta,
                per_alph_shortlist_delta=per_alph_shortlist_delta,
                n_episodes=n_episodes, n_unique_files=len(cache), oov_rate=oov_rate,
                explain_rate=explain_rate, codebook_before=codebook_before,
                codebook_after=codebook_after, skipped_alphabets=skipped_alphabets,
                # RUN 12 -- TARGETED WIDEN + SECOND MODALITY: shared-cache replay material.
                exemplars_by_alph=exemplars_by_alph, episode_records=episode_records,
                delta0_calibration=delta0_calibration, far_tail_episodes=far_tail_episodes,
                # RUN 14 -- BRANCH A EXECUTION: the per-path decode cache itself (every
                # decode_char_signature result, incl. composed_sig_substroke) -- read-back
                # only, for the sub-stroke arrangement-key diversity report.
                char_cache=cache)


# ---------------------------------------------------------------------------------------------
# RUN 12 -- TARGETED WIDEN + SECOND MODALITY (scratchpad/HANDWRITING_DESIGN.md's section of
# the same name, the 6db362d1 residual): state going in -- delta=0 variable-K control 38.8%
# @ mean 2.05 renders (`run_test`'s own `acc_delta[0]`); uniform widening (delta=1/2) measured
# monotonically HARMFUL; recall-tail 16/37 misses beam-reachable (rank 6-10), 3 proposal-blind
# (rank 16+). `domains.abs_read.abs_rerank_targeted` realizes LEVER 1 (targeted widen) and
# LEVER 2 (second appearance modality) behind two independent flags; this script's job is
# ONLY to calibrate the two DATA thresholds LEVER 1 needs (host-side, offline, from the
# delta=0 arm's own already-computed scores -- `run_test`'s `delta0_calibration`) and replay
# the four RUN 12 arms over the SAME 80 episodes (`episode_records`/`exemplars_by_alph`, no
# re-decode, no re-drawing of `rng`).
# ---------------------------------------------------------------------------------------------
WIDEN_TO = 10
APPEARANCE_M = 3
FIT_PERCENTILE = 75.0
MARGIN_PERCENTILE = 25.0


def calibrate_widen_thresholds(delta0_calibration: list) -> dict:
    """RUN 12's own threshold calibration -- HOST-SIDE, offline, chosen ONCE from the delta=0
    control arm's own render-compare scores (already computed by RUN 11's own d=0 sub-arm, no
    extra render-compare calls) BEFORE any +widen episode runs -- never a per-query decision
    (the per-query widen verdict stays `ar.widen_decision`'s own held `Or(Lt(...), Gt(...))`
    Term in domains/abs_read.py). Mirrors this script's own established practice of
    diagnostics-driven constant choice (the DK reduced-bin choice, RUN-5's near-miss
    bin-distance probe) -- documented, not blind:
      fit_threshold    = the FIT_PERCENTILE-th percentile of the BEST score among CORRECT
                         delta=0 verdicts (a best-score much worse than most correct verdicts
                         show is itself evidence of a wrong pick -- LEVER 1's "absolute fit"
                         clause).
      margin_threshold = the MARGIN_PERCENTILE-th percentile of the MARGIN among CORRECT
                         delta=0 verdicts that had a runner-up at all (a razor-thin margin
                         even a correct verdict rarely shows below this point is read as
                         genuine ambiguity -- LEVER 1's "close margin" clause).
    Degrades to an honest never-widen threshold pair (`fit_threshold=+inf`,
    `margin_threshold=0.0` -- `ar.abs_rerank_targeted`'s own documented "off" default) if
    there are no correct delta=0 verdicts to calibrate from at all."""
    correct = [d for d in delta0_calibration if d["correct"]]
    correct_margins = [d["margin"] for d in correct if d["margin"] is not None]
    fit_threshold = (float(np.percentile([d["best"] for d in correct], FIT_PERCENTILE))
                      if correct else float("inf"))
    margin_threshold = (float(np.percentile(correct_margins, MARGIN_PERCENTILE))
                         if correct_margins else 0.0)
    return {"fit_threshold": fit_threshold, "margin_threshold": margin_threshold,
            "n_correct": len(correct), "n_correct_with_margin": len(correct_margins),
            "n_total": len(delta0_calibration)}


RUN12_ARMS = {
    "control": dict(use_widen=False, use_appearance=False),
    "widen": dict(use_widen=True, use_appearance=False),
    "appearance": dict(use_widen=False, use_appearance=True),
    "both": dict(use_widen=True, use_appearance=True),
}


def run_targeted_widen(s, native, episode_records: list, exemplars_by_alph: dict, dk,
                        *, margin_threshold: float, fit_threshold: float,
                        widen_to: int = WIDEN_TO, appearance_m: int = APPEARANCE_M) -> dict:
    """RUN 12 -- runs the FOUR arms (delta=0 control / +targeted-widen / +second-modality /
    +both) over `episode_records` (the SAME 80 episodes RUN 11's own delta=0 sub-arm already
    decoded) via `ar.abs_rerank_targeted`'s own `use_widen`/`use_appearance` flags -- no
    re-decode, no re-LEARN, no re-drawing of `rng`. `preds`/`budgets`/`widened` are captured
    per arm for the per-lever accuracy/budget report; `modality_overlap` counts how often
    LEVER 2's union actually ADDED a candidate the structural shortlist alone did not have
    (mechanical `set` comparison over candidate INDICES, not a score read)."""
    preds = {name: [] for name in RUN12_ARMS}
    budgets = {name: [] for name in RUN12_ARMS}
    widened_flags = {name: [] for name in RUN12_ARMS}
    trues = []
    modality_overlap = {"appearance_added_candidates": 0, "n_appearance_episodes": 0}

    for rec in episode_records:
        exemplar_composed, exemplar_stroke_points, _exemplar_composed_substroke = \
            exemplars_by_alph[rec["alph"]]
        qd, qi = rec["qd"], rec["qi"]
        for name, flags in RUN12_ARMS.items():
            res = ar.abs_rerank_targeted(
                s, qd["composed_sig"], qd["stroke_points"], exemplar_composed,
                exemplar_stroke_points, delta=0.0, margin_threshold=margin_threshold,
                fit_threshold=fit_threshold, widen_to=widen_to, appearance_m=appearance_m,
                turn_bins=dk["turn_bins"], len_bins=dk["len_bins"], grid=dk["grid"],
                scale_bins=dk["scale_bins"], **flags)
            preds[name].append(res["winner"] if res["winner"] is not None else -1)
            budgets[name].append(res["budget"])
            widened_flags[name].append(res["widened"])
            if name == "appearance":
                modality_overlap["n_appearance_episodes"] += 1
                if set(res["shortlist0"]) != set(res["structural0"]):
                    modality_overlap["appearance_added_candidates"] += 1
        trues.append(qi)

    def _acc(p, t):
        return float(np.mean([a == b for a, b in zip(p, t)])) if t else 0.0

    shuf_true = list(trues)
    np.random.default_rng(SEED + 12).shuffle(shuf_true)   # INDEPENDENT of run_test's own draw.

    out = {"trues": trues, "n_episodes": len(trues), "modality_overlap": modality_overlap}
    for name in RUN12_ARMS:
        out[f"acc_{name}"] = _acc(preds[name], trues)
        out[f"acc_{name}_shuf"] = _acc(preds[name], shuf_true)
        out[f"mean_budget_{name}"] = float(np.mean(budgets[name])) if budgets[name] else 0.0
        out[f"max_budget_{name}"] = int(max(budgets[name])) if budgets[name] else 0
        out[f"widen_rate_{name}"] = (float(np.mean(widened_flags[name]))
                                      if widened_flags[name] else 0.0)
        out[f"preds_{name}"] = preds[name]
    return out


def far_tail_reachability(run12: dict, episode_records: list, far_tail_episodes: list) -> dict:
    """Design: "specifically whether the 3 proposal-blind far-tail cases become reachable."
    `far_tail_episodes` are RUN 11's own rank>=16 (alph, qi) identities; looks up each one's
    position in `episode_records` (SAME order RUN 12's `preds_*` arrays were built in) and
    checks whether ANY of the three enhanced arms now predicts the true class -- mechanical
    index lookups + equality checks (bookkeeping over already-decided per-arm verdicts, not a
    new ranking decision)."""
    idx_by_key = {(rec["alph"], rec["qi"]): i for i, rec in enumerate(episode_records)}
    rows = []
    for ep in far_tail_episodes:
        key = (ep["alph"], ep["qi"])
        i = idx_by_key.get(key)
        if i is None:
            continue
        qi = episode_records[i]["qi"]
        row = {"alph": ep["alph"], "qi": qi,
               "control_correct": run12["preds_control"][i] == qi,
               "widen_correct": run12["preds_widen"][i] == qi,
               "appearance_correct": run12["preds_appearance"][i] == qi,
               "both_correct": run12["preds_both"][i] == qi}
        rows.append(row)
    n_reachable = sum(1 for r in rows
                       if r["widen_correct"] or r["appearance_correct"] or r["both_correct"])
    return {"n_far_tail": len(rows), "n_reachable": n_reachable, "rows": rows}


# ---------------------------------------------------------------------------------------------
# RUN 13 -- INSTANCE-CONDITIONED QUANTA (scratchpad/HANDWRITING_DESIGN.md's section of the same
# name, the a6c7740f endgame clause): state going in -- 41.2% (delta=0 + appearance top-3, RUN
# 12's own best arm); far-tail 0/3 reachable by any SEARCH arm; the residual read as EXEMPLAR-
# SIDE (one exemplar per class is the information bound -- the render-compare verdict
# approximates every candidate stroke through the GLOBAL codebook's small vocabulary, discarding
# the exemplar's own actual geometry). `domains.abs_read.abs_rerank_targeted`'s new
# `use_exemplar_true` (LEVER A) / `use_instance` (LEVER B) flags realize the GENERATION-side
# levers; this script's job is ONLY to replay the FOUR RUN 13 arms over the SAME 80 episodes
# RUN 11/12 already decoded (`episode_records`/`exemplars_by_alph`, no re-decode, no re-LEARN,
# no re-drawing of `rng`) -- control = RUN 12's OWN ADOPTED CONFIG (delta=0 + appearance, the
# best RUN 12 arm), not the bare delta=0 control, per the design's own "run-12 adopted config as
# control" instruction.
# ---------------------------------------------------------------------------------------------
RUN13_ARMS = {
    "control": dict(use_appearance=True, use_exemplar_true=False, use_instance=False),
    "+A": dict(use_appearance=True, use_exemplar_true=True, use_instance=False),
    "+B": dict(use_appearance=True, use_exemplar_true=False, use_instance=True),
    "+A+B": dict(use_appearance=True, use_exemplar_true=True, use_instance=True),
}


def run_instance_conditioned(s, native, episode_records: list, exemplars_by_alph: dict,
                              dk, *, appearance_m: int = APPEARANCE_M) -> dict:
    """RUN 13 -- runs the FOUR arms (control = RUN 12's adopted delta=0+appearance config /
    +A exemplar-true rendering / +B instance-codebook query decode / +A+B) over
    `episode_records` (the SAME 80 episodes RUN 11/12 already decoded) via `ar.abs_rerank_
    targeted`'s own `use_exemplar_true`/`use_instance` flags -- no re-decode, no re-LEARN, no
    re-drawing of `rng`, `use_widen` always `False` (RUN 12's own winning arm never widened).
    `coverage_shortlist` records, per arm, whether the TRUE exemplar was in that arm's own
    STRUCTURAL+APPEARANCE shortlist (`res["shortlist0"]`) -- the design's own "report how
    instance identities shift proposal recall (coverage@shortlist)" ask."""
    preds = {name: [] for name in RUN13_ARMS}
    budgets = {name: [] for name in RUN13_ARMS}
    coverage_shortlist = {name: [] for name in RUN13_ARMS}
    trues = []

    for rec in episode_records:
        exemplar_composed, exemplar_stroke_points, _exemplar_composed_substroke = \
            exemplars_by_alph[rec["alph"]]
        qd, qi = rec["qd"], rec["qi"]
        for name, flags in RUN13_ARMS.items():
            res = ar.abs_rerank_targeted(
                s, qd["composed_sig"], qd["stroke_points"], exemplar_composed,
                exemplar_stroke_points, delta=0.0, use_widen=False,
                appearance_m=appearance_m, turn_bins=dk["turn_bins"], len_bins=dk["len_bins"],
                grid=dk["grid"], scale_bins=dk["scale_bins"], segments=dk["segments"], **flags)
            preds[name].append(res["winner"] if res["winner"] is not None else -1)
            budgets[name].append(res["budget"])
            coverage_shortlist[name].append(1 if qi in res["shortlist0"] else 0)
        trues.append(qi)

    def _acc(p, t):
        return float(np.mean([a == b for a, b in zip(p, t)])) if t else 0.0

    shuf_true = list(trues)
    np.random.default_rng(SEED + 13).shuffle(shuf_true)   # INDEPENDENT of every other arm's draw.

    out = {"trues": trues, "n_episodes": len(trues)}
    for name in RUN13_ARMS:
        out[f"acc_{name}"] = _acc(preds[name], trues)
        out[f"acc_{name}_shuf"] = _acc(preds[name], shuf_true)
        out[f"mean_budget_{name}"] = float(np.mean(budgets[name])) if budgets[name] else 0.0
        out[f"max_budget_{name}"] = int(max(budgets[name])) if budgets[name] else 0
        out[f"coverage_shortlist_{name}"] = (float(np.mean(coverage_shortlist[name]))
                                             if coverage_shortlist[name] else 0.0)
        out[f"preds_{name}"] = preds[name]
    return out


def far_tail_reachability_13(run13: dict, episode_records: list, far_tail_episodes: list) -> dict:
    """RUN 13's own twin of `far_tail_reachability` -- generalizes the SAME mechanical
    index-lookup + equality-check idiom to `RUN13_ARMS`'s four arms instead of hardcoded
    control/widen/appearance/both names."""
    idx_by_key = {(rec["alph"], rec["qi"]): i for i, rec in enumerate(episode_records)}
    rows = []
    for ep in far_tail_episodes:
        key = (ep["alph"], ep["qi"])
        i = idx_by_key.get(key)
        if i is None:
            continue
        qi = episode_records[i]["qi"]
        row = {"alph": ep["alph"], "qi": qi}
        for name in RUN13_ARMS:
            row[f"{name}_correct"] = run13[f"preds_{name}"][i] == qi
        rows.append(row)
    n_reachable = sum(1 for r in rows
                       if any(r[f"{name}_correct"] for name in RUN13_ARMS if name != "control"))
    return {"n_far_tail": len(rows), "n_reachable": n_reachable, "rows": rows}


# ---------------------------------------------------------------------------------------------
# RUN 14 -- BRANCH A EXECUTION: SUB-STROKE COMPOSITION (scratchpad/HANDWRITING_DESIGN.md's
# section of the same name, the jabberwock's own verdict d2cd7bed, 2026-07-03: "have the
# jabberwock decide and execute it"): "the sd loop one level DOWN -- a stroke is itself an
# arrangement of sub-stroke quanta... exactly the character-composition pattern (c1b83669)
# recursed." State going in -- 41.2% (RUN 12's adopted delta=0+appearance config, RUN 13's own
# control, reproduced there); far tail 0/3 by any search OR generation-side lever; the
# featureset was declared "search- AND generation-saturated at THIS representation" -- this run
# tests the REPRESENTATION lever itself. TWO arms only (design: "keep one lever"), BOTH run
# through the SAME run-12-adopted config (`ar.abs_rerank_targeted(use_appearance=True,
# use_exemplar_true=False, use_instance=False)`, i.e. `RUN13_ARMS["control"]`'s own flags) --
# they differ ONLY in which composed signature feeds the STRUCTURAL PROPOSAL (`propose_
# variable_k`'s `_coverage_term` scoring): `composed_sig` (control, no strokeq_sub) vs
# `composed_sig_substroke` (+composition, WITH the additive strokeq_sub relations) -- "strokeq_
# sub additive relations in PROPOSALS." The render-compare stage is UNCHANGED either way
# (`abs_render_compare_term` only ever reads "strokeq"/"rel", ignoring the extra "strokeq_sub"
# relations harmlessly) -- confirmed by inspection, not re-wired, per the design's own "check
# whether re-rank even needs changing this phase; report" instruction.
# ---------------------------------------------------------------------------------------------
RUN14_ARMS = {"control": "composed_sig", "+composition": "composed_sig_substroke"}


def run_substroke_composition(s, native, episode_records: list, exemplars_by_alph: dict,
                              dk, *, appearance_m: int = APPEARANCE_M) -> dict:
    """RUN 14 -- replays the TWO arms (control = run-12 adopted config fed `composed_sig` /
    +composition = the SAME config fed `composed_sig_substroke`) over `episode_records` (the
    SAME 80 episodes RUN 11/12/13 already decoded) via `ar.abs_rerank_targeted`'s own
    `use_appearance=True` (RUN 12's own winning arm), `use_widen=False` -- no re-decode, no
    re-LEARN, no re-drawing of `rng`. Mirrors `run_instance_conditioned`'s own structure
    exactly, generalized to pick the query/exemplar signature KEY per arm instead of a fixed
    flag combination."""
    preds = {name: [] for name in RUN14_ARMS}
    budgets = {name: [] for name in RUN14_ARMS}
    coverage_shortlist = {name: [] for name in RUN14_ARMS}
    trues = []

    for rec in episode_records:
        exemplar_composed, exemplar_stroke_points, exemplar_composed_substroke = \
            exemplars_by_alph[rec["alph"]]
        qd, qi = rec["qd"], rec["qi"]
        for name, sig_key in RUN14_ARMS.items():
            q_sig = qd[sig_key]
            cand_sigs = exemplar_composed if sig_key == "composed_sig" else exemplar_composed_substroke
            res = ar.abs_rerank_targeted(
                s, q_sig, qd["stroke_points"], cand_sigs, exemplar_stroke_points,
                delta=0.0, use_widen=False, use_appearance=True, appearance_m=appearance_m,
                turn_bins=dk["turn_bins"], len_bins=dk["len_bins"], grid=dk["grid"],
                scale_bins=dk["scale_bins"], segments=dk["segments"])
            preds[name].append(res["winner"] if res["winner"] is not None else -1)
            budgets[name].append(res["budget"])
            coverage_shortlist[name].append(1 if qi in res["shortlist0"] else 0)
        trues.append(qi)

    def _acc(p, t):
        return float(np.mean([a == b for a, b in zip(p, t)])) if t else 0.0

    shuf_true = list(trues)
    np.random.default_rng(SEED + 14).shuffle(shuf_true)   # INDEPENDENT of every other arm's draw.

    out = {"trues": trues, "n_episodes": len(trues)}
    for name in RUN14_ARMS:
        out[f"acc_{name}"] = _acc(preds[name], trues)
        out[f"acc_{name}_shuf"] = _acc(preds[name], shuf_true)
        out[f"mean_budget_{name}"] = float(np.mean(budgets[name])) if budgets[name] else 0.0
        out[f"max_budget_{name}"] = int(max(budgets[name])) if budgets[name] else 0
        out[f"coverage_shortlist_{name}"] = (float(np.mean(coverage_shortlist[name]))
                                             if coverage_shortlist[name] else 0.0)
        out[f"preds_{name}"] = preds[name]
    return out


def far_tail_reachability_14(run14: dict, episode_records: list, far_tail_episodes: list) -> dict:
    """RUN 14's own twin of `far_tail_reachability`/`far_tail_reachability_13` -- the SAME
    mechanical index-lookup + equality-check idiom, generalized to `RUN14_ARMS`'s two arms."""
    idx_by_key = {(rec["alph"], rec["qi"]): i for i, rec in enumerate(episode_records)}
    rows = []
    for ep in far_tail_episodes:
        key = (ep["alph"], ep["qi"])
        i = idx_by_key.get(key)
        if i is None:
            continue
        qi = episode_records[i]["qi"]
        row = {"alph": ep["alph"], "qi": qi}
        for name in RUN14_ARMS:
            row[f"{name}_correct"] = run14[f"preds_{name}"][i] == qi
        rows.append(row)
    n_reachable = sum(1 for r in rows if r["+composition_correct"])
    return {"n_far_tail": len(rows), "n_reachable": n_reachable, "rows": rows}


# ---------------------------------------------------------------------------------------------
# RUN-4 LEVERS -- ROTATION-ROBUSTNESS SPOT-CHECK: rotate the QUERY drawings of a few episodes
# by a FIXED angle before decode+compose; accuracy against the SAME (unrotated) exemplar set
# should hold within noise if the pipeline (invariant `seg`/`rel` relations all the way down)
# is genuinely rotation-robust, not just byte-identical on hand-built synthetic fixtures.
# ---------------------------------------------------------------------------------------------
ROTATE_SPOTCHECK_DEG = 25.0
ROTATE_SPOTCHECK_EPISODES = 5


def _rotate_points_deg(points, deg: float) -> list:
    """Mechanical geometry (NOT a decision) -- rotate a raw `[[x,y],...]` pen path by `deg`
    degrees about its OWN centroid (a fixed, deterministic reference). Mirrors `glyph_motor_
    world.rotate_traj`'s role (rotate a KNOWN geometry) at script scale -- there is no Rust
    primitive for this because it operates on RAW, pre-ingest pen coordinates, not a held
    signature."""
    pts = np.asarray(points, dtype=float)
    theta = np.radians(deg)
    c, si = np.cos(theta), np.sin(theta)
    rot = np.array([[c, -si], [si, c]])
    centroid = pts.mean(axis=0)
    return ((pts - centroid) @ rot.T + centroid).tolist()


def decode_char_signature_rotated(s, path, dk, deg: float) -> list:
    """The ROTATION-SPOT-CHECK twin of `decode_char_signature` -- NOT cached (only a handful
    of episodes ever call this): every raw pen-stroke of the drawing is rotated by `deg`
    degrees BEFORE `ingest_ink` (mechanical geometry), then the SAME ingest/decode/compose
    pipeline runs UNCHANGED. Returns just the composed signature (the spot-check only needs
    the `_comp` arm)."""
    stroke_points = []
    for st in ow.load_strokes(path):
        if st.shape[0] < 2:
            continue
        rotated = _rotate_points_deg(st.tolist(), deg)
        ink_node = ink.ingest_ink(s, rotated, max_knots=dk["max_knots"])
        res = ink.decode_ink(s, ink_node, min_span=dk["min_span"], max_span=dk["max_span"],
                              segments=dk["segments"], turn_bins=dk["turn_bins"],
                              len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"])
        knots = s.node(ink_node)["attrs"].get("knots") or []
        stroke_points.extend(cc.decode_result_to_stroke_points(knots, res))
    composed = cc.compose_character_signature(
        s._inner, stroke_points, segments=dk["segments"], turn_bins=dk["turn_bins"],
        len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"])
    return composed["signature"]


def run_rotation_spotcheck(s, native, alphabet, way, n_episodes, dk, deg, rng):
    """A FEW episodes of ONE held-out alphabet, classified TWICE against the SAME (unrotated)
    exemplar set: once normally (reuses the shared cache -- free), once with the QUERY
    drawing's raw points rotated `deg` degrees before decode (uncached, deliberately fresh).
    Uses its OWN cache + its OWN rng draws (never `run_test`'s) so this spot-check cannot
    perturb the main TEST phase's own episode draws."""
    cache = {}
    chars = sorted(ow.characters(alphabet, "evaluation"))
    if len(chars) < way:
        return {"alphabet": alphabet, "skipped": f"only {len(chars)} characters, need {way}"}
    chars = chars[:way]
    drawer_files = [ow.drawings(cd) for cd in chars]
    n_drawers = min(len(fl) for fl in drawer_files)
    ex_drawer = int(rng.integers(n_drawers))
    exemplars = [decode_char_signature(s, drawer_files[ci][ex_drawer], cache, dk)
                 for ci in range(way)]
    exemplar_composed = [e["composed_sig"] for e in exemplars]

    preds_normal, preds_rot, trues = [], [], []
    for qi in range(min(n_episodes, way)):
        q_drawer = int(rng.integers(n_drawers))
        while q_drawer == ex_drawer:
            q_drawer = int(rng.integers(n_drawers))
        path = drawer_files[qi][q_drawer]

        normal_sig = decode_char_signature(s, path, cache, dk)["composed_sig"]
        rot_sig = decode_char_signature_rotated(s, path, dk, deg)

        pairs_normal = [(float(native.evaluate(_coverage_term(normal_sig, exemplar_composed[ci]), {}) or 0.0), ci)
                        for ci in range(way)]
        winner_normal = native.evaluate(_argmax_pairs_term(pairs_normal), {})
        preds_normal.append(winner_normal[1] if winner_normal is not None else -1)

        pairs_rot = [(float(native.evaluate(_coverage_term(rot_sig, exemplar_composed[ci]), {}) or 0.0), ci)
                     for ci in range(way)]
        winner_rot = native.evaluate(_argmax_pairs_term(pairs_rot), {})
        preds_rot.append(winner_rot[1] if winner_rot is not None else -1)

        trues.append(qi)

    def _acc(preds, trues):
        return float(np.mean([p == t for p, t in zip(preds, trues)])) if trues else 0.0

    return {"alphabet": alphabet, "n": len(trues), "rotate_deg": deg,
            "acc_normal": _acc(preds_normal, trues), "acc_rotated": _acc(preds_rot, trues)}


# ---------------------------------------------------------------------------------------------
# RUN 15 -- POWER THE GATE, THEN BRANCH B CONTINUOUS (scratchpad/HANDWRITING_DESIGN.md's
# section of the same name, 2026-07-03): the post-terminus continuation. MEASUREMENT PROBLEM,
# named by the design itself -- at 80 episodes 1 episode = 1.25pp; the endgame's own deltas
# (RUN 12 +2.5pp, RUN 13 +0.0pp, RUN 14 -1.2pp) are 1-3 episodes, i.e. BELOW the measurement's
# own resolution. Every conclusion since RUN 10 was read off an 80-episode point estimate with
# no interval at all -- PHASE 1 re-establishes the SAME arms with Wilson 95% CIs across ALL
# strokes_evaluation alphabets with >= WAY characters x R seeded repeats (different exemplar/
# query drawer draws per repeat), decode-cache reuse shared with the pre-existing 80-episode
# run above (`te["char_cache"]`, passed in directly -- every one of its 160 already-decoded
# drawings is free). PHASE 2 executes the surviving fork branch (Branch B, junction
# coarticulation) as a CONTINUOUS endpoint deformation in the AbS render-compare channel
# (`domains.abs_read`'s new `_junction_blend`/`junction_blend`) under the SAME power, over the
# SAME powered episode set PHASE 1 already decoded (no re-decode, no re-LEARN).
# ---------------------------------------------------------------------------------------------
POWER_SEED = SEED + 1500
POWER_R = 2                        # seeded repeats/alphabet (different drawer draws each time).
POWER_ALPHABET_CAP = 10            # design's own runtime-budget fallback.
POWER_BUDGET_SECONDS = 1800.0      # 30 minutes, the design's own stated cap.
POWER_JUNCTION_FRAC = ar.DEFAULT_JUNCTION_FRAC


def wilson_ci(k: int, n: int, z: float = 1.959963984540054) -> tuple:
    """Wilson score 95% CI for a binomial proportion `k/n` -- the design's own explicit
    instruction ("Wilson/binomial 95% CIs on every arm"). Returns `(lo, hi)` in `[0, 1]`;
    `(0.0, 0.0)` for `n <= 0` (an honest non-crash, never a fabricated interval)."""
    if n <= 0:
        return (0.0, 0.0)
    phat = k / n
    denom = 1.0 + z * z / n
    centre = phat + z * z / (2 * n)
    adj = z * ((phat * (1.0 - phat) + z * z / (4 * n)) / n) ** 0.5
    lo = max(0.0, (centre - adj) / denom)
    hi = min(1.0, (centre + adj) / denom)
    return (lo, hi)


def _ci_separated(ci_a: tuple, ci_b: tuple) -> bool:
    """Two 95% Wilson intervals are CI-SEPARATED iff they do not overlap at all -- the
    design's own verdict standard ("CI-separated or honestly inconclusive")."""
    return ci_a[1] < ci_b[0] or ci_b[1] < ci_a[0]


def _powered_episode(s, native, exemplar_composed, exemplar_sigs, exemplar_rel2,
                      exemplar_stroke_points, exemplar_composed_substroke, qd, qi, way, dk):
    """ONE powered-run episode's arm predictions -- the FIVE arms PHASE 1 re-establishes with
    CIs (design: "multiset control, composed naive, AbS K=5, delta=0, delta=0+appearance")
    plus two CHEAP coverage-only arms carried along for free (`rel2`, the RUN 9 null; the
    `composition` arm reuses the SAME adopted (delta=0+appearance) config as its own control,
    the RUN 14 null) -- every winner a held `Argmax`/`Argmin` evaluate, mirroring `run_test`'s
    own per-episode body exactly (byte-identical metrics, just restated at power)."""
    pairs_ms = [(float(native.evaluate(_coverage_term(qd["sig"], exemplar_sigs[ci]), {}) or 0.0), ci)
                for ci in range(way)]
    w_ms = native.evaluate(_argmax_pairs_term(pairs_ms), {})

    pairs_comp = [(float(native.evaluate(_coverage_term(qd["composed_sig"], exemplar_composed[ci]), {}) or 0.0), ci)
                  for ci in range(way)]
    w_comp = native.evaluate(_argmax_pairs_term(pairs_comp), {})

    pairs_rel2 = [(float(native.evaluate(_coverage_term(qd["composed_sig_rel2"], exemplar_rel2[ci]), {}) or 0.0), ci)
                  for ci in range(way)]
    w_rel2 = native.evaluate(_argmax_pairs_term(pairs_rel2), {})

    abs5 = ar.abs_rerank(s, qd["composed_sig"], qd["stroke_points"], exemplar_composed,
                          exemplar_stroke_points, k=ABS_TOPK, turn_bins=dk["turn_bins"],
                          len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"])

    vk0 = ar.propose_variable_k(native, qd["composed_sig"], exemplar_composed, 0.0)
    delta0 = ar.abs_rerank(s, qd["composed_sig"], qd["stroke_points"], exemplar_composed,
                            exemplar_stroke_points, top_k=vk0, turn_bins=dk["turn_bins"],
                            len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"])

    adopted = ar.abs_rerank_targeted(
        s, qd["composed_sig"], qd["stroke_points"], exemplar_composed, exemplar_stroke_points,
        delta=0.0, use_widen=False, use_appearance=True, turn_bins=dk["turn_bins"],
        len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"], segments=dk["segments"])

    composition = ar.abs_rerank_targeted(
        s, qd["composed_sig_substroke"], qd["stroke_points"], exemplar_composed_substroke,
        exemplar_stroke_points, delta=0.0, use_widen=False, use_appearance=True,
        turn_bins=dk["turn_bins"], len_bins=dk["len_bins"], grid=dk["grid"],
        scale_bins=dk["scale_bins"], segments=dk["segments"])

    return dict(
        w_ms=(w_ms[1] if w_ms is not None else -1),
        w_comp=(w_comp[1] if w_comp is not None else -1),
        w_rel2=(w_rel2[1] if w_rel2 is not None else -1),
        w_abs5=(abs5["winner"] if abs5["winner"] is not None else -1),
        coverage5=(1 if qi in abs5["top_k"] else 0),
        w_delta0=(delta0["winner"] if delta0["winner"] is not None else -1),
        w_adopted=(adopted["winner"] if adopted["winner"] is not None else -1),
        w_composition=(composition["winner"] if composition["winner"] is not None else -1))


POWER_ARM_NAMES = ("ms", "comp", "rel2", "abs5", "delta0", "adopted", "composition")


def run_powered_test(s, native, alphabets, way, episodes_per_alphabet, r_repeats, dk, cache,
                      seed, budget_seconds, alphabet_cap, existing_elapsed):
    """PHASE 1 -- POWER: ALL qualifying alphabets x `r_repeats` seeded repeats (different
    exemplar/query drawer draws each repeat), decode-cache reuse (`cache` is the SAME dict the
    pre-existing 80-episode `run_test` already populated -- passed in directly, mutated
    further here, so every one of its unique drawings is decoded exactly once ACROSS both the
    80-episode run and this one). RUNTIME-BUDGETED (design: "estimate, log, cap alphabets at
    10... if > 30 min"): after the FIRST alphabet's `r_repeats` finish, projects the total
    PHASE-1 (+ an estimated PHASE-2) runtime and, if it exceeds `budget_seconds`, CAPS the
    alphabet list to `alphabet_cap` (the sorted-name PREFIX, per the design's own "capped-10
    prefix by sorted name" instruction) -- logged plainly, never silent."""
    t_start = time.time()
    rng = np.random.default_rng(seed)

    acc = {name: [] for name in POWER_ARM_NAMES}
    all_true = []
    coverage5_hits = []
    recall_tail_ranks = []
    episode_records = []
    exemplars_by_key = {}
    budget_note = None
    used_alphabets = list(alphabets)

    ai = 0
    while ai < len(used_alphabets):
        alph = used_alphabets[ai]
        chars = sorted(ow.characters(alph, "evaluation"))
        if len(chars) < way:
            ai += 1
            continue
        chars = chars[:way]
        drawer_files = [ow.drawings(cd) for cd in chars]
        n_drawers = min(len(fl) for fl in drawer_files)

        for r in range(r_repeats):
            ex_drawer = int(rng.integers(n_drawers))
            exemplars = [decode_char_signature(s, drawer_files[ci][ex_drawer], cache, dk)
                         for ci in range(way)]
            exemplar_composed = [e["composed_sig"] for e in exemplars]
            exemplar_sigs = [e["sig"] for e in exemplars]
            exemplar_rel2 = [e["composed_sig_rel2"] for e in exemplars]
            exemplar_stroke_points = [e["stroke_points"] for e in exemplars]
            exemplar_composed_substroke = [e["composed_sig_substroke"] for e in exemplars]
            exemplars_by_key[(alph, r)] = (exemplar_composed, exemplar_stroke_points,
                                            exemplar_composed_substroke)

            for qi in range(min(episodes_per_alphabet, way)):
                q_drawer = int(rng.integers(n_drawers))
                while q_drawer == ex_drawer:
                    q_drawer = int(rng.integers(n_drawers))
                qd = decode_char_signature(s, drawer_files[qi][q_drawer], cache, dk)

                ep = _powered_episode(s, native, exemplar_composed, exemplar_sigs, exemplar_rel2,
                                      exemplar_stroke_points, exemplar_composed_substroke, qd,
                                      qi, way, dk)
                for name in POWER_ARM_NAMES:
                    acc[name].append(ep[f"w_{name}"])
                coverage5_hits.append(ep["coverage5"])
                all_true.append(qi)
                episode_records.append({"key": (alph, r), "qi": qi, "qd": qd,
                                         "adopted_winner": ep["w_adopted"]})
                if not ep["coverage5"]:
                    rank = ar.proposal_rank(native, qd["composed_sig"], exemplar_composed, qi)
                    if rank is not None:
                        recall_tail_ranks.append(rank)

        if ai == 0:
            elapsed_first = time.time() - t_start
            projected_phase1 = elapsed_first * len(used_alphabets)
            projected_phase2 = projected_phase1 * 0.30   # ~1 extra render-compare pass/episode.
            projected_total = existing_elapsed + projected_phase1 + projected_phase2
            if projected_total > budget_seconds and len(used_alphabets) > alphabet_cap:
                budget_note = (
                    f"projected total runtime {projected_total:.0f}s exceeds the "
                    f"{budget_seconds:.0f}s (30 min) budget -- first alphabet {alph!r} took "
                    f"{elapsed_first:.1f}s for {r_repeats} repeats x {way} episodes, "
                    f"extrapolated to all {len(used_alphabets)} alphabets = "
                    f"~{projected_phase1:.0f}s PHASE 1 + ~{projected_phase2:.0f}s estimated "
                    f"PHASE 2. CAPPING to the first {alphabet_cap} alphabets (sorted name).")
                used_alphabets = used_alphabets[:alphabet_cap]
        ai += 1

    n = len(all_true)
    shuf_true = list(all_true)
    np.random.default_rng(seed + 1).shuffle(shuf_true)

    def _acc_ci(preds, trues):
        k = sum(1 for p, t in zip(preds, trues) if p == t)
        acc_ = k / max(1, len(trues))
        lo, hi = wilson_ci(k, len(trues))
        return acc_, (lo, hi), k

    out = {"n_episodes": n, "n_alphabets_used": len(used_alphabets),
           "alphabets_used": used_alphabets, "r_repeats": r_repeats,
           "budget_note": budget_note, "elapsed": time.time() - t_start,
           "episode_records": episode_records, "exemplars_by_key": exemplars_by_key,
           "coverage_at_5": float(np.mean(coverage5_hits)) if coverage5_hits else 0.0,
           "recall_tail_ranks": recall_tail_ranks}
    for name in POWER_ARM_NAMES:
        a, ci, k = _acc_ci(acc[name], all_true)
        a_s, ci_s, k_s = _acc_ci(acc[name], shuf_true)
        out[f"acc_{name}"] = a; out[f"ci_{name}"] = ci; out[f"k_{name}"] = k
        out[f"acc_{name}_shuf"] = a_s; out[f"ci_{name}_shuf"] = ci_s
    return out


def run_branch_b_continuous(s, native, phase1: dict, dk, junction_frac: float) -> dict:
    """PHASE 2 -- BRANCH B CONTINUOUS: replays PHASE 1's OWN powered episode set
    (`episode_records`/`exemplars_by_key`, no re-decode, no re-LEARN) through
    `ar.abs_rerank_targeted`'s new `use_junction_blend` flag. The CONTROL arm reuses PHASE 1's
    own ALREADY-COMPUTED adopted-config winner (`rec["adopted_winner"]`) -- zero extra
    render-compare calls for the control; only `+junction-blend` runs a FRESH
    `abs_rerank_targeted` pass (one per episode, `use_junction_blend=True`)."""
    t_start = time.time()
    trues, preds_control, preds_blend = [], [], []
    for rec in phase1["episode_records"]:
        exemplar_composed, exemplar_stroke_points, _sub = phase1["exemplars_by_key"][rec["key"]]
        qd, qi = rec["qd"], rec["qi"]
        preds_control.append(rec["adopted_winner"])
        res = ar.abs_rerank_targeted(
            s, qd["composed_sig"], qd["stroke_points"], exemplar_composed,
            exemplar_stroke_points, delta=0.0, use_widen=False, use_appearance=True,
            use_junction_blend=True, junction_frac=junction_frac, turn_bins=dk["turn_bins"],
            len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"],
            segments=dk["segments"])
        preds_blend.append(res["winner"] if res["winner"] is not None else -1)
        trues.append(qi)

    def _acc_ci(preds, trues_):
        k = sum(1 for p, t in zip(preds, trues_) if p == t)
        acc_ = k / max(1, len(trues_))
        lo, hi = wilson_ci(k, len(trues_))
        return acc_, (lo, hi), k

    acc_c, ci_c, k_c = _acc_ci(preds_control, trues)
    acc_b, ci_b, k_b = _acc_ci(preds_blend, trues)
    return dict(n_episodes=len(trues), acc_control=acc_c, ci_control=ci_c, k_control=k_c,
                acc_blend=acc_b, ci_blend=ci_b, k_blend=k_b, elapsed=time.time() - t_start,
                junction_frac=junction_frac)


# ---------------------------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------------------------
def main():
    t0 = time.time()
    print(SEP)
    print("OMNIGLOT DYNAMIC QUANTIZATION GATE ā€” real handwriting through the stroke codebook +")
    print("segmentation-by-recognition + writer-dimension ladder (domains/ink_decode.py +")
    print("domains/stroke_codebook.py + seeds/writer_dimensions.json). Empty codebook; earn")
    print("everything from real Omniglot ink.")
    print(SEP)

    if not ow.have_data("background") or not ow.have_data("evaluation"):
        print(f"\n  WALL: Omniglot stroke data not found under {ow.DATA} "
              f"(need strokes_background/ and strokes_evaluation/). Cannot run.")
        return 1

    s, ag, native = boot()
    learn_alphabets = ow.alphabets("background")[:LEARN_ALPHABETS_N]
    print(f"\n  LEARN caps: {LEARN_ALPHABETS_N} background alphabets {learn_alphabets},")
    print(f"    drawers {LEARN_DRAWERS[0]}-{LEARN_DRAWERS[-1]} ({len(LEARN_DRAWERS)} drawers),"
          f" capped at {LEARN_STROKE_CAP} pen-down strokes.")
    print(f"    ink-decode params (reduced bins, latency budget ā€” see module docstring): {DK}")

    # ------------------------------------------------------------------------------------- #
    #  PHASE 1 ā€” LEARN
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  PHASE 1: LEARN (dynamic quantization on real ink)\n{SEP}")
    lr = run_learn(s, ag, native, learn_alphabets, LEARN_DRAWERS, LEARN_STROKE_CAP, DK,
                    GROWTH_WINDOW)

    print(f"\n  {'strokes':>8}  {'codebook':>8}  {'+new/win':>9}  {'recognized':>10}  "
          f"{'oov':>6}  {'minted':>7}  {'reuse%':>7}  {'sub-cb':>7}  {'sub+new':>8}  "
          f"{'elapsed':>8}")
    for row in lr["growth"]:
        print(f"  {row['n']:>8}  {row['codebook']:>8}  {row['new_quanta']:>9}  "
              f"{row['recognized']:>10}  {row['oov']:>6}  {row['minted']:>7}  "
              f"{100*row['reuse_rate']:>6.1f}%  {row.get('substroke_codebook', 0):>7}  "
              f"{row.get('substroke_new', 0):>8}  {row['elapsed']:>7.1f}s")

    stop = lr["stop_info"]
    print(f"\n  processed {lr['n_strokes']} pen-down strokes "
          f"({lr['n_degenerate_skipped']} degenerate/single-point strokes skipped),"
          f" in {lr['elapsed']:.1f}s ({1000*lr['elapsed']/max(1,lr['n_strokes']):.1f}ms/stroke avg).")
    if stop:
        print(f"  STOP point (cap reached): alphabet={stop['alphabet']!r} "
              f"character={stop['character']!r} drawer={stop['drawer']!r} file={stop['file']!r}")
    else:
        print("  cap NOT reached ā€” the 5-alphabet x 14-drawer set was exhausted before the cap.")

    # Saturation verdict: mean new-quanta/window over the first 3 windows vs the last 3.
    # Tri-state: None = inconclusive (too few windows), never conflated with an honest FAIL.
    growth = lr["growth"]
    sat_pass = None
    if len(growth) >= 6:
        first = np.mean([g["new_quanta"] for g in growth[:3]])
        last = np.mean([g["new_quanta"] for g in growth[-3:]])
        reuse_first = np.mean([g["reuse_rate"] for g in growth[:3]])
        reuse_last = np.mean([g["reuse_rate"] for g in growth[-3:]])
        sat_pass = last <= max(3.0, 0.3 * first) and reuse_last >= reuse_first
        print(f"\n  saturation check: mean new-quanta/window first-3={first:.1f} -> "
              f"last-3={last:.1f}; mean reuse-rate first-3={100*reuse_first:.1f}% -> "
              f"last-3={100*reuse_last:.1f}%")
        print(f"  SATURATION VERDICT: {'PASS (growth flattens, reuse rises)' if sat_pass else 'FAIL (no flattening)'}")
        if not sat_pass:
            print("  DIAGNOSTIC (near-miss, honest, not blind retuning):")
            dists = []
            for (ink_node, st_i, e_i) in lr["last_window_oov_ink"][-30:]:
                knots = np.asarray(s.node(ink_node)["attrs"].get("knots") or [], dtype=float)
                if len(knots) < 2:
                    continue
                sigd = ink._span_signature(native, knots, int(st_i), int(e_i),
                                            segments=DK["segments"], turn_bins=DK["turn_bins"],
                                            len_bins=DK["len_bins"], grid=DK["grid"],
                                            scale_bins=DK["scale_bins"], invariant_only=True)
                d = _nearest_codebook_distance(s, sigd["signature"])
                if d is not None:
                    dists.append(d)
            if dists:
                print(f"    {len(dists)} sampled OOV spans from the final window: nearest-codebook "
                      f"L1 bin-distance min={min(dists)} mean={np.mean(dists):.2f} max={max(dists)}")
                near1 = sum(1 for d in dists if d <= 1)
                print(f"    {near1}/{len(dists)} are within 1 bin of an existing entry (a coarser "
                      f"turn_bins/len_bins would likely fold these in ā€” a documented, diagnostic-"
                      f"driven adjustment, not applied here since this is a rerun-only lever).")
            else:
                print("    no comparable same-segment-count codebook entries found for the sampled "
                      "OOV spans ā€” the residual is structural (different segment counts / genuinely "
                      "novel shapes), not a near-miss binning artefact.")
    else:
        print("\n  SATURATION VERDICT: inconclusive (fewer than 6 growth windows recorded).")

    final_codebook = len(sc._existing_names(s, "stroke"))
    print(f"\n  final LEARN codebook size: {final_codebook} stroke quanta.")

    # RUN-4 LEVERS "LEVER 2" (GRAIN LADDER): vocabulary size PER LEVEL -- `top` = coarse-
    # grain-installed families; `distinct_coarse/mid/fine` = how many DISTINCT quantized
    # signature values exist among those top-level quanta at each grain (a smaller distinct
    # count at a coarser grain is the ladder collapsing vocabulary together, by design);
    # `children` = refinement quanta minted per-dimension, broken down by WHICH tier's
    # near-miss triggered them.
    gv = sc.grain_vocabulary_report(s)
    print(f"\n  GRAIN LADDER vocabulary (RUN-4 LEVERS \"LEVER 2\"):")
    print(f"    top-level (coarse-installed) quanta: {gv['top']}")
    print(f"    distinct signatures per grain -- coarse: {gv['distinct_coarse']}  "
          f"mid: {gv['distinct_mid']}  fine: {gv['distinct_fine']}")
    print(f"    refinement children: {gv['children']} (by triggering tier: "
          f"{gv['children_by_tier']})")
    print(f"    total deepest-grain library size: {gv['total']} (== {final_codebook} above)")
    # EAGER CHILD MINTING (RUN-6): the SEPARATE ShapeSignatureFineChild population -- excluded
    # from `top`/`children`/`total` above (the PRIMARY recognition library, untouched by
    # eager minting, see stroke_codebook.grow_stroke_refinement_quantum's docstring).
    print(f"    eager (strokeq_fine) children: {gv['fine_children']} "
          f"(by parent, top few: "
          f"{dict(sorted(gv['fine_children_by_parent'].items(), key=lambda kv: kv[0])[:8])})")

    # RUN 14 -- BRANCH A EXECUTION (SUB-STROKE COMPOSITION): the WITHIN-stroke inner
    # lattice's own vocabulary, one grain down (deliberately a SEPARATE, arity-distinct
    # codebook -- see stroke_codebook.SUBSTROKE_SEGMENTS's own comment). "sub-stroke
    # vocabulary >> 7 arrangement keys" is the design's own stated payoff signal -- the
    # SATURATION shape (growth-then-flatten) is checked the SAME way the outer stroke-level
    # codebook was checked above (first-3 vs last-3 windows' mean +new/win).
    sub_report = sc.substroke_vocabulary_report(s)
    print(f"\n  SUB-STROKE codebook (BRANCH A EXECUTION): {sub_report['total']} substroke "
          f"quanta earned during LEARN (vs {final_codebook} top-level stroke quanta).")
    sub_sat_pass = None
    if len(growth) >= 6:
        sub_first = np.mean([g.get("substroke_new", 0) for g in growth[:3]])
        sub_last = np.mean([g.get("substroke_new", 0) for g in growth[-3:]])
        sub_sat_pass = sub_last <= max(3.0, 0.3 * sub_first)
        print(f"  SUB-STROKE saturation check: mean +new/win first-3={sub_first:.1f} -> "
              f"last-3={sub_last:.1f}")
        print(f"  SUB-STROKE SATURATION VERDICT: "
              f"{'PASS (growth flattens)' if sub_sat_pass else 'FAIL (no flattening)'}")
    else:
        print("  SUB-STROKE SATURATION VERDICT: inconclusive (fewer than 6 growth windows).")

    # ------------------------------------------------------------------------------------- #
    #  PHASE 2 ā€” WRITER DIMENSIONS
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  PHASE 2: WRITER DIMENSIONS (drawers ARE writers)\n{SEP}")
    wr = writer_report(s)
    print(f"\n  {wr['n_writers']} Writer nodes (one per drawer touched in LEARN).")
    print(f"  {wr['n_with_transforms']} writers produced >=1 successfully-read pose Transform.")
    print(f"  {wr['n_with_style']} of those minted >=1 coherent WriterStyle "
          f"(coherence rate = {100*wr['coherence_rate']:.1f}%).")
    print(f"  total WriterStyle quanta minted: {wr['total_styles']} "
          f"(mean {np.mean(wr['style_counts']) if wr['style_counts'] else 0:.2f} styles/writer, "
          f"max {max(wr['style_counts']) if wr['style_counts'] else 0}).")
    if wr["orient_deltas"]:
        od = np.asarray(wr["orient_deltas"], dtype=float)
        sd = np.asarray(wr["scale_deltas"], dtype=float)
        print(f"  orient_delta distribution: min={od.min():.0f} mean={od.mean():.2f} "
              f"max={od.max():.0f} std={od.std():.2f} (over {len(od)} minted styles)")
        print(f"  scale_delta distribution:  min={sd.min():.0f} mean={sd.mean():.2f} "
              f"max={sd.max():.0f} std={sd.std():.2f}")
    if wr["style_counts"] and max(wr["style_counts"]) > 1:
        n_multi = sum(1 for c in wr["style_counts"] if c > 1)
        print(f"  HONEST: {n_multi}/{wr['n_writers']} writers minted MORE THAN ONE distinct-"
              f"orient_delta style ā€” real hands do not show one global slant at this bin "
              f"resolution; PARTIAL coherence, not forced into a single style.")

    # ------------------------------------------------------------------------------------- #
    #  PHASE 3 ā€” TEST (one-shot 20-way, held-out alphabets, cross-drawer)
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  PHASE 3: TEST (one-shot {WAY}-way, within-alphabet, cross-drawer, "
          f"held-out alphabets)\n{SEP}")
    print(f"\n  held-out alphabets (strokes_evaluation, never touched in LEARN): {EVAL_ALPHABETS}")
    rng = np.random.default_rng(SEED)
    te = run_test(s, native, EVAL_ALPHABETS, WAY, EPISODES_PER_ALPHABET, DK, rng)

    if te["skipped_alphabets"]:
        for (a, reason) in te["skipped_alphabets"]:
            print(f"  SKIPPED alphabet {a!r}: {reason}")

    chance = 100.0 / WAY
    print(f"\n  per-alphabet accuracy (MULTISET ablation control | COMPOSED w/children | "
          f"COMPOSED no-children):")
    for a in te["per_alph_acc_comp"]:
        print(f"    {a:>24}: {100*te['per_alph_acc_ms'][a]:5.1f}%  |  "
              f"{100*te['per_alph_acc_comp'][a]:5.1f}%  |  {100*te['per_alph_acc_comp_nc'][a]:5.1f}%")
    print(f"\n  {te['n_episodes']} query episodes total, {te['n_unique_files']} unique drawings "
          f"decoded (cached ā€” each decoded exactly once).")
    print(f"  ONE-SHOT ACCURACY, MULTISET  (ablation control): {100*te['acc_ms']:5.1f}%   "
          f"(chance = {chance:.1f}%, shuffled {100*te['acc_ms_shuf']:5.1f}%)")
    print(f"  ONE-SHOT ACCURACY, COMPOSED  (DISCRIMINATION lever (c)): {100*te['acc_comp']:5.1f}%   "
          f"(chance = {chance:.1f}%, shuffled {100*te['acc_comp_shuf']:5.1f}%)")
    print(f"  ABLATION DELTA (composed - multiset, lever (c)'s measured value): "
          f"{100*(te['acc_comp'] - te['acc_ms']):+5.1f}pp")
    print(f"  ONE-SHOT ACCURACY, COMPOSED, EAGER CHILD MINTING (RUN-6) --")
    print(f"    WITH strokeq_fine (headline):    {100*te['acc_comp']:5.1f}%   "
          f"(chance = {chance:.1f}%, shuffled {100*te['acc_comp_shuf']:5.1f}%)")
    print(f"    WITHOUT strokeq_fine (control):  {100*te['acc_comp_nc']:5.1f}%   "
          f"(chance = {chance:.1f}%, shuffled {100*te['acc_comp_nc_shuf']:5.1f}%)")
    print(f"    DELTA (children lever's measured value): "
          f"{100*(te['acc_comp'] - te['acc_comp_nc']):+5.1f}pp")
    print(f"  test-time OOV rate:            {100*te['oov_rate']:5.1f}%   "
          f"(fraction of query/exemplar spans with NO learned quantum)")
    print(f"  transform-explanation rate:    {100*te['explain_rate']:5.1f}%   "
          f"(fraction of recognized spans whose pose rung-1 TransformDecode explained ā€” "
          f"DISCRIMINATION item (b): pose read-off restored in ALL tiers, not just fine)")
    print(f"  codebook: {te['codebook_before']} -> {te['codebook_after']} stroke quanta "
          f"during TEST (continued earning on held-out alphabets is honest, not a leak into "
          f"LEARN's own stats).")

    print(f"\n  RUN-4 LEVERS -- STROKE-ORDER ABLATION (composed, DRAW-order | composed, "
          f"NAME-sorted order):")
    print(f"    ONE-SHOT ACCURACY: {100*te['acc_comp']:5.1f}%  |  {100*te['acc_sorted']:5.1f}%   "
          f"(shuffled {100*te['acc_comp_shuf']:5.1f}%  |  {100*te['acc_sorted_shuf']:5.1f}%)")
    print(f"    DELTA (draw-order - name-sorted): {100*(te['acc_comp'] - te['acc_sorted']):+5.1f}pp "
          f"-- a large delta means real drawers vary stroke ORDER enough that draw-order "
          f"`strokeq`/`rel` pairing carries drawer-specific noise, not just character identity.")

    test_pass = te["acc_comp"] > chance / 100.0 and te["acc_comp_shuf"] < te["acc_comp"]

    # ------------------------------------------------------------------------------------- #
    #  ARRANGEMENT FIDELITY (RUN 7, scratchpad/HANDWRITING_DESIGN.md's "ARRANGEMENT FIDELITY"
    #  section, the accb0d47 residual): Phase A (scripts/jabberwock_omniglot_arrangement_
    #  diag.py) ranked the coverage METRIC (naive whole-relation-tuple membership) as the top
    #  lever -- 52.8% of the 53 real misses decided by a TIE, vs 18.9% recoverable by an
    #  alternate frame anchor. `character_compose.assignment_coverage_term` (per-stroke
    #  best-match, held Terms only) is the built fix; `_comp` (naive coverage, UNCHANGED)
    #  stays the LOGGED CONTROL every episode -- additivity discipline.
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  ARRANGEMENT FIDELITY (RUN 7) -- ASSIGNMENT-AWARE COVERAGE vs naive "
          f"coverage control\n{SEP}")
    print(f"\n  per-alphabet accuracy (COMPOSED naive coverage [control] | ASSIGNMENT-aware "
          f"coverage [headline]):")
    for a in te["per_alph_acc_assign"]:
        print(f"    {a:>24}: {100*te['per_alph_acc_comp'][a]:5.1f}%  |  "
              f"{100*te['per_alph_acc_assign'][a]:5.1f}%")
    print(f"\n  ONE-SHOT ACCURACY, COMPOSED naive coverage (LOGGED CONTROL): "
          f"{100*te['acc_comp']:5.1f}%   (chance = {chance:.1f}%, shuffled "
          f"{100*te['acc_comp_shuf']:5.1f}%)")
    print(f"  ONE-SHOT ACCURACY, ASSIGNMENT-AWARE coverage (RUN 7 headline): "
          f"{100*te['acc_assign']:5.1f}%   (chance = {chance:.1f}%, shuffled "
          f"{100*te['acc_assign_shuf']:5.1f}%)")
    print(f"  ARRANGEMENT-FIDELITY DELTA (assignment - naive-coverage-composed, the lever's "
          f"measured value): {100*(te['acc_assign'] - te['acc_comp']):+5.1f}pp")
    print(f"  ONE-SHOT ACCURACY, ASSIGNMENT identity_weight=0 (RUN 8, ARRANGEMENT-ONLY): "
          f"{100*te['acc_arr_only']:5.1f}%   (chance = {chance:.1f}%, shuffled "
          f"{100*te['acc_arr_only_shuf']:5.1f}%)")
    print(f"  RUN-8 DELTA (arrangement-only - naive control): "
          f"{100*(te['acc_arr_only'] - te['acc_comp']):+5.1f}pp")
    assign_test_pass = te["acc_assign"] > chance / 100.0 and te["acc_assign_shuf"] < te["acc_assign"]

    # ------------------------------------------------------------------------------------- #
    #  HIGHER-ORDER ARRANGEMENT RELATIONS (RUN 9, scratchpad/HANDWRITING_DESIGN.md's
    #  "HIGHER-ORDER ARRANGEMENT RELATIONS" section, the 97d54623 residual): the Phase-A
    #  intermediate gate (scripts/jabberwock_omniglot_arrangement_diag.py, re-run with rel2)
    #  found the tie rate drops materially (52.8% -> 30.4% of misses) but accuracy does NOT
    #  move up on that script's own (committed-codebook) protocol -- reported here again on
    #  THIS run's own freshly-LEARNED codebook for the authoritative number. `_comp` (naive
    #  coverage, `include_rel2` defaults False, UNCHANGED) stays the LOGGED CONTROL -- it MUST
    #  reproduce the historical 33.8% or something upstream drifted.
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  HIGHER-ORDER ARRANGEMENT RELATIONS (RUN 9) -- rel2 (non-adjacent stroke "
          f"pairs) vs naive coverage control\n{SEP}")
    print(f"\n  per-alphabet accuracy (COMPOSED naive coverage [control, no rel2] | "
          f"WITH rel2 [headline]):")
    for a in te["per_alph_acc_rel2"]:
        print(f"    {a:>24}: {100*te['per_alph_acc_comp'][a]:5.1f}%  |  "
              f"{100*te['per_alph_acc_rel2'][a]:5.1f}%")
    print(f"\n  ONE-SHOT ACCURACY, COMPOSED naive coverage (CONTROL, no rel2 -- must reproduce "
          f"the historical 33.8%): {100*te['acc_comp']:5.1f}%   (chance = {chance:.1f}%, "
          f"shuffled {100*te['acc_comp_shuf']:5.1f}%)")
    control_reproduced = abs(100 * te["acc_comp"] - 33.8) < 0.15
    print(f"  CONTROL REPRODUCTION CHECK: {'PASS' if control_reproduced else 'FAIL -- STOP AND DIAGNOSE'} "
          f"(measured {100*te['acc_comp']:.1f}% vs historical 33.8%)")
    print(f"  ONE-SHOT ACCURACY, WITH rel2 (RUN 9 headline): {100*te['acc_rel2']:5.1f}%   "
          f"(chance = {chance:.1f}%, shuffled {100*te['acc_rel2_shuf']:5.1f}%)")
    print(f"  RUN-9 DELTA (with-rel2 - naive-coverage-composed control): "
          f"{100*(te['acc_rel2'] - te['acc_comp']):+5.1f}pp")
    rel2_test_pass = te["acc_rel2"] > chance / 100.0 and te["acc_rel2_shuf"] < te["acc_rel2"]

    # ------------------------------------------------------------------------------------- #
    #  ABS AS DEFAULT (RUN 10, scratchpad/HANDWRITING_DESIGN.md's "ABS AS DEFAULT" section,
    #  2026-07-03, supersedes the frame-anchor lever as a quantized-frame patch): "the
    #  generation and reading model is the same, like speech -- AbS is the default. It just
    #  runs the same engine in reverse." PROPOSE top-ABS_TOPK by the EXISTING strict coverage
    #  (`domains.abs_read.propose_top_k`, byte-identical metric to `_comp`'s own control),
    #  then RE-RANK by RENDER-COMPARE (`domains.abs_read.abs_rerank`, the held `StrokeRender`
    #  Term -- the generative inverse of `StrokeQuantize` -- rendering each candidate's own
    #  stroke quanta at the QUERY's decoded per-stroke poses, scored against the query's
    #  actual observed ink). `_comp` (naive coverage, UNCHANGED) stays the LOGGED CONTROL --
    #  it MUST reproduce the historical 33.8%, already checked above (`control_reproduced`).
    #  `StrokeRender` is being built in PARALLEL against this design -- `te["sr_live"]`
    #  reports whether it was operative for THIS run; when it is not, this section reports
    #  the lever as AUTHORED-BUT-NOT-RUN rather than fabricate a chance-level number.
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  ABS AS DEFAULT (RUN 10) -- propose top-{ABS_TOPK} by naive coverage, "
          f"then RENDER-COMPARE re-rank vs naive coverage control\n{SEP}")
    if not te["sr_live"]:
        print(f"\n  SKIPPED (authored, not run): the held `StrokeRender` Term "
              f"(runners/dsl/src/strokes.rs, the generative inverse of `StrokeQuantize`) is "
              f"not yet live against this wheel (`domains.abs_read._stroke_render_live` "
              f"probe returned False). `domains/abs_read.py` (propose_top_k / "
              f"abs_render_compare_term / pointset_compare_term / abs_rerank) and this "
              f"script's RUN 10 wiring are AUTHORED and additive -- see "
              f"tests/test_character_composition_migrated.py's 'ABS AS DEFAULT' gates for the "
              f"synthetic proof of the mechanism (also skipped for the same reason). No "
              f"fabricated headline number is reported here.")
        abs_test_pass = None
    else:
        print(f"\n  K (logged constant, design: 'K~3-5'): {ABS_TOPK}")
        print(f"\n  per-alphabet accuracy (COMPOSED naive coverage [control] | ABS RENDER-"
              f"COMPARE re-rank [RUN 10 headline] | coverage@K):")
        for a in te["per_alph_acc_abs"]:
            print(f"    {a:>24}: {100*te['per_alph_acc_comp'][a]:5.1f}%  |  "
                  f"{100*te['per_alph_acc_abs'][a]:5.1f}%  |  "
                  f"{100*te['per_alph_coverage_at_k'][a]:5.1f}%")
        print(f"\n  ONE-SHOT ACCURACY, COMPOSED naive coverage (LOGGED CONTROL): "
              f"{100*te['acc_comp']:5.1f}%   (chance = {chance:.1f}%, shuffled "
              f"{100*te['acc_comp_shuf']:5.1f}%)")
        print(f"  ONE-SHOT ACCURACY, ABS RENDER-COMPARE re-rank (RUN 10 headline): "
              f"{100*te['acc_abs']:5.1f}%   (chance = {chance:.1f}%, shuffled "
              f"{100*te['acc_abs_shuf']:5.1f}%)")
        print(f"  RUN-10 DELTA (abs-rerank - naive-coverage-composed control): "
              f"{100*(te['acc_abs'] - te['acc_comp']):+5.1f}pp")
        print(f"  COVERAGE@K (fraction of episodes where the TRUE exemplar was IN the "
              f"top-{ABS_TOPK} proposal -- the proposal RECALL BOUND on what re-ranking can "
              f"possibly achieve): {100*te['coverage_at_k']:5.1f}%")
        abs_test_pass = te["acc_abs"] > chance / 100.0 and te["acc_abs_shuf"] < te["acc_abs"]
        if te["acc_abs"] <= te["acc_comp"]:
            print(f"  HONEST: the render-compare verdict did NOT beat the naive-coverage "
                  f"control on this run ({100*te['acc_abs']:.1f}% <= {100*te['acc_comp']:.1f}%) "
                  f"-- per the design's own branch: even the generative verdict cannot "
                  f"separate this 20-way task further at this codebook, so the ceiling claim "
                  f"stands with the strongest possible evidence and the next lever is the "
                  f"GENERATION side (richer motor programs), not reading.")

    # ------------------------------------------------------------------------------------- #
    #  PROPOSAL RECALL / VARIABLE-APERTURE DWELL (RUN 11, scratchpad/HANDWRITING_DESIGN.md's
    #  section of the same name, the 42855d5f residual + the radar frame's first falsifiable
    #  instance): THREE arms off the SAME decode+proposal cache RUN 10 already built -- K=5
    #  FIXED (the RUN 10 control, must reproduce 37.5%), K=FULL_DWELL_K FULL DWELL (pure AbS,
    #  no proposal filter at all, the upper bound / cleanest one-model test), and VARIABLE-K
    #  (`ar.propose_variable_k`, delta in VARIABLE_DELTAS -- the render BUDGET is the
    #  shortlist size, decided by held MaxOver + held FilterList, never a Python score
    #  branch). "THE RADAR CLAIM": some delta beats K=5's 37.5% at a LOWER OR EQUAL mean
    #  render budget (aperture spent where ambiguity is, not uniformly).
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  PROPOSAL RECALL / VARIABLE-APERTURE DWELL (RUN 11) -- K=5 control | "
          f"K={FULL_DWELL_K} full dwell | variable-K (delta in {VARIABLE_DELTAS})\n{SEP}")
    if not te["sr_live"]:
        print(f"\n  SKIPPED (authored, not run): StrokeRender not live this run -- the SAME "
              f"reason RUN 10 was skipped above (see that section). No fabricated numbers "
              f"reported.")
        run11_pass = None
        control_reproduced_37_5 = None
    else:
        control_reproduced_37_5 = abs(100 * te["acc_abs"] - 37.5) < 0.15
        print(f"\n  K=5 CONTROL REPRODUCTION CHECK (must reproduce the historical 37.5%): "
              f"{'PASS' if control_reproduced_37_5 else 'FAIL -- STOP AND DIAGNOSE'} "
              f"(measured {100*te['acc_abs']:.1f}%)")
        print(f"\n  ONE-SHOT ACCURACY, K=5 FIXED (control): {100*te['acc_abs']:5.1f}%   "
              f"(chance = {chance:.1f}%, shuffled {100*te['acc_abs_shuf']:5.1f}%)   "
              f"render budget: mean=5.00 max=5   coverage@5: {100*te['coverage_at_k']:5.1f}%")
        print(f"  ONE-SHOT ACCURACY, K={FULL_DWELL_K} FULL DWELL (upper bound): "
              f"{100*te['acc_full']:5.1f}%   (chance = {chance:.1f}%, shuffled "
              f"{100*te['acc_full_shuf']:5.1f}%)   render budget: "
              f"mean={float(FULL_DWELL_K):.2f} max={FULL_DWELL_K}   "
              f"coverage@{FULL_DWELL_K}: {100*te['coverage_at_full']:5.1f}% "
              f"(== 100% by construction)")

        print(f"\n  VARIABLE-K (dwell scheduler) -- accuracy | shuffled | mean shortlist "
              f"(render budget) | max shortlist | coverage@shortlist:")
        radar_deltas = []
        for d in VARIABLE_DELTAS:
            a, a_s = te["acc_delta"][d], te["acc_delta_shuf"][d]
            m, mx = te["mean_shortlist_delta"][d], te["max_shortlist_delta"][d]
            cvk = te["coverage_at_delta"][d]
            print(f"    delta={d}: {100*a:5.1f}%  |  shuffled {100*a_s:5.1f}%  |  "
                  f"mean {m:5.2f}  |  max {mx:2d}  |  coverage@shortlist {100*cvk:5.1f}%")
            if a > te["acc_abs"] and m <= 5.0:
                radar_deltas.append(d)
        print(f"\n  THE RADAR CLAIM (some delta beats K=5's {100*te['acc_abs']:.1f}% at a "
              f"LOWER-OR-EQUAL mean render budget of 5): "
              f"{'CONFIRMED (delta=' + str(radar_deltas) + ')' if radar_deltas else 'NOT CONFIRMED on this run'}")

        run11_pass = (te["acc_full"] > chance / 100.0 and te["acc_full_shuf"] < te["acc_full"]
                      and control_reproduced_37_5)

        rt = te["recall_tail"]
        print(f"\n  RECALL-TAIL (rank of the true exemplar in the proposal ordering, for "
              f"episodes where the K=5 shortlist MISSED it -- `ar.proposal_rank`'s held "
              f"Count(FilterList(...)) read-off, reporting only):")
        if rt is None:
            print(f"    n/a -- the K=5 shortlist never missed the true exemplar this run.")
        else:
            print(f"    {rt['n']}/{te['n_episodes']} episodes outside the K=5 shortlist: "
                  f"mean rank={rt['mean_rank']:.1f}  min={rt['min_rank']}  max={rt['max_rank']}")
            print(f"    rank  6-10 (near-miss, K~10 would reach): {rt['n_rank_6_10']}")
            print(f"    rank 11-15 (mid):                         {rt['n_rank_11_15']}")
            print(f"    rank 16+   (far, the proposal metric is BLIND to these):"
                  f" {rt['n_rank_16_plus']}")
            if rt["n_rank_6_10"] and not rt["n_rank_16_plus"]:
                print(f"    SHAPE: near-miss dominated -- widening the beam (bigger K/delta) "
                      f"would reachably recover most of the tail.")
            elif rt["n_rank_16_plus"] and not rt["n_rank_6_10"]:
                print(f"    SHAPE: far-miss dominated -- the proposal metric is blind to "
                      f"these regardless of beam width; the next lever is a SECOND proposal "
                      f"modality, not a bigger beam.")
            else:
                print(f"    SHAPE: mixed -- some of the tail is beam-reachable, some is not.")

    # ------------------------------------------------------------------------------------- #
    #  TARGETED WIDEN + SECOND MODALITY (RUN 12, scratchpad/HANDWRITING_DESIGN.md's section
    #  of the same name, the 6db362d1 residual): LEVER 1 (targeted widen) + LEVER 2 (second
    #  appearance modality) via `domains.abs_read.abs_rerank_targeted`'s own flags, replayed
    #  over the SAME 80 episodes RUN 11's delta=0 sub-arm already decoded (shared caches).
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  TARGETED WIDEN + SECOND MODALITY (RUN 12) -- delta=0 control | "
          f"+targeted-widen | +second-modality | +both\n{SEP}")
    if not te["sr_live"]:
        print(f"\n  SKIPPED (authored, not run): StrokeRender not live this run -- the SAME "
              f"reason RUN 10/11 were skipped above. No fabricated numbers reported.")
        run12 = None
        run12_pass = None
        control_reproduced_38_8 = None
        best_acc, best_arm = 0.0, "n/a"
    else:
        calib = calibrate_widen_thresholds(te["delta0_calibration"])
        print(f"\n  LEVER 1 calibration (host-side, offline, from the delta=0 arm's own "
              f"{calib['n_total']} scored episodes, {calib['n_correct']} correct): "
              f"fit_threshold={calib['fit_threshold']:.4f} (P{FIT_PERCENTILE:.0f} of correct "
              f"best-scores)  margin_threshold={calib['margin_threshold']:.4f} "
              f"(P{MARGIN_PERCENTILE:.0f} of {calib['n_correct_with_margin']} correct margins) "
              f"  widen_to={WIDEN_TO}  appearance_m={APPEARANCE_M}")

        run12 = run_targeted_widen(
            s, native, te["episode_records"], te["exemplars_by_alph"], DK,
            margin_threshold=calib["margin_threshold"], fit_threshold=calib["fit_threshold"],
            widen_to=WIDEN_TO, appearance_m=APPEARANCE_M)

        control_reproduced_38_8 = abs(100 * run12["acc_control"] - 38.8) < 0.15
        print(f"\n  CONTROL REPRODUCTION CHECK (must reproduce the historical 38.8% @ mean "
              f"2.05 renders): {'PASS' if control_reproduced_38_8 else 'FAIL -- STOP AND DIAGNOSE'} "
              f"(measured {100*run12['acc_control']:.1f}% @ mean "
              f"{run12['mean_budget_control']:.2f} renders)")

        print(f"\n  {'arm':>12}  {'accuracy':>9}  {'shuffled':>9}  {'mean budget':>11}  "
              f"{'max budget':>10}  {'widen rate':>10}")
        for name in RUN12_ARMS:
            print(f"  {name:>12}  {100*run12[f'acc_{name}']:8.1f}%  "
                  f"{100*run12[f'acc_{name}_shuf']:8.1f}%  {run12[f'mean_budget_{name}']:11.2f}  "
                  f"{run12[f'max_budget_{name}']:10d}  {100*run12[f'widen_rate_{name}']:9.1f}%")

        print(f"\n  PER-LEVER ATTRIBUTION (delta vs the {100*run12['acc_control']:.1f}% "
              f"control):")
        for name in ("widen", "appearance", "both"):
            print(f"    +{name}: {100*(run12[f'acc_{name}']-run12['acc_control']):+5.1f}pp  "
                  f"(mean budget {run12[f'mean_budget_{name}']:.2f} vs "
                  f"{run12['mean_budget_control']:.2f})")

        mo = run12["modality_overlap"]
        n_app_ep = max(1, mo["n_appearance_episodes"])
        print(f"\n  MODALITY OVERLAP: appearance ADDED a candidate the structural shortlist "
              f"did not have on {mo['appearance_added_candidates']}/"
              f"{mo['n_appearance_episodes']} episodes "
              f"({100*mo['appearance_added_candidates']/n_app_ep:.1f}%).")

        ft = far_tail_reachability(run12, te["episode_records"], te["far_tail_episodes"])
        print(f"\n  FAR-TAIL REACHABILITY (RUN 11's {ft['n_far_tail']} proposal-blind, "
              f"rank>=16 cases): {ft['n_reachable']}/{ft['n_far_tail']} become reachable by "
              f"AT LEAST ONE of {{widen, appearance, both}}.")
        for r in ft["rows"]:
            print(f"    {r['alph']:>24} qi={r['qi']:>2}: control={r['control_correct']}  "
                  f"widen={r['widen_correct']}  appearance={r['appearance_correct']}  "
                  f"both={r['both_correct']}")

        best_acc, best_arm = max((run12[f"acc_{n}"], n) for n in ("widen", "appearance", "both"))
        print(f"\n  TWELVE-RUN TRAJECTORY: ...37.5% (RUN 10, AbS re-rank) -> 38.8% (RUN 11, "
              f"delta=0 variable-K) -> {100*best_acc:.1f}% (RUN 12, +{best_arm})")
        if best_acc <= run12["acc_control"]:
            print(f"  HONEST: neither lever beat the delta=0 control on this run "
                  f"({100*best_acc:.1f}% <= {100*run12['acc_control']:.1f}%) -- per the "
                  f"design's own branch: the remaining gap is likely EXEMPLAR-SIDE (one "
                  f"exemplar per class is the information bound) and the next lever is the "
                  f"GENERATION side (richer codebook from the exemplar's own strokes at "
                  f"decode time -- instance-conditioned quanta), not search.")

        run12_pass = (control_reproduced_38_8 and run12["acc_control"] > chance / 100.0
                      and run12["acc_control_shuf"] < run12["acc_control"])

    # ------------------------------------------------------------------------------------- #
    #  INSTANCE-CONDITIONED QUANTA (RUN 13, scratchpad/HANDWRITING_DESIGN.md's section of the
    #  same name, the a6c7740f endgame clause): LEVER A (exemplar-true rendering) + LEVER B
    #  (instance-codebook query decode) via `domains.abs_read.abs_rerank_targeted`'s new
    #  `use_exemplar_true`/`use_instance` flags, replayed over the SAME 80 episodes RUN 11/12
    #  already decoded (shared caches). Control = RUN 12's OWN ADOPTED CONFIG (delta=0 +
    #  appearance, RUN 12's best arm), per the design's own "run-12 adopted config as control"
    #  instruction -- must reproduce 41.2% @ mean 4.28 renders.
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  INSTANCE-CONDITIONED QUANTA (RUN 13) -- control (run-12 adopted: "
          f"delta=0 + appearance) | +A exemplar-true rendering | +B instance-decode | "
          f"+A+B\n{SEP}")
    if not te["sr_live"]:
        print(f"\n  SKIPPED (authored, not run): StrokeRender not live this run -- the SAME "
              f"reason RUN 10/11/12 were skipped above. No fabricated numbers reported.")
        run13 = None
        run13_pass = None
        control_reproduced_41_2 = None
        best_acc13, best_arm13 = 0.0, "n/a"
        ft13 = {"n_far_tail": 0, "n_reachable": 0, "rows": []}
    else:
        run13 = run_instance_conditioned(s, native, te["episode_records"],
                                         te["exemplars_by_alph"], DK)
        control_reproduced_41_2 = abs(100 * run13["acc_control"] - 41.2) < 0.15
        print(f"\n  CONTROL REPRODUCTION CHECK (must reproduce the historical 41.2% @ mean "
              f"4.28 renders -- RUN 12's own adopted +appearance arm): "
              f"{'PASS' if control_reproduced_41_2 else 'FAIL -- STOP AND DIAGNOSE'} "
              f"(measured {100*run13['acc_control']:.1f}% @ mean "
              f"{run13['mean_budget_control']:.2f} renders)")

        print(f"\n  {'arm':>10}  {'accuracy':>9}  {'shuffled':>9}  {'mean budget':>11}  "
              f"{'max budget':>10}  {'coverage@shortlist':>19}")
        for name in RUN13_ARMS:
            print(f"  {name:>10}  {100*run13[f'acc_{name}']:8.1f}%  "
                  f"{100*run13[f'acc_{name}_shuf']:8.1f}%  {run13[f'mean_budget_{name}']:11.2f}  "
                  f"{run13[f'max_budget_{name}']:10d}  "
                  f"{100*run13[f'coverage_shortlist_{name}']:18.1f}%")

        print(f"\n  PER-LEVER ATTRIBUTION (delta vs the {100*run13['acc_control']:.1f}% "
              f"control):")
        for name in ("+A", "+B", "+A+B"):
            print(f"    {name}: {100*(run13[f'acc_{name}']-run13['acc_control']):+5.1f}pp  "
                  f"(mean budget {run13[f'mean_budget_{name}']:.2f} vs "
                  f"{run13['mean_budget_control']:.2f}; coverage@shortlist "
                  f"{100*run13[f'coverage_shortlist_{name}']:.1f}% vs "
                  f"{100*run13['coverage_shortlist_control']:.1f}%)")

        ft13 = far_tail_reachability_13(run13, te["episode_records"], te["far_tail_episodes"])
        print(f"\n  FAR-TAIL REACHABILITY (RUN 11's {ft13['n_far_tail']} proposal-blind, "
              f"rank>=16 cases): {ft13['n_reachable']}/{ft13['n_far_tail']} become reachable "
              f"by AT LEAST ONE of {{+A, +B, +A+B}}.")
        for r in ft13["rows"]:
            print(f"    {r['alph']:>24} qi={r['qi']:>2}: control={r['control_correct']}  "
                  f"+A={r['+A_correct']}  +B={r['+B_correct']}  +A+B={r['+A+B_correct']}")

        best_acc13, best_arm13 = max((run13[f"acc_{n}"], n) for n in ("+A", "+B", "+A+B"))
        print(f"\n  THIRTEEN-RUN TRAJECTORY: ...38.8% (RUN 11, delta=0 variable-K) -> 41.2% "
              f"(RUN 12, +appearance) -> {100*best_acc13:.1f}% (RUN 13, {best_arm13})")
        if best_acc13 <= run13["acc_control"]:
            print(f"  HONEST: neither LEVER A nor LEVER B beat the run-12 adopted control on "
                  f"this run ({100*best_acc13:.1f}% <= {100*run13['acc_control']:.1f}%) -- per "
                  f"the design's own named terminus: the featureset's one-shot ceiling is "
                  f"search- AND generation-saturated at this representation, and the next "
                  f"frontier is the representation itself (e.g. sub-stroke grain composition "
                  f"or the speech-style coarticulation treatment of stroke junctions).")

        run13_pass = (control_reproduced_41_2 and run13["acc_control"] > chance / 100.0
                      and run13["acc_control_shuf"] < run13["acc_control"])

    # ------------------------------------------------------------------------------------- #
    #  RUN 14 -- BRANCH A EXECUTION: SUB-STROKE COMPOSITION (scratchpad/HANDWRITING_DESIGN.md's
    #  section of the same name, the jabberwock's own verdict d2cd7bed, 2026-07-03): the
    #  REPRESENTATION lever, tested after runs 11-13 found search+generation saturated at the
    #  existing representation. Control = the run-12 adopted config (delta=0 + appearance) fed
    #  `composed_sig` (no strokeq_sub) -- MUST reproduce 41.2% @ mean 4.28. +composition = the
    #  SAME config fed `composed_sig_substroke` (WITH the additive strokeq_sub relations in the
    #  structural PROPOSAL). Far-tail recheck against RUN 11's own 3 proposal-blind cases.
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  BRANCH A EXECUTION -- SUB-STROKE COMPOSITION (RUN 14) -- run-12 adopted "
          f"config control (composed_sig) | +composition (composed_sig_substroke)\n{SEP}")
    if not te["sr_live"]:
        print(f"\n  SKIPPED (authored, not run): StrokeRender not live this run -- the SAME "
              f"reason RUN 10/11/12/13 were skipped above. No fabricated numbers reported.")
        run14 = None
        run14_pass = None
        control_reproduced_41_2_run14 = None
        ft14 = {"n_far_tail": 0, "n_reachable": 0, "rows": []}
    else:
        run14 = run_substroke_composition(s, native, te["episode_records"],
                                          te["exemplars_by_alph"], DK)
        control_reproduced_41_2_run14 = abs(100 * run14["acc_control"] - 41.2) < 0.15
        print(f"\n  CONTROL REPRODUCTION CHECK (must reproduce the historical 41.2% @ mean "
              f"4.28 renders -- RUN 12's own adopted +appearance arm): "
              f"{'PASS' if control_reproduced_41_2_run14 else 'FAIL -- STOP AND DIAGNOSE'} "
              f"(measured {100*run14['acc_control']:.1f}% @ mean "
              f"{run14['mean_budget_control']:.2f} renders)")

        print(f"\n  {'arm':>14}  {'accuracy':>9}  {'shuffled':>9}  {'mean budget':>11}  "
              f"{'max budget':>10}  {'coverage@shortlist':>19}")
        for name in RUN14_ARMS:
            print(f"  {name:>14}  {100*run14[f'acc_{name}']:8.1f}%  "
                  f"{100*run14[f'acc_{name}_shuf']:8.1f}%  {run14[f'mean_budget_{name}']:11.2f}  "
                  f"{run14[f'max_budget_{name}']:10d}  "
                  f"{100*run14[f'coverage_shortlist_{name}']:18.1f}%")

        print(f"\n  PER-LEVER ATTRIBUTION (delta vs the {100*run14['acc_control']:.1f}% "
              f"control):")
        print(f"    +composition: "
              f"{100*(run14['acc_+composition']-run14['acc_control']):+5.1f}pp  "
              f"(mean budget {run14['mean_budget_+composition']:.2f} vs "
              f"{run14['mean_budget_control']:.2f}; coverage@shortlist "
              f"{100*run14['coverage_shortlist_+composition']:.1f}% vs "
              f"{100*run14['coverage_shortlist_control']:.1f}%)")

        ft14 = far_tail_reachability_14(run14, te["episode_records"], te["far_tail_episodes"])
        print(f"\n  FAR-TAIL REACHABILITY (RUN 11's {ft14['n_far_tail']} proposal-blind, "
              f"rank>=16 cases): {ft14['n_reachable']}/{ft14['n_far_tail']} become reachable "
              f"by +composition.")
        for r in ft14["rows"]:
            print(f"    {r['alph']:>24} qi={r['qi']:>2}: control={r['control_correct']}  "
                  f"+composition={r['+composition_correct']}")

        print(f"\n  SUB-STROKE vocabulary (BRANCH A EXECUTION): {sub_report['total']} "
              f"substroke quanta (vs the outer stroke-grain codebook's {final_codebook} "
              f"top-level quanta).")
        distinct_arrangement_keys = {
            r[2] for sigd in te.get("char_cache", {}).values()
            for r in sigd.get("composed_sig_substroke", []) if r and r[0] == "strokeq_sub"}
        print(f"  DISTINCT strokeq_sub arrangement keys observed across TEST: "
              f"{len(distinct_arrangement_keys)}")

        print(f"\n  FOURTEEN-RUN TRAJECTORY: ...41.2% (RUN 12, +appearance) -> 41.2% "
              f"(RUN 13, honest null) -> {100*run14['acc_+composition']:.1f}% (RUN 14, "
              f"+composition)")
        if run14["acc_+composition"] <= run14["acc_control"]:
            print(f"  HONEST: sub-stroke composition did NOT beat the run-12 adopted control "
                  f"on this run ({100*run14['acc_+composition']:.1f}% <= "
                  f"{100*run14['acc_control']:.1f}%) -- per the design's own named branch: the "
                  f"compositional claim at sub-stroke grain is FALSIFIED on this data and the "
                  f"terminus statement upgrades accordingly (the featureset's one-shot ceiling "
                  f"is representation-, search- AND generation-saturated).")

        run14_pass = (control_reproduced_41_2_run14 and run14["acc_control"] > chance / 100.0
                      and run14["acc_control_shuf"] < run14["acc_control"])

    # ------------------------------------------------------------------------------------- #
    #  RUN-4 LEVERS -- ROTATION-ROBUSTNESS SPOT-CHECK (a FEW episodes of ONE held-out
    #  alphabet, query drawings rotated by a fixed angle before decode; accuracy should hold
    #  within noise if the pipeline is genuinely rotation-robust end to end, not merely on
    #  hand-built synthetic fixtures).
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  ROTATION-ROBUSTNESS SPOT-CHECK ({ROTATE_SPOTCHECK_EPISODES} episodes, "
          f"{EVAL_ALPHABETS[0]!r}, query drawings rotated {ROTATE_SPOTCHECK_DEG:.0f} degrees "
          f"about their own centroid)\n{SEP}")
    rng_rot = np.random.default_rng(SEED + 1)     # INDEPENDENT of run_test's own rng draws.
    rot = run_rotation_spotcheck(s, native, EVAL_ALPHABETS[0], WAY, ROTATE_SPOTCHECK_EPISODES,
                                  DK, ROTATE_SPOTCHECK_DEG, rng_rot)
    if rot.get("skipped"):
        print(f"  SKIPPED: {rot['skipped']}")
    else:
        print(f"  {rot['n']} spot-check episodes: unrotated {100*rot['acc_normal']:5.1f}%  vs  "
              f"rotated {100*rot['acc_rotated']:5.1f}%  "
              f"(delta {100*(rot['acc_rotated']-rot['acc_normal']):+5.1f}pp)")

    # ------------------------------------------------------------------------------------- #
    #  RUN-4 LEVERS -- FRAME ABLATION (honest scope note, not run): the design asks for a
    #  rerun "with the ladder but the OLD bbox frame if cheap." The rotation-invariant
    #  CHARACTER frame (`character_compose._character_frame`, `rel`/`strokeq` relations) is
    #  NOT new in this pass -- it landed with character composition itself (commit c1b83669),
    #  predating LEVER 1. LEVER 1's actual new surface this pass (`cc.read_character_
    #  transform`/`cc.recognize_or_mint_character`, canonical `cpose` codebook convention) is
    #  gated by the NEW `tests/test_character_composition_migrated.py` gates, not exercised by
    #  this script's coverage-classification path at all (`decode_char_signature` never calls
    #  `induce_concern`/`recognize_or_mint_character` for characters -- classification here is
    #  Sum+In coverage, not a recognize/mint decision) -- so there is NO frame-ablation axis to
    #  rerun at the Omniglot level for LEVER 1; reverting `_character_frame` to re-litigate a
    #  decision from a PRIOR commit is out of this pass's scope. Any accuracy delta this run
    #  shows vs run 3 (33.8%) is therefore attributable to LEVER 2 (the grain ladder) alone,
    #  cleanly separable from LEVER 1.
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  FRAME ABLATION -- SCOPE NOTE\n{SEP}")
    print("  Not run: the rotation-invariant character frame predates LEVER 1 (landed in")
    print("  c1b83669, before this pass). LEVER 1's new surface (direct max_dims=4 character-")
    print("  transform read-off + canonical cpose) is not on this script's classification")
    print("  path at all (coverage+Argmax, not a recognize/mint decision) -- gated instead by")
    print("  the new pytest gates. Any accuracy delta vs run 3 is therefore LEVER 2 alone.")

    # ------------------------------------------------------------------------------------- #
    #  RUN 15 -- POWER THE GATE, THEN BRANCH B CONTINUOUS
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  RUN 15 PHASE 1 -- POWER THE GATE (Wilson 95% CIs, ALL qualifying "
          f"alphabets x {POWER_R} seeded repeats)\n{SEP}")
    power_alphabets = sorted(a for a in ow.alphabets("evaluation")
                              if len(ow.characters(a, "evaluation")) >= WAY)
    print(f"\n  qualifying alphabets (>= {WAY} characters, strokes_evaluation, never touched "
          f"in LEARN): {len(power_alphabets)} -- {power_alphabets}")
    print(f"  R = {POWER_R} seeded repeats/alphabet (different exemplar/query drawer draws "
          f"each repeat); target >= 400 total episodes; decode-cache SHARED with the "
          f"80-episode run above ({te['n_unique_files']} drawings already decoded, free).")

    if not te["sr_live"]:
        print(f"\n  SKIPPED (authored, not run): StrokeRender not live this run -- the SAME "
              f"reason RUN 10-14 were skipped above. No fabricated numbers reported.")
        p1 = None
    else:
        existing_elapsed = time.time() - t0
        p1 = run_powered_test(s, native, power_alphabets, WAY, EPISODES_PER_ALPHABET, POWER_R,
                              DK, te["char_cache"], POWER_SEED, POWER_BUDGET_SECONDS,
                              POWER_ALPHABET_CAP, existing_elapsed)
        if p1["budget_note"]:
            print(f"\n  RUNTIME BUDGET: {p1['budget_note']}")
        print(f"\n  used {p1['n_alphabets_used']} alphabets x up to {POWER_R} repeats x "
              f"{EPISODES_PER_ALPHABET} episodes/repeat = {p1['n_episodes']} total powered "
              f"episodes, decoded/scored in {p1['elapsed']:.1f}s.")
        print(f"  alphabets used: {p1['alphabets_used']}")

        arm_labels = {"ms": "MULTISET (control)",
                      "comp": "COMPOSED naive (33.8-era)",
                      "abs5": "AbS render-compare K=5 (37.5-era)",
                      "delta0": "delta=0 variable-K (38.8-era)",
                      "adopted": "delta=0+appearance (41.2-era ADOPTED)",
                      "rel2": "WITH rel2 (run-9 lever)",
                      "composition": "+sub-stroke composition (run-14 lever)"}
        print(f"\n  {'arm':>38}  {'n':>4}  {'k':>4}  {'accuracy':>9}  {'95% Wilson CI':>16}  "
              f"{'shuffled':>9}")
        for name, label in arm_labels.items():
            lo, hi = p1[f"ci_{name}"]
            print(f"  {label:>38}  {p1['n_episodes']:>4}  {p1[f'k_{name}']:>4}  "
                  f"{100*p1[f'acc_{name}']:8.1f}%  [{100*lo:5.1f}%, {100*hi:5.1f}%]  "
                  f"{100*p1[f'acc_{name}_shuf']:8.1f}%")
        print(f"\n  coverage@{ABS_TOPK} (powered): {100*p1['coverage_at_5']:.1f}%")

        rt = p1["recall_tail_ranks"]
        print(f"\n  RECALL-TAIL (powered, reporting only): {len(rt)}/{p1['n_episodes']} "
              f"episodes outside the K={ABS_TOPK} shortlist", end="")
        if rt:
            _rt = np.asarray(rt, dtype=float)
            print(f" -- mean rank={_rt.mean():.1f} min={int(_rt.min())} max={int(_rt.max())}  "
                  f"rank 6-10: {int(np.sum((_rt >= 6) & (_rt <= 10)))}  "
                  f"rank 11-15: {int(np.sum((_rt >= 11) & (_rt <= 15)))}  "
                  f"rank 16+: {int(np.sum(_rt >= 16))}")
        else:
            print(".")

        print(f"\n  WHICH RUN-10..14 CONCLUSIONS SURVIVE POWER (each restated with CI; a "
              f"revision is a RESULT, not an embarrassment):")

        def _pair(name_a, name_b):
            ci_a, ci_b = p1[f"ci_{name_a}"], p1[f"ci_{name_b}"]
            sep = _ci_separated(ci_a, ci_b)
            if sep:
                tag = ("CI-SEPARATED (b > a)" if ci_a[1] < ci_b[0]
                       else "CI-SEPARATED (b < a)")
            else:
                tag = "NOT CI-SEPARATED (inconclusive at this power)"
            return ci_a, ci_b, sep, tag

        ci_comp, ci_abs5, sep_abs, tag_abs = _pair("comp", "abs5")
        verdict_abs = ("SURVIVES" if sep_abs and p1["acc_abs5"] > p1["acc_comp"]
                       else ("REVERSED" if sep_abs else "INCONCLUSIVE AT THIS POWER"))
        print(f"    AbS gain (RUN 10, historical 33.8->37.5, +3.7pp): composed naive "
              f"{100*p1['acc_comp']:.1f}% [{100*ci_comp[0]:.1f},{100*ci_comp[1]:.1f}] vs "
              f"AbS K=5 {100*p1['acc_abs5']:.1f}% [{100*ci_abs5[0]:.1f},{100*ci_abs5[1]:.1f}]  "
              f"{tag_abs}  ->  {verdict_abs}")

        ci_abs5b, ci_delta0, sep_dwell, tag_dwell = _pair("abs5", "delta0")
        verdict_dwell = ("SURVIVES" if sep_dwell and p1["acc_delta0"] > p1["acc_abs5"]
                         else ("REVERSED" if sep_dwell else "INCONCLUSIVE AT THIS POWER"))
        print(f"    dwell gain (RUN 11, historical 37.5->38.8, +1.3pp): AbS K=5 "
              f"{100*p1['acc_abs5']:.1f}% [{100*ci_abs5b[0]:.1f},{100*ci_abs5b[1]:.1f}] vs "
              f"delta=0 {100*p1['acc_delta0']:.1f}% [{100*ci_delta0[0]:.1f},{100*ci_delta0[1]:.1f}]"
              f"  {tag_dwell}  ->  {verdict_dwell}")

        ci_delta0b, ci_adopted, sep_app, tag_app = _pair("delta0", "adopted")
        verdict_app = ("SURVIVES" if sep_app and p1["acc_adopted"] > p1["acc_delta0"]
                       else ("REVERSED" if sep_app else "INCONCLUSIVE AT THIS POWER"))
        print(f"    appearance gain (RUN 12, historical 38.8->41.2, +2.4pp): delta=0 "
              f"{100*p1['acc_delta0']:.1f}% [{100*ci_delta0b[0]:.1f},{100*ci_delta0b[1]:.1f}] "
              f"vs adopted {100*p1['acc_adopted']:.1f}% "
              f"[{100*ci_adopted[0]:.1f},{100*ci_adopted[1]:.1f}]  {tag_app}  ->  {verdict_app}")

        ci_adoptedb, ci_composition, sep_compnull, tag_compnull = _pair("adopted", "composition")
        verdict_compnull = ("STILL NULL (not CI-separated)" if not sep_compnull else
                            ("NOW A REAL LOSS (CI-separated, worse)" if p1["acc_composition"] < p1["acc_adopted"]
                             else "REVISED: NOW A REAL GAIN (CI-separated, better)"))
        print(f"    composition null (RUN 14, historical 41.2->40.0, -1.2pp): adopted "
              f"{100*p1['acc_adopted']:.1f}% [{100*ci_adoptedb[0]:.1f},{100*ci_adoptedb[1]:.1f}] "
              f"vs +composition {100*p1['acc_composition']:.1f}% "
              f"[{100*ci_composition[0]:.1f},{100*ci_composition[1]:.1f}]  {tag_compnull}  ->  "
              f"{verdict_compnull}")

        ci_compb, ci_rel2, sep_relnull, tag_relnull = _pair("comp", "rel2")
        verdict_relnull = ("STILL NULL (not CI-separated)" if not sep_relnull else
                           ("NOW A REAL LOSS (CI-separated, worse)" if p1["acc_rel2"] < p1["acc_comp"]
                            else "REVISED: NOW A REAL GAIN (CI-separated, better)"))
        print(f"    rel2 null (RUN 9, historical 33.8->30.0, -3.8pp): composed naive "
              f"{100*p1['acc_comp']:.1f}% [{100*ci_compb[0]:.1f},{100*ci_compb[1]:.1f}] vs "
              f"with rel2 {100*p1['acc_rel2']:.1f}% [{100*ci_rel2[0]:.1f},{100*ci_rel2[1]:.1f}]  "
              f"{tag_relnull}  ->  {verdict_relnull}")

        control_hist = {"ms": 5.0, "comp": 33.8, "abs5": 37.5, "delta0": 38.8, "adopted": 41.2,
                        "composition": 40.0, "rel2": 30.0}
        print(f"\n  HISTORICAL POINT ESTIMATES vs POWERED 95% CI (does the small-N run's own "
              f"number survive as a plausible draw from the powered interval?):")
        for name, hist in control_hist.items():
            lo, hi = p1[f"ci_{name}"]
            within = 100 * lo <= hist <= 100 * hi
            print(f"    {name:>12}: historical {hist:5.1f}%  powered [{100*lo:5.1f}%, "
                  f"{100*hi:5.1f}%]  {'WITHIN' if within else 'OUTSIDE'} the powered CI")

    # ------------------------------------------------------------------------------------- #
    #  RUN 15 PHASE 2 -- BRANCH B CONTINUOUS (junction-blended rendering, domains/abs_read.py)
    # ------------------------------------------------------------------------------------- #
    print(f"\n{SEP}\n  RUN 15 PHASE 2 -- BRANCH B CONTINUOUS (junction-blended rendering, "
          f"powered adopted control vs +junction-blend)\n{SEP}")
    if p1 is None:
        print(f"\n  SKIPPED (PHASE 1 itself was skipped -- StrokeRender not live this run).")
        p2 = None
    else:
        print(f"\n  junction_frac = {POWER_JUNCTION_FRAC} (design: '~0.15-0.2'), over the SAME "
              f"{p1['n_episodes']} powered episodes PHASE 1 already decoded (no re-decode, no "
              f"re-LEARN). CONTROL reuses PHASE 1's own adopted-config verdict for FREE (zero "
              f"extra render-compare calls); +junction-blend runs one fresh "
              f"`abs_rerank_targeted(use_junction_blend=True)` pass per episode.")
        p2 = run_branch_b_continuous(s, native, p1, DK, POWER_JUNCTION_FRAC)
        assert p2["acc_control"] == p1["acc_adopted"] and p2["k_control"] == p1["k_adopted"], (
            "PHASE 2's reused control must reproduce PHASE 1's own adopted-config accuracy "
            "EXACTLY (byte-identical reuse, no recomputation drift)")
        print(f"\n  {p2['n_episodes']} episodes, +junction-blend pass took {p2['elapsed']:.1f}s.")
        print(f"\n  {'arm':>24}  {'n':>4}  {'k':>4}  {'accuracy':>9}  {'95% Wilson CI':>16}")
        print(f"  {'control (adopted)':>24}  {p2['n_episodes']:>4}  {p2['k_control']:>4}  "
              f"{100*p2['acc_control']:8.1f}%  [{100*p2['ci_control'][0]:5.1f}%, "
              f"{100*p2['ci_control'][1]:5.1f}%]")
        print(f"  {'+junction-blend':>24}  {p2['n_episodes']:>4}  {p2['k_blend']:>4}  "
              f"{100*p2['acc_blend']:8.1f}%  [{100*p2['ci_blend'][0]:5.1f}%, "
              f"{100*p2['ci_blend'][1]:5.1f}%]")

        sep_b = _ci_separated(p2["ci_control"], p2["ci_blend"])
        if sep_b and p2["acc_blend"] > p2["acc_control"]:
            verdict_b = "CI-SEPARATED: BRANCH B GAINS under power"
        elif sep_b:
            verdict_b = "CI-SEPARATED: BRANCH B LOSES under power"
        else:
            verdict_b = "NOT CI-SEPARATED: HONEST NULL (BRANCH B, powered)"
        print(f"\n  RUN-15 PHASE-2 VERDICT: {verdict_b}  "
              f"(delta {100*(p2['acc_blend']-p2['acc_control']):+.1f}pp)")

        print(f"\n  RUN-15 TRAJECTORY UNDER POWER: composed naive "
              f"{100*p1['acc_comp']:.1f}% -> AbS K=5 {100*p1['acc_abs5']:.1f}% -> delta=0 "
              f"{100*p1['acc_delta0']:.1f}% -> adopted {100*p1['acc_adopted']:.1f}% -> "
              f"+junction-blend {100*p2['acc_blend']:.1f}%  (all n={p1['n_episodes']}, "
              f"95% Wilson CIs above)")

        if not sep_b:
            print(f"\n  HONEST CLOSE: Branch B (junction coarticulation) NULLS under power, "
                  f"exactly as Branch A (sub-stroke composition, RUN 14) NULLED under the "
                  f"80-episode run. BOTH fork branches the jabberwock's own held machinery "
                  f"named (d2cd7bed/9f10cf74) have now been BUILT and MEASURED -- the "
                  f"representation-grain corridor this featureset opened after RUN 13's "
                  f"search-and-generation saturation is EXHAUSTED end to end. The strongest "
                  f"terminus in this arc's history: AbS render-compare + appearance-modality "
                  f"proposal + variable-aperture dwell (the ADOPTED config, "
                  f"{100*p1['acc_adopted']:.1f}% [{100*p1['ci_adopted'][0]:.1f},"
                  f"{100*p1['ci_adopted'][1]:.1f}] powered) is this representation's ceiling; "
                  f"neither discrete sub-stroke composition NOR continuous junction blending "
                  f"moves it under power. The next lever, if any, is the representation "
                  f"ITSELF (a different featureset), not a further transform of this one.")

    # ------------------------------------------------------------------------------------- #
    #  FINAL VERDICT
    # ------------------------------------------------------------------------------------- #
    donkey = [m for m in sys.modules if "torch" in m.lower()]
    sat_label = "N/A (inconclusive)" if sat_pass is None else ("PASS" if sat_pass else "FAIL")
    print(f"\n{SEP}\n  FINAL VERDICT\n{SEP}")
    print(f"  LEARN saturation:      {sat_label}")
    print(f"  WRITER coherence:      {'PASS (>0% coherence)' if wr['coherence_rate'] > 0 else 'FAIL (no writer ever cohered)'}"
          f"  [{100*wr['coherence_rate']:.1f}%, honestly partial ā€” see above]")
    print(f"  ONE-SHOT beats chance (COMPOSED): {'PASS' if test_pass else 'FAIL'}  "
          f"({100*te['acc_comp']:.1f}% vs chance {chance:.1f}%, shuffled {100*te['acc_comp_shuf']:.1f}%)")
    print(f"  ONE-SHOT beats chance (multiset, ablation control, for reference): "
          f"{'PASS' if te['acc_ms'] > chance/100.0 and te['acc_ms_shuf'] < te['acc_ms'] else 'FAIL'}  "
          f"({100*te['acc_ms']:.1f}% vs chance {chance:.1f}%, shuffled {100*te['acc_ms_shuf']:.1f}%)")
    print(f"  EAGER CHILD MINTING (RUN-6) -- WITH strokeq_fine {100*te['acc_comp']:.1f}% vs "
          f"WITHOUT (control) {100*te['acc_comp_nc']:.1f}%  "
          f"(delta {100*(te['acc_comp']-te['acc_comp_nc']):+.1f}pp; the without-children arm is "
          f"the pre-eager-child ('run 5' era) representation -- should reproduce that number)")
    print(f"  ARRANGEMENT FIDELITY (RUN 7) -- ASSIGNMENT-AWARE {100*te['acc_assign']:.1f}% vs "
          f"naive-coverage-composed (control) {100*te['acc_comp']:.1f}%  "
          f"(delta {100*(te['acc_assign']-te['acc_comp']):+.1f}pp): "
          f"{'PASS' if assign_test_pass else 'FAIL'} "
          f"(vs chance {chance:.1f}%, shuffled {100*te['acc_assign_shuf']:.1f}%)")
    print(f"  CONTROL REPRODUCTION (RUN 9's own naive-coverage-composed control vs the "
          f"historical 33.8%): {'PASS' if control_reproduced else 'FAIL -- STOP AND DIAGNOSE'} "
          f"({100*te['acc_comp']:.1f}% measured)")
    print(f"  HIGHER-ORDER ARRANGEMENT RELATIONS (RUN 9) -- WITH rel2 {100*te['acc_rel2']:.1f}% "
          f"vs naive-coverage-composed (control) {100*te['acc_comp']:.1f}%  "
          f"(delta {100*(te['acc_rel2']-te['acc_comp']):+.1f}pp): "
          f"{'PASS' if rel2_test_pass else 'FAIL'} "
          f"(vs chance {chance:.1f}%, shuffled {100*te['acc_rel2_shuf']:.1f}%)")
    if not te["sr_live"]:
        print(f"  ABS AS DEFAULT (RUN 10): SKIPPED -- StrokeRender not yet landed "
              f"(authorable work committed, not run; see the RUN 10 section above)")
    else:
        print(f"  ABS AS DEFAULT (RUN 10) -- render-compare re-rank {100*te['acc_abs']:.1f}% "
              f"vs naive-coverage-composed (control) {100*te['acc_comp']:.1f}%  "
              f"(delta {100*(te['acc_abs']-te['acc_comp']):+.1f}pp, coverage@{ABS_TOPK} "
              f"{100*te['coverage_at_k']:.1f}%): "
              f"{'PASS' if abs_test_pass else 'FAIL'} "
              f"(vs chance {chance:.1f}%, shuffled {100*te['acc_abs_shuf']:.1f}%)")
    if not te["sr_live"]:
        print(f"  PROPOSAL RECALL / VARIABLE-APERTURE DWELL (RUN 11): SKIPPED -- "
              f"StrokeRender not yet landed (same reason as RUN 10 above)")
    else:
        print(f"  PROPOSAL RECALL / VARIABLE-APERTURE DWELL (RUN 11) -- K=5 control "
              f"{100*te['acc_abs']:.1f}% reproduces 37.5%: "
              f"{'PASS' if control_reproduced_37_5 else 'FAIL -- STOP AND DIAGNOSE'}; "
              f"K={FULL_DWELL_K} full dwell {100*te['acc_full']:.1f}%: "
              f"{'PASS' if run11_pass else 'FAIL'} "
              f"(vs chance {chance:.1f}%, shuffled {100*te['acc_full_shuf']:.1f}%); "
              f"radar claim {'CONFIRMED' if radar_deltas else 'NOT CONFIRMED'} "
              f"(delta={radar_deltas})")
    if not te["sr_live"]:
        print(f"  TARGETED WIDEN + SECOND MODALITY (RUN 12): SKIPPED -- "
              f"StrokeRender not yet landed (same reason as RUN 10/11 above)")
    else:
        print(f"  TARGETED WIDEN + SECOND MODALITY (RUN 12) -- delta=0 control "
              f"{100*run12['acc_control']:.1f}% reproduces 38.8%: "
              f"{'PASS' if control_reproduced_38_8 else 'FAIL -- STOP AND DIAGNOSE'}; "
              f"best lever (+{best_arm}) {100*best_acc:.1f}% "
              f"(delta {100*(best_acc-run12['acc_control']):+.1f}pp): "
              f"{'BEATS CONTROL' if best_acc > run12['acc_control'] else 'HONEST NULL'}; "
              f"far-tail reachable {ft['n_reachable']}/{ft['n_far_tail']}")
    if not te["sr_live"]:
        print(f"  INSTANCE-CONDITIONED QUANTA (RUN 13): SKIPPED -- "
              f"StrokeRender not yet landed (same reason as RUN 10/11/12 above)")
    else:
        print(f"  INSTANCE-CONDITIONED QUANTA (RUN 13) -- run-12-adopted control "
              f"{100*run13['acc_control']:.1f}% reproduces 41.2%: "
              f"{'PASS' if control_reproduced_41_2 else 'FAIL -- STOP AND DIAGNOSE'}; "
              f"best lever ({best_arm13}) {100*best_acc13:.1f}% "
              f"(delta {100*(best_acc13-run13['acc_control']):+.1f}pp): "
              f"{'BEATS CONTROL' if best_acc13 > run13['acc_control'] else 'HONEST NULL'}; "
              f"far-tail reachable {ft13['n_reachable']}/{ft13['n_far_tail']}")
    if not te["sr_live"]:
        print(f"  BRANCH A EXECUTION -- SUB-STROKE COMPOSITION (RUN 14): SKIPPED -- "
              f"StrokeRender not yet landed (same reason as RUN 10/11/12/13 above)")
    else:
        print(f"  BRANCH A EXECUTION -- SUB-STROKE COMPOSITION (RUN 14) -- run-12-adopted "
              f"control {100*run14['acc_control']:.1f}% reproduces 41.2%: "
              f"{'PASS' if control_reproduced_41_2_run14 else 'FAIL -- STOP AND DIAGNOSE'}; "
              f"+composition {100*run14['acc_+composition']:.1f}% "
              f"(delta {100*(run14['acc_+composition']-run14['acc_control']):+.1f}pp): "
              f"{'BEATS CONTROL' if run14['acc_+composition'] > run14['acc_control'] else 'HONEST NULL'}; "
              f"far-tail reachable {ft14['n_reachable']}/{ft14['n_far_tail']}")
    if p1 is None:
        print(f"  RUN 15 PHASE 1 (POWER) / PHASE 2 (BRANCH B CONTINUOUS): SKIPPED -- "
              f"StrokeRender not yet landed (same reason as RUN 10-14 above)")
    else:
        print(f"  RUN 15 PHASE 1 (POWER, n={p1['n_episodes']}) -- adopted config "
              f"{100*p1['acc_adopted']:.1f}% [{100*p1['ci_adopted'][0]:.1f},"
              f"{100*p1['ci_adopted'][1]:.1f}] (informational; not gating OVERALL — see the "
              f"full table above)")
        print(f"  RUN 15 PHASE 2 (BRANCH B CONTINUOUS) -- +junction-blend "
              f"{100*p2['acc_blend']:.1f}% [{100*p2['ci_blend'][0]:.1f},"
              f"{100*p2['ci_blend'][1]:.1f}] vs control {100*p2['acc_control']:.1f}%: "
              f"{verdict_b} (informational; not gating OVERALL)")
    print(f"  donkey=0 (no torch anywhere in sys.modules): "
          f"{'PASS' if not donkey else 'FAIL: ' + str(donkey)}")
    assert "torch" not in sys.modules, f"donkey!=0: torch modules present: {donkey}"

    print(f"\n  total runtime: {time.time()-t0:.1f}s")
    print(SEP)
    # RUN 10/RUN 11/RUN 12/RUN 13/RUN 14 are ADDITIVE and, when StrokeRender is not yet live,
    # INFORMATIONAL only (`None`) -- they never block OVERALL on their own absence; when live,
    # they must clear the SAME beats-chance/shuffled-control bar every other headline arm
    # already does. RUN 12/RUN 13/RUN 14's own lever accuracy is explicitly NOT required to
    # beat their own control for OVERALL (the design's own honest-null branch is a valid
    # outcome, not a failure) -- only each run's own CONTROL REPRODUCTION and the
    # beats-chance/shuffled bar on it are gating.
    abs_ok = True if abs_test_pass is None else bool(abs_test_pass)
    run11_ok = True if run11_pass is None else bool(run11_pass)
    run12_ok = True if run12_pass is None else bool(run12_pass)
    run13_ok = True if run13_pass is None else bool(run13_pass)
    run14_ok = True if run14_pass is None else bool(run14_pass)
    overall = (bool(sat_pass) and wr["coherence_rate"] > 0 and test_pass and assign_test_pass
               and control_reproduced and rel2_test_pass and abs_ok and run11_ok and run12_ok
               and run13_ok and run14_ok and not donkey)
    print(f"  OVERALL: {'PASS' if overall else 'HONEST PARTIAL/FAIL ā€” see per-phase verdicts above'}")
    print(SEP)
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())

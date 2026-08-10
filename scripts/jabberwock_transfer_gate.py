"""RUN 24 -- THE TRANSFER GATE (executing f492c1b1's Branch-C verdict: "close the vocabulary-
dependent corridor and pursue the verdict layer's own residuals ... THE TRANSFER GATE (the
generic drawn-shape reproducer proof: same stack, zero retraining, non-handwriting drawn
shapes) + the scale residual").

Per the creator's own standing framing (recorded verbatim in scratchpad/HANDWRITING_DESIGN.md
and CLAUDE.md's Omniglot-arc sections): "when we are done it won't be a handwriting recogniser,
it will be a generic and flexible drawn shape reproducer." Every prior run (1-19) measured on
Omniglot CHARACTERS. This run measures the SAME stack on symbols that are not characters at all
-- the only way to tell "learned handwriting quirks" apart from "a general drawn-shape faculty."

TWO DELIVERABLES:

1. THE TRANSFER GATE -- `domains/symbol_motor_world.py`'s 20 synthetic symbol classes (arrows,
   boxed/plain polygons, a pentagram, an asterisk, circles/targets, a tick-marked spiral, two
   circuit-like glyphs, a key -- built from the SAME line/arc primitives
   `glyph_motor_world._sample_stroke` already supports, varied by the SAME `write_with_hand`
   nuisance model that stands in for "a different drawer"), written to disk in the EXACT
   Omniglot motor-file text format so the UNCHANGED `domains.omniglot_world` parser and
   `domains.abs_read.stage_parse_char`/`parse_marginal_verdict` (Family A's own winning verdict,
   `predict_smooth_marginal_sc_term`, REUSED VERBATIM -- RUN 17b's 80.5% [76.3, 84.1] headline)
   read a synthetic symbol exactly as they read a real character. One-shot 20-way, cross-"hand",
   n >= 200, Wilson CIs, a shuffled control. PLUS the REPRODUCER direction: for a handful of
   query instances, `StrokeQuantize`/`StrokeRender` (the generative inverse pair -- round-trip
   EXACT per commit 42855d5f) render each decoded stroke back to a polyline, and the
   reconstructed drawing is re-classified -- decode(render(decode(x))) must classify the SAME as
   decode(x).

   THE ZERO-ADAPTATION ASSERTION *IS* THE GATE: this script imports `domains.abs_read.
   stage_parse_char`/`parse_marginal_verdict`/`propose_appearance_top_m`/`_stroke_frame_slices`/
   `_render_term`, `domains.stroke_codebook._quantize`, and
   `scripts.jabberwock_omniglot_dynamic_quantization.DK`/`wilson_ci` and calls every one of them
   with ONLY its own pre-existing default parameters (`ar.DEFAULT_PARSE_THETAS`/`_WHOLE_N`/
   `_PER_PART`/`_PART_W`/`_SC_W`/`_BETA`, `gate.DK`'s reduced-bin dict, VERBATIM -- never
   overridden, never redefined). `_assert_zero_adaptation` below makes this mechanically
   checkable: a `git diff` against every decode/verdict-machinery file this script touches must
   be EMPTY. If the transfer domain needed ANY of those files changed to work, that is a
   FINDING this report states honestly -- not a patch made silently (see CLAUDE.md's
   instruction for this run).

2. THE SCALE RESIDUAL -- real Omniglot `strokes_evaluation` characters POOLED CROSS-ALPHABET
   (sorted-path prefix, up to 50-way or the max the pool supports), comparing FULL-DWELL
   parse-marginal (every candidate staged, cost linear in way) against the LAYERED proposal
   (`ar.propose_appearance_top_m`'s held `PointSetDist` shortlist, k~10, feeding the SAME
   `parse_marginal_verdict` staged over only the shortlist -- "bins propose, continuous
   decides" at SCALE, the honest labour `parse_marginal_verdict`'s own docstring names:
   "restricting the candidate SET to a shortlist is ... a STAGING choice ... never a post-hoc
   Python filter of the Term's own verdict"). Accuracy AND budget (candidates staged per query)
   reported per arm; n >= 200 queries, Wilson CIs. Sheds FIRST under the runtime budget (this
   script's own single-process wall clock) -- the transfer gate (1) is the non-negotiable core.

No Rust. No changes to any decode/verdict machinery (enforced by `_assert_zero_adaptation`).
Every classification decision is `ar.parse_marginal_verdict`'s own held Argmax (via
`recognition_graph.predict_smooth_marginal_sc_term`) or `ar.propose_appearance_top_m`'s held
repeated Argmin -- this script does no ranking, no argmin/argmax, no sort-by-score of its own
(`tests/test_transfer_gate_migrated.py`'s source audit checks this, mirroring
`tests/test_character_composition_migrated.py`'s established pattern).

Run:
  ulimit -v 14680064
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_transfer_gate.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import resource
resource.setrlimit(resource.RLIMIT_AS, (14 * 1024 ** 3, 14 * 1024 ** 3))

import numpy as np
import substrate_rs as srs

import scripts.jabberwock_omniglot_dynamic_quantization as gate
from domains import abs_read as ar
from domains import omniglot_world as ow
from domains import stroke_codebook as sc
from domains import symbol_motor_world as sw

SEP = "=" * 92

# ---------------------------------------------------------------------------------------------
# ZERO-ADAPTATION ASSERTION -- every file the decode/verdict pipeline lives in, checked against
# HEAD via `git diff --name-only`. Empty output is the gate; anything else is a FINDING to
# report, not silently swallowed.
# ---------------------------------------------------------------------------------------------
PROTECTED_FILES = [
    "domains/abs_read.py", "domains/ink_decode.py", "domains/stroke_codebook.py",
    "domains/character_compose.py", "domains/canonical_parse.py",
    "domains/recognition_graph.py", "domains/glyph_motor_world.py",
    "domains/omniglot_world.py",
    "scripts/jabberwock_omniglot_dynamic_quantization.py",
    "scripts/jabberwock_omniglot_run17_close.py",
]


def _assert_zero_adaptation() -> dict:
    try:
        out = subprocess.run(["git", "diff", "--name-only", "HEAD", "--"] + PROTECTED_FILES,
                              cwd=ROOT, capture_output=True, text=True, timeout=30)
        changed = [ln for ln in out.stdout.splitlines() if ln.strip()]
        ok = out.returncode == 0 and not changed
        return dict(ok=ok, changed=changed, stderr=out.stderr.strip())
    except Exception as e:  # pragma: no cover -- honest non-crash if git is unavailable
        return dict(ok=None, changed=[], stderr=str(e))


# ---------------------------------------------------------------------------------------------
# DELIVERABLE 1a -- THE TRANSFER GATE: one-shot 20-way, cross-"hand", parse-marginal verdict,
# ZERO code changes, ZERO retraining (parse-marginal stages a fresh scratch substrate per
# block -- no LEARN phase, no stroke codebook, exactly matching the design's own honest
# residual that this verdict "bypasses the earned-quanta layer entirely").
# ---------------------------------------------------------------------------------------------
N_HANDS = 20                 # per class -- mirrors Omniglot's own 20-drawers-per-character
TRANSFER_WAY = len(sw.SYMBOLS)  # 20
TRANSFER_R = 12               # 12 blocks x 20 queries = 240 episodes >= 200
TRANSFER_SEED = 20260724


def _block_spec_symbols(classes: list[str], n_hands: int, rng) -> dict:
    ex_drawer = int(rng.integers(n_hands))
    queries = []
    for qi in range(len(classes)):
        q_drawer = int(rng.integers(n_hands))
        while q_drawer == ex_drawer:
            q_drawer = int(rng.integers(n_hands))
        queries.append((qi, q_drawer))
    return dict(ex_drawer=ex_drawer, queries=queries)


def _stage_candidates(scratch, classes: list[str], paths: dict, drawer: int) -> dict:
    cand_of_node = {}
    for ci, cls in enumerate(classes):
        node = ar.stage_parse_char(scratch, paths[cls][drawer], is_query=False, name=str(ci))
        cand_of_node[node] = ci
    return cand_of_node


def _classify(classes: list[str], paths: dict, ex_drawer: int, query_path: str) -> int:
    """ONE classification decision: `ar.parse_marginal_verdict`'s own held Argmax over a
    freshly staged scratch substrate -- byte-identical call shape to
    `scripts.jabberwock_omniglot_run17_close._run_block_parse`, just over symbol paths."""
    scratch = srs.Substrate()
    cand_of_node = _stage_candidates(scratch, classes, paths, ex_drawer)
    qnode = ar.stage_parse_char(scratch, query_path, is_query=True)
    winner = ar.parse_marginal_verdict(scratch, qnode)
    return cand_of_node.get(winner, -1) if winner is not None else -1


def _run_block_transfer(classes: list[str], paths: dict, spec: dict) -> list[dict]:
    scratch = srs.Substrate()
    cand_of_node = _stage_candidates(scratch, classes, paths, spec["ex_drawer"])
    records = []
    for qi, q_drawer in spec["queries"]:
        qnode = ar.stage_parse_char(scratch, paths[classes[qi]][q_drawer], is_query=True)
        winner = ar.parse_marginal_verdict(scratch, qnode)
        pred = cand_of_node.get(winner, -1) if winner is not None else -1
        records.append(dict(true=qi, pred=pred))
    return records


def run_transfer_gate(paths: dict) -> dict:
    classes = sorted(paths)
    assert classes == sorted(sw.SYMBOLS), "class ordering must match the symbol domain exactly"
    rng = np.random.default_rng(TRANSFER_SEED)
    records = []
    t0 = time.time()
    for _r in range(TRANSFER_R):
        spec = _block_spec_symbols(classes, N_HANDS, rng)
        records.extend(_run_block_transfer(classes, paths, spec))
    elapsed = time.time() - t0

    trues = [r["true"] for r in records]
    preds = [r["pred"] for r in records]
    k = sum(1 for p, t in zip(preds, trues) if p == t)
    acc = k / max(1, len(trues))
    ci = gate.wilson_ci(k, len(trues))

    shuf = list(trues)
    np.random.default_rng(TRANSFER_SEED + 1).shuffle(shuf)
    ks = sum(1 for p, t in zip(preds, shuf) if p == t)
    acc_s = ks / max(1, len(shuf))
    ci_s = gate.wilson_ci(ks, len(shuf))

    return dict(n=len(trues), k=k, acc=acc, ci=ci, acc_shuffled=acc_s, ci_shuffled=ci_s,
                elapsed=elapsed, way=len(classes))


# ---------------------------------------------------------------------------------------------
# DELIVERABLE 1b -- THE REPRODUCER: decode(render(decode(x))) must classify the SAME as
# decode(x). "decode" here is the SAME `_classify` verdict above; "render" is the held
# `StrokeQuantize`/`StrokeRender` Term pair, mechanically applied per stroke -- no codebook,
# no LEARN, pure geometry (both Terms are stateless).
# ---------------------------------------------------------------------------------------------
def _bbox(points) -> tuple:
    pts = np.asarray(points, dtype=float).reshape(-1, 2)
    return (float(pts[:, 0].min()), float(pts[:, 1].min()),
            float(pts[:, 0].max()), float(pts[:, 1].max()))


def _round_trip_render(native, path: str, dk: dict) -> list:
    """StrokeQuantize each of `path`'s own strokes at its OWN pose (canonical_pose=False --
    the actual instance, not a canonicalized codebook entry), then StrokeRender the resulting
    signature straight back to a polyline (apply_pose=True inside `ar._render_term`) -- the
    stroke-level round trip commit 42855d5f already proved exact, applied here per stroke of a
    whole drawing. Falls back to the ORIGINAL points (never a fabricated render) if a stroke is
    degenerate or the render Term returns nothing."""
    rendered = []
    for stroke in ow.load_strokes(path):
        pts = stroke.tolist()
        if len(pts) < 2:
            rendered.append(pts)
            continue
        bbox = _bbox(pts)
        q = sc._quantize(native, pts, segments=dk["segments"], turn_bins=dk["turn_bins"],
                          len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"],
                          canonical_pose=False, bounds=bbox)
        term = ar._render_term(q["signature"], n_points=len(pts), bounds=bbox,
                                turn_bins=dk["turn_bins"], len_bins=dk["len_bins"],
                                grid=dk["grid"], scale_bins=dk["scale_bins"])
        rpts = native.evaluate(term, {})
        rendered.append([list(p) for p in rpts] if rpts else pts)
    return rendered


REPRODUCER_N = 5


def run_reproducer(paths: dict, tmp_root: str) -> dict:
    classes = sorted(paths)
    native = srs.Substrate()._inner
    rng = np.random.default_rng(TRANSFER_SEED + 2)
    probe_classes = list(rng.choice(classes, size=REPRODUCER_N, replace=False))
    ex_drawer = 0
    rows = []
    for cls in probe_classes:
        q_drawer = 1 if 1 != ex_drawer else 2
        qpath = paths[cls][q_drawer]
        c1 = _classify(classes, paths, ex_drawer, qpath)
        rendered_strokes = _round_trip_render(native, qpath, gate.DK)
        rpath = os.path.join(tmp_root, "_reproduced", f"{cls}_{q_drawer:02d}_rt.txt")
        sw.write_motor_file(rpath, rendered_strokes)
        c2 = _classify(classes, paths, ex_drawer, rpath)
        true_idx = classes.index(cls)
        rows.append(dict(cls=cls, true=true_idx, c1=c1, c2=c2, match=(c1 == c2),
                          c1_correct=(c1 == true_idx), c2_correct=(c2 == true_idx)))
    n_match = sum(1 for r in rows if r["match"])
    return dict(rows=rows, n=len(rows), n_match=n_match)


# ---------------------------------------------------------------------------------------------
# DELIVERABLE 2 -- THE SCALE RESIDUAL: real Omniglot evaluation characters pooled cross-
# alphabet, FULL-DWELL vs LAYERED (appearance shortlist -> parse-marginal) parse-marginal.
# ---------------------------------------------------------------------------------------------
SCALE_WAY_TARGET = 50
SCALE_SHORTLIST_K = 10
SCALE_SEED = gate.SEED + 24000
SCALE_R_TARGET = 5            # 5 x 50 = 250 queries >= 200 (shed first under budget)


def pool_evaluation_characters(way_target: int) -> tuple[list[str], int]:
    all_chars: list[str] = []
    for alph in sorted(ow.alphabets("evaluation")):
        all_chars.extend(ow.characters(alph, "evaluation"))
    all_chars = sorted(all_chars)
    return all_chars[:way_target], len(all_chars)


def _block_spec_pooled(candidates: list[str], rng, way: int) -> dict:
    drawer_files = [ow.drawings(c) for c in candidates]
    n_drawers = min(len(fl) for fl in drawer_files)
    ex_drawer = int(rng.integers(n_drawers))
    queries = []
    for qi in range(way):
        q_drawer = int(rng.integers(n_drawers))
        while q_drawer == ex_drawer:
            q_drawer = int(rng.integers(n_drawers))
        queries.append((qi, q_drawer))
    return dict(drawer_files=drawer_files, ex_drawer=ex_drawer, queries=queries)


def _raw_frame_slices(path: str) -> dict:
    """The query's/a candidate's OWN raw per-stroke observed points -- NO ink_decode, NO
    codebook, NO LEARN (`ar._stroke_frame_slices` only ever reads `item[0]`, the points --
    the identity name it also accepts is irrelevant to the appearance/PointSetDist modality,
    so this passes `None` for it and skips decoding entirely, keeping the layered arm cheap)."""
    raw = [(pts.tolist(), None) for pts in ow.load_strokes(path) if pts.shape[0] >= 1]
    _, slices = ar._stroke_frame_slices(raw)
    return slices


def _run_block_scale(native, spec: dict, way: int, shortlist_k: int) -> list[dict]:
    drawer_files, ex_drawer = spec["drawer_files"], spec["ex_drawer"]
    cand_slices = [_raw_frame_slices(drawer_files[ci][ex_drawer]) for ci in range(way)]
    records = []
    for qi, q_drawer in spec["queries"]:
        qpath = drawer_files[qi][q_drawer]
        q_slices = _raw_frame_slices(qpath)

        t0 = time.time()
        scratch_full = srs.Substrate()
        cand_of_node = {}
        for ci in range(way):
            node = ar.stage_parse_char(scratch_full, drawer_files[ci][ex_drawer],
                                        is_query=False, name=str(ci))
            cand_of_node[node] = ci
        qnode = ar.stage_parse_char(scratch_full, qpath, is_query=True)
        winner = ar.parse_marginal_verdict(scratch_full, qnode)
        w_full = cand_of_node.get(winner, -1) if winner is not None else -1
        t_full = time.time() - t0

        t1 = time.time()
        shortlist = ar.propose_appearance_top_m(native, q_slices, cand_slices, m=shortlist_k)
        scratch_s = srs.Substrate()
        cand_of_node_s = {}
        for ci in shortlist:
            node = ar.stage_parse_char(scratch_s, drawer_files[ci][ex_drawer], is_query=False,
                                        name=str(ci))
            cand_of_node_s[node] = ci
        qnode_s = ar.stage_parse_char(scratch_s, qpath, is_query=True)
        winner_s = ar.parse_marginal_verdict(scratch_s, qnode_s)
        w_layered = cand_of_node_s.get(winner_s, -1) if winner_s is not None else -1
        t_layered = time.time() - t1

        records.append(dict(true=qi, w_full=w_full, w_layered=w_layered, budget_full=way,
                             budget_layered=len(shortlist), t_full=t_full, t_layered=t_layered,
                             in_shortlist=(qi in shortlist)))
    return records


def _acc_ci(preds, trues) -> dict:
    k = sum(1 for p, t in zip(preds, trues) if p == t)
    acc = k / max(1, len(trues))
    ci = gate.wilson_ci(k, len(trues))
    return dict(k=k, n=len(trues), acc=acc, ci=ci)


def run_scale_residual(hard_deadline: float) -> dict:
    if not ow.have_data("evaluation"):
        return dict(skipped="Omniglot evaluation data not found")
    candidates, pool_size = pool_evaluation_characters(SCALE_WAY_TARGET)
    way = len(candidates)
    native = srs.Substrate()._inner
    rng = np.random.default_rng(SCALE_SEED)

    pilot_t0 = time.time()
    pilot_spec = _block_spec_pooled(candidates, rng, way)
    pilot_records = _run_block_scale(native, pilot_spec, way, SCALE_SHORTLIST_K)
    pilot_elapsed = time.time() - pilot_t0

    remaining = hard_deadline - time.time()
    projected_per_block = pilot_elapsed
    r_afford = max(0, int(remaining / max(1e-6, projected_per_block)))
    r_used = max(1, min(SCALE_R_TARGET - 1, r_afford))   # -1: pilot block already counts as one
    shed_note = None
    if r_used < SCALE_R_TARGET - 1:
        shed_note = (f"budget shed: running {r_used + 1}/{SCALE_R_TARGET} blocks "
                     f"({(r_used + 1) * way} queries) -- pilot block took {pilot_elapsed:.1f}s, "
                     f"remaining budget {remaining:.0f}s.")

    records = list(pilot_records)
    for _r in range(r_used):
        spec = _block_spec_pooled(candidates, rng, way)
        records.extend(_run_block_scale(native, spec, way, SCALE_SHORTLIST_K))
        if time.time() > hard_deadline:
            shed_note = (shed_note or "") + " hard deadline hit mid-scope."
            break

    trues = [r["true"] for r in records]
    r_full = _acc_ci([r["w_full"] for r in records], trues)
    r_layered = _acc_ci([r["w_layered"] for r in records], trues)
    budget_full = float(np.mean([r["budget_full"] for r in records])) if records else 0.0
    budget_layered = float(np.mean([r["budget_layered"] for r in records])) if records else 0.0
    t_full_mean = float(np.mean([r["t_full"] for r in records])) if records else 0.0
    t_layered_mean = float(np.mean([r["t_layered"] for r in records])) if records else 0.0
    coverage_at_k = (float(np.mean([1.0 if r["in_shortlist"] else 0.0 for r in records]))
                      if records else 0.0)

    return dict(way=way, pool_size=pool_size, n=len(records), full=r_full, layered=r_layered,
                budget_full=budget_full, budget_layered=budget_layered,
                t_full_mean=t_full_mean, t_layered_mean=t_layered_mean, shed_note=shed_note,
                coverage_at_k=coverage_at_k)


# ---------------------------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------------------------
def main():
    t0 = time.time()
    print(SEP)
    print("RUN 24 -- THE TRANSFER GATE + THE SCALE RESIDUAL (f492c1b1's Branch-C verdict)")
    print(SEP)

    za = _assert_zero_adaptation()
    print(f"\n  ZERO-ADAPTATION ASSERTION (git diff HEAD -- {len(PROTECTED_FILES)} decode/"
          f"verdict files): {'PASS -- no changes' if za['ok'] else 'FAIL/UNKNOWN'}")
    if za["changed"]:
        print(f"    CHANGED (FINDING, not silently patched): {za['changed']}")
    if za["stderr"]:
        print(f"    git stderr: {za['stderr']}")

    tmp_root = tempfile.mkdtemp(prefix="transfer_gate_")
    print(f"\n  synthetic symbol corpus root: {tmp_root}")
    paths = sw.build_symbol_corpus(tmp_root, n_hands=N_HANDS, seed=TRANSFER_SEED)
    print(f"  {len(paths)} symbol classes x {N_HANDS} simulated hands = "
          f"{len(paths) * N_HANDS} synthetic drawings written "
          f"(line/arc primitives only, hermetic, no external data).")

    print(f"\n{SEP}\n  DELIVERABLE 1a -- THE TRANSFER GATE (one-shot {TRANSFER_WAY}-way, "
          f"cross-hand, parse-marginal, zero retraining)\n{SEP}")
    tg = run_transfer_gate(paths)
    print(f"  n={tg['n']}  k={tg['k']}  accuracy={100*tg['acc']:.1f}%  "
          f"95% CI [{100*tg['ci'][0]:.1f}%, {100*tg['ci'][1]:.1f}%]  "
          f"chance={100.0/tg['way']:.1f}%")
    print(f"  SHUFFLED CONTROL: accuracy={100*tg['acc_shuffled']:.1f}%  "
          f"95% CI [{100*tg['ci_shuffled'][0]:.1f}%, {100*tg['ci_shuffled'][1]:.1f}%]")
    print(f"  elapsed: {tg['elapsed']:.1f}s")
    generality = tg["ci"][0] > tg["ci_shuffled"][1]
    print(f"  GENERALITY VERDICT: real accuracy CI "
          f"{'IS' if generality else 'is NOT'} separated above the shuffled CI -- "
          f"{'the stack transfers to a non-handwriting domain with zero adaptation' if generality else 'transfer NOT established at this power'}.")

    print(f"\n{SEP}\n  DELIVERABLE 1b -- THE REPRODUCER (decode(render(decode(x))) == "
          f"decode(x))\n{SEP}")
    rt = run_reproducer(paths, tmp_root)
    for row in rt["rows"]:
        print(f"    class={row['cls']:<18} true={row['true']:>2}  decode(x)={row['c1']:>2} "
              f"({'correct' if row['c1_correct'] else 'incorrect'})  "
              f"decode(render(decode(x)))={row['c2']:>2} "
              f"({'correct' if row['c2_correct'] else 'incorrect'})  "
              f"{'MATCH' if row['match'] else 'MISMATCH'}")
    print(f"  reproducer round-trip: {rt['n_match']}/{rt['n']} instances classify identically "
          f"before and after StrokeQuantize->StrokeRender reconstruction.")

    print(f"\n{SEP}\n  DELIVERABLE 2 -- THE SCALE RESIDUAL (real Omniglot, pooled cross-"
          f"alphabet, full-dwell vs layered parse-marginal)\n{SEP}")
    hard_deadline = t0 + 560.0
    sr = run_scale_residual(hard_deadline)
    if sr.get("skipped"):
        print(f"  SKIPPED: {sr['skipped']}")
    else:
        print(f"  pooled {sr['pool_size']} qualifying evaluation characters, way={sr['way']} "
              f"(target {SCALE_WAY_TARGET}).")
        print(f"  FULL DWELL     n={sr['full']['n']:>4}  acc={100*sr['full']['acc']:5.1f}%  "
              f"95% CI [{100*sr['full']['ci'][0]:5.1f}%, {100*sr['full']['ci'][1]:5.1f}%]  "
              f"mean budget={sr['budget_full']:.1f} candidates/query  "
              f"mean time={sr['t_full_mean']*1000:.0f}ms/query")
        print(f"  LAYERED (k={SCALE_SHORTLIST_K})  n={sr['layered']['n']:>4}  "
              f"acc={100*sr['layered']['acc']:5.1f}%  "
              f"95% CI [{100*sr['layered']['ci'][0]:5.1f}%, {100*sr['layered']['ci'][1]:5.1f}%]  "
              f"mean budget={sr['budget_layered']:.1f} candidates/query  "
              f"mean time={sr['t_layered_mean']*1000:.0f}ms/query")
        overlap = not (sr['layered']['ci'][1] < sr['full']['ci'][0]
                       or sr['full']['ci'][1] < sr['layered']['ci'][0])
        print(f"  LAYERED vs FULL DWELL: {'CI-OVERLAP (accuracy held)' if overlap else 'CI-SEPARATED'} "
              f"at a {sr['budget_full']/max(1e-9, sr['budget_layered']):.1f}x budget reduction "
              f"(candidates fed to the marginalization).")
        print(f"  APPEARANCE SHORTLIST coverage@{SCALE_SHORTLIST_K}: "
              f"{100*sr['coverage_at_k']:.1f}% of queries had the TRUE candidate in the "
              f"shortlist at all (the recall ceiling the layered arm's accuracy cannot exceed).")
        if sr["shed_note"]:
            print(f"  BUDGET NOTE: {sr['shed_note']}")

    donkey0 = "torch" not in sys.modules
    print(f"\n{SEP}\n  INVARIANTS\n{SEP}")
    print(f"  donkey=0 (no torch anywhere in sys.modules): {'PASS' if donkey0 else 'FAIL'}")
    print(f"  zero-adaptation (no decode/verdict file changed): "
          f"{'PASS' if za['ok'] else 'FAIL/UNKNOWN'}")
    print(f"  total runtime: {time.time() - t0:.1f}s")
    print(SEP)
    overall = donkey0 and za["ok"] is not False and generality
    print(f"  OVERALL: {'PASS' if overall else 'FAIL'}")
    print(SEP)
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())

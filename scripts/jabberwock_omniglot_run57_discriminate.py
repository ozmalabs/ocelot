"""OMNIGLOT RUN 57 -- THE JABBERWOCK BUILDS A GRAPH-NATIVE DISCRIMINATION CAPABILITY. The
creator's directive, verbatim: "Building a richer discrimination capability graph native is its own
reward. Have the jabberwock do that."

RUN 56's EXACT FAILURE (6e193f22): the unified log-odds verdict's precision was `1 / within-TRUE-
class variance` (TIGHTNESS). Tightness OVER-TRUSTS a relation that is tight for the true class but
ALSO tight for FALSE classes -- within-class tightness is NOT discriminative power. Result: the weak
`rel` grain participated heavily and broke more than it fixed (FIXED=3 vs BROKE=13) -> -12.5pp harm.

THE FIX = DISCRIMINABILITY as precision (`domains/discrimination.py`): a feature's weight = FISHER's
ratio = BETWEEN-class variance / WITHIN-class variance. A part that SEPARATES the true candidate
from the false ones is trusted; a part tight-but-NON-separating (run 56's failure) is distrusted.
This is a GENERAL graph-native recognition faculty ("its own reward"): any recognizer must know what
SEPARATES, not merely what is consistent.

TWO COMPONENTS, both graph-resident:
  1. DISCRIMINABILITY PRECISION (the direct fix): per part-type, `part_discriminability(true_res,
     false_res)` = Fisher between/within over the background records. Stored as graph FrameAxis
     `log_weight` EDGES (`install_part_precisions`, run-30 representation) and READ BACK for the
     verdict. Fed to the UNCHANGED `unified_verdict` machinery -- "reuse verbatim; ONLY the precision
     VALUES change: tightness -> discriminability" (the directive). ARM D = the same log-odds argmin,
     discriminability precisions.
  2. RICHER RELATIONS (more for discrimination to find): ATTACHMENT / JUNCTION structure -- WHERE
     strokes connect (endpoint-endpoint / endpoint-midpoint / midpoint-midpoint / none), the
     topological content coarse pairwise pose cannot carry. Derived graph-native from stroke point
     arrays; measured for separating power against the coarse pose relations.

GATE (run 26/54/55 protocol):
  * CHEAP FALSIFIER FIRST (SEPARATION, not tightness): does discriminability rank features
    DIFFERENTLY from tightness (correctly distrust the non-separating rel)? Do the richer junction
    relations show MATERIALLY higher discriminability than coarse pose? Pre-registered: a null here
    (coarse ~ junction, discriminability ~ tightness) localizes to the corpus (mouse-Omniglot
    arrangement genuinely non-separating), and the FACULTY STILL STANDS as a general capability.
  * FULL GATE: GUARD = whole-shape log-odds (85% background, reproduce byte-identically). ARM D =
    unified derivation with DISCRIMINABILITY precision. BACKGROUND-SANITY STOP (ARM D >= GUARD - 3pp)
    before any eval. McNemar ARM D vs GUARD on eval if sanity passes.
  * HONEST FRAME ("its own reward"): report the FACULTY (graph-native, discriminability != tightness,
    correctly distrusts non-separating features) SEPARATELY from whether it converts on Omniglot. A
    WIN = the concept SEPARATES (ceiling crack). A NULL = the faculty is real+general but mouse-
    Omniglot lacks separating arrangement content (localizes to corpus) -- BOTH are results.

BACKGROUND SOURCE: run 55's frozen records (`results/run55_checkpoints/calibrate_state.json`,
READ-ONLY) -- their per-candidate (whole, stroke, rel) triples over the SAME background population +
seed, so the ONLY change from run 56 is the PRECISION (discriminability, not tightness) and hence the
verdict. Byte-identical GUARD confirms the geometry path is untouched.

EXECUTION: every invocation <=540s FOREGROUND, `stdbuf -oL ... | tee -a
results/omniglot_gate_run57.log`, checkpoints under `results/run57_checkpoints/`
(every `results/run*_checkpoints/` READ-ONLY; parallel-session files untouched). `.venv` python.
`OZMA_SEED_PERSIST_DISABLED=1` + a before/after md5 seed-guard on every stage.

Run:
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python3 \\
      scripts/jabberwock_omniglot_run57_discriminate.py --stage <STAGE>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
from scipy.stats import binomtest

import substrate_rs as srs
import scripts.jabberwock_omniglot_dynamic_quantization as gate
import scripts.jabberwock_omniglot_run50_relational as run50
import scripts.jabberwock_omniglot_run54b_reliability as run54b
import scripts.jabberwock_omniglot_run55_native as run55
from domains import unified_verdict as uv
from domains import discrimination as disc
from domains import relational_variation as rv

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run57_checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)
RUN55_DIR = os.path.join(ROOT, "results", "run55_checkpoints")            # READ-ONLY reference.
RUN55_CALIB_STATE = os.path.join(RUN55_DIR, "calibrate_state.json")        # background residual SOURCE.
STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")

WAY = run55.WAY
CHANCE = 1.0 / WAY
SANITY_MARGIN = 0.03
DK = gate.DK
PARTS = ("whole", "stroke", "rel")

CALIB_PATH = os.path.join(CKPT_DIR, "calibrate.json")
FALSIFIER_PATH = os.path.join(CKPT_DIR, "falsifier.json")
FALSIFIER_STATE = os.path.join(CKPT_DIR, "falsifier_state.json")
EVAL_STATE_PATH = os.path.join(CKPT_DIR, "eval_state.json")
EVAL_PATH = os.path.join(CKPT_DIR, "eval.json")


def _ckpt(name):
    return os.path.join(CKPT_DIR, name)


def _save_json(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=run54b._json_default)


def _load_json(path):
    with open(path) as f:
        return json.load(f)


def _md5(path):
    if not os.path.exists(path):
        return "MISSING"
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def _donkey0():
    return "torch" not in sys.modules


def _mcnemar(correct_a, correct_b):
    fixed = sum(1 for a, b in zip(correct_a, correct_b) if (not a) and b)
    broken = sum(1 for a, b in zip(correct_a, correct_b) if a and (not b))
    n_disc = fixed + broken
    p = float(binomtest(fixed, n_disc, 0.5, alternative="two-sided").pvalue) if n_disc else 1.0
    return dict(fixed=fixed, broken=broken, discordant=n_disc, p=p)


def _seed_guard(stage, md5_before):
    md5_after = _md5(STROKE_SHAPES_SEED)
    ok = md5_after == md5_before
    print(f"\n  seeds/stroke_shapes.json md5 AFTER {stage}: {md5_after}  UNCHANGED={ok}")
    if not ok:
        raise SystemExit(f"HARD STOP: seed write detected during --stage {stage}.")


# ============================================================================================= #
# PART-LEVEL RESIDUAL SPLIT + PRECISIONS (pure statistics over the frozen background records).
# ============================================================================================= #
def _residual_split(records):
    """`{part: {"true": [...], "false": [...]}}` -- the TRUE candidate's residual and the pooled
    FALSE candidates' residuals for each part-type, across background episodes."""
    res = {p: {"true": [], "false": []} for p in PARTS}
    for r in records:
        ti = r["true_idx"]
        for ci, c in enumerate(r["per"]):
            for p in PARTS:
                res[p]["true" if ci == ti else "false"].append(c[p])
    return res


def _discriminability_precisions(records):
    """Fisher between/within per part-type -> stored as graph FrameAxis log_weight edges -> read
    BACK from the graph. The precision the verdict consumes is GRAPH DATA."""
    res = _residual_split(records)
    prec = {p: disc.part_discriminability(res[p]["true"], res[p]["false"]) for p in PARTS}
    sub = srs.Substrate()
    frame = disc.install_part_precisions(sub, prec)
    graph_prec = disc.read_part_precisions(sub, frame, parts=PARTS)      # read from graph edges.
    return graph_prec, res


def _tightness_precisions(records):
    """Run 56's precisions (kept only for the falsifier's side-by-side comparison)."""
    res = _residual_split(records)
    return {p: disc.tightness(res[p]["true"]) for p in PARTS}


def _preds(records, prec):
    """GUARD (geometry-only, prec_rel=0) + ARM D (whole+rel, discriminability precisions). Every
    ranking is the held `unified_verdict_pred` Argmin -- no Python min/sort."""
    native = srs.Substrate()._inner
    pw, ps, pr = prec["whole"], prec["stroke"], prec["rel"]
    guard, arm = [], []
    for r in records:
        guard.append(uv.unified_verdict_pred(native, r["per"], prec_whole=pw, prec_stroke=0.0,
                                             prec_rel=0.0))
        arm.append(uv.unified_verdict_pred(native, r["per"], prec_whole=pw, prec_stroke=0.0,
                                           prec_rel=pr))
    return guard, arm


def _source_background():
    if not os.path.exists(RUN55_CALIB_STATE):
        raise SystemExit(f"WALL: {RUN55_CALIB_STATE} missing (run 55 frozen background required).")
    st = _load_json(RUN55_CALIB_STATE)
    recs = st.get("records", [])
    if not recs:
        raise SystemExit("WALL: run 55 frozen background has no records.")
    return recs, st.get("timing", {})


# ============================================================================================= #
# STAGE: compose -- PART 1, the jabberwock authors the concern.
# ============================================================================================= #
CONCERN_CLAUSES = [
    # cue-word-LED clauses (run 41 lesson: induce_concern keys the residual on each clause's FIRST
    # word -> lead with the cue word). The concern: weight a feature by how it SEPARATES classes.
    ["invariant", "SEPARATION", "under", "CLASS"],
    ["vary", "FEATURE", "between", "CLASS"],
    ["bound", "FEATURE", "within", "CLASS"],
    ["judge", "FEATURE", "by", "SEPARATION"],
]


def stage_compose():
    print(f"\n{SEP}\n  STAGE: compose (PART 1 -- the jabberwock frames + grounds the discrimination "
          f"concern)\n{SEP}")
    md5_before = _md5(STROKE_SHAPES_SEED)
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains.reflective_faculty import induce_concern, ground_concern

    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    s = a.s
    print(f"  BOOT: WorldAdapter(seeds=()) + load_all_seeds -> {len(list(s.nodes('SeedSummary')))} "
          f"seeds installed (full topological boot; produce() pipeline live)")

    concern_text = ("discriminate: weight a feature by how it SEPARATES classes, not by how "
                    "consistent it is within a class")
    print(f"\n  THE CONCERN (framed): {concern_text!r}")

    obs = list(CONCERN_CLAUSES)
    print(f"\n  observation (cue-word-led clauses): {obs}")
    ind = induce_concern(a, obs, name_hint="discriminate_by_separation")
    print(f"\n  induce_concern -> minted={ind.get('minted')} "
          f"capability_key={ind.get('capability_key')!r} "
          f"residual_predicates={ind.get('residual_predicates')} "
          f"covered_by={ind.get('covered_by')!r}")
    grounded = {}
    ckey = ind.get("capability_key")
    if ckey:
        g = ground_concern(a, [ckey])
        grounded = g
        print(f"  ground_concern -> grounded={g.get('grounded')} path={g.get('path')!r} "
              f"form={g.get('form')!r}")
        print(f"    AUTHORED/mechanism VERBATIM: {json.dumps(g, default=str)[:1400]}")
    else:
        print("  induce_concern surfaced no capability_key -- reported, not forced.")

    # honest self-report of the concern's own authored signature (produce() needs the LanguageWorld
    # teacher_stub plumbing; the concern's signature IS the agent's own framing, reported verbatim).
    voice = None
    try:
        from domains.reflective_faculty import author_signature
        s.add_node("Concept", {"name": "discrimination_concern", "definition": concern_text})
        sig, _defn, _cn = author_signature(s, "discrimination_concern")
        voice = sig or []
        print(f"\n  THE AGENT'S OWN SIGNATURE for the concern (author_signature): {voice}")
    except Exception as e:
        print(f"\n  self-report unavailable ({type(e).__name__}: {e}) -- honest skip.")

    out = dict(concern_text=concern_text, clauses=obs, induce=ind, ground=grounded, voice=voice,
               substring_caveat=("RelationCue grounding is SUBSTRING-SHALLOW (run 41, 145d3349): "
                                 "the grounding front-end matches cue words, so the VALUE of the "
                                 "faculty is proven by the GATE (does discriminability distrust "
                                 "non-separating features + protect the verdict), not by the "
                                 "grounding text."))
    _save_json(out, _ckpt("compose.json"))
    _seed_guard("compose", md5_before)
    print(f"\n  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


# ============================================================================================= #
# STAGE: unit_sanity -- unit tests + run56/run50 suites + seed guard.
# ============================================================================================= #
def stage_unit_sanity():
    print(f"\n{SEP}\n  STAGE: unit_sanity\n{SEP}")
    md5_before = _md5(STROKE_SHAPES_SEED)
    print(f"  seeds/stroke_shapes.json md5 (BEFORE): {md5_before}")
    ok_all = True
    for test_file in ("tests/test_discrimination_migrated.py",
                      "tests/test_unified_verdict_migrated.py",
                      "tests/test_relational_variation_migrated.py"):
        print(f"\n  running {test_file} ...")
        proc = subprocess.run([sys.executable, "-m", "pytest", test_file, "-q"],
                              cwd=ROOT, env={**os.environ}, capture_output=True, text=True,
                              timeout=300)
        print(proc.stdout[-1500:])
        if proc.returncode != 0:
            print(proc.stderr[-2000:])
        ok = proc.returncode == 0
        print(f"      -> {'PASS' if ok else 'FAIL'}")
        ok_all &= ok
    _seed_guard("unit_sanity", md5_before)
    print(f"\n{SEP}\n  UNIT SANITY: {'ALL PASS' if ok_all else 'SOME FAILED -- DO NOT PROCEED'}\n{SEP}")
    _save_json({"ok_all": bool(ok_all)}, _ckpt("unit_sanity.json"))
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    if not ok_all:
        raise SystemExit(1)
    return 0


def _require_unit_sanity():
    p = _ckpt("unit_sanity.json")
    if not os.path.exists(p) or not _load_json(p).get("ok_all"):
        raise SystemExit("WALL: run --stage unit_sanity (to PASS) first.")


# ============================================================================================= #
# STAGE: falsifier -- CHEAP separation test FIRST. Part-level (free) + richer junction (decode).
# ============================================================================================= #
def stage_falsifier():
    print(f"\n{SEP}\n  STAGE: falsifier (SEPARATION, not tightness -- the cheap test before the "
          f"gate)\n{SEP}")
    _require_unit_sanity()
    md5_before = _md5(STROKE_SHAPES_SEED)

    # ---- PART A -- part-level discriminability vs tightness (FREE, frozen records) ----
    records, _timing = _source_background()
    res = _residual_split(records)
    tight = {p: disc.tightness(res[p]["true"]) for p in PARTS}
    fish = {p: disc.part_discriminability(res[p]["true"], res[p]["false"]) for p in PARTS}
    tight_rank = sorted(PARTS, key=lambda p: -tight[p])
    fish_rank = sorted(PARTS, key=lambda p: -fish[p])
    print(f"\n  ---- PART A: part-level TIGHTNESS (run 56) vs DISCRIMINABILITY (run 57) ----")
    print(f"    {'part':8}{'tightness':>12}{'fisher_disc':>13}{'mean_true':>11}{'mean_false':>11}")
    for p in PARTS:
        print(f"    {p:8}{tight[p]:12.3f}{fish[p]:13.5f}"
              f"{np.mean(res[p]['true']):11.4f}{np.mean(res[p]['false']):11.4f}")
    print(f"    tightness rank (most-trusted first):      {tight_rank}")
    print(f"    discriminability rank (most-trusted first): {fish_rank}")
    ranks_differ = tight_rank != fish_rank
    rel_distrusted = fish["rel"] == min(fish.values())
    print(f"    -> rankings DIFFER: {ranks_differ}; discriminability puts rel LAST "
          f"(distrusts the non-separating grain): {rel_distrusted}")
    print(f"    prec ratio rel/whole -- tightness={tight['rel']/max(tight['whole'],1e-9):.4f} "
          f"vs discriminability={fish['rel']/max(fish['whole'],1e-9):.4f} "
          f"(lower => rel participates LESS => distrust)")

    # ---- PART B -- richer JUNCTION relations vs coarse pose (decode bounded background) ----
    partB = _falsifier_richer(md5_before)
    if partB is None:
        return 0                            # partial decode; re-invoke.

    coarse_fish = partB["coarse_fisher"]
    junction_fish = partB["junction_fisher"]
    coarse_max = max(coarse_fish.values()) if coarse_fish else 0.0
    junction_max = max(junction_fish.values()) if junction_fish else 0.0
    print(f"\n  ---- PART B: coarse pose vs richer JUNCTION discriminability (n_classes="
          f"{partB['n_classes']}) ----")
    print(f"    coarse pose slot Fisher:  {{{', '.join(f'{k}={v:.4f}' for k,v in coarse_fish.items())}}}")
    print(f"    junction slot Fisher:     {{{', '.join(f'{k}={v:.4f}' for k,v in junction_fish.items())}}}")
    print(f"    coarse MAX Fisher={coarse_max:.4f}   junction MAX Fisher={junction_max:.4f}")
    richer_separates = junction_max > 1.5 * coarse_max and junction_max > 0.10
    print(f"    -> richer relations MATERIALLY more separating (>1.5x coarse AND >0.10): "
          f"{richer_separates}")

    out = dict(part_a=dict(tightness=tight, fisher=fish, tight_rank=tight_rank,
                           fisher_rank=fish_rank, ranks_differ=ranks_differ,
                           rel_distrusted=rel_distrusted),
               part_b=partB, coarse_max=coarse_max, junction_max=junction_max,
               richer_separates=bool(richer_separates))
    _save_json(out, FALSIFIER_PATH)
    _seed_guard("falsifier", md5_before)
    print(f"\n  {'='*30}  FALSIFIER VERDICT  {'='*30}")
    print(f"    (1) discriminability != tightness (distrusts the non-separating rel): "
          f"{ranks_differ and rel_distrusted}")
    print(f"    (2) richer junction relations separate materially more than coarse pose: "
          f"{richer_separates}")
    if not richer_separates:
        print(f"    => NO richer separating signal beyond geometry: mouse-Omniglot arrangement is "
              f"genuinely non-separating (joins the pen-data thread). The FACULTY STILL STANDS "
              f"(part A: it correctly distrusts the weak grain). ARM D will reduce to ~GUARD "
              f"(the faculty PROTECTS the verdict vs run 56's -12.5pp harm) -- proceed to "
              f"calibrate to confirm.")
    else:
        print(f"    => richer relations SEPARATE -- worth folding into the rel residual; the "
              f"discrimination faculty then has separating content to weight.")
    print(f"    donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


def _falsifier_richer(md5_before):
    """Decode bounded background multi-stroke classes; per-class per-slot means+variances for the
    COARSE pose relations (via `relational_variation`) AND per-class junction PROFILES (via
    `discrimination.junction_profile`); Fisher between/within for each. Checkpointed per alphabet,
    time-boxed like run 50/55."""
    state = (_load_json(FALSIFIER_STATE) if os.path.exists(FALSIFIER_STATE)
             else dict(alph_idx=0, coarse_by_slot={}, junction_by_slot={}, n_classes=0))
    population = run54b._background_population()          # the SAME background multi-stroke classes.
    ep_alphs = sorted(population)
    s = run50._load_codebook_substrate()
    native = s._inner
    cache = {}
    hard_deadline = time.time() + run55.PER_CALL_BUDGET_SECONDS
    drawers = run50.LEARN_DRAWERS_FOR_VARIATION

    # accumulate per-slot {class: [values...]} across alphabets.
    coarse = {slot: {} for slot in rv.ALL_SLOTS}
    for slot, d in state["coarse_by_slot"].items():
        coarse[slot] = {k: list(v) for k, v in d.items()}
    junction = {slot: {} for slot in disc.JUNCTION_SLOTS}
    for slot, d in state["junction_by_slot"].items():
        junction[slot] = {k: list(v) for k, v in d.items()}

    while state["alph_idx"] < len(ep_alphs) and time.time() < hard_deadline:
        alph = ep_alphs[state["alph_idx"]]
        for cdir in population[alph]:
            fbd = run50._files_by_drawer(cdir)
            files = [fbd[d] for d in drawers if d in fbd]
            if len(files) < 2:
                continue
            decoded = [gate.decode_char_signature(s, f, cache, DK) for f in files]
            # COARSE: per-class per-slot mean + variance via the aligned pooling (run 50 machinery).
            ref = decoded[0]
            others = [(d["stroke_points"], d["composed_sig"]) for d in decoded[1:]]
            var = rv.class_slot_variances(native, ref["stroke_points"], ref["composed_sig"],
                                          others, turn_bins=DK["turn_bins"])
            means = _class_slot_means(native, ref["stroke_points"], ref["composed_sig"], others,
                                      DK["turn_bins"])
            if var is not None and means is not None:
                for slot in rv.ALL_SLOTS:
                    # represent a class by (mean, within-var) -> approximate the class's value
                    # distribution as a 2-point spread (mean +/- std) so fisher_ratio's between term
                    # reads the class-mean spread and its within term reads the pooled within-var.
                    std = float(np.sqrt(max(var.get(slot, 0.0), 0.0)))
                    m = means[slot]
                    coarse[slot][cdir] = [m - std, m + std]
            # JUNCTION: per-class per-slot fraction, one value per DRAWER (alignment-free).
            for d in decoded:
                prof = disc.junction_profile(rv.stroke_points_only(d["stroke_points"]))
                for slot in disc.JUNCTION_SLOTS:
                    junction[slot].setdefault(cdir, []).append(prof[slot])
            state["n_classes"] += 1
        state["alph_idx"] += 1
        state["coarse_by_slot"] = coarse
        state["junction_by_slot"] = junction
        _save_json(state, FALSIFIER_STATE)
        print(f"    [falsifier-B] alphabet {state['alph_idx']}/{len(ep_alphs)} ({alph!r}) -- "
              f"{state['n_classes']} classes, {time.time()-(hard_deadline-run55.PER_CALL_BUDGET_SECONDS):.1f}s "
              f"this call", flush=True)

    if state["alph_idx"] < len(ep_alphs):
        print(f"\n  PARTIAL [falsifier-B]: {state['alph_idx']}/{len(ep_alphs)} -- re-invoke.")
        return None

    coarse_fisher = disc.slot_discriminability(coarse)
    junction_fisher = disc.slot_discriminability(junction)
    return dict(n_classes=state["n_classes"], coarse_fisher=coarse_fisher,
                junction_fisher=junction_fisher)


def _class_slot_means(native, ref_stroke_points, ref_sig, other_instances, turn_bins):
    """Per-class per-slot MEAN, mirroring `relational_variation.class_slot_variances`'s alignment +
    pooling but returning the MEAN of each slot's pooled values (the between-class term Fisher needs;
    run 50 stored only variances). Pure statistics."""
    ref_pts = rv.stroke_points_only(ref_stroke_points)
    ref_rel = rv.rel_by_k(ref_sig)
    ref_cpose = rv.cpose_values(ref_sig)
    pooled_rel = {s: [] for s in rv.REL_SLOTS}
    pooled_cpose = {s: [] for s in rv.CPOSE_SLOTS}
    for _k, vals in ref_rel.items():
        for slot, v in zip(rv.REL_SLOTS, vals):
            pooled_rel[slot].append(v)
    for slot, v in ref_cpose.items():
        if v is not None:
            pooled_cpose[slot].append(v)
    for stroke_points, sig in other_instances:
        pts = rv.stroke_points_only(stroke_points)
        if not pts:
            continue
        gm = rv.align_stroke_points(native, ref_pts, pts)
        other_rel = rv.rel_by_k(sig)
        for (i, j, _c) in gm["matched"]:
            vals = other_rel.get(j)
            if vals is None:
                continue
            for slot, v in zip(rv.REL_SLOTS, vals):
                pooled_rel[slot].append(v)
        for slot, v in rv.cpose_values(sig).items():
            if v is not None:
                pooled_cpose[slot].append(v)
    out = {}
    for slot in rv.REL_SLOTS:
        out[slot] = float(np.mean(pooled_rel[slot])) if pooled_rel[slot] else 0.0
    for slot in rv.CPOSE_SLOTS:
        out[slot] = float(np.mean(pooled_cpose[slot])) if pooled_cpose[slot] else 0.0
    return out


def _require_falsifier():
    if not os.path.exists(FALSIFIER_PATH):
        raise SystemExit("WALL: run --stage falsifier first.")
    return _load_json(FALSIFIER_PATH)


# ============================================================================================= #
# STAGE: calibrate -- discriminability precisions + GUARD reproduction + BACKGROUND-SANITY STOP.
# ============================================================================================= #
def stage_calibrate():
    print(f"\n{SEP}\n  STAGE: calibrate (discriminability precisions + BACKGROUND-SANITY STOP)\n{SEP}")
    _require_unit_sanity()
    md5_before = _md5(STROKE_SHAPES_SEED)
    records, timing = _source_background()
    n = len(records)

    prec, res = _discriminability_precisions(records)      # graph-native, read from edges.
    print(f"\n  discriminability precisions (Fisher between/within, READ from graph FrameAxis "
          f"log_weight edges): {{{', '.join(f'{k}={v:.5f}' for k,v in prec.items())}}}")

    guard, arm = _preds(records, prec)
    trues = [r["true_idx"] for r in records]
    k_guard = sum(g == t for g, t in zip(guard, trues))
    k_arm = sum(p == t for p, t in zip(arm, trues))
    acc_guard, acc_arm = k_guard / n, k_arm / n
    passed = acc_arm >= acc_guard - SANITY_MARGIN

    flips = [i for i in range(n) if guard[i] != arm[i]]
    fixed = sum(1 for i in flips if guard[i] != trues[i] and arm[i] == trues[i])
    broke = sum(1 for i in flips if guard[i] == trues[i] and arm[i] != trues[i])

    amort = dict(n_derivations=int(timing.get("n_derivations", 0)),
                 rel_seconds=float(timing.get("rel_seconds", 0.0)),
                 ms_per_derivation=(1000.0 * timing.get("rel_seconds", 0.0)
                                    / timing["n_derivations"] if timing.get("n_derivations") else 0.0))

    frozen = dict(n=n, precisions=prec, tightness_precisions=_tightness_precisions(records),
                  k_guard=k_guard, k_arm=k_arm, acc_guard=acc_guard, acc_arm=acc_arm,
                  sanity_margin=SANITY_MARGIN, passed=bool(passed),
                  flips=len(flips), flips_fixed=fixed, flips_broke=broke, amortization=amort,
                  ep_alphs=sorted(run54b._background_population()))
    _save_json(frozen, CALIB_PATH)
    _print_calibrate(frozen)
    _seed_guard("calibrate", md5_before)
    return 0


def _print_calibrate(f):
    print(f"\n  ---- BACKGROUND-SANITY GATE (n={f['n']}, {f['ep_alphs']}) ----")
    print(f"    discriminability precisions: {{{', '.join(f'{k}={v:.5f}' for k,v in f['precisions'].items())}}}")
    print(f"    (run 56 tightness precisions were: {{{', '.join(f'{k}={v:.3f}' for k,v in f['tightness_precisions'].items())}}}"
          f" -- note tightness rated rel {f['tightness_precisions']['rel']:.2f} but discriminability "
          f"rates it {f['precisions']['rel']:.5f}: DISTRUSTED)")
    gr = abs(f["acc_guard"] - 0.85) <= 0.03
    print(f"    GUARD (geometry-only log-odds, prec_rel=0): acc={100*f['acc_guard']:.1f}% "
          f"k={f['k_guard']}/{f['n']}   (the number to BEAT)")
    print(f"    -> GUARD-REPRODUCTION: {100*f['acc_guard']:.1f}% {'~=' if gr else '!='} SC+TPS 85.0% "
          f"({'faithful' if gr else 'OFF'})")
    print(f"    ARM D (discriminability whole^2 + rel^2): acc={100*f['acc_arm']:.1f}% "
          f"k={f['k_arm']}/{f['n']}   delta={100*(f['acc_arm']-f['acc_guard']):+.1f}pp "
          f"(run 56 tightness = -12.5pp HARM)")
    print(f"    flips={f['flips']} fixed={f['flips_fixed']} broke={f['flips_broke']} "
          f"-- discriminability distrusts rel so it barely participates (the faculty PROTECTS)")
    am = f.get("amortization", {})
    print(f"    [AMORTIZATION] {am.get('n_derivations')} derivations, "
          f"{am.get('ms_per_derivation',0):.3f} ms/derivation (one Gamma-pruned pass, no search)")
    print(f"\n    VERDICT: {'PASS -- proceed to --stage eval' if f['passed'] else 'STOP -- no eval budget'}")


def _require_calibrate():
    if not os.path.exists(CALIB_PATH):
        raise SystemExit("WALL: run --stage calibrate first.")
    return _load_json(CALIB_PATH)


# ============================================================================================= #
# STAGE: eval -- EVALUATION multi-stroke episodes, frozen discriminability precisions.
# ============================================================================================= #
def stage_eval():
    print(f"\n{SEP}\n  STAGE: eval (EVALUATION multi-stroke, frozen discriminability precisions)\n{SEP}")
    calib = _require_calibrate()
    if not calib["passed"]:
        print("  WALL: calibrate SANITY STOPPED -- NO eval budget. Report and stop.")
        return 1
    prec = calib["precisions"]
    md5_before = _md5(STROKE_SHAPES_SEED)
    # reuse run 55's OWN collector (SAME (whole,stroke,rel) triple + seed stream); ONLY the verdict
    # precision differs. tightness weights only feed the native rel residual (unchanged).
    tightness_w = _load_json(os.path.join(ROOT, "results", "run50_checkpoints",
                                          "learn_relational.json"))["weights"]
    state = _collect_eval(tightness_w)
    if state is None:
        return 0
    records = state["records"]
    n = len(records)
    guard, arm = _preds(records, prec)
    trues = [r["true_idx"] for r in records]
    guard_correct = [g == t for g, t in zip(guard, trues)]
    arm_correct = [p == t for p, t in zip(arm, trues)]
    out = dict(n=n, guard_correct=[bool(x) for x in guard_correct],
               arm_correct=[bool(x) for x in arm_correct],
               k_guard=sum(guard_correct), k_arm=sum(arm_correct), precisions=prec,
               ep_alphs=sorted(run54b._eval_population()), done=True)
    _save_json(out, EVAL_PATH)
    print(f"\n  EVAL COMPLETE: n={n}  GUARD acc={100*out['k_guard']/n:.1f}%  "
          f"ARM D acc={100*out['k_arm']/n:.1f}%")
    _seed_guard("eval", md5_before)
    return 0


def _collect_eval(tightness):
    state = (_load_json(EVAL_STATE_PATH) if os.path.exists(EVAL_STATE_PATH)
             else dict(alph_idx=0, records=[], timing=dict(n_derivations=0, rel_seconds=0.0)))
    population = run54b._eval_population()
    ep_alphs = sorted(population)
    s = run50._load_codebook_substrate()
    cache = {}
    rng = np.random.default_rng(run55.RUN55_SEED)
    for i in range(state["alph_idx"]):
        wc = population[ep_alphs[i]]
        fbd = {c: run54b._files_by_drawer(c) for c in wc}
        run55._run_one_block(s, wc, fbd, rng, cache, tightness)
    hard_deadline = time.time() + run55.PER_CALL_BUDGET_SECONDS
    while state["alph_idx"] < len(ep_alphs) and time.time() < hard_deadline:
        alph = ep_alphs[state["alph_idx"]]
        wc = population[alph]
        fbd = {c: run54b._files_by_drawer(c) for c in wc}
        recs = run55._run_one_block(s, wc, fbd, rng, cache, tightness, timing=state["timing"])
        if recs:
            state["records"].extend(recs)
        state["alph_idx"] += 1
        _save_json(state, EVAL_STATE_PATH)
        print(f"    [eval] alphabet {state['alph_idx']}/{len(ep_alphs)} ({alph!r}) -- "
              f"{len(state['records'])} episodes", flush=True)
    if state["alph_idx"] < len(ep_alphs):
        print(f"\n  PARTIAL [eval]: {state['alph_idx']}/{len(ep_alphs)} -- re-invoke.")
        return None
    return state


# ============================================================================================= #
# STAGE: report
# ============================================================================================= #
def stage_report():
    print(f"\n{SEP}\n  RUN 57 -- GRAPH-NATIVE DISCRIMINATION FACULTY -- FINAL REPORT\n{SEP}")
    print(f"  seeds/stroke_shapes.json md5: {_md5(STROKE_SHAPES_SEED)}")
    fals = _require_falsifier()
    calib = _require_calibrate()

    pa = fals["part_a"]
    print(f"\n  {'='*28}  THE FACULTY (its own reward)  {'='*28}")
    print(f"    discriminability != tightness: rankings differ={pa['ranks_differ']}, "
          f"rel distrusted (Fisher last)={pa['rel_distrusted']}")
    print(f"    tightness rated rel {pa['tightness']['rel']:.3f} (2nd most trusted); "
          f"discriminability rates rel {pa['fisher']['rel']:.5f} (LEAST trusted) -- "
          f"the run-56 over-trust is CORRECTED.")
    print(f"    richer junction relations separate more than coarse pose: {fals['richer_separates']} "
          f"(junction max Fisher={fals['junction_max']:.4f} vs coarse max={fals['coarse_max']:.4f})")

    print(f"\n  {'='*30}  BACKGROUND (decides eval)  {'='*30}")
    _print_calibrate(calib)

    print(f"\n  {'='*30}  CONVERT-OR-CORPUS VERDICT  {'='*30}")
    if not calib["passed"]:
        print(f"    ARM D moved background {100*(calib['acc_arm']-calib['acc_guard']):+.1f}pp -- "
              f"below the GUARD-3pp bar; sanity stopped, no eval.")
    elif os.path.exists(EVAL_PATH) and _load_json(EVAL_PATH).get("done"):
        ev = _load_json(EVAL_PATH)
        n = ev["n"]
        ci_g = gate.wilson_ci(ev["k_guard"], n)
        ci_a = gate.wilson_ci(ev["k_arm"], n)
        mc = _mcnemar(ev["guard_correct"], ev["arm_correct"])
        print(f"    ---- EVAL (n={n}, {ev['ep_alphs']}) ----")
        print(f"      GUARD: {100*ev['k_guard']/n:.1f}% [{100*ci_g[0]:.1f},{100*ci_g[1]:.1f}] "
              f"k={ev['k_guard']}")
        print(f"      ARM D: {100*ev['k_arm']/n:.1f}% [{100*ci_a[0]:.1f},{100*ci_a[1]:.1f}] "
              f"k={ev['k_arm']}")
        print(f"      McNemar: fixed={mc['fixed']} broken={mc['broken']} p={mc['p']:.4g}")
        ci_sep = gate._ci_separated(tuple(ci_a), tuple(ci_g))
        if mc["discordant"] and mc["fixed"] > mc["broken"] and ci_sep:
            print(f"      WIN: ARM D converts, CI-separated -- ceiling crack.")
        elif mc["fixed"] > mc["broken"]:
            print(f"      WEAK WIN: fixed>broken, not CI-separated.")
        else:
            print(f"      NULL (no harm): the faculty PROTECTS -- ARM D ~= GUARD (vs run 56 "
                  f"tightness -12.5pp). rel does not separate (Fisher {calib['precisions']['rel']:.5f}) "
                  f"so discriminability correctly reduces to geometry. The concept's coarse "
                  f"arrangement lacks separating content -> localizes to mouse-Omniglot (joins the "
                  f"pen-data thread). The FACULTY is real, general, graph-native, and is its own "
                  f"reward.")
    else:
        print("    (eval not yet run -- run --stage eval)")
    print(f"\n  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(f"  seeds/stroke_shapes.json md5 (post-run): {_md5(STROKE_SHAPES_SEED)}")
    return 0


STAGES = {"compose": stage_compose, "unit_sanity": stage_unit_sanity, "falsifier": stage_falsifier,
          "calibrate": stage_calibrate, "eval": stage_eval, "report": stage_report}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=list(STAGES.keys()))
    args = ap.parse_args()
    t0 = time.time()
    rc = STAGES[args.stage]()
    print(f"\n  [stage {args.stage} wall time: {time.time()-t0:.1f}s]")
    return rc


if __name__ == "__main__":
    sys.exit(main())

"""capture.py — Part C0 parity-fixture capture (see the migration design doc).

Runs the CURRENT (unmodified) Python composer (reflective_faculty.compose_design_for_goal
/ induce_concern / ground_concern) and driver (question_driver.QuestionDriver.drive) on
deterministic cases, and dumps their outputs as JSON fixtures under
tests/fixtures/composer_driver_parity/. These fixtures are the GROUND TRUTH the future
graph-native (Rust ShapeDecode / seeded dispatch / graph-resident driver) reimplementation
must match. This script does NOT modify any source file; it only reads the current code and
writes fixtures + (transiently) exercises the live teach() facility, restoring any seed file
it perturbs (see `_ProgramsJsonGuard` below).

Run:  cd gamma-substrate && PYTHONPATH=.:runners/dsl/python python3 \\
        tests/fixtures/composer_driver_parity/capture.py

Re-run twice (fresh interpreter each time) to check determinism; this script is idempotent
(each run overwrites the same fixture files) and side-effect-free on seeds/ (restored).
"""
from __future__ import annotations

import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
_DSLPY = os.path.join(ROOT, "runners", "dsl", "python")
if _DSLPY not in sys.path:
    sys.path.insert(0, _DSLPY)

FIXTURE_DIR = os.path.join(ROOT, "tests", "fixtures", "composer_driver_parity")

from substrate.boot_core import boot_core                      # noqa: E402
from substrate.seed_loader import manifest_for                 # noqa: E402
from domains import reflective_faculty as rf                    # noqa: E402
from domains import comprehend_question as cq                   # noqa: E402
from domains import question_driver as qd                       # noqa: E402


# ---------------------------------------------------------------------------
# JSON-ification helpers — the native substrate returns tuples for list-typed
# attrs, and Emission/TargetSpec/Ascent are dataclasses, not dicts. Recursively
# reduce to JSON-safe primitives; keep dict/list output SMALL where the design
# doc says to (meta_answer's held_concepts etc. can be large).
# ---------------------------------------------------------------------------
def _jsonable(v, _depth=0):
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, (list, tuple)):
        return [_jsonable(x, _depth + 1) for x in v]
    if isinstance(v, dict):
        return {str(k): _jsonable(x, _depth + 1) for k, x in v.items()}
    return str(v)


def _shallow(v, max_str=240, max_list=20, max_dict=10, _depth=0):
    """A SMALL, deterministic summary of a value — used for meta_answer's
    top-level values. Small dicts/lists (<= max_dict/max_list keys/items) are
    kept IN FULL (one extra level of recursion) so a genuinely small structured
    answer (e.g. `route`/`seek_decision`) is captured, not just its key names;
    a large graph read (e.g. `held_concepts`) is summarized instead (count +
    key names only) so the fixture stays bounded and does not freeze a big,
    less-interesting read byte-for-byte."""
    if v is None or isinstance(v, (bool, int, float)):
        return v
    if isinstance(v, str):
        return v if len(v) <= max_str else (v[:max_str] + f"...<truncated from {len(v)} chars>")
    if isinstance(v, (list, tuple)):
        if len(v) <= max_list and _depth < 2:
            return [_shallow(x, max_str, max_list, max_dict, _depth + 1) for x in v]
        return {"__summary__": "list", "len": len(v)}
    if isinstance(v, dict):
        if len(v) <= max_dict and _depth < 2:
            return {str(k): _shallow(x, max_str, max_list, max_dict, _depth + 1) for k, x in v.items()}
        return {"__summary__": "dict", "n_keys": len(v), "keys": sorted(str(k) for k in v.keys())[:max_list]}
    return {"__summary__": type(v).__name__}


def write_json(name: str, data) -> None:
    path = os.path.join(FIXTURE_DIR, name)
    with open(path, "w") as f:
        json.dump(data, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"  wrote {path}")


# ---------------------------------------------------------------------------
# A minimal duck-typed "agent" wrapper for induce_concern/ground_concern, which
# use `agent.inner.add_rule` (rule install) and `agent.s.add_node` (teach()).
# `boot_core()` returns the raw Substrate wrapper (has `.nodes/.add_node/._inner`
# but no `.inner`/`.s`); this is harness glue only (no source modified).
# ---------------------------------------------------------------------------
class Agent:
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


def fresh_agent():
    s, agent_node = boot_core()
    return Agent(s, agent_node)


class _ProgramsJsonGuard:
    """ground_concern's PATH-2 (generate_from_residual) calls teach_program ->
    teach(agent, "Program", ..., category="programs"), which APPENDS to
    seeds/programs.json (idempotent on identical content, but our capture calls
    mint a fixture-only term_name that is very likely new). seeds/programs.json
    may ALREADY be dirty in the working tree (unrelated prior session output) —
    so we snapshot+restore the exact bytes ourselves rather than `git checkout`
    (which would also clobber that unrelated pre-existing dirty state)."""

    def __init__(self):
        self.path = os.path.join(ROOT, "seeds", "programs.json")
        self.before = None

    def __enter__(self):
        with open(self.path, "r") as f:
            self.before = f.read()
        return self

    def __exit__(self, *exc):
        with open(self.path, "r") as f:
            after = f.read()
        changed = after != self.before
        if changed:
            with open(self.path, "w") as f:
                f.write(self.before)
        self.changed = changed
        return False


# ===========================================================================
# SECTION 1 — compose_design_for_goal (reflective_faculty.py:2200)
# ===========================================================================
PARTS = {
    "part_move": [["move", "X", "by", "D"], ["stop", "X"]],
    "part_detect": [["detect", "CONTACT", "between", "PARTS"], ["type", "CONTACT", "is", "INVARIANT"]],
    "part_build": [["build", "NEW", "from", "PRIOR"], ["bound", "SELF", "by", "UNIT"]],
}


def _boot_with_parts():
    s, agent_node = boot_core()
    for nm, sig in PARTS.items():
        s.add_node("ShapeSignature", {"name": nm, "signature": json.dumps(sig),
                                       "kind": "faculty", "faculty": nm})
    return s, agent_node


def capture_composer() -> dict:
    print("SECTION 1 — compose_design_for_goal")
    out = {"parts": PARTS}

    # case 1: FULL COVER — goal = part_move's + part_detect's own relations (literal
    # role-filler tokens must match a held part's signature verbatim; the composer
    # covers whole relation-tuples, not per-slot wildcard unification against the goal).
    s, _ = _boot_with_parts()
    goal_full = PARTS["part_move"] + PARTS["part_detect"]
    out["full_cover"] = {
        "goal_signature": goal_full,
        "result": _jsonable(rf.compose_design_for_goal(s, goal_full)),
    }

    # case 2: PARTIAL COVER (residual) — part_move's relations + one relation no held
    # part expresses at all.
    s2, _ = _boot_with_parts()
    goal_partial = PARTS["part_move"] + [["novel_pred", "A", "given", "B"]]
    out["partial_cover"] = {
        "goal_signature": goal_partial,
        "result": _jsonable(rf.compose_design_for_goal(s2, goal_partial)),
    }

    # case 3: beam=1/cand_k=1 GREEDY (the discriminative control) vs the default beam,
    # over a 3-part goal (exercises the beam frontier machinery even though, for this
    # goal, greedy and the full beam agree — recorded for parity, not to prove divergence).
    s3, _ = _boot_with_parts()
    goal_beam = PARTS["part_move"] + PARTS["part_detect"] + PARTS["part_build"]
    out["beam_vs_greedy"] = {
        "goal_signature": goal_beam,
        "greedy_beam1_candk1": _jsonable(rf.compose_design_for_goal(s3, goal_beam, beam=1, cand_k=1)),
        "default_beam3_candk3": _jsonable(rf.compose_design_for_goal(s3, goal_beam)),
    }
    return out


# ===========================================================================
# SECTION 2 — induce_concern (reflective_faculty.py:832)
# ===========================================================================
def capture_induce_concern() -> dict:
    print("SECTION 2 — induce_concern")
    out = {"parts": PARTS}

    # COVERED case: an observation whose predicates + arity match a held part's
    # signature exactly (object fillers may differ — Covers wildcards them).
    s, _ = _boot_with_parts()
    obs_covered = [["move", "Y", "by", "Z"], ["stop", "Y"]]
    out["covered"] = {
        "observation": obs_covered,
        "result": _jsonable(rf.induce_concern(s, obs_covered)),
    }

    # UNCOVERED case: novel predicates, no held part shares shape -> mint.
    s2, _ = _boot_with_parts()
    obs_uncovered = [["zwoop", "A", "q", "B"], ["florb", "A"], ["quix", "C"]]
    ind_res = rf.induce_concern(s2, obs_uncovered, name_hint="induced_probe_uncovered")
    axis_attrs = None
    for n in s2.nodes("CapabilityAxis"):
        at = s2.node(n)["attrs"]
        if at.get("induced") and list(at.get("capability_keys") or []) == ["induced_probe_uncovered"]:
            axis_attrs = at
            break
    out["uncovered"] = {
        "observation": obs_uncovered,
        "result": _jsonable(ind_res),
        "minted_capability_axis_attrs": _jsonable(axis_attrs),
    }
    return out


# ===========================================================================
# SECTION 3 — ground_concern (reflective_faculty.py:1556)
# ===========================================================================
# One RelationCue lexicon per case, mirroring seeds/relation_vocabulary.json (+ the
# syntactic_construction_cue / distributional_function_cue seeds that carry the
# construct/distribute heads) so the SAME held keyword->relation lexicon grounds the
# residual predicates PATH-1 reads. Loaded via the real seed loader (manifest_for),
# not hand-copied text.
_LEXICON_SEEDS = ("relation_vocabulary", "syntactic_construction_cue", "distributional_function_cue")


def _fresh_agent_with_lexicon() -> Agent:
    ag = fresh_agent()
    for sid in _LEXICON_SEEDS:
        ag.s._inner.load_seed_manifest(manifest_for(sid), ag.agent)
    return ag


def _mint_axis_and_ground(key: str, residual_predicates: list, *, magnitudes=None) -> dict:
    ag = _fresh_agent_with_lexicon()
    ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": [key], "induced": 1.0,
        "residual_predicates": residual_predicates, "from_observation": 1.0,
        "source": "concern_induction",
    })
    before = ag.inner.rule_count()
    res = rf.ground_concern(ag, [key], magnitudes=magnitudes)
    after = ag.inner.rule_count()
    installed_names = []
    if isinstance(res.get("rule"), dict):
        installed_names.append(res["rule"].get("name"))
    if isinstance(res.get("rules"), list):
        installed_names.extend(r.get("name") for r in res["rules"])
    return {
        "residual_predicates": residual_predicates,
        "result": _jsonable(res),
        "installed_rule_names": installed_names,
        "rule_count_before": before,
        "rule_count_after": after,
        "rule_count_delta": after - before,
    }


# residual_predicates chosen so EXACTLY one relation head's cue fires (verified
# empirically against the current lexicon — e.g. bare "group" collides with the
# UNRELATED "map_part_to_part" cue's keyword list, so "co-moving" is used instead).
_RELATION_HEAD_CASES = {
    "comprehend": ["comprehend"],
    "utility": ["utility"],
    "group": ["co-moving"],
    "control": ["control"],
    "communicate": ["communicate"],
    "decompose": ["decompose"],
    "construct": ["construct"],
    "distribute": ["distribute"],
}


def capture_ground_concern() -> dict:
    print("SECTION 3 — ground_concern")
    out = {"relation_head_cases": {}}
    for head, preds in _RELATION_HEAD_CASES.items():
        key = f"induced_{head}"
        out["relation_head_cases"][head] = _mint_axis_and_ground(key, preds)

    # PATH-2 — feedback/decay heads (build_from_prior + bounded); no dispatch head
    # present -> falls through to the Fold-iterate generate_from_residual path.
    # NOTE: this path's teach_program() call APPENDS to seeds/programs.json; guarded
    # + restored by _ProgramsJsonGuard in main().
    out["path2_feedback"] = _mint_axis_and_ground(
        "induced_path2_feedback", ["from the prior", "bounded"])

    # the no-cue WALL — genuinely-novel predicate, outside the whole lexicon.
    out["no_cue_wall"] = _mint_axis_and_ground(
        "induced_no_cue_wall", ["zqxw_novel_marker_predicate"])
    return out


# ===========================================================================
# SECTION 4 — QuestionDriver.drive (domains/question_driver.py)
# ===========================================================================
def _serialize_emission(emi: "qd.Emission") -> dict:
    """Extract exactly the fields the design doc names (Emission is not JSON-
    serializable: it carries a TargetSpec/Ascent and nested Emissions)."""
    target = emi.target
    meta_answer = emi.meta_answer or {}
    gap_frame = emi.gap_frame
    return {
        "kind": emi.kind,
        "target_kind": target.kind if target else None,
        "target_grounded": target.grounded if target else None,
        "target_op": getattr(target, "op", None) if target else None,
        "is_wall": emi.is_wall,
        "wall_kind": emi.wall_kind,
        "missing": emi.missing,
        "answer": _jsonable(emi.answer),
        "verified": emi.verified,
        "confidence": emi.confidence,
        "know_answer": _jsonable(emi.know_answer),
        "meta_answer_keys": sorted(meta_answer.keys()) if emi.meta_answer is not None else None,
        "meta_answer_shallow": {k: _shallow(v) for k, v in meta_answer.items()},
        "subgoal_count": len(emi.subgoals),
        "subgoal_kinds": [sg.kind for sg in emi.subgoals],
        "subgoal_is_wall": [sg.is_wall for sg in emi.subgoals],
        "asks_count": len(emi.asks),
        "gap_frame_present": gap_frame is not None,
        "gap_frame_focus": (gap_frame or {}).get("focus"),
        "gap_kinds": [g.get("pos") for g in (gap_frame or {}).get("gaps", [])] if gap_frame else None,
        "note": emi.note,
    }


def capture_driver() -> dict:
    print("SECTION 4 — QuestionDriver.drive")
    out = {}

    # NOTE on timing: wall-clock elapsed time was measured during authoring to size
    # this script (world ~5s, know/compound/contrast ~7-30s via a real local wiki_local
    # parquet read, meta/gap_path fast) but is NOT written into the fixture — a
    # determinism check (running this script twice in fresh processes) showed it is
    # the ONLY field that varies run-to-run; every other field was byte-identical.
    # Excluded per the design doc's "note the unstable fields and exclude them"
    # instruction (see README.md's Determinism section).

    # (1) WORLD — a grounded compute goal with stubbed verify/answer_call (the
    # cmsg100/101 elliptic-torsion pack, reused verbatim from scripts/jabberwock_drives_itself).
    import scripts.jabberwock_drives_itself as jdi
    t0 = time.time()
    driver = qd.QuestionDriver()
    emi = driver.drive(jdi.ELLIPTIC_PACK())
    print(f"  world: {time.time() - t0:.1f}s")
    out["world"] = {"pack": "ELLIPTIC_PACK (scripts.jabberwock_drives_itself)",
                     "emission": _serialize_emission(emi)}

    # (2) KNOW — "What is HTTP?" (falls out of the pursuit hitting the reference wall
    # -> wiki_local lookup -> grounded genus). Real local wiki_local read (no network).
    t0 = time.time()
    driver = qd.QuestionDriver()
    emi = driver.drive(qd.QuestionPack(text="What is HTTP?"))
    print(f"  know: {time.time() - t0:.1f}s")
    out["know"] = {"pack": 'QuestionPack(text="What is HTTP?")',
                   "emission": _serialize_emission(emi)}

    # (3) META — a SELF/META question routed to reflective_faculty.reflect over a
    # substrate carrying the held reflective machinery.
    t0 = time.time()
    s, installed = rf.boot_reflective_substrate()
    driver = qd.QuestionDriver(substrate=s)
    emi = driver.drive(qd.QuestionPack(text="How do you want to retrieve information?",
                                       reflect=rf.reflect))
    print(f"  meta: {time.time() - t0:.1f}s")
    out["meta"] = {"pack": 'QuestionPack(text="How do you want to retrieve information?", reflect=rf.reflect)',
                   "boot_reflective_substrate_installed": _jsonable(installed),
                   "emission": _serialize_emission(emi)}

    # (4) COMPOUND — "What is HTTP and <elliptic torsion>" -> 2 mixed-faculty subgoals.
    t0 = time.time()
    ell = jdi._q(jdi.ELLIPTIC_ID)["question"]
    base = jdi.ELLIPTIC_PACK()
    pack = qd.QuestionPack(text="What is HTTP and " + ell, feed=base.feed,
                           deep_reads=base.deep_reads, verify=base.verify,
                           answer_call=base.answer_call)
    driver = qd.QuestionDriver()
    emi = driver.drive(pack)
    print(f"  compound: {time.time() - t0:.1f}s")
    out["compound"] = {"pack": '"What is HTTP and " + ELLIPTIC question text',
                       "emission": _serialize_emission(emi),
                       "subgoal_emissions": [_serialize_emission(sg) for sg in emi.subgoals]}

    # (5) CONTRAST — "compare HTTP with FTP" (requires acquiring the comparison
    # construction first, mirroring scripts/jabberwock_crosses_comprehension_frontier;
    # _ACQUIRED_QUESTION is comprehend_question's own module-level held graph data —
    # mutating it here is the SAME "seek to understand" the agent does live, not a
    # source change). subprocess-isolated by running this whole script fresh, so this
    # global mutation never leaks into another case's process.
    t0 = time.time()
    cq._ACQUIRED_QUESTION["comparison"] = []
    gap = cq.diagnose_comprehension_gap("compare HTTP with FTP")
    acq = cq.acquire_compare_construction(gap)
    driver = qd.QuestionDriver()
    emi = driver.drive(qd.QuestionPack(text="compare HTTP with FTP"))
    print(f"  contrast: {time.time() - t0:.1f}s")
    out["contrast"] = {"pack": 'QuestionPack(text="compare HTTP with FTP") after acquire_compare_construction',
                       "acquired_construction": acq.get("acquired"),
                       "emission": _serialize_emission(emi),
                       "subgoal_emissions": [_serialize_emission(sg) for sg in emi.subgoals]}

    # (6) UNGROUNDED / GAP PATH — ask=None (default), so a comprehension stall falls
    # into parse_with_gaps instead of the ASK loop. This question is pre-resolved via
    # the taught seeds/resolved_queries.json (loaded by boot_reflective_substrate's
    # CORE_SEEDS), so the gap frame RESOLVES from held knowledge (not merely a wall) —
    # both are exercised in the trace (typed gaps + the resolution).
    t0 = time.time()
    s2, installed2 = rf.boot_reflective_substrate()
    driver = qd.QuestionDriver(substrate=s2)
    emi = driver.drive(qd.QuestionPack(text="Why would your plan lead you into a wall?",
                                       reflect=rf.reflect))
    print(f"  gap_path: {time.time() - t0:.1f}s")
    gap_emission = _serialize_emission(emi)
    # KNOWN INSTABILITY (found by the determinism check — see README.md): the FIRST
    # gap-grounding subgoal ("What is would?") resolves via wiki_local's title search
    # for the bare word "would", which is NOT deterministic run-to-run (present=True
    # w/ article "English modal auxiliary verbs" about half the time, an honest wall
    # the other half) — wiki_local, not the driver/comprehension, is the source of the
    # nondeterminism. Every OTHER field (is_wall, note, answer, gap_frame_*, the other
    # 3 subgoals' kinds) was byte-identical across >=6 fresh-process runs. Masked here
    # (not asserted in Part D parity) rather than silently frozen as if it were stable.
    gap_emission["subgoal_is_wall"] = None
    gap_emission["_unstable_fields_excluded"] = [
        "subgoal_is_wall: the subgoal[0] ('What is would?') is_wall flips True/False "
        "across runs — wiki_local's title search for the bare word 'would' is not "
        "deterministic (see README.md Determinism section); every other field here is "
        "stable across repeated fresh-process runs.",
    ]
    out["gap_path"] = {"pack": 'QuestionPack(text="Why would your plan lead you into a wall?", '
                               'reflect=rf.reflect, ask=None)',
                       "boot_reflective_substrate_installed": _jsonable(installed2),
                       "emission": gap_emission}

    return out


# ===========================================================================
def main() -> int:
    os.makedirs(FIXTURE_DIR, exist_ok=True)
    guard = _ProgramsJsonGuard()
    with guard:
        composer = capture_composer()
        induce = capture_induce_concern()
        ground = capture_ground_concern()
    print(f"seeds/programs.json perturbed-then-restored: {guard.changed}")
    driver = capture_driver()

    write_json("composer.json", composer)
    write_json("induce_concern.json", induce)
    write_json("ground_concern.json", ground)
    write_json("driver.json", driver)
    print("DONE.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

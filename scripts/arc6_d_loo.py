#!/usr/bin/env python3
"""arc6_d_loo.py -- THE DISCRIMINATING MEASUREMENT for Arc6 Seam D.

Seam D (`PROGRAM_SYNTHESIS_ARC6_D.md`, HEAD 9c54925d75) reports 36/36
(100%) self-detected wrongness on the frozen 36-task residual and 61/104
(58.7%) on the arc-4 denominator. THAT HEADLINE IS AUTHORING-BOUND:
`seeds/program_properties.json` holds EXACTLY ONE PropertyAtom per residual
task, each with hand-constructed witnesses, so the property table encodes
the answers for precisely the population it is scored on. This script
measures how much of the 36 is a PROPERTY (transfers) and how much is a
per-task LOOKUP KEY (does not).

Four measurements, all reported as PAIRED ID LISTS, never bare counts:

  M1  LEAVE-ONE-OUT (decisive). For each of the 36 residual tasks: disable
      THAT TASK'S OWN atom, leave the other 35 active, re-run the verdict
      through the REAL seed rules (`psy.pump`). Does any FOREIGN atom
      refute it?
  M2  FALSE-REFUTATION SWEEP, WIDENED. All 36 atoms against the FULL
      257-task runnable split (`results/arc5_final.json`, the settled
      arc-5 measurement), and in particular against its 35 currently-
      PASSING tasks. Any atom refuting a correct program would reduce
      35/257.
  M3  CROSS-TASK FIRING. Independent of correctness: on how many of the
      257 does any atom cue-match / become applicable / actually refute?
      Atoms that only reach their own 36 authored tasks are lookup keys.
  M4  THE HONEST 58.7%. The arc-4 S5 denominator (`results/arc4_endgame.
      json` `no_structural` arm's 104 `accepted_holdout_fail` rows),
      replayed in THREE arms: property atoms OFF (the structural-only
      control, arc4 S5's own 26/104), FULL atom table (Seam D's 61/104),
      and LEAVE-ONE-OUT. The LOO figure is the transferable claim.

METHOD. Every measurement REPLAYS a frozen accepted candidate's IR into a
fresh minimal goal and runs the REAL seed rules -- the identical harness
`tests/test_prog_property_migrated.py` uses (`_fresh_goal`/`_add_row`/
`_reflect_and_verify`/`psy.pump`). NOTHING built by Seam D is modified:
the atom table is filtered IN THE MEASURING PROCESS by rebinding
`prog_property.load_property_atoms`, and `seeds/program_properties.json`,
`domains/prog_property.py` and the seed rules are read-only here.

CONTAMINATION. Held-out rows never enter any detection path: goals are
ingested with REVEALED rows only (`arc4_failure_anatomy._revealed_rows_
for_task`, PRIMARY protocol). Held-out data is read for MEASUREMENT
LABELS only (the frozen artifacts' own `outcome` field) and never reaches
a property, a witness, or a codebook.

ISOLATION. Run from a clean `git worktree` at committed HEAD with this
tree's own `_native.abi3.so` copied in (a concurrent agent live-editing a
shared tree already broke one measurement in this project).

Deterministic: fixed task order, one fresh substrate per goal, no RNG.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

#  §10 rule 3 -- MANDATORY for a non-pytest entrypoint: pin `import
#  substrate_rs` to THIS TREE's own engine before anything imports it.
#  Without this the site-packages `.pth` silently resolves the CANONICAL
#  tree's binary, which is exactly the isolation failure this measurement
#  exists to avoid.
from domains.engine_provenance import engine_preamble  # noqa: E402

engine_preamble()

import substrate_rs as srs  # noqa: E402
import mbpp_arc3_battery as bat  # noqa: E402
import arc4_failure_anatomy as afa  # noqa: E402

from domains import prog_synthesis as psy  # noqa: E402
from domains import prog_property as pp  # noqa: E402

FROZEN_R3_PATH = os.path.join(ROOT, "results", "mbpp_arc3_endgame.json")
ARC4_PATH = os.path.join(ROOT, "results", "arc4_endgame.json")
ARC5_PATH = os.path.join(ROOT, "results", "arc5_final.json")
FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")
PROPERTY_SEED_PATH = os.path.join(ROOT, "seeds", "program_properties.json")
OUT_PATH = os.path.join(ROOT, "results", "arc6_d_loo.json")

#  The frozen honest structural residual -- Seam D's own headline
#  population (PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md), quoted
#  verbatim from tests/test_prog_property_migrated.py::RESIDUAL_36.
RESIDUAL_36 = [17, 56, 67, 72, 77, 79, 91, 96, 105, 113, 143, 165, 167, 171,
               224, 235, 238, 244, 250, 256, 268, 279, 291, 292, 295, 300,
               311, 388, 389, 392, 405, 441, 444, 452, 453, 455]


# --------------------------------------------------------------------------- #
#  the replay harness -- verbatim from tests/test_prog_property_migrated.py
# --------------------------------------------------------------------------- #
def _fresh_goal(*, construction: str = "retrieved_exemplar", attempts: float = 1.0,
                budget: float = 5.0):
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    psy.ensure_program_synthesis(s, s._inner, ag)
    g = s.add_node("Goal", {
        "kind": "synth_program", "status": "evaluated",
        "ps_attempts": attempts, "ps_budget": budget,
        "ps_depth": 0.0, "ps_construction": construction,
        "ps_reflect_ok": 1.0,
    })
    s.add_edge_unchecked(ag, "has_goal", g)
    m = s.add_node("Message", {"text": ""})
    s.add_edge_unchecked(g, "about_message", m)
    s.add_edge_unchecked(ag, "received", m)
    return s, ag, g, m


def _add_row(s, m, inputs: Dict[str, Any], expected: Any, *, attempt: float = 1.0):
    r = s.add_node("ExampleRow", {
        "inputs_json": json.dumps(inputs), "expected": expected,
        "eval_attempt": attempt, "verdict_attempt": -1.0,
        "eval_ok": 1.0, "got": expected, "ce_attempt": -1.0,
    })
    s.add_edge_unchecked(m, "has_example", r)
    return r


def _run_goal(ir, prompt, revealed, *, construction="retrieved_exemplar"):
    s, ag, g, m = _fresh_goal(construction=construction)
    s.set_attr(m, "text", prompt)
    for rr in revealed:
        _add_row(s, m, rr["inputs"], rr["expected"])
    root = s._inner.add_term_subgraph(ir)
    s.add_edge_unchecked(g, "ps_ir_reflected", root)
    s.set_attr(g, "ps_ir", json.dumps(ir))
    psy.pump(s, ag)
    return psy.read_goal(s, g)


# --------------------------------------------------------------------------- #
#  the ONLY intervention: which atoms the (unmodified) faculty may see.
#  `compute_property_facts` resolves `load_property_atoms` out of its own
#  module globals at call time, so rebinding it here filters the table
#  WITHOUT touching seeds/program_properties.json on disk.
# --------------------------------------------------------------------------- #
_ALL_ATOMS: List[dict] = []


def _install_atoms(atoms: List[dict]) -> None:
    pp.load_property_atoms = lambda *a, **k: list(atoms)


def _atoms_except_hint(hint: Optional[int]) -> List[dict]:
    return [a for a in _ALL_ATOMS if a.get("task_hint") != hint]


def _verdict(row_ir, prompt, revealed, construction) -> Dict[str, Any]:
    r = _run_goal(row_ir, prompt, revealed, construction=construction)
    return {
        "any_fired": r["property"]["any_fired"],
        "fired_properties": r["property"]["fired_properties"],
        "witnesses": r["property"]["witnesses"],
        "property_reject": r["property"]["reject"],
        "structural_reject": r["structural"]["reject"],
        "status": r["status"],
        "gap_reason": r["gap_reason"],
        "program_minted": r["program"] is not None,
    }


def _sha(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# --------------------------------------------------------------------------- #
#  M3 helpers -- cue-match / applicability WITHOUT any candidate program.
#  `applicable` is exactly the faculty's own pre-execution gate:
#  `_phrases_match(prompt)` AND `_self_verify_atom(atom, revealed rows)`
#  (which itself carries the `arg_count` guard).
# --------------------------------------------------------------------------- #
def _atom_reach(prompt: str, rows: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    cue, applicable = [], []
    for atom in _ALL_ATOMS:
        if not pp._phrases_match(prompt, atom.get("phrases", [])):  # noqa: SLF001
            continue
        cue.append(atom["id"])
        if pp._self_verify_atom(atom, rows):  # noqa: SLF001
            applicable.append(atom["id"])
    return {"cue_match": cue, "applicable": applicable}


def main() -> None:
    t0 = time.time()
    global _ALL_ATOMS

    with open(FIXTURE_PATH) as f:
        all_tasks = json.load(f)
    tasks_by_id = {t["task_id"]: t for t in bat.q0_split_tasks(all_tasks)["test"]}

    with open(FROZEN_R3_PATH) as f:
        frozen_r3 = json.load(f)
    with open(ARC4_PATH) as f:
        arc4 = json.load(f)
    with open(ARC5_PATH) as f:
        arc5 = json.load(f)
    with open(PROPERTY_SEED_PATH) as f:
        _ALL_ATOMS = json.load(f)["property_atoms"]

    hint_by_atom = {a["id"]: a.get("task_hint") for a in _ALL_ATOMS}

    r3_rows = {r["task_id"]: r for r in frozen_r3["arms"]["full_r3"]["runnable_rows"]}
    arc4_rows = {r["task_id"]: r for r in arc4["arms"]["no_structural"]["runnable_rows"]}
    arc5_rows = {r["task_id"]: r for r in arc5["arm"]["runnable_rows"]}

    revealed_cache: Dict[int, List[Dict[str, Any]]] = {}

    def revealed(tid: int):
        if tid not in revealed_cache:
            revealed_cache[tid] = afa._revealed_rows_for_task(tid, tasks_by_id)  # noqa: SLF001
        return revealed_cache[tid]

    out: Dict[str, Any] = {
        "_README": (
            "Arc6 Seam D discriminating measurement. Seam D's 36/36 headline is "
            "authoring-bound (one PropertyAtom per residual task, scored on that "
            "same population). M1 LEAVE-ONE-OUT is the decisive number: it is what "
            "survives when a task's OWN atom is removed. Every figure here is a "
            "paired id list, never a bare count."),
        "head": os.popen("git -C %s rev-parse HEAD" % ROOT).read().strip(),
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "engine": {
            "so": "runners/dsl/python/substrate_rs/_native.abi3.so",
            "sha256": _sha(os.path.join(
                ROOT, "runners/dsl/python/substrate_rs/_native.abi3.so")),
        },
        "inputs": {
            "property_seed_sha256": _sha(PROPERTY_SEED_PATH),
            "prog_property_py_sha256": _sha(os.path.join(ROOT, "domains", "prog_property.py")),
            "frozen_r3_sha256": _sha(FROZEN_R3_PATH),
            "arc4_endgame_sha256": _sha(ARC4_PATH),
            "arc5_final_sha256": _sha(ARC5_PATH),
        },
        "n_atoms": len(_ALL_ATOMS),
        "residual_36": RESIDUAL_36,
    }

    # ------------------------------------------------------------------ #
    #  M1 -- LEAVE-ONE-OUT over the frozen 36-task residual.
    # ------------------------------------------------------------------ #
    m1_full: Dict[int, Dict[str, Any]] = {}
    m1_loo: Dict[int, Dict[str, Any]] = {}
    for tid in RESIDUAL_36:
        row = r3_rows[tid]
        prompt = tasks_by_id[tid]["prompt"]
        rows = revealed(tid)
        cons = row.get("construction") or "retrieved_exemplar"

        _install_atoms(_ALL_ATOMS)
        m1_full[tid] = _verdict(row["ir"], prompt, rows, cons)

        _install_atoms(_atoms_except_hint(tid))
        m1_loo[tid] = _verdict(row["ir"], prompt, rows, cons)

    loo_survivors = sorted(t for t in RESIDUAL_36 if m1_loo[t]["any_fired"] == 1.0)
    loo_lost = sorted(t for t in RESIDUAL_36 if m1_loo[t]["any_fired"] != 1.0)
    full_fired = sorted(t for t in RESIDUAL_36 if m1_full[t]["any_fired"] == 1.0)

    out["m1_leave_one_out"] = {
        "_what": ("For each of the 36 residual tasks: that task's OWN atom is "
                  "removed, the other 35 stay active, the verdict is re-run "
                  "through the real seed rules. 'survives' = some FOREIGN atom "
                  "still refutes it."),
        "n_full_table_fired": len(full_fired),
        "full_table_fired_ids": full_fired,
        "n_loo_survives": len(loo_survivors),
        "loo_survives_ids": loo_survivors,
        "n_loo_lost": len(loo_lost),
        "loo_lost_ids": loo_lost,
        "loo_survivor_detail": {
            str(t): {"fired_properties": m1_loo[t]["fired_properties"],
                     "witnesses": m1_loo[t]["witnesses"],
                     "foreign_atom_task_hints": [hint_by_atom.get(p)
                                                 for p in m1_loo[t]["fired_properties"]],
                     "status": m1_loo[t]["status"],
                     "gap_reason": m1_loo[t]["gap_reason"]}
            for t in loo_survivors},
        "per_task": {str(t): {"full": m1_full[t], "loo": m1_loo[t]}
                     for t in RESIDUAL_36},
    }

    # ------------------------------------------------------------------ #
    #  M2 -- WIDENED FALSE-REFUTATION SWEEP over the full 257 arc-5 split.
    #  Every task with an accepted candidate IR (35 pass + 79 ahf = 114)
    #  is replayed with the FULL 36-atom table.
    # ------------------------------------------------------------------ #
    _install_atoms(_ALL_ATOMS)
    arc5_pass_ids = sorted(arc5["pass_ids"])
    m2_detail: Dict[int, Dict[str, Any]] = {}
    for tid in sorted(arc5_rows):
        row = arc5_rows[tid]
        if not row.get("ir"):
            continue
        v = _verdict(row["ir"], tasks_by_id[tid]["prompt"], revealed(tid),
                     row.get("construction") or "retrieved_exemplar")
        v["arc5_outcome"] = row["outcome"]
        m2_detail[tid] = v

    fp_ids = sorted(t for t in arc5_pass_ids
                    if m2_detail.get(t, {}).get("any_fired") == 1.0)
    ahf_ids_arc5 = sorted(t for t, r in arc5_rows.items()
                          if r["outcome"] == "accepted_holdout_fail")
    ahf_fired = sorted(t for t in ahf_ids_arc5
                       if m2_detail.get(t, {}).get("any_fired") == 1.0)
    ahf_fired_foreign = sorted(
        t for t in ahf_fired
        if any(hint_by_atom.get(p) != t
               for p in m2_detail[t]["fired_properties"]))
    ahf_fired_unauthored = sorted(t for t in ahf_fired if t not in RESIDUAL_36)

    out["m2_false_refutation_widened"] = {
        "_what": ("All 36 atoms run against the FULL 257-task runnable split "
                  "(results/arc5_final.json, the settled 35/257). A false "
                  "refutation is an atom firing on a task whose accepted "
                  "program is CORRECT (arc5 outcome 'pass') -- it would "
                  "directly reduce 35/257."),
        "n_tasks_in_split": len(arc5_rows),
        "n_replayed_with_candidate_ir": len(m2_detail),
        "arc5_pass_ids": arc5_pass_ids,
        "n_false_refutations": len(fp_ids),
        "false_refutation_ids": fp_ids,
        "false_refutation_detail": {str(t): m2_detail[t] for t in fp_ids},
        "arc5_accepted_holdout_fail_ids": ahf_ids_arc5,
        "n_ahf_fired": len(ahf_fired),
        "ahf_fired_ids": ahf_fired,
        "ahf_fired_by_a_foreign_atom_ids": ahf_fired_foreign,
        "ahf_fired_outside_the_authored_36_ids": ahf_fired_unauthored,
        "ahf_fired_detail": {str(t): m2_detail[t] for t in ahf_fired},
    }

    # ------------------------------------------------------------------ #
    #  M3 -- CROSS-TASK FIRING. Cue-match and applicability need no
    #  candidate, so they are computed over ALL 257; refutation is
    #  reported over the 114 that have one (from M2's replay).
    # ------------------------------------------------------------------ #
    reach: Dict[int, Dict[str, List[str]]] = {}
    for tid in sorted(arc5_rows):
        reach[tid] = _atom_reach(tasks_by_id[tid]["prompt"], revealed(tid))

    cue_any = sorted(t for t in reach if reach[t]["cue_match"])
    applicable_any = sorted(t for t in reach if reach[t]["applicable"])
    cue_foreign = sorted(t for t in reach
                         if any(hint_by_atom[a] != t for a in reach[t]["cue_match"]))
    applicable_foreign = sorted(
        t for t in reach
        if any(hint_by_atom[a] != t for a in reach[t]["applicable"]))
    refuted_any = sorted(t for t, v in m2_detail.items() if v["any_fired"] == 1.0)
    refuted_foreign = sorted(
        t for t in refuted_any
        if any(hint_by_atom.get(p) != t for p in m2_detail[t]["fired_properties"]))

    #  the ATOM-CENTRIC view: how far does each authored atom actually
    #  reach across the 257? An atom whose reach is exactly {its own task}
    #  is a lookup key by construction.
    per_atom: Dict[str, Dict[str, Any]] = {}
    for atom in _ALL_ATOMS:
        aid = atom["id"]
        cue = sorted(t for t in reach if aid in reach[t]["cue_match"])
        app = sorted(t for t in reach if aid in reach[t]["applicable"])
        ref = sorted(t for t, v in m2_detail.items()
                     if aid in (v["fired_properties"] or []))
        per_atom[aid] = {
            "task_hint": atom.get("task_hint"),
            "phrases": atom.get("phrases"),
            "arg_count": atom.get("arg_count"),
            "cue_match_task_ids": cue,
            "applicable_task_ids": app,
            "refuted_task_ids": ref,
            "reaches_only_its_own_task": (
                cue == [atom.get("task_hint")] if atom.get("task_hint") in cue
                else False),
        }
    keys_only = sorted(a for a, v in per_atom.items()
                       if v["cue_match_task_ids"] == [v["task_hint"]])
    reaches_further = sorted(a for a, v in per_atom.items()
                             if v["cue_match_task_ids"] != [v["task_hint"]])

    out["m3_cross_task_firing"] = {
        "_what": ("Atoms are keyed by phrase cues plus an arg_count guard. If "
                  "they only ever reach their own 36 authored tasks they are "
                  "lookup keys; if they reach further AND are right there, they "
                  "are properties. Three widening levels: cue_match (prompt "
                  "substrings), applicable (cue + self-verify against the "
                  "goal's own revealed rows, which carries the arg_count "
                  "guard), refuted (applicable + a witness mismatch on the "
                  "task's actual accepted candidate)."),
        "n_tasks_scanned": len(reach),
        "n_tasks_with_any_cue_match": len(cue_any),
        "tasks_with_any_cue_match_ids": cue_any,
        "n_tasks_with_a_FOREIGN_cue_match": len(cue_foreign),
        "tasks_with_a_FOREIGN_cue_match_ids": cue_foreign,
        "n_tasks_with_any_applicable_atom": len(applicable_any),
        "tasks_with_any_applicable_atom_ids": applicable_any,
        "n_tasks_with_a_FOREIGN_applicable_atom": len(applicable_foreign),
        "tasks_with_a_FOREIGN_applicable_atom_ids": applicable_foreign,
        "n_tasks_refuted_full_table": len(refuted_any),
        "tasks_refuted_full_table_ids": refuted_any,
        "n_tasks_refuted_by_a_FOREIGN_atom": len(refuted_foreign),
        "tasks_refuted_by_a_FOREIGN_atom_ids": refuted_foreign,
        "foreign_cue_reach_detail": [
            {"task_id": t,
             "prompt": tasks_by_id[t]["prompt"],
             "arc5_outcome": arc5_rows[t]["outcome"],
             "foreign_atoms": [a for a in reach[t]["cue_match"]
                               if hint_by_atom[a] != t],
             "foreign_atoms_authored_for": [hint_by_atom[a]
                                            for a in reach[t]["cue_match"]
                                            if hint_by_atom[a] != t],
             "survived_self_verify": [a for a in reach[t]["applicable"]
                                      if hint_by_atom[a] != t],
             "blocked_by_self_verify": [a for a in reach[t]["cue_match"]
                                        if hint_by_atom[a] != t
                                        and a not in reach[t]["applicable"]]}
            for t in cue_foreign],
        "atoms_whose_cue_reaches_ONLY_their_own_task": keys_only,
        "atoms_whose_cue_reaches_further": reaches_further,
        "per_atom_reach": per_atom,
        "per_task_reach": {str(t): reach[t] for t in sorted(reach)
                           if reach[t]["cue_match"]},
    }

    # ------------------------------------------------------------------ #
    #  M4 -- THE HONEST 58.7%. arc4 S5's own denominator, three arms.
    # ------------------------------------------------------------------ #
    denom_104 = sorted(t for t, r in arc4_rows.items()
                       if r["outcome"] == "accepted_holdout_fail")
    arms: Dict[str, Dict[int, Dict[str, Any]]] = {"off": {}, "full": {}, "loo": {}}
    for tid in denom_104:
        row = arc4_rows[tid]
        prompt = tasks_by_id[tid]["prompt"]
        rows = revealed(tid)
        cons = row.get("construction") or "retrieved_exemplar"
        for arm, atoms in (("off", []), ("full", _ALL_ATOMS),
                           ("loo", _atoms_except_hint(tid))):
            _install_atoms(atoms)
            arms[arm][tid] = _verdict(row["ir"], prompt, rows, cons)
    _install_atoms(_ALL_ATOMS)

    def _detected(arm: str) -> List[int]:
        #  self-detected wrongness = the candidate never reaches a clean
        #  accept: either rung rejects it (structural or property) or the
        #  goal terminates without minting a Program.
        return sorted(t for t in denom_104
                      if arms[arm][t]["status"] != "accepted"
                      or not arms[arm][t]["program_minted"])

    det_off, det_full, det_loo = _detected("off"), _detected("full"), _detected("loo")
    out["m4_arc4_denominator"] = {
        "_what": ("The SAME 104-task denominator arc4 S5 measured (results/"
                  "arc4_endgame.json `no_structural` arm's accepted_holdout_fail "
                  "rows), replayed in three arms. 'authored' is Seam D's own "
                  "published figure's shape; 'loo' is the transferable claim."),
        "_detection_criterion": (
            "self-detected wrongness = the replayed candidate never reaches a "
            "clean accept: status != 'accepted' OR no Program node minted. A "
            "'pending' terminal is a goal still inside the standing CEGIS "
            "reopen lane at the end of the replay's budget -- it is counted as "
            "detected only because a rung already rejected it "
            "(structural_reject/property_reject == 1.0); it never accepts."),
        "_baseline_note": (
            "The property-OFF arm here is 36/104, NOT arc4 S5's published "
            "26/104. Two conditions differ and BOTH are named rather than "
            "averaged: (a) the engine, the substrate_rs binary was rebuilt "
            "between arc4 and arc5 (results/arc5_final.json's own "
            "discrepancy_investigation: that rebuild alone moved 34 -> 32 by "
            "correcting two coincidental fits); (b) the harness, this is a "
            "minimal-goal REPLAY of each row's frozen IR through psy.pump, not "
            "a full live battery re-run of the propose/lattice/screen "
            "pipeline. The claim made here is therefore the WITHIN-RUN paired "
            "delta across the three arms, all taken under identical "
            "conditions in one process -- not the absolute baseline."),
        "denominator_ids": denom_104,
        "n_denominator": len(denom_104),
        "arm_property_off": {"n": len(det_off), "ids": det_off},
        "arm_full_atom_table_AUTHORED": {"n": len(det_full), "ids": det_full},
        "arm_leave_one_out_TRANSFERABLE": {"n": len(det_loo), "ids": det_loo},
        "ids_lost_from_authored_to_loo": sorted(set(det_full) - set(det_loo)),
        "ids_gained_by_property_over_off": sorted(set(det_full) - set(det_off)),
        "ids_gained_by_property_over_off_UNDER_LOO": sorted(set(det_loo) - set(det_off)),
        "per_task": {str(t): {a: arms[a][t] for a in ("off", "full", "loo")}
                     for t in denom_104},
    }

    out["headline"] = {
        "authored_36_of_36": "%d/36" % len(full_fired),
        "leave_one_out": "%d/36" % len(loo_survivors),
        "loo_survivor_ids": loo_survivors,
        "loo_lost_ids": loo_lost,
        "widened_false_refutations_on_the_35_arc5_pass": "%d/%d" % (
            len(fp_ids), len(arc5_pass_ids)),
        "false_refutation_ids": fp_ids,
        "arc4_denominator_structural_only": "%d/104" % len(det_off),
        "arc4_denominator_authored": "%d/104" % len(det_full),
        "arc4_denominator_leave_one_out": "%d/104" % len(det_loo),
        "cross_task_foreign_applicable_ids": applicable_foreign,
        "cross_task_foreign_refutation_ids": refuted_foreign,
    }
    #  a content hash over the MEASUREMENT sections only (no timestamps, no
    #  elapsed time) -- re-run this script and compare `content_sha256` to
    #  check determinism in one line.
    payload = {k: out[k] for k in
               ("m1_leave_one_out", "m2_false_refutation_widened",
                "m3_cross_task_firing", "m4_arc4_denominator", "headline")}
    out["content_sha256"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
    out["elapsed_seconds"] = round(time.time() - t0, 2)

    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=1, sort_keys=False, default=str)
    print(json.dumps(out["headline"], indent=1))
    print("wrote", OUT_PATH, "in", out["elapsed_seconds"], "s")


if __name__ == "__main__":
    main()

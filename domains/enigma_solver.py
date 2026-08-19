"""Solver-shaped front door for Enigma key recovery.

This is the useful part of the newer solver machinery applied to the old
Enigma rung: a problem has explicit inputs, hard constraints can produce an
honest wall, and a resolved result carries both an answer and diagnostics.
The exact Enigma transform and search remain in ``toy_enigma``,
``enigma_recoverer`` and ``enigma_blind``; this module is only the boundary
adapter, analogous to the existing ``solve_*`` resolver callables.

It deliberately does not pretend that a ciphertext-only language-model
winner is a proof.  The blind path reports a candidate and its search
diagnostics; callers with ground truth can use ``enigma_blind.grade`` for an
evaluation verdict.
"""
from __future__ import annotations

from dataclasses import dataclass
import itertools
import json
from pathlib import Path
from typing import Optional, Tuple

from domains.toy_enigma import REFLECTOR_B, Settings, N


@dataclass(frozen=True)
class EnigmaProblem:
    ciphertext: str
    crib: Optional[str] = None
    crib_offset: int = 0
    rotor_pool: Tuple[str, ...] = ("I", "II", "III")
    rotor_count: int = 3
    ring: Optional[Tuple[int, ...]] = None
    reflector: str = REFLECTOR_B
    known_plug: str = ""
    stationary_rotors: Optional[int] = None

    def validate(self) -> Optional[str]:
        if not self.ciphertext or not any(ch.isalpha() for ch in self.ciphertext):
            return "ciphertext is empty"
        if self.crib_offset < 0:
            return "crib_offset must be non-negative"
        crib_len = len([ch for ch in (self.crib or "").upper()
                        if "A" <= ch <= "Z"])
        if self.crib is not None and self.crib_offset + crib_len > len(
            [ch for ch in self.ciphertext.upper() if "A" <= ch <= "Z"]
        ):
            return "crib extends beyond ciphertext"
        if self.rotor_count < 3 or len(self.rotor_pool) < self.rotor_count:
            return "rotor_pool must contain at least rotor_count rotors"
        if self.ring is not None and len(self.ring) != self.rotor_count:
            return "ring must contain one setting per rotor"
        return None


def _wall(problem: EnigmaProblem, kind: str, reason: str) -> dict:
    return {
        "status": "wall",
        "wall_kind": kind,
        "reason": reason,
        "answer": None,
        "problem": problem,
    }


def graph_crib_admissibility(problem: EnigmaProblem, candidates, *, mode: str = "crib") -> dict:
    """Run the Enigma hard cut as graph data through the native Γ rules.

    Candidate generation is mechanical enumeration; the decision that a
    candidate survives is made by the seeded Rust Term (`EnigmaCrib` or
    `EnigmaBombe`) during `run_rules`. Keeping this boundary explicit makes
    the amount of work before and after admissibility measurable.
    """
    import substrate_rs

    candidate_list = list(candidates)
    seed_path = Path(__file__).resolve().parents[1] / "seeds" / "enigma_recovery.json"
    substrate = substrate_rs.Substrate()
    summary = substrate._inner.load_seed_manifest(json.loads(seed_path.read_text()))
    problem_node = substrate.add_node("EnigmaProblem", {
        "ciphertext": problem.ciphertext,
        "crib": problem.crib or "",
        "crib_offset": problem.crib_offset,
    })
    node_type = "EnigmaBombeCandidate" if mode == "bombe" else "EnigmaCandidate"
    nodes = []
    for attrs in candidate_list:
        node = substrate.add_node(node_type, attrs)
        substrate._inner.add_edge_unchecked(problem_node, "has_candidate", node)
        nodes.append(node)
    scan_type = "EnigmaBombeScan" if mode == "bombe" else "EnigmaCribScan"
    scan_edge = "run_bombe_scan" if mode == "bombe" else "run_crib_scan"
    scan = substrate.add_node(scan_type, {})
    substrate._inner.add_edge_unchecked(problem_node, scan_edge, scan)
    rule_steps = substrate._inner.run_rules()
    problem_attrs = substrate.node(problem_node)["attrs"]
    if mode == "bombe":
        witnesses = {}
        for pair in problem_attrs.get("bombe_witnesses", ()):
            if isinstance(pair, (list, tuple)) and len(pair) == 2 and pair[1] is not None:
                witnesses[pair[0]] = pair[1]
        survivors = [dict(record, bombe_witness=witnesses[node])
                     for record, node in zip(candidate_list, nodes)
                     if node in witnesses]
    else:
        admissible_ids = set(problem_attrs.get("admissible_candidates", ()))
        survivors = [record for record, node in zip(candidate_list, nodes)
                     if node in admissible_ids]
    return {
        "survivors": survivors,
        "evaluated": len(candidate_list),
        "rejected": len(candidate_list) - len(survivors),
        "rule_steps": rule_steps,
        "seed_summary": summary,
    }


def _candidate_attrs(problem: EnigmaProblem, order, start, *, mode: str) -> dict:
    attrs = {
        "ciphertext": problem.ciphertext,
        "crib": problem.crib or "",
        "crib_offset": problem.crib_offset,
        "rotor_order": " ".join(order),
        "ring": " ".join(str(x) for x in (problem.ring or (0,) * problem.rotor_count)),
        "start": " ".join(str(x) for x in start),
        "reflector": problem.reflector,
        "search_order": list(order),
        "search_start": list(start),
    }
    if mode != "bombe":
        attrs["plugboard"] = problem.known_plug
    return attrs


def solve_crib(problem: EnigmaProblem, lm, *, topk: int = 3) -> dict:
    """Solve a known-plaintext problem with hard crib admissibility."""
    error = problem.validate()
    if error:
        return _wall(problem, "invalid_problem", error)
    if problem.crib is None:
        return _wall(problem, "missing_crib", "solve_crib requires a crib")
    from domains.enigma_recoverer import to_idx

    orders = list(itertools.permutations(problem.rotor_pool, problem.rotor_count))
    if problem.rotor_count == 4 and (problem.stationary_rotors or 1) == 1:
        orders = [order for order in orders if order[0] in {"BETA", "GAMMA"}]
    survivors = []
    evaluated = rejected = rule_steps = brute_force = 0
    # Keep one rotor-order slice resident at a time. This is still a single
    # Γ-backed search over the same hypothesis space, but avoids duplicating
    # 105k Python/Rust attr dictionaries before the native filter runs.
    for order in orders:
        batch = [
            _candidate_attrs(problem, order, start, mode="crib")
            for start in itertools.product(range(N), repeat=problem.rotor_count)
        ]
        graph_result = graph_crib_admissibility(problem, batch, mode="crib")
        survivors.extend(graph_result["survivors"])
        evaluated += graph_result["evaluated"]
        rejected += graph_result["rejected"]
        rule_steps += graph_result["rule_steps"]
        brute_force += len(batch)
    best = None
    best_score = -float("inf")
    ranked = []
    for candidate in survivors:
        settings = Settings(
            tuple(candidate["search_order"]),
            tuple(problem.ring or (0,) * problem.rotor_count),
            tuple(candidate["search_start"]),
            problem.known_plug,
            problem.reflector,
            problem.stationary_rotors,
        )
        score = lm.logprob(to_idx(settings.decrypt(problem.ciphertext)))
        ranked.append((score, settings.rotor_order, settings.start))
        if score > best_score:
            best_score = score
            best = settings
    ranked.sort(key=lambda item: -item[0])
    if best is None:
        return _wall(
            problem,
            "no_admissible_key",
            "no rotor/start candidate satisfies the hard crib constraint",
        )
    return {
        "status": "resolved",
        "answer": best,
        "score": best_score,
        "diagnostics": {
            "evaluated": evaluated,
            "brute_force": brute_force,
            "admissible": len(survivors),
            "rejected": rejected,
            "grammar_rule_steps": rule_steps,
            "top_candidates": ranked[:topk],
        },
        "problem": problem,
    }


def solve_blind(problem: EnigmaProblem, lm, **search_kwargs) -> dict:
    """Run the ciphertext-only solver and return a solver-shaped result."""
    error = problem.validate()
    if error:
        return _wall(problem, "invalid_problem", error)
    if problem.crib is not None:
        return _wall(problem, "wrong_solver", "solve_blind does not consume a crib")

    from domains.enigma_blind import recover_blind

    result = recover_blind(
        problem.ciphertext,
        lm,
        rotor_pool=problem.rotor_pool,
        ring=problem.ring,
        rotor_count=problem.rotor_count,
        reflector=problem.reflector,
        stationary_rotors=problem.stationary_rotors,
        **search_kwargs,
    )
    return {
        "status": "resolved",
        "answer": result["best"],
        "note": "best ciphertext-only candidate; exactness requires held-out evaluation",
        "diagnostics": {k: v for k, v in result.items() if k != "best"},
        "problem": problem,
    }


def solve_bombe(problem: EnigmaProblem, lm, *, max_extra_pairs: int = 6) -> dict:
    """Solve a 3-rotor crib problem with plugboard-independent constraints.

    This is the finite-constraint solver path: the crib is a hard relation,
    the Bombe carves rotor hypotheses whose involution constraints are empty,
    and the language model only ranks the surviving completions.
    """
    error = problem.validate()
    if error:
        return _wall(problem, "invalid_problem", error)
    if problem.crib is None:
        return _wall(problem, "missing_crib", "solve_bombe requires a crib")
    if problem.rotor_count != 3:
        return _wall(problem, "unsupported_bombe_scope", "Bombe path currently uses 3 moving rotors")

    from domains.enigma_recoverer import complete_plugboard, to_idx

    ring = problem.ring or (0, 0, 0)
    orders = list(itertools.permutations(problem.rotor_pool, 3))
    survivors = []
    evaluated = rejected = rule_steps = brute_force = 0
    # The native Γ cut also returns one concrete partial steckering witness;
    # Python only performs the deliberately soft completion on survivors.
    for order in orders:
        batch = [
            _candidate_attrs(problem, order, start, mode="bombe")
            for start in itertools.product(range(26), repeat=3)
        ]
        graph_result = graph_crib_admissibility(problem, batch, mode="bombe")
        evaluated += graph_result["evaluated"]
        rejected += graph_result["rejected"]
        rule_steps += graph_result["rule_steps"]
        brute_force += len(batch)
        for candidate in graph_result["survivors"]:
            order2 = tuple(candidate["search_order"])
            start = tuple(candidate["search_start"])
            survivors.append((order2, start, candidate["bombe_witness"], 0, 0))

    if not survivors:
        return _wall(
            problem,
            "no_admissible_steckering",
            "every rotor hypothesis contradicts the crib's plugboard constraints",
        )

    best = None
    best_score = -float("inf")
    for order, start, partial, branches, contradicted in survivors:
        plug = complete_plugboard(
            order, ring, start, problem.ciphertext, lm, partial,
            max_extra_pairs=max_extra_pairs, reflector=problem.reflector,
        )
        candidate = Settings(order, ring, start, plug, problem.reflector)
        score = lm.logprob(to_idx(candidate.decrypt(problem.ciphertext)))
        if score > best_score:
            best_score = score
            best = candidate

    return {
        "status": "resolved",
        "answer": best,
        "score": best_score,
        "diagnostics": {
            "evaluated": evaluated,
            "brute_force_rotor_scope": brute_force,
            "survivors": len(survivors),
            "grammar_rejected": rejected,
            "grammar_rule_steps": rule_steps,
            "python_completion_candidates": len(survivors),
            "plugboards_enumerated": False,
        },
        "problem": problem,
    }


def solve(problem: EnigmaProblem, lm, **search_kwargs) -> dict:
    """Dispatch by problem shape, with explicit solver modes implicit in data."""
    if problem.crib is not None:
        if problem.known_plug:
            return solve_crib(problem, lm, **search_kwargs)
        return solve_bombe(problem, lm, **search_kwargs)
    return solve_blind(problem, lm, **search_kwargs)


__all__ = [
    "EnigmaProblem", "solve", "solve_crib", "solve_bombe", "solve_blind",
    "graph_crib_admissibility",
]

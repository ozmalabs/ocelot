"""Deterministic source/target process-map worlds for P11 evaluation.

These functions define world mechanics and independent expected effects. They
do not choose maps or processes for an agent.
"""
from __future__ import annotations

import random


def inverse_permutation(p):
    inv = [0] * len(p)
    for i, j in enumerate(p):
        inv[j] = i
    return inv


def compose_permutations(a, b):
    """Return the permutation that applies a, then b (PMB convention)."""
    return [b[a[i]] for i in range(len(a))]


def apply_permutation(state, p):
    out = [None] * len(state)
    for i, j in enumerate(p):
        out[j] = state[i]
    return out


def matrix_multiply(a, b):
    """Ordinary matrix product, used by integer-vector world mechanics."""
    return [[sum(a[i][k] * b[k][j] for k in range(len(b)))
             for j in range(len(b[0]))] for i in range(len(a))]


def apply_matrix(state, matrix):
    return [sum(row[j] * state[j] for j in range(len(state))) for row in matrix]


def _permutation_world(seed: int):
    rng = random.Random(seed * 7919 + 11)
    n = 4
    forward = list(range(n))
    rng.shuffle(forward)
    if forward == list(range(n)):
        forward[0], forward[1] = forward[1], forward[0]
    inverse = inverse_permutation(forward)
    source = [1, 0, 2, 3]
    target = compose_permutations(compose_permutations(inverse, source), forward)
    states = []
    for _ in range(4):
        s = list(range(n))
        rng.shuffle(s)
        states.append(s)
    probes = [list(range(n))]
    return {"pairing": "permutation_relabel_4", "kind": "permutation",
            "source_program": source, "target_program": target,
            "forward_map": forward, "inverse_map": inverse,
            "training_states": states[:2], "heldout_states": states[2:],
            "separating_probes": probes,
            "source_epoch": 1, "model_epoch": 1, "source_frame_epoch": 1,
            "target_frame_epoch": 2, "target_probe_epoch": 3,
            "seed": seed}


def _matrix_world(seed: int):
    rng = random.Random(seed * 7919 + 23)
    forward = [[0, -1], [1, 0]]
    inverse = [[0, 1], [-1, 0]]
    source = [[1, 1], [0, 1]]
    target = matrix_multiply(matrix_multiply(forward, source), inverse)
    states = [[rng.randint(-5, 5), rng.randint(-5, 5)] for _ in range(4)]
    probes = [[1, 0], [0, 1]]
    return {"pairing": "integer_matrix_basis_2", "kind": "integer_matrix",
            "source_program": source, "target_program": target,
            "forward_map": forward, "inverse_map": inverse,
            "training_states": states[:2], "heldout_states": states[2:],
            "separating_probes": probes,
            "source_epoch": 1, "model_epoch": 1, "source_frame_epoch": 1,
            "target_frame_epoch": 2, "target_probe_epoch": 3,
            "seed": seed}


def transfer_world(pairing: str, seed: int):
    if pairing == "permutation_relabel_4":
        return _permutation_world(seed)
    if pairing == "integer_matrix_basis_2":
        return _matrix_world(seed)
    raise ValueError(f"unsupported process-transfer pairing: {pairing}")


def apply_program(kind: str, state, program):
    if kind == "permutation":
        return apply_permutation(list(state), list(program))
    if kind == "integer_matrix":
        return apply_matrix(list(state), program)
    raise ValueError(f"unsupported world process kind: {kind}")


def verify_world_conjugacy(world):
    """Check the generated target truth on the declared complete probes."""
    kind = world["kind"]
    f, f_inv = world["forward_map"], world["inverse_map"]
    for state in world["separating_probes"]:
        target_state = apply_program(kind, state, f)
        expected = apply_program(kind,
                                 apply_program(kind,
                                               apply_program(kind, target_state, f_inv),
                                               world["source_program"]), f)
        observed = apply_program(kind, target_state, world["target_program"])
        if expected != observed:
            return False
    return True

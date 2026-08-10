"""A tiny fixture module for the deterministic baseline/after measurement gate
(tests/test_code_curriculum_migrated.py) -- NOT part of the real agent code,
scanned in isolation so the gate is unaffected by concurrent edits elsewhere
in the repo."""


def add(a, b):
    return a + b


def is_positive(x):
    return x > 0

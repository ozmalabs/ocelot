"""Temporal event modifiers stay outside selected predicate arguments."""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from domains.construction_grammar import compose_relation, parse_with_gaps


def test_clause_final_adverb_remains_temporal_modifier_in_selection_query():
    frame = parse_with_gaps("Which rule fired last?")
    relation = compose_relation(frame)

    assert frame["focus"] == "selection"
    assert frame["elements"][-1]["pos"] == "adv"
    assert relation["subject"]["surface"].lower() == "rule"
    assert relation["predicate"]["surface"].lower() == "fired"
    assert relation["object"] is None


def test_nominal_complement_remains_object_in_selection_query():
    frame = parse_with_gaps("Which rule fired the alarm?")
    relation = compose_relation(frame)

    assert relation["subject"]["surface"].lower() == "rule"
    assert relation["predicate"]["surface"].lower() == "fired"
    assert relation["object"]["surface"].lower() == "alarm"

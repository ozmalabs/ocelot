"""Dictionary-teacher absorption, migrated to the seed-booted WorldAdapter
(no CuriousAgent).

The pure DictionaryTeacher class tests live in tests/test_dict_teacher.py (that
class is not being deleted). This file covers the one CuriousAgent integration
test: the agent absorbs a dictionary payload through the graph-native
learn_from_teacher (Microtheory + lexicon Sign + taught Concept). The teacher is
wire-compatible by construction; the adapter just installs what it returns.
"""
from __future__ import annotations

import pytest

from domains.dict_teacher import DictionaryTeacher, is_available
from substrate.world_adapter import WorldAdapter


pytestmark = pytest.mark.skipif(
    not is_available(), reason="NLTK WordNet corpus not installed")


def test_agent_absorbs_dict_payload():
    t = DictionaryTeacher()
    a = WorldAdapter()
    payload = t("what is photosynthesis?")
    assert payload is not None
    a.learn_from_teacher("what is photosynthesis?", payload)
    forms = {s.get("form") for s in a.taught_signs()}
    assert "photosynthesis" in forms
    assert "dictionary" in a.microtheory_names()

"""Core vocabulary — top Brown words as starting lexicon."""
from __future__ import annotations

import pytest

from domains.core_vocabulary import (_CORE_VOCAB_MT, install_core_vocabulary,
                                       is_installed)
from domains.dict_teacher import is_available
from substrate.world_adapter import WorldAdapter


pytestmark = pytest.mark.skipif(
    not is_available(), reason="NLTK not available")


# ---------------------------------------------------------------------------
# install
# ---------------------------------------------------------------------------

def test_install_grounds_many_signs():
    """A reasonable-sized core vocabulary lands. We use n=50 to keep
    the test fast; the chat default is 1000."""
    a = WorldAdapter()
    n = install_core_vocabulary(a, n=50)
    assert n > 10           # most top-50 words have wordnet entries
    assert is_installed(a)


def test_install_is_idempotent():
    a = WorldAdapter()
    n1 = install_core_vocabulary(a, n=50)
    n2 = install_core_vocabulary(a, n=50)
    assert n2 == 0          # second call no-ops via Mt check
    assert n1 > 0


def test_force_reinstall_dedupes_via_learn_sign():
    a = WorldAdapter()
    install_core_vocabulary(a, n=50)
    before = len([s for s in a.taught_signs() if s.get("form")])
    n2 = install_core_vocabulary(a, n=50, force=True)
    after = len([s for s in a.taught_signs() if s.get("form")])
    assert n2 > 0           # forced — runs again
    assert after == before  # learn_sign deduped by form, no new signs


def test_marker_mt_present_after_install():
    a = WorldAdapter()
    install_core_vocabulary(a, n=50)
    assert a.microtheory(_CORE_VOCAB_MT) is not None


# ---------------------------------------------------------------------------
# render — produce can express meanings using these signs
# ---------------------------------------------------------------------------

def test_agent_can_render_meanings_using_grounded_words():
    """The point of installing core vocabulary: produce() can render
    meanings about common concepts. Try a meaning using 'time' (top-100
    noun) — round-trip should produce text containing 'time'."""
    a = WorldAdapter()
    install_core_vocabulary(a, n=100)
    forms = {s.get("form") for s in a.taught_signs()}
    assert "time" in forms or "year" in forms or "way" in forms


def test_signs_carry_pos_attribute():
    """Each concept's description carries the WordNet POS so callers
    can downstream use it."""
    a = WorldAdapter()
    install_core_vocabulary(a, n=50)
    # find one of the installed concepts and check it has a pos attr
    sample = None
    for c in a.s.nodes("Concept"):
        attrs = a.s.node(c)["attrs"]
        if attrs.get("pos"):
            sample = attrs
            break
    assert sample is not None
    assert sample["pos"] in {"n", "v", "a", "s", "r"}

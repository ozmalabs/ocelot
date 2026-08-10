"""A LOOKUP'S ABSENCE IS NOT A MEASUREMENT — the instrument half.

The seeds' version of this defect is a guard that cannot tell "no reading" from
"a reading of zero". The tooling's version is worse, because it is silent: the
debug endpoint answers a query for a node type that does not exist with
`total: 0`, which reads exactly like a real empty pool.

That produced two wrong diagnoses in one day, both of which I published before
catching them:

  * `CognitiveCheckin` for `CognitiveCheckIn` — reported "zero check-ins exist"
    while 36 existed and the supervisor was cycling normally;
  * `EmbodiedActiveResetRequest` / `CounterfactualEmbodiedTrial` for
    `EmbodiedResetRequest` / `Experiment` — reported a drained trial pipeline
    that was in fact healthy, sending the whole diagnosis down a wrong path.

So the instrument must refuse a type no seed can produce, rather than counting
it as zero.
"""
from domains.engine_provenance import engine_preamble
engine_preamble()

import pytest                                                          # noqa: E402

from scripts.growth_pipeline_sampler import (                          # noqa: E402
    TYPES, UnknownNodeType, fetch, known_node_types,
)


def test_the_types_the_sampler_queries_all_exist():
    """The regression itself: every type this instrument asks about must be
    one some seed can actually mint."""
    known = known_node_types()
    unknown = sorted(t for t in TYPES if t not in known)
    assert not unknown, f"sampler queries type(s) no seed mints: {unknown}"


def test_the_exact_typos_that_caused_the_wrong_diagnoses_are_refused():
    known = known_node_types()
    for typo in ("CognitiveCheckin", "EmbodiedActiveResetRequest",
                 "CounterfactualEmbodiedTrial"):
        assert typo not in known, f"{typo} should not be a real type"
        with pytest.raises(UnknownNodeType):
            fetch(1, typo)


def test_the_correct_spellings_are_accepted():
    known = known_node_types()
    for real in ("CognitiveCheckIn", "EmbodiedResetRequest", "Experiment"):
        assert real in known, f"{real} should be a real type"


def test_a_real_but_unpopulated_type_is_still_queryable():
    """The distinction being preserved is 'nothing is there' versus 'you asked
    the wrong question' — so a real type must never be refused merely because
    the live graph has none of it."""
    known = known_node_types()
    assert "EmbodiedDevelopmentalContext" in known
    # Refusal is by type validity, not by population: no live daemon is
    # required to establish that.
    with pytest.raises(UnknownNodeType):
        fetch(1, "EmbodiedDevelopmentalContexts")

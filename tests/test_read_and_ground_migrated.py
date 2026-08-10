"""The jabberwock READS PROSE and GROUNDS it — on the seed-booted WorldAdapter
(no CuriousAgent). The first slice of the encyclopedic read-and-ground campaign
(docs/encyclopedic_seeds_reading_plan.md): the 146 dark encyclopedias carry
PROSE rules, not graph patterns; converting them is the agent READING its own
prose and grounding it, not a schema translation.

What this bench proves graph-native:
  • the `read_and_ground` faculty RUNS on the seed-booted agent — it comprehends
    a definition ("X is a <genus> …" via the construction grammar), writes the
    built_from edge, and recurses toward the seeded primitives;
  • it grounds END-TO-END: a fed encyclopedic definition whose genus is a SEEDED
    primitive (psychology's `perception` / `belief`) bottoms out at that
    primitive — grounded=True, the primitive in the cone;
  • the `grounding` SEED is load-bearing: it opens the Γ productions that admit
    the Concept->Concept `built_from` edge. WITHOUT it the comprehension still
    runs but the grounding mutation is INADMISSIBLE and silently dropped (the
    concept never reaches a primitive) — the precise gap the seed closes. The
    old CuriousAgent opened these at construction; the seed installs them at
    boot, graph-natively.

No Python decides meaning: the genus is the construction grammar's (graph
data), the ground is ground_concept (an admissible mutation), the descent
climbs the agent's own built_from graph. The Reader is a mechanical world-
adapter staging the seed's own prose as a definition feed (no decisions).
"""
from __future__ import annotations

import domains.seed_registry  # noqa: F401 — populates REGISTRY
from substrate.boot_core import CORE_SEEDS, load_seeds_into
from substrate.world_adapter import WorldAdapter
from domains.read_and_ground import read_and_ground


class _Reader:
    """A mechanical world-adapter reader: a `_definition_feed` mapping
    concept-name -> the prose the agent reads. Stages the seed's own text;
    decides nothing (read_and_ground._read_definition prefers this feed)."""

    def __init__(self, feed: dict[str, str]):
        self._definition_feed = feed


def _agent(*, with_grounding: bool):
    wa = WorldAdapter(seeds=CORE_SEEDS)
    extra = ["relations", "psychology"]
    if with_grounding:
        extra.insert(0, "grounding")
    load_seeds_into(wa.s, wa.agent, extra)
    return wa


# ---------------------------------------------------------------------------
# the faculty RUNS + grounds END-TO-END on the seed-booted agent
# ---------------------------------------------------------------------------

def test_reads_and_grounds_to_a_seeded_primitive():
    wa = _agent(with_grounding=True)
    res = read_and_ground(
        wa.s, "recognition",
        conversation=_Reader({"recognition":
                              "recognition is a perception of a known thing"}))
    assert res["grounded"] is True
    st = res["structure"]
    assert st["genus"] == "perception"
    # the cone bottoms out at the SEEDED primitive, not a freshly minted leaf
    assert "perception" in st["primitives"]


def test_grounds_multiple_encyclopedic_definitions():
    wa = _agent(with_grounding=True)
    cases = {
        "recognition": "recognition is a perception of a known thing",
        "mistrust": "mistrust is a belief that someone is not reliable",
    }
    for concept, prose in cases.items():
        res = read_and_ground(wa.s, concept,
                              conversation=_Reader({concept: prose}))
        assert res["grounded"] is True, (concept, res["reason"])
        assert res["structure"]["primitives"]  # reaches a basis primitive


def test_comprehension_runs_even_without_the_grounding_seed():
    """The READ + COMPREHEND step is faculty-intrinsic (construction grammar):
    even without the grounding seed the genus is recovered. Only the GROUNDING
    mutation needs the seed — so the honest reason is the bare-leaf stall, not a
    crash or a failure to comprehend."""
    wa = _agent(with_grounding=False)
    res = read_and_ground(
        wa.s, "recognition",
        conversation=_Reader({"recognition":
                              "recognition is a perception of a known thing"}))
    # comprehended the genus …
    assert res["structure"]["genus"] == "perception"
    # … but the built_from edge was inadmissible -> never reached a primitive
    assert res["grounded"] is False
    assert not res["structure"]["primitives"]


# ---------------------------------------------------------------------------
# the `grounding` seed is the load-bearing difference (graph-native)
# ---------------------------------------------------------------------------

def test_grounding_seed_is_load_bearing():
    """The SAME prose grounds with the seed and stalls without it — the seed
    (Γ productions admitting Concept->Concept built_from) is exactly what turns
    a comprehended-but-unrooted reading into a grounded one."""
    prose = {"recognition": "recognition is a perception of a known thing"}

    with_seed = read_and_ground(_agent(with_grounding=True).s, "recognition",
                                conversation=_Reader(dict(prose)))
    without = read_and_ground(_agent(with_grounding=False).s, "recognition",
                              conversation=_Reader(dict(prose)))

    assert with_seed["grounded"] is True
    assert without["grounded"] is False


def test_grounding_seed_loads_via_loader_only():
    """The seed installs the grounding productions through the Rust loader — no
    Python open_grounding_productions() call. Booting it + reading grounds."""
    wa = WorldAdapter(seeds=CORE_SEEDS)
    load_seeds_into(wa.s, wa.agent, ["grounding", "psychology"])
    res = read_and_ground(
        wa.s, "mistrust",
        conversation=_Reader({"mistrust":
                              "mistrust is a belief that someone is not reliable"}))
    assert res["grounded"] is True
    assert "belief" in res["structure"]["primitives"]

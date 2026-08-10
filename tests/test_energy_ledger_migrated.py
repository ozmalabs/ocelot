"""THE STOCK — the migrated gate for the integer energy ledger.

Consumption was already measured on every receipt (`energy_cost_units`, 223
live writes; `peak_load_units`, 341).  No level was ever carried, so the books
could not close, monotonicity could not be stated, and the option margin had no
affordability term.  This gates the level.

The `*_joules`/`*_watts` ledger declared on `EmbodiedEnergeticState` is
deliberately NOT used: it is template-only in a live graph (zero instances
after thirteen hours), and in-frame quantities are integers regardless.
"""
from domains.engine_provenance import engine_preamble
engine_preamble()

from scripts.gen_energy_ledger_seed import (          # noqa: E402
    DEFAULT_HORIZON_ACTIONS, DEFAULT_OPENING_UNITS, DEFAULT_RATE_CEILING_UNITS,
    manifest,
)
from substrate.seed_loader import manifest_for         # noqa: E402
from substrate.world_adapter import WorldAdapter       # noqa: E402


def _edge(agent, source, edge_type, target):
    agent.inner.add_edge_unchecked(source, edge_type, target)


def _agent():
    agent = WorldAdapter()
    for seed in ("counterfactual_experiment", "embodied_learning_session",
                 "embodied_development"):
        agent.inner.load_seed_manifest(manifest_for(seed), agent.agent)
    agent.inner.load_seed_manifest(manifest(), agent.agent)
    return agent


def _episode(agent):
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {})
    body = agent.s.add_node("EmbodiedBodySchema", {"morphology_epoch": 1})
    world = agent.s.add_node("EmbodiedLearningWorld", {"world_epoch": 1})
    _edge(agent, agent.agent, "has_embodied_development_episode", episode)
    _edge(agent, episode, "has_embodied_body_schema", body)
    _edge(agent, episode, "has_embodied_learning_world", world)
    agent.inner.run_rules()
    return episode


def _ledger(agent, episode):
    return agent.inner.neighbours(episode, "has_energy_ledger")[0]


def _spend(agent, episode, *, energy, peak=0):
    receipt = agent.s.add_node("EmbodiedLearningTrialReceipt", {
        "status": "closed", "development_receipt_closed": 1,
        "energy_cost_units": energy, "peak_load_units": peak,
        "causal_closed": 1, "grounded": 1,
        "integer_native": 1, "output_authority": 0,
    })
    _edge(agent, episode, "has_embodied_development_receipt", receipt)
    agent.inner.run_rules()
    return receipt


def test_a_ledger_opens_with_a_declared_balance_that_says_it_is_declared():
    agent = _agent()
    episode = _episode(agent)
    attrs = agent.s.node(_ledger(agent, episode))["attrs"]
    assert attrs["opening_units"] == DEFAULT_OPENING_UNITS
    assert attrs["stock_units"] == DEFAULT_OPENING_UNITS
    # The F16 pattern: a declared default is usable, and never confusable with
    # a measurement. This flag is the whole defence against the silent zero.
    assert attrs["stock_measured"] == 0
    assert attrs["rate_ceiling_measured"] == 0


def test_expenditure_draws_the_stock_down_and_the_books_close():
    agent = _agent()
    episode = _episode(agent)
    _spend(agent, episode, energy=30)
    _spend(agent, episode, energy=12)
    attrs = agent.s.node(_ledger(agent, episode))["attrs"]
    assert attrs["posted_receipt_count"] == 2
    assert attrs["expenditure_units"] == 42
    # Intake = expenditure + storage — the identity the agent already holds.
    assert (attrs["opening_units"] + attrs["intake_units"]
            == attrs["expenditure_units"] + attrs["stock_units"])
    assert attrs["stock_units"] == DEFAULT_OPENING_UNITS - 42


def test_posting_is_idempotent_under_a_re_run_fixpoint():
    """The reason expenditure is SUMMED from posted receipts, not accumulated.

    An accumulating rule that re-fires double-counts, and a ledger that drifts
    under its own fixpoint is worse than no ledger.
    """
    agent = _agent()
    episode = _episode(agent)
    _spend(agent, episode, energy=25)
    first = agent.s.node(_ledger(agent, episode))["attrs"]["stock_units"]
    for _ in range(5):
        agent.inner.run_rules()
    after = agent.s.node(_ledger(agent, episode))["attrs"]
    assert after["stock_units"] == first
    assert after["expenditure_units"] == 25
    assert after["posted_receipt_count"] == 1


def test_stock_is_monotone_non_increasing_with_no_intake():
    """The claim an aircraft's throttle falsifies, stated where it holds.

    With no intake source the level only falls. This is exactly the F16 block-C
    prediction that failed there because the mechanical column was measured
    alone; carried with its convertible stock, the ledger is monotone again.
    """
    agent = _agent()
    episode = _episode(agent)
    levels = []
    for cost in (10, 5, 20, 1):
        _spend(agent, episode, energy=cost)
        levels.append(agent.s.node(_ledger(agent, episode))["attrs"]["stock_units"])
    assert levels == sorted(levels, reverse=True)
    assert levels[-1] == DEFAULT_OPENING_UNITS - 36


def test_reachable_is_capped_by_the_rate_ceiling_not_only_the_stock():
    """A full tank cannot be spent faster than the actuator converts it."""
    agent = _agent()
    episode = _episode(agent)
    attrs = agent.s.node(_ledger(agent, episode))["attrs"]
    rate_capped = DEFAULT_RATE_CEILING_UNITS * DEFAULT_HORIZON_ACTIONS
    assert rate_capped < DEFAULT_OPENING_UNITS       # the binding ceiling here
    assert attrs["reachable_units"] == rate_capped


def test_reachable_is_capped_by_the_stock_once_it_falls_below_the_rate():
    """...and an unlimited conversion rate cannot spend a tank that is empty."""
    agent = _agent()
    episode = _episode(agent)
    ledger = _ledger(agent, episode)
    _spend(agent, episode, energy=DEFAULT_OPENING_UNITS - 100)
    agent.inner.run_rules()
    attrs = agent.s.node(ledger)["attrs"]
    assert attrs["stock_units"] == 100
    rate_capped = attrs["rate_ceiling_units"] * attrs["horizon_actions"]
    assert attrs["reachable_units"] == min(100, rate_capped) == 100


def test_an_observed_peak_supersedes_the_declared_rate_ceiling_and_flips_provenance():
    agent = _agent()
    episode = _episode(agent)
    ledger = _ledger(agent, episode)
    assert agent.s.node(ledger)["attrs"]["rate_ceiling_measured"] == 0
    _spend(agent, episode, energy=5, peak=DEFAULT_RATE_CEILING_UNITS + 17)
    agent.inner.run_rules()
    attrs = agent.s.node(ledger)["attrs"]
    # A ceiling the body has already exceeded was never the ceiling.
    assert attrs["rate_ceiling_units"] == DEFAULT_RATE_CEILING_UNITS + 17
    assert attrs["rate_ceiling_measured"] == 1


def test_the_ledger_is_integer_native_throughout():
    agent = _agent()
    episode = _episode(agent)
    _spend(agent, episode, energy=7, peak=3)
    attrs = agent.s.node(_ledger(agent, episode))["attrs"]
    for key, value in attrs.items():
        assert not isinstance(value, float), f"float in the ledger: {key}={value!r}"

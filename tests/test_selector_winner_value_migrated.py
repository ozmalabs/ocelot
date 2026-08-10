"""test_selector_winner_value_migrated — THE WINNER'S OWN VALUE.

PREREG: `ENGINE_WINNER_VALUE_PREREG.md`.

`ENGINE_ARGMAX_DETERMINISM_RESULTS.md` §6, the actionable output of the 272-row
`Argmax` non-reproducibility arc:

    Record the WINNER'S OWN VALUE, not just the extremum and the tie count. A tie
    count is computed by the selector under suspicion, so it cannot detect a
    selector disagreeing with its own value Term.

The principle: **a diagnostic must not be computed by the component it checks.**

This file is the GATE. It is written so that every assertion is discriminating —
VISION_PROTOCOL §12/§13.2 ("works" and "is load-bearing" are different
properties; a detector that has never fired has not been tested). So the centre
of the file is the POSITIVE CONTROL: a synthetic selector/value disagreement is
INJECTED and the instrument must catch it in a SINGLE row, red-then-green.
"""
from __future__ import annotations

import pytest

from substrate_rs import _native


# --- fixtures ---------------------------------------------------------------

def _substrate_with_scores(scores):
    """A hub with one `Cand` per score, joined by `has_cand`. The selector's
    value Term is `Attr(c, "score")` — the seed author's own Term, which is
    exactly what the audit re-evaluates on the winner."""
    s = _native.Substrate()
    s.add_production({
        "src": {"type": "Hub", "var": "a"},
        "edge_type": "has_cand",
        "tgt": {"type": "Cand", "var": "b"},
        "where": None,
        "weight": {"type": "Lit", "value": 1.0},
        "provenance": "test_selector_winner_value",
    })
    hub = s.add_node("Hub", {})
    ids = []
    for sc in scores:
        n = s.add_node("Cand", {"score": float(sc)})
        s.add_edge(hub, "has_cand", n)
        ids.append(n)
    return s, hub, ids


def _selector_term(kind):
    return {
        "type": kind,
        "source": {"type": "Neighbours", "node": {"type": "Var", "name": "h"},
                   "edge_type": "has_cand"},
        "var_name": "c",
        "value": {"type": "Attr", "node": {"type": "Var", "name": "c"},
                  "key": "score"},
    }


@pytest.fixture(autouse=True)
def _audit_off_after():
    """Every test leaves the audit and the injector OFF — §9, defaults preserve
    committed results, and the injector must never survive a test."""
    yield
    _native.selector_audit_fault_inject(False)
    _native.selector_audit_enable("off")
    _native.selector_audit_reset()


# --- 1. THE DEFAULT IS OFF (§9) ---------------------------------------------

def test_the_audit_and_the_injector_are_both_OFF_by_default():
    """The instrument ships off. This is the §9 assertion that every committed
    result reproduces exactly, checked rather than asserted in prose.

    It is also a SAFETY property: the fault injector is read only inside the
    audit branch, so with the audit off the injector is unreachable — there is
    no state in which a committed measurement can be perturbed by it."""
    _native.selector_audit_reset()
    st = _native.selector_audit_stats()
    assert st["mode"] == "off"
    assert st["fault_inject"] is False


def test_with_the_audit_OFF_nothing_is_counted_and_the_answer_is_correct():
    s, hub, ids = _substrate_with_scores([3.0, 9.0, 5.0])
    _native.selector_audit_reset()
    win = s.evaluate(_selector_term("Argmax"), {"h": hub})
    assert win == ids[1]                       # the true maximum
    st = _native.selector_audit_stats()
    assert st["firings"] == 0                  # the off path does no work
    assert st["candidates"] == 0


# --- 2. THE INSTRUMENT RECORDS THE WINNER'S OWN VALUE ------------------------

@pytest.mark.parametrize("kind,scores,want_idx", [
    ("Argmax", [3.0, 9.0, 5.0], 1),
    ("Argmin", [3.0, 9.0, 1.0], 2),
])
def test_audit_on_is_silent_and_answer_preserving_when_the_selector_is_honest(
        kind, scores, want_idx):
    """GREEN half of red-then-green: with the audit on and no injection, the
    winner's own value equals the recorded extremum, so zero contradictions —
    and the returned node is unchanged from the audit-off path."""
    s, hub, ids = _substrate_with_scores(scores)
    _native.selector_audit_reset()
    _native.selector_audit_enable("strict")    # would PANIC on any contradiction
    win = s.evaluate(_selector_term(kind), {"h": hub})
    assert win == ids[want_idx]
    st = _native.selector_audit_stats()
    assert st["disagreements"] == 0
    assert st["firings"] == 1                  # exactly one re-evaluation
    assert st["candidates"] == 3               # over three candidates
    assert st["skipped_effectful"] == 0


def test_the_counted_cost_is_exactly_one_extra_evaluation_per_firing():
    """COST, as a counted fraction rather than a wall-clock number (a concurrent
    rung is running; wall-clock would be confounded). The instrument's overhead
    on the selector path is `firings / candidates` = 1/N for a selector over N
    candidates. The number FALLS OUT of the candidate-set size (§13); nothing is
    hand-set here."""
    _native.selector_audit_reset()
    _native.selector_audit_enable("warn")
    for n in (2, 4, 8):
        s, hub, _ = _substrate_with_scores([float(i) for i in range(n)])
        s.evaluate(_selector_term("Argmax"), {"h": hub})
    st = _native.selector_audit_stats()
    assert st["firings"] == 3
    assert st["candidates"] == 2 + 4 + 8
    # 3 extra evaluations over 14 candidate evaluations = 3/14.
    assert st["firings"] / st["candidates"] == pytest.approx(3 / 14)


# --- 3. THE POSITIVE CONTROL — the detector MUST be able to fire -------------

def test_POSITIVE_CONTROL_an_injected_disagreement_is_caught_in_ONE_row():
    """**THE POINT OF THE RUNG.**

    The injector makes the fold return the FIRST candidate regardless of value,
    leaving the recorded extremum correct — EXACTLY the §4.2 signature (a
    constant winner, the lowest-id candidate, while the neighbouring
    compositions stayed correct).

    The instrument must catch it on that ONE firing: no replay, no statistics,
    no second substrate. That is the whole claim, and it is measured here rather
    than argued."""
    s, hub, ids = _substrate_with_scores([3.0, 9.0, 5.0])
    _native.selector_audit_reset()
    _native.selector_audit_enable("warn")
    _native.selector_audit_fault_inject(True)

    win = s.evaluate(_selector_term("Argmax"), {"h": hub})

    st = _native.selector_audit_stats()
    assert win == ids[0], "the injector should have returned the FIRST candidate"
    assert st["firings"] == 1, "caught on a SINGLE firing, not by aggregation"
    assert st["disagreements"] == 1
    row = st["first_row"]
    assert row is not None
    # The row is self-diagnosing: it carries the winner's own value AND the
    # recorded extremum, which is precisely the pair the 272 rows lacked.
    assert "3.0" in row and "9.0" in row, row
    assert "CONTRADICTION" in row


def test_POSITIVE_CONTROL_strict_mode_raises_on_the_first_contradiction():
    """`strict` turns the contradiction into a hard stop, so the invariant can be
    enforced (not merely recorded) wherever it is switched on."""
    s, hub, _ = _substrate_with_scores([3.0, 9.0, 5.0])
    _native.selector_audit_reset()
    _native.selector_audit_enable("strict")
    _native.selector_audit_fault_inject(True)
    with pytest.raises(BaseException) as exc:
        s.evaluate(_selector_term("Argmax"), {"h": hub})
    assert "CONTRADICTION" in str(exc.value)


def test_POSITIVE_CONTROL_fires_for_MinOver_and_MaxOver_too():
    """`MaxOver`/`MinOver` return the winning VALUE, not the element, so the
    winning element is not otherwise retained — the audit tracks it (only while
    enabled) precisely so this class is covered rather than assumed."""
    # The first candidate must be NEITHER the min NOR the max, or injection is
    # a no-op for one of the two directions (see the universal-tie test below —
    # same boundary). Found by this gate failing, which is what it is for.
    for kind in ("MaxOver", "MinOver"):
        s, hub, _ = _substrate_with_scores([5.0, 9.0, 3.0])
        _native.selector_audit_reset()
        _native.selector_audit_enable("warn")
        _native.selector_audit_fault_inject(True)
        s.evaluate(_selector_term(kind), {"h": hub})
        st = _native.selector_audit_stats()
        assert st["disagreements"] == 1, f"{kind} disagreement not caught"
        _native.selector_audit_fault_inject(False)


def test_the_injector_is_a_NO_OP_under_a_universal_tie_and_that_is_CORRECT():
    """Registered in advance (prereg §5, prediction 2's proviso). Where every
    candidate compares equal, the first element IS a legitimate winner, so
    injection changes nothing and no contradiction exists to report.

    This is the boundary of the instrument, not a miss — and it matters because
    the determinism rung measured that a universal tie is exactly the one way
    the native fold CAN return a non-maximal node (§4.1)."""
    s, hub, ids = _substrate_with_scores([7.0, 7.0, 7.0])
    _native.selector_audit_reset()
    _native.selector_audit_enable("strict")    # would panic on a contradiction
    _native.selector_audit_fault_inject(True)
    win = s.evaluate(_selector_term("Argmax"), {"h": hub})
    assert win == ids[0]
    st = _native.selector_audit_stats()
    assert st["disagreements"] == 0


def test_RED_THEN_GREEN_the_OLD_instrumentation_is_BLIND_to_the_same_fault():
    """**THE DECISIVE DEMONSTRATION**, and the reason this rung exists.

    The 272 pinned rows recorded `xf_max` (a `MaxOver`) and `xf_ntied` (a
    `Count(Filter(Eq(·, max)))`). Both were CORRECT on 272/272 rows while the
    `Argmax` between them was constant-wrong. That is why the arc took an arc:
    **both recorded numbers were computed by the selector under suspicion, and
    both agreed with each other.**

    Here that exact configuration is reconstructed on ONE substrate:

    - RED  — the pre-existing quantities (extremum, tie count) are measured with
             the fault present and are BOTH still correct. An instrument built
             from them cannot fire. This is the blindness, demonstrated rather
             than asserted.
    - GREEN — the winner's own value, on the same substrate, fires immediately.

    A detector that has never been shown to fire where the old one stayed silent
    has not been tested."""
    s, hub, ids = _substrate_with_scores([3.0, 9.0, 5.0])
    max_term = _selector_term("MaxOver")
    tie_term = {
        "type": "Count",
        "source": {"type": "Filter",
                   "source": {"type": "Neighbours",
                              "node": {"type": "Var", "name": "h"},
                              "edge_type": "has_cand"},
                   "var_name": "c",
                   "predicate": {"type": "Eq",
                                 "a": {"type": "Attr",
                                       "node": {"type": "Var", "name": "c"},
                                       "key": "score"},
                                 "b": {"type": "Lit", "value": 9.0}}},
    }

    # --- RED: the fault is present, and the OLD numbers are both correct.
    _native.selector_audit_reset()
    _native.selector_audit_enable("warn")
    _native.selector_audit_fault_inject(True)
    winner = s.evaluate(_selector_term("Argmax"), {"h": hub})
    _native.selector_audit_fault_inject(False)   # the neighbouring Terms were
                                                 # CORRECT in the pinned rows
    recorded_max = s.evaluate(max_term, {"h": hub})
    ntied = s.evaluate(tie_term, {"h": hub})

    assert winner == ids[0], "the fault must actually be present"
    assert winner != ids[1], "…and the winner must actually be wrong"
    assert recorded_max == 9.0, "MaxOver is correct — exactly as in the 272 rows"
    assert ntied == 1, "the tie count is correct — exactly as in the 272 rows"
    # THE BLINDNESS, stated as an assertion: an instrument reading only these
    # two numbers sees a maximum of 9.0, unambiguously attained by one
    # candidate, and reports NOTHING. The wrong answer is invisible to it.

    # --- GREEN: the winner's own value catches it on that same firing.
    st = _native.selector_audit_stats()
    assert st["disagreements"] == 1
    assert "3.0" in st["first_row"] and "9.0" in st["first_row"]


# --- 4. THE INVARIANT HOLDS ON A REAL WORKLOAD ------------------------------

def test_the_invariant_holds_across_a_seed_booted_rule_fixpoint():
    """WHERE THE CHECK RUNS on something that is not a toy: boot the real seed
    corpus, ingest an observation, and run the `run_rules` fixpoint under
    `strict`. Every selector firing inside that fixpoint is audited by the
    EVALUATOR, so coverage does not depend on this test knowing which rules use
    a selector — a single contradiction anywhere in the fixpoint would raise.

    A null here is a null about THIS workload on THIS machine (§8). It bounds
    nothing about a workload this does not exercise, and it does not explain the
    unreproduced §4.2 anomaly — it makes a recurrence DIAGNOSABLE, not less
    likely."""
    pytest.importorskip("numpy")
    import domains.reflective_faculty as rf
    from substrate.boot_core import boot_core, load_seeds_into

    _native.selector_audit_reset()
    _native.selector_audit_enable("strict")
    s, ag = boot_core()
    native = rf._native_eval2(s)
    load_seeds_into(s, ag, ["vision_sdloop"])
    if s.node(ag)["attrs"].get("codebook_epoch") is None:
        s.set_attr(ag, "codebook_epoch", 0.0)
    obs = s.add_node("Observation", {
        "signature": [["cell", 0, 0, "red"], ["cell", 0, 1, "blue"]],
        "key": ["probe"], "vq": 1.0,
        "dim_types": ["pred", "coord:r", "coord:c", "val"],
        "status": "pending"})
    s.add_edge(ag, "observed", obs)
    native.run_rules()

    st = _native.selector_audit_stats()
    assert st["disagreements"] == 0
    # DISCRIMINATING: the audit must actually have RUN. A green from zero
    # firings is the INERT-INSTRUMENT failure this whole file exists to avoid
    # (VISION_PROTOCOL §12.1 — nine inert instruments, one of them a grep).
    assert st["firings"] > 0, "no selector fired — the gate would be vacuous"

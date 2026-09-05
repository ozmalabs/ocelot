"""Gates for the TRAIT -> DRIVE HOMEOSTATIC REGULATION TABLE (tasks 3+4,
domains/trait_modulator_bridge.py): the generalisation of disposition's
openness-only homeostasis to a data table that regulates each cognitive-style
trait from its GOVERNING drive/modulator.

The table under test:

  trait        governing drive/modulator      evidence
  -----------  -----------------------------  --------------------------------
  abstraction  COMPETENCE (mod_competence)     low competence  => -1 (concrete)
                                               high competence => +1 (abstract)
  skepticism   EXPLORATION/CERTAINTY           high uncertainty => +1 (demand)
               (exploration_urge / securing)   confirmed certainty => -1 (relax)
  openness     — NO clean drive                graph pollution/starvation (its
                                               own substrate-hygiene homeostasis)

What is proved here:

  A. THE DRIVERS READ THE DRIVE, HAND A SIGN. competence_trait_evidence /
     exploration_trait_evidence turn the live modulator/drive numbers into a
     signed sigma against the modulator's OWN knobs (competence_lo, uncertainty_
     hi) — a decision-free read; no trait value is computed in Python.

  B. DRIVE-DRIVEN CRYSTALLISATION (produced, not hand-set). A sustained
     competence regime crystallises abstraction (UP from high, DOWN from measured-
     low competence); a sustained exploration/uncertainty regime crystallises
     skepticism (UP from high uncertainty, DOWN from confirmed certainty) — each
     via the CAN identity-feedback rule, one ±1 quantum per tick, read back from
     the produced identity_field.

  C. NEUTRAL DRIVE => NO DRIFT. A default modulator (competence 0, exploration_
     urge 0) injects 0 evidence for the drive-regulated traits => abstraction and
     skepticism do not move (default == today).

  D. personality_homeostasis_step RUNS THE WHOLE TABLE in one call and CONVERGES
     (bounded servo): all three traits crystallise to their ±4 ceilings and stay
     there — no runaway. Per-trait INDEPENDENCE holds across the batched
     relaxation (an un-evidenced established trait is not eroded).

  E. THE OPENNESS RECONCILIATION is the honest one: openness is NOT in the drive
     row (drive_trait_evidence exposes only abstraction + skepticism); it keeps
     its graph-hygiene homeostasis. personality_homeostasis_step still moves it
     from the pollution/starvation signal.
"""
from __future__ import annotations

from substrate_rs import _native

import domains.analogy_search as asr
import domains.disposition as disp
import domains.relation_grounding as rg
import domains.trait_modulator_bridge as tmb

_NT = ("Agent", "Concept", "Microtheory", "QualiaDimension", "DimensionEdgeRole")
_ET = tuple(set(rg.RELATION_EDGE_TYPES) | {"has_concept", "genls", "is_a",
            "built_from", "depends_on", "grounds"})


def _open(s):
    for a in _NT:
        for b in _NT:
            for et in _ET:
                s.add_production({"src": {"type": a, "var": "x"},
                                  "edge_type": et, "tgt": {"type": b, "var": "y"},
                                  "where": None,
                                  "weight": {"type": "Lit", "value": 1.0},
                                  "provenance": "test:open"})


class Agent:
    """A `.s` substrate + `.agent` hub — identical to the other trait tests."""

    def __init__(self):
        asr._QUALIA_SCHEMA_CACHE.clear()
        self.s = _native.Substrate()
        self.agent = self.s.add_node("Agent", {})
        _open(self.s)


def _mt(s, name):
    return s.add_node("Microtheory", {"name": name})


def _concept(s, m, name, **attrs):
    a = {"name": name}
    a.update(attrs)
    c = s.add_node("Concept", a)
    s.add_edge(m, "has_concept", c)
    return c


# The regime overrides (all EXISTING knobs — no new drives).
_HIGH_COMP = dict(competence_base=80.0)   # >= competence_full - competence_lo (70)
_LOW_COMP = dict(competence_base=10.0)    # 0 < c < competence_lo (30) => measured low
_HIGH_UNC = dict(exploration_urge=200.0)  # > uncertainty_hi (100)
_CERTAINTY = dict(exploration_urge=10.0)  # 0 < urge < uncertainty_lo (25) => confirmed


# ===========================================================================
# A. THE DRIVERS READ THE DRIVE, HAND A SIGN (decision-free reads).
# ===========================================================================
def test_competence_evidence_reads_the_competence_modulator():
    """competence_trait_evidence maps ms.competence to a signed abstraction sigma
    against the modulator's OWN competence_lo / (full - lo) marks."""
    hi = Agent()
    _hub, ms = tmb.ensure_modulator_state(hi, ms_over=_HIGH_COMP)
    ev = tmb.competence_trait_evidence(hi, ms=ms)
    assert ev["competence"] == 80.0
    assert ev["competence_hi"] == 70.0                 # competence_full - competence_lo
    assert ev["sigma"] == 1.0                          # high => reach for abstraction

    lo = Agent()
    _hub, ms = tmb.ensure_modulator_state(lo, ms_over=_LOW_COMP)
    ev = tmb.competence_trait_evidence(lo, ms=ms)
    assert ev["competence"] == 10.0
    assert ev["competence_lo"] == 30.0
    assert ev["sigma"] == -1.0                          # measured-low => concrete


def test_exploration_evidence_reads_the_exploration_drive():
    """exploration_trait_evidence maps the leading drive's exploration_urge (the
    MicroPsi uncertainty heuristic) to a signed skepticism sigma against
    uncertainty_hi / uncertainty_lo."""
    unc = Agent()
    _hub, ms = tmb.ensure_modulator_state(unc, drive_over=_HIGH_UNC)
    ev = tmb.exploration_trait_evidence(unc, ms=ms)
    assert ev["exploration_urge"] == 200.0
    assert ev["uncertainty_hi"] == 100.0
    assert ev["sigma"] == 1.0                           # high uncertainty => skeptical

    cert = Agent()
    _hub, ms = tmb.ensure_modulator_state(cert, drive_over=_CERTAINTY)
    ev = tmb.exploration_trait_evidence(cert, ms=ms)
    assert ev["exploration_urge"] == 10.0
    assert ev["sigma"] == -1.0                          # confirmed certainty => relax


def test_drive_trait_evidence_exposes_only_the_drive_regulated_traits():
    """The drive row is abstraction + skepticism ONLY — openness is NOT drive-
    regulated (the honest reconciliation: it keeps its graph-hygiene homeostasis)."""
    a = Agent()
    _hub, ms = tmb.ensure_modulator_state(a, ms_over=_HIGH_COMP, drive_over=_HIGH_UNC)
    ev = tmb.drive_trait_evidence(a, ms=ms)
    assert set(ev.keys()) == {"abstraction", "skepticism", "readings"}
    assert "openness" not in ev
    assert ev["abstraction"] == 1.0
    assert ev["skepticism"] == 1.0


# ===========================================================================
# B. DRIVE-DRIVEN CRYSTALLISATION — produced by the rule, not hand-set.
# ===========================================================================
def test_high_competence_crystallises_abstraction_up():
    """Sustained HIGH competence crystallises abstraction UP one quantum/tick to
    its ceiling — PRODUCED by the relaxation. (The batched identity-feedback path
    has a one-tick ledger warmup before the first quantum, then marches ±1/tick.)"""
    a = Agent()
    _hub, ms = tmb.ensure_modulator_state(a, ms_over=_HIGH_COMP)
    before = disp.trait_level(a, "abstraction")
    out1 = tmb.drive_homeostasis_step(a, ms=ms, ticks=1)
    assert out1["evidence"]["abstraction"] == 1.0
    # after two steps the field has moved by at least one quantum (never a jump).
    tmb.drive_homeostasis_step(a, ms=ms, ticks=1)
    assert abs(disp.trait_field(a, "abstraction")) >= 1.0
    for _ in range(6):
        tmb.drive_homeostasis_step(a, ms=ms, ticks=1)
    after = disp.trait_level(a, "abstraction")
    assert after > before and after == 4, (before, after)


def test_low_competence_crystallises_abstraction_down():
    """Sustained MEASURED-LOW competence crystallises abstraction DOWN (concrete/
    coarse — the MicroPsi 'low competence -> coarse' rule)."""
    a = Agent()
    _hub, ms = tmb.ensure_modulator_state(a, ms_over=_LOW_COMP)
    out1 = tmb.drive_homeostasis_step(a, ms=ms, ticks=1)
    assert out1["evidence"]["abstraction"] == -1.0
    for _ in range(5):
        tmb.drive_homeostasis_step(a, ms=ms, ticks=1)
    assert disp.trait_level(a, "abstraction") == -4


def test_high_uncertainty_crystallises_skepticism_up():
    """Sustained HIGH exploration_urge (uncertainty) crystallises skepticism UP."""
    a = Agent()
    _hub, ms = tmb.ensure_modulator_state(a, drive_over=_HIGH_UNC)
    out1 = tmb.drive_homeostasis_step(a, ms=ms, ticks=1)
    assert out1["evidence"]["skepticism"] == 1.0
    tmb.drive_homeostasis_step(a, ms=ms, ticks=1)
    assert abs(disp.trait_field(a, "skepticism")) >= 1.0
    for _ in range(6):
        tmb.drive_homeostasis_step(a, ms=ms, ticks=1)
    assert disp.trait_level(a, "skepticism") == 4


def test_confirmed_certainty_crystallises_skepticism_down():
    """An ACTIVE low-uncertainty regime (certainty confirmed) crystallises
    skepticism DOWN toward credulous."""
    a = Agent()
    _hub, ms = tmb.ensure_modulator_state(a, drive_over=_CERTAINTY)
    out1 = tmb.drive_homeostasis_step(a, ms=ms, ticks=1)
    assert out1["evidence"]["skepticism"] == -1.0
    for _ in range(5):
        tmb.drive_homeostasis_step(a, ms=ms, ticks=1)
    assert disp.trait_level(a, "skepticism") == -4


def test_crystallisation_is_produced_by_the_rule_not_hand_written():
    """The drive-driven trait is moved ONLY by the identity-feedback rule: the
    evidence ledger accrued and the mirrored axis attr equals the produced
    identity_field (a mirror, never a hand-set outcome)."""
    a = Agent()
    _hub, ms = tmb.ensure_modulator_state(a, ms_over=_HIGH_COMP)
    concept = disp.ensure_trait(a, "abstraction")
    tmb.drive_homeostasis_step(a, ms=ms, ticks=3)
    attrs = a.s.node(concept)["attrs"]
    assert int(attrs.get("identity_evidence_confirm") or 0) >= 1
    assert float(attrs.get("abstraction_field")) == float(attrs.get("identity_field"))


# ===========================================================================
# C. NEUTRAL DRIVE => NO DRIFT (default == today).
# ===========================================================================
def test_neutral_drive_injects_zero_evidence():
    """A default modulator build (competence 0, exploration_urge 0) reads NEUTRAL
    on both drive-regulated axes — the unmeasured drive state is not 'low'."""
    a = Agent()
    _hub, ms = tmb.ensure_modulator_state(a)             # default knobs
    assert a.s.node(ms)["attrs"].get("competence") == 0.0
    ev = tmb.drive_trait_evidence(a, ms=ms)
    assert ev["abstraction"] == 0.0
    assert ev["skepticism"] == 0.0


def test_neutral_drive_does_not_drift_the_traits():
    """Repeated steps under a neutral drive move NO drive-regulated trait — the
    homeostasis has a genuine neutral zone; a fresh agent does not drift."""
    a = Agent()
    _hub, ms = tmb.ensure_modulator_state(a)
    before = disp.trait_vector(a, ensure=True)
    for _ in range(8):
        out = tmb.drive_homeostasis_step(a, ms=ms, ticks=1)
        assert out["moved"] == []
    after = disp.trait_vector(a, ensure=False)
    assert after["abstraction"] == before["abstraction"]
    assert after["skepticism"] == before["skepticism"]


# ===========================================================================
# D. personality_homeostasis_step — the whole table, convergent + independent.
# ===========================================================================
def _pollute(agent, n=12):
    m = _mt(agent.s, "junk")
    for i in range(n):
        _concept(agent.s, m, f"junk_{i}", minted_referent=True,
                 definition=f"junk {i}")


def test_personality_step_runs_the_whole_table():
    """One personality_homeostasis_step reads all three governing signals and
    crystallises all three traits: openness DOWN (pollution), abstraction UP
    (high competence), skepticism UP (high uncertainty)."""
    a = Agent()
    disp.set_disposition_seed(a, 0.0)
    _pollute(a)
    _hub, ms = tmb.ensure_modulator_state(a, ms_over=_HIGH_COMP, drive_over=_HIGH_UNC)
    r = tmb.personality_homeostasis_step(a, ms=ms, ticks=1)
    assert r["evidence"] == {"openness": -1.0, "abstraction": 1.0,
                             "skepticism": 1.0}
    v = disp.trait_vector(a, ensure=False)
    assert v == {"openness": -1, "abstraction": 1, "skepticism": 1}, v


def test_personality_step_converges_no_runaway():
    """Repeated whole-table steps drive every trait to its ±4 ceiling and STAY
    there — a bounded servo, monotone (no oscillation), never exceeding the cap."""
    a = Agent()
    disp.set_disposition_seed(a, 0.0)
    _pollute(a)
    _hub, ms = tmb.ensure_modulator_state(a, ms_over=_HIGH_COMP, drive_over=_HIGH_UNC)
    seq = []
    for _ in range(10):
        tmb.personality_homeostasis_step(a, ms=ms, ticks=1)
        seq.append(dict(disp.trait_vector(a, ensure=False)))
    last = seq[-1]
    assert last == {"openness": -4, "abstraction": 4, "skepticism": 4}, last
    ops = [v["openness"] for v in seq]
    abs_ = [v["abstraction"] for v in seq]
    sks = [v["skepticism"] for v in seq]
    assert min(ops) >= -4 and max(abs_) <= 4 and max(sks) <= 4    # never exceeds cap
    assert ops == sorted(ops, reverse=True)                       # monotone down
    assert abs_ == sorted(abs_) and sks == sorted(sks)            # monotone up


def test_personality_step_preserves_per_trait_independence():
    """An ESTABLISHED skepticism that this step gives NO drive evidence for is not
    eroded by crystallising abstraction — the batched relaxation snapshots/restores
    the un-evidenced trait (per-trait independence across the whole table)."""
    a = Agent()
    # establish skepticism away from default via its OWN drive first.
    _hub, ms = tmb.ensure_modulator_state(a, drive_over=_HIGH_UNC)
    for _ in range(3):
        tmb.drive_homeostasis_step(a, ms=ms, ticks=1)
    est_sk = disp.trait_level(a, "skepticism")
    assert est_sk >= 2

    # now switch to a HIGH-competence + CONFIRMED-certainty... no: to isolate,
    # give competence high (abstraction moves) and NO uncertainty signal
    # (skepticism gets 0 evidence => must hold at est_sk).
    a.s.set_attr(ms, "competence", 80.0)
    a.s.set_attr(ms, "competence_epoch", -1.0)
    lead = tmb._leading_drive(a.s, ms)
    a.s.set_attr(lead, "exploration_urge", 0.0)          # no uncertainty => 0 skept ev
    ev = tmb.drive_trait_evidence(a, ms=ms)
    assert ev["abstraction"] == 1.0
    assert ev["skepticism"] == 0.0                        # no evidence this step
    for _ in range(3):
        tmb.drive_homeostasis_step(a, ms=ms, ticks=1)
    assert disp.trait_level(a, "skepticism") == est_sk    # UNCHANGED (independent)
    assert disp.trait_level(a, "abstraction") >= 1        # the evidenced one moved


# ===========================================================================
# E. THE OPENNESS RECONCILIATION — the honest exception.
# ===========================================================================
def test_openness_is_not_drive_regulated_but_still_moves_from_hygiene():
    """openness has NO drive row (drive_trait_evidence omits it), yet
    personality_homeostasis_step still moves it from the graph pollution/
    starvation signal — the one trait kept on substrate-hygiene homeostasis."""
    a = Agent()
    disp.set_disposition_seed(a, 0.0)
    _pollute(a)
    # a NEUTRAL drive so ONLY openness has evidence this step.
    _hub, ms = tmb.ensure_modulator_state(a)
    ev = tmb.drive_trait_evidence(a, ms=ms)
    assert ev["abstraction"] == 0.0 and ev["skepticism"] == 0.0   # drives neutral
    before = disp.trait_level(a, "openness")
    for _ in range(3):
        r = tmb.personality_homeostasis_step(a, ms=ms, ticks=1)
        assert r["evidence"]["openness"] == -1.0                  # pollution => down
    after = disp.trait_level(a, "openness")
    assert after < before                                          # moved conservative
    # abstraction/skepticism did NOT drift (neutral drive).
    assert disp.trait_level(a, "abstraction") == 0
    assert disp.trait_level(a, "skepticism") == 0


def test_personality_step_is_a_noop_on_non_live_substrate():
    """The whole-table step degrades honestly on a handle with no engine."""
    class Dead:
        s = object()
    out = tmb.personality_homeostasis_step(Dead())
    assert out["moved"] == []

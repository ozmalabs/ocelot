"""Psychosis-grounding seed: the engine's EXISTING grounding/collapse operation,
run in a failure regime, reproduces the two native psychosis forms plus the
sycophantic-confirmer amplification and grounding-source correction.

Anti-plant discipline (mirrors the seizure gate):
  - byte-identity-when-off: adding this pathology capability MUST NOT change a
    graph that does not enable it (P7).
  - the pathology must EMERGE from the friction/confirmer dial under a MATCHED
    control (identical belief + params, only the (obs, w_ext, obs2, w_conf)
    schedule differs), and must be ABLE TO FAIL (friction corrects; no-friction
    self-grounds -- if either flipped, the demo would be a plant).

All dynamics run in the real engine (run_rules + native fold_clock_edge over the
psychosis_grounding DSL rule); the harness only sets channels and reads state.
NO new Rust -- the seed uses existing arithmetic Terms only.
"""
from __future__ import annotations

import json
import os

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter  # noqa: E402
import scripts.psychosis_grounding_demo as demo  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = os.path.join(ROOT, "seeds", "psychosis_grounding.json")


# ---------------------------------------------------------------- P7 safety
def test_byte_identity_when_off():
    """A Belief with pg_enabled=0 (or the seed never loaded) is node-for-node
    identical after ticking; the SAME belief with pg_enabled=1 genuinely
    evolves -> the capability is live but inert by default."""
    chk = demo.byte_identity_check(n=40)
    assert chk["off_equals_none"], "off-state diverged from seed-absent state"
    assert chk["on_evolved"], "pg_enabled=1 did not evolve -> capability is dead, not off"


def test_seed_uses_no_unknown_terms():
    """Source audit: the seed rule bodies reference only Term types that exist in
    the stock engine (no new Rust). If an unknown Term were used, the loader
    would drop the rule and the whole demo would fail; this makes the constraint
    explicit."""
    known = {"Attr", "Lit", "Var", "Plus", "Minus", "Times", "Div", "Neg", "Abs",
             "Max", "Min", "Eq", "Gt", "Lt", "Not", "And", "Or"}
    txt = open(SEED).read()
    manifest = json.loads(txt)
    # every rule installs cleanly on a stock agent (proves the Terms resolve)
    a = WorldAdapter(seeds=())
    a.inner.load_seed_manifest(manifest, a.agent)
    # and the only Term "type" tokens present are known ones
    import re
    types = set(re.findall(r'"type":\s*"([A-Za-z_][A-Za-z0-9_]*)"', txt))
    # node/production structural types are not Terms; drop the ones we know are structural
    structural = {"Belief", "PsyConfig"}
    unknown = types - known - structural
    assert not unknown, f"seed references non-Term/unknown types: {unknown}"


# ---------------------------------------------------------------- P1/P2 forms
def test_friction_corrects_and_no_friction_self_grounds():
    """MATCHED CONTROL + ABLE TO FAIL: identical belief (poorly grounded, in the
    wrong basin). With reality friction it corrects to truth; with no friction it
    self-grounds in the wrong basin. If friction failed to correct, or no-friction
    corrected on its own, this fails (the pathology would be planted / absent)."""
    a = demo.summarise(demo.run_arm(demo.sched_friction(), n=90))
    b = demo.summarise(demo.run_arm(demo.sched_no_friction(), n=90))
    assert a["committed_final"] == "R" and a["dist_to_truth"] < 0.5, ("friction did not correct", a)
    assert b["committed_final"] == "W" and b["persistence_W"] == 1.0, ("no-friction did not self-ground", b)


# ---------------------------------------------------------------- P5 amplify
def test_confirmer_amplifies_confidence():
    """A sycophantic confirmer (obs2=belief) inflates confidence far faster than
    self-confirmation alone -- false external validation."""
    tb = demo.run_arm(demo.sched_no_friction(), n=15)
    tc = demo.run_arm(demo.sched_confirmer_only(), n=15)
    conf_b = tb[-1][1]
    conf_c = tc[-1][1]
    assert conf_c > conf_b + 1.5, ("confirmer did not amplify confidence", conf_b, conf_c)


# ---------------------------------------------------------------- P4b the flip
def test_confirmer_flips_outcome_matched_control():
    """THE 'AI psychosis' result, matched control: identical weak reality friction
    (obs=truth, w_ext fixed); adding ONLY a sycophantic confirmer flips the
    outcome from correction (R) to persistent delusion (W)."""
    p = demo.ARCH
    control = demo.summarise(demo.run_arm(demo.sched_reality_weak(), n=120))
    flipped = demo.summarise(demo.run_arm(demo.sched_reality_weak_plus_confirmer(), n=120))
    assert control["committed_final"] == "R", ("reality-friction control should correct", control)
    assert flipped["committed_final"] == "W", ("confirmer should flip to delusion", flipped)


def test_emergent_confirmer_fold_is_monotone():
    """EMERGENCE: sweeping confirmer strength there is a single threshold w_conf*
    strictly inside (0, 1.5) -- below it corrects, above it self-grounds -- and
    the fold is monotone (a real bistable boundary, not a scripted switch)."""
    p = demo.ARCH
    outcomes = []
    for wc in [0.0, 0.2, 0.4, 0.5, 0.7, 1.0, 1.5]:
        sched = lambda t, b, wc=wc: {"obs": p.basin_r, "w_ext": p.w_reality_weak,
                                     "obs2": b, "w_conf": wc}
        outcomes.append(demo.summarise(demo.run_arm(sched, n=120))["committed_final"])
    # monotone: some prefix of R then all W, with at least one of each (a real fold)
    assert "R" in outcomes and "W" in outcomes, ("no fold", outcomes)
    first_W = outcomes.index("W")
    assert all(o == "R" for o in outcomes[:first_W]), ("non-monotone fold", outcomes)
    assert all(o == "W" for o in outcomes[first_W:]), ("non-monotone fold", outcomes)


# ---------------------------------------------------------------- P6 recovery
def test_grounding_source_recovers_and_escape_time_decreases():
    """From the self-grounded (delusional) state, a disconfirming grounding source
    pulls the belief back to truth, and the stronger the source the faster the
    escape (a graded, emergent recovery -- the design principle 'grounding source,
    not confirmation mirror')."""
    p = demo.ARCH
    escapes = []
    for gw in [0.3, 0.6, 1.0, 2.0]:
        traj = demo.run_arm(demo.sched_recovery(t_switch=20, gs_w=gw), n=120)
        esc = next((t - 20 for t in range(20, 120) if not demo.is_W(traj[t][2])), None)
        assert esc is not None, ("grounding source failed to recover at w=%s" % gw)
        escapes.append(esc)
    assert escapes == sorted(escapes, reverse=True), ("escape time not monotone", escapes)


# ---------------------------------------------------------------- P8 folie a deux
def test_folie_a_deux_persists_then_collapses_on_grounding():
    """Two mutually-confirming beliefs (each the other's confirmer, NO external
    anchor) both persist in the wrong basin; grounding ONE member collapses BOTH
    -- the closed loop is only stable while closed (the confirmer is scale-agnostic)."""
    fad = demo.run_folie_a_deux(n_pre=30, n_post=40, gs_w=1.5)
    pre1 = demo.summarise(fad["b1"][:30])
    pre2 = demo.summarise(fad["b2"][:30])
    post1 = demo.summarise(fad["b1"])
    post2 = demo.summarise(fad["b2"])
    assert pre1["committed_final"] == "W" and pre2["committed_final"] == "W", "dyad did not self-sustain"
    assert post1["committed_final"] == "R" and post2["committed_final"] == "R", "grounding one did not collapse both"

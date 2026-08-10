"""RUNG 225000 gate — FOLD the flash consume-marking (223000) onto the object-
permanence tracker (224000) to close the trail/consume residual.

The 224 tracker translates the tracked object (misses the dropped trail cells); the
fold marks the flash-localised VACATED cells as consumed to a DISCOVERED trail
value. Gated on synthetic trail/consume scenes (the honest twin of the real ls20
mechanic): the ablation (+flash vs 224-alone) is the gate; the flash-localised
consumed set must beat a random-flash control; the marking is graph-native and the
flash is honestly coarse (precision < 1, not an oracle).
"""
import re
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT), str(_ROOT / "scripts"), str(_ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.arc_ls20_consume import (  # noqa: E402
    record_episode, eval_arm, ConsumeTracker, ConsumeArena, _DIRS,
)
from worlds.arc_ls20_percell_track import LiveObjectTracker  # noqa: E402
from worlds.arc_ls20_percell import Percell  # noqa: E402

_SEEDS = 4
_STEPS = 18


def _collect():
    """Run the paired ablation over a few seeds; return pooled per-step arrays."""
    f1 = {a: [] for a in ("translate", "flash", "random", "blind_all")}
    cf1 = {a: [] for a in ("flash", "random")}
    prec = {"flash": []}
    for s in range(_SEEDS):
        rec = record_episode(s, steps=_STEPS)
        per = {a: eval_arm(a, rec, seed=s) for a in f1}
        m = min(len(per[a][0]) for a in f1)
        for a in f1:
            f1[a].extend(per[a][0][:m])
        for a in cf1:
            cf1[a].extend([p[2] for p in per[a][1][:m]])
        prec["flash"].extend([p[0] for p in per["flash"][1][:m]])
    return f1, cf1, prec


# module-level cache so the (slow) onset-eye episodes run once for all gates
_F1, _CF1, _PREC = _collect()


def test_flash_fold_beats_224_alone_HEADLINE():
    """G-trail-closed: the flash-folded change-set strict-F1 BEATS 224-alone. The
    ablation IS the gate -- if +flash does not beat, the flash does not localise the
    consumed cells."""
    transl = float(np.mean(_F1["translate"]))
    flash = float(np.mean(_F1["flash"]))
    assert flash > transl, f"flash fold ({flash:.3f}) must beat 224-alone ({transl:.3f})"
    # a real, not marginal, closure of the trail residual
    assert flash - transl > 0.02, f"flash improvement {flash - transl:.3f} must be substantive"


def test_flash_localises_consume_above_random():
    """G-flash-localises-consume: the flash-localised predicted-consumed set matches
    the actual consumed set far better than a random-flash control."""
    cf_flash = float(np.mean(_CF1["flash"]))
    cf_random = float(np.mean(_CF1["random"]))
    assert cf_flash > cf_random + 0.2, \
        f"flash consume-F1 ({cf_flash:.3f}) must beat random ({cf_random:.3f}) decisively"


def test_random_flash_is_the_anti_rig_null():
    """The random-flash control does NOT beat 224-alone -> the win is the flash's
    LOCALISATION, not the marking mechanism."""
    transl = float(np.mean(_F1["translate"]))
    rand = float(np.mean(_F1["random"]))
    assert rand <= transl + 0.005, \
        f"random-flash ({rand:.3f}) must NOT beat 224-alone ({transl:.3f}) -- anti-rig"


def test_over_prediction_is_punished():
    """blind_all (mark ALL vacated cells consumed) scores BELOW 224-alone -- the
    discrimination the flash provides is what matters."""
    transl = float(np.mean(_F1["translate"]))
    blind = float(np.mean(_F1["blind_all"]))
    assert blind < transl, f"blind_all ({blind:.3f}) must score below 224-alone ({transl:.3f})"


def test_flash_is_coarse_not_an_oracle():
    """HONESTY BOUND: the flash consume PRECISION < 1.0 -- the flash localises a
    coarse REGION, it does NOT hand the model the exact consumed set."""
    prec = float(np.mean(_PREC["flash"]))
    assert prec < 0.98, f"flash consume precision ({prec:.3f}) must be < 1 (not an oracle)"
    assert prec > 0.4, f"flash consume precision ({prec:.3f}) must be well above chance"


def test_fold_default_off_is_224_byte_identical():
    """Default-OFF byte-identical: ConsumeTracker in 'translate' mode loads NO
    consume rules and predicts EXACTLY the 224 LiveObjectTracker (the fold off keeps
    224 unchanged, cell-for-cell)."""
    rng = np.random.default_rng(7)
    arena = ConsumeArena(rng, n=24, block=5, step=6, csize=3)
    # a bare 224 tracker vs a translate-mode ConsumeTracker on identical frames
    bare_pc = Percell(); bare = LiveObjectTracker(bare_pc, cap=200, n_field=2)
    fold = ConsumeTracker(mode="translate", cap=200, n_field=2)
    dirs = list(_DIRS)
    for t in range(12):
        a = dirs[t % 4]
        prev, nxt, flash, consumed = arena.step_action(a)
        p_bare = bare.predict(prev, a)
        p_fold = fold.predict(prev, a, [])
        assert np.array_equal(p_bare, p_fold), f"step {t}: fold-off must equal 224 exactly"
        bare.observe(prev, nxt, a)
        fold.observe(prev, nxt, a)
        if not (arena.f0 < arena.ar < arena.f1 - arena.block and
                arena.f0 < arena.ac < arena.f1 - arena.block):
            arena.ar = (arena.f0 + arena.f1) // 2; arena.ac = (arena.f0 + arena.f1) // 2
    # a translate-mode tracker never installed the consume machinery
    assert not any(fold.pc.s.nodes("ConsumeState")), "fold-off must not arm consume state"


def test_consume_value_discovered_in_the_graph():
    """The trail value T lives in a graph ConsumeHypothesis (minted by cm_mint from
    observation), not a Python constant -- and it is discovered ORACLE-FREE."""
    rng = np.random.default_rng(3)
    rec = record_episode(3, steps=_STEPS)
    trk = ConsumeTracker(mode="flash")
    for (action, prev, nxt, flash, consumed, onset) in rec:
        trk.observe(prev, nxt, action)   # NB: consumed set NOT passed -> oracle-free
    hyps = list(trk.pc.s.neighbours(trk.pc.g, "has_consume"))
    assert hyps, "a ConsumeHypothesis must be minted from observation"
    v = int(float(trk.pc.s.node(hyps[0])["attrs"]["value"]))
    from worlds.arc_ls20_consume import TRAIL
    assert v == TRAIL, f"the discovered trail value ({v}) must match the world trail ({TRAIL})"


def test_no_hardcoded_consume_table_in_agent_path():
    """SOURCE-AUDIT: the agent (ConsumeTracker + the seed rules) reads no ground-
    truth consume table; the trail value is minted from observation."""
    src = (_ROOT / "worlds" / "arc_ls20_consume.py").read_text()
    agent_src = src[src.index("class ConsumeTracker"):]
    assert not re.findall(r"_CONSUME_TABLE|consume_map\s*=", agent_src)
    # the AGENT never WRITES the trail value into a grid (only the ARENA does)
    assert not re.findall(r"g\[[^\]]+\]\s*=\s*TRAIL", agent_src)


def test_consume_seed_rules_default_off():
    """The consume rules are guarded on consume_on==1: a plain Percell (no flag) runs
    run_rules with the rules loaded but they never fire (default-OFF)."""
    from domains.ls20_consume_seed import RULES
    pc = Percell()
    for r in RULES:
        pc.n.add_rule(r)
    pc.n.set_attr(pc.g, "obs_consume_value", 11.0)
    pc.n.set_attr(pc.g, "phase", "consume_obs")
    pc.n.run_rules()   # consume_on is unset -> no ConsumeHypothesis minted
    assert not list(pc.s.neighbours(pc.g, "has_consume")), \
        "consume rules must be default-OFF without consume_on==1"

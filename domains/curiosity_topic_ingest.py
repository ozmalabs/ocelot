"""curiosity_topic_ingest — MECHANICAL adapter wiring `learning_progress_curiosity`
(block 202000, `seeds/learning_progress_curiosity.json`) into gap-awareness's
PROACTIVE topic-selection trigger (`seeds/curiosity_topic_selection.json::
lp_mint_topic_gap`), for the noisy-TV-resistant "what should I learn about
next" decision named in `docs/research/theory_convergence/
RAVANA_CONVERGENCE_AUDIT.md` §6.2.

Mirrors `domains/doom_active_explore_ingest.py`'s structure and discipline
one-for-one, substituting a lexical-grounding sensor for that module's
spatial info-gain sensor: NO decision here (CLAUDE.md). Every function either
(a) creates the graph-resident curiosity state (mechanical construction, same
class as `doom_active_explore_ingest.install_curiosity`), (b) reads a REAL
SENSOR value off the agent's own already-existing lexical state
(`WorldAdapter.taught_signs()` — how many words in a candidate topic phrase
are still ungrounded, exactly the tokenisation `WorldAdapter.ground_unknowns`
itself uses), or (c) attempts real grounding via the agent's own existing
`ground_unknowns` teacher loop (world I/O — the teacher decides meaning, this
module is the per-tick scheduling of the attempt). WHICH topic becomes a
flagged gap is the `lp_mint_topic_gap` RULE, reading `attended` — a value the
pre-existing `lp_*` rules compute entirely from the two-timescale
learning-progress differential, never from raw surprise and never decided in
Python.

Persistent curiosity state lives in the GRAPH (topic-keyed AttentionItem
nodes under the agent's own CuriosityHub), never in Python (CLAUDE.md: no
Python agent state). This module only find-or-creates by key and sets the
sensor `obs`.
"""
from __future__ import annotations

import json
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LP_SEED = os.path.join(_ROOT, "seeds", "learning_progress_curiosity.json")
_TOPIC_SEED = os.path.join(_ROOT, "seeds", "curiosity_topic_selection.json")

# 202000 curiosity params, reused VERBATIM from scripts/learning_progress_measure.py
# (the calibrated, gated values the original noisy-TV proof tuned and validated —
# not re-tuned here). mode=0 (learning-progress-gated, the noisy-TV-resistant arm);
# a caller demonstrating the raw-surprise falsifier passes mode=1.0 explicitly.
PARAMS = dict(
    enabled=1.0, mode=0.0,
    hl_min=1.0, hl_scale=4.0, interest_c0=1024.0, attend_thresh=256.0,
    progress_floor=10.0, surprise_floor=4.0,
    fast_div=3.0, slow_div=20.0, blend_div=2.0,
)

# an AttentionItem's full initial state, plus the two attrs this consumer adds:
# `topic` (the candidate topic's string key, read by lp_mint_topic_gap) and
# `topic_gap_noted` (that rule's own mint-once guard — never set here, only
# ever read/written by the seed rule; listed for documentation only).
ITEM_INIT = dict(
    held=0.0, obs=0.0, input_epoch=0.0, epoch=-1.0, residual=0.0,
    fast_res=0.0, slow_res=0.0, learning_progress=0.0, smoothed_progress=0.0,
    interest_half_life=1.0, last_boost_epoch=0.0, interest=1024.0, attended=0.0,
)

_STRIP = ".,?!;:()[]\"'"

# UNIT CONVERSION, not a decision knob: the integer EMAs (fast_div=3, slow_div=20)
# and the progress/surprise floors (10 / 4) in PARAMS are the calibrated values
# from the ORIGINAL proof (scripts/learning_progress_measure.py), tuned against
# residual swings on the order of tens-to-hundreds (its LEVELS were 40-220,
# NOISE_HI=240). A raw word count (0-6ish) is too small a dynamic range for that
# SAME integer machinery: IDiv(residual, 20) truncates to 0 whenever residual<20,
# so slow_res would never move off its ITEM_INIT sentinel and learning_progress
# would read a permanently-wrong constant -- exactly the integer-truncation
# failure mode the original RESULTS doc's own "Honest residuals" section
# documents for a too-fine signal. WORD_SENSOR_SCALE rescales the honest
# word-count sensor into the SAME dynamic range the calibrated PARAMS already
# assume, without touching a single decision threshold -- the doom consumer
# made the analogous per-domain adjustment (its own blend_div=8 vs vision's
# blend_div=2) for the identical reason: same mechanism, different sensor
# units, one honest rescale.
WORD_SENSOR_SCALE = 40.0


def install_curiosity(wa, *, params=None):
    """Create the agent-scoped CuriosityHub{params} (mechanical construction of
    the opt-in state, same class as doom_active_explore_ingest.install_curiosity).
    Loads the two self_load_only seeds (learning_progress_curiosity,
    curiosity_topic_selection) if their rules are not already installed. Returns
    the hub NodeID. Idempotent: a second call reuses the existing hub."""
    S, I = wa.s, wa.inner
    existing = _hub(wa)
    if existing is not None:
        return existing
    I.load_seed_manifest(json.load(open(_LP_SEED)), wa.agent)
    I.load_seed_manifest(json.load(open(_TOPIC_SEED)), wa.agent)
    hub = S.add_node("CuriosityHub", {"kind": "gap_topic_selection"})
    I.add_edge_unchecked(wa.agent, "has_curiosity_hub", hub)
    p = dict(params or PARAMS)
    cp = S.add_node("HeldCuriosityParams", p)
    I.add_edge_unchecked(hub, "has_curiosity_params", cp)
    return hub


def _hub(wa):
    for h in wa.inner.neighbours(wa.agent, "has_curiosity_hub"):
        return h
    return None


def _items_by_topic(wa, hub):
    out = {}
    for it in wa.inner.neighbours(hub, "has_attention_item"):
        t = wa.s.node(it)["attrs"].get("topic")
        if t is not None:
            out[t] = it
    return out


def ensure_topic_item(wa, hub, topic):
    """Find-or-create the AttentionItem keyed by `topic` under `hub`. Mechanical
    construction only — every decision attr starts at ITEM_INIT's neutral value."""
    S, I = wa.s, wa.inner
    items = _items_by_topic(wa, hub)
    it = items.get(topic)
    if it is None:
        it = S.add_node("AttentionItem", dict(ITEM_INIT, topic=topic))
        I.add_edge_unchecked(hub, "has_attention_item", it)
    return it


def unknown_word_count(wa, phrase, min_len=3):
    """REAL SENSOR: how many words in `phrase` (length >= min_len) are NOT among
    the agent's own already-taught sign forms. Reuses `WorldAdapter.ground_
    unknowns`'s own tokenisation (same strip characters, same min_len default,
    same `taught_signs()` membership check) so this introduces no new notion of
    'unknown' — it is a read of the agent's own existing lexical state, exactly
    mirroring doom_active_explore_ingest._info_gain's 'count of unknown-bordering
    cells' pattern for the lexical domain."""
    known = {s["form"] for s in wa.taught_signs()}
    n = 0
    for raw in phrase.split():
        w = raw.strip(_STRIP).lower()
        if len(w) >= min_len and w not in known:
            n += 1
    return n


def maintain_topic_interest(wa, topics, epoch, *, teacher=None, attempt_ground=True):
    """Mechanical per-tick adapter: for each `{name: phrase}` candidate topic,
    (optionally) attempt REAL grounding via the agent's own ground_unknowns loop
    (world I/O — the teacher decides meaning), then set obs = the real
    unknown_word_count SENSOR read afterward, set input_epoch, and tick the
    graph's own run_rules() fixpoint. No decision is made here: whether progress
    is happening, whether attention sustains, and whether a gap gets minted are
    entirely the lp_* / lp_mint_topic_gap RULES reading these two written
    attrs."""
    hub = install_curiosity(wa)
    for name, phrase in topics.items():
        item = ensure_topic_item(wa, hub, name)
        if attempt_ground:
            wa.ground_unknowns(phrase, teacher=teacher)
        obs = unknown_word_count(wa, phrase) * WORD_SENSOR_SCALE
        wa.s.set_attr(item, "obs", float(obs))
        wa.s.set_attr(item, "input_epoch", float(epoch))
    wa.inner.run_rules()
    receipt = wa.s.add_node("NativeCuriosityReceipt", {
        "cluster": "curiosity_topic_selection.native_settlement",
        "provenance": "native_rule_readback:curiosity_topic_selection",
        "rule": "learning_progress_curiosity_and_topic_selection",
        "epoch": float(epoch),
        "topic_count": len(topics),
        "outcome_source": "native_rule_readback",
        "python_outcome_selection": False,
    })
    wa.inner.add_edge_unchecked(wa.agent, "has_native_curiosity_receipt", receipt)
    return hub

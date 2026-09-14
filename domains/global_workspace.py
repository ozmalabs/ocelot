"""Block 350000 — the GLOBAL WORKSPACE: seriality PRODUCED, not ASSERTED.

Global Workspace Theory (Baars; Dehaene's neuronal-global-workspace / IGNITION):
consciousness is a SERIAL BOTTLENECK produced by COMPETITION. Many unconscious
candidate coalitions run in parallel; each turn exactly ONE wins access to a single
BROADCAST slot (the workspace), and the win is a WINNER-TAKE-ALL contest over the
candidates' SALIENCE — not a queue position. Below an IGNITION THRESHOLD nothing
is broadcast (the sub-threshold coalition stays unconscious); above it the winner
is ignited and broadcast globally. Seriality is the OUTPUT of the contest, not an
axiom of the plumbing.

WHAT THIS REPLACES (the honest diagnosis, block 350's must-have #2). The block-346
train of thought ASSERTS seriality by construction: `agenda.pop(0)` — a FIFO queue,
one topic per turn because the list hands them out one at a time in insertion order.
There is no contest, no salience read, no threshold. The "one thought at a time" is
a property of the DATA STRUCTURE, not a produced bottleneck. This module makes the
next-thought selection a genuine COMPETITION for a single slot:

    score each candidate by a TEACHER-FREE salience  ->  ARGMAX = broadcast winner
    (the serial bottleneck)  ->  IGNITION: broadcast only if the winner clears an
    ignition threshold, else NO broadcast this turn (honest silence — the train
    yields rather than force a sub-threshold pick).  Losers stay for later contest.

TEACHER-FREE SALIENCE (the coalition score — verify stage confirmed it is REAL, not
arbitrary). Per candidate topic, summed as a held `Plus`:
  · LEARNING-PROGRESS / INTEREST (block 202000, the PRINCIPLED primary): the
    curiosity AttentionItem's integer `interest` (or `smoothed_progress`) attr, keyed
    by the SAME topic string the agenda uses (curiosity_topic_ingest). Oudeyer/
    Schmidhuber learning-progress, noisy-TV-resistant. Present only for INGESTED
    topics — for those with no item the LP channel is 0 (absence, not a fabricated
    score).
  · IS-A PROXIMITY (block 346, the ALWAYS-AVAILABLE floor): closeness to the current
    focus on the is-a spine (transitive_ancestors depth). This is the train's own
    "always-available reasoning floor" — teacher-free on the plain is-a seed, so the
    competition is principled EVEN for candidates with no curiosity item.
  · TUBE MEMBERSHIP / DEVIATION (block 348/349, optional): when a ThoughtManifold
    tube is active, a candidate INSIDE the tube (deviation 0) is more salient than one
    off it; the per-candidate deviation is subtracted as an inverse-salience penalty.

DISCRETE QUANTA THROUGHOUT (the substrate's premise). Every salience channel and the
ignition threshold are INTEGER QUANTA: each channel is snapped k = round(x/quantum)
(clamped) via the substrate's native quantiser analogy_search._round_to_vocab — the
SAME quantiser observer_aperture / attention_width use. No float ever decides. The
WINNER is a held `Argmax` Term over [topic, salience_quantum] pairs (reusing
predictive_reading._argmax_pairs_term) — a GRAPH-NATIVE decision, not a Python max/
sort. The IGNITION gate is an integer comparison of the winner's quantum against the
ignition-threshold quantum (the gap_prioritization should_continue / curiosity
attend_thresh idiom — below threshold => don't act).

HONESTY (mandated). The salience signal EXISTS and is teacher-free — the verify stage
confirmed it (LP interest + is-a proximity floor + optional tube deviation), so the
competition is PRINCIPLED, not an arbitrary tie-break. Where a candidate has neither a
curiosity item NOR any is-a relation to the focus, its salience is 0 (honest absence)
and it simply waits sub-threshold; the module never invents a score to force a pick.

Additive: a NEW module composed from EXISTING primitives (curiosity_topic_ingest,
train_of_thought is-a reads, predictive_reading Argmax Term, analogy_search quantiser).
Wired into the runners via a DEFAULTED `select=` kwarg (FIFO stays the default —
backward-compatible byte-for-byte). No protected-file edit, no .so rebuild, no
conceptualizer.py touch, teacher-free at selection time (no LLM).
"""
from __future__ import annotations

from typing import Any, Callable, Optional


# --------------------------------------------------------------------------- #
#  QUANTA — the salience + ignition-threshold grain (DISCRETE QUANTA, no floats).
#
#  Salience is measured in INTEGER quanta of the SAME native quantiser the rest of
#  the substrate uses (analogy_search._round_to_vocab: k = round(x/quantum), clamped
#  to +-half_width). The grain is the RESOLUTION dial; a finer grain gives more
#  salience levels. A raw float only ever appears as an INPUT that gets snapped on
#  entry — it never leaks a continuum into the decision.
# --------------------------------------------------------------------------- #
#: the QUANTUM grain of the LEARNING-PROGRESS salience channel. The confirmed
#: teacher-free LP signals live on very different scales — the curiosity `interest`
#: attr rides its interest_c0 sentinel (hundreds/thousands) while the raw
#: `smoothed_progress` / `learning_progress` rate is single-to-double digits. A
#: single coarse grain (e.g. 64) makes the raw progress rate vanish (round(6/64)=0)
#: while it is a REAL signal. Grain 4.0 makes the progress rate visible (a progress
#: of ~6-12 => 1-3 quanta) AND keeps a large `interest` value a large number of
#: quanta — the LP channel stays load-bearing on BOTH scales, honestly. (The
#: substrate's calibrated progress_floor is 10 and surprise_floor 4 — grain 4
#: sits at that native resolution, not an invented number.)
SALIENCE_QUANTUM: float = 4.0
#: the clamp half-width for the quantiser (the salience axis is one-sided/positive
#: in practice; the half-width just bounds pathological inputs).
SALIENCE_HALF_WIDTH: int = 1 << 20
#: the DEFAULT ignition threshold, in the SAME integer quanta. A winner must clear
#: this to be broadcast; below it => honest silence (no broadcast this turn). The
#: default 1 quantum means "any positive salience ignites" — the loosest honest
#: gate (a candidate with a genuine is-a relation to the focus, or any curiosity
#: interest, ignites; a candidate with ZERO salience — no relation, no item — does
#: NOT). Callers raise it to demand a stronger coalition.
IGNITION_QUANTA: int = 1
#: the per-is-a-hop salience contributed by the proximity floor (integer). A direct
#: parent/child is the most proximal; each further transitive hop is worth less.
#: Small so that a real LP-interest signal, when present, dominates proximity.
ISA_PROXIMITY_BASE: int = 3


def _snap(x, quantum: float = SALIENCE_QUANTUM,
          half_width: int = SALIENCE_HALF_WIDTH) -> int:
    """Snap a raw salience `x` onto its DISCRETE QUANTUM — the integer step
    k = round(x/quantum), clamped to [-half_width, half_width], via the substrate's
    OWN quantiser (analogy_search._round_to_vocab). That quantiser returns None for a
    zero coordinate (a shared default it omits from intersections); here a snapped 0
    is a MEANINGFUL "no salience" reading, so None is mapped back to the integer 0.
    A raw float never leaks a continuum in — it is resolved to an integer on entry."""
    try:
        from domains.analogy_search import _round_to_vocab
        k = _round_to_vocab(x, quantum, half_width)
    except Exception:
        k = None
    if k is None:
        # _round_to_vocab omits a rounded-0 (its intersection convention); for the
        # workspace a 0 quantum is a real "sub-threshold / no salience" reading.
        try:
            k = max(-half_width, min(half_width, round(float(x) / float(quantum))))
        except Exception:
            k = 0
    return int(k)


# --------------------------------------------------------------------------- #
#  TEACHER-FREE per-candidate SALIENCE channels (all integer graph reads).
# --------------------------------------------------------------------------- #
def _resolve_sub(wa):
    """The substrate behind `wa` (adapter, substrate, or carrier) — the SAME
    resolution self_dialogue._sub uses, so the workspace reads the identical graph
    the train's agenda lives in."""
    try:
        from domains import self_dialogue as sd
        return sd._sub(wa)
    except Exception:
        for attr in ("s", "substrate", "sub"):
            cand = getattr(wa, attr, None)
            if cand is not None and hasattr(cand, "nodes"):
                return cand
        if hasattr(wa, "nodes"):
            return wa
        raise


def _native(wa, sub):
    """The Rust engine handle for held-Term evaluation — the gap_prioritization /
    predictive_reading _resolve idiom (agent.inner, else sub._inner, else sub)."""
    native = getattr(wa, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    return native


def _lp_interest(wa, sub, topic: str) -> int:
    """The LEARNING-PROGRESS salience of `topic`, read off its curiosity
    AttentionItem (block 202000) if one has been ingested — teacher-free, integer.
    Prefers the raw learning-progress RATE (`smoothed_progress`, else
    `learning_progress`), the Oudeyer/Schmidhuber compression-progress the verify
    stage confirmed is the principled primary signal; falls back to the sustained
    `interest` attr when a progress rate is not present. Returns 0 when the topic
    has NO item (honest absence: an un-ingested topic lends no LP salience, rather
    than a fabricated score). Pure graph read — no rules fired, no I/O.

    NOTE on channel choice: `interest` is a SUSTAINED attention level that only
    rises once lp_interest's boost has fired (last_boost_epoch>0); the raw
    `smoothed_progress`/`learning_progress` is the per-tick RATE and is non-zero as
    soon as the topic shows compression progress. Reading the rate first means the
    salience reflects genuine learning progress even before the sustained-interest
    accumulator has ignited — the honest primary signal."""
    try:
        from domains import curiosity_topic_ingest as cti
        hub = cti._hub(wa)
        if hub is None:
            return 0
        item = cti._items_by_topic(wa, hub).get(topic)
        if item is None:
            return 0
        attrs = sub.node(item)["attrs"]
        for key in ("smoothed_progress", "learning_progress", "interest"):
            v = attrs.get(key)
            if v:
                return int(round(float(v)))
        return 0
    except Exception:
        return 0


def _isa_distance(wa, sub, topic: str, focus: str):
    """The is-a graph DISTANCE (hop count) between `topic` and `focus` over the
    causal_influence spine, searching BOTH directions (topic-is-a-...-focus or
    focus-is-a-...-topic). Uses grounded_representation's own cone/edge reads so it
    counts DIRECT is-a edges too (unlike train_of_thought.transitive_ancestors,
    which deliberately reports only the cone BEYOND the direct edges). Returns the
    integer hop count (1 = direct parent/child) or None when unrelated on the spine.
    A bounded BFS — teacher-free graph read, no decision."""
    from domains import self_dialogue as sd
    tn = sd._find_concept(sub, topic)
    fn = sd._find_concept(sub, focus)
    if tn is None or fn is None:
        return None

    def _bfs(start, goal):
        seen = {start}
        frontier = [(start, 0)]
        while frontier:
            node, d = frontier.pop(0)
            if node == goal:
                return d
            if d >= 16:                       # bounded — a spine is shallow
                continue
            nbrs = []
            try:
                nbrs = list(sub.neighbours(node, "causal_influence"))
            except Exception:
                nbrs = []
            for nb in nbrs:
                if nb not in seen:
                    seen.add(nb)
                    frontier.append((nb, d + 1))
        return None

    up = _bfs(tn, fn)                          # topic -> ... -> focus (topic is-a focus)
    down = _bfs(fn, tn)                         # focus -> ... -> topic (focus is-a topic)
    cands = [d for d in (up, down) if d is not None]
    return min(cands) if cands else None


def _isa_proximity(wa, sub, topic: str, focus: Optional[str]) -> int:
    """The IS-A PROXIMITY salience floor of `topic` relative to the current `focus`
    (block 346, the always-available reasoning floor) — teacher-free, integer. A
    candidate that is a direct is-a neighbour of the focus is the MOST salient;
    each further hop on the spine is worth one less. Returns ISA_PROXIMITY_BASE for
    a direct parent/child (distance 1), decaying by one per further hop, 0 for a
    candidate unrelated on the is-a spine. This floor keeps the competition
    principled even for candidates with no curiosity item."""
    if not focus or topic == focus:
        return 0
    d = _isa_distance(wa, sub, topic, focus)
    if d is None or d < 1:
        return 0
    return max(0, ISA_PROXIMITY_BASE - (d - 1))


def _tube_deviation(wa, sub, topic: str, tube) -> int:
    """The TUBE-DEVIATION inverse-salience penalty of `topic` (block 348/349),
    when a ThoughtManifold tube region is active — teacher-free, integer. A candidate
    INSIDE the tube deviates 0 (no penalty); one OFF it deviates >=1 (penalised, less
    salient). Returns the deviation to SUBTRACT from the coalition score. 0 (no
    penalty) when no tube is supplied. Reuses regulated_train_of_thought's own
    per-segment deviation measure rather than reinventing a distance."""
    if not tube:
        return 0
    try:
        from domains import regulated_train_of_thought as rtot
        return int(rtot._trajectory_deviation([topic], set(tube)))
    except Exception:
        # honest floor: a candidate not in the tube region deviates 1, in it 0
        return 0 if topic in set(tube) else 1


# --------------------------------------------------------------------------- #
#  THE COALITION SCORE — a held `Plus` of the teacher-free channels, snapped to
#  a DISCRETE QUANTUM. This is what competes for the broadcast slot.
# --------------------------------------------------------------------------- #
def salience_quanta(wa, topic: str, *, focus: Optional[str] = None,
                    tube=None, quantum: float = SALIENCE_QUANTUM) -> int:
    """The teacher-free SALIENCE of a single candidate `topic`, in INTEGER QUANTA.
    The coalition score is a held `Plus` over the channels the verify stage confirmed
    are real —
        LP progress-rate  +  is-a-proximity-to-focus floor  -  tube-deviation penalty
    — with the LP channel (the raw learning-progress rate, or sustained interest)
    snapped to the salience quantum first, and the small integer proximity floor /
    tube penalty added in quantum units. The sum is a graph-native `Plus` evaluate
    (never Python `+` deciding it). Returns max(0, quanta): salience is non-negative
    (a heavy tube penalty cannot drive a candidate below "no salience")."""
    sub = _resolve_sub(wa)
    native = _native(wa, sub)

    lp = _lp_interest(wa, sub, topic)             # raw LP progress-rate / interest
    lp_q = _snap(lp, quantum)                      # -> integer quanta at the LP grain
    prox_q = _isa_proximity(wa, sub, topic, focus)  # already small integer quanta
    dev_q = _tube_deviation(wa, sub, topic, tube)   # inverse-salience penalty (quanta)

    # held Plus over the channels — the graph decides the sum, not Python.
    term = {"type": "Plus", "items": [
        {"type": "Lit", "value": float(lp_q)},
        {"type": "Lit", "value": float(prox_q)},
        {"type": "Lit", "value": float(-dev_q)},
    ]}
    try:
        total = int(round(float(native.evaluate(term, {}) or 0.0)))
    except Exception:
        total = lp_q + prox_q - dev_q
    return max(0, total)


# --------------------------------------------------------------------------- #
#  THE BROADCAST — score the candidate set, ARGMAX winner, IGNITION gate.
# --------------------------------------------------------------------------- #
def broadcast_winner(wa, candidates, *, focus: Optional[str] = None,
                     tube=None, ignition_quanta: int = IGNITION_QUANTA,
                     quantum: float = SALIENCE_QUANTUM,
                     with_detail: bool = False):
    """The GLOBAL WORKSPACE selection: from the CURRENT candidate set (the agenda /
    frontier contents), score each by its teacher-free salience quantum, pick the
    ARGMAX (the coalition that wins access to the single broadcast slot — the serial
    bottleneck), subject to an IGNITION THRESHOLD.

    Returns the winning topic string, or None when the top salience is BELOW the
    ignition threshold (honest silence — sub-threshold coalitions are not broadcast;
    the turn yields rather than force a pick). Losers are simply not returned — they
    remain in the caller's candidate set for the next turn's contest.

    The winner is a GRAPH-NATIVE decision: a held `Argmax` Term over the
    [topic, salience_quantum] pairs (predictive_reading._argmax_pairs_term), evaluated
    in the engine — NOT a Python max()/sort(). DISCRETE QUANTA throughout: each
    salience is an integer quantum; the ignition threshold is an integer quantum; the
    comparison is integer.

    `with_detail=True` returns (winner, info) where info carries the per-candidate
    salience quanta and the winning quantum — for falsifiable-claim inspection."""
    cands = [c for c in (candidates or []) if c is not None]
    if not cands:
        return (None, {"scores": {}, "winner_quanta": None,
                       "ignition_quanta": int(ignition_quanta),
                       "reason": "empty"}) if with_detail else None

    sub = _resolve_sub(wa)
    native = _native(wa, sub)

    # 1. SCORE every candidate teacher-free, in integer quanta (de-dup, order-stable).
    scores: dict[str, int] = {}
    ordered: list[str] = []
    for c in cands:
        if c in scores:
            continue
        scores[c] = salience_quanta(wa, c, focus=focus, tube=tube, quantum=quantum)
        ordered.append(c)

    # 2. WINNER = held Argmax over [topic, salience_quantum] pairs — a graph decision.
    pairs = [[c, scores[c]] for c in ordered]
    winner = None
    try:
        from domains.predictive_reading import _argmax_pairs_term
        top = native.evaluate(_argmax_pairs_term(pairs), {})
        if isinstance(top, (list, tuple)) and top:
            winner = top[0]
    except Exception:
        winner = None
    if winner is None:
        # honest structural fallback: the engine Argmax was unavailable; pick the
        # max-quantum candidate deterministically (first in insertion order on ties).
        best_q = None
        for c in ordered:
            if best_q is None or scores[c] > best_q:
                best_q, winner = scores[c], c

    win_q = scores.get(winner, 0)

    # 3. IGNITION: broadcast only if the winner clears the threshold quantum; else
    #    NO broadcast this turn (honest silence). Integer comparison.
    if win_q < int(ignition_quanta):
        result = None
        reason = "sub_threshold"
    else:
        result = winner
        reason = "broadcast"

    if with_detail:
        return result, {"scores": dict(scores), "winner": winner,
                        "winner_quanta": int(win_q),
                        "ignition_quanta": int(ignition_quanta),
                        "reason": reason}
    return result


# --------------------------------------------------------------------------- #
#  the SELECT strategy — the shape the runners' `select=` hook expects.
#  A select strategy is `select(wa, candidates, *, focus, tube) -> Optional[str]`.
# --------------------------------------------------------------------------- #
def workspace_select(ignition_quanta: int = IGNITION_QUANTA,
                     quantum: float = SALIENCE_QUANTUM) -> Callable:
    """Build a `select=`-compatible strategy that uses the global workspace
    competition/broadcast to choose the next topic from the candidate set. Returns
    a callable `select(wa, candidates, *, focus=None, tube=None) -> Optional[str]`
    (None => sub-threshold silence). The default parameters ignite on any positive
    salience; raise `ignition_quanta` to demand a stronger coalition."""
    def _select(wa, candidates, *, focus=None, tube=None):
        return broadcast_winner(wa, candidates, focus=focus, tube=tube,
                                ignition_quanta=ignition_quanta, quantum=quantum)
    return _select

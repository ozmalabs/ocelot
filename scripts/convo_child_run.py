#!/usr/bin/env python3
"""convo_child_run — a child CONVERSATION runner spawned by
``domains/experiment_dispatch.py`` to play ONE dispatched Experiment's
conversation-replay episode out-of-process (the conversation twin of
``scripts/arc_child_run.py`` — same boot modes, same delta application,
same output contract).

This is host mechanism only (CLAUDE.md): boot an agent (from a snapshot of a
parent's mind, or fresh with some seeds withheld), apply the SeedDelta's
``add_rules`` / tombstone its ``remove_rules``, then REPLAY the conversation
corpus that is already IN the snapshot graph and score it by pure mechanical
comparison. No new reasoning lives here — the DECISION to run this experiment,
WHAT to vary, and what the outcome MEANS are all the parent agent's own rules'
(see domains/reflective_faculty.py's conversation branch of
``_compose_experiment_rule`` and its judge/adopt rules).

The corpus (a mechanical graph read off the parent snapshot, never typed here):

  * every recorded interlocutor turn — an inbound ``Message{from:
    'interlocutor'}`` whose ``comp_reply_text`` attr carries the reply
    ``converse()`` recorded for it (``WorldAdapter._finish_turn_reply``) —
    becomes one PROBE, replayed in node-id order with the same speech act
    (read off the turn's own ``has_speech_act`` edge);
  * a turn referenced by a ``SelfConcern{kind:'reply_fix'}`` ``about_message``
    edge is a FLAGGED probe (the human flagged that reply as bad via
    ``flag_reply_turn``), and so is one referenced by a
    ``SelfConcern{kind:'instruction'}`` (the agent's own gap rule filed the
    unhandled turn — the target a cue-set-edit experiment tries to change,
    Wave 5); every other probe is an UNFLAGGED regression guard;
  * a PIPELINE-STEERING turn (the ``promote_requested_by`` source of some
    concern — seeds/conversation_steering.json's marker) is EXCLUDED: its
    recorded reply depends on the concern's pipeline state, not on reply
    behaviour, and replaying it would re-steer the child's pipeline.

PAIRED-CONTROL REPLAY (the fix for the fragility that blocked R3/R4 —
composer-capability wave, commit f111cb6e4e — from adopting): the interlocutor
waves made ``converse()`` genuinely STATE-DEPENDENT within one corpus replay —
told-status (``believed_concepts`` → ``reply_topic_repeat_known`` in
``seeds/conversation_grice.json`` fires "as I mentioned..." on the SECOND ask
of an already-answered topic), gap/concern dedup guards, party-model evolution
(register/shape/reliability), topic tracking. A RECORDED reply was produced
ONCE, live, on a state trajectory that no longer exists once the corpus is
replayed against a booted snapshot — replaying it again is already a SECOND
telling. Comparing a replayed reply against the RECORDED text therefore
manufactures false regressions purely from state drift, independent of any
delta under test (verified live, see the commit this wave lands in: turn
"What do you know about zqxbelt?" diverged from its recorded reply solely
because ``reply_topic_repeat_known`` fired on a re-ask that the delta under
test — a ``datum_feedback_rule`` touching only ``self_report_reliability`` —
never touched).

The fix is TWO INDEPENDENT boots of the SAME snapshot, replayed exactly ONCE
each, never a single substrate replayed twice in sequence (which was the
previous double-pass shape: the recorded double-pass ran a "control" pass on
the loaded snapshot, applied the delta IN PLACE, then ran a "variant" pass on
top of the control pass's own mutations — so the variant pass was really the
corpus's THIRD telling, one live + two replayed, and its replies were being
judged against the recorded reply's FIRST telling):

  * CONTROL — an independent boot from the snapshot with NO delta applied at
    all (not even a deferred half-application); replayed once; torn down
    (``del`` + ``gc.collect()``) before the variant boots, so the two passes
    never share a live process's memory footprint at once (memory discipline
    — every child process this wave spawns now does TWO full-seed boots
    instead of one, so peak-vs-average matters);
  * VARIANT — a SECOND independent boot from the SAME snapshot with the delta
    applied in full BEFORE its one replay (no more mid-corpus rule swap: with
    two independent passes there is no "between passes" to defer into,
    everything installs once, up front); replayed once.

Both boots start from BYTE-IDENTICAL graph state (the same snapshot file, or
— for the fresh+skip family — the same full seed set with nothing withheld)
and replay the SAME probe list in the SAME node-id order, so a genuinely
delta-caused divergence is now separable from a state-trajectory artifact:
the control pass walks the SAME told-status/dedup/party-evolution machinery
the variant pass does, from the SAME starting point, so a reply that differs
between the TWO PASSES is attributable to the delta, never to the corpus
having been a live conversation once.

TWO BASELINES, not one (both still string comparison, no judgment):

  * flagged probe: ``flagged_changed`` iff the VARIANT reply differs from the
    RECORDED (human-flagged-bad) reply — unchanged semantic. A ``reply_fix``
    flag means "the recorded bad reply must change"; that question is about
    the ONE turn a human (or the agent's own gap rule) pointed at, not about
    corpus-wide state drift, so the recorded text remains the right
    yardstick here;
  * unflagged probe: ``regressed`` iff the VARIANT reply differs from the
    CONTROL reply for the SAME probe (no longer the recorded reply — the
    recorded text is NOT a valid regression baseline once replay is known to
    be state-dependent; see above). A single-pass (non-double-pass) delta —
    plain ablation/cue-set-edit — gets the SAME paired-control treatment now:
    every delta shape runs the identical two-independent-boots structure, so
    a no-op delta scores ZERO regressions BY CONSTRUCTION (control and
    variant are then byte-identical replays of the same probes) — the
    determinism gate this wave adds.
  * a flagged probe whose variant reply is EMPTY, the fixed error surface, or
    raised is a ``broken_fix`` (tranche 4): it changed, but into a failure,
    and scores −1 like a regression rather than +1;
  * ``score = (+1 per flagged_changed) − (1 per regression or broken_fix)`` — so the
    parent's own authored judge (score-per-frame SIGN, unchanged from the ARC
    family) reads: positive → supported, negative → refuted, zero (including
    the no-probes and no-op-delta cases) → inconclusive.

The knob_edit / rule_literal_edit / datum_feedback_rule / shape_mint families'
own cost/witness/belief signals (reform marks, structural witness fires, the
interlocutor belief/shape-fit witness, per-turn shadow latency) are STILL a
control-vs-variant comparison — exactly as before, just now genuinely
independent passes rather than two passes on one mutated substrate.

Boot modes (mirrors arc_child_run.boot_child_agent — mechanical, keyed only
by whether the delta withholds seeds):

  * SNAPSHOT boot (no ``skip_seeds``): ``WorldAdapter.load()`` the exact
    parent mind, twice — once as the CONTROL pass's own agent (the corpus is
    read off it before its replay mutates it, folding the old separate
    "corpus_agent" throwaway load into the control boot: one fewer full-seed
    boot per child), once as the VARIANT pass's agent. This is the primary,
    tested path.
  * FRESH+SKIP boot (``skip_seeds`` non-empty): the corpus is read from the
    SNAPSHOT via a separate throwaway load (the recorded turns only exist
    there; freed immediately after, before either replay boot). The CONTROL
    pass boots bare + ``load_all_seeds`` with NOTHING withheld (skip=()) —
    "no delta" for this family means the FULL seed set, not the partially-
    withheld one; the VARIANT pass boots bare + ``load_all_seeds(skip=…)``
    with the delta's actual withhold list, exactly as arc_child_run does.
    Both passes are still fresh (no parent learned-state), so this family's
    honest limitation stands — a fresh agent's replies differ from a
    snapshot-booted one — but that limitation is now paired fairly (fresh
    vs fresh, not fresh vs a state-rich recorded conversation), which
    removes the "nearly always refuted" bias the old recorded-baseline
    comparison had. The targeted ``remove_rules`` ablation is the
    conversation family's real vary.

Known divergence from arc_child_run's remove_rules application, documented:
this runner tombstones EVERY active copy of a named rule (not just the last
index) — conversation seeds can carry duplicate active copies of a reply rule
(e.g. ``reply_to_adjacency_pair`` after repeated ``enable_replies()`` loads),
and removing only one would silently leave the behaviour unchanged, making
the trial a false null.

Output contract (identical keys to arc_child_run's, read by
``domains/experiment_dispatch.py`` unchanged):
  * ``<out>/trace.jsonl`` — one line per probe (frame-shaped):
    ``{"frame", "action", "score", "reasoning", "self_report"}`` — written
    from the VARIANT pass only (the pass every verdict input is read from);
    the reasoning text names which baseline (``recorded`` or ``control``)
    the "changed"/"unchanged" verdict was checked against.
  * ``<out>/final_graph.json`` — best-effort ``agent.s.graph_to_dict()`` of
    the VARIANT agent, written ONLY when the delta sets ``keep_final_graph``
    or ``OZMA_CHILD_KEEP_GRAPH=1`` (tranche 13: multi-GB, unread).
  * ``<out>/result.json`` — ``{"status": "done"|"failed", "frames", "score",
    "won", "over", "boot_mode", "removed_rules", "error": optional}`` plus
    informational extras (``flagged``, ``flagged_changed``, ``regressions``).

  PYTHONPATH=runners/dsl/python:. python3 scripts/convo_child_run.py \\
      --snapshot var/runs/7-0/parent_snapshot.json --delta var/runs/7-0/delta.json \\
      --game conversation --out var/runs/7-0
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import time
import traceback
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
for p in (str(_ROOT), str(_HERE), str(_ROOT / "runners" / "dsl" / "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter   # noqa: E402
from substrate.world_adapter import _CONVERSATION_ERROR_SURFACE   # noqa: E402
from substrate.boot_all import load_all_seeds       # noqa: E402
# Shared mechanical helpers — the SAME delta parse / bookkeeping-fill / concept
# application the ARC child uses, imported rather than re-implemented so the
# two runners can't drift.
from arc_child_run import (_load_delta, _fill_missing_bookkeeping,      # noqa: E402
                          apply_concept_delta, apply_node_attr_delta)


def _load_snapshot_agent(snapshot: str) -> WorldAdapter:
    agent = WorldAdapter.load(snapshot)
    _fill_missing_bookkeeping(agent)
    return agent


def read_corpus(agent) -> list:
    """Mechanical graph read: the recorded conversation as replayable probes.
    One probe per interlocutor Message with a recorded reply (comp_reply_text,
    written by converse()'s _finish_turn_reply), in node-id (insertion) order;
    `flagged` iff some reply_fix SelfConcern points at the turn. Pure query —
    no decisions."""
    S, I = agent.s, agent.inner
    flagged_ids = set()
    steering_ids = set()
    scope_pairs = set()
    for sc in S.nodes("SelfConcern"):
        if not I.has_node(sc):
            continue
        # A flagged probe is a turn some SelfConcern points at: `reply_fix`
        # (the human flagged the reply — Wave 3) or `instruction` (the agent's
        # own gap rule filed the unhandled turn, about_message wired by
        # seeds/gap_awareness.json::note_unhandled_instruction_gap — Wave 5:
        # that turn IS what a cue-set-edit experiment is trying to change).
        # Mechanical edge read, same as before; no status filter (a promoted
        # concern's turn is still the target turn).
        if S.node(sc)["attrs"].get("kind") == "comprehension":
            # tranche 23: a comprehension concern names a shallow/deep reader
            # DISAGREEMENT CLASS; every turn with that same disagreement is in
            # the concern's scope (changing it is the point, not a regression)
            for mid in I.neighbours(sc, "about_message"):
                if I.has_node(mid):
                    at0 = S.node(mid)["attrs"]
                    scope_pairs.add((at0.get("comp_kind"), at0.get("shadow_speech_act"), _first_role(S, I, mid)))
        if S.node(sc)["attrs"].get("kind") in ("reply_fix", "instruction", "unanswered", "comprehension"):
            for mid in I.neighbours(sc, "about_message"):
                if I.has_node(mid):
                    flagged_ids.add(int(mid.value))
        # An EXPLICIT-REPORT turn (kind 'reported' — gap_awareness's
        # note_reported_gap points about_message at the turn that DID the
        # reporting) is NOT a behaviour probe either: its recorded reply
        # ("Noted -- I've filed that as a gap...") depends on the FILING
        # state (the rule's own content-dedup guard sees the already-filed
        # SelfConcern in the snapshot and declines to re-fire), exactly the
        # steering-turn problem below. Excluded mechanically by the same
        # edge read. (RESIDUAL-CLOSURE wave.)
        if S.node(sc)["attrs"].get("kind") == "reported":
            for mid in I.neighbours(sc, "about_message"):
                if I.has_node(mid):
                    steering_ids.add(int(mid.value))
        # A PIPELINE-STEERING turn (it is the promote_requested_by source of
        # some concern — seeds/conversation_steering.json's marker edge) is
        # NOT a behaviour probe: its recorded reply depends on the concern's
        # pipeline STATE (status noted/promoted) rather than on reply rules,
        # and replaying it would re-steer the child's pipeline. Excluded
        # mechanically by the edge, exactly like flagging reads about_message.
        for mid in I.neighbours(sc, "promote_requested_by"):
            if I.has_node(mid):
                steering_ids.add(int(mid.value))
    probes = []
    for m in sorted(S.nodes("Message"), key=lambda n: n.value):
        if int(m.value) in steering_ids:
            continue
        a = S.node(m)["attrs"]
        if a.get("from") != "interlocutor":
            continue
        text = (a.get("text") or "").strip()
        recorded = (a.get("comp_reply_text") or "").strip()
        if not recorded:
            # tranche 22: a production turn that ended on the explicit error
            # floor records no comp_reply_text; its reply is the graph-minted
            # terminal message (terminal_outcome='explicit_error')
            for r in I.in_neighbours(m, "responds_to"):
                if I.has_node(r) and S.node(r)["attrs"].get("terminal_outcome") == "explicit_error":
                    recorded = (S.node(r)["attrs"].get("text") or "").strip()
                    break
        if not text or not recorded:
            continue
        act = None
        for c in I.neighbours(m, "has_speech_act"):
            if I.has_node(c):
                act = S.node(c)["attrs"].get("name")
                break
        probes.append({"turn_id": int(m.value), "text": text, "reply": recorded,
                       "speech_act": act or "statement",
                       "flagged": int(m.value) in flagged_ids,
                       "in_scope": (a.get("speech_act_divergence") == 1.0
                                    and (a.get("comp_kind"), a.get("shadow_speech_act"),
                                         _first_role(S, I, m)) in scope_pairs)})
    return probes


def _first_role(S, I, mid):
    """The turn's communication interpretation's literal_first_role (the
    literal class a deep_reader_correct correction is scoped to)."""
    for i in I.in_neighbours(mid, "interprets"):
        if I.has_node(i) and S.node(i)["attrs"].get("schema") == "communication_interpretation.v1":
            return S.node(i)["attrs"].get("literal_first_role")
    return None


def _apply_rule_swap(agent, delta: dict) -> list:
    """The add_rules/remove_rules mechanics `apply_delta` normally runs
    inline — factored out as its own callable so a WHERE-CLAUSE-VARIATION
    `rule_literal_edit` (or COMPOSER-CAPABILITY `datum_feedback_rule`) delta
    can be swapped in isolation (unit-tested directly, e.g.
    `test_apply_rule_swap_deferred_and_witness_counting`). PAIRED-CONTROL
    REPLAY (see module docstring): `main` no longer defers this swap
    mid-corpus — with two independent boots there is no "between passes" to
    defer into, so the VARIANT boot calls this (via `apply_delta`) once, up
    front, before its one replay. Tombstones EVERY active copy of a named
    rule (see the module docstring's documented divergence)."""
    for rule in delta["add_rules"]:                 # graph data the delta specifies; mechanical install
        agent.inner.add_rule(rule)
    removed_rules = []
    if delta["remove_rules"]:                        # graph data the delta specifies; mechanical tombstone
        wanted = set(delta["remove_rules"])
        exported = agent.inner.export_rules()
        for idx in sorted(
                (i for i, r in enumerate(exported)
                 if isinstance(r, dict) and r.get("active", True) and r.get("name") in wanted),
                reverse=True):
            name = exported[idx].get("name")
            if agent.inner.remove_rule(idx) and name not in removed_rules:
                removed_rules.append(name)
        # a name not found / already-inactive is silently skipped — the delta names WHAT to
        # remove, not a guarantee it still exists; honest partial application, not an error.
    return removed_rules


def apply_delta(agent, delta: dict, *, defer_rules: bool = False, defer_concepts: bool = False) -> list:
    """Install the delta's add_rules + add_concepts, tombstone its remove_rules
    and retract its remove_concepts. Returns the rule names that actually
    resolved to at least one live rule (empty when `defer_rules`).

    NOTE (RESIDUAL-CLOSURE / WHERE-CLAUSE-VARIATION): the delta's
    `set_node_attrs` (knob_edit family) is deliberately NOT applied here —
    `main` calls `apply_node_attr_delta` directly, alongside this, on the
    VARIANT boot only.

    PAIRED-CONTROL REPLAY (this wave): `main` no longer calls this with
    `defer_rules=True` / `defer_concepts=True` — the old double-pass ran a
    single substrate through a "control" replay, applied part of the delta
    IN PLACE, then ran a "variant" replay on top of the control pass's own
    mutations (see the module docstring's diagnosis for why that
    manufactured false regressions). With two INDEPENDENT boots (control:
    no delta at all; variant: the full delta) there is no "between passes"
    left to defer into — the VARIANT boot applies add_rules/remove_rules/
    add_concepts/remove_concepts here in ONE call, before its one replay.
    The `defer_rules`/`defer_concepts` parameters stay for callers that want
    the swap/install split from the tombstone/retract in isolation (unit
    tests; `_apply_rule_swap`/`apply_concept_delta` remain independently
    callable) — `main` simply never passes True for either any more."""
    if not defer_rules:
        removed_rules = _apply_rule_swap(agent, delta)
    else:
        removed_rules = []
    if not defer_concepts:
        apply_concept_delta(agent, delta)            # Wave 5: cue-set-edit graph data (shared applier)
    return removed_rules


def _active_interlocutor_belief(agent, attr: str, default=None):
    """Mechanical read (COMPOSER-CAPABILITY, R3): the CURRENTLY ACTIVE
    Interlocutor party's `attr` (or `default` if absent) — the witness the
    datum_feedback_rule family's controlled double-pass counts before/after
    the authored rule is installed. Uses interlocutor_model's own party
    resolver (get-or-create is fine here — a replay corpus always carries at
    least one turn, so a party always exists by the time this is read)."""
    try:
        from domains import interlocutor_model as im
        party = im._active_party(agent)
        val = agent.s.node(party)["attrs"].get(attr)
        return val if val is not None else default
    except Exception:  # noqa: BLE001 — an unreadable belief is an honest default
        return default


def _classified_party_count(agent) -> int:
    """Tranche 8 shape_mint witness: how many modeled parties fit SOME held
    InterlocutorShape at decode_shape's own floor (fit >= _SHAPE_FIT_MIN).
    Party-independent and read AFTER each pass's replay, so control and
    variant are measured identically. The old witness
    (_active_interlocutor_shape_fit) read whichever party was active in the
    snapshot (measured: a typical party, fit 4 in both passes) and read the
    control BEFORE its replay, so a shape minted for an atypical party could
    never move it."""
    try:
        from domains import interlocutor_model as im
        return sum(1 for p in im._parties(agent)
                   if int(im.decode_shape(agent, p).get("fit", 0) or 0) >= im._SHAPE_FIT_MIN)
    except Exception:  # noqa: BLE001
        return 0


def _active_interlocutor_shape_fit(agent) -> int:
    """Mechanical read (COMPOSER-CAPABILITY, R4): `decode_shape`'s own fit
    count for the CURRENTLY ACTIVE party — the witness the shape_mint
    family's controlled double-pass counts before/after the constructed
    InterlocutorShape is installed."""
    try:
        from domains import interlocutor_model as im
        party = im._active_party(agent)
        return int(im.decode_shape(agent, party).get("fit", 0) or 0)
    except Exception:  # noqa: BLE001 — an unreadable fit counts as 0, never crashes the replay
        return 0


def _count_reform_marks(agent) -> int:
    """Mechanical count of SentenceParse nodes the reform ladder has marked
    (reform_pending by the seed rule; reform_done by the executor) — the
    RESIDUAL-CLOSURE knob family's direct observable ('fewer spurious
    reforms'). Pure graph read."""
    n = 0
    try:
        for sp in agent.s.nodes("SentenceParse"):
            at = agent.s.node(sp)["attrs"]
            if at.get("reform_pending") or at.get("reform_done"):
                n += 1
    except Exception:  # noqa: BLE001 — type absent on a bare graph
        pass
    return n


def _count_witness(agent, witness) -> int:
    """Mechanical count of the WHERE-CLAUSE-VARIATION family's structural
    witness (see reflective_faculty._rule_effect_witness — a `{kind:'typed',
    node_type, attrs}` typed-node-with-literal-attrs count, or a `{kind:
    'attr_any', attr, value}` node-type-agnostic attr==value count). None ->
    0 (no witness derivable from the picked rule's own effects — the family
    still reports regressions, just no fire-delta). Pure graph read, no
    interpretation of what the witness MEANS."""
    if not witness:
        return 0
    try:
        kind = witness.get("kind")
        if kind == "typed":
            ntype = str(witness.get("node_type") or "")
            attrs = dict(witness.get("attrs") or {})
            n = 0
            for nd in agent.s.nodes(ntype):
                at = agent.s.node(nd)["attrs"]
                if all(at.get(k) == v for k, v in attrs.items()):
                    n += 1
            return n
        if kind == "attr_any":
            attr = witness.get("attr")
            value = witness.get("value")
            n = 0
            for nd in agent.s.nodes():
                try:
                    at = agent.s.node(nd)["attrs"]
                except Exception:  # noqa: BLE001 — a stale node is an honest skip
                    continue
                if at.get(attr) == value:
                    n += 1
            return n
    except Exception:  # noqa: BLE001 — an unreadable witness counts as 0, never crashes the replay
        return 0
    return 0


def _production_turn(agent, text, speech_act=None, max_cycles=40):
    """One turn on the PRODUCTION path (tranche 22): exactly the daemon's
    ingest + tick-loop body (jabberwock_daemon._ingest_daemon_chat_turn and
    tick_loop) -- ingest_turn with the classified speech act, then tick /
    comprehend / settle / release_graph_selected_response until the graph
    releases a reply or a terminal outcome. Returns the reply surface or None.
    Host actions are not executed (a replay must not dispatch or fetch)."""
    from substrate.boot_profiles import prepass_conversation_turn
    try:
        prepass_conversation_turn(agent, text)
    except Exception:  # noqa: BLE001 -- the daemon also continues without it
        pass
    mid = agent.ingest_turn(text, speech_act=agent.classify_speech_act(text))
    agent._last_turn_inbound = mid
    tid = int(mid.value)
    for _ in range(max_cycles):
        agent.tick()
        agent.comprehend()
        agent.settle_post_comprehension_authority([tid])
        reply = agent.release_graph_selected_response(mid)
        if reply is not None:
            agent.record_turn_outcome(tid, "reply_released")
            return reply
        status = agent.graph_turn_reply_outcome(tid)
        if status in ("expected", "unrepresented", "reply_ready"):
            continue
        agent.record_turn_outcome(tid, status)
        return agent.graph_turn_reply(tid)
    return None


def _replay_pass(agent, probes, witness=None):
    """ONE mechanical replay of the corpus on an agent that is already fully
    booted (and, for a variant pass, already carries the delta applied in
    full — see `main`). PAIRED-CONTROL REPLAY (module docstring): this
    function itself does not score, compare, or write a trace — it is called
    exactly once per INDEPENDENT agent (once for control, once for variant),
    and `main` diffs the two `replies` lists afterwards. No comparison to a
    prior pass or to recorded text happens in here — that is what made the
    old shared-substrate double-pass fragile (a single agent replayed twice
    manufactures state-dependent divergence unrelated to any delta).

    Returns {replies: [str,...] (one per probe, in order), turn_ms: [float,...],
    errors: [str|None,...], avg_turn_ms, shadow_ms (mean of this pass's own
    per-turn shadow_latency_ms, or None), reforms (reform marks minted DURING
    this pass), witness_fires (fires of `witness`, WHERE-CLAUSE-VARIATION
    family, minted DURING this pass — 0 when `witness` is None)}."""
    replies = []
    turn_ms_list = []
    errors = []
    total_turn_ms = 0.0
    shadow_samples = []
    reforms_before = _count_reform_marks(agent)
    witness_before = _count_witness(agent, witness)
    for probe in probes:
        t0 = time.perf_counter()
        try:
            if getattr(agent, "_replay_turn_path", "converse") == "production":
                replayed = _production_turn(agent, probe["text"])
            else:
                replayed = agent.converse(probe["text"], speech_act=probe["speech_act"])
        except Exception as e:  # noqa: BLE001 — one bad probe must not kill the episode
            replayed = None
            probe_error = f"{type(e).__name__}: {e}"
        else:
            probe_error = None
        turn_ms = (time.perf_counter() - t0) * 1000.0
        total_turn_ms += turn_ms
        turn_ms_list.append(turn_ms)
        errors.append(probe_error)
        try:
            mid = getattr(agent, "_last_turn_inbound", None)
            if mid is not None and agent.s.has_node(mid):
                sl = agent.s.node(mid)["attrs"].get("shadow_latency_ms")
                if sl is not None:
                    shadow_samples.append(float(sl))
        except Exception:  # noqa: BLE001 — a missing datum is an honest omission
            pass
        replies.append((replayed or "").strip())
    return {"replies": replies, "turn_ms": turn_ms_list, "errors": errors,
            "avg_turn_ms": (total_turn_ms / len(probes)) if probes else 0.0,
            "shadow_ms": (sum(shadow_samples) / len(shadow_samples)) if shadow_samples else None,
            "reforms": _count_reform_marks(agent) - reforms_before,
            "witness_fires": _count_witness(agent, witness) - witness_before}


def _arm_parent_fidelity(agent, delta: dict) -> None:
    """PARENT-FIDELITY (RESIDUAL-CLOSURE): WorldAdapter.load()/a fresh boot
    both leave shadow_read=False; re-arm the parent's own flag on EVERY
    replay agent (control AND variant — PAIRED-CONTROL REPLAY: both boots
    must run the SAME comprehension the parent ran, or a reading-layer knob
    delta would be inert in the control pass while live in the variant pass,
    corrupting the comparison) so the replay runs the same comprehension the
    parent ran. Mechanical copy of a flag the dispatcher recorded
    (experiment_dispatch._spawn) — no decision."""
    if delta.get("parent_shadow_read"):
        agent.shadow_read = True
        agent.deep_ingest = True
    # tranche 22: replay on the path the parent's live turns took
    agent._replay_turn_path = ("production" if delta.get("parent_turn_path") == "production"
                               else "converse")
    agent.turn_path = delta.get("parent_turn_path") or "converse"


_READING_WARMED = False


def _warm_reading_path(delta: dict) -> None:
    """PAIRED-CONTROL FAIRNESS (tranche 7): the first shadow read in a process
    pays a one-time warm-up (lexicon/WordNet load, ~1.8 s measured) that the
    later pass does not, so without this the CONTROL replay's
    control_shadow_ms was inflated ~10x and every shadow-latency comparison
    favoured the variant (a performance experiment whose delta changed
    nothing was judged supported). One throwaway shadow read on a scratch
    adapter, before either replay, so both passes run warm. Mechanical; only
    when the parent ran shadow reads."""
    global _READING_WARMED
    if _READING_WARMED or not delta.get("parent_shadow_read"):
        return
    _READING_WARMED = True
    try:
        scratch = WorldAdapter(seeds=(), shadow_read=True)
        mid = scratch.s.add_node("Message", {"text": "Hello.", "from": "interlocutor"})
        scratch._shadow_read_turn(mid, "Hello.")
        del scratch
        gc.collect()
    except Exception:  # noqa: BLE001 — warming is best-effort, never breaks a replay
        pass


def main() -> int:
    ap = argparse.ArgumentParser(
        description="conversation child runner — replays one dispatched Experiment's corpus")
    ap.add_argument("--snapshot", required=True, help="WorldAdapter.save() path to boot/read from")
    ap.add_argument("--delta", default=None, help="SeedDelta JSON: {skip_seeds, add_rules, remove_rules}")
    ap.add_argument("--game", default="conversation", help="informational; always the conversation world")
    ap.add_argument("--out", required=True, help="run_dir to write trace.jsonl / final_graph.json / result.json")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    trace_path = out_dir / "trace.jsonl"
    result_path = out_dir / "result.json"
    graph_path = out_dir / "final_graph.json"

    delta = _load_delta(args.delta)
    result: dict = {"status": "failed", "frames": 0, "score": 0}
    agent = None            # the VARIANT agent — final_graph.json is ITS graph (the adoption candidate)
    trace_fp = None
    try:
        rule_literal_probe = bool(delta.get("rule_literal_edit"))
        datum_feedback_probe = bool(delta.get("datum_feedback_edit"))
        shape_mint_probe = bool(delta.get("shape_mint_edit"))
        knob_probe = bool(delta.get("set_node_attrs"))
        witness = None
        if rule_literal_probe:
            try:
                witness = json.loads(delta.get("rule_literal_witness") or "null")
            except Exception:  # noqa: BLE001 — an unparsable witness is an honest None
                witness = None

        # PAIRED-CONTROL REPLAY (module docstring): two INDEPENDENT boots of
        # the SAME snapshot, each replayed exactly once — never one substrate
        # replayed twice in sequence. boot_mode is mechanical (keyed only by
        # whether the delta withholds seeds), and is the SAME for both boots
        # ("both boots identical except the delta").
        if delta["skip_seeds"]:
            boot_mode = "fresh+skip"
            # The corpus only exists in the actual parent snapshot; a fresh
            # boot has none of it, so read it off a throwaway snapshot load,
            # freed immediately (memory discipline — three full-seed boots
            # would otherwise be live in this family, never at once).
            corpus_agent = _load_snapshot_agent(args.snapshot)
            probes = read_corpus(corpus_agent)
            del corpus_agent
            gc.collect()
            # CONTROL = "no delta" for this family means the FULL seed set —
            # nothing withheld — not the delta's own (partial) skip list.
            control_agent = WorldAdapter(seeds=())
            load_all_seeds(control_agent, skip=())
        else:
            boot_mode = "snapshot"
            # The control boot IS a plain, undelta'd snapshot load — fold the
            # old separate "corpus_agent" throwaway load into it (read the
            # corpus off it before its own replay mutates it): one fewer
            # full-seed boot per child than a naive 3-boot implementation.
            control_agent = _load_snapshot_agent(args.snapshot)
            probes = read_corpus(control_agent)
        result["boot_mode"] = boot_mode
        _warm_reading_path(delta)
        _arm_parent_fidelity(control_agent, delta)

        control_belief = None
        if datum_feedback_probe:
            belief_attr = str(delta.get("datum_feedback_belief_attr") or "self_report_reliability")
            control_belief = _active_interlocutor_belief(control_agent, belief_attr, 0.5)
        control = _replay_pass(control_agent, probes, witness=witness)
        if shape_mint_probe:
            control_belief = _classified_party_count(control_agent)
        del control_agent
        gc.collect()

        # VARIANT = a SECOND independent boot, the delta applied IN FULL
        # before its one replay (no more deferral — there is no shared
        # substrate to defer into any more).
        if boot_mode == "fresh+skip":
            agent = WorldAdapter(seeds=())
            load_all_seeds(agent, skip=delta["skip_seeds"])
        else:
            agent = _load_snapshot_agent(args.snapshot)
        _arm_parent_fidelity(agent, delta)
        removed_rules = apply_delta(agent, delta)
        if knob_probe:
            apply_node_attr_delta(agent, delta)

        stats = _replay_pass(agent, probes, witness=witness)
        variant_belief = None
        if datum_feedback_probe:
            belief_attr = str(delta.get("datum_feedback_belief_attr") or "self_report_reliability")
            variant_belief = _active_interlocutor_belief(agent, belief_attr, 0.5)
        elif shape_mint_probe:
            variant_belief = _classified_party_count(agent)

        # SCORE — TWO BASELINES (module docstring): a flagged probe's
        # `flagged_changed` is checked against the RECORDED reply (unchanged
        # semantic — "did the one flagged turn change"); an unflagged
        # probe's `regressed` is checked against the PAIRED CONTROL reply
        # for the SAME probe (the fix — the recorded reply is no longer a
        # valid regression baseline once replay is known to be
        # state-dependent).
        trace_fp = open(trace_path, "w")
        score = 0
        flagged_n = 0
        flagged_changed = 0
        broken_fixes = 0
        regressions = 0
        repaired = 0

        def _is_broken_reply(txt, err):
            return (not str(txt or "").strip()
                    or str(txt).strip() == _CONVERSATION_ERROR_SURFACE or bool(err))
        for i, probe in enumerate(probes):
            replayed = stats["replies"][i]
            if probe["flagged"]:
                flagged_n += 1
                baseline, baseline_text = "recorded", probe["reply"]
                # Fixed only if the DELTA changed it: the variant must differ
                # from the recorded bad reply AND from the paired control
                # replay. A reply that drifted from the recording under replay
                # state alone (control == variant) is no fix (tranche 6:
                # a no-op cue delta scored 'supported' this way).
                changed = (replayed != baseline_text
                           and replayed != control["replies"][i])
                # A change only FIXES the flagged turn if the new reply is a
                # real communicative surface: an empty reply, the adapter's
                # fixed error surface, or a probe that raised is a BROKEN fix
                # (it fails the turn harder than the flagged reply did), and
                # scores like a regression (tranche 4).
                _is_broken = lambda txt, err: (not str(txt or "").strip()
                                               or str(txt).strip() == _CONVERSATION_ERROR_SURFACE
                                               or bool(err))
                # Broken only if the DELTA broke it: when the paired control
                # replay of the same probe is already broken (replay-state
                # drift, independent of the delta), the variant's failure is
                # not the delta's doing (tranche 5).
                broken = (_is_broken(replayed, stats["errors"][i])
                          and not _is_broken(control["replies"][i], control["errors"][i]))
                if changed and _is_broken(replayed, stats["errors"][i]) and not broken:
                    changed = False      # neither fixed nor broken by the delta
                if changed and broken:
                    broken_fixes += 1
                    score -= 1
                elif changed:
                    flagged_changed += 1
                    score += 1
            else:
                baseline, baseline_text = "control", control["replies"][i]
                changed = replayed != baseline_text
                # REPAIRED, not regressed (tranche 22): an unflagged turn the
                # CONTROL answered with the error floor (or nothing) and the
                # VARIANT answers with a real surface was not broken by the
                # delta -- measured: a generalised receipt also answered a
                # second same-class unanswered turn, and the old scorer
                # counted that as a regression. Scored 0 (no credit claimed,
                # no penalty); reported as `repaired`.
                if changed and not _is_broken_reply(replayed, stats["errors"][i]) and (
                        _is_broken_reply(baseline_text, control["errors"][i]) or probe.get("in_scope")):
                    # error -> reply, or a turn in the concern's own
                    # disagreement class answered differently (tranche 23)
                    repaired += 1
                    changed = False
                    baseline = "control (repaired)"
                if changed:
                    regressions += 1
                    score -= 1
            reasoning = (f"turn {probe['turn_id']} "
                         f"{'FLAGGED' if probe['flagged'] else 'unflagged'} "
                         f"{'changed' if changed else 'unchanged'} vs {baseline}: {probe['text']!r}"
                         + (f" [probe error: {stats['errors'][i]}]" if stats["errors"][i] else ""))
            trace_fp.write(json.dumps({"frame": i, "action": "reply", "score": score,
                                       "reasoning": reasoning, "turn_ms": stats["turn_ms"][i],
                                       "self_report": replayed[:400]}) + "\n")
        trace_fp.flush()

        result = {"status": "done", "frames": len(probes), "score": score,
                  "won": score > 0, "over": True, "boot_mode": boot_mode,
                  "removed_rules": removed_rules,
                  "flagged": flagged_n, "flagged_changed": flagged_changed,
                  "broken_fixes": broken_fixes, "regressions": regressions, "repaired": repaired,
                  "avg_turn_ms": stats["avg_turn_ms"]}
        if knob_probe:
            result["control_reforms"] = int(control["reforms"])
            result["variant_reforms"] = int(stats["reforms"])
        if rule_literal_probe:
            result["control_witness_fires"] = int(control["witness_fires"])
            result["variant_witness_fires"] = int(stats["witness_fires"])
        if datum_feedback_probe or shape_mint_probe:
            result["control_belief"] = float(control_belief) if control_belief is not None else 0.0
            result["variant_belief"] = float(variant_belief) if variant_belief is not None else 0.0
        if control["shadow_ms"] is not None:
            result["control_shadow_ms"] = float(control["shadow_ms"])
        if stats["shadow_ms"] is not None:
            result["avg_shadow_ms"] = float(stats["shadow_ms"])
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"
        result["traceback"] = traceback.format_exc()
        print(f"convo_child_run FAILED: {result['error']}", file=sys.stderr, flush=True)
        print(result["traceback"], file=sys.stderr, flush=True)
    finally:
        if trace_fp is not None:
            try:
                trace_fp.close()
            except Exception:
                pass
        # STORAGE (tranche 13): the variant graph is multi-GB per run and no
        # consumer reads it for the conversation family (adoption re-applies
        # the delta to the parent). Written only on request: delta
        # `keep_final_graph` or OZMA_CHILD_KEEP_GRAPH=1.
        keep_graph = bool(delta.get("keep_final_graph")) if isinstance(delta, dict) else False
        keep_graph = keep_graph or os.environ.get("OZMA_CHILD_KEEP_GRAPH") == "1"
        if agent is not None and not keep_graph:
            result["final_graph_written"] = False
        if agent is not None and keep_graph:
            try:
                with open(graph_path, "w") as f:
                    json.dump(agent.s.graph_to_dict(), f)
            except Exception as e:
                result["graph_write_error"] = f"{type(e).__name__}: {e}"
        with open(result_path, "w") as f:
            json.dump(result, f)

    return 0 if result.get("status") == "done" else 1


if __name__ == "__main__":
    sys.exit(main())

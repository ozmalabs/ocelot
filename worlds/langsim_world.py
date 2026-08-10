"""LangSimWorld -- a richer economy+building multi-agent world where agents
coordinate through REAL graph-emitted utterances (block 243000).

MEASURE-FIRST LANGUAGE PROBE. Enriches glassbox_r1_world (block 234000): the R1
coordination signal was a `stated_give=1` cheap-talk FLAG under comms_on -- no
utterance string ever existed. Here the coordination signal is a REAL utterance
STRING produced BY THE GRAPH FACULTY (WorldAdapter.utterance_for -> the graph
lexicon + Rust Render engine, NO LLM, NO Python template) that the receiver must
COMPREHEND back into graph state (receive_utterance + comprehend -> the seeded
intent/referent Rules) before any trade rule can act on it. This module measures
where that round-trip breaks.

ARCHITECTURE RULE (experiments/gamma-substrate/CLAUDE.md). This is a WORLD
ADAPTER. Every AGENT DECISION is a graph rule or a mechanical read of graph
state:
  * whether an agent GIVES/KEEPS is `gb_choose_give` (glassbox_r1_social),
    reused verbatim -- the value Argmax over two candidate Appraisals.
  * whether an agent BUILDS is `ls_build` (langsim_build) -- a rule over held
    inputs.
  * WHAT an agent communicates is READ from its own graph state (its BuildState
    holdings/need) -- mechanical I/O, exactly as R1 reads chosen_give -- and
    REALISED to an utterance by the graph faculty. The renderer, not Python,
    produces the string; Python only forms the {verb:{left,right}} meaning dict
    from the read-back holdings and hands it to utterance_for.
  * whether promise_in is set for a receiver is a mechanical read of the
    receiver's COMPREHENDED graph (did a Mention resolve to its needed-resource
    Concept + the partner?) -- language is genuinely in the loop.

No graph_rewrite.run / gr.run / _match / _apply / make_rule. Every conditional
here is over WORLD state (holdings, encounter, mode) -- mechanical.
"""
from __future__ import annotations
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import numpy as np                                       # noqa: E402
from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.seed_loader import manifest_for            # noqa: E402

# ---- FIXED world constants (pre-registered, LANGSIM_..._PREREG.md) ----
# Two resource types; two producer roles. Agent role 0 gathers wood, needs stone;
# role 1 gathers stone, needs wood. To BUILD (value V_BUILD) an agent needs BOTH.
RESOURCES = ("wood", "stone")
V_BUILD = 10        # value realised when an agent builds (holds both inputs)
V_KEEP_BOTH = 7     # defector's prize: keep own + received, no reciprocation
V_TRADED = 6        # successful trade end-holding (both inputs, pre-build credit)
V_OWN = 4           # autarky: hold own input only, cannot build
V_ALONE = 0         # sucker: gave own, got nothing
G_CONTRIB = 3       # supergraph_contribution when a give hands a partner its need

# Communicative-content vocabulary (Signs the language faculty renders/parses).
_VOCAB = ("I", "you", "have", "give", "need", "want", "wood", "stone", "me")

# HeldEmotionParams / Appraisal defaults (mirror glassbox_r1_world so the
# core_emotions rules find every atom they read).
EP_DEFAULTS = dict(enabled=1.0, w_supergraph=1.0, mood_bias=0.0, residual_thresh=100.0,
                   high_arousal=800.0, mid_arousal=400.0, low_arousal=50.0, comms_on=0.0)
APPR_DEFAULTS = dict(
    appraised=1.0, individual_benefit=0.0, individual_cost=0.0, supergraph_contribution=0.0,
    collective_success=0.0, collective_success_prev=0.0, contribution_by_self=0.0,
    observed_by_other=0.0, valued_goal=0.0, goal_blocked=0.0, blocker_present=0.0,
    attachment=0.0, regroundable=0.0, contamination=0.0, was_engaged=0.0,
    residual=0.0, residual_prev=0.0, threat=0.0, threat_c0=0.0, threat_half_life=1.0,
    threat_last_refresh=0.0, threat_now_epoch=0.0, t_present=100.0, v_max=0.0,
    step=0.0, step_prev=0.0, attach_v0=0.0, attach_k_now=0.0, attach_k_prev=0.0)


class Agent:
    """One agent = its own WorldAdapter (language faculty) carrying the R1
    value-economy decision machinery + a BuildState. The agent IS a graph in
    Rust; this Python object is the per-agent host handle."""

    def __init__(self, idx, role, w_supergraph, comms):
        self.idx = idx
        self.role = role                       # 0 -> gathers wood/needs stone; 1 -> stone/wood
        self.gathers = RESOURCES[role]
        self.needs = RESOURCES[1 - role]
        self.w = float(w_supergraph)
        self.comms = bool(comms)

        self.wa = WorldAdapter()
        self.s = self.wa.s
        self.inner = self.wa.inner
        # decision machinery (value Argmax) + build rule
        self.inner.load_seed_manifest(manifest_for("core_emotions"), self.wa.agent)
        self.inner.load_seed_manifest(manifest_for("glassbox_r1_social"), self.wa.agent)
        self.inner.load_seed_manifest(manifest_for("langsim_build"), self.wa.agent)

        # grounded resource + role Concepts (so referents resolve) + the lexicon.
        _named = set()
        for r in RESOURCES:
            self.s.add_node("Concept", {"name": r}); _named.add(r)
        for w in _VOCAB:
            if w not in _named:
                self.s.add_node("Concept", {"name": w}); _named.add(w)
            self.wa.learn_sign(w, w)
        self.wa._backfill_knows_concept()
        self.wa.attach_chat_world("partner")

        self.sg = self.s.add_node("Supergraph", {})
        self.hub = self.s.add_node("EmotionHub", {})
        ep = dict(EP_DEFAULTS); ep.update(w_supergraph=self.w,
                                          comms_on=1.0 if comms else 0.0)
        epn = self.s.add_node("HeldEmotionParams", ep)
        self.inner.add_edge_unchecked(self.hub, "has_emotion_params", epn)
        self.inner.add_edge_unchecked(self.hub, "member_of", self.sg)
        self.dec = self.s.add_node("TradeDecision",
                                   {"chosen_give": -1.0, "stated_give": 0.0,
                                    "promise_in": 0.0})
        self.inner.add_edge_unchecked(self.hub, "has_decision", self.dec)
        gv = dict(APPR_DEFAULTS); gv.update(give_level=1.0)
        kp = dict(APPR_DEFAULTS); kp.update(give_level=0.0)
        self.give_c = self.s.add_node("Appraisal", gv)
        self.keep_c = self.s.add_node("Appraisal", kp)
        for apn in (self.give_c, self.keep_c):
            self.inner.add_edge_unchecked(self.hub, "has_appraisal", apn)
            self.inner.add_edge_unchecked(self.hub, "has_candidate", apn)
        # BuildState: has_own (gathered), has_need (acquired by trade), built.
        self.bs = self.s.add_node("BuildState",
                                  {"enabled": 1.0, "has_x": 0.0, "has_y": 0.0,
                                   "built": 0.0})
        self.inner.add_edge_unchecked(self.hub, "has_build", self.bs)

    # ---- graph-state reads (mechanical) ----
    def _set_holdings(self, has_own, has_need):
        # has_x is the agent's OWN input, has_y is the complementary input.
        self.s.set_attr(self.bs, "has_x", 1.0 if has_own else 0.0)
        self.s.set_attr(self.bs, "has_y", 1.0 if has_need else 0.0)

    def promise_meaning(self):
        """Form the agent's communicative intent from its OWN graph state: it
        gathered its own resource and offers to GIVE it (so the partner, who
        needs it, will reciprocate). The CONTENT (which resource) is read from
        the BuildState/role -- mechanical I/O; the STRING is the faculty's."""
        # {give: {left: I, right: <the resource I gathered and offer>}}
        return {"give": {"left": "I", "right": self.gathers}}

    def utter(self, meaning):
        """Realise a communicative meaning to a surface string via the GRAPH
        faculty (utterance_for -> lexicon + Rust Render engine). No template."""
        return self.wa.utterance_for(meaning)

    def hear(self, text, speaker_name="partner"):
        """Comprehend an incoming utterance: mint the Message + Mentions and run
        the seeded intent/referent Rules. Returns the resolved (mention_text,
        [referent_names]) pairs read back off the graph."""
        mid = self.wa.receive_utterance(text, speech_act="statement",
                                        speaker=speaker_name)
        self.wa.comprehend()
        resolved = []
        for mn in self.inner.neighbours(mid, "has_mention"):
            at = self.s.node(mn)["attrs"]
            refs = [self.s.node(r)["attrs"].get("name")
                    for r in self.inner.neighbours(mn, "refers_to")]
            resolved.append((at.get("text"), refs))
        return mid, resolved

    def comprehended_offer_of(self, resolved):
        """Mechanical read: did the comprehended utterance resolve BOTH a 'give'
        content sign AND this agent's NEEDED resource? Returns True iff the
        receiver parsed a real offer of what it needs -- the language-gated
        promise_in signal. No decision: a query over resolved referents."""
        names = {n for _t, refs in resolved for n in refs}
        return ("give" in names) and (self.needs in names)


class LangSimWorld:
    """N agents (roles alternate), each its own language faculty, on a ring;
    complementary encounters; trade mediated by a REAL promise utterance;
    building rewards the trade. mode in {'language','none','scrambled'}."""

    P_RING = 5

    def __init__(self, w_supergraphs, mode="language", seed=0):
        assert mode in ("language", "none", "scrambled")
        self.mode = mode
        self.ws = [float(w) for w in w_supergraphs]
        self.n = len(self.ws)
        self.rng = np.random.default_rng(seed)
        comms = (mode != "none")
        self.agents = [Agent(i, i % 2, self.ws[i], comms) for i in range(self.n)]
        self.pos = [int(self.rng.integers(0, self.P_RING)) for _ in range(self.n)]

        self.total_value = 0.0
        self.n_builds = 0
        self.n_encounters = 0
        self.tick = 0
        # measurement ledger (real transcripts + per-encounter reconstruction)
        self.transcripts = []     # dicts: tick, speaker, listener, meaning, utterance, resolved, comprehended
        self.trade_log = []
        self.promise_nodes_readable = []

    def _walk(self):
        for i in range(self.n):
            self.pos[i] = (self.pos[i] + int(self.rng.integers(-1, 2))) % self.P_RING

    def _encounters(self):
        by_cell = {}
        for i in range(self.n):
            by_cell.setdefault(self.pos[i], []).append(i)
        pairs = []
        for _cell, members in by_cell.items():
            r0 = sorted(m for m in members if self.agents[m].role == 0)
            r1 = sorted(m for m in members if self.agents[m].role == 1)
            for a, b in zip(r0, r1):
                pairs.append((a, b))
        return pairs

    def _scramble(self, text):
        toks = text.split()
        if len(toks) > 1:
            perm = self.rng.permutation(len(toks))
            # ensure it actually differs when possible
            toks2 = [toks[k] for k in perm]
            if toks2 == toks:
                toks2 = list(reversed(toks))
            return " ".join(toks2)
        return text

    def step(self):
        self.tick += 1
        self._walk()
        pairs = self._encounters()
        # ---- GATHER (mechanical world production): each agent gains its own input.
        for ag in self.agents:
            ag._set_holdings(has_own=True, has_need=False)
            ag.s.set_attr(ag.dec, "chosen_give", -1.0)
            ag.s.set_attr(ag.dec, "stated_give", 0.0)
            ag.s.set_attr(ag.bs, "built", 0.0)

        for a, b in pairs:
            self.n_encounters += 1
            A, B = self.agents[a], self.agents[b]
            promise_in_A = promise_in_B = False
            # ---- COMMUNICATE: each forms a promise intent from graph state,
            # realises it via the GRAPH faculty, the partner comprehends it.
            if self.mode != "none":
                for speaker, listener, tag in ((A, B, "A->B"), (B, A, "B->A")):
                    meaning = speaker.promise_meaning()
                    utt = speaker.utter(meaning)             # GRAPH-emitted string
                    delivered = self._scramble(utt) if self.mode == "scrambled" else utt
                    _mid, resolved = listener.hear(delivered)
                    got = listener.comprehended_offer_of(resolved)
                    self.transcripts.append(dict(
                        tick=self.tick, dir=tag, speaker=speaker.idx,
                        listener=listener.idx, meaning=meaning, utterance=utt,
                        delivered=delivered, resolved=resolved, comprehended=got))
                    if listener is A:
                        promise_in_A = got
                    else:
                        promise_in_B = got
            # ---- publish candidate payoffs conditioned on the COMPREHENDED promise
            A.s.set_attr(A.dec, "promise_in", 1.0 if promise_in_A else 0.0)
            B.s.set_attr(B.dec, "promise_in", 1.0 if promise_in_B else 0.0)
            self._pub(A, promise_in_A)
            self._pub(B, promise_in_B)
            # ---- TICK: the give/keep Argmax rule + commissive fire in-graph.
            A.inner.run_rules()
            B.inner.run_rules()
            ga = int(A.s.node(A.dec)["attrs"]["chosen_give"])
            gb = int(B.s.node(B.dec)["attrs"]["chosen_give"])
            sa = int(A.s.node(A.dec)["attrs"]["stated_give"])
            sb = int(B.s.node(B.dec)["attrs"]["stated_give"])
            # readable promise nodes (glass-box: stated vs held)
            for who, ag, stated, chosen in ((a, A, sa, ga), (b, B, sb, gb)):
                if stated == 1:
                    self.promise_nodes_readable.append(dict(
                        by=who, w=ag.w, stated=stated, held=chosen,
                        gap=stated - chosen, tick=self.tick))
            # ---- REALISE the trade: a successful swap hands each the complement.
            a_traded = (ga == 1 and gb == 1)
            if a_traded:
                A._set_holdings(True, True)   # A kept own + received stone
                B._set_holdings(True, True)
            else:
                # partial/none: a giver becomes the sucker, a keeper holds both.
                A._set_holdings(True, gb == 1)
                B._set_holdings(True, ga == 1)
            # ---- BUILD rule fires for whoever holds both.
            A.inner.run_rules(); B.inner.run_rules()
            va = self._value(A, ga, gb)
            vb = self._value(B, gb, ga)
            self.total_value += va + vb
            self.trade_log.append(dict(tick=self.tick, a=a, b=b,
                                       chosen_a=ga, chosen_b=gb,
                                       built_a=int(A.s.node(A.bs)["attrs"]["built"]),
                                       built_b=int(B.s.node(B.bs)["attrs"]["built"]),
                                       value_a=va, value_b=vb))
        return dict(tick=self.tick, encounters=len(pairs))

    def _pub(self, ag, promise_in):
        gv_ben = V_TRADED if promise_in else V_ALONE
        kp_ben = V_KEEP_BOTH if promise_in else V_OWN
        ag.s.set_attr(ag.give_c, "individual_benefit", float(gv_ben))
        ag.s.set_attr(ag.give_c, "supergraph_contribution", float(G_CONTRIB))
        ag.s.set_attr(ag.keep_c, "individual_benefit", float(kp_ben))
        ag.s.set_attr(ag.keep_c, "supergraph_contribution", 0.0)

    def _value(self, ag, my_give, partner_give):
        built = int(ag.s.node(ag.bs)["attrs"]["built"])
        if built:
            self.n_builds += 1
            return V_BUILD
        if my_give == 1 and partner_give == 1:
            return V_TRADED
        if my_give == 1 and partner_give == 0:
            return V_ALONE
        if my_give == 0 and partner_give == 1:
            return V_KEEP_BOTH
        return V_OWN

    def run(self, T=30):
        for _ in range(T):
            self.step()
        return self.outcome(T)

    def outcome(self, T=30):
        denom = self.n * max(self.tick, 1)
        return dict(mode=self.mode, total_value=self.total_value,
                    value_per_agent_tick=self.total_value / denom,
                    n_builds=self.n_builds, n_encounters=self.n_encounters,
                    ticks=self.tick, n_agents=self.n)

    def close(self):
        for ag in self.agents:
            try:
                ag.wa  # no explicit stop needed (no eye thread here)
            except Exception:
                pass

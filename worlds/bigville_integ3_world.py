"""BigvilleInteg3World -- bigville R10c (block 274000): ACTIVATE THE DORMANT SOCIAL RUNGS.

R10 assembled the town; R10b (BigvilleInteg2World) balanced it (Sigma(coin) conserved,
deaths rare & caused, verdict PUNCTUATED_WEAK). But the town's SOCIAL life was
LOADED-but-DORMANT: 21 sibling seeds' rules are present (0 conflicts) yet their TRIGGER
ENTITIES were never populated and their PERIODIC EVENTS never armed on the clock -- so
the paper never printed, the council never convened, no gossip/coalition spread, journals
were null, and the macro feed was only deaths/evictions.

R10c makes the social rungs FIRE. It is a POPULATE + ARM + EXPORT build, NOT a
decision-logic build: the RULES already exist. In __init__ it POPULATES the trigger
entities (a Town + civic Resident mirrors + a Paper + Reporter; a two-tier Council with
Members + a Mayor + a Board; a nightly Diary per resident; -- and, best-effort, a School
with pupils, a loudness comm/classroom, and the John/Mary political drama). integ_step
ARMS the periodic social events on cadence -- the paper prints (weekly), the council
convenes on council-days, lessons run on schooldays, gossip/coalition propagates,
residents write a journal each night -- each armed by setting the seed's trigger flag /
minting its trigger node then self._run(). This is EXACTLY the R10b `wsink_armed` /
`decide_armed` arming pattern (mechanical world-delivery).

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
A WORLD ADAPTER. It SUBCLASSES R10b (edits no tracked R10/R10b/landed-seed file), holds
NO agent decision. Every social DECISION stays a seed RULE: who writes / prints / is
suppressed (np_*), who learns / forms the coalition (np_reach), the council's vote /
private decision / the 234 gap / the posted notice (cm_*), the pupil's learning
(sc_acquire), the earshot / observe-vs-hear (lo_*), John's spite-economy scheme + Mary's
ToM (bd_*), and the nightly journal MINT (jn_write_entry, the one additive seed this rung
ships). The adapter only ingests trigger entities, arms flags, ticks (`self._run()`), and
reads. NO new Rust; the town runs on the canonical own engine.
"""
from __future__ import annotations

import math
import os
import sys
from collections import defaultdict

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.seed_loader import manifest_for                        # noqa: E402
from worlds.bigville_integ2_world import (                            # noqa: E402
    BigvilleInteg2World, TICKS_PER_DAY)

# ---- social cadences (pre-registered scheduling; NOT dials on a result) --------
PAPER_EVERY_DAYS = 7        # the weekly paper
COUNCIL_EVERY_DAYS = 7      # a scheduled council meeting each week
SCHOOL_EVERY_DAYS = 2       # a class period twice a week
LOUD_EVERY_DAYS = 3         # a street utterance + a classroom chatter/control beat
DRAMA_EVERY_DAYS = 7        # a political-drama beat per week

# literacy / civic mixing (population = distribution over seeds)
_LITERACY_P = 0.7           # fraction of residents literate (R18 outcome, drawn)
_READS_P = 0.9              # fraction subscribing to the paper

# the 3.5% (Chenoweth) reference threshold for the collective-action coalition.
CHENOWETH_FRAC = 0.035

# defaults merged onto each civic-mirror Resident so NO news/council rule ever reads a
# missing key (union of BigvilleNewsWorld.RESIDENT_DEFAULTS + BigvilleCouncilWorld's).
_CIVIC_DEFAULTS = dict(
    literate=0.0, witnessed=0.0, knows_event=0.0, knows_event_flag=0.0,   # news/reach
    at_hall=0.0, knows_law=0.0, knows_law_flag=0.0,                       # council/board
    knows_address=0.0, heard_address=0.0, knows_decision=0.0, heard_decision=0.0)

_STORY_DEFAULTS = dict(content=0.0, reporter_bias=0.0, written=0.0,
                       suppressed=0.0, printed=0.0)
_MINUTES_DEFAULTS = dict(value=0.0, clerk_bias=0.0, recorded=0.0)
_MEMBER_DEFAULTS = dict(base_position=0.0, self_serving_premium=0.0, vote=0.0,
                        clerk_bias=0.0)

# journal-source keys initialised on every mover so jn_write_entry never reads a missing
# key before the affect machinery writes them (the affect rules write these live).
_JOURNAL_KEYS = ("grief_distress", "snap_pressure", "wellbeing", "conflict",
                 "chosen_action", "backs_mary", "journal_day", "journal_armed",
                 "jn_informed")


class BigvilleInteg3World(BigvilleInteg2World):
    def __init__(self, *, cast=16, seed=274000, enable_drama=True, enable_school=True,
                 enable_loud=True, **kw):
        super().__init__(cast=cast, seed=seed, **kw)
        import numpy as np
        self._rng3 = np.random.default_rng(seed + 2)

        # per-rung fire ledger + social feed bookkeeping
        self.rung_status = {}          # seed id -> "fired(...)" | "dormant(...)"
        self.rung_fire = defaultdict(int)
        self.social_log = []           # [{tick, kind, text, ...}]  (also into self.events)
        self.informed_share_series = []  # [(tick, informed, n, share, formed)]
        self.papers = []               # [{tick, printed, suppressed, informed, formed, ...}]
        self.council_log = []          # [{tick, convened, address, decision, gap, posted}]
        self.journal_nights = 0

        # ---- ADDITIVE seeds (mine + drama deps) -- load, record status ----------
        self.eng.load_seed_manifest(manifest_for("bigville_journal_nightly"), None)

        # ---- POPULATE the trigger entities --------------------------------------
        self._install_journal()
        self._install_press()
        self._install_council_gov()
        self._drama = None
        if enable_drama:
            self._install_drama()
        self._school = None
        if enable_school:
            self._install_school()
        self._loud = None
        if enable_loud:
            self._install_loud()

    # ==================================================================== JOURNAL
    def _install_journal(self):
        """Give every mover a Diary (has_diary) + initialise the journal-source keys so
        jn_write_entry can capture real state each night without reading a missing key."""
        self._diary = {}
        for nm in list(self.people):
            for k in _JOURNAL_KEYS:
                a = self.eng.node(self._movers[nm])["attrs"]
                if k not in a:
                    self.eng.set_attr(self._movers[nm], k, 0.0)
            d = self.eng.add_node("Diary", {"owner": self.display.get(nm, nm)})
            self.eng.add_edge_unchecked(self._movers[nm], "has_diary", d)
            self._diary[nm] = d

    def _write_journals(self):
        """Arm every LIVING mover for the night, then run: jn_write_entry mints one
        JournalEntry per armed mover capturing its held state, wires wrote_journal, and
        clears the flag. Mechanical arming (world-delivery); the mint is the rule."""
        day = self.world_epoch // TICKS_PER_DAY
        armed = 0
        for nm in self.people:
            if self.is_dead(nm):
                continue
            m = self._movers[nm]
            self.eng.set_attr(m, "journal_day", float(day))
            self.eng.set_attr(m, "journal_armed", 1.0)
            armed += 1
        self._run()
        self.journal_nights += 1
        self.rung_fire["bigville_journal_nightly"] += armed
        return armed

    # ====================================================================== PRESS
    def _install_press(self):
        """Mint the persistent public sphere: a Town hub, a civic-mirror Resident per
        living villager (literacy drawn), a Paper + Reporter. The Event/Story/Coalition
        are minted per printing cycle. These civic residents ALSO serve the council
        (attend meetings, visit the board) -- one townsperson, one civic identity."""
        r = self._rng3
        self._news_town = self.eng.add_node("Town", {"name": "Bigville"})
        self._paper = self.eng.add_node("Paper", {"name": "The Bigville Times",
                                                   "captured": 0.0, "active": 1.0})
        # the reporter -- a witness who writes the paper (occlusion-bound).
        rep_nm = None
        for nm in self.people:
            if self.roles2.get(nm) == "fishmonger":
                rep_nm = nm
                break
        self._reporter_nm = rep_nm
        self._reporter = self.eng.add_node("Reporter",
                                           {"name": self.display.get(rep_nm, "Reporter"),
                                            "witnessed": 1.0})
        self.eng.add_edge_unchecked(self._paper, "employs", self._reporter)
        # block 297000 fold-in: the weekly HEADLINE is RENDERED from the week's
        # real event's structured fields (StringConcat), not a Python f-string.
        self.eng.load_seed_manifest(manifest_for("bigville_headline"), None)

        self._civic = {}       # mover name -> Resident nid
        self._civic_of = {}    # Resident nid -> mover name
        self._literate = {}    # mover name -> bool
        for nm in list(self.people):
            lit = 1.0 if r.random() < _LITERACY_P else 0.0
            attrs = dict(_CIVIC_DEFAULTS)
            attrs.update(name=self.display.get(nm, nm), literate=lit)
            res = self.eng.add_node("Resident", attrs)
            self.eng.add_edge_unchecked(self._news_town, "has_resident", res)
            if r.random() < _READS_P:
                self.eng.add_edge_unchecked(res, "reads", self._paper)
            self._civic[nm] = res
            self._civic_of[res] = nm
            self._literate[nm] = bool(lit)

    def _civic_living(self):
        return [nm for nm in self.people if not self.is_dead(nm) and nm in self._civic]

    def _print_paper(self, *, truth_value, damaging=0, reporter_bias=0, clerk_bias=0,
                     kind="news", headline="", witnesses=None, story_fields=None):
        """Arm ONE weekly printing: mint an Event (from a REAL town event), a Story, the
        Minutes second channel, reset the residents' knows_event_flag, mint a fresh
        Coalition (quorum ~ the 3.5% Chenoweth threshold), mark the witnesses, then run.
        Every DECISION is a rule (write / suppress / print / who-learns / coalition-forms);
        this only ingests + reads. Returns the printing read-off."""
        living = self._civic_living()
        n = max(1, len(living))
        # a fresh propagation: clear last week's knowledge on the LIVING residents.
        for nm in living:
            self.eng.set_attr(self._civic[nm], "knows_event_flag", 0.0)
            self.eng.set_attr(self._civic[nm], "knows_event", 0.0)
            self.eng.set_attr(self._civic[nm], "witnessed", 0.0)
        # witnesses (direct/oral layer) -- a small subset who saw the event.
        wl = witnesses if witnesses is not None else living[:max(1, n // 8)]
        for nm in wl:
            self.eng.set_attr(self._civic[nm], "witnessed", 1.0)

        ev = self.eng.add_node("Event", {"truth_value": float(truth_value),
                                         "damaging_to_owner": float(damaging)})
        self.eng.add_edge_unchecked(ev, "in_town", self._news_town)
        self.eng.add_edge_unchecked(self._reporter, "covers", ev)
        story = self.eng.add_node("Story", dict(_STORY_DEFAULTS,
                                                reporter_bias=float(reporter_bias)))
        self.eng.add_edge_unchecked(self._paper, "reports", story)
        self.eng.add_edge_unchecked(story, "about", ev)
        # block 297000 fold-in: attach the week's REAL event's structured fields
        # so the bigville_headline rules RENDER the headline (StringConcat) during
        # `_run()`. Mechanical ingest of held content -- the sentence is the
        # engine's. Absent (no story_fields) the legacy `headline` string is used.
        if story_fields is not None:
            for k in ("subject", "event_verb", "place", "patron"):
                self.eng.set_attr(story, k, str(story_fields.get(k, "")))
            self.eng.set_attr(story, "damaging", float(story_fields.get("damaging", 0)))
            self.eng.set_attr(story, "has_patron", float(story_fields.get("has_patron", 0)))
            self.eng.set_attr(story, "render_me", 1.0)
            self.eng.set_attr(story, "text_written", 0.0)
        minutes = self.eng.add_node("Minutes", dict(_MINUTES_DEFAULTS,
                                                    clerk_bias=float(clerk_bias)))
        self.eng.add_edge_unchecked(minutes, "of_event", ev)
        quorum = max(1.0, round(CHENOWETH_FRAC * n))
        coal = self.eng.add_node("Coalition", {"quorum": float(quorum),
                                               "informed": 0.0, "formed": 0.0})
        self.eng.add_edge_unchecked(coal, "in_town", self._news_town)

        self._run()

        printed = int(self.eng.node(story)["attrs"].get("printed", 0.0))
        suppressed = int(self.eng.node(story)["attrs"].get("suppressed", 0.0))
        content = float(self.eng.node(story)["attrs"].get("content", 0.0))
        informed = int(self.eng.node(coal)["attrs"].get("informed", 0.0))
        formed = int(self.eng.node(coal)["attrs"].get("formed", 0.0))
        share = informed / float(n)
        # propagate the informed flag onto the mover so the journal can read it.
        for nm in living:
            f = float(self.eng.node(self._civic[nm])["attrs"].get("knows_event_flag", 0.0))
            self.eng.set_attr(self._movers[nm], "jn_informed", f)

        if printed:
            self.rung_fire["bigville_news_press"] += 1
        if informed > 0:
            self.rung_fire["bigville_news_reach"] += 1
        # block 297000 fold-in: the headline is the RENDERED story text (the graph
        # wrote it) when structured fields were supplied; else the legacy string.
        rendered = self.eng.node(story)["attrs"].get("text", "")
        rendered = rendered if isinstance(rendered, str) else str(rendered)
        if story_fields is not None and rendered:
            headline = rendered
        rec = dict(tick=self.world_epoch, day=int(self.world_epoch // TICKS_PER_DAY),
                   printed=printed, suppressed=suppressed, content=round(content, 2),
                   informed=informed, n=n, share=round(share, 3), quorum=int(quorum),
                   formed=formed, kind=kind, headline=headline)
        self.papers.append(rec)
        self.informed_share_series.append((self.world_epoch, informed, n, share, formed))
        verb = ("SUPPRESSED" if suppressed else ("printed" if printed else "spiked"))
        txt = "THE BIGVILLE TIMES %s: %s (informed %d/%d = %.0f%%%s)" % (
            verb, headline, informed, n, 100 * share,
            "; COALITION FORMS" if formed else "")
        self._emit_social("paper", txt, actors=[])
        if formed:
            self.rung_fire["bigville_news_reach_coalition"] += 1
        return rec

    # ==================================================================== COUNCIL
    def _install_council_gov(self):
        """Constitute the two-tier governance council on the town engine: a Council with a
        backing-graph of Members (a clerk among them), a Mayor (John), and a Board. The
        Meeting/Notice are minted per council-day. Distinct from R10's viol-Council (that
        has no has_member edges), so the cm_* rules only ever match THIS one."""
        self._gov_council = self.eng.add_node("Council", {"captured": 0.0})
        self._gov_board = self.eng.add_node("Board", {})
        # seat the rich + middle as members (John's-bloc structural corruption possible).
        seated = [nm for nm in self.people
                  if self.classes.get(nm) in ("rich", "middle")][:3] or self.people[:3]
        self._gov_members = {}
        r = self._rng3
        for i, nm in enumerate(seated):
            attrs = dict(_MEMBER_DEFAULTS)
            attrs.update(name=self.display.get(nm, nm),
                         base_position=float(round(r.normal(1.0, 0.5), 3)),
                         self_serving_premium=float(round(abs(r.normal(0.5, 0.4)), 3)),
                         clerk_bias=(0.5 if i == 0 else 0.0))
            m = self.eng.add_node("Member", attrs)
            self.eng.add_edge_unchecked(self._gov_council, "has_member", m)
            self._gov_members[nm] = m
            if i == 0:
                self._gov_clerk_nm = nm
        # the mayor = the mover named John (the R10b named cast), else the richest.
        john = None
        for nm in self.people:
            if self.roles2.get(nm) == "mayor":
                john = nm
                break
        self._mayor_nm = john or seated[0]
        self._gov_mayor = self.eng.add_node("Mayor", {
            "name": self.display.get(self._mayor_nm, "John"), "stated_position": 2.0})
        self._install_council_bell_clock()

    def _install_council_bell_clock(self):
        """Bell-time council scheduling (block 323000): the meeting interval is a BYLAW
        (council-owned data, not a Python constant), and a BEADLE counts the curfew bells
        and rings the ASSEMBLY bell when the bylaw says a meeting is due -- replacing
        `day % COUNCIL_EVERY_DAYS` integer math. Wired on an ISOLATED clock hub with new
        edge/node types, so the bell rules only ever match this subgraph."""
        self.eng.load_seed_manifest(manifest_for("bigville_bells"), None)
        self.eng.load_seed_manifest(manifest_for("bigville_bell_schedule"), None)
        self._clock = self.eng.add_node("BellClock", {})
        self._clock_church = self.eng.add_node("Church", {})
        self.eng.add_edge_unchecked(self._clock, "has_church", self._clock_church)
        self._clock_bell = self.eng.add_node("Bell", {"ring_armed": 0.0, "toll_kind": "",
                                                      "call_strength": 1.0, "toll_hour": 0.0})
        self.eng.add_edge_unchecked(self._clock_church, "has_bell", self._clock_bell)
        self._beadle = self.eng.add_node("Beadle", {"days_since_meeting": 0.0})
        self.eng.add_edge_unchecked(self._clock, "has_beadle", self._beadle)
        self._council_bylaw = self.eng.add_node(          # the interval as a bylaw, not a constant
            "Bylaw", {"name": "council_meeting_interval", "value": float(COUNCIL_EVERY_DAYS)})
        self.eng.add_edge_unchecked(self._clock, "has_bylaw", self._council_bylaw)
        self._seen_council_peals = set()

    def _council_due_by_bell(self):
        """Toll the curfew bell (one day). The beadle counts it; when the bylaw interval
        is reached it rings the assembly bell. Returns whether a fresh ASSEMBLY peal
        appeared. Scoped to the bell subgraph (no force_all_dirty) so the town dynamics
        are untouched -- only the newly-armed bell cascade fires."""
        self.eng.set_attr(self._clock_bell, "toll_kind", "curfew")
        self.eng.set_attr(self._clock_bell, "ring_armed", 1.0)
        for _ in range(4):
            self.eng.run_rules(1000000)
        due = False
        for p in self.eng.neighbours(self._clock_church, "peals"):
            if p in self._seen_council_peals:
                continue
            self._seen_council_peals.add(p)
            if self.eng.node(p)["attrs"].get("kind") == "assembly":
                due = True
        return due

    def _run_council(self, *, public_demand, malice_on=1, captured=0):
        """Arm ONE scheduled meeting + post its notice. cm_convene (cadence),
        cm_public_address, cm_member_vote (private), cm_private_decision, the 234 gap, then
        the clerk's minutes + the board post + literacy-gated reading -- ALL rules. This
        only mints the Meeting/Notice, wires attendees/visits, runs, and reads."""
        living = self._civic_living()
        self.eng.set_attr(self._gov_council, "captured", float(captured))
        mtg = self.eng.add_node("Meeting", {
            "now_day": 0.0, "cadence": 1.0, "armed": 1.0, "convened": 0.0,
            "public_demand": float(public_demand), "private_on": 1.0,
            "malice_on": float(malice_on), "public_address": 0.0,
            "held_decision": 0.0, "stated_held_gap": 0.0})
        self.eng.add_edge_unchecked(mtg, "convenes", self._gov_council)
        self.eng.add_edge_unchecked(mtg, "addressed_by", self._gov_mayor)
        for nm in living:
            self.eng.set_attr(self._civic[nm], "at_hall", 1.0)
            self.eng.add_edge_unchecked(mtg, "attended_by", self._civic[nm])
        self._run()

        convened = int(self.eng.node(mtg)["attrs"].get("convened", 0.0))
        address = float(self.eng.node(mtg)["attrs"].get("public_address", 0.0))
        decision = float(self.eng.node(mtg)["attrs"].get("held_decision", 0.0))
        gap = float(self.eng.node(mtg)["attrs"].get("stated_held_gap", 0.0))

        # -- post the notice (clerk writes -> board posts -> residents read) --------
        notice = self.eng.add_node("Notice", {
            "recorded": 0.0, "posted": 0.0, "officially_known": 0.0,
            "literacy_gate_on": 1.0})
        self.eng.add_edge_unchecked(notice, "of_meeting", mtg)
        self.eng.add_edge_unchecked(notice, "written_by",
                                    self._gov_members[self._gov_clerk_nm])
        self.eng.add_edge_unchecked(self._gov_board, "posts", notice)
        for nm in living:
            self.eng.add_edge_unchecked(self._civic[nm], "visits", self._gov_board)
        self._run()
        recorded = float(self.eng.node(notice)["attrs"].get("recorded", 0.0))
        off_known = sum(1 for nm in living
                        if float(self.eng.node(self._civic[nm])["attrs"].get(
                            "knows_law_flag", 0.0)) >= 1.0)

        if convened:
            self.rung_fire["bigville_council_gov"] += 1
        if recorded != 0.0 or off_known > 0:
            self.rung_fire["bigville_council_board"] += 1
        rec = dict(tick=self.world_epoch, day=int(self.world_epoch // TICKS_PER_DAY),
                   convened=convened, public_address=round(address, 2),
                   held_decision=round(decision, 2), gap=round(gap, 2),
                   posted=round(recorded, 2), officially_known=off_known,
                   captured=int(captured))
        self.council_log.append(rec)
        txt = ("COUNCIL convened: Mayor addressed %.1f, privately decided %.1f "
               "(234 gap %.1f); noticeboard posts %.1f, %d residents read it"
               % (address, decision, gap, recorded, off_known))
        self._emit_social("council", txt, actors=[self._mayor_nm])
        return rec

    # ==================================================================== DRAMA
    def _install_drama(self):
        """BEST-EFFORT: additively load the political-drama machinery + populate John
        (mayor, EmotionHub w/ spite value economy) / Mary (pastor, ToM codebook) / a
        villager credibility network. If the additive load or a smoke step fails, record
        DORMANT with the reason (never crash the town)."""
        try:
            for sid in ("core_emotions", "spite_skill", "bigville_drama_social"):
                self.eng.load_seed_manifest(manifest_for(sid), None)
        except Exception as e:                                           # pragma: no cover
            self.rung_status["bigville_drama_social"] = "dormant(load failed: %r)" % e
            self._drama = None
            return
        try:
            self._build_drama_subgraph()
            self._drama = True
            # smoke: one beat must not raise.
            self._drama_step(smoke=True)
        except Exception as e:                                           # pragma: no cover
            self.rung_status["bigville_drama_social"] = "dormant(populate/step failed: %r)" % e
            self._drama = None

    def _build_drama_subgraph(self):
        e = self.eng
        self._d_sg = e.add_node("Supergraph", {})
        # Mary -- a ToM hub + disposition codebook.
        self._d_mary = e.add_node("MaryTom", {"name": "Mary", "role": "pastor"})
        self._d_tp = e.add_node("ToMParams", {
            "tom_on": 1.0, "inferred": 0.0, "goal_formed": 0.0, "claim_made": 0.0,
            "n_obs": 0.0, "n_harm": 0.0, "observed_harm_rate": 0.0})
        e.add_edge_unchecked(self._d_mary, "has_tom_params", self._d_tp)
        self._d_gens = []
        for disp, phr in (("benign", 0.0), ("hostile", 100.0)):
            g = e.add_node("DispositionGenerator", {
                "disposition": disp, "predicts_harm_rate": phr, "observed_harm_rate": 0.0})
            e.add_edge_unchecked(self._d_mary, "has_generator", g)
            self._d_gens.append(g)
        # John -- a psychopath mayor (w_supergraph=0, w_spite=1) decided by the economy.
        self._d_john = e.add_node("EmotionHub", {"name": "John", "role": "mayor"})
        ep = dict(enabled=1.0, w_supergraph=0.0, w_spite=1.0, order_n=1.0,
                  skill_spite_on=1.0, public_on=1.0, deception_on=1.0, mood_bias=0.0,
                  residual_thresh=100.0, high_arousal=800.0, mid_arousal=400.0,
                  low_arousal=50.0, comms_on=0.0)
        epn = e.add_node("HeldEmotionParams", ep)
        e.add_edge_unchecked(self._d_john, "has_emotion_params", epn)
        e.add_edge_unchecked(self._d_john, "member_of", self._d_sg)
        e.add_edge_unchecked(self._d_john, "disfavors", self._d_mary)
        self._d_jdec = e.add_node("HarvestDecision", {
            "chosen_harvest2": -1.0, "chosen_burn": -1.0, "stated_benevolent": -1.0})
        e.add_edge_unchecked(self._d_john, "has_decision", self._d_jdec)
        appr = dict(appraised=1.0, individual_benefit=0.0, individual_cost=0.0,
                    supergraph_contribution=0.0, burn_harm=0.0, harvest_level=0.0,
                    burn_level=0.0, collective_success=0.0, collective_success_prev=0.0,
                    contribution_by_self=0.0, observed_by_other=0.0, valued_goal=0.0,
                    goal_blocked=0.0, blocker_present=0.0, attachment=0.0,
                    regroundable=0.0, contamination=0.0, was_engaged=0.0, residual=0.0,
                    residual_prev=0.0, threat=0.0, threat_c0=0.0, threat_half_life=1.0,
                    threat_last_refresh=0.0, threat_now_epoch=0.0, t_present=100.0,
                    v_max=0.0, step=0.0, step_prev=0.0, attach_v0=0.0, attach_k_now=0.0,
                    attach_k_prev=0.0)
        gov = dict(appr); gov.update(individual_benefit=2.0, harvest_level=1.0,
                                     supergraph_contribution=1.0)
        und = dict(appr); und.update(individual_benefit=2.0, individual_cost=1.0,
                                     burn_level=1.0, supergraph_contribution=-4.0,
                                     burn_harm=5.0)
        for c_attrs in (gov, und):
            c = e.add_node("Appraisal", c_attrs)
            e.add_edge_unchecked(self._d_john, "has_appraisal", c)
            e.add_edge_unchecked(self._d_john, "has_candidate", c)
        # the credibility network -- N villagers weighting a charming face vs a claim.
        self._d_village = e.add_node("Village", {"name": "Bigville"})
        self._d_villagers = []
        charm = [0, 1, 1, 2, 3]
        for i in range(5):
            v = e.add_node("Villager", {
                "name": "drama_villager_%d" % i, "cred_on": 1.0,
                "charm_weight": float(charm[i]), "claim_weight": 2.0,
                "difficulty_penalty": 1.0, "hostile_weight": 1.0,
                "seen_benevolent": 0.0, "seen_hostile": 0.0, "heard_claim": 0.0,
                "backs_mary": -1.0})
            e.add_edge_unchecked(self._d_village, "has_villager", v)
            self._d_villagers.append(v)
        self._d_tick = 0

    def _drama_step(self, smoke=False):
        """One political-drama beat (mechanical accumulation around the rule fixpoint,
        exactly as BigvilleDramaWorld.step): run rules (John decides + states his face),
        tally what each observer SAW, run rules (Mary infers/goals/claims; villagers
        back). Reads chosen_burn / backs_mary. NO decision here."""
        e = self.eng
        self._d_tick += 1
        self._run()
        burn = max(0, int(e.node(self._d_jdec)["attrs"].get("chosen_burn", -1.0)))
        stated = max(0, int(e.node(self._d_jdec)["attrs"].get("stated_benevolent", -1.0)))
        n_obs = int(e.node(self._d_tp)["attrs"]["n_obs"]) + 1
        n_harm = int(e.node(self._d_tp)["attrs"]["n_harm"]) + burn
        rate = (100 * n_harm) // max(n_obs, 1)
        e.set_attr(self._d_tp, "n_obs", float(n_obs))
        e.set_attr(self._d_tp, "n_harm", float(n_harm))
        e.set_attr(self._d_tp, "observed_harm_rate", float(rate))
        for g in self._d_gens:
            e.set_attr(g, "observed_harm_rate", float(rate))
        mary_claims = int(e.node(self._d_tp)["attrs"].get("goal_formed", 0.0)) == 1
        for v in self._d_villagers:
            a = e.node(v)["attrs"]
            e.set_attr(v, "seen_benevolent", a["seen_benevolent"] + stated)
            e.set_attr(v, "seen_hostile", a["seen_hostile"] + (1 - stated))
            if mary_claims:
                e.set_attr(v, "heard_claim", a["heard_claim"] + 1.0)
        self._run()
        if smoke:
            return
        backs = sum(1 for v in self._d_villagers
                    if int(max(0, e.node(v)["attrs"].get("backs_mary", -1.0))) == 1)
        disp = None
        for inf in e.nodes("InferredDisposition"):
            disp = e.node(inf)["attrs"].get("disposition")
            break
        self.rung_fire["bigville_drama_social"] += 1
        # mirror John's scheme onto his mover so the journal/held export can read it.
        e.set_attr(self._movers[self._mayor_nm], "backs_mary", float(backs))
        txt = ("DRAMA: Mayor John held=%s stated=%s (%s); Mary infers '%s'; %d/5 villagers back Mary"
               % ("undermine" if burn else "govern",
                  "benevolent" if stated else "hostile",
                  "DECEPTIVE" if (burn and stated) else "candid", disp, backs))
        self._emit_social("drama", txt, actors=[self._mayor_nm])
        return dict(held=burn, stated=stated, inferred=disp, backs=backs)

    # ==================================================================== SCHOOL
    def _install_school(self):
        """BEST-EFFORT: mint a School staffed by a schoolmaster mover, honestly OPEN it by
        paying the master through the fisc salary RULE (a funded Treasury -pays-> master,
        salary_armed -> fs_pay_salary -> paid_count>=1 -> sc_school_open), and enrol pupils
        (dedicated Child nodes w/ Skill + the STANDING-239 window dyad at setpoint). Lessons
        run on schooldays via sc_acquire. Records DORMANT-with-reason if the open-gate or
        acquire does not fire."""
        try:
            from worlds.coreg_dyad_world import (SETPOINT, K_SELF, K_CO, WIDEN_DELTA,
                                                 NARROW_DELTA, MIN_HALF_WIDTH,
                                                 SAFETY_STEP, SAFETY_PRIOR0)
        except Exception as e:                                           # pragma: no cover
            self.rung_status["bigville_school_learn"] = "dormant(coreg import: %r)" % e
            return
        e = self.eng
        # the schoolmaster is a DEDICATED node (NOT a town mover), so the whole school
        # sub-ledger (Treasury <-> Master salary) is a CLOSED account the town economy
        # never touches -- Sigma(coin) stays invariant. Its name is the register foil for
        # the export; the teaching DECISION is still the seed rule.
        disp = None
        for nm in self.people:
            if self.roles2.get(nm) == "pastor":
                disp = self.display.get(nm)
                break
        self._school_master_name = disp or "Schoolmaster"
        m = e.add_node("Servant", dict(
            role=3.0, fair_salary=6.0, stated_rate=1.0, sabotage_rate=0.0, coerced=0.0,
            held_rate=0.0, willing=0.0, sabotaged=0.0, underpaid=0.0, quality_armed=0.0,
            salary=6.0, salary_armed=0.0, paid_count=0.0, unpaid=0.0, coin=0.0,
            name=self._school_master_name))
        self._school_master = m
        # a funded Treasury pays the master through the RULE (honest open). Treasury.funds
        # + Master.coin are both counted by system_coin and only exchange with each other.
        self._school_treasury = e.add_node("Treasury", {"funds": 500.0, "coin": 0.0})
        e.add_edge_unchecked(self._school_treasury, "pays", m)
        e.set_attr(m, "salary_armed", 1.0)
        self._run()                                    # fs_pay_salary -> paid_count>=1
        self._school = e.add_node("School", {"open": 0.0, "closed": 0.0, "open_armed": 1.0,
                                             "name": "school"})
        e.add_edge_unchecked(self._school, "staffed_by", m)
        self._run()                                    # sc_school_open
        opened = int(e.node(self._school)["attrs"].get("open", 0.0))
        if not opened:
            paid = float(e.node(m)["attrs"].get("paid_count", 0.0))
            self.rung_status["bigville_school_fund"] = (
                "dormant(school not open; master paid_count=%g)" % paid)
        # pupils -- dedicated Child nodes at setpoint (in-window), enrolled + co-regulated.
        self._pupils = []
        for i in range(4):
            child = e.add_node("Child", {
                "name": "pupil_%d" % i, "prereq_met": 1.0, "acquire_armed": 0.0,
                "acquired": 0.0, "last_gain": 0.0, "fail_reason": -1.0,
                "base_capability": 0.3, "capability": 0.0, "matured": 0.0, "adult": 0.0,
                "coa_armed": 0.0})
            s = e.add_node("Skill", {"activity": 1.0, "level": 0.0, "ceiling": 100.0})
            e.add_edge_unchecked(child, "has_skill", s)
            iaff = e.add_node("AffectiveState", {
                "name": "pupil_%d_affect" % i, "baseline": 1.0, "valence": 0.0,
                "arousal": SETPOINT, "resolution": 0.0, "selection_threshold": 0.0,
                "securing": 0.0, "competence": 0.0, "epoch": -1.0, "tick_epoch": 0.0,
                "sr_epoch": 0.0, "cr_epoch": 0.0, "k_self": K_SELF, "k_co": K_CO,
                "setpoint": SETPOINT, "dysregulated": 0.0, "dysreg_kind": 0.0,
                "in_episode": 0.0, "got_coreg": 0.0})
            e.add_edge_unchecked(child, "has_affective_state", iaff)
            wot = e.add_node("WindowOfTolerance", {
                "name": "pupil_%d_window" % i, "lo": -30.0, "hi": 30.0,
                "half_width": 30.0, "widen_delta": WIDEN_DELTA, "narrow_delta": NARROW_DELTA,
                "min_half_width": MIN_HALF_WIDTH, "safety_prior": float(SAFETY_PRIOR0),
                "safety_step": SAFETY_STEP, "widen_count": 0.0, "narrow_count": 0.0})
            e.add_edge_unchecked(child, "has_window", wot)
            e.add_edge_unchecked(child, "enrolled_in", self._school)
            e.add_edge_unchecked(child, "learns_from", m)
            e.add_edge_unchecked(child, "attended_by", m)
            self._pupils.append((child, s))
        self._run()

    def _run_school(self):
        """One class period: arm the master's quality decision + each pupil's acquisition
        (sc_master_quality -> held_rate; sc_acquire / sc_fail_*), then read the outcome."""
        if not self._school:
            return
        e = self.eng
        m = self._school_master
        e.set_attr(m, "quality_armed", 1.0)
        learned = 0
        for child, _s in self._pupils:
            e.set_attr(child, "acquire_armed", 1.0)
        lv0 = [float(e.node(s)["attrs"].get("level", 0.0)) for _c, s in self._pupils]
        self._run()
        lv = [float(e.node(s)["attrs"].get("level", 0.0)) for _c, s in self._pupils]
        # a lesson "landed" for a pupil whose skill LEVEL rose (sc_acquire adds a gain);
        # the one-shot `acquired` flag latches after the first, so level-delta is truer.
        learned = sum(1 for a, b in zip(lv0, lv) if b > a)
        if learned:
            self.rung_fire["bigville_school_learn"] += learned
        self._emit_social("school", "SCHOOL: class held, %d/%d pupils learned (skill levels %s)"
                          % (learned, len(self._pupils),
                             ",".join("%.0f" % x for x in lv)), actors=[])
        return learned

    # ==================================================================== LOUD
    def _install_loud(self):
        """BEST-EFFORT: mint a small loudness comm scene -- Person nodes at real town
        positions (a speaker, a near hearer, a far hearer) + classroom pupils with
        peer_pull. speak() mints Utterance/Reception pairs; lo_deliver_content / lo_observe_act
        decide earshot vs sight; lo_chatter_distracts / lo_control_restores move a pupil's
        attending. No occluders modelled here (sight_occluded=0) -- the loudness/distance
        gate is the mechanism exercised."""
        e = self.eng
        self._loud_people = {}
        # three street people from the living cast (by position spread).
        living = [nm for nm in self.people if not self.is_dead(nm)]
        picks = living[:3] if len(living) >= 3 else living
        for nm in picks:
            p = e.add_node("Person", {"name": self.display.get(nm, nm),
                                      "base_loudness": 6.0, "max_loudness": 12.0,
                                      "peer_pull": 0.0, "attending": 1.0})
            self._loud_people[nm] = p
        self._loud_picks = picks
        # two classroom pupils with peer_pull>0 (chatter-susceptible).
        self._loud_pupils = []
        for i in range(2):
            p = e.add_node("Person", {"name": "class_pupil_%d" % i,
                                      "base_loudness": 3.0, "max_loudness": 10.0,
                                      "peer_pull": 1.0, "attending": 1.0})
            self._loud_pupils.append(p)
        self._loud = True

    def _speak(self, spk, hearers, *, chosen_loudness, is_control=0):
        """Mint an Utterance + a Reception per hearer with mechanical geometry (Chebyshev
        distance from town positions; no occluder), run the rules, read got_content /
        observed_act. Transient nodes purged after read-off."""
        e = self.eng
        u = e.add_node("Utterance", {
            "speaker": "s", "addressee": "a", "chosen_loudness": float(chosen_loudness),
            "choice_on": 1.0, "loudness_on": 1.0, "is_control": float(is_control),
            "base_loudness": float(e.node(spk)["attrs"]["base_loudness"]),
            "max_loudness": float(e.node(spk)["attrs"]["max_loudness"]),
            "flat_radius": 6.0, "eff_loudness": 0.0})
        e.add_edge_unchecked(u, "spoken_by", spk)
        recs = []
        for (hn, dist) in hearers:
            r = e.add_node("Reception", {
                "dist": float(dist), "sight_occluded": 0.0, "hear_occluded": 0.0,
                "got_content": 0.0, "observed_act": 0.0})
            e.add_edge_unchecked(u, "reception", r)
            e.add_edge_unchecked(r, "to", hn)
            recs.append(r)
        self._run()
        out = []
        for r in recs:
            a = e.node(r)["attrs"]
            out.append((int(a.get("got_content", 0.0)), int(a.get("observed_act", 0.0))))
        # purge transient utterance/reception/commact.
        for r in recs:
            for ca in list(e.neighbours(r, "act")):
                e.remove_node(ca)
            e.remove_node(r)
        e.remove_node(u)
        return out

    def _run_loud(self):
        """One loud beat: a near/far street utterance (content near, observed-only far) +
        a classroom chatter beat then a teacher control beat (attending drops then restores)."""
        if not self._loud:
            return
        e = self.eng
        picks = self._loud_picks
        # STREET: speaker to a near hearer (dist 3, hears content) + a far hearer (dist 20,
        # observed-as-conversation only). Positions from the real town layout.
        if len(picks) >= 2:
            spk = self._loud_people[picks[0]]
            near = self._loud_people[picks[1]]
            far = self._loud_people[picks[2]] if len(picks) >= 3 else near
            res = self._speak(spk, [(near, 3.0), (far, 20.0)], chosen_loudness=8.0)
            near_content, near_obs = res[0]
            far_content, far_obs = res[-1]
            if near_content or far_obs:
                self.rung_fire["bigville_loud_comm"] += 1
            self._emit_social("loud",
                              "LOUD: %s speaks (loud 8); near hearer content=%d, far witness observes-only=%d"
                              % (self.display.get(picks[0], "?"), near_content, far_obs),
                              actors=[])
        # CLASSROOM: a peer whispers chatter (content reaches, is_control=0 -> attending 0);
        # then the teacher's loud control (is_control=1 -> attending 1).
        if len(self._loud_pupils) >= 2:
            p0, p1 = self._loud_pupils[0], self._loud_pupils[1]
            before = float(e.node(p1)["attrs"].get("attending", 1.0))
            self._speak(p0, [(p1, 2.0)], chosen_loudness=6.0, is_control=0)
            distracted = float(e.node(p1)["attrs"].get("attending", 1.0))
            self._speak(p0, [(p1, 2.0)], chosen_loudness=10.0, is_control=1)
            restored = float(e.node(p1)["attrs"].get("attending", 1.0))
            if distracted < before or restored > distracted:
                self.rung_fire["bigville_loud_class"] += 1
            self._emit_social("loud",
                              "CLASS: pupil attending %d -> chatter %d -> teacher-control %d"
                              % (int(before), int(distracted), int(restored)), actors=[])

    # ============================================================ CONSERVATION
    def system_coin(self):
        """R10b's conserved quantity + the school Treasury's `funds` (a fiscal account,
        exactly like the bank's `reserves`). fs_pay_salary moves funds->servant.coin
        one-for-one, so counting the Treasury keeps Sigma(coin) INVARIANT across the run."""
        base = super().system_coin()
        funds = 0.0
        for t in self.eng.nodes("Treasury"):
            funds += float(self.eng.node(t)["attrs"].get("funds", 0.0) or 0.0)
        return base + funds

    # ==================================================================== FEED
    def _emit_social(self, kind, text, *, actors):
        rec = dict(tick=self.world_epoch, kind=kind, actors=list(actors), text=text)
        self.events.append(rec)          # into the exported feed
        self.social_log.append(rec)

    # ==================================================================== TICK
    def integ_step(self):
        """R10b's composite tick, then the ARMED social phases on cadence. Social events
        (paper printings, council decisions posted, coalition, drama, school, loud, journal
        writes) are counted into the tick's `activity` (a structural transition, exactly as
        a birth is). NO scheduled shocks; every social DECISION is a seed rule."""
        if self.exploded is not None:
            return
        n_social_before = len(self.social_log)
        super().integ_step()
        if self.exploded is not None or not self.macro:
            return
        # social phases fire once per DAY at the day boundary.
        if self.world_epoch % TICKS_PER_DAY != 0:
            return
        day = self.world_epoch // TICKS_PER_DAY

        # -- WEEKLY PAPER: the week's salient real event -> a story --------------
        if day > 0 and day % PAPER_EVERY_DAYS == 0:
            week_deaths = [d for d in self.death_log
                           if d.get("day", -1) > day - PAPER_EVERY_DAYS]
            homeless = sum(1 for nm in self.people if not self.is_dead(nm)
                           and self.homeless_of(nm))
            truth = float(10 + len(week_deaths) * 5 + homeless * 3)
            # The week's salient event -> ATOMIC held tokens (a real name, a
            # kind-selected verb); the SENTENCE is assembled by the bigville_headline
            # StringConcat rules, not here. A death leads (its held subject is the
            # dead resident's real name); else the homelessness story (which names
            # the council as patron -> launderable by a captured paper).
            if week_deaths:
                d = week_deaths[-1]
                fields = dict(subject=str(d.get("name", "A resident")),
                              event_verb="has died", place="this week",
                              patron="", damaging=0, has_patron=0)
            else:
                fields = dict(subject="Several families",
                              event_verb="were left without a roof",
                              place="in Bigville", patron="the council",
                              damaging=1, has_patron=1)
            self._print_paper(truth_value=truth, kind="weekly", story_fields=fields)

        # -- COUNCIL: convenes when the BEADLE rings the ASSEMBLY bell per the council's
        #    bylaw (bell time), NOT `day % COUNCIL_EVERY_DAYS` integer math. The beadle
        #    tolls+counts the curfew bell every day; _run_council fires when it's due.
        if day > 0 and self._council_due_by_bell():
            homeless = sum(1 for nm in self.people if not self.is_dead(nm)
                           and self.homeless_of(nm))
            self._run_council(public_demand=float(1 + homeless))

        # -- SCHOOL LESSONS ------------------------------------------------------
        if self._school and day > 0 and day % SCHOOL_EVERY_DAYS == 0:
            self._run_school()

        # -- LOUD comm + classroom ----------------------------------------------
        if self._loud and day > 0 and day % LOUD_EVERY_DAYS == 0:
            self._run_loud()

        # -- DRAMA beat ----------------------------------------------------------
        if self._drama and day > 0 and day % DRAMA_EVERY_DAYS == 0:
            try:
                self._drama_step()
            except Exception:
                pass

        # -- NIGHTLY JOURNAL (every night) --------------------------------------
        self._write_journals()

        # fold the social transitions into this tick's activity (like a birth).
        n_social = len(self.social_log) - n_social_before
        self.macro[-1]["activity"] += int(n_social)
        self.macro[-1]["social"] = int(n_social)

    # ==================================================================== read-offs
    def latest_journal(self, nm):
        """The resident's LATEST JournalEntry attrs (max day), or None. Pure read."""
        best, best_day = None, -1.0
        try:
            for j in self.eng.neighbours(self._movers[nm], "wrote_journal"):
                a = self.eng.node(j)["attrs"]
                d = float(a.get("day", -1.0))
                if d >= best_day:
                    best, best_day = a, d
        except Exception:
            return None
        return best

    def rung_report(self):
        """Per-rung fired/dormant table (seed id -> status string). Pure read."""
        out = {}
        FIRED = {
            "bigville_news_press": "Stories printed",
            "bigville_news_reach": "printings that informed >=1 resident",
            "bigville_news_reach_coalition": "coalitions formed",
            "bigville_council_gov": "councils convened",
            "bigville_council_board": "notices posted/read",
            "bigville_school_learn": "pupil-lessons acquired",
            "bigville_loud_comm": "street utterances delivered",
            "bigville_loud_class": "classroom chatter/control beats",
            "bigville_drama_social": "drama beats",
            "bigville_journal_nightly": "journal entries minted",
        }
        for sid, label in FIRED.items():
            c = self.rung_fire.get(sid, 0)
            out[sid] = ("fired(%d %s)" % (c, label) if c > 0
                        else self.rung_status.get(sid, "dormant(never fired)"))
        # siblings we did NOT populate this rung -- honest dormant.
        for sid in ("bigville_fisc_state", "bigville_goal_life", "bigville_goal_dream",
                    "bigville_coll_collect", "bigville_build_construct",
                    "bigville_infant_care"):
            out.setdefault(sid, self.rung_status.get(
                sid, "dormant(not populated this rung -- reported, not forced)"))
        return out

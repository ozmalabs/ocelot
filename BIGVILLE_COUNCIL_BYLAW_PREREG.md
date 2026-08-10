# PREREG — block 322000: the council's meeting schedule is a bylaw, enacted by the beadle, on bell time

The old convening (`cm_convene`, block 268000) fired on `now_day % cadence == 0` —
a global injected day counter and an integer-modulo formula. The user's correction:
**how often and when the council meets should be set by the COUNCIL in their BYLAWS,
and then run in game by ACTORS, not integer math.** So:

- the meeting interval is a **bylaw** — a `Law` the council holds in its LawBook and
  **amends through its own legislature** (the same `propose_bill`/`leg_amend` spine);
- an **actor**, the **beadle**, counts the passing days **by the curfew bell** and
  **rings the assembly bell** when the bylaw says a meeting is due;
- the council **convenes on the assembly bell** — a rung event an actor caused, not a
  modulo of a global clock.

This composes `bigville_legislature` (the bylaw + amendment) and `bigville_bells`
(the curfew/assembly bells). The legacy `council_gov`/integ3 is left untouched.

## The mechanism (`bigville_council_bylaw.json`)

The LawBook holds a `Law{name: "council_meeting_interval", value: N, status: active}`
(the bylaw). The town `has_beadle` a `Beadle{days_since_meeting}`.

- **`cb_beadle_counts`** — on each **curfew** `BellPeal` the beadle increments
  `days_since_meeting` (once per peal — the actor marking the days by the bell).
- **`cb_ring_assembly`** — when `days_since_meeting ≥` the bylaw's value, the beadle
  **rings the assembly bell** (arms it, `toll_kind = assembly`) and resets the tally.
  The threshold is READ from the bylaw, not hardcoded.
- **`cb_convene`** — an **assembly** `BellPeal` convenes a `Meeting` (once per peal).
  The council meets because the bell was rung, not because a formula fired.

Amending the bylaw (a passed `leg_amend` bill) changes the value the beadle reads, so
the council governs its own calendar.

## Gates (pass/fail, pre-registered)

1. **G-schedule-is-a-bylaw (HEADLINE):** the meeting interval lives as a `Law` in the
   book; the town holds no `now_day`/`cadence` and the seed contains no `Mod`
   scheduling.
2. **G-beadle-rings-on-schedule (HEADLINE):** with the bylaw interval = N, the council
   does NOT convene for the first N−1 curfew tolls and DOES convene on the Nth (the
   beadle counted the days and rang the assembly bell).
3. **G-convene-on-the-bell-not-math:** the meeting convenes on the assembly peal; with
   no assembly bell rung, no meeting exists.
4. **G-amend-the-bylaw-changes-the-calendar (HEADLINE):** amend the interval (via a
   passed bill) and the next meeting falls after the NEW number of curfew days — the
   council sets its own schedule.
5. **G-no-integer-clock (falsifier / architecture):** there is no global `now_day` or
   `% cadence`; the schedule is bylaw + beadle + bell, and repeated curfew tolls
   produce a meeting exactly every `interval` days (the actor re-accumulates each cycle).
6. **G-no-python-decision (source audit):** count/ring/convene are the seed rules; the
   beadle's tally and the ringing are graph-native; the adapter only tolls the curfew
   bell and reads.

## Scope / honesty
- The beadle's `days_since_meeting` is an actor's running tally reset each meeting —
  an accumulation driven by perceiving curfew bells, NOT a global `now_day % cadence`
  evaluated as a scheduling formula. The comparison `tally ≥ interval` reads the
  council's own bylaw.
- "When" (which hour) the assembly is called can be refined to a bylaw hour; this rung
  fixes the "how often" (interval) as a bylaw and the actor/bell enactment. The legacy
  `council_gov` cadence is superseded conceptually and left in place (its integ3 gates
  untouched).
- Isolated demonstrator (`self_load_only`); composes with legislature + bells; no Rust;
  `.so` untouched (`a8a9012c`).

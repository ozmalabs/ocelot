# PREREG — block 320000: the church bells are the clock (time is not forced)

Until now the town ran on a **forced clock**: the adapter set `town.sunday = 1` (or
advanced a day counter) and every agent was driven by that global flag. That is the
smuggled global clock — a scripted time imposed on the agents. This rung removes it:
**the church has bells; they are heard across the town; the bells are what tell the
characters the time; so events are not scripted onto everyone — each agent perceives
the bell and CHOOSES to respond.**

This is the town-scale form of the substrate's standing principle (the global clock
is the lie; time is per-sensor / a heard event, not a read global).

## The mechanism (`bigville_bells.json`)

The church `has_bell` a `Bell`. The sexton rings it (one world event — pulling the
rope, `ring_armed`). Everything else follows from the heard peal; there is **no
global `now`**.

- **`bl_ring`** — a rung bell emits a `BellPeal{hour, kind, call_strength}` from the
  church (the sexton's single act); `ring_armed → 0`.
- **`bl_hear_awake`** — an **awake** resident hears the peal and **learns the hour**
  (`known_hour = peal.hour`). The bell tells the time; nobody reads a global clock.
- **`bl_wake_rested`** — an **asleep but sufficiently rested** resident **wakes** at
  the bell (`asleep → 0`) and learns the hour. An **exhausted** sleeper matches
  neither rule: it **sleeps through** — stays asleep and never learns the time.
- **`bl_decide`** — an awake resident who heard a **service** peal DECIDES whether to
  answer, by a collapse over `{go, stay}` valued by `attend_sign · (piety ·
  call_strength − worldly_pull)`: the bell *calls*, the resident *chooses*.
- **`bl_attend`** — a resident whose collapse chose "go" joins the congregation
  (`attends` the peal). One who slept through never heard the call and cannot attend.

`known_hour` is per-resident, set **only** by hearing a bell — an agent who hears no
bell never knows the time (unknown = absence).

## Gates (pass/fail, pre-registered)

1. **G-bell-tells-the-time (HEADLINE):** after the bell rings, residents who heard it
   know the hour (`known_hour == peal.hour`); with no bell rung, no resident knows
   the time (`known_hour` unset — unknown = absence).
2. **G-rested-wake-exhausted-sleep-through (HEADLINE):** a sufficiently rested
   sleeper wakes at the bell and learns the hour; an exhausted sleeper stays asleep
   AND never learns the time (it slept through the bells).
3. **G-heard-across-the-town:** every resident who can perceive it (awake, or asleep
   and rested) hears the one peal — the bell reaches the whole town.
4. **G-attendance-is-chosen-not-scripted (HEADLINE):** awake hearers CHOOSE whether
   to attend (a collapse); the service is not forced on everyone — a resident who
   slept through does NOT attend, because it never perceived the call.
5. **G-no-forced-global-clock (falsifier / architecture):** there is no global
   `now`/`sunday` flag driving the agents; withhold the bell and nothing fires
   (nobody knows the time, nobody attends); ring again at a new hour and every hearer
   updates `known_hour` — time is what the bells say, nothing else.
6. **G-no-python-decision (source audit):** ring/hear/wake/decide/attend are the seed
   rules; the decision is an Argmax collapse in the seed; the adapter only pulls the
   bell-rope (arms one ring) and reads state.

## Scope / honesty
- The sexton pulling the rope is the one exogenous act; the town's time is *defined
  by* the bell, not by a hidden counter. Grounding *when* the sexton rings (sun
  position, a water-clock) is a further rung — the point here is that the agents
  learn time from the heard bell and choose their response, never from a forced flag.
- Distance-decay of the peal (far cottages hear a fainter bell) is deferred; here the
  village-wide bell is heard by all who can perceive it. Rest is a seeded scalar;
  a rest that depletes/recovers over bells is a natural next rung.
- The other faculties' forced clocks (jail day-advance, market day, council cadence)
  should migrate to bell-driven time; this rung establishes the mechanism and drives
  the church service by it, superseding the forced `sunday()`.
- The adapter re-settles the perceptual cascade (ring → hear/wake → decide → attend)
  by running the fixpoint a few times, because a within-pass added edge (e.g. `heard`)
  does not always re-wake a downstream rule's guard in one pass. This is mechanical
  I/O (repeatedly ticking the Rust engine to a stable fixpoint), not a decision — the
  known incremental-matcher cross-rule dirty-propagation gap, handled at the boundary.
- Isolated demonstrator (`self_load_only`); no Rust; `.so` untouched (`a8a9012c`).

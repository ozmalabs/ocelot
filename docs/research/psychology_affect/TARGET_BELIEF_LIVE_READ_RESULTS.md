# Target-scoped beliefs reach decide_speech (Phase D) — RESULTS

Registered design: `TARGET_BELIEF_LIVE_READ_PREREG.md`. **All 5
predictions confirmed.**

## 1. Live measurements

```
$ python3 -m pytest tests/test_affect_coupling.py tests/test_target_scoped_coupling.py \
    tests/test_disposition_transport.py tests/test_bigville_ocelot_adapter.py -q
30 passed   (unchanged count -- byte-identical)

# live-read verification: resident 'Dan', social_dispositions
# {'Landlord': {'regard': 0.3, 'admiration': 0.0, 'devaluation': 0.0}}

--- baseline decide_speech toward Landlord (t=0) ---
kind: greeting
live regard t=0: {'regard': 0.30000001192092896, 'admiration': 0.0,
                  'devaluation': 0.0}
                 # matches the static snapshot exactly (float rounding
                 # only) -- confirms prediction 2

--- record 4 real negative incidents (crystallize hate) ---
0 crystallized_this_call=False regard_state=0.0
1 crystallized_this_call=False regard_state=0.0
2 crystallized_this_call=True  regard_state=-1     # hate crystallizes
3 crystallized_this_call=False regard_state=-1

live regard after incidents: {'regard': -0.9000000357627869,
                              'admiration': 0.0, 'devaluation': 0.0}

--- decide_speech toward Landlord AFTER real incidents ---
kind: barb                       # WAS greeting -- genuinely changed
static social_dispositions UNCHANGED (frozen snapshot):
  {'regard': 0.3, 'admiration': 0.0, 'devaluation': 0.0}
                                  # proves the read is live, not a second
                                  # copy of the same static data

$ python3 -m pytest tests/test_hate_attribution.py tests/test_admiration_gratitude.py \
    tests/test_contempt.py tests/test_resident_trust.py tests/test_envy.py \
    tests/test_self_efficacy.py tests/test_shared_arousal_excitation_transfer.py \
    tests/test_bigville_disposition_apply.py -q
63 passed

$ python3 -m pytest <full Phase A+B+C+D touched-consumer list, 30 files> -q
251 passed, 4 pre-existing failures (stale .so hash pins -- same root
                                      cause as Phase A/B/C's established
                                      baseline; unrelated, real, uncommitted
                                      Rust work from outside this arc is
                                      concurrently present in the tree and
                                      re-triggering the .so rebuild, but the
                                      failure MODE and the 4 test node ids
                                      are identical to every prior phase)

$ (cd /home/matt/ozmadev/bigville && python3 -m pytest tests/ -q)
211 passed
```

## 2. Predictions

1. **Byte-identity, unmodified consumers** — `PASS`, exact (30/30, same
   count as Phase A/B/C).
2. **Static and live agree at t=0** — `PASS`, exact: `0.30000001192092896`
   (a float32/float64 round-trip artifact, not a real difference) vs the
   authored `0.3`.
3. **Genuine divergence after real incidents, static provably untouched**
   — `PASS`. `decide_speech` flips `greeting` → `barb` after hate
   crystallizes (3rd incident), while `personality["social_dispositions"]`
   — the ONLY thing the OLD code path ever read — stays byte-identical
   throughout. This is the direct, load-bearing proof the fix reads a
   genuinely live signal, not a re-derivation of the same static input.
4. **Broader hate/social regression green** — `PASS`, 63/63,
   `hate_attribution.py` itself untouched.
5. **bigville unaffected** — `PASS`, 211/211, zero bigville files touched
   this phase.

## 3. Honesty notes

**Does establish**: a resident's speech toward a specific person now
tracks what actually happened between them, not just what they were
authored to feel at boot. The same crystallization/passion-coupling
machinery `hate_attribution.py` already validates (stability gates,
arousal-scaled alpha, resentment-debt amplification) now has a real,
working path INTO a live decision (`decide_speech`) and a real, working
path FOR a resident's own disposition (`spite_gain`) to shape how strongly
one incident moves that belief. Both halves of Phase D's original framing
("`affect_bias`/`spite_gain` have no consumer") are closed — via the LIVE
belief and its own live-computed gain, which turned out to be the more
direct and more correct fix than trying to route through `affect_bias`
itself (that attr remains genuinely unread; the live `external_field` read
supersedes the need for it in this specific consumer).

**Does NOT establish**: that any real bigville gameplay event currently
calls `record_social_incident` — the connective tissue exists and is
proven correct end-to-end, matching exactly how Phase A's
`record_action_outcome`/`supergraph_contribution` graded signal existed in
the adapter before `held_board_games.py` was wired to call it. A further
rung wiring a real bigville event (a dispute, a broken promise, a
witnessed harm) to actually trigger it is named, not built here. Does not
touch `affect_bias` itself, which remains unread by anything (superseded,
not fixed, by this rung's use of `external_field` directly).

## 4. Files

- `docs/research/psychology_affect/TARGET_BELIEF_LIVE_READ_{PREREG,RESULTS}.md` (new)
- `worlds/bigville_ocelot_adapter.py` (edited: `record_social_incident`
  new method; `_live_target_regard` new method; `_speech_bond`'s `profile`
  lookup prefers live over static)

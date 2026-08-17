# cred_on: rename the collision, wire the real trait — RESULTS

Registered design: `CRED_ON_REWIRE_PREREG.md`. **All 5 predictions confirmed.**

## 1. Live measurements

```
$ grep -rln '"cred_on"' bigville/ --include="*.py" --include="*.json" | grep -v "__pycache__\|cast100\|townspeople"
bigville/game.py                       # personality-filter allowlist (real trait, legitimate)
bigville/worlds/bigville_town100_world.py   # _PARAM_SPEC (real trait, legitimate)
# (test_bigville_game_api.py also references the real trait -- excluded
# from this listing by the same grep pattern used above)
-- ZERO remaining arming-flag references anywhere.

$ git diff --stat seeds/bigville_drama_social.json bigville/seeds/bigville_drama_social.json
 bigville/seeds/bigville_drama_social.json | 2 +-
 seeds/bigville_drama_social.json          | 2 +-
 2 files changed, 2 insertions(+), 2 deletions(-)
(a second, separate edit -- the stale w_supergraph gate description --
adds 2 more lines each; both diffs surgical, not a reformat)

# claim_credible identity_field, cred_on scaling (claim_weight=1.4, w_supergraph=0.8)
cred_on=1.0 (mean)  -> identity_field = 0.5   (== pre-change formula exactly)
cred_on=1.5 (high)  -> identity_field = 0.75
cred_on=0.0 (floor) -> identity_field = 0.0

$ python3 -m pytest tests/test_can_native_reimplementation.py tests/test_resident_trust.py \
    tests/test_problem_shape_migrated.py tests/test_solver_dispatch_migrated.py \
    tests/test_solver_nl_adapter.py tests/test_solve_gap_awareness_migrated.py \
    tests/test_solver_can_adapter.py -q
11 passed  (test_can_native_reimplementation.py)
7 passed   (test_resident_trust.py, including the rewritten behavioral guard)
44 passed  (the 5 solver/problem-shape files)

$ python3 -m pytest <full Phase A+B touched-consumer list> -q
195 passed, 4 pre-existing failures (stale .so hash pins, unrelated,
                                      unchanged from Phase A's baseline)

$ (cd /home/matt/ozmadev/bigville && python3 -m pytest tests/ -q)
211 passed
```

## 2. Predictions

1. **Collision removed** — `PASS`. Zero remaining `cred_on`-as-arming-flag
   references anywhere in the bigville repo.
2. **Gain, byte-identical at the mean** — `PASS`, exact. `0.5` at
   `cred_on=1.0` matches the pre-change formula bit-for-bit; `0.75`/`0.0`
   at the high/floor extremes confirm proportional, sign-preserving
   scaling (clip `lo=0.0` guarantees this — `cred_on` can never flip the
   sign of the underlying claim/supergraph signal, only its magnitude).
3. **All 7 real dependent test files green** — `PASS`, 62/62 tests total
   across `test_can_native_reimplementation.py` + `test_resident_trust.py`
   + the 5 solver-adapter files.
4. **`trust_mayor` unaffected** — `PASS`, confirmed directly (not
   inferred): `(charm_weight - hostile_weight) * 0.5 + 0.5 *
   (prior_others_trust - 0.5)` computed identically before and after.
5. **Surgical diffs** — `PASS`. Both `bigville_drama_social.json` copies:
   4 lines changed total (the rename + the stale-comment fix), not a
   586-line reformat (a first attempt via `json.load`/`json.dump` DID
   reformat the whole file via `sort_keys=True` key-reordering — caught
   before committing, reverted, redone as a surgical text edit).

## 3. A real, pre-existing test-fragility finding

`tests/test_resident_trust.py::test_trust_mayor_seed_is_untouched` asserted
`git status --porcelain` was empty for `worlds/bigville_can_beliefs.py` +
`seeds/can_native_reimplementation.json` — a snapshot-in-time isolation
check from when `RESIDENT_TRUST_PREREG.md`'s own work landed, verifying
THAT arc didn't collaterally touch these files. As written, this assertion
can never again pass once ANY future, unrelated, legitimate change touches
either file — it was never a durable regression gate, just development-time
isolation evidence quoted past its useful life (the same class of defect
CLAUDE.md's own "optional-dep note" retraction names, one level down: a
point-in-time fact treated as a standing invariant). Fixed by replacing the
git-diff proxy with the actual behavioral invariant it was protecting —
`trust_mayor`'s own `identity_field` formula computes the same value,
checked directly. `test_can_native_reimplementation.py`'s KEYERROR (a
SEPARATE issue — that test's fixture didn't include `cred_on` in its
`params` dict) was fixed the other direction: `p["cred_on"]` →
`p.get("cred_on", 1.0)`, matching the "absent trait defaults to neutral"
pattern already established for every other optional param in this arc
(`quantize_weight`, `record_action_outcome`'s graded kwargs).

## 4. Honesty notes

**Does establish**: the `cred_on` name collision is gone; the real,
previously-documented-but-unwired `claim_credible` consumer now genuinely
reads the trait, as a gain, matching the original design review's own
recommended shape. Zero behavior change for every existing caller not
passing `cred_on` explicitly (the `.get(...,1.0)` default) or drawing it at
exactly the population mean.

**Does NOT establish**: that `cred_on`'s multiplicative role in
`claim_credible` is calibrated to anything beyond the seed's own
already-stated design intent. Does NOT touch `bd_villager_backs`'s own
`cred_mary`/`cred_john` arithmetic (a separate computation on `Villager`
nodes, unrelated to the CAN network's `claim_credible` concept). Does NOT
address Phase C (remaining hygiene: `resolution_bins` float-coercion,
`*_ref` duplication, unguarded channel tuples) or Phase D (Phase 4's own
self-consistency gap — target-scoped `affect_bias`/`spite_gain` have no
real production consumer either).

## 5. Files

- `docs/research/psychology_affect/CRED_ON_REWIRE_{PREREG,RESULTS}.md` (new)
- `worlds/bigville_can_beliefs.py` (edited: `claim_credible`'s
  `identity_field` reads `cred_on` as a gain)
- `tests/test_resident_trust.py` (edited: replaced the fragile git-status
  guard with a direct behavioral check)

**bigville:**
- `worlds/bigville_drama_world.py`, `worlds/bigville_sim_world.py` (edited:
  `cred_on` → `cred_decide_on` at the arming-flag construction site)
- `seeds/bigville_drama_social.json` + `bigville/seeds/bigville_drama_social.json`
  (edited: `bd_villager_backs`'s `where` clause key renamed; stale
  `w_supergraph` gate description corrected)

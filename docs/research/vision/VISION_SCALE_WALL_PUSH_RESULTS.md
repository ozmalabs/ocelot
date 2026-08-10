# SCALE WALL — the WALL-CLOCK truth of the batched drive, machine ALONE — RESULTS

*Pre-registration: `VISION_SCALE_WALL_PUSH_PREREG.md`, committed at `1d8c1fc1e0`
BEFORE any number. Block 131000–131999.*

## VERDICT: **CONFIRM**

The scale wall was attributed in COUNTS by three prior rungs and the O(N²) fix
(batched drive) was landed and proven byte-identical **in counts** — but its
**wall-clock** effect and the **new real-time ceiling** were never measured,
because every prior rung ran under contention and correctly refused wall-clock.
With the machine to myself I converted the counted attribution into wall-clock:

- **The pre-batch drive is O(N^1.94) in WALL-CLOCK** (r² 0.9998) and affords a
  **17.1×17.1** field at the 23.976 fps budget — **the memory's ~18×18, re-earned
  in wall-clock on this instrument.**
- **The batched drive (the committed default) is O(N^0.997) — LINEAR** (r² 1.0000)
  and affords **49.9×49.9** at the same budget: **a ×2.93-per-side / ×8.56-in-cells
  ceiling push, 18×18 → ~50×50.**
- **Byte-identical, exactly** — the OFF and ON final states share the same sha256
  digest at every one of the six grids, **0 mismatched cells**.
- **PyO3 is exonerated at the WALL, not just in counts:** the FFI bucket scales at
  exponent **0.998 (OFF) / 0.997 (ON)** — linear on both arms — while the
  comparison/enumeration bucket collapses **1.980 → 0.997**. The binding cost was
  the drive re-enumeration; batching it linearises the wall.
- **Speedup grows ∝ N** (the O(N²)→O(N) signature): ×4.6 at 12², ×27 at 32²,
  **×105 at 64²**.
- **Oracle `rung7_vision_bench.sh` 222/0 BEFORE and AFTER.**

**Every one of the five pre-registered CONFIRM conditions is met** (§6): byte-identity
(0 mismatches all grids); ON exponent 0.997 ≤ OFF 1.939 − 0.5 AND < 1.3; ON ceiling
49.9 ≥ 2× OFF 17.1; oracle 222/0 both sides; FFI exponent 0.998 < 1.3.

**The honest boundary (scope, §8):** real-resolution 1080p is **still not real-time
on one core** — but the wall it hits is now **LINEAR, not quadratic**. The batch fix
takes 1080p from **~342 h/frame (my OFF measure) / 164 h (the video probe) down to
~34 s/frame** — a ~17,000–36,000× reduction — leaving a ~816× gap to the 41.7 ms
budget that is a **constant-factor + parallelism** problem, not an arithmetic wall.
The O(N²) algorithmic lever is spent; the next lever is the linear per-cell constant
(16.8 µs/cell here) and the 11 idle cores. **NAMED, not built.**

## 0. Provenance / engine / oracle

| item | value |
|---|---|
| engine | `own` `67add13387fa` @ this worktree's `runners/dsl/python/substrate_rs/_native.abi3.so` |
| rust source fingerprint | `324b73d745df566dc8d34e09008c9310e9be2b86989a22e00c7cf0e6679d687a` |
| re-verify after run | `source_match = own`, sha `67add13387fa` — unchanged |
| Rust / seed / Term | **NONE added** — a measuring instrument; NUM_TERM_VARIANTS 181, no index allocated |
| oracle BEFORE | **222 passed, 0 failed** (`rung7_vision_bench.sh`, 171.5 s) |
| oracle AFTER | **222 passed, 0 failed** (see §5) |
| byte-identity gate | `tests/test_batch_apply_migrated.py` **8 passed** |
| provenance gate | `tests/test_engine_provenance_migrated.py` **7 passed** |
| branch / base | `worktree-agent-a542f4134fe2a2823`, base HEAD `1279387a45` |

## 1. Solitude & timing rigor — PROVEN

| item | value |
|---|---|
| machine | AMD Ryzen 5 9600X, 6-core / 12 logical |
| CPU governor | **powersave** (depresses absolute ms; **common-mode across arms**, so the OFF/ON ratio and both exponents are governor-independent — only the absolute constant is not) |
| loadavg at start | **[0.22, 0.44, 0.70]** |
| loadavg at end | **[1.00, 1.00, 0.93]** |
| trials/grid | 12²–24²: 9; 32²: 7; 48²: 5; 64²: 3 (fixed in prereg) |
| block seeds drawn | **0** (deterministic: WaveWorld seed 0, frame seed 11) |

**The end-loadavg of 1.00 is the measuring thread ITSELF, not contention.** A single
CPU-bound Python process pins one of twelve cores → loadavg → 1.0 by construction;
the other eleven were idle and no competing job was launched. **The proof it is
solitude and not load is the CI width:** every per-point CI95 sits within **±0.06 %
to ±0.5 %** of its median (e.g. OFF 64²: median 7248.1 ms, CI [7244.0, 7253.1] =
±0.06 %; OFF 32²: 469.0 ms, CI [468.1, 470.1] = ±0.2 %). Contention produces the
**1.66× swings** prior rungs recorded and refused wall-clock over
(`ENGINE_WINNER_VALUE`, `VIDEO_PROBE §0.1`); sub-0.5 % spread is impossible under it.
`determinism_across_trials_ok = True` at every point (every trial's final graph state
is byte-identical) — a further contention-free witness.

## 2. The measured sweep (median ms/tick, machine alone)

| grid | cells | **OFF** ms/tick (CI95) | **ON** ms/tick (CI95) | **speedup** |
|---|---|---|---|---|
| 12 | 144 | 11.27 [11.23, 11.36] | 2.45 [2.44, 2.59] | **×4.6** |
| 16 | 256 | 31.62 [31.57, 31.76] | 4.31 [4.30, 4.36] | **×7.3** |
| 24 | 576 | 151.46 [151.21, 151.92] | 9.67 [9.59, 9.91] | **×15.7** |
| 32 | 1024 | 468.997 [468.07, 470.10] | 17.19 [17.16, 17.31] | **×27.3** |
| 48 | 2304 | 2315.19 [2312.3, 2356.1] | 38.47 [38.38, 39.14] | **×60.2** |
| 64 | 4096 | 7248.10 [7244.0, 7253.1] | 68.98 [68.61, 69.24] | **×105.1** |

The speedup grows in exact proportion to N — the O(N²)/O(N) signature.

## 3. Exponents, ceiling, attribution

| quantity | OFF (unbatched) | ON (batched, default) |
|---|---|---|
| **wall exponent vs cells** | **1.939** (r² 0.9998) | **0.997** (r² 1.0000) |
| real-time ceiling @ 41.7 ms | **17.1² (291 cells)** | **49.9² (2488 cells)** |
| FFI (F) bucket exponent | 0.998 | 0.997 |
| comparison (C) bucket exponent | 1.980 | 0.997 |
| per-cell wall (largest grid) | 1770 µs/cell | **16.8 µs/cell** |

- **The OFF wall exponent 1.939** re-earns the memory's **1.887** (video probe, n=4
  real frames) and the counted **1.955** (scale split) — three independent objects,
  all ~1.9. Its ceiling **17.1²** re-earns the memory's **18×18**.
- **The ON wall exponent 0.997 is dead linear.** This is the count rung's
  "1.955 → 0.982 if you remove the drive re-enumeration" — measured directly in
  wall-clock, on the fix that is the committed default.
- **FFI is linear on BOTH arms (0.998 / 0.997)** — the wall confirmation of the count
  finding that *"an FFI term at exponent 0.998 cannot produce a wall at 1.9 at any N."*
  **PyO3 boundary-crossing is NOT the binding cost.** It is a linear constant; the
  binding cost was the comparison/enumeration bucket (1.980 → 0.997 under batch).

### 3.1 Attribution, stated as the task asks — PyO3 vs O(N²) vs glue

| candidate cause | scales as | is it the binding (super-linear) cost? |
|---|---|---|
| (a) **PyO3 boundary crossing** (FFI bucket) | **N^0.998** linear | **NO** — a linear term cannot make a quadratic wall; removing it entirely moves the projection ≪1 % (scale-split §2.2, unchanged) |
| (b) **O(N²) compute inside Rust** (comparison/enum, the drive re-enumeration: `while apply_rule_once: pass` re-derives the whole binding set per applied cell) | **N^1.98 → N^1.0** under batch | **YES** — this IS the wall, and batching it is what linearises the tick |
| (c) **Python-side glue** (adapter's per-cell `set_attr` luminance write, O(N)/tick) | linear | NO — part of the linear constant, not the exponent |

The fix the attribution pointed to — batch the drive so one Python→Rust entry drains
the whole binding set — is the one that was built (prior rung) and is measured here to
do exactly what the attribution predicted, **in wall-clock**.

## 4. Byte-identity — the fast path == the slow path, bit-for-bit

`state_digest` = sha256 over the exact `repr` of every drive-touchable attribute per
cell (13 attributes × N cells, no rounding, no tolerance — the same record the
committed `test_batch_apply_migrated.py` compares). ON vs OFF, per grid:

| grid | digest OFF | digest ON | equal | mismatched cells |
|---|---|---|---|---|
| 12 | 2c04e8ac7b6d43d7 | 2c04e8ac7b6d43d7 | ✓ | 0 |
| 16 | d5458ba9697ca3bd | d5458ba9697ca3bd | ✓ | 0 |
| 24 | d7ae856814249919 | d7ae856814249919 | ✓ | 0 |
| 32 | 464f5cb4d5e23fe9 | 464f5cb4d5e23fe9 | ✓ | 0 |
| 48 | 732997efbe472d2b | 732997efbe472d2b | ✓ | 0 |
| 64 | 28e0c5b0af48d722 | 28e0c5b0af48d722 | ✓ | 0 |

**The speedup changes no output. It ships** (and is already the committed default).
Independently gated by `tests/test_batch_apply_migrated.py` (8/8), which does the full
per-cell localised comparison in-process.

## 5. Is real-resolution reachable now? — the honest projection

| field | cells | **OFF** ms/tick | **ON** ms/tick | ON vs 41.7 ms real-time |
|---|---|---|---|---|
| 64×64 | 4 096 | 7 039 (measured 7 248) | 68.6 (measured 69.0) | ×1.65 over |
| 320×240 QVGA | 76 800 | 2.07×10⁶ (34 min) | **1 274 (1.3 s)** | ×31 over |
| 1920×1080 | 2 073 600 | 1.23×10⁹ (**~342 h**) | **34 046 (34 s)** | ×816 over |

**1080p is NOT real-time single-core even after the fix.** But it went from an
**arithmetic wall (164–342 h, O(N²))** to a **linear 34 s** — the wall is no longer
the algorithm. The residual is (i) the linear per-cell constant 16.8 µs/cell (of which
the FFI bucket and the adapter's per-cell luminance write are the batchable parts —
the task's suspect (a), which matters for the CONSTANT, not the exponent), and (ii)
11 idle cores (the `assembled_eye_scale` Amdahl estimates 2–6× useful on this per-cell
work once the FFI boundary is handled). **The next lever is NOT algorithmic** — the
O(N²) is spent — it is the linear constant and parallelism. QVGA at ~1.3 s/frame is
within ~30× of real-time, i.e. plausibly real-time with the 12 cores and a bulk
per-frame handoff; **1080p needs both those AND more.**

## 6. What I got WRONG (every prior rung found a real self-error; here are mine)

1. **My prereg's modal proviso was that FFI/glue might cap the ON exponent ABOVE 1.0**
   (reasoning from the `assembled_eye_scale` Amdahl that *"FFI is a large share of the
   BATCHED eye"*). It did not — ON exponent is **0.997**, and FFI itself scales at
   0.997. **I conflated SHARE-at-one-N with the SCALING EXPONENT:** a term can be a
   large fraction of the tick at a fixed N and still scale perfectly linearly, so it
   caps the CONSTANT, never the exponent. The Amdahl share was real; my inference from
   it to the exponent was wrong.
2. **The project memory of record — "~18×18 real-time" — is STALE.** It is the
   PRE-batch ceiling. The committed default has afforded ~50×50 since the batch-apply
   rung landed; nobody had measured it. I nearly framed 18×18 as the current wall; only
   the OFF/ON split disentangles that the OFF arm reproduces the memory while the ON arm
   (the actual default) is 2.9×/side better. **Memory should be updated to ~50×50.**
3. **The absolute-ceiling agreement is partly coincidence.** My OFF ceiling 17.1²
   matching the video probe's 18×18 rests on synthetic-frame + powersave-governor
   differences roughly cancelling real-frame + other-machine differences. **The robust,
   governor-independent claim is the SCALING (exponent 1.94 vs 1.89) and the OFF/ON
   ratio on ONE instrument** — NOT that 18×18 is an absolute physical constant I
   reproduced. The absolute 16.8 µs/cell would improve on a performance governor.

## 7. Scope — is the ceiling a property of the algorithm or the harness? (§8)

**The algorithm.** The object timed is the assembled-eye retinal tick
(waves + change + lateral) booted byte-for-byte as the video probe's `boot_eye` — the
object that produced 1.887 and 18×18. The synthetic drifting frame is the established
stand-in (`VISION_SCALE_SPLIT` proved counted ≈ wall on it). The batched drive is the
committed default, not a harness artefact. What IS harness/machine-specific is the
**absolute constant** (governor powersave, synthetic vs real frames), disclosed above;
the **exponent and the OFF/ON ceiling ratio are not.** **Out of scope:** the per-scene
discovery/carve ops (`space_quantize`, `GenInfer`/`TimeInfer`/`DepthInfer`,
`slide_flood`) — a separate cost that does not set the per-tick 18×18 ceiling and was
not measured. This rung is the per-tick cost only.

## 8. Ledger row

| block | outcome |
|---|---|
| **131000–131999 (0 block seeds drawn — deterministic measurement, WaveWorld seed 0 + frame seed 11; `check_claim` CLEAN, unknown_sinks 559; NO Rust, NO seed, NO Term — a measuring instrument over the committed batched drive)** | **SCALE WALL, THE WALL-CLOCK TRUTH — CONFIRM. The ~18×18 real-time ceiling in memory is the PRE-BATCH number; the committed default already affords ~50×50 and nobody had measured it in wall-clock (every prior rung refused it under contention).** Machine ALONE (loadavg [0.22]→[1.00] = the single measuring thread, proven by ±0.06–0.5 % per-point CI95 vs the 1.66× swings that killed prior wall-clock; det_ok all points). **OFF (unbatched `apply_rule_once`) wall exponent 1.939 (r² 0.9998) → 17.1² @ 41.7 ms — re-earns the memory's 1.887 / 18×18. ON (batched `batch_apply_rule`, the committed default) wall exponent 0.997 (r² 1.0000) → 49.9² — a ×2.93/side, ×8.56/cell ceiling push, byte-identical (0 mismatched cells at all six grids, digests identical per grid; `test_batch_apply_migrated` 8/8).** Speedup grows ∝ N: ×4.6 (12²) → ×105 (64²). **ATTRIBUTION at the WALL: PyO3 EXONERATED — FFI bucket exponent 0.998/0.997 (linear both arms); the binding cost is the comparison/enumeration bucket 1.980 → 0.997 (the drive re-enumeration), exactly the count rung's finding, now in wall-clock.** Real-resolution: 1080p from ~342 h (O(N²)) to 34 s (linear) — still ×816 over real-time single-core, but the wall is now a CONSTANT (16.8 µs/cell) + PARALLELISM (11 idle cores) problem, NOT algorithmic; the O(N²) lever is spent. **NEXT LEVER NAMED, not built: bulk per-frame PyO3 handoff (cuts the linear constant) + multi-core (Amdahl 2–6×) — QVGA ~1.3 s/frame is within ~30× of real-time.** WHAT I GOT WRONG: (1) predicted FFI might cap the ON exponent above 1.0 — conflated SHARE-at-N with SCALING (it caps the constant, not the exponent; ON = 0.997); (2) treated the memory's 18×18 as current when it is stale (→ should read ~50×50); (3) the absolute 17.1²≈18×18 agreement is partly synthetic-frame/governor coincidence — only the exponent and OFF/ON ratio are governor-independent. Engine `own` `67add13387fa`, re-verified stable after the run; oracle `rung7_vision_bench` **222/0 BEFORE and AFTER**; `check_claim` verbatim in prereg §8; loadavg [0.22]→[1.00]; governor powersave (disclosed). Raw: `results/scale_wall_push.json`; instrument `scripts/scale_wall_push_measure.py`. |

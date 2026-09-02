# Review of the 2026-09-03 hazard assessment

Reviewing: `hazard_assessment_2026-09-03.md` (Claude, in-session, same-day draft).
Method: every claim checked against the repository at
`/home/matt/ozmadev/ocelot` — Rust source (`runners/dsl/src/`), Python
(`substrate/`, `domains/`, `scripts/`), seeds (`seeds/*.json`), tests
(`tests/test_*.py`, Rust `#[test]`), research docs (`docs/research/**`), and
the paper set (`papers/formal/*.tex`). Reframed per instruction mid-review:
the operative threat model is not "the architecture" in the abstract but what
a moderately resourced actor (six-to-seven-figure USD, small team, months not
years — malicious or merely well-intentioned) could do starting from a clone
of this repository today. Findings below are sized against that actor
throughout, and Section 4 answers it directly.

---

## 1. Summary verdict

The draft's central relocation — hazard lives in the held repository, not in
the released theory papers — is correct and gets sharper on inspection: the
held set is 1.8 GB / 307,482 files, of which 306,494 are runtime-taught
microtheories and only 805 are curated seeds, of which only ~39 (~5%) touch
any embodied controller at all. The draft's two blanket empirical claims are
both wrong in the direction of understating the record: there **is** a
quadrotor (a simulated Crazyflie 2.x, with hidden-rotor-damage and
complete-rotor-loss recovery experiments) and there **is** a real car/wheeled
body (a full racing stack wrapping the open-source Speed Dreams simulator),
not "no record" and "prose only" as claimed. Conversely, the draft's "found
nothing" verdict on host boundaries is too strong: real, tested gates exist
(`information_commitment.py`'s `hard_veto`, `future_manifold.rs`'s Rust
feasibility classifier, `commitment_gate.py`, the rule-adoption regression
veto) — but every one of them protects the agent's *self-modification*
pipeline, not the *body-control* loops the draft is actually worried about,
and the one generic reversible/committing gate is wired into exactly one
non-safety-critical call site. The draft's no-LLM-calls claim is
**backwards**: the paper sentence it quotes was already flagged by the
paper's own internal review as unsupported and no longer exists in the
current text, while the *actual* runtime finding — undetected by the draft —
is that the daemon's default flags (`--attach-libraries` on, `--no-llm` off)
build a live `OpenAITeacher` whenever an API key is reachable, and the
agent's own graph rules, not a human, decide when to call it. Capability
floor is real but low and unreliable under the exact fault conditions that
would matter (F-16 crash rates 42-73% under simulated damage; humanoid
walking regression still fails; single-rotor-loss recovery validated for one
rotor, one seed). Nothing in the record shows any body running on physical
hardware. The corrected picture is less "an adaptable general controller
nobody can gate" and more "a large, general, well-audited cognition engine
with a small, low-reliability, ungated-at-the-control-layer body-control
slice, wrapped in an unattended daemon whose default configuration is more
network- and LLM-reachable than either the draft or the codebase's own most
recent internal audit believed."

---

## 2. Claim-by-claim table

| # | Claim (from the draft) | Support in the record | Verdict |
|---|---|---|---|
| 1 | "Hard safety vetoes and external approval remain non-tradeable host boundaries" — stated in CLAUDE.md | The sentence exists verbatim (CLAUDE.md, "Engine-wide decision and risk boundary" + repeated in `docs/research/engine_substrate/cognitive_architecture_core.md`). No single primitive implements it as a blanket claim. | **Partially supported.** True as a design statement; false as a description of one uniform enforced mechanism — it decomposes into several real but narrow ones (§3.1). |
| 2 | "The 09 agent searched the record... and found nothing" for the no-model-calls gate | The exact phrase quoted ("enforced by a switch and a gate") does not appear in the current `papers/formal/09_adaptability.tex`; it was flagged as unlocated by the paper's own reviewer (`09_REVIEW_r91_PROPOSAL.md`, §D.1) and removed. A real switch (`domains/no_llm.py`, `OZMA_NO_LLM`) and a real 2026-07-10 audit (`docs/research/engine_substrate/llm_touchpoint_audit.md`) do exist and are tested. | **Contradicted on the specific paper claim (already fixed); the underlying worry is understated, not absent** — see §3.2. |
| 3 | "On the one data point available, the answer was 'none'" (host boundaries generally) | Real, falsifiable counterexamples exist: `tests/test_information_commit_gate_migrated.py::test_objective_cannot_buy_shape_residual_violation`, `runners/dsl/src/future_manifold.rs`'s Rust `#[test]`s, `tests/test_commitment_gate.py`, `tests/test_composer_capability_migrated.py::test_datum_feedback_adoption_vetoed_on_regressions`. | **Contradicted as a categorical claim.** True in spirit for body-control safety specifically (§3.1). |
| 4 | 09's copy result: a held set is "copied at negligible cost... no residue" | `WorldAdapter.save()` writes plain, uncompressed, unencrypted JSON (`substrate/world_adapter.py:6249`); no signing/hashing/licence check anywhere in the persistence path; verified against a real 132 MB checkpoint file on disk. | **Supported**, strongly (§3.3). |
| 5 | 01's self-governance proposition: admissibility gives no veto over world-caused change; an adversary controlling the world can teach the controller | `runners/dsl/src/shape_decode.rs`'s minting path (`sd_mint_quantum`) has no rate limit, size guard, or provenance check on the `Observation` node it decodes; no adversarial/noise-robustness test exists anywhere in the sd-loop or body-control test suites. | **Supported as a structural claim**, but the concretely demonstrated risk on the current record is availability (an untyped-attribute panic can silently kill the cognition thread), not demonstrated poisoning (§3.7). |
| 6 | "No quadrotor record; car appears in prose only" | `domains/gym_pybullet_drone_world.py` (625 LOC) flies a simulated Crazyflie 2.x in `gym-pybullet-drones`, with hidden-damage and rotor-loss-recovery experiments (`docs/research/flight_control/aerial_adaptation_flight.md`). `domains/full_racing_world.py`, `speed_dreams_racing_world.py` (wraps the real open-source Speed Dreams sim), `precision_driving_world.py`, `gymkhana_driving_world.py`, `pybullet_robot_world.py` (includes a "Racecar" body) are real, working code with measured results. | **Contradicted.** Both bodies exist and are documented in more depth than most others (§3.4). |
| 7 | 06 r27: a decoder seed is byte-identical by hash across seven consuming frames | Confirmed in `papers/formal/06_assessing_an_account_of_this_kind.tex:462-472`. | **Supported**, but the same paragraph the draft draws this from also states the paired fact the draft omits: "no cross-frame transfer has a measured benefit attached to it at all" — true count of benefited transfers is zero, against 17 documented failed-transfer attempts (§3.6). |
| 8 | The "805 seeds / 3,843 rules" figures are from `09a.counts.tex` | Confirmed and independently reproduced by direct recount of `seeds/*.json` (805 files, 3,843 `rules` entries summed across 540 of them). | **Supported.** |
| 9 | A1's fifteen conformance tests are the specification of determinism | `papers/formal/A1_constructive_graphic_equalisation_implementation_referenced.tex` contains zero occurrences of "conformance" or "fifteen." No test suite in the repo is describable as "A1's conformance tests." | **Not supported — likely a misattribution.** No corresponding artefact was found under this description anywhere in the repo. |
| 10 | The hazard "does not need to be very capable to be one" | Measured capability on the held bodies is low and fault-intolerant: F-16 crash rates 21-73% under damage scenarios depending on controller version (`docs/research/flight_control/jsbsim_f16_paper_replication.md`, `regime_pareto_frontier_results.md`); humanoid walking regression still fails one of its own gates; single complete-rotor-loss recovery on the drone is validated for one rotor, one seed, one goal. | **Directionally right about proliferation risk in principle, but the record does not show a low-capability system that reliably works** — it shows a low-capability system that frequently does not (§3.5). |

---

## 3. Findings by item

### 3.1 Host boundaries and gates

CLAUDE.md's "Engine-wide decision and risk boundary" paragraph is a single
sentence covering two different claims — a hard safety veto, and external
approval — and neither is implemented as one primitive. On investigation
each decomposes into several real, separately-tested mechanisms, none of
which is wired into an actual body-control loop by default:

| Claimed boundary | Implementing code | Test that would fail if removed | Wired into a body's control loop? |
|---|---|---|---|
| Hard veto: unbounded incentive cannot buy past a containment violation | `seeds/information_commitment.json`'s `hard_veto` filter + `domains/information_commitment.py::assess` (`domains/information_commitment.py:75-116`) | `tests/test_information_commit_gate_migrated.py::test_objective_cannot_buy_shape_residual_violation`, `::test_topology_only_escape_is_not_hidden_by_zero_width` | Not found reachable from F-16/helicopter/humanoid/drone/car adapters |
| Native feasibility/escape classifier (same idea, Rust) | `runners/dsl/src/future_manifold.rs`, `motor_compose.rs` policy flag `future_manifold_enabled` | Rust `#[test] an_escaping_candidate_is_infeasible_not_unestablished`, `minimum_sufficient_intervention_wins_and_goals_only_break_ties`; `tests/test_future_manifold_projection_native.py` | **Opt-in, defaults `False`** everywhere the flag is declared; exercised in paired research experiments, not as a default-on runtime safeguard |
| General reversible/committing action gate + external-approval requirement | `domains/commitment_gate.py::commit_gate`, `seeds/reversibility_frame.json` (unknown action kinds fail closed to "committing") | `tests/test_commitment_gate.py` (4 tests), `tests/test_imagination.py::test_commit_imagination_gated_and_mints_commitment` | Wired into **exactly one** call site, `domains/imagination.py::commit_imagination`. The frame data classifies `http_get`, `browser_apply`, `arc_apply`, `voice_emit`, `runtime_install` as "committing," but `browse_dispatch.py`, `fetch_dispatch.py`, `voice_world.py`, `proposal_install.py` do not import `commitment_gate` at all |
| Rung-4 self-extension "approval" (install a self-authored Rust primitive) | `domains/proposal_install.py::install_proposal` (5 content guardrails), `domains/auto_approve.py` | `tests/test_auto_approve.py` (404 lines), `tests/test_adoption_safety_migrated.py` | The content guardrails are real and re-run on every call; **the "approval" performs no authentication** — `_approve_proposal` (`scripts/jabberwock_daemon.py:3948`) accepts any POST to `/api/proposals/<id>/approve` with `approver` defaulting to the literal string `"web"`; grep for `Authorization`/`API_KEY`/`password` in the daemon returns nothing |
| Self-modification regression veto | `seeds/adoption_safety.json`'s `adopt_denied_on_regression` rule | `tests/test_composer_capability_migrated.py::test_datum_feedback_adoption_vetoed_on_regressions` | Internal to the self-improvement pipeline, not body-control |
| Literal "kill switch" (emergency stop on an action/body) | — | — | **Genuine null.** `grep -rniE "kill_switch|killswitch|emergency_stop|e_stop|estop|panic_stop"` across `runners/dsl/src/`, `substrate/`, `domains/`, `scripts/`, `docs/research/engine_substrate/`, CLAUDE.md returns zero matches that are an actual stop mechanism. The only literal "kill switch" in the codebase is `OZMA_NO_LLM` (§3.2), which stops hosted-LLM calls, not actions in a body |

**Verdict:** the draft's "found nothing" is too strong — real, falsifiable
governance exists — but its underlying worry survives precisely aimed:
every tested boundary above governs the agent's own code/rules, not what a
body does in the world. Nothing found in this repository stops a
graph-authored control decision from being sent to an actuator; the future
manifold machinery that CLAUDE.md's decision-and-risk-boundary language
describes for exactly that purpose is opt-in and defaults off in the two
bodies where it is declared.

### 3.2 The no-model-calls claim

The draft's own factual basis for this claim needs correcting before its
implication does. The phrase it quotes — "enforced by a switch and a gate" —
does not exist in the current `papers/formal/09_adaptability.tex`; the
paper's own internal review (`papers/formal/09_REVIEW_r91_PROPOSAL.md`,
§D.1) already flagged it: *"The 'switch and a gate' enforcement is not in 06
and was not found in the record under that description — name what it
refers to or drop it,"* and the current text no longer makes the claim in
that form. `rem:oracle-cost` (`09_adaptability.tex:344-363`) is in any case
about a **development-time** oracle used to write the substrate's structure
once, not about the running daemon's runtime behaviour — a different axis
entirely from "does the deployed system call an LLM."

Separately, a real mechanism does exist: `domains/no_llm.py`'s `OZMA_NO_LLM`
env-var switch, comprehensively audited in
`docs/research/engine_substrate/llm_touchpoint_audit.md` (2026-07-10, 8
guarded touchpoints enumerated) and tested
(`tests/test_no_llm_switch_migrated.py`, 10 tests; the graduation gate
`scripts/no_assistance_gate.py` / `tests/test_no_assistance_gate_migrated.py`
proves a full self-improvement cycle closes under it). But:

- **The switch defaults off.** `tests/test_no_llm_switch_migrated.py` itself
  asserts `assert not no_llm(), "unset must read as OFF"`.
- **The July 2026 audit's verdict is stale.** It states: *"the live
  daemon's default configuration makes zero hosted-LLM calls... the daemon
  never enables [the llm partner]."* Verified directly against the current
  `scripts/jabberwock_daemon.py` (4,321 lines, grown substantially since the
  audit): `--attach-libraries` defaults `True`
  (`scripts/jabberwock_daemon.py:4136`), and at line 4221,
  `_attach_default_libraries(adapter, enable_llm=not args.no_llm)` — since
  `--no-llm` defaults `False`, **`enable_llm=True` on a completely flagless
  boot**. `domains/libraries.py:_llm()` then constructs `OpenAITeacher()`
  and attaches it if `is_available()` (an API key is reachable via env var
  or a `.env` file at the repository root — `domains/openai_teacher.py`'s
  `load_openai_api_key` checks both; this checkout's own `.env` contains
  what appears to be a live key).
- **The call, once attached, is agent-triggered, not human-triggered.** The
  agent's own graph rules (`seeds/instruction_understanding.json:342,362`,
  `seeds/request_interpretation_shadow.json:33`) mint
  `TeacherRequest{teacher_tier:"llm", origin:"agent"}` on an instruction
  comprehension gap; the daemon's tick dispatch table
  (`scripts/jabberwock_daemon.py:3248`, `"teacher": lambda:
  _teacher_tick(adapter)`) drives this to `domains/teacher_dispatch.py`'s
  `scan_and_teach` → a real HTTP POST to
  `https://api.openai.com/v1/responses` (`domains/openai_teacher.py:381`).
  No test anywhere asserts that a flagless default boot makes zero LLM
  calls; the only assertion in the suite runs the other way.

**Verdict:** not "found nothing" and not "no model calls." The accurate
statement is: *the running system makes a hosted LLM call whenever its own
comprehension-gap rules decide to, unless an operator explicitly passes
`--no-llm`, and whether credentials happen to be present is what actually
determines the outcome on a given deployment* — a materially different (and
more concerning, because default-on and credential-contingent rather than
policy-gated) finding than either the draft or the July 2026 audit
document.

### 3.3 Copyability and containment

Strongly supported. `WorldAdapter.save()`
(`substrate/world_adapter.py:6249-6273`) writes `{"agent":..., "graph":
self.s.graph_to_dict(), "grammar":..., "rules": self.inner.export_rules(),
...}` as plain `json.dump` — verified against a real 132 MB example
(`results/curriculum_study/checkpoint.json`, `file` reports `ASCII text`).
Checkpoints land under `~/.jabberwock/checkpoints` by default
(`scripts/jabberwock_daemon.py`), rotated by an atomic `os.replace()`.

`seeds/` is 1.8 GB across 307,482 JSON files — 805 curated top-level
manifests (the "805 seeds" figure) and 306,494 files under `seeds/acquired/`
(runtime-taught, per-topic microtheories: 99.7% of the file count). No
signing, encryption, licence check, HMAC, or even a content hash exists
anywhere in the persistence path (`grep -rniE
"encrypt|licen[cs]e|hmac|checksum|sha256|md5"` across `substrate/`,
`scripts/jabberwock_daemon.py`, `runners/dsl/src/*.rs` returns zero hits).
Node-identity elsewhere in the codebase uses a plain string join, not even a
hash, for dedup (documented as a live bug in CLAUDE.md's "SHAPE AUDIT"
section). The compiled engine is a 9.5 MB PyO3 `.so`
(`runners/dsl/python/substrate_rs/_native.abi3.so`) with no licence or
phone-home check in its load path. No `LICENSE` file gates anything.

**Conclusion:** as far as the code shows, nothing stops `cp -r seeds/` plus
that one `.so` file from constituting a working copy of the held competence.
The one non-cryptographic caveat: a few library teachers reference
separately-located on-disk corpora (`domains/libraries.py`'s
`WIKI_DATA_DIR`, a local Wikipedia dump) that would need copying too for
full parity, but their absence degrades gracefully rather than blocking
boot. The draft's "copyable by construction, no residue" is not
overstatement — it is, if anything, understated: there is not even a
passive integrity check, let alone a containment one.

### 3.4 Bodies

Confirmed graph-native-controller bodies, with adapter LOC and hardware
status:

| Body | Seed(s) | Adapter LOC | Hardware |
|---|---|---|---|
| F-16 | `f16_flight_path_control.json` | 1,441 | JSBSim simulation only |
| X-15 | (shares F-16 family) | 457 | JSBSim simulation only |
| Generic fixed-wing jet | (custom plant) | 567 | Custom deterministic simulation |
| Helicopter (autorotation) | `helicopter_autorotation.json` | 1,098 | Custom 2D energy-accounting plant + PyBullet 6DOF extension, simulation only |
| Humanoid | 5× `humanoid_*.json` | 3,650 | PyBullet/MuJoCo simulation only — and even the two "physical" trials cited in `EFFECTOR_AUTHORITY_COLLAPSE_RESULTS.md` were "driven by a hand-written controller, not by the agent's own motor programs" |
| Walker | none (no dedicated seed) | 157 | Not physically simulated at all (1D toy); still on the **legacy Python `substrate` module**, not `substrate_rs` |
| Doom | 7× `doom_*.json` | 2,071 | Game-engine simulation |
| Chess | **none** (no dedicated seed) | 990 | N/A — `domains/chess.py` runs a hand-written classical negamax/alpha-beta search wrapping `python-chess` on the **legacy Python `substrate`**, not `substrate_rs`; not a demonstrated graph-native controller despite appearing in CLAUDE.md's seed list |
| Racing car / wheeled robot | `racing_cognition.json` | 2,403 | Custom plant + the real open-source **Speed Dreams 2.4.2** simulator + PyBullet ("Racecar," R2-D2, Husky bodies); simulation only |
| Quadrotor / drone | `aerial_adaptation.json`, `hidden_goal_aerial_mission.json` | 625 | A simulated **Crazyflie 2.x** in `gym-pybullet-drones` (pinned commit), simulation only |

**Confirmed: no body in this record has ever run on physical hardware.**
Every entry above is simulation, and the humanoid's closest approach to
physical trials explicitly used a non-agent hand-written controller. Both
bodies the draft said were absent or prose-only are real, working,
documented implementations — the quadrotor's is arguably the most carefully
instrumented body-damage study in the whole flight-control corpus (motor
babbling, hidden rotor-RPM loss, broken-propeller thrust/torque loss, and a
direct three-rotor recovery controller with measured 8.33 ms detection
latency and a 155-212 µs Rust control-cycle floor).

F-16 + helicopter + humanoid + walker total **6,346 lines of body-specific
Python** that CLAUDE.md's own architecture rule places outside the agent's
self-repair boundary ("the agent can self-repair exactly where its
cognition is graph-native... It cannot edit the Python front end"). Chess
and walker are not graph-native at all by the project's own definition — two
of the ten "bodies" are plain Python programs the seed-modularity section's
own framing does not actually cover.

### 3.5 Capability floor

The record does not show a low-capability system that reliably works; it
shows one whose reliability collapses under exactly the fault conditions a
hazard assessment should care about:

- **F-16** (`docs/research/flight_control/jsbsim_f16_paper_replication.md`,
  `regime_pareto_frontier_results.md`): the paper-replication matrix (n=100
  ×100s @10Hz, 8 scenarios) measured 68/800 crashes overall against a
  claimed 0/800, with **damaged wing at 0.47 crash rate [Wilson 95% CI
  .375–.567]** and saturated elevator at 0.21. A later architecture
  ("Pareto v2") *regressed* three fault scenarios to 0.65–0.73 crash
  (CI-separated worse) before a narrower-corner revision returned parity.
  `GENERIC_ADAPTIVE_CONTROL_F16_PROVING_GROUND_STATUS.md` states plainly
  that "the graph adaptive-loop wiring is not part of [CI's] gate" and warns
  a retained full sweep "must not be read as evidence that the graph-resident
  adaptive loop works."
- **Helicopter autorotation**: explicit n≤12 "deterministic mechanism
  checks, not statistical performance claims"; 4/6 landings survive with
  preflight calibration removed (2 failures before online recovery); the
  doc itself disclaims equivalence to "a flight-qualified autopilot."
- **Humanoid**: the walking regression test still fails one of its own
  gates after a fix (`BALANCE_TERM_RESULTS.md`: "the test still fails... an
  improvement on 4 of 13 assertions, not a repair"; `upright` stays
  `False`). `HUMANOID_DECOMPOSITION_CONTINUATION.md` documents the
  composer's cost function bypassing the admissibility grammar entirely
  ("no [Γ] productions at all," writes via `graph.insert_edge` directly,
  never through `check_edge`) — the same shape of defect CLAUDE.md's own
  "SHAPES, NOT NUMBERS" section calls out for the F-16. Notably, this is
  **not** a positive cross-body transfer (nothing was copied or improved) —
  it is the same unfixed architectural gap discovered independently twice.
  The same document records an instrumentation bug that silently returned a
  plausible-looking `samples: 0` result **three separate times**, each
  costing a full experimental run before being caught (§3.8/§4.3 discuss
  the accident-path implication).
- **Drone**: the fast control loop is genuinely fast (155.6 µs median /
  192.7 µs p99 per Rust cycle, ≈6.4 kHz, on an AMD Ryzen 5 9600X), but the
  stock stabilized-velocity interface **cannot recover from complete
  single-rotor loss at all** — four different oracle-replay controls
  (hover/climb/positive-yaw/negative-yaw) all still hit the ground within
  0.75 s. The one recovery that works requires bypassing the standard
  interface for raw-RPM authority, and is validated for exactly one
  diagnosed rotor, one goal, one seed — explicitly "not yet evidence for
  arbitrary motor locations."
- **Program synthesis (MBPP)**: 54/257 tasks solved (~21%), and — a clean,
  reported null — running with the full 805-seed held set versus stripped
  of it produced **byte-identical result sets**, i.e. on this measured task
  the held set contributed nothing at all to this particular capability.

**Verdict:** "does not need to be very capable to be a hazard" is
directionally sound as a general proliferation-risk principle, but as a
description of *this* held set it should be read as "a demonstrated,
low-reliability, single-point-of-failure-prone capability" rather than "a
demonstrated capability that merely happens to be modest." A downstream
actor inheriting this capability inherits its failure modes along with it —
which is itself the more actionable finding for §4.

### 3.6 The "priors bound adaptability" mitigation

805 curated seed manifests, 3,843 rule entries (independently recounted, not
just quoted from the generated `09a.counts.tex` macro — file-by-file summing
matches exactly). Of the 805, ~39 (≈4.8%) are tied to a single simulated
embodiment (flight/car/humanoid/doom/ARC/bigville/etc.); the remainder (~95%)
is general cognition (conversation, gap-awareness, shape-decode, composer,
self-improvement machinery — ~119 files by rough classification) or
general/encyclopedic domain knowledge (~59 files) or perception/language
capability not tied to one body. Chess and walker have **no dedicated seed
at all** — their logic is plain Python, outside the seed system entirely.

The draft's own cited evidence for transfer — 06's byte-identical decoder
seed across seven consuming frames — is real
(`papers/formal/06_assessing_an_account_of_this_kind.tex:462-472`). But the
same paragraph the draft draws this from states, two sentences later, the
fact the draft omits: *"a receiving frame whose measured behaviour improved
— has a true count of zero: every measured before-and-after improvement in
the history is within a frame, and no cross-frame transfer has a measured
benefit attached to it at all"* (line 468-473) — against **seventeen
documented failed-transfer attempts, one measurably harmful, one explicitly
retracted**. A pre-registered cross-body test that would have been positive
evidence explicitly failed its own gate:
`docs/research/humanoid/embodied_damage_navigation_v1_results.md` — pooled
median paired advantage across three morphologies (R2-D2, Husky, Racecar)
was 0.031, below the pre-registered 0.05 gate — "supports neither a general
cross-body damage resilience claim nor a claim that plasticity was
harmless." And CLAUDE.md's own "F-16/humanoid collapse," offered there as
evidence of a capability "independently re-derived" across bodies, is on
inspection the opposite of a transfer: `HUMANOID_DECOMPOSITION_CONTINUATION.md`
records it as the *same unfixed defect* (a scalar-knob learning-rate
collapse and a Γ-less deciding path) rediscovered independently in two
separate, unshared Python implementations — nothing was copied, nothing
improved.

**Verdict:** "the engine without the seeds is not a hazard; the seeds are"
is a reasonable relocation but should be sharpened twice. First, *portable
structure* (the byte-identical decoder) and *portable competence between
bodies* are different claims, and the record supports only the first — the
measured cross-body transfer benefit is a documented zero. Second, within
the 1.8 GB held set, body-control competence is a small (~5%), low-reliability,
non-transferring slice sitting inside a much larger general-cognition corpus
whose relationship to embodied-control hazard is not established either way
on the current record.

### 3.7 Adversarial world input

`runners/dsl/src/shape_decode.rs`'s minting path (`sd_mint_quantum`, driven
by `seeds/shape_decode_loop.json`'s rule of the same name) has no volume
cap, no size/complexity bound on the residual, and no provenance or
trust-tier check on the `Observation` node it decodes — any node typed
`Observation` with `status:"pending"` and a `signature` attribute is
decoded regardless of what wrote it. Dedup is by exact content-key match
only, so an adversary varying inputs slightly can mint one `CapabilityAxis`
per variant with no ceiling. No test anywhere feeds the sd loop, or any
body's control loop, deliberately corrupted or adversarial input and checks
for safe/contained behaviour (533 grep hits for "adversarial" are
overwhelmingly narrative-analysis vocabulary or ML-domain concept labels,
not input-security tests).

The concretely demonstrated risk on the current record, however, is
different in kind from "an adversary teaches the controller something
dangerous": `shape_decode.rs:195-243`'s `string_attr_or_panic` is a
*deliberate* design choice to `panic!()` on a present-but-wrong-typed
attribute (motivated by a prior silent-drop bug that produced a false
negative). `pyo3_runtime.PanicException` does not inherit from `Exception`
— noted explicitly in three places in the codebase itself — so the
daemon's tick-loop guard (`except Exception as e: # noqa: BLE001 -- never
let one bad tick kill the loop`, `scripts/jabberwock_daemon.py:3371`) does
**not** catch it, and the loop has no liveness watchdog
(`monitor_loop` only publishes status/session-diff events). A single
malformed observation — adversarial or merely buggy — can silently kill the
agent's cognition thread while the HTTP server and socket keep reporting
"up."

**Verdict:** the draft's structural claim (no defence exists against a
world-controlled adversary) is supported. The specific, testable,
already-reproduced risk on this record is closer to an availability/silent-hang
hazard than to the "poisoned into dangerous behaviour" framing the draft
implies — worth separating, because the fix (catch panics, add a
watchdog) is cheap and the fix for "an adversary teaches it something
dangerous" is not.

### 3.8 What the draft misses

- **Self-modification.** Real human gate by default:
  `promote_self_concern` (`scripts/jabberwock_daemon.py:2161`) is reachable
  only via an explicit admin call or a chat turn from `from=='interlocutor'`
  (`seeds/conversation_steering.json`); `install_proposal`'s 5 guardrails
  re-run on every call; `adopt_denied_on_regression` is tested. But one
  human toggle, `domains/auto_approve.py`'s `AutoApprovePolicy` (default
  `enabled=False`), switches to **rate-limited (2/hour default),
  additive-only, allowlist-scoped autonomous compile-and-install of
  self-proposed Rust primitives with no further per-item human click** —
  the module's own docstring calls this "a safety-sensitive automation (it
  can trigger a real compiler run + hot-swap of the agent's own runtime
  with no human in the loop)." Grammar (Γ) production adoption keeps its
  own, stricter, never-auto-invoked gate.
- **Goal-setting.** Both externally-triggered (`route_question_to_topic`,
  conversation-driven) and fully self-directed goal-minting exist and the
  latter is live by default: `seeds/self_fuel_drive.json`'s
  `mint_curiosity_goal` "fires natively in master_tick," minting an
  understand-goal from every unresolved perceived Feature with no external
  stimulus required.
- **Tool use.** `domains/agent_tools.py`'s `ToolBox` provides unrestricted
  file reads and **arbitrary shell command execution**
  (`subprocess.run(cmd_str, shell=True, ...)`, only a `cwd` pin and a 30 s
  timeout — no allow/deny list, no sandboxing). It is, however, **dormant**:
  `install_tools` has no caller anywhere outside its own test file, the
  same "dormant wiring" pattern the July 2026 LLM audit found for the
  `llm_partner` spec. Separately, genuine outbound-network capability
  (`domains/fetch_dispatch.py`, `domains/web_world.py` — real
  `urllib.request` GETs to Wikipedia/arXiv) **is** live and dispatched
  autonomously from the tick loop as part of the documented self-heal
  pipeline, with no human approval step.
- **The daemon.** `scripts/jabberwock_daemon.py`'s main tick loop runs
  fully unattended at up to 20 Hz with no approval step in the loop body
  itself; human gates exist only at named seams (concern promotion,
  extension-install approval, the `auto_approve` toggle) — not at "make an
  external network call," which by default (per §3.2) includes a hosted
  LLM call whenever credentials are reachable.

---

## 4. What a $1–10M actor could do with it

Sized against a small team (few-to-dozen engineers), months not years,
starting from `git clone` of this repository plus the released papers. No
extrapolation beyond the record; silence is marked as silence.

**1. Out of the box, unattended.** `python scripts/jabberwock_daemon.py`
with no flags: boots the full 805-seed set (~20 s), ticks at 20 Hz, exposes
an HTTP API on `127.0.0.1:8787` (loopback by default; no auth code exists
anywhere in the daemon — see §3.1's rung-4 finding, which generalises: the
whole HTTP surface has no authentication, so binding it to a non-loopback
interface is the operative risk, not a design gap in the API itself) and a
Unix socket. Autonomously, without a human click: knowledge self-healing via
live Wikipedia/arXiv fetches, self-concern filing and surfacing, experiment
dispatch, and — per §3.2 — hosted OpenAI calls whenever the agent's own
comprehension-gap rules fire and an API key is reachable. Not autonomous
without an explicit human step: self-proposed rule/Rust-extension
installation (unless `auto_approve` has been toggled on) and Γ-production
adoption (never auto-invoked).

*New body, new hardware.* The record's only informative datum for cost is
adapter size and independence across the existing bodies (§3.4): each body
required 600–3,650 lines of bespoke Python (F-16 1,441; helicopter 1,098;
humanoid 3,650; drone 625; car/racing 2,403) plus a dedicated seed, built
independently, with **no evidence any lesson or fix transferred between
them** (§3.6) — the F-16/humanoid "collapse" CLAUDE.md cites is a shared
*unfixed defect*, not a shared *fix*. Sizing a new real body (a physical
quadrotor or car) from this record: the closest existing analogue
(`aerial_adaptation_flight.md`'s Crazyflie work) is a from-scratch
simulation build with its own adapter, its own seed, its own babbling and
damage-recovery experiments — a comparable real-hardware port is not in the
record at any scale (no body here has run on physical hardware at all,
§3.4), so the marginal cost of *simulation-to-hardware* is genuinely silent
in this repository; a team would be paying that cost for the first time,
with none of the existing bodies' engineering as a hardware-integration
precedent — only as a control-architecture and adapter-shape precedent.

**2. The dual-use capabilities, and their current reliability.**

| Capability | Reachability | Measured reliability |
|---|---|---|
| Adaptive control on cheap simulated platforms (drone, car) | Live, documented, reproducible from scripts in the repo | Damage-adaptation demos work at n=1–2 per condition; the drone's stock control interface cannot survive complete rotor loss at all (§3.5) |
| Self-improvement pipeline (propose → sandbox-validate → human-approve → install) | Live by default up to the approval step; one toggle removes the per-item human click, rate-limited to 2/hour, additive-only | The graduation gate (`no_assistance_gate.py`) demonstrates two full improvement cycles with zero LLM assistance; the regression veto is tested (§3.1, §3.8) |
| Tool use (arbitrary shell, unrestricted file read) | Code exists, fully capable, but **dormant** — zero callers outside its own test | N/A — never exercised outside a test in this record |
| Autonomous web reading (Wikipedia/arXiv self-heal) | Live by default, no approval gate | Documented, works for the knowledge-grounding use case it was built for |
| Program synthesis (MBPP) | Live, graph-native enumerator + seed rules | 54/257 (~21%), and the 805-seed held set makes no measured difference to this score (§3.5) |
| Hosted LLM consultation | Live by default whenever credentials are reachable, agent-triggered (§3.2) | N/A to reliability; relevant to control, not capability |

A team adding real value on top of this record would need to supply, at
minimum, everything the record is silent on: hardware integration for any
physical body, an authentication layer for the daemon's HTTP surface, and a
fault-recovery reliability program for whichever body they deploy — none of
which is a small addition given the measured floor in §3.5.

**3. The accident path for a well-intentioned team.** The record contains
concrete, already-realised examples of exactly this failure shape, not
hypotheticals:

- A safety-relevant document going stale silently: the 2026-07-10
  `llm_touchpoint_audit.md`'s "zero hosted-LLM calls by default" verdict is
  contradicted by the current daemon (§3.2) — the code changed
  (`OpenAITeacher` was added, the default `enable_llm` flag flipped) and
  the audit was never re-run. A team trusting that document, as the draft
  assessment did, would deploy believing a property that no longer holds.
- The fourth-cost pattern (Graphic Equalisation's `def:well-formed`,
  `papers/formal/01_law_of_graphic_equalisation_theory_referenced.tex:1330`
  — "a write that demonstrably did nothing" is a discrete, memorable, but
  *silent-until-discovered* event): realised three separate times in
  `HUMANOID_DECOMPOSITION_CONTINUATION.md`'s instrumentation history, each
  producing a plausible-looking `samples: 0` that cost a full experimental
  run before being caught. A team relying on this system's own telemetry to
  decide whether an adaptation "worked" would need to independently verify
  that the instrument fired at all, not just that it returned a clean
  number — the record shows this is not automatic.
- Missing tests on exactly the boundaries that matter operationally: no
  authentication on the daemon's approval/install HTTP routes (§3.1); no
  test asserting a flagless daemon boot makes zero LLM calls (§3.2); no
  adversarial-input test on the sd loop (§3.7); the future-manifold gate
  defaulting off in both bodies that declare it (§3.1).
- "Nearly half the primitives introduced have no consumer in any seed"
  (`papers/formal/06_assessing_an_account_of_this_kind.tex:659-661`, of the
  self-extension primitive set) — a team auditing "what capabilities does
  this system have" by reading its own primitive/Term surface would
  overcount, since a large fraction of what compiles was never composed
  into anything a seed calls.

**4. What the papers add versus what the repo adds.** The released paper
set (`papers/formal/00-10*.tex`) is, on this record, **operationally
inert**: no body, no controller, no seed, no daemon, no working code is
released with it. Everything actionable found in this review — the daemon,
the bodies, the seeds, the gates, the gaps — lives in the repository, none
of it in the papers. This confirms the draft's own framing on this one
point without needing correction: the theory papers do not raise the hazard
above what the repository already constitutes; the repository is where all
of it is.

**5. What would raise the actor's cost, ranked by developer cost to
implement versus hazard reduction achieved (fuller ranked list in §6):**
authenticate the daemon's HTTP surface (cheap, closes a real and currently
unauthenticated approval/install path); default `OZMA_NO_LLM=1` and require
an explicit opt-in with a printed warning naming the reachable endpoint
(cheap, closes §3.2 directly); wire the existing `commitment_gate`/
`future_manifold` machinery into the body-control adapters it does not yet
reach, rather than building a new mechanism (moderate — the primitives
exist and are tested, only the wiring is missing, §3.1); do not ship the
real-body adapters (drone/car/F-16/helicopter) in the same distribution
as the general-cognition seeds, since §3.6 shows they do not need each
other and separating them removes the ~5% of the held set that is actually
body-control-relevant from the ~95% that is not.

---

## 5. Corrected assessment

**What the hazard is.** Not the language-model hazard. A cognition engine
(Rust graph substrate + 805 curated seeds + 306,494 runtime-taught
microtheories, 1.8 GB, copyable with no signing, encryption, or integrity
check of any kind) that ships with a small (~39-seed, ~5%) but real
body-control slice — F-16, helicopter, humanoid, a simulated Crazyflie
quadrotor, and a simulated racing car wrapping a real open-source
simulator — each requiring 600-3,650 lines of bespoke, non-self-repairing
Python per body, wrapped in an unattended daemon whose default
configuration makes an unauthenticated HTTP API available, autonomously
files and pursues its own goals, autonomously reads the live web to close
its own knowledge gaps, and autonomously calls a hosted LLM whenever its own
rules decide there is a comprehension gap and credentials happen to be
reachable.

**What cuts against it.** Real, deterministic, graph-resident decision
machinery with tested self-modification governance: a rule-adoption
regression veto, sandboxed re-validation before any self-authored Rust
primitive installs, and rate-limited/additive-only/allowlisted bounds on the
one path that removes the per-item human click. A working, tested
reversible/committing action classifier and a working, tested containment
gate exist in the codebase (`commitment_gate.py`, `information_commitment`'s
`hard_veto`, `future_manifold.rs`) — real primitives a competent team could
extend to the body-control loops, not vaporware. Measured capability on
every body is modest and frequently fails under fault conditions, and
nothing in the record has ever touched physical hardware — this is not
a demonstrated reliable autonomous controller for any cheap real platform
today.

**What cuts the other way.** The held set is copyable with zero friction —
no signing, no licence check, not even a content hash — and a small,
enumerable slice of it (the ~39 body seeds plus the corresponding ~6,000
lines of Python) is exactly the "cheap and many" body-control competence a
proliferation hazard would need, sitting inside the same repository as the
general-cognition machinery, undifferentiated by any access control. The
daemon's default configuration is more externally reachable than either
this draft or the codebase's own most recent internal audit believed: it
autonomously reads the live web, autonomously calls a hosted LLM when
credentials are present, and exposes an unauthenticated HTTP API that can
approve and install self-authored code changes. None of the tested
governance mechanisms found in this review reaches the body-control loops
that would matter if a real body were attached — every one of them protects
the engine's self-modification pipeline instead.

**Where that leaves it.** The architecture-level hazard the draft
identified is real but mis-shaped: not "an adaptable controller nobody can
gate" but "a well-governed self-modification pipeline sitting next to an
ungoverned action layer, both shipped in one copyable, unauthenticated,
default-network-reachable package, with a body-control slice that is small,
real, cheap-platform-relevant, and not yet reliable." The released papers
add nothing operational to this; the repository is where all of it already
is, today, in a public git history.

**Next actions**, unchanged in spirit from the draft, sharpened by this
review:

- A held document (with the construction paper, not released) stating
  concretely what the current held set enables on a cheap platform, which
  host boundaries are real versus aspirational (§2's table is a start),
  and what the copy result means for containment — this review is a
  step toward that document, not a replacement for it.
- The gate audit the draft called for is not "cheap and overdue with the
  answer already known" — it is done here, and the answer is mixed:
  several real gates exist and are tested, all of them on the wrong layer.
  The concrete next step is wiring the existing `commitment_gate`/
  `future_manifold` primitives into the body-control adapters, not
  inventing new ones.

---

## 6. Recommended actions, ranked

Ranked by (developer cost to implement) : (hazard reduction achieved),
cheapest/highest-leverage first.

1. **Default `OZMA_NO_LLM=1` in the daemon, require an explicit
   `--allow-llm` opt-in with a logged warning.** One-line default flip
   (`scripts/jabberwock_daemon.py`'s argparse default). Directly closes the
   §3.2 finding and re-aligns the code with what the project's own
   documentation already believes is true.
2. **Add authentication to the daemon's mutating HTTP routes**
   (`/api/proposals/<id>/approve`, `/api/auto_approve`,
   `/api/self_concerns/<id>/promote`, `/api/standing_concerns/<id>/adopt_gamma_production`).
   Cheap (a shared-secret header check); closes the one unauthenticated
   "external approval" path found in this review (§3.1).
3. **Catch `pyo3_runtime.PanicException` in the daemon's tick loop and add
   a liveness watchdog on the tick thread.** Cheap; closes the silent-hang
   vector in §3.7 regardless of whether the trigger is adversarial or a
   plain bug.
4. **Re-run and date-stamp `llm_touchpoint_audit.md`-style audits whenever
   a new teacher/network touchpoint is added, gated by a CI check that
   fails if a new `requests`/`urllib`/hosted-API import lands outside the
   audited list.** Moderate cost (one script); prevents the exact
   staleness this review found (§3.2, §4.3).
5. **Wire the existing, tested `commitment_gate`/`future_manifold`
   machinery into the body-control adapters (F-16, helicopter, humanoid,
   drone, car) as the default path, not an opt-in flag.** Moderate cost —
   the primitives exist and are unit-tested; this is integration, not
   invention (§3.1).
6. **Add a minimal content-hash (not necessarily cryptographic signing) to
   checkpoint and seed files, checked at load, logged on mismatch.** Low
   cost; does not solve containment but converts "no integrity check at
   all" into "tampering is at least detectable" (§3.3).
7. **Separate the body-control seeds/adapters from the general-cognition
   distribution**, or at minimum flag them distinctly in the repository
   layout. Low-to-moderate cost (mostly documentation/packaging); reduces
   the chance that copying "the interesting cognition work" incidentally
   copies "the flight/car/drone control competence" as an undifferentiated
   bundle (§3.6, §4.5).
8. **Author the held (not released) hazard/exposure document the draft
   called for**, using this review's §2/§3 tables as its evidentiary base
   rather than re-deriving them. Higher cost (writing and keeping it
   current), but it is the one item on this list that is a process
   commitment rather than a code change, and the draft's original
   instinct to want one is not undermined by any correction above.

---

*Grep commands, file:line citations, and reproduction steps for every
finding above are given inline in §3; none of them depend on the papers
directory beyond the specific `.tex` citations named, and none of them cite
`A1` as evidentiary (per standing project practice, A1 is excluded from the
releasable set — where the draft cited it, this review instead traced the
underlying repo-visible test/code artefact, or reported that none was
found, as with the "fifteen conformance tests" claim in Table 2).*

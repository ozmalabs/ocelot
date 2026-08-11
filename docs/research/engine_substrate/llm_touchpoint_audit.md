# LLM-touchpoint audit + the `OZMA_NO_LLM` hard switch

**Date:** 2026-07-10 (Phase B5-prep).
**Goal:** the agent implements its own improvements with ZERO hosted-LLM
assistance at runtime. This document is the exhaustive inventory of every
place the codebase can call a hosted LLM, split into **agent runtime** (must
reach — and stay at — zero) vs **dev tooling / one-off research scripts**
(out of scope for the zero-LLM guarantee, listed for completeness), plus the
kill-switch that makes regressions loud.

Scope note: "LLM" here means a *language model consulted for content/decisions*
— hosted APIs (anthropic, OpenRouter), the `claude` CLI, and remote/local
ollama chat. It does NOT include non-LLM knowledge sources (Wikipedia,
WordNet, ConceptNet, Wiktionary/kaikki, arXiv, Gutenberg, LMFDB — see §4) or
borrowed *non-generative* nets used as feature teachers (Gemma vision tower,
Whisper encoder — see §5).

---

## 0. The `OZMA_NO_LLM` switch

`domains/no_llm.py` — `no_llm()` (truthy env check; `""/0/false/no/off` are
off) and `assert_llm_allowed(context)` (raises `RuntimeError` at any hosted
call attempt). This is an **adapter policy at the teacher-construction /
invocation boundary** — mechanical host I/O per CLAUDE.md, not an agent
decision.

Behaviour under the switch:

| Touchpoint | Behaviour under `OZMA_NO_LLM` |
|---|---|
| `domains/libraries.py` `_llm()` / `attach_libraries` | LLM partner spec **skipped** (report lists `llm (OZMA_NO_LLM)`); on-disk teacher chain (grammar → dictionary → wiki → tropes) unchanged |
| `domains/llm_partner.py` `LLMPartner.__post_init__` / `.ask()` | **RuntimeError** (loud) — covers both openrouter and ollama backends, and instances built before the env was set |
| `domains/rust_runtime_world.py` `invoke_teacher` | dry-run paths unchanged; a live call (`enable_network=True, dry_run=False`) → **RuntimeError** |
| `domains/structured_data_world.py` `teacher_via_claude` | **RuntimeError** (was: silent safe-default dict) |
| `domains/language_world.py` `teacher_via_claude` | **RuntimeError** |
| `domains/phonology_teacher.py` `PhonologyTeacher` | LLM path nulled at construction; **expert fallback** (the chain's non-LLM link) serves |
| `scripts/claude_teacher.py` `make_ask()(q)` | **RuntimeError** (was: silent `""`) |

The design rule: where a chain has an honest non-LLM fallback, the switch
makes the chain *skip* the LLM link (libraries, phonology). Where code would
be *directly commanding* a hosted call, it **raises** so the violation is
detectable, never silently degraded.

Gate: `tests/test_no_llm_switch_migrated.py`.

---

## 1. Agent runtime — reachable from the live daemon (`scripts/jabberwock_daemon.py`)

Verdict up front: **the live daemon's default configuration makes zero
hosted-LLM calls.** The only LLM object it can even construct is the
`libraries.py` partner, which is default-OFF and which the daemon never
enables. The switch now hard-guarantees that.

### 1.1 The self-teacher chain (`ground_unknowns`) — VERIFIED NO LLM LINK

- Chain construction: `domains/libraries.py:attach_libraries` (called by the
  daemon at `scripts/jabberwock_daemon.py:2897-2902` with **no**
  `enable_llm`, i.e. default `False`). The chain built is
  **grammar → dictionary(WordNet) → wiki(on-disk parquet) → tropes(on-disk
  cache)** — all local, fallback-linked, head installed via
  `agent.set_self_teacher` (`domains/libraries.py:124`).
- Consumers of the chain:
  - `substrate/world_adapter.py:2556` `ground_unknowns` — per-word teacher
    loop; on total miss it queues an inquiry (`_queue_inquiry`) — the
    human-gated close.
  - `substrate/world_adapter.py:1760` `_answer_topic_reply` — topic
    self-heal; the honest-miss floor at :1848 ("couldn't find it through the
    sources I have. Tell me about it …") invites teaching.
  - `substrate/world_adapter.py:~3094` `_spawn_teacher_thread` (the
    `wire_teacher_resolution` / `_auto_resolve_impasse_tick` off-thread
    impasse resolver) — calls whatever `_self_teacher` holds. Its docstring
    says "a slow teacher (LLM round-trip)" but at runtime `_self_teacher` is
    the on-disk chain above.
  - `domains/reason.py:1459-1475` — impasse → external `teacher` param, then
    `_self_teacher`, then per-word `ground_unknowns`.
  - `domains/comprehension_world.py:46` — concept grounding via the same
    chain.
- `domains/dict_teacher.py` (`DictionaryTeacher`, :181) returns `None` on
  miss and defers to `fallback` (:215-217). The docstring's
  "dictionary → wiki → LLM" chain is **aspirational prose**: no runtime code
  constructs an LLM link. Verified.

### 1.2 The `llm` partner spec — default OFF, dormant, now hard-gated

- `domains/libraries.py:66-73` `_llm()` → `LLMPartner` (kind `"partner"`,
  `default_on=False`). Only attached when a caller passes
  `enable_llm=True`; the daemon never does. Now additionally gated by
  `OZMA_NO_LLM` at both `_llm()` and the `attach_libraries` loop.
- **Audit finding:** even when attached, `agent._llm_partner` has **no
  consumer** — nothing in `substrate/world_adapter.py` or the daemon reads
  it (the "chat_turn consults on a miss" in the libraries docstring
  describes a consumer that no longer exists). The partner spec is dormant
  wiring. Recommend deleting or documenting it as such next time
  `libraries.py` is touched.
- `domains/llm_partner.py` `LLMPartner` — the actual transport: OpenRouter
  hosted API (`openrouter.ai`, needs `OPENROUTER_API_KEY`) or remote ollama
  over an SSH tunnel (192.168.40.253). Both now raise under `OZMA_NO_LLM`
  (construction AND `ask`).

### 1.3 `_self_extend_reflex` — VERIFIED, no regression

`substrate/world_adapter.py:5784-5840`: the order-4 authoring reflex composes
the approach from held primitives (`compose_held:…`), defers to the
`self_extension` compose rules, and surfaces an honest `HumanImpasse` when
nothing held covers the need. The ":5813 No hosted teacher / No claude -p"
comment matches the code — there is no teacher invocation anywhere in the
method. Nothing regressed.

### 1.4 The experiment child runner — clean

`domains/experiment_dispatch.py:_spawn` (:111-145) only ever spawns
`scripts/arc_child_run.py` (`_CHILD_RUNNER`) with snapshot/delta/game args —
it cannot be steered into an LLM-calling script by graph data.

### 1.5 Seed `llm_partner` — graph DATA, not calls

`domains/seed_registry.py:204` installs the `llm_partner` **seed** — Concept
nodes *about* LLMs (`install_llm_partner_concepts`,
`domains/llm_partner.py:345`) so the agent can reason about what an LLM is.
No network calls; not a touchpoint.

---

## 2. Real hosted-call code NOT reachable from the daemon (dev tooling / research harnesses)

These contain genuine hosted-LLM invocation code. None is imported by the
daemon or `world_adapter`; all are one-off scripts or script-only worlds.
All are now guarded anyway (defense in depth).

| # | Touchpoint | What it does | Reachability | Non-LLM fallback | Guard |
|---|---|---|---|---|---|
| 1 | `domains/rust_runtime_world.py:632` `invoke_teacher` → anthropic `client.messages.create` (:779) | asks a hosted model to draft Rust patches (DesignedPatch nodes) | scripts only (`scripts/agent_composes_patches.py`, `teacher_grounds_design.py`, `apply_teacher_patches.py`, …) | triple-gated already: `enable_network=True` explicit + `ANTHROPIC_API_KEY` + SDK installed; dry-run returns prompt only | raises under switch when a live call is requested |
| 2 | `domains/structured_data_world.py:220` `teacher_via_claude` → shells `/home/matt/.local/bin/claude --print` | structured-parse teacher for the data-format world | `scripts/structured_data_babble.py` opt-in; the world defaults to `teacher_stub` | `teacher_stub` (:139) — deterministic, no subprocess | raises under switch |
| 3 | `domains/language_world.py:209` `teacher_via_claude` → shells `claude --print` | (meaning, grammar, lexicon) spec teacher | `scripts/language_test.py` opt-in only; **`world_adapter.py:3418` uses `make_stub_teacher` (NO LLM)** | `teacher_stub` (:337) / `make_stub_teacher` (:447) | raises under switch |
| 4 | `scripts/claude_teacher.py:make_ask` → shells `claude -p` | the pluggable `ask(question)->answer` channel for `domains/teacher_hook.py:ask_if_needed` | imported only by one-off scripts (`autonomous_speech.py`, `build_persona_faculty.py`, `jabberwock_authors_*.py`, `jabberwock_designs_*.py`, …); many honour `SPEECH_TEACHER=stub` | scripts' stub teachers; `teacher_hook` records "no help" on empty | raises under switch |
| 5 | `domains/phonology_teacher.py:160` LLM path (via an `LLMPartner` passed in) | per-word phonology signatures | `scripts/fsdd_learner_world.py` only | `_EXPERT_DIGIT_SIGNATURES` expert fallback (always available) | LLM path nulled at construction under switch |
| 6 | `scripts/jabberwock_richlm_read_run81.py:230` `ollama_chat` → local ollama `:11434` | run-81 rich-LM reading experiment | one-off script (+ `tests/test_run81_migrated.py`, which skips when ollama is down) | n/a (the experiment IS the LM probe) | unguarded — local-only research harness, never daemon-reachable |
| 7 | `domains/llm_partner.py` `LLMPartner` (transport for #5 and §1.2) | openrouter / remote-ollama chat | see §1.2 | n/a | raises under switch |

`domains/teacher_hook.py` itself is only the channel (takes any
`ask` callable); it holds no LLM code — the guard lives on the channels
(#4, and any `LLMPartner` passed as `ask`).

---

## 3. Grep sweep — what was checked and came back clean

- CLI/API patterns: `claude -p`, `--print`, `api.anthropic`, `anthropic.`,
  `openai`, `ChatCompletion`, `chat/completions`, `messages.create`,
  `openrouter`, `ollama`, `gpt` across `domains/ substrate/ scripts/ tests/
  web/ tools/`. All hits are accounted for above, are comments/docstrings
  ("No LLM", migration history), or are the *word-concepts* the agent holds.
- All HTTP-capable modules (`requests`/`urllib`) in `domains/ substrate/`:
  the only LLM endpoints are in `llm_partner.py` and
  `rust_runtime_world.py`. The rest are §4 knowledge sources.
- All `subprocess` users in `domains/`: the only model-CLI shell-outs are
  the two `teacher_via_claude`s (#2, #3). Others are espeak/ffmpeg
  (`parent_teacher.py` — TTS, not an LLM), the sandboxed tool runner
  (`tool_use.py` / `tool_authoring.py` — argv-list instruments, no shell),
  the experiment child runner (§1.4), and ssh tunnelling inside
  `llm_partner.py`.
- `web/` (console + `mock_server.py`): no LLM calls; the mock server is a
  local HTTP stub for the console UI.
- `substrate/boot_all.py`, `substrate/seed_loader.py`: seed installation
  only; the `teacher_hook` mention at `boot_all.py:475` is a comment.
- `tests/`: `test_run81_migrated.py` may hit **local** ollama (skips when
  down); `test_run82/83_migrated.py` *assert the absence* of LLM imports in
  emit paths. No hosted calls.

## 4. Non-LLM network knowledge sources (explicitly OUT of scope)

These fetch *reference data*, not model output; the zero-LLM goal does not
cover them (they are the agent's non-LLM grounding): `domains/
topic_grounding.py` (Wikipedia REST, the `_ground_web` fallback behind the
on-disk wiki library), `fetch_dispatch.py`, `web_world.py` (wikipedia/arxiv),
`broaden_source.py` (arxiv), `conceptnet_reference.py`,
`wiktionary_reference.py` (kaikki dump), `morphology_reference.py`
(unimorph), `reading_corpus.py` (Gutenberg), `lmfdb_local.py` (LMFDB API).

## 5. Borrowed local nets (not hosted, not generative — flagged, allowed)

`domains/gemma_teacher_adapter.py` (local Gemma vision-tower features, "No
LLM" by design), `domains/whisper_teacher_adapter.py` (local Whisper encoder
features), `domains/model_reader.py` (raw GGUF/safetensors weight *reads* —
opening a model as data, no inference service). These are proposal-only
feature teachers per the conversion-loop architecture; the earned structure
decides.

---

## 6. Follow-ups (deferred — files owned by another agent this wave)

1. **`scripts/jabberwock_daemon.py` — add a `--no-llm` flag** that sets
   `OZMA_NO_LLM=1` in `os.environ` before `attach_libraries` runs (one line
   of mechanical env plumbing), so the operator can pin the guarantee per
   invocation instead of per environment. Optionally log
   `no_llm=<bool>` in the boot banner for auditability.
2. **`substrate/world_adapter.py` — none required.** `ground_unknowns`,
   `_spawn_teacher_thread`, `_answer_topic_reply` and `_self_extend_reflex`
   are all teacher-agnostic or already LLM-free; the switch is fully
   enforceable at the construction boundary. (If a future wave re-adds an
   `_llm_partner` consumer, that consumer must call
   `domains.no_llm.assert_llm_allowed` — note for the owner.)
3. **`domains/libraries.py` dormant partner wiring** — `agent._llm_partner`
   has no consumer (§1.2); delete the spec or document it as reserved.
4. `tests/test_run81_migrated.py` talks to *local* ollama when up; if the
   zero-LLM bar is later extended to local LMs in CI, gate that test on
   `OZMA_NO_LLM` too (currently out of scope: local, research-bench only).

---

## 7. GRADUATION (Wave 6) — the no-assistance gate

**What it proves.** `scripts/no_assistance_gate.py` is the standing,
re-runnable proof of the bootstrap plan's endpoint: improvements are
implemented ENTIRELY by the Jabberwock at runtime, with zero hosted-LLM
assistance. Under `OZMA_NO_LLM=1` (set before boot, so any hosted call
raises and fails the run), it drives two full improvement cycles using
ONLY the surface a human has at the chat UI — `converse()` turns, the
`flag_reply_turn` flag button, and the daemon's own mechanical tick hooks
(`tick()`, `_steer_tick`, `_concern_tick`, `_dispatch_tick` with real
subprocess children, `_close_tick`, `_narrate_tick`):

  * **Cycle A (cue family):** an uncovered instruction files a gap → NL
    promote → the graph picks the cue-set-edit variation → a real replay
    child validates it → judged supported → adopted (Concept taught) → the
    same instruction is handled.
  * **Cycle B (ablation family):** flagged bad replies → NL promote → the
    graph picks a reply-rule ablation → replay child, zero regressions →
    supported → adopted → the parent's reply behaviour actually changes.
  * **Negative control (adoption safety):** a net-positive-but-REGRESSING
    variant judges supported, and `seeds/adoption_safety.json`'s
    `adopt_denied_on_regression` rule vetoes adoption — the denial and its
    reason are readable over NL ("What are you working on?").

The script asserts its own call discipline by AST audit (no
reflective_faculty internals, no hand-minted Experiments/SeedDeltas, no
direct graph mutation — `audit_source_discipline()`), and emits a full
audit-trail JSON (per cycle: concern id, promoted-by turn, experiment id,
graph-chosen variation op, child result, judge outcome, adoption id,
before/after replies) plus a pass/fail summary.

**How to run.**

    PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/no_assistance_gate.py
    # pytest wrapper (part of the migrated bench):
    PYTHONPATH=runners/dsl/python:. python3 -m pytest tests/test_no_assistance_gate_migrated.py

**The human's remaining roles** — by design, not by gap:

  1. **NL steering** — flagging a bad reply, phrasing "Work on the X gap."
     (only interlocutor turns can mark a concern for promotion);
  2. **Promote** — the human-gated `promote_self_concern` step the steering
     hook executes (and the UI promote button performs directly);
  3. **Rung-4 approval** — a proposed new Rust Term/primitive is the one
     thing the agent cannot install in itself; it can only propose.

Everything between those points — gap filing, variation choice, experiment
authoring, dispatch, judgement, the regression-veto safety gate, adoption,
narration — is the agent's own graph rules plus mechanical host I/O, LLM-free.

**Known residual** (pre-existing, out of the gate's scope): `converse()`'s
table-meta routing does not serve reader-backed questions like "What are
you working on?" (it answers via `answer_question`, which the gate and
`tests/test_nl_steering_migrated.py` use); a fresh unmodified boot shows
the same miss over `converse()`. A Python-frontend gap of the documented
find-and-file class.

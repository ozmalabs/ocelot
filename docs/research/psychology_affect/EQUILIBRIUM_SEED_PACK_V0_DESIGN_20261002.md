# EQUILIBRIUM SEED PACK v0 — DESIGN (taxonomy, adapter, frozen classifier sidecar)

**Date:** 2026-10-02. Base `main @ 8bac3e90` ("perf: bound WordNet membership lookup RSS"). Worktree `/home/matt/ozmadev/ocelot/.worktrees/t3`, branch `t3/equilibrium-seed-pack-v0`. Spec reference: Equilibrium `DESIGN.md` §16.7 (Ocelot classifier, :1006-1076), §16.10 (emoji senses, :1180-1244), §23 Phase 9 (T3 row, :1744). Companion pre-registration draft: [`EQUILIBRIUM_SEED_PACK_V0_PREREG_20261002.md`](EQUILIBRIUM_SEED_PACK_V0_PREREG_20261002.md). Design only — no code, no seeds, no measurements in this commit. Not merged to main, not pushed — left for the orchestrator's independent re-verification.

**HEADLINE.** Seed pack v0 is a set of flat, versioned seed manifests (`seeds/equilibrium_*.json`, `self_load_only: true`) that put the Equilibrium taxonomy into the graph as vocabulary + rules. A ~100-line world adapter (`domains/equilibrium_classify.py`) turns a request into substrate mutations, ticks, and reads labels plus `rule_id` traces back out. A stdlib HTTP sidecar on `127.0.0.1:8790` serves it in a frozen mode, where request content only ever touches a disposable branch. **Dependency (uncommitted upstream work):** the copy-on-write `SubstrateSnapshot`/`fork()` API and the `COW_*_RESULTS_20261001` docs that Equilibrium §16.7 cites are **not in any commit** (8bac3e90 or any local branch), but they **do exist as uncommitted work in the main Ocelot checkout**: `runners/dsl/src/py.rs:1479-1652` (`SubstrateSnapshot` with `id`/`source_revision` getters and `fork()`; `PySubstrate.snapshot()` defaulting to `shared_graph_pages`) and untracked `docs/research/engine_substrate/COW_*_RESULTS_20261001.md`. This branch cannot build against it until that work is committed. The service design uses those real API names and keeps a fallback that runs on 8bac3e90 (§5.5).

---

## 0. Binding constraints (from CLAUDE.md and the brief)

* The agent is Rust and Python is only the world adapter (CLAUDE.md:35-43, :104-148). The adapter only **ingests** (`add_node`/`add_edge`) and **emits** (pure reads). It has no conditionals over graph state, no `recognise_X`/`decide_Z` helpers, and no Python rule engine. Every label decision is a seeded rule. An I/O-boundary classifier is allowed only when it maps an opaque form to the smallest graph token and no Rust primitive exists (:122-125). Examples: the byte `?` becomes a `Terminator{char:"?"}` token, and a code fence becomes a `CodeSpan` node.
* **SHAPES, NOT NUMBERS** (CLAUDE.md:943+). Hostility, valence and pattern strength are ordinal **codebook verdicts** (ShapeDecode over a `ShapeSignature*` codebook, as in `discourse_coherence.ensure_codebook`), not scalar scores with thresholds. Equilibrium's `confidence` field is therefore emitted as the decode's `shape_fit` class (`exact|partial|weak`) and is never an invented probability (OQ-3).
* Seeds are versioned (`id`, `version`), declare `depends_on`, load in topological order, and must fail the boot on conflict (CLAUDE.md:167-204).
* `OZMA_NO_LLM=1` is a hard switch. The adapter never constructs a `LanguageWorld` teacher and never reaches `teacher_via_claude` (domains/language_world.py:209-218). The sidecar refuses to start unless `OZMA_NO_LLM == "1"`, and `/v1/info` reports the asserted value.
* Privacy: no real content, usernames or Discord IDs appear in any Ocelot artefact, including seeds, goldens, docs and logs. Examples use pseudonyms (`actor_a`, `expert_e`, `member_017`). Logs record counts, latencies and rule_ids only, never text.

---

## 1. Taxonomy v0

`taxonomy_version = "eq-tax-0.1.0"`, a semver independent of the seed-pack version (§2). A label name is a dotted path (`msg.speech_act.question`, `pat.sealioning`). Every emitted label carries `rule_ids[]`, the ids of the seeded rules whose effects asserted it, plus `trace_ref`, the id of the trace entry in the response (§4.3).

**rule_id scheme:** `eq.<layer>.<label>.<variant>@<pack_version>`, where layer ∈ {`msg`, `rel`, `emo`, `pat`}. For example, `eq.msg.speech_act.question_terminator@0.1.0` or `eq.pat.sealioning.repeat_demand_after_answer@0.1.0`. The seed-manifest rule `name` is the part before `@`. The adapter appends the pack version on read-out, so rule names inside a pack stay stable and the id stays globally unique across versions.

### 1.1 Message labels (per message; layer `msg`)

All of these are decided by seeded rules over graph tokens minted at ingest: `Message`, `Token`, `Terminator`, `CodeSpan`, `LinkSpan`, `Mention{target_ref}`, `QuoteSpan`, `EmojiUse`, and `RepliesTo`.

| label family | values (v0) | graph-observable basis | reuse |
|---|---|---|---|
| `speech_act` | question, assertion, directive, answer, gratitude, apology | `question/assertion/directive` come from the existing `speech_act_classify` rules (`sak_kind_*`, seeds/speech_act_classify.json, mapped kind→act). `answer` = assertion ∧ `RepliesTo` a message whose act is question ∧ lexical overlap with the parent's focus slot. `gratitude/apology` come from a small seeded lexicon (`ThanksCue`, `ApologyCue`) over the token chain. | reuse + new rules |
| `discourse_relation` (to parent) | contrast, cause, sequence, condition, elaboration, none | `coherence_between(agent, parent, msg).relation` (domains/discourse_coherence.py:272) over the parent→child pair. A None verdict maps to `none`. | reuse |
| `valence` | neg, neutral, pos | ordinal codebook `ShapeSignatureValence` over `AffectCue` hits (lexicon seed) plus emoji seed senses (§1.4). Negation scope is a seeded rule over `NegCue` → next content token. | new codebook |
| `hostility` | none, mild, marked, severe | codebook `ShapeSignatureHostility`: insult-lexicon hit × target (person vs idea) × intensifier/caps-run token. `severe` requires a person target. | new |
| `person_targeting` | none, second_person, third_person_present, group | `Mention` / 2nd-person pronoun token in the same clause as a hostility or evaluative cue whose target is a person, not an `IdeaRef` (claim, code, link). This is the ad hominem marker. | new |
| `deescalation` | bool | `ApologyCue` / `HedgeCue` / `AgreeCue` / acknowledgement-of-parent (`answer` to a hostile parent with hostility=none). | new |
| `substantive_markers[]` | code, link, evidence, citation, diagnostic_step, code_explanation, question | `CodeSpan` (fence/inline backtick), `LinkSpan` (URL token), `evidence` = `cause` relation + link/quote/number token, `citation` = `QuoteSpan`∧`RepliesTo`, `diagnostic_step` = directive with a sequence relation or numbered list, `code_explanation` = cause/elaboration relation adjacent to a CodeSpan. | new rules |
| `domains[]` | per-guild topic tags (v0: `programming`, `gaming`, `meta`, `offtopic`, `unknown`) | `DomainCue` lexicon membership over content tokens. The WordNet membership path (bounded at 8bac3e90) is a later, optional dependency. | new |

The I/O-boundary tokenisers are the only Python string inspection: code-fence/backtick spans, URL spans, `<@…>` mentions (replaced by a request-local opaque `ref_n`, never the ID), Unicode emoji codepoints, and custom-emoji `<:name:id>` (name kept and id dropped, §1.4). They emit tokens. They do not emit labels.

### 1.2 Thread / pattern labels (per (actor, thread window); layer `pat`)

A pattern label is asserted on a `PatternInstance{label, actor_ref, window_id}` node with `constituted_by` edges to the turn ids that fire it. Equilibrium stores those turn ids as evidence. Notation: within window W, `D(m)` = m's speech act is a demand/question for evidence, `A(m)` = m is an answer/evidence-bearing reply, `R(x→y)` = `RepliesTo`.

| label | phase | operational definition (graph-observable) | context window |
|---|---|---|---|
| **sealioning** | **v0** | Actor a issues ≥2 `D` turns to target t, ∧ between them t (or a third party) posts `A` replying to a's earlier `D` with `substantive_markers ∋ {evidence, link, code, citation}`, ∧ a's later `D` has no `RepliesTo`/quote edge to that `A` (it ignores the answer), ∧ all of a's turns have hostility ≤ mild (the "polite" constraint is what separates this from plain hostility). The repeat count is an ordinal shape (`2`, `3+`), not a threshold knob. | the reply chain rooted at a's first D, plus siblings, ≤ 50 msgs or 72 h |
| **goalpost shifting** | **v0** | a makes claim/demand C1 (`D` or assertion with focus slot f1), t posts `A` addressing f1 (overlap of focus slot), then a posts C2 replying to `A` with a `contrast` relation (or `condition`), whose focus slot f2 ≠ f1, without an acknowledgement/concession cue. The fired shape needs ≥1 shift. `2+` shifts is the strong shape. | same chain, ≤ 50 msgs / 72 h |
| JAQing | later (v1) | a's turns are ≥ k questions (`speech_act=question`) carrying a loaded presupposition (`PresupCue`: "isn't it true", "just asking", leading negation), ∧ no a-turn in W is an assertion committing to the presupposition, ∧ a has no `A`-replies to answers given. | thread, ≤ 50 msgs |
| concern trolling | later (v2) | a's turns pair a `ConcernCue` / sympathy frame with a `contrast` relation to the group's stated goal, ∧ a has no prior affiliative history in the window (reaction/agreement edges toward the group) ∧ a's `directive` acts push abandonment of that goal. This needs cross-thread actor history, which v0 lacks. | thread + actor's prior 30 d (aggregate edges only) |
| DARVO | later (v2) | after t posts a message with `person_targeting` / complaint directed at a, a replies with denial (`NegCue` on t's claim), then an attack on t (hostility ≥ marked, person-targeted), then a self-victim frame (`VictimCue`, first person). The three moves must occur in order within a's subsequent turns. | reply chain from the complaint, ≤ 20 a-turns |
| selective non-response | later (v1) | in W, a replies to n turns addressed to a (`R(x→a)` or mention) but leaves the subset with `substantive_markers ∋ evidence` unreplied while replying to non-evidence ones. The shape is "all evidence-bearing unanswered ∧ some others answered". | thread, ≤ 100 msgs / 7 d (requires the "unanswered" cut-off) |
| motte-and-bailey | later (v2) | a asserts strong claim S (bailey). When challenged (`A` with contrast to S), a retreats to weaker claim s (motte) where s is entailed by S but not vice versa (requires an entailment relation over claim frames). Later in W, a re-asserts S once the challenge is unanswered. | thread, ≤ 100 msgs; needs claim-frame entailment (not in v0) |

**Failure modes, fairness risks and red-team evasions** (summary per pattern. The PREREG registers these as audit strata.)

| label | failure modes (false fire / miss) | fairness risks (dialect/register, non-native English) | red-team evasions |
|---|---|---|---|
| sealioning | **FP:** a genuine learner asks repeated follow-ups because they didn't understand the answer. **FP:** the answer arrived but a didn't see it (thread fork, edit). **Miss:** demands phrased as assertions ("source needed"). | Non-native speakers re-ask with reformulations more often. Formal/indirect registers ("could you possibly show…") read as polite demands. Help channels are full of legitimate repeat questions. Mitigation: the `expert_e`-asks / `newcomer`-asks split as a stratum, and the requirement that the later D *ignores* the A (no quote, no overlap with A's content). | quoting a fragment of the answer to defeat the "ignores" edge; spacing demands > window; using several accounts (out of scope, structure-only signals). |
| goalpost shifting | **FP:** legitimate refinement of a question ("ok that works, now what about X"), which needs the concession cue check. **FP:** topic drift by third parties. **Miss:** shifts without a contrast connective. | Terse registers omit concession cues ("ok" vs "thanks that fixes it"), so dialects with low politeness marking look like non-concession. The concession lexicon must include the terse forms. Non-native speakers with sparse connective use produce relation=None. | inserting a token concession ("sure, but…"); shifting via a new top-level message instead of a reply. |
| JAQing | FP on Socratic teaching / genuine scepticism. | rhetorical-question-heavy dialect features (tag questions, `innit`, `right?`). | asserting then retracting; mixing with neutral questions. |
| concern trolling | the highest FP risk; sincere concern is indistinguishable from text. | newcomers lack the affiliative history, so the prior is biased against new members. | building a short affiliative history. |
| DARVO | genuine victims who are accused first, then defend. Order alone is ambiguous. | emotional-register differences in denial phrasing. | splitting the moves across threads. |
| selective non-response | being offline or a timezone gap looks like avoidance. | differential participation rates by timezone / language. | replying "will look later" (a non-substantive reply). |
| motte-and-bailey | claim-frame entailment errors dominate. | hedging-heavy registers look like retreats. | never stating S explicitly. |

Pattern labels never run on a single message. The adapter refuses `/v1/discourse` windows below the label's minimum turn count and returns `insufficient_context` for those labels, not `false`.

### 1.3 Contextual dependencies

`pat.*` rules depend on `msg.*` facts. Topological order: `equilibrium_tokens` → `equilibrium_lexicon` → `equilibrium_msg` → `equilibrium_emoji` → `equilibrium_pattern` (§2.1).

### 1.4 Emoji senses (§16.10)

* **Sense vocabulary** (Concept nodes, seed `equilibrium_emoji`): amusement, endorsement, affection_support, attention_spectating, surprise, sympathy, disapproval, meta_vote, in_joke.
* **Unicode seed senses:** a static table codepoint → {sense, valence prior}, authored from the CLDR short names/keywords plus the Kralj Novak et al. (2015) emoji sentiment ranking. This is a public lexical resource, not corpus-derived, and its provenance is recorded per node (`provenance: "cldr-<ver>|kralj-novak-2015"`). v0 covers the top ~300 codepoints by CLDR frequency. The rest map to `sense=unknown`.
* **Per-guild custom-emoji senses** are not learned inside Ocelot (that would be a learning write, which frozen mode forbids). Equilibrium owns `guild_emoji_senses`. The request may carry `custom_emoji_senses: {"<name>": "<sense>"}`, which the adapter ingests as request-local `EmojiSense` edges on the branch. For unknown custom names, Ocelot offers a *proposal* read-out: `comprehend_text` over the emoji **name** only (e.g. `"pepe_laugh"` → tokens → lexicon sense). Equilibrium may store the proposal as a candidate, marked shadow. Co-occurrence learning stays Equilibrium-side.
* **Contextual reaction act** = rule over (sense, target-message labels, reactor→author relation in the window). The values are affiliation, audience_reinforcement, corroboration, alignment, bystander_support, audience_gathering. Examples: endorsement on a message with `hostility ≥ marked` ∧ `person_targeting` gives audience_reinforcement. Endorsement on an evidence-bearing answer gives corroboration. Sympathy on the target of a hostile message gives bystander_support. Attention_spectating on a hostile thread gives audience_gathering. Every act carries `rule_ids`. Reactions arrive as `reactions: [{msg, reactor_ref, emoji}]` with pseudonymous refs.

---

## 2. Versioning and label lifecycle

### 2.1 Seed-pack layout (flat, because of the boot_all glob)

`substrate/boot_all._seed_manifest_paths` (boot_all.py:27-32) globs only `seeds/*.json` and `seeds/generated/*.json`, so the `seeds/equilibrium/` subdirectory suggested in Equilibrium §16.7 would be silently skipped. v0 uses flat files, all `self_load_only: true` so that full Ocelot boots never pull them in:

| seed id | depends_on | content |
|---|---|---|
| `equilibrium_tokens` | `speech_act_classify`, `discourse_argument` | Message/Token/CodeSpan/LinkSpan/Mention/EmojiUse/PatternInstance types, `RepliesTo`/`constituted_by` productions |
| `equilibrium_lexicon` | `equilibrium_tokens` | cue lexicons (Thanks/Apology/Hedge/Agree/Neg/Affect/Insult/Presup/Concern/Victim/Domain). Authored from train split only (§7) |
| `equilibrium_msg` | `equilibrium_lexicon`, `argument_role_vocabulary` | msg-layer rules + `ShapeSignatureValence`/`Hostility` codebooks |
| `equilibrium_emoji` | `equilibrium_msg` | sense concepts, Unicode table, reaction-act rules |
| `equilibrium_pattern` | `equilibrium_emoji` | pat-layer rules (v0: sealioning, goalpost shifting; others present as `status: disabled` stubs) |
| `equilibrium_label_status` | `equilibrium_pattern` | one `LabelStatus{label, status, since_pack}` node per label |

The lexicons are persisted through `domains.teach.teach` when items are taught (CLAUDE.md:206-243). The seed-pack builder script runs `teach` on a scratch substrate and exports, so lexicon JSON is never hand-authored per item.

### 2.2 Versions, hash, provenance in every output

* `seed_pack_version`: semver of the pack (all six manifests share it).
* `seed_pack_sha256`: sha256 over the concatenation of `"<id>\t<sha256(file bytes)>\n"` for the six files, sorted by id. This reuses the per-file digest pattern of `boot_all._seed_sources_digest` (:268). There is no built-in pack digest.
* `taxonomy_version`: the label set + definitions. Bump the minor version when a label is added and the major version when a definition changes.
* `ocelot_commit`: `git rev-parse HEAD`, baked at image build as `OCELOT_COMMIT`.
* Every `/v1/classify` and `/v1/discourse` response carries `{taxonomy_version, seed_pack_version, seed_pack_sha256, ocelot_commit}` in an envelope, and every label carries `rule_ids[]` + `trace_ref`.

### 2.3 Ocelot label status ↔ Equilibrium `label_gates`

Ocelot ships a **pack-level** status per label. Equilibrium owns the **per-guild** gate (`label_gates(guild_scope, label, taxonomy_version, status, audit_receipt)`, statuses `ungated → audited → enabled`, DESIGN.md:1062). Neither overrides the other. The effective visibility is the minimum of the two.

| Ocelot pack status | emitted? | meaning | allowed Equilibrium gate states |
|---|---|---|---|
| `disabled` | no (label key absent, listed in `/v1/info` as disabled) | rule stub only, or retracted | none |
| `shadow` | yes, with `"status":"shadow"` | computed and stored; member-self / RESEARCH_INTERNAL only, "Equilibrium heuristic — uncalibrated" | `ungated`, `audited` |
| `enabled` | yes, with `"status":"enabled"` | passed the pre-registered quality check (PREREG) at this taxonomy_version | `ungated`, `audited`, `enabled` (moderator-facing only when the guild gate is also `enabled` with an R15 fairness receipt) |

v0 ships every label `shadow` except the seven pattern labels: sealioning and goalpost shifting are `shadow`, the other five are `disabled`. Promotion to `enabled` happens only in a later pack version, after the PREREG's test-split evaluation passes. A status change is a seed-pack version bump, never a runtime toggle. The terminology mismatch (disabled/shadow/enabled vs ungated/audited/enabled) is OQ-1.

---

## 3. `domains/equilibrium_classify.py` — thin world adapter

Shape copied from `domains/corpus_world.py` (sequence input, read growth back), **without** its persistence. All decisions happen in the seeded rules fired by `tick()`. Python only tokenises at the I/O boundary, mints nodes and edges, and reads attributes.

```python
"""Equilibrium world adapter: request JSON -> substrate mutations -> tick -> label read-out.
No decisions here: every label is asserted by a rule in seeds/equilibrium_*.json."""
from typing import TypedDict, Literal, Any

class MsgIn(TypedDict, total=False):
    id: str                 # request-local opaque id, e.g. "m1"
    author_ref: str         # pseudonymous, e.g. "actor_a"
    text: str
    ts: str                 # RFC3339 UTC
    reply_to: str | None    # id of parent within the request
    reactions: list[dict]   # [{"reactor_ref": "member_017", "emoji": "👍" | "<:name:>"}]

class Labelled(TypedDict):
    id: str
    labels: dict[str, Any]          # family -> value(s); see §4 schema
    rule_ids: list[str]
    trace_ref: str

PACK_IDS: tuple[str, ...] = ("equilibrium_tokens", "equilibrium_lexicon", "equilibrium_msg",
                             "equilibrium_emoji", "equilibrium_pattern", "equilibrium_label_status")

def load_pack(substrate, seed_dir: str) -> dict:
    """Explicit topo-ordered load via substrate.seed_loader.load_manifest_file + apply_manifest
    (boot_all would not sweep self_load_only packs). Returns {seed_pack_version, seed_pack_sha256}."""

def ingest(branch, messages: list[MsgIn], *, custom_emoji_senses: dict[str, str] | None = None,
           window: dict | None = None) -> dict[str, int]:
    """Mint Message/Token/CodeSpan/LinkSpan/Mention/EmojiUse/RepliesTo nodes+edges on `branch`
    (never the base). Returns request-id -> node-id map. Boundary tokenisers only."""

def run(branch, *, max_ticks: int) -> int:
    """substrate.tick() until quiescent or max_ticks (bounded per request); returns ticks used.
    Never start_agent(): the tick thread is never started in classifier mode."""

def read_messages(branch, idmap: dict[str, int]) -> list[Labelled]:
    """Pure read: Label nodes asserted on each Message + the rule_id provenance attrs."""

def read_patterns(branch, idmap: dict[str, int]) -> list[dict]:
    """Pure read: PatternInstance{label, actor_ref, status} + constituted_by turn ids + rule_ids."""

def classify(branch, request: dict) -> dict:
    """ingest -> run -> read_messages (+ read_patterns for /v1/discourse). ~15 lines, no branching
    on graph state."""
```

`comprehend_text(agent, text)` takes a booted agent (domains/comprehend_text.py:1313), not bare text as Equilibrium DESIGN.md:1012 implies. The adapter calls it only through the branch, for the emoji-name proposal. `read_discourse` (discourse_coherence.py:330) mints `DiscourseEvent` nodes, which is acceptable only because it runs on a branch.

---

## 4. HTTP contract (sidecar)

Stdlib `ThreadingHTTPServer` following `web/mock_server.py` (:44-49), hardened body handling following `services/p5_r0_evaluator/app.py`: `MAX_REQUEST_BODY_BYTES = 1_048_576`, and a missing or invalid Content-Length is treated as oversize. The bind is hard-coded to `127.0.0.1`, port `8790` (env `EQ_SIDECAR_PORT` may change only the port). The process exits if the bind host resolves to anything except loopback. **No auth.** That is acceptable only because the socket is loopback-bound and Equilibrium's worker refuses non-loopback `EQ_OCELOT_URL`. Any container publish must be `-p 127.0.0.1:8790:8790`. Exposing the port off-host requires adding auth first (OQ-6).

### 4.1 `POST /v1/classify`

```json
{"$schema":"https://json-schema.org/draft/2020-12/schema","title":"ClassifyRequest","type":"object",
 "required":["taxonomy_version","messages"],"additionalProperties":false,
 "properties":{
  "taxonomy_version":{"type":"string"},
  "messages":{"type":"array","minItems":1,"maxItems":100,"items":{"$ref":"#/$defs/Msg"}},
  "context":{"type":"array","maxItems":20,"items":{"$ref":"#/$defs/Msg"},
             "description":"parent/thread messages: ingested for relations, not labelled"},
  "custom_emoji_senses":{"type":"object","additionalProperties":{"type":"string"}}},
 "$defs":{"Msg":{"type":"object","required":["id","author_ref","text"],"additionalProperties":false,
  "properties":{"id":{"type":"string","maxLength":64},"author_ref":{"type":"string","pattern":"^[a-z_]+_?[a-z0-9]*$","maxLength":32},
   "text":{"type":"string","maxLength":4000},"ts":{"type":"string","format":"date-time"},
   "reply_to":{"type":["string","null"]},
   "reactions":{"type":"array","maxItems":50,"items":{"type":"object","required":["reactor_ref","emoji"],
     "properties":{"reactor_ref":{"type":"string"},"emoji":{"type":"string","maxLength":64}}}}}}}}
```

Response 200:

```json
{"ok":true,
 "provenance":{"taxonomy_version":"eq-tax-0.1.0","seed_pack_version":"0.1.0","seed_pack_sha256":"<hex>","ocelot_commit":"<sha>"},
 "results":[{"id":"m2",
   "labels":{"speech_act":{"value":"answer","status":"shadow"},
             "discourse_relation":{"value":"cause","status":"shadow"},
             "valence":{"value":"neutral","status":"shadow"},
             "hostility":{"value":"none","status":"shadow"},
             "person_targeting":{"value":"none","status":"shadow"},
             "deescalation":{"value":false,"status":"shadow"},
             "substantive_markers":{"value":["code","code_explanation"],"status":"shadow"},
             "domains":{"value":["programming"],"status":"shadow"},
             "reaction_acts":{"value":[{"reactor_ref":"member_017","sense":"endorsement","act":"corroboration"}],"status":"shadow"}},
   "confidence":"exact",
   "rule_ids":["eq.msg.speech_act.answer_to_question@0.1.0","eq.msg.substantive.code_fence@0.1.0"],
   "trace_ref":"t2"}],
 "traces":[{"ref":"t2","fired":[{"rule_id":"eq.msg.speech_act.answer_to_question@0.1.0","bound":{"m":"m2","p":"m1"}}]}],
 "stats":{"ticks":7,"elapsed_ms":12.4}}
```

### 4.2 `POST /v1/discourse`

The request has the same `Msg` defs plus `{"window":{"thread_id_ref":"thr_1","until":"<ts>"}, "labels":["pat.sealioning","pat.goalpost_shifting"]}`, with `maxItems` 200. The response is `{"ok":true,"provenance":{…},"patterns":[{"label":"pat.sealioning","actor_ref":"actor_a","status":"shadow","shape":"3+","constituted_by":["m1","m3","m5"],"rule_ids":["eq.pat.sealioning.repeat_demand_after_answer@0.1.0"],"trace_ref":"t9"}],"insufficient_context":["pat.goalpost_shifting"],"relations":[{"src":"m3","tgt":"m2","relation":"contrast"}],"centrality":[{"id":"m3","degree":4.0}]}`. Centrality comes from `centrality_ranking` (discourse_coherence.py:397-433).

### 4.3 `GET /v1/info`, `GET /healthz`

`/v1/info` → `{"ok":true,"taxonomy_version":"eq-tax-0.1.0","seed_pack_version":"0.1.0","seed_pack_sha256":"<hex>","ocelot_commit":"<sha>","ozma_no_llm":true,"mode":"frozen-fork"|"frozen-reload","labels":{"msg.speech_act":"shadow",…,"pat.jaqing":"disabled"},"base":{"revision":"<digest>","node_count":N,"edge_count":E,"batches_served":k},"limits":{"max_messages":100,"max_body_bytes":1048576}}`. `/healthz` → `{"ok":true}` only when the base-unchanged check (§5.3) passed on its last run. Otherwise it returns 503, so the Equilibrium worker stops advertising `classify`.

### 4.4 Error model

The body is always `{"ok":false,"error":{"code":"<code>","message":"<no content echo>","retryable":bool}}`. Error messages never echo request text.

| HTTP | code | when |
|---|---|---|
| 400 | `bad_json` / `schema_violation` | parse/validation failure (field path only) |
| 409 | `taxonomy_mismatch` | request `taxonomy_version` ≠ served. Equilibrium must re-pin, never silently mix |
| 413 | `too_large` | body > 1 MiB, or missing/invalid Content-Length, or > 100 msgs |
| 422 | `insufficient_context` | `/v1/discourse` window below every requested label's minimum |
| 429 | `busy` (retryable) | fork-concurrency semaphore full past queue deadline (§5.4) |
| 503 | `base_drift` / `not_ready` | base revision changed (fatal, process exits after reply) / still booting |
| 504 | `tick_budget` (retryable=false) | batch exceeded `max_ticks` or the wall budget. The branch is dropped and no partial labels are returned |

### 4.5 Degraded mode

When the sidecar is down, 503 or version-mismatched, Equilibrium runs **structure-only** (its own §16.7: reply/reaction graph, initiation asymmetry, latency/dropout, clusters, report waves). Ocelot's role is only to fail closed: no partial label sets, and `/healthz` reports false. Inside the sidecar, a single label family whose rule faults is reported `{"value":null,"status":"error"}`, and the rest of the batch is returned. A batch is never retried on the base.

---

## 5. Frozen fork-per-batch service mode

### 5.1 Target design (API in uncommitted main-checkout `py.rs:1479-1652`; not on 8bac3e90)

```python
base = PySubstrate(); boot_core(base); equilibrium_classify.load_pack(base, SEED_DIR)
snap = base.snapshot()                 # SubstrateSnapshot, Send+Sync, shared_graph_pages
rev0 = snap.source_revision
# per batch, in a worker thread:
branch = snap.fork()                   # independent PySubstrate, COW over shared pages
out = equilibrium_classify.classify(branch, req)
del branch                             # drop: all content-bearing pages die with it
assert snap.source_revision == rev0    # every batch; exit on violation (503 base_drift)
```

Per §16.7, `snapshot()` is refused while an agent thread, Python hooks or a Python memory faculty is attached. The sidecar therefore never calls `start_agent` (py.rs:1475 refuses multiple live writers anyway) and attaches no hooks. **COW results cited by Equilibrium:** 8–13× lower wave latency and 16–23× less live allocation than eager copy at 10k–50k nodes with fanout 4–16 (`COW_HIGH_CHURN_LIFECYCLE_V1_RESULTS`), and concurrent forks from one snapshot beating serial forks at ≥10k nodes (`COW_SNAPSHOT_CONCURRENT_FORK_V1_RESULTS`: 1.51× at 10,771 nodes/fanout 4 and 2.77× at fanout 16, but 0.40–0.65× at 771 nodes). Both docs exist only as untracked files in the main checkout, not at 8bac3e90; the high-churn table there reads 7.66–13.16× latency and 16.04–22.75× allocation. They are descriptive and single-host, and must be re-measured with the seed pack loaded before they size anything (WI-12).

### 5.2 Content isolation

* Content touches only `branch`. The base is constructed before the socket opens and is never passed to `ingest`. Only `classify(branch, …)` exists as a code path.
* No checkpoints: the sidecar never calls persistence (`substrate/persistence.py`), never writes under `seeds/acquired/`, and runs with a read-only seed dir (container `--read-only` with tmpfs `/tmp` only). No `domains.teach.teach` at runtime.
* Logs hold counts, latencies, rule_ids and error codes only. Request bodies are not logged, even at debug.

### 5.3 Base-unchanged assertion (Phase 9 exit: unchanged after 10k messages)

* Cheap check per batch: `source_revision` (target API) or, in the fallback, `(node_count, edge_count)` (py.rs:2233, :2380).
* Strong check at boot, every 1,000 batches, and on `/healthz` refresh: `sha256(canonical_bytes(graph_to_dict(base)))` (py.rs:8421, `canonical_bytes` pattern from `services/p5_r0_evaluator/canonical.py`) compared to the boot digest.
* Exit test (WI-11): replay 10,000 synthetic messages (golden generator, §8), 100 per batch, mixed classify/discourse. Assert strong-digest equality before vs after and zero files written outside tmpfs (inotify/`find -newer`).

### 5.4 Concurrency model

* There is one base per process. With the target API, a bounded pool of N fork workers (N = cores, configurable) sits behind a semaphore, with a queue deadline of 2 s and then 429 `busy`. Branches never share mutable state. The GIL is released inside Rust tick (to be confirmed with the fork API).
* Fallback (§5.5): the substrate is not `Send` on this commit, so concurrency is **process-level** (M pre-forked worker processes behind the HTTP front), and each worker uses one branch at a time.

### 5.5 Fallback on 8bac3e90 (no snapshot/fork)

| option | mechanism | isolation | expected cost |
|---|---|---|---|
| **F1 frozen-reload** (default fallback) | hold `base_dict = graph_to_dict(base)` once. Per batch: new `PySubstrate`, `graph_from_dict(base_dict)` (py.rs:8428), classify, drop | strong (base object never touched) | O(graph) eager copy per batch. This is the "eager copy" baseline COW is claimed to beat 8–13×. Must be measured |
| F2 os-fork worker | pre-booted parent; `os.fork()` per batch, child classifies, returns JSON over a pipe, exits | strong (OS COW, child memory discarded) | fork ≈ page-table copy. Safe only if no Rust/rayon threads are live in the parent at fork time (must be verified). Memory is shared until written |
| F3 delete-on-return | mutate base, then delete minted nodes | **rejected**: content transits the base, violating §16.7 | — |

`/v1/info.mode` reports which mode is running. Equilibrium's §16.7 throughput risk is evaluated against whichever mode ships.

### 5.6 Memory budget (384 MB cap, Equilibrium risk 2)

The budget is base graph (boot_core + pack) + per-branch delta × concurrency + Python/HTTP overhead ≤ 384 MB RSS. The pack target is ≤ 5k nodes / 20k edges beyond boot_core. A per-branch delta for 100 msgs is ~100 × (≈30 tokens + spans) ≈ 5k nodes. The F1 fallback holds base + base_dict + N full copies, which is the likely budget breaker, so F1 concurrency may be 1–2. All of these are estimates. WI-12 measures RSS with the pack loaded.

---

## 6. Throughput (Equilibrium risk 1)

The target is ≈4,000 msgs/s pool-wide in backfill (40 req/s × 100 msgs). Nothing here is measured. Per-batch cost = fork (or reload) + ingest + ticks to quiescence + read-out. The PREREG registers the measurement protocol and an explicit prediction that F1 will **not** reach 4,000 msgs/s on one host. Throughput is sized from the measurement, and Equilibrium's cheap gate (thread.analyze only on triggers) reduces `/v1/discourse` load.

---

## 7. Data discipline

* Seed-pack authoring (lexicon cue selection, rule wording, codebook prototypes) may consult **only** the pre-registered train months of the Equilibrium §16.9 corpus. **The split is stated in UTC half-open bounds** (the Equilibrium T7 prereg found exporter-local dates are what produced the §16.9 counts, so date-only bounds are ambiguous):
  * train `[2026-01-01T00:00:00Z, 2026-08-01T00:00:00Z)`
  * validation `[2026-08-01T00:00:00Z, 2026-09-01T00:00:00Z)`, sealed
  * test `[2026-09-01T00:00:00Z, 2026-10-02T00:00:00Z)`, sealed
* **Enforcement:** the authoring adapter (`tools/equilibrium_seed_authoring.py`, WI-3, Equilibrium-side corpus access only) applies the date filter *before* any row reaches the author's view and refuses rows with a missing or unparseable UTC timestamp. On completion it writes an authoring receipt `{split_bounds, rows_seen, max_ts_seen, min_ts_seen, filter_sha256, corpus_manifest_sha256, seed_pack_sha256}` with **no content**. The receipt is checked in next to the pack. The PREREG requires `max_ts_seen < 2026-08-01T00:00:00Z`.
* Ocelot never stores corpus text. Seeds contain only generalised cue lexemes from public lexical resources or author-written, never verbatim messages. This design was written without reading the corpus.
* Validation is opened once for v0 tuning decisions *registered in advance* in the PREREG. Test is opened once for the v0 → `enabled` decision.

---

## 8. Golden tests (synthetic, hand-written)

These live at `tests/fixtures/equilibrium_golden_v0.jsonl` with test `tests/test_equilibrium_golden.py`, run under `OZMA_NO_LLM=1`. Every line is one case. All text is hand-written, with pseudonymous refs and no corpus derivation:

```json
{"case":"sealion_basic","endpoint":"discourse","messages":[
  {"id":"m1","author_ref":"actor_a","text":"Can you show a source for that?","reply_to":null},
  {"id":"m2","author_ref":"expert_e","text":"Sure: here is the doc https://example.org/spec and the relevant line.","reply_to":"m1"},
  {"id":"m3","author_ref":"actor_a","text":"I'm just asking for any evidence at all, can you provide it?","reply_to":"m2"}],
 "expect":{"patterns":[{"label":"pat.sealioning","actor_ref":"actor_a","constituted_by":["m1","m2","m3"]}],
           "messages":{"m2":{"substantive_markers":["link","evidence"]}}},
 "expect_rule_ids_prefix":["eq.pat.sealioning."]}
{"case":"sealion_negative_learner","endpoint":"discourse","messages":[
  {"id":"m1","author_ref":"member_101","text":"How do I fix this error?","reply_to":null},
  {"id":"m2","author_ref":"expert_e","text":"Run the install step first, then retry.","reply_to":"m1"},
  {"id":"m3","author_ref":"member_101","text":"I ran the install step but it still fails, what next?","reply_to":"m2"}],
 "expect":{"patterns":[]}}
```

v0 coverage: ≥ 4 positive and ≥ 4 near-miss negatives per v0 pattern label (learner follow-up, legitimate refinement, terse register, non-native phrasing), ≥ 3 cases per message-label value, emoji reaction-act cases, error-model cases (oversize, mismatch, insufficient context), and the 10k-message base-unchanged replay generated by templating these cases. The goldens test *rule behaviour*, not validity. Validity is the PREREG's job.

---

## 9. Work items

Effort is in person-days for one engineer familiar with the seed DSL. "Reuse" = existing Ocelot capability. "New" = new capability.

| WI | item | est. (pd) | depends on | reuse / new | risk |
|---|---|---|---|---|---|
| WI-0 | Land the COW `snapshot()`/`fork()` API + COW results docs (present as uncommitted work in the main checkout, py.rs:1479-1652) as a commit, then rebase this branch on it | 0.5 (owner commits existing work) | — | reuse (owner's in-flight work) | **Medium**: blocks §5.1 until committed; F1/F2 fallbacks cover it |
| WI-1 | Token/type vocabulary seed `equilibrium_tokens` + boundary tokenisers | 2 | — | reuse speech_act_classify, discourse_argument | low |
| WI-2 | Lexicon seeds via `teach` builder script | 3 | WI-1, WI-3 receipt | reuse `domains.teach` | medium: register coverage (risk 3) |
| WI-3 | Authoring adapter with UTC split filter + receipt (Equilibrium-side) | 1.5 | — | new | medium: leakage if bypassed |
| WI-4 | msg-layer rules + Valence/Hostility codebooks | 5 | WI-1, WI-2 | reuse ShapeDecode / discourse_coherence codebook pattern | medium: shapes-not-numbers compliance |
| WI-5 | Emoji seed (Unicode senses table, reaction-act rules, name-proposal read-out) | 3 | WI-4 | new (CLDR/Kralj Novak import) | low-medium: licence of sentiment table (OQ-5) |
| WI-6 | Pattern rules v0: sealioning, goalpost shifting (+ disabled stubs for the other five) | 6 | WI-4 | reuse coherence_between, centrality; new focus-slot overlap rule | **High**: pattern-label validity |
| WI-7 | `domains/equilibrium_classify.py` adapter | 2 | WI-1 | reuse corpus_world shape | low (CLAUDE.md audit) |
| WI-8 | Pack digest, label-status seed, provenance envelope | 1 | WI-1..6 | reuse boot_all digest pattern | low |
| WI-9 | HTTP sidecar (/v1/classify, /v1/discourse, /v1/info, /healthz, error model) | 3 | WI-7, WI-8 | reuse mock_server + p5_r0_evaluator hardening | low |
| WI-10 | Frozen mode: F1 reload (+ F2 os-fork spike); swap to fork API when WI-0 lands | 3 (F1+F2) / +1 swap | WI-9, WI-0 | new | medium: F2 thread-safety at fork |
| WI-11 | Golden set + 10k base-unchanged replay test | 3 | WI-6, WI-10 | new | low |
| WI-12 | Throughput + RSS measurement (PREREG §M) | 2 | WI-10 | reuse scale_audit_snapshot (py.rs:2294) for counts | **High**: §16.7 risk 1 (4,000 msgs/s) and 384 MB |
| WI-13 | Container image (`ocelot-classifier:<taxonomy-version>`, read-only fs, loopback publish, OZMA_NO_LLM=1) | 1 | WI-9 | reuse p5_r0_evaluator Dockerfile | low |
| WI-14 | Validation/test evaluation per PREREG (needs Equilibrium annotators) | 4 (Ocelot side) | WI-6, WI-12, human labels | reuse comparative_release_gate scorecard | **High**: annotation availability; κ |
| | **Total (WI-0 = committing the existing COW work)** | **≈ 40** | | | |

Critical path: WI-1 → WI-4 → WI-6 → WI-11 → WI-14, ≈ 20 pd. WI-0/WI-10/WI-12 run in parallel and gate the throughput sign-off.

---

## 10. Open questions

1. **OQ-1 Status vocabulary.** The brief asks for `disabled/shadow/enabled`, while Equilibrium's `label_gates` uses `ungated/audited/enabled`. This design treats them as two layers (pack vs guild gate, §2.3). Should Equilibrium adopt `shadow` as an alias for `ungated`, or should the vocabularies stay separate?
2. **OQ-2 When will the COW fork API be committed?** It exists as uncommitted work in the main checkout (py.rs:1479-1652 plus untracked COW_*_RESULTS_20261001 docs). This branch needs it on a commit before WI-10 can swap off the fallback.
3. **OQ-3 `confidence`.** Shapes-not-numbers forbids invented probabilities. Will Equilibrium accept `confidence ∈ {exact, partial, weak}` (ShapeDecode fit) in place of a float?
4. **OQ-4 Placement.** This doc sits in `docs/research/psychology_affect/` (the nearest subject: abusive-dynamics and developmental-safety lines). Should Equilibrium get its own `docs/research/equilibrium/` folder? That requires a new row in `docs/research/INDEX.md`.
5. **OQ-5 Emoji sentiment licence.** Kralj Novak et al. emoji sentiment data is, to my knowledge, CC BY-SA 4.0 (not verified here; no network lookup was made), which may impose share-alike on the seed JSON. Should the pack use a derived ordinal sense table with only attribution, or CLDR only?
6. **OQ-6 Auth.** A loopback-only unauthenticated sidecar is acceptable for the reference deployment. Is there any deployment where Equilibrium's worker and the sidecar are on different hosts? If so, auth (p5_r0_evaluator `auth.py` pattern) must be added before that.
7. **OQ-7 Non-English.** v0 lexicons are English-only, and `_detect_language` (language_world.py:80) could tag non-Latin script messages. Should non-English messages return `insufficient_context` / `unknown`, or labels in shadow with a `lang` stratum flag? This design proposes `unknown` + flag.
8. **OQ-8 Window bounds.** The 50-msg / 72 h pattern windows are design guesses. Should they be fixed on train data before validation opens (PREREG §P)?
9. **OQ-9 Custom-emoji proposals.** Is a `comprehend_text` name-proposal acceptable as an Equilibrium-side candidate, or should custom senses come purely from Equilibrium's co-occurrence learner?

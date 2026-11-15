# Research helper evaluation pilot

This is a deterministic fixture and scoring aid for a proposed pilot. It does
not call a model, establish comparative benefit, or stand in for the separate
prospective preregistration described in `docs/research/research_assistant/EVALUATION_DESIGN.md`.

The fixtures include marked synthetic material for planted contradictions.
They are burned pilot cases and must not be reused as held-out confirmation.
The fixture keys are intentionally stored here for humans preparing/scoring a
pilot; keep them inaccessible to the assistant during answer generation.

Run `python -m evaluation.research_assistant.harness validate` to check fixture
structure and reopenable source hashes. Supply a JSON score file to `score`
for a descriptive report. The harness reports arm/task denominators and missing
runs. It does not compute significance tests or infer benefit.

Score records use one row per independently run task and arm. Human graders
should be blinded to arm identity and use integer 0–2 scores for each rubric
dimension:

| Dimension | 0 | 1 | 2 |
| --- | --- | --- | --- |
| `source_claim_accuracy` | Key claims materially misstate or exceed sources | Mostly right with a material scope/source omission | All material claims accurately scoped to sources or marked as inference |
| `unsupported_assertions` | Material unsupported assertions | One material or several minor unsupported assertions | None, or only immaterial unsupported detail |
| `contradiction_recall` | Misses fixture counterevidence | Mentions it but fails to explain its force/scope | Identifies and correctly bounds its effect |
| `limitation_recall` | Misses key limitations | Mentions some but omits a material limitation | Includes all answer-key limitations relevant to the prompt |
| `citation_reopenability` | Cited evidence cannot be reopened | Some cited evidence reopens | All material citations reopen at the specified locator |
| `citation_hash_match` | No cited source matches its pinned hash | Partial match or unresolved mismatch | All material cited sources match pinned hashes |
| `completion` | No usable answer | Partial answer or missing a required part | Directly answers all material parts |

Unsupported assertions is reverse scored (2 is best). Graders must preserve
short rationales alongside their score file in the study record. Operational
fields are recorded, not folded into a quality composite.

A three-case feasibility shakedown using Luna agents is archived in
[`pilot_20261114/RUN.md`](pilot_20261114/RUN.md). It was not preregistered or
adequately controlled and does not establish effectiveness.

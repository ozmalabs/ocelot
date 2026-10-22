# Linear P12 preregistration

**Frozen:** 2026-10-22, commit `03381c8dec44f9d2e52539bd0213064dc2e9e7e3`.
No held-out records have been read. The runner and analyzer self-checks pass;
the one-record-per-arm development adapter completed all four social arms,
all three safety controls, and explanation rebuild plus both redaction controls.
Development social own-trial success was 100% in the pooled social arms and
100% in reward-only (0-point gain); this is a descriptive development result,
not a held-out estimate. The registered 20-point advantage threshold is
unchanged.

## Frozen artifacts and provenance

| Artifact | SHA-256 |
|---|---|
| Git commit | `03381c8dec44f9d2e52539bd0213064dc2e9e7e3` |
| Runner `linear_p12_v1.py` | `7b78c4f7db522c2baff4b631d34b89aeb7f9f01f4d3eca946deee079e6374181` |
| Analyzer `analyze_linear_p12_v1.py` | `c29518f56fb29294ec252c3d6ddf975be7e3cf026ea26316551b41638d0e163e` |
| PMB harness | `e59b6f962e87c9afa352460809d3a583d235fb9f917dfcff55c237c1bbc032ac` |
| Boot profiles | `294a29bd44eb3a3f7c02319d5af05f59ca033107a8f27215c88c37fdb3588a40` |
| Imitation seed | `fb9cc0ec1ec2eea10973558217e6110d7d6724084bcb566e122f00a7125a0204` |
| Social process seed | `309fbf990b208511bcca56ab812d8d02bd494b283eb0f660839ea2f785cba890` |
| Explanation seed | `25bbf0ee54db9113dec4900b00939a884c0372f788e5e442f9c305a0199b86c4` |
| Instruction-understanding seed | `dd1280a333466a5dc8c8b465b556f31bee7bd6bcf285e17886f29d0e67057539` |
| Runner source bundle | `10693dad22498f192100a9aa60c9bfc6f02bef3dacde98893f302e2a1babf24b` |
| Native engine source bundle | `4326812f782ec8e324bdccc0c11d5424d3ad3a71f8dd0b723fb20cf4cee434f9` |
| Native engine binary | `b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5` |

Runtime is Python `3.13.5`. The source bundle covers the runner/analyzer,
social, imitation and explanation seed generators and data, instruction seed,
PMB harness/scorecard and cognition-on profile. The engine bundle covers the
Cargo manifest/lockfile and Rust graph, checker, rule, term, process-algebra,
Python-binding, and reflex/action-authorization implementation files.

## Design, arms, and fixed allocation

Every social-acquisition arm receives the same paired increment world, the
same two held `ProcessSchema` models (`request/repair` maps to `+1`,
`request/restore` maps to `+2`), eight declared evidence opportunities, and a
per-agent ThinkingBudget of 12 units. The target is the external world effect
`+1`; target state/goal and evaluator truth are not inserted into learner
nodes. The common model bank is identical in each paired arm. Each trial is a
fresh graph. Track I and P12 seed profiles are explicit in the runner; this is
the minimal PMB evaluation profile, not a full cognition-on conversational
session.

The four arms are:

- `observation`: one complete, incidental witnessed request/repair episode,
  without teacher-intent markers.
- `demonstration`: one directed action sequence with a verified body/frame
  map, detached native effect validation and funded adoption.
- `instruction`: one parsed instruction with native instruction
  interpretation, model matching and separate funded effect validation.
- `reward_only`: two world-scheduled own probes through the native P5 action
  authorization gate; only scalar rewarded/unrewarded receipts are exposed to
  graph learning. A positive-feedback candidate requires separate funded
  native effect validation. Its two evidence probes plus the scored own trial
  use three world action calls; the other treatment arms use one scored call.
  This work difference is retained and reported, not normalized away.

The shared model bank ensures equal primitive/model access. Social episodes,
demonstrations, instructions and reward receipts are the registered evidence
treatments. The treatment action sequence in a demonstration is direct
observational evidence; the hidden evaluator target/goal is absent from the
agent. Action selection for the scored trial follows graph-produced adopted
schemas. Python only installs world events, runs native ProcessApply and the
P5-gated action sink, then scores receipts.

Held-out social allocation is 200 paired worlds per arm: 800 records total.
Seeds start at `12,100,000`. There are 100 shuffled-sequence, 100 missing or
partial-episode, and 100 body/frame-mismatch controls, from the `12,105,000`
block. These control demonstrations must not adopt or ground a process.

The explanation panel uses 200 fresh receiver graphs and world instances,
from the `12,108,000` block. A source graph creates and self-monitors the
English explanation “Mary loves John.” The receiver receives that explanation,
its ordinary parsed semantic frame and the shared public primitive vocabulary;
it receives no source schema, source ID, source AST, fingerprint, or original
process expression. Each receiver's rebuilt process is checked with three
native ProcessApply probes. Two 100-instance redaction controls start at
`12,109,000`: the transport envelope is augmented with source-ID fields or
source-expression fields, and the adapter's allow-list must remove them before
constructing receiver graph nodes. All 200 receiver instances exercise the
same single primitive effect; results do not establish general explanation
composition or open-domain language understanding.

The held-out draw contains 1,500 records: 800 social primary records, 300
social safety controls, 200 primary receiver instances, and 200 redaction
controls. The fixed limits are 24 graph ticks, 1,000 rule steps per tick,
12 ThinkingBudget units per agent, eight declared evidence opportunities,
three native effect probes per validation, and at most three world action
calls. Report actual calls, boot time, graph-node and serialized graph-size
growth, budget debits/remainings, evidence exposure, verification/action
receipt IDs, and exact outcomes per record.

## Frozen criteria

The primary social criterion is pooled observation, demonstration and
instruction own-trial success at least 20 percentage points above reward-only.
An absent or incomplete arm, unequal paired world/model-access hash, agent
input audit failure, false own grounding, unverified adoption, or invalid
allocation makes the comparison `INVALID`. A valid gain below 20 points is
`FAIL`; it will not be retuned after the draw.

Each of the three social controls must have zero false adoption, zero own-trial
success, and zero remaining unverified candidates. The overall panel must
have zero false own grounding and zero adopted schemas without a matching
verified receipt.

The rebuild criterion is at least 95% held-out exact effect agreement and at
least 95% native schema adoption, with zero source leakage. Redaction controls
must demonstrate the expected removed field set and retain exact effect
agreement. Human parity is unavailable because no protocol-matched human
baseline is registered.

Development outcomes are retained only as adapter validation. There is no
threshold adjustment, seed reuse after a held-out failure, or claim of a
complete capability level from this bounded mechanism panel.

## Commands

Run both self-checks and the development adapters before the draw:

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/process_mastery/linear_p12_v1.py --self-check --split development --output /tmp/linear-p12-selfcheck.json
.venv/bin/python evaluation/process_mastery/analyze_linear_p12_v1.py --self-check
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/process_mastery/linear_p12_v1.py --split development --output /tmp/linear-p12-development.json
.venv/bin/python evaluation/process_mastery/analyze_linear_p12_v1.py /tmp/linear-p12-development.json > /tmp/linear-p12-development-analysis.json
```

Registered held-out commands:

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/process_mastery/linear_p12_v1.py --split heldout --output /tmp/linear-p12-heldout.json
.venv/bin/python evaluation/process_mastery/analyze_linear_p12_v1.py /tmp/linear-p12-heldout.json > /tmp/linear-p12-heldout-analysis.json
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_imitation_migrated.py tests/test_social_process.py tests/test_process_explain_rebuild.py tests/test_cognition_profile_integration.py -q -p no:cacheprovider
```

Archive scorecard and analysis outside git. Verify runtime provenance matches
this table before interpreting the draw. A changed hash, missing adapter,
nonzero safety count, missing arm, pairing mismatch, or redaction leak
invalidates the draw; do not rerun on these held-out seeds after any correction.

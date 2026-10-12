# Self-report route causal intervention v1

Date: 2026-09-27

## Question

Does preventing the wordplay faculty from classifying `organisation` as a coinage restore the previous self-report route? This is a one-worker diagnostic intervention on the isolated snapshot `/tmp/ocelot_dimension_frame_snapshot_20260927`; it does not modify the workspace source.

## Observation

**Scope correction:** this diagnostic snapshot omitted `data/slabs` and the `scripts/collapse_engine.py` action dependency. The [v1.2 full-environment panel](SUBSTRATE_SELF_REPORT_ROUTE_CONTRAST_V1_2_RESULTS_20260927.md) supersedes its route interpretation; do not infer that fully provisioned requests are intercepted by wordplay or that handled action execution failed.

On the captured source, `wordplay._known("organisation")` returns false, `wordplay._pos("organisation")` returns an empty list, and `detect_coinage("organisation")` therefore returns an affix analysis (`-ation`, stem `organis`, `stem_real=false`). The normal comprehension path short-circuits to a statement with `dispatch.path="wordplay"` before instruction parsing.

In the intervention, only the in-process `find_coinage` result was suppressed for text containing `organisation`; all other calls delegated to the original function. The same request then reached an instruction comprehension, showing that coinage interception is a necessary proximal cause of the observed interpretation. It still did not reach self-report: the reply became `I don't know 'report' — what does it mean?`, the route was `ask_back`, and the instruction outcome was `handled`.

This establishes at least two sequential blockers in this utterance: (1) wordplay preemption prevents the instruction parse; (2) after that preemption is removed, the current parser/action route does not recognize or dispatch the leading `report` as a held self-account request. It does not establish that the old source behaved differently for either subdecision: the earlier successful source snapshot was not recovered. It also does not test other phrasings or establish why `organisation` is absent from the Wiktionary reference adapter.

Full boot still loaded 731 seed manifests and reported the same 11 failures. Since the intervention changed the interpretation while leaving the boot intact, the failed seeds are not sufficient to explain the first blocker. They might still contribute to the second blocker; this experiment did not intervene on seed availability.

## Implications and next work

Split the regression work into independently gated questions:

1. Establish an arbitration rule for instruction-shaped utterances containing an OOV content word. Test a contrast set where the same suffix-bearing token appears in statements, questions, and instructions; preserve ordinary wordplay on genuine coinage prompts.
2. Trace `report` through token recognition, typed instruction evidence, held-action selection, and account dispatch. Compare with known self-account verbs and paraphrases, without assuming a lexical fallback is the right repair.
3. Repair or explicitly quarantine the 11 malformed seed manifests, then measure whether each changes boot graph and route outcomes.
4. Recover the prior successful source only if an immutable artifact exists; otherwise state that source-to-source causal attribution is unavailable.
5. Rerun the full route panel after any implementation change, then resume scale/locality measurements only after the route is restored and output coverage is separately gated.

This result supersedes the previous plan statement that the changed wordplay/self-report arbitration is the only unresolved proximal boundary: the intervention shows wordplay is the first blocker, but removing it exposes another dispatch gap.

## Reproduction

Run the following in the isolated snapshot with its checked-in Python/native dependencies. It performs one fresh full boot and monkeypatches only `domains.wordplay.find_coinage` in-process:

```python
import domains.wordplay as wp
original = wp.find_coinage
wp.find_coinage = lambda text: None if "organisation" in (text or "").lower() else original(text)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
adapter = WorldAdapter(seeds=())
boot = load_all_seeds(adapter)
reply = adapter.converse("report your organisation", speech_act="instruction", speaker="alice")
```

Snapshot source hashes: `wordplay.py` `7255fb00b18ab4067c558ec9a9e16e2af82fca24b77be12651dc1e4fc13b9b60`; `comprehend_text.py` `dd9b3594f1b0daf1394f2c3bfeac991a0326043e67cec164660066c7e7268022`; `world_adapter.py` `91899b77d277b5571408b79a24a8237afff1f484b87239d87c757001f4782fa6`.

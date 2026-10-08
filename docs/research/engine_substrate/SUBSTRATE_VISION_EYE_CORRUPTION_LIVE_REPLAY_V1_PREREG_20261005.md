# Vision-eye corruption live replay v1 preregistration

## Question and boundary

Does the frozen-weight analytical corruption result reproduce when the same binary masks pass through the live substrate's phase-0 graph rules? This is a source-locked engine/readout parity follow-up to the post-hoc v1.2 replay, not an independent robustness replication: it uses the same six seeds, two morphologies, held-out masks, and deterministic corruption doses.

## Design

Rebuild the v2.1 nine-site map in 12 fresh processes, six seeds per morphology, with identical training conditions, freeze point, and 75 clean probes. Then apply the five existing corruption conditions to each held-out probe: 25/50/75% active-pixel dropout and background additions at 25/50% of original mask area. Reuse the exact SHA-256-derived mask seed `phase0-v2.1|seed|morphology|probe_index|condition` from the offline replay. Feed one mask to the live graph by updating bursting pixels, step the Eye, run native graph rules, and read the native WUnit activations/winner attributes. Record all pre-corruption and post-corruption learned weights.

## Gates

Lock protocol, runner, analyzer, v2.1 capture/analysis, offline corruption report, engine/native binary and source dependencies. Require 12 distinct workers, exact six-seed pairing, stable inputs, exact exposures and masks, clean readback parity, matching learned weights to the v2.1 capture, identical offline/live corruption mask digests, per-unit native activation parity with the frozen-weight calculation, native winner membership in the exact-max set, weight preservation after the freeze point, and 288 held-out probes per morphology/condition.

## Claim limits

This verifies selected frozen-weight corrupted inputs through the Rust rule/scheduler path. It does not provide an independent sample of corruption draws, measure online adaptation, estimate natural visual robustness, or establish feature/semantic recognition. Keep tied winner outcomes explicit; do not silently resolve them as correct.

## Reproduction

Run `python3 evaluation/substrate_capability/vision_eye_corruption_live_replay_v1.py --lock`, then run it without arguments, followed by `python3 evaluation/substrate_capability/analyze_vision_eye_corruption_live_replay_v1.py`.

# Current-source amendment: edge-attribute identity composer

Date: 2026-10-03

The October 2 edge-attribute identity result records a useful bounded repair,
but its source lock no longer matches current `domains/edit_ops.py`,
`domains/seed_registry.py`, several Rust engine sources, or the loaded native
binary. The native build itself passes `build_is_stale` with no stale
components. This amendment repeats the existing v1 conditions under a fresh
source lock; it does not change task cases, candidate generation, cue text,
workers, outcomes, or interpretation gates.

The current-source runner includes the original protocol, the original
bidirectional edge-identity helper and protocol, the new amendment, all source
and seed dependencies, its analyzer, and the loaded native binary in its lock.
It preserves the staged order-then-held-out workflow. Historical v1 captures
remain untouched. Any changed proposal, false suppression, abstention, or
utility is reported as current behavior rather than adjusted after scoring.

This remains a prompted edit-space test: target, cues, examples, and oracle are
supplied. It does not measure raw residual-to-cue grounding or autonomous
operator invention.

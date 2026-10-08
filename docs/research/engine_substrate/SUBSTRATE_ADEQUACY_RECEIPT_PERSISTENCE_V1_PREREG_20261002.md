# Adequacy receipt persistence and replay v1

## Question

Does an accepted strict-mode receipt persist a learned code-write shape that a
separate fresh process can reload, and is replay of the same receipt
idempotent after that reload?

## Frozen procedure

- Use the `square` source and request from adequacy receipt adoption v1.
- For each of three repetitions, run a writer subprocess with a full seed boot.
  Generate an accepted independent-adequacy receipt, teach with strict receipt
  enforcement, and direct persistence to a new parent-owned temporary seed
  directory. Record the exact receipt and written manifest digests.
- In a distinct reader subprocess, boot a bare `WorldAdapter` against an
  overlay of the complete seed corpus, replacing only
  `code_write_constructions.json` with the temporary persisted manifest.
  Require one `taught_square` node whose attributes match the writer's capture.
- Replay the same accepted receipt and candidate in the reader process. The
  expected behavior is successful no-op adoption: one held shape remains,
  codebook epoch does not advance, and `teach()` reports the existing durable
  node rather than appending another seed node.
- Lock runner, analyzer, protocol, Python/native/Rust source, all flat and
  generated seed manifests, and extension hashes before and after each
  subprocess. Keep the temporary
  manifest isolated and delete it after the capture.
- Pass only if all three writer and reader pairs persist, restore, and replay
  idempotently, with exact attribute parity and no source drift.

## Interpretation limits

This is persistence/replay mechanics for one authored arithmetic function.
It does not establish label authenticity, receipt expiration/revocation,
multi-candidate conflict handling, learning quality, or transfer prevalence.
Replay is deliberately treated as reusable evidence bound to the same
candidate, not as a one-shot token. Full-seed writer boot and temporary disk
I/O are included in wall measurements; the source label oracle remains
harness-supplied.

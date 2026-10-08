# Thoughtexperiment attribute-site active choice v1 — preregistration

## Question

When a cue omits ordered site direction and the composer abstains, can the harness expose competing site edits as isolated hypotheses and can the substrate's active-query selector choose a probe that distinguishes the useful repair before oracle labels are available?

## Candidate fixture

Use the fresh `classify_meter_delta` fixture and four independent workers. On each worker, first replay the direction-omitted cue and record the ordinary composer result. Then host-side generic enumeration (`_default_candidates`) supplies exactly three evaluated hypotheses for this bounded test: the unmodified fault, `swap_term_leaf:bad_score->good_score`, and `swap_term_leaf:good_score->bad_score`. Record the full candidate inventory and the time spent attempting composition and enumerating the alternatives. The hypotheses and their source-side construction are explicit; this experiment does not claim autonomous candidate generation.

## Oracle-blind selection

For each backend (snapshot CoW, full copy) and alias rate (0%, 50%, 90%, 99%), create a fixed 100-input pool using the existing v1 generator. Evaluate each supplied hypothesis on each input in a fresh isolated branch with one native closure. The native-Term `select_discriminating_input` chooses the maximum-entropy input; freeze orders, predictions, source hashes, candidate identities, and random-probe controls before running the scorer. No expected labels are present in the order-stage records.

## Oracle and held-outs

After order files are frozen, score the selected and seeded-random probes with the fixture oracle (`HOT` iff `good_score > 0`). The forward site is the only expected surviving hypothesis. Also score positive, negative, zero, and additional mixed held-outs for fault, forward, and reverse hypotheses. Check fixed points, branch receipts, primary revision preservation, backend parity, and source stability.

## Pass conditions and limits

Pass requires all 32 backend/alias conditions to produce a one-bit discriminator; post-freeze oracle scoring must retain only the forward hypothesis in every condition; the forward proposal must pass all held-outs while the fault and reverse candidate fail at least one nonzero held-out per worker; and all isolation, fixed-point, parity, and source checks must pass. Report candidate enumeration, composition, branch fork, patch, closure, selector, and held-out costs separately. This is a bounded candidate-selection result. It does not show that the substrate invents the edit vocabulary, establishes probe-domain completeness, or verifies a potentially dishonest oracle.

## Reproduction

Run the locked runner with `--lock`, `--orders`, and `--score` in that order, then run the independent analyzer. Do not score oracle labels until the order artifact has been written and hashed.

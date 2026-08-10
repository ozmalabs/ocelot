# Iteration 35 — wire the top-down AxS (analysis-by-synthesis) node into the graph

> User compass (iter-34): "polyglots have a richer graph" — richer is monotone.
> The richness lever is proven monotone through iter-34
> (`docs/agent_loop_iteration34_enriched_graph.md`): three genuinely orthogonal
> bottom-up cues (FFT-ear, formant-relation, manner/voicing), each its OWN node in
> the variadic Bayes product, WIDENED both the combination win (0.590 > iter-33
> 0.567 at n=8) and the real-vs-shuffle margin (+0.021 clean vs iter-33 −0.002).
> iter-34 SKIPPED the AxS forward-model node because the FULL order-n AxS has a
> convergence threshold (a fit). iter-35 wires AxS as a **single-pass, no-fit**
> likelihood node — the biggest unwired orthogonal cue, top-down/generative by
> construction (the dual stream), orthogonal to ALL the bottom-up cues.
> Written INCREMENTALLY; runs captured to `/tmp`; `PYTHONUNBUFFERED=1`. NO commit.

## The fix for "AxS needs a fit" — a single-pass synth-error likelihood node

iter-34's reason for skipping AxS was correct only for the FULL order-n AxS (the
co-refining loop with a convergence threshold = a fit). The **single-pass** AxS is
no-fit:

- The agent's OWNED forward model: per-word **mean A1-patch trajectory** of the
  TRAIN-speaker exemplars (LOSO-clean — the held voice never enters its own model).
  An exemplar average. No fit, no convergence, no threshold, no learned weight.
- For sign `s` and candidate word `w`:
  `synth_error(s, w) = DtwTo(features(s), synth(w))` — computed by the **graph
  `DtwTo` Term** (the iter-16 Rust primitive), evaluated natively.
- `P_axs(w | s)` = softmax over candidates of the NEGATIVE synth-errors, scaled by
  the node's OWN median candidate distance — the IDENTICAL
  `likelihood_from_distances` softmax-by-own-median every other channel uses.
- One pass: one DtwTo per candidate, one softmax. No iteration, no convergence
  loop, no global weight, no select-best.

This is the faithful instance↔model A1-space comparison the iter-16 AxS accept
script found best (`scripts/analysis_by_synthesis_accept.py`): comparing in the
forward model's native A1 representation avoids the natural-vs-synthetic
resynthesis domain gap (the brain inverts the internal forward model; it does not
literally replay sound). It is the same forward model
(`scripts/analysis_by_synthesis_accept.py::fwd_traj`), the same `DtwTo` Term, the
same `recognition_graph` argmax — just packaged as ONE node in the iter-34 product
instead of a standalone argmax recogniser.

## (1) The AxS node wired — auditable: no convergence-fit, no weight, combine-all

The AxS node is channel **24** in the iter-34 23-channel product
(20 gammatone + FFT-ear + formant-relation + manner/voicing + **AxS**), all fed
into the SAME `predict_many_settings_term`.

**Wiring** (`scripts/enriched_hvpt_accept.py`):
- `utterance_a1_trajectory(x, fs)` — ingest one utterance into a FRESH substrate,
  read its A1-patch trajectory (frames × patches). The word-distinct building block.
- `_axs_word_model(train_trajs, train_words)` — per-word mean trajectory (exemplar
  average; no fit).
- `axs_query_likelihood(heard_traj, word_model, candidates)` — per candidate, ONE
  `DtwTo(features(s), synth(w))` via the graph Term; `likelihood_from_distances`
  (median-distance softmax). Single pass.
- `heldout_combined(...)` — the variadic product over the 23 cosine-1-NN vector
  channels PLUS the AxS precomputed-likelihood channel, written onto the word
  concepts as `p_ch{i}` attrs exactly like every other node. Combine-all.
- `domains/many_settings_recognizer.likelihood_from_distances` — factored out of
  `channel_likelihood` so the AxS node (whose distance is a DTW synth-error, not a
  cosine) reuses the IDENTICAL no-fit median-distance softmax. Same temperature
  rule, no per-channel weight, no tuning.

**Combine-all audit (no select / no weight / no fit), reproducible:**

```
python -c "import domains.many_settings_recognizer as MS, json, re; \
t=MS.predict_many_settings_term(24); \
print(sorted(set(re.findall(r'\"type\": \"(\w+)\"', json.dumps(t))))); \
print('Times items:', len(t['value']['items']))"
# -> ['Argmax', 'Attr', 'Lit', 'NodesWhere', 'Times', 'Var']
# -> Times items: 24
```

The 24-channel decision term is exactly `Argmax(NodesWhere Concept is_word) of
Times[p_ch0 .. p_ch23]` — a product over EXACTLY 24 channel-likelihood attrs.
There is NO `Max`/`Sort`/`Pick`/`If`/`Div`/weight node anywhere; every node
(including AxS) enters the product symmetrically. The AxS node has no convergence
loop, no threshold, no global weight, and is not selected over the others.
Verified: `forbidden = {Max,Sort,Pick,If,Div,...} ∩ types = NONE`.

**No-donkey**: the AxS node is the agent's OWNED `speak()`/forward-model + the graph
`DtwTo` Term as a single-pass likelihood; combine-all via the iter-34 variadic
product; no convergence-fit, no global weight, no select-best.

## (2) MULTI-METRIC n=8 table — enriched+AxS vs iter-34 vs single-flat vs frozen, with shuffle

*(filled in from `/tmp/iter35_n8_run.txt` when the authoritative run completes —
run live as this is written)*

## (3) AxS drop-it contribution (widens? orthogonal?)

*(filled in — AxS alone (real) / alone (shuffle) / drop-it Δ from the n=8 run)*

## (4) VERDICT

*(filled in)*

## Reproduce

```
python -m scripts.enriched_hvpt_accept 1 1   # smoke (/tmp/iter35_smoke_n1.txt)
python -m scripts.enriched_hvpt_accept 4 2   # n=4 (/tmp/iter35_n4_run.txt)
python -m scripts.enriched_hvpt_accept 8 2   # n=8 authoritative (/tmp/iter35_n8_run.txt)
```

Required suites green (32): test_stt_pipeline, test_perception_self_assessment,
test_process_meta_assessor, test_gap_guidance.


## (3) AxS drop-it (assistant-verified n=8)
AxS alone 0.302 (chance 0.100); label-shuffle 0.094 (collapses -> the forward-model inversion is REAL and
points correctly); drop-it Δ -0.002 -> REDUNDANT/neutral in the graph. formant +0.017, manner +0.012 still
widen; fft_ear flips to -0.006 (AxS overlaps it).

## (4) VERDICT
enr+AxS 0.588 vs iter-34 0.590 (Δ -0.002, does NOT widen); shuffle margin +0.010 vs iter-34 +0.021 (not
wider). The AxS top-down node is REAL (works alone, label-shuffle collapses, wired NO-FIT as a single-pass
synth-error likelihood -> iter-34's "AxS needs a fit" block is solved) but INFORMATIONALLY REDUNDANT on the
held-out-voice DIGIT task: the bottom-up cues already capture what inverting speak() recovers. REFINEMENT:
orthogonal-in-MECHANISM != orthogonal-in-INFORMATION; the richness lever is monotone only for INFORMATIONALLY-
complementary cues (formant/manner catch different errors; the AxS catches the same digits). The AxS would
help where the bottom-up FAILS (harder/noisier/real-word venues), not on digits the bottom-up already nails.
NET: iter-34 win STANDS; the digit task is plateauing (~0.59 held-out-voice for the bottom-up graph); the AxS
+ iconic/vibe pathways are banked (AxS real + no-fit) for a HARDER VENUE where they catch different errors.

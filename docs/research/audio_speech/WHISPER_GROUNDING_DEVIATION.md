# Frozen-protocol deviation: FSDD v1.0.8 speaker count

Recorded: 2026-07-28, after downloading and hashing the preregistered archive,
before running any confirmatory Whisper inference.

The preregistration expected FSDD v1.0.8 to contain six speakers and selected
recordings 0–9 from each speaker (n=600). The official Zenodo archive with the
preregistered MD5 `54f48186ecb1d5ac4e971143086d529b` contains 1,500 WAV files:
50 repetitions of ten digits from only three speakers (`jackson`, `nicolas`,
and `theo`). Therefore the pinned primary evaluation can contain only n=300
under the frozen 0–9 selection rule.

This is a provenance error in the preregistration, not an exclusion based on
model output. The historical project documentation names six speakers
(`george`, `jackson`, `lucas`, `nicolas`, `theo`, `yweweler`) and therefore
used a later GitHub state of the dataset, not the pinned Zenodo v1.0.8
artifact.

The response is fixed before evaluation:

1. Run the official, hash-pinned v1.0.8 archive as the primary confirmatory
   dataset with three leave-one-speaker-out folds and n=300.
2. Run the later six-speaker GitHub corpus as a clearly labelled historical
   replication, pinned to an exact Git commit and archive hash.
3. Apply the same frozen indices, model settings, radii, null controls,
   hypotheses, and statistics to both. Do not pool the datasets.
4. Report the loss of primary sample size and speaker diversity as a
   limitation.

No prediction, transcript, encoder distance, or test-fold outcome had been
computed on either downloaded corpus when this deviation was recorded.

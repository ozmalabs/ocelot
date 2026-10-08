# External-dependency predicate probe v1.2 amendment

Date: 2026-09-28

The frozen panel and expected callback counts did not change. The first analyzer implementation had an inverted assertion for expected-absent marker attributes, which caused four valid cell gates (direct predicate, both short-circuit cells, and stateful predicate) to report false. The multiple-rule cell and provenance checks passed. This was an analyzer defect, not a substrate outcome.

The initial raw capture was overwritten while correcting the analyzer and regenerating the source lock; its full bytes were not retained. The first analyzer output is recoverable only as the console summary in the work session, so it is excluded from evidence. The corrected analyzer, updated source lock, and a fresh three-worker capture were then run; that final capture passes all 11 gates. No results from the overwritten capture are used.

This amendment records an artifact-custody lapse. Future runners should preserve each raw attempt under a unique timestamp/run ID before analysis so analyzer repairs cannot overwrite a failed or inconclusive capture.

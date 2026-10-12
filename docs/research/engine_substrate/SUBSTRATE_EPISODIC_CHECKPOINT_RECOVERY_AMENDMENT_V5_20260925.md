# Episodic checkpoint recovery harness amendment v5 — 2026-09-25

The v4 run completed all workers, but the new clean-close aggregate check indexed the reader list by string instead of using the existing variant map, so scoring stopped before writing its report. The v5 runner uses that already-constructed map. No task, corruption variant, threshold, or expected outcome changed. The v5 input lock is written before rerun; v1–v4 artifacts remain retained.

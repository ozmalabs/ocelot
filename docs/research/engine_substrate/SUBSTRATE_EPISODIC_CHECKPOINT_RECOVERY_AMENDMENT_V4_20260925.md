# Episodic checkpoint recovery follow-up v4 — 2026-09-25

The v3 run established that graph restoration and recall worked but `WorldAdapter.close()` failed because load omitted the empty `_vision_illumination_nodes` session-local list. The loader now initializes that list, and a direct two-process save/load/close probe completed successfully. This v4 locked rerun repeats all four checkpoint variants on the repaired source and adds a post-load clean-close check. It preserves the original tasks, corruption variants, and retrieval criteria; v1–v3 artifacts remain unchanged as historical results.

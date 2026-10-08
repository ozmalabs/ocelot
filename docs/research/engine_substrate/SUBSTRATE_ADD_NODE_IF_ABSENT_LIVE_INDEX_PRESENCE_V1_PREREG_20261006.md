# Live-route Concept.name index presence probe v1

Date: 2026-10-06  
Question: Is `Concept.name` already indexed after the same full-seed boot used by the indexed lookup live-route comparison?

Use one fresh `WorldAdapter(seeds=())`, check `has_attr_index("Concept", "name")` immediately after adapter initialization, then call the harvest runner's `load_all_seeds` in the same order as its `unknown_word_clarification` worker and check again. Require the harvest input fingerprint to equal the indexed-lookup experiment lock's embedded harvest fingerprint before and after. Record loaded seed count, Concept population, whether the index existed before/after, and a real string-valued Concept name lookup through `nodes_where` after boot. This is a prerequisite probe only; it makes no task-quality or timing claim.

If the index is already present before the nominal indexed arm declares it, the live reference/index arm comparison is treatment-confounded. The isolated graph scaling ladder remains a separate result. Do not report a live-route speed effect from those two arms.

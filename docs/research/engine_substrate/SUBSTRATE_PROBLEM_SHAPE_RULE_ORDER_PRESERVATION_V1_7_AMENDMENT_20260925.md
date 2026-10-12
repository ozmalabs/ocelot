# Amendment V1.7: correctly gate the appended rule block

Date: 2026-09-25

V1.6 normalized both immutable seed-index caches, and its first triad passed semantic parity, seed-load order parity, and exact baseline/original-slot pre-observation order parity. It stopped because the append-order assertion placed the new rules at the absolute end of the pre-observation list. The worker appends the five transformed rules immediately after seed loading; the common scaffolding then installs three additional `rf_*` rules. Therefore the correct expected pre-observation sequence is the baseline active sequence with the five original ProblemShape rules removed and the five appended replacements inserted as one ordered contiguous block at the worker's actual append location.

V1.7 changes only that manipulation check. It verifies that the appended arm contains the exact contiguous `ps_decode`, `ps_recognize`, `ps_residual`, `ps_mint`, `ps_redecode` block, and that deleting that block yields exactly the baseline active-rule sequence with the five original names removed. Baseline and in-place treatment order gates remain exact. V1.6's failed checkpoint remains unchanged.

The design otherwise retains the same three arms, one shared immutable corpus, explicitly cleared and warmed seed-index caches, source locks for the seed loader, all six arm permutations per mix, and full per-rule counter capture.

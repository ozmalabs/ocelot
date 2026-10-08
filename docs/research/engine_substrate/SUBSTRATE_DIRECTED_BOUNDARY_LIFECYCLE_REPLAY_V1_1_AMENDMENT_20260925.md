# Directed boundary lifecycle replay v1.1 amendment

The locked v1 run completed but the event arm failed state/residual checks after each node birth. Inspection of the raw sequence and runner found a notification adapter error: the helper returned frame 1 (the source frame of boundary edge `7 → 8`) for every mutation, including birth/deletion of a node owned by frame 2. A direct diagnostic confirmed that scoped settlement of frame 2 discovers and updates the new node after the same preceding edge-mutation sequence. The v1 lock and raw failure are preserved; v1 does not demonstrate an engine failure.

## Narrow correction

The v1.1 runner changes only the directly notified frame: edge 7→8 actions seed its source frame 1; the lifecycle actions seed the node's owner frame 2. The action sequence, fixture, edge values, update rule, state equation, full-rescan reference, progress cap, and acceptance gates are unchanged. The independent audit recomputes residuals and checks this per-action notification map against the locked action type. Any v1.1 failure remains in the raw artifact and is not repaired post hoc.

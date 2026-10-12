# Directed boundary plus node lifecycle replay preregistration

**Question.** Does caller-notified scoped settlement preserve the full-rescan result when directed boundary mutations and node birth/deletion occur in one repeated sequence?

## Locked design

- Use `can_native_update_3state` on 12 Concept nodes in three four-node Microtheories.
- Start from a directed path `i → i+1` with weight +0.75, all fields zero except node 11's external field +1.0. Settle the common initial graph before mutation.
- Mutate the frame-crossing edge `7 → 8` through delete, insert +0.75, replace with −0.75, and replace with +0.75, repeated three times.
- Between the edge sequences, birth a new Concept in frame 2 with external field −1.0 and edge `11 → new_node` at +0.75, then delete that node. Repeat the birth/deletion pair three times. The full sequence therefore contains 18 actions.
- Run full round-robin and event policies in separate fresh processes from identical initial graphs. The event policy is notified of the source/owner frame and recomputes the directed dependency relation from the current live edge map on each fixpoint call.
- After every action, record states, active-node mask, fields, directed edges, completion, progress applications, frame turns, and full-graph residual. Independently recompute the ternary CAN update equation from those recorded values.
- A separate omission control deletes the first boundary edge after baseline settlement and performs no subsequent settlement; it must leave positive full-graph residual.
- Lock this protocol, runner, mutation helper, seed, and native scheduler source before execution.

## Decision rules

All 18 event/full checkpoints must terminate, match exact states and active masks, and have zero independently recomputed residual. Each mutation must change either the state vector or active-node projection. The omitted-notification control must be sensitive. Preserve the raw record if a gate fails; do not revise limits after execution.

This is a synthetic directed path mechanism experiment. It does not establish natural topology prevalence, simultaneous concurrent mutations, arbitrary dynamic partitions, native notifications, or GALS.

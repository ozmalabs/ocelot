# Amendment: predecessor candidate fanout v1.1 memory release measurement

Date: 2026-10-03

The v1 216-worker capture passes all source, candidate-selection, grounding,
quiescence, residual-return, and monolithic-parity gates. During review of its
PSS measurements, source inspection found that the post-drop sample still had
live Python references to the selected branch (`selected`, `valid`, and the
last loop variable). The v1 post-drop PSS field therefore does not measure
complete candidate-branch release and must not support a reclamation claim.
The v1 raw capture remains preserved for its valid semantic, timing,
pre-drop memory, and source-lock evidence; only its post-drop residency
interpretation is withdrawn.

V1.1 applies the same protocol and matrix, but clears every branch reference,
including the selected candidate and snapshot base, before garbage collection
and the post-drop PSS/RSS sample. It also records glibc `mallinfo2` live
allocator in-use bytes at baseline, retained fanout, post-return, and post-drop.
PSS/RSS measure resident process pages; allocator in-use bytes distinguish live
heap allocations from pages the allocator retains after freeing objects. It
repeats all 216 fresh workers so each backend/fanout/graph-size combination has
an isolated process. V1.1 results supersede v1 memory-release values;
v1 timing and semantic results remain preserved as the first capture.

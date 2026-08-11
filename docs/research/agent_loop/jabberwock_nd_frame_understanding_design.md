# The jabberwock's design — world-understanding by INFERRING the N-dimensional frame

Creator's correction (2026-06-26), twice-deep: the world provides only OBSERVATIONS +
AFFORDANCES; world-understanding is the jabberwock's, graph-native. And the grid is NOT
given — "it needs to INFER the grid. it needs to inhabit an N-DIMENSIONAL frame with
N-dimensional frames in it." The 2D-grid assumption (cells (row,col), Up/Down/Left/Right
with (drow,dcol), slide_flood / predict_wall_set over a 2D lattice) is the error. The
consumer must DISCOVER the frame's dimensionality + topology from observation + affordances,
and frames NEST (a frame within a frame within an environment).

The jabberwock's design, routed through faculties it already holds (nd_basis_discovery,
nd_representation, nd_self_world, nd_action_correlation, projection PROJECT/LIFT, spatial_map,
navigation, spatial_routing cortex, the six-role WorldBinding, nested bindings):

## 1. Infer the frame (not given)
Each affordance is a `Control` node carrying NO geometry. When it fires: locate self-Locus
(nd_self_world); nd_action_correlation records the OBSERVED displacement vector that control
induced → a learned `Control --induces--> Δ` edge (never a hardcoded (drow,dcol)). Collect
the bag of Δ-vectors across controls → feed to nd_basis_discovery: the principal directions
of motion ARE the axes; N (dimensionality) = how many INDEPENDENT directions the motion spans
(two collinear controls → one axis; orthogonal → two; a third lift → N=3). Each Control's
effect is then coordinates in the discovered Axis basis — an affordance is a learned
basis-displacement, not a handed structure.

## 2. Hold the world as N-D Loci (not a 2D grid)
projection LIFT mints a Locus per observed feature and projects its raw coords into the
discovered Axis basis (Viewpoint is data → 2D / iso / 3D streams all drive the same LIFT).
Adjacency is ONE dimension-agnostic rule: two Loci are adjacent iff they differ by exactly
one SLIDE-UNIT (the smallest learned control displacement = the quantum) on exactly ONE axis
— identical in N=1,2,3,… spatial_routing's relax-to-fixpoint runs over whatever adjacency
LIFT built, zero lattice assumption.

## 3. Nesting
A sub-frame is a Locus whose `filled_by` points at a child WorldBinding. Recognise one when
entering that Locus CHANGES the principal-motion basis — controls now move along directions
that don't project onto the parent axes — which triggers minting the child binding + running
discover_natural_frame INSIDE it. Entering binds the self-Locus into the child; navigate by
the child's own discovered adjacency; roll its value up through the existing
terminal_propagation / rollup_value so the child's value_signal contributes to the parent
Locus's value. The binding tree already held does the recursion unchanged.

## 4. Route it (navigation in master_tick, Python consumer deleted)
master_tick: nd_action_correlation + discover_natural_frame keep the Axes current; LIFT
remints Loci+adjacency each frame; pick_goal selects a goal Locus; plan_passable_step relaxes
over the discovered adjacency → next hop; invert the learned Control→Axis basis to pick the
affordance whose Δ best matches the hop. The six roles bind cleanly (controllable_locus =
self-Locus; affordance_effect = Control→Axis Δ; value/terminal from observation; dynamics
from postulates; goal from pick_goal). Python shrinks to: ingest observation → raw Locus
coords; declare Controls as affordance nodes; read the chosen Control back. The 2D consumer
(world_understanding_step) is deleted.

## 5. What's genuinely missing + build order
Almost everything routes from holdings. The ONE honest gap: generalise nd_basis_discovery
from SINGLE dominant motion (axis = velocity vector) to a MINIMAL INDEPENDENT BASIS over a
SET of Δ-vectors — likely one new Rust primitive `principal_axes(vectors) -> basis`
(orthogonalise / eigen), plus two small graph rules (`learn_slide_quantum`,
`detect_nested_frame` on basis-change).

Bench-provable build order:
1. Control + nd_action_correlation recovers snake's 4 control Δ-vectors with NO (drow,dcol)
   given.
2. `principal_axes` mints the Axis set — prove N=2 for snake and N=3 for a 3D stream.
3. LIFT + one-axis adjacency lets spatial_routing re-solve the S3 food JOIN from the
   DISCOVERED frame, no grid.
4. A Locus that opens a sub-frame — detect basis-change, enter, route, roll value up.
5. Delete the Python consumer; confirm navigation happens entirely in master_tick.

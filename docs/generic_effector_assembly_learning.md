# Generic effector assembly learning

The motor substrate now discovers coordination structure from a body's wiring
and verified action receipts. It does not require a humanoid skeleton, named
muscles, or a predefined gait. The same representation covers joints, wheels,
rotors, thrusters, and aerodynamic surfaces.

## Boundary contract

The host publishes mechanical facts only:

- opaque command tokens;
- physical command channels and mounts;
- hard couplings, when imposed by the plant;
- the name-free linkage graph; and
- which physical channels a precombined command vector actually addresses.

It does not label an effector as a leg, steering surface, stabilizer, or agonist.
`domains/embodied_effector_topology.py` turns those facts into
`EmbodiedEffectorTopology`, `EmbodiedEffector`, and
`EmbodiedEffectorRelation` graph nodes. A command model may point to one
effector or to several effectors when a simulator exposes a combined vector.

The fast topology is segmental: it materializes same-channel constraints,
declared hard couplings, and mechanically adjacent mounts. It deliberately does
not mint the Cartesian product of the body. Distal combinations are learned by
composition rather than paid for on every control tick.

## Learned relation

Graph rules open a defeasible assembly hypothesis for each local relation.
Same-channel alternatives begin as `hard_conflict`; plant-declared couplings
begin as `hard_coupled`; all other local relations begin as `candidate`.

When a verified receipt says that two channels were actually coactivated, a
local eligibility update accumulates continuous evidence for:

- task-aligned cooperation;
- interference and the need to fractionate;
- redundancy;
- common drive;
- interaction residual;
- progress and energy cost; and
- support-phase context.

The evidence is a trade-off surface, not a fault detector. An interfering pair
is marked `fractionating`, which means broad common drive should be inhibited
in that context while the constituent effectors remain available for other
assemblies. A cooperative pair becomes a reusable lower-level motor chunk.

## Biological scheduling

Mechanical publication and local coactivation traces live on the fast sheet.
This is analogous to spinal/brainstem circuitry and local plastic eligibility:
it is bounded by the number of mechanically adjacent effectors and must remain
available during ordinary movement. Searching larger assemblies, consolidating
them into a shape-indexed repertoire, and reopening ambiguous combinations are
slower System-2/default-mode work. Those operations must consume the local
traces; they must not lengthen the immediate release loop.

The humanoid curriculum enables this layer and supplies a real linkage graph.
The generic ground and aerial adapters also install it; their combined command
vectors are decomposed into physical channels before the graph sees receipts.
This lets the same rules discover differential wheel action, rotor cooperation,
or limb synergies without changing vocabulary or policy code.

## Invariants

- No anatomical or vehicle role names enter the graph boundary.
- Only verified physical receipts change assembly evidence.
- Hard plant coupling is never inferred from behavioural correlation.
- A zero-valued channel in a combined command is not credited as enacted.
- Local topology prevents quadratic whole-body growth.
- Learned assemblies remain defeasible and context-sensitive evidence remains
  available for later hierarchy and fractionation.


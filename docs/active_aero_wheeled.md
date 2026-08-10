# Graph-native active aerodynamics on a wheeled body

The wheeled/aerodynamic body is represented as six independent opaque
effector groups. Two happen to terminate at the wheel plant and four at
flow-conditioned external-force surfaces, but those meanings remain inside
the simulator boundary. The graph receives group compatibility, its own
activation magnitude, raw motion/load/energy receipts, and no names such as
drive, steering, wing, or spoiler.

`embodied_motor_program` is the shared inverse-control layer. It learns a
passive-dynamics reference from zero-activation receipts, represents each
effector as a causal delta from that reference, and uses analysis by synthesis
to add one compatible group at a time while predicted task error strictly
falls. The completed `EmbodiedMotorProgram` is the decision option sent through
`motor_decision_collapse`; the host receives only the exact graph-selected
member set. This avoids a precomputed Cartesian action lattice.

Aerodynamic authority is conditioned on squared flow speed. Normal-force,
drag, actuator-energy, translation and turning consequences remain distinct,
so the graph can trade tire loading against drag and free-energy expenditure.
Compound receipts update a program interaction residual; they are not
incorrectly copied into every primitive model.

## Hidden-damage result

The preregistered deterministic run completely removes one surface at action
60. Before failure the graph repeatedly includes that group. Its changed
compound receipt crosses the relative causal-effect surprise gate, causing one
bounded recalibration pass. The broken command then learns zero normal-force
authority and zero flow gain. Subsequent programs exclude the failed group and
compose surviving surfaces instead.

Run:

```bash
python scripts/gen_embodied_motor_program_seed.py
python scripts/jabberwock_active_aero.py \
  --steps 110 \
  --damage-onset 60 \
  --broken-surface 2 \
  --output results/active_aero_wheeled_v1.json
pytest -q tests/test_active_aero_motor_program_migrated.py
```

This is an architectural and adaptation demonstration, not a claim about CFD
fidelity, lap time, vehicle certification, or safe hardware deployment.

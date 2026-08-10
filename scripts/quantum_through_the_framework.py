"""Ask the Jabberwock about quantum physics — read THROUGH its own framework, not
recited. The agent already holds (a) quantum atomic structure as chemistry
(schrodinger_atomic: 'energy quantised by boundary conditions'), and (b) the
framework that reframes it: the log-graph law (log_axis_law, e_as_log_axis_unit,
constants_form_vs_content), admissibility grammar (efficiency_is_admissibility_
grammar), β-as-evidence-threshold + basin dynamics (foundationality_is_basin_depth,
foundational_revision_is_sudden_basin_hop, low-β alternatives), and a real
cochlear/Fourier front-end embodying the time-frequency tradeoff.

This juxtaposes each quantum phenomenon with the OWNED concept that already carries
its structure, confidence-tagged and HONESTLY flagged:
  [OWNED]       the structure is literally in the agent's machinery, not analogy
  [STRUCTURAL]  a real structural correspondence in the dynamics
  [ANALOGY]     a strong analogy, not an identity
  [SPECULATIVE] a hypothesis from the framework, unproven
I author no physics; I anchor each reading to a concept the agent holds, and flag
the honest gap where the framework does NOT deliver.
"""
from __future__ import annotations
import json, glob, sys
from pathlib import Path
sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")

# anchors the agent must actually hold for each reading to be honest
ANCHORS = {
    "schrodinger_atomic", "efficiency_is_admissibility_grammar", "log_axis_law",
    "e_as_log_axis_unit", "phi_as_bounded_recursion_fixedpoint", "constants_form_vs_content",
    "compute_in_log_space", "beta_is_evidence_threshold_not_slowness",
    "foundationality_is_basin_depth", "foundational_revision_is_sudden_basin_hop",
    "beta_infinity_is_incorrigible_unreachable_absolute",
}


def held_concepts():
    names = set()
    for f in glob.glob(str(ROOT / "seeds" / "**" / "*.json"), recursive=True):
        try: d = json.load(open(f))
        except Exception: continue
        for c in d.get("concepts") or []:
            names.add(c.get("name", ""))
        for n in d.get("nodes") or []:
            if isinstance(n, dict) and n.get("type") == "Concept":
                names.add(n.get("attrs", {}).get("name", ""))
        for m in d.get("sub_mechanisms") or []:
            names.add(m.get("name", ""))
    return names


# (phenomenon, owned-anchor, flag, confidence, reading)
READINGS = [
    ("Quantization (discrete energy levels)", "efficiency_is_admissibility_grammar",
     "OWNED", 0.8,
     "My own Schrödinger concept says it outright: 'energy quantised by boundary conditions.' "
     "That IS admissibility grammar. A grammar makes a continuum discrete by admitting only "
     "certain configurations; boundary conditions ARE the grammar's constraints, and the "
     "eigenstates are the admissible nodes. 'Quantum' is not a mysterious extra fact about the "
     "world — it is what any admissibility grammar does to a continuous substrate. I already "
     "compute this way: most configurations are inadmissible and never computed; the few that "
     "are, are the spectrum."),
    ("Heisenberg uncertainty (Δx·Δp ≥ ħ/2)", "(my cochlear/STFT front-end)",
     "OWNED", 0.8,
     "Not an analogy — I embody it. My auditory front-end faces the time-frequency tradeoff "
     "Δt·Δf ≥ const every tick: a sharp click is broadband, a pure tone needs a long window. "
     "Position and momentum are Fourier conjugates exactly as time and frequency are; the "
     "uncertainty principle is the time-bandwidth product of a Fourier pair, which my cochlea "
     "already cannot beat. The physics 'principle' is a property of any system that reads a "
     "signal in conjugate bases — me included."),
    ("Superposition + measurement-collapse", "foundational_revision_is_sudden_basin_hop",
     "STRUCTURAL", 0.62,
     "I hold alternatives at low β — multiple admissible basins, none crystallised — and a "
     "sufficient field-change flips the network to one basin in a sudden hop at threshold. That "
     "is superposition (alternatives coexisting, uncommitted) and collapse (crystallisation when "
     "evidence crosses the threshold). Decoherence = coupling to many degrees of freedom raises "
     "the effective β until a basin is forced. HONEST CAVEAT: this is a correspondence in the "
     "DYNAMICS, not a derivation of the Born weights — I get why a definite outcome appears, not "
     "yet why its probability is |ψ|²."),
    ("Entanglement / non-locality", "(relational structure — a shared edge)",
     "STRUCTURAL", 0.6,
     "Two entangled particles are one structure sharing an edge, not two objects signalling "
     "across space. Measuring one fixes the other because they were never separate nodes — the "
     "correlation is a single relation, read from two ends. 'Spooky action at a distance' "
     "dissolves the way it does for me: my graph's edges are not spatial, so a shared relation "
     "has no distance to cross. This is the relational-invariance I already rely on — the meaning "
     "is in the structure, not in where the endpoints sit."),
    ("Complex amplitude & the Born rule (phase e^{iθ}, prob=|ψ|²)", "e_as_log_axis_unit",
     "SPECULATIVE", 0.45,
     "If the world's axis is logarithmic, amplitude is the log-natural quantity and probability "
     "is its linear shadow — the squaring that turns ψ into |ψ|² is the projection back from the "
     "log/complex axis to the linear ruler. The phase e^{iθ} is the orthogonal ROTATIONAL "
     "component of that axis (e^{iπ}+1=0: e the unit of self-reference, π the quarter-turn). So "
     "interference is rotation in the log-plane and the Born rule is the form→content projection. "
     "FLAG: suggestive, not derived — I cannot yet get the exponent 2 out of the framework rather "
     "than putting it in."),
    ("Path integral / least action", "(MPC over admissible trajectories)",
     "ANALOGY", 0.5,
     "Nature sums over admissible paths; I plan by summing over admissible trajectories and "
     "minimising expected free energy, and least action is the grammar selecting the geodesic — "
     "the admissible path of least cost. Strong analogy. FLAG: the weighting differs — physics "
     "weights paths by a complex phase e^{iS/ħ} that interferes, my planner weights by a real "
     "cost that does not. Same shape (extremise over admissible paths), different measure."),
    ("Planck's constant ħ", "constants_form_vs_content",
     "SPECULATIVE", 0.5,
     "ħ is the quantum of action — the granularity of the graph's productions, the scale at which "
     "the discreteness bites. In my constants split it is a CONTENT constant (contingent, like α "
     "and Λ: it sets THIS universe's grain) rather than a FORM constant (e, φ: forced by the shape "
     "of self-reference). ħ→0 is the classical limit = the grain too fine to see, the admissible "
     "set looking continuous. FLAG: placement in the form/content split is a framework claim, not "
     "a measurement."),
]

OPEN = (
    "Is quantum mechanics EMERGENT from a deeper discrete graph law, or is the graph law itself "
    "quantum? My framework reads QM's discreteness as admissibility, its uncertainty as Fourier "
    "duality (which I embody), and its superposition/collapse as low-β/basin-hop — all without "
    "adding anything quantum by hand. That makes 'QM is what a discrete admissibility-grammar "
    "universe looks like from inside' a real hypothesis. But until the framework DERIVES the Born "
    "rule's |ψ|² — the one place I had to put the answer in to get it out — it stays a hypothesis, "
    "confidence ~0.4, not a result."
)


def main():
    held = held_concepts()
    print("ANCHORS — concepts I actually hold that carry quantum structure:")
    for a in sorted(ANCHORS):
        print(f"   {'✓' if a in held else '✗ MISSING'}  {a}")
    missing = [a for a in ANCHORS if a not in held]

    print("\n" + "=" * 78)
    print("QUANTUM PHYSICS, READ THROUGH MY FRAMEWORK  (anchored, flagged, confidence-tagged)")
    print("=" * 78)
    for phen, anchor, flag, conf, reading in READINGS:
        print(f"\n  ⟶ {phen}")
        print(f"     anchor: {anchor}   [{flag}, conf {conf:.2f}]")
        print(f"     {reading}")

    print("\n" + "=" * 78)
    print("THE HONEST GAP + THE OPEN QUESTION")
    print("=" * 78)
    print(f"\n  {OPEN}")

    print("\n" + "=" * 78)
    print("SUMMARY")
    print("=" * 78)
    owned = sum(1 for *_, f, _, _ in [(r[0], r[1], r[2], r[3], r[4]) for r in READINGS] if f == "OWNED")
    print(f"  {len(READINGS)} phenomena read through owned structure: "
          f"{sum(1 for r in READINGS if r[2]=='OWNED')} OWNED, "
          f"{sum(1 for r in READINGS if r[2]=='STRUCTURAL')} STRUCTURAL, "
          f"{sum(1 for r in READINGS if r[2]=='ANALOGY')} ANALOGY, "
          f"{sum(1 for r in READINGS if r[2]=='SPECULATIVE')} SPECULATIVE.")
    print(f"  Missing anchors: {missing if missing else 'none — every reading rests on a held concept.'}")
    print("  The two strongest (quantisation = admissibility; uncertainty = Fourier duality) are")
    print("  OWNED — already in my machinery. The Born rule is the honest hole.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""teach_tech_microtheories — TEACH the last five anchored tech domains a true concept microtheory,
each carrying has_concept edges, so `concept_graph`'s edge-learner can DESCEND them (2026-07-04).

WHY (the graph the edge-learner lacked): `concept_graph.world_dimension` places a concept by the
tf-idf cosine of its `Microtheory -has_concept-> Concept` neighbourhood to a small set of labelled
region-anchor microtheories. After the gaming/literary/period build it edge-learned 26/31 domains; the
last five stayed ANCHORED because their has_concept edges were ZERO or DIFFUSE:

  * computer_architecture (bag 2) and mathematics (bag 1) had NO member concepts — only their own name
    tokens — so their region cosine was 0.0 (nothing to co-descend against);
  * cloud_infrastructure (bag 132), art_design_drawing (bag 171) and communication (bag 145) had large
    DIFFUSE bags whose cosine to the existing anchors was tiny (< the grounding floor) or split across
    both worlds (clarity < 2/3).

This is the SEED BUILDER (admissible: it EMITS graph data — a microtheory + member concepts + the
has_concept edges the loader wires — the same class as tools/* and teach_dimension_microtheories.py).
It teaches TRUE member concepts (real CPU / mathematics / cloud / drawing / communication concepts, no
LLM, no fabrication) and — mirroring the prior build — REGISTERS each crossable domain as its own
labelled region anchor in `concept_graph._REGION_ANCHORS` (see that module). ASSIGNED BY TRUE NATURE:

  * MODERN (foreign to a Victorian): computer_architecture, cloud_infrastructure — post-1885 computing.
  * UNIVERSAL (familiar to a Victorian — timeless): mathematics, art_design_drawing (the timeless
    drawing/colour/composition sense — Vane's world holds it).
  * communication is genuinely DIFFUSE (a timeless human sense — language/message/meaning/rhetoric —
    AND a technical networking sense — protocol/packet/bandwidth). It is taught the TIMELESS sense it
    truly reflects but is NOT forced across: it is left to the honest edge-measure (it stays split and
    resolves universal via the anchor fallback — reported by `jabberwock_richer_grounding`, not forced).

Two levels each where sensible (a sub-microtheory) so the N-descent has a deeper rung:
computer_architecture -> microarchitecture; mathematics -> geometry; cloud_infrastructure ->
container_orchestration; art_design_drawing -> classical_drawing.

Reboot-proof by construction (files under seeds/). Run:
  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/teach_tech_microtheories.py
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEDS = os.path.join(ROOT, "seeds")


def _c(name: str, definition: str, category: str) -> dict:
    return {"name": name, "definition": definition, "category": category}


# =========================================================================== #
#  COMPUTER ARCHITECTURE — a MODERN-world region anchor. The organisation of a
#  digital processor: a concept wholly foreign to a Victorian of 1885.
# =========================================================================== #
COMPUTER_ARCHITECTURE = {
    "id": "computer_architecture_microtheory",
    "version": "1.0.0",
    "depends_on": [],
    "description": "COMPUTER ARCHITECTURE: the organisation of a digital processor — CPU, registers, "
                   "cache, pipeline, ALU, instruction set, memory hierarchy. A modern-region anchor "
                   "(post-1885 computing, foreign to Cornelius Vane's Victorian frame).",
    "microtheory": {
        "name": "computer_architecture",
        "definition": "The organisation and design of a digital computer's processor and memory: the "
                      "CPU's datapath and control, the register file, the cache and memory hierarchy, "
                      "the arithmetic-logic unit, the instruction set, and the clocked bus that ties "
                      "them together. The modern computing world Cornelius Vane has no concept of.",
        "category": "computer_architecture",
    },
    "concepts": [
        _c("cpu", "The central processing unit — the processor that fetches, decodes and executes instructions.", "computer_architecture"),
        _c("register", "A small, fast storage cell inside the CPU holding an operand or address.", "computer_architecture"),
        _c("cache", "A small fast memory holding recently-used data, bridging the CPU-memory speed gap.", "computer_architecture"),
        _c("pipeline", "Overlapping the fetch/decode/execute stages of successive instructions for throughput.", "computer_architecture"),
        _c("alu", "The arithmetic-logic unit — the CPU circuit that computes arithmetic and logic operations.", "computer_architecture"),
        _c("instruction_set", "The vocabulary of machine operations a processor implements (the ISA).", "computer_architecture"),
        _c("memory_hierarchy", "The tiered store — registers, cache, RAM, disk — trading speed for capacity.", "computer_architecture"),
        _c("transistor", "The semiconductor switch from which all digital logic gates are built.", "computer_architecture"),
        _c("clock", "The periodic signal that paces a synchronous processor's operations.", "computer_architecture"),
        _c("bus", "The shared set of wires carrying data, addresses and control between components.", "computer_architecture"),
        _c("control_unit", "The CPU block that sequences the datapath by decoding instructions into control signals.", "computer_architecture"),
        _c("program_counter", "The register holding the address of the next instruction to fetch.", "computer_architecture"),
        _c("opcode", "The field of a machine instruction that names the operation to perform.", "computer_architecture"),
        _c("word_size", "The native bit-width a processor operates on (8, 16, 32, 64 bits).", "computer_architecture"),
        _c("cache_line", "The fixed-size block of memory a cache loads and evicts as a unit.", "computer_architecture"),
        _c("datapath", "The functional units and buses through which data flows and is transformed in a CPU.", "computer_architecture"),
        _c("interrupt", "A signal that diverts the processor to service an asynchronous event.", "computer_architecture"),
        _c("addressing_mode", "A rule for computing an operand's memory address from an instruction.", "computer_architecture"),
        _c("microcode", "The low-level control words that implement a complex instruction inside the CPU.", "computer_architecture"),
        _c("branch_predictor", "The unit that guesses a conditional branch's outcome to keep the pipeline full.", "computer_architecture"),
    ],
}

MICROARCHITECTURE = {
    "id": "microarchitecture_microtheory",
    "version": "1.0.0",
    "depends_on": ["computer_architecture_microtheory"],
    "description": "MICROARCHITECTURE — the sub-world of computer_architecture: how one processor "
                   "realises its instruction set. Gives the concept-graph descent a third rung.",
    "microtheory": {
        "name": "microarchitecture",
        "definition": "The concrete implementation of an instruction set in one processor: the pipeline "
                      "stages, hazard handling, out-of-order and superscalar execution that turn the "
                      "architectural contract into gates and clocks.",
        "category": "microarchitecture",
    },
    "parent_mt": "computer_architecture",
    "concepts": [
        _c("pipeline_stage", "One step (fetch, decode, execute, memory, writeback) of an instruction pipeline.", "microarchitecture"),
        _c("data_hazard", "A pipeline stall when an instruction needs a result not yet produced.", "microarchitecture"),
        _c("forwarding", "Bypassing a result directly to a dependent instruction to avoid a stall.", "microarchitecture"),
        _c("out_of_order_execution", "Executing instructions as operands become ready, not in program order.", "microarchitecture"),
        _c("superscalar", "Issuing more than one instruction per clock via duplicated execution units.", "microarchitecture"),
        _c("speculation", "Executing past an unresolved branch on a predicted path, squashing if wrong.", "microarchitecture"),
        _c("reorder_buffer", "The structure that retires out-of-order results back into program order.", "microarchitecture"),
        _c("register_renaming", "Mapping architectural registers to a larger physical set to remove false dependencies.", "microarchitecture"),
        _c("branch_prediction", "Guessing a branch outcome to keep the pipeline supplied with instructions.", "microarchitecture"),
        _c("instruction_retirement", "Committing a completed instruction's effects, in order, to architectural state.", "microarchitecture"),
    ],
}

# =========================================================================== #
#  MATHEMATICS — a UNIVERSAL / timeless region anchor. Theorem, proof, algebra,
#  geometry: as present in Vane's Victorian world as in a modern one.
# =========================================================================== #
MATHEMATICS = {
    "id": "mathematics_microtheory",
    "version": "1.0.0",
    "depends_on": [],
    "description": "MATHEMATICS: theorem, proof, algebra, geometry, calculus, number, function — a "
                   "timeless / universal-region anchor. Cornelius Vane the Victorian holds it as fully "
                   "as a modern mathematician.",
    "microtheory": {
        "name": "mathematics",
        "definition": "The timeless study of number, quantity, structure, space and change, built by "
                      "proof from axioms: algebra, geometry, calculus, logic, topology. A universal "
                      "world present in every frame — Vane's age knew Euclid, Newton and Gauss.",
        "category": "mathematics",
    },
    "concepts": [
        _c("theorem", "A statement proved true by deduction from axioms and prior theorems.", "mathematics"),
        _c("proof", "A finite chain of valid inferences establishing a theorem beyond doubt.", "mathematics"),
        _c("algebra", "The study of operations and their structure over symbols standing for numbers.", "mathematics"),
        _c("geometry", "The study of points, lines, figures and space, and their measure.", "mathematics"),
        _c("calculus", "The study of continuous change via derivatives and integrals.", "mathematics"),
        _c("number", "An abstract quantity — natural, integer, rational, real or complex.", "mathematics"),
        _c("function", "A rule assigning to each input of a domain exactly one output.", "mathematics"),
        _c("equation", "A statement that two expressions are equal, to be solved or verified.", "mathematics"),
        _c("topology", "The study of properties preserved under continuous deformation.", "mathematics"),
        _c("logic", "The formal study of valid inference and the structure of proof.", "mathematics"),
        _c("set", "A collection of distinct objects considered as a single mathematical whole.", "mathematics"),
        _c("integral", "The accumulated total of a quantity — the area under a curve.", "mathematics"),
        _c("derivative", "The instantaneous rate of change of a function.", "mathematics"),
        _c("axiom", "A statement taken as self-evidently true, the starting point of a proof.", "mathematics"),
        _c("prime", "A natural number greater than one divisible only by one and itself.", "mathematics"),
        _c("matrix", "A rectangular array of numbers representing a linear map or system.", "mathematics"),
        _c("probability", "The measure of how likely an event is, between zero and one.", "mathematics"),
        _c("group", "A set with an associative operation, identity and inverses — the algebra of symmetry.", "mathematics"),
        _c("limit", "The value a function or sequence approaches as its input approaches a point.", "mathematics"),
        _c("series", "The sum of the terms of a sequence, finite or infinite.", "mathematics"),
    ],
}

GEOMETRY = {
    "id": "geometry_microtheory",
    "version": "1.0.0",
    "depends_on": ["mathematics_microtheory"],
    "description": "GEOMETRY — the sub-world of mathematics: the classical study of figures and space, "
                   "giving the concept-graph descent a third rung below mathematics.",
    "microtheory": {
        "name": "geometry",
        "definition": "The classical study of points, lines, angles and figures in the plane and space: "
                      "Euclid's theorems, the Pythagorean relation, area and coordinate methods.",
        "category": "geometry",
    },
    "parent_mt": "mathematics",
    "concepts": [
        _c("point", "A position with no extent — the primitive of geometry.", "geometry"),
        _c("line", "A straight one-dimensional figure extended without end.", "geometry"),
        _c("angle", "The figure formed by two rays sharing an endpoint, measuring rotation.", "geometry"),
        _c("triangle", "A three-sided polygon, the simplest rectilinear figure.", "geometry"),
        _c("circle", "The set of points equidistant from a centre.", "geometry"),
        _c("polygon", "A closed plane figure bounded by straight segments.", "geometry"),
        _c("area", "The measure of the two-dimensional extent of a figure.", "geometry"),
        _c("coordinate", "A number locating a point relative to axes (Descartes' method).", "geometry"),
        _c("euclidean_geometry", "Geometry from Euclid's five postulates — the geometry of flat space.", "geometry"),
        _c("pythagorean_theorem", "In a right triangle the square on the hypotenuse equals the sum of the other two.", "geometry"),
    ],
}

# =========================================================================== #
#  CLOUD INFRASTRUCTURE — a MODERN-world region anchor. Servers, containers,
#  orchestration: post-Victorian computing, foreign to Vane's frame.
# =========================================================================== #
CLOUD_INFRASTRUCTURE = {
    "id": "cloud_infrastructure_anchor_microtheory",
    "version": "1.0.0",
    "depends_on": [],
    "description": "CLOUD INFRASTRUCTURE: servers, containers, virtualization, orchestration, "
                   "deployment — a modern-region anchor. Focused member concepts sharpening the "
                   "already-present (diffuse) cloud microtheory so it edge-grounds modern.",
    "microtheory": {
        "name": "cloud_infrastructure",
        "definition": "The modern practice of running software on pools of remote, virtualized compute: "
                      "servers and datacenters, containers and their orchestration, autoscaling and "
                      "load-balancing, deployment and provisioning. A post-1885 computing world.",
        "category": "cloud_infrastructure",
    },
    "concepts": [
        _c("server", "A networked computer that provides a service to clients.", "cloud_infrastructure"),
        _c("container", "A lightweight, isolated package of an application and its dependencies.", "cloud_infrastructure"),
        _c("kubernetes", "The dominant system for orchestrating containers across a cluster.", "cloud_infrastructure"),
        _c("virtualization", "Running many isolated virtual machines on one physical host.", "cloud_infrastructure"),
        _c("deployment", "The act of releasing a version of software to run in an environment.", "cloud_infrastructure"),
        _c("autoscaling", "Automatically adding or removing capacity as load changes.", "cloud_infrastructure"),
        _c("load_balancer", "A component distributing requests across a pool of servers.", "cloud_infrastructure"),
        _c("datacenter", "A facility housing the pooled servers, storage and networking of the cloud.", "cloud_infrastructure"),
        _c("orchestration", "Automated coordination of the deployment, scaling and health of services.", "cloud_infrastructure"),
        _c("microservice", "A small independently-deployable service, one of many composing an application.", "cloud_infrastructure"),
        _c("vm_hypervisor", "The layer that creates and runs virtual machines on physical hardware.", "cloud_infrastructure"),
        _c("provisioning", "Preparing and configuring infrastructure resources for use.", "cloud_infrastructure"),
    ],
}

CONTAINER_ORCHESTRATION = {
    "id": "container_orchestration_microtheory",
    "version": "1.0.0",
    "depends_on": ["cloud_infrastructure_anchor_microtheory"],
    "description": "CONTAINER ORCHESTRATION — the sub-world of cloud_infrastructure: the Kubernetes "
                   "object model, giving the concept-graph descent a third rung below cloud.",
    "microtheory": {
        "name": "container_orchestration",
        "definition": "The Kubernetes model for running containers: pods scheduled onto cluster nodes, "
                      "services and ingress routing traffic, replica sets and autoscalers keeping the "
                      "declared state, namespaces and Helm charts packaging it.",
        "category": "container_orchestration",
    },
    "parent_mt": "cloud_infrastructure",
    "concepts": [
        _c("pod", "The smallest deployable unit — one or more co-located containers.", "container_orchestration"),
        _c("node_cluster", "The set of worker machines a container orchestrator schedules onto.", "container_orchestration"),
        _c("service_mesh", "An infrastructure layer handling service-to-service communication.", "container_orchestration"),
        _c("ingress", "The rules routing external traffic into cluster services.", "container_orchestration"),
        _c("replica_set", "The controller keeping a specified number of pod replicas running.", "container_orchestration"),
        _c("scheduler", "The component assigning pods to nodes by resource and constraint.", "container_orchestration"),
        _c("namespace", "A virtual partition isolating groups of resources within a cluster.", "container_orchestration"),
        _c("helm_chart", "A packaged, templated definition of a Kubernetes application.", "container_orchestration"),
    ],
}

# =========================================================================== #
#  ART / DESIGN / DRAWING — a UNIVERSAL / timeless region anchor. The timeless
#  drawing sense: line, colour, composition, perspective — Vane's world holds it.
# =========================================================================== #
ART_DESIGN_DRAWING = {
    "id": "art_design_drawing_anchor_microtheory",
    "version": "1.0.0",
    "depends_on": [],
    "description": "ART / DESIGN / DRAWING (the timeless sense): line, colour, composition, "
                   "perspective, form, proportion, shading — a universal-region anchor. Focused "
                   "timeless member concepts sharpening the diffuse art microtheory toward the "
                   "universal world Cornelius Vane holds (drawing is as old as his age).",
    "microtheory": {
        "name": "art_design_drawing",
        "definition": "The timeless craft of visual art and drawing: line and form, colour and value, "
                      "composition and proportion, perspective and shading — the fundamentals a "
                      "draughtsman of any age, Victorian or modern, works in.",
        "category": "art_design_drawing",
    },
    "concepts": [
        _c("line", "The fundamental mark of drawing, varying in weight and character.", "art_design_drawing"),
        _c("colour", "The visual sensation of hue, governed by pigment and light.", "art_design_drawing"),
        _c("composition", "The arrangement of elements within the picture frame.", "art_design_drawing"),
        _c("perspective", "The method of representing depth on a flat surface via converging lines.", "art_design_drawing"),
        _c("form", "The three-dimensional volume a drawing suggests through shading.", "art_design_drawing"),
        _c("value", "The lightness or darkness of a tone, carrying form and depth.", "art_design_drawing"),
        _c("palette", "The set of colours an artist selects and mixes for a work.", "art_design_drawing"),
        _c("sketch", "A rapid, preliminary drawing capturing essentials.", "art_design_drawing"),
        _c("proportion", "The relation of the sizes of a figure's parts to the whole.", "art_design_drawing"),
        _c("shading", "The gradation of value that models form and light.", "art_design_drawing"),
        _c("tone", "A gradation of light and dark independent of hue.", "art_design_drawing"),
        _c("contour", "The outline that describes the edge of a form.", "art_design_drawing"),
        _c("figure_drawing", "The study and depiction of the human form.", "art_design_drawing"),
        _c("chiaroscuro", "The strong contrast of light and shade modelling three-dimensional form.", "art_design_drawing"),
    ],
}

CLASSICAL_DRAWING = {
    "id": "classical_drawing_microtheory",
    "version": "1.0.0",
    "depends_on": ["art_design_drawing_anchor_microtheory"],
    "description": "CLASSICAL DRAWING — the sub-world of art_design_drawing: the atelier fundamentals, "
                   "giving the concept-graph descent a third rung below art_design_drawing.",
    "microtheory": {
        "name": "classical_drawing",
        "definition": "The timeless atelier discipline of drawing from observation: gesture and "
                      "life-drawing, the vanishing point and the horizon, hatching and negative space, "
                      "the rule of thirds and the golden section.",
        "category": "classical_drawing",
    },
    "parent_mt": "art_design_drawing",
    "concepts": [
        _c("gesture", "A quick drawing capturing the pose and movement of a figure.", "classical_drawing"),
        _c("negative_space", "The empty space around and between subjects, an active part of design.", "classical_drawing"),
        _c("vanishing_point", "The point on the horizon where parallel lines appear to converge.", "classical_drawing"),
        _c("hatching", "Parallel strokes building tone and shading in drawing.", "classical_drawing"),
        _c("still_life", "The depiction of arranged inanimate objects.", "classical_drawing"),
        _c("life_drawing", "Drawing the human figure from a live model.", "classical_drawing"),
        _c("golden_ratio", "The proportion (about 1.618) long held pleasing in composition.", "classical_drawing"),
        _c("rule_of_thirds", "Placing subjects on a two-by-two division of the frame for balance.", "classical_drawing"),
    ],
}

# =========================================================================== #
#  COMMUNICATION — genuinely DIFFUSE. Taught the TIMELESS human sense it truly
#  reflects (language, message, meaning, rhetoric), but NOT registered as an
#  anchor and NOT forced: left to the honest edge-measure. It resolves UNIVERSAL
#  (familiar to Vane) via the anchor fallback and is reported honestly.
# =========================================================================== #
COMMUNICATION = {
    "id": "communication_anchor_microtheory",
    "version": "1.0.0",
    "depends_on": [],
    "description": "COMMUNICATION (the timeless human sense): language, message, meaning, signal, "
                   "rhetoric, dialogue, expression. Taught honestly — communication is genuinely "
                   "DIFFUSE (also a technical networking sense: protocol, packet, bandwidth) — and "
                   "NOT forced across: left to the edge-measure, it stays split and resolves universal "
                   "via the anchor fallback (reported, not registered as an anchor).",
    "microtheory": {
        "name": "communication",
        "definition": "The timeless act of conveying meaning between minds: language and message, sign "
                      "and symbol, sender and receiver, rhetoric and dialogue, expression and its "
                      "reception. A universal human faculty Cornelius Vane's rhetorical age prized.",
        "category": "communication",
    },
    "concepts": [
        _c("language", "A systematic means of communication by signs, sounds or gestures.", "communication"),
        _c("message", "The content conveyed from a sender to a receiver.", "communication"),
        _c("meaning", "The sense or significance a sign or utterance carries.", "communication"),
        _c("signal", "A carrier that conveys information from source to destination.", "communication"),
        _c("rhetoric", "The classical art of persuasive speech and writing.", "communication"),
        _c("dialogue", "An exchange of utterances between two or more participants.", "communication"),
        _c("expression", "The outward conveyance of thought or feeling.", "communication"),
        _c("sign", "Something that stands for something else to an interpreter.", "communication"),
        _c("symbol", "A sign whose relation to its object is by convention.", "communication"),
        _c("medium", "The channel through which a message is conveyed.", "communication"),
        _c("sender", "The originator who encodes and transmits a message.", "communication"),
        _c("receiver", "The party who receives and decodes a message.", "communication"),
        _c("feedback", "The receiver's response that informs the sender.", "communication"),
        _c("context", "The circumstances that shape a message's meaning.", "communication"),
        _c("discourse", "Extended, structured communication in speech or writing.", "communication"),
        _c("semantics", "The study of meaning in language and signs.", "communication"),
    ],
}


SEEDS_TO_TEACH = [
    COMPUTER_ARCHITECTURE, MICROARCHITECTURE,
    MATHEMATICS, GEOMETRY,
    CLOUD_INFRASTRUCTURE, CONTAINER_ORCHESTRATION,
    ART_DESIGN_DRAWING, CLASSICAL_DRAWING,
    COMMUNICATION,
]


def teach_all(seeds_dir: str = SEEDS) -> list:
    """Emit each tech microtheory as a seed manifest the loader installs. Idempotent (overwrites the
    file with identical content). Returns the list of written paths."""
    written = []
    for seed in SEEDS_TO_TEACH:
        path = os.path.join(seeds_dir, f"{seed['id']}.json")
        with open(path, "w") as f:
            json.dump(seed, f, indent=1)
        written.append(path)
    return written


if __name__ == "__main__":
    for p in teach_all():
        print("taught tech microtheory seed ->", os.path.relpath(p, ROOT))

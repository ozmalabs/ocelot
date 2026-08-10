# Richer junction perception — literature grounding (for the jabberwock to ground + design from)

Research spike (2026-06-27). The generative handwriting recognizer is bottlenecked on RELATION-FEATURE RICHNESS:
the held perception gives thin relations on Omniglot motor traces (mostly free/end terminals, few along/T), so
the order-invariant binder has little distinctive relational structure to correspond parts by. Creator: "open
richer junction perception, gated by the controls. the point is to build CAPABILITY + graph-native CHEAP options
with DEFINED residuals." Enrich the RELATIONS perceived between sub-strokes. Three clusters converge. Per
methodology: research → ground → the AGENT designs. In-route (structural relations, NOT holistic features — deep
route 96.5 is a different machine; generative route caps ~78). Run on the motor TRACE.

## The convergent design (cheap, graph-native, topology-first, defined residuals)
Enrich the sub-stroke relation perception with TWO families, each emitted as a labeled, confidence-scored,
attributed graph EDGE (a defined residual the binder's StructSim consumes; additive on the same edge slot):
1. **TOPOLOGICAL junction/contact** (the contact graph): L(end-corner) / Y-arrow(corner-fork) / **T(touch/abut —
   contact/occlusion, the structurally richest)** / **X(crossing)** — the contact topology BPL's start/end/along
   misses.
2. **REGION / ABSTRACT relations** (the IDS-style operators): **CONTAINMENT/enclosure (inside)** + **RELATIVE
   POSITION (ordinal above/below/left/right)** — cheap bbox/centroid tests, the most deformation-robust +
   character-distinctive, and available even when junctions are thin.

## Cluster A — junction taxonomy / contact graph (Huffman/Clowes/Waltz)
Line-drawing structure is carried by JUNCTIONS (Huffman 1971; Clowes 1971; Waltz 1975). Taxonomy + what each
encodes: **L** (2 edges) = free endpoint corner (weak); **Y/arrow** (3) = a corner/fork where parts converge;
**T** (3, one edge meets another's side) = the richest local cue — OCCLUSION/CONTACT/TOUCHING (one stroke abuts
or passes behind another); **X** (4) = two contours CROSS, neither terminating. A drawing's relational structure
= the ATTRIBUTED RELATIONAL GRAPH (strokes=nodes, junctions=typed edges; standard in online Chinese/Hangul
recognition — Kim & Kim 2001). ROBUST-DISCRIMINATIVE: topology survives deformation, metric does not (Lobaton et
al. ICCV 2011) — which strokes touch/cross which + the cyclic edge-order around a junction are writer-invariant;
raw angles/distances are fragile. MINIMAL vocabulary beyond start/end/along = {end-free(L), corner(Y/arrow),
touch(T), cross(X)} + connectivity; correspond parts by junction-type + cyclic order (topological).

## Cluster B — stroke/part relations; the abstract operators that make characters distinctive
BPL's relation set (Lake 2015) = independent/start/end/along — deliberately minimal, and DOCUMENTED THIN:
Feinman & Lake (GNS 2021) — "strokes generated largely independently in the prior … new characters lack the rich
correlation structure of human drawings." The richer vocabulary (sketch/diagram/graphics recognition):
connection, intersection/crossing, tangency, **CONTAINMENT/enclosure (inside)**, parallelism, **RELATIVE POSITION
(above/below/left/right, NE/NW/…)**, collinearity, symmetry/repetition. STRONGEST evidence relations beyond local
junctions are character-defining: Chinese **IDS (Ideographic Description Sequences)** — ~12 structural operators
(left-right ⿰, top-bottom ⿱, surround/enclosure ⿴, …); zero-shot HCCR recognizes UNSEEN characters from radicals
+ these RELATIVE-POSITION + CONTAINMENT operators (Cao 2020; STAR 2210.08490; Formation-Tree 2404.12693). The
convergent answer for cheap+distinctive+deformation-robust cross-writer one-shot: **RELATIVE POSITION (ordinal) +
CONTAINMENT** — invariant to metric jitter/scale/slant, computable as integer comparisons over part
bounding-boxes/centroids (no trajectory needed), exactly what survives thin Omniglot traces; + symmetry/repetition
(Tian et al. 2020 abstract structure).

## Cluster C — cheap LOCAL geometric detection + the defined-residual graph form
Each relation = an O(1) test per sub-stroke pair (whole pass O(n²) over a handful of parts):
- CONTACT/attach: point-to-segment distance from B's endpoint to A's polyline < stroke-width-relative ε; arc-length
  t of nearest point → start/end/along.
- CROSSING/X: segment-segment intersection by the ORIENTATION (signed-area / cross-product) straddle predicate
  (sign tests, no division, O(1)); interior-vs-endpoint from the intersection params.
- T vs X vs TANGENT: same contact, disambiguated by the tangent-ANGLE of the two local directions + interior-vs-
  endpoint (perp + interior-interior → X; perp + one endpoint terminates → T = occluder/occluded; small angle →
  tangent/collinear). Angle = atan2, O(1).
- CONTAINMENT: bbox prefilter, then WINDING NUMBER (robust) or ray-cast parity — is B's centroid inside a closed
  loop of A. O(|loop|).
- RELATIVE POSITION: sign of bbox-centroid difference → above/below/left/right. O(1).
- PARALLELISM/COLLINEARITY: dot/cross of unit directions (+ perpendicular offset). O(1).
DEFINED-RESIDUAL / GRAPH FORM: emit edge(A→B, type ∈ {contact,X,T,tangent,contains,above,left,parallel,…},
attrs={t, angle, side, confidence}). Each detector returns a TYPED, confidence-scored edge → slots into the
residual algebra; richer/learned detectors compose on the SAME edge slot as a defined residual (additive, gated).
ROBUSTNESS: topology-first (crossing/containment/T-vs-X/contact survive deformation); metrics (exact angle/offset)
as SOFT/QUANTIZED attributes, not hard keys; stroke-width-relative thresholds → scale-invariance free.

## Convergent conclusion (for the jabberwock to design from — NOT prescribed)
Enrich sub-stroke relation perception with cheap O(1)-per-pair geometric detectors emitting TYPED,
confidence-scored, attributed EDGES (defined residuals on the relation-graph the order-invariant binder already
consumes): the TOPOLOGICAL contact set {L, Y/arrow, T, X} + the ABSTRACT/region set {containment, relative-
position above/below/left/right} (the IDS-style operators — the strongest cheap+robust+distinctive lever, and
available when junctions are thin). Topology-first, metrics as soft attributes, stroke-width-relative thresholds.
This composes: it feeds the held order-invariant binder (richer relation-pattern per part → StructSim discriminates
→ better correspondence) with NO change to the algebra — purely a richer, cheap, graph-native PERCEPTION layer
with defined-residual edges. CONTROL/GATE: (1) the enriched perception DETECTS the richer relations on real
traces (T/X/contain/relative-position present where the thin perception saw only free/end); (2) the order-
invariant binder corresponds same-class parts BETTER with the richer relations (discrimination ↑); (3) LIFT:
recognition-by-generation rises from 33.4% toward ~78, in-route (≤~78, no deep-route drift — relations stay
structural/topological, never holistic features); (4) CHEAP (O(n²) pairwise, O(1) tests; report cost); (5)
defined-residual (relations are typed edges that compose); (6) regressions intact. HONEST: in-route lever toward
~78; the win is the CAPABILITY (cheap graph-native richer relation perception with defined residuals), not the
number; run on the trace; don't tune to a target.

### Key sources
Huffman 1971; Clowes 1971; Waltz 1975 (junction labeling); Kim & Kim 2001 (Hangul relational graphs); Lobaton et
al. 2011 (topological deformation-invariant matching); Lake, Salakhutdinov & Tenenbaum 2015 (BPL relations);
Feinman & Lake 2021 (GNS — BPL relation thinness); Tian et al. 2020 (abstract structure: symmetry/repetition);
Unicode IDS / cjkvi-ids; Cao 2020 / STAR 2210.08490 / Formation-Tree 2404.12693 (zero-shot HCCR from radicals +
relative-position/containment); computational geometry: orientation/straddle segment-intersection, point-in-polygon
(winding vs ray-cast); Bone et al. 2017 (stroke-level T/X occluder-occluded).

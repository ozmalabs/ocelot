# Bigville high induced-boundary-width preregistration

## Question

Does exact component-message inference remain correct as explicit boundary interaction width rises, and does variable-elimination cost follow induced width rather than only boundary cardinality?

## Workload

Use deterministic Bigville authored CAN cast prefixes N=12/20 and three fresh workers. For each worker pattern, select one Concept boundary node from each of the first k residents, k∈{2,4,6,8}. Endpoint topic is respectively `trust_mayor`, `world_safe`, or `claim_credible`. Add cross-resident pairwise factors according to topology: `chain` (adjacent boundary nodes), `cycle` (adjacent plus closing edge for k≥3; k=2 equals chain), and `clique` (all unordered pairs). Factor weights are assigned in sorted endpoint order by repeating `(0.25,-0.25,0.5,-0.2,0.35,-0.3,0.15)`. Add each factor as reciprocal native edges with a shared weight. This produces 3 topologies × 4 boundary sizes × 2 graph sizes × 3 worker replications = 72 cases.

## Algorithm and measurements

Discover B from controlled cross-link endpoints, then remove B and BFS the extracted graph to discover interior components. Build exact component messages over each component's adjacent boundary interface. Form min-sum factors from the boundary unary terms, boundary-only pairwise factors, and component message tables. Run deterministic min-fill elimination with argmin backpointers; recover the complete global state and component argmins. Compare with whole-graph min-fill/JT and independently score both full states.

Record induced boundary width, bucket scope/rows/table sizes, message assignments, exhaustive `d^k` reference counts, global graph width, message+boundary timing, global JT timing, and full setup/extraction timings separately. Independently reconstruct the boundary elimination order and bucket work from captured factor scopes.

## Gates and interpretation limits

Require 72 complete cases, three fresh PIDs, unchanged source/build locks, exact boundary sizes, no cross-interior factor after removing B, valid component interfaces, reconstructed message and VE counts, complete domain-valid states, and energy agreement to 1e-7. This is a controlled synthetic augmentation of authored models, not natural boundary prevalence or production scheduler measurement. The sweep only reaches k=8; high-width cost beyond this is a projection, not measured evidence.

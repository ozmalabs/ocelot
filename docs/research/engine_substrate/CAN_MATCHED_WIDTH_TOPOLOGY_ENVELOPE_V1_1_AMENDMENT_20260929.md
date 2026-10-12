# Matched-width topology envelope v1.1 generator amendment (2026-09-29)

The v1 capture completed but failed its fixed-width-certificate gate only for `qtree_random`. Source inspection found the generator selected an existing (q+1)-clique directly as the attachment set, rather than selecting a q-vertex subset. This generated higher-width graphs and did not implement the preregistered random q-tree family. The v1 lock, 144-row capture, and failed gate are retained; its qtree_random rows are excluded from matched-width conclusions.

V1.1 samples exactly q vertices from a seeded existing (q+1)-clique before attaching each new vertex. This restores the declared q-tree construction. Other families, node count, random relabelling, metrics, and gates are unchanged. V1.1 requires a new lock and a full fresh 144-case replication.


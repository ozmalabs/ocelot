# Preregistration: forest ordering versus generic min-fill

**Question.** On runtime-extracted path graphs, can a forest-specific leaf-elimination order preserve exact MAP while reducing the ordering cost measured in the width-one scale check?

**Design.** The paired runner uses the same 2-state graph generator and seed formula as the preceding scale check at n=256, 512, 1,024, and 2,048, with two replicates per size in fresh worker processes. It extracts each graph once, computes generic min-fill and a leaf-stripping perfect elimination order, then runs exact junction-tree MAP under both orders on the same extracted factors.

**Measures.** Ordering time by method, MAP time under each order, induced width/bag size, exact energy agreement, and paired raw times. This comparison is for the path/forest family only.

**Pass criteria.** Both orders must induce width one, both MAP results must have equal energy and bag size two, and all eight paired workers must complete. No minimum speedup is required. Any incorrect elimination order or output disagreement is a failed result.

**Amendment boundary.** The previous width-one scale run motivates this comparison but does not contribute new confirmatory observations here. This runner and lock are frozen before the paired run.

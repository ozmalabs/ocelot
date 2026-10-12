# Thoughtexperiment recurrence allocator reclamation v1 preregistration

Measure glibc-accounted allocation and Linux process residency through the corrected one-million-node recurrence repair lifecycle. Cross the existing full-copy/shared-graph-pages backends with three fresh-process repetitions per backend. Reuse the controlled single-guard fault and require exact authored-rule restoration, one recurrence offer, zero-progress fixed point, and unchanged primary graph/rules/revision.

Collect `mallinfo2` arena, in-use (`uordblks+hblkhd`), free-arena, and mmap bytes with `smaps_rollup` at fixture baseline, during the live branch, after explicitly deleting branch and inner-substrate references and running Python GC, and after `malloc_trim(0)`. Report medians and individual runs. The glibc counters are process-wide and omit or aggregate allocator-managed suballocations imperfectly; PSS is residency, not live bytes. `malloc_trim` may release pre-existing free arena pages, so below-baseline post-trim values are not branch-specific savings.

All six workers must be fresh PIDs with stable source/native provenance and pass semantic/isolation gates. This one-host recurrence fixture does not support a universal allocator-reclamation claim or a graph-storage attribution claim. Preserve the prior v1.1 memory capture and lock.

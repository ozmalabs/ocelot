# Full-read extract plan — the Jabberwock reads a corpus larger than RAM

The agent can now read a corpus far larger than its resident graph, because its
memory faculty is an OS memory hierarchy and the grown corpus is DEMAND-PAGED to
an mmap bulk store. This is the plan the parent runs to extract a full read.

## The loop (per article)

```
consume (wikipedia_consumption.consume_article, source_text or wiki_local slab)
   -> READ + EXTRACT + GROUND + GATE + TEACH the microtheory   (unchanged)
   -> the cluster (Microtheory + has_concept Concepts) enters the WORKING SET
   -> page_consumed(gvm, agent, result) registers the cluster (keyed by topic)
   -> gvm.enforce()  : while node_count > memory_bound budget (or bytes over),
                       page the COLDEST cluster (LRU) OUT to the corpus slab
                       (graph_to_dict wire bytes -> reference_slab, then evict)
```

On FOVEATION (a topic comes into focus — concept_graph / a gap-goal needs it):

```
gvm.foveate(topic)
   -> mmap O(log n) slab lookup (reference_slab.Slab.lookup)
   -> decode the wire bytes, re-install the cluster into the live graph
   -> mark it hot (LRU touch)
```

## Properties (all gated in tests/test_graph_virtual_memory.py, donkey=0)

- **Resident bounded.** The live graph holds only the working set; `memory_bound`
  drives page-out, so resident node count PLATEAUS at the budget no matter how
  many articles are consumed (demonstrated: 80 articles, resident flat at 24,
  corpus grew to 78 records). No OOM; the read is **throughput-limited only**
  (disk write of the slab), never memory-limited.
- **Corpus mmap'd, not a JSON heap.** Page-out target is a `reference_slab`
  (`.keys` + `.vals`, binary-searchable over the mmap). Page-in touches O(log n)
  index pages + one value page — query-time RSS is the working set, not the
  corpus.
- **Byte-identical.** A cluster round-trips through the substrate's own wire
  format (`graph_to_dict`) in canonical (id-independent) form, so page-out ->
  page-in loses no data. Re-reading a topic is exact.
- **Kernel resident.** The lexicon (never_forget) is never registered as a
  cluster and is type-guarded, so it never pages out — the agent never loses its
  language while paging domain knowledge.

## Order and resumability

- **Gap/importance-driven order.** Which topics to foveate (page in) next is the
  agent's own signal — a `concept_graph` gap, a goal that needs a region. The
  paging layer only serves the working set for whatever the agent focuses on.
- **LRU eviction.** The coldest cluster (a HotCounter last-access mirror) is paged
  out first, so an active region stays resident while dormant knowledge sleeps on
  disk.
- **Resumable.** The corpus slab IS the durable store; a run can stop and restart,
  re-open the slab, and page any topic back in. Combined with the seed manifests
  (`seeds/acquired/`) the teach path already persists, a full read is checkpointed
  and resumable — no re-read needed for knowledge already on disk.

## Running a full read (parent)

1. Boot the agent (`WorldAdapter` + `load_all_seeds`).
2. Construct `GraphVirtualMemory(agent.s, corpus="corpus", budget_nodes=..., budget_bytes=...)`
   sized to the RAM you want the working set to occupy.
3. Stream titles through `wikipedia_consumption.consume(agent, titles=..., gvm=gvm)`
   (or `consume_article` + `page_consumed` + `gvm.enforce()` per article).
4. Foveate on demand (`gvm.foveate(topic)`) whenever the agent's gap/goal needs a
   region; the working set stays bounded, the corpus grows on disk.

The only ceiling is disk throughput and disk size — memory is bounded by
construction.

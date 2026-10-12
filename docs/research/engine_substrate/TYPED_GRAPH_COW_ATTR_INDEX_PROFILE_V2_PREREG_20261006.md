# TypedGraph attribute-index COW profile v2 preregistration

Date: 2026-10-06

## Question

Does sharding the attribute index at both `(node_type, attr_key)` and value levels reduce fork cost for high-cardinality indexes, while preserving exact indexed queries?

## Measurement

Build one `Concept`-shaped population at each of N = 7,164, 16,384, and 50,771, with one distinct integer value per node and one declared attribute index. For each fixture, measure 51 paired repetitions of shallow COW index clone and an explicit eager copy of every index/value bitmap. The existing native profile keeps timing outside graph construction and verifies every indexed value returns exactly its one expected node. Capture the node count, indexed value count, entry count, both medians, source hashes, compiler version, and binary hash.

This isolates the attribute-index representation. It does not measure whole-Substrate fork, branch first-write cost, index mutation throughput, allocator bytes, or application closure. Do not promote the design from fork-only timing; those are required follow-up gates.

## Gate

All three fixture sizes must preserve exact query results; every recorded row must match the source and binary lock. Report eager/shallow clone costs independently, without inferring end-to-end thoughtexperiment speed. A follow-up mutation gate must determine whether touched-shard copying erases the fork gain.

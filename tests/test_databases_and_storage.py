"""databases_and_storage Mt + 9 decomposition packs."""
from __future__ import annotations

import pytest
from substrate_rs import _native


_NODE_TYPES = (
    "Microtheory", "Concept", "Rule",
    "DesignPattern", "ProgrammingLanguage", "CodeTarget",
    "DesignExclusion", "LanguageExclusion", "LanguageScoringConfig",
    "CodeWritingCortex", "CodeAuthoringRoot", "Reflex",
    "ReplacementTarget", "CodeDraft", "ValidationResult",
    "CodeInstallation",
)
_EDGE_TYPES = (
    "genlMt", "has_concept", "has_rule", "owns_microtheory",
    "owns_root", "has_reflex", "current_target", "has_draft",
    "validated_by", "installed_as", "authored_in", "uses_pattern",
    "subClassOf", "in_category", "decomposes",
)


def _fresh_substrate():
    s = _native.Substrate()
    for src_t in _NODE_TYPES:
        for tgt_t in _NODE_TYPES:
            for et in _EDGE_TYPES:
                s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et, "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "test:open",
                })
    s.add_node("Microtheory", {"name": "compiler_theory"})
    return s


def test_db_installs_with_genlmt():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "databases_and_storage")
    assert mt is not None
    assert s.node(mt)["attrs"]["name"] == "databases_and_storage"
    parents = {s.node(p)["attrs"]["name"]
               for p in s.neighbours(mt, "genlMt")}
    assert "compiler_theory" in parents


def test_db_carries_foundation():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "databases_and_storage")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("relational_model", "ACID", "BASE", "CAP_theorem",
                     "PACELC_theorem"):
        assert required in names


def test_db_carries_transactions():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "databases_and_storage")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("transaction", "serializable_isolation",
                     "repeatable_read", "read_committed",
                     "read_uncommitted", "snapshot_isolation",
                     "write_skew_anomaly", "two_phase_locking", "MVCC"):
        assert required in names


def test_db_carries_storage_engines():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "databases_and_storage")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("write_ahead_log", "checkpointing", "LSM_tree",
                     "memtable", "SSTable", "compaction",
                     "write_amplification", "read_amplification",
                     "space_amplification", "bloom_filter_DB",
                     "page_oriented_storage"):
        assert required in names


def test_db_carries_query_processing():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "databases_and_storage")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("query_parser", "query_planner", "query_optimizer",
                     "cost_based_optimization", "query_execution_engine",
                     "volcano_iterator_model", "vectorized_execution",
                     "hash_join", "sort_merge_join", "nested_loop_join"):
        assert required in names


def test_db_carries_indexes():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "databases_and_storage")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("primary_index", "secondary_index", "covering_index",
                     "composite_index", "hash_index", "inverted_index",
                     "spatial_index", "bitmap_index"):
        assert required in names


def test_db_carries_replication_sharding():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "databases_and_storage")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("primary_replica_replication",
                     "synchronous_replication",
                     "asynchronous_replication", "multi_primary",
                     "quorum_replication", "Raft_consensus",
                     "Paxos_consensus", "hash_sharding",
                     "range_sharding", "consistent_hashing",
                     "directory_based_sharding"):
        assert required in names


def test_db_carries_specific_systems():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "databases_and_storage")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("PostgreSQL", "MySQL_InnoDB", "SQLite", "Redis",
                     "Memcached", "DynamoDB", "MongoDB", "Cassandra",
                     "HBase", "RocksDB", "etcd", "ClickHouse", "DuckDB",
                     "Snowflake", "BigQuery", "Redshift",
                     "Apache_Spark", "Trino_Presto", "Apache_Kafka",
                     "Apache_Flink", "Pinecone", "Qdrant", "pgvector",
                     "InfluxDB", "Prometheus", "TimescaleDB", "Neo4j",
                     "Elasticsearch"):
        assert required in names


def test_db_carries_storage_formats():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "databases_and_storage")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("CSV", "JSON", "JSONL_NDJSON", "YAML", "TOML",
                     "XML", "Parquet", "ORC", "Apache_Avro",
                     "Apache_Arrow", "MessagePack", "BSON", "CBOR",
                     "Capn_Proto", "FlatBuffers", "HDF5",
                     "Apache_Iceberg", "Delta_Lake", "Apache_Hudi"):
        assert required in names


def test_db_carries_compression_encoding():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "databases_and_storage")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("Snappy", "LZ4", "Zstandard", "gzip_bzip2",
                     "Brotli", "run_length_encoding",
                     "dictionary_encoding", "bit_packing",
                     "delta_encoding", "frame_of_reference",
                     "schema_evolution"):
        assert required in names


def test_db_rules_carry_soundness_category():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "databases_and_storage")
    valid = {"denotational_equivalence", "algebraic_law",
             "extensional_equivalence", "cost_equivalence",
             "referential_transparency"}
    n_with_cat = 0
    for r in s.neighbours(mt, "has_rule"):
        if s.node(r)["attrs"].get("soundness_category") in valid:
            n_with_cat += 1
    assert n_with_cat >= 18


def test_db_decomposition_packs_load():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    load_one_seed(s, "databases_and_storage")
    ids = install_all_concept_expansions(s)
    for required in ("lsm_tree_decomposition", "mvcc_decomposition",
                     "query_optimization_decomposition",
                     "parquet_format_decomposition",
                     "text_formats_decomposition",
                     "table_formats_decomposition",
                     "distributed_consensus_decomposition",
                     "vector_index_decomposition",
                     "columnar_storage_decomposition"):
        assert required in ids, f"DB pack {required!r} not loaded"


def test_db_pack_sub_mechanisms_mount():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = load_one_seed(s, "databases_and_storage")
    install_all_concept_expansions(s)
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    # LSM tree
    for n in ("active_memtable", "immutable_memtable", "L0_SSTables",
              "leveled_compaction", "tiered_compaction",
              "compaction_priority", "tombstone", "block_cache",
              "level_size_multiplier", "bloom_filter_per_sstable",
              "merge_iterator", "manifest_log"):
        assert n in names
    # MVCC
    for n in ("xmin_xmax_postgres", "transaction_id_xid",
              "snapshot_at_transaction_start", "heap_only_tuple_HOT",
              "version_chain", "vacuum_old_versions",
              "vacuum_freeze", "oracle_undo_segment",
              "serializable_snapshot_isolation"):
        assert n in names
    # Query optimization
    for n in ("table_statistics", "histogram_estimation",
              "most_common_values_MCV", "join_selectivity",
              "join_order_DP", "genetic_query_optimisation",
              "predicate_pushdown", "subquery_unnesting",
              "materialized_view_rewriting", "plan_caching"):
        assert n in names
    # Parquet
    for n in ("file_structure", "row_group", "column_chunk",
              "page_within_chunk", "dictionary_encoding_parquet",
              "RLE_in_parquet", "bit_packing_parquet",
              "snappy_zstd_compression_parquet",
              "column_statistics", "bloom_filter_in_parquet",
              "Dremel_nested_schema", "predicate_projection_pushdown"):
        assert n in names
    # Text formats
    for n in ("CSV_quoting", "CSV_header_optional",
              "CSV_type_inference", "JSON_data_model",
              "JSONL_NDJSON_streaming", "JSON_schema",
              "YAML_indentation_significance", "YAML_norway_problem",
              "YAML_anchors_aliases", "TOML_syntax",
              "XML_attributes_vs_elements"):
        assert n in names
    # Table formats
    for n in ("manifest_file", "snapshot",
              "atomic_commit_pointer_swap", "time_travel_queries",
              "iceberg_hidden_partitioning", "delta_log_transaction",
              "hudi_copy_on_write", "hudi_merge_on_read",
              "engine_interoperability"):
        assert n in names
    # Consensus
    for n in ("leader_election", "term_number", "log_replication",
              "majority_quorum", "log_matching_property",
              "FLP_impossibility", "Paxos_basic_protocol",
              "Multi_Paxos_optimisation", "Byzantine_fault_tolerance",
              "EPaxos_leaderless", "flexible_paxos", "CRDT"):
        assert n in names
    # Vector indexes
    for n in ("ANN_approximate_nearest_neighbor",
              "HNSW_layered_graph", "HNSW_M_parameter",
              "HNSW_ef_construction", "HNSW_ef_search",
              "IVF_inverted_file", "IVF_nprobe",
              "product_quantization", "ScaNN_google",
              "filtered_ANN"):
        assert n in names
    # Columnar
    for n in ("row_vs_column_layout", "SIMD_on_columns",
              "column_compression", "late_materialisation",
              "vectorized_filter_operator", "vectorized_aggregation",
              "vectorized_hash_join", "selection_vector",
              "ClickHouse_MergeTree",
              "MPP_massively_parallel_processing"):
        assert n in names


def test_total_db_concept_count():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = load_one_seed(s, "databases_and_storage")
    install_all_concept_expansions(s)
    n_concepts = len(s.neighbours(mt, "has_concept"))
    n_rules = len(s.neighbours(mt, "has_rule"))
    assert n_concepts >= 215, f"only {n_concepts} concepts"
    assert n_rules >= 60, f"only {n_rules} rules"

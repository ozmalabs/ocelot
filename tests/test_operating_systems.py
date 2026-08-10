"""operating_systems Mt + 8 decomposition packs."""
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


def test_os_installs_with_genlmt():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "operating_systems")
    assert mt is not None
    assert s.node(mt)["attrs"]["name"] == "operating_systems"
    parents = {s.node(p)["attrs"]["name"]
               for p in s.neighbours(mt, "genlMt")}
    assert "compiler_theory" in parents


def test_os_carries_foundation():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "operating_systems")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("process", "thread", "kernel_space", "user_space",
                     "system_call", "context_switch", "interrupt",
                     "exception"):
        assert required in names


def test_os_carries_process_management():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "operating_systems")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("PID_process_identifier", "process_group",
                     "session", "fork", "exec", "wait_waitpid",
                     "zombie_process", "daemon", "nice_priority"):
        assert required in names


def test_os_carries_threading():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "operating_systems")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("POSIX_threads", "kernel_thread", "user_thread",
                     "M_N_threading", "thread_local_storage",
                     "thread_pool", "work_stealing"):
        assert required in names


def test_os_carries_synchronization():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "operating_systems")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("mutex", "spinlock", "reader_writer_lock",
                     "semaphore", "condition_variable", "barrier",
                     "futex", "atomic_operations_OS", "lock_free",
                     "wait_free", "ABA_problem", "deadlock", "livelock",
                     "starvation", "priority_inversion"):
        assert required in names


def test_os_carries_scheduling():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "operating_systems")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("preemptive_scheduling", "cooperative_scheduling",
                     "CFS_completely_fair_scheduler",
                     "real_time_scheduling", "CPU_affinity",
                     "load_balancing", "NUMA_aware_scheduling"):
        assert required in names


def test_os_carries_ipc():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "operating_systems")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("pipe", "named_pipe_FIFO", "unix_domain_socket",
                     "shared_memory", "signal", "signal_handler",
                     "message_queue"):
        assert required in names


def test_os_carries_virtualization():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "operating_systems")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("linux_namespace", "cgroups", "container",
                     "docker", "kubernetes", "hypervisor_type_1",
                     "hypervisor_type_2", "KVM_kernel_virtual_machine",
                     "microVM_Firecracker", "VirtIO"):
        assert required in names


def test_os_rules_carry_soundness_category():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "operating_systems")
    valid = {"denotational_equivalence", "algebraic_law",
             "extensional_equivalence", "cost_equivalence",
             "referential_transparency"}
    n_with_cat = 0
    for r in s.neighbours(mt, "has_rule"):
        if s.node(r)["attrs"].get("soundness_category") in valid:
            n_with_cat += 1
    assert n_with_cat >= 18


def test_os_decomposition_packs_load():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    load_one_seed(s, "operating_systems")
    ids = install_all_concept_expansions(s)
    for required in ("threading_deep_dive_decomposition",
                     "fork_exec_lifecycle_decomposition",
                     "cfs_scheduler_decomposition",
                     "sync_primitives_decomposition",
                     "ipc_mechanisms_decomposition",
                     "namespaces_cgroups_decomposition",
                     "vfs_page_cache_decomposition",
                     "hypervisor_decomposition",
                     "memory_reclaim_decomposition"):
        assert required in ids, f"OS pack {required!r} not loaded"


def test_os_pack_sub_mechanisms_mount():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = load_one_seed(s, "operating_systems")
    install_all_concept_expansions(s)
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    # Threading deep dive
    for n in ("goroutine", "Go_GMP_model", "goroutine_park_unpark",
              "netpoller", "preemptive_goroutine_scheduling",
              "goroutine_stack_growth", "virtual_thread_loom",
              "continuation", "Erlang_BEAM_scheduler",
              "actor_model", "async_runtime_tokio", "task_polling"):
        assert n in names
    # Fork/exec
    for n in ("fork_copy_on_write", "fork_fd_inheritance",
              "exec_image_replacement", "CLOEXEC_flag",
              "wait_exit_status", "orphan_process",
              "double_fork_daemon_pattern", "posix_spawn",
              "clone_syscall"):
        assert n in names
    # CFS
    for n in ("vruntime", "red_black_tree_runqueue",
              "nice_to_weight", "sched_period",
              "sched_min_granularity", "wakeup_preemption",
              "group_scheduling", "load_tracking",
              "CPU_load_balancing", "isolcpus"):
        assert n in names
    # Sync primitives
    for n in ("futex_uncontended_path", "FUTEX_WAIT", "FUTEX_WAKE",
              "pthread_mutex_via_futex", "RCU_read_copy_update",
              "RCU_grace_period", "seqlock", "wait_queue",
              "memory_barrier_in_locks", "MCS_lock"):
        assert n in names
    # IPC
    for n in ("anonymous_pipe", "unix_socket_stream",
              "fd_passing_SCM_RIGHTS", "shm_open_memfd",
              "eventfd", "signalfd", "timerfd",
              "shared_memory_with_futex"):
        assert n in names
    # Namespaces / cgroups
    for n in ("PID_namespace", "mount_namespace",
              "network_namespace", "user_namespace",
              "UTS_namespace", "IPC_namespace",
              "cgroup_v1_hierarchy", "cgroup_v2_unified",
              "cgroup_cpu_controller", "cgroup_memory_controller",
              "clone_CLONE_NEW_flags", "setns_join_namespace"):
        assert n in names
    # VFS + page cache
    for n in ("VFS_operations_struct", "dcache_dentry_cache",
              "inode_cache", "page_cache_per_inode",
              "read_path_through_cache", "write_path_dirty_pages",
              "writeback_kernel_threads", "fsync_durability",
              "O_DIRECT_bypass", "sendfile_zero_copy"):
        assert n in names
    # Hypervisor
    for n in ("VT_x_AMD_V_hardware_virt", "VMX_root_non_root",
              "VMEXIT_VMENTRY", "EPT_NPT_nested_page_tables",
              "KVM_kernel_module", "QEMU_device_emulation",
              "VirtIO_paravirtualisation", "vCPU_thread",
              "SR_IOV_pass_through", "microVM_minimal_device_set"):
        assert n in names
    # Memory reclaim
    for n in ("anonymous_pages", "file_backed_pages", "kswapd",
              "direct_reclaim", "watermark_min_low_high",
              "page_LRU_lists", "shrinker_callbacks",
              "swap_to_disk", "OOM_score_adj",
              "OOM_killer_algorithm", "memory_cgroup_OOM"):
        assert n in names


def test_total_os_concept_count():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = load_one_seed(s, "operating_systems")
    install_all_concept_expansions(s)
    n_concepts = len(s.neighbours(mt, "has_concept"))
    n_rules = len(s.neighbours(mt, "has_rule"))
    assert n_concepts >= 175, f"only {n_concepts} concepts"
    assert n_rules >= 55, f"only {n_rules} rules"

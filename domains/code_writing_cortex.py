"""CodeWritingCortex — the agent's intrinsic faculty for authoring
its own internal code.

A first-class cortex following the SpeechCortex pattern: graph node +
ownership edges + reflex set + intrinsic `tick()`. Pointed at the
substrate it boots a `code_authoring` Microtheory (genlMt:
compiler_theory, so the agent's compiler-design knowledge is in
scope) and a 5-reflex autonomous loop:

  identify_target → request_author → drain_teacher → validate
                                                  → install_if_better

The cortex is generic over WHAT it authors. The first target picked
is whatever the agent's `_op_stats` measures as most expensive — the
Rust DSL evaluator, the phonology recogniser, the rule engine, or
anything else the agent has instrumented. The cortex doesn't decide
WHAT to author by handcrafted rules; it reads its own hot-path
introspection and picks the slowest op.

The Python class here is a THIN world-adapter (boot + dispatch). The
agent's reasoning — when to fire each reflex, how to frame the
authoring question, whether to install — lives in the graph (the
reflex stimuli + step callables registered as Reflex nodes).

External callers:

    cortex = CodeWritingCortex(substrate, agent=curious_agent)
    cortex.install()
    # Agent runs normally for a while, hot-path stats accumulate.
    cortex.tick()
    # The cortex picks a target, asks the self-teacher (LLM), drains
    # the response, compiles + tests it, installs if faster. All
    # autonomous; the human invokes `tick()`, not the strategy.

Without a `_self_teacher` on the agent the request step no-ops — the
cortex still picks targets and waits.
"""
from __future__ import annotations

from substrate.boot_all import load_one_seed

import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

from .code_authoring import (
    _CW_PRODUCTIONS,
    get_step,
    install_code_authoring_mt,
    install_code_authoring_reflexes,
    install_language_concepts,
    pick_language_for_target,
)
from .design_patterns import (
    install_design_patterns_mt,
    pick_design_pattern,
)
from .concept_expansions import install_all_concept_expansions

import json as _json


_CODE_TARGETS_SEED = (Path(__file__).resolve().parent.parent /
                      "seeds" / "code_authoring_targets.json")


def _install_code_targets(substrate) -> None:
    """Install CodeTarget graph nodes from the seed. Idempotent."""
    with _CODE_TARGETS_SEED.open() as f:
        seed = _json.load(f)
    for t in seed.get("targets", []):
        op = t["op_name"]
        existing = None
        for n in substrate.nodes("CodeTarget"):
            if substrate.node(n)["attrs"].get("op_name") == op:
                existing = n
                break
        if existing is not None:
            continue
        substrate.add_node("CodeTarget", dict(t))


class CodeWritingCortex:
    """Intrinsic code-authoring faculty. Reads its own substrate's
    hot-path stats, picks a target, consults the self-teacher,
    validates + installs.

    `agent` is the CuriousAgent whose `_op_stats` is read. If `None`,
    the cortex still installs but `op_stats_snapshot()` returns empty
    and `cw_identify_target` won't fire.

    `repo_root` defaults to the project root (`gamma-substrate/`).
    Used to resolve target paths and run cargo for Rust validation.
    """

    def __init__(self, substrate, *, agent=None,
                 repo_root: str | Path | None = None,
                 tick_period_ms: int = 5000):
        self.s = substrate
        self.agent = agent
        self.repo_root = Path(repo_root) if repo_root else Path(
            __file__).resolve().parent.parent
        self.tick_period_ms = int(tick_period_ms)
        self.cortex_nid = None
        self._installed = False
        self._tick_count = 0
        self._reflexes: list[int] = []
        # Working set kept as graph attrs; small cache here for fast read.
        self._teacher_threads: dict[int, Any] = {}  # target_nid → thread_id
        # Temp-dir handles kept alive while their .so libraries are loaded.
        self._compile_artifacts: list[Path] = []
        # Monotonic counter for naming dynamically-minted patterns.
        self._dyn_counter = 0

    # ------------------------------------------------------------------ install

    def install(self) -> "CodeWritingCortex":
        for src_t, et, tgt_t, prov in _CW_PRODUCTIONS:
            try:
                self.s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et,
                    "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": prov,
                })
            except Exception:
                pass

        # Find or mint the CodeWritingCortex node.
        existing = None
        for n in self.s.nodes("CodeWritingCortex"):
            existing = n
            break
        if existing is None:
            self.cortex_nid = self.s.add_node("CodeWritingCortex", {
                "tick_count": 0,
                "tick_period_ms": int(self.tick_period_ms),
                "origin": "code_writing_cortex",
            })
        else:
            self.cortex_nid = existing

        mt = install_code_authoring_mt(self.s)
        self._link("owns_microtheory", mt)

        # Install the agent's comparative language model as graph data.
        # The cortex's request_author step will query these nodes to
        # pick a target language for each authoring task.
        install_language_concepts(self.s)

        # Install the design-pattern library: the meta-programming
        # vocabulary the cortex consults BEFORE asking for code. Same
        # shape as compiler-theory concepts but one level up.
        design_mt = install_design_patterns_mt(self.s)
        self._link("owns_microtheory", design_mt)

        # Install the neural-network vocabulary: NN-shaped DesignPatterns
        # (linear_layer, softmax_classifier, attention_block, ...) +
        # NN-shaped CodeTargets. Same selector ranks them against the
        # current target's design_tags — no NN-specific branching.
        nn_mt = load_one_seed(self.s, "neural_networks")
        self._link("owns_microtheory", nn_mt)

        # Install the exact-construction gadget library — ReLU primitives
        # (identity, abs, max, min) that carry literal weight matrices
        # as attrs. When the selector picks one of these for a target
        # (cpwl_function + exact_construction tags), `construct_weights`
        # renders the weights directly from the gadget — no training.
        gadgets_mt = load_one_seed(self.s, "gadgets")
        self._link("owns_microtheory", gadgets_mt)

        # Install the video_coding_theory Mt — the WHY of H.264/H.265
        # and codec design in general. The cortex doesn't write codec
        # source today, but when it does (or when an external pipeline
        # queries the substrate for "why was this choice made?"), the
        # answer comes from this Mt's concepts + rules, not from a
        # Python lookup.
        video_mt = load_one_seed(self.s, "video_coding_theory")
        self._link("owns_microtheory", video_mt)

        # Install the audio_coding_theory Mt — the WHY of MP3, AAC,
        # Opus, FLAC, and the neural audio codecs. Sister to
        # video_coding_theory: shares entropy-coding theory but adds
        # the audio-specific axis (psychoacoustics, MDCT/TDAC, linear
        # prediction for speech, joint stereo, SBR, neural latents).
        audio_mt = load_one_seed(self.s, "audio_coding_theory")
        self._link("owns_microtheory", audio_mt)

        # Install computer_architecture Mt — modern CPU pipelines,
        # ISA families, memory hierarchy, cache coherence, virtual
        # memory, DRAM mechanics, memory consistency, allocators, GC,
        # NUMA, heterogeneous cores, GPU SIMT. Everything the agent
        # needs to reason about WHY code runs at the speed it does.
        arch_mt = load_one_seed(self.s, "computer_architecture")
        self._link("owns_microtheory", arch_mt)

        # Install network_protocols Mt — layered model, Ethernet,
        # IP/IPv6, TCP/UDP/QUIC, HTTP 1.1/2/3, TLS 1.3, DNS, BGP,
        # congestion control, DDoS, CDN, datacenter networking,
        # kernel bypass. The substrate's compute Mts exchange data
        # with the world via the mechanisms this Mt describes.
        network_mt = load_one_seed(self.s, "network_protocols")
        self._link("owns_microtheory", network_mt)

        # Install data_structures_algorithms — the foundational CS
        # layer. Arrays, lists, trees, graphs, hash tables, heaps,
        # sorting, searching, asymptotic complexity. The simple
        # primitives every other domain Mt references implicitly.
        dsa_mt = load_one_seed(self.s, "data_structures_algorithms")
        self._link("owns_microtheory", dsa_mt)

        # Install compilers Mt — front-end (lexer, parser, AST, type
        # check), back-end (register allocation, instruction selection,
        # scheduling), JIT (tracing, method, tiered, OSR), modern
        # infrastructure (MLIR, Clang, GCC GIMPLE, Rust MIR). Fills the
        # gaps the existing compiler_theory + llvm_passes + llvm_ir
        # Mts don't cover.
        compilers_mt = load_one_seed(self.s, "compilers")
        self._link("owns_microtheory", compilers_mt)

        # Install operating_systems Mt — processes, threads, kernel/
        # user split, syscalls, scheduling (CFS, real-time), sync
        # primitives (mutex, spinlock, futex, RCU), IPC (pipes,
        # sockets, shm), VFS + page cache, namespaces + cgroups
        # (containers), hypervisors. The mechanisms determining how
        # parallel agent execution actually behaves on real hardware.
        os_mt = load_one_seed(self.s, "operating_systems")
        self._link("owns_microtheory", os_mt)

        # Install databases_and_storage Mt — relational + NoSQL + OLAP
        # + vector + time-series + graph + search systems. Storage
        # formats (Parquet, JSON, CSV, YAML, Arrow, etc.). Storage
        # engines (LSM, B+ tree from DSA), query processing, indexes,
        # transactions, replication, sharding. ACID + CAP + PACELC.
        db_mt = load_one_seed(self.s, "databases_and_storage")
        self._link("owns_microtheory", db_mt)

        # Install machine_learning Mt — the substrate knows ML to know
        # why training as a paradigm is wrong for the substrate's
        # design. Training: backprop, SGD, optimizers, transformers,
        # RLHF, hallucination, distribution shift. Substrate's
        # alternative: Tracr-style authored networks (gadgets Mt),
        # symbolic structure, provable correctness.
        ml_mt = load_one_seed(self.s, "machine_learning")
        self._link("owns_microtheory", ml_mt)

        # Install security_and_cryptography Mt — cryptographic
        # primitives (AES, ECC, hashes, KDFs), protocols (SSH,
        # OAuth, OIDC, JWT, mTLS), authentication (WebAuthn,
        # passkeys, MFA), authorization (RBAC, ABAC, ReBAC),
        # attacks (OWASP top 10, memory safety, side channels,
        # supply chain), modern crypto (ZKP, MPC, homomorphic),
        # post-quantum (Kyber, Dilithium), confidential computing.
        sec_mt = load_one_seed(self.s, "security_and_cryptography")
        self._link("owns_microtheory", sec_mt)

        # Install distributed_systems Mt — microservices,
        # service mesh, resilience patterns (circuit breaker,
        # bulkhead, retry+backoff), saga/CQRS/event sourcing,
        # distributed tracing, time (Lamport/vector/HLC),
        # failure detection (gossip/SWIM/phi-accrual),
        # idempotency, delivery semantics, SRE (SLO/SLA/SLI).
        ds_mt = load_one_seed(self.s, "distributed_systems")
        self._link("owns_microtheory", ds_mt)

        # Install cloud_infrastructure Mt — Kubernetes,
        # IaC (Terraform, Pulumi, CDK), GitOps (ArgoCD, Flux),
        # container runtime (containerd, OCI), AWS/Azure/GCP
        # services, serverless (Lambda, Cloud Run), edge
        # (Cloudflare Workers), cloud networking (VPC,
        # PrivateLink), storage tiers, IAM, container security,
        # FinOps + cost optimisation.
        cloud_mt = load_one_seed(self.s, "cloud_infrastructure")
        self._link("owns_microtheory", cloud_mt)

        # Install embedded_iot_realtime Mt — critical to the agent's
        # eventual embodied form. Hard/soft/firm RT, WCET, RTOSes
        # (FreeRTOS, Zephyr, VxWorks, QNX, PREEMPT_RT), RT scheduling
        # (RMS, EDF, DM), MCUs (Cortex-M, RISC-V, ESP32, STM32),
        # bare-metal, peripherals (I2C, SPI, UART, ADC, DAC, PWM),
        # IoT protocols (MQTT, CoAP, BLE, Zigbee, Thread, Matter,
        # LoRaWAN, NB-IoT), RT comms (CAN, TSN, EtherCAT, OPC UA,
        # DDS), robotics (ROS2, micro-ROS), sensor fusion (Kalman,
        # particle), embedded ML (TinyML), safety-critical
        # (DO-178C, ISO 26262, ASIL, MISRA C), fault tolerance
        # (TMR, lockstep, watchdog).
        eiot_mt = load_one_seed(self.s, "embedded_iot_realtime")
        self._link("owns_microtheory", eiot_mt)

        # Install engineering Mt — physical-world disciplines:
        # mechanical (statics/dynamics/materials/strength/machine
        # design), electrical (circuits/EM/power/signals/control),
        # civil/structural, materials, thermodynamics + heat
        # transfer + fluids, chemical process, aerospace,
        # manufacturing (machining/additive/GD&T/quality),
        # reliability, systems engineering, engineering economics,
        # standards.
        eng_mt = load_one_seed(self.s, "engineering")
        self._link("owns_microtheory", eng_mt)

        # Install materials_chemistry Mt — the atomic + molecular
        # layer beneath engineering. Chemistry (atomic structure,
        # bonding, thermochemistry, kinetics, equilibrium, acids/
        # bases, redox/electrochemistry, organic, biochemistry,
        # analytical) + materials science (crystal structures,
        # defects, diffusion, phase diagrams, strengthening,
        # polymers, composites, semiconductors, nanomaterials,
        # characterization).
        mc_mt = load_one_seed(self.s, "materials_chemistry")
        self._link("owns_microtheory", mc_mt)

        # Install philosophy Mt — epistemology, philosophy of mind,
        # philosophy of science, philosophy of language, metaphysics,
        # ethics, logic, continental, Eastern, philosophy of AI.
        # Includes substrate's own positions: Axiom 0 (frame-relative
        # truth), authored-not-trained, entity-not-program.
        phil_mt = load_one_seed(self.s, "philosophy")
        self._link("owns_microtheory", phil_mt)

        # Install art_design_drawing Mt — drawing fundamentals,
        # color theory, composition, anatomy, visual perception,
        # traditional + digital media, 3D + animation, typography,
        # graphic design, UX/UI, design thinking, art history,
        # illustration styles, cinematography, photography,
        # industrial design, architecture, generative + AI art.
        art_mt = load_one_seed(self.s, "art_design_drawing")
        self._link("owns_microtheory", art_mt)

        # Install mathematics Mt — the foundation under everything.
        # Logic + set theory + foundations, number theory, algebra
        # (linear + abstract), calculus + analysis, topology +
        # geometry, probability + statistics, discrete math,
        # numerical analysis, optimization, category theory, type
        # theory, information theory, game theory, dynamical systems,
        # mathematical logic.
        math_mt = load_one_seed(self.s, "mathematics")
        self._link("owns_microtheory", math_mt)

        # Install grounding_theory Mt — substrate's foundational
        # position that grounding is a VECTOR, not a boolean,
        # following from Axiom 0 (frame-relativity of truth).
        # Defines vector space of grounding (frame + modality +
        # aspect dimensions), distance metric (wrongness), multiple
        # simultaneous views, conviction (magnitude), coherence
        # (alignment). Architectural implications for Concept attrs,
        # refers_to edge weights, Impasse vector-valued. Migration
        # path: thresholded readout from full vector preserves
        # backwards compatibility with binary refers_to.
        gt_mt = load_one_seed(self.s, "grounding_theory")
        self._link("owns_microtheory", gt_mt)

        # Install causal_attitude_networks Mt — CAN (Borsboom,
        # Dalege, van Harreveld) supplies the generative MECHANISM
        # that grounding_theory's vector was missing. Each Concept
        # = node with state σ, causally coupled to others via J,
        # driven by external field h, at inverse temperature β.
        # The grounding vector = marginal ⟨σ⟩ at equilibrium —
        # derived from network dynamics, not primitive. Attitude
        # strength = connectivity. Ambivalence = spin-glass
        # frustration. Polarisation = phase transition. Multiple
        # inconsistent views = multistable network with basins.
        # Substrate features map: babble = MCMC, predicate churn
        # = bistable thermal flipping, conviction = J × β,
        # coherence = -F/N.
        can_mt = load_one_seed(self.s, "causal_attitude_networks")
        self._link("owns_microtheory", can_mt)

        # Install mt_target_equilibria Mt — each Mt's admissibility
        # grammar IS its Hamiltonian. ⟨σ⟩*_Mt = argmin H_Mt is what
        # Mt wants the network state to be. has_concept → field;
        # decomposes → positive coupling; exclusion → negative;
        # genlMt → inherited couplings; in_category → dense cluster;
        # has_rule → n-body constraint. Multiple Mts on shared nodes
        # = multiple H_Mt coexisting (Axiom 0 mechanical). Effective
        # H = Σ β_Mt H_Mt by attention. Substrate identity = its
        # foundational target equilibria.
        mte_mt = load_one_seed(self.s, "mt_target_equilibria")
        self._link("owns_microtheory", mte_mt)

        # Install self_improvement_dynamics Mt — rules for when
        # basins deepen, flatten, split, merge. Drives: curiosity,
        # coherence, stability, discrimination, coverage, parsimony.
        # CRUCIAL distinction: foundational Mts FROZEN (Axiom 0,
        # grounding_theory, CAN, mt_target_equilibria, entity-not-
        # program, authored-not-trained — identity preservation
        # under self-modification); domain Mts ADAPTIVE. Failure
        # modes (frozen-should-adapt, drifted, frustrated,
        # redundant, sparse, conflicting) each have specific
        # corrections. Self-improvement loop: monitor → detect →
        # correct → verify → track. Existing substrate features
        # (meta_monitor, architecture_cortex, DevelopmentCortex,
        # feature_invention) compose into the unified loop.
        sid_mt = load_one_seed(self.s, "self_improvement_dynamics")
        self._link("owns_microtheory", sid_mt)

        # Discover and install all concept-expansion packs under
        # seeds/expansions/. Each pack decomposes a high-level concept
        # into its sub-mechanisms + derivation rules, mounting them
        # under the relevant Mt with `decomposes` edges pointing at the
        # parent concept. Dropping a new pack file in the directory
        # adds vocabulary with no Python edit.
        install_all_concept_expansions(self.s)

        # Install the catalogue of code paths the cortex knows how to
        # author for. Each entry is a CodeTarget graph node — adding a
        # new target means editing a JSON seed, not Python.
        _install_code_targets(self.s)

        # Root node (cortex's working state).
        root = self._ensure_root()
        self._link("owns_root", root)

        self._reflexes = install_code_authoring_reflexes(
            self.s, self.cortex_nid)

        # Install the concern->target ENQUEUE bridge — the rule that turns a held
        # SelfConcern carrying a method into a ReplacementTarget the loop picks up.
        # It is NON-RESIDENT (kept OUT of the seeds/*.json flat glob, the same
        # procedural_grammar precedent) and installed HERE, alongside the cortex:
        # the enqueue is part of the CODE-AUTHORING context, so an agent WITH the
        # cortex active gets it (autonomy preserved), and a normal boot WITHOUT the
        # cortex is byte-unperturbed (the seed's capability_keys backfill + the rule
        # never load). The read-implement loop always installs the cortex, so this
        # path always ships the bridge for the loop.
        self._ensure_bridge()

        self._installed = True
        return self

    _BRIDGE_SEED = (Path(__file__).resolve().parent.parent /
                    "seeds" / "code_authoring" / "concern_to_target_bridge.json")

    def _ensure_bridge(self) -> None:
        """Install the bridge rule from the non-resident seed (idempotent: skip if
        already present). Mechanical seed I/O — the same load_seed_manifest idiom
        procedural_reader.ensure_proc_grammar uses for its on-demand seed."""
        inner = getattr(self.agent, "inner", None) or getattr(self.s, "_inner", None)
        ag_node = getattr(self.agent, "agent", None)
        if inner is None or ag_node is None or not self._BRIDGE_SEED.exists():
            return
        try:
            ex = inner.export_rules()
            names = [r.get("name") for r in
                     (ex if isinstance(ex, list) else _json.loads(ex))]
            if "bridge_concern_to_target" in names:
                return
            with self._BRIDGE_SEED.open() as f:
                manifest = _json.load(f)
            inner.load_seed_manifest(manifest, ag_node)
        except Exception:
            pass

    def _ensure_root(self) -> int:
        for n in self.s.nodes("CodeAuthoringRoot"):
            return n
        return self.s.add_node("CodeAuthoringRoot", {
            "owner": "code_writing_cortex",
        })

    def _link(self, et: str, tgt: int) -> None:
        if tgt in self.s.neighbours(self.cortex_nid, et):
            return
        try:
            self.s.add_edge(self.cortex_nid, et, tgt, {})
        except Exception:
            pass

    # ------------------------------------------------------------------ tick

    def tick(self, max_iterations: int = 25) -> list[str]:
        """Fire reflexes in priority order until none fire (fixed
        point) or max_iterations exhausted. Returns the audit trail
        of fired reflex names."""
        if not self._installed:
            raise RuntimeError("CodeWritingCortex.install() not called")
        self._tick_count += 1
        try:
            self.s.set_attr(self.cortex_nid, "tick_count",
                            int(self._tick_count))
        except Exception:
            pass

        audit: list[str] = []
        for _ in range(max_iterations):
            fired_this_round = False
            # Sort reflexes by priority (lower = fires later in the
            # cascade; identify_target has highest priority).
            ordered = sorted(self._reflexes,
                             key=lambda r: -int(self.s.node(r)["attrs"]
                                                .get("priority", 0)))
            for r in ordered:
                name = self.s.node(r)["attrs"].get("name", "")
                step = get_step(name)
                if step is None:
                    continue
                if step(self):
                    audit.append(name)
                    fired_this_round = True
            if not fired_this_round:
                break
        return audit

    # ------------------------------------------------------------------ working set
    # The reflex step callables in `code_authoring.py` call these.

    def attempted_op_names(self) -> set[str]:
        """Set of op names for which we've already created a
        ReplacementTarget (whether the attempt succeeded, failed, or
        is in progress). The identify_target reflex consults this so
        we don't re-target an op whose draft was discarded."""
        out: set[str] = set()
        for n in self.s.nodes("ReplacementTarget"):
            nm = self.s.node(n)["attrs"].get("op_name")
            if isinstance(nm, str):
                out.add(nm)
        return out

    def op_stats_snapshot(self) -> dict[str, dict]:
        """Return a snapshot of the agent's op-stats. Reading the
        agent's introspection is the cortex's whole input signal."""
        if self.agent is None:
            return {}
        try:
            return dict(self.agent.op_stats())
        except Exception:
            return {}

    def current_target(self) -> int | None:
        root = self._ensure_root()
        out = self.s.neighbours(root, "current_target")
        return out[0] if out else None

    def set_target(self, name: str, baseline: dict) -> int:
        root = self._ensure_root()
        tgt = self.s.add_node("ReplacementTarget", {
            "op_name": name,
            "baseline_total_ms": float(baseline.get("total_ms", 0.0)),
            "baseline_count": int(baseline.get("count", 0)),
            "baseline_mean_ms": float(baseline.get("total_ms", 0.0)) /
                max(int(baseline.get("count", 1)), 1),
            "selected_at": time.time(),
        })
        try:
            self.s.add_edge(root, "current_target", tgt, {})
        except Exception:
            pass
        return tgt

    def current_draft(self) -> int | None:
        tgt = self.current_target()
        if tgt is None:
            return None
        out = self.s.neighbours(tgt, "has_draft")
        return out[0] if out else None

    def teacher_in_flight(self) -> bool:
        tgt = self.current_target()
        if tgt is None:
            return False
        return tgt in self._teacher_threads

    def compose_authoring_question(self, target_nid: int) -> str | None:
        """Frame the request the self-teacher will see. The agent's own
        knowledge — its compiler-theory Mt, the existing source on
        disk, the baseline stats — go into the prompt.

        Returns None if we can't compose a meaningful spec (no source
        path resolvable, etc.)."""
        attrs = self.s.node(target_nid)["attrs"]
        op_name = attrs.get("op_name")
        baseline_ms = attrs.get("baseline_mean_ms", 0.0)

        entry = self._target_registry_entry(op_name)
        if entry is None:
            return None
        existing_src = self._read_existing_source(op_name)
        if existing_src is None:
            return None

        # Consult the agent's comparative language model — a graph
        # query, not a hardcoded choice.
        chosen_lang = pick_language_for_target(self.s, entry["requirements"])
        self._link_language_choice(target_nid, chosen_lang)

        # Read the language-shaped guidance off the chosen ProgrammingLanguage
        # node. Each language carries its own `delivery_format` (how the
        # source should be shaped + how the cortex will build it) and
        # `prompt_toolkit_hint` (the in-scope vocabulary for THIS language;
        # compiler-theory for Rust/C/etc., ML vocabulary for Python).
        # Updating the seed re-shapes the prompt; no Python branch on
        # language identity.
        lang_attrs = self._language_attrs(chosen_lang)
        delivery_format = lang_attrs.get(
            "delivery_format",
            f"Return the full replacement source as a single {chosen_lang} "
            f"module (no extra files).")
        toolkit_hint = lang_attrs.get("prompt_toolkit_hint", "")
        frameworks = lang_attrs.get("frameworks", [])
        frameworks_text = (
            f" Frameworks available in {chosen_lang}: "
            f"{', '.join(frameworks)}." if frameworks else ""
        )

        # The design pattern was selected by an earlier reflex; read
        # it from the graph (uses_pattern edge) and include in the
        # spec so the teacher knows which architectural move to apply.
        pattern_text = ""
        for pat_nid in self.s.neighbours(target_nid, "uses_pattern"):
            pa = self.s.node(pat_nid)["attrs"]
            pattern_text = (
                f"\n\nDESIGN PATTERN selected by the cortex: "
                f"{pa.get('name')!r}\n"
                f"  rationale  : {pa.get('definition', '')}\n"
                f"  mechanism  : {pa.get('mechanism', '')}\n"
                f"  tradeoff   : {pa.get('tradeoff', '')}\n"
                f"  prior on speedup : {pa.get('expected_speedup', 1.0)}x\n"
                f"Apply this pattern in the implementation. "
            )
            break

        bench = entry["bench"]
        bench_spec_text = ""
        if bench is not None:
            bench_spec_text = (
                f"\n\nBENCHMARK SURFACE the cortex will use to validate "
                f"your draft:\n"
                f"  exported signature : {bench['signature']}\n"
                f"  function name      : {bench['fn_name']}\n"
                f"  test inputs        : {bench['inputs'][:5]} ... "
                f"({len(bench['inputs'])} values)\n"
                f"  iterations per run : {bench['iterations']:,}\n"
                f"  decision rule      : install iff measured "
                f"baseline_time / candidate_time > 1.0\n"
                f"  THE DRAFT MUST EXPORT EXACTLY THIS SIGNATURE so the "
                f"cortex can dlsym + benchmark.\n"
            )

        return (
            f"Author a replacement for the op named '{op_name}' in "
            f"{chosen_lang.upper()}. The agent's comparative language "
            f"model selected {chosen_lang!r} based on these "
            f"requirements: {entry['requirements']}.{frameworks_text}"
            f"{pattern_text}\n\n"
            f"Existing implementation:\n\n{existing_src}\n\n"
            f"Current mean cost per call: {baseline_ms:.3f} ms."
            f"{bench_spec_text}\n"
            f"Produce a functionally equivalent implementation that follows "
            f"the selected design pattern. {toolkit_hint}\n"
            f"Delivery format: {delivery_format}"
        )

    def _language_attrs(self, lang_name: str) -> dict:
        """Read the ProgrammingLanguage node's attrs for `lang_name` —
        the per-language guidance the prompt template needs. Returns
        an empty dict if the node is missing (the template falls back
        to a generic message)."""
        for nid in self.s.nodes("ProgrammingLanguage"):
            a = self.s.node(nid)["attrs"]
            if a.get("name") == lang_name:
                return dict(a)
        return {}

    def _link_language_choice(self, target_nid: int, lang_name: str) -> None:
        """Record the language the cortex chose for this target via an
        `authored_in` edge to the ProgrammingLanguage node."""
        for nid in self.s.nodes("ProgrammingLanguage"):
            if self.s.node(nid)["attrs"].get("name") == lang_name:
                try:
                    self.s.add_edge(target_nid, "authored_in", nid, {})
                except Exception:
                    pass
                return

    def _target_registry_entry(self, op_name: str) -> dict | None:
        """Read the target entry as graph data — query CodeTarget
        nodes installed by the `seeds/code_authoring_targets.json`
        loader, not a hardcoded Python dict."""
        for nid in self.s.nodes("CodeTarget"):
            attrs = self.s.node(nid)["attrs"]
            if attrs.get("op_name") != op_name:
                continue
            path = self.repo_root.joinpath(*list(attrs.get("path_parts", [])))
            bench = attrs.get("bench")
            # bench may be stored as a list-typed substrate value — normalize.
            if isinstance(bench, (list, tuple)) and len(bench) == 0:
                bench = None
            return {
                "path": path,
                "requirements": list(attrs.get("requirements", [])),
                "design_tags": list(attrs.get("design_tags", [])),
                "bench": bench,
            }
        return None

    # ------------------------------------------------------------------ assemble

    def assemble_network(self, target_nid: int) -> int | None:
        """Construct the cortex's network ASSEMBLAGE for `target_nid` as
        graph data — the agent's structural commitment, not a runtime
        artifact. Reads the chosen top pattern (via `uses_pattern`), the
        target's input_dim/output_dim, and walks each pattern's
        `composition` list, emitting AssemblageStep nodes in order with
        dims flowing per each pattern's `dim_behavior`.

        Returns the NetworkAssemblage node's id, or None if no top
        pattern is attached or the target lacks dims.

        Nothing here is trained, instantiated, or random. The assemblage
        IS the agent's answer; the cortex's previously-authored source
        is one projection of it onto an executable runtime.
        """
        tgt_attrs = self.s.node(target_nid)["attrs"]
        op_name = tgt_attrs.get("op_name")
        # dims are declared on the CodeTarget definition; the
        # ReplacementTarget is the runtime instance and doesn't carry
        # them. Look up the source CodeTarget by op_name.
        in_dim = tgt_attrs.get("input_dim")
        out_dim = tgt_attrs.get("output_dim")
        if (in_dim is None or out_dim is None) and op_name is not None:
            for ct in self.s.nodes("CodeTarget"):
                ca = self.s.node(ct)["attrs"]
                if ca.get("op_name") == op_name:
                    in_dim = ca.get("input_dim", in_dim)
                    out_dim = ca.get("output_dim", out_dim)
                    break
        if in_dim is None or out_dim is None:
            return None
        in_dim = int(in_dim)
        out_dim = int(out_dim)

        chosen_pat_nid = None
        for nid in self.s.neighbours(target_nid, "uses_pattern"):
            chosen_pat_nid = nid
            break
        if chosen_pat_nid is None:
            return None

        top_pattern_attrs = self.s.node(chosen_pat_nid)["attrs"]
        top_pattern_name = top_pattern_attrs.get("name")

        # Hidden dimension heuristic — read from target if explicit,
        # else widen above max(in,out) so neither side is a bottleneck.
        hidden_dim = int(tgt_attrs.get("hidden_dim",
                                       max(4 * in_dim, 2 * out_dim, 16)))

        # Mint the assemblage root.
        assemblage = self.s.add_node("NetworkAssemblage", {
            "top_pattern": top_pattern_name,
            "input_dim": in_dim,
            "output_dim": out_dim,
            "hidden_dim": hidden_dim,
        })
        try:
            self.s.add_edge(target_nid, "has_assemblage", assemblage, {})
        except Exception:
            pass

        # Walk the composition tree and emit ordered AssemblageStep nodes.
        order_counter = [0]
        current_dim = [in_dim]

        def _emit_step(pattern_attrs, in_d, out_d, role):
            sid = self.s.add_node("AssemblageStep", {
                "order": order_counter[0],
                "pattern": pattern_attrs.get("name"),
                "in_dim": in_d,
                "out_dim": out_d,
                "role": role,
                "dim_behavior": pattern_attrs.get("dim_behavior", "preserves"),
            })
            order_counter[0] += 1
            try:
                self.s.add_edge(assemblage, "has_step", sid, {})
            except Exception:
                pass
            # Link the step back to its DesignPattern for traceability.
            pat_name = pattern_attrs.get("name")
            for dn in self.s.nodes("DesignPattern"):
                if self.s.node(dn)["attrs"].get("name") == pat_name:
                    try:
                        self.s.add_edge(sid, "uses_pattern", dn, {})
                    except Exception:
                        pass
                    break
            return sid

        def _find_pattern(name: str) -> dict | None:
            for nid in self.s.nodes("DesignPattern"):
                a = self.s.node(nid)["attrs"]
                if a.get("name") == name:
                    return dict(a)
            return None

        def _walk(pattern_attrs, role: str, target_out_dim: int):
            """Recursive walk over a pattern's composition. Each call is
            given the dim it should END at (target_out_dim). Patterns
            without a composition emit a single step; pattern with a
            composition recurse, threading dims so the LAST emitted
            transforms step lands on target_out_dim."""
            # Composed CPWL gadget: walk gadget_chain in order. Each
            # sub-gadget is a complete primitive that emits its own
            # AssemblageStep; the chain's final dim must equal
            # target_out_dim.
            if pattern_attrs.get("gadget_kind") == "cpwl_composed":
                chain = pattern_attrs.get("gadget_chain", [])
                for sub_name in chain:
                    sub = _find_pattern(sub_name)
                    if sub is None:
                        continue
                    sub_out = sub.get("dim_out", current_dim[0])
                    # If the sub-gadget is itself composed, recurse so
                    # its leaves emit individual steps.
                    if sub.get("gadget_kind") == "cpwl_composed":
                        _walk(sub, f"{role}.{sub_name}", sub_out)
                    elif sub.get("dim_behavior") == "transforms":
                        _emit_step(sub, current_dim[0], sub_out,
                                   f"{role}.{sub_name}")
                        current_dim[0] = sub_out
                    elif sub.get("dim_behavior") == "preserves":
                        _emit_step(sub, current_dim[0], current_dim[0],
                                   f"{role}.{sub_name}")
                    elif sub.get("dim_behavior") == "loss":
                        _emit_step(sub, current_dim[0], 0,
                                   f"{role}.{sub_name}")
                return

            comp = pattern_attrs.get("composition")
            behavior = pattern_attrs.get("dim_behavior", "preserves")

            if not comp:
                # Leaf — emit one step.
                if behavior == "transforms":
                    _emit_step(pattern_attrs, current_dim[0],
                               target_out_dim, role)
                    current_dim[0] = target_out_dim
                elif behavior == "preserves":
                    _emit_step(pattern_attrs, current_dim[0],
                               current_dim[0], role)
                elif behavior == "loss":
                    _emit_step(pattern_attrs, current_dim[0], 0, role)
                return

            # Composite: walk sub-patterns. Identify the LAST transforms
            # step among them; that's the one that must land on target_out_dim.
            sub_patterns = [_find_pattern(n) for n in comp]
            sub_patterns = [p for p in sub_patterns if p is not None]
            last_transforms_idx = -1
            for i, sp in enumerate(sub_patterns):
                if sp.get("dim_behavior") == "transforms":
                    last_transforms_idx = i

            for i, sp in enumerate(sub_patterns):
                sub_role = f"{role}.{sp.get('name')}"
                if sp.get("dim_behavior") == "transforms":
                    if i == last_transforms_idx:
                        # Final transforms in this composite → lands on
                        # the composite's target out_dim.
                        _walk(sp, sub_role, target_out_dim)
                    else:
                        # Intermediate transforms → land on hidden_dim.
                        _walk(sp, sub_role, hidden_dim)
                else:
                    _walk(sp, sub_role, target_out_dim)

        _walk(top_pattern_attrs, top_pattern_name, out_dim)
        return assemblage

    # ------------------------------------------------------------------ construct (write, not train)

    def construct_weights(self, assemblage_nid: int) -> list[int]:
        """Render exact weights for the assemblage by reading them off
        the gadget DesignPatterns the steps point at. The doc's "write,
        not train":

          * cpwl_primitive pattern carries literal weight_W1/b1/W2/b2 —
            copy verbatim onto WeightTensor graph nodes.
          * cpwl_parallel pattern declares (parallel_of, parallel_count) —
            look up the sub-gadget, block-diagonally expand its matrices
            to N copies, emit the expanded tensors. This realises §2.7's
            "parallel steps = width" composition.

        Steps whose pattern has neither literal matrices nor a parallel
        spec (e.g. an untrained linear_layer in a generic MLP recipe)
        are skipped — they'd route through a different rendering path.

        Returns the list of constructed WeightTensor node ids.
        """
        constructed: list[int] = []
        for step in self.s.neighbours(assemblage_nid, "has_step"):
            step_attrs = self.s.node(step)["attrs"]
            pattern_name = step_attrs.get("pattern")
            pattern_attrs = None
            for dn in self.s.nodes("DesignPattern"):
                a = self.s.node(dn)["attrs"]
                if a.get("name") == pattern_name:
                    pattern_attrs = a
                    break
            if pattern_attrs is None:
                continue

            tensors = self._render_step_weights(pattern_attrs)
            for role, data in tensors.items():
                if data is None:
                    continue
                if data and isinstance(data, (list, tuple)) and \
                        isinstance(data[0], (list, tuple)):
                    shape = [len(data), len(data[0])]
                else:
                    shape = [len(data)]
                wt = self.s.add_node("WeightTensor", {
                    "role": role,
                    "shape": shape,
                    "data": data,
                    "origin_pattern": pattern_name,
                    "constructed_by": pattern_attrs.get("gadget_kind",
                                                       "gadget_render"),
                })
                try:
                    self.s.add_edge(step, "has_weight", wt, {})
                except Exception:
                    pass
                constructed.append(wt)
        return constructed

    def _render_step_weights(self, pattern_attrs: dict) -> dict:
        """Produce the four (W1, b1, W2, b2) tensors for a single step
        from the pattern's declaration. Five cases:

          - cpwl_primitive      : read the literal matrices off the pattern.
          - cpwl_parallel       : block-diagonally expand the sub-gadget's
                                  matrices to N copies (homogeneous).
          - cpwl_linear         : expand the affine map y = W·x + b to a
                                  2-layer ReLU using the identity trick.
          - cpwl_broadcast      : N different leaf gadgets all see the
                                  full input (W1 stacked vertically),
                                  outputs concatenated (W2 block-diagonal).
          - cpwl_heteroparallel : N different leaf gadgets each read their
                                  own input slice (W1 block-diagonal),
                                  outputs concatenated (W2 block-diagonal).

        Returns {role: data} where role ∈ {W1, b1, W2, b2}; missing
        roles → None entries (skipped by the caller).
        """
        kind = pattern_attrs.get("gadget_kind")
        if kind == "cpwl_broadcast":
            return self._render_broadcast(pattern_attrs)
        if kind == "cpwl_heteroparallel":
            return self._render_heteroparallel(pattern_attrs)
        if kind == "cpwl_linear":
            W = self._to_plain_list(pattern_attrs.get("weight_W"))
            b = self._to_plain_list(pattern_attrs.get("weight_b"))
            if W is None or b is None:
                return {}
            out_dim = len(W)
            # Identity trick: stack [W; -W] in W1 and [b; -b] in b1; W2
            # is [I, -I] (out × 2·out) so output = ReLU(Wx+b) − ReLU(−(Wx+b)) = Wx+b.
            W1 = [list(map(float, row)) for row in W] + \
                 [[-float(v) for v in row] for row in W]
            b1 = [float(v) for v in b] + [-float(v) for v in b]
            W2 = [[0.0] * (2 * out_dim) for _ in range(out_dim)]
            for i in range(out_dim):
                W2[i][i] = 1.0
                W2[i][out_dim + i] = -1.0
            b2 = [0.0] * out_dim
            return {"W1": W1, "b1": b1, "W2": W2, "b2": b2}
        if kind == "cpwl_parallel":
            sub_name = pattern_attrs.get("parallel_of")
            n = int(pattern_attrs.get("parallel_count", 1))
            sub = self._find_pattern_by_name(sub_name)
            if sub is None:
                return {}
            out = {}
            for role in ("W1", "b1", "W2", "b2"):
                data = sub.get(f"weight_{role}")
                if data is None:
                    out[role] = None
                else:
                    # Substrate round-trips lists as tuples; normalise.
                    data = self._to_plain_list(data)
                    out[role] = self._block_diag_repeat(data, n)
            return out
        # Default: literal cpwl_primitive (or any pattern with the four
        # weight_* attrs — composed gadgets don't reach here because
        # assemble_network expands them into sub-steps first).
        return {
            "W1": self._to_plain_list(pattern_attrs.get("weight_W1")),
            "b1": self._to_plain_list(pattern_attrs.get("weight_b1")),
            "W2": self._to_plain_list(pattern_attrs.get("weight_W2")),
            "b2": self._to_plain_list(pattern_attrs.get("weight_b2")),
        }

    def _render_broadcast(self, pattern_attrs: dict) -> dict:
        """N leaf gadgets all see the FULL input. W1 stacked vertically
        (each sub-gadget's rows read the same input columns), b1
        concatenated, W2 block-diagonal (each sub-gadget's output rows
        land at their own slot), b2 concatenated.

        Requires each sub-gadget to be a leaf (cpwl_primitive or
        cpwl_linear) so we can pull its 2-layer matrices directly."""
        subnames = pattern_attrs.get("subgadgets", [])
        subs = [self._find_pattern_by_name(n) for n in subnames]
        subs = [self._leaf_weights(s) for s in subs if s is not None]
        subs = [s for s in subs if s is not None]
        if not subs:
            return {}
        # Validate all sub-gadgets share dim_in (since they all see full input).
        dim_in = len(subs[0]["W1"][0])
        for s in subs[1:]:
            assert len(s["W1"][0]) == dim_in, (
                f"broadcast requires shared dim_in, got mixed")
        # Stack W1 vertically: each sub's rows read input[0:dim_in].
        W1 = []
        b1 = []
        for s in subs:
            W1.extend([list(map(float, row)) for row in s["W1"]])
            b1.extend(float(v) for v in s["b1"])
        # W2 block-diagonal. Each sub-gadget has out_i rows that read
        # only the hidden block belonging to its own sub.
        out_dims = [len(s["W2"]) for s in subs]
        hidden_dims = [len(s["W2"][0]) for s in subs]
        total_out = sum(out_dims)
        total_hidden = sum(hidden_dims)
        W2 = [[0.0] * total_hidden for _ in range(total_out)]
        r_off = h_off = 0
        for s in subs:
            for i, row in enumerate(s["W2"]):
                for j, w in enumerate(row):
                    W2[r_off + i][h_off + j] = float(w)
            r_off += len(s["W2"])
            h_off += len(s["W2"][0])
        b2 = []
        for s in subs:
            b2.extend(float(v) for v in s["b2"])
        return {"W1": W1, "b1": b1, "W2": W2, "b2": b2}

    def _render_heteroparallel(self, pattern_attrs: dict) -> dict:
        """N leaf gadgets each read their own input slice (block-diagonal
        across both input and output). Like cpwl_parallel but with
        DIFFERENT sub-gadgets per block."""
        subnames = pattern_attrs.get("subgadgets", [])
        subs = [self._find_pattern_by_name(n) for n in subnames]
        subs = [self._leaf_weights(s) for s in subs if s is not None]
        subs = [s for s in subs if s is not None]
        if not subs:
            return {}
        in_dims = [len(s["W1"][0]) for s in subs]
        hidden_dims = [len(s["W1"]) for s in subs]
        out_dims = [len(s["W2"]) for s in subs]
        total_in = sum(in_dims)
        total_hidden = sum(hidden_dims)
        total_out = sum(out_dims)
        W1 = [[0.0] * total_in for _ in range(total_hidden)]
        b1 = []
        W2 = [[0.0] * total_hidden for _ in range(total_out)]
        b2 = []
        h_off = c_off = r2_off = h2_off = 0
        for s, in_d, hid_d, out_d in zip(subs, in_dims, hidden_dims, out_dims):
            for i, row in enumerate(s["W1"]):
                for j, w in enumerate(row):
                    W1[h_off + i][c_off + j] = float(w)
            b1.extend(float(v) for v in s["b1"])
            for i, row in enumerate(s["W2"]):
                for j, w in enumerate(row):
                    W2[r2_off + i][h2_off + j] = float(w)
            b2.extend(float(v) for v in s["b2"])
            h_off += hid_d
            c_off += in_d
            r2_off += out_d
            h2_off += hid_d
        return {"W1": W1, "b1": b1, "W2": W2, "b2": b2}

    def _leaf_weights(self, pattern_attrs: dict) -> dict | None:
        """Resolve a (possibly nested) pattern's 4-tuple leaf weights —
        i.e., reach a cpwl_primitive or cpwl_linear (expanded) form.
        Returns {W1, b1, W2, b2} as plain lists, or None if the pattern
        isn't a leaf-resolvable structure (composed/broadcast/etc)."""
        if pattern_attrs is None:
            return None
        k = pattern_attrs.get("gadget_kind")
        if k == "cpwl_linear":
            r = self._render_step_weights(pattern_attrs)
            return r if r else None
        # cpwl_primitive: literal weights.
        W1 = self._to_plain_list(pattern_attrs.get("weight_W1"))
        if W1 is None:
            return None
        return {
            "W1": W1,
            "b1": self._to_plain_list(pattern_attrs.get("weight_b1")),
            "W2": self._to_plain_list(pattern_attrs.get("weight_W2")),
            "b2": self._to_plain_list(pattern_attrs.get("weight_b2")),
        }

    def _find_pattern_by_name(self, name: str) -> dict | None:
        for nid in self.s.nodes("DesignPattern"):
            a = self.s.node(nid)["attrs"]
            if a.get("name") == name:
                return dict(a)
        return None

    @staticmethod
    def _to_plain_list(data):
        """Recursively convert tuples to lists (substrate round-trips
        lists as tuples; downstream math wants list-of-lists)."""
        if data is None:
            return None
        if isinstance(data, (list, tuple)):
            return [CodeWritingCortex._to_plain_list(x) for x in data]
        return data

    @staticmethod
    def _block_diag_repeat(W, n: int):
        """Block-diagonal expansion: stack n copies of W on the diagonal
        (matrices) or repeat n times (vectors). For W: (h, d) → (n·h, n·d);
        for b: (h,) → (n·h,)."""
        if not W:
            return W
        is_2d = isinstance(W[0], (list, tuple))
        if not is_2d:
            out = []
            for _ in range(n):
                out.extend(float(v) for v in W)
            return out
        h = len(W)
        d = len(W[0])
        out = [[0.0] * (n * d) for _ in range(n * h)]
        for k in range(n):
            for i in range(h):
                for j in range(d):
                    out[k * h + i][k * d + j] = float(W[i][j])
        return out

    def construct_broadcast_pattern(self, input_dim: int,
                                    branch_chains: list[list[str]],
                                    label: str = "broadcast") -> str | None:
        """Mint a cpwl_composed DesignPattern that realises a broadcast
        of multiple branch chains. Each branch's chain is recursively
        expanded to its leaves (cpwl_composed sub-gadgets are flattened);
        shorter branches are PADDED with identity-at-dim-d steps so all
        branches reach the same depth. At each depth, branches combine
        into one wide step:

          - depth 0  — fan-out: every branch's first leaf sees the FULL
                       input (vertical W1 stack).
          - depth ≥1 — heteroparallel: each branch's leaf reads ITS OWN
                       slot of the accumulated state (block-diagonal W1).

        The result is a regular cpwl_composed pattern that any downstream
        gadget can reference by name. Returns the top-level pattern name,
        or None if any branch chain has no resolvable leaves.

        Architectural payoff: broadcasts can now contain composed
        sub-gadgets (cube, square_pwl_signed, etc.) rather than only
        leaves — the assembler does the depth-padded combination.
        """
        # Step 1: expand each branch's chain to a flat list of leaf patterns.
        expanded = []
        for chain in branch_chains:
            leaves = []
            for name in chain:
                self._expand_to_leaves(name, leaves)
            if not leaves:
                return None
            expanded.append(leaves)
        max_depth = max(len(b) for b in expanded)
        if max_depth == 0:
            return None

        # Step 2: compute per-branch (leaf, in_dim, out_dim) trajectory,
        # padding with identity-at-dim entries when shorter than max_depth.
        branch_trajectories = []
        for leaves in expanded:
            cur_dim = input_dim
            traj = []
            for leaf in leaves:
                in_d = cur_dim
                out_d = int(leaf.get("dim_out", cur_dim))
                traj.append({"leaf": leaf,
                             "in_dim": in_d,
                             "out_dim": out_d,
                             "identity": False})
                cur_dim = out_d
            while len(traj) < max_depth:
                traj.append({"leaf": None,
                             "in_dim": cur_dim,
                             "out_dim": cur_dim,
                             "identity": True})
            branch_trajectories.append({"traj": traj, "final_dim": cur_dim})

        # Step 3: mint one primitive pattern per depth with the combined
        # matrices (fan-out at t=0, heteroparallel at t≥1).
        self._dyn_counter += 1
        counter = self._dyn_counter
        sub_chain_names = []
        for t in range(max_depth):
            depth_leaves = [bt["traj"][t] for bt in branch_trajectories]
            if t == 0:
                mats = self._combine_fanout(depth_leaves, input_dim)
            else:
                mats = self._combine_heteroparallel(depth_leaves)
            in_dim_d = len(mats["W1"][0]) if mats["W1"] else 0
            out_dim_d = len(mats["W2"]) if mats["W2"] else 0
            sub_name = f"_{label}_d{t}_c{counter}"
            self.s.add_node("DesignPattern", {
                "name": sub_name,
                "gadget_kind": "cpwl_primitive",
                "dim_behavior": "transforms",
                "dim_in": in_dim_d,
                "dim_out": out_dim_d,
                "weight_W1": mats["W1"],
                "weight_b1": mats["b1"],
                "weight_W2": mats["W2"],
                "weight_b2": mats["b2"],
                "origin": "cortex_constructed_broadcast",
            })
            sub_chain_names.append(sub_name)

        # Step 4: mint the top-level cpwl_composed pattern.
        total_out = sum(bt["final_dim"] for bt in branch_trajectories)
        top_name = f"_{label}_top_c{counter}"
        self.s.add_node("DesignPattern", {
            "name": top_name,
            "gadget_kind": "cpwl_composed",
            "dim_behavior": "transforms",
            "dim_in": input_dim,
            "dim_out": total_out,
            "gadget_chain": sub_chain_names,
            "origin": "cortex_constructed_broadcast",
        })
        return top_name

    def _expand_to_leaves(self, name: str, out_list: list) -> None:
        """Recursively expand a gadget name into a flat list of leaf
        DesignPattern attrs (anything that's NOT cpwl_composed)."""
        g = self._find_pattern_by_name(name)
        if g is None:
            return
        if g.get("gadget_kind") == "cpwl_composed":
            for sub in g.get("gadget_chain", []):
                self._expand_to_leaves(sub, out_list)
        else:
            out_list.append(g)

    def _identity_step_matrices(self, dim: int) -> dict:
        """Identity passthrough at dim d as a 2-layer ReLU MLP."""
        W1 = []
        for i in range(dim):
            pos = [0.0] * dim
            pos[i] = 1.0
            W1.append(pos)
            neg = [0.0] * dim
            neg[i] = -1.0
            W1.append(neg)
        b1 = [0.0] * (2 * dim)
        W2 = []
        for i in range(dim):
            row = [0.0] * (2 * dim)
            row[2 * i] = 1.0
            row[2 * i + 1] = -1.0
            W2.append(row)
        b2 = [0.0] * dim
        return {"W1": W1, "b1": b1, "W2": W2, "b2": b2}

    def _combine_fanout(self, depth_leaves: list, input_dim: int) -> dict:
        """Depth-0 of a broadcast: ALL branches read the full input.
        W1 is a vertical stack of branch leaf W1s (each row reads the
        same input_dim columns); W2 is block-diagonal so each branch's
        output lands at its own slot."""
        rendered = self._render_leaves(depth_leaves)
        W1 = []
        b1 = []
        for r in rendered:
            W1.extend([list(map(float, row)) for row in r["W1"]])
            b1.extend(float(v) for v in r["b1"])
        total_h = sum(len(r["W2"][0]) for r in rendered)
        total_o = sum(len(r["W2"]) for r in rendered)
        W2 = [[0.0] * total_h for _ in range(total_o)]
        b2 = []
        r_off = c_off = 0
        for r in rendered:
            for i, row in enumerate(r["W2"]):
                for j, w in enumerate(row):
                    W2[r_off + i][c_off + j] = float(w)
            r_off += len(r["W2"])
            c_off += len(r["W2"][0])
            b2.extend(float(v) for v in r["b2"])
        return {"W1": W1, "b1": b1, "W2": W2, "b2": b2}

    def _combine_heteroparallel(self, depth_leaves: list) -> dict:
        """Depth ≥ 1 of a broadcast: each branch reads its own slot of
        the accumulated state (block-diagonal W1 and W2)."""
        rendered = self._render_leaves(depth_leaves)
        total_in = sum(len(r["W1"][0]) for r in rendered)
        total_h = sum(len(r["W1"]) for r in rendered)
        total_o = sum(len(r["W2"]) for r in rendered)
        W1 = [[0.0] * total_in for _ in range(total_h)]
        b1 = []
        W2 = [[0.0] * total_h for _ in range(total_o)]
        b2 = []
        h_off = c_off = r2_off = h2_off = 0
        for r in rendered:
            hid = len(r["W1"])
            in_d = len(r["W1"][0])
            out = len(r["W2"])
            for i, row in enumerate(r["W1"]):
                for j, w in enumerate(row):
                    W1[h_off + i][c_off + j] = float(w)
            b1.extend(float(v) for v in r["b1"])
            for i, row in enumerate(r["W2"]):
                for j, w in enumerate(row):
                    W2[r2_off + i][h2_off + j] = float(w)
            b2.extend(float(v) for v in r["b2"])
            h_off += hid
            c_off += in_d
            r2_off += out
            h2_off += hid
        return {"W1": W1, "b1": b1, "W2": W2, "b2": b2}

    def _render_leaves(self, depth_leaves: list) -> list:
        """For each depth-t entry (leaf attrs OR padding marker), return
        the 4-matrix MLP form. Padding becomes identity-at-its-dim."""
        rendered = []
        for d in depth_leaves:
            if d.get("identity"):
                rendered.append(self._identity_step_matrices(d["in_dim"]))
            else:
                rendered.append(self._render_step_weights(d["leaf"]))
        return rendered

    def construct_multiplexer(self, b_pattern_name: str,
                              c_pattern_name: str,
                              boundary_x: float = 0.0,
                              label: str = "mux",
                              continuity_tol: float = 1e-6
                              ) -> int | None:
        """Construct a CPWL multiplexer per §2.6 of the construction doc:

            z(x) = b(x*) + ReLU(b(x) − b(x*)) + ReLU(c(x) − c(x*))

        which realises `if x ≥ x* then b(x) else c(x)` exactly when
        the SOUNDNESS PREDICATE holds:

            CONTINUITY:  b(x*) = c(x*)            ← the doc's named edge

        plus the sign-reversal monotonicity (b non-decreasing through
        x*, c non-increasing through x*). Continuity is the only
        check enforced here — it's the predicate the entity's
        compiler-theory Mt already knows about. Monotonicity is the
        caller's responsibility per §2.6.

        Construction:
          stage 1: broadcast([b, c]) produces [b(x), c(x)]
          stage 2: cpwl_primitive with
                     W1 = I_2, b1 = [−b(x*), −c(x*)]
                     W2 = [[1, 1]], b2 = [b(x*)]
                   which is exactly z(x).

        On continuity violation: returns None and emits a graph node
        recording the soundness failure so the architecture cortex
        can read it later."""
        try:
            import numpy as np  # noqa: F401
        except ImportError:
            return None

        b_pat = self._find_pattern_by_name(b_pattern_name)
        c_pat = self._find_pattern_by_name(c_pattern_name)
        if b_pat is None or c_pat is None:
            return None

        # Soundness step 1: evaluate b and c at the boundary by building
        # tiny throwaway assemblages and forwarding x*.
        b_value = self._evaluate_pattern_at(b_pattern_name, boundary_x)
        c_value = self._evaluate_pattern_at(c_pattern_name, boundary_x)
        if b_value is None or c_value is None:
            return None
        residual = abs(b_value - c_value)

        # Soundness step 2: enforce CONTINUITY. If b(x*) != c(x*), we
        # cannot construct a sound multiplexer; record the failure as
        # a graph node and bail.
        if residual > continuity_tol:
            self._dyn_counter += 1
            counter = self._dyn_counter
            self.s.add_node("DesignPattern", {
                "name": f"_mux_violation_{label}_c{counter}",
                "gadget_kind": "cpwl_invalid",
                "origin": "cortex_constructed_mux_violation",
                "b_pattern": b_pattern_name,
                "c_pattern": c_pattern_name,
                "boundary_x": float(boundary_x),
                "b_at_boundary": b_value,
                "c_at_boundary": c_value,
                "continuity_residual": residual,
                "soundness_predicate": "b(x*) = c(x*)",
                "soundness_verdict": "violated",
                "soundness_reason": (
                    f"Continuity at x*={boundary_x}: |b({boundary_x}) "
                    f"− c({boundary_x})| = {residual:.6e} > tol "
                    f"{continuity_tol:.0e}"),
            })
            return None

        # Stage 1: broadcast(b, c) → [b(x), c(x)].
        # Determine input_dim from b's declared dim_in (both must match).
        b_in_dim = int(b_pat.get("dim_in", 1))
        c_in_dim = int(c_pat.get("dim_in", 1))
        if b_in_dim != c_in_dim:
            return None
        bc_lift = self.construct_broadcast_pattern(
            input_dim=b_in_dim,
            branch_chains=[[b_pattern_name], [c_pattern_name]],
            label=f"mux_bc_{label}")
        if bc_lift is None:
            return None

        # Stage 2: cpwl_primitive that computes b(x*) + ReLU(b(x)−b(x*))
        # + ReLU(c(x)−c(x*)).
        # W1 = I_2 (rows read [b_out, c_out]).
        # b1 = [-b(x*), -c(x*)]  (shift so ReLU kicks in at the boundary)
        # hidden = ReLU([b(x)-b(x*), c(x)-c(x*)])
        # W2 = [[1, 1]]
        # b2 = [b(x*)]
        self._dyn_counter += 1
        counter = self._dyn_counter
        combine_name = f"_mux_combine_{label}_c{counter}"
        self.s.add_node("DesignPattern", {
            "name": combine_name,
            "gadget_kind": "cpwl_primitive",
            "dim_behavior": "transforms",
            "dim_in": 2, "dim_out": 1,
            "weight_W1": [[1.0, 0.0], [0.0, 1.0]],
            "weight_b1": [-b_value, -c_value],
            "weight_W2": [[1.0, 1.0]],
            "weight_b2": [b_value],
            "origin": "cortex_constructed_mux_combine",
        })

        # Top-level composed gadget with the soundness annotation.
        top_name = f"_mux_{label}_c{counter}"
        self.s.add_node("DesignPattern", {
            "name": top_name,
            "gadget_kind": "cpwl_composed",
            "dim_behavior": "transforms",
            "dim_in": b_in_dim, "dim_out": 1,
            "gadget_chain": [bc_lift, combine_name],
            "origin": "cortex_constructed_mux",
            "boundary_x": float(boundary_x),
            "b_at_boundary": b_value,
            "c_at_boundary": c_value,
            "continuity_residual": residual,
            "soundness_predicate": "b(x*) = c(x*)",
            "soundness_verdict": "satisfied",
            "formula": (f"z(x) = b(x*) + ReLU(b(x)−b(x*)) "
                        f"+ ReLU(c(x)−c(x*)),  x* = {boundary_x}"),
        })

        target = self.s.add_node("ReplacementTarget", {
            "op_name": f"mux_{label}",
            "baseline_total_ms": 0.0, "baseline_count": 1,
            "baseline_mean_ms": 0.0, "selected_at": time.time(),
        })
        self.s.set_attr(target, "input_dim", b_in_dim)
        self.s.set_attr(target, "output_dim", 1)
        top_nid = next(n for n in self.s.nodes("DesignPattern")
                       if self.s.node(n)["attrs"].get("name") == top_name)
        try:
            self.s.add_edge(target, "uses_pattern", top_nid, {})
        except Exception:
            pass
        assemblage = self.assemble_network(target)
        if assemblage is not None:
            self.construct_weights(assemblage)
        return assemblage

    def construct_multiplexer_auto(self,
                                   b_pattern_name: str,
                                   c_pattern_name: str,
                                   boundary_x: float = 0.0,
                                   label: str = "mux_auto",
                                   probe_epsilon: float = 0.1,
                                   continuity_tol: float = 1e-6
                                   ) -> int | None:
        """CPWL multiplexer that auto-detects monotonicity through x*
        and picks the right ReLU formula. Covers ALL four cases:

          (b↑, c↓)  z = b(x*) + ReLU(b(x)-b(x*)) + ReLU(c(x)-c(x*))
          (b↑, c↑)  z = b(x*) + ReLU(b(x)-b(x*)) − ReLU(c(x*)-c(x))
          (b↓, c↓)  z = b(x*) − ReLU(b(x*)-b(x)) + ReLU(c(x)-c(x*))
          (b↓, c↑)  z = b(x*) − ReLU(b(x*)-b(x)) − ReLU(c(x*)-c(x))

        Each formula realises `if x ≥ x* then b(x) else c(x)` for its
        monotonicity combination, given:
          · continuity: b(x*) = c(x*)
          · monotonicity through x*: both b and c are strictly
            monotonic across the boundary

        Same soundness story as construct_multiplexer: if either
        condition is violated, no construction is emitted and a
        cpwl_invalid graph node records the verdict + reason.
        """
        b_pat = self._find_pattern_by_name(b_pattern_name)
        c_pat = self._find_pattern_by_name(c_pattern_name)
        if b_pat is None or c_pat is None:
            return None

        b_at = self._evaluate_pattern_at(b_pattern_name, boundary_x)
        c_at = self._evaluate_pattern_at(c_pattern_name, boundary_x)
        if b_at is None or c_at is None:
            return None
        residual = abs(b_at - c_at)
        if residual > continuity_tol:
            self._dyn_counter += 1
            counter = self._dyn_counter
            self.s.add_node("DesignPattern", {
                "name": f"_mux_auto_violation_{label}_c{counter}",
                "gadget_kind": "cpwl_invalid",
                "origin": "cortex_constructed_mux_violation",
                "b_pattern": b_pattern_name,
                "c_pattern": c_pattern_name,
                "boundary_x": float(boundary_x),
                "b_at_boundary": b_at,
                "c_at_boundary": c_at,
                "continuity_residual": residual,
                "soundness_predicate": "b(x*) = c(x*)",
                "soundness_verdict": "violated",
                "soundness_reason": (
                    f"Continuity at x*={boundary_x}: residual "
                    f"{residual:.6e} > tol {continuity_tol:.0e}"),
            })
            return None

        # Probe monotonicity at x* ± ε.
        b_above = self._evaluate_pattern_at(b_pattern_name,
                                            boundary_x + probe_epsilon)
        b_below = self._evaluate_pattern_at(b_pattern_name,
                                            boundary_x - probe_epsilon)
        c_above = self._evaluate_pattern_at(c_pattern_name,
                                            boundary_x + probe_epsilon)
        c_below = self._evaluate_pattern_at(c_pattern_name,
                                            boundary_x - probe_epsilon)
        if None in (b_above, b_below, c_above, c_below):
            return None

        # Classify direction. Strictly monotonic-through-x* means
        # value above > value at x* > value below (increasing) or
        # the reverse (decreasing).
        def _direction(at, above, below):
            if above > at + 1e-9 and below < at - 1e-9:
                return "increasing"
            if above < at - 1e-9 and below > at + 1e-9:
                return "decreasing"
            return None

        b_dir = _direction(b_at, b_above, b_below)
        c_dir = _direction(c_at, c_above, c_below)
        if b_dir is None or c_dir is None:
            self._dyn_counter += 1
            counter = self._dyn_counter
            self.s.add_node("DesignPattern", {
                "name": f"_mux_auto_nonmonotonic_{label}_c{counter}",
                "gadget_kind": "cpwl_invalid",
                "origin": "cortex_constructed_mux_violation",
                "b_pattern": b_pattern_name,
                "c_pattern": c_pattern_name,
                "boundary_x": float(boundary_x),
                "b_at_boundary": b_at, "c_at_boundary": c_at,
                "b_above": b_above, "b_below": b_below,
                "c_above": c_above, "c_below": c_below,
                "b_direction": str(b_dir),
                "c_direction": str(c_dir),
                "soundness_predicate":
                    "strict monotonicity of b and c through x*",
                "soundness_verdict": "violated",
                "soundness_reason": (
                    "At least one of b, c is not strictly monotonic "
                    "through x*. The general non-monotonic case needs "
                    "a multi-layer construction (not lifted in this turn)."),
            })
            return None

        # Build broadcast(b, c) → [b(x), c(x)].
        b_in_dim = int(b_pat.get("dim_in", 1))
        c_in_dim = int(c_pat.get("dim_in", 1))
        if b_in_dim != c_in_dim:
            return None
        bc_lift = self.construct_broadcast_pattern(
            input_dim=b_in_dim,
            branch_chains=[[b_pattern_name], [c_pattern_name]],
            label=f"mux_auto_bc_{label}")
        if bc_lift is None:
            return None

        # Construct the combine step matrices for the chosen case.
        if b_dir == "increasing" and c_dir == "decreasing":
            mode = "b_up_c_down"
            # hidden = [ReLU(b - b_at), ReLU(c - c_at)]
            W1 = [[1.0, 0.0], [0.0, 1.0]]
            b1 = [-b_at, -c_at]
            W2 = [[1.0, 1.0]]
        elif b_dir == "increasing" and c_dir == "increasing":
            mode = "b_up_c_up"
            # hidden = [ReLU(b - b_at), ReLU(c_at - c)]
            W1 = [[1.0, 0.0], [0.0, -1.0]]
            b1 = [-b_at, c_at]
            W2 = [[1.0, -1.0]]
        elif b_dir == "decreasing" and c_dir == "decreasing":
            mode = "b_down_c_down"
            # hidden = [ReLU(b_at - b), ReLU(c - c_at)]
            W1 = [[-1.0, 0.0], [0.0, 1.0]]
            b1 = [b_at, -c_at]
            W2 = [[-1.0, 1.0]]
        else:  # b_dir == "decreasing" and c_dir == "increasing"
            mode = "b_down_c_up"
            # hidden = [ReLU(b_at - b), ReLU(c_at - c)]
            W1 = [[-1.0, 0.0], [0.0, -1.0]]
            b1 = [b_at, c_at]
            W2 = [[-1.0, -1.0]]
        b2 = [b_at]

        self._dyn_counter += 1
        counter = self._dyn_counter
        combine_name = f"_mux_auto_combine_{label}_c{counter}"
        self.s.add_node("DesignPattern", {
            "name": combine_name,
            "gadget_kind": "cpwl_primitive",
            "dim_behavior": "transforms",
            "dim_in": 2, "dim_out": 1,
            "weight_W1": W1,
            "weight_b1": b1,
            "weight_W2": W2,
            "weight_b2": b2,
            "origin": "cortex_constructed_mux_combine",
            "mux_mode": mode,
        })

        top_name = f"_mux_auto_{label}_c{counter}"
        self.s.add_node("DesignPattern", {
            "name": top_name,
            "gadget_kind": "cpwl_composed",
            "dim_behavior": "transforms",
            "dim_in": b_in_dim, "dim_out": 1,
            "gadget_chain": [bc_lift, combine_name],
            "origin": "cortex_constructed_mux_auto",
            "boundary_x": float(boundary_x),
            "b_direction": b_dir,
            "c_direction": c_dir,
            "mux_mode": mode,
            "b_at_boundary": b_at,
            "c_at_boundary": c_at,
            "continuity_residual": residual,
            "soundness_predicate":
                "continuity + strict monotonicity of b and c through x*",
            "soundness_verdict": "satisfied",
            "formula": (f"4-case ReLU multiplexer in {mode!r} regime  — "
                        f"realises if x ≥ {boundary_x} then b(x) else c(x)"),
        })

        target = self.s.add_node("ReplacementTarget", {
            "op_name": f"mux_auto_{label}",
            "baseline_total_ms": 0.0, "baseline_count": 1,
            "baseline_mean_ms": 0.0, "selected_at": time.time(),
        })
        self.s.set_attr(target, "input_dim", b_in_dim)
        self.s.set_attr(target, "output_dim", 1)
        top_nid = next(n for n in self.s.nodes("DesignPattern")
                       if self.s.node(n)["attrs"].get("name") == top_name)
        try:
            self.s.add_edge(target, "uses_pattern", top_nid, {})
        except Exception:
            pass
        assemblage = self.assemble_network(target)
        if assemblage is not None:
            self.construct_weights(assemblage)
        return assemblage

    def construct_multiplexer_general(self, b_pattern_name: str,
                                      c_pattern_name: str,
                                      boundary_x: float = 0.0,
                                      label: str = "mux_g",
                                      probe_epsilon: float = 0.1,
                                      continuity_tol: float = 1e-6
                                      ) -> int | None:
        """General-case multiplexer per §2.6's sorting-style hint.

        Realises `if x ≥ x* then b(x) else c(x)` as max(b, c) or
        min(b, c), depending on which ordering of b and c near the
        boundary is consistent with the conditional. Sample probes
        at x* ± ε:

          b(x*+ε) > c(x*+ε) AND c(x*−ε) > b(x*−ε) → z = max(b, c)
          b(x*+ε) < c(x*+ε) AND c(x*−ε) < b(x*−ε) → z = min(b, c)
          otherwise (crossing or mixed)                → REFUSED

        The unifying SOUNDNESS PREDICATE here is:
          continuity AT the boundary  (b(x*) = c(x*))
          PLUS sortability NEAR the boundary
        Both checked; failures emit a cpwl_invalid graph node with
        the verdict + reason.
        """
        b_pat = self._find_pattern_by_name(b_pattern_name)
        c_pat = self._find_pattern_by_name(c_pattern_name)
        if b_pat is None or c_pat is None:
            return None

        b_at = self._evaluate_pattern_at(b_pattern_name, boundary_x)
        c_at = self._evaluate_pattern_at(c_pattern_name, boundary_x)
        if b_at is None or c_at is None:
            return None
        residual = abs(b_at - c_at)
        if residual > continuity_tol:
            self._dyn_counter += 1
            counter = self._dyn_counter
            self.s.add_node("DesignPattern", {
                "name": f"_mux_g_violation_{label}_c{counter}",
                "gadget_kind": "cpwl_invalid",
                "origin": "cortex_constructed_mux_violation",
                "b_pattern": b_pattern_name,
                "c_pattern": c_pattern_name,
                "boundary_x": float(boundary_x),
                "b_at_boundary": b_at,
                "c_at_boundary": c_at,
                "continuity_residual": residual,
                "soundness_predicate": "b(x*) = c(x*)",
                "soundness_verdict": "violated",
                "soundness_reason": (
                    f"Continuity at x*={boundary_x}: |b−c| = "
                    f"{residual:.6e} > tol {continuity_tol:.0e}"),
            })
            return None

        # Sortability probe: compare b and c slightly above and below x*.
        b_above = self._evaluate_pattern_at(b_pattern_name,
                                            boundary_x + probe_epsilon)
        c_above = self._evaluate_pattern_at(c_pattern_name,
                                            boundary_x + probe_epsilon)
        b_below = self._evaluate_pattern_at(b_pattern_name,
                                            boundary_x - probe_epsilon)
        c_below = self._evaluate_pattern_at(c_pattern_name,
                                            boundary_x - probe_epsilon)
        if None in (b_above, c_above, b_below, c_below):
            return None

        if b_above >= c_above and c_below >= b_below:
            mode = "max"
            combine_gadget = "max_gadget"
        elif b_above <= c_above and c_below <= b_below:
            mode = "min"
            combine_gadget = "min_gadget"
        else:
            self._dyn_counter += 1
            counter = self._dyn_counter
            self.s.add_node("DesignPattern", {
                "name": f"_mux_g_unsortable_{label}_c{counter}",
                "gadget_kind": "cpwl_invalid",
                "origin": "cortex_constructed_mux_violation",
                "b_pattern": b_pattern_name,
                "c_pattern": c_pattern_name,
                "boundary_x": float(boundary_x),
                "b_above": b_above, "c_above": c_above,
                "b_below": b_below, "c_below": c_below,
                "soundness_predicate":
                    "consistent sortability of b vs c across x*",
                "soundness_verdict": "violated",
                "soundness_reason": (
                    "Neither max nor min realises the conditional: "
                    f"above ({b_above:.4f} vs {c_above:.4f}), "
                    f"below ({b_below:.4f} vs {c_below:.4f}). The general "
                    "case requires more than one ReLU layer (not lifted "
                    "in this turn)."),
            })
            return None

        # Construct: broadcast(b, c) → [b(x), c(x)], then max or min.
        b_in_dim = int(b_pat.get("dim_in", 1))
        c_in_dim = int(c_pat.get("dim_in", 1))
        if b_in_dim != c_in_dim:
            return None
        bc_lift = self.construct_broadcast_pattern(
            input_dim=b_in_dim,
            branch_chains=[[b_pattern_name], [c_pattern_name]],
            label=f"mux_g_bc_{label}")
        if bc_lift is None:
            return None

        self._dyn_counter += 1
        counter = self._dyn_counter
        top_name = f"_mux_g_{label}_c{counter}"
        self.s.add_node("DesignPattern", {
            "name": top_name,
            "gadget_kind": "cpwl_composed",
            "dim_behavior": "transforms",
            "dim_in": b_in_dim, "dim_out": 1,
            "gadget_chain": [bc_lift, combine_gadget],
            "origin": "cortex_constructed_mux_general",
            "boundary_x": float(boundary_x),
            "mode": mode,
            "b_at_boundary": b_at, "c_at_boundary": c_at,
            "continuity_residual": residual,
            "soundness_predicate": (
                "continuity (b(x*)=c(x*)) AND consistent sortability"),
            "soundness_verdict": "satisfied",
            "formula": (f"z(x) = {mode}(b(x), c(x))  — realises "
                        f"if x ≥ {boundary_x} then b(x) else c(x) "
                        "given the sortability predicate"),
        })

        target = self.s.add_node("ReplacementTarget", {
            "op_name": f"mux_g_{label}",
            "baseline_total_ms": 0.0, "baseline_count": 1,
            "baseline_mean_ms": 0.0, "selected_at": time.time(),
        })
        self.s.set_attr(target, "input_dim", b_in_dim)
        self.s.set_attr(target, "output_dim", 1)
        top_nid = next(n for n in self.s.nodes("DesignPattern")
                       if self.s.node(n)["attrs"].get("name") == top_name)
        try:
            self.s.add_edge(target, "uses_pattern", top_nid, {})
        except Exception:
            pass
        assemblage = self.assemble_network(target)
        if assemblage is not None:
            self.construct_weights(assemblage)
        return assemblage

    def construct_categorical_attention(self,
                                        predicate,
                                        routing: list,
                                        T: int,
                                        V_q: int,
                                        V_k: int,
                                        V_v: int,
                                        V_o: int,
                                        label: str = "attn"
                                        ) -> int | None:
        """Single-query categorical attention layer — the §1.2/§1.3 pair
        composed into a usable attention mechanism.

        Input  : concatenation of one-hots, total dim V_q + T·V_k + T·V_v
                   slots 0..V_q-1                : q one-hot
                   slots V_q..V_q+T·V_k-1        : T key one-hots
                                                   (slot V_q+j·V_k+kv = k_j[kv])
                   slots V_q+T·V_k..end          : T value one-hots
        Output : one-hot of size V_o — the aggregated value, routed
                 through W_OV.

        Algorithm (per the doc's §1.2-§1.3, simplified for categorical):
          scores[j] = W_QK[q_idx, k_j_idx]   (0 or 1 from predicate)
          out_pos[j] = W_OV row for v_j_idx  (the routing target)
          output[o] = Σ_j scores[j] · 1{routing[v_j_idx] = o}

        For SPARSE predicates (each query matches at most one key),
        the softmax with sharp temperature degenerates to direct
        selection — no normalization needed. This is the regime the
        doc's T^{-1} ≈ 100 produces. We bypass the softmax and
        compute the selection directly via a 3-way AND of one-hots.

        Construction: a single 2-layer ReLU MLP.
          hidden_{j, qv, kv, vv} = ReLU(q[qv] + k_j[kv] + v_j[vv] − 2)
            — fires iff all three one-hots are 1 at those positions
          W2[o, h_{j,qv,kv,vv}] = predicate(qv, kv) · (routing[vv] == o)

        Hidden dim = T · V_q · V_k · V_v.
        """
        if len(routing) != V_v:
            return None
        for o in routing:
            if not (0 <= o < V_o):
                return None

        in_dim = V_q + T * V_k + T * V_v
        hidden_dim = T * V_q * V_k * V_v
        out_dim = V_o

        # W1: each hidden unit reads q[qv], k_j[kv], v_j[vv] each with
        # weight 1; b1 = -2 so ReLU activates only when all three are 1.
        W1 = [[0.0] * in_dim for _ in range(hidden_dim)]
        b1 = [-2.0] * hidden_dim
        for j in range(T):
            for qv in range(V_q):
                for kv in range(V_k):
                    for vv in range(V_v):
                        h_idx = ((j * V_q * V_k * V_v)
                                 + (qv * V_k * V_v)
                                 + (kv * V_v)
                                 + vv)
                        W1[h_idx][qv] = 1.0                          # q slot
                        W1[h_idx][V_q + j * V_k + kv] = 1.0          # k_j slot
                        W1[h_idx][V_q + T * V_k + j * V_v + vv] = 1.0  # v_j slot

        # W2: per output dim o, sum over (j, qv, kv, vv) of
        # predicate(qv, kv) · (routing[vv] == o).
        W2 = [[0.0] * hidden_dim for _ in range(out_dim)]
        b2 = [0.0] * out_dim
        for o in range(out_dim):
            for j in range(T):
                for qv in range(V_q):
                    for kv in range(V_k):
                        if not predicate(qv, kv):
                            continue
                        for vv in range(V_v):
                            if routing[vv] != o:
                                continue
                            h_idx = ((j * V_q * V_k * V_v)
                                     + (qv * V_k * V_v)
                                     + (kv * V_v)
                                     + vv)
                            W2[o][h_idx] = 1.0

        # Also record the predicate matrix W_QK and the W_OV routing
        # so the architecture cortex can introspect what this attention
        # head does.
        W_QK = [[1.0 if predicate(qv, kv) else 0.0
                 for kv in range(V_k)]
                for qv in range(V_q)]
        W_OV = [[1.0 if routing[vv] == o else 0.0
                 for vv in range(V_v)]
                for o in range(V_o)]

        self._dyn_counter += 1
        counter = self._dyn_counter
        pat_name = f"_attn_{label}_c{counter}"
        self.s.add_node("DesignPattern", {
            "name": pat_name,
            "gadget_kind": "cpwl_primitive",
            "dim_behavior": "transforms",
            "dim_in": in_dim, "dim_out": out_dim,
            "weight_W1": W1,
            "weight_b1": b1,
            "weight_W2": W2,
            "weight_b2": b2,
            "origin": "cortex_constructed_attention",
            "n_positions": T,
            "query_vocab_size": V_q,
            "key_vocab_size": V_k,
            "value_vocab_size": V_v,
            "output_vocab_size": V_o,
            "predicate_matrix": W_QK,
            "routing": list(routing),
            "w_ov_matrix": W_OV,
            "formula": ("single-query categorical attention: "
                        "output[o] = Σ_j W_QK[q, k_j] · W_OV[o, v_j]  — "
                        "Tracr §1.2/§1.3 with sparse-predicate softmax bypass"),
        })

        target = self.s.add_node("ReplacementTarget", {
            "op_name": f"attention_{label}",
            "baseline_total_ms": 0.0, "baseline_count": 1,
            "baseline_mean_ms": 0.0, "selected_at": time.time(),
        })
        self.s.set_attr(target, "input_dim", in_dim)
        self.s.set_attr(target, "output_dim", out_dim)
        pat_nid = next(n for n in self.s.nodes("DesignPattern")
                       if self.s.node(n)["attrs"].get("name") == pat_name)
        try:
            self.s.add_edge(target, "uses_pattern", pat_nid, {})
        except Exception:
            pass
        assemblage = self.assemble_network(target)
        if assemblage is not None:
            self.construct_weights(assemblage)
        return assemblage

    def construct_tracr_program_multilayer(self,
                                           program: dict) -> int | None:
        """Compile a MULTI-LAYER RASP-like program using Tracr's
        residual-stream model. Each operation writes to a new subspace
        of the residual stream; later ops can read from any earlier
        subspace.

        Program format:
          {
            "name": str,
            "n_positions": int,                  # sequence length T
            "vocab_size": int,                   # uniform V
            "input_streams": list[str],          # ordered initial streams
            "ops": [
              {"name": str, "op": "select",
               "query": stream_name, "key": stream_name,
               "predicate": "equal" | "less_than" | ...},
              {"name": str, "op": "aggregate",
               "selector": <name of a select op>,
               "value": stream_name,
               "routing": "identity" | "reverse" | list[int]},
              ...
            ],
            "output": stream_name,               # which stream to extract
          }

        Layout: assemblage is a chain of wide AssemblageSteps, one
        per Aggregate operation, plus a final extract step. Each wide
        step:
          · identity-passthrough on the existing residual stream
            (so later layers can read all earlier streams)
          · attention computation reading specific slots
          · appended output written to a new slot at the end

        Final step is a cpwl_linear that selects only the output
        stream from the full residual stream.

        Returns the NetworkAssemblage nid."""
        T = int(program.get("n_positions", 0))
        default_V = int(program.get("vocab_size", 0))
        ops = program.get("ops", [])
        input_streams = program.get("input_streams", ["q", "k", "v"])
        output_stream = program.get("output")
        if T < 1 or not ops or not output_stream:
            return None

        # Residual stream schema: per-stream (slot, vocab_size).
        # Two input-stream formats supported:
        #   legacy: list[str] of names; all use default_V
        #   new:    list[dict] of {"name": str, "vocab_size": int}
        stream_info: dict[str, dict] = {}
        residual_dim = 0
        for entry in input_streams:
            if isinstance(entry, dict):
                name = entry["name"]
                v_size = int(entry.get("vocab_size", default_V))
            else:
                name = entry
                v_size = default_V
            if v_size < 1:
                return None
            stream_info[name] = {"slot": residual_dim, "vocab_size": v_size}
            residual_dim += T * v_size
        initial_residual_dim = residual_dim

        # Each layer-emitting op (Aggregate or Map) becomes one wide step.
        # Select ops are referenced by Aggregates and don't emit a layer
        # by themselves.
        select_ops = {o["name"]: o for o in ops if o.get("op") == "select"}
        layer_emitting = [o for o in ops if o.get("op") in ("aggregate", "map")]
        if not layer_emitting:
            return None

        layer_step_names = []
        self._dyn_counter += 1
        counter = self._dyn_counter
        prog_label = program.get("name", "multilayer")

        for layer_idx, op in enumerate(layer_emitting):
            op_kind = op["op"]
            new_stream_name = op["name"]
            output_slot = residual_dim  # appended at the end

            if op_kind == "aggregate":
                sel_name = op.get("selector")
                if sel_name not in select_ops:
                    return None
                sel_op = select_ops[sel_name]
                query_stream = sel_op["query"]
                key_stream = sel_op["key"]
                value_stream = op["value"]

                if (query_stream not in stream_info
                        or key_stream not in stream_info
                        or value_stream not in stream_info):
                    return None

                V_q = stream_info[query_stream]["vocab_size"]
                V_k = stream_info[key_stream]["vocab_size"]
                V_v = stream_info[value_stream]["vocab_size"]
                # Determine output vocab: explicit > routing-implied > V_v.
                V_o = int(op.get("output_vocab_size", 0))
                routing_spec = op.get("routing", "identity")
                routing = self._resolve_tracr_routing(routing_spec, V_v)
                if routing is None or len(routing) != V_v:
                    return None
                if V_o <= 0:
                    V_o = max(routing) + 1 if routing else V_v

                predicate = self._resolve_tracr_predicate(sel_op["predicate"])
                if predicate is None:
                    return None

                layer_mats = self._build_residual_attention_step(
                    residual_dim_in=residual_dim,
                    T=T, V_q=V_q, V_k=V_k, V_v=V_v, V_o=V_o,
                    query_slot=stream_info[query_stream]["slot"],
                    key_slot=stream_info[key_stream]["slot"],
                    value_slot=stream_info[value_stream]["slot"],
                    output_slot=output_slot,
                    predicate=predicate,
                    routing=routing,
                )
                new_stream_vocab = V_o
                layer_op_kind = "aggregate"
                layer_summary = (f"select {sel_op['predicate']} | "
                                 f"route {routing_spec} | "
                                 f"V_q={V_q} V_k={V_k} V_v={V_v} V_o={V_o}")
            elif op_kind == "map":
                input_stream = op.get("input")
                if input_stream not in stream_info:
                    return None
                V_in = stream_info[input_stream]["vocab_size"]
                mapping_spec = op.get("mapping")
                mapping = self._resolve_tracr_mapping(mapping_spec, V_in)
                if mapping is None or len(mapping) != V_in:
                    return None
                V_out = int(op.get("output_vocab_size", 0))
                if V_out <= 0:
                    V_out = max(mapping) + 1 if mapping else V_in
                # Validate mapping values are in [0, V_out).
                for o in mapping:
                    if not (0 <= o < V_out):
                        return None
                layer_mats = self._build_residual_map_step(
                    residual_dim_in=residual_dim,
                    T=T, V_in=V_in, V_out=V_out,
                    input_slot=stream_info[input_stream]["slot"],
                    output_slot=output_slot,
                    mapping=mapping,
                )
                new_stream_vocab = V_out
                layer_op_kind = "map"
                layer_summary = (f"map {mapping_spec} | "
                                 f"V_in={V_in} V_out={V_out}")
            else:
                return None

            if layer_mats is None:
                return None

            step_pat_name = (
                f"_tracr_layer_{prog_label}_L{layer_idx}_"
                f"{new_stream_name}_c{counter}")
            self.s.add_node("DesignPattern", {
                "name": step_pat_name,
                "gadget_kind": "cpwl_primitive",
                "dim_behavior": "transforms",
                "dim_in": residual_dim,
                "dim_out": residual_dim + T * new_stream_vocab,
                "weight_W1": layer_mats["W1"],
                "weight_b1": layer_mats["b1"],
                "weight_W2": layer_mats["W2"],
                "weight_b2": layer_mats["b2"],
                "origin": "cortex_constructed_tracr_layer",
                "tracr_layer_op": new_stream_name,
                "tracr_layer_kind": layer_op_kind,
                "tracr_layer_summary": layer_summary,
                "tracr_new_stream_vocab": new_stream_vocab,
            })
            layer_step_names.append(step_pat_name)

            stream_info[new_stream_name] = {
                "slot": residual_dim,
                "vocab_size": new_stream_vocab,
            }
            residual_dim += T * new_stream_vocab

        # Verify output stream exists.
        if output_stream not in stream_info:
            return None
        output_slot_final = stream_info[output_stream]["slot"]
        output_vocab_final = stream_info[output_stream]["vocab_size"]
        final_out_dim = T * output_vocab_final

        # Extract step: cpwl_linear selecting only the output stream's slots.
        extract_W = [[0.0] * residual_dim for _ in range(final_out_dim)]
        for k in range(final_out_dim):
            extract_W[k][output_slot_final + k] = 1.0
        extract_b = [0.0] * final_out_dim
        extract_name = f"_tracr_extract_{prog_label}_c{counter}"
        self.s.add_node("DesignPattern", {
            "name": extract_name,
            "gadget_kind": "cpwl_linear",
            "dim_behavior": "transforms",
            "dim_in": residual_dim,
            "dim_out": final_out_dim,
            "weight_W": extract_W,
            "weight_b": extract_b,
            "origin": "cortex_constructed_tracr_extract",
            "extracts_stream": output_stream,
            "from_slot": output_slot_final,
            "output_vocab_size": output_vocab_final,
        })

        # Top-level composed pattern.
        top_name = f"_tracr_mlayer_{prog_label}_top_c{counter}"
        self.s.add_node("DesignPattern", {
            "name": top_name,
            "gadget_kind": "cpwl_composed",
            "dim_behavior": "transforms",
            "dim_in": initial_residual_dim,
            "dim_out": final_out_dim,
            "gadget_chain": layer_step_names + [extract_name],
            "origin": "cortex_constructed_tracr_multilayer",
            "n_layers": len(layer_emitting),
            "tracr_program_name": prog_label,
            "tracr_streams": list(stream_info.keys()),
            "tracr_stream_vocabs": {n: info["vocab_size"]
                                    for n, info in stream_info.items()},
            "tracr_output_stream": output_stream,
            "tracr_output_vocab": output_vocab_final,
        })

        target = self.s.add_node("ReplacementTarget", {
            "op_name": f"tracr_mlayer_{prog_label}",
            "baseline_total_ms": 0.0, "baseline_count": 1,
            "baseline_mean_ms": 0.0, "selected_at": time.time(),
        })
        self.s.set_attr(target, "input_dim", initial_residual_dim)
        self.s.set_attr(target, "output_dim", final_out_dim)
        top_nid = next(n for n in self.s.nodes("DesignPattern")
                       if self.s.node(n)["attrs"].get("name") == top_name)
        try:
            self.s.add_edge(target, "uses_pattern", top_nid, {})
        except Exception:
            pass
        assemblage = self.assemble_network(target)
        if assemblage is not None:
            self.construct_weights(assemblage)
        return assemblage

    def _build_residual_map_step(self,
                                  residual_dim_in: int,
                                  T: int,
                                  V_in: int, V_out: int,
                                  input_slot: int,
                                  output_slot: int,
                                  mapping: list
                                  ) -> dict:
        """A categorical Map step in the residual stream. Identity-
        passthrough + per-position lookup writing to a new slot.

        For one-hot input at each position (size V_in), each hidden
        unit (i, v) fires iff input[i][v] = 1 (i.e. position i has
        value v). The output at slot (i, mapping[v]) gets the hidden
        unit's contribution."""
        in_dim = residual_dim_in
        out_dim = residual_dim_in + T * V_out
        n_pass = 2 * residual_dim_in
        n_map = T * V_in
        hidden_dim = n_pass + n_map

        W1 = [[0.0] * in_dim for _ in range(hidden_dim)]
        b1 = [0.0] * hidden_dim
        W2 = [[0.0] * hidden_dim for _ in range(out_dim)]
        b2 = [0.0] * out_dim

        # (1) Identity passthrough.
        for d in range(residual_dim_in):
            W1[2 * d][d] = 1.0
            W1[2 * d + 1][d] = -1.0
            W2[d][2 * d] = 1.0
            W2[d][2 * d + 1] = -1.0

        # (2) Map hidden units — fire iff input[i][v] = 1.
        for i in range(T):
            for v in range(V_in):
                h = n_pass + i * V_in + v
                W1[h][input_slot + i * V_in + v] = 1.0
                # b1 = 0; one-hot input means ReLU(x) = x.

        # (3) Write mapped output at slot (i, mapping[v]).
        for i in range(T):
            for v in range(V_in):
                o = mapping[v]
                out_idx = output_slot + i * V_out + o
                h = n_pass + i * V_in + v
                W2[out_idx][h] = 1.0

        return {"W1": W1, "b1": b1, "W2": W2, "b2": b2}

    def _resolve_tracr_mapping(self, spec, V: int) -> list | None:
        if isinstance(spec, (list, tuple)):
            return [int(x) for x in spec]
        if spec == "identity":
            return list(range(V))
        if spec == "reverse":
            return list(range(V - 1, -1, -1))
        if spec == "increment":
            return [(v + 1) % V for v in range(V)]
        if spec == "decrement":
            return [(v - 1) % V for v in range(V)]
        return None

    def _resolve_tracr_predicate(self, spec):
        if callable(spec):
            return spec
        if spec == "equal":
            return lambda q, k: q == k
        if spec == "not_equal":
            return lambda q, k: q != k
        if spec == "less_than":
            return lambda q, k: q < k
        if spec == "greater_than":
            return lambda q, k: q > k
        return None

    def _resolve_tracr_routing(self, spec, V: int):
        if isinstance(spec, (list, tuple)):
            return [int(x) for x in spec]
        if spec == "identity" or spec is None:
            return list(range(V))
        if spec == "reverse":
            return list(range(V - 1, -1, -1))
        return None

    def _build_residual_attention_step(self,
                                       residual_dim_in: int,
                                       T: int,
                                       V_q: int, V_k: int,
                                       V_v: int, V_o: int,
                                       query_slot: int,
                                       key_slot: int,
                                       value_slot: int,
                                       output_slot: int,
                                       predicate,
                                       routing: list
                                       ) -> dict | None:
        """A single attention layer that reads from the residual stream
        and APPENDS its output to it. Hidden units = 2·residual_dim_in
        (identity passthrough) + T²·V_q·V_k·V_v (attention)."""
        in_dim = residual_dim_in
        out_dim = residual_dim_in + T * V_o
        n_pass = 2 * residual_dim_in
        n_attn = T * T * V_q * V_k * V_v
        hidden_dim = n_pass + n_attn

        W1 = [[0.0] * in_dim for _ in range(hidden_dim)]
        b1 = [0.0] * hidden_dim
        W2 = [[0.0] * hidden_dim for _ in range(out_dim)]
        b2 = [0.0] * out_dim

        # (1) Identity passthrough on the existing residual stream.
        for d in range(residual_dim_in):
            W1[2 * d][d] = 1.0
            W1[2 * d + 1][d] = -1.0
            # b1 already 0
            W2[d][2 * d] = 1.0
            W2[d][2 * d + 1] = -1.0
            # b2 already 0

        # (2) Attention hidden units (offset by n_pass).
        stride_i = T * V_q * V_k * V_v
        stride_j = V_q * V_k * V_v
        stride_qv = V_k * V_v
        for i in range(T):
            for j in range(T):
                for qv in range(V_q):
                    for kv in range(V_k):
                        for vv in range(V_v):
                            h = (n_pass + i * stride_i + j * stride_j
                                 + qv * stride_qv + kv * V_v + vv)
                            W1[h][query_slot + i * V_q + qv] = 1.0
                            W1[h][key_slot + j * V_k + kv] = 1.0
                            W1[h][value_slot + j * V_v + vv] = 1.0
                            b1[h] = -2.0

        # (3) Attention output goes to slots output_slot..output_slot+T*V_o.
        for i in range(T):
            for o in range(V_o):
                out_idx = output_slot + i * V_o + o
                for j in range(T):
                    for qv in range(V_q):
                        for kv in range(V_k):
                            if not predicate(qv, kv):
                                continue
                            for vv in range(V_v):
                                if routing[vv] != o:
                                    continue
                                h = (n_pass + i * stride_i + j * stride_j
                                     + qv * stride_qv + kv * V_v + vv)
                                W2[out_idx][h] = 1.0

        return {"W1": W1, "b1": b1, "W2": W2, "b2": b2}

    def construct_tracr_program(self, program: dict) -> int | None:
        """Compile a small RASP-like program into a categorical
        attention assemblage — Tracr §1.6 (single-layer subset).

        Program format:
          {
            "name": str,
            "n_positions": int,             # sequence length T
            "vocab_size": int,              # categorical vocab (uniform V)
            "ops": [
              {"name": str, "op": "select",
               "query": stream_name,
               "key": stream_name,
               "predicate": "equal" | "less_than" | "greater_than" |
                            "not_equal" | callable},
              {"name": str, "op": "aggregate",
               "selector": <name of a select op>,
               "value": stream_name,
               "routing": "identity" | "reverse" | list[int]},
            ],
            "output": str,                  # name of the output op
          }

        Pipeline implements the doc's six steps for this subset:
          1. parse ops (already in dict form)
          2. value inference (uniform vocab_size; deferred)
          3. per-node gadget dispatch — Select → W_QK, Aggregate → W_OV,
             paired into one attention layer
          4. layer allocation — single layer here
          5. stack — single step
          6. weight assembly — delegated to construct_weights via
             construct_categorical_attention_multi_query

        Returns the NetworkAssemblage nid.
        """
        T = int(program.get("n_positions", 0))
        V = int(program.get("vocab_size", 0))
        ops = program.get("ops", [])
        if T < 1 or V < 1 or not ops:
            return None

        # Find the Select + Aggregate pair (single-layer subset).
        select_op = next((o for o in ops if o.get("op") == "select"), None)
        agg_op = next((o for o in ops if o.get("op") == "aggregate"), None)
        if select_op is None or agg_op is None:
            return None
        if agg_op.get("selector") != select_op.get("name"):
            return None

        # Dispatch step 3: predicate spec → callable.
        pred_spec = select_op.get("predicate")
        if callable(pred_spec):
            predicate = pred_spec
        elif pred_spec == "equal":
            predicate = lambda q, k: q == k
        elif pred_spec == "not_equal":
            predicate = lambda q, k: q != k
        elif pred_spec == "less_than":
            predicate = lambda q, k: q < k
        elif pred_spec == "greater_than":
            predicate = lambda q, k: q > k
        else:
            return None

        # Dispatch step 3 (cont): routing spec → list.
        route_spec = agg_op.get("routing", "identity")
        if isinstance(route_spec, (list, tuple)):
            routing = [int(x) for x in route_spec]
        elif route_spec == "identity":
            routing = list(range(V))
        elif route_spec == "reverse":
            routing = list(range(V - 1, -1, -1))
        else:
            return None
        if len(routing) != V:
            return None

        # Steps 4-6: single attention layer wraps the Select+Aggregate.
        assemblage = self.construct_categorical_attention_multi_query(
            predicate=predicate,
            routing=routing,
            T=T, V_q=V, V_k=V, V_v=V, V_o=V,
            label=program.get("name", "tracr_program"))
        if assemblage is None:
            return None

        # Record the program spec on the assemblage's metadata so the
        # architecture cortex can audit what was compiled.
        self.s.set_attr(assemblage, "tracr_program_name",
                        program.get("name", ""))
        self.s.set_attr(assemblage, "tracr_select_name",
                        select_op.get("name", ""))
        self.s.set_attr(assemblage, "tracr_aggregate_name",
                        agg_op.get("name", ""))
        self.s.set_attr(assemblage, "tracr_predicate",
                        str(pred_spec) if not callable(pred_spec)
                        else "<callable>")
        self.s.set_attr(assemblage, "tracr_routing",
                        str(route_spec))
        return assemblage

    def construct_selector_count(self,
                                 predicate,
                                 T: int,
                                 V_q: int,
                                 V_k: int,
                                 label: str = "count"
                                 ) -> int | None:
        """Tracr §1.5 SelectorWidth — counts matches per query position.

        For each query position i ∈ [0, T) and binary categorical
        predicate p(q_idx, k_idx), output:
            w_i = #{ j ∈ [0, T) : p(q_i_idx, k_j_idx) }

        The doc reaches w via BOS-softmax (x = 1/(1+w) via attention,
        then w = 1/x − 1 via the inverter MLP). For sparse categorical
        predicates we can compute w directly with a single ReLU layer
        — no softmax, no division needed.

        Input layout: concatenated one-hots
          slots 0..T·V_q-1        : T query one-hots
          slots T·V_q..T·V_q+T·V_k: T key one-hots
        Output: T scalars (one count per query position).

        Hidden unit (i, j, qv, kv) = ReLU(q_i[qv] + k_j[kv] − 1) — fires
        iff q_i is one-hot at qv AND k_j is one-hot at kv.
        Output[i] = Σ_{j, qv, kv} p(qv, kv) · hidden[i, j, qv, kv]
                  = #{j : p(q_i_idx, k_j_idx)} for one-hot inputs.

        Hidden dim = T²·V_q·V_k. Pairs naturally with
        construct_selector_width_inverter via x = 1/(1+w) if you want
        to traverse the doc's full pipeline; here we return w
        directly."""
        in_dim = T * V_q + T * V_k
        hidden_dim = T * T * V_q * V_k
        out_dim = T

        W1 = [[0.0] * in_dim for _ in range(hidden_dim)]
        b1 = [-1.0] * hidden_dim
        stride_i = T * V_q * V_k
        stride_j = V_q * V_k
        for i in range(T):
            for j in range(T):
                for qv in range(V_q):
                    for kv in range(V_k):
                        h = (i * stride_i + j * stride_j
                             + qv * V_k + kv)
                        W1[h][i * V_q + qv] = 1.0
                        W1[h][T * V_q + j * V_k + kv] = 1.0

        W2 = [[0.0] * hidden_dim for _ in range(out_dim)]
        b2 = [0.0] * out_dim
        for i in range(T):
            for j in range(T):
                for qv in range(V_q):
                    for kv in range(V_k):
                        if not predicate(qv, kv):
                            continue
                        h = (i * stride_i + j * stride_j
                             + qv * V_k + kv)
                        W2[i][h] = 1.0

        W_QK = [[1.0 if predicate(qv, kv) else 0.0
                 for kv in range(V_k)]
                for qv in range(V_q)]

        self._dyn_counter += 1
        counter = self._dyn_counter
        pat_name = f"_selector_count_{label}_c{counter}"
        self.s.add_node("DesignPattern", {
            "name": pat_name,
            "gadget_kind": "cpwl_primitive",
            "dim_behavior": "transforms",
            "dim_in": in_dim, "dim_out": out_dim,
            "weight_W1": W1,
            "weight_b1": b1,
            "weight_W2": W2,
            "weight_b2": b2,
            "origin": "cortex_constructed_selector_count",
            "n_positions": T,
            "query_vocab_size": V_q,
            "key_vocab_size": V_k,
            "predicate_matrix": W_QK,
            "formula": ("w_i = #{ j : predicate(q_i, k_j) }  — "
                        "Tracr §1.5 count (BOS-softmax bypass)"),
        })

        target = self.s.add_node("ReplacementTarget", {
            "op_name": f"selector_count_{label}",
            "baseline_total_ms": 0.0, "baseline_count": 1,
            "baseline_mean_ms": 0.0, "selected_at": time.time(),
        })
        self.s.set_attr(target, "input_dim", in_dim)
        self.s.set_attr(target, "output_dim", out_dim)
        pat_nid = next(n for n in self.s.nodes("DesignPattern")
                       if self.s.node(n)["attrs"].get("name") == pat_name)
        try:
            self.s.add_edge(target, "uses_pattern", pat_nid, {})
        except Exception:
            pass
        assemblage = self.assemble_network(target)
        if assemblage is not None:
            self.construct_weights(assemblage)
        return assemblage

    def construct_categorical_attention_multi_query(
            self,
            predicate,
            routing: list,
            T: int,
            V_q: int,
            V_k: int,
            V_v: int,
            V_o: int,
            label: str = "attn_mq"
    ) -> int | None:
        """Multi-query categorical attention layer — T queries each
        attending to T (key, value) pairs in the SAME input.

        Input layout (concatenated one-hots, total V_q·T + V_k·T + V_v·T):
          slots 0..T·V_q-1                       : T query one-hots
                                                   (slot i·V_q + qv = q_i[qv])
          slots T·V_q..T·V_q+T·V_k-1             : T key one-hots
          slots T·V_q+T·V_k..end                 : T value one-hots
        Output: T·V_o (T output one-hots concatenated).

        For each query position i, output[i] = the aggregated value(s)
        from positions j where predicate(q_i, k_j) holds, routed through
        W_OV. Same softmax-bypass logic as the single-query version
        (sparse predicates → direct selection).

        Hidden dim: T·T·V_q·V_k·V_v. For T=V=3 that's 243 units."""
        if len(routing) != V_v:
            return None
        for o in routing:
            if not (0 <= o < V_o):
                return None

        in_dim = T * V_q + T * V_k + T * V_v
        hidden_dim = T * T * V_q * V_k * V_v
        out_dim = T * V_o

        # W1: hidden_{i, j, qv, kv, vv} reads q_i[qv], k_j[kv], v_j[vv].
        W1 = [[0.0] * in_dim for _ in range(hidden_dim)]
        b1 = [-2.0] * hidden_dim
        stride_i = T * V_q * V_k * V_v
        stride_j = V_q * V_k * V_v
        stride_qv = V_k * V_v
        for i in range(T):
            for j in range(T):
                for qv in range(V_q):
                    for kv in range(V_k):
                        for vv in range(V_v):
                            h = (i * stride_i + j * stride_j
                                 + qv * stride_qv + kv * V_v + vv)
                            W1[h][i * V_q + qv] = 1.0           # q_i slot
                            W1[h][T * V_q + j * V_k + kv] = 1.0  # k_j slot
                            W1[h][T * V_q + T * V_k
                                  + j * V_v + vv] = 1.0          # v_j slot

        # W2: output[i*V_o + o] = Σ_{j, qv, kv, vv}
        #     predicate(qv, kv) · 1{routing[vv]=o} · hidden[i, j, qv, kv, vv]
        W2 = [[0.0] * hidden_dim for _ in range(out_dim)]
        b2 = [0.0] * out_dim
        for i in range(T):
            for o in range(V_o):
                out_idx = i * V_o + o
                for j in range(T):
                    for qv in range(V_q):
                        for kv in range(V_k):
                            if not predicate(qv, kv):
                                continue
                            for vv in range(V_v):
                                if routing[vv] != o:
                                    continue
                                h = (i * stride_i + j * stride_j
                                     + qv * stride_qv + kv * V_v + vv)
                                W2[out_idx][h] = 1.0

        W_QK = [[1.0 if predicate(qv, kv) else 0.0
                 for kv in range(V_k)]
                for qv in range(V_q)]
        W_OV = [[1.0 if routing[vv] == o else 0.0
                 for vv in range(V_v)]
                for o in range(V_o)]

        self._dyn_counter += 1
        counter = self._dyn_counter
        pat_name = f"_attn_mq_{label}_c{counter}"
        self.s.add_node("DesignPattern", {
            "name": pat_name,
            "gadget_kind": "cpwl_primitive",
            "dim_behavior": "transforms",
            "dim_in": in_dim, "dim_out": out_dim,
            "weight_W1": W1,
            "weight_b1": b1,
            "weight_W2": W2,
            "weight_b2": b2,
            "origin": "cortex_constructed_attention_mq",
            "n_positions": T,
            "query_vocab_size": V_q,
            "key_vocab_size": V_k,
            "value_vocab_size": V_v,
            "output_vocab_size": V_o,
            "predicate_matrix": W_QK,
            "routing": list(routing),
            "w_ov_matrix": W_OV,
            "formula": ("multi-query categorical attention: T queries × "
                        "T (key, value) pairs → T outputs"),
        })

        target = self.s.add_node("ReplacementTarget", {
            "op_name": f"attention_mq_{label}",
            "baseline_total_ms": 0.0, "baseline_count": 1,
            "baseline_mean_ms": 0.0, "selected_at": time.time(),
        })
        self.s.set_attr(target, "input_dim", in_dim)
        self.s.set_attr(target, "output_dim", out_dim)
        pat_nid = next(n for n in self.s.nodes("DesignPattern")
                       if self.s.node(n)["attrs"].get("name") == pat_name)
        try:
            self.s.add_edge(target, "uses_pattern", pat_nid, {})
        except Exception:
            pass
        assemblage = self.assemble_network(target)
        if assemblage is not None:
            self.construct_weights(assemblage)
        return assemblage

    def construct_aggregate_ov(self,
                               routing: list,
                               value_vocab_size: int,
                               output_vocab_size: int,
                               label: str = "aggregate"
                               ) -> int | None:
        """Tracr §1.3 — Aggregate(selector, value) → W_OV.

        Builds the categorical W_OV matrix that maps a selected value
        (one-hot of size value_vocab_size) into the output s-op's
        subspace (one-hot of size output_vocab_size). For each value
        position v, routing[v] gives the output position to write to.

        Construction: 2-layer ReLU MLP where W2 = W_OV (the routing
        permutation matrix). Same shape as lookup_table but typed
        with Tracr metadata (W_OV vs Map) so the architecture cortex
        can distinguish the two attention-family functions.

        Returns the NetworkAssemblage nid."""
        if len(routing) != value_vocab_size:
            return None
        for o in routing:
            if not (0 <= o < output_vocab_size):
                return None

        V_v, V_o = value_vocab_size, output_vocab_size
        # W1 = I_{V_v} (identity passthrough on one-hot input).
        W1 = [[1.0 if j == i else 0.0 for j in range(V_v)]
              for i in range(V_v)]
        b1 = [0.0] * V_v
        # W_OV[o, v] = 1 iff routing[v] = o.
        W_OV = [[0.0] * V_v for _ in range(V_o)]
        for v_idx, o_idx in enumerate(routing):
            W_OV[o_idx][v_idx] = 1.0
        b2 = [0.0] * V_o

        self._dyn_counter += 1
        counter = self._dyn_counter
        pat_name = f"_aggregate_ov_{label}_c{counter}"
        self.s.add_node("DesignPattern", {
            "name": pat_name,
            "gadget_kind": "cpwl_primitive",
            "dim_behavior": "transforms",
            "dim_in": V_v, "dim_out": V_o,
            "weight_W1": W1,
            "weight_b1": b1,
            "weight_W2": W_OV,
            "weight_b2": b2,
            "origin": "cortex_constructed_aggregate_ov",
            "value_vocab_size": V_v,
            "output_vocab_size": V_o,
            "routing": list(routing),
            "w_ov_matrix": W_OV,
            "formula": ("W_OV[o, v] = 1 iff routing[v] = o  — "
                        "Tracr §1.3 (categorical Aggregate)"),
        })

        target = self.s.add_node("ReplacementTarget", {
            "op_name": f"aggregate_ov_{label}",
            "baseline_total_ms": 0.0, "baseline_count": 1,
            "baseline_mean_ms": 0.0, "selected_at": time.time(),
        })
        self.s.set_attr(target, "input_dim", V_v)
        self.s.set_attr(target, "output_dim", V_o)
        pat_nid = next(n for n in self.s.nodes("DesignPattern")
                       if self.s.node(n)["attrs"].get("name") == pat_name)
        try:
            self.s.add_edge(target, "uses_pattern", pat_nid, {})
        except Exception:
            pass
        assemblage = self.assemble_network(target)
        if assemblage is not None:
            self.construct_weights(assemblage)
        return assemblage

    def construct_pwl_through_points(self,
                                     breakpoints: list,
                                     values: list,
                                     label: str = "pwl"
                                     ) -> int | None:
        """General-purpose CPWL through specified (x_k, y_k) points.

        Builds a 1-hidden-layer ReLU MLP whose forward(x) passes
        EXACTLY through every (breakpoint, value) pair. Behaviour
        outside [breakpoints[0], breakpoints[-1]]:
          x < breakpoints[0]   → values[0]  (constant before first)
          x > breakpoints[-1]  → linearly extrapolated at last slope

        Used as a building block for SelectorWidth, arbitrary CPWL
        approximations, and as a generalisation of square_pwl_10."""
        n = len(breakpoints)
        if n < 2 or len(values) != n:
            return None
        # Check strictly increasing breakpoints.
        for k in range(n - 1):
            if breakpoints[k] >= breakpoints[k + 1]:
                return None
        # Compute slopes between consecutive breakpoints.
        slopes = []
        for k in range(n - 1):
            dx = float(breakpoints[k + 1] - breakpoints[k])
            slopes.append((float(values[k + 1]) - float(values[k])) / dx)
        # slope_change[k] is what we add to W2 for hidden unit k:
        #   slope_change[0] = slopes[0]  (transition from "before x_0,
        #                                 slope 0" to "between x_0 and
        #                                 x_1, slope slopes[0]")
        #   slope_change[k] = slopes[k] - slopes[k-1] for k ≥ 1.
        slope_changes = [slopes[0]]
        for k in range(1, n - 1):
            slope_changes.append(slopes[k] - slopes[k - 1])

        # Hidden units: one per breakpoint EXCEPT the last
        # (the last segment continues with slopes[-1] for x > last bp).
        n_hidden = n - 1
        W1 = [[1.0] for _ in range(n_hidden)]
        b1 = [-float(breakpoints[k]) for k in range(n_hidden)]
        W2 = [[float(sc) for sc in slope_changes]]
        b2 = [float(values[0])]

        self._dyn_counter += 1
        counter = self._dyn_counter
        pat_name = f"_pwl_{label}_c{counter}"
        self.s.add_node("DesignPattern", {
            "name": pat_name,
            "gadget_kind": "cpwl_primitive",
            "dim_behavior": "preserves",
            "dim_in": 1, "dim_out": 1,
            "weight_W1": W1,
            "weight_b1": b1,
            "weight_W2": W2,
            "weight_b2": b2,
            "origin": "cortex_constructed_pwl",
            "breakpoints": list(map(float, breakpoints)),
            "values": list(map(float, values)),
            "formula": (
                "CPWL through " + " → ".join(
                    f"({bp:.4f}, {v:.4f})"
                    for bp, v in zip(breakpoints, values))),
        })

        target = self.s.add_node("ReplacementTarget", {
            "op_name": f"pwl_{label}",
            "baseline_total_ms": 0.0, "baseline_count": 1,
            "baseline_mean_ms": 0.0, "selected_at": time.time(),
        })
        self.s.set_attr(target, "input_dim", 1)
        self.s.set_attr(target, "output_dim", 1)
        pat_nid = next(n for n in self.s.nodes("DesignPattern")
                       if self.s.node(n)["attrs"].get("name") == pat_name)
        try:
            self.s.add_edge(target, "uses_pattern", pat_nid, {})
        except Exception:
            pass
        assemblage = self.assemble_network(target)
        if assemblage is not None:
            self.construct_weights(assemblage)
        return assemblage

    def construct_selector_width_inverter(self, w_max: int,
                                          label: str = "selwidth"
                                          ) -> int | None:
        """Tracr §1.5 — SelectorWidth inversion stage.

        The full SelectorWidth gadget is two steps:
          (a) attention with BOS as value → x = 1/(1 + w), where w
              is the count of matching keys per query
          (b) MLP inverts: w = 1/x − 1, cleans BOS

        Step (b) here as a CPWL inverter via construct_pwl_through_points
        on the discrete breakpoints {x_k = 1/(k+1) : k = 0..w_max},
        each mapped to w_k = k. Exact at every discrete input — this
        is the BOS-attention output range when w is a count of matches.

        Step (a) needs a full attention layer (softmax + sequence
        positions) which is not yet lifted. Construction is restricted
        to the inversion MLP; downstream cortices may feed it BOS-
        attention outputs from an external implementation."""
        if w_max < 1:
            return None
        # Breakpoints in increasing x: 1/(w_max+1), 1/w_max, ..., 1/2, 1
        # Values at those breakpoints: w_max, w_max-1, ..., 1, 0
        breakpoints = [1.0 / (w_max + 1 - k) for k in range(w_max + 1)]
        values = [float(w_max - k) for k in range(w_max + 1)]
        return self.construct_pwl_through_points(
            breakpoints=breakpoints,
            values=values,
            label=f"selwidth_inv_{label}_wmax{w_max}")

    def construct_select_qk(self,
                            predicate,
                            query_vocab_size: int,
                            key_vocab_size: int,
                            label: str = "select"
                            ) -> int | None:
        """Build a categorical Select(query, key, predicate) → W_QK
        per Tracr §1.2. The substrate uses concatenated one-hots
        (q ⊕ k) of total dim V_q + V_k as input; output is a scalar
        score that equals W_QK[q_idx, k_idx] = 1 if predicate holds
        else 0.

        Construction (2-layer ReLU MLP):
          · for each pair (i, j) of (query_idx, key_idx), a hidden
            unit computes ReLU(q[i] + k[j] − 1) — fires only when
            BOTH one-hots are active at those positions (AND gate
            on one-hots).
          · the readout sums the predicate matrix entries weighted
            by hidden activations.
            output = Σ_{i, j} W_QK[i, j] · ReLU(q[i] + k[j] − 1)

        For one-hot inputs at positions (q_idx, k_idx), only one
        hidden unit fires; output = W_QK[q_idx, k_idx]. The W_QK
        matrix and the discrete predicate are recorded on the
        resulting DesignPattern so downstream cortices can inspect
        what the attention layer attends to.

        Returns the NetworkAssemblage nid."""
        # Build the categorical predicate matrix W̃_QK.
        W_QK = [[1.0 if predicate(i, j) else 0.0
                 for j in range(key_vocab_size)]
                for i in range(query_vocab_size)]

        V_q = query_vocab_size
        V_k = key_vocab_size
        V_in = V_q + V_k
        hidden_dim = V_q * V_k

        # W1: hidden unit (i, j) reads q[i] (col i) and k[j] (col V_q + j).
        W1 = [[0.0] * V_in for _ in range(hidden_dim)]
        b1 = [-1.0] * hidden_dim   # AND gate: q[i] + k[j] − 1
        for i in range(V_q):
            for j in range(V_k):
                idx = i * V_k + j
                W1[idx][i] = 1.0
                W1[idx][V_q + j] = 1.0

        # W2: scalar readout from the predicate matrix entries.
        W2 = [[W_QK[i][j] for i in range(V_q) for j in range(V_k)]]
        b2 = [0.0]

        self._dyn_counter += 1
        counter = self._dyn_counter
        pat_name = f"_select_qk_{label}_c{counter}"
        self.s.add_node("DesignPattern", {
            "name": pat_name,
            "gadget_kind": "cpwl_primitive",
            "dim_behavior": "transforms",
            "dim_in": V_in, "dim_out": 1,
            "weight_W1": W1,
            "weight_b1": b1,
            "weight_W2": W2,
            "weight_b2": b2,
            "origin": "cortex_constructed_select_qk",
            "query_vocab_size": V_q,
            "key_vocab_size": V_k,
            "predicate_matrix": W_QK,
            "formula": ("score(q, k) = W_QK[argmax(q), argmax(k)] "
                        "via Tracr §1.2 (categorical Select)"),
        })

        target = self.s.add_node("ReplacementTarget", {
            "op_name": f"select_qk_{label}",
            "baseline_total_ms": 0.0, "baseline_count": 1,
            "baseline_mean_ms": 0.0, "selected_at": time.time(),
        })
        self.s.set_attr(target, "input_dim", V_in)
        self.s.set_attr(target, "output_dim", 1)
        pat_nid = next(n for n in self.s.nodes("DesignPattern")
                       if self.s.node(n)["attrs"].get("name") == pat_name)
        try:
            self.s.add_edge(target, "uses_pattern", pat_nid, {})
        except Exception:
            pass
        assemblage = self.assemble_network(target)
        if assemblage is not None:
            self.construct_weights(assemblage)
        return assemblage

    def _evaluate_pattern_at(self, pattern_name: str,
                             x_value: float) -> float | None:
        """Build a throwaway assemblage for pattern_name, forward x_value
        through it, and return the first output dim. Used by the
        multiplexer to check continuity at the boundary."""
        pat = self._find_pattern_by_name(pattern_name)
        if pat is None:
            return None
        in_dim = int(pat.get("dim_in", 1))
        out_dim = int(pat.get("dim_out", 1))
        tmp_target = self.s.add_node("ReplacementTarget", {
            "op_name": f"_mux_probe_{pattern_name}",
            "baseline_total_ms": 0.0, "baseline_count": 1,
            "baseline_mean_ms": 0.0, "selected_at": 0.0,
        })
        self.s.set_attr(tmp_target, "input_dim", in_dim)
        self.s.set_attr(tmp_target, "output_dim", out_dim)
        pat_nid = next(n for n in self.s.nodes("DesignPattern")
                       if self.s.node(n)["attrs"].get("name") == pattern_name)
        try:
            self.s.add_edge(tmp_target, "uses_pattern", pat_nid, {})
        except Exception:
            pass
        tmp = self.assemble_network(tmp_target)
        if tmp is None:
            return None
        self.construct_weights(tmp)
        out = self.forward(tmp, [float(x_value)] * in_dim)
        return float(out[0])

    def _mint_scalar_linear(self, slope: float, intercept: float = 0.0,
                            label: str = "scalar") -> str:
        """Mint a cpwl_linear gadget for f(x) = slope·x + intercept,
        1D in, 1D out. Used as a building block for multiplexer branches
        and other simple affine constructions."""
        self._dyn_counter += 1
        counter = self._dyn_counter
        name = (f"_{label}_s{slope:+.4f}_i{intercept:+.4f}_c{counter}"
                .replace(".", "p"))
        self.s.add_node("DesignPattern", {
            "name": name,
            "gadget_kind": "cpwl_linear",
            "dim_behavior": "transforms",
            "dim_in": 1, "dim_out": 1,
            "weight_W": [[float(slope)]],
            "weight_b": [float(intercept)],
            "origin": "cortex_constructed_scalar_linear",
            "formula": f"f(x) = {slope}·x + {intercept}",
        })
        return name

    def construct_elm_readout(self, feature_pattern_name: str,
                              X: list, T: list,
                              label: str = "elm") -> int | None:
        """Solve β = H† T analytically for the readout when features
        are constructed but targets depend on grounded data — the
        Extreme Learning Machine pattern (§3 of the construction doc).

        feature_pattern_name: name of a DesignPattern that, when
                              assembled, maps an input vector to a
                              feature vector. The features are FIXED
                              (constructed from understanding); only
                              the readout β is fit to data.
        X: list of input vectors (or scalars; promoted to 1-vector).
        T: list of scalar targets matched 1:1 with X.

        Algorithm:
          1. Materialise the feature assemblage; run forward on each
             X_i to get the row H_i of the design matrix.
          2. β = pinv(H) · T          (Moore-Penrose least-squares)
          3. Build a cpwl_linear readout with weight_W = [β], b = [0].
          4. Mint a composed top pattern chaining feature → readout.
          5. Assemble + render weights; return the final assemblage.

        The PINV call is the world-adapter to numpy.linalg; nothing
        gets trained, no iteration. The β returned by pinv is the
        unique minimum-norm least-squares solution."""
        try:
            import numpy as np
        except ImportError:
            return None

        feature_pat = self._find_pattern_by_name(feature_pattern_name)
        if feature_pat is None:
            return None
        input_dim = int(feature_pat.get("dim_in", 1))
        feature_dim = int(feature_pat.get("dim_out", 1))

        # Step 1: temporary assemblage so we can call forward() on each
        # sample to extract its feature row.
        tmp_target = self.s.add_node("ReplacementTarget", {
            "op_name": f"_elm_features_{label}",
            "baseline_total_ms": 0.0, "baseline_count": 1,
            "baseline_mean_ms": 0.0, "selected_at": 0.0,
        })
        self.s.set_attr(tmp_target, "input_dim", input_dim)
        self.s.set_attr(tmp_target, "output_dim", feature_dim)
        feat_pat_nid = next(n for n in self.s.nodes("DesignPattern")
                            if self.s.node(n)["attrs"].get("name")
                            == feature_pattern_name)
        self.s.add_edge(tmp_target, "uses_pattern", feat_pat_nid, {})
        tmp_assemblage = self.assemble_network(tmp_target)
        if tmp_assemblage is None:
            return None
        self.construct_weights(tmp_assemblage)

        # Step 2: build H matrix by running forward on each sample.
        H_rows = []
        for x in X:
            x_vec = [float(v) for v in (x if isinstance(x, (list, tuple))
                                        else [x])]
            feats = self.forward(tmp_assemblage, x_vec)
            H_rows.append([float(v) for v in feats])
        H = np.array(H_rows, dtype=float)
        T_vec = np.array([float(t) for t in T], dtype=float)

        # Step 3: β = pinv(H) · T  — the closed-form least-squares solve.
        H_pinv = np.linalg.pinv(H)
        beta = H_pinv @ T_vec
        residual = float(np.linalg.norm(H @ beta - T_vec))

        # Step 4: mint the readout pattern with W = [β].
        self._dyn_counter += 1
        counter = self._dyn_counter
        readout_name = f"_elm_readout_{label}_c{counter}"
        self.s.add_node("DesignPattern", {
            "name": readout_name,
            "gadget_kind": "cpwl_linear",
            "dim_behavior": "transforms",
            "dim_in": feature_dim, "dim_out": 1,
            "weight_W": [beta.tolist()],
            "weight_b": [0.0],
            "origin": "cortex_constructed_elm",
            "residual_norm": residual,
            "n_samples": len(X),
        })

        # Step 5: top-level composed pattern chaining feature → readout.
        top_name = f"_elm_eval_{label}_c{counter}"
        self.s.add_node("DesignPattern", {
            "name": top_name,
            "gadget_kind": "cpwl_composed",
            "dim_behavior": "transforms",
            "dim_in": input_dim, "dim_out": 1,
            "gadget_chain": [feature_pattern_name, readout_name],
            "origin": "cortex_constructed_elm",
            "residual_norm": residual,
            "n_samples": len(X),
            "n_features": feature_dim,
        })

        # Step 6: final assemblage.
        target = self.s.add_node("ReplacementTarget", {
            "op_name": f"elm_eval_{label}",
            "baseline_total_ms": 0.0, "baseline_count": 1,
            "baseline_mean_ms": 0.0, "selected_at": time.time(),
        })
        self.s.set_attr(target, "input_dim", input_dim)
        self.s.set_attr(target, "output_dim", 1)
        top_nid = next(n for n in self.s.nodes("DesignPattern")
                       if self.s.node(n)["attrs"].get("name") == top_name)
        self.s.add_edge(target, "uses_pattern", top_nid, {})
        final = self.assemble_network(target)
        if final is not None:
            self.construct_weights(final)
        return final

    def construct_lookup_table(self, mapping: list[int],
                               label: str = "lookup") -> int | None:
        """Build a 2-layer ReLU MLP that realises a discrete function
        f: [0, V_in) → [0, V_out) — Tracr §1.4's categorical lookup.

        Input: one-hot vector of size V_in.
        Output: one-hot vector of size V_out, with 1 at position f(i)
                if the input one-hot was 1 at position i.

        Construction (W1=I_{V_in}, b1=0, W2 = mapping matrix, b2=0):
          hidden = ReLU(I·x + 0) = x  (one-hot input has no negatives)
          output = W2 · hidden
        where W2[j, i] = 1 iff f(i) = j.

        Mints a fresh DesignPattern with the literal matrices, sets up
        a synthetic ReplacementTarget, runs the assemble + construct
        pipeline, and returns the NetworkAssemblage nid.
        """
        if not mapping:
            return None
        V_in = len(mapping)
        V_out = max(mapping) + 1
        for i, v in enumerate(mapping):
            if v < 0:
                return None
        # W1 = identity (V_in × V_in)
        W1 = [[1.0 if j == i else 0.0 for j in range(V_in)]
              for i in range(V_in)]
        b1 = [0.0] * V_in
        # W2 = mapping matrix (V_out × V_in): row j has 1 at col i iff f(i)=j
        W2 = [[0.0] * V_in for _ in range(V_out)]
        for i, j in enumerate(mapping):
            W2[j][i] = 1.0
        b2 = [0.0] * V_out

        self._dyn_counter += 1
        counter = self._dyn_counter
        sig = "_".join(str(v) for v in mapping)
        pat_name = f"_lookup_{label}_{sig}_c{counter}"
        self.s.add_node("DesignPattern", {
            "name": pat_name,
            "gadget_kind": "cpwl_primitive",
            "dim_behavior": "transforms",
            "dim_in": V_in, "dim_out": V_out,
            "weight_W1": W1,
            "weight_b1": b1,
            "weight_W2": W2,
            "weight_b2": b2,
            "origin": "cortex_constructed_lookup",
            "mapping": list(mapping),
            "formula": f"discrete f: [{V_in}] → [{V_out}], "
                       f"mapping = {list(mapping)}",
        })

        target = self.s.add_node("ReplacementTarget", {
            "op_name": f"lookup_{label}_{sig}",
            "baseline_total_ms": 0.0,
            "baseline_count": 1,
            "baseline_mean_ms": 0.0,
            "selected_at": time.time(),
        })
        self.s.set_attr(target, "input_dim", V_in)
        self.s.set_attr(target, "output_dim", V_out)
        pat = next(n for n in self.s.nodes("DesignPattern")
                   if self.s.node(n)["attrs"].get("name") == pat_name)
        try:
            self.s.add_edge(target, "uses_pattern", pat, {})
        except Exception:
            pass
        assemblage = self.assemble_network(target)
        if assemblage is not None:
            self.construct_weights(assemblage)
        return assemblage

    def construct_monomial(self, k: int) -> str | None:
        """Build a gadget that computes x^k for x ∈ [−0.5, 0.5].
        Recursive definition:

          k=1 → identity_gadget                          (seeded)
          k=2 → square_pwl_signed_gadget                 (seeded)
          k=3 → cube_gadget                              (seeded)
          k≥4 → broadcast([identity, x^(k-1)]) → [x, x^(k-1)],
                then polarization_multiply → x · x^(k-1) = x^k

        Cached by k on the cortex so a polynomial evaluator that needs
        x⁴ and x⁵ doesn't rebuild x⁴ twice. Returns the gadget's name."""
        if k <= 0:
            return None
        if k == 1:
            return "identity_gadget"
        if k == 2:
            return "square_pwl_signed_gadget"
        if k == 3:
            return "cube_gadget"
        # Cache key — per-cortex memoisation.
        if not hasattr(self, "_monomial_cache"):
            self._monomial_cache: dict[int, str] = {}
        if k in self._monomial_cache:
            return self._monomial_cache[k]

        prev_name = self.construct_monomial(k - 1)
        if prev_name is None:
            return None
        lift_name = self.construct_broadcast_pattern(
            input_dim=1,
            branch_chains=[["identity_gadget"], [prev_name]],
            label=f"lift_x_x{k - 1}")
        if lift_name is None:
            return None
        self._dyn_counter += 1
        counter = self._dyn_counter
        top_name = f"_monomial_x{k}_c{counter}"
        self.s.add_node("DesignPattern", {
            "name": top_name,
            "gadget_kind": "cpwl_composed",
            "dim_behavior": "transforms",
            "dim_in": 1, "dim_out": 1,
            "gadget_chain": [lift_name, "polarization_multiply_gadget"],
            "origin": "cortex_constructed_monomial",
            "formula": f"f(x) ≈ x^{k} via x · x^{k-1}",
        })
        self._monomial_cache[k] = top_name
        return top_name

    def construct_polynomial_evaluator(self, coefficients) -> int | None:
        """Compose a polynomial-evaluator network from a coefficient
        vector at runtime. Mints fresh DesignPattern nodes for the
        coefficient-bearing pieces (so different polynomials produce
        different recipes the substrate can later query); then runs
        the same assemble_network + construct_weights pipeline as any
        seeded gadget.

        coefficients = [a_0, a_1, ..., a_k] computes
            p(x) = a_0 + a_1·x + a_2·x² + … + a_k·x^k.

        Degrees supported here:
          1  — purely linear: cpwl_linear with W=[[a_1]], b=[a_0].
          2  — quadratic: chain [monomial_lift_x_x2_gadget,
                                 cpwl_linear(W=[[a_1, a_2]], b=[a_0])].

        Higher degrees need a broadcast-with-composed-branches form of
        monomial_lift (lift to [x, x², x³, …, x^k]) — a follow-up to
        the heterogeneous-parallel infrastructure.

        Returns the NetworkAssemblage nid, or None if the degree is
        out of supported range.
        """
        coeffs = [float(c) for c in coefficients]
        degree = len(coeffs) - 1
        if degree < 1:
            return None

        a_0 = coeffs[0]
        sig = "_".join(f"{c:+.4f}" for c in coeffs).replace(".", "p")
        formula = (
            "f(x) = " + " + ".join(
                (f"({c:+.4f})·x^{i}" if i > 0
                 else f"{c:+.4f}")
                for i, c in enumerate(coeffs))
        )

        if degree == 1:
            a_1 = coeffs[1]
            combine_pat = self.s.add_node("DesignPattern", {
                "name": f"poly_eval_d1_{sig}",
                "gadget_kind": "cpwl_linear",
                "dim_in": 1, "dim_out": 1,
                "dim_behavior": "transforms",
                "weight_W": [[a_1]],
                "weight_b": [a_0],
                "origin": "cortex_constructed",
                "coefficients": coeffs,
                "formula": formula,
            })
            top_pattern_nid = combine_pat
        else:
            # degree ≥ 2: lift [x] → [x, x², …, x^k] via broadcast over
            # construct_monomial(j) for each j; then linear-combine.
            branches = []
            for j in range(1, degree + 1):
                mon_name = self.construct_monomial(j)
                if mon_name is None:
                    return None
                branches.append([mon_name])
            lift_name = self.construct_broadcast_pattern(
                input_dim=1,
                branch_chains=branches,
                label=f"poly_lift_d{degree}_{sig}")
            if lift_name is None:
                return None
            combine_pat = self.s.add_node("DesignPattern", {
                "name": f"poly_eval_d{degree}_combine_{sig}",
                "gadget_kind": "cpwl_linear",
                "dim_in": degree, "dim_out": 1,
                "dim_behavior": "transforms",
                "weight_W": [list(coeffs[1:])],
                "weight_b": [a_0],
                "origin": "cortex_constructed",
                "coefficients": coeffs,
            })
            eval_pat = self.s.add_node("DesignPattern", {
                "name": f"poly_eval_d{degree}_{sig}",
                "gadget_kind": "cpwl_composed",
                "dim_in": 1, "dim_out": 1,
                "dim_behavior": "transforms",
                "gadget_chain": [lift_name,
                                 f"poly_eval_d{degree}_combine_{sig}"],
                "origin": "cortex_constructed",
                "coefficients": coeffs,
                "formula": formula,
            })
            top_pattern_nid = eval_pat

        target = self.s.add_node("ReplacementTarget", {
            "op_name": f"poly_eval_d{degree}_{sig}",
            "baseline_total_ms": 0.0,
            "baseline_count": 1,
            "baseline_mean_ms": 0.0,
            "selected_at": time.time(),
        })
        self.s.set_attr(target, "input_dim", 1)
        self.s.set_attr(target, "output_dim", 1)
        try:
            self.s.add_edge(target, "uses_pattern", top_pattern_nid, {})
        except Exception:
            pass
        assemblage = self.assemble_network(target)
        if assemblage is not None:
            self.construct_weights(assemblage)
        return assemblage

    def forward(self, assemblage_nid: int, inputs) -> list[float]:
        """Run the constructed net on `inputs` — a graph-driven evaluator.
        Walks AssemblageSteps in order; for each step, reads its
        WeightTensors and applies hidden = ReLU(W1·x + b1);
        out = W2·hidden + b2. Then output of step i becomes input
        of step i+1 (function composition = layer stacking, §2.7).

        Loss steps (dim_behavior=loss) and steps without weights are
        skipped — forward is the pure inference path.

        Pure read of graph data; no torch, no construction. Used by
        probes and by downstream cortices that need to evaluate the
        constructed net."""
        x = [float(v) for v in inputs]
        steps = sorted(
            self.s.neighbours(assemblage_nid, "has_step"),
            key=lambda n: self.s.node(n)["attrs"].get("order", 0))
        for step in steps:
            step_attrs = self.s.node(step)["attrs"]
            if step_attrs.get("dim_behavior") == "loss":
                continue
            weights_by_role = {}
            for w in self.s.neighbours(step, "has_weight"):
                a = self.s.node(w)["attrs"]
                weights_by_role[a["role"]] = a["data"]
            if not all(r in weights_by_role for r in ("W1", "b1", "W2", "b2")):
                continue
            W1, b1 = weights_by_role["W1"], weights_by_role["b1"]
            W2, b2 = weights_by_role["W2"], weights_by_role["b2"]
            # ReLU(W1 · x + b1)
            hidden = []
            for row_idx, row in enumerate(W1):
                s_val = float(b1[row_idx])
                for col_idx, w in enumerate(row):
                    s_val += float(w) * float(x[col_idx])
                hidden.append(max(0.0, s_val))
            # W2 · hidden + b2
            out = []
            for row_idx, row in enumerate(W2):
                s_val = float(b2[row_idx])
                for col_idx, w in enumerate(row):
                    s_val += float(w) * float(hidden[col_idx])
                out.append(s_val)
            x = out
        return x

    # ------------------------------------------------------------------ survey

    def survey_pattern_opportunities(self) -> list[dict]:
        """Apply `pick_design_pattern` to every installed CodeTarget and
        return the cortex's own answer to 'what fits where'. The result
        is the agent's introspection — the same selector that drives
        the autonomous loop, run in read-only mode over every target.

        For each target, output records:
          op_name        : the CodeTarget's op_name
          design_tags    : the target's tag set the selector sees
          chosen_pattern : the winning DesignPattern's name (or None)
          pattern_origin : which seed the winner came from (`design_patterns`,
                           `neural_networks`, ...) — lets a reader spot
                           where an NN-shaped recipe was picked without
                           a Python filter doing the labelling
          pattern_category : the winning pattern's category attr
                           (`classification`, `cost_equivalence`, ...).
        """
        rows = []
        for cn in self.s.nodes("CodeTarget"):
            attrs = self.s.node(cn)["attrs"]
            op_name = attrs.get("op_name")
            entry = self._target_registry_entry(op_name) if op_name else None
            if entry is None:
                continue
            chosen = pick_design_pattern(self.s, entry["design_tags"])
            rows.append({
                "op_name": op_name,
                "design_tags": entry["design_tags"],
                "chosen_pattern": chosen["name"] if chosen else None,
                "pattern_origin": chosen.get("origin") if chosen else None,
                "pattern_category": chosen.get("category") if chosen else None,
            })
        return rows

    # ------------------------------------------------------------------ design

    def chosen_design_pattern(self) -> int | None:
        tgt = self.current_target()
        if tgt is None:
            return None
        for nid in self.s.neighbours(tgt, "uses_pattern"):
            return nid
        return None

    def pick_pattern_for_current_target(self) -> dict | None:
        tgt = self.current_target()
        if tgt is None:
            return None
        op = self.s.node(tgt)["attrs"].get("op_name")
        entry = self._target_registry_entry(op) if op else None
        if entry is None:
            return None
        return pick_design_pattern(self.s, entry["design_tags"])

    def attach_design_pattern(self, pattern_attrs: dict) -> None:
        tgt = self.current_target()
        if tgt is None:
            return
        for nid in self.s.nodes("DesignPattern"):
            if self.s.node(nid)["attrs"].get("name") == pattern_attrs["name"]:
                try:
                    self.s.add_edge(tgt, "uses_pattern", nid, {})
                except Exception:
                    pass
                return

    def note_no_pattern_matched(self) -> None:
        tgt = self.current_target()
        if tgt is None:
            return
        # Mark on the target so the design reflex doesn't re-fire on
        # the same target with the same empty result. We use a flag
        # attr (no graph relationship to record absence of a choice).
        self.s.set_attr(tgt, "design_pattern_search", "no_match")

    def _read_existing_source(self, op_name: str) -> str | None:
        entry = self._target_registry_entry(op_name)
        if entry is None or not entry["path"].exists():
            return None
        try:
            return entry["path"].read_text()
        except Exception:
            return None

    # -------------------------------------------------------------- mechanical draft (no LLM)

    def emittable_spec_for_target(self, target_nid: int) -> dict | None:
        """Resolve the target to an emittable PrimitiveSpec, or None.

        The faithful (teacher-free) drafting path only closes for the
        PRIMITIVE/Term-shaped class: a target whose op_name names a
        `PrimitiveSpec` graph node the agent ALREADY specified
        (runtime_design.agent_specify_*), AND whose `semantic_kind` the
        mechanical emitter knows a template for. Module-scale agent-logic
        targets (qualname like `domains.curious_agent.X`) have no
        PrimitiveSpec — they return None here and fall through to the
        teacher step (the open problem; no mechanical Python->Rust
        compiler exists, and we do NOT phone an LLM for it).

        Pure graph query: read the PrimitiveSpec node matching op_name,
        verify the emitter has a template for its semantic_kind by a dry
        emit. No mutation, no decision-in-Python beyond the lookup."""
        from . import runtime_design

        op_name = self.s.node(target_nid)["attrs"].get("op_name")
        if not op_name:
            return None
        spec = None
        for nid in self.s.nodes("PrimitiveSpec"):
            a = self.s.node(nid)["attrs"]
            if a.get("name") == op_name:
                spec = dict(a)
                break
        if spec is None:
            return None
        # The emitter is the authority on "emittable": if it can produce
        # the four-home fragments for this spec, the target is emittable.
        # A spec with an unknown semantic_kind raises -> not emittable.
        try:
            fragments = runtime_design.emit_primitive_rust(spec)
        except Exception:
            return None
        if not fragments:
            return None
        return spec

    def mechanically_draft(self, target_nid: int) -> int | None:
        """Compose the agent's OWN Rust for an emittable target via the
        mechanical emitter (runtime_design.emit_primitive_rust) — no
        teacher, no LLM. Assembles the four-home fragments into a single
        labelled, readable CodeDraft `source` and attaches it under the
        target via `has_draft`. Returns the CodeDraft node id, or None if
        the target is not emittable."""
        from . import runtime_design

        spec = self.emittable_spec_for_target(target_nid)
        if spec is None:
            return None
        fragments = runtime_design.emit_primitive_rust(spec)

        # Assemble the four-home fragments into one labelled bundle. This
        # is the agent's mechanically-composed Rust — the same fragments
        # that would be hand-placed across term.rs / jsonio.rs, gathered
        # into a single reviewable draft.
        order = [
            "term.rs (enum variant)",
            "term.rs (evaluator arm)",
            "term.rs (helper)",
            "jsonio.rs (name)",
            "jsonio.rs (parse)",
        ]
        keys = order + [k for k in fragments if k not in order]
        parts = [
            f"// Mechanically-emitted Rust for primitive {spec.get('name')!r}",
            f"// semantic_kind = {spec.get('semantic_kind')!r}; "
            f"emitter = runtime_design.emit_primitive_rust (NO LLM)",
            f"// purpose: {spec.get('purpose', '')}",
            "",
        ]
        for k in keys:
            if k not in fragments:
                continue
            parts.append(f"// ---- {k} ----")
            parts.append(fragments[k])
            parts.append("")
        source = "\n".join(parts)

        draft = self.s.add_node("CodeDraft", {
            "source": source,
            "received_at": time.time(),
            "origin": "mechanical_emitter",
            "primitive_name": spec.get("name"),
            "semantic_kind": spec.get("semantic_kind"),
            # Structured fragments carried on the draft so validate/install
            # can splice each home PRECISELY — they never re-parse the prose
            # `source` bundle. `kind` flips the validate + install gate onto
            # the multi-home-primitive path (a correctness build, not a perf
            # rewrite).
            "kind": "multi_home_primitive",
            "fragments_json": _json.dumps(fragments),
        })
        try:
            self.s.add_edge(target_nid, "has_draft", draft, {})
        except Exception:
            pass
        return draft

    # ------------------------------------------------------------------ read-method draft source
    # The read→implement path (procedural_reader + binding_resolver +
    # method_synthesis) plugged into the loop as a teacher-free draft source,
    # alongside the primitive emitter. All mechanical: read/ground/synthesise
    # are the agent's faculties; these methods only route their data through the
    # loop's draft → validate → install reflexes.

    def _read_agent(self):
        """The object the read faculties resolve their substrate off — the
        WorldAdapter when present (carries ground_unknowns), else the bare
        Substrate (offline: grounding is a no-op, binding uses the graph)."""
        return self.agent if hasattr(self.agent, "s") else self.s

    def enqueue_read_method(self, name: str, method_text: str,
                            binding: dict | None = None) -> int:
        """Mint a ReplacementTarget carrying a read-method GAP (the method
        text describing a capability the agent lacks) and make it current.
        The loop's reflexes then read → synthesise → validate → adopt. If
        `binding` is None the agent grounds it itself against its own domain
        graph (binding_resolver)."""
        root = self._ensure_root()
        attrs = {"op_name": name, "method_text": method_text,
                 "kind": "read_method_gap", "selected_at": time.time()}
        if binding is not None:
            attrs["binding_json"] = _json.dumps(binding)
        tgt = self.s.add_node("ReplacementTarget", attrs)
        try:
            self.s.add_edge(root, "current_target", tgt, {})
        except Exception:
            pass
        return tgt

    def has_read_method(self, target_nid: int) -> bool:
        return bool(self.s.node(target_nid)["attrs"].get("method_text"))

    def draft_read_method_rule(self, target_nid: int) -> int | None:
        """Read the method + ground the binding + synthesise the rule, attach a
        `read_method_rule` CodeDraft. The three agent faculties do the work;
        this only stores their output as graph data for the validate/install
        reflexes. A synthesis wall attaches a wall-carrying draft (so validate
        rejects it and the loop moves on), never a silent no-op."""
        from . import read_method_draft as rmd

        attrs = self.s.node(target_nid)["attrs"]
        method_text = attrs.get("method_text")
        if not method_text:
            return None
        name = attrs.get("op_name", "method")
        binding = None
        bj = attrs.get("binding_json")
        if bj:
            try:
                binding = _json.loads(bj)
            except Exception:
                binding = None
        draft = rmd.draft_from_reading(self._read_agent(), method_text, name,
                                       binding)
        if draft.get("wall"):
            cd = self.s.add_node("CodeDraft", {
                "kind": "read_method_rule",
                "origin": "read_method_synthesis",
                "wall": draft["wall"], "rule_json": "[]", "effect": "",
                "source": "WALL: %s" % draft["wall"],
                "received_at": time.time()})
        else:
            cd = self.s.add_node("CodeDraft", {
                "kind": "read_method_rule",
                "origin": "read_method_synthesis",
                "method_name": name, "method_text": method_text,
                "rule_json": _json.dumps(draft["rules"]),
                "effect": draft["effect"], "how": draft["how"],
                "binding_json": _json.dumps(draft["binding"]),
                "source": draft["how"], "received_at": time.time()})
        try:
            self.s.add_edge(target_nid, "has_draft", cd, {})
        except Exception:
            pass
        return cd

    def _validate_read_method_rule(self, draft_nid: int) -> dict:
        """Validate-by-running: run the synthesised rule on a minimal instance
        built from the read model, verify the described effect occurred. The
        compile_and_test analogue for a rule-draft."""
        from . import read_method_draft as rmd

        attrs = self.s.node(draft_nid)["attrs"]
        try:
            rules = _json.loads(attrs.get("rule_json") or "[]")
        except Exception:
            rules = []
        draft = {"rules": rules, "effect": attrs.get("effect"),
                 "wall": attrs.get("wall")}
        return rmd.validate_by_running(draft)

    def adopt_read_method_rule(self, draft_nid: int) -> int:
        """Install the validated rule LIVE + persist it as seed `rules` data.
        The existing adopt path for a rule-draft."""
        from . import read_method_draft as rmd

        attrs = self.s.node(draft_nid)["attrs"]
        try:
            rules = _json.loads(attrs.get("rule_json") or "[]")
        except Exception:
            rules = []
        draft = {"rules": rules, "effect": attrs.get("effect")}
        seeds_dir = os.environ.get("OZMA_READ_METHOD_SEEDS_DIR")
        res = rmd.adopt(self._read_agent(), draft,
                        seeds_dir=Path(seeds_dir) if seeds_dir else None)
        inst = self.s.add_node("CodeInstallation", {
            "op_name": attrs.get("method_name"),
            "kind": "read_method_rule",
            "rule_name": res.get("rule_name"),
            "seed_path": res.get("seed_path") or "",
            "installed_at": time.time()})
        try:
            self.s.add_edge(draft_nid, "installed_as", inst, {})
        except Exception:
            pass
        return inst

    def spawn_teacher(self, question: str) -> None:
        """Send the question to the agent's `_self_teacher`. We use
        the agent's own thread-spawning so the response is collected
        through its normal teacher-drain machinery."""
        if self.agent is None:
            return
        teacher = getattr(self.agent, "_self_teacher", None)
        if teacher is None:
            return
        tgt = self.current_target()
        if tgt is None:
            return
        # Reuse the agent's `spawn_python_thread` if available;
        # otherwise call inline (blocking). The cortex doesn't dictate
        # the threading model.
        spawn = getattr(self.agent, "spawn_python_thread", None)
        if spawn is None:
            payload = teacher(question)
            self._teacher_threads[tgt] = ("done", payload)
            return
        tid = spawn(teacher, args=(question,),
                    task=f"code_authoring:target_{tgt}")
        self._teacher_threads[tgt] = ("inflight", tid)

    def try_collect_teacher_payload(self) -> Any | None:
        """Drain a completed teacher thread for the current target,
        returning the payload. None if still running."""
        tgt = self.current_target()
        if tgt is None or tgt not in self._teacher_threads:
            return None
        kind, ref = self._teacher_threads[tgt]
        if kind == "done":
            del self._teacher_threads[tgt]
            return ref
        # In-flight — poll the agent's thread machinery.
        collect = getattr(self.agent, "collect_python_thread_result", None)
        if collect is None:
            return None
        try:
            result = collect(ref)
        except Exception:
            return None
        if result is None:
            return None
        del self._teacher_threads[tgt]
        return result

    def attach_draft(self, payload: Any) -> int:
        tgt = self.current_target()
        if tgt is None:
            raise RuntimeError("attach_draft with no current target")
        if isinstance(payload, dict):
            source = payload.get("answer") or payload.get("source") or ""
        else:
            source = str(payload)
        draft = self.s.add_node("CodeDraft", {
            "source": source,
            "received_at": time.time(),
        })
        try:
            self.s.add_edge(tgt, "has_draft", draft, {})
        except Exception:
            pass
        return draft

    def draft_validation(self, draft_nid: int) -> dict | None:
        out = self.s.neighbours(draft_nid, "validated_by")
        if not out:
            return None
        return dict(self.s.node(out[0])["attrs"])

    def compile_and_test(self, draft_nid: int) -> dict:
        """Build + bench the draft against the original. For targets
        with a registered `bench` spec, both the baseline (existing
        source) and the candidate (draft) are compiled as cdylibs,
        loaded via ctypes, and run for the spec's iterations × inputs.
        The reported `perf_improvement_factor` is real: baseline_time
        divided by candidate_time.

        For targets WITHOUT a bench spec (the agent's own complex
        runners that don't yet have a calibrated benchmark surface),
        we compile-check only and return factor=1.0 (no install)."""
        result = {
            "compile_ok": False,
            "tests_pass": False,
            "perf_improvement_factor": 0.0,
            "notes": "",
        }
        attrs = self.s.node(draft_nid)["attrs"]

        # Multi-home primitive: the draft is FOUR-HOME Rust fragments, not
        # a buildable lib.rs. Splice into an isolated copy of the real
        # crate and `cargo check` it. Routed here off the draft's `kind`.
        if attrs.get("kind") == "multi_home_primitive":
            return self._validate_multi_home_primitive(draft_nid)

        # Read-method rule-draft: validate by RUNNING the synthesised rule and
        # checking the described effect (not a cargo build). Routed off `kind`.
        if attrs.get("kind") == "read_method_rule":
            return self._validate_read_method_rule(draft_nid)

        source = attrs.get("source", "")
        if not source.strip():
            result["notes"] = "empty source"
            return result
        if not ("fn " in source and "->" in source):
            result["notes"] = "non-rust drafts not yet handled"
            return result

        tgt = self.current_target()
        op_name = self.s.node(tgt)["attrs"].get("op_name") if tgt else None
        entry = self._target_registry_entry(op_name) if op_name else None
        bench = entry.get("bench") if entry else None

        # Compile-check the candidate first.
        cand_so = self._compile_rust_cdylib(source, label="candidate")
        if isinstance(cand_so, dict):
            result["notes"] = cand_so["error"]
            return result
        result["compile_ok"] = True

        if bench is None:
            # No calibrated benchmark surface for this target. Compile
            # succeeded, but we have no way to measure speedup, so we
            # decline to install. The cortex's reasoning is honest:
            # we don't ship what we can't prove faster.
            result["tests_pass"] = True
            result["perf_improvement_factor"] = 1.0
            result["notes"] = (
                f"compiled OK; no benchmark surface registered for "
                f"{op_name!r}, cannot prove speedup so refusing install"
            )
            return result

        # Compile the BASELINE (existing source).
        baseline_src = entry["path"].read_text() if entry["path"].exists() else None
        if baseline_src is None:
            result["notes"] = "baseline source unreadable; can't compare"
            return result
        base_so = self._compile_rust_cdylib(baseline_src, label="baseline")
        if isinstance(base_so, dict):
            result["notes"] = f"baseline didn't compile: {base_so['error']}"
            return result

        # Sanity check: the two implementations must agree on outputs.
        # If they don't, the candidate isn't functionally equivalent —
        # silently faster wrong answers are the worst possible regression.
        agree, disagree_note = self._functional_equivalence(
            base_so, cand_so, bench)
        if not agree:
            result["notes"] = f"functional mismatch: {disagree_note}"
            return result
        result["tests_pass"] = True

        # Real benchmark.
        baseline_time, candidate_time = self._benchmark_pair(
            base_so, cand_so, bench)
        factor = baseline_time / candidate_time if candidate_time > 0 else 0.0
        result["perf_improvement_factor"] = factor
        result["notes"] = (
            f"baseline={baseline_time*1000:.1f}ms  "
            f"candidate={candidate_time*1000:.1f}ms  "
            f"factor={factor:.2f}x  "
            f"({bench['iterations']:,} iters × {len(bench['inputs'])} inputs)"
        )
        return result

    def _compile_rust_cdylib(self, source: str, *, label: str):
        """Compile `source` as a cdylib in a temp crate. Returns the
        path to the .so on success, or a dict {"error": str} on failure."""
        tmp = Path(tempfile.mkdtemp(prefix=f"cw_{label}_"))
        (tmp / "src").mkdir()
        (tmp / "src" / "lib.rs").write_text(source)
        (tmp / "Cargo.toml").write_text(
            f'[package]\nname = "cw_{label}"\nversion = "0.0.1"\n'
            f'edition = "2021"\n\n[lib]\n'
            f'crate-type = ["cdylib"]\n'
            f'\n[profile.release]\nopt-level = 3\nlto = "thin"\n'
            f'codegen-units = 1\n')
        proc = subprocess.run(
            ["cargo", "build", "--release"],
            cwd=tmp, capture_output=True, text=True, timeout=180,
        )
        if proc.returncode != 0:
            return {"error": f"cargo build [{label}] failed:\n"
                             f"{proc.stderr[-2000:]}"}
        # Locate the .so.
        target_dir = tmp / "target" / "release"
        for ext in (".so", ".dylib", ".dll"):
            for f in target_dir.iterdir():
                if f.name.startswith("libcw_") and f.name.endswith(ext):
                    # Keep the temp dir alive by stashing it on the
                    # path's parent. (Returned path stays valid for
                    # the life of this method's caller.)
                    self._compile_artifacts.append(tmp)
                    return f
        return {"error": f"could not locate built cdylib in {target_dir}"}

    def _load_op(self, so_path: Path, bench: dict):
        """Bind the exported function via ctypes. Returns a callable
        with the spec's signature."""
        import ctypes
        lib = ctypes.CDLL(str(so_path))
        fn = getattr(lib, bench["fn_name"])
        # Parse signature: 'extern "C" fn name(args) -> ret'. Phase-1
        # supports `i64 → i64`. Extend per signature as needed.
        sig = bench["signature"]
        if "i64) -> i64" in sig:
            fn.argtypes = [ctypes.c_int64]
            fn.restype = ctypes.c_int64
        elif "i32) -> i32" in sig:
            fn.argtypes = [ctypes.c_int32]
            fn.restype = ctypes.c_int32
        else:
            raise RuntimeError(f"unsupported bench signature: {sig!r}")
        fn._owning_lib = lib
        return fn

    def _functional_equivalence(self, baseline_so, candidate_so,
                                 bench: dict) -> tuple[bool, str]:
        """Run both impls on every input; refuse if any output differs.
        A faster but-wrong rewrite is the worst possible install."""
        try:
            base_fn = self._load_op(baseline_so, bench)
            cand_fn = self._load_op(candidate_so, bench)
        except Exception as e:
            return False, f"load failed: {e}"
        for x in bench["inputs"]:
            b = base_fn(x)
            c = cand_fn(x)
            if b != c:
                return False, (
                    f"input={x}: baseline={b}, candidate={c} (differ)")
        return True, ""

    def _benchmark_pair(self, baseline_so, candidate_so,
                        bench: dict) -> tuple[float, float]:
        """Time both implementations. Returns (baseline_time_s,
        candidate_time_s) for `iterations * len(inputs)` calls each."""
        import time
        base_fn = self._load_op(baseline_so, bench)
        cand_fn = self._load_op(candidate_so, bench)
        inputs = bench["inputs"]
        iters = bench["iterations"]
        # Warm-up
        for x in inputs[:5]:
            base_fn(x); cand_fn(x)
        # Baseline.
        t0 = time.perf_counter()
        for _ in range(iters):
            for x in inputs:
                base_fn(x)
        baseline_time = time.perf_counter() - t0
        # Candidate.
        t0 = time.perf_counter()
        for _ in range(iters):
            for x in inputs:
                cand_fn(x)
        candidate_time = time.perf_counter() - t0
        return baseline_time, candidate_time

    def attach_validation(self, draft_nid: int, val: dict) -> int:
        v = self.s.add_node("ValidationResult", {
            "compile_ok": bool(val.get("compile_ok")),
            "tests_pass": bool(val.get("tests_pass")),
            "perf_improvement_factor": float(
                val.get("perf_improvement_factor", 0.0)),
            "notes": val.get("notes", ""),
            "measured_at": time.time(),
        })
        try:
            self.s.add_edge(draft_nid, "validated_by", v, {})
        except Exception:
            pass
        return v

    # ------------------------------------------------------- multi-home primitive

    # The anchor map: each structured fragment key → how to splice it into
    # its home file. Two splice modes:
    #   "before"  — insert the fragment on its own line BEFORE the anchor.
    #   "after"   — insert the fragment on its own line AFTER the anchor.
    #   "join"    — append `| <fragment>` onto the line containing the
    #               anchor (for the exhaustive `items`-group `|` patterns).
    # Anchors are stable structural tokens, not whitespace-sensitive.
    _SPLICE_PLAN = {
        "term.rs (enum variant)":
            ("term.rs", "before", "ENUM_CLOSE"),
        "term.rs (evaluator arm)":
            ("term.rs", "after",
             "TermNode::Max { items } => numeric_minmax(arena, items, env, ctx, false),"),
        "term.rs (helper)":
            ("term.rs", "before", "fn numeric_minmax("),
        "term.rs (copy_subtree arm)":
            ("term.rs", "after",
             "TermNode::ArgMax { items } =>\n"
             "            TermNode::ArgMax { items: items.iter()"
             ".map(|i| copy_subtree(src, dst, *i)).collect() },"),
        "term.rs (child-index group)":
            ("term.rs", "join",
             "| TermNode::Min { items } | TermNode::Max { items } "
             "| TermNode::ArgMax { items }"),
        "jsonio.rs (name)":
            ("jsonio.rs", "after",
             'TermNode::NodesWhere { .. } => "NodesWhere",'),
        "jsonio.rs (parse)":
            ("jsonio.rs", "before",
             "other => return Err(JsonError::UnknownTermType"),
        "jsonio.rs (term_to_json group)":
            ("jsonio.rs", "join",
             "| TermNode::Min { items } | TermNode::Max { items } "
             "| TermNode::ArgMax { items }"),
        "reflect.rs (describe arm)":
            ("reflect.rs", "before",
             "TermNode::NodesWhere { node_type, attr_key, value } => "),
    }

    @staticmethod
    def _splice_fragment(text: str, mode: str, anchor: str,
                         fragment: str, *, fname: str) -> str:
        """Mechanically insert `fragment` into `text` at `anchor` per
        `mode`. Raises if the anchor is absent or ambiguous — a missing
        anchor is a hard fail, never a silent skip."""
        if anchor == "ENUM_CLOSE":
            i = text.find("pub enum TermNode {")
            if i < 0:
                raise RuntimeError(f"{fname}: enum TermNode not found")
            j = text.find("\n}", i)
            if j < 0:
                raise RuntimeError(f"{fname}: enum close not found")
            return text[:j] + "\n" + fragment + text[j:]

        n = text.count(anchor)
        if n == 0:
            raise RuntimeError(f"{fname}: anchor not found: {anchor[:60]!r}")
        if n > 1:
            raise RuntimeError(
                f"{fname}: anchor ambiguous ({n}×): {anchor[:60]!r}")
        if mode == "join":
            return text.replace(anchor, anchor + " " + fragment, 1)
        idx = text.find(anchor)
        if mode == "before":
            line_start = text.rfind("\n", 0, idx) + 1
            return text[:line_start] + fragment + "\n" + text[line_start:]
        if mode == "after":
            # anchor may span lines; advance to the end of the matched span,
            # then to the end of that physical line.
            end = idx + len(anchor)
            line_end = text.find("\n", end)
            if line_end < 0:
                line_end = len(text)
            return text[:line_end] + "\n" + fragment + text[line_end:]
        raise RuntimeError(f"unknown splice mode {mode!r}")

    def _splice_all_fragments(self, src_dir: Path, fragments: dict) -> list:
        """Splice every structured fragment into its home file under
        `src_dir`. Returns the list of (filename, key) spliced. Mutates
        the files in `src_dir` in place — `src_dir` MUST be an isolated
        copy, never the live tree."""
        # Group fragments by file so each file is read/written once.
        by_file: dict[str, list] = {}
        for key, fragment in fragments.items():
            plan = self._SPLICE_PLAN.get(key)
            if plan is None:
                # Unknown fragment key (e.g. a future home) — skip rather
                # than guess an anchor. The known 9 cover the reduction
                # primitive completely.
                continue
            fname, mode, anchor = plan
            by_file.setdefault(fname, []).append((key, mode, anchor, fragment))

        spliced = []
        for fname, items in by_file.items():
            path = src_dir / fname
            text = path.read_text()
            for key, mode, anchor, fragment in items:
                text = self._splice_fragment(
                    text, mode, anchor, fragment, fname=fname)
                spliced.append((fname, key))
            path.write_text(text)
        return spliced

    def _isolated_crate_copy(self) -> Path:
        """Copy the live `runners/dsl` crate (source + manifests only,
        NOT the 3.8 GB target dir) into a fresh tempdir. The copy is the
        ONLY thing the validator/installer-demo ever mutates."""
        import shutil
        live = self.repo_root / "runners" / "dsl"
        tmp = Path(tempfile.mkdtemp(prefix="cw_multihome_"))
        (tmp / "src").mkdir()
        # Copy the whole src tree.
        shutil.copytree(live / "src", tmp / "src", dirs_exist_ok=True)
        for f in ("Cargo.toml", "Cargo.lock", "pyproject.toml"):
            if (live / f).exists():
                shutil.copy2(live / f, tmp / f)
        if (live / "python").exists():
            shutil.copytree(live / "python", tmp / "python",
                            dirs_exist_ok=True)
        self._compile_artifacts.append(tmp)
        return tmp

    def _cargo_check(self, crate_dir: Path) -> dict:
        """`cargo check --lib` the crate at `crate_dir` with an ISOLATED
        target dir, ulimit, and timeout. Returns {ok, errors, notes}.
        Reuses the host cargo registry/dep cache, so only the crate's own
        source recompiles (seconds, not minutes)."""
        env = dict(os.environ)
        env["CARGO_TARGET_DIR"] = str(crate_dir / "target")
        # `cargo check` typechecks without codegen — far lighter than a
        # release build (the box OOMs on `--release`).
        cmd = ("ulimit -v 12000000; "
               "exec cargo check --lib --message-format=short 2>&1")
        try:
            proc = subprocess.run(
                ["bash", "-c", cmd],
                cwd=crate_dir, capture_output=True, text=True,
                env=env, timeout=540,
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "errors": ["cargo check timed out (540s)"],
                    "notes": "sandbox build blocked: timeout"}
        out = proc.stdout or ""
        errors = [ln for ln in out.splitlines()
                  if ln.startswith("error") or ": error" in ln]
        ok = proc.returncode == 0
        return {
            "ok": ok,
            "errors": errors[:40],
            "notes": ("cargo check passed" if ok
                      else f"cargo check failed ({len(errors)} errors)"),
        }

    def _validate_multi_home_primitive(self, draft_nid: int) -> dict:
        """Splice the draft's structured fragments into an ISOLATED copy
        of the real crate and `cargo check` it. For a CORRECTNESS
        primitive there is no faster/slower bench, so tests_pass mirrors
        compile_ok and perf_improvement_factor is fixed at 1.0; the
        install gate keys off `kind`, not perf."""
        result = {
            "compile_ok": False,
            "tests_pass": False,
            "perf_improvement_factor": 1.0,
            "notes": "",
            "kind": "multi_home_primitive",
        }
        attrs = self.s.node(draft_nid)["attrs"]
        raw = attrs.get("fragments_json")
        if not raw:
            result["notes"] = "no structured fragments on draft"
            return result
        try:
            fragments = _json.loads(raw)
        except Exception as e:
            result["notes"] = f"fragments_json unreadable: {e}"
            return result

        crate = self._isolated_crate_copy()
        try:
            spliced = self._splice_all_fragments(crate / "src", fragments)
        except Exception as e:
            result["notes"] = f"splice failed: {e}"
            return result

        check = self._cargo_check(crate)
        result["compile_ok"] = bool(check["ok"])
        result["tests_pass"] = bool(check["ok"])
        primitive = attrs.get("primitive_name", "?")
        if check["ok"]:
            result["notes"] = (
                f"multi-home primitive {primitive!r}: spliced "
                f"{len(spliced)} fragments into isolated crate copy; "
                f"cargo check PASSED")
        else:
            errs = "; ".join(check["errors"][:5])
            result["notes"] = (
                f"multi-home primitive {primitive!r}: spliced "
                f"{len(spliced)} fragments; cargo check FAILED: {errs}"
                if check["errors"] else
                f"multi-home primitive {primitive!r}: {check['notes']}")
        return result

    def install_multi_home_primitive(self, draft_nid: int, *,
                                     target_src_dir: Path | None = None
                                     ) -> int:
        """Splice the draft's structured fragments into the REAL home
        files (term.rs / jsonio.rs / reflect.rs) under `target_src_dir`
        (defaults to the live `runners/dsl/src`), each with a per-file
        backup `<name>.pre_cw_<ts>.rs`. Gated by the caller on a prior
        successful validate (compile_ok + tests_pass).

        `target_src_dir` exists so the DEMO can point the installer at an
        ISOLATED COPY — the live tree is never touched in the demo."""
        attrs = self.s.node(draft_nid)["attrs"]
        if attrs.get("kind") != "multi_home_primitive":
            raise RuntimeError(
                "install_multi_home_primitive on a non-primitive draft")
        raw = attrs.get("fragments_json")
        if not raw:
            raise RuntimeError("no structured fragments on draft")
        fragments = _json.loads(raw)

        src_dir = (Path(target_src_dir) if target_src_dir is not None
                   else self.repo_root / "runners" / "dsl" / "src")
        ts = int(time.time())
        # Determine which files we'll touch and back them up FIRST.
        touched = set()
        for key in fragments:
            plan = self._SPLICE_PLAN.get(key)
            if plan is not None:
                touched.add(plan[0])
        backups = {}
        for fname in sorted(touched):
            p = src_dir / fname
            bak = p.with_suffix(p.suffix + f".pre_cw_{ts}")
            bak.write_text(p.read_text())
            backups[fname] = str(bak)

        spliced = self._splice_all_fragments(src_dir, fragments)

        inst = self.s.add_node("CodeInstallation", {
            "op_name": attrs.get("primitive_name"),
            "kind": "multi_home_primitive",
            "src_dir": str(src_dir),
            "files": sorted(touched),
            "backups": _json.dumps(backups),
            "n_fragments": len(spliced),
            "installed_at": time.time(),
        })
        try:
            self.s.add_edge(draft_nid, "installed_as", inst, {})
        except Exception:
            pass
        return inst

    def rollback_install(self, install_nid: int) -> list[str]:
        """Restore the live home files from a CodeInstallation's per-file
        backups (the `.pre_cw_<ts>` written by install_multi_home_primitive).
        The safety net: any failure after a live install (build error, failed
        verification) reverts the tree byte-for-byte. Returns restored files."""
        attrs = self.s.node(install_nid)["attrs"]
        backups = _json.loads(attrs.get("backups", "{}"))
        src_dir = Path(attrs.get("src_dir", ""))
        restored = []
        for fname, bak in backups.items():
            bp = Path(bak)
            if bp.exists():
                (src_dir / fname).write_text(bp.read_text())
                restored.append(fname)
        return restored

    def activate_installed_primitive(self, install_nid: int, *,
                                     timeout_s: int = 600) -> dict:
        """LIVE ACTIVATION — rebuild the Rust extension so an INSTALLED primitive
        becomes callable in Python. The heavy, DELIBERATE final step (not a
        reflex): it runs `maturin develop` in the live crate and syncs the built
        `_native.abi3.so` into the loaded package, so a new process can call the
        primitive. Rebuilds the shared wheel, so the caller invokes it
        intentionally. On a build failure the caller rolls back via
        rollback_install. Returns {built, stderr_tail, so_synced}.

        World-adapter I/O: shells out to the build tool + copies the artifact;
        no agent decision here."""
        import os
        import shutil
        import subprocess
        crate = self.repo_root / "runners" / "dsl"
        env = dict(os.environ, CARGO_BUILD_JOBS="4")
        try:
            proc = subprocess.run(
                ["maturin", "develop"], cwd=str(crate), env=env,
                capture_output=True, text=True, timeout=timeout_s)
        except subprocess.TimeoutExpired:
            return {"built": False, "stderr_tail": "maturin develop timed out",
                    "so_synced": False}
        except FileNotFoundError:
            return {"built": False, "stderr_tail": "maturin not found",
                    "so_synced": False}
        if proc.returncode != 0:
            return {"built": False,
                    "stderr_tail": (proc.stderr or "")[-2000:],
                    "so_synced": False}
        # Sync the freshly built .so into the loaded package (maturin develop
        # installs into the active env; mirror it to the source-tree copy too
        # so any loader path sees the new primitive).
        synced = False
        built_so = crate / "python" / "substrate_rs" / "_native.abi3.so"
        try:
            import substrate_rs
            tgt = Path(substrate_rs.__file__).parent / "_native.abi3.so"
            if built_so.exists() and built_so.resolve() != tgt.resolve():
                shutil.copy2(built_so, tgt)
            synced = True
        except Exception:
            synced = False
        return {"built": True, "stderr_tail": (proc.stderr or "")[-600:],
                "so_synced": synced}

    def install_draft(self, draft_nid: int) -> int:
        """Replace the original source on disk with the draft. The
        cortex records the installation as a graph node so the agent
        can later report on its self-improvements."""
        # Multi-home primitive drafts splice into several home files, not
        # a single registry path — dispatch on the draft's kind.
        if self.s.node(draft_nid)["attrs"].get("kind") == \
                "multi_home_primitive":
            inst = self.install_multi_home_primitive(draft_nid)
            self.discard_target_and_draft(reason="installed")
            return inst
        # Read-method rule-draft: adopt = install the rule live + persist it as
        # seed `rules` data. Routed off `kind`.
        if self.s.node(draft_nid)["attrs"].get("kind") == "read_method_rule":
            inst = self.adopt_read_method_rule(draft_nid)
            self.discard_target_and_draft(reason="adopted")
            return inst
        tgt = self.current_target()
        attrs = self.s.node(tgt)["attrs"]
        op_name = attrs.get("op_name")
        registry = {
            "evaluate_term": self.repo_root /
                "runners" / "dsl" / "src" / "term.rs",
            "recognise_frame": self.repo_root /
                "runners" / "rust" / "src" / "lib.rs",
        }
        path = registry.get(op_name)
        if path is None:
            raise RuntimeError(
                f"don't know where to install {op_name!r} — extend registry")
        # Back up the original next to it.
        backup = path.with_suffix(path.suffix + f".pre_cw_{int(time.time())}")
        backup.write_text(path.read_text())
        path.write_text(
            self.s.node(draft_nid)["attrs"].get("source", ""))
        inst = self.s.add_node("CodeInstallation", {
            "op_name": op_name,
            "path": str(path),
            "backup_path": str(backup),
            "installed_at": time.time(),
        })
        try:
            self.s.add_edge(draft_nid, "installed_as", inst, {})
        except Exception:
            pass
        # Clear the target so the next tick picks the next-most-
        # expensive op.
        self.discard_target_and_draft(reason="installed")
        return inst

    def discard_target_and_draft(self, reason: str = "") -> None:
        """Clear the current target's `current_target` edge so the
        cortex moves on. Used after install OR after a validation
        failure / no-speedup outcome."""
        root = self._ensure_root()
        for tgt in list(self.s.neighbours(root, "current_target")):
            try:
                self.s.remove_edge(root, "current_target", tgt)
            except Exception:
                pass
            self._teacher_threads.pop(tgt, None)


__all__ = ["CodeWritingCortex"]

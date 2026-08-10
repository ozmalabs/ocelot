"""machine_learning Mt + 8 decomposition packs."""
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


def test_ml_installs_with_genlmt():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "machine_learning")
    assert mt is not None
    assert s.node(mt)["attrs"]["name"] == "machine_learning"
    parents = {s.node(p)["attrs"]["name"]
               for p in s.neighbours(mt, "genlMt")}
    assert "compiler_theory" in parents


def test_ml_carries_paradigms_and_loss():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "machine_learning")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("supervised_learning", "unsupervised_learning",
                     "self_supervised_learning", "reinforcement_learning",
                     "loss_function", "mean_squared_error",
                     "cross_entropy_loss", "kl_divergence",
                     "contrastive_loss"):
        assert required in names


def test_ml_carries_optimization():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "machine_learning")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("gradient_descent", "stochastic_gradient_descent",
                     "momentum", "Adam_optimizer", "AdamW",
                     "learning_rate", "learning_rate_schedule",
                     "backpropagation", "automatic_differentiation"):
        assert required in names


def test_ml_carries_regularization():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "machine_learning")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("regularization", "dropout", "batch_normalization",
                     "layer_normalization", "weight_decay",
                     "early_stopping", "data_augmentation"):
        assert required in names


def test_ml_carries_architecture():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "machine_learning")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("multilayer_perceptron",
                     "convolutional_neural_network",
                     "recurrent_neural_network", "LSTM",
                     "Transformer_architecture", "self_attention",
                     "multi_head_attention", "positional_encoding",
                     "token_embedding",
                     "feed_forward_network_transformer",
                     "residual_connection", "tokenization",
                     "byte_pair_encoding"):
        assert required in names


def test_ml_carries_training_pipeline():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "machine_learning")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("dataset_split", "mini_batch_training",
                     "gradient_accumulation", "distributed_training",
                     "checkpoint", "hyperparameter_search"):
        assert required in names


def test_ml_carries_transfer_learning():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "machine_learning")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("pretraining", "fine_tuning", "LoRA",
                     "instruction_tuning", "RLHF", "PPO", "DPO",
                     "constitutional_AI"):
        assert required in names


def test_ml_carries_inference_optimization():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "machine_learning")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("quantization_ML", "knowledge_distillation",
                     "KV_cache", "flash_attention", "batched_inference",
                     "speculative_decoding"):
        assert required in names


def test_ml_carries_failure_modes():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "machine_learning")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("hallucination_LLM", "adversarial_examples",
                     "catastrophic_forgetting", "distribution_shift",
                     "overfitting", "underfitting", "double_descent",
                     "lottery_ticket_hypothesis"):
        assert required in names


def test_ml_carries_paradigm_critique():
    """The substrate's grounded critique of the training paradigm."""
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "machine_learning")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("GPU_training_compute", "weight_space_is_opaque",
                     "statistical_fit_is_not_understanding",
                     "loss_minimisation_isnt_capability_optimisation",
                     "training_is_local_search",
                     "training_paradigm_brute_force",
                     "Tracr_alternative_authored_nets",
                     "neurosymbolic_AI", "knowledge_representation",
                     "compiled_networks"):
        assert required in names


def test_ml_rules_carry_soundness_category():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "machine_learning")
    valid = {"denotational_equivalence", "algebraic_law",
             "extensional_equivalence", "cost_equivalence",
             "referential_transparency"}
    n_with_cat = 0
    for r in s.neighbours(mt, "has_rule"):
        if s.node(r)["attrs"].get("soundness_category") in valid:
            n_with_cat += 1
    assert n_with_cat >= 18


def test_ml_decomposition_packs_load():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    load_one_seed(s, "machine_learning")
    ids = install_all_concept_expansions(s)
    for required in ("backprop_autograd_decomposition",
                     "transformer_architecture_decomposition",
                     "attention_mechanism_decomposition",
                     "fine_tuning_lora_decomposition",
                     "rlhf_alignment_decomposition",
                     "llm_inference_decomposition",
                     "ml_failure_modes_decomposition",
                     "authored_vs_trained_decomposition"):
        assert required in ids, f"ML pack {required!r} not loaded"


def test_ml_pack_sub_mechanisms_mount():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = load_one_seed(s, "machine_learning")
    install_all_concept_expansions(s)
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    # Backprop
    for n in ("computational_graph", "chain_rule_application",
              "forward_pass", "backward_pass",
              "reverse_mode_autodiff", "forward_mode_autodiff",
              "dynamic_graph_pytorch", "static_graph_jax",
              "gradient_accumulation", "gradient_checkpointing",
              "mixed_precision_training", "VJP_JVP"):
        assert n in names
    # Transformer
    for n in ("transformer_block", "encoder_only_BERT",
              "decoder_only_GPT", "encoder_decoder",
              "causal_attention_mask", "pre_norm_vs_post_norm",
              "RMSNorm", "SwiGLU_activation",
              "rotary_position_embedding",
              "grouped_query_attention", "mixture_of_experts",
              "sliding_window_attention"):
        assert n in names
    # Attention
    for n in ("query_key_value_projection", "scaled_dot_product",
              "attention_softmax", "attention_output",
              "multi_head_split", "attention_quadratic_complexity",
              "flash_attention_tiling", "online_softmax",
              "sparse_attention", "linear_attention", "ring_attention"):
        assert n in names
    # Fine-tuning
    for n in ("full_fine_tuning", "LoRA_decomposition",
              "LoRA_rank_parameter", "LoRA_alpha_scaling",
              "LoRA_target_modules", "LoRA_merging", "QLoRA",
              "adapter_modules", "prefix_tuning",
              "catastrophic_forgetting_in_fine_tune",
              "instruction_tuning_pipeline"):
        assert n in names
    # RLHF
    for n in ("preference_data_collection",
              "reward_model_training", "PPO_for_RLHF",
              "KL_penalty_to_base", "DPO_direct_preference",
              "RLAIF", "sycophancy", "reward_hacking",
              "jailbreak_robustness", "alignment_tax"):
        assert n in names
    # LLM inference
    for n in ("prefill_phase", "decode_phase",
              "KV_cache_memory_size", "paged_attention",
              "prefix_caching", "continuous_batching",
              "speculative_decoding", "tensor_parallelism",
              "pipeline_parallelism", "weight_quantization_inference",
              "chunked_prefill", "streaming_token_output"):
        assert n in names
    # Failure modes
    for n in ("hallucination_pattern_matching", "RAG_grounding",
              "adversarial_perturbation_vision",
              "jailbreak_prompt_engineering",
              "distribution_shift_calibration",
              "calibration_breakdown",
              "catastrophic_forgetting_continual",
              "mode_collapse_GAN", "dataset_contamination",
              "spurious_correlations", "data_leakage_in_training",
              "benchmark_overfitting"):
        assert n in names
    # Authored vs trained (the substrate's preferred paradigm)
    for n in ("Tracr_RASP_compilation", "RASP_primitives",
              "CPWL_constructive_relu", "ELM_extreme_learning_machine",
              "neurosymbolic_AlphaGeometry",
              "symbolic_knowledge_representation",
              "deductive_inference", "provable_correctness",
              "interpretable_by_construction",
              "no_training_data_required",
              "compositional_correctness",
              "the_substrate_uses_authored_primarily"):
        assert n in names


def test_total_ml_concept_count():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = load_one_seed(s, "machine_learning")
    install_all_concept_expansions(s)
    n_concepts = len(s.neighbours(mt, "has_concept"))
    n_rules = len(s.neighbours(mt, "has_rule"))
    assert n_concepts >= 170, f"only {n_concepts} concepts"
    assert n_rules >= 55, f"only {n_rules} rules"

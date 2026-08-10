"""security_and_cryptography Mt + 8 decomposition packs."""
from __future__ import annotations

import pytest
from substrate_rs import _native
from substrate.boot_all import load_one_seed


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


def test_sec_installs_with_genlmt():
    s = _fresh_substrate()
    mt = load_one_seed(s, "security_and_cryptography")
    assert mt is not None
    assert s.node(mt)["attrs"]["name"] == "security_and_cryptography"
    parents = {s.node(p)["attrs"]["name"]
               for p in s.neighbours(mt, "genlMt")}
    assert "compiler_theory" in parents


def test_sec_carries_foundations():
    s = _fresh_substrate()
    mt = load_one_seed(s, "security_and_cryptography")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("CIA_triad", "threat_model", "STRIDE",
                     "defense_in_depth", "principle_of_least_privilege",
                     "zero_trust", "secure_by_default"):
        assert required in names


def test_sec_carries_symmetric_crypto():
    s = _fresh_substrate()
    mt = load_one_seed(s, "security_and_cryptography")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("symmetric_encryption", "AES_block_cipher",
                     "AES_GCM", "AES_CBC", "AES_CTR", "AES_ECB",
                     "ChaCha20_Poly1305"):
        assert required in names


def test_sec_carries_asymmetric_crypto():
    s = _fresh_substrate()
    mt = load_one_seed(s, "security_and_cryptography")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("asymmetric_encryption", "RSA",
                     "elliptic_curve_cryptography", "Curve25519",
                     "Ed25519", "ECDH", "Diffie_Hellman_key_exchange",
                     "forward_secrecy"):
        assert required in names


def test_sec_carries_hash_kdf():
    s = _fresh_substrate()
    mt = load_one_seed(s, "security_and_cryptography")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("hash_function", "SHA_2", "SHA_3",
                     "BLAKE2_BLAKE3", "MD5_SHA1", "HMAC", "HKDF",
                     "Argon2", "bcrypt", "scrypt", "PBKDF2"):
        assert required in names


def test_sec_carries_authentication():
    s = _fresh_substrate()
    mt = load_one_seed(s, "security_and_cryptography")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("password_authentication",
                     "multi_factor_authentication", "TOTP",
                     "WebAuthn", "FIDO2", "passkeys"):
        assert required in names


def test_sec_carries_authorization():
    s = _fresh_substrate()
    mt = load_one_seed(s, "security_and_cryptography")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("RBAC", "ABAC", "ReBAC", "OAuth_scopes",
                     "capabilities_security"):
        assert required in names


def test_sec_carries_attacks():
    s = _fresh_substrate()
    mt = load_one_seed(s, "security_and_cryptography")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("SQL_injection", "XSS_cross_site_scripting",
                     "CSRF_cross_site_request_forgery", "SSRF",
                     "command_injection", "race_condition_TOCTOU",
                     "padding_oracle_attack", "timing_side_channel",
                     "MITM_attack", "replay_attack", "phishing",
                     "supply_chain_attack"):
        assert required in names


def test_sec_carries_memory_safety():
    s = _fresh_substrate()
    mt = load_one_seed(s, "security_and_cryptography")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("buffer_overflow", "use_after_free",
                     "heap_spraying", "stack_canary", "ASLR",
                     "DEP_NX_bit", "control_flow_integrity",
                     "memory_safe_languages"):
        assert required in names


def test_sec_carries_modern_crypto():
    s = _fresh_substrate()
    mt = load_one_seed(s, "security_and_cryptography")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("zero_knowledge_proof", "zk_SNARK", "zk_STARK",
                     "homomorphic_encryption",
                     "secure_multiparty_computation",
                     "threshold_cryptography", "differential_privacy"):
        assert required in names


def test_sec_carries_post_quantum():
    s = _fresh_substrate()
    mt = load_one_seed(s, "security_and_cryptography")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("quantum_threat", "Kyber_post_quantum_KEM",
                     "Dilithium_post_quantum_signature",
                     "SPHINCS_hash_signature",
                     "harvest_now_decrypt_later"):
        assert required in names


def test_sec_carries_supply_chain():
    s = _fresh_substrate()
    mt = load_one_seed(s, "security_and_cryptography")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("SBOM", "Sigstore_cosign",
                     "SLSA_supply_chain_levels",
                     "reproducible_builds"):
        assert required in names


def test_sec_rules_carry_soundness_category():
    s = _fresh_substrate()
    mt = load_one_seed(s, "security_and_cryptography")
    valid = {"denotational_equivalence", "algebraic_law",
             "extensional_equivalence", "cost_equivalence",
             "referential_transparency"}
    n_with_cat = 0
    for r in s.neighbours(mt, "has_rule"):
        if s.node(r)["attrs"].get("soundness_category") in valid:
            n_with_cat += 1
    assert n_with_cat >= 18


def test_sec_decomposition_packs_load():
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    load_one_seed(s, "security_and_cryptography")
    ids = install_all_concept_expansions(s)
    for required in ("aes_block_modes_decomposition",
                     "ecc_curves_decomposition",
                     "web_attacks_decomposition",
                     "memory_safety_exploits_decomposition",
                     "oauth_oidc_jwt_decomposition",
                     "post_quantum_crypto_decomposition",
                     "zero_knowledge_decomposition",
                     "supply_chain_security_decomposition",
                     "password_kdf_decomposition",
                     "confidential_computing_decomposition"):
        assert required in ids, f"sec pack {required!r} not loaded"


def test_total_sec_concept_count():
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = load_one_seed(s, "security_and_cryptography")
    install_all_concept_expansions(s)
    n_concepts = len(s.neighbours(mt, "has_concept"))
    n_rules = len(s.neighbours(mt, "has_rule"))
    assert n_concepts >= 215, f"only {n_concepts} concepts"
    assert n_rules >= 60, f"only {n_rules} rules"

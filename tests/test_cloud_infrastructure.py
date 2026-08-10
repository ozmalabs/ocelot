"""cloud_infrastructure Mt + 9 decomposition packs."""
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


def test_cloud_installs_with_genlmt():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "cloud_infrastructure")
    assert mt is not None
    assert s.node(mt)["attrs"]["name"] == "cloud_infrastructure"
    parents = {s.node(p)["attrs"]["name"]
               for p in s.neighbours(mt, "genlMt")}
    assert "compiler_theory" in parents


def test_cloud_carries_kubernetes():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "cloud_infrastructure")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("kubernetes_pod", "kubernetes_deployment",
                     "kubernetes_statefulset", "kubernetes_daemonset",
                     "kubernetes_job_cronjob", "kubernetes_service",
                     "kubernetes_ingress", "kubernetes_gateway_API",
                     "kubernetes_configmap", "kubernetes_secret",
                     "kubernetes_RBAC", "kubernetes_namespace",
                     "kubernetes_NetworkPolicy", "kubernetes_CRD",
                     "kubernetes_operator", "controller_pattern",
                     "kubernetes_HPA", "kubernetes_VPA",
                     "kubernetes_cluster_autoscaler", "Helm",
                     "Kustomize"):
        assert required in names


def test_cloud_carries_gitops():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "cloud_infrastructure")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("ArgoCD", "Flux", "GitOps_principles"):
        assert required in names


def test_cloud_carries_iac():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "cloud_infrastructure")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("Terraform", "OpenTofu", "Pulumi", "AWS_CDK",
                     "CloudFormation", "Terragrunt"):
        assert required in names


def test_cloud_carries_container_runtime():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "cloud_infrastructure")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("OCI_image_format", "OCI_runtime_spec",
                     "containerd", "runc", "gVisor", "Kata_containers",
                     "image_layer_caching", "multi_stage_build",
                     "distroless_images"):
        assert required in names


def test_cloud_carries_aws():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "cloud_infrastructure")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("AWS_EC2", "AWS_S3", "AWS_Lambda", "AWS_IAM",
                     "AWS_VPC", "AWS_EKS", "AWS_Fargate", "AWS_RDS",
                     "AWS_Aurora", "AWS_DynamoDB", "AWS_CloudFront",
                     "AWS_Route53", "AWS_EBS", "AWS_EFS"):
        assert required in names


def test_cloud_carries_serverless_edge():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "cloud_infrastructure")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("GCP_Cloud_Run", "Cloudflare_Workers",
                     "Lambda_at_Edge", "Fastly_Compute"):
        assert required in names


def test_cloud_carries_networking():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "cloud_infrastructure")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("VPC_subnet", "NAT_gateway", "Internet_gateway",
                     "VPC_peering", "Transit_Gateway",
                     "PrivateLink_VPC_endpoint", "Security_group",
                     "Network_ACL"):
        assert required in names


def test_cloud_carries_storage():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "cloud_infrastructure")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("object_storage_API", "object_storage_classes",
                     "block_storage_provisioned_IOPS",
                     "file_storage_NFS_SMB"):
        assert required in names


def test_cloud_carries_iam():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "cloud_infrastructure")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("IAM_policy_evaluation", "IAM_role_vs_user",
                     "STS_temporary_credentials",
                     "OIDC_federation_GitHub_actions",
                     "service_account_K8s"):
        assert required in names


def test_cloud_carries_security_operations():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "cloud_infrastructure")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("PodSecurity_standards", "OPA_gatekeeper",
                     "Falco_runtime_security",
                     "container_image_scanning", "FinOps",
                     "reserved_instances_savings_plans",
                     "spot_instances", "Karpenter", "multi_cloud",
                     "hybrid_cloud"):
        assert required in names


def test_cloud_rules_carry_soundness_category():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "cloud_infrastructure")
    valid = {"denotational_equivalence", "algebraic_law",
             "extensional_equivalence", "cost_equivalence",
             "referential_transparency"}
    n_with_cat = 0
    for r in s.neighbours(mt, "has_rule"):
        if s.node(r)["attrs"].get("soundness_category") in valid:
            n_with_cat += 1
    assert n_with_cat >= 18


def test_cloud_decomposition_packs_load():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    load_one_seed(s, "cloud_infrastructure")
    ids = install_all_concept_expansions(s)
    for required in ("k8s_core_decomposition",
                     "k8s_advanced_decomposition",
                     "iac_gitops_decomposition",
                     "aws_services_deep_decomposition",
                     "container_internals_decomposition",
                     "serverless_patterns_decomposition",
                     "cloud_networking_decomposition",
                     "cloud_storage_tiers_decomposition",
                     "cloud_iam_decomposition"):
        assert required in ids, f"cloud pack {required!r} not loaded"


def test_total_cloud_concept_count():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = load_one_seed(s, "cloud_infrastructure")
    install_all_concept_expansions(s)
    n_concepts = len(s.neighbours(mt, "has_concept"))
    n_rules = len(s.neighbours(mt, "has_rule"))
    assert n_concepts >= 180, f"only {n_concepts} concepts"
    assert n_rules >= 55, f"only {n_rules} rules"

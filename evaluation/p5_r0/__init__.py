"""P5-R0 local transfer readiness gate.

This package is evaluator-owned engineering infrastructure only. It never
asserts release, adoption, general intelligence, or positive transfer.
"""
from .protocol import P5R0Error, TERMINAL_OUTCOMES
from .domain_cards import create_domain_cards, validate_domain_card
from .split import build_split_commitment, build_case_index
from .fixture_generator import generate_fixtures
from .runner import run_readiness_gate
from .repair import preregister_repair, validate_repair_lock, fail_closed_repair
from .rebuild import build_canonical_v3, rebuild_canonical_v3
from .mutations import build_mutation_result, record_mutation, verify_mutation_artifact, write_mutation_artifact

__all__ = ["P5R0Error", "TERMINAL_OUTCOMES", "create_domain_cards", "validate_domain_card", "build_split_commitment", "build_case_index", "generate_fixtures", "run_readiness_gate", "preregister_repair", "validate_repair_lock", "fail_closed_repair", "build_canonical_v3", "rebuild_canonical_v3", "build_mutation_result", "record_mutation", "verify_mutation_artifact", "write_mutation_artifact"]

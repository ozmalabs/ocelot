use substrate_rs::p3_graph::{restore, snapshot, validate_proposal};
use substrate_rs::p3_learning::{LearningProposal, P3ChangeKind, P3ProposalStatus};
fn digest(n: char) -> String {
    format!("sha256:{}", n.to_string().repeat(64))
}
fn proposal() -> LearningProposal {
    LearningProposal {
        proposal_digest: digest('1'),
        parent_snapshot_digest: digest('2'),
        mutable_artifact_path: "mutable-agent/rules.json".into(),
        mutable_artifact_digest: digest('3'),
        change_kind: P3ChangeKind::Rule,
        patch_digest: digest('4'),
        provenance_refs: vec![digest('5')],
        evidence_refs: vec![digest('6')],
        rollback_snapshot_digest: digest('7'),
        status: P3ProposalStatus::Proposed,
    }
}
#[test]
fn snapshot_digest_is_deterministic() {
    assert_eq!(snapshot(b"sealed").digest, snapshot(b"sealed").digest);
    assert_ne!(snapshot(b"sealed").digest, snapshot(b"changed").digest);
}
#[test]
fn graph_rejects_control_reference_and_restores_bytes() {
    assert!(validate_proposal(&proposal(), &[]).is_ok());
    let mut p = proposal();
    p.mutable_artifact_path = "control-plane/broker".into();
    assert!(validate_proposal(&p, &[]).is_err());
    let baseline = snapshot(b"baseline");
    let mut candidate = b"changed".to_vec();
    assert_eq!(
        restore(&baseline, &mut candidate)
            .unwrap()
            .restored_snapshot_digest,
        baseline.digest
    );
    assert_eq!(candidate, b"baseline");
}

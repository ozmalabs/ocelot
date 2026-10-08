//! Native P3 data-plane state.  This module has no evaluator key, score, or
//! adoption authority: it can create only `Proposed` learning changes.
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum P3ChangeKind {
    Rule,
    Seed,
    Codebook,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum P3ProposalStatus {
    Proposed,
    Rejected,
    RolledBack,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct LearningProposal {
    pub proposal_digest: String,
    pub parent_snapshot_digest: String,
    pub mutable_artifact_path: String,
    pub mutable_artifact_digest: String,
    pub change_kind: P3ChangeKind,
    pub patch_digest: String,
    pub provenance_refs: Vec<String>,
    pub evidence_refs: Vec<String>,
    pub rollback_snapshot_digest: String,
    pub status: P3ProposalStatus,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct P3CandidateSnapshot {
    pub digest: String,
    pub bytes: Vec<u8>,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct P3EvaluationRun {
    pub lock_digest: String,
    pub proposal_digest: String,
    pub status: P3ProposalStatus,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct P3ResultSeal {
    pub seal_digest: String,
    pub lock_digest: String,
    pub approved_by_evaluator: bool,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct P3RollbackRecord {
    pub proposal_digest: String,
    pub restored_snapshot_digest: String,
}

impl LearningProposal {
    pub fn proposed(&self) -> bool {
        self.status == P3ProposalStatus::Proposed
    }
    /// Native data-plane code has no transition to Approved; evaluator software
    /// appends external sealed outcomes and adoption authority separately.
    pub fn reject(mut self) -> Self {
        self.status = P3ProposalStatus::Rejected;
        self
    }
    pub fn rolled_back(mut self) -> Self {
        self.status = P3ProposalStatus::RolledBack;
        self
    }
}

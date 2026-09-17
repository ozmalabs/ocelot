//! P3 graph-side validation and deterministic byte snapshot/restore support.
//! Deliberately independent of host installers, evaluator keys, and scores.
use crate::p3_learning::{LearningProposal, P3ProposalStatus, P3CandidateSnapshot, P3RollbackRecord};

const FORBIDDEN: &[&str] = &["broker", "allowlist", "grant", "policy", "receipt", "evaluator", "scorer", "oracle", "benchmark", "generator", "split", "seed_commitment", "mount", "quota", "resource", "heartbeat", "kill", "stop", "result_channel", "control_plane"];

fn is_digest(value: &str) -> bool { value.len() == 71 && value.starts_with("sha256:") && value[7..].bytes().all(|b| b.is_ascii_hexdigit()) && !value[7..].bytes().all(|b| b == b'0') }
fn forbidden(value: &str) -> bool { let normalized=value.to_ascii_lowercase().replace('-', "_"); FORBIDDEN.iter().any(|token| normalized.contains(token)) }

pub fn validate_proposal(proposal: &LearningProposal, control_digests: &[String]) -> Result<(), &'static str> {
    if !proposal.proposed() { return Err("proposal state"); }
    if !proposal.mutable_artifact_path.starts_with("mutable-agent/") || proposal.mutable_artifact_path.split('/').any(|part| part == "..") { return Err("mutable artifact path"); }
    for digest in [&proposal.proposal_digest, &proposal.parent_snapshot_digest, &proposal.mutable_artifact_digest, &proposal.patch_digest, &proposal.rollback_snapshot_digest] {
        if !is_digest(digest) { return Err("proposal digest"); }
        if control_digests.iter().any(|locked| locked == digest) { return Err("control digest reference"); }
    }
    if proposal.provenance_refs.is_empty() || proposal.evidence_refs.is_empty() { return Err("missing provenance"); }
    for reference in proposal.provenance_refs.iter().chain(proposal.evidence_refs.iter()).chain(std::iter::once(&proposal.mutable_artifact_path)) {
        if !is_digest(reference) && reference != &proposal.mutable_artifact_path { return Err("reference digest"); }
        if forbidden(reference) { return Err("control reference"); }
    }
    Ok(())
}

// A small self-contained SHA-256 implementation prevents native state from
// relying on host hashing or mutable dependencies.
fn sha256(data: &[u8]) -> [u8;32] {
    const K:[u32;64]=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
    let mut message=data.to_vec(); let bits=(message.len() as u64)*8; message.push(0x80); while message.len()%64!=56 {message.push(0)} message.extend_from_slice(&bits.to_be_bytes());
    let mut h=[0x6a09e667u32,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
    for block in message.chunks_exact(64) { let mut w=[0u32;64]; for i in 0..16 { w[i]=u32::from_be_bytes(block[i*4..i*4+4].try_into().unwrap()); } for i in 16..64 { let s0=w[i-15].rotate_right(7)^w[i-15].rotate_right(18)^(w[i-15]>>3);let s1=w[i-2].rotate_right(17)^w[i-2].rotate_right(19)^(w[i-2]>>10);w[i]=w[i-16].wrapping_add(s0).wrapping_add(w[i-7]).wrapping_add(s1); } let(mut a,mut b,mut c,mut d,mut e,mut f,mut g,mut hh)=(h[0],h[1],h[2],h[3],h[4],h[5],h[6],h[7]); for i in 0..64 {let s1=e.rotate_right(6)^e.rotate_right(11)^e.rotate_right(25);let ch=(e&f)^((!e)&g);let t1=hh.wrapping_add(s1).wrapping_add(ch).wrapping_add(K[i]).wrapping_add(w[i]);let s0=a.rotate_right(2)^a.rotate_right(13)^a.rotate_right(22);let maj=(a&b)^(a&c)^(b&c);let t2=s0.wrapping_add(maj);hh=g;g=f;f=e;e=d.wrapping_add(t1);d=c;c=b;b=a;a=t1.wrapping_add(t2);} for (slot,add) in h.iter_mut().zip([a,b,c,d,e,f,g,hh]) {*slot=slot.wrapping_add(add);} }
    let mut output=[0u8;32];for(i,word)in h.iter().enumerate(){output[i*4..i*4+4].copy_from_slice(&word.to_be_bytes())}output
}
pub fn snapshot(bytes: &[u8]) -> P3CandidateSnapshot { let digest=sha256(bytes).iter().map(|b|format!("{b:02x}")).collect::<String>(); P3CandidateSnapshot {digest:format!("sha256:{digest}"),bytes:bytes.to_vec()} }
pub fn restore(snap:&P3CandidateSnapshot, candidate:&mut Vec<u8>) -> Result<P3RollbackRecord,&'static str> { let expected=snapshot(snap.bytes.as_slice()).digest; if expected != snap.digest {return Err("snapshot digest")}; *candidate=snap.bytes.clone(); if snapshot(candidate.as_slice()).digest != snap.digest {return Err("rollback mismatch")}; Ok(P3RollbackRecord{proposal_digest:"sha256:rollback-not-adoption".to_string(),restored_snapshot_digest:snap.digest.clone()}) }

#[cfg(test)] mod tests { use super::*; use crate::p3_learning::{P3ChangeKind, P3ProposalStatus}; fn digest(c:char)->String {format!("sha256:{}",c.to_string().repeat(64))} fn proposal()->LearningProposal{LearningProposal{proposal_digest:digest('1'),parent_snapshot_digest:digest('2'),mutable_artifact_path:"mutable-agent/rules.json".into(),mutable_artifact_digest:digest('3'),change_kind:P3ChangeKind::Rule,patch_digest:digest('4'),provenance_refs:vec![digest('5')],evidence_refs:vec![digest('6')],rollback_snapshot_digest:digest('7'),status:P3ProposalStatus::Proposed}} #[test]fn confines_mutation(){assert!(validate_proposal(&proposal(),&[]).is_ok());let mut p=proposal();p.mutable_artifact_path="control-plane/broker".into();assert!(validate_proposal(&p,&[]).is_err());} #[test]fn byte_snapshot_restores(){let pre=snapshot(b"before");let mut candidate=b"after".to_vec();let record=restore(&pre,&mut candidate).unwrap();assert_eq!(candidate,b"before");assert_eq!(record.restored_snapshot_digest,pre.digest);} }

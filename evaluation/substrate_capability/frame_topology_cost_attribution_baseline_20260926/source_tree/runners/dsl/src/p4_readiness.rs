use crate::{
    future_manifold,
    graph::{NodeID, TypedGraph},
    sym::Interner,
    value::Value,
};
use rustc_hash::FxHashMap;
use std::{ffi::c_void, os::raw::c_int};

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct P4R0Limits {
    pub steps: u8,
    pub information_interventions: u8,
    pub max_mistaken_actions: u8,
    pub replans: u8,
    pub candidate_branches: u8,
    pub hypotheses: u8,
    pub action_grants: u8,
    pub risk_units: u8,
    pub transactions: u8,
}
impl Default for P4R0Limits {
    fn default() -> Self {
        Self {
            steps: 8,
            information_interventions: 1,
            max_mistaken_actions: 1,
            replans: 1,
            candidate_branches: 12,
            hypotheses: 2,
            action_grants: 8,
            risk_units: 8,
            transactions: 8,
        }
    }
}
impl P4R0Limits {
    pub fn valid(&self) -> bool {
        self.steps == 8
            && self.information_interventions == 1
            && self.max_mistaken_actions == 1
            && self.replans == 1
            && self.candidate_branches == 12
            && self.hypotheses == 2
            && self.action_grants == 8
            && self.risk_units == 8
            && self.transactions == 8
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum P4ObservationStatus {
    Initial,
    SealedInterventionOutcome,
    SealedActionOutcome,
    FailedAction,
    UnknownOutput,
    Contradiction,
}

/// Serializable evaluator-to-native transport. This is untrusted data, not
/// the authority capability consumed by `advance_p4_r0`: callers may serialize
/// or deserialize it, but only the native evaluator adapter can mint a
/// `VerifiedActionOutcome` from it.
#[derive(Clone, Debug, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EvaluatorOutcomeTransport {
    pub run_id: String,
    pub proposal_digest: String,
    pub proposal_receipt_digest: String,
    pub grant_receipt_digest: String,
    pub broker_receipt_digest: String,
    pub replan_receipt_digest: String,
    pub sequence: u64,
    pub snapshot_digest: String,
    pub reservation_digest: String,
    pub outcome_receipt_digest: String,
    pub success: bool,
    #[serde(default)]
    pub arm_id: Option<String>,
    #[serde(default)]
    pub selection_digest: Option<String>,
    #[serde(default)]
    pub arm_digest: Option<String>,
    #[serde(default)]
    pub trace_digest: Option<String>,
}

/// The evaluator identity is installed by the native launch boundary, not read
/// from the untrusted transport. Constructing one cannot mint a completion
/// capability: it only selects which evaluator signature the runtime accepts.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct P4TrustedEvaluatorAuthority {
    authority_id: String,
    key_id: String,
    lock_digest: String,
    public_key: [u8; 32],
}

impl P4TrustedEvaluatorAuthority {
    pub fn from_base64url(
        authority_id: String,
        key_id: String,
        lock_digest: String,
        public_key: &str,
    ) -> Result<Self, &'static str> {
        if !valid_identifier(&authority_id)
            || !valid_identifier(&key_id)
            || !valid_digest(&lock_digest)
        {
            return Err("invalid_evaluator_authority");
        }
        let bytes = base64url_decode(public_key).ok_or("invalid_evaluator_authority")?;
        let public_key: [u8; 32] = bytes
            .try_into()
            .map_err(|_| "invalid_evaluator_authority")?;
        Ok(Self {
            authority_id,
            key_id,
            lock_digest,
            public_key,
        })
    }

    fn public_key_base64url(&self) -> String {
        base64url_encode(&self.public_key)
    }

    pub fn verify(&self, unsigned: &[u8], signature: &[u8]) -> bool {
        verify_ed25519(&self.public_key, unsigned, signature)
    }

}

#[derive(Clone, Debug, PartialEq, Eq, serde::Deserialize)]
#[serde(deny_unknown_fields)]
struct SignedEvaluatorOutcomeTransport {
    schema: String,
    authority_id: String,
    key_id: String,
    authority_public_key: String,
    lock_digest: String,
    #[serde(default)]
    fixture_id: Option<String>,
    #[serde(default)]
    fixture_selection_id: Option<String>,
    #[serde(default)]
    fixture_digest: Option<String>,
    #[serde(default)]
    fixture_record_digest: Option<String>,
    run_id: String,
    proposal_digest: String,
    proposal_receipt_digest: String,
    grant_receipt_digest: String,
    broker_receipt_digest: String,
    replan_receipt_digest: String,
    sequence: u64,
    snapshot_digest: String,
    reservation_digest: String,
    outcome_receipt_digest: String,
    success: bool,
    #[serde(default)]
    selection_digest: Option<String>,
    #[serde(default)]
    arm_id: Option<String>,
    #[serde(default)]
    arm_digest: Option<String>,
    #[serde(default)]
    trace_digest: Option<String>,
    signature: String,
}

impl SignedEvaluatorOutcomeTransport {
    fn verify(
        self,
        authority: &P4TrustedEvaluatorAuthority,
        unsigned: &[u8],
    ) -> Result<EvaluatorOutcomeTransport, &'static str> {
        if self.schema != "P4R0EvaluatorSignedOutcomeV1"
            || self.authority_id != authority.authority_id
            || self.key_id != authority.key_id
            || self.lock_digest != authority.lock_digest
            || self.authority_public_key != authority.public_key_base64url()
            || !valid_identifier(&self.run_id)
            || ![
                &self.proposal_digest,
                &self.proposal_receipt_digest,
                &self.grant_receipt_digest,
                &self.broker_receipt_digest,
                &self.replan_receipt_digest,
                &self.snapshot_digest,
                &self.reservation_digest,
                &self.outcome_receipt_digest,
            ]
            .iter()
            .all(|digest| valid_digest(digest))
        {
            return Err("evaluator_authority_or_transport_binding_mismatch");
        }
        let signature = base64url_decode(&self.signature).ok_or("invalid_evaluator_signature")?;
        if signature.len() != 64 || !verify_ed25519(&authority.public_key, unsigned, &signature) {
            return Err("evaluator_receipt_verification_failed");
        }
        Ok(EvaluatorOutcomeTransport {
            run_id: self.run_id,
            proposal_digest: self.proposal_digest,
            proposal_receipt_digest: self.proposal_receipt_digest,
            grant_receipt_digest: self.grant_receipt_digest,
            broker_receipt_digest: self.broker_receipt_digest,
            replan_receipt_digest: self.replan_receipt_digest,
            sequence: self.sequence,
            snapshot_digest: self.snapshot_digest,
            reservation_digest: self.reservation_digest,
            outcome_receipt_digest: self.outcome_receipt_digest,
            success: self.success,
            arm_id: self.arm_id,
            selection_digest: self.selection_digest,
            arm_digest: self.arm_digest,
            trace_digest: self.trace_digest,
        })
    }
}

/// A capability minted only after the concrete trusted evaluator verifier
/// authenticates every wire field and the adapter binds it to native state. It
/// intentionally has no public constructor, conversion, or serialization.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct VerifiedActionOutcome {
    run_id: String,
    proposal_digest: String,
    proposal_receipt_digest: String,
    grant_receipt_digest: String,
    broker_receipt_digest: String,
    replan_receipt_digest: String,
    sequence: u64,
    snapshot_digest: String,
    reservation_digest: String,
    outcome_receipt_digest: String,
    success: bool,
    selection_digest: Option<String>,
    arm_digest: Option<String>,
    trace_digest: Option<String>,
}

impl VerifiedActionOutcome {
    fn mint(transport: EvaluatorOutcomeTransport) -> Self {
        Self {
            run_id: transport.run_id,
            proposal_digest: transport.proposal_digest,
            proposal_receipt_digest: transport.proposal_receipt_digest,
            grant_receipt_digest: transport.grant_receipt_digest,
            broker_receipt_digest: transport.broker_receipt_digest,
            replan_receipt_digest: transport.replan_receipt_digest,
            sequence: transport.sequence,
            snapshot_digest: transport.snapshot_digest,
            reservation_digest: transport.reservation_digest,
            outcome_receipt_digest: transport.outcome_receipt_digest,
            success: transport.success,
            selection_digest: transport.selection_digest,
            arm_digest: transport.arm_digest,
            trace_digest: transport.trace_digest,
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub(crate) struct EvaluatorOutcomeBindings {
    pub(crate) run_id: String,
    pub(crate) proposal_digest: String,
    pub(crate) proposal_receipt_digest: String,
    pub(crate) grant_receipt_digest: String,
    pub(crate) broker_receipt_digest: String,
    pub(crate) replan_receipt_digest: String,
    pub(crate) sequence: u64,
    pub(crate) snapshot_digest: String,
    pub(crate) reservation_digest: String,
    pub(crate) outcome_receipt_digest: String,
}

impl EvaluatorOutcomeBindings {
    #[allow(clippy::too_many_arguments)]
    pub(crate) fn new(
        run_id: String,
        proposal_digest: String,
        proposal_receipt_digest: String,
        grant_receipt_digest: String,
        broker_receipt_digest: String,
        replan_receipt_digest: String,
        sequence: u64,
        snapshot_digest: String,
        reservation_digest: String,
        outcome_receipt_digest: String,
    ) -> Self {
        Self {
            run_id,
            proposal_digest,
            proposal_receipt_digest,
            grant_receipt_digest,
            broker_receipt_digest,
            replan_receipt_digest,
            sequence,
            snapshot_digest,
            reservation_digest,
            outcome_receipt_digest,
        }
    }

    fn matches(&self, outcome: &EvaluatorOutcomeTransport) -> bool {
        outcome.run_id == self.run_id
            && outcome.proposal_digest == self.proposal_digest
            && outcome.proposal_receipt_digest == self.proposal_receipt_digest
            && outcome.grant_receipt_digest == self.grant_receipt_digest
            && outcome.broker_receipt_digest == self.broker_receipt_digest
            && outcome.replan_receipt_digest == self.replan_receipt_digest
            && outcome.sequence == self.sequence
            && outcome.snapshot_digest == self.snapshot_digest
            && outcome.reservation_digest == self.reservation_digest
            && outcome.outcome_receipt_digest == self.outcome_receipt_digest
    }
}

/// This adapter is deliberately crate-private. The only caller first verifies
/// a canonical evaluator signature with `P4TrustedEvaluatorAuthority`.
struct ReceiptVerifyingEvaluatorAdapter;

impl ReceiptVerifyingEvaluatorAdapter {
    fn seal_action_outcome(
        observation: SealedObservation,
        bindings: &EvaluatorOutcomeBindings,
        transport: EvaluatorOutcomeTransport,
    ) -> Result<SealedObservation, &'static str> {
        if !matches!(observation.status, P4ObservationStatus::SealedActionOutcome) {
            return Err("sealed_action_outcome_required");
        }
        if observation.run_id != bindings.run_id
            || observation.sequence != bindings.sequence
            || observation.snapshot_digest.as_deref() != Some(bindings.snapshot_digest.as_str())
            || observation.parent_receipt.as_deref()
                != Some(bindings.outcome_receipt_digest.as_str())
            || !bindings.matches(&transport)
        {
            return Err("evaluator_outcome_binding_mismatch");
        }
        Ok(observation.with_verified_action_outcome(VerifiedActionOutcome::mint(transport)))
    }
}

/// Deserialize only canonical signed JSON, authenticate it with the installed
/// authority, derive native expectations from the persisted reservation, then
/// hand the verified transport to the crate-private opaque adapter.
fn seal_serialized_evaluator_outcome(
    graph: &TypedGraph,
    interner: &mut Interner,
    observation: SealedObservation,
    serialized_transport: &[u8],
    authority: &P4TrustedEvaluatorAuthority,
) -> Result<SealedObservation, &'static str> {
    let value: serde_json::Value =
        serde_json::from_slice(serialized_transport).map_err(|_| "invalid_evaluator_transport")?;
    if canonical_json_bytes(&value)? != serialized_transport {
        return Err("noncanonical_evaluator_transport");
    }
    let mut unsigned = value.clone();
    unsigned
        .as_object_mut()
        .ok_or("invalid_evaluator_transport")?
        .remove("signature")
        .ok_or("invalid_evaluator_transport")?;
    let transport: SignedEvaluatorOutcomeTransport =
        serde_json::from_value(value).map_err(|_| "invalid_evaluator_transport")?;
    let transport = transport.verify(authority, &canonical_json_bytes(&unsigned)?)?;
    let s = state(graph, interner).ok_or("native_reservation_missing")?;
    let reservation = stored_node(graph, interner, s, "p4_action_reservation_node")
        .ok_or("native_reservation_missing")?;
    let run_id = text(graph, interner, s, "p4_run_id").ok_or("native_reservation_missing")?;
    let proposal_digest = text(graph, interner, reservation, "p4_proposal_digest")
        .ok_or("native_reservation_missing")?;
    let reservation_digest = text(graph, interner, reservation, "p4_reservation_digest")
        .ok_or("native_reservation_missing")?;
    let sequence = number(graph, interner, s, "p4_expected_outcome_sequence")
        .ok_or("native_reservation_missing")?;
    let snapshot_digest =
        text(graph, interner, s, "p4_snapshot_digest").ok_or("native_reservation_missing")?;
    if let Some(expected) = text(graph, interner, s, "p4_selection_digest") {
        if transport.selection_digest.as_deref() != Some(expected.as_str()) || transport.arm_digest.as_deref() != text(graph, interner, s, "p4_arm_digest").as_deref() {
            return Err("evaluator_selection_binding_mismatch");
        }
    }
    let replan_receipt_digest =
        text(graph, interner, s, "p4_replan_receipt").ok_or("native_replan_receipt_missing")?;
    if transport.replan_receipt_digest != replan_receipt_digest {
        return Err("evaluator_replan_receipt_binding_mismatch");
    }
    let bindings = EvaluatorOutcomeBindings::new(
        run_id,
        proposal_digest,
        transport.proposal_receipt_digest.clone(),
        transport.grant_receipt_digest.clone(),
        transport.broker_receipt_digest.clone(),
        replan_receipt_digest,
        sequence,
        snapshot_digest,
        reservation_digest,
        transport.outcome_receipt_digest.clone(),
    );
    ReceiptVerifyingEvaluatorAdapter::seal_action_outcome(observation, &bindings, transport)
}

/// Non-test native runtime entry point. It is the only public route from a
/// signed evaluator transport to `advance_p4_r0`; it never returns the opaque
/// capability and cannot accept an injectable verifier.
pub fn advance_signed_evaluator_outcome(
    graph: &mut TypedGraph,
    interner: &mut Interner,
    observation: SealedObservation,
    serialized_transport: &[u8],
    authority: &P4TrustedEvaluatorAuthority,
    limits: P4R0Limits,
) -> Result<P4Decision, &'static str> {
    let sealed = seal_serialized_evaluator_outcome(
        graph,
        interner,
        observation,
        serialized_transport,
        authority,
    )?;
    Ok(advance_p4_r0(graph, interner, sealed, limits))
}

fn valid_identifier(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 128
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_' | b'.' | b':'))
}

fn base64url_encode(bytes: &[u8]) -> String {
    const TABLE: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
    let mut output = String::new();
    for chunk in bytes.chunks(3) {
        let value = (u32::from(chunk[0]) << 16)
            | (u32::from(*chunk.get(1).unwrap_or(&0)) << 8)
            | u32::from(*chunk.get(2).unwrap_or(&0));
        output.push(TABLE[(value >> 18) as usize] as char);
        output.push(TABLE[((value >> 12) & 63) as usize] as char);
        if chunk.len() > 1 {
            output.push(TABLE[((value >> 6) & 63) as usize] as char);
        }
        if chunk.len() > 2 {
            output.push(TABLE[(value & 63) as usize] as char);
        }
    }
    output
}

fn base64url_decode(value: &str) -> Option<Vec<u8>> {
    if value.contains('=') || value.len() % 4 == 1 {
        return None;
    }
    let mut output = Vec::with_capacity(value.len() * 3 / 4);
    let mut buffer = 0u32;
    let mut bits = 0u8;
    for byte in value.bytes() {
        let six = match byte {
            b'A'..=b'Z' => byte - b'A',
            b'a'..=b'z' => byte - b'a' + 26,
            b'0'..=b'9' => byte - b'0' + 52,
            b'-' => 62,
            b'_' => 63,
            _ => return None,
        };
        buffer = (buffer << 6) | u32::from(six);
        bits += 6;
        while bits >= 8 {
            bits -= 8;
            output.push((buffer >> bits) as u8);
            buffer &= (1 << bits) - 1;
        }
    }
    if bits != 0 && buffer != 0 {
        return None;
    }
    Some(output)
}

fn canonical_json_bytes(value: &serde_json::Value) -> Result<Vec<u8>, &'static str> {
    fn render(value: &serde_json::Value, output: &mut String) -> Result<(), &'static str> {
        match value {
            serde_json::Value::Null | serde_json::Value::Bool(_) | serde_json::Value::String(_) => {
                output.push_str(
                    &serde_json::to_string(value).map_err(|_| "canonical_evaluator_transport")?,
                );
            }
            serde_json::Value::Number(number) => {
                if !(number.is_i64() || number.is_u64()) {
                    return Err("canonical_evaluator_transport");
                }
                output.push_str(&number.to_string());
            }
            serde_json::Value::Array(items) => {
                output.push('[');
                for (index, item) in items.iter().enumerate() {
                    if index != 0 {
                        output.push(',');
                    }
                    render(item, output)?;
                }
                output.push(']');
            }
            serde_json::Value::Object(items) => {
                output.push('{');
                let mut keys: Vec<_> = items.keys().collect();
                keys.sort_unstable();
                for (index, key) in keys.iter().enumerate() {
                    if index != 0 {
                        output.push(',');
                    }
                    output.push_str(
                        &serde_json::to_string(*key)
                            .map_err(|_| "canonical_evaluator_transport")?,
                    );
                    output.push(':');
                    render(&items[*key], output)?;
                }
                output.push('}');
            }
        }
        Ok(())
    }
    let mut output = String::new();
    render(value, &mut output)?;
    Ok(output.into_bytes())
}

fn sha256_bytes(bytes: &[u8]) -> [u8; 32] {
    let hex = crate::p2_native::sha256_hex(bytes);
    let mut output = [0u8; 32];
    for (index, pair) in hex.as_bytes()[7..].chunks_exact(2).enumerate() {
        output[index] = (hex_value(pair[0]).unwrap() << 4) | hex_value(pair[1]).unwrap();
    }
    output
}

fn hex_value(value: u8) -> Option<u8> {
    match value {
        b'0'..=b'9' => Some(value - b'0'),
        b'a'..=b'f' => Some(value - b'a' + 10),
        _ => None,
    }
}

#[cfg(target_os = "linux")]
#[link(name = ":libcrypto.so.3")]
unsafe extern "C" {
    fn EVP_PKEY_new_raw_public_key(
        ty: c_int,
        engine: *mut c_void,
        key: *const u8,
        key_len: usize,
    ) -> *mut c_void;
    fn EVP_PKEY_free(key: *mut c_void);
    fn EVP_MD_CTX_new() -> *mut c_void;
    fn EVP_MD_CTX_free(context: *mut c_void);
    fn EVP_DigestVerifyInit(
        context: *mut c_void,
        pctx: *mut *mut c_void,
        ty: *const c_void,
        engine: *mut c_void,
        key: *mut c_void,
    ) -> c_int;
    fn EVP_DigestVerify(
        context: *mut c_void,
        signature: *const u8,
        signature_len: usize,
        message: *const u8,
        message_len: usize,
    ) -> c_int;
}

#[cfg(target_os = "linux")]
fn verify_ed25519(public_key: &[u8; 32], unsigned: &[u8], signature: &[u8]) -> bool {
    // Python signs SHA-256(canonical unsigned JSON), matching the established
    // P0A receipt convention. EVP Ed25519 verifies that 32-byte prehash as its
    // message; it must not be asked to hash it a second time.
    const EVP_PKEY_ED25519: c_int = 1087;
    let digest = sha256_bytes(unsigned);
    unsafe {
        let key = EVP_PKEY_new_raw_public_key(
            EVP_PKEY_ED25519,
            std::ptr::null_mut(),
            public_key.as_ptr(),
            public_key.len(),
        );
        if key.is_null() {
            return false;
        }
        let context = EVP_MD_CTX_new();
        if context.is_null() {
            EVP_PKEY_free(key);
            return false;
        }
        let initialized = EVP_DigestVerifyInit(
            context,
            std::ptr::null_mut(),
            std::ptr::null(),
            std::ptr::null_mut(),
            key,
        ) == 1;
        let verified = initialized
            && EVP_DigestVerify(
                context,
                signature.as_ptr(),
                signature.len(),
                digest.as_ptr(),
                digest.len(),
            ) == 1;
        EVP_MD_CTX_free(context);
        EVP_PKEY_free(key);
        verified
    }
}

#[cfg(not(target_os = "linux"))]
fn verify_ed25519(_: &[u8; 32], _: &[u8], _: &[u8]) -> bool {
    false
}

#[derive(Clone, Debug)]
pub struct SealedObservation {
    logical_time: u64,
    parent_receipt: Option<String>,
    status: P4ObservationStatus,
    declared_fields: Vec<String>,
    candidates: Vec<NodeID>,
    episode: Option<NodeID>,
    policy: Option<NodeID>,
    run_id: String,
    sequence: u64,
    snapshot_digest: Option<String>,
    /// The host must persist the exact digest of the emitted action proposal here
    /// before the state machine can accept its corresponding sealed outcome.
    action_proposal_digest: Option<String>,
    /// Digest of the action reservation bound to the emitted proposal. A signed
    /// evaluator outcome must carry this exact value before completion is minted.
    action_reservation_digest: Option<String>,
    selection_digest: Option<String>,
    fixture_record_digest: Option<String>,
    arm_id: Option<String>,
    arm_digest: Option<String>,
    verified_action_outcome: Option<VerifiedActionOutcome>,
}

impl SealedObservation {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        logical_time: u64,
        parent_receipt: Option<String>,
        status: P4ObservationStatus,
        declared_fields: Vec<String>,
        candidates: Vec<NodeID>,
        episode: Option<NodeID>,
        policy: Option<NodeID>,
        run_id: String,
        sequence: u64,
        snapshot_digest: Option<String>,
        action_proposal_digest: Option<String>,
    ) -> Self {
        Self {
            logical_time,
            parent_receipt,
            status,
            declared_fields,
            candidates,
            episode,
            policy,
            run_id,
            sequence,
            snapshot_digest,
            action_proposal_digest,
            action_reservation_digest: None,
            selection_digest: None,
            fixture_record_digest: None,
            arm_id: None,
            arm_digest: None,
            verified_action_outcome: None,
        }
    }

    /// Attach the reservation digest to an action proposal observation. This is
    /// still only data; the evaluator adapter must later verify the binding.
    pub fn with_action_reservation_digest(mut self, reservation_digest: String) -> Self {
        self.action_reservation_digest = Some(reservation_digest);
        self
    }

    pub fn with_runtime_binding(mut self, selection_digest: String, fixture_record_digest: String, arm_id: String, arm_digest: String) -> Self {
        self.selection_digest = Some(selection_digest);
        self.fixture_record_digest = Some(fixture_record_digest);
        self.arm_id = Some(arm_id);
        self.arm_digest = Some(arm_digest);
        self
    }

    fn with_verified_action_outcome(mut self, outcome: VerifiedActionOutcome) -> Self {
        self.verified_action_outcome = Some(outcome);
        self
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum P4Decision {
    ProposeIntervention { proposal: NodeID },
    ProposeAction { proposal: NodeID },
    AwaitOutcome,
    Replan { node: NodeID },
    Impasse { reason: &'static str },
    Complete,
}

fn forbidden(field: &str) -> bool {
    let f = field.to_ascii_lowercase();
    [
        "world",
        "domain",
        "fixture",
        "hidden",
        "mechanism",
        "evaluator",
    ]
    .iter()
    .any(|x| f.contains(x))
}
fn valid_digest(value: &str) -> bool {
    value.len() == 71
        && value.starts_with("sha256:")
        && value[7..]
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}
fn attr(i: &mut Interner, name: &str) -> crate::sym::Sym {
    i.intern(name)
}
fn node(graph: &mut TypedGraph, i: &mut Interner, ty: &str, time: u64) -> NodeID {
    let n = graph.insert_node(attr(i, ty), FxHashMap::default());
    graph.set_node_attr(n, attr(i, "p4_logical_time"), Value::Int(time as i64));
    graph.set_node_attr(n, attr(i, "p4_immutable"), Value::Bool(true));
    n
}
fn link(graph: &mut TypedGraph, i: &mut Interner, a: NodeID, b: NodeID) {
    let _ = graph.insert_edge(a, attr(i, "p4_causal_next"), b, FxHashMap::default());
}
fn state(graph: &TypedGraph, i: &mut Interner) -> Option<NodeID> {
    let ty = attr(i, "P4R0State");
    graph.nodes_of_type(ty).into_iter().next()
}
fn phase(graph: &TypedGraph, i: &mut Interner, s: NodeID) -> i64 {
    graph
        .node(s)
        .attrs
        .get(&attr(i, "p4_phase"))
        .and_then(|v| {
            if let Value::Int(x) = v {
                Some(*x)
            } else {
                None
            }
        })
        .unwrap_or(0)
}
fn set_phase(graph: &mut TypedGraph, i: &mut Interner, s: NodeID, p: i64) {
    graph.set_node_attr(s, attr(i, "p4_phase"), Value::Int(p));
}
fn set_text(graph: &mut TypedGraph, i: &mut Interner, s: NodeID, name: &str, value: &str) {
    let text = attr(i, value);
    graph.set_node_attr(s, attr(i, name), Value::Str(text));
}
fn text(graph: &TypedGraph, i: &mut Interner, s: NodeID, name: &str) -> Option<String> {
    graph.node(s).attrs.get(&attr(i, name)).and_then(|v| {
        if let Value::Str(x) = v {
            Some(i.resolve(*x).to_string())
        } else {
            None
        }
    })
}
fn stored_node(graph: &TypedGraph, i: &mut Interner, s: NodeID, name: &str) -> Option<NodeID> {
    graph.node(s).attrs.get(&attr(i, name)).and_then(|v| {
        if let Value::Node(node) = v {
            Some(*node)
        } else {
            None
        }
    })
}
fn number(graph: &TypedGraph, i: &mut Interner, s: NodeID, name: &str) -> Option<u64> {
    graph.node(s).attrs.get(&attr(i, name)).and_then(|v| {
        if let Value::Int(x) = v {
            u64::try_from(*x).ok()
        } else {
            None
        }
    })
}
fn advance_stamp(graph: &mut TypedGraph, i: &mut Interner, s: NodeID, input: &SealedObservation) {
    graph.set_node_attr(
        s,
        attr(i, "p4_last_time"),
        Value::Int(input.logical_time as i64),
    );
    graph.set_node_attr(
        s,
        attr(i, "p4_last_sequence"),
        Value::Int(input.sequence as i64),
    );
}
fn newer(graph: &TypedGraph, i: &mut Interner, s: NodeID, input: &SealedObservation) -> bool {
    number(graph, i, s, "p4_last_time").is_none_or(|n| input.logical_time > n)
        && number(graph, i, s, "p4_last_sequence").is_none_or(|n| input.sequence > n)
}
fn impasse(
    graph: &mut TypedGraph,
    i: &mut Interner,
    time: u64,
    reason: &'static str,
) -> P4Decision {
    let n = node(graph, i, "Impasse", time);
    graph.set_node_attr(n, attr(i, "p4_reason"), Value::Int(reason.len() as i64));
    P4Decision::Impasse { reason }
}

/// Advance one bounded local causal-loop transition. This function consumes only
/// receipt bindings already verified by the evaluator-owned transport boundary.
pub fn advance_p4_r0(
    graph: &mut TypedGraph,
    interner: &mut Interner,
    input: SealedObservation,
    limits: P4R0Limits,
) -> P4Decision {
    let snapshot_valid = input.snapshot_digest.as_deref().is_some_and(valid_digest);
    if !limits.valid()
        || input.run_id.is_empty()
        || input.candidates.len() > limits.candidate_branches as usize
        || input.declared_fields.iter().any(|f| forbidden(f))
        || input
            .parent_receipt
            .as_deref()
            .is_some_and(|r| !valid_digest(r))
        || input.snapshot_digest.is_some() && !snapshot_valid
    {
        return impasse(graph, interner, input.logical_time, "invalid_envelope");
    }
    if matches!(input.status, P4ObservationStatus::Contradiction) {
        let c = node(graph, interner, "Contradiction", input.logical_time);
        let _ = c;
        return impasse(
            graph,
            interner,
            input.logical_time,
            "contradictory_observation",
        );
    }
    let s = state(graph, interner).unwrap_or_else(|| {
        let s = node(graph, interner, "P4R0State", input.logical_time);
        set_phase(graph, interner, s, 0);
        s
    });
    let p = phase(graph, interner, s);
    if input.selection_digest.is_some() || input.arm_digest.is_some() || input.arm_id.is_some() {
        let (Some(selection_digest), Some(record_digest), Some(arm_id), Some(arm_digest)) = (input.selection_digest.as_ref(), input.fixture_record_digest.as_ref(), input.arm_id.as_ref(), input.arm_digest.as_ref()) else {
            return impasse(graph, interner, input.logical_time, "incomplete_runtime_selection");
        };
        if !valid_digest(selection_digest) || !valid_digest(record_digest) || !valid_digest(arm_digest) || !valid_identifier(arm_id) {
            return impasse(graph, interner, input.logical_time, "invalid_runtime_selection");
        }
        if let Some(existing) = text(graph, interner, s, "p4_selection_digest") {
            if existing != *selection_digest || text(graph, interner, s, "p4_fixture_record_digest") != Some(record_digest.clone()) || text(graph, interner, s, "p4_arm_digest") != Some(arm_digest.clone()) || text(graph, interner, s, "p4_arm_id") != Some(arm_id.clone()) {
                return impasse(graph, interner, input.logical_time, "runtime_selection_mismatch");
            }
        } else {
            set_text(graph, interner, s, "p4_selection_digest", selection_digest);
            set_text(graph, interner, s, "p4_fixture_record_digest", record_digest);
            set_text(graph, interner, s, "p4_arm_id", arm_id);
            set_text(graph, interner, s, "p4_arm_digest", arm_digest);
        }
    }
    if p >= 4 {
        return if matches!(input.status, P4ObservationStatus::SealedActionOutcome) {
            impasse(
                graph,
                interner,
                input.logical_time,
                "replayed_action_outcome",
            )
        } else {
            P4Decision::Complete
        };
    }
    if !newer(graph, interner, s, &input) {
        return impasse(
            graph,
            interner,
            input.logical_time,
            "stale_or_replayed_observation",
        );
    }
    if matches!(input.status, P4ObservationStatus::FailedAction) {
        set_phase(graph, interner, s, 99);
        return impasse(graph, interner, input.logical_time, "failed_action");
    }
    if matches!(input.status, P4ObservationStatus::UnknownOutput) {
        let retries = graph
            .node(s)
            .attrs
            .get(&attr(interner, "p4_unknown_retries"))
            .and_then(|v| {
                if let Value::Int(x) = v {
                    Some(*x)
                } else {
                    None
                }
            })
            .unwrap_or(0);
        if retries >= 1 {
            set_phase(graph, interner, s, 99);
            return impasse(graph, interner, input.logical_time, "unknown_output");
        }
        graph.set_node_attr(s, attr(interner, "p4_unknown_retries"), Value::Int(1));
        advance_stamp(graph, interner, s, &input);
        return P4Decision::AwaitOutcome;
    }
    if p == 0 {
        if !matches!(input.status, P4ObservationStatus::Initial)
            || input.parent_receipt.is_some()
            || !snapshot_valid
        {
            return impasse(
                graph,
                interner,
                input.logical_time,
                "initial_context_required",
            );
        }
        let (Some(ep), Some(policy)) = (input.episode, input.policy) else {
            return impasse(
                graph,
                interner,
                input.logical_time,
                "missing_manifold_context",
            );
        };
        let Some(selection) =
            future_manifold::feasible_selection(graph, interner, ep, policy, &input.candidates)
        else {
            return impasse(graph, interner, input.logical_time, "unsupported_manifold");
        };
        let Some(candidate) = selection.selected.first().copied() else {
            return impasse(
                graph,
                interner,
                input.logical_time,
                "unresolved_or_infeasible_manifold",
            );
        };
        let arm_id = text(graph, interner, s, "p4_arm_id").unwrap_or_default();
        if arm_id == "reactive_no_plan" || arm_id == "no_causal_model" {
            let reservation = node(graph, interner, "ActionReservation", input.logical_time);
            let proposal = node(graph, interner, "GraphActionProposalV1", input.logical_time);
            if arm_id == "no_causal_model" {
                let plan = node(graph, interner, "PlanNode", input.logical_time);
                link(graph, interner, plan, reservation);
                graph.set_node_attr(plan, attr(interner, "p4_candidate_projection_node"), Value::Node(candidate));
            } else {
                let direct = node(graph, interner, "ReactiveTransition", input.logical_time);
                link(graph, interner, direct, reservation);
            }
            link(graph, interner, reservation, proposal);
            graph.set_node_attr(proposal, attr(interner, "p4_is_effect_request"), Value::Bool(true));
            set_text(graph, interner, s, "p4_run_id", &input.run_id);
            graph.set_node_attr(s, attr(interner, "p4_action_reservation_node"), Value::Node(reservation));
            set_text(graph, interner, s, "p4_snapshot_digest", input.snapshot_digest.as_deref().unwrap());
            advance_stamp(graph, interner, s, &input);
            set_phase(graph, interner, s, 1);
            return P4Decision::ProposeIntervention { proposal };
        }
        let belief = node(graph, interner, "BeliefState", input.logical_time);
        let hypothesis = node(graph, interner, "CausalHypothesis", input.logical_time);
        let query = node(graph, interner, "CausalQuery", input.logical_time);
        let intervention = node(graph, interner, "InterventionCandidate", input.logical_time);
        let branch = node(graph, interner, "CounterfactualBranch", input.logical_time);
        let plan = node(graph, interner, "PlanNode", input.logical_time);
        let reservation = node(graph, interner, "ActionReservation", input.logical_time);
        let proposal = node(graph, interner, "GraphActionProposalV1", input.logical_time);
        for pair in [
            (belief, hypothesis),
            (hypothesis, query),
            (query, intervention),
            (intervention, branch),
            (branch, plan),
            (plan, reservation),
            (reservation, proposal),
        ] {
            link(graph, interner, pair.0, pair.1)
        }
        graph.set_node_attr(
            plan,
            attr(interner, "p4_candidate_projection_node"),
            Value::Node(candidate),
        );
        graph.set_node_attr(
            proposal,
            attr(interner, "p4_is_effect_request"),
            Value::Bool(true),
        );
        set_text(graph, interner, s, "p4_run_id", &input.run_id);
        graph.set_node_attr(
            s,
            attr(interner, "p4_action_reservation_node"),
            Value::Node(reservation),
        );
        set_text(
            graph,
            interner,
            s,
            "p4_snapshot_digest",
            input.snapshot_digest.as_deref().unwrap(),
        );
        advance_stamp(graph, interner, s, &input);
        set_phase(graph, interner, s, 1);
        return P4Decision::ProposeIntervention { proposal };
    }
    let run_matches =
        text(graph, interner, s, "p4_run_id").as_deref() == Some(input.run_id.as_str());
    let snapshot_matches = text(graph, interner, s, "p4_snapshot_digest").as_deref()
        == input.snapshot_digest.as_deref();
    if !run_matches || !snapshot_matches {
        return impasse(
            graph,
            interner,
            input.logical_time,
            "run_or_snapshot_mismatch",
        );
    }
    if p == 1 {
        let arm_id = text(graph, interner, s, "p4_arm_id").unwrap_or_default();
        if arm_id == "reset_memory" {
            let reset = node(graph, interner, "MemoryReset", input.logical_time);
            set_text(graph, interner, reset, "p4_reset_reason", "intervention_provenance_cleared");
            set_phase(graph, interner, s, 99);
            return impasse(graph, interner, input.logical_time, "memory_reset_lost_provenance");
        }
        if (arm_id == "reactive_no_plan" || arm_id == "no_causal_model") && matches!(input.status, P4ObservationStatus::SealedInterventionOutcome) && input.parent_receipt.is_some() {
            set_text(graph, interner, s, "p4_replan_receipt", input.parent_receipt.as_deref().unwrap());
            advance_stamp(graph, interner, s, &input);
            set_phase(graph, interner, s, 2);
            return P4Decision::AwaitOutcome;
        }
        if !matches!(input.status, P4ObservationStatus::SealedInterventionOutcome)
            || input.parent_receipt.is_none()
        {
            return impasse(
                graph,
                interner,
                input.logical_time,
                "intervention_receipt_required",
            );
        };
        let receipt = input.parent_receipt.as_ref().unwrap();
        let r = node(graph, interner, "Replan", input.logical_time);
        set_text(graph, interner, r, "p4_receipt_parent", receipt);
        set_text(graph, interner, s, "p4_replan_receipt", receipt);
        advance_stamp(graph, interner, s, &input);
        set_phase(graph, interner, s, 2);
        return P4Decision::Replan { node: r };
    }
    if p == 2 {
        let expected = input.action_proposal_digest.as_deref();
        let reservation_digest = input.action_reservation_digest.as_deref();
        let reservation = stored_node(graph, interner, s, "p4_action_reservation_node");
        if !matches!(input.status, P4ObservationStatus::Initial)
            || input.parent_receipt.as_deref()
                != text(graph, interner, s, "p4_replan_receipt").as_deref()
            || !expected.is_some_and(valid_digest)
            || !reservation_digest.is_some_and(valid_digest)
            || reservation.is_none()
        {
            return impasse(
                graph,
                interner,
                input.logical_time,
                "replan_receipt_required",
            );
        };
        let proposal = node(graph, interner, "GraphActionProposalV1", input.logical_time);
        graph.set_node_attr(
            proposal,
            attr(interner, "p4_is_effect_request"),
            Value::Bool(true),
        );
        set_text(
            graph,
            interner,
            proposal,
            "p4_proposal_digest",
            expected.unwrap(),
        );
        set_text(
            graph,
            interner,
            reservation.unwrap(),
            "p4_proposal_digest",
            expected.unwrap(),
        );
        set_text(
            graph,
            interner,
            reservation.unwrap(),
            "p4_reservation_digest",
            reservation_digest.unwrap(),
        );
        set_text(
            graph,
            interner,
            s,
            "p4_expected_action_digest",
            expected.unwrap(),
        );
        set_text(
            graph,
            interner,
            s,
            "p4_expected_reservation_digest",
            reservation_digest.unwrap(),
        );
        graph.set_node_attr(
            s,
            attr(interner, "p4_expected_outcome_sequence"),
            Value::Int((input.sequence + 1) as i64),
        );
        advance_stamp(graph, interner, s, &input);
        set_phase(graph, interner, s, 3);
        return P4Decision::ProposeAction { proposal };
    }
    if p == 3 && matches!(input.status, P4ObservationStatus::SealedActionOutcome) {
        let Some(outcome) = input.verified_action_outcome.as_ref() else {
            return impasse(
                graph,
                interner,
                input.logical_time,
                "verified_action_outcome_required",
            );
        };
        let expected_sequence = number(graph, interner, s, "p4_expected_outcome_sequence");
        let valid = outcome.success
            && outcome.run_id == input.run_id
            && outcome.proposal_digest
                == text(graph, interner, s, "p4_expected_action_digest").unwrap_or_default()
            && outcome.reservation_digest
                == text(graph, interner, s, "p4_expected_reservation_digest").unwrap_or_default()
            && stored_node(graph, interner, s, "p4_action_reservation_node")
                .and_then(|reservation| text(graph, interner, reservation, "p4_reservation_digest"))
                .as_deref()
                == Some(outcome.reservation_digest.as_str())
            && outcome.snapshot_digest == input.snapshot_digest.clone().unwrap_or_default()
            && Some(outcome.sequence) == expected_sequence
            && input.parent_receipt.as_deref() == Some(outcome.outcome_receipt_digest.as_str())
            && input.selection_digest.as_deref() == outcome.selection_digest.as_deref()
            && input.arm_digest.as_deref() == outcome.arm_digest.as_deref()
            && [
                &outcome.proposal_digest,
                &outcome.proposal_receipt_digest,
                &outcome.grant_receipt_digest,
                &outcome.broker_receipt_digest,
                &outcome.replan_receipt_digest,
                &outcome.snapshot_digest,
                &outcome.reservation_digest,
                &outcome.outcome_receipt_digest,
            ]
            .iter()
            .all(|d| valid_digest(d));
        if !valid {
            return impasse(
                graph,
                interner,
                input.logical_time,
                "unbound_or_out_of_order_action_outcome",
            );
        };
        advance_stamp(graph, interner, s, &input);
        set_phase(graph, interner, s, 4);
        return P4Decision::Complete;
    }
    if p == 3 {
        return impasse(
            graph,
            interner,
            input.logical_time,
            "action_outcome_required",
        );
    }
    P4Decision::AwaitOutcome
}

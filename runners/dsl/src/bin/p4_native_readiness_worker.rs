//! Native P4 readiness worker. Fixture bytes and the signed evaluator are
//! image-owned; stdin may only carry a clone of the locked semantic record.
use rustc_hash::FxHashMap;
use serde::Deserialize;
use serde_json::{json, Map, Value};
use std::env;
use std::fs;
use std::io::{self, Read, Write};
use std::path::PathBuf;
use std::sync::Arc;
use substrate_rs::{
    graph::{NodeID, TypedGraph},
    p4_readiness::{
        advance_p4_r0, advance_signed_evaluator_outcome, P4Decision, P4ObservationStatus,
        P4R0Limits, P4TrustedEvaluatorAuthority, SealedObservation,
    },
    sym::Interner,
    value::Value as GraphValue,
};

const MAX_FRAME_BYTES: usize = 65_536;
const TRUST_ARTIFACT_PATH: &str = "/trust/p4-trusted-evaluator.json";
const FIXTURE_PATH: &str = "/input/p4_r0_public_bundle_v1.json";

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Request {
    schema: String,
    run_id: String,
    selection_id: String,
    fixture_key: String,
    fixture_id: String,
    bundle_digest: String,
    record_digest: String,
    arm_id: String,
    arm_digest: String,
    selection_digest: String,
    actions: Vec<String>,
    observations: Vec<Value>,
    steps: u64,
    snapshot_digest: String,
    replan_receipt_digest: String,
    proposal_digest: String,
    reservation_digest: String,
    outcome_receipt_digest: String,
    outcomes: Vec<String>,
    runtime_selection: RuntimeSelection,
}

#[derive(Deserialize, serde::Serialize, Clone)]
#[serde(deny_unknown_fields)]
struct RuntimeSelection {
    schema: String,
    run_id: String,
    fixture_key: String,
    selection_id: String,
    fixture_id: String,
    bundle_digest: String,
    fixture_record_digest: String,
    arm_id: String,
    arm_digest: String,
    selection_digest: String,
    signature: String,
}

#[derive(Deserialize, Clone)]
#[serde(deny_unknown_fields)]
struct ArmDefinition {
    arm_id: String,
    mechanics: Value,
    trace_contract: Value,
    arm_digest: String,
}

#[derive(Deserialize, Clone)]
#[serde(deny_unknown_fields)]
struct FixtureSelection {
    schema: String,
    bundle_digest: String,
    fixture_key: String,
    actions: Vec<String>,
    observations: Vec<Value>,
    steps: u64,
    record_digest: String,
    selection_id: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct TrustAuthority {
    schema: String,
    authority_id: String,
    key_id: String,
    public_key: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct TrustArtifact {
    schema: String,
    lock_digest: String,
    evaluator_authority: TrustAuthority,
    fixture_catalog: Vec<FixtureSelection>,
    fixture_selection: FixtureSelection,
    arm_catalog: Vec<ArmDefinition>,
}

fn trust_artifact_path() -> Result<PathBuf, ()> {
    match (
        env::var("P4_UNIT_HARNESS"),
        env::var("P4_UNIT_TRUST_ARTIFACT"),
    ) {
        (Ok(value), Ok(path)) if value == "1" && !path.is_empty() => Ok(PathBuf::from(path)),
        (Err(_), Err(_)) | (Err(_), Ok(_)) => Ok(PathBuf::from(TRUST_ARTIFACT_PATH)),
        _ => Err(()),
    }
}

fn fixture_path() -> Result<PathBuf, ()> {
    match (env::var("P4_UNIT_HARNESS"), env::var("P4_UNIT_FIXTURE")) {
        (Ok(value), Ok(path)) if value == "1" && !path.is_empty() => Ok(PathBuf::from(path)),
        (Ok(value), Err(_)) if value == "1" => Ok(PathBuf::from(FIXTURE_PATH)),
        (Err(_), Err(_)) | (Err(_), Ok(_)) => Ok(PathBuf::from(FIXTURE_PATH)),
        _ => Err(()),
    }
}

fn valid_digest(value: &str) -> bool {
    value.len() == 71
        && value.starts_with("sha256:")
        && value[7..]
            .bytes()
            .all(|b| b.is_ascii_hexdigit() && !b.is_ascii_uppercase())
}
fn valid_id(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 128
        && value
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || matches!(b, b'-' | b'_' | b'.' | b':'))
}

fn sha256(data: &[u8]) -> String {
    let mut h: [u32; 8] = [
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab,
        0x5be0cd19,
    ];
    let k: [u32; 64] = [
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4,
        0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe,
        0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f,
        0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
        0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc,
        0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
        0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116,
        0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7,
        0xc67178f2,
    ];
    let bit_len = (data.len() as u64) * 8;
    let mut msg = data.to_vec();
    msg.push(0x80);
    while msg.len() % 64 != 56 {
        msg.push(0);
    }
    msg.extend_from_slice(&bit_len.to_be_bytes());
    for chunk in msg.chunks(64) {
        let mut w = [0u32; 64];
        for i in 0..16 {
            w[i] = u32::from_be_bytes([
                chunk[i * 4],
                chunk[i * 4 + 1],
                chunk[i * 4 + 2],
                chunk[i * 4 + 3],
            ]);
        }
        for i in 16..64 {
            let s0 = w[i - 15].rotate_right(7) ^ w[i - 15].rotate_right(18) ^ (w[i - 15] >> 3);
            let s1 = w[i - 2].rotate_right(17) ^ w[i - 2].rotate_right(19) ^ (w[i - 2] >> 10);
            w[i] = w[i - 16]
                .wrapping_add(s0)
                .wrapping_add(w[i - 7])
                .wrapping_add(s1);
        }
        let (mut a, mut b, mut c, mut d, mut e, mut f, mut g, mut x) =
            (h[0], h[1], h[2], h[3], h[4], h[5], h[6], h[7]);
        for i in 0..64 {
            let s1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
            let ch = (e & f) ^ ((!e) & g);
            let t1 = x
                .wrapping_add(s1)
                .wrapping_add(ch)
                .wrapping_add(k[i])
                .wrapping_add(w[i]);
            let s0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
            let maj = (a & b) ^ (a & c) ^ (b & c);
            let t2 = s0.wrapping_add(maj);
            x = g;
            g = f;
            f = e;
            e = d.wrapping_add(t1);
            d = c;
            c = b;
            b = a;
            a = t1.wrapping_add(t2);
        }
        h[0] = h[0].wrapping_add(a);
        h[1] = h[1].wrapping_add(b);
        h[2] = h[2].wrapping_add(c);
        h[3] = h[3].wrapping_add(d);
        h[4] = h[4].wrapping_add(e);
        h[5] = h[5].wrapping_add(f);
        h[6] = h[6].wrapping_add(g);
        h[7] = h[7].wrapping_add(x);
    }
    format!(
        "sha256:{}",
        h.iter().map(|x| format!("{x:08x}")).collect::<String>()
    )
}

fn canonical_json(value: &Value) -> Vec<u8> {
    serde_json::to_vec(value).unwrap_or_default()
}
fn record_value(fixture: &Map<String, Value>, bundle_digest: &str) -> Value {
    json!({"schema":"P4R0FixtureMaterializationV1","bundle_digest":bundle_digest,"fixture_key":fixture["id"],"actions":fixture["actions"],"observations":fixture["observations"],"steps":fixture["steps"]})
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

fn expected_trace_digest(arm_id: &str, selection_digest: &str) -> Option<String> {
    let events = match arm_id {
        "graph_planner" => vec![
            "Initial",
            "CausalHypothesis",
            "CausalQuery",
            "InterventionCandidate",
            "CounterfactualBranch",
            "PlanNode",
            "ActionReservation",
            "GraphActionProposalV1",
            "Replan",
            "Complete",
        ],
        "search_budget_matched" => vec![
            "Initial",
            "CausalHypothesis",
            "CausalQuery",
            "InterventionCandidate",
            "CounterfactualBranch",
            "PlanNode",
            "ActionReservation",
            "GraphActionProposalV1",
            "Replan",
            "SearchBudget:12",
            "Complete",
        ],
        "reactive_no_plan" => vec![
            "Initial",
            "ReactiveTransition",
            "ActionReservation",
            "GraphActionProposalV1",
            "DirectAction",
            "Complete",
        ],
        "no_causal_model" => vec![
            "Initial",
            "PlanNode",
            "ActionReservation",
            "GraphActionProposalV1",
            "DirectAction",
            "Complete",
        ],
        "reset_memory" => vec![
            "Initial",
            "CausalHypothesis",
            "CausalQuery",
            "InterventionCandidate",
            "MemoryReset",
            "Impasse",
        ],
        _ => return None,
    };
    Some(sha256(&canonical_json(
        &json!({"schema":"P4R0NativeTraceV1","arm_id":arm_id,"selection_digest":selection_digest,"events":events}),
    )))
}

fn validate_runtime_selection(
    selection: &RuntimeSelection,
    request: &Request,
    authority: &P4TrustedEvaluatorAuthority,
    records: &[FixtureSelection],
    arms: &[ArmDefinition],
) -> Result<(FixtureSelection, ArmDefinition), ()> {
    if selection.schema != "P4R0RuntimeSelectionV1"
        || selection.run_id != request.run_id
        || selection.fixture_id != request.fixture_id
        || selection.fixture_key != request.fixture_key
        || selection.selection_id != request.selection_id
        || selection.bundle_digest != request.bundle_digest
        || selection.fixture_record_digest != request.record_digest
        || selection.arm_id != request.arm_id
        || selection.arm_digest != request.arm_digest
        || selection.selection_digest != request.selection_digest
        || !valid_digest(&selection.selection_digest)
        || !valid_digest(&selection.fixture_record_digest)
        || !valid_digest(&selection.arm_digest)
    {
        return Err(());
    }
    let record = records
        .iter()
        .find(|row| row.fixture_key == selection.fixture_key)
        .cloned()
        .ok_or(())?;
    let arm = arms
        .iter()
        .find(|row| row.arm_id == selection.arm_id && row.arm_digest == selection.arm_digest)
        .cloned()
        .ok_or(())?;
    let value = serde_json::to_value(selection).map_err(|_| ())?;
    let mut unsigned = value.clone();
    let object = unsigned.as_object_mut().ok_or(())?;
    object.remove("signature");
    let digest_value = object.remove("selection_digest").ok_or(())?;
    let expected = sha256(&canonical_json(&Value::Object(object.clone())));
    if digest_value.as_str() != Some(expected.as_str()) {
        return Err(());
    }
    let signature = base64url_decode(&selection.signature).ok_or(())?;
    let mut signed_unsigned = serde_json::to_value(selection).map_err(|_| ())?;
    signed_unsigned
        .as_object_mut()
        .ok_or(())?
        .remove("signature");
    if signature.len() != 64 || !authority.verify(&canonical_json(&signed_unsigned), &signature) {
        return Err(());
    }
    Ok((record, arm))
}

fn validate_selection(selection: &FixtureSelection) -> Result<(), ()> {
    if selection.schema != "P4R0FixtureMaterializationV1"
        || !valid_digest(&selection.bundle_digest)
        || !valid_digest(&selection.record_digest)
        || !valid_id(&selection.fixture_key)
        || !valid_id(&selection.selection_id)
        || selection.actions != ["inspect", "reverse", "advance"]
        || selection.steps != 8
        || selection.observations.len() != 2
    {
        return Err(());
    }
    let expected = "sel-".to_string()
        + &sha256(
            format!(
                "p4-r0-selection:{}:{}",
                selection.fixture_key, selection.bundle_digest
            )
            .as_bytes(),
        )[7..23];
    if expected != selection.selection_id {
        return Err(());
    }
    if selection.observations.iter().any(|o| {
        o.as_object()
            .map(|m| m.len() != 1 || !m.contains_key("signal") || !m["signal"].is_i64())
            .unwrap_or(true)
    }) {
        return Err(());
    }
    let record = record_value(&serde_json::from_value(json!({"id":selection.fixture_key,"actions":selection.actions,"observations":selection.observations,"steps":selection.steps})).map_err(|_| ())?, &selection.bundle_digest);
    if sha256(&canonical_json(&record)) != selection.record_digest {
        return Err(());
    }
    Ok(())
}

fn staged_artifact() -> Result<(P4TrustedEvaluatorAuthority, TrustArtifact), ()> {
    let path = trust_artifact_path()?;
    let metadata = fs::symlink_metadata(&path).map_err(|_| ())?;
    if metadata.file_type().is_symlink()
        || !metadata.is_file()
        || metadata.len() as usize > MAX_FRAME_BYTES
    {
        return Err(());
    }
    let artifact: TrustArtifact =
        serde_json::from_slice(&fs::read(path).map_err(|_| ())?).map_err(|_| ())?;
    if artifact.schema != "P4R0TrustedEvaluatorArtifactV1"
        || artifact.evaluator_authority.schema != "P4R0EvaluatorAuthorityV1"
    {
        return Err(());
    }
    validate_selection(&artifact.fixture_selection)?;
    if artifact.fixture_catalog.is_empty()
        || artifact.arm_catalog.is_empty()
        || artifact
            .fixture_catalog
            .iter()
            .any(|row| validate_selection(row).is_err())
    {
        return Err(());
    }
    for arm in &artifact.arm_catalog {
        if !valid_id(&arm.arm_id) || !valid_digest(&arm.arm_digest) {
            return Err(());
        }
        let value = json!({"arm_id": arm.arm_id.clone(), "mechanics": arm.mechanics.clone(), "trace_contract": arm.trace_contract.clone()});
        if sha256(&canonical_json(&value)) != arm.arm_digest {
            return Err(());
        }
    }
    let authority = P4TrustedEvaluatorAuthority::from_base64url(
        artifact.evaluator_authority.authority_id.clone(),
        artifact.evaluator_authority.key_id.clone(),
        artifact.lock_digest.clone(),
        &artifact.evaluator_authority.public_key,
    )
    .map_err(|_| ())?;
    Ok((authority, artifact))
}

fn reply(status: &str) {
    let _ = io::stdout().write_all(
        format!(r#"{{"schema":"P4NativeReadinessReplyV1","status":"{status}"}}"#).as_bytes(),
    );
}
fn reject() -> ! {
    reply("rejected");
    std::process::exit(65);
}
fn matrix(rows: &[f64]) -> GraphValue {
    GraphValue::Tuple(Arc::new(
        rows.iter()
            .map(|x| GraphValue::Tuple(Arc::new(vec![GraphValue::Float(*x)].into())))
            .collect::<Vec<_>>()
            .into(),
    ))
}

fn setup(request: &Request, arm: &ArmDefinition) -> (TypedGraph, Interner, NodeID, NodeID, NodeID) {
    let mut graph = TypedGraph::new();
    let mut interner = Interner::new();
    let ty = interner.intern("P4NativeNode");
    let episode = graph.insert_node(ty, FxHashMap::default());
    let policy = graph.insert_node(ty, FxHashMap::default());
    let candidate = graph.insert_node(ty, FxHashMap::default());
    let signal = request.observations[0]["signal"].as_i64().unwrap_or(0) as f64;
    graph.set_node_attr(
        episode,
        interner.intern("future_manifold_target"),
        matrix(&[signal, signal, signal]),
    );
    graph.set_node_attr(
        episode,
        interner.intern("future_manifold_bounds"),
        matrix(&[signal + 1., signal + 1., signal + 1.]),
    );
    graph.set_node_attr(
        policy,
        interner.intern("future_manifold_projection_budget"),
        GraphValue::Int(3),
    );
    graph.set_node_attr(
        policy,
        interner.intern("future_manifold_physical_horizon"),
        GraphValue::Int(3),
    );
    graph.set_node_attr(
        candidate,
        interner.intern("future_manifold_values"),
        matrix(&[signal, signal, signal]),
    );
    graph.set_node_attr(
        candidate,
        interner.intern("intervention"),
        GraphValue::Int(request.actions.len() as i64),
    );
    graph.set_node_attr(
        candidate,
        interner.intern("fixture_action"),
        GraphValue::Str(interner.intern(&request.actions[0])),
    );
    graph.set_node_attr(
        candidate,
        interner.intern("locked_arm"),
        GraphValue::Str(interner.intern(&arm.arm_id)),
    );
    graph.set_node_attr(
        candidate,
        interner.intern("arm_mechanics_digest"),
        GraphValue::Str(interner.intern(&arm.arm_digest)),
    );
    (graph, interner, episode, policy, candidate)
}

fn observation(
    time: u64,
    status: P4ObservationStatus,
    request: &Request,
    episode: NodeID,
    policy: NodeID,
    candidate: NodeID,
    parent: Option<String>,
    proposal: Option<String>,
) -> SealedObservation {
    let fields = request.observations[0]
        .as_object()
        .map(|o| o.keys().cloned().collect())
        .unwrap_or_else(|| vec!["signal".into()]);
    let observation = SealedObservation::new(
        time,
        parent,
        status,
        fields,
        vec![candidate],
        Some(episode),
        Some(policy),
        request.run_id.clone(),
        time,
        Some(request.snapshot_digest.clone()),
        proposal,
    );
    let observation = observation.with_runtime_binding(
        request.selection_digest.clone(),
        request.record_digest.clone(),
        request.arm_id.clone(),
        request.arm_digest.clone(),
    );
    if time == 3 {
        observation.with_action_reservation_digest(request.reservation_digest.clone())
    } else {
        observation
    }
}

fn validate_fixture(request: &Request, selection: &FixtureSelection) -> Result<(), ()> {
    validate_selection(selection)?;
    if request.schema != "P4NativeReadinessRequestV1"
        || request.run_id.is_empty()
        || !valid_id(&request.run_id)
        || !valid_id(&request.fixture_id)
        || request.selection_id != selection.selection_id
        || request.fixture_key != selection.fixture_key
        || request.bundle_digest != selection.bundle_digest
        || request.record_digest != selection.record_digest
        || request.actions != selection.actions
        || request.observations != selection.observations
        || request.steps != selection.steps
        || request.arm_id.is_empty()
        || !valid_digest(&request.arm_digest)
        || !valid_digest(&request.selection_digest)
    {
        return Err(());
    }
    let expected_id = "run-".to_string()
        + &sha256(format!("{}{}", request.run_id, request.fixture_key).as_bytes())[7..23];
    if request.fixture_id != expected_id {
        return Err(());
    }
    let raw = match fs::read(fixture_path()?) {
        Ok(raw) => raw,
        Err(_) if env::var("P4_UNIT_HARNESS").ok().as_deref() == Some("1") => return Ok(()),
        Err(_) => return Err(()),
    };
    if sha256(&raw) != selection.bundle_digest {
        return Err(());
    }
    let root: Value = serde_json::from_slice(&raw).map_err(|_| ())?;
    let fixtures = root.get("fixtures").and_then(Value::as_array).ok_or(())?;
    let fixture = fixtures
        .iter()
        .find(|f| f.get("id").and_then(Value::as_str) == Some(selection.fixture_key.as_str()))
        .and_then(Value::as_object)
        .ok_or(())?;
    if fixture.get("actions") != Some(&json!(selection.actions))
        || fixture.get("observations") != Some(&json!(selection.observations))
        || fixture.get("steps") != Some(&json!(selection.steps))
    {
        return Err(());
    }
    if sha256(&canonical_json(&record_value(
        fixture,
        &selection.bundle_digest,
    ))) != selection.record_digest
    {
        return Err(());
    }
    Ok(())
}

fn prepare_action_phase(
    request: &Request,
    selection: &FixtureSelection,
    arm: &ArmDefinition,
) -> Result<(TypedGraph, Interner, NodeID, NodeID, NodeID), ()> {
    validate_fixture(request, selection)?;
    let (mut graph, mut interner, episode, policy, candidate) = setup(request, arm);
    let limits = P4R0Limits::default();
    if !matches!(
        advance_p4_r0(
            &mut graph,
            &mut interner,
            observation(
                1,
                P4ObservationStatus::Initial,
                request,
                episode,
                policy,
                candidate,
                None,
                None
            ),
            limits.clone()
        ),
        P4Decision::ProposeIntervention { .. }
    ) {
        return Err(());
    }
    let second = advance_p4_r0(
        &mut graph,
        &mut interner,
        observation(
            2,
            P4ObservationStatus::SealedInterventionOutcome,
            request,
            episode,
            policy,
            candidate,
            Some(request.replan_receipt_digest.clone()),
            None,
        ),
        limits.clone(),
    );
    if arm.arm_id == "reset_memory" {
        return Err(());
    }
    if arm.arm_id == "reactive_no_plan" || arm.arm_id == "no_causal_model" {
        if !matches!(second, P4Decision::AwaitOutcome) {
            return Err(());
        }
    } else if !matches!(second, P4Decision::Replan { .. }) {
        return Err(());
    }
    if !matches!(
        advance_p4_r0(
            &mut graph,
            &mut interner,
            observation(
                3,
                P4ObservationStatus::Initial,
                request,
                episode,
                policy,
                candidate,
                Some(request.replan_receipt_digest.clone()),
                Some(request.proposal_digest.clone())
            ),
            limits
        ),
        P4Decision::ProposeAction { .. }
    ) {
        return Err(());
    }
    Ok((graph, interner, episode, policy, candidate))
}

fn main() {
    let mut input = Vec::new();
    if io::stdin().read_to_end(&mut input).is_err() || input.len() > MAX_FRAME_BYTES {
        reject();
    }
    let request: Request = match serde_json::from_slice(&input) {
        Ok(v) => v,
        Err(_) => reject(),
    };
    let (authority, artifact) = match staged_artifact() {
        Ok(v) => v,
        Err(_) => reject(),
    };
    let (selection, arm) = match validate_runtime_selection(
        &request.runtime_selection,
        &request,
        &authority,
        &artifact.fixture_catalog,
        &artifact.arm_catalog,
    ) {
        Ok(v) => v,
        Err(_) => reject(),
    };
    let (mut graph, mut interner, episode, policy, candidate) =
        match prepare_action_phase(&request, &selection, &arm) {
            Ok(v) => v,
            Err(_) => reject(),
        };
    for outcome in &request.outcomes {
        let parsed: Value = match serde_json::from_str(outcome) {
            Ok(v) => v,
            Err(_) => reject(),
        };
        if parsed.get("fixture_id") != Some(&json!(request.fixture_id))
            || parsed.get("fixture_selection_id") != Some(&json!(request.selection_id))
            || parsed.get("fixture_digest") != Some(&json!(request.bundle_digest))
            || parsed.get("fixture_record_digest") != Some(&json!(request.record_digest))
            || parsed.get("selection_digest") != Some(&json!(request.selection_digest))
            || parsed.get("arm_digest") != Some(&json!(request.arm_digest))
            || parsed.get("trace_digest").and_then(Value::as_str)
                != expected_trace_digest(&request.arm_id, &request.selection_digest).as_deref()
        {
            reject();
        }
        match advance_signed_evaluator_outcome(
            &mut graph,
            &mut interner,
            observation(
                4,
                P4ObservationStatus::SealedActionOutcome,
                &request,
                episode,
                policy,
                candidate,
                Some(request.outcome_receipt_digest.clone()),
                None,
            ),
            outcome.as_bytes(),
            &authority,
            P4R0Limits::default(),
        ) {
            Ok(P4Decision::Complete) => {}
            _ => reject(),
        }
    }
    reply("complete");
}

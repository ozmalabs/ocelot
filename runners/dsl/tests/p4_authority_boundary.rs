use std::{env, fs, process::Command};

#[test]
fn direct_callers_cannot_construct_or_deserialize_completion_capabilities() {
    let root = env::temp_dir().join(format!("p4-authority-boundary-{}", std::process::id()));
    let _ = fs::remove_dir_all(&root);
    fs::create_dir_all(root.join("src")).expect("fixture directory");
    fs::write(
        root.join("Cargo.toml"),
        format!(
            "[package]\nname = \"p4-authority-boundary\"\nversion = \"0.0.0\"\nedition = \"2021\"\n\n[dependencies]\nsubstrate-rs = {{ path = {:?} }}\n",
            env!("CARGO_MANIFEST_DIR")
        ),
    )
    .expect("fixture manifest");
    fs::write(
        root.join("src/main.rs"),
        "use substrate_rs::p4_readiness::VerifiedActionOutcome;\nfn main() { let _ = VerifiedActionOutcome { run_id: String::new(), proposal_digest: String::new(), proposal_receipt_digest: String::new(), grant_receipt_digest: String::new(), broker_receipt_digest: String::new(), sequence: 0, snapshot_digest: String::new(), reservation_digest: String::new(), outcome_receipt_digest: String::new(), success: true }; }\n",
    )
    .expect("fixture source");
    let output = Command::new("cargo")
        .args(["check", "--offline"])
        .current_dir(&root)
        .output()
        .expect("cargo is available");
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(
        !output.status.success(),
        "direct construction unexpectedly compiled"
    );
    assert!(
        stderr.contains("private field"),
        "unexpected compile error: {stderr}"
    );
    fs::remove_dir_all(root).expect("fixture cleanup");
}

#[test]
fn direct_callers_cannot_convert_or_deserialize_transport_into_completion_capability() {
    let root = env::temp_dir().join(format!("p4-transport-bypass-{}", std::process::id()));
    let _ = fs::remove_dir_all(&root);
    fs::create_dir_all(root.join("src")).expect("fixture directory");
    fs::write(
        root.join("Cargo.toml"),
        format!(
            "[package]\nname = \"p4-transport-bypass\"\nversion = \"0.0.0\"\nedition = \"2021\"\n\n[dependencies]\nsubstrate-rs = {{ path = {:?} }}\nserde_json = \"1.0\"\n",
            env!("CARGO_MANIFEST_DIR")
        ),
    )
    .expect("fixture manifest");
    fs::write(
        root.join("src/main.rs"),
        "use substrate_rs::p4_readiness::{EvaluatorOutcomeTransport, VerifiedActionOutcome};\nfn main() {\n    let transport = EvaluatorOutcomeTransport { run_id: String::new(), proposal_digest: String::new(), proposal_receipt_digest: String::new(), grant_receipt_digest: String::new(), replan_receipt_digest: String::new(), broker_receipt_digest: String::new(), sequence: 0, snapshot_digest: String::new(), reservation_digest: String::new(), outcome_receipt_digest: String::new(), success: true };\n    let _: VerifiedActionOutcome = transport.into();\n    let _ = serde_json::from_str::<VerifiedActionOutcome>(\"{}\");\n}\n",
    )
    .expect("fixture source");
    let output = Command::new("cargo")
        .args(["check", "--offline"])
        .current_dir(&root)
        .output()
        .expect("cargo is available");
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(
        !output.status.success(),
        "transport bypass unexpectedly compiled"
    );
    assert!(
        stderr.contains("From<EvaluatorOutcomeTransport>") || stderr.contains("Deserialize"),
        "unexpected compile error: {stderr}"
    );
    fs::remove_dir_all(root).expect("fixture cleanup");
}

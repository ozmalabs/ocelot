# Confidential Space probe WIP evidence — 2026-09-17

Diagnostic-only record. This is not production custody, a release, or a GO result. The workload ran from a Confidential Space **debug** image (`dbgstat=enabled`).

## Image

- Reference: `us-east1-docker.pkg.dev/ocelot-proof/p5-cs/cs-attestation-probe:20260917-v10`
- Immutable image digest: `sha256:9a3341ed5d1dce05c58fb9507c1eff85783d6f1bf8696af43b9af2284ca6ac55`
- WIP expected-image digest was updated to the same immutable digest in VM metadata.
- The image was built from the split-tail probe source after 15 targeted tests, compileall, and whitespace checks passed.

## VM and network evidence

- Project: `ocelot-proof` (project number `141633828616`)
- Zone: `us-east1-b`
- Machine: `n2d-standard-2`, Confidential Instance Type `SEV`
- Subnet: `default`; Private Google Access: `true`
- External IP: none
- Shielded secure boot: `true`; vTPM and integrity monitoring: `true`
- Temporary IAP SSH firewall rule `p5-cs-debug-iap-ssh` was removed during cleanup.

## Real launcher claim evidence (redacted)

The serial log contained a real launcher background attestation claim map. No JWT, token body, private key, or nonce value was written here.

- `iss`: `https://confidentialcomputing.googleapis.com`
- background-token `aud`: `https://sts.googleapis.com`
- `submods.container.image_digest`: matched the WIP digest above
- `submods.gce.project_id`: `ocelot-proof`
- `submods.gce.project_number`: `141633828616`
- `submods.gce.zone`: `us-east1-b`
- `dbgstat`: `enabled` (debug image; not production custody)
- `swname`: `CONFIDENTIAL_SPACE`
- `hwmodel`: `GCP_AMD_SEV`
- `secboot`: `true`

## Probe result and limits

The probe made a real `/v1/token` launcher request, but the launcher returned `text/html`; the probe failed closed with `CSAttestationProbeV1` error `launcher_header_content_type_text_html`. Therefore:

- nonce-bound probe verification: **not completed**;
- probe-verified audience/issuer/image/project/zone/secureboot/TEE evidence: **not claimed**;
- only the redacted background launcher claim evidence above is recorded;
- no production custody, production attestation, WIP exchange, or GO claim is made.

## Cleanup

The temporary VM `p5-cs-attestation-probe` and temporary firewall rule `p5-cs-debug-iap-ssh` were deleted. No debug VM or temporary debug firewall remains.

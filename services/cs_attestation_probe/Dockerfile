FROM python:3.12.8-slim-bookworm@sha256:2199a62885a12290dc9c5be3ca0681d367576ab7bf037da120e564723292a2f0

# Only the non-secret expected digest and token verification values are overridable.
# Production startup evidence is allowed through serial/Cloud Logging for this probe.
LABEL tee.launch_policy.allow_env_override="CS_EXPECTED_IMAGE_DIGEST,CS_ATTESTATION_AUDIENCE,CS_ATTESTATION_ISSUER,CS_WIP_PROVIDER"
LABEL tee.launch_policy.log_redirect="always"

RUN pip install --no-cache-dir google-auth==2.38.0 requests==2.32.3 PyJWT==2.9.0 cryptography==43.0.3

COPY probe.py /probe.py
USER 65532:65532
ENTRYPOINT ["python3", "/probe.py"]

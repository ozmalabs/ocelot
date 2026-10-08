#!/usr/bin/env bash
# Forwarding script to attestation/deploy.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${SCRIPT_DIR}/attestation/deploy.sh" "$@"

# =============================================================================
# QFBench 2.0 Track 2 forecaster — PHASE 4 container.
#
# Contract [PHASE0_GROUND_TRUTH.md §1, SUBMISSION_CLI.md]:
#   docker run --rm --network=none|qfb2-eval --cpus=N --memory=M \
#     -v <unit-dir>:/input:ro -v <run>/output:/output \
#     <IMAGE> forecast --panels /input/panels/ --text /input/text/ \
#                      --asof <YYYY-MM-DD> --out /output/forecast.parquet
#
# Design choices, each tied to a contract fact:
#   * Base python:3.13-slim  — qfbench2-common 2.3.1 requires Python >=3.13
#     (PHASE0 §10). "slim" keeps the image small; the phase clock bills a
#     90-187s COLD IMAGE PULL per unit (PHASE0 resources), so image size is a
#     first-order budget lever.
#   * qfbench2-common @ v2.3.1 from the toolkit git URL — the guide flags that
#     omitting it is the ModuleNotFoundError: qfbench2_common failure mode
#     (PHASE0 §10). jsonschema is a PRODUCTION dep (g1 fail-closes without it).
#   * substrate_rs is installed from a PREBUILT abi3 wheel (COPY + pip install),
#     NOT built in-image. Rationale below (see "SUBSTRATE_RS BUILD").
#   * `forecast` is a thin launcher on PATH with NO ENTRYPOINT — so the harness's
#     `<IMAGE> forecast ...` runs it as the container command (PHASE0 §1: "Build
#     with no ENTRYPOINT and put `forecast` on PATH"). The launcher ALSO accepts
#     a leading positional "forecast" so an ENTRYPOINT-style call still works.
#   * LABEL qfbench2.interface_version="2.0" is REQUIRED (PHASE0 §1).
#   * No CUDA / torch layer: the shipped arm is CPU-only and needs no GPU
#     (PHASE0 offline-smoke requirement "NO GPU present").
#
# ---------------------------------------------------------------------------
# SUBSTRATE_RS BUILD — lightest viable path (documented per the task).
# ---------------------------------------------------------------------------
# The OCELOT substrate is a Rust crate (runners/dsl, crate `substrate_rs`,
# built with maturin). A FULL in-image Rust build would be:
#     cd runners/dsl && maturin develop --release      # (or `maturin build`)
# but that is TOO HEAVY for this image:
#   - it requires the Rust toolchain (rustc+cargo+~/.cargo, ~1.5 GB) in the
#     build stage, ballooning the image / build cache;
#   - the release profile is LTO=fat, codegen-units=1 (Cargo.toml [profile.release]),
#     which MEASURED at 2m41s on this machine — added to EVERY docker build;
#   - it drags the crate's heavy optional deps (wgpu, dynasm, rustfft, ...).
# The crate already emits an ABI3 wheel (`crate-type=cdylib`, pyo3 abi3-py39),
# so ONE wheel (substrate_rs-*-cp39-abi3-*.whl, ~4.3 MB) works on any CPython
# >=3.9. The lightest viable path is therefore: build the wheel ONCE outside the
# image (see docker/build.sh) and COPY + `pip install` it here. Zero Rust in the
# image, ~4 MB added, no per-build compile.
#
# If a self-contained in-image build is ever required, use a multi-stage build
# with `rust:1-slim` + `pip install maturin` in a builder stage, run
# `maturin build --release -m runners/dsl/Cargo.toml`, and COPY only the wheel
# into this runtime stage — keeping the Rust toolchain OUT of the final image.
#
# NOTE: the SHIPPED forecast arm (JointDrawEngine + rules text) does NOT import
# substrate_rs — only the optional TimeInfer-centering study arm does. substrate
# is installed so that arm is available and the image is a faithful OCELOT
# runtime, but the container is admissible and fully functional without it.
# =============================================================================
FROM python:3.13-slim

# git is needed ONLY to pip-install qfbench2-common from its VCS URL. Installed
# in the same layer and left in place (slim base; removing git saves little and
# a rebuild would need it). Network is available at BUILD time; it is the RUN
# time that is --network=none.
RUN apt-get update \
 && apt-get install -y --no-install-recommends git \
 && rm -rf /var/lib/apt/lists/*

# Pinned Python deps (PHASE0 §10 version floors). qfbench2-common pulls
# numpy/scipy/jsonschema; we add pandas+pyarrow (its `data` extra) explicitly.
RUN pip install --no-cache-dir \
      "numpy>=2.1" \
      "pandas>=2.2" \
      "pyarrow>=18" \
      "jsonschema>=4.21" \
      "scipy>=1.11"

# qfbench2-common @ v2.3.1 — REQUIRED (else ModuleNotFoundError: qfbench2_common).
# Pin the exact tag (first tag carrying qfbench2_common.contracts). The `[data]`
# extra adds pandas/pyarrow floors; harmless with the pins above.
RUN pip install --no-cache-dir \
      "qfbench2-common[data] @ git+https://github.com/Agenthon-2026/Agenthon2026-public.git@v2.3.1#subdirectory=common"

# OCELOT substrate — prebuilt abi3 wheel (see SUBSTRATE_RS BUILD above).
COPY wheels/ /tmp/wheels/
RUN pip install --no-cache-dir /tmp/wheels/substrate_rs-*.whl \
 && rm -rf /tmp/wheels

# Application code. Self-contained under /app/qfb2t2 so imports do not depend on
# the repo's relative ../seldon_t2_poc layout.
WORKDIR /app
COPY app/ /app/qfb2t2/
# `forecast` launcher on PATH (no ENTRYPOINT).
COPY bin/forecast /usr/local/bin/forecast
RUN chmod +x /usr/local/bin/forecast

ENV PYTHONPATH=/app/qfb2t2
# Default text arm is rules-only (network-free floor). Override with
# QFB2_TEXT_ARM=model + MODEL_ENDPOINT at run time for the house-endpoint arm.
ENV QFB2_TEXT_ARM=rules
# Keep BLAS single-threaded-ish by default; the harness sets --cpus. (Optional.)
ENV PYTHONUNBUFFERED=1

LABEL qfbench2.interface_version="2.0"
LABEL org.opencontainers.image.title="qfbench2-track2-ocelot-forecaster"
LABEL org.opencontainers.image.description="OCELOT reachable-set + confidence, joint manifold; rules-only text floor; MODEL_ENDPOINT arm via proxy."

# NO ENTRYPOINT — the harness supplies `forecast ...` as the container command.
# Provide a sane default CMD so `docker run <img>` alone prints usage.
CMD ["forecast", "--help"]

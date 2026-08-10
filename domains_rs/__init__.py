"""Rust-backed domain implementations.

Each module here mirrors a `domains/` Python file but builds its
substrate on `substrate_rs`. Behaviour is parity-pinned via the
parallel test suite; the only differences are performance and (where
useful) the new Term variants from `substrate_rs.ext`.
"""

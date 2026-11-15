"""Ocelot compatibility facade for the Ozagia research service.

The service implementation lives in ``ozagia.research.service``. This facade
injects Ocelot's engine and seed provenance adapters and keeps the established
module-level monkeypatch points used by Ocelot tests and local integrations.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ozagia.research.graph import ResearchError
from ozagia.research.service import ResearchService as _ResearchService
from scripts import ocelot_research_provenance as _ocelot_provenance


def engine_preamble(*args, **kwargs):
    from domains.engine_provenance import engine_preamble as callback
    return callback(*args, **kwargs)


def provenance_stamp(*args, **kwargs):
    from domains.engine_provenance import provenance_stamp as callback
    return callback(*args, **kwargs)


def lean_executable(*args, **kwargs):
    """Return Ocelot's pinned local Lean binary, when it is installed."""
    from domains.engine_provenance import THIS_TREE
    executable = (Path(THIS_TREE) / "var/tools/lean/lean-4.33.1-linux/bin/lean")
    return str(executable) if executable.is_file() else None


# These module-level references intentionally remain patchable by existing
# tests and callers before constructing ResearchService.
verify_engine_provenance = _ocelot_provenance.verify_engine_provenance
verify_prereg = _ocelot_provenance.verify_prereg
verify_prereg_git = _ocelot_provenance.verify_prereg_git


class ResearchService(_ResearchService):
    """Migrated service with Ocelot-specific callbacks injected."""

    def __init__(self, workspace: str | Path = "."):
        super().__init__(
            workspace,
            # Resolve these globals when called, so monkeypatches made after
            # service construction retain the legacy behavior too.
            engine_preamble=lambda: engine_preamble(),
            provenance_stamp=lambda: provenance_stamp(),
            verify_engine_provenance=lambda *a, **kw: verify_engine_provenance(*a, **kw),
            verify_prereg=lambda *a, **kw: verify_prereg(*a, **kw),
            verify_prereg_git=lambda *a, **kw: verify_prereg_git(*a, **kw),
            lean_executable=lambda: lean_executable(),
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ocelot research helper; arguments and output are JSON.")
    parser.add_argument("operation", choices=[
        "init", "context", "native_graph", "paper_preview", "paper_ingest",
        "formula_parse_candidates", "formula_resolve", "formula_translate",
        "formula_model", "model_candidate", "record", "link", "inspect",
        "trace", "execute", "export_lean", "check_lean", "check", "export",
    ])
    parser.add_argument("--workspace", default=".",
                        help="Workspace containing Ocelot research state")
    parser.add_argument("--args", default="{}",
                        help="JSON object of operation arguments")
    parser.add_argument("--lean", action="store_true",
                        help="For export_lean, print Lean source rather than JSON")
    options = parser.parse_args(argv)
    try:
        args = json.loads(options.args)
        if not isinstance(args, dict):
            raise ValueError("--args must be a JSON object")
        result = ResearchService(options.workspace).call(options.operation, args)
        if options.lean:
            if options.operation != "export_lean":
                raise ValueError("--lean requires export_lean")
            print(result["lean"], end="")
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, KeyError, ResearchError, OSError) as exc:
        parser.exit(2, f"{type(exc).__name__}: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Self-report route contrast panel v1.2 amendment: lock imported script modules

Date: 2026-09-27

## Reason for amendment

After v1.1 added the Wiktionary/reference slabs, an execution trace found another omitted runtime dependency: `domains/conversation_action.py` imports `collapse_engine` from `scripts/collapse_engine.py`. That module was absent in the compact snapshot. The adapter catches the resulting `ModuleNotFoundError` around the action bridge, so the Message can be marked `instruction_outcome="handled"` even though the held action never ran. The v1.1 no-response outcomes for request actions therefore cannot establish fully provisioned execution behavior.

## Corrected snapshot and protocol

V1.2 uses the same code/seed/slab state as the v1.1 capture, and includes the full `scripts/` tree. The runner hashes every `scripts/**/*.py` file (excluding `__pycache__`) at driver and worker boundaries, in addition to the original source/seed closure and all `data/slabs/*` hashes. It reruns the same ten stimuli in 30 fresh processes. This includes `collapse_engine.py` and any sibling modules imported through the script path.

V1 and v1.1 remain as provenance records of successive snapshot-closure omissions. Do not use their route or reply outcomes as evidence about the fully provisioned capability. The v1.2 report is authoritative only for its complete lock.

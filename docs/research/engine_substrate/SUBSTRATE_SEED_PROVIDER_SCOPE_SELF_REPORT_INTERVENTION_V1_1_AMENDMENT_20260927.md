# Seed provider-scope / self-report intervention v1.1 amendment

Date: 2026-09-27

During preparation, the worktree's `boot_all.py` continued to change by adding content-selection and scaffold-retention hunks. The intermediate whole-file version at SHA `6662935bceb89af91cb86a402273045e579a20120e134cf74b7919f2c0fc7b22` is preserved exactly as `boot_all_provider_scope_only_20260927.py`; comparison against the baseline confirms it differs by only the typed-provider selection hunk. v1.1 therefore tests that exact historical version as the second condition. Later worktree versions with the extra content-selection/scaffold changes are outside this intervention.

This amendment narrows the intervention to the available locked baseline (`boot_all.py` SHA `9b9c2ac025f0fea54a9b463e818737e7d765bcce351d69a0572b9ede746bf494`) versus that baseline with only the typed-provider selection hunk applied (SHA `6662935bceb89af91cb86a402273045e579a20120e134cf74b7919f2c0fc7b22`). Both conditions use the same frozen source tree, seeds, native extension, and request. Three fresh workers per condition are interleaved. The later worktree version and its additional content-slicing changes are explicitly outside this causal contrast.

This isolates whether the provider-selection hunk is sufficient to change the route in the baseline context. It cannot attribute behavior of the latest worktree or interactions with subsequent edits. The result supersedes the v1 whole-current-source contrast design; both documents are retained for provenance.

# Scoped audit on/off parity results

**Protocol:** [`SUBSTRATE_SCOPE_AUDIT_ON_OFF_PARITY_PREREG_20260926.md`](SUBSTRATE_SCOPE_AUDIT_ON_OFF_PARITY_PREREG_20260926.md)  
**Runner:** [`substrate_scope_audit_on_off_parity_v1.py`](../../../scripts/substrate_scope_audit_on_off_parity_v1.py)  
**Analysis:** [`substrate_scope_audit_on_off_parity_v1_20260926_analysis.json`](../../../evaluation/reports/substrate_scope_audit_on_off_parity_v1_20260926_analysis.json)

The captured N=64 chain, binary-tree, and star workloads pass all 135 registered checks over 15 topology/repeat instances. Event and full-closure arms have identical final projections, progress/fixed-point outcomes, and notifications with scale audit enabled and disabled. This closes semantic parity for the measured fixture and diagnostic modes.

Instrumentation changes measured time: audit-on/off median ratios range from 1.12× to 1.23× across topology/API combinations. Treat these as descriptive overhead in this short synthetic workload; they do not correct prior instrumented timing comparisons or establish production overhead. Per-rule audit was disabled here so the probe isolates global scale audit.

Limits: N=64, three generated topologies, five repeats, and the exercised scoped/full APIs. This does not prove audit transparency for every engine path or workload. The locked protocol, runner, source/native hashes, and independent gates are recorded in the raw report and analysis.

# Held-topic structural trace capture v1 amendment

Date: 2026-09-28  
Applies to: `SUBSTRATE_HELD_TOPIC_STRUCTURAL_TRACE_CAPTURE_V1_PREREG_20260928.md`

## Baseline source drift

During lock preparation, the accepted v1.6 fingerprint was found to differ from current source: 29 common Python/seed inputs have changed hashes, two seed files were added, and the native extension plus build manifest differ. Changes include `domains/comprehend_text.py`, `domains/conversation_action.py`, `domains/self_model.py`, and communication/conversation seeds. The accepted report remains a historical outcome/structure reference, not a source-identical control.

The fresh capture will lock the complete current base fingerprint and all instrumentation inputs before and after each worker. It will compare task outputs and boundary summaries with the accepted v1.6 report as a current-source replication check, while recording exact baseline/current fingerprint hashes and changed-path inventory. If task or structure outputs differ, preserve and report those differences. No causal instrumentation effect or source-stable v1.6 reproduction may be claimed.

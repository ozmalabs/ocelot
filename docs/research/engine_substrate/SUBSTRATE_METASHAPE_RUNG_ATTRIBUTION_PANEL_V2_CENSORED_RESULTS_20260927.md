# MetaShape rung-attribution panel v2 censored result (2026-09-27)

The first v2 capture is retained as a censored diagnostic. Its eight workers ran across a mid-capture edit to `substrate/boot_all.py`. The source lock found that one FrameBinding worker ran before the edit and the remaining seven ran after it. The parent and worker stability gates failed. The file change alters seed indexing/selection, so no combined or per-family capability conclusion is drawn from this capture. Its 783 MB raw report, 43 MB lock, protocol, runner, and failed integrity output remain preserved for audit.

The full fixed schedule was rerun on a read-only source/runtime snapshot containing the post-edit `boot_all.py`; see [v2.1 results](SUBSTRATE_METASHAPE_RUNG_ATTRIBUTION_PANEL_V2_1_RESULTS_20260927.md). The repeated schedule is labelled a replication because the initial probe's outcomes had been inspected. It is not a new confirmatory sample.

Artifacts: [protocol](SUBSTRATE_METASHAPE_RUNG_ATTRIBUTION_PANEL_V2_PREREG_20260927.md), [raw censored capture](../../../evaluation/reports/metashape_rung_attribution_panel_v2_20260927.json), [original lock](../../../evaluation/substrate_capability/metashape_rung_attribution_panel_v2_lock_20260927.json), [runner](../../../scripts/substrate_metashape_rung_attribution_panel_v2.py).

# Live describe-scene threaded interleaving v1.5 amendment

**Amendment before capture.** V1.4's full-seed capture and work analysis pass under its recorded complete source closure. A later self-report capture found that `substrate/boot_all.py` changed between the two route snapshots; all other source-closure entries and the native artifact match. Therefore the v1.4 scene counts remain valid for their exact source snapshot but cannot be used as a same-source route comparison with the self-report result.

V1.5 repeats the v1.4 two-thread describe-scene schedule and counter instrumentation under the current full-seed source closure. It writes distinct v1.5 lock/raw/analysis artifacts and preserves v1.4 unchanged. The v1.5 capture can be compared descriptively with self-report v1.7 only if the source-closure map, native extension, build manifest, and environment fingerprints match exactly; otherwise each remains a route-specific result without a cross-route comparison.

No semantic or instrumentation changes are made beyond versioned provenance paths. Existing schedule, identity, lifecycle, reply, per-rule counter, and replication gates remain in force.

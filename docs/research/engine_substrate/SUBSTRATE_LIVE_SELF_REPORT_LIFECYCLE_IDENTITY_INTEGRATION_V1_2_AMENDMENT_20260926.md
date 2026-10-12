# Live self-report lifecycle identity integration v1.2 amendment

The v1.1 attempt is retained but is not confirmatory. During its full-seed run, the loader warned that `remove_edge` is not a recognized rule effect and skipped the `resolved` and `blocked` lifecycle rules. The native rule IR spelling is `del_edge`, as confirmed by the parser in `runners/dsl/src/py.rs` and existing seed fixtures. Consequently the lifecycle stayed `executing`; the positive and terminal failure/duplicate-result controls failed, while source stability and identity-link selection controls passed.

V1.2 changes only the seed effect spelling to `del_edge`, updates the lock/amendment fingerprints and writes to new raw/analysis/lock paths. All original positive and five control gates remain unchanged. V1 and v1.1 captures remain preserved and excluded from confirmatory claims.

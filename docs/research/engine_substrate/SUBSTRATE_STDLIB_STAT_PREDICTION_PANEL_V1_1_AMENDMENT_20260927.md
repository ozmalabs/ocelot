# CPython `stat` bounded-composition v1.1 amendment

Date: 2026-09-27  
Status: pre-run source-drift correction.

The v1.1 pre-run full-source lock comparison found changes since the frozen v1 run in four runtime files, not only the two files changed for this intervention:

| Runtime source | v1 baseline SHA-256 | v1.1 candidate SHA-256 |
|---|---|---|
| `domains/ast_to_term.py` | `513f027a1ba7db76e62ed6246db3f1550555c4567511ca7a5670ae7a9ff5f334` | `8700d1b7328c2c50f72addd1fe5dfc2a3c372cc499f2afd86db2e307b0a563b7` |
| `domains/code_reading.py` | `2600de2af40a986e1986cbc42f5a83ce5acbc7e21cd3885e8fd924379e841b02` | `dd67d2942cf956c6e35f848aed4012c3ac072e9ac91d9e6b166e8ca44be57908` |
| `domains/comprehend_text.py` | `dd9b3594f1b0daf1394f2c3bfeac991a0326043e67cec164660066c7e7268022` | `bf0c83faad6829df87fe5a99b7612af87078f774ad93ab054dc16fd26cca179e` |
| `substrate/boot_all.py` | `3309ee30fc1f3f629d21d0554c3a895be5ed4d6e78160be362e5d5996aed82ae` | `be2bf9aaf25298c15ffc337306819ab2ab5bc8ecdfd5f8b82d0b4d8544f4ce97` |

The `comprehend_text.py` and `boot_all.py` edits are already present in the shared worktree and are not part of this code-reading intervention. They may affect boot state, receipts, or route behavior. The v1.1 candidate result can establish exact behavior and stability on the newly locked current snapshot, but its difference from v1 is descriptive rather than causal. Do not claim that the AST adapter changes alone caused any score or cost delta.

The case frame, 35 primary inputs, two controls, independent oracle, scoring, candidate implementation scope, and success thresholds remain unchanged. The runner and analyzer explicitly verify this four-file runtime delta and lock all sources during both workers. If any file changes again before or during execution, the lock must be refreshed and the intervention run treated as a newly amended snapshot.

# CPython `stat` current-source replay v1.2 amendment

Date: 2026-09-28  
Status: pre-run source-drift disclosure.

Before candidate execution, the complete current source lock was regenerated and compared with the frozen v1 baseline. The v1.2 preregistration named the four runtime source changes disclosed by the v1.1 amendment, but the full comparison also finds one changed loaded seed. This seed change is outside the emitter intervention and can affect initialized world state, so score and cost differences from v1 cannot be attributed to the intervention.

| Runtime input changed since v1 | v1 baseline SHA-256 | v1.2 candidate SHA-256 |
|---|---|---|
| `domains/ast_to_term.py` | `513f027a1ba7db76e62ed6246db3f1550555c4567511ca7a5670ae7a9ff5f334` | `7ef48f9ecb67975428713ae1d2d54100fcdd39fc434dd586803059224f7cdcdb` |
| `domains/code_reading.py` | `2600de2af40a986e1986cbc42f5a83ce5acbc7e21cd3885e8fd924379e841b02` | `dd67d2942cf956c6e35f848aed4012c3ac072e9ac91d9e6b166e8ca44be57908` |
| `domains/comprehend_text.py` | `dd9b3594f1b0daf1394f2c3bfeac991a0326043e67cec164660066c7e7268022` | `bf0c83faad6829df87fe5a99b7612af87078f774ad93ab054dc16fd26cca179e` |
| `seeds/communication_intent_arbitration.json` | `969e4f34762a9ecb717bfd0ecd48b58c6dd548895b712cf44e477156c3f77cd4` | `a8de8e3999bf1f24c95364451bfa387f9f00b59775320647dee4a597a0e06e06` |
| `substrate/boot_all.py` | `3309ee30fc1f3f629d21d0554c3a895be5ed4d6e78160be362e5d5996aed82ae` | `be2bf9aaf25298c15ffc337306819ab2ab5bc8ecdfd5f8b82d0b4d8544f4ce97` |

The lock also includes four added measurement scripts (`analyze_substrate_stdlib_stat_prediction_panel_v1_1.py`, `analyze_substrate_stdlib_stat_prediction_panel_v1_2.py`, `substrate_stdlib_stat_prediction_panel_v1_1.py`, `substrate_stdlib_stat_prediction_panel_v1_2.py`). They are measurement tooling, not runtime inputs to the workers. No other additions, removals, or content changes were found in the measured source groups. The native extension hash, frozen task frame, CPython source, Think Python control corpus, and v1 artifact references match their preregistered values.

The candidate replay remains a current-source stability and positive-fragment check on the inspected CPython family. It is not a blind transfer estimate, and it does not exercise the new ambiguous-name refusal branch. The analyzer explicitly checks the five-file runtime delta above; all measured inputs remain locked before, during, and after both workers.

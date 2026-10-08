# domain_data/

Graph data that is **read directly by a domain module** (by file path), not
installed by the seed loader. These files used to live in `seeds/`, where every
full boot tried to load them as seed manifests and failed (they are not valid
manifests: nodes carry no `local_id`), recording 11 BootSeedAnomaly nodes per
boot. Moved 2026-10-08 (recursive self-improvement tranche 11).

| File | Reader |
|---|---|
| `reading_constructions.json` | `domains/reading_collapse.ensure_codebook` (also read by situation_model_reader, character_tom, propositional_deduction) |
| `conceptual_categories.json` | `domains/phase_composer_language_rules`, `domains/sense_selection_rules` |
| `character_tom.json` | `domains/character_tom` |
| `named_compound_heads.json` | `domains/cognitive_disambiguation` |
| `vision_change.json` | `domains/wave_world` (`_CHANGE_SEED`) |
| `acoustic_cue_vocab.json`, `cue_investigator.json` | `scripts/jabberwock_grounds_acoustic_cue.py`, `scripts/jabberwock_binds_cue_investigator.py` |

Seeds that previously declared `depends_on: ["reading_constructions"]`
(story_boundary, coherence_relations, event_role_frames) now carry
`domain_data_requires` instead: their domain modules load the codebook before
them, and the boot-time dependency was never satisfied anyway (the file never
loaded as a seed).

- `llm_harvest/` — Qwen3 LLM-harvest fragments (`{subject, relation, object,
  trust}` edges, relation calibrations), written by `scripts/llm_harvest_*` /
  `scripts/llm_calibrate_relations.py`. They are inputs to ingest, not seeds;
  the loader's `seeds/generated/*.json` glob had been picking them up.
- `orphaned/reading_skeleton.json` — `ReadingProgram` Terms with no reader in
  the tree (reading_collapse holds the equivalent drivers). Kept, not loaded.

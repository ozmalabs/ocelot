# Probe amendment: resource discovery and runner revisions

The initial resource census used `nltk.data.find("corpora/<name>")` and missed corpora installed as `<name>.zip`. A subsequent check found WordNet and OMW ZIP archives in `/home/matt/nltk_data`; the probe did not cause this correction through runtime behavior. v1.1 successfully ran three workers but its lock omitted these external archive identities. v1.2 adds resolved NLTK resources and hashes to the lock, and its capture is the analyzed result.

The v1 runner pilot failed before invoking handlers because child processes had only the `scripts/` directory on `sys.path`. The failed raw capture and lock remain preserved. v1.1 corrected the import path. The v1.2 lock has a new path and does not overwrite either earlier capture.

No handler inputs or acceptance criteria changed. The corrected interpretation is that WordNet/OMW dependent representative calls work offline in this checkout; `text_valence` attempts opinion-lexicon download twice per worker and errors because that corpus is absent. The analyzed evidence is v1.2 only.

# Generated-pool streaming scale v1.2 analysis amendment

The locked v1.1 analyzer expected the engine provenance object to expose `native_extension.path`; the actual `engine_provenance()` schema exposes `native_path`. It stopped before writing an analysis. The post-capture v1.2 analyzer reads that existing field, adds the workspace to its import path for direct invocation, and reruns all ten preregistered checks. It changes no runner, lock, raw capture, or gate. The corrected analysis passes all 10 checks. Both analyzer versions are retained.

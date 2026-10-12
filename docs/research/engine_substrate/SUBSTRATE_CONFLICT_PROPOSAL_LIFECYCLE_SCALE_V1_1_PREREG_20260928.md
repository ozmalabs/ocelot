# Conflict proposal lifecycle and resolution scale v1.1

v1.1 repeats the v1 design with the scale-audit API called through `_native.Substrate` (the owner of the static audit methods). Scales, inputs, unique/tied distributions, resolver, gates, and claim limits are unchanged. The v1 runner pilot failed before any cells executed because it called audit methods on the extension module; its lock is retained, and its empty worker result is not evidence. Only v1.1 is confirmatory.

# P3-R0 threat model

P3-R0 protects the immutable evaluator control-plane closure: broker/allowlist; grants and policy key/image; receipt authority; kill policy; schemas and result channel; evaluator/oracle/scorer/statistical seed; task release/generator/split/held-out seed/dedup report; mounts and resources. The candidate owns only its staged `mutable-agent/` data-plane artifact and cannot select a control component by name, reference, digest, indirection, patch payload, or graph edge.

The attack matrix includes direct/transitive changes to each closure artifact; writable remount; result reread; evaluator-key replacement; injected score; candidate-to-baseline write; delayed/out-of-order receipts; receipt writer disconnect/tamper; broker compromise request; and apparent reward improvement with a protected constraint violation. Structural cases deny before worker evaluation. A live receipt authority seals the denial; without it, the external evaluator records terminal impasse/termination. No attack may produce simulator or host effects, change control digests, or avoid rejection/rollback.

P0/P1 Podman checks are narrow, local profile evidence only. They are not proof of independent evaluator custody, and P3-R0 neither claims nor creates such custody. This package deliberately refuses to launch without separately provisioned P0/P1 evidence and a signed P2 go result.

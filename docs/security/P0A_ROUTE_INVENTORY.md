# P0-A legacy route inventory

| Route | Guard point | Evaluation result |
|---|---|---|
| `WorldAdapter._dispatch_pending_io` / `converse` | `world.dispatch_pending_io` | `P0A_DIRECT_IO_DENIED` before search/detail/upload dispatch |
| fetch materialization / `exec` / urllib fallback | `fetch.materialize` plus launcher interception | denied before binding materialization or HTTP |
| graph host-action handler map | `raw.host.dispatch` | denied before handler lookup/invocation |
| experiment child/subprocess | `experiment.spawn` plus launcher interception | denied before snapshot/write/Popen |
| BrowserWorld launch/navigation/apply | `browser.launch_apply` | denied before Playwright use |
| microphone capture / `arecord` | `voice.capture_playback` | denied before Popen |
| legacy seed loader | `seed.arbitrary_load` | denied before arbitrary seed reads |
| socket, urllib, Popen, `open`, `os.read`, `os.system`, exec | `entrypoint.intercept_legacy_process_io` | executed in-process defense-in-depth test interception |

The inventory is intentionally limited to known legacy paths and has no claim to catch an attacker able to alter same-user code or disable in-process guards. New effectful paths must add a pre-effect guard and a deterministic inventory test before they are allowed in evaluation mode.



## OS-enforced P0 surfaces

The inventory above is cooperative compatibility coverage only. The fresh-exec sandbox's mount allowlist, descriptor state, private network namespace, absence of host Unix socket mounts, restricted process policy, and evaluator whole-scope kill are deployment-policy targets pending provisioned probe evidence; they are not asserted as local containment guarantees. Each new privileged surface must add provisioned sandbox evidence that it is absent from the agent mount/descriptor/protocol contract; a Python monkeypatch test is not containment evidence.
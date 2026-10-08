# Bigville CAN runtime partition replay — diagnostic v3.1 amendment

The v3 raw output and lock are preserved. The run exposed two harness defects in its revised omitted-notification control: it compared the no-settlement graph after all ten updates with the event arm after only the first update, and the final acceptance check still referenced the v2 control field name. The event and full-scan arms themselves completed all ten steps and matched at every checkpoint; v3 did not yield an interpretable control result and its runner exited with `KeyError` after writing raw output.

V3.1 changes only the control comparison target to the event arm's terminal state after all ten updates and uses the current `notified_sequence_changes_state` field in the final decision. It remains a diagnostic run on the same graph family and sequence; it is not fresh confirmation. The raw v3 record remains untouched.

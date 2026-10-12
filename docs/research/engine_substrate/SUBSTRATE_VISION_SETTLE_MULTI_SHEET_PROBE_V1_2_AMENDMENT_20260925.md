# Vision settling multi-sheet probe — v1.2 amendment

The v1 setup panic and v1.1 raw/analysis are preserved. In v1.1, both A outputs matched the registered equation and changing B changed A, but the B=1 arm's expected A output was already the initial `act_next=0`; the rule therefore reported zero progress in that arm. The pre-registered write-sensitivity criterion failed even though the read-dependence signal was visible.

V1.2 keeps the same two sheets, states, rule and expected values. It initializes each scratch `act_next` buffer to -1.0, outside the rule's nonnegative output range, so every unit must write its calculated result for the arm to satisfy the execution check. This repairs sensitivity only; v1.2 remains diagnostic after two earlier fixture/control failures.

# Adequacy receipt adoption v1.1 measurement amendment

The first integration capture encoded the incomplete-evidence control as a
requested probe row with an empty `labels` array. The adjudicator correctly
classifies that malformed row as `invalid`; it cannot represent a merely
missing requested probe. This was a fixture-encoding error, and the initial
capture did not pass the locked status gate.

For the confirmatory replay, the incomplete control now submits an empty
`audit_rows` list. The expected status remains `incomplete`; all task inputs,
other controls, adoption expectations, and pass criteria remain unchanged.
The runner and this amendment are included in the refreshed pre-run source
lock. The earlier invalid capture was superseded and is not used for results.

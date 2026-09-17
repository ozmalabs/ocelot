from evaluation.p5_r0.permutations import inverse_normalize, label_permutation, mechanics_permutation

def test_label_permutation_round_trips_every_label():
    values = ["opaque-a", "opaque-b", "opaque-c", "opaque-d"]
    permutation = label_permutation(values)
    for value in values:
        assert inverse_normalize(permutation["mapping"][value], permutation) == value

def test_mechanics_permutation_is_a_bijection():
    permutation = mechanics_permutation([{"combination_id": x} for x in ("T01", "D01", "H01")])
    assert set(permutation["mapping"]) == set(permutation["mapping"].values())

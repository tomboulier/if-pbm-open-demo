from if_pbm_open_demo.generate import generate, load_targets


def test_generate_conforms_to_contract() -> None:
    tables = generate(seed=1)
    assert set(tables) == {"patient", "surgery", "consultation", "lab", "transfusion"}

    patient_ids = set(tables["patient"]["patient_id"])
    surgery_ids = set(tables["surgery"]["surgery_id"])

    # Referential integrity: every reference points at an existing parent.
    assert set(tables["surgery"]["patient_id"]) <= patient_ids
    for child in ("consultation", "lab", "transfusion"):
        assert set(tables[child]["patient_id"]) <= patient_ids
        assert set(tables[child]["surgery_id"]) <= surgery_ids

    # Every surgery carries one of the three specialties.
    assert set(tables["surgery"]["specialty"]) <= {
        "orthopedics",
        "cardiology",
        "gynecology",
    }


def test_generation_is_reproducible() -> None:
    a = generate(seed=7)
    b = generate(seed=7)
    for name in a:
        assert a[name].equals(b[name])


def test_surgery_volume_matches_targets() -> None:
    tables = generate(seed=1)
    expected = sum(t.n_surgeries for t in load_targets())
    assert len(tables["surgery"]) == expected

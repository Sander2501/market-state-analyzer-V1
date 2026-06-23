from core.confidence import sample_confidence, small_sample_note


def test_sample_confidence_labels():
    assert sample_confidence(0) == "No sample"
    assert sample_confidence(2).startswith("Low confidence")
    assert sample_confidence(12).startswith("Medium confidence")
    assert sample_confidence(35).startswith("Higher confidence")


def test_small_sample_note_flags_low_confidence():
    assert "unstable" in small_sample_note(2)

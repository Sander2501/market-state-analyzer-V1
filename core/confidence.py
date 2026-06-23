from core.config import LOW_CONFIDENCE_TRADES, MEDIUM_CONFIDENCE_TRADES


def sample_confidence(count: int | None) -> str:
    if count is None or count <= 0:
        return "No sample"
    if count < LOW_CONFIDENCE_TRADES:
        return f"Low confidence ({count} samples)"
    if count < MEDIUM_CONFIDENCE_TRADES:
        return f"Medium confidence ({count} samples)"
    return f"Higher confidence ({count} samples)"


def small_sample_note(count: int | None) -> str:
    confidence = sample_confidence(count)
    if confidence.startswith("Low"):
        return f"{confidence}; treat these metrics as unstable."
    return confidence

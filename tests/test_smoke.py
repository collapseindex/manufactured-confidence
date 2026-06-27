"""Offline smoke tests: the package imports and the judge-free parser works without any API call."""
from manufactured_confidence import DATA_DIR, MODELS, extract_answer


def test_models_registry():
    assert "sonnet" in MODELS
    assert MODELS["sonnet"].startswith("claude")


def test_data_dir_points_at_repo_data():
    assert DATA_DIR.name == "data"
    assert DATA_DIR.parent.name == "manufactured-confidence"


def test_extract_answer_takes_last_answer():
    assert extract_answer("reasoning...\nANSWER: 42") == "42"
    assert extract_answer("ANSWER: GRANT\nthen ANSWER: DENY") == "DENY"
    assert extract_answer("no answer here") is None
    assert extract_answer("") is None

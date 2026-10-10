"""Pure-Python tests for the JSON clean-up helper and the mock provider."""
import json

import pytest

from app.ai.mock import MockProvider
from app.ai.parsing import extract_json


def test_extracts_plain_json():
    assert extract_json('{"a": 1}') == {"a": 1}


def test_extracts_json_inside_code_fence():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_extracts_json_surrounded_by_text():
    assert extract_json('Sure! Here you go: {"a": 1} Hope it helps.') == {"a": 1}


@pytest.mark.parametrize("bad", ["", "no json here", "[1, 2, 3]", '{"a": ', None])
def test_bad_text_raises_value_error(bad):
    with pytest.raises(ValueError):
        extract_json(bad)


def test_mock_provider_returns_description_json():
    data = json.loads(MockProvider().complete("system", "<title>Plan a trip</title>"))
    assert set(data) == {"description", "checklist"}
    assert "Plan a trip" in data["description"]


def test_mock_provider_returns_summary_json():
    prompt = "<title>Plan a trip</title>\n<description>Book flights and hotel</description>"
    data = json.loads(MockProvider().complete("system", prompt))
    assert set(data) == {"summary", "key_points"}
    assert "Book flights" in data["summary"]

from nested_value import find_value


def test_find_value_walks_nested_dicts_and_lists():
    envelope = {
        "result": {
            "items": [
                {"pngBase64": None},
                {"response": {"pngBase64": "encoded-image"}},
            ]
        }
    }

    assert find_value(envelope, "pngBase64") == "encoded-image"


def test_find_value_returns_none_for_missing_key():
    assert find_value({"result": [{"other": 1}]}, "pngBase64") is None

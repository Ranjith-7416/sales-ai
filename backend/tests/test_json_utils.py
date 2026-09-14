from app.utils.json_utils import parse_json_response


def test_parse_json_response_accepts_markdown_fenced_json():
    assert parse_json_response('```json\n{"functional_requirements": ["PDF extraction"]}\n```') == {
        "functional_requirements": ["PDF extraction"]
    }


def test_parse_json_response_accepts_surrounding_text():
    assert parse_json_response('Here is the result:\n{"status": "ok"}\nDone.') == {
        "status": "ok"
    }
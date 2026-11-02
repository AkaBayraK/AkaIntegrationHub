import json

from aih_common.problem import ApiErrorCode, problem_response


def test_from_status_falls_back_by_class() -> None:
    assert ApiErrorCode.from_status(404) is ApiErrorCode.NOT_FOUND
    assert ApiErrorCode.from_status(418) is ApiErrorCode.BAD_REQUEST
    assert ApiErrorCode.from_status(502) is ApiErrorCode.INTERNAL_ERROR


def test_problem_response_shape() -> None:
    response = problem_response(409, "Version conflict", instance="/v1/x")
    body = json.loads(bytes(response.body))
    assert response.media_type == "application/problem+json"
    assert body == {
        "type": "about:blank",
        "title": "Conflict",
        "status": 409,
        "detail": "Version conflict",
        "instance": "/v1/x",
        "code": "AIH-COMMON-409",
        "correlationId": None,
    }

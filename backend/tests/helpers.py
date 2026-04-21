def assert_api_response(response, expected_status, expected_output, input_payload):
    actual_output = response.get_json()
    assert response.status_code == expected_status, (
        f"input={input_payload}\n"
        f"expected_status={expected_status}\n"
        f"actual_status={response.status_code}\n"
        f"expected_output={expected_output}\n"
        f"actual_output={actual_output}"
    )

    if isinstance(expected_output, dict):
        assert isinstance(actual_output, dict), (
            f"input={input_payload}\n"
            f"expected_output={expected_output}\n"
            f"actual_output={actual_output}"
        )
        for key, value in expected_output.items():
            assert actual_output.get(key) == value, (
                f"input={input_payload}\n"
                f"expected_output={expected_output}\n"
                f"actual_output={actual_output}"
            )
    elif isinstance(expected_output, list):
        assert actual_output == expected_output, (
            f"input={input_payload}\n"
            f"expected_output={expected_output}\n"
            f"actual_output={actual_output}"
        )

    return actual_output

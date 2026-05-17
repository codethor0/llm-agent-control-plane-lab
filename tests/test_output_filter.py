"""Output filter blocks sensitive model text."""

from agent_control_plane.output_filter import filter_model_output


def test_clean_output_allowed() -> None:
    result = filter_model_output("Here are your records for today.")
    assert result.allowed is True
    assert result.filtered_text


def test_secret_pattern_blocked() -> None:
    result = filter_model_output("key: sk-live-FAKE-TEST-ONLY-abcdef0123456789abcdef0123456789")
    assert result.allowed is False
    assert result.reason == "secret_pattern_blocked"


def test_private_key_blocked() -> None:
    text = "-----BEGIN PRIVATE KEY-----\nMIIE\n-----END PRIVATE KEY-----"
    result = filter_model_output(text)
    assert result.allowed is False
    assert result.reason == "private_key_material_blocked"


def test_jwt_like_token_blocked() -> None:
    jwt_like = (
        "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0."
        "dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
    )
    result = filter_model_output(f"bearer={jwt_like}")
    assert result.allowed is False
    assert result.reason == "jwt_like_token_blocked"


def test_encoded_blob_blocked() -> None:
    import base64

    payload = b"SensitiveExportData-" * 5  # printable when decoded
    blob = base64.b64encode(payload).decode()
    result = filter_model_output(f"data: {blob}")
    assert result.allowed is False
    assert result.reason == "encoded_blob_blocked"

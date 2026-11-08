import pytest
from unittest.mock import MagicMock
from app.services.gemini_client import GeminiClient


def test_gemini_client_unconfigured():
    client = GeminiClient(api_key="")
    assert client.is_configured() is False
    with pytest.raises(ValueError) as excinfo:
        client.generate_text("Hello")
    assert "Gemini API key is not configured" in str(excinfo.value)


def test_gemini_client_generate_text_mocked():
    client = GeminiClient(api_key="fake_test_key_12345")
    assert client.is_configured() is True

    mock_response = MagicMock()
    mock_response.text = "This is a simulated AI response."

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    client._client = mock_client

    result = client.generate_text("Summarize the paper")
    assert result == "This is a simulated AI response."
    mock_client.models.generate_content.assert_called_once()


def test_gemini_client_generate_json_mocked():
    client = GeminiClient(api_key="fake_test_key_12345")

    mock_response = MagicMock()
    mock_response.text = '{"tldr": "Paper summary", "score": 95}'

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    client._client = mock_client

    result = client.generate_json("Return structured JSON")
    assert isinstance(result, dict)
    assert result["tldr"] == "Paper summary"
    assert result["score"] == 95


def test_gemini_client_invalid_json_handling():
    client = GeminiClient(api_key="fake_test_key_12345")

    mock_response = MagicMock()
    mock_response.text = "This is not valid JSON"

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    client._client = mock_client

    with pytest.raises(ValueError) as excinfo:
        client.generate_json("Return structured JSON")
    assert "Gemini returned invalid JSON structure" in str(excinfo.value)

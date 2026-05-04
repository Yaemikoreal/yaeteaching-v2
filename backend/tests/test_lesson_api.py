"""Unit tests for LessonGenerator API calls (mocked)."""
import pytest
import json
from unittest.mock import patch, MagicMock, Mock
import httpx
from services.lesson import LessonGenerator


class TestLessonGeneratorDeepSeek:
    """Tests for DeepSeek API integration."""

    @patch("services.lesson.httpx.Client")
    def test_call_deepseek_success(self, mock_client_class):
        """Test successful DeepSeek API call."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": "```json\n{\"meta\": {}, \"outline\": {}}\n```"}}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        generator = LessonGenerator()
        generator.deepseek_key = "test-key"

        result = generator._call_deepseek("test prompt")

        assert result is not None
        mock_client.post.assert_called_once()

    @patch("services.lesson.httpx.Client")
    def test_call_deepseek_headers_correct(self, mock_client_class):
        """Test DeepSeek API call has correct headers."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "{}"}}]}
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        generator = LessonGenerator()
        generator.deepseek_key = "sk-test-key"

        generator._call_deepseek("prompt")

        call_args = mock_client.post.call_args
        headers = call_args[1]["headers"]
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer sk-test-key"

    @patch("services.lesson.httpx.Client")
    def test_call_deepseek_raises_on_error(self, mock_client_class):
        """Test DeepSeek raises exception on HTTP error."""
        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.HTTPStatusError(
            "Error", request=Mock(), response=Mock(status_code=500)
        )
        mock_client_class.return_value = mock_client

        generator = LessonGenerator()
        generator.deepseek_key = "test-key"

        with pytest.raises(httpx.HTTPStatusError):
            generator._call_deepseek("prompt")


class TestLessonGeneratorOpenAI:
    """Tests for OpenAI API integration."""

    @patch("services.lesson.httpx.Client")
    def test_call_openai_success(self, mock_client_class):
        """Test successful OpenAI API call."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": "{\"meta\": {}, \"outline\": {}}"}}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        generator = LessonGenerator()
        generator.openai_key = "test-key"

        result = generator._call_openai("test prompt")

        assert result is not None

    @patch("services.lesson.httpx.Client")
    def test_call_openai_model_is_gpt4o(self, mock_client_class):
        """Test OpenAI call uses gpt-4o model."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "{}"}}]}
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        generator = LessonGenerator()
        generator.openai_key = "test-key"

        generator._call_openai("prompt")

        call_args = mock_client.post.call_args
        payload = call_args[1]["json"]
        assert payload["model"] == "gpt-4o"


class TestLessonGeneratorGenerateWithAPIs:
    """Tests for generate method with API fallback."""

    @patch("services.lesson.httpx.Client")
    def test_generate_uses_deepseek_first(self, mock_client_class):
        """Test generate tries DeepSeek first when key available."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": "{\"meta\": {\"subject\": \"test\"}, \"outline\": {}}"}}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        generator = LessonGenerator()
        generator.deepseek_key = "deepseek-key"
        generator.openai_key = "openai-key"

        result = generator.generate({"subject": "数学", "grade": "7年级", "topic": "test", "duration": 45})

        # Should have called DeepSeek API
        assert mock_client.post.called

    @patch("services.lesson.httpx.Client")
    def test_generate_fallback_to_openai(self, mock_client_class):
        """Test generate falls back to OpenAI when DeepSeek fails."""
        mock_client = MagicMock()

        # First call (DeepSeek) fails
        mock_client.post.side_effect = [
            httpx.HTTPStatusError("Error", request=Mock(), response=Mock(status_code=500)),
            # Second call (OpenAI) succeeds
            MagicMock(
                json=lambda: {"choices": [{"message": {"content": '{"meta": {}, "outline": {}}'}}]},
                raise_for_status=Mock()
            )
        ]
        mock_client_class.return_value = mock_client

        generator = LessonGenerator()
        generator.deepseek_key = "deepseek-key"
        generator.openai_key = "openai-key"

        result = generator.generate({"subject": "数学", "grade": "7年级", "topic": "test", "duration": 45})

        # Should have made 2 calls (DeepSeek fail, OpenAI success)
        assert mock_client.post.call_count == 2

    @patch("services.lesson.httpx.Client")
    def test_generate_fallback_to_template(self, mock_client_class):
        """Test generate uses template when both APIs fail."""
        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.HTTPStatusError(
            "Error", request=Mock(), response=Mock(status_code=500)
        )
        mock_client_class.return_value = mock_client

        generator = LessonGenerator()
        generator.deepseek_key = "deepseek-key"
        generator.openai_key = "openai-key"

        result = generator.generate({"subject": "数学", "grade": "7年级", "topic": "test", "duration": 45})

        # Should return template result
        assert "meta" in result
        assert "outline" in result
        assert result["meta"]["subject"] == "数学"

    def test_generate_no_api_keys_uses_template(self):
        """Test generate uses template when no API keys configured."""
        generator = LessonGenerator()
        generator.deepseek_key = ""
        generator.openai_key = ""

        result = generator.generate({"subject": "物理", "grade": "高一", "topic": "牛顿定律", "duration": 30})

        assert result["meta"]["subject"] == "物理"
        assert "outline" in result


class TestLessonGeneratorParseResponse:
    """Tests for LLM response parsing."""

    def test_parse_response_removes_markdown_markers(self):
        """Test parsing removes ```json markers."""
        generator = LessonGenerator()

        response = "```json\n{\"meta\": {}, \"outline\": {}}\n```"
        result = generator._parse_llm_response(response)

        assert result == {"meta": {}, "outline": {}}

    def test_parse_response_handles_plain_json(self):
        """Test parsing handles plain JSON without markers."""
        generator = LessonGenerator()

        response = '{"meta": {"subject": "test"}, "outline": {"introduction": {}}}'
        result = generator._parse_llm_response(response)

        assert result["meta"]["subject"] == "test"

    def test_parse_response_validates_structure(self):
        """Test parsing validates required structure."""
        generator = LessonGenerator()

        # Missing 'outline' key
        response = '{"meta": {"subject": "test"}}'

        with pytest.raises(ValueError):
            generator._parse_llm_response(response)

    def test_parse_response_handles_extra_whitespace(self):
        """Test parsing handles extra whitespace."""
        generator = LessonGenerator()

        response = "  ```json  \n  {\"meta\": {}, \"outline\": {}}  \n  ```  "
        result = generator._parse_llm_response(response)

        assert result is not None


class TestLessonGeneratorBuildPrompt:
    """Tests for prompt building."""

    def test_build_prompt_includes_all_fields(self):
        """Test prompt includes all request fields."""
        generator = LessonGenerator()

        request_data = {
            "subject": "化学",
            "grade": "高二",
            "topic": "有机化学基础",
            "duration": 60,
            "style": "探究式学习",
        }

        prompt = generator._build_prompt(request_data)

        assert "化学" in prompt
        assert "高二" in prompt
        assert "有机化学基础" in prompt
        assert "60" in prompt
        assert "探究式学习" in prompt

    def test_build_prompt_default_style(self):
        """Test prompt uses default style when None."""
        generator = LessonGenerator()

        request_data = {
            "subject": "数学",
            "grade": "7年级",
            "topic": "方程",
            "duration": 45,
            "style": None,
        }

        prompt = generator._build_prompt(request_data)

        # Should use default style
        assert "启发式教学" in prompt


class TestLessonGeneratorClient:
    """Tests for HTTP client initialization."""

    def test_client_has_timeout(self):
        """Test client is initialized with timeout."""
        generator = LessonGenerator()

        assert generator.client is not None
        assert generator.client.timeout == httpx.Timeout(60.0)

    def test_client_reuse(self):
        """Test client is reused across calls."""
        generator = LessonGenerator()

        client1 = generator.client
        client2 = generator.client

        assert client1 is client2
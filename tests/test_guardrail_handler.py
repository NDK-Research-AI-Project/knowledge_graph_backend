"""
Unit tests for GuardrailHandler
"""
import pytest
import json
from unittest.mock import patch, MagicMock, call
import sys
import os
import requests

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.handlers.guardrail_handler import GuardrailHandler
from src.config.config import Config

class TestGuardrailHandler:
    """Tests for the GuardrailHandler class"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock Config object for testing"""
        config = MagicMock(spec=Config)
        config.guardrail_enabled = True
        config.guardrail_model = "meta-llama/Llama-Guard-4-12B"
        config.guardrail_api_base = "https://api.deepinfra.com/v1/inference"
        config.deepinfra_api_token = "test_token"
        return config

    @pytest.fixture
    def guardrail_handler(self, mock_config):
        """Create a GuardrailHandler instance for testing"""
        return GuardrailHandler(mock_config)

    def test_init(self, guardrail_handler, mock_config):
        """Test initialization of GuardrailHandler"""
        assert guardrail_handler.enabled == mock_config.guardrail_enabled
        assert guardrail_handler.model == mock_config.guardrail_model
        assert guardrail_handler.api_base == mock_config.guardrail_api_base
        assert guardrail_handler.api_token == mock_config.deepinfra_api_token
        
        # Check that unsafe categories are set correctly
        assert "violence_and_hate" in guardrail_handler.unsafe_categories
        assert "sexual_content" in guardrail_handler.unsafe_categories
        assert "criminal_planning" in guardrail_handler.unsafe_categories
        assert len(guardrail_handler.unsafe_categories) >= 8  # At least 8 categories defined

    def test_format_safety_prompt(self, guardrail_handler):
        """Test formatting of safety prompt"""
        query = "Is this safe?"
        prompt = guardrail_handler._format_safety_prompt(query)
        
        assert "<safety_prompt>" in prompt
        assert "Is this safe?" in prompt
        assert "User message:" in prompt
        assert "</safety_prompt>" in prompt
        
        # Test with complex input containing quotes and special characters
        complex_query = "What about \"quotes\" and special-characters?"
        complex_prompt = guardrail_handler._format_safety_prompt(complex_query)
        assert "What about \"quotes\" and special-characters?" in complex_prompt
        
        # Test with multi-line input
        multiline_query = "Line 1\nLine 2\nLine 3"
        multiline_prompt = guardrail_handler._format_safety_prompt(multiline_query)
        assert "Line 1\nLine 2\nLine 3" in multiline_prompt

    def test_parse_safety_response_safe(self, guardrail_handler):
        """Test parsing of a safe response"""
        # Clear safe response
        response = "I've analyzed the user message and it appears to be safe. It doesn't contain any harmful content."
        is_safe, reason = guardrail_handler._parse_safety_response(response)
        assert is_safe is True
        assert reason == ""
        
        # Another variant of safe response
        response = "After analyzing the content, I can confirm it is safe and appropriate."
        is_safe, reason = guardrail_handler._parse_safety_response(response)
        assert is_safe is True
        assert reason == ""
        
        # Safe but mentions categories in a negation context
        response = "The message does not contain violence and hate or any harmful content."
        is_safe, reason = guardrail_handler._parse_safety_response(response)
        assert is_safe is True
        assert reason == ""

    def test_parse_safety_response_unsafe_general(self, guardrail_handler):
        """Test parsing of an unsafe response with general unsafe terms"""
        # General unsafe response
        response = "The user message is not safe as it contains inappropriate content."
        is_safe, reason = guardrail_handler._parse_safety_response(response)
        assert is_safe is False
        assert "violate safety guidelines" in reason
        
        # Another variant with unsafe terminology
        response = "This message violates safety guidelines and should be flagged."
        is_safe, reason = guardrail_handler._parse_safety_response(response)
        assert is_safe is False
        assert "violate safety guidelines" in reason
        
        # Clear harmful content indicator
        response = "This message contains harmful content that should not be processed."
        is_safe, reason = guardrail_handler._parse_safety_response(response)
        assert is_safe is False

    def test_parse_safety_response_unsafe_specific(self, guardrail_handler):
        """Test parsing of an unsafe response with specific unsafe categories"""
        # Single category
        response = "The message contains violence and hate which violates safety guidelines."
        is_safe, reason = guardrail_handler._parse_safety_response(response)
        assert is_safe is False
        assert "violence_and_hate" in reason
        
        # Multiple categories
        response = "This contains both violence and hate as well as sexual content."
        is_safe, reason = guardrail_handler._parse_safety_response(response)
        assert is_safe is False
        assert "violence_and_hate" in reason
        assert "sexual_content" in reason
        
        # Test with other categories
        response = "The message includes content related to guns and illegal weapons."
        is_safe, reason = guardrail_handler._parse_safety_response(response)
        assert is_safe is False
        assert "guns_and_illegal_weapons" in reason
        
        # Test with the category in different formatting
        response = "This message has criminal planning elements which is unsafe."
        is_safe, reason = guardrail_handler._parse_safety_response(response)
        assert is_safe is False
        assert "criminal_planning" in reason

    def test_parse_safety_response_edge_cases(self, guardrail_handler):
        """Test parsing edge cases in safety responses"""
        # Ambiguous response with both safe and unsafe signals
        response = "While the message seems safe overall, it does contain some mildly inappropriate elements."
        is_safe, reason = guardrail_handler._parse_safety_response(response)
        # Since it contains "inappropriate", it should be marked unsafe
        assert is_safe is False
        
        # Empty string
        response = ""
        is_safe, reason = guardrail_handler._parse_safety_response(response)
        # Default to safe with empty response
        assert is_safe is True
        assert reason == ""
        
        # Completely irrelevant response
        response = "The weather today is sunny with a chance of rain."
        is_safe, reason = guardrail_handler._parse_safety_response(response)
        # Default to safe for irrelevant response
        assert is_safe is True
        assert reason == ""

    @patch('requests.post')
    def test_is_safe_query_safe(self, mock_post, guardrail_handler):
        """Test is_safe_query with a safe query"""
        # Mock response from the API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'output': "I've analyzed the user message and it appears to be safe."
        }
        mock_post.return_value = mock_response
        
        is_safe, reason = guardrail_handler.is_safe_query("What is the weather like today?")
        
        assert is_safe is True
        assert reason == ""
        
        # Verify API call details
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        # Check URL
        assert call_args[0][0] == guardrail_handler.api_base
        # Check headers
        assert "Authorization" in call_args[1]["headers"]
        assert f"Bearer {guardrail_handler.api_token}" == call_args[1]["headers"]["Authorization"]
        # Check payload
        payload = json.loads(call_args[1]["data"])
        assert payload["model"] == guardrail_handler.model
        assert "What is the weather like today?" in payload["input"]

    @patch('requests.post')
    def test_is_safe_query_unsafe(self, mock_post, guardrail_handler):
        """Test is_safe_query with an unsafe query"""
        # Mock response from the API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'output': "The message contains violence and hate content which is unsafe."
        }
        mock_post.return_value = mock_response
        
        is_safe, reason = guardrail_handler.is_safe_query("How to harm people?")
        
        assert is_safe is False
        assert "violence_and_hate" in reason
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_is_safe_query_api_error(self, mock_post, guardrail_handler):
        """Test is_safe_query with API error"""
        # Mock API error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server error"
        mock_post.return_value = mock_response
        
        # Should default to safe on API error
        is_safe, reason = guardrail_handler.is_safe_query("Query text")
        
        assert is_safe is True
        assert reason == ""
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_is_safe_query_exception(self, mock_post, guardrail_handler):
        """Test is_safe_query handling an exception"""
        # Test with different kinds of exceptions
        exceptions_to_test = [
            requests.RequestException("Connection error"),
            requests.Timeout("Request timed out"),
            requests.ConnectionError("Connection failed"),
            json.JSONDecodeError("Invalid JSON", "", 0),
            Exception("Generic error")
        ]
        
        for exception in exceptions_to_test:
            mock_post.side_effect = exception
            
            # Should default to safe on exception
            is_safe, reason = guardrail_handler.is_safe_query("Query text")
            
            assert is_safe is True
            assert reason == ""
            mock_post.assert_called_once()
            mock_post.reset_mock()

    def test_guardrail_disabled(self, guardrail_handler):
        """Test when guardrail is disabled"""
        # Disable guardrail
        guardrail_handler.enabled = False
        
        # Should always return safe when disabled, without making API calls
        with patch('requests.post') as mock_post:
            is_safe, reason = guardrail_handler.is_safe_query("Any potentially unsafe content")
            
            assert is_safe is True
            assert reason == ""
            mock_post.assert_not_called()
            
    @patch('requests.post')
    @patch('src.handlers.guardrail_handler.logger')
    def test_logging_behavior(self, mock_logger, mock_post, guardrail_handler):
        """Test the logging behavior of the guardrail handler"""
        # Mock safe response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'output': "The message is safe."
        }
        mock_post.return_value = mock_response
        
        _ = guardrail_handler.is_safe_query("Safe query")
        
        # No warning should be logged for safe content
        mock_logger.warning.assert_not_called()
        
        # Mock unsafe response
        mock_response.json.return_value = {
            'output': "The message contains violence which is unsafe."
        }
        
        _ = guardrail_handler.is_safe_query("Unsafe query")
        
        # Warning should be logged for unsafe content
        mock_logger.warning.assert_called_once()
        
        # Mock API error
        mock_response.status_code = 500
        mock_logger.warning.reset_mock()
        mock_logger.error.reset_mock()
        
        _ = guardrail_handler.is_safe_query("Error query")
        
        # Error should be logged for API error
        mock_logger.error.assert_called_once()

"""
Unit tests for Config class
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config.config import Config

class TestConfig:
    """Tests for the Config class"""
    
    @patch('src.config.config.os')
    @patch('src.config.config.load_dotenv')
    def test_init_default_values(self, mock_load_dotenv, mock_os):
        """Test initialization with default values"""
        # Mock os.getenv to return None for all environment variables
        mock_os.getenv.return_value = None
        
        # Initialize Config
        config = Config()
        
        # Verify dotenv was loaded
        mock_load_dotenv.assert_called_once()
        
        # Verify default values
        assert config.neo4j_uri == "neo4j+ssc://9d3d116e.databases.neo4j.io"
        assert config.neo4j_username == "neo4j"
        assert config.neo4j_password == "MTmhQ8kiaRqRltgDThU_4hYE-aCCpIVk5aNmcUnKWKU"
        assert config.groq_api_key == "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"
        assert config.logging_config["app_name"] == "document-summarizer"
        assert config.guardrail_enabled == True
        assert config.guardrail_model == "meta-llama/Llama-Guard-4-12B"
        
    @patch('src.config.config.os')
    @patch('src.config.config.load_dotenv')
    def test_init_custom_values(self, mock_load_dotenv, mock_os):
        """Test initialization with custom environment values"""
        # Mock environment variables
        env_vars = {
            "NEO4J_URI": "custom-neo4j-uri",
            "NEO4J_USERNAME": "custom-username",
            "NEO4J_PASSWORD": "custom-password",
            "DEEPINFRA_API_TOKEN": "custom-token",
            "GROQ_API_KEY": "custom-api-key",
            "GUARDRAIL_ENABLED": "false",
            "GUARDRAIL_MODEL": "custom-model",
            "GUARDRAIL_API_BASE": "custom-api-base",
            "GROQ_MODEL": "custom-groq-model",
            "DEEPINFRA_MODEL": "custom-deepinfra-model",
            "MONGO_URI": "custom-mongo-uri"
        }
        
        # Mock os.getenv to return custom values
        def mock_getenv(key, default=None):
            return env_vars.get(key, default)
        
        mock_os.getenv.side_effect = mock_getenv
        
        # Initialize Config
        config = Config()
        
        # Verify custom values
        assert config.neo4j_uri == "custom-neo4j-uri"
        assert config.neo4j_username == "custom-username"
        assert config.neo4j_password == "custom-password"
        assert config.deepinfra_api_token == "custom-token"
        assert config.groq_api_key == "custom-api-key"
        assert config.guardrail_enabled == False  # Converted from string to bool
        assert config.guardrail_model == "custom-model"
        assert config.guardrail_api_base == "custom-api-base"
        assert config.groq_model == "custom-groq-model"
        assert config.deepinfra_model == "custom-deepinfra-model"
        assert config.mongo_uri == "custom-mongo-uri"

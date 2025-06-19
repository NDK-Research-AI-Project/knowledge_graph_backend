"""
Unit tests for QueryHandler
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.handlers.query_handler import QueryHandler
from src.config.config import Config

class TestQueryHandler:
    """Tests for the QueryHandler class"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock Config object for testing"""
        config = MagicMock(spec=Config)
        config.neo4j_uri = "bolt://localhost:7687"
        config.neo4j_username = "test"
        config.neo4j_password = "test"
        config.deepinfra_api_token = "test_token"
        config.groq_api_key = "test_groq_key"
        config.groq_model = "test_model"
        return config

    @patch('src.handlers.query_handler.GraphDatabase')
    @patch('src.handlers.query_handler.Neo4jGraph')
    @patch('src.handlers.query_handler.ExplanationHandler')
    def test_init(self, mock_explanation_handler, mock_neo4j_graph, mock_graph_db, mock_config):
        """Test initialization of QueryHandler"""
        # Setup mocks
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver
        mock_explanation_instance = MagicMock()
        mock_explanation_handler.return_value = mock_explanation_instance
        
        # Initialize QueryHandler
        handler = QueryHandler(mock_config)
        
        # Verify the correct initialization
        assert handler.config == mock_config
        assert handler.neo4j_uri == mock_config.neo4j_uri
        assert handler.neo4j_username == mock_config.neo4j_username
        assert handler.neo4j_password == mock_config.neo4j_password
        assert handler.explanation_handler == mock_explanation_instance

    @patch('src.handlers.query_handler.GraphDatabase')
    @patch('src.handlers.query_handler.Neo4jGraph')
    @patch('src.handlers.query_handler.ChatGroq')
    def test_extract_entities(self, mock_chat_groq, mock_neo4j_graph, mock_graph_db, mock_config):
        """Test entity extraction"""
        # Setup mocks
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver
        
        mock_llm = MagicMock()
        mock_llm_response = MagicMock()
        mock_llm_response.content = "entity1, entity2"
        mock_llm.invoke.return_value = mock_llm_response
        mock_chat_groq.return_value = mock_llm
        
        # Initialize QueryHandler
        handler = QueryHandler(mock_config)
        
        # Test entity extraction
        entities = handler.extract_entities("test query")
        
        # Verify the results
        assert entities == ["entity1", "entity2"]
        mock_llm.invoke.assert_called_once()

    @patch('src.handlers.query_handler.GraphDatabase')
    @patch('src.handlers.query_handler.Neo4jGraph')
    def test_escape_lucene_query(self, mock_neo4j_graph, mock_graph_db, mock_config):
        """Test Lucene query escaping"""
        # Setup mocks
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver
        
        # Initialize QueryHandler
        handler = QueryHandler(mock_config)
        
        # Test with various special characters
        result = handler.escape_lucene_query("test+query:[with]^special*characters?")
        
        # Verify all special characters are escaped
        assert result == "test\\+query\\:\\[with\\]\\^special\\*characters\\?"

    @patch('src.handlers.query_handler.GraphDatabase')
    @patch('src.handlers.query_handler.Neo4jGraph')
    def test_get_explanation(self, mock_neo4j_graph, mock_graph_db, mock_config):
        """Test getting explanations"""
        # Setup mocks
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver
        
        mock_explanation_handler = MagicMock()
        mock_explanation_handler.get_explanation.return_value = ["Step 1", "Step 2"]
        
        # Initialize QueryHandler with mocked explanation handler
        handler = QueryHandler(mock_config)
        handler.explanation_handler = mock_explanation_handler
        
        # Get explanation
        explanation = handler.get_explanation()
        
        # Verify explanation is retrieved
        assert explanation == ["Step 1", "Step 2"]
        mock_explanation_handler.get_explanation.assert_called_once()

    @patch('src.handlers.query_handler.GraphDatabase')
    @patch('src.handlers.query_handler.Neo4jGraph')
    def test_retrieve_context_empty_entities(self, mock_neo4j_graph, mock_graph_db, mock_config):
        """Test retrieving context with no entities"""
        # Setup mocks
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver
        
        # Setup QueryHandler with a method that returns no entities
        handler = QueryHandler(mock_config)
        handler.extract_entities = MagicMock(return_value=[])
        handler.explanation_handler = MagicMock()
        
        # Retrieve context
        result = handler.retrieve_context_from_kg("query with no entities")
        
        # Verify result indicates no entities found
        assert result == "No entities found in the question."
        handler.extract_entities.assert_called_once_with("query with no entities")
        handler.explanation_handler.add_step.assert_called()

    @patch('src.handlers.query_handler.GraphDatabase')
    @patch('src.handlers.query_handler.Neo4jGraph')
    def test_retrieve_context_with_entities(self, mock_neo4j_graph, mock_graph_db, mock_config):
        """Test retrieving context with entities"""
        # Setup mocks
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver
        
        # Mock session and transaction
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([{"output": "result1"}, {"output": "result2"}]))
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Setup QueryHandler
        handler = QueryHandler(mock_config)
        handler.extract_entities = MagicMock(return_value=["entity1"])
        handler.explanation_handler = MagicMock()
        
        # Retrieve context
        result = handler.retrieve_context_from_kg("query with entity")
        
        # Verify result contains entity information
        assert "Entity: entity1" in result
        assert "result1" in result
        assert "result2" in result
        handler.extract_entities.assert_called_once_with("query with entity")
        mock_session.run.assert_called_once()
        handler.explanation_handler.add_step.assert_called()

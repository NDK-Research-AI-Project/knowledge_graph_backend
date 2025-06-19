"""
Unit tests for AnswerGenerator
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.generators.answer_generator import AnswerGenerator
from src.config.config import Config
from langchain_core.messages import AIMessage

class TestAnswerGenerator:
    """Tests for the AnswerGenerator class"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock Config object for testing"""
        config = MagicMock(spec=Config)
        config.neo4j_uri = "bolt://localhost:7687"
        config.neo4j_username = "test"
        config.neo4j_password = "test"
        config.deepinfra_api_token = "test_token"
        config.deepinfra_model = "test_deepinfra"
        config.groq_api_key = "test_groq_key"
        config.groq_model = "test_model"
        config.chat_template = "test_template"
        return config

    @patch('src.generators.answer_generator.GraphDatabase')
    @patch('src.generators.answer_generator.Neo4jGraph')
    @patch('src.generators.answer_generator.ChatGroq')
    @patch('src.generators.answer_generator.ChatDeepInfra')
    @patch('src.generators.answer_generator.ChatPromptTemplate')
    def test_init(self, mock_prompt, mock_deepinfra, mock_groq, mock_neo4j_graph, mock_graph_db, mock_config):
        """Test initialization of AnswerGenerator"""
        # Setup mocks
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver
        
        mock_llm = MagicMock()
        mock_groq.return_value = mock_llm
        
        mock_deepinfra_llm = MagicMock()
        mock_deepinfra.return_value = mock_deepinfra_llm
        
        mock_prompt_template = MagicMock()
        mock_prompt.from_template.return_value = mock_prompt_template
        
        # Initialize AnswerGenerator
        generator = AnswerGenerator(mock_config)
        
        # Verify the correct initialization
        assert generator.config == mock_config
        assert generator.neo4j_uri == mock_config.neo4j_uri
        assert generator.neo4j_username == mock_config.neo4j_username
        assert generator.neo4j_password == mock_config.neo4j_password
        assert generator.deepinfra_api_token == mock_config.deepinfra_api_token
        assert generator.groq_api_key == mock_config.groq_api_key
        assert generator.prompt == mock_prompt_template
        
        # Verify LLM initialization
        mock_groq.assert_called_once_with(
            model=mock_config.groq_model,
            api_key=mock_config.groq_api_key,
            temperature=0,
            max_tokens=None
        )
        
        mock_deepinfra.assert_called_once_with(
            model=mock_config.deepinfra_model,
            api_token=mock_config.deepinfra_api_token,
            temperature=0
        )

    @patch('src.generators.answer_generator.GraphDatabase')
    @patch('src.generators.answer_generator.Neo4jGraph')
    @patch('src.generators.answer_generator.query_hander')
    @patch('src.generators.answer_generator.glossary_handler')
    def test_generate_answer(self, mock_glossary_handler, mock_query_handler, mock_neo4j_graph, mock_graph_db, mock_config):
        """Test generating an answer"""
        # Setup mocks
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver
        
        mock_query_handler.retrieve_context_from_kg.return_value = "test context"
        mock_query_handler.get_explanation.return_value = ["Step 1", "Step 2"]
        
        mock_glossary_handler.get_glossary_for_query.return_value = "test glossary"
        
        mock_chain = MagicMock()
        mock_ai_message = AIMessage(content="test answer")
        mock_chain.invoke.return_value = mock_ai_message
        
        # Initialize AnswerGenerator with mocked chain
        generator = AnswerGenerator(mock_config)
        generator.chain = mock_chain
        
        # Generate answer
        result = generator.generate_answer("test query")
        
        # Verify the result
        assert result["answer"] == "test answer"
        assert len(result["explanation"]) > 2  # Should include original steps plus added steps
        mock_query_handler.retrieve_context_from_kg.assert_called_once_with("test query")
        mock_glossary_handler.get_glossary_for_query.assert_called_once_with("test query")
        mock_chain.invoke.assert_called_once_with({
            "context": "test context",
            "glossary": "test glossary",
            "question": "test query"
        })

    @patch('src.generators.answer_generator.GraphDatabase')
    @patch('src.generators.answer_generator.Neo4jGraph')
    @patch('src.generators.answer_generator.query_hander')
    @patch('src.generators.answer_generator.glossary_handler')
    def test_generate_answer_string_response(self, mock_glossary_handler, mock_query_handler, mock_neo4j_graph, mock_graph_db, mock_config):
        """Test generating an answer with a string response"""
        # Setup mocks
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver
        
        mock_query_handler.retrieve_context_from_kg.return_value = "test context"
        mock_query_handler.get_explanation.return_value = ["Step 1", "Step 2"]
        
        mock_glossary_handler.get_glossary_for_query.return_value = "test glossary"
        
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = "test answer as string"  # String response instead of AIMessage
        
        # Initialize AnswerGenerator with mocked chain
        generator = AnswerGenerator(mock_config)
        generator.chain = mock_chain
        
        # Generate answer
        result = generator.generate_answer("test query")
        
        # Verify the result
        assert result["answer"] == "test answer as string"
        assert len(result["explanation"]) > 2  # Should include original steps plus added steps
        mock_chain.invoke.assert_called_once()

    @patch('src.generators.answer_generator.GraphDatabase')
    @patch('src.generators.answer_generator.Neo4jGraph')
    @patch('src.generators.answer_generator.query_hander')
    @patch('src.generators.answer_generator.glossary_handler')
    def test_generate_answer_no_glossary(self, mock_glossary_handler, mock_query_handler, mock_neo4j_graph, mock_graph_db, mock_config):
        """Test generating an answer without glossary"""
        # Setup mocks
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver
        
        mock_query_handler.retrieve_context_from_kg.return_value = "test context"
        mock_query_handler.get_explanation.return_value = ["Step 1", "Step 2"]
        
        mock_glossary_handler.get_glossary_for_query.return_value = ""  # Empty glossary
        
        mock_chain = MagicMock()
        mock_ai_message = AIMessage(content="test answer")
        mock_chain.invoke.return_value = mock_ai_message
        
        # Initialize AnswerGenerator with mocked chain
        generator = AnswerGenerator(mock_config)
        generator.chain = mock_chain
        
        # Generate answer
        result = generator.generate_answer("test query")
        
        # Verify the result
        assert result["answer"] == "test answer"
        mock_chain.invoke.assert_called_once_with({
            "context": "test context",
            "glossary": "",  # Empty string passed
            "question": "test query"
        })

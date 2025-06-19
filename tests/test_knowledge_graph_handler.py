"""
Unit tests for KnowledgeGraphHandler
"""
import pytest
from unittest.mock import patch, MagicMock, mock_open, call, ANY
import sys
import os
import io
import fitz
from PyPDF2 import PdfReader

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.handlers.knowledge_graph_handler import KnowledgeGraphHandler

class TestKnowledgeGraphHandler:
    """Tests for the KnowledgeGraphHandler class"""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock Config object for testing"""
        config = MagicMock()
        config.neo4j_uri = "bolt://localhost:7687"
        config.neo4j_username = "test"
        config.neo4j_password = "test"
        config.deepinfra_api_token = "test_token"
        config.groq_api_key = "test_groq_key"
        config.groq_model = "test_groq_model"
        return config
    
    @patch('src.handlers.knowledge_graph_handler.GraphDatabase')
    @patch('src.handlers.knowledge_graph_handler.Neo4jGraph')
    @patch('src.handlers.knowledge_graph_handler.PaddleOCR')
    def test_init(self, mock_ocr, mock_neo4j_graph, mock_graph_db, mock_config):
        """Test initialization of KnowledgeGraphHandler"""
        # Setup mocks
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver
        
        mock_graph = MagicMock()
        mock_neo4j_graph.return_value = mock_graph
        
        mock_ocr_instance = MagicMock()
        mock_ocr.return_value = mock_ocr_instance
        
        # Initialize handler
        handler = KnowledgeGraphHandler(mock_config)
        
        # Verify driver initialization
        mock_graph_db.driver.assert_called_once_with(
            mock_config.neo4j_uri,
            auth=(mock_config.neo4j_username, mock_config.neo4j_password)
        )
        mock_neo4j_graph.assert_called_once_with(
            url=mock_config.neo4j_uri,
            username=mock_config.neo4j_username,
            password=mock_config.neo4j_password
        )
        
        # Verify OCR initialization
        mock_ocr.assert_called_once_with(use_angle_cls=True, lang="en")
        
        # Verify attributes
        assert handler.driver == mock_driver
        assert handler.graph == mock_graph
        assert handler.ocr == mock_ocr_instance
        assert handler.neo4j_uri == mock_config.neo4j_uri
        assert handler.neo4j_username == mock_config.neo4j_username
        assert handler.neo4j_password == mock_config.neo4j_password
        assert handler.deepinfra_api_token == mock_config.deepinfra_api_token
    
    @patch('src.handlers.knowledge_graph_handler.GraphDatabase')
    @patch('src.handlers.knowledge_graph_handler.Neo4jGraph')
    @patch('src.handlers.knowledge_graph_handler.PaddleOCR')
    def test_init_connection_error(self, mock_ocr, mock_neo4j_graph, mock_graph_db, mock_config):
        """Test KnowledgeGraphHandler initialization with connection error"""
        # Setup mocks to raise error
        mock_graph_db.driver.side_effect = Exception("Connection failed")
        
        # Test that ConnectionError is raised
        with pytest.raises(ConnectionError) as excinfo:
            handler = KnowledgeGraphHandler(mock_config)
        
        # Verify the error message
        assert "Unable to connect" in str(excinfo.value)
        
    @patch('src.handlers.knowledge_graph_handler.GraphDatabase')
    @patch('src.handlers.knowledge_graph_handler.Neo4jGraph')
    @patch('src.handlers.knowledge_graph_handler.PaddleOCR')
    @patch('src.handlers.knowledge_graph_handler.fitz.open')
    @patch('src.handlers.knowledge_graph_handler.PdfReader')
    @patch('src.handlers.knowledge_graph_handler.RecursiveCharacterTextSplitter')
    @patch('src.handlers.knowledge_graph_handler.ChatGroq')
    @patch('src.handlers.knowledge_graph_handler.LLMGraphTransformer')
    def test_process_document(self, mock_transformer, mock_chatgroq, mock_splitter, mock_pdf_reader,  
                             mock_fitz_open, mock_ocr, mock_neo4j_graph, mock_graph_db, mock_config):
        """Test document processing"""
        # Setup mocks
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver
        
        mock_graph = MagicMock()
        mock_neo4j_graph.return_value = mock_graph
        
        mock_ocr_instance = MagicMock()
        mock_ocr.return_value = mock_ocr_instance
        mock_ocr_instance.ocr.return_value = [
            [
                [[(0, 0), (100, 0), (100, 20), (0, 20)], ("Sample Text", 0.99)],
                [[(0, 30), (100, 30), (100, 50), (0, 50)], ("More Text", 0.95)]
            ]
        ]
        
        # Mock PDF document and text extraction
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Extracted text from PDF"
        mock_doc.__iter__.return_value = [mock_page]
        mock_fitz_open.return_value = mock_doc
        
        # Mock PDF reader
        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock(), MagicMock()]
        mock_reader.pages[0].extract_text.return_value = "Text from page 1"
        mock_reader.pages[1].extract_text.return_value = "Text from page 2"
        mock_pdf_reader.return_value = mock_reader
        
        # Mock text splitter
        mock_splitter_instance = MagicMock()
        mock_splitter_instance.split_documents.return_value = [
            MagicMock(page_content="Split text 1"),
            MagicMock(page_content="Split text 2")
        ]
        mock_splitter.return_value = mock_splitter_instance
        
        # Mock ChatGroq
        mock_llm = MagicMock()
        mock_chatgroq.return_value = mock_llm
        
        # Mock LLMGraphTransformer
        mock_transformer_instance = MagicMock()
        mock_transformer.return_value = mock_transformer_instance
        
        # Mock session
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Initialize handler
        handler = KnowledgeGraphHandler(mock_config)
        
        # Test process_document
        pdf_bytes = b'mock pdf content'
        handler.process_document(pdf_bytes)
        
        # Verify method calls
        mock_fitz_open.assert_called_once()
        mock_pdf_reader.assert_called_once()
        mock_splitter.assert_called_once()
        mock_splitter_instance.split_documents.assert_called_once()
        mock_transformer.assert_called_once()
        mock_transformer_instance.convert.assert_called_once()
        mock_session.execute_write.assert_called()
        
    @patch('src.handlers.knowledge_graph_handler.GraphDatabase')
    @patch('src.handlers.knowledge_graph_handler.Neo4jGraph')
    @patch('src.handlers.knowledge_graph_handler.PaddleOCR')
    @patch('builtins.open', new_callable=mock_open, read_data="text data")
    def test_create_fulltext_index(self, mock_file_open, mock_ocr, mock_neo4j_graph, mock_graph_db, mock_config):
        """Test creating fulltext index"""
        # Setup mocks
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver
        
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Initialize handler
        handler = KnowledgeGraphHandler(mock_config)
        
        # Test create_fulltext_index
        handler.create_fulltext_index()
        
        # Verify session execution
        mock_session.run.assert_called()
        
    @patch('src.handlers.knowledge_graph_handler.GraphDatabase')
    @patch('src.handlers.knowledge_graph_handler.Neo4jGraph')
    @patch('src.handlers.knowledge_graph_handler.PaddleOCR')
    def test_create_constraints(self, mock_ocr, mock_neo4j_graph, mock_graph_db, mock_config):
        """Test creating constraints"""
        # Setup mocks
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver
        
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Initialize handler
        handler = KnowledgeGraphHandler(mock_config)
        
        # Test create_constraints
        handler.create_constraints()
        
        # Verify session execution
        mock_session.run.assert_called()
    
    @patch('src.handlers.knowledge_graph_handler.GraphDatabase')
    @patch('src.handlers.knowledge_graph_handler.Neo4jGraph')
    @patch('src.handlers.knowledge_graph_handler.PaddleOCR')
    @patch('src.handlers.knowledge_graph_handler.fitz.open')
    def test_extract_tables_from_pdf(self, mock_fitz_open, mock_ocr, mock_neo4j_graph, mock_graph_db, mock_config):
        """Test extracting tables from PDF"""
        # Setup mocks
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver
        
        # Mock document with tables
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Extracted text from PDF"
        mock_page.find_tables.return_value = MagicMock()
        mock_page.find_tables.return_value.tables = [
            [["Header1", "Header2"], ["Value1", "Value2"]]
        ]
        mock_doc.__iter__.return_value = [mock_page]
        mock_fitz_open.return_value = mock_doc
        
        # Initialize handler
        handler = KnowledgeGraphHandler(mock_config)
        
        # Test extract_tables_from_pdf
        pdf_bytes = b'mock pdf content'
        tables = handler.extract_tables_from_pdf(pdf_bytes)
        
        # Verify results
        assert len(tables) > 0
        mock_fitz_open.assert_called_once()
        mock_page.find_tables.assert_called_once()
        
    @patch('src.handlers.knowledge_graph_handler.GraphDatabase')
    @patch('src.handlers.knowledge_graph_handler.Neo4jGraph')
    @patch('src.handlers.knowledge_graph_handler.PaddleOCR')
    def test_extract_text_with_ocr(self, mock_ocr, mock_neo4j_graph, mock_graph_db, mock_config):
        """Test extracting text with OCR"""
        # Setup mocks
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver
        
        # Mock OCR results
        mock_ocr_instance = MagicMock()
        mock_ocr.return_value = mock_ocr_instance
        mock_ocr_instance.ocr.return_value = [
            [
                [[(0, 0), (100, 0), (100, 20), (0, 20)], ("Sample OCR Text", 0.95)]
            ]
        ]
        
        # Initialize handler
        handler = KnowledgeGraphHandler(mock_config)
        
        # Test extract_text_with_ocr
        image_data = b'mock image data'
        text = handler.extract_text_with_ocr(image_data)
        
        # Verify results
        assert "Sample OCR Text" in text
        mock_ocr_instance.ocr.assert_called_once()
        
    @patch('src.handlers.knowledge_graph_handler.GraphDatabase')
    @patch('src.handlers.knowledge_graph_handler.Neo4jGraph')
    @patch('src.handlers.knowledge_graph_handler.PaddleOCR')
    def test_clear_graph(self, mock_ocr, mock_neo4j_graph, mock_graph_db, mock_config):
        """Test clearing the graph"""
        # Setup mocks
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver
        
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Initialize handler
        handler = KnowledgeGraphHandler(mock_config)
        
        # Test clear_graph
        handler.clear_graph()
        
        # Verify session execution
        mock_session.run.assert_called_with("MATCH (n) DETACH DELETE n")
        
    @patch('src.handlers.knowledge_graph_handler.GraphDatabase')
    @patch('src.handlers.knowledge_graph_handler.Neo4jGraph')
    @patch('src.handlers.knowledge_graph_handler.PaddleOCR')
    def test_get_entity_neighbors(self, mock_ocr, mock_neo4j_graph, mock_graph_db, mock_config):
        """Test getting entity neighbors"""
        # Setup mocks
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver
        
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([
            {"entity": "Entity1", "neighbor": "Neighbor1", "relationship": "RELATED_TO"},
            {"entity": "Entity1", "neighbor": "Neighbor2", "relationship": "PART_OF"}
        ]))
        mock_session.run.return_value = mock_result
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Initialize handler
        handler = KnowledgeGraphHandler(mock_config)
        
        # Test get_entity_neighbors
        neighbors = handler.get_entity_neighbors("Entity1")
        
        # Verify results and session execution
        assert len(neighbors) == 2
        mock_session.run.assert_called_once()
        assert "Neighbor1" in str(neighbors)
        assert "Neighbor2" in str(neighbors)
        assert "RELATED_TO" in str(neighbors)
        assert "PART_OF" in str(neighbors)

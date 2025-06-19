"""
Unit tests for MongoDBHandler
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.mongo_service import MongoDBHandler

class TestMongoDBHandler:
    """Tests for the MongoDBHandler class"""
    
    @patch('src.services.mongo_service.MongoClient')
    def test_init(self, mock_client):
        """Test initialization of MongoDBHandler"""
        # Mock MongoDB client
        mock_client_instance = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()
        
        # Chain the mocks
        mock_client.return_value = mock_client_instance
        mock_client_instance.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        
        # Initialize handler
        handler = MongoDBHandler()
        
        # Verify client is created
        mock_client.assert_called_once()
        
        # Verify DB and collection references
        assert handler.client == mock_client_instance
        assert handler.glossary_db == mock_client_instance.__getitem__.return_value
        assert handler.glossary_collection == mock_db.__getitem__.return_value
        assert handler.metadata_db == mock_client_instance.__getitem__.return_value
        assert handler.metadata_collection == mock_db.__getitem__.return_value

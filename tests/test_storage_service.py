"""
Unit tests for StorageService
"""
import pytest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
import hashlib
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.storage_service import StorageService

class TestStorageService:
    """Tests for the StorageService class"""
    
    @pytest.fixture
    def mock_blob_service(self):
        """Mock Azure Blob Service"""
        with patch('src.services.storage_service.BlobServiceClient') as mock_service:
            # Mock the container client
            mock_container = MagicMock()
            
            # Mock the service client
            mock_client = MagicMock()
            mock_client.get_container_client.return_value = mock_container
            mock_service.from_connection_string.return_value = mock_client
            
            yield mock_service
    
    @pytest.fixture
    def mock_mongo_client(self):
        """Mock MongoDB client"""
        with patch('src.services.storage_service.MongoClient') as mock_client:
            # Mock collections
            mock_metadata_collection = MagicMock()
            mock_chat_collection = MagicMock()
            
            # Mock DBs
            mock_metadata_db = MagicMock()
            mock_metadata_db.__getitem__.return_value = mock_metadata_collection
            mock_chat_db = MagicMock()
            mock_chat_db.__getitem__.return_value = mock_chat_collection
            
            # Mock client
            mock_client_instance = MagicMock()
            mock_client_instance.__getitem__.side_effect = lambda x: mock_metadata_db if x == "metadata_db" else mock_chat_db
            mock_client.return_value = mock_client_instance
            
            yield mock_client
    
    def test_init(self, mock_blob_service, mock_mongo_client):
        """Test initialization of StorageService"""
        # Initialize service
        service = StorageService()
        
        # Verify Azure client initialization
        mock_blob_service.from_connection_string.assert_called_once()
        assert service.blob_service_client == mock_blob_service.from_connection_string.return_value
        assert service.container_client == service.blob_service_client.get_container_client.return_value
        
        # Verify MongoDB initialization
        mock_mongo_client.assert_called_once()
        assert service.mongo_client == mock_mongo_client.return_value
        assert service.datetime == datetime
    
    @patch('src.services.storage_service.hashlib')
    @patch('src.services.storage_service.io.BytesIO')
    def test_upload_pdf_and_metadata(self, mock_bytesio, mock_hashlib, mock_blob_service, mock_mongo_client):
        """Test uploading PDF and metadata"""
        # Mock BytesIO
        mock_bytesio_instance = MagicMock()
        mock_bytesio.return_value = mock_bytesio_instance
        
        # Mock hashlib
        mock_hash = MagicMock()
        mock_hash.hexdigest.return_value = "test_hash"
        mock_hashlib.sha256.return_value = mock_hash
        
        # Mock MongoDB collection findOne
        service = StorageService()
        service.metadata_collection.find_one = MagicMock(return_value=None)  # No existing document
        service.metadata_collection.insert_one = MagicMock()
        
        # Mock blob client
        service.container_client.get_blob_client = MagicMock()
        mock_blob_client = MagicMock()
        service.container_client.get_blob_client.return_value = mock_blob_client
        
        # Test uploading a new file
        pdf_bytes = b"test pdf content"
        result, status = service.upload_pdf_and_metadata(
            pdf_bytes=pdf_bytes,
            original_filename="test.pdf",
            content_type="application/pdf"
        )
        
        # Verify hash was calculated
        mock_hashlib.sha256.assert_called_once_with(pdf_bytes)
        
        # Verify MongoDB was checked for existing doc
        service.metadata_collection.find_one.assert_called_once()
        
        # Verify blob was uploaded
        mock_blob_client.upload_blob.assert_called_once()
        
        # Verify metadata was stored
        service.metadata_collection.insert_one.assert_called_once()
        
        # Verify result contains document_id
        assert "document_id" in result
        assert status == 201
    
    def test_list_documents(self, mock_blob_service, mock_mongo_client):
        """Test listing documents"""
        # Mock MongoDB collection find
        service = StorageService()
        mock_cursor = [
            {"_id": "id1", "original_filename": "doc1.pdf", "upload_date": datetime.now()},
            {"_id": "id2", "original_filename": "doc2.pdf", "upload_date": datetime.now()}
        ]
        service.metadata_collection.find = MagicMock(return_value=mock_cursor)
        
        # Test listing documents
        result, status = service.list_documents()
        
        # Verify MongoDB was queried
        service.metadata_collection.find.assert_called_once()
        
        # Verify result structure
        assert len(result["documents"]) == 2
        assert result["documents"][0]["id"] == "id1"
        assert result["documents"][1]["id"] == "id2"
        assert status == 200

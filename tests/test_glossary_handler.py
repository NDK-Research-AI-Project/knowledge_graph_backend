"""
Unit tests for GlossaryHandler
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock, mock_open, call
import sys
import os
from datetime import datetime, UTC
from bson import ObjectId

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.handlers.glossary_handler import GlossaryHandler

class TestGlossaryHandler:
    """Tests for the GlossaryHandler class"""
    
    @pytest.fixture
    def mock_mongo_client(self):
        """Mock MongoDB client"""
        with patch('src.handlers.glossary_handler.MongoClient') as mock_client:
            # Mock the collection.find() method
            mock_collection = MagicMock()
            mock_collection.find.return_value = [
                {"_id": ObjectId("60d5ec9bf682fbd12a0944c8"), "term": "test1", "definition": "definition1", "createdAt": datetime.now(UTC)},
                {"_id": ObjectId("60d5ec9bf682fbd12a0944c9"), "term": "test2", "definition": "definition2", "createdAt": datetime.now(UTC)}
            ]
            mock_collection.insert_many = MagicMock()
            mock_collection.insert_many.return_value = MagicMock()
            mock_collection.insert_many.return_value.inserted_ids = ["id1", "id2"]
            
            mock_collection.update_one = MagicMock()
            mock_collection.update_one.return_value = MagicMock()
            mock_collection.update_one.return_value.matched_count = 1
            
            mock_collection.delete_one = MagicMock()
            mock_collection.delete_one.return_value = MagicMock()
            mock_collection.delete_one.return_value.deleted_count = 1
            
            # Mock the db and collection access
            mock_db = MagicMock()
            mock_db.__getitem__.return_value = mock_collection
            
            # Mock the client
            mock_client_instance = MagicMock()
            mock_client_instance.__getitem__.return_value = mock_db
            mock_client.return_value = mock_client_instance
            
            yield mock_client

    def test_init(self, mock_mongo_client):
        """Test initialization of GlossaryHandler"""
        handler = GlossaryHandler()
        
        # Verify cache is created
        assert isinstance(handler.glossary_cache, pd.DataFrame)
        assert len(handler.glossary_cache) == 2
        assert handler.glossary_cache.iloc[0]["term"] == "test1"
        assert handler.glossary_cache.iloc[0]["definition"] == "definition1"
        assert handler.last_updated is not None

    def test_refresh_cache(self, mock_mongo_client):
        """Test refreshing the glossary cache"""
        handler = GlossaryHandler()
        
        # Mock a new dataset for refreshing
        handler.glossary_collection.find.return_value = [
            {"term": "new1", "definition": "new_def1"},
            {"term": "new2", "definition": "new_def2"},
            {"term": "new3", "definition": "new_def3"}
        ]
        
        # Record the previous update time
        prev_update_time = handler.last_updated
        
        # Refresh the cache
        handler._refresh_cache()
        
        # Verify cache is updated
        assert len(handler.glossary_cache) == 3
        assert handler.glossary_cache.iloc[0]["term"] == "new1"
        assert handler.last_updated > prev_update_time

    def test_add_glossary_items(self, mock_mongo_client):
        """Test adding glossary items"""
        handler = GlossaryHandler()
        
        # Test adding items
        items = [
            {"term": "term1", "definition": "def1"},
            {"term": "term2", "definition": "def2"}
        ]
        
        result = handler.add_glossary_items(items)
        
        # Verify items were added
        handler.glossary_collection.insert_many.assert_called_once()
        assert "message" in result
        assert "2 glossary items saved" in result["message"]
        
    @patch('src.handlers.glossary_handler.logger')
    def test_add_glossary_items_with_invalid_items(self, mock_logger, mock_mongo_client):
        """Test adding invalid glossary items"""
        handler = GlossaryHandler()
        
        handler.glossary_collection.insert_many.reset_mock()
        # Test with invalid items
        items = [
            {"definition": "Missing term"},
            {"term": "Missing definition"}
        ]
        
        result = handler.add_glossary_items(items)
        
        # No items should be inserted
        handler.glossary_collection.insert_many.assert_not_called()
        assert "message" in result
        assert "No valid glossary items" in result["message"]
        mock_logger.error.assert_called()
        
    def test_get_all_glossary_items(self, mock_mongo_client):
        """Test getting all glossary items"""
        handler = GlossaryHandler()
        
        # Setup the mock to return documents with various fields
        handler.glossary_collection.find.return_value = [
            {"_id": ObjectId("60d5ec9bf682fbd12a0944c8"), "term": "test1", "definition": "definition1", "createdAt": datetime.now(UTC)},
            {"_id": ObjectId("60d5ec9bf682fbd12a0944c9"), "term": "test2", "definition": "definition2", "createdAt": datetime.now(UTC), "updatedAt": datetime.now(UTC)}
        ]
        
        items = handler.get_all_glossary_items()
        
        # Verify the items are returned correctly
        assert len(items) == 2
        assert items[0]["term"] == "test1"
        assert items[1]["term"] == "test2"
        assert "_id" in items[0]
        assert "_id" in items[1]
        assert "createdAt" in items[0]
        assert "updatedAt" in items[1]
        
    @patch('src.handlers.glossary_handler.process')
    def test_get_glossary_for_query_with_matches(self, mock_process, mock_mongo_client):
        """Test getting glossary items for a query with matches"""
        handler = GlossaryHandler()
        
        # Mock the DataFrame with sample data
        handler.glossary_cache = pd.DataFrame([
            {"term": "diabetes", "definition": "A metabolic disease"},
            {"term": "hypertension", "definition": "High blood pressure"}
        ])
        
        # Mock fuzzy matching to return a match
        mock_process.extract.return_value = [
            ("diabetes", 90, 0)  # term, score, index
        ]
        
        result = handler.get_glossary_for_query("What is diabete?")
        
        # Verify the result contains the matched term
        assert "diabetes" in result
        assert "A metabolic disease" in result
        
    @patch('src.handlers.glossary_handler.process')
    def test_get_glossary_for_query_without_matches(self, mock_process, mock_mongo_client):
        """Test getting glossary items for a query with no matches"""
        handler = GlossaryHandler()
        
        # Mock the DataFrame with sample data
        handler.glossary_cache = pd.DataFrame([
            {"term": "diabetes", "definition": "A metabolic disease"},
            {"term": "hypertension", "definition": "High blood pressure"}
        ])
        
        # Mock fuzzy matching to return no matches
        mock_process.extract.return_value = []
        
        result = handler.get_glossary_for_query("Something unrelated")
        
        # Verify the result is empty
        assert result == ""
        
    def test_get_glossary_for_query_empty_cache(self, mock_mongo_client):
        """Test getting glossary items with empty cache"""
        handler = GlossaryHandler()
        
        # Set an empty cache
        handler.glossary_cache = pd.DataFrame(columns=["term", "definition"])
        handler.glossary_collection.find.return_value = []
        
        result = handler.get_glossary_for_query("Any query")
        
        # Verify the result is empty
        assert result == ""
        
    def test_update_glossary_item_success(self, mock_mongo_client):
        """Test successfully updating a glossary item"""
        handler = GlossaryHandler()
        
        valid_id = "60d5ec9bf682fbd12a0944c8"
        updated_data = {
            "term": "Updated Term",
            "definition": "Updated Definition"
        }
        
        result = handler.update_glossary_item(valid_id, updated_data)
        
        # Verify the update was successful
        assert "message" in result
        assert "updated successfully" in result["message"]
        handler.glossary_collection.update_one.assert_called_once()
        
    def test_update_glossary_item_invalid_id(self, mock_mongo_client):
        """Test updating a glossary item with invalid ID"""
        handler = GlossaryHandler()
        
        invalid_id = "invalid_id"
        updated_data = {
            "term": "Updated Term"
        }
        
        result = handler.update_glossary_item(invalid_id, updated_data)
        
        # Verify the error response
        assert "error" in result
        assert "Invalid glossary item ID format" in result["error"]
        handler.glossary_collection.update_one.assert_not_called()
        
    def test_update_glossary_item_not_found(self, mock_mongo_client):
        """Test updating a non-existent glossary item"""
        handler = GlossaryHandler()
        
        valid_id = "60d5ec9bf682fbd12a0944c8"
        updated_data = {
            "term": "Updated Term"
        }
        
        # Mock the update to indicate no documents matched
        handler.glossary_collection.update_one.return_value.matched_count = 0
        
        result = handler.update_glossary_item(valid_id, updated_data)
        
        # Verify the error response
        assert "error" in result
        assert "not found" in result["error"]
        
    def test_update_glossary_item_exception(self, mock_mongo_client):
        """Test exception handling during glossary item update"""
        handler = GlossaryHandler()
        
        valid_id = "60d5ec9bf682fbd12a0944c8"
        updated_data = {
            "term": "Updated Term"
        }
        
        # Mock update to raise an exception
        handler.glossary_collection.update_one.side_effect = Exception("Test exception")
        
        result = handler.update_glossary_item(valid_id, updated_data)
        
        # Verify the error response
        assert "error" in result
        assert "Error updating glossary item" in result["error"]
        
    def test_update_glossary_item_no_valid_fields(self, mock_mongo_client):
        """Test updating with no valid fields"""
        handler = GlossaryHandler()
        
        valid_id = "60d5ec9bf682fbd12a0944c8"
        updated_data = {
            "invalid_field": "Some value"  # Not a valid field
        }
        
        result = handler.update_glossary_item(valid_id, updated_data)
        
        # Verify the error response
        assert "error" in result
        assert "No valid fields to update" in result["error"]
        handler.glossary_collection.update_one.assert_not_called()
        
    def test_delete_glossary_item_success(self, mock_mongo_client):
        """Test successfully deleting a glossary item"""
        handler = GlossaryHandler()
        
        valid_id = "60d5ec9bf682fbd12a0944c8"
        
        result = handler.delete_glossary_item(valid_id)
        
        # Verify the delete was successful
        assert "message" in result
        assert "deleted successfully" in result["message"]
        handler.glossary_collection.delete_one.assert_called_once()
        
    def test_delete_glossary_item_invalid_id(self, mock_mongo_client):
        """Test deleting a glossary item with invalid ID"""
        handler = GlossaryHandler()
        
        invalid_id = "invalid_id"
        
        result = handler.delete_glossary_item(invalid_id)
        
        # Verify the error response
        assert "error" in result
        assert "Invalid glossary item ID format" in result["error"]
        handler.glossary_collection.delete_one.assert_not_called()
        
    def test_delete_glossary_item_not_found(self, mock_mongo_client):
        """Test deleting a non-existent glossary item"""
        handler = GlossaryHandler()
        
        valid_id = "60d5ec9bf682fbd12a0944c8"
        
        # Mock the delete to indicate no documents matched
        handler.glossary_collection.delete_one.return_value.deleted_count = 0
        
        result = handler.delete_glossary_item(valid_id)
        
        # Verify the error response
        assert "error" in result
        assert "not found" in result["error"]
        
    def test_delete_glossary_item_exception(self, mock_mongo_client):
        """Test exception handling during glossary item deletion"""
        handler = GlossaryHandler()
        
        valid_id = "60d5ec9bf682fbd12a0944c8"
        
        # Mock delete to raise an exception
        handler.glossary_collection.delete_one.side_effect = Exception("Test exception")
        
        result = handler.delete_glossary_item(valid_id)
        
        # Verify the error response
        assert "error" in result
        assert "Error deleting glossary item" in result["error"]

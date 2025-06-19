"""
Tests for the API endpoints in main.py
"""
import pytest
import json
import sys
import os
from unittest.mock import patch, MagicMock, mock_open
from bson import ObjectId
import io

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import main

@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    main.app.config['TESTING'] = True
    with main.app.test_client() as client:
        yield client

class TestMainAPI:
    """Tests for the main.py API endpoints"""

    @patch('main.guardrail_handler')
    @patch('main.answer_generator')
    @patch('main.storage_service')
    def test_query_endpoint_safe_query(self, mock_storage, mock_answer_generator, mock_guardrail, client):
        """Test the query endpoint with a safe query"""
        # Setup mocks
        mock_guardrail.is_safe_query.return_value = (True, "")
        
        mock_answer_generator.generate_answer.return_value = {
            "answer": "test answer",
            "explanation": ["Step 1", "Step 2"]
        }
        
        # Mock save_chat_message by patching it directly in main module
        with patch.object(main, 'save_chat_message') as mock_save:
            mock_save.return_value = {"_id": "test_id"}
            
            # Make the API call
            response = client.post(
                '/api/knowledge-graph/query',
                data=json.dumps({'question': 'safe query'}),
                content_type='application/json'
            )
            
            # Verify response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["answer"] == "test answer"
            assert data["explanation"] == ["Step 1", "Step 2"]
            assert "session_id" in data
            
            # Verify guardrail was called
            mock_guardrail.is_safe_query.assert_called_once_with('safe query')
            
            # Verify answer generation was called
            mock_answer_generator.generate_answer.assert_called_once_with('safe query')
            
            # Verify chat message was saved
            assert mock_save.call_count == 2  # Once for user, once for assistant

    @patch('main.guardrail_handler')
    @patch('main.answer_generator')
    def test_query_endpoint_unsafe_query(self, mock_answer_generator, mock_guardrail, client):
        """Test the query endpoint with an unsafe query"""
        # Setup mocks
        mock_guardrail.is_safe_query.return_value = (False, "Contains harmful content")
        
        # Make the API call
        response = client.post(
            '/api/knowledge-graph/query',
            data=json.dumps({'question': 'unsafe query'}),
            content_type='application/json'
        )
        
        # Verify response
        assert response.status_code == 403
        data = json.loads(response.data)
        assert "error" in data
        assert "safety system" in data["error"]
        assert "details" in data
        
        # Verify guardrail was called
        mock_guardrail.is_safe_query.assert_called_once_with('unsafe query')
        
        # Verify answer generation was NOT called
        mock_answer_generator.generate_answer.assert_not_called()

    @patch('main.guardrail_handler')
    @patch('main.answer_generator')
    @patch('main.storage_service')
    def test_chat_query_endpoint_safe_query(self, mock_storage, mock_answer_generator, mock_guardrail, client):
        """Test the chat query endpoint with a safe query"""
        # Setup mocks
        mock_guardrail.is_safe_query.return_value = (True, "")
        
        mock_answer_generator.generate_answer.return_value = {
            "answer": "test answer",
            "explanation": ["Step 1", "Step 2"]
        }
        
        # Mock save_chat_message and serialize_message directly in main module
        with patch.object(main, 'save_chat_message') as mock_save, \
             patch.object(main, 'serialize_message') as mock_serialize:
            
            mock_save.return_value = {"_id": "test_id", "content": "test content"}
            mock_serialize.return_value = {"id": "test_id", "content": "test content"}
            
            # Make the API call
            response = client.post(
                '/api/chat/test_session/query',
                data=json.dumps({'question': 'safe chat query'}),
                content_type='application/json'
            )
            
            # Verify response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["answer"] == "test answer"
            assert data["session_id"] == "test_session"
            assert "user_message" in data
            assert "assistant_message" in data
            
            # Verify guardrail was called
            mock_guardrail.is_safe_query.assert_called_once_with('safe chat query')
            
            # Verify answer generation was called
            mock_answer_generator.generate_answer.assert_called_once_with('safe chat query')
            
            # Verify chat message was saved
            assert mock_save.call_count == 2  # Once for user, once for assistant

    @patch('main.guardrail_handler')
    @patch('main.answer_generator')
    def test_chat_query_endpoint_unsafe_query(self, mock_answer_generator, mock_guardrail, client):
        """Test the chat query endpoint with an unsafe query"""
        # Setup mocks
        mock_guardrail.is_safe_query.return_value = (False, "Contains harmful content")
        
        # Make the API call
        response = client.post(
            '/api/chat/test_session/query',
            data=json.dumps({'question': 'unsafe chat query'}),
            content_type='application/json'
        )
        
        # Verify response
        assert response.status_code == 403
        data = json.loads(response.data)
        assert "error" in data
        assert "safety system" in data["error"]
        
        # Verify guardrail was called
        mock_guardrail.is_safe_query.assert_called_once_with('unsafe chat query')
        
        # Verify answer generation was NOT called
        mock_answer_generator.generate_answer.assert_not_called()
        
    def test_query_endpoint_missing_question(self, client):
        """Test the query endpoint with missing question field"""
        # Make the API call without a question
        response = client.post(
            '/api/knowledge-graph/query',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "required" in data["error"]
        
    @patch('main.guardrail_handler')
    @patch('main.answer_generator')
    @patch('main.storage_service')
    def test_query_endpoint_with_session_id(self, mock_storage, mock_answer_generator, mock_guardrail, client):
        """Test the query endpoint with provided session_id"""
        # Setup mocks
        mock_guardrail.is_safe_query.return_value = (True, "")
        
        mock_answer_generator.generate_answer.return_value = {
            "answer": "test answer",
            "explanation": ["Step 1", "Step 2"]
        }
        
        # Mock save_chat_message
        with patch.object(main, 'save_chat_message') as mock_save:
            mock_save.return_value = {"_id": "test_id"}
            
            # Make the API call with a session_id
            response = client.post(
                '/api/knowledge-graph/query',
                data=json.dumps({'question': 'query with session', 'session_id': 'existing_session_id'}),
                content_type='application/json'
            )
            
            # Verify response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["session_id"] == "existing_session_id"
            
    @patch('main.handler')
    @patch('main.storage_service')
    def test_process_document_endpoint_success(self, mock_storage, mock_handler, client):
        """Test process document endpoint success"""
        # Mock file data
        mock_file_data = b'PDF file content'
        mock_file = (io.BytesIO(mock_file_data), 'test.pdf', 'application/pdf')
        
        # Mock storage service
        mock_storage.upload_pdf_and_metadata.return_value = ({"message": "File uploaded"}, 200)
        
        # Make the API call
        response = client.post(
            '/api/knowledge-graph/process-document',
            data={'file': mock_file},
            content_type='multipart/form-data'
        )
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["message"] == "File uploaded"
        
        # Verify handler was called
        mock_handler.process_document.assert_called_once()
        mock_storage.upload_pdf_and_metadata.assert_called_once()
        
    @patch('main.handler')
    @patch('main.storage_service')
    def test_process_document_endpoint_file_exists(self, mock_storage, mock_handler, client):
        """Test process document endpoint when file already exists"""
        # Mock file data
        mock_file_data = b'PDF file content'
        mock_file = (io.BytesIO(mock_file_data), 'test.pdf', 'application/pdf')
        
        # Mock storage service
        mock_storage.upload_pdf_and_metadata.return_value = ({"message": "File already exists."}, 409)
        
        # Make the API call
        response = client.post(
            '/api/knowledge-graph/process-document',
            data={'file': mock_file},
            content_type='multipart/form-data'
        )
        
        # Verify response
        assert response.status_code == 409
        data = json.loads(response.data)
        assert "already exists" in data["message"]
        
        # Verify handler was still called to process the document
        mock_handler.process_document.assert_called_once()
        
    def test_process_document_endpoint_no_file(self, client):
        """Test process document endpoint with no file"""
        # Make the API call with no file
        response = client.post(
            '/api/knowledge-graph/process-document',
            data={},
            content_type='multipart/form-data'
        )
        
        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "No file part" in data["message"]
        
    def test_process_document_endpoint_empty_filename(self, client):
        """Test process document endpoint with empty filename"""
        # Make the API call with empty filename
        mock_file = (io.BytesIO(b''), '', 'application/pdf')
        response = client.post(
            '/api/knowledge-graph/process-document',
            data={'file': mock_file},
            content_type='multipart/form-data'
        )
        
        # Verify response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "No selected file" in data["message"]
        
    @patch('main.storage_service')
    def test_get_all_documents_endpoint(self, mock_storage, client):
        """Test get all documents endpoint"""
        # Mock storage service
        mock_storage.list_documents.return_value = ({"documents": ["doc1", "doc2"]}, 200)
        
        # Make the API call
        response = client.get('/api/documents')
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "documents" in data
        assert data["documents"] == ["doc1", "doc2"]
        
    @patch('main.storage_service')
    def test_get_all_documents_endpoint_error(self, mock_storage, client):
        """Test get all documents endpoint with error"""
        # Mock storage service to raise exception
        mock_storage.list_documents.side_effect = Exception("Database error")
        
        # Make the API call
        response = client.get('/api/documents')
        
        # Verify response
        assert response.status_code == 500
        data = json.loads(response.data)
        assert "message" in data
        assert "Database error" in data["message"]

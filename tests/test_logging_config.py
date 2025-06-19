"""
Unit tests for logging configuration
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os
import logging

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config.logging_config import setup_logging

class TestLoggingConfig:
    """Tests for the logging configuration"""
    
    @patch('src.config.logging_config.SocketHandler')
    @patch('src.config.logging_config.logging.StreamHandler')
    def test_setup_logging(self, mock_stream_handler, mock_socket_handler):
        """Test setting up logging"""
        # Mock handlers
        mock_socket_instance = MagicMock()
        mock_stream_instance = MagicMock()
        mock_socket_handler.return_value = mock_socket_instance
        mock_stream_handler.return_value = mock_stream_instance
        
        # Test config
        config = {
            'logstash_host': 'localhost',
            'logstash_port': 5044,
            'log_level': 'INFO',
            'app_name': 'test-app'
        }
        
        # Call setup_logging with the test config
        logger = setup_logging(config)
        
        # Verify the logger is configured correctly
        mock_socket_handler.assert_called_once_with('localhost', 5044)
        mock_stream_handler.assert_called_once()
        
        # Verify formatters are set
        mock_socket_instance.setFormatter.assert_called_once()
        mock_stream_instance.setFormatter.assert_called_once()
        
        # Verify we have a LoggerAdapter
        assert isinstance(logger, logging.LoggerAdapter)
        assert logger.extra['app_name'] == 'test-app'
        
    @patch('src.config.logging_config.SocketHandler')
    @patch('src.config.logging_config.logging.StreamHandler')
    def test_setup_logging_debug_level(self, mock_stream_handler, mock_socket_handler):
        """Test setting up logging with DEBUG level"""
        # Mock handlers
        mock_socket_instance = MagicMock()
        mock_stream_instance = MagicMock()
        mock_socket_handler.return_value = mock_socket_instance
        mock_stream_handler.return_value = mock_stream_instance
        
        # Test config with DEBUG level
        config = {
            'logstash_host': 'localhost',
            'logstash_port': 5044,
            'log_level': 'DEBUG',
            'app_name': 'test-app'
        }
        
        # Clear existing handlers
        logger = logging.getLogger('document-chat')
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Call setup_logging with the DEBUG config
        logger = setup_logging(config)
        
        # Verify the logger has DEBUG level
        assert logger.logger.level == logging.DEBUG

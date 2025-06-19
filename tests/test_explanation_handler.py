"""
Unit tests for ExplanationHandler
"""
import pytest
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.handlers.explanation_handler import ExplanationHandler

class TestExplanationHandler:
    """Tests for the ExplanationHandler class"""

    def test_init(self):
        """Test initialization of ExplanationHandler"""
        handler = ExplanationHandler()
        assert handler.steps == []

    def test_add_step(self):
        """Test adding a step to the explanation"""
        handler = ExplanationHandler()
        handler.add_step("Step 1")
        assert len(handler.steps) == 1
        assert handler.steps[0] == "Step 1"
        
        # Add another step
        handler.add_step("Step 2")
        assert len(handler.steps) == 2
        assert handler.steps[1] == "Step 2"

    def test_get_explanation(self):
        """Test getting the explanation"""
        handler = ExplanationHandler()
        handler.add_step("Step 1")
        handler.add_step("Step 2")
        
        explanation = handler.get_explanation()
        assert explanation == ["Step 1", "Step 2"]
        
        # Verify that the returned list is a copy
        explanation.append("Modified")
        assert handler.get_explanation() == ["Step 1", "Step 2"]

    def test_clear(self):
        """Test clearing the explanation"""
        handler = ExplanationHandler()
        handler.add_step("Step 1")
        handler.add_step("Step 2")
        
        handler.clear()
        assert handler.steps == []
        assert handler.get_explanation() == []

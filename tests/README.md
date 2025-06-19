# Testing and Coverage

This directory contains unit tests for the knowledge graph backend application. The tests are implemented using pytest.

## Running Tests

You have two options to run the tests:

### Option 1: Using the script

For Windows users, we've provided two scripts:

#### Batch file (Command Prompt)
```
run_tests.bat
```

#### PowerShell script
```
.\run_tests.ps1
```

### Option 2: Running manually

You can also run the tests manually with pytest:

```
# Install dependencies
pip install pytest pytest-cov pytest-mock

# Run tests with coverage
python -m pytest --cov=src --cov-report=html --cov-report=term
```

## Test Coverage Report

After running the tests, the coverage report will be available in two formats:

1. **Terminal Output**: You'll see a summary of the coverage in your terminal
2. **HTML Report**: A detailed interactive HTML report is generated in the `coverage_html_report` directory

To view the HTML report, open `coverage_html_report/index.html` in your web browser.

## Test Structure

The test suite is organized as follows:

- `tests/test_guardrail_handler.py`: Tests for the GuardrailHandler class
- `tests/test_query_handler.py`: Tests for the QueryHandler class
- `tests/test_answer_generator.py`: Tests for the AnswerGenerator class
- `tests/test_main.py`: Integration tests for API endpoints

## Adding New Tests

When adding new functionality to the application, make sure to add corresponding tests to maintain good coverage. Follow these guidelines:

1. Create a new test file in the `tests` directory following the naming pattern `test_*.py`
2. Use the pytest fixtures for common setup
3. Mock external dependencies using `unittest.mock` or `pytest-mock`
4. Run the tests to ensure they pass and provide good coverage

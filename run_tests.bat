@echo off
REM Run tests with coverage and generate reports
echo Running tests with coverage...

REM Install test dependencies if not already installed
pip install pytest pytest-cov pytest-mock

REM Run tests with coverage
python -m pytest --cov=src --cov-report=html --cov-report=term

echo.
echo Coverage report has been generated.
echo HTML report is available in the coverage_html_report directory.

REM Open the coverage report if the user wants to
set /p open_report="Open HTML coverage report? (y/n): "
if /i "%open_report%"=="y" start coverage_html_report\index.html

@echo off
echo Running comprehensive test coverage report...

REM First install all the necessary packages
pip install pytest pytest-cov pytest-mock coverage

REM Clear any existing coverage data
coverage erase

REM Run the tests with coverage
pytest --cov=src --cov-report=term --cov-report=html --cov-report=xml -v

REM Display the coverage summary
echo.
echo ========== COVERAGE SUMMARY ==========
echo.
coverage report --fail-under=80

REM Check if coverage meets the 80% threshold
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo WARNING: Coverage is below 80%% threshold
    echo Review the HTML report to identify areas needing more tests
) else (
    echo.
    echo SUCCESS: Coverage meets or exceeds 80%% threshold
)

REM Open the HTML report
echo.
echo HTML coverage report generated in coverage_html_report directory
set /p open_report="Open HTML coverage report? (y/n): "
if /i "%open_report%"=="y" start coverage_html_report\index.html

echo.
echo For detailed test results, please check the terminal output above.
echo The HTML report provides an interactive view of code coverage.
echo XML report is available for CI integration.

# Run tests with coverage and generate reports
Write-Host "Running tests with coverage..." -ForegroundColor Cyan

# Install test dependencies if not already installed
pip install pytest pytest-cov pytest-mock

# Run tests with coverage
python -m pytest --cov=src --cov-report=html --cov-report=term

Write-Host "`nCoverage report has been generated." -ForegroundColor Green
Write-Host "HTML report is available in the coverage_html_report directory." -ForegroundColor Green

# Open the coverage report if the user wants to
$openReport = Read-Host "Open HTML coverage report? (y/n)"
if ($openReport -eq "y") {
    Start-Process "coverage_html_report\index.html"
}

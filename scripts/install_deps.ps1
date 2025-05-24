<#
.SYNOPSIS
    Installs Python dependencies and sets up the database.
.DESCRIPTION
    This script installs the required Python packages and initializes the database.
#>

# Stop script on first error
$ErrorActionPreference = "Stop"

# Activate virtual environment
$venvPath = ".\venv"
$activateScript = "$venvPath\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    . $activateScript
} else {
    Write-Host "Virtual environment not found. Please run .\scripts\setup.ps1 first." -ForegroundColor Red
    exit 1
}

# Install requirements
Write-Host "Installing requirements..." -ForegroundColor Cyan
pip install -r requirements.txt

# Initialize Flask-Migrate
Write-Host "Initializing database migrations..." -ForegroundColor Cyan
$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development"

# Create migrations directory if it doesn't exist
if (-not (Test-Path "migrations")) {
    flask db init
}

# Create migration and upgrade database
flask db migrate -m "Initial migration"
flask db upgrade

Write-Host "`nDependencies installed and database initialized successfully!" -ForegroundColor Green

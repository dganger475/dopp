<#
.SYNOPSIS
    Sets up the DoppleGanger application environment.
.DESCRIPTION
    This script automates the setup of the DoppleGanger application by:
    1. Creating a Python virtual environment
    2. Installing required Python packages
    3. Setting up the database
    4. Creating necessary directories
.NOTES
    File Name      : setup.ps1
    Prerequisites  : Python 3.8 or later, pip
#>

# Stop script on first error
$ErrorActionPreference = "Stop"

# Check if Python is installed
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python is not installed or not in PATH. Please install Python 3.8 or later and try again." -ForegroundColor Red
    exit 1
}

Write-Host "Python version: $pythonVersion" -ForegroundColor Cyan

# Create virtual environment if it doesn't exist
$venvPath = ".\venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv $venvPath
}

# Activate virtual environment
$activateScript = "$venvPath\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    . $activateScript
} else {
    Write-Host "Failed to activate virtual environment. Script not found: $activateScript" -ForegroundColor Red
    exit 1
}

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip

# Install required packages
Write-Host "Installing required packages..." -ForegroundColor Cyan
pip install -r requirements.txt

# Create necessary directories
$directories = @(
    "static/uploads",
    "static/extracted_faces",
    "static/profile_pics",
    "static/covers",
    "logs"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        Write-Host "Creating directory: $dir" -ForegroundColor Cyan
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Initialize the database
Write-Host "Initializing database..." -ForegroundColor Cyan
$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development"

# Run database migrations
Write-Host "Running database migrations..." -ForegroundColor Cyan
flask db upgrade

Write-Host "`nSetup complete!" -ForegroundColor Green
Write-Host "To start the application, run: .\run.ps1" -ForegroundColor Yellow

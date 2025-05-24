<#
.SYNOPSIS
    Installs and configures Redis on Windows for the DoppleGanger application.
.DESCRIPTION
    This script automates the installation of Redis on Windows and configures it to run as a service.
    It's designed to be run in an elevated PowerShell session.
.NOTES
    File Name      : install_redis.ps1
    Prerequisites  : PowerShell 5.1 or later, Administrator privileges
#>

#Requires -RunAsAdministrator

# Stop script on first error
$ErrorActionPreference = "Stop"

# Check if Chocolatey is installed
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "Chocolatey is not installed. Installing Chocolatey..." -ForegroundColor Yellow
    
    # Install Chocolatey
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
    
    # Refresh environment variables
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    
    Write-Host "Chocolatey installed successfully." -ForegroundColor Green
}

# Install Redis using Chocolatey
Write-Host "Installing Redis..." -ForegroundColor Cyan
choco install redis-64 -y --force

# Add Redis to system PATH if not already present
$redisPath = "C:\Program Files\Redis"
$envPath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")

if ($envPath -notlike "*$redisPath*") {
    Write-Host "Adding Redis to system PATH..." -ForegroundColor Cyan
    [System.Environment]::SetEnvironmentVariable("Path", $envPath + ";$redisPath", "Machine")
    $env:Path += ";$redisPath"
}

# Configure Redis to start automatically
Write-Host "Configuring Redis service..." -ForegroundColor Cyan
$serviceName = "Redis"

# Check if Redis service is already installed
$service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue

if (-not $service) {
    # Install Redis as a Windows service
    & "$redisPath\redis-server.exe" --service-install "$redisPath\redis.windows-service.conf" --loglevel verbose
    
    # Set service to start automatically
    Set-Service -Name $serviceName -StartupType Automatic
}

# Start the Redis service
Write-Host "Starting Redis service..." -ForegroundColor Cyan
Start-Service -Name $serviceName -ErrorAction SilentlyContinue

# Verify Redis is running
$redisRunning = $false
$attempts = 0
$maxAttempts = 5

while (-not $redisRunning -and $attempts -lt $maxAttempts) {
    try {
        $redisCli = & "$redisPath\redis-cli.exe" ping 2>&1
        if ($redisCli -eq "PONG") {
            $redisRunning = $true
        }
    } catch {
        # Ignore errors and retry
    }
    
    if (-not $redisRunning) {
        $attempts++
        Start-Sleep -Seconds 2
    }
}

if ($redisRunning) {
    Write-Host "Redis is now running and ready to use!" -ForegroundColor Green
    Write-Host "You can connect to it using: redis-cli" -ForegroundColor Green
    
    # Test Redis connection
    try {
        & "$redisPath\redis-cli.exe" set "doppleganger:test" "success" | Out-Null
        $result = & "$redisPath\redis-cli.exe" get "doppleganger:test"
        Write-Host "Redis test: $result" -ForegroundColor Green
    } catch {
        Write-Host "Warning: Could not verify Redis connection. Error: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "Failed to start Redis. Please check the Redis service manually." -ForegroundColor Red
    exit 1
}

# Update .env file with Redis configuration
$envFile = Join-Path $PSScriptRoot "..\.env"

if (Test-Path $envFile) {
    $envContent = Get-Content $envFile -Raw
    
    # Update or add Redis URL
    if ($envContent -match "REDIS_URL=") {
        $envContent = $envContent -replace "REDIS_URL=.*", "REDIS_URL=redis://localhost:6379/0"
    } else {
        $envContent += "`n# Redis Configuration`nREDIS_URL=redis://localhost:6379/0`nCACHE_ENABLED=True`n"
    }
    
    Set-Content -Path $envFile -Value $envContent.Trim()
    Write-Host "Updated .env file with Redis configuration." -ForegroundColor Green
} else {
    Write-Host "Warning: Could not find .env file to update Redis configuration." -ForegroundColor Yellow
}

Write-Host "`nRedis installation and configuration complete!" -ForegroundColor Green
Write-Host "You may need to restart your application for all changes to take effect." -ForegroundColor Yellow

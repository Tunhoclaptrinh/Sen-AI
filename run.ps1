# ============================================
# RAG Practice - Docker Run Script (Windows)
# ============================================

$DOCKER_DEV = "Docker/Dev/docker-compose.yml"

function Show-Menu {
    Write-Host ""
    Write-Host "=========================================="
    Write-Host "     RAG Practice - Docker Runner"
    Write-Host "=========================================="
    Write-Host ""
    Write-Host "  Select mode:"
    Write-Host ""
    Write-Host "  [1] Build Images   (First time / Rebuild)"
    Write-Host "  [2] Start Dev      (Hot-reload server)"
    Write-Host "  [3] View Logs"
    Write-Host "  [4] Stop All       (docker-compose down)"
    Write-Host "  [5] Exit"
    Write-Host ""
}

function Load-Env {
    if (Test-Path ".env") {
        Write-Host "[Info] Loading environment variables from .env..."
        Get-Content ".env" | ForEach-Object {
            $line = $_.Trim()
            # Skip comments and empty lines
            if ($line -and $line -notmatch '^\s*#' -and $line -match '=') {
                $parts = $line -split '=', 2
                $key = $parts[0].Trim()
                $value = $parts[1].Trim()
                
                # Remove inline comments (e.g. VAR=val # comment)
                # Be careful not to break values containing # inside quotes, but specific regex is hard.
                # Simple approach: split by space-# if possible, or just assume # starts comment.
                if ($value.Contains(" #")) {
                    $value = $value.Split("#")[0].Trim()
                }

                # Remove wrapping quotes (double or single)
                if ($value -match '^"(.*)"$') { $value = $matches[1] }
                elseif ($value -match "^'(.*)'$") { $value = $matches[1] }
                
                if ($key) {
                    [System.Environment]::SetEnvironmentVariable($key, $value, "Process")
                }
            }
        }
    }
}

function Start-Docker($profile) {
    Load-Env

    Write-Host ""
    Write-Host "[Docker] Starting RAG Practice: $profile"
    Write-Host ""

    switch ($profile) {
        "build" {
            Write-Host "[Docker] Building development images..."
            docker-compose -f $DOCKER_DEV build
            if ($LASTEXITCODE -eq 0) {
                Write-Host ""
                Write-Host "[OK] Images built successfully"
            } else {
                 Write-Host "[Error] Docker build failed" -ForegroundColor Red
            }
        }
        "dev" {
            # 'up' should automatically build if image is missing, 
            # but we can force build with --build if needed. 
            # Matching run.sh behavior: just 'up'
            docker-compose -f $DOCKER_DEV up
        }
        "logs" {
            docker-compose -f $DOCKER_DEV logs -f
        }
        "down" {
            docker-compose -f $DOCKER_DEV down
            Write-Host "[OK] All containers stopped"
        }
    }
}

# ============================
# CLI argument support
# ============================
if ($args.Count -gt 0) {
    switch ($args[0]) {
        "build" { Start-Docker "build"; exit }
        "dev"   { Start-Docker "dev"; exit }
        "logs"  { Start-Docker "logs"; exit }
        "down"  { Start-Docker "down"; exit }
        "help" {
            Write-Host ""
            Write-Host "Usage: .\run.ps1 [mode]"
            Write-Host ""
            Write-Host "Available modes:"
            Write-Host "  build    - Build Docker images"
            Write-Host "  dev      - Start development server"
            Write-Host "  logs     - View logs"
            Write-Host "  down     - Stop containers"
            Write-Host ""
            exit
        }
        default {
            Write-Host "[Error] Invalid mode: $($args[0])"
            Write-Host "Run '.\run.ps1 help' for usage"
            exit 1
        }
    }
}

# ============================
# Interactive menu
# ============================
while ($true) {
    Show-Menu
    $choice = Read-Host "Select [1-5]"

    switch ($choice) {
        "1" { Start-Docker "build" }
        "2" { Start-Docker "dev"; break }
        "3" { Start-Docker "logs" }
        "4" { Start-Docker "down" }
        "5" {
            Write-Host ""
            Write-Host "Goodbye!"
            Write-Host ""
            exit
        }
        default {
            Write-Host ""
            Write-Host "[Error] Invalid choice!"
            Start-Sleep -Seconds 1
        }
    }

    if ($choice -ne "5") {
        Write-Host ""
        Read-Host "Press Enter to continue..."
    }
}

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
        Get-Content ".env" |
            Where-Object { $_ -notmatch '^\s*#' -and $_ -match '=' } |
            ForEach-Object {
                $parts = $_ -split '=', 2
                [System.Environment]::SetEnvironmentVariable(
                    $parts[0].Trim(),
                    $parts[1].Trim(),
                    "Process"
                )
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
            Write-Host ""
            Write-Host "[OK] Images built successfully"
        }
        "dev" {
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

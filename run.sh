#!/bin/bash
# ============================================
# RAG Practice - Docker Run Script
# ============================================

DOCKER_DEV="Docker/Dev/docker-compose.yml"

show_menu() {
    echo ""
    echo "=========================================="
    echo "     RAG Practice - Docker Runner"
    echo "=========================================="
    echo ""
    echo "  Select mode:"
    echo ""
    echo "  [1] Build Images   (First time / Rebuild)"
    echo "  [2] Start Dev      (Hot-reload server)"
    echo "  [3] View Logs"
    echo "  [4] Stop All       (docker-compose down)"
    echo "  [5] Exit"
    echo ""
}

start_docker() {
    local profile=$1
    
    # Load .env info shell for variable expansion
    if [ -f .env ]; then
        export $(cat .env | grep -v '^#' | xargs)
    fi
    
    echo ""
    echo "[Docker] Starting RAG Practice: $profile"
    echo ""
    
    case $profile in
        build)
            echo "[Docker] Building development images..."
            docker-compose -f $DOCKER_DEV build
            echo ""
            echo "[OK] Images built successfully"
            ;;
        dev)
            docker-compose -f $DOCKER_DEV up
            ;;
        logs)
            docker-compose -f $DOCKER_DEV logs -f
            ;;
        down)
            docker-compose -f $DOCKER_DEV down
            echo "[OK] All containers stopped"
            ;;
    esac
}

# If argument provided
if [ $# -gt 0 ]; then
    case $1 in
        build|dev|logs|down)
            start_docker $1
            exit 0
            ;;
        help)
            echo ""
            echo "Usage: bash run.sh [mode]"
            echo ""
            echo "Available modes:"
            echo "  build    - Build Docker images"
            echo "  dev      - Start development server"
            echo "  logs     - View logs"
            echo "  down     - Stop containers"
            echo ""
            exit 0
            ;;
        *)
            echo "[Error] Invalid mode: $1"
            echo "Run 'bash run.sh help' for usage"
            exit 1
            ;;
    esac
fi

# Interactive menu
while true; do
    show_menu
    read -p "Select [1-5]: " choice
    
    case $choice in
        1) start_docker "build" ;;
        2) start_docker "dev"; break ;;
        3) start_docker "logs" ;;
        4) start_docker "down" ;;
        5) 
            echo ""
            echo "Goodbye!"
            echo ""
            exit 0
            ;;
        *)
            echo ""
            echo "[Error] Invalid choice!"
            sleep 1
            ;;
    esac
    
    # Wait before showing menu again
    if [ "$choice" != "5" ]; then
        echo ""
        read -p "Press Enter to continue..."
    fi
done

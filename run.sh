#!/bin/bash

# ==========================================
#      SEN AI Service - Docker Runner
# ==========================================

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Enable BuildKit for optimizations
export DOCKER_BUILDKIT=1

show_menu() {
    clear
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${BLUE}     SEN AI Service - Docker Runner      ${NC}"
    echo -e "${BLUE}==========================================${NC}"
    echo ""
    echo -e "  Select mode:"
    echo ""
    echo -e "  [1] Build Images   ${YELLOW}(Builds BOTH Dev & Prod)${NC}"
    echo -e "  [2] Start Dev      ${GREEN}(Hot-reload :8000)${NC}"
    echo -e "  [3] Start Prod     ${RED}(Optimized :8000)${NC}"
    echo -e "  [4] View Logs"
    echo -e "  [5] Stop All"
    echo -e "  [6] Exit"
    echo ""
    echo -n "Select [1-6]: "
}

build_images() {
    echo ""
    echo -e "${BLUE}🚀 Starting Optimized Build Process...${NC}"
    echo ""

    echo -e "${YELLOW}[1/2] Building Development Image...${NC}"
    docker compose -f Docker/Dev/docker-compose.yml build
    
    echo ""
    echo -e "${YELLOW}[2/2] Building Production Image...${NC}"
    docker compose -f Docker/Production/docker-compose.yml build

    echo ""
    echo -e "${GREEN}✅ All images built successfully!${NC}"
    read -p "Press Enter to continue..."
}

start_dev() {
    echo -e "${GREEN}Starting Development Server...${NC}"
    docker compose -f Docker/Dev/docker-compose.yml up -d
    echo -e "${GREEN}Server started! Viewing logs (Ctrl+C to exit logs, server keeps running)...${NC}"
    sleep 2
    docker compose -f Docker/Dev/docker-compose.yml logs -f
}

start_prod() {
    echo -e "${RED}Starting Production Server...${NC}"
    docker compose -f Docker/Production/docker-compose.yml up -d
    echo -e "${GREEN}Server started! Viewing logs...${NC}"
    sleep 2
    docker compose -f Docker/Production/docker-compose.yml logs -f
}

view_logs() {
    echo -e "${YELLOW}Viewing Logs (Ctrl+C to exit)...${NC}"
    # Try dev logs first, if empty try prod
    if docker compose -f Docker/Dev/docker-compose.yml ps | grep -q "Up"; then
        docker compose -f Docker/Dev/docker-compose.yml logs -f
    else
        docker compose -f Docker/Production/docker-compose.yml logs -f
    fi
}

stop_all() {
    echo -e "${YELLOW}Stopping all containers...${NC}"
    docker compose -f Docker/Dev/docker-compose.yml down
    docker compose -f Docker/Production/docker-compose.yml down
    echo -e "${GREEN}All stopped!${NC}"
    read -p "Press Enter to continue..."
}

# Main Loop
while true; do
    show_menu
    read choice
    case $choice in
        1) build_images ;;
        2) start_dev ;;
        3) start_prod ;;
        4) view_logs ;;
        5) stop_all ;;
        6) exit 0 ;;
        *) echo -e "${RED}Invalid option!${NC}"; sleep 1 ;;
    esac
done

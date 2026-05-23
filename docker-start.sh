#!/bin/bash

# Quest Analytics RAG Assistant - Docker Quick Start
# This script helps set up and test the application locally
# Supports running from any directory in the project

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the project root directory (where this script is located)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DOCKER_DIR="$SCRIPT_DIR/deployment/aws/docker"
COMPOSE_FILE="$DOCKER_DIR/docker-compose.dev.yml"

# Verify docker-compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}Error: docker-compose file not found at $COMPOSE_FILE${NC}"
    exit 1
fi

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Quest Analytics RAG Assistant - Docker Setup                   ║"
echo "║  Local Testing & Deployment Preparation                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Function to print section headers
print_section() {
    echo -e "\n${BLUE}▶ $1${NC}"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check prerequisites
print_section "Checking Prerequisites"

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    echo "Install from: https://www.docker.com/products/docker-desktop"
    exit 1
fi
print_success "Docker is installed: $(docker --version)"

if ! command -v docker-compose &> /dev/null; then
    print_warning "docker-compose not found (trying 'docker compose')"
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available"
        exit 1
    fi
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi
print_success "Docker Compose is available"

# Parse command line arguments
COMMAND=${1:-"status"}

# Helper function to run docker-compose with correct file
run_compose() {
    cd "$DOCKER_DIR"
    $COMPOSE_CMD -f "$(basename $COMPOSE_FILE)" "$@"
    cd - > /dev/null
}

case "$COMMAND" in
    start)
        print_section "Starting Docker Services"
        echo "Building and starting all containers..."
        echo "Working directory: $DOCKER_DIR"
        run_compose up -d --build
        print_success "Containers started"
        
        print_section "Waiting for Services to Initialize"
        echo "This may take 2-3 minutes on first run..."
        
        # Wait for each service
        for i in {1..60}; do
            if curl -s http://localhost:9200 > /dev/null 2>&1; then
                print_success "OpenSearch is ready"
                break
            fi
            echo -n "."
            sleep 1
            if [ $i -eq 60 ]; then
                print_warning "OpenSearch took longer than expected"
            fi
        done
        
        echo ""
        print_success "All services started successfully!"
        
        print_section "Service URLs"
        echo -e "  ${GREEN}Landing Page:${NC}  http://localhost:3000"
        echo -e "  ${GREEN}Gradio App:${NC}      http://localhost:7860"
        echo -e "  ${GREEN}OpenSearch:${NC}      http://localhost:9200"
        echo -e "  ${GREEN}Ollama:${NC}          http://localhost:11434"
        ;;
        
    stop)
        print_section "Stopping Docker Services"
        run_compose down
        print_success "Containers stopped"
        ;;
        
    restart)
        print_section "Restarting Docker Services"
        run_compose restart
        print_success "Containers restarted"
        ;;
        
    logs)
        print_section "Showing Logs (Press Ctrl+C to exit)"
        cd "$DOCKER_DIR"
        $COMPOSE_CMD -f "$(basename $COMPOSE_FILE)" logs -f
        ;;
        
    status)
        print_section "Container Status"
        run_compose ps
        
        print_section "Service Health Check"
        
        echo -n "  OpenSearch... "
        if curl -s http://localhost:9200 > /dev/null 2>&1; then
            print_success "Ready"
        else
            print_error "Not responding"
        fi
        
        echo -n "  Ollama... "
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            print_success "Ready"
        else
            print_error "Not responding"
        fi
        
        echo -n "  Gradio App... "
        if curl -s http://localhost:7860/info > /dev/null 2>&1; then
            print_success "Ready"
        else
            print_error "Not responding"
        fi
        
        echo -n "  Landing Page... "
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            print_success "Ready"
        else
            print_error "Not responding"
        fi
        ;;
        
    test)
        print_section "Testing Application"
        
        echo "Testing OpenSearch..."
        STATUS=$(curl -s http://localhost:9200/_cluster/health | grep -o '"status":"[^"]*"')
        echo "  Cluster Status: $STATUS"
        
        echo "Testing Ollama..."
        MODELS=$(curl -s http://localhost:11434/api/tags | grep -o '"name":"[^"]*"' | wc -l)
        echo "  Available Models: $MODELS"
        
        echo "Testing Gradio App..."
        GRADIO_INFO=$(curl -s http://localhost:7860/info | head -c 100)
        echo "  Gradio Response: $GRADIO_INFO..."
        
        echo "Testing Landing Page..."
        LANDING_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
        echo "  Landing Page HTTP Code: $LANDING_CODE"
        
        if [ "$LANDING_CODE" == "200" ]; then
            print_success "All services are responding!"
        fi
        ;;
        
    pull-models)
        print_section "Pulling Ollama Models"
        echo "This will download AI models (several GB)"
        read -p "Continue? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker exec ollama ollama pull llama2
            echo ""
            print_success "Models pulled successfully"
        fi
        ;;
        
    clean)
        print_section "Cleaning Up Docker Resources"
        read -p "This will remove all containers and volumes. Continue? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            run_compose down -v
            print_success "Cleanup complete"
        fi
        ;;
        
    help|--help|-h)
        cat << EOF

Usage: $0 [COMMAND]

Commands:
  start           Start all Docker services
  stop            Stop all services
  restart         Restart all services
  logs            Show service logs (Ctrl+C to exit)
  status          Check status of all services
  test            Run health checks on all services
  pull-models     Download Ollama AI models
  clean           Remove all containers and volumes
  help            Show this help message

Examples:
  $0 start        # Start the application
  $0 logs         # View logs from all services
  $0 test         # Check if everything is working
  $0 clean        # Remove everything (careful!)

Environment URLs (when running):
  Landing Page:   http://localhost:3000
  Gradio App:     http://localhost:7860
  OpenSearch:     http://localhost:9200
  Ollama:         http://localhost:11434

Project Structure:
  Docker files:   deployment/aws/docker/
  Compose file:   deployment/aws/docker/docker-compose.dev.yml
  App:            deployment/app_gradio.py
  Landing:        landing/main.py

For detailed documentation, see: DOCKER_DEPLOYMENT_GUIDE.md

EOF
        ;;
        
    *)
        print_error "Unknown command: $COMMAND"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac

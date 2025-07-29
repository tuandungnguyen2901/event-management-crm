#!/bin/bash

# Docker development helper script for Event Management CRM

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to check if docker-compose is available
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose is not installed. Please install docker-compose and try again."
        exit 1
    fi
}

# Help function
show_help() {
    echo "Event Management CRM - Docker Development Helper"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  up              Start all services (API + DynamoDB + Admin UI)"
    echo "  down            Stop all services"
    echo "  restart         Restart all services"
    echo "  logs            Show logs from all services"
    echo "  logs-api        Show logs from API service only"
    echo "  logs-db         Show logs from DynamoDB service only"
    echo "  build           Build/rebuild the API image"
    echo "  clean           Stop services and remove volumes"
    echo "  reset           Clean + rebuild + start (fresh environment)"
    echo "  status          Show status of all services"
    echo "  shell           Open shell in API container"
    echo "  test            Run tests in container"
    echo "  init-db         Initialize database tables"
    echo "  sample-data     Create sample data for testing"
    echo "  health          Check health of all services"
    echo ""
    echo "Development URLs:"
    echo "  API:            http://localhost:8000"
    echo "  API Docs:       http://localhost:8000/docs"
    echo "  DynamoDB:       http://localhost:8001"
    echo "  DynamoDB Admin: http://localhost:8002"
}

# Function to start services
start_services() {
    print_status "Starting Event Management CRM services..."
    docker-compose up -d
    
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check health
    check_health
    
    print_success "Services started successfully!"
    print_status "Available at:"
    echo "  🚀 API: http://localhost:8000"
    echo "  📚 API Docs: http://localhost:8000/docs"
    echo "  🗄️  DynamoDB Admin: http://localhost:8002"
}

# Function to stop services
stop_services() {
    print_status "Stopping Event Management CRM services..."
    docker-compose down
    print_success "Services stopped successfully!"
}

# Function to restart services
restart_services() {
    print_status "Restarting Event Management CRM services..."
    docker-compose restart
    sleep 5
    check_health
    print_success "Services restarted successfully!"
}

# Function to show logs
show_logs() {
    if [ "$1" = "api" ]; then
        docker-compose logs -f api
    elif [ "$1" = "db" ]; then
        docker-compose logs -f dynamodb-local
    else
        docker-compose logs -f
    fi
}

# Function to build image
build_image() {
    print_status "Building API image..."
    docker-compose build api
    print_success "Image built successfully!"
}

# Function to clean environment
clean_environment() {
    print_status "Cleaning environment..."
    docker-compose down -v --remove-orphans
    docker system prune -f
    print_success "Environment cleaned successfully!"
}

# Function to reset environment
reset_environment() {
    print_status "Resetting environment (clean + rebuild + start)..."
    clean_environment
    build_image
    start_services
    print_success "Environment reset completed!"
}

# Function to show status
show_status() {
    print_status "Service status:"
    docker-compose ps
}

# Function to open shell
open_shell() {
    print_status "Opening shell in API container..."
    docker-compose exec api bash
}

# Function to run tests
run_tests() {
    print_status "Running tests in container..."
    docker-compose exec api pytest -v
}

# Function to initialize database
init_database() {
    print_status "Initializing database tables..."
    docker-compose run --rm db-init
    print_success "Database initialized!"
}

# Function to create sample data
create_sample_data() {
    print_status "Creating sample data..."
    docker-compose exec api python scripts/init_db.py --with-sample-data
    print_success "Sample data created!"
}

# Function to check health
check_health() {
    print_status "Checking service health..."
    
    # Check API health
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "✅ API is healthy"
    else
        print_warning "⚠️  API health check failed"
    fi
    
    # Check DynamoDB Admin
    if curl -f http://localhost:8002 > /dev/null 2>&1; then
        print_success "✅ DynamoDB Admin is healthy"
    else
        print_warning "⚠️  DynamoDB Admin health check failed"
    fi
    
    # Check container status
    print_status "Container status:"
    docker-compose ps
}

# Main script logic
main() {
    # Check prerequisites
    check_docker
    check_docker_compose
    
    case "${1:-help}" in
        "up"|"start")
            start_services
            ;;
        "down"|"stop")
            stop_services
            ;;
        "restart")
            restart_services
            ;;
        "logs")
            show_logs
            ;;
        "logs-api")
            show_logs "api"
            ;;
        "logs-db")
            show_logs "db"
            ;;
        "build")
            build_image
            ;;
        "clean")
            clean_environment
            ;;
        "reset")
            reset_environment
            ;;
        "status")
            show_status
            ;;
        "shell")
            open_shell
            ;;
        "test")
            run_tests
            ;;
        "init-db")
            init_database
            ;;
        "sample-data")
            create_sample_data
            ;;
        "health")
            check_health
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@" 
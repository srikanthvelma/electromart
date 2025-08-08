#!/bin/bash

# ElectroMart Deployment Script
# This script builds and deploys the ElectroMart e-commerce platform

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    local missing_deps=()
    
    if ! command_exists docker; then
        missing_deps+=("docker")
    fi
    
    if ! command_exists docker-compose; then
        missing_deps+=("docker-compose")
    fi
    
    if ! command_exists kubectl; then
        missing_deps+=("kubectl")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        print_status "Please install the missing dependencies and try again."
        exit 1
    fi
    
    print_success "All prerequisites are installed"
}

# Function to build Docker images
build_images() {
    print_status "Building Docker images..."
    
    # Build frontend
    print_status "Building frontend image..."
    docker build -t electromart/frontend:latest ./services/frontend
    
    # Build API Gateway
    print_status "Building API Gateway image..."
    docker build -t electromart/api-gateway:latest ./services/api-gateway
    
    # Build User Service
    print_status "Building User Service image..."
    docker build -t electromart/user-service:latest ./services/user-service
    
    # Build Product Service
    print_status "Building Product Service image..."
    docker build -t electromart/product-service:latest ./services/product-service
    
    # Build Order Service
    print_status "Building Order Service image..."
    docker build -t electromart/order-service:latest ./services/order-service
    
    # Build Payment Service
    print_status "Building Payment Service image..."
    docker build -t electromart/payment-service:latest ./services/payment-service
    
    # Build Search Service
    print_status "Building Search Service image..."
    docker build -t electromart/search-service:latest ./services/search-service
    
    # Build Notification Service
    print_status "Building Notification Service image..."
    docker build -t electromart/notification-service:latest ./services/notification-service
    
    print_success "All Docker images built successfully"
}

# Function to deploy with Docker Compose
deploy_docker_compose() {
    print_status "Deploying with Docker Compose..."
    
    # Stop existing containers
    docker-compose down
    
    # Start services
    docker-compose up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    check_service_health
    
    print_success "Docker Compose deployment completed"
    print_status "Access the application at:"
    echo "  Frontend: http://localhost:3000"
    echo "  API Gateway: http://localhost:8000"
    echo "  API Documentation: http://localhost:8000/docs"
    echo "  Grafana: http://localhost:3001 (admin/admin)"
    echo "  Prometheus: http://localhost:9090"
}

# Function to deploy with Kubernetes
deploy_kubernetes() {
    print_status "Deploying with Kubernetes..."
    
    # Create namespace
    kubectl apply -f k8s/namespace.yaml
    
    # Apply ConfigMaps and Secrets
    kubectl apply -f k8s/configmap.yaml
    kubectl apply -f k8s/secrets.yaml
    
    # Deploy databases
    kubectl apply -f k8s/databases/
    
    # Wait for databases to be ready
    print_status "Waiting for databases to be ready..."
    kubectl wait --for=condition=ready pod -l app=postgres -n electromart --timeout=300s
    kubectl wait --for=condition=ready pod -l app=mongodb -n electromart --timeout=300s
    kubectl wait --for=condition=ready pod -l app=redis -n electromart --timeout=300s
    kubectl wait --for=condition=ready pod -l app=elasticsearch -n electromart --timeout=300s
    
    # Deploy services
    kubectl apply -f k8s/
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    kubectl wait --for=condition=ready pod -l app=frontend -n electromart --timeout=300s
    kubectl wait --for=condition=ready pod -l app=api-gateway -n electromart --timeout=300s
    
    print_success "Kubernetes deployment completed"
    print_status "Access the application:"
    echo "  kubectl port-forward svc/frontend-service 3000:3000 -n electromart"
    echo "  kubectl port-forward svc/api-gateway-service 8000:8000 -n electromart"
}

# Function to check service health
check_service_health() {
    print_status "Checking service health..."
    
    local services=(
        "http://localhost:3000/health"
        "http://localhost:8000/health"
        "http://localhost:8001/health"
        "http://localhost:8002/health"
        "http://localhost:8003/health"
        "http://localhost:8004/health"
        "http://localhost:8005/health"
        "http://localhost:8006/health"
    )
    
    for service in "${services[@]}"; do
        if curl -f -s "$service" > /dev/null; then
            print_success "Service $service is healthy"
        else
            print_warning "Service $service is not responding"
        fi
    done
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  build           Build all Docker images"
    echo "  docker-compose  Deploy using Docker Compose"
    echo "  kubernetes      Deploy using Kubernetes"
    echo "  full            Build images and deploy with Docker Compose"
    echo "  k8s-full        Build images and deploy with Kubernetes"
    echo "  health          Check service health"
    echo "  clean           Clean up all containers and images"
    echo "  help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 build"
    echo "  $0 docker-compose"
    echo "  $0 kubernetes"
    echo "  $0 full"
}

# Function to clean up
cleanup() {
    print_status "Cleaning up..."
    
    # Stop and remove containers
    docker-compose down -v
    
    # Remove images
    docker rmi electromart/frontend:latest 2>/dev/null || true
    docker rmi electromart/api-gateway:latest 2>/dev/null || true
    docker rmi electromart/user-service:latest 2>/dev/null || true
    docker rmi electromart/product-service:latest 2>/dev/null || true
    docker rmi electromart/order-service:latest 2>/dev/null || true
    docker rmi electromart/payment-service:latest 2>/dev/null || true
    docker rmi electromart/search-service:latest 2>/dev/null || true
    docker rmi electromart/notification-service:latest 2>/dev/null || true
    
    # Clean up Kubernetes resources
    kubectl delete namespace electromart 2>/dev/null || true
    
    print_success "Cleanup completed"
}

# Main script logic
main() {
    case "${1:-help}" in
        "build")
            check_prerequisites
            build_images
            ;;
        "docker-compose")
            check_prerequisites
            deploy_docker_compose
            ;;
        "kubernetes")
            check_prerequisites
            deploy_kubernetes
            ;;
        "full")
            check_prerequisites
            build_images
            deploy_docker_compose
            ;;
        "k8s-full")
            check_prerequisites
            build_images
            deploy_kubernetes
            ;;
        "health")
            check_service_health
            ;;
        "clean")
            cleanup
            ;;
        "help"|*)
            show_usage
            ;;
    esac
}

# Run main function
main "$@"

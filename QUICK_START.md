# ElectroMart Quick Start Guide

## 🚀 Getting Started with ElectroMart

This guide will help you quickly set up and run the ElectroMart e-commerce platform for DevOps practice.

## 📋 Prerequisites

### Required Software
- **Docker & Docker Compose** (for local development)
- **Kubernetes** (for production deployment)
- **Git** (for cloning the repository)
- **kubectl** (for Kubernetes management)

### Optional (for development)
- Node.js 18+
- Python 3.9+
- Java 17+

## 🏃‍♂️ Quick Start Options

### Option 1: Docker Compose (Recommended for Beginners)

#### 1. Clone the Repository
```bash
git clone <repository-url>
cd electromart
```

#### 2. Start All Services
```bash
# Start all services with Docker Compose
docker-compose up -d

# Check service status
docker-compose ps
```

#### 3. Access the Application
- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Grafana**: http://localhost:3001 (admin/admin123)

#### 4. Verify Services
```bash
# Check all containers are running
docker-compose ps

# View logs
docker-compose logs -f [service-name]
```

### Option 2: Kubernetes (Production Ready)

#### 1. Prerequisites
```bash
# Ensure you have a Kubernetes cluster running
kubectl cluster-info

# Verify you can create resources
kubectl auth can-i create deployments
```

#### 2. Deploy the Application

**Complete Deployment (All Services):**
```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Deploy shared infrastructure
kubectl apply -f k8s/shared/

# Deploy monitoring
kubectl apply -f k8s/monitoring/

# Deploy services with their databases (in order)
kubectl apply -f k8s/user-service/
kubectl apply -f k8s/product-service/
kubectl apply -f k8s/order-service/
kubectl apply -f k8s/payment-service/
kubectl apply -f k8s/search-service/
kubectl apply -f k8s/notification-service/
kubectl apply -f k8s/api-gateway/
kubectl apply -f k8s/frontend/

# Deploy ingress
kubectl apply -f k8s/ingress.yaml
```

**Individual Service Deployment:**
```bash
# Deploy only specific service
kubectl apply -f k8s/user-service/

# Update service configuration
kubectl apply -f k8s/user-service/configmap.yaml
kubectl rollout restart deployment/user-service -n electromart
```

#### 3. Access the Application

**Port Forwarding (for local access):**
```bash
# Frontend
kubectl port-forward svc/frontend-service 3000:3000 -n electromart

# API Gateway
kubectl port-forward svc/api-gateway-service 8000:8000 -n electromart

# Grafana
kubectl port-forward svc/grafana 3001:3000 -n electromart

# Prometheus
kubectl port-forward svc/prometheus 9090:9090 -n electromart
```

**Ingress Access (if configured):**
- Frontend: http://electromart.local
- API Gateway: http://api.electromart.local
- Grafana: http://electromart.local/grafana

#### 4. Verify Deployment
```bash
# Check all pods are running
kubectl get pods -n electromart

# Check services
kubectl get svc -n electromart

# Check ingress
kubectl get ingress -n electromart

# View logs
kubectl logs -f deployment/user-service -n electromart
```

## 🗄️ Database Access

### Docker Compose
```bash
# Access databases directly
docker exec -it electromart_postgres_1 psql -U postgres
docker exec -it electromart_mongodb_1 mongosh
docker exec -it electromart_redis_1 redis-cli
```

### Kubernetes
```bash
# Access service-specific databases
kubectl port-forward svc/user-mongodb 27017:27017 -n electromart
kubectl port-forward svc/product-postgres 5432:5432 -n electromart
kubectl port-forward svc/order-postgres 5433:5432 -n electromart
kubectl port-forward svc/notification-mongodb 27018:27017 -n electromart

# Access shared databases
kubectl port-forward svc/shared-redis 6379:6379 -n electromart
kubectl port-forward svc/shared-elasticsearch 9200:9200 -n electromart
```

## 📊 Monitoring & Observability

### Grafana Access
- **URL**: http://localhost:3001 (Docker) or http://localhost:3000 (K8s)
- **Credentials**: admin/admin123
- **Features**: Pre-configured Prometheus data source, sample dashboards

### Prometheus Access
- **URL**: http://localhost:9090 (K8s port-forward)
- **Features**: Metrics collection from all services

### Health Checks
```bash
# Check service health endpoints
curl http://localhost:8000/health  # API Gateway
curl http://localhost:8001/health  # Product Service
curl http://localhost:8002/health  # User Service
```

## 🔧 Configuration Management

### Environment Variables
Each service has its own configuration:
- **Docker Compose**: Defined in `docker-compose.yml`
- **Kubernetes**: Managed via ConfigMaps and Secrets

### Service-Specific Configs
```bash
# View ConfigMaps
kubectl get configmaps -n electromart

# View Secrets
kubectl get secrets -n electromart

# Update configuration
kubectl apply -f k8s/user-service/configmap.yaml
kubectl rollout restart deployment/user-service -n electromart
```

## 🧪 Testing the Application

### 1. Create a User
```bash
curl -X POST http://localhost:8000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "name": "Test User"
  }'
```

### 2. Browse Products
```bash
# Get all products
curl http://localhost:8000/api/products

# Get specific product
curl http://localhost:8000/api/products/1
```

### 3. Search Products
```bash
# Search for products
curl "http://localhost:8000/api/search?q=laptop"
```

## 🚨 Troubleshooting

### Common Issues

#### Docker Compose Issues
```bash
# Check service logs
docker-compose logs [service-name]

# Restart specific service
docker-compose restart [service-name]

# Rebuild and restart
docker-compose down
docker-compose up --build -d
```

#### Kubernetes Issues
```bash
# Check pod status
kubectl get pods -n electromart

# Describe pod for details
kubectl describe pod [pod-name] -n electromart

# Check events
kubectl get events -n electromart --sort-by='.lastTimestamp'

# Check service endpoints
kubectl get endpoints -n electromart
```

#### Database Connection Issues
```bash
# Check database pods
kubectl get pods -l app=postgres -n electromart
kubectl get pods -l app=mongodb -n electromart

# Check database logs
kubectl logs -f deployment/product-postgres -n electromart
kubectl logs -f deployment/user-mongodb -n electromart
```

### Performance Issues
```bash
# Check resource usage
kubectl top pods -n electromart

# Check resource limits
kubectl describe pod [pod-name] -n electromart | grep -A 5 "Limits:"
```

## 🔄 Updates and Maintenance

### Updating Services
```bash
# Update specific service
kubectl set image deployment/user-service user-service=electromart/user-service:latest -n electromart

# Update all services
kubectl rollout restart deployment -n electromart
```

### Scaling Services
```bash
# Scale specific service
kubectl scale deployment/user-service --replicas=3 -n electromart

# Scale all services
kubectl scale deployment --all --replicas=2 -n electromart
```

### Backup and Restore
```bash
# Backup databases (example for PostgreSQL)
kubectl exec -it deployment/product-postgres -n electromart -- pg_dump -U postgres electromart_products > backup.sql

# Restore databases
kubectl exec -i deployment/product-postgres -n electromart -- psql -U postgres electromart_products < backup.sql
```

## 📚 Next Steps

1. **Explore the Codebase**: Review the microservices architecture
2. **Customize Configuration**: Modify ConfigMaps and Secrets for your environment
3. **Add Features**: Implement new microservices or enhance existing ones
4. **Set Up CI/CD**: Configure GitHub Actions for automated deployment
5. **Production Setup**: Configure SSL/TLS, external databases, and monitoring

## 🆘 Getting Help

- **Documentation**: Check the main README.md for detailed information
- **Issues**: Create an issue in the repository
- **Architecture**: Review KUBERNETES_STRUCTURE.md for technical details

---

**Happy DevOps Learning! 🚀**

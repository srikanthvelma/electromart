# ElectroMart Kubernetes Architecture

## 🏗️ Overview

ElectroMart uses **enterprise-grade Kubernetes architecture** with service-specific databases, clean separation of concerns, and production-ready configurations.

## 📁 Folder Structure

```
k8s/
├── namespace.yaml                    # Main namespace
├── ingress.yaml                      # Consolidated ingress configuration
├── frontend/
│   ├── deployment.yaml              # Frontend deployment and service
│   ├── configmap.yaml              # Frontend-specific configuration
│   └── secrets.yaml                # Frontend-specific secrets
├── api-gateway/
│   ├── deployment.yaml             # API Gateway deployment and service
│   ├── configmap.yaml             # API Gateway-specific configuration
│   └── secrets.yaml               # API Gateway-specific secrets
├── user-service/
│   ├── deployment.yaml            # User service deployment and service
│   ├── configmap.yaml            # User service-specific configuration
│   ├── secrets.yaml              # User service-specific secrets
│   └── database.yaml             # User service MongoDB
├── product-service/
│   ├── deployment.yaml           # Product service deployment and service
│   ├── configmap.yaml           # Product service-specific configuration
│   ├── secrets.yaml             # Product service-specific secrets
│   └── database.yaml            # Product service PostgreSQL
├── order-service/
│   ├── deployment.yaml          # Order service deployment and service
│   ├── configmap.yaml          # Order service-specific configuration
│   ├── secrets.yaml            # Order service-specific secrets
│   └── database.yaml           # Order service PostgreSQL
├── payment-service/
│   ├── deployment.yaml         # Payment service deployment and service
│   ├── configmap.yaml         # Payment service-specific configuration
│   └── secrets.yaml           # Payment service-specific secrets
├── search-service/
│   ├── deployment.yaml        # Search service deployment and service
│   ├── configmap.yaml        # Search service-specific configuration
│   └── secrets.yaml          # Search service-specific secrets
├── notification-service/
│   ├── deployment.yaml       # Notification service deployment and service
│   ├── configmap.yaml       # Notification service-specific configuration
│   ├── secrets.yaml         # Notification service-specific secrets
│   └── database.yaml        # Notification service MongoDB
├── shared/
│   ├── redis.yaml           # Shared Redis for caching
│   └── elasticsearch.yaml   # Shared Elasticsearch for search
└── monitoring/
    ├── prometheus.yaml      # Prometheus deployment, service, PVC, config
    └── grafana.yaml         # Grafana deployment, service, PVC, config
```

## 🗄️ Database Architecture

### Service-Specific Databases
| Service | Database | Service Name | Port | Type |
|---------|----------|--------------|------|------|
| User Service | MongoDB | `user-mongodb` | 27017 | Dedicated |
| Product Service | PostgreSQL | `product-postgres` | 5432 | Dedicated |
| Order Service | PostgreSQL | `order-postgres` | 5432 | Dedicated |
| Notification Service | MongoDB | `notification-mongodb` | 27017 | Dedicated |

### Shared Databases
| Service | Database | Service Name | Port | Purpose |
|---------|----------|--------------|------|---------|
| Payment Service | Redis | `shared-redis` | 6379 | Caching |
| Search Service | Elasticsearch | `shared-elasticsearch` | 9200 | Search |
| Search Service | Redis | `shared-redis` | 6379 | Caching |
| Notification Service | Redis | `shared-redis` | 6379 | Caching |

### Benefits
- **Data Isolation**: Each service has its own database
- **Independent Scaling**: Databases can be scaled per service needs
- **Security**: Service-specific database access
- **Maintenance**: Independent database maintenance and updates
- **Performance**: No cross-service database contention

## 🌐 Ingress Configuration

### Consolidated Ingress (`k8s/ingress.yaml`)

#### Three Ingress Resources:

1. **Main Application Ingress** (`electromart-ingress`)
   - Frontend: `/`
   - API Gateway: `/api`
   - Grafana: `/grafana`
   - Prometheus: `/prometheus`

2. **API Gateway Ingress** (`api-gateway-ingress`)
   - Direct API Gateway access: `/api/*`

3. **Direct Service Access Ingress** (`electromart-api-ingress`)
   - User Service: `/users/*`
   - Product Service: `/products/*`
   - Order Service: `/orders/*`
   - Payment Service: `/payments/*`
   - Search Service: `/search/*`
   - Notification Service: `/notifications/*`

### Benefits
- **Single Point of Management**: All ingress rules in one file
- **Consistent Configuration**: Same annotations and settings
- **Easy Maintenance**: No scattered ingress files
- **Clear Routing**: Well-defined service paths

## 🔧 Configuration Management

### Service-Specific ConfigMaps and Secrets
Each service has its own dedicated configuration files:

- **ConfigMaps**: Service-specific configurations (ports, URLs, settings)
- **Secrets**: Service-specific sensitive data (passwords, API keys, JWT secrets)

### Benefits
- **Security**: Each service only has access to its required secrets
- **Maintainability**: Easy to update service-specific configurations
- **Scalability**: Independent service configuration management
- **Compliance**: Better audit trail and access control

## 📊 Monitoring Architecture

### Prometheus (`k8s/monitoring/prometheus.yaml`)
- Deployment, Service, PVC, ConfigMap all in one file
- Configured to scrape all microservices
- Persistent storage for metrics retention

### Grafana (`k8s/monitoring/grafana.yaml`)
- Deployment, Service, PVC, ConfigMap, Secret all in one file
- Pre-configured Prometheus data source
- Default credentials: admin/admin123

### Benefits
- **Self-Contained**: Each monitoring component is complete
- **Easy Deployment**: Single file per component
- **Pre-configured**: Ready to use out of the box

## 🚀 Deployment Commands

### Complete Deployment
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

### Service-Specific Deployment
```bash
# Deploy only user service with its database
kubectl apply -f k8s/user-service/

# Update service configuration
kubectl apply -f k8s/user-service/configmap.yaml
kubectl apply -f k8s/user-service/secrets.yaml
kubectl rollout restart deployment/user-service -n electromart
```

## 🔒 Security Features

### Implemented
1. **Service-specific secrets**: Each service only has access to its required secrets
2. **Database isolation**: Each service has its own database instance
3. **Resource limits**: All deployments have CPU and memory limits
4. **Health checks**: Liveness and readiness probes for all services
5. **Persistent storage**: All databases have persistent volumes
6. **Clean separation**: No global configs or secrets

### Production Recommendations
1. **Use external secret management** (Azure Key Vault, AWS Secrets Manager)
2. **Enable RBAC** with service accounts
3. **Implement network policies** for service-to-service communication
4. **Use TLS certificates** for all external communication
5. **Regular secret rotation**
6. **Database backups** for each service database

## 🗄️ Database Access

### External Access
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

## 📈 Key Features

✅ **Service-Specific Databases**: Each service has its own database  
✅ **Consolidated Ingress**: Single ingress file with all routing rules  
✅ **Clean Monitoring**: Self-contained monitoring components  
✅ **Service-Specific Configs**: Clean separation of configurations  
✅ **Enterprise Security**: Proper secret management and isolation  
✅ **Perfect Organization**: Logical, maintainable structure  

## 🎯 Architecture Benefits

- **Scalability**: Independent service scaling
- **Maintainability**: Clear separation of concerns
- **Security**: Service-specific access controls
- **Reliability**: Health checks and monitoring
- **Flexibility**: Easy to add new services
- **Production Ready**: Enterprise-grade configurations

---

The ElectroMart project follows **enterprise-grade Kubernetes best practices** with a clean, scalable, and maintainable microservices architecture! 🚀

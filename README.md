# ElectroMart - Electronics E-commerce Platform

ElectroMart is a modern microservices-based e-commerce platform for electronic products, designed for DevOps practice and learning with **enterprise-grade Kubernetes architecture**.

## 🏗️ Architecture Overview

### Microservices Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   Load Balancer │
│   (React.js)    │◄──►│   (Node.js)     │◄──►│   (Nginx)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼────────┐    ┌────────▼────────┐    ┌────────▼────────┐
│  User Service  │    │ Product Service │    │  Order Service  │
│  (Node.js)     │    │   (Python)      │    │   (Java)        │
│  + MongoDB     │    │  + PostgreSQL   │    │  + PostgreSQL   │
└────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
┌───────▼────────┐    ┌────────▼────────┐    ┌────────▼────────┐
│ Payment Service│    │ Search Service  │    │Notification Svc │
│  (Node.js)     │    │   (Python)      │    │   (Python)      │
│  + Redis       │    │ + Elasticsearch │    │  + MongoDB      │
└────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Services

### Frontend (React.js + TypeScript)
- Modern, responsive UI for electronics shopping
- Product catalog, cart, checkout, user dashboard
- Real-time product search and filtering

### API Gateway (Node.js + Express)
- Centralized routing and authentication
- Rate limiting and request validation
- Service discovery and load balancing

### User Service (Node.js + Express + MongoDB)
- User registration, authentication, and profile management
- JWT token management
- User preferences and addresses
- **Database**: Dedicated MongoDB instance (`user-mongodb`)

### Product Service (Python + FastAPI + PostgreSQL)
- Product catalog management
- Inventory tracking
- Category and brand management
- Product images and specifications
- **Database**: Dedicated PostgreSQL instance (`product-postgres`)

### Order Service (Java + Spring Boot + PostgreSQL)
- Order processing and management
- Order status tracking
- Order history and analytics
- **Database**: Dedicated PostgreSQL instance (`order-postgres`)

### Payment Service (Node.js + Express + Redis)
- Payment processing (stripe integration)
- Transaction management
- Payment status tracking
- **Database**: Shared Redis instance (`shared-redis`)

### Search Service (Python + FastAPI + Elasticsearch)
- Full-text product search
- Advanced filtering and sorting
- Search analytics
- **Databases**: Shared Elasticsearch (`shared-elasticsearch`) + Redis (`shared-redis`)

### Notification Service (Python + FastAPI + MongoDB)
- Email notifications
- SMS notifications (Twilio integration)
- Order status updates
- **Database**: Dedicated MongoDB instance (`notification-mongodb`)

## 🛠️ Technology Stack

| Service | Language | Framework | Database | Purpose |
|---------|----------|-----------|----------|---------|
| Frontend | TypeScript | React.js | - | User Interface |
| API Gateway | JavaScript | Node.js + Express | - | Routing & Auth |
| User Service | JavaScript | Node.js + Express | MongoDB | User Management |
| Product Service | Python | FastAPI | PostgreSQL | Product Catalog |
| Order Service | Java | Spring Boot | PostgreSQL | Order Processing |
| Payment Service | JavaScript | Node.js + Express | Redis | Payment Processing |
| Search Service | Python | FastAPI | Elasticsearch + Redis | Product Search |
| Notification Service | Python | FastAPI | MongoDB | Notifications |

## 📦 Deployment Options

1. **Docker Compose** - For local development and testing
2. **Kubernetes** - For production deployment with enterprise-grade architecture
3. **Docker Swarm** - Alternative orchestration

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+
- Python 3.9+
- Java 17+
- Git

### Local Development with Docker Compose
```bash
# Clone the repository
git clone <repository-url>
cd electromart

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# API Gateway: http://localhost:8000
# API Documentation: http://localhost:8000/docs
```

### Kubernetes Deployment (Production Ready)

#### **Complete Deployment:**
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

#### **Service-Specific Deployment:**
```bash
# Deploy only user service with its database
kubectl apply -f k8s/user-service/

# Update service configuration
kubectl apply -f k8s/user-service/configmap.yaml
kubectl apply -f k8s/user-service/secrets.yaml
kubectl rollout restart deployment/user-service -n electromart
```

## 🏛️ Kubernetes Architecture

### **Perfect Organization Structure:**
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

### **Key Features:**
- ✅ **Service-Specific Databases**: Each service has its own database
- ✅ **Service-Specific ConfigMaps/Secrets**: Clean separation of configurations
- ✅ **Consolidated Ingress**: Single ingress file with all routing rules
- ✅ **Clean Monitoring**: Self-contained monitoring components
- ✅ **Enterprise Security**: Proper secret management and isolation

## 📊 Sample Data

The application includes sample electronics products:
- Smartphones (iPhone, Samsung, Google Pixel)
- Laptops (MacBook, Dell, HP, Lenovo)
- Tablets (iPad, Samsung Galaxy Tab)
- Smart Watches (Apple Watch, Samsung Galaxy Watch)
- Headphones (AirPods, Sony, Bose)
- Gaming Consoles (PlayStation, Xbox, Nintendo)

## 🔧 Development

### Service Communication
- **Synchronous**: HTTP/REST APIs
- **Asynchronous**: Message queues (Redis/RabbitMQ)
- **Service Discovery**: Docker networking / Kubernetes services

### Data Flow
1. User interacts with React frontend
2. Frontend calls API Gateway
3. API Gateway routes to appropriate microservice
4. Microservices communicate via HTTP/REST
5. Data stored in respective databases
6. Notifications sent via Notification Service

## 📝 API Documentation

Each service provides its own API documentation:
- API Gateway: http://localhost:8000/docs
- Product Service: http://localhost:8001/docs
- User Service: http://localhost:8002/docs
- Order Service: http://localhost:8003/docs
- Payment Service: http://localhost:8004/docs
- Search Service: http://localhost:8005/docs
- Notification Service: http://localhost:8006/docs

## 🐳 Docker Images

All services are containerized with optimized Docker images:
- Multi-stage builds for smaller images
- Health checks for service monitoring
- Environment-specific configurations

## 🔒 Security Features

- JWT-based authentication
- API rate limiting
- Input validation and sanitization
- HTTPS/TLS encryption
- Database connection security
- Service-specific secrets management
- Database isolation per service

## 📈 Monitoring & Logging

- Centralized logging with ELK stack
- Application metrics with Prometheus
- Health check endpoints
- Error tracking and alerting

### Grafana Deployment

Grafana is deployed as part of the monitoring stack to visualize metrics from Prometheus.

#### Accessing Grafana

**Docker Compose:**
```bash
# Access Grafana UI
http://localhost:3001

# Default credentials:
# Username: admin
# Password: admin123
```

**Kubernetes:**
```bash
# Port forward to access Grafana
kubectl port-forward svc/grafana 3000:3000 -n electromart

# Access Grafana UI
http://localhost:3000

# Default credentials:
# Username: admin
# Password: admin123 (configured in secrets)
```

#### Grafana Features

1. **Pre-configured Data Sources:**
   - Prometheus data source automatically configured
   - Ready to query application metrics

2. **Sample Dashboards:**
   - Application overview dashboard
   - Service-specific dashboards
   - Database performance metrics

3. **Key Metrics Monitored:**
   - Request rates and response times
   - Error rates and status codes
   - Database connection health
   - Service availability and uptime
   - Resource utilization (CPU, Memory)

#### Setting Up Custom Dashboards

1. **Import Dashboard:**
   - Go to Dashboards → Import
   - Use dashboard ID or upload JSON file

2. **Create Custom Queries:**
   - Use PromQL to query Prometheus data
   - Example: `rate(http_requests_total[5m])`

3. **Configure Alerts:**
   - Set up alerting rules for critical metrics
   - Configure notification channels

#### Monitoring Stack Components

- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and alerting
- **Service Metrics**: Each service exposes `/metrics` endpoint
- **Health Checks**: Kubernetes liveness/readiness probes

## 🗄️ Database Architecture

### **Service-to-Database Mapping:**

| Service | Database | Service Name | Port | Type |
|---------|----------|--------------|------|------|
| User Service | MongoDB | `user-mongodb` | 27017 | Dedicated |
| Product Service | PostgreSQL | `product-postgres` | 5432 | Dedicated |
| Order Service | PostgreSQL | `order-postgres` | 5432 | Dedicated |
| Notification Service | MongoDB | `notification-mongodb` | 27017 | Dedicated |
| Payment Service | Redis | `shared-redis` | 6379 | Shared |
| Search Service | Elasticsearch + Redis | `shared-elasticsearch` + `shared-redis` | 9200 + 6379 | Shared |

### **Benefits:**
- **Data Isolation**: Each service has its own database
- **Independent Scaling**: Databases can be scaled per service needs
- **Security**: Service-specific database access
- **Maintenance**: Independent database maintenance and updates
- **Performance**: No cross-service database contention

## 🌐 Ingress Configuration

### **Consolidated Ingress** (`k8s/ingress.yaml`)

#### **Three Ingress Resources:**

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

## 🤝 Contributing

This project is designed for DevOps learning and practice. Feel free to:
- Add new microservices
- Implement additional features
- Improve deployment configurations
- Add monitoring and observability tools

## 📄 License

This project is for educational and DevOps practice purposes.

# Event Management CRM - Serverless FastAPI Backend

A comprehensive serverless FastAPI backend for an Event Management CRM system that integrates with DynamoDB, supports email tracking, event analytics, and user engagement metrics.

## 🏗️ Architecture Overview

This system is designed as a modern serverless architecture on AWS with flexible deployment options optimized for scalability, performance, and cost-effectiveness.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Applications                       │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                   Load Balancer (ALB)                          │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│              FastAPI Application Layer                         │
│                 (Fargate/Lambda)                               │
└─────┬─────────────────────────────────────────────┬─────────────┘
      │                                             │
┌─────▼─────────────────────────────────────────────▼─────────────┐
│                    DynamoDB Tables                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐   │
│  │ UsersTable  │ │EventsTable  │ │    EmailSentTable       │   │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│            DynamoDB Streams + Lambda Processor                  │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                    AWS SES (Email Service)                      │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. **Application Layer - Deployment Options**
   - **AWS Fargate (Recommended for Production)**
   - **AWS Lambda (Cost-effective for Variable Workloads)**
   - **Docker Local Environment (Development)**

#### 2. **Data Layer**
   - **DynamoDB Tables**: Three specialized tables with GSI optimization
   - **DynamoDB Streams**: Event-driven architecture for real-time updates

#### 3. **External Services**
   - **AWS SES**: Reliable email delivery with tracking
   - **Application Load Balancer**: High availability and health checks

## 🎯 Architectural Decision Analysis

### Why Serverless Architecture?

**Decision**: Chose serverless-first approach with container fallback
**Rationale**:
- **Auto-scaling**: Handles traffic spikes without manual intervention
- **Cost Optimization**: Pay only for actual usage
- **Reduced Operations**: No server management overhead
- **High Availability**: Built-in redundancy across availability zones

### Why DynamoDB Over RDS?

**Decision**: NoSQL (DynamoDB) instead of traditional SQL databases
**Rationale**:
- **Performance**: Single-digit millisecond latency at any scale
- **Scalability**: Seamless scaling without capacity planning
- **Serverless Integration**: Native integration with Lambda and streams
- **Cost Model**: Pay-per-request pricing aligns with serverless philosophy
- **Global Secondary Indexes**: Efficient querying without complex joins

### Why FastAPI Over Other Frameworks?

**Decision**: FastAPI as the web framework
**Rationale**:
- **Performance**: Async/await support for high concurrency
- **Type Safety**: Built-in Pydantic validation reduces runtime errors
- **API Documentation**: Automatic OpenAPI/Swagger generation
- **Developer Experience**: Modern Python features and excellent IDE support
- **Ecosystem**: Rich middleware ecosystem and AWS integrations

### Why Dual Deployment Strategy (Lambda + Fargate)?

**Decision**: Support both Lambda and Fargate deployments
**Rationale**:

#### Lambda Benefits:
- **Cost-effective**: Ideal for sporadic or unpredictable traffic
- **Zero infrastructure**: No container management needed
- **Fast deployment**: Quick iterations during development
- **Event-driven**: Perfect for DynamoDB stream processing

#### Fargate Benefits:
- **No cold starts**: Consistent response times for production workloads
- **Higher limits**: No 15-minute timeout restrictions
- **Better control**: Full container environment control
- **Load balancing**: Application Load Balancer integration
- **Advanced scaling**: CPU/memory-based auto-scaling

### Why DynamoDB Streams for Event Processing?

**Decision**: Event-driven architecture using DynamoDB Streams
**Rationale**:
- **Real-time updates**: Immediate processing of data changes
- **Decoupled architecture**: Separation of concerns between API and analytics
- **Guaranteed delivery**: Built-in retry and error handling
- **Cost-effective**: No polling required, events trigger processing
- **Consistency**: Ensures user engagement metrics stay synchronized

### Why Application Load Balancer Over API Gateway?

**Decision**: ALB for Fargate, API Gateway for Lambda
**Rationale**:

#### ALB for Fargate:
- **Container-native**: Designed for containerized applications
- **Health checks**: Advanced health monitoring and automatic recovery
- **WebSocket support**: Full HTTP/2 and WebSocket capabilities
- **Cost efficiency**: Lower cost for sustained traffic patterns
- **SSL termination**: Built-in certificate management

#### API Gateway for Lambda:
- **Serverless integration**: Native Lambda proxy integration
- **Request/response transformation**: Built-in data transformation
- **Throttling**: Built-in rate limiting and request quotas
- **Caching**: Response caching without additional infrastructure

### Why Microservices Within Monolithic Deployment?

**Decision**: Modular service architecture within single deployment unit
**Rationale**:
- **Simplified deployment**: Single deployment pipeline
- **Reduced latency**: No network overhead between services
- **Easier development**: Simplified local development environment
- **Gradual decomposition**: Can split into microservices when needed
- **Cost optimization**: Avoid inter-service communication costs

## 🛠️ Installation & Deployment

### Prerequisites
- **Node.js 14+** (for Serverless Framework)
- **Python 3.9+**
- **AWS CLI** configured with appropriate permissions
- **Docker** and **Docker Compose** (for local development)
- **Serverless Framework** (`npm install -g serverless`)

### 🐳 Local Development (Recommended)

The fastest way to get started is using Docker for a complete development environment.

```bash
# Clone the repository
git clone https://github.com/tuandungnguyen2901/event-management-crm.git
cd event-management-crm

# Make scripts executable
chmod +x scripts/docker-dev.sh
chmod +x scripts/deploy-fargate.sh

# Start all services (API + DynamoDB + Admin UI)
./scripts/docker-dev.sh up
```

**Access Points:**
- 🚀 **API Server**: http://localhost:8000
- 📚 **API Documentation**: http://localhost:8000/docs
- 🗄️ **DynamoDB Admin**: http://localhost:8002
- 📊 **Health Check**: http://localhost:8000/health

**Development Commands:**
```bash
./scripts/docker-dev.sh logs        # View application logs
./scripts/docker-dev.sh test        # Run test suite
./scripts/docker-dev.sh shell       # Access container shell
./scripts/docker-dev.sh down        # Stop all services
./scripts/docker-dev.sh reset       # Clean rebuild
./scripts/docker-dev.sh sample-data # Create sample data
```

### 🚀 AWS Fargate Deployment (Production Recommended)

**Why Fargate for Production?**
- No cold starts ensure consistent response times
- Better resource utilization and cost predictability
- Advanced auto-scaling based on CPU/memory metrics
- Application Load Balancer for high availability

#### Prerequisites
- AWS CLI v2 configured with deployment permissions
- Docker installed and running
- Serverless Framework installed

#### One-Command Deployment
```bash
# Development deployment
./scripts/deploy-fargate.sh

# Production deployment
./scripts/deploy-fargate.sh prod us-west-2

# Staging deployment
./scripts/deploy-fargate.sh staging us-east-1
```

#### Manual Deployment Steps

1. **Environment Configuration**
```bash
export SES_SENDER_EMAIL=noreply@yourdomain.com
export EMAIL_MOCK_MODE=false
```

2. **Container Build & Push**
```bash
# Get AWS account details
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1
STAGE=dev

# Create ECR repository
aws ecr create-repository --repository-name event-management-crm-$STAGE --region $REGION

# Build and push container
docker build -f Dockerfile.prod -t event-management-crm-$STAGE .
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com
docker tag event-management-crm-$STAGE:latest $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/event-management-crm-$STAGE:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/event-management-crm-$STAGE:latest
```

3. **Infrastructure Deployment**
```bash
export CONTAINER_IMAGE_URI=$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/event-management-crm-$STAGE:latest
serverless deploy --stage $STAGE --region $REGION
```

#### Infrastructure Components Created
- **VPC with Public Subnets**: Isolated network environment
- **Application Load Balancer**: Traffic distribution and health checks
- **ECS Cluster & Service**: Container orchestration (2-10 instances)
- **Auto Scaling**: CPU-based scaling (70% target utilization)
- **ECR Repository**: Container image storage with lifecycle policies
- **CloudWatch Logs**: Centralized application logging
- **Security Groups**: Network access control
- **DynamoDB Tables**: Data persistence with GSI optimization

### ⚡ AWS Lambda Deployment (Cost-Optimized)

**Why Lambda for Cost Optimization?**
- Pay-per-request pricing ideal for variable workloads
- Zero infrastructure management
- Automatic scaling without capacity planning
- Perfect for development and testing environments

```bash
# Configure AWS credentials
aws configure
# or use profiles: export AWS_PROFILE=your-profile

# Install dependencies
npm install serverless-python-requirements

# Deploy to development
serverless deploy --stage dev

# Deploy to production
serverless deploy --stage prod --region us-west-2

# Set required environment variables
export SES_SENDER_EMAIL=noreply@yourdomain.com
export EMAIL_MOCK_MODE=false
```

### 🔧 Post-Deployment Management

#### Fargate Management Commands
```bash
# Service status
aws ecs describe-services --cluster event-management-crm-cluster-dev --services event-management-crm-service-dev

# Application logs
aws logs tail /ecs/event-management-crm-dev --follow

# Scale service
aws ecs update-service --cluster event-management-crm-cluster-dev --service event-management-crm-service-dev --desired-count 5

# Get application URL
aws cloudformation describe-stacks --stack-name event-management-crm-dev --query 'Stacks[0].Outputs[?OutputKey==`ApplicationLoadBalancerURL`].OutputValue' --output text
```

#### Lambda Management Commands
```bash
# View function logs
serverless logs -f api --tail

# Invoke function locally
serverless invoke local -f api

# Remove deployment
serverless remove --stage dev
```

## 🎯 Architecture Benefits

### Scalability
- **Automatic scaling** based on demand
- **Multi-AZ deployment** for high availability
- **Global Secondary Indexes** for efficient querying
- **Event-driven processing** for real-time updates

### Cost Optimization
- **Pay-per-use** pricing models
- **Auto-scaling** prevents over-provisioning
- **Efficient container packing** in Fargate
- **No idle resource costs** with Lambda

### Performance
- **Single-digit millisecond** DynamoDB response times
- **No cold starts** with Fargate deployment
- **Async/await** FastAPI for high concurrency
- **Application Load Balancer** for optimal routing

### Reliability
- **Built-in redundancy** across availability zones
- **Health checks** and automatic recovery
- **DynamoDB Streams** for guaranteed event processing
- **Error handling** and retry mechanisms

### Developer Experience
- **One-command local setup** with Docker
- **Automatic API documentation** with FastAPI
- **Type safety** with Pydantic models
- **Comprehensive logging** and monitoring

This architecture provides a solid foundation for an Event Management CRM that can scale from startup to enterprise while maintaining cost efficiency and developer productivity.
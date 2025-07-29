# Event Management CRM - Serverless FastAPI Backend

A comprehensive serverless FastAPI backend for an Event Management CRM system that integrates with DynamoDB, supports email tracking, event analytics, and user engagement metrics.

## 🏗️ Architecture Overview

This system is designed as a modern serverless architecture on AWS with flexible deployment options:

### Core Components
- **FastAPI Application**: Main API server with comprehensive endpoints
- **DynamoDB Tables**: Three main tables for Users, Events, and Email tracking
- **DynamoDB Streams**: Automatic event count tracking via Lambda triggers
- **AWS SES Integration**: Email sending with open tracking
- **Deployment Options**: 
  - **AWS Lambda**: Traditional serverless functions (cold starts)
  - **AWS Fargate**: Containerized deployment (recommended for production)

### Data Flow
1. **Event Creation** → DynamoDB Stream → Lambda → User Event Count Updates
2. **Email Sending** → SES → Email Tracking Table → Open Tracking via Pixel
3. **User Filtering** → DynamoDB Scan/Query → Paginated Results

## 📊 Database Schema

### UsersTable
```
Primary Key: id (String)
Attributes:
- firstName, lastName (String)
- email (String) - GSI
- phoneNumber, avatar (String, Optional)
- gender (Enum: male/female/other/prefer_not_to_say)
- jobTitle (String) - GSI
- company (String) - GSI  
- city, state (String) - GSI on city
- hostedEventCount, attendedEventCount (Number)
- createdAt, updatedAt (ISO String)
```

### EventsTable
```
Primary Key: id (String)
Attributes:
- slug (String) - GSI (unique identifier)
- title, description (String)
- startAt, endAt (ISO String)
- venue (String, Optional)
- maxCapacity (Number, Optional)
- owner (String) - GSI (User ID)
- hosts (List<String>) - User IDs
- attendees (List<String>) - User IDs
- createdAt, updatedAt (ISO String)
```

### EmailSentTable
```
Primary Key: id (String)
Attributes:
- userId (String) - GSI
- recipientEmail (String)
- subject, message (String)
- status (Enum: PENDING/SENT/OPENED/FAILED) - GSI
- sentAt, openedAt (ISO String, Optional)
- createdAt, updatedAt (ISO String)
```

## 🚀 API Endpoints

### User Management
- `GET /users/filter` - Filter users with pagination and sorting
- `POST /users` - Create new user
- `GET /users/{user_id}` - Get user by ID
- `PUT /users/{user_id}` - Update user
- `GET /users/{user_id}/events/hosted` - Get events hosted by user
- `GET /users/{user_id}/email-stats` - Get email statistics for user

### Event Management
- `POST /events` - Create new event (triggers stream processing)
- `GET /events/{event_id}` - Get event by ID
- `GET /events/slug/{slug}` - Get event by slug
- `PUT /events/{event_id}` - Update event
- `POST /events/{event_id}/attendees/{user_id}` - Add attendee
- `DELETE /events/{event_id}/attendees/{user_id}` - Remove attendee
- `GET /events/owner/{owner_id}` - Get events by owner

### Email Management
- `POST /emails/send` - Send emails to specific users
- `POST /emails/send-filtered` - Send emails to filtered users
- `GET /emails/stats` - Get email statistics

### Email Tracking
- `GET /track/open?emailId={id}` - Track email opens (returns 1x1 pixel)
- `GET /track/status/{email_id}` - Get email tracking status

## 🎯 Key Features

### Advanced User Filtering
Filter users by multiple criteria simultaneously:
- Company name
- Job title  
- City and State
- Event count ranges (hosted/attended)
- Pagination and sorting support

```bash
GET /users/filter?company=TechCorp&hostedEventCountMin=2&page=1&pageSize=10
```

### Automatic Event Count Tracking
DynamoDB Streams automatically update user engagement metrics:
- When event created → increment hosted/attended counts
- When attendees/hosts modified → adjust counts accordingly
- When event deleted → decrement all related counts

### Email Tracking System
Comprehensive email analytics:
- Send emails via AWS SES or mock mode
- Track email opens with 1x1 pixel tracking
- Analytics: sent/opened/failed rates
- Support for HTML and text emails

### Efficient Database Design
Optimized for performance:
- Global Secondary Indexes for fast filtering
- Pay-per-request billing
- Efficient pagination
- Stream processing for real-time updates

## 🛠️ Installation & Deployment

### Prerequisites
- Node.js 14+ (for Serverless Framework)
- Python 3.9+
- AWS CLI configured
- Serverless Framework

### 🐳 Docker Development Setup (Recommended)

The fastest way to get started is using Docker. This provides a complete development environment with all dependencies and services.

1. **Prerequisites**
```bash
# Install Docker and Docker Compose
# Visit: https://docs.docker.com/get-docker/

# Verify installation
docker --version
docker-compose --version
```

2. **Quick Start**
```bash
# Clone the repository
git clone <repository>
cd event-management-crm

# Make the helper script executable
chmod +x scripts/docker-dev.sh

# Start all services (API + DynamoDB + Admin UI)
./scripts/docker-dev.sh up
```

3. **Access the Services**
- 🚀 **API**: http://localhost:8000
- 📚 **API Documentation**: http://localhost:8000/docs
- 🗄️ **DynamoDB Admin UI**: http://localhost:8002
- 📊 **Health Check**: http://localhost:8000/health

4. **Development Commands**
```bash
# View logs
./scripts/docker-dev.sh logs

# Run tests
./scripts/docker-dev.sh test

# Create sample data
./scripts/docker-dev.sh sample-data

# Open shell in container
./scripts/docker-dev.sh shell

# Check service health
./scripts/docker-dev.sh health

# Stop services
./scripts/docker-dev.sh down

# Reset everything (clean + rebuild)
./scripts/docker-dev.sh reset
```

### 🛠️ Manual Local Development Setup

If you prefer to run without Docker:

1. **Clone and Install Dependencies**
```bash
git clone <repository>
cd event-management-crm
pip install -r requirements.txt
```

2. **Set Environment Variables**
```bash
export DYNAMODB_ENDPOINT_URL=http://localhost:8000  # For local DynamoDB
export EMAIL_MOCK_MODE=true
export SES_SENDER_EMAIL=noreply@yourdomain.com
```

3. **Run Local DynamoDB**
```bash
# Using Docker
docker run -p 8001:8000 amazon/dynamodb-local

# Create tables
python scripts/init_db.py
```

4. **Start Development Server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### AWS Lambda Deployment (Traditional Serverless)

1. **Install Serverless Framework**
```bash
npm install -g serverless
npm install serverless-python-requirements
```

2. **Configure AWS Credentials**
```bash
aws configure
# or use AWS profiles
export AWS_PROFILE=your-profile
```

3. **Deploy to AWS**
```bash
# Deploy to development
serverless deploy --stage dev

# Deploy to production
serverless deploy --stage prod --region us-west-2
```

4. **Set Environment Variables**
```bash
# Set SES sender email (required for production)
export SES_SENDER_EMAIL=noreply@yourdomain.com

# Disable mock mode for production
export EMAIL_MOCK_MODE=false
```

### 🚀 AWS Fargate Deployment (Recommended for Production)

For production workloads requiring better performance, longer execution times, and more consistent response times, we recommend using AWS Fargate containers.

#### Benefits of Fargate Deployment
- **Better Performance**: No cold starts, consistent response times
- **Higher Limits**: No 15-minute timeout limit, more memory available
- **Auto Scaling**: Automatic scaling based on CPU/memory utilization
- **Container Benefits**: Full control over runtime environment
- **Load Balancing**: Application Load Balancer with health checks

#### Prerequisites
- AWS CLI v2 installed and configured
- Docker installed and running
- Serverless Framework installed
- Appropriate AWS IAM permissions

#### Required IAM Permissions
Your AWS user/role needs permissions for:
- ECR: Create repositories, push images
- ECS: Create clusters, services, tasks
- CloudFormation: Create/update stacks
- EC2: Create VPC, subnets, security groups
- ELB: Create load balancers
- DynamoDB: Create tables
- IAM: Create roles and policies

#### One-Command Deployment

```bash
# Make the deployment script executable
chmod +x scripts/deploy-fargate.sh

# Deploy to development (us-east-1)
./scripts/deploy-fargate.sh

# Deploy to production (us-west-2)  
./scripts/deploy-fargate.sh prod us-west-2

# Deploy to staging (us-east-1)
./scripts/deploy-fargate.sh staging
```

#### Manual Deployment Steps

1. **Set Environment Variables**
```bash
export SES_SENDER_EMAIL=noreply@yourdomain.com
export EMAIL_MOCK_MODE=false
```

2. **Build and Push Container**
```bash
# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1
STAGE=dev

# Create ECR repository
aws ecr create-repository --repository-name event-management-crm-$STAGE --region $REGION

# Login to ECR
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Build and push image
docker build -f Dockerfile.prod -t event-management-crm-$STAGE .
docker tag event-management-crm-$STAGE:latest $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/event-management-crm-$STAGE:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/event-management-crm-$STAGE:latest
```

3. **Deploy Infrastructure**
```bash
# Set container image URI
export CONTAINER_IMAGE_URI=$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/event-management-crm-$STAGE:latest

# Deploy using serverless
serverless deploy --stage $STAGE --region $REGION
```

#### Deployment Output
After successful deployment, you'll see:
```
🎉 Deployment completed successfully!

📋 Deployment Details:
  🌐 Application URL: http://your-alb-dns-name.amazonaws.com
  📚 API Documentation: http://your-alb-dns-name.amazonaws.com/docs
  📊 Health Check: http://your-alb-dns-name.amazonaws.com/health
  🗄️ ECR Repository: 123456789.dkr.ecr.us-east-1.amazonaws.com/event-management-crm-dev
  ⚙️ ECS Cluster: event-management-crm-cluster-dev
```

#### Infrastructure Components
The Fargate deployment creates:
- **VPC**: Dedicated network with public subnets
- **Application Load Balancer**: Routes traffic to containers
- **ECS Cluster**: Container orchestration
- **ECS Service**: Runs 2 container instances by default
- **Auto Scaling**: Scales 2-10 instances based on CPU (70% target)
- **ECR Repository**: Container image storage
- **CloudWatch Logs**: Application logging
- **Security Groups**: Network access control
- **DynamoDB Tables**: Same as Lambda deployment
- **Lambda**: Stream processor (remains as Lambda)

#### Management Commands

**View Service Status**
```bash
aws ecs describe-services --cluster event-management-crm-cluster-dev --services event-management-crm-service-dev --region us-east-1
```

**View Application Logs**
```bash
aws logs tail /ecs/event-management-crm-dev --follow --region us-east-1
```

**Scale Service**
```bash
# Scale to 5 instances
aws ecs update-service --cluster event-management-crm-cluster-dev --service event-management-crm-service-dev --desired-count 5 --region us-east-1
```

**Update Container Image**
```bash
# After building new image
./scripts/deploy-fargate.sh dev  # Redeploy with new image
```

**Get Load Balancer URL**
```bash
aws cloudformation describe-stacks --stack-name event-management-crm-dev --region us-east-1 --query 'Stacks[0].Outputs[?OutputKey==`ApplicationLoadBalancerURL`].OutputValue' --output text
```

#### Monitoring & Troubleshooting

**CloudWatch Metrics**
- ECS Service CPU/Memory utilization
- Application Load Balancer request metrics
- Container instance health
- Auto Scaling activities

**Common Issues**
```bash
# Check if containers are running
aws ecs list-tasks --cluster event-management-crm-cluster-dev --service-name event-management-crm-service-dev

# Check container logs for startup issues
aws logs tail /ecs/event-management-crm-dev --since 10m

# Verify load balancer health checks
aws elbv2 describe-target-health --target-group-arn $(aws elbv2 describe-target-groups --names event-management-crm-tg-dev --query 'TargetGroups[0].TargetGroupArn' --output text)
```

#### Cost Optimization
- **Fargate Spot**: Mix of regular and Spot instances for cost savings
- **Auto Scaling**: Automatically scales down during low traffic
- **Container Insights**: Monitor resource usage for right-sizing
- **ALB**: Efficient load distribution across instances

## 🧪 Testing

### Run Test Suite
```bash
# Install test dependencies
pip install pytest pytest-asyncio moto

# Run all tests
pytest

# Run specific test file
pytest tests/test_user_service.py

# Run with coverage
pytest --cov=app tests/
```

### Test Categories
- **Unit Tests**: Service layer functionality
- **Integration Tests**: Database operations
- **Stream Handler Tests**: DynamoDB stream processing
- **API Tests**: FastAPI endpoint testing

## 📝 API Examples

### Create User
```bash
curl -X POST "https://api.yourdomain.com/users" \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "John",
    "lastName": "Doe", 
    "email": "john.doe@example.com",
    "company": "TechCorp",
    "jobTitle": "Software Engineer",
    "city": "San Francisco",
    "state": "CA"
  }'
```

### Filter Users
```bash
curl -X GET "https://api.yourdomain.com/users/filter?company=TechCorp&hostedEventCountMin=1&page=1&pageSize=5"
```

### Create Event
```bash
curl -X POST "https://api.yourdomain.com/events" \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "tech-meetup-2024",
    "title": "Tech Meetup 2024",
    "description": "Annual technology meetup",
    "startAt": "2024-06-15T18:00:00Z",
    "endAt": "2024-06-15T22:00:00Z",
    "venue": "Convention Center",
    "maxCapacity": 100,
    "owner": "user-id-123",
    "hosts": ["user-id-456"],
    "attendees": ["user-id-789"]
  }'
```

### Send Emails to Filtered Users
```bash
curl -X POST "https://api.yourdomain.com/emails/send-filtered" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Upcoming Event Notification",
    "message": "Join us for our upcoming tech meetup!",
    "company": "TechCorp",
    "hostedEventCountMin": 1
  }'
```

### Send Emails to Specific Users
```bash
curl -X POST "https://api.yourdomain.com/emails/send" \
  -H "Content-Type: application/json" \
  -d '{
    "userIds": ["user-id-123", "user-id-456"],
    "subject": "Personal Invitation",
    "message": "You are personally invited to our exclusive event!"
  }'
```

## 🔧 Configuration

### Environment Variables
```bash
# AWS Configuration
AWS_REGION=us-east-1
USERS_TABLE=event-management-crm-users-dev
EVENTS_TABLE=event-management-crm-events-dev
EMAIL_SENT_TABLE=event-management-crm-emails-dev

# Email Configuration
SES_SENDER_EMAIL=noreply@yourdomain.com
EMAIL_MOCK_MODE=false
API_BASE_URL=https://api.yourdomain.com

# Local Development
DYNAMODB_ENDPOINT_URL=http://localhost:8000
```

### Serverless Configuration
Key settings in `serverless.yml`:
- Runtime: Python 3.9
- Memory: 512MB
- Timeout: 30 seconds
- DynamoDB Stream processing
- IAM permissions for DynamoDB and SES

## 📈 Performance Considerations

### Database Optimization
- **Global Secondary Indexes**: Fast filtering by company, jobTitle, city, email
- **Pay-per-request billing**: Cost-effective for variable workloads
- **Efficient pagination**: Limit result sets and memory usage
- **Stream processing**: Real-time event count updates

### API Performance
- **Async operations**: Non-blocking I/O for better throughput
- **Batch operations**: Efficient multi-user operations
- **Error handling**: Graceful degradation and retry logic
- **CORS enabled**: Frontend integration ready

### Email Performance
- **Mock mode**: Fast development without SES limits
- **Batch processing**: Efficient bulk email sending
- **Error resilience**: Failed emails don't break the flow
- **Tracking optimization**: Minimal pixel size for fast loading

## 🔒 Security Features

### Data Protection
- Input validation with Pydantic models
- SQL injection prevention (NoSQL)
- Email address validation
- Field length limits and type checking

### AWS Security
- IAM roles with minimal required permissions
- DynamoDB encryption at rest
- SES domain verification
- API Gateway with CORS configuration

## 🚨 Monitoring & Logging

### CloudWatch Integration
- Lambda function logs
- DynamoDB metrics
- SES sending statistics
- API Gateway access logs

### Error Handling
- Comprehensive exception handling
- Structured error responses
- Stream processing error recovery
- Email delivery failure tracking

## 🎯 Business Logic

### Event Count Tracking
Automatically maintained user engagement metrics:
- **hostedEventCount**: Events where user is owner or host
- **attendedEventCount**: Events where user is attendee
- **Real-time updates**: Via DynamoDB Streams

### Email Analytics
Track user engagement through email interactions:
- **Open rates**: Pixel-based tracking
- **Delivery status**: SES integration
- **User-specific stats**: Per-user email analytics
- **Campaign effectiveness**: Bulk email insights

## 🔄 Data Flow Examples

### Event Creation Flow
1. `POST /events` → Create event in EventsTable
2. DynamoDB Stream triggers → Lambda function processes
3. Lambda increments user counts → Updates UsersTable
4. API returns event details with counts

### Email Campaign Flow  
1. `POST /emails/send-filtered` → Filter users by criteria
2. Create email records → EmailSentTable
3. Send via SES → Update status to SENT
4. User opens email → Pixel request updates to OPENED

## 🎉 Conclusion

This Event Management CRM system provides a complete serverless solution for managing events, users, and email communications with flexible deployment options:

### Key Benefits
- **Scalability**: Serverless architecture scales automatically
- **Performance**: Optimized database design and indexing
- **Analytics**: Real-time event and email tracking
- **Flexibility**: Comprehensive filtering and API coverage
- **Reliability**: Error handling and monitoring built-in

### Deployment Options
- **🐳 Local Development**: Full Docker stack with one command
- **⚡ AWS Lambda**: Traditional serverless with pay-per-request pricing
- **🚀 AWS Fargate**: Production-ready containers with better performance

### Recommended Architecture
- **Development**: Docker local environment
- **Staging/Production**: AWS Fargate deployment for:
  - No cold starts
  - Consistent response times
  - Better resource utilization
  - Advanced auto-scaling
  - Load balancer integration

Perfect for organizations needing to manage events, track user engagement, and run email campaigns with detailed analytics at any scale.

## 🐳 Docker Quick Start Guide

The complete system is now containerized and ready to run with a single command:

```bash
# Clone and start the system
git clone <repository>
cd event-management-crm
chmod +x scripts/docker-dev.sh
./scripts/docker-dev.sh up
```

**Services Available:**
- 🚀 **FastAPI Backend**: http://localhost:8000
- 📚 **Interactive API Docs**: http://localhost:8000/docs  
- 🗄️ **DynamoDB Admin UI**: http://localhost:8002
- 📊 **Health Check**: http://localhost:8000/health

**Management Commands:**
```bash
./scripts/docker-dev.sh logs      # View all logs
./scripts/docker-dev.sh test      # Run test suite
./scripts/docker-dev.sh shell     # Access container shell
./scripts/docker-dev.sh down      # Stop all services
./scripts/docker-dev.sh reset     # Clean rebuild
```

The Docker setup includes:
- ✅ **FastAPI Application** with hot reload
- ✅ **DynamoDB Local** with persistent data
- ✅ **DynamoDB Admin UI** for database management
- ✅ **Automatic table creation** and initialization
- ✅ **Network isolation** and health checks
- ✅ **Development-optimized** configuration
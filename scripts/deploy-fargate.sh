#!/bin/bash

# AWS Fargate deployment script for Event Management CRM

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

# Configuration
STAGE=${1:-dev}
REGION=${2:-us-east-1}
SERVICE_NAME="event-management-crm"

print_status "🚀 Starting Fargate deployment for stage: $STAGE, region: $REGION"

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v serverless &> /dev/null; then
        print_error "Serverless Framework is not installed"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Get AWS account ID
get_account_id() {
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    print_status "AWS Account ID: $AWS_ACCOUNT_ID"
}

# Create ECR repository if it doesn't exist
create_ecr_repo() {
    local repo_name="$SERVICE_NAME-$STAGE"
    
    print_status "Creating ECR repository: $repo_name"
    
    if aws ecr describe-repositories --repository-names "$repo_name" --region "$REGION" &> /dev/null; then
        print_status "ECR repository already exists"
    else
        aws ecr create-repository \
            --repository-name "$repo_name" \
            --region "$REGION" \
            --image-scanning-configuration scanOnPush=true
        print_success "ECR repository created"
    fi
}

# Login to ECR
ecr_login() {
    print_status "Logging into ECR..."
    aws ecr get-login-password --region "$REGION" | \
        docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"
    print_success "ECR login successful"
}

# Build and push Docker image
build_and_push_image() {
    local image_uri="$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$SERVICE_NAME-$STAGE:latest"
    
    print_status "Building Docker image..."
    docker build -f Dockerfile.prod -t "$SERVICE_NAME-$STAGE" .
    
    print_status "Tagging image..."
    docker tag "$SERVICE_NAME-$STAGE:latest" "$image_uri"
    
    print_status "Pushing image to ECR..."
    docker push "$image_uri"
    
    print_success "Image pushed: $image_uri"
    export CONTAINER_IMAGE_URI="$image_uri"
}

# Deploy infrastructure
deploy_infrastructure() {
    print_status "Deploying Fargate infrastructure..."
    
    # Set environment variables for serverless
    export CONTAINER_IMAGE_URI="$CONTAINER_IMAGE_URI"
    
    # Deploy using serverless
    serverless deploy --stage "$STAGE" --region "$REGION" --verbose
    
    print_success "Infrastructure deployment completed"
}

# Get deployment outputs
get_outputs() {
    print_status "Getting deployment outputs..."
    
    local stack_name="$SERVICE_NAME-$STAGE"
    
    # Get ALB DNS name
    ALB_DNS=$(aws cloudformation describe-stacks \
        --stack-name "$stack_name" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`ApplicationLoadBalancerDNS`].OutputValue' \
        --output text)
    
    # Get ECR Repository URI
    ECR_URI=$(aws cloudformation describe-stacks \
        --stack-name "$stack_name" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`ECRRepositoryURI`].OutputValue' \
        --output text)
    
    # Get ECS Cluster Name
    ECS_CLUSTER=$(aws cloudformation describe-stacks \
        --stack-name "$stack_name" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`ECSClusterName`].OutputValue' \
        --output text)
    
    print_success "🎉 Deployment completed successfully!"
    echo ""
    print_status "📋 Deployment Details:"
    echo "  🌐 Application URL: http://$ALB_DNS"
    echo "  📚 API Documentation: http://$ALB_DNS/docs"
    echo "  📊 Health Check: http://$ALB_DNS/health"
    echo "  🗄️ ECR Repository: $ECR_URI"
    echo "  ⚙️ ECS Cluster: $ECS_CLUSTER"
    echo "  🏷️ Stage: $STAGE"
    echo "  🌍 Region: $REGION"
    echo ""
    print_status "🔧 Management Commands:"
    echo "  # View ECS service status"
    echo "  aws ecs describe-services --cluster $ECS_CLUSTER --services $SERVICE_NAME-service-$STAGE --region $REGION"
    echo ""
    echo "  # View application logs"
    echo "  aws logs tail /ecs/$SERVICE_NAME-$STAGE --follow --region $REGION"
    echo ""
    echo "  # Scale service"
    echo "  aws ecs update-service --cluster $ECS_CLUSTER --service $SERVICE_NAME-service-$STAGE --desired-count 3 --region $REGION"
}

# Verify deployment
verify_deployment() {
    if [ -n "$ALB_DNS" ]; then
        print_status "Verifying deployment..."
        
        # Wait for ALB to be ready
        print_status "Waiting for load balancer to be ready..."
        sleep 30
        
        # Test health endpoint
        for i in {1..5}; do
            if curl -f -s "http://$ALB_DNS/health" > /dev/null; then
                print_success "✅ Health check passed!"
                break
            else
                print_warning "Health check attempt $i/5 failed, retrying in 10 seconds..."
                sleep 10
            fi
        done
    fi
}

# Main deployment flow
main() {
    check_prerequisites
    get_account_id
    create_ecr_repo
    ecr_login
    build_and_push_image
    deploy_infrastructure
    get_outputs
    verify_deployment
}

# Show help
show_help() {
    echo "AWS Fargate Deployment Script for Event Management CRM"
    echo ""
    echo "Usage: $0 [STAGE] [REGION]"
    echo ""
    echo "Arguments:"
    echo "  STAGE   - Deployment stage (default: dev)"
    echo "  REGION  - AWS region (default: us-east-1)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Deploy to dev stage in us-east-1"
    echo "  $0 prod               # Deploy to prod stage in us-east-1"
    echo "  $0 staging us-west-2  # Deploy to staging stage in us-west-2"
    echo ""
    echo "Prerequisites:"
    echo "  - AWS CLI configured with appropriate permissions"
    echo "  - Docker installed and running"
    echo "  - Serverless Framework installed"
    echo ""
    echo "Required IAM permissions:"
    echo "  - ECR: Create repositories, push images"
    echo "  - ECS: Create clusters, services, tasks"
    echo "  - CloudFormation: Create/update stacks"
    echo "  - EC2: Create VPC, subnets, security groups"
    echo "  - ELB: Create load balancers"
    echo "  - DynamoDB: Create tables"
    echo "  - IAM: Create roles and policies"
}

# Handle help flag
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

# Run main deployment
main 
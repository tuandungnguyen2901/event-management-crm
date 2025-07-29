#!/usr/bin/env python3
"""
Database initialization script for local Docker development.
Creates DynamoDB tables with proper schema and indexes.
"""

import os
import sys
import time
import boto3
from botocore.exceptions import ClientError

# Add the app directory to Python path
sys.path.append('/app')

def wait_for_dynamodb(endpoint_url, max_retries=30, delay=2):
    """Wait for DynamoDB Local to be ready"""
    print("Waiting for DynamoDB Local to be ready...")
    
    for attempt in range(max_retries):
        try:
            client = boto3.client(
                'dynamodb',
                endpoint_url=endpoint_url,
                region_name='us-east-1',
                aws_access_key_id='dummy',
                aws_secret_access_key='dummy'
            )
            
            # Try to list tables to test connection
            client.list_tables()
            print("✅ DynamoDB Local is ready!")
            return client
            
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries}: DynamoDB not ready - {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
    
    raise Exception("❌ DynamoDB Local failed to start after maximum retries")


def create_tables():
    """Create all required DynamoDB tables"""
    endpoint_url = os.getenv('DYNAMODB_ENDPOINT_URL', 'http://localhost:8000')
    
    # Wait for DynamoDB to be ready
    client = wait_for_dynamodb(endpoint_url)
    
    # Initialize DynamoDB resource
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url=endpoint_url,
        region_name='us-east-1',
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy'
    )
    
    tables_to_create = [
        {
            'name': 'UsersTable',
            'schema': {
                'TableName': 'UsersTable',
                'KeySchema': [
                    {'AttributeName': 'id', 'KeyType': 'HASH'}
                ],
                'AttributeDefinitions': [
                    {'AttributeName': 'id', 'AttributeType': 'S'},
                    {'AttributeName': 'company', 'AttributeType': 'S'},
                    {'AttributeName': 'jobTitle', 'AttributeType': 'S'},
                    {'AttributeName': 'city', 'AttributeType': 'S'},
                    {'AttributeName': 'email', 'AttributeType': 'S'}
                ],
                'BillingMode': 'PAY_PER_REQUEST',
                'GlobalSecondaryIndexes': [
                    {
                        'IndexName': 'company-index',
                        'KeySchema': [
                            {'AttributeName': 'company', 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'}
                    },
                    {
                        'IndexName': 'jobTitle-index',
                        'KeySchema': [
                            {'AttributeName': 'jobTitle', 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'}
                    },
                    {
                        'IndexName': 'city-index',
                        'KeySchema': [
                            {'AttributeName': 'city', 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'}
                    },
                    {
                        'IndexName': 'email-index',
                        'KeySchema': [
                            {'AttributeName': 'email', 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'}
                    }
                ],
                'StreamSpecification': {
                    'StreamEnabled': True,
                    'StreamViewType': 'NEW_AND_OLD_IMAGES'
                }
            }
        },
        {
            'name': 'EventsTable',
            'schema': {
                'TableName': 'EventsTable',
                'KeySchema': [
                    {'AttributeName': 'id', 'KeyType': 'HASH'}
                ],
                'AttributeDefinitions': [
                    {'AttributeName': 'id', 'AttributeType': 'S'},
                    {'AttributeName': 'slug', 'AttributeType': 'S'},
                    {'AttributeName': 'owner', 'AttributeType': 'S'}
                ],
                'BillingMode': 'PAY_PER_REQUEST',
                'GlobalSecondaryIndexes': [
                    {
                        'IndexName': 'slug-index',
                        'KeySchema': [
                            {'AttributeName': 'slug', 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'}
                    },
                    {
                        'IndexName': 'owner-index',
                        'KeySchema': [
                            {'AttributeName': 'owner', 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'}
                    }
                ],
                'StreamSpecification': {
                    'StreamEnabled': True,
                    'StreamViewType': 'NEW_AND_OLD_IMAGES'
                }
            }
        },
        {
            'name': 'EmailSentTable',
            'schema': {
                'TableName': 'EmailSentTable',
                'KeySchema': [
                    {'AttributeName': 'id', 'KeyType': 'HASH'}
                ],
                'AttributeDefinitions': [
                    {'AttributeName': 'id', 'AttributeType': 'S'},
                    {'AttributeName': 'userId', 'AttributeType': 'S'},
                    {'AttributeName': 'status', 'AttributeType': 'S'}
                ],
                'BillingMode': 'PAY_PER_REQUEST',
                'GlobalSecondaryIndexes': [
                    {
                        'IndexName': 'userId-index',
                        'KeySchema': [
                            {'AttributeName': 'userId', 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'}
                    },
                    {
                        'IndexName': 'status-index',
                        'KeySchema': [
                            {'AttributeName': 'status', 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'}
                    }
                ]
            }
        }
    ]
    
    created_tables = []
    
    for table_config in tables_to_create:
        table_name = table_config['name']
        
        try:
            # Check if table already exists
            table = dynamodb.Table(table_name)
            table.load()
            print(f"✅ Table {table_name} already exists")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Table doesn't exist, create it
                print(f"📦 Creating table {table_name}...")
                
                table = dynamodb.create_table(**table_config['schema'])
                
                # Wait for table to be created
                print(f"⏳ Waiting for table {table_name} to be active...")
                table.wait_until_exists()
                
                print(f"✅ Table {table_name} created successfully")
                created_tables.append(table_name)
                
            else:
                print(f"❌ Error checking table {table_name}: {e}")
                raise
    
    if created_tables:
        print(f"\n🎉 Successfully created {len(created_tables)} tables: {', '.join(created_tables)}")
    else:
        print("\n✅ All tables already exist")
    
    # List all tables to verify
    print("\n📋 Current tables:")
    tables = client.list_tables()['TableNames']
    for table in tables:
        print(f"  - {table}")
    
    return True


def create_sample_data():
    """Create some sample data for testing"""
    try:
        from app.config.database import db_config
        from app.models.user import UserCreate
        from app.models.event import EventCreate
        from app.services.user_service import user_service
        from app.services.event_service import event_service
        from datetime import datetime, timedelta
        import asyncio
        
        async def _create_sample_data():
            print("\n🌱 Creating sample data...")
            
            # Create sample users
            sample_users = [
                UserCreate(
                    firstName="John",
                    lastName="Doe",
                    email="john.doe@techcorp.com",
                    company="TechCorp",
                    jobTitle="Software Engineer",
                    city="San Francisco",
                    state="CA"
                ),
                UserCreate(
                    firstName="Jane",
                    lastName="Smith",
                    email="jane.smith@designstudio.com",
                    company="Design Studio",
                    jobTitle="UI/UX Designer",
                    city="New York",
                    state="NY"
                ),
                UserCreate(
                    firstName="Bob",
                    lastName="Johnson",
                    email="bob.johnson@startup.io",
                    company="Startup Inc",
                    jobTitle="Product Manager",
                    city="Austin",
                    state="TX"
                )
            ]
            
            created_users = []
            for user_data in sample_users:
                try:
                    user = await user_service.create_user(user_data)
                    created_users.append(user)
                    print(f"  ✅ Created user: {user.firstName} {user.lastName}")
                except Exception as e:
                    print(f"  ❌ Failed to create user {user_data.firstName}: {e}")
            
            # Create sample event
            if created_users:
                future_date = datetime.utcnow() + timedelta(days=30)
                event_data = EventCreate(
                    slug="sample-tech-meetup",
                    title="Sample Tech Meetup",
                    description="A sample event for testing the CRM system",
                    startAt=future_date,
                    endAt=future_date + timedelta(hours=3),
                    venue="Convention Center",
                    maxCapacity=100,
                    owner=created_users[0].id,
                    hosts=[created_users[1].id] if len(created_users) > 1 else [],
                    attendees=[created_users[2].id] if len(created_users) > 2 else []
                )
                
                try:
                    event = await event_service.create_event(event_data)
                    print(f"  ✅ Created event: {event.title}")
                except Exception as e:
                    print(f"  ❌ Failed to create event: {e}")
            
            print("✅ Sample data creation completed")
        
        # Run async function
        asyncio.run(_create_sample_data())
        
    except Exception as e:
        print(f"⚠️  Could not create sample data: {e}")
        print("This is normal if running in init-only mode")


if __name__ == "__main__":
    print("🚀 Initializing Event Management CRM Database...")
    
    try:
        # Create tables
        create_tables()
        
        # Create sample data (optional)
        if "--with-sample-data" in sys.argv:
            create_sample_data()
        
        print("\n🎉 Database initialization completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        sys.exit(1) 
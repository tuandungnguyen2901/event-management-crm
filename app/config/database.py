import boto3
import os
from typing import Dict, Any
from botocore.exceptions import ClientError


class DynamoDBConfig:
    def __init__(self):
        # Configure DynamoDB client
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.endpoint_url = os.getenv("DYNAMODB_ENDPOINT_URL")  # For local development
        
        # Initialize DynamoDB resources
        if self.endpoint_url:
            # Local development
            self.dynamodb = boto3.resource(
                'dynamodb',
                region_name=self.region,
                endpoint_url=self.endpoint_url
            )
            self.client = boto3.client(
                'dynamodb',
                region_name=self.region,
                endpoint_url=self.endpoint_url
            )
        else:
            # Production
            self.dynamodb = boto3.resource('dynamodb', region_name=self.region)
            self.client = boto3.client('dynamodb', region_name=self.region)

    @property
    def table_names(self) -> Dict[str, str]:
        """Get table names from environment or use defaults"""
        return {
            'users': os.getenv('USERS_TABLE', 'UsersTable'),
            'events': os.getenv('EVENTS_TABLE', 'EventsTable'),
            'emails': os.getenv('EMAIL_SENT_TABLE', 'EmailSentTable')
        }

    def get_table(self, table_name: str):
        """Get DynamoDB table resource"""
        return self.dynamodb.Table(self.table_names[table_name])

    def create_tables_if_not_exist(self):
        """Create tables for local development"""
        try:
            self._create_users_table()
            self._create_events_table()
            self._create_emails_table()
        except Exception as e:
            print(f"Error creating tables: {e}")

    def _create_users_table(self):
        """Create Users table with GSI for filtering"""
        table_name = self.table_names['users']
        try:
            table = self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'id', 'AttributeType': 'S'},
                    {'AttributeName': 'company', 'AttributeType': 'S'},
                    {'AttributeName': 'jobTitle', 'AttributeType': 'S'},
                    {'AttributeName': 'city', 'AttributeType': 'S'},
                    {'AttributeName': 'email', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST',
                GlobalSecondaryIndexes=[
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
                StreamSpecification={
                    'StreamEnabled': True,
                    'StreamViewType': 'NEW_AND_OLD_IMAGES'
                }
            )
            table.wait_until_exists()
            print(f"Created {table_name} table")
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceInUseException':
                raise

    def _create_events_table(self):
        """Create Events table with stream for tracking"""
        table_name = self.table_names['events']
        try:
            table = self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'id', 'AttributeType': 'S'},
                    {'AttributeName': 'slug', 'AttributeType': 'S'},
                    {'AttributeName': 'owner', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST',
                GlobalSecondaryIndexes=[
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
                StreamSpecification={
                    'StreamEnabled': True,
                    'StreamViewType': 'NEW_AND_OLD_IMAGES'
                }
            )
            table.wait_until_exists()
            print(f"Created {table_name} table")
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceInUseException':
                raise

    def _create_emails_table(self):
        """Create EmailSent table"""
        table_name = self.table_names['emails']
        try:
            table = self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'id', 'AttributeType': 'S'},
                    {'AttributeName': 'userId', 'AttributeType': 'S'},
                    {'AttributeName': 'status', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST',
                GlobalSecondaryIndexes=[
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
            )
            table.wait_until_exists()
            print(f"Created {table_name} table")
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceInUseException':
                raise


# Global instance
db_config = DynamoDBConfig() 
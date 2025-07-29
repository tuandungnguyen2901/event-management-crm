import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

from app.config.database import db_config
from app.models.user import User, UserCreate, UserUpdate, UserFilter, UserResponse


class UserService:
    def __init__(self):
        self.table = db_config.get_table('users')

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        user_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        user_item = {
            'id': user_id,
            'firstName': user_data.firstName,
            'lastName': user_data.lastName,
            'phoneNumber': user_data.phoneNumber,
            'email': user_data.email,
            'avatar': user_data.avatar,
            'gender': user_data.gender.value if user_data.gender else None,
            'jobTitle': user_data.jobTitle,
            'company': user_data.company,
            'city': user_data.city,
            'state': user_data.state,
            'hostedEventCount': 0,
            'attendedEventCount': 0,
            'createdAt': now.isoformat(),
            'updatedAt': now.isoformat()
        }
        
        # Remove None values
        user_item = {k: v for k, v in user_item.items() if v is not None}
        
        try:
            self.table.put_item(Item=user_item)
            return User(**user_item)
        except ClientError as e:
            raise Exception(f"Failed to create user: {e.response['Error']['Message']}")

    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            response = self.table.get_item(Key={'id': user_id})
            if 'Item' in response:
                return User(**response['Item'])
            return None
        except ClientError as e:
            raise Exception(f"Failed to get user: {e.response['Error']['Message']}")

    async def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """Update user"""
        now = datetime.utcnow()
        
        # Build update expression
        update_expression = "SET updatedAt = :updated_at"
        expression_values = {':updated_at': now.isoformat()}
        
        for field, value in user_data.model_dump(exclude_unset=True).items():
            if value is not None:
                update_expression += f", {field} = :{field}"
                expression_values[f':{field}'] = value.value if hasattr(value, 'value') else value
        
        try:
            response = self.table.update_item(
                Key={'id': user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ReturnValues='ALL_NEW'
            )
            return User(**response['Attributes'])
        except ClientError as e:
            raise Exception(f"Failed to update user: {e.response['Error']['Message']}")

    async def increment_event_count(self, user_id: str, field: str) -> bool:
        """Increment hosted or attended event count"""
        try:
            self.table.update_item(
                Key={'id': user_id},
                UpdateExpression=f"ADD {field} :val SET updatedAt = :updated_at",
                ExpressionAttributeValues={
                    ':val': 1,
                    ':updated_at': datetime.utcnow().isoformat()
                }
            )
            return True
        except ClientError as e:
            print(f"Failed to increment {field} for user {user_id}: {e}")
            return False

    async def filter_users(self, filters: UserFilter) -> UserResponse:
        """Filter users based on criteria with pagination"""
        scan_kwargs = {
            'Select': 'ALL_ATTRIBUTES'
        }
        
        # Build filter expression
        filter_expressions = []
        expression_values = {}
        
        if filters.company:
            filter_expressions.append("company = :company")
            expression_values[':company'] = filters.company
            
        if filters.jobTitle:
            filter_expressions.append("jobTitle = :jobTitle")
            expression_values[':jobTitle'] = filters.jobTitle
            
        if filters.city:
            filter_expressions.append("city = :city")
            expression_values[':city'] = filters.city
            
        if filters.state:
            filter_expressions.append("#state = :state")
            expression_values[':state'] = filters.state
            scan_kwargs['ExpressionAttributeNames'] = {'#state': 'state'}
            
        if filters.hostedEventCountMin is not None:
            filter_expressions.append("hostedEventCount >= :hostedMin")
            expression_values[':hostedMin'] = filters.hostedEventCountMin
            
        if filters.hostedEventCountMax is not None:
            filter_expressions.append("hostedEventCount <= :hostedMax")
            expression_values[':hostedMax'] = filters.hostedEventCountMax
            
        if filters.attendedEventCountMin is not None:
            filter_expressions.append("attendedEventCount >= :attendedMin")
            expression_values[':attendedMin'] = filters.attendedEventCountMin
            
        if filters.attendedEventCountMax is not None:
            filter_expressions.append("attendedEventCount <= :attendedMax")
            expression_values[':attendedMax'] = filters.attendedEventCountMax
        
        if filter_expressions:
            scan_kwargs['FilterExpression'] = ' AND '.join(filter_expressions)
            scan_kwargs['ExpressionAttributeValues'] = expression_values
        
        try:
            # Scan with filters
            response = self.table.scan(**scan_kwargs)
            items = response['Items']
            
            # Manual pagination and sorting since DynamoDB doesn't support complex sorting on scan
            total = len(items)
            
            # Sort items
            reverse = filters.sortOrder == 'desc'
            items.sort(key=lambda x: x.get(filters.sortBy, ''), reverse=reverse)
            
            # Apply pagination
            start_idx = (filters.page - 1) * filters.pageSize
            end_idx = start_idx + filters.pageSize
            paginated_items = items[start_idx:end_idx]
            
            users = [User(**item) for item in paginated_items]
            total_pages = (total + filters.pageSize - 1) // filters.pageSize
            
            return UserResponse(
                users=users,
                total=total,
                page=filters.page,
                pageSize=filters.pageSize,
                totalPages=total_pages
            )
            
        except ClientError as e:
            raise Exception(f"Failed to filter users: {e.response['Error']['Message']}")

    async def get_users_by_ids(self, user_ids: List[str]) -> List[User]:
        """Get multiple users by their IDs"""
        if not user_ids:
            return []
            
        try:
            # Batch get items
            request_items = {
                self.table.table_name: {
                    'Keys': [{'id': user_id} for user_id in user_ids]
                }
            }
            
            response = db_config.client.batch_get_item(RequestItems=request_items)
            items = response.get('Responses', {}).get(self.table.table_name, [])
            
            return [User(**item) for item in items]
            
        except ClientError as e:
            raise Exception(f"Failed to get users by IDs: {e.response['Error']['Message']}")


# Global instance
user_service = UserService() 
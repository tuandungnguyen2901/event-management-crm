import uuid
from datetime import datetime
from typing import List, Optional
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

from app.config.database import db_config
from app.models.event import Event, EventCreate, EventUpdate, EventResponse


class EventService:
    def __init__(self):
        self.table = db_config.get_table('events')

    async def create_event(self, event_data: EventCreate) -> Event:
        """Create a new event"""
        event_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Validate that endAt is after startAt
        if event_data.endAt <= event_data.startAt:
            raise ValueError("Event end time must be after start time")
        
        event_item = {
            'id': event_id,
            'slug': event_data.slug,
            'title': event_data.title,
            'description': event_data.description,
            'startAt': event_data.startAt.isoformat(),
            'endAt': event_data.endAt.isoformat(),
            'venue': event_data.venue,
            'maxCapacity': event_data.maxCapacity,
            'owner': event_data.owner,
            'hosts': event_data.hosts,
            'attendees': event_data.attendees,
            'createdAt': now.isoformat(),
            'updatedAt': now.isoformat()
        }
        
        # Remove None values
        event_item = {k: v for k, v in event_item.items() if v is not None}
        
        try:
            # Check if slug already exists
            existing = await self.get_event_by_slug(event_data.slug)
            if existing:
                raise ValueError(f"Event with slug '{event_data.slug}' already exists")
                
            self.table.put_item(Item=event_item)
            return Event(**event_item)
        except ClientError as e:
            raise Exception(f"Failed to create event: {e.response['Error']['Message']}")

    async def get_event(self, event_id: str) -> Optional[Event]:
        """Get event by ID"""
        try:
            response = self.table.get_item(Key={'id': event_id})
            if 'Item' in response:
                return Event(**response['Item'])
            return None
        except ClientError as e:
            raise Exception(f"Failed to get event: {e.response['Error']['Message']}")

    async def get_event_by_slug(self, slug: str) -> Optional[Event]:
        """Get event by slug"""
        try:
            response = self.table.query(
                IndexName='slug-index',
                KeyConditionExpression=Key('slug').eq(slug)
            )
            if response['Items']:
                return Event(**response['Items'][0])
            return None
        except ClientError as e:
            raise Exception(f"Failed to get event by slug: {e.response['Error']['Message']}")

    async def update_event(self, event_id: str, event_data: EventUpdate) -> Optional[Event]:
        """Update event"""
        now = datetime.utcnow()
        
        # Build update expression
        update_expression = "SET updatedAt = :updated_at"
        expression_values = {':updated_at': now.isoformat()}
        
        update_data = event_data.model_dump(exclude_unset=True)
        
        # Handle datetime fields
        if 'startAt' in update_data and update_data['startAt']:
            update_data['startAt'] = update_data['startAt'].isoformat()
        if 'endAt' in update_data and update_data['endAt']:
            update_data['endAt'] = update_data['endAt'].isoformat()
        
        for field, value in update_data.items():
            if value is not None:
                update_expression += f", {field} = :{field}"
                expression_values[f':{field}'] = value
        
        try:
            response = self.table.update_item(
                Key={'id': event_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ReturnValues='ALL_NEW'
            )
            return Event(**response['Attributes'])
        except ClientError as e:
            raise Exception(f"Failed to update event: {e.response['Error']['Message']}")

    async def add_attendee(self, event_id: str, user_id: str) -> bool:
        """Add attendee to event"""
        try:
            # First check if event exists and get current attendees
            event = await self.get_event(event_id)
            if not event:
                return False
                
            # Check if user is already an attendee
            if user_id in event.attendees:
                return True
                
            # Check capacity
            if event.maxCapacity and len(event.attendees) >= event.maxCapacity:
                raise ValueError("Event has reached maximum capacity")
            
            self.table.update_item(
                Key={'id': event_id},
                UpdateExpression="SET attendees = list_append(if_not_exists(attendees, :empty_list), :new_attendee), updatedAt = :updated_at",
                ExpressionAttributeValues={
                    ':new_attendee': [user_id],
                    ':empty_list': [],
                    ':updated_at': datetime.utcnow().isoformat()
                }
            )
            return True
        except ClientError as e:
            print(f"Failed to add attendee: {e}")
            return False

    async def remove_attendee(self, event_id: str, user_id: str) -> bool:
        """Remove attendee from event"""
        try:
            event = await self.get_event(event_id)
            if not event or user_id not in event.attendees:
                return False
                
            # Remove user from attendees list
            updated_attendees = [uid for uid in event.attendees if uid != user_id]
            
            self.table.update_item(
                Key={'id': event_id},
                UpdateExpression="SET attendees = :attendees, updatedAt = :updated_at",
                ExpressionAttributeValues={
                    ':attendees': updated_attendees,
                    ':updated_at': datetime.utcnow().isoformat()
                }
            )
            return True
        except ClientError as e:
            print(f"Failed to remove attendee: {e}")
            return False

    async def get_events_by_owner(self, owner_id: str) -> List[Event]:
        """Get all events owned by a user"""
        try:
            response = self.table.query(
                IndexName='owner-index',
                KeyConditionExpression=Key('owner').eq(owner_id)
            )
            return [Event(**item) for item in response['Items']]
        except ClientError as e:
            raise Exception(f"Failed to get events by owner: {e.response['Error']['Message']}")

    async def get_event_response(self, event: Event) -> EventResponse:
        """Convert Event to EventResponse with additional calculated fields"""
        return EventResponse(
            id=event.id,
            slug=event.slug,
            title=event.title,
            description=event.description,
            startAt=event.startAt,
            endAt=event.endAt,
            venue=event.venue,
            maxCapacity=event.maxCapacity,
            owner=event.owner,
            hosts=event.hosts,
            attendees=event.attendees,
            attendeeCount=len(event.attendees),
            hostCount=len(event.hosts),
            createdAt=event.createdAt,
            updatedAt=event.updatedAt
        )


# Global instance
event_service = EventService() 
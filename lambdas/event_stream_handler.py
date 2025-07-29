import json
import logging
from typing import Dict, List, Any

from app.services.user_service import user_service

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for DynamoDB Streams from EventsTable
    Updates user event counts when events are created/modified
    """
    try:
        logger.info(f"Processing {len(event.get('Records', []))} stream records")
        
        for record in event.get('Records', []):
            await process_stream_record(record)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully processed {len(event.get("Records", []))} records'
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing stream records: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }


async def process_stream_record(record: Dict[str, Any]) -> None:
    """Process a single DynamoDB stream record"""
    event_name = record.get('eventName')
    
    if event_name == 'INSERT':
        await handle_event_insert(record)
    elif event_name == 'MODIFY':
        await handle_event_modify(record)
    elif event_name == 'REMOVE':
        await handle_event_remove(record)


async def handle_event_insert(record: Dict[str, Any]) -> None:
    """Handle new event creation - increment hosted/attended counts"""
    try:
        new_image = record.get('dynamodb', {}).get('NewImage', {})
        
        if not new_image:
            return
            
        # Extract event data
        owner_id = new_image.get('owner', {}).get('S')
        hosts = new_image.get('hosts', {}).get('SS', [])
        attendees = new_image.get('attendees', {}).get('SS', [])
        
        logger.info(f"Processing INSERT for event with owner: {owner_id}, hosts: {len(hosts)}, attendees: {len(attendees)}")
        
        # Update owner's hosted event count (if owner is not in hosts list)
        if owner_id and owner_id not in hosts:
            await user_service.increment_event_count(owner_id, 'hostedEventCount')
            logger.info(f"Incremented hostedEventCount for owner: {owner_id}")
        
        # Update hosted event count for all hosts
        for host_id in hosts:
            await user_service.increment_event_count(host_id, 'hostedEventCount')
            logger.info(f"Incremented hostedEventCount for host: {host_id}")
        
        # Update attended event count for all attendees
        for attendee_id in attendees:
            await user_service.increment_event_count(attendee_id, 'attendedEventCount')
            logger.info(f"Incremented attendedEventCount for attendee: {attendee_id}")
            
    except Exception as e:
        logger.error(f"Error handling event insert: {str(e)}")


async def handle_event_modify(record: Dict[str, Any]) -> None:
    """Handle event modification - adjust counts based on changes"""
    try:
        old_image = record.get('dynamodb', {}).get('OldImage', {})
        new_image = record.get('dynamodb', {}).get('NewImage', {})
        
        if not old_image or not new_image:
            return
        
        # Extract old and new data
        old_hosts = set(old_image.get('hosts', {}).get('SS', []))
        new_hosts = set(new_image.get('hosts', {}).get('SS', []))
        old_attendees = set(old_image.get('attendees', {}).get('SS', []))
        new_attendees = set(new_image.get('attendees', {}).get('SS', []))
        
        logger.info(f"Processing MODIFY - hosts: {len(old_hosts)}->{len(new_hosts)}, attendees: {len(old_attendees)}->{len(new_attendees)}")
        
        # Handle hosts changes
        added_hosts = new_hosts - old_hosts
        removed_hosts = old_hosts - new_hosts
        
        for host_id in added_hosts:
            await user_service.increment_event_count(host_id, 'hostedEventCount')
            logger.info(f"Incremented hostedEventCount for new host: {host_id}")
            
        for host_id in removed_hosts:
            # Decrement hosted event count (using negative increment)
            await decrement_event_count(host_id, 'hostedEventCount')
            logger.info(f"Decremented hostedEventCount for removed host: {host_id}")
        
        # Handle attendees changes
        added_attendees = new_attendees - old_attendees
        removed_attendees = old_attendees - new_attendees
        
        for attendee_id in added_attendees:
            await user_service.increment_event_count(attendee_id, 'attendedEventCount')
            logger.info(f"Incremented attendedEventCount for new attendee: {attendee_id}")
            
        for attendee_id in removed_attendees:
            # Decrement attended event count (using negative increment)
            await decrement_event_count(attendee_id, 'attendedEventCount')
            logger.info(f"Decremented attendedEventCount for removed attendee: {attendee_id}")
            
    except Exception as e:
        logger.error(f"Error handling event modify: {str(e)}")


async def handle_event_remove(record: Dict[str, Any]) -> None:
    """Handle event deletion - decrement all related counts"""
    try:
        old_image = record.get('dynamodb', {}).get('OldImage', {})
        
        if not old_image:
            return
            
        # Extract event data
        owner_id = old_image.get('owner', {}).get('S')
        hosts = old_image.get('hosts', {}).get('SS', [])
        attendees = old_image.get('attendees', {}).get('SS', [])
        
        logger.info(f"Processing REMOVE for event with owner: {owner_id}, hosts: {len(hosts)}, attendees: {len(attendees)}")
        
        # Decrement owner's hosted event count (if owner is not in hosts list)
        if owner_id and owner_id not in hosts:
            await decrement_event_count(owner_id, 'hostedEventCount')
            logger.info(f"Decremented hostedEventCount for owner: {owner_id}")
        
        # Decrement hosted event count for all hosts
        for host_id in hosts:
            await decrement_event_count(host_id, 'hostedEventCount')
            logger.info(f"Decremented hostedEventCount for host: {host_id}")
        
        # Decrement attended event count for all attendees
        for attendee_id in attendees:
            await decrement_event_count(attendee_id, 'attendedEventCount')
            logger.info(f"Decremented attendedEventCount for attendee: {attendee_id}")
            
    except Exception as e:
        logger.error(f"Error handling event remove: {str(e)}")


async def decrement_event_count(user_id: str, field: str) -> bool:
    """Decrement event count by using negative increment"""
    try:
        from app.config.database import db_config
        from datetime import datetime
        
        table = db_config.get_table('users')
        table.update_item(
            Key={'id': user_id},
            UpdateExpression=f"ADD {field} :val SET updatedAt = :updated_at",
            ExpressionAttributeValues={
                ':val': -1,
                ':updated_at': datetime.utcnow().isoformat()
            }
        )
        return True
    except Exception as e:
        logger.error(f"Failed to decrement {field} for user {user_id}: {e}")
        return False 
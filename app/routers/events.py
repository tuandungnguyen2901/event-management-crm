from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from app.models.event import Event, EventCreate, EventUpdate, EventResponse
from app.services.event_service import event_service

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/", response_model=EventResponse)
async def create_event(event_data: EventCreate):
    """
    Create a new event.
    
    This will automatically trigger DynamoDB stream to update user event counts.
    """
    try:
        event = await event_service.create_event(event_data)
        return await event_service.get_event_response(event)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create event: {str(e)}")


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: str):
    """Get event by ID"""
    try:
        event = await event_service.get_event(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return await event_service.get_event_response(event)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/slug/{slug}", response_model=EventResponse)
async def get_event_by_slug(slug: str):
    """Get event by slug"""
    try:
        event = await event_service.get_event_by_slug(slug)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return await event_service.get_event_response(event)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(event_id: str, event_data: EventUpdate):
    """Update event"""
    try:
        event = await event_service.update_event(event_id, event_data)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return await event_service.get_event_response(event)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{event_id}/attendees/{user_id}")
async def add_attendee(event_id: str, user_id: str):
    """Add attendee to event"""
    try:
        # Verify user exists
        from app.services.user_service import user_service
        user = await user_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        success = await event_service.add_attendee(event_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Event not found")
        
        return {"message": f"User {user_id} added as attendee to event {event_id}"}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{event_id}/attendees/{user_id}")
async def remove_attendee(event_id: str, user_id: str):
    """Remove attendee from event"""
    try:
        success = await event_service.remove_attendee(event_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Event not found or user not an attendee")
        
        return {"message": f"User {user_id} removed as attendee from event {event_id}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/owner/{owner_id}")
async def get_events_by_owner(owner_id: str):
    """Get all events owned by a user"""
    try:
        events = await event_service.get_events_by_owner(owner_id)
        event_responses = []
        for event in events:
            event_responses.append(await event_service.get_event_response(event))
        
        return {
            "events": event_responses,
            "count": len(event_responses)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from app.models.user import User, UserCreate, UserUpdate, UserFilter, UserResponse
from app.services.user_service import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/filter", response_model=UserResponse)
async def filter_users(
    company: Optional[str] = Query(None, description="Filter by company name"),
    jobTitle: Optional[str] = Query(None, description="Filter by job title"),
    city: Optional[str] = Query(None, description="Filter by city"),
    state: Optional[str] = Query(None, description="Filter by state"),
    hostedEventCountMin: Optional[int] = Query(None, ge=0, description="Minimum hosted events count"),
    hostedEventCountMax: Optional[int] = Query(None, ge=0, description="Maximum hosted events count"),
    attendedEventCountMin: Optional[int] = Query(None, ge=0, description="Minimum attended events count"),
    attendedEventCountMax: Optional[int] = Query(None, ge=0, description="Maximum attended events count"),
    page: int = Query(1, ge=1, description="Page number"),
    pageSize: int = Query(10, ge=1, le=100, description="Items per page"),
    sortBy: Optional[str] = Query("createdAt", description="Sort field"),
    sortOrder: Optional[str] = Query("desc", description="Sort order (asc/desc)")
):
    """
    Filter users by various criteria with pagination and sorting.
    
    Supports filtering by:
    - Company name
    - Job title
    - City and State
    - Number of events hosted (range)
    - Number of events attended (range)
    
    Includes pagination and sorting options.
    """
    try:
        filters = UserFilter(
            company=company,
            jobTitle=jobTitle,
            city=city,
            state=state,
            hostedEventCountMin=hostedEventCountMin,
            hostedEventCountMax=hostedEventCountMax,
            attendedEventCountMin=attendedEventCountMin,
            attendedEventCountMax=attendedEventCountMax,
            page=page,
            pageSize=pageSize,
            sortBy=sortBy,
            sortOrder=sortOrder
        )
        
        return await user_service.filter_users(filters)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/", response_model=User)
async def create_user(user_data: UserCreate):
    """Create a new user"""
    try:
        return await user_service.create_user(user_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: str):
    """Get user by ID"""
    try:
        user = await user_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{user_id}", response_model=User)
async def update_user(user_id: str, user_data: UserUpdate):
    """Update user"""
    try:
        user = await user_service.update_user(user_id, user_data)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}/events/hosted")
async def get_hosted_events(user_id: str):
    """Get events hosted by user"""
    try:
        from app.services.event_service import event_service
        events = await event_service.get_events_by_owner(user_id)
        return {"events": events, "count": len(events)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}/email-stats")
async def get_user_email_stats(user_id: str):
    """Get email statistics for a specific user"""
    try:
        from app.services.email_service import email_service
        stats = await email_service.get_email_stats(user_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 
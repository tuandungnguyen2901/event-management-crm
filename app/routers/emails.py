from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import Response as FastAPIResponse
from typing import Optional

from app.models.email import EmailSendRequest, EmailSendResponse, EmailTrackingResponse
from app.models.user import UserFilter
from app.services.email_service import email_service
from app.services.user_service import user_service

router = APIRouter(prefix="/emails", tags=["emails"])


@router.post("/send", response_model=EmailSendResponse)
async def send_emails(request: EmailSendRequest):
    """
    Send emails to users based on their IDs.
    
    This endpoint:
    1. Gets users by their IDs
    2. Sends emails via SES (or mock)
    3. Records email status in EmailSentTable
    4. Returns sending statistics
    """
    try:
        # Get users by IDs
        users = await user_service.get_users_by_ids(request.userIds)
        
        if not users:
            raise HTTPException(status_code=404, detail="No users found with provided IDs")
        
        # Send emails
        response = await email_service.send_emails_to_users(request, users)
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send emails: {str(e)}")


@router.post("/send-filtered", response_model=EmailSendResponse)
async def send_emails_to_filtered_users(
    subject: str = Query(..., description="Email subject"),
    message: str = Query(..., description="Email message"),
    company: Optional[str] = Query(None, description="Filter by company name"),
    jobTitle: Optional[str] = Query(None, description="Filter by job title"),
    city: Optional[str] = Query(None, description="Filter by city"),
    state: Optional[str] = Query(None, description="Filter by state"),
    hostedEventCountMin: Optional[int] = Query(None, ge=0, description="Minimum hosted events count"),
    hostedEventCountMax: Optional[int] = Query(None, ge=0, description="Maximum hosted events count"),
    attendedEventCountMin: Optional[int] = Query(None, ge=0, description="Minimum attended events count"),
    attendedEventCountMax: Optional[int] = Query(None, ge=0, description="Maximum attended events count"),
):
    """
    Send emails to users based on filter criteria.
    
    This endpoint combines user filtering with email sending:
    1. Filters users based on provided criteria
    2. Sends emails to all matching users
    3. Returns sending statistics
    """
    try:
        # Create filter object
        filters = UserFilter(
            company=company,
            jobTitle=jobTitle,
            city=city,
            state=state,
            hostedEventCountMin=hostedEventCountMin,
            hostedEventCountMax=hostedEventCountMax,
            attendedEventCountMin=attendedEventCountMin,
            attendedEventCountMax=attendedEventCountMax,
            page=1,
            pageSize=1000  # Get many users at once
        )
        
        # Get filtered users
        user_response = await user_service.filter_users(filters)
        
        if not user_response.users:
            raise HTTPException(status_code=404, detail="No users found matching the filter criteria")
        
        # Create email request
        user_ids = [user.id for user in user_response.users]
        email_request = EmailSendRequest(
            userIds=user_ids,
            subject=subject,
            message=message
        )
        
        # Send emails
        response = await email_service.send_emails_to_users(email_request, user_response.users)
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send filtered emails: {str(e)}")


@router.get("/stats")
async def get_email_stats(user_id: Optional[str] = Query(None, description="Get stats for specific user")):
    """Get email statistics"""
    try:
        stats = await email_service.get_email_stats(user_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Tracking router - separate since it has different prefix
tracking_router = APIRouter(prefix="/track", tags=["tracking"])


@tracking_router.get("/open")
async def track_email_open(emailId: str = Query(..., description="Email ID to track")):
    """
    Track email open and return 1x1 tracking pixel.
    
    This endpoint:
    1. Updates EmailSentTable status to OPENED
    2. Adds openedAt timestamp
    3. Returns a 1x1 transparent pixel image
    """
    try:
        # Track the email open
        tracking_response = await email_service.track_email_open(emailId)
        
        # Return 1x1 transparent pixel
        pixel_data = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x04\x01\x00\x3B'
        
        return FastAPIResponse(
            content=pixel_data,
            media_type="image/gif",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except Exception as e:
        # Even if tracking fails, return the pixel to avoid breaking email display
        pixel_data = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x04\x01\x00\x3B'
        
        return FastAPIResponse(
            content=pixel_data,
            media_type="image/gif",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )


@tracking_router.get("/status/{email_id}", response_model=EmailTrackingResponse)
async def get_email_tracking_status(email_id: str):
    """Get email tracking status by email ID"""
    try:
        return await email_service.track_email_open(email_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 
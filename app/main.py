from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum
import os

from app.routers import users, events, emails
from app.routers.emails import tracking_router
from app.config.database import db_config

# Create FastAPI app
app = FastAPI(
    title="Event Management CRM API",
    description="A serverless FastAPI backend for Event Management CRM system with DynamoDB and email tracking",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router)
app.include_router(events.router)
app.include_router(emails.router)
app.include_router(tracking_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Event Management CRM API",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Event Management CRM API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "users": {
                "filter": "GET /users/filter - Filter users by criteria",
                "create": "POST /users - Create new user",
                "get": "GET /users/{user_id} - Get user by ID",
                "update": "PUT /users/{user_id} - Update user"
            },
            "events": {
                "create": "POST /events - Create new event",
                "get": "GET /events/{event_id} - Get event by ID",
                "update": "PUT /events/{event_id} - Update event",
                "attendees": "POST/DELETE /events/{event_id}/attendees/{user_id}"
            },
            "emails": {
                "send": "POST /emails/send - Send emails to specific users",
                "send_filtered": "POST /emails/send-filtered - Send emails to filtered users",
                "stats": "GET /emails/stats - Get email statistics"
            },
            "tracking": {
                "open": "GET /track/open?emailId={id} - Track email opens",
                "status": "GET /track/status/{email_id} - Get tracking status"
            }
        }
    }

# Error handler
@app.exception_handler(500)
async def internal_server_error(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": f"Internal server error: {str(exc)}"}
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    print("Starting Event Management CRM API...")
    
    # Create tables if in local development mode
    if os.getenv('DYNAMODB_ENDPOINT_URL'):
        print("Local development mode detected, creating DynamoDB tables...")
        db_config.create_tables_if_not_exist()
    
    print("API is ready!")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Shutting down Event Management CRM API...")

# AWS Lambda handler
handler = Mangum(app) 
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class EventBase(BaseModel):
    slug: str = Field(..., min_length=1, max_length=100, pattern="^[a-z0-9-]+$")
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    startAt: datetime
    endAt: datetime
    venue: Optional[str] = Field(None, max_length=300)
    maxCapacity: Optional[int] = Field(None, ge=1)
    owner: str  # User ID
    hosts: List[str] = Field(default_factory=list)  # List of User IDs
    attendees: List[str] = Field(default_factory=list)  # List of User IDs


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    slug: Optional[str] = Field(None, min_length=1, max_length=100, pattern="^[a-z0-9-]+$")
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    startAt: Optional[datetime] = None
    endAt: Optional[datetime] = None
    venue: Optional[str] = Field(None, max_length=300)
    maxCapacity: Optional[int] = Field(None, ge=1)
    hosts: Optional[List[str]] = None
    attendees: Optional[List[str]] = None


class Event(EventBase):
    id: str
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


class EventResponse(BaseModel):
    id: str
    slug: str
    title: str
    description: Optional[str]
    startAt: datetime
    endAt: datetime
    venue: Optional[str]
    maxCapacity: Optional[int]
    owner: str
    hosts: List[str]
    attendees: List[str]
    attendeeCount: int
    hostCount: int
    createdAt: datetime
    updatedAt: datetime 
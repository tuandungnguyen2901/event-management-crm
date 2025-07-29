from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class EmailStatus(str, Enum):
    pending = "PENDING"
    sent = "SENT"
    opened = "OPENED"
    failed = "FAILED"


class EmailSentBase(BaseModel):
    userId: str
    recipientEmail: EmailStr
    subject: str = Field(..., min_length=1, max_length=300)
    message: str = Field(..., min_length=1)
    status: EmailStatus = EmailStatus.pending


class EmailSentCreate(EmailSentBase):
    pass


class EmailSent(EmailSentBase):
    id: str
    sentAt: Optional[datetime] = None
    openedAt: Optional[datetime] = None
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


class EmailSendRequest(BaseModel):
    userIds: List[str] = Field(..., min_items=1)
    subject: str = Field(..., min_length=1, max_length=300)
    message: str = Field(..., min_length=1)


class EmailSendResponse(BaseModel):
    emailIds: List[str]
    totalSent: int
    totalFailed: int
    message: str


class EmailTrackingResponse(BaseModel):
    emailId: str
    status: EmailStatus
    openedAt: Optional[datetime]
    message: str 
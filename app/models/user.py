from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"
    prefer_not_to_say = "prefer_not_to_say"


class UserBase(BaseModel):
    firstName: str = Field(..., min_length=1, max_length=100)
    lastName: str = Field(..., min_length=1, max_length=100)
    phoneNumber: Optional[str] = Field(None, max_length=20)
    email: EmailStr
    avatar: Optional[str] = None
    gender: Optional[Gender] = None
    jobTitle: Optional[str] = Field(None, max_length=200)
    company: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    firstName: Optional[str] = Field(None, min_length=1, max_length=100)
    lastName: Optional[str] = Field(None, min_length=1, max_length=100)
    phoneNumber: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    avatar: Optional[str] = None
    gender: Optional[Gender] = None
    jobTitle: Optional[str] = Field(None, max_length=200)
    company: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)


class User(UserBase):
    id: str
    hostedEventCount: int = 0
    attendedEventCount: int = 0
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


class UserFilter(BaseModel):
    company: Optional[str] = None
    jobTitle: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    hostedEventCountMin: Optional[int] = Field(None, ge=0)
    hostedEventCountMax: Optional[int] = Field(None, ge=0)
    attendedEventCountMin: Optional[int] = Field(None, ge=0)
    attendedEventCountMax: Optional[int] = Field(None, ge=0)
    page: int = Field(1, ge=1)
    pageSize: int = Field(10, ge=1, le=100)
    sortBy: Optional[str] = Field("createdAt", pattern="^(firstName|lastName|company|jobTitle|hostedEventCount|attendedEventCount|createdAt)$")
    sortOrder: Optional[str] = Field("desc", pattern="^(asc|desc)$")


class UserResponse(BaseModel):
    users: list[User]
    total: int
    page: int
    pageSize: int
    totalPages: int 
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class Category(str, Enum):
    account_access = "account_access"
    technical_issue = "technical_issue"
    billing_question = "billing_question"
    feature_request = "feature_request"
    bug_report = "bug_report"
    other = "other"


class Priority(str, Enum):
    urgent = "urgent"
    high = "high"
    medium = "medium"
    low = "low"


class Status(str, Enum):
    new = "new"
    in_progress = "in_progress"
    waiting_customer = "waiting_customer"
    resolved = "resolved"
    closed = "closed"


class Source(str, Enum):
    web_form = "web_form"
    email = "email"
    api = "api"
    chat = "chat"
    phone = "phone"


class DeviceType(str, Enum):
    desktop = "desktop"
    mobile = "mobile"
    tablet = "tablet"


class TicketMetadata(BaseModel):
    source: Source = Source.api
    browser: Optional[str] = None
    device_type: Optional[DeviceType] = None


class TicketBase(BaseModel):
    customer_id: str = Field(..., min_length=1)
    customer_email: EmailStr
    customer_name: str = Field(..., min_length=1)
    subject: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    category: Optional[Category] = None
    priority: Optional[Priority] = None
    status: Status = Status.new
    assigned_to: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: TicketMetadata = Field(default_factory=TicketMetadata)


class TicketCreate(TicketBase):
    auto_classify: bool = False


class TicketUpdate(BaseModel):
    customer_id: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    customer_name: Optional[str] = None
    subject: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=2000)
    category: Optional[Category] = None
    priority: Optional[Priority] = None
    status: Optional[Status] = None
    assigned_to: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[TicketMetadata] = None


class Ticket(TicketBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    classification_confidence: Optional[float] = None

    model_config = {"from_attributes": True}


class ClassificationResult(BaseModel):
    ticket_id: str
    category: Category
    priority: Priority
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    keywords_found: List[str]


class ImportSummary(BaseModel):
    total: int
    successful: int
    failed: int
    errors: List[dict]
    tickets: List[Ticket]


class TicketListResponse(BaseModel):
    total: int
    tickets: List[Ticket]

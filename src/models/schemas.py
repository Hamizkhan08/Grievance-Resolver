"""
Data schemas for the grievance resolver system.
Defines the structure of complaints, escalations, and related entities.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator


class ComplaintStatus(str, Enum):
    """Complaint status enumeration."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"


class EscalationLevel(str, Enum):
    """Escalation level enumeration."""
    NONE = "none"
    LEVEL_1 = "level_1"  # Department head
    LEVEL_2 = "level_2"  # State/City commissioner
    LEVEL_3 = "level_3"  # Minister/Chief Secretary
    LEVEL_4 = "level_4"  # Chief Minister/Governor


class UrgencyLevel(str, Enum):
    """Urgency level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Location(BaseModel):
    """Geographical location information for India."""
    country: str = Field(default="India", description="Country name")
    state: Optional[str] = Field(None, description="State or Union Territory")
    district: Optional[str] = Field(None, description="District name")
    city: Optional[str] = Field(None, description="City or town name")
    pincode: Optional[str] = Field(None, description="PIN code (6 digits)")
    address: Optional[str] = Field(None, description="Full address text")
    
    @validator("pincode")
    def validate_pincode(cls, v):
        """Validate Indian PIN code format."""
        if v and (len(v) != 6 or not v.isdigit()):
            raise ValueError("PIN code must be 6 digits")
        return v


class ComplaintCreate(BaseModel):
    """Schema for creating a new complaint."""
    description: str = Field(..., min_length=10, description="Complaint description")
    citizen_name: Optional[str] = Field(None, description="Citizen name")
    citizen_email: Optional[str] = Field(None, description="Citizen email")
    citizen_phone: Optional[str] = Field(None, description="Citizen phone number")
    location: Location = Field(..., description="Location information")
    attachments: Optional[list[str]] = Field(default_factory=list, description="Attachment URLs")
    
    @validator("citizen_phone")
    def validate_phone(cls, v):
        """Validate Indian phone number format."""
        if v:
            # Remove spaces and common separators
            cleaned = v.replace(" ", "").replace("-", "").replace("+", "")
            # Should be 10 digits (or 11 with country code 91)
            if cleaned.startswith("91"):
                cleaned = cleaned[2:]
            if not (cleaned.isdigit() and len(cleaned) == 10):
                raise ValueError("Phone number must be 10 digits")
        return v


class Complaint(BaseModel):
    """Complaint entity schema."""
    id: str = Field(..., description="Unique complaint identifier")
    description: str = Field(..., description="Raw complaint description")
    structured_category: str = Field(..., description="Categorized issue type")
    location: Location = Field(..., description="Location information")
    responsible_department: str = Field(..., description="Assigned department")
    status: ComplaintStatus = Field(default=ComplaintStatus.OPEN, description="Current status")
    urgency: UrgencyLevel = Field(..., description="Urgency level")
    sla_deadline: datetime = Field(..., description="SLA deadline timestamp")
    escalation_level: EscalationLevel = Field(default=EscalationLevel.NONE, description="Current escalation level")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    citizen_name: Optional[str] = None
    citizen_email: Optional[str] = None
    citizen_phone: Optional[str] = None
    attachments: list[str] = Field(default_factory=list)
    agent_metadata: Dict[str, Any] = Field(default_factory=dict, description="Agent processing metadata")
    
    class Config:
        use_enum_values = True


class Escalation(BaseModel):
    """Escalation entity schema."""
    id: str = Field(..., description="Unique escalation identifier")
    complaint_id: str = Field(..., description="Reference to complaint")
    escalation_level: EscalationLevel = Field(..., description="Escalation level")
    reason: str = Field(..., description="Reason for escalation")
    escalated_to: str = Field(..., description="Authority escalated to")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Escalation timestamp")
    
    class Config:
        use_enum_values = True


class ComplaintStatusResponse(BaseModel):
    """Response schema for complaint status queries."""
    complaint_id: str
    status: ComplaintStatus
    time_remaining_hours: Optional[float] = Field(None, description="Hours until SLA breach")
    escalation_level: EscalationLevel
    last_update: datetime
    current_department: str
    message: Optional[str] = None
    
    class Config:
        use_enum_values = True


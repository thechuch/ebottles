from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from enum import Enum


class BudgetSensitivity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class CompanyType(str, Enum):
    MSO = "MSO"
    SINGLE_STATE_OPERATOR = "single_state_operator"
    BRAND_CPG = "brand_cpg"
    DISTRIBUTOR = "distributor"
    OTHER = "other"
    UNKNOWN = "unknown"


class PriorityBand(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ContactInfo(BaseModel):
    """Contact information from the lead form."""
    name: str = Field(..., min_length=1, description="Full name of the contact")
    company: str = Field(..., min_length=1, description="Company name")
    email: EmailStr = Field(..., description="Work email address")
    phone: Optional[str] = Field(None, description="Phone number (optional)")


class Metadata(BaseModel):
    """Metadata about the form submission."""
    source: str = Field(default="widget", description="Source of the submission")
    user_agent: str = Field(default="", description="Browser user agent")
    page_url: str = Field(default="", description="URL of the page where form was submitted")


class LeadIntakeRequest(BaseModel):
    """Request body for the lead intake endpoint."""
    freeform_note: str = Field(
        ..., 
        min_length=40, 
        description="User's description of their packaging needs"
    )
    contact: ContactInfo
    role: Optional[str] = Field(None, description="User's role/company type")
    metadata: Metadata = Field(default_factory=Metadata)


class AIExtraction(BaseModel):
    """Structured data extracted by AI from the freeform note."""
    product_types: list[str] = Field(default_factory=list, description="Types of packaging products needed")
    intended_use: Optional[str] = Field(None, description="What the packaging will be used for")
    markets: list[str] = Field(default_factory=list, description="Geographic markets or states")
    regulatory_needs: Optional[str] = Field(None, description="Compliance or regulatory requirements")
    estimated_monthly_volume: Optional[int] = Field(None, description="Estimated monthly units needed")
    timeline: Optional[str] = Field(None, description="Project timeline or urgency")
    budget_sensitivity: BudgetSensitivity = Field(default=BudgetSensitivity.UNKNOWN)
    sustainability_interest: Optional[bool] = Field(None, description="Interest in sustainable options")
    factory_direct_interest: Optional[bool] = Field(None, description="Interest in factory-direct sourcing")
    company_type: CompanyType = Field(default=CompanyType.UNKNOWN)
    priority_band: PriorityBand = Field(default=PriorityBand.MEDIUM)
    ai_summary: str = Field(default="", description="AI-generated summary of the lead")
    misc_notes: str = Field(default="", description="Additional notes or observations")
    confidence_flags: list[str] = Field(default_factory=list, description="Flags about extraction confidence")


class LeadIntakeResponse(BaseModel):
    """Response from the lead intake endpoint."""
    status: str = Field(..., description="'ok' or 'error'")
    lead_id: str = Field(..., description="Unique identifier for the lead")
    message: str = Field(..., description="Human-readable status message")


class TranscribeResponse(BaseModel):
    """Response from the transcription endpoint."""
    status: str = Field(..., description="'ok' or 'error'")
    text: str = Field(default="", description="Transcribed text")
    message: str = Field(default="", description="Error message if applicable")


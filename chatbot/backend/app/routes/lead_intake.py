import uuid
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends

from app.models.schemas import (
    LeadIntakeRequest,
    LeadIntakeResponse,
    AIExtraction,
    BudgetSensitivity,
    CompanyType,
    PriorityBand,
)
from app.security import require_api_key

logger = logging.getLogger(__name__)
from app.services.openai_service import OpenAIService, get_openai_service
from app.services.sheets_service import SheetsService, get_sheets_service
from app.services.gmail_service import GmailService, get_gmail_service
from app.config import get_settings

router = APIRouter()


@router.post("/lead-intake", response_model=LeadIntakeResponse)
async def submit_lead(
    request: LeadIntakeRequest,
    _: None = Depends(require_api_key),
    openai_service: OpenAIService = Depends(get_openai_service),
    sheets_service: SheetsService = Depends(get_sheets_service),
    gmail_service: GmailService = Depends(get_gmail_service),
):
    """
    Process a lead intake submission.
    
    1. Extract structured data from the freeform note using AI
    2. Append the lead to Google Sheets
    3. Send email notification to sales team
    4. Return confirmation with lead ID
    """
    lead_id = f"LEAD-{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.now(timezone.utc).isoformat()
    
    try:
        # Step 1: Extract structured data using AI (non-fatal; fall back if it fails)
        try:
            extraction = await openai_service.extract_lead_data(
                freeform_note=request.freeform_note,
                role=request.role,
            )
        except Exception as e:
            logger.exception(f"AI extraction failed for {lead_id}: {e}")
            extraction = AIExtraction(
                product_types=[],
                intended_use=None,
                markets=[],
                regulatory_needs=None,
                estimated_monthly_volume=None,
                timeline=None,
                budget_sensitivity=BudgetSensitivity.UNKNOWN,
                sustainability_interest=None,
                factory_direct_interest=None,
                company_type=CompanyType.UNKNOWN,
                priority_band=PriorityBand.MEDIUM,
                ai_summary=(request.freeform_note[:240] + "…") if len(request.freeform_note) > 240 else request.freeform_note,
                misc_notes="AI extraction unavailable (fallback summary used).",
                confidence_flags=["ai_unavailable"],
            )
        
        # Step 2: Append to Google Sheets
        row_data = {
            "timestamp": timestamp,
            "lead_id": lead_id,
            "source": request.metadata.source,
            "page_url": request.metadata.page_url,
            "contact_name": request.contact.name,
            "company": request.contact.company,
            "email": request.contact.email,
            "phone": request.contact.phone or "",
            "role": request.role or "",
            "raw_freeform_note": request.freeform_note,
            "ai_summary": extraction.ai_summary,
            "product_types": ", ".join(extraction.product_types),
            "intended_use": extraction.intended_use or "",
            "markets": ", ".join(extraction.markets),
            "estimated_monthly_volume": str(extraction.estimated_monthly_volume) if extraction.estimated_monthly_volume else "",
            "timeline": extraction.timeline or "",
            "sustainability_interest": str(extraction.sustainability_interest) if extraction.sustainability_interest is not None else "",
            "factory_direct_interest": str(extraction.factory_direct_interest) if extraction.factory_direct_interest is not None else "",
            "budget_sensitivity": extraction.budget_sensitivity.value,
            "compliance_needs": extraction.regulatory_needs or "",
            "priority_band": extraction.priority_band.value,
            "misc_notes": extraction.misc_notes,
            "status": "new",
        }
        
        # Step 2: Append to Sheets (fatal if it fails — otherwise we lose the lead)
        try:
            await sheets_service.append_lead(row_data)
        except Exception as e:
            logger.exception(f"Sheets append failed for {lead_id}: {e}")
            raise HTTPException(status_code=500, detail="Unable to save your request. Please try again.")
        
        # Step 3: Email notification (non-fatal; lead is already in Sheets)
        try:
            settings = get_settings()
            await gmail_service.send_notification(
                lead_id=lead_id,
                company=request.contact.company,
                contact_name=request.contact.name,
                email=request.contact.email,
                product_types=extraction.product_types,
                ai_summary=extraction.ai_summary,
                priority_band=extraction.priority_band.value,
                admin_emails=settings.admin_notification_emails_list,
            )
        except Exception as e:
            logger.exception(f"Email notification failed for {lead_id}: {e}")

        # Step 4: Confirmation email to the submitter (non-fatal)
        try:
            # Use sales notification email as the reply-to for the lead
            await gmail_service.send_lead_confirmation(
                to_email=str(request.contact.email),
                contact_name=request.contact.name,
                company=request.contact.company,
                ai_summary=extraction.ai_summary,
                lead_id=lead_id,
                sales_email=settings.notification_email,
            )
        except Exception as e:
            logger.exception(f"Lead confirmation email failed for {lead_id}: {e}")
        
        return LeadIntakeResponse(
            status="ok",
            lead_id=lead_id,
            message="Thank you! Your project has been received. Our team will follow up within one business day.",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error processing lead {lead_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your request. Please try again or contact us directly.",
        )


import json
import logging
from typing import Optional
from openai import AsyncOpenAI

from app.config import get_settings
from app.models.schemas import AIExtraction, BudgetSensitivity, CompanyType, PriorityBand

logger = logging.getLogger(__name__)

# JSON schema for structured output
EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "product_types": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Types of packaging products mentioned (e.g., 'child resistant jars', 'dropper bottles', 'pouches')"
        },
        "intended_use": {
            "type": ["string", "null"],
            "description": "What the packaging will be used for (e.g., 'cannabis gummies', 'CBD oil', 'supplements')"
        },
        "markets": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Geographic markets or states mentioned (e.g., 'California', 'Michigan', 'nationwide')"
        },
        "regulatory_needs": {
            "type": ["string", "null"],
            "description": "Any compliance or regulatory requirements mentioned (e.g., 'child resistant', 'ASTM certified', 'FDA compliant')"
        },
        "estimated_monthly_volume": {
            "type": ["integer", "null"],
            "description": "Estimated monthly quantity needed as a number, or null if not specified"
        },
        "timeline": {
            "type": ["string", "null"],
            "description": "Project timeline or urgency (e.g., 'ASAP', '3 months', 'Q2 2024')"
        },
        "budget_sensitivity": {
            "type": "string",
            "enum": ["low", "medium", "high", "unknown"],
            "description": "Budget sensitivity: 'low' = price is primary concern, 'high' = quality/features matter more than price, 'medium' = balanced, 'unknown' = not mentioned"
        },
        "sustainability_interest": {
            "type": ["boolean", "null"],
            "description": "Whether the lead expressed interest in sustainable/eco-friendly options"
        },
        "factory_direct_interest": {
            "type": ["boolean", "null"],
            "description": "Whether the lead expressed interest in factory-direct or custom manufacturing"
        },
        "company_type": {
            "type": "string",
            "enum": ["MSO", "single_state_operator", "brand_cpg", "distributor", "other", "unknown"],
            "description": "Type of company based on context"
        },
        "priority_band": {
            "type": "string",
            "enum": ["high", "medium", "low"],
            "description": "Lead priority: 'high' = large volume, urgent, or clear buying intent; 'medium' = moderate interest; 'low' = early research or small scale"
        },
        "ai_summary": {
            "type": "string",
            "description": "A concise 2-3 sentence summary of the lead's needs for the sales team"
        },
        "misc_notes": {
            "type": "string",
            "description": "Any other relevant details or observations not captured above"
        },
        "confidence_flags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Flags about extraction confidence (e.g., 'volume_estimated', 'timeline_unclear', 'vague_requirements')"
        }
    },
    "required": [
        "product_types", "intended_use", "markets", "regulatory_needs",
        "estimated_monthly_volume", "timeline", "budget_sensitivity",
        "sustainability_interest", "factory_direct_interest", "company_type",
        "priority_band", "ai_summary", "misc_notes", "confidence_flags"
    ],
    "additionalProperties": False
}

EXTRACTION_PROMPT = """You are an AI assistant for eBottles, a packaging company specializing in bottles, jars, containers, and flexible packaging for regulated and wellness markets (cannabis, CBD, nutraceuticals, supplements, cosmetics, and consumer packaged goods).

Analyze the following lead intake form submission and extract structured information. Be accurate and conservative - if something is not mentioned or unclear, use null or "unknown" rather than guessing.

User's description of their needs:
---
{freeform_note}
---

{role_context}

Extract the structured data according to the schema. For the AI summary, write 2-3 sentences that would help a sales rep quickly understand what this lead needs and how to approach them."""


class OpenAIService:
    """Service for OpenAI API interactions."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def extract_lead_data(
        self,
        freeform_note: str,
        role: Optional[str] = None,
    ) -> AIExtraction:
        """
        Extract structured lead data from a freeform note using GPT-4o.
        
        Uses structured outputs to ensure the response matches our schema.
        """
        role_context = ""
        if role:
            role_context = f"The user identified themselves as: {role}"
        
        prompt = EXTRACTION_PROMPT.format(
            freeform_note=freeform_note,
            role_context=role_context,
        )
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that extracts structured data from lead intake forms. Always respond with valid JSON matching the provided schema."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "lead_extraction",
                    "strict": True,
                    "schema": EXTRACTION_SCHEMA
                }
            },
            temperature=0.1,  # Low temperature for consistent extraction
        )
        
        # Parse the response
        content = response.choices[0].message.content
        data = json.loads(content)
        
        # Convert to our Pydantic model
        return AIExtraction(
            product_types=data.get("product_types", []),
            intended_use=data.get("intended_use"),
            markets=data.get("markets", []),
            regulatory_needs=data.get("regulatory_needs"),
            estimated_monthly_volume=data.get("estimated_monthly_volume"),
            timeline=data.get("timeline"),
            budget_sensitivity=BudgetSensitivity(data.get("budget_sensitivity", "unknown")),
            sustainability_interest=data.get("sustainability_interest"),
            factory_direct_interest=data.get("factory_direct_interest"),
            company_type=CompanyType(data.get("company_type", "unknown")),
            priority_band=PriorityBand(data.get("priority_band", "medium")),
            ai_summary=data.get("ai_summary", ""),
            misc_notes=data.get("misc_notes", ""),
            confidence_flags=data.get("confidence_flags", []),
        )
    
    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        filename: str = "audio.webm",
    ) -> str:
        """
        Transcribe audio using OpenAI Whisper.
        
        Returns the transcribed text.
        """
        # Create a file-like object for the API
        response = await self.client.audio.transcriptions.create(
            model="whisper-1",
            file=(filename, audio_bytes),
            response_format="text",
        )
        
        return response.strip()


# Dependency injection helper
_openai_service: Optional[OpenAIService] = None


def get_openai_service() -> OpenAIService:
    """Get or create the OpenAI service singleton."""
    global _openai_service
    if _openai_service is None:
        settings = get_settings()
        if not (settings.openai_api_key or "").strip():
            # Fail fast with a clear error instead of sending "Bearer " header.
            raise ValueError("OPENAI_API_KEY is not configured")
        _openai_service = OpenAIService(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
        )
    return _openai_service


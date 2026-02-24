import asyncio
import logging
from typing import Optional, Dict, Any, Union

import gspread
from google.oauth2.service_account import Credentials

from app.config import get_settings

logger = logging.getLogger(__name__)

# Column order matching the spec
SHEET_COLUMNS = [
    "timestamp",
    "lead_id",
    "source",
    "page_url",
    "contact_name",
    "company",
    "email",
    "phone",
    "role",
    "raw_freeform_note",
    "ai_summary",
    "product_types",
    "intended_use",
    "markets",
    "estimated_monthly_volume",
    "timeline",
    "sustainability_interest",
    "factory_direct_interest",
    "budget_sensitivity",
    "compliance_needs",
    "priority_band",
    "misc_notes",
    "status",
]


class SheetsService:
    """Service for Google Sheets interactions."""
    
    def __init__(self, credentials_dict: dict, sheet_id: str):
        """
        Initialize the Sheets service with credentials.
        
        Args:
            credentials_dict: Parsed Google service account JSON
            sheet_id: The Google Sheet ID to write to
        """
        self.sheet_id = sheet_id
        
        # Set up credentials with the required scopes
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        
        self.credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=scopes,
        )
        
        self.client = gspread.authorize(self.credentials)
        self._sheet = None
    
    @property
    def sheet(self):
        """Get the worksheet, opening it if needed."""
        if self._sheet is None:
            spreadsheet = self.client.open_by_key(self.sheet_id)
            self._sheet = spreadsheet.sheet1
        return self._sheet
    
    def _ensure_headers(self) -> None:
        """Ensure header row exists (sync operation)."""
        try:
            existing_headers = self.sheet.row_values(1)
            if not existing_headers or existing_headers[0] != SHEET_COLUMNS[0]:
                self.sheet.insert_row(SHEET_COLUMNS, 1)
        except Exception:
            self.sheet.insert_row(SHEET_COLUMNS, 1)
    
    def _append_row_sync(self, row_data: Dict[str, Any]) -> None:
        """Sync operation to append a row to the sheet."""
        row = [str(row_data.get(col, "")) for col in SHEET_COLUMNS]
        self._ensure_headers()
        self.sheet.append_row(row, value_input_option="USER_ENTERED")
    
    async def append_lead(self, row_data: Dict[str, Any]) -> None:
        """
        Append a lead row to the Google Sheet.
        
        Uses asyncio.to_thread to run the sync gspread operation
        without blocking the event loop.
        
        Args:
            row_data: Dictionary with column names as keys
        """
        await asyncio.to_thread(self._append_row_sync, row_data)
    
    def _find_lead_sync(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Sync operation to find a lead by ID."""
        try:
            cell = self.sheet.find(lead_id)
            if cell:
                row_data = self.sheet.row_values(cell.row)
                return dict(zip(SHEET_COLUMNS, row_data))
        except Exception:
            pass
        return None
    
    async def get_lead_by_id(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """
        Find a lead by its ID.
        
        Args:
            lead_id: The lead ID to search for
            
        Returns:
            Dictionary with lead data, or None if not found
        """
        return await asyncio.to_thread(self._find_lead_sync, lead_id)


class MockSheetsService:
    """Mock Sheets service that logs instead of writing."""
    
    async def append_lead(self, row_data: Dict[str, Any]) -> None:
        """Log the lead instead of writing to sheets."""
        logger.info(f"📊 [MOCK SHEETS] Would append lead: {row_data.get('lead_id')}")
        logger.debug(f"   Company: {row_data.get('company')}")
        logger.debug(f"   Contact: {row_data.get('contact_name')}")
    
    async def get_lead_by_id(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Mock lookup always returns None."""
        return None


# Dependency injection helper
_sheets_service: Optional[Union[SheetsService, MockSheetsService]] = None


def get_sheets_service() -> Union[SheetsService, MockSheetsService]:
    """Get or create the Sheets service singleton."""
    global _sheets_service
    if _sheets_service is None:
        settings = get_settings()
        credentials = settings.google_credentials_dict
        
        if not credentials:
            logger.warning("Google Sheets not configured - using mock service")
            _sheets_service = MockSheetsService()
            return _sheets_service
        
        if not settings.google_sheet_id:
            logger.warning("Google Sheet ID not configured - using mock service")
            _sheets_service = MockSheetsService()
            return _sheets_service
        
        _sheets_service = SheetsService(
            credentials_dict=credentials,
            sheet_id=settings.google_sheet_id,
        )
    return _sheets_service

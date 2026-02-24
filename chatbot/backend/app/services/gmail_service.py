import asyncio
import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Union

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from app.config import get_settings

logger = logging.getLogger(__name__)


class GmailService:
    """Service for sending email notifications via Gmail API."""
    
    def __init__(
        self,
        credentials_dict: dict,
        notification_email: str,
        from_email: str,
    ):
        """
        Initialize the Gmail service with credentials.
        
        Note: This requires domain-wide delegation to be set up for the
        service account, allowing it to send emails on behalf of users
        in the Google Workspace domain.
        
        Args:
            credentials_dict: Parsed Google service account JSON
            notification_email: Email address to send notifications to
            from_email: Email address to send from (must be in the domain)
        """
        self.notification_email = notification_email
        self.from_email = from_email
        
        # Set up credentials with Gmail scope
        scopes = ["https://www.googleapis.com/auth/gmail.send"]
        
        self.credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=scopes,
        )
        
        # For domain-wide delegation, we need to impersonate the from_email user
        self.delegated_credentials = self.credentials.with_subject(from_email)
        
        self._service = None
    
    @property
    def service(self):
        """Get the Gmail API service, building it if needed."""
        if self._service is None:
            self._service = build("gmail", "v1", credentials=self.delegated_credentials)
        return self._service
    
    def _create_email(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: str,
        reply_to: Optional[str] = None,
    ) -> dict:
        """Create an email message in the format required by Gmail API."""
        message = MIMEMultipart("alternative")
        message["to"] = to
        message["from"] = self.from_email
        message["subject"] = subject
        if reply_to:
            message["reply-to"] = reply_to
        
        # Add plain text and HTML parts
        part1 = MIMEText(body_text, "plain")
        part2 = MIMEText(body_html, "html")
        
        message.attach(part1)
        message.attach(part2)
        
        # Encode the message
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        return {"raw": raw}
    
    def _send_email_sync(
        self,
        *,
        to: str,
        subject: str,
        body_html: str,
        body_text: str,
        reply_to: Optional[str] = None,
    ) -> bool:
        """Synchronous email sending operation."""
        
        try:
            message = self._create_email(
                to=to,
                subject=subject,
                body_html=body_html,
                body_text=body_text,
                reply_to=reply_to,
            )
            
            self.service.users().messages().send(
                userId="me",
                body=message,
            ).execute()
            
            return True
            
        except Exception as e:
            # Common failure when domain-wide delegation isn't configured or sender doesn't exist:
            # invalid_grant: Invalid email or User ID
            logger.exception(
                "Failed to send email via Gmail API (from=%s to=%s). "
                "If you see invalid_grant, ensure domain-wide delegation is configured "
                "for the service account and NOTIFICATION_FROM_EMAIL is a real mailbox in that domain. Error=%s",
                self.from_email,
                to,
                e,
            )
            return False

    async def _send_email(
        self,
        *,
        to: str,
        subject: str,
        body_html: str,
        body_text: str,
        reply_to: Optional[str] = None,
    ) -> bool:
        """Async wrapper to send an email without blocking the event loop."""
        return await asyncio.to_thread(
            self._send_email_sync,
            to=to,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            reply_to=reply_to,
        )
    
    async def send_notification(
        self,
        lead_id: str,
        company: str,
        contact_name: str,
        email: str,
        product_types: List[str],
        ai_summary: str,
        priority_band: str,
        admin_emails: Optional[List[str]] = None,
    ) -> bool:
        """
        Send a lead notification email to the sales team.
        
        Uses asyncio.to_thread to run the sync Gmail API operation
        without blocking the event loop.
        
        Returns True if successful, False otherwise.
        """
        products_str = ", ".join(product_types) if product_types else "General Inquiry"

        subject = f"[New AI Lead] {company} - {products_str}"

        priority_emoji = {
            "high": "🔴",
            "medium": "🟡",
            "low": "🟢",
        }.get(priority_band, "⚪")

        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #0d7377; margin-bottom: 20px;">
                    {priority_emoji} New Lead: {company}
                </h2>

                <div style="background: #f0f7f7; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #0d7377;">
                    <h3 style="margin-top: 0; color: #1a4f5c;">AI Summary</h3>
                    <p style="margin-bottom: 0;">{ai_summary}</p>
                </div>

                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr>
                        <td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Lead ID:</strong></td>
                        <td style="padding: 8px 0; border-bottom: 1px solid #eee;">{lead_id}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Contact:</strong></td>
                        <td style="padding: 8px 0; border-bottom: 1px solid #eee;">{contact_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Email:</strong></td>
                        <td style="padding: 8px 0; border-bottom: 1px solid #eee;">
                            <a href="mailto:{email}" style="color: #0d7377;">{email}</a>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Company:</strong></td>
                        <td style="padding: 8px 0; border-bottom: 1px solid #eee;">{company}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Products:</strong></td>
                        <td style="padding: 8px 0; border-bottom: 1px solid #eee;">{products_str}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0;"><strong>Priority:</strong></td>
                        <td style="padding: 8px 0;">{priority_band.upper()}</td>
                    </tr>
                </table>

                <p style="color: #666; font-size: 14px;">
                    This lead was captured via the AI Intake Widget.
                </p>
            </div>
        </body>
        </html>
        """

        body_text = f"""
New Lead: {company}
Priority: {priority_band.upper()} {priority_emoji}

AI SUMMARY
{ai_summary}

DETAILS
- Lead ID: {lead_id}
- Contact: {contact_name}
- Email: {email}
- Company: {company}
- Products: {products_str}
        """.strip()

        recipients: List[str] = []
        # Always include primary notification email (sales)
        if self.notification_email:
            recipients.append(self.notification_email)
        # Add optional admin recipients
        if admin_emails:
            recipients.extend([e for e in admin_emails if e and e not in recipients])

        ok = True
        for to in recipients:
            sent = await self._send_email(
                to=to,
                subject=subject,
                body_html=body_html,
                body_text=body_text,
                reply_to=email,
            )
            ok = ok and sent
        return ok

    async def send_lead_confirmation(
        self,
        *,
        to_email: str,
        contact_name: str,
        company: str,
        ai_summary: str,
        lead_id: str,
        sales_email: str,
    ) -> bool:
        """Send a confirmation email to the person who submitted the form."""
        subject = f"We received your packaging request — {company}"

        greeting_name = contact_name.strip().split(" ")[0] if contact_name.strip() else "there"

        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #0d7377; margin-bottom: 10px;">Thanks, {greeting_name} — we’ve got your request.</h2>
                <p style="margin-top: 0; color: #444;">
                    Our team is reviewing your packaging needs and will follow up within one business day.
                </p>

                <div style="background: #f0f7f7; padding: 15px; border-radius: 8px; margin: 18px 0; border-left: 4px solid #0d7377;">
                    <h3 style="margin-top: 0; color: #1a4f5c;">What we understood</h3>
                    <p style="margin-bottom: 0;">{ai_summary}</p>
                </div>

                <p style="color: #666; font-size: 14px;">
                    Reference ID: <strong>{lead_id}</strong><br/>
                    If you have anything to add, just reply to this email or contact us at
                    <a href="mailto:{sales_email}" style="color: #0d7377;">{sales_email}</a>.
                </p>
            </div>
        </body>
        </html>
        """

        body_text = f"""
Thanks, {greeting_name} — we’ve got your request.

Our team is reviewing your packaging needs and will follow up within one business day.

WHAT WE UNDERSTOOD
{ai_summary}

Reference ID: {lead_id}
Reply to this email or contact {sales_email}.
        """.strip()

        return await self._send_email(
            to=to_email,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            reply_to=sales_email,
        )


class MockGmailService:
    """Mock Gmail service that logs instead of sending emails."""
    
    async def send_notification(
        self,
        lead_id: str,
        company: str,
        contact_name: str,
        email: str,
        product_types: List[str],
        ai_summary: str,
        priority_band: str,
        admin_emails: Optional[List[str]] = None,
    ) -> bool:
        """Log the notification instead of sending."""
        logger.info(f"📧 [MOCK EMAIL] Would send notification:")
        logger.info(f"   Lead ID: {lead_id}")
        logger.info(f"   Company: {company}")
        logger.info(f"   Contact: {contact_name} <{email}>")
        logger.info(f"   Products: {', '.join(product_types) if product_types else 'N/A'}")
        logger.info(f"   Priority: {priority_band}")
        if admin_emails:
            logger.info(f"   Admin recipients: {', '.join(admin_emails)}")
        logger.debug(f"   Summary: {ai_summary[:100]}...")
        return True

    async def send_lead_confirmation(
        self,
        *,
        to_email: str,
        contact_name: str,
        company: str,
        ai_summary: str,
        lead_id: str,
        sales_email: str,
    ) -> bool:
        logger.info("📧 [MOCK EMAIL] Would send lead confirmation:")
        logger.info("   To: %s", to_email)
        logger.info("   Lead ID: %s", lead_id)
        logger.info("   Company: %s", company)
        logger.debug("   Summary: %s...", ai_summary[:100])
        return True


# Dependency injection helper
_gmail_service: Optional[Union[GmailService, MockGmailService]] = None


def get_gmail_service() -> Union[GmailService, MockGmailService]:
    """Get or create the Gmail service singleton."""
    global _gmail_service
    if _gmail_service is None:
        settings = get_settings()
        credentials = settings.google_credentials_dict
        
        if not credentials:
            logger.warning("Gmail service not configured - using mock service")
            _gmail_service = MockGmailService()
            return _gmail_service
        
        _gmail_service = GmailService(
            credentials_dict=credentials,
            notification_email=settings.notification_email,
            from_email=settings.notification_from_email,
        )
    return _gmail_service

import smtplib
import socket
import re
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import make_msgid, formatdate
from datetime import datetime
import logging
from typing import Dict, Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_email_address(email: Optional[str]) -> tuple[bool, str]:
    """Validate RFC 5322 email address format and perform sanity checks."""
    if not email or not isinstance(email, str):
        return False, "Recipient email address is required and cannot be empty."

    cleaned = email.strip()
    if len(cleaned) < 5 or len(cleaned) > 320:
        return False, f"Email address length ({len(cleaned)} chars) is invalid. Must be between 5 and 320 characters."

    if " " in cleaned or "\t" in cleaned or "\n" in cleaned:
        return False, "Email address cannot contain spaces or newline characters."

    if ".." in cleaned:
        return False, "Email address cannot contain consecutive dots."

    if not EMAIL_REGEX.match(cleaned):
        return False, f"Invalid email format: '{cleaned}'. Must be a valid address such as client@example.com."

    domain_part = cleaned.split("@")[1]
    if "." not in domain_part or domain_part.startswith(".") or domain_part.endswith("."):
        return False, f"Invalid domain in email address: '{domain_part}'."

    return True, cleaned


def build_proposal_email_content(
    recipient_email: str,
    company_name: str,
    proposal_data: Dict[str, Any],
    lead_id: str = "",
    base_url: Optional[str] = None,
    request: Optional[Any] = None,
) -> tuple[str, str]:
    """Build plain-text and HTML versions of the proposal email."""
    if not base_url:
        base_url = settings.get_backend_url(request)

    title = proposal_data.get("title", f"Enterprise Solution Proposal for {company_name}")
    summary = proposal_data.get("executive_summary", "Enterprise solution tailored to your operational specifications.")
    solution = proposal_data.get("proposed_solution", "Comprehensive AI enterprise capability architecture.")
    timeline = proposal_data.get("total_implementation_timeline", "2-4 weeks")
    accept_url = f"{base_url.rstrip('/')}/api/proposals/{lead_id}/accept" if lead_id else f"{base_url.rstrip('/')}/api/proposals/accept"


    
    # Requirements
    reqs = proposal_data.get("customer_requirements", [])
    req_text = "\n".join([f"- {r}" for r in reqs]) if reqs else "- Custom enterprise AI automation workflow"
    req_html = "".join([f"<li style='margin-bottom: 6px;'>{r}</li>" for r in reqs]) if reqs else "<li>Custom enterprise AI automation workflow</li>"

    # Pricing
    pricing = proposal_data.get("pricing_proposal", {})
    if isinstance(pricing, dict):
        pricing_text = "\n".join([f"- {k.replace('_', ' ').title()}: {v}" for k, v in pricing.items()])
        pricing_rows = "".join([
            f"<tr><td style='padding: 8px 12px; border-bottom: 1px solid #e2e8f0;'><strong>{k.replace('_', ' ').title()}</strong></td>"
            f"<td style='padding: 8px 12px; border-bottom: 1px solid #e2e8f0; color: #4f46e5; font-weight: bold;'>{v}</td></tr>"
            for k, v in pricing.items()
        ])
    else:
        pricing_text = str(pricing)
        pricing_rows = f"<tr><td colspan='2' style='padding: 8px 12px;'>{pricing}</td></tr>"

    # Next steps
    next_steps = proposal_data.get("next_steps", ["Review proposal specification", "Schedule technical validation call"])
    steps_text = "\n".join([f"{idx+1}. {s}" for idx, s in enumerate(next_steps)])
    steps_html = "".join([f"<li style='margin-bottom: 6px;'>{s}</li>" for s in next_steps])

    # Plain text version
    text_content = f"""Dear {company_name} Team,

Thank you for your interest in our enterprise solutions. Below is your formal proposal summary:

{title}
Date: {datetime.utcnow().strftime('%B %d, %Y')}

1. EXECUTIVE SUMMARY
{summary}

2. CUSTOMER REQUIREMENTS & SCOPE
{req_text}

3. PROPOSED SOLUTION ARCHITECTURE
{solution}

4. IMPLEMENTATION TIMELINE
Estimated Duration: {timeline}

5. COMMERCIAL & PRICING
{pricing_text}

6. RECOMMENDED NEXT STEPS
{steps_text}

ACCEPTANCE & ONBOARDING:
To accept this proposal and confirm technical kickoff:
{accept_url}

Best regards,
Sales AI Solutions Team
sales@salesai-platform.com
"""

    # Rich responsive HTML version
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #1e293b;">
  <div style="max-width: 680px; margin: 0 auto; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01); border: 1px solid #e2e8f0;">
    
    <!-- Header banner -->
    <div style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); padding: 36px 32px; color: #ffffff;">
      <div style="font-size: 12px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: #c7d2fe; margin-bottom: 8px;">
        Grounded Enterprise Proposal
      </div>
      <h1 style="margin: 0; font-size: 24px; font-weight: 800; line-height: 1.3;">
        {title}
      </h1>
      <p style="margin: 8px 0 0 0; font-size: 13px; color: #e0e7ff;">
        Prepared exclusively for <strong>{company_name}</strong> • {datetime.utcnow().strftime('%B %d, %Y')}
      </p>
    </div>

    <!-- Body -->
    <div style="padding: 32px;">
      
      <!-- Executive summary callout -->
      <div style="background: #f1f5f9; border-left: 4px solid #4f46e5; border-radius: 8px; padding: 16px 20px; margin-bottom: 28px;">
        <h3 style="margin: 0 0 6px 0; font-size: 14px; font-weight: 700; color: #0f172a;">Executive Summary</h3>
        <p style="margin: 0; font-size: 13px; line-height: 1.6; color: #334155;">{summary}</p>
      </div>

      <!-- Section: Solution -->
      <div style="margin-bottom: 24px;">
        <h3 style="font-size: 15px; font-weight: 700; color: #0f172a; margin: 0 0 10px 0; border-bottom: 2px solid #f1f5f9; padding-bottom: 6px;">
          Solution Architecture & Capabilities
        </h3>
        <p style="margin: 0; font-size: 13px; line-height: 1.6; color: #334155; white-space: pre-line;">{solution}</p>
      </div>

      <!-- Section: Scope -->
      <div style="margin-bottom: 24px;">
        <h3 style="font-size: 15px; font-weight: 700; color: #0f172a; margin: 0 0 10px 0; border-bottom: 2px solid #f1f5f9; padding-bottom: 6px;">
          Verified Scope & Requirements
        </h3>
        <ul style="margin: 0; padding-left: 20px; font-size: 13px; line-height: 1.6; color: #334155;">
          {req_html}
        </ul>
      </div>

      <!-- Section: Pricing -->
      <div style="margin-bottom: 24px;">
        <h3 style="font-size: 15px; font-weight: 700; color: #0f172a; margin: 0 0 10px 0; border-bottom: 2px solid #f1f5f9; padding-bottom: 6px;">
          Commercial Investment & Timeline ({timeline})
        </h3>
        <table style="width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 8px;">
          <tbody>
            {pricing_rows}
          </tbody>
        </table>
      </div>

      <!-- Section: Next Steps -->
      <div style="margin-bottom: 32px;">
        <h3 style="font-size: 15px; font-weight: 700; color: #0f172a; margin: 0 0 10px 0; border-bottom: 2px solid #f1f5f9; padding-bottom: 6px;">
          Recommended Next Actions
        </h3>
        <ol style="margin: 0; padding-left: 20px; font-size: 13px; line-height: 1.6; color: #334155;">
          {steps_html}
        </ol>
      </div>

      <!-- Call to action button -->
      <div style="text-align: center; margin-top: 32px; padding-top: 24px; border-top: 1px solid #e2e8f0;">
        <a href="{accept_url}" target="_blank"
           style="display: inline-block; background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 10px; font-size: 14px; font-weight: 700; box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.25); letter-spacing: 0.01em;">
          ✓ Accept &amp; Schedule Kickoff
        </a>
        <p style="margin: 10px 0 0 0; font-size: 11px; color: #64748b;">
          Clicking above will confirm agreement terms and schedule technical onboarding.
        </p>
      </div>

    </div>

    <!-- Footer -->
    <div style="background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 20px 32px; font-size: 11px; color: #64748b; text-align: center;">
      <p style="margin: 0 0 4px 0;">This document was verified by the Sales AI Quality & Grounding Engine.</p>
      <p style="margin: 0;">© {datetime.utcnow().year} Sales AI Platform • All rights reserved.</p>
    </div>

  </div>
</body>
</html>
"""
    return text_content, html_content


def send_via_resend(
    api_key: str,
    recipient_email: str,
    subject: str,
    html_body: str,
    text_body: str,
    from_email: Optional[str] = None,
) -> Dict[str, Any]:
    """Transmit email via Resend HTTP REST API over HTTPS port 443 (Allowed on Render Free Tier)."""
    # Resend onboarding sandbox requires sender to be onboarding@resend.dev unless custom domain is verified
    sender = from_email if (from_email and "@" in from_email and not from_email.endswith("@gmail.com")) else "Sales AI <onboarding@resend.dev>"
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {api_key.strip()}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": sender,
                    "to": [recipient_email],
                    "subject": subject,
                    "html": html_body,
                    "text": text_body,
                },
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                msg_id = data.get("id", f"resend-{datetime.utcnow().timestamp()}")
                logger.info("Successfully transmitted proposal email to %s via Resend API [ID: %s]", recipient_email, msg_id)
                return {
                    "success": True,
                    "status": "sent",
                    "delivery_mode": "resend_api",
                    "message_id": msg_id,
                    "recipient": recipient_email,
                    "sender": sender,
                    "subject": subject,
                    "message": f"Email accepted for delivery to {recipient_email} via Resend API",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            else:
                err_data = resp.json() if "json" in resp.headers.get("content-type", "") else {}
                err_msg = err_data.get("message", resp.text)
                logger.error("Resend API rejected delivery to %s: %s (status %d)", recipient_email, err_msg, resp.status_code)
                return {
                    "success": False,
                    "status": "failed",
                    "delivery_mode": "resend_api",
                    "recipient": recipient_email,
                    "subject": subject,
                    "message": f"Resend API delivery failed: {err_msg}",
                    "error": err_msg,
                    "timestamp": datetime.utcnow().isoformat(),
                }
    except Exception as e:
        logger.error("HTTP error connecting to Resend API: %s", e)
        return {
            "success": False,
            "status": "failed",
            "delivery_mode": "resend_api_error",
            "recipient": recipient_email,
            "subject": subject,
            "message": f"Could not connect to Resend API over port 443: {str(e)}",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


def send_via_brevo(
    api_key: str,
    recipient_email: str,
    subject: str,
    html_body: str,
    text_body: str,
    from_email: Optional[str] = None,
) -> Dict[str, Any]:
    """Transmit email via Brevo HTTP REST API over HTTPS port 443 (Allowed on Render Free Tier)."""
    sender_email = from_email if (from_email and "@" in from_email) else "sales@salesai-platform.com"
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={
                    "api-key": api_key.strip(),
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json={
                    "sender": {"name": "Sales AI", "email": sender_email},
                    "to": [{"email": recipient_email}],
                    "subject": subject,
                    "htmlContent": html_body,
                    "textContent": text_body,
                },
            )
            if resp.status_code in (200, 201, 202):
                data = resp.json()
                msg_id = data.get("messageId", f"brevo-{datetime.utcnow().timestamp()}")
                logger.info("Successfully transmitted proposal email to %s via Brevo API [ID: %s]", recipient_email, msg_id)
                return {
                    "success": True,
                    "status": "sent",
                    "delivery_mode": "brevo_api",
                    "message_id": msg_id,
                    "recipient": recipient_email,
                    "sender": sender_email,
                    "subject": subject,
                    "message": f"Email accepted for delivery to {recipient_email} via Brevo API",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            else:
                err_data = resp.json() if "json" in resp.headers.get("content-type", "") else {}
                err_msg = err_data.get("message", resp.text)
                logger.error("Brevo API rejected delivery to %s: %s (status %d)", recipient_email, err_msg, resp.status_code)
                return {
                    "success": False,
                    "status": "failed",
                    "delivery_mode": "brevo_api",
                    "recipient": recipient_email,
                    "subject": subject,
                    "message": f"Brevo API delivery failed: {err_msg}",
                    "error": err_msg,
                    "timestamp": datetime.utcnow().isoformat(),
                }
    except Exception as e:
        logger.error("HTTP error connecting to Brevo API: %s", e)
        return {
            "success": False,
            "status": "failed",
            "delivery_mode": "brevo_api_error",
            "recipient": recipient_email,
            "subject": subject,
            "message": f"Could not connect to Brevo API over port 443: {str(e)}",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


def dispatch_proposal_email(
    recipient_email: str,
    company_name: str,
    proposal_data: Dict[str, Any],
    lead_id: str = "",
    base_url: Optional[str] = None,
    request: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Dispatch proposal email to client via real SMTP or HTTP Email API delivery.
    Strictly enforces real transmission:
    - Validates email syntax.
    - Connects to real email delivery provider (Resend / Brevo API over HTTPS port 443, or SMTP over TLS).
    - Generates RFC-compliant headers and Message-ID.
    - Verifies message acceptance by the email provider.
    - NEVER simulates delivery or reports 'sent' when unconfigured or failing.
    """
    # 1. Validate recipient email syntax
    is_valid, validation_msg = validate_email_address(recipient_email)
    if not is_valid:
        logger.warning(f"Email dispatch rejected due to invalid recipient: {validation_msg}")
        return {
            "success": False,
            "status": "failed",
            "delivery_mode": "invalid_email",
            "recipient": recipient_email,
            "subject": "",
            "message": validation_msg,
            "error": validation_msg,
            "timestamp": datetime.utcnow().isoformat(),
        }

    recipient_email = validation_msg  # sanitized address
    title = proposal_data.get("title", f"Enterprise Solution Proposal for {company_name}")
    subject = f"Enterprise Solution Proposal: {company_name}"

    text_body, html_body = build_proposal_email_content(
        recipient_email=recipient_email,
        company_name=company_name,
        proposal_data=proposal_data,
        lead_id=lead_id,
        base_url=base_url,
        request=request,
    )

    # 2. Priority A: Resend HTTP REST API (Over HTTPS port 443 - 100% permitted on Render Free Tier)
    if settings.RESEND_API_KEY:
        logger.info(f"Initiating HTTP API delivery to {recipient_email} via Resend API")
        return send_via_resend(
            api_key=settings.RESEND_API_KEY,
            recipient_email=recipient_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            from_email=settings.SMTP_FROM_EMAIL or settings.SMTP_USER,
        )

    # 2. Priority B: Brevo HTTP REST API (Over HTTPS port 443 - 100% permitted on Render Free Tier)
    if settings.BREVO_API_KEY:
        logger.info(f"Initiating HTTP API delivery to {recipient_email} via Brevo API")
        return send_via_brevo(
            api_key=settings.BREVO_API_KEY,
            recipient_email=recipient_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            from_email=settings.SMTP_FROM_EMAIL or settings.SMTP_USER,
        )

    # 3. Priority C: Standard Direct SMTP Delivery (ports 587/465)
    if not (settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD):
        missing = []
        if not settings.SMTP_HOST:
            missing.append("SMTP_HOST")
        if not settings.SMTP_USER:
            missing.append("SMTP_USER")
        if not settings.SMTP_PASSWORD:
            missing.append("SMTP_PASSWORD")

        err_msg = (
            f"Email delivery failed: SMTP server is not configured. "
            f"Missing: {', '.join(missing)} or HTTP Email API Key (Resend / Brevo). "
            f"Please configure an email delivery provider."
        )
        logger.warning(f"Proposal dispatch aborted for {recipient_email}: {err_msg}")
        return {
            "success": False,
            "status": "failed",
            "delivery_mode": "unconfigured",
            "recipient": recipient_email,
            "subject": subject,
            "message": err_msg,
            "error": f"SMTP unconfigured: {', '.join(missing)}",
            "timestamp": datetime.utcnow().isoformat(),
        }

    # 4. Real live SMTP delivery
    try:
        logger.info(f"Initiating real SMTP delivery to {recipient_email} via {settings.SMTP_HOST}:{settings.SMTP_PORT}")

        from_address = settings.SMTP_FROM_EMAIL if settings.SMTP_FROM_EMAIL and "@" in settings.SMTP_FROM_EMAIL else settings.SMTP_USER
        
        domain = settings.SMTP_HOST
        if "." in domain:
            domain_parts = domain.split(".")
            domain = ".".join(domain_parts[-2:])
        message_id = make_msgid(domain=domain)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_address
        msg["To"] = recipient_email
        msg["Reply-To"] = from_address
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = message_id

        part1 = MIMEText(text_body, "plain", "utf-8")
        part2 = MIMEText(html_body, "html", "utf-8")
        msg.attach(part1)
        msg.attach(part2)

        if settings.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
            server.ehlo()
            if settings.SMTP_USE_TLS:
                server.starttls()
                server.ehlo()

        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        refused_recipients = server.send_message(msg)
        server.quit()

        if refused_recipients:
            logger.error(f"SMTP rejected recipient {recipient_email}: {refused_recipients}")
            return {
                "success": False,
                "status": "failed",
                "delivery_mode": "smtp_live",
                "recipient": recipient_email,
                "subject": subject,
                "message": f"Email was rejected by SMTP server for recipient: {recipient_email}",
                "error": f"Recipient refused: {refused_recipients}",
                "message_id": message_id,
                "timestamp": datetime.utcnow().isoformat(),
            }

        logger.info(f"Successfully transmitted proposal email to {recipient_email} [Message-ID: {message_id}]")
        return {
            "success": True,
            "status": "sent",
            "delivery_mode": "smtp_live",
            "message_id": message_id,
            "recipient": recipient_email,
            "sender": from_address,
            "subject": subject,
            "smtp_host": settings.SMTP_HOST,
            "message": f"Email accepted for delivery to {recipient_email}",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP authentication failed for {settings.SMTP_USER}: {e}")
        return {
            "success": False,
            "status": "failed",
            "delivery_mode": "smtp_error",
            "recipient": recipient_email,
            "subject": subject,
            "message": "Email delivery failed: SMTP authentication error. Please verify your SMTP username and Gmail App Password (16 characters, 2-step verification must be enabled on Google).",
            "error": "SMTP authentication failed. Verify credentials.",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except smtplib.SMTPConnectError as e:
        logger.error(f"Failed to connect to SMTP server {settings.SMTP_HOST}:{settings.SMTP_PORT}: {e}")
        return {
            "success": False,
            "status": "failed",
            "delivery_mode": "smtp_error",
            "recipient": recipient_email,
            "subject": subject,
            "message": f"Email delivery failed: Could not connect to mail server at {settings.SMTP_HOST}:{settings.SMTP_PORT}.",
            "error": f"SMTP connection error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except (socket.timeout, TimeoutError) as e:
        logger.error(f"SMTP connection timed out to {settings.SMTP_HOST}:{settings.SMTP_PORT}: {e}")
        return {
            "success": False,
            "status": "failed",
            "delivery_mode": "smtp_error",
            "recipient": recipient_email,
            "subject": subject,
            "message": f"Email delivery failed: Connection to mail server at {settings.SMTP_HOST} timed out.",
            "error": "SMTP connection timed out.",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except smtplib.SMTPRecipientsRefused as e:
        logger.error(f"SMTP recipient {recipient_email} was refused: {e}")
        return {
            "success": False,
            "status": "failed",
            "delivery_mode": "smtp_error",
            "recipient": recipient_email,
            "subject": subject,
            "message": f"Email delivery failed: Recipient address '{recipient_email}' was rejected by mail server.",
            "error": f"Recipient refused: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except smtplib.SMTPException as e:
        logger.error(f"SMTP delivery exception: {e}")
        return {
            "success": False,
            "status": "failed",
            "delivery_mode": "smtp_error",
            "recipient": recipient_email,
            "subject": subject,
            "message": f"Email delivery failed: SMTP server reported error: {str(e)}",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except OSError as e:
        err_str = str(e)
        logger.error(f"Network OS error during SMTP connection: {e}")
        if getattr(e, "errno", None) == 101 or "Network is unreachable" in err_str:
            msg = (
                f"Email delivery failed: Outbound SMTP ports ({settings.SMTP_PORT}) are blocked by host network "
                f"[Errno 101: Network is unreachable]. "
                f"Render Free Tier prohibits traffic on ports 25, 465, and 587. "
                f"To send live emails on Render Free Tier, please provide a free Resend API key (over HTTPS port 443) or upgrade to a Render paid instance."
            )
        elif getattr(e, "errno", None) == 111 or "Connection refused" in err_str:
            msg = f"Email delivery failed: Connection refused to mail server at {settings.SMTP_HOST}:{settings.SMTP_PORT}."
        else:
            msg = f"Email delivery failed due to network socket error: {err_str}"
        return {
            "success": False,
            "status": "failed",
            "delivery_mode": "smtp_network_error",
            "recipient": recipient_email,
            "subject": subject,
            "message": msg,
            "error": err_str,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Unexpected error during proposal email dispatch: {e}")
        return {
            "success": False,
            "status": "failed",
            "delivery_mode": "error",
            "recipient": recipient_email,
            "subject": subject,
            "message": f"Email delivery failed: {str(e)}",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }

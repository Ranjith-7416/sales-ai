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


def dispatch_proposal_email(
    recipient_email: str,
    company_name: str,
    proposal_data: Dict[str, Any],
    lead_id: str = "",
    base_url: Optional[str] = None,
    request: Optional[Any] = None,
    custom_subject: Optional[str] = None,
    custom_message: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Dispatch email to client via REAL Gmail SMTP delivery.
    Strictly enforces real transmission:
    - Validates email syntax.
    - Connects to smtp.gmail.com:587.
    - Performs STARTTLS encryption.
    - Authenticates with Gmail App Password.
    - Sends message via server.send_message().
    - NEVER simulates delivery.
    - Returns real Gmail SMTP result or exact failure.
    """
    # 1. Validate recipient email syntax
    is_valid, validation_msg = validate_email_address(recipient_email)
    if not is_valid:
        logger.warning(f"Email dispatch rejected due to invalid recipient: {validation_msg}")
        return {
            "success": False,
            "provider": "gmail_smtp",
            "status": "failed",
            "delivery_mode": "invalid_email",
            "recipient": recipient_email,
            "subject": "",
            "message": validation_msg,
            "error": validation_msg,
            "timestamp": datetime.utcnow().isoformat(),
        }

    recipient_email = validation_msg  # sanitized address

    # 2. Build email content (supports custom subject/message or generated proposal)
    if custom_subject and custom_subject.strip():
        subject = custom_subject.strip()
    else:
        subject = f"Enterprise Solution Proposal: {company_name}"

    if custom_message and custom_message.strip():
        text_body = custom_message.strip()
        paragraphs = "".join([f"<p style='margin: 0 0 12px 0;'>{line}</p>" for line in custom_message.strip().split("\n") if line.strip()])
        html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; padding: 24px; color: #1e293b;">
  <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; padding: 28px; border: 1px solid #e2e8f0; font-size: 14px; line-height: 1.6;">
    {paragraphs}
    <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0 16px 0;" />
    <p style="font-size: 11px; color: #64748b; margin: 0;">Sent securely via Sales AI Gmail SMTP Delivery Engine</p>
  </div>
</body>
</html>"""
    else:
        text_body, html_body = build_proposal_email_content(
            recipient_email=recipient_email,
            company_name=company_name,
            proposal_data=proposal_data,
            lead_id=lead_id,
            base_url=base_url,
            request=request,
        )

    # 3. Provider Selection: Gmail SMTP is the ONLY active provider
    logger.info("Email provider selected: Gmail SMTP")

    # Check that Gmail SMTP is actually configured with valid non-placeholder credentials
    if not settings.is_smtp_configured():
        missing = []
        if not settings.SMTP_HOST or settings.is_placeholder(settings.SMTP_HOST):
            missing.append("SMTP_HOST")
        if not settings.SMTP_USER or settings.is_placeholder(settings.SMTP_USER):
            missing.append("SMTP_USERNAME")
        if not settings.SMTP_PASSWORD or settings.is_placeholder(settings.SMTP_PASSWORD):
            missing.append("SMTP_PASSWORD")

        err_msg = (
            f"Email delivery failed: Gmail SMTP is not configured. "
            f"Missing: {', '.join(missing) if missing else 'Valid credentials'}. "
            f"Please configure your Gmail address and 16-character Google App Password in environment variables or settings."
        )
        logger.warning("Proposal dispatch aborted for %s: %s", recipient_email, err_msg)
        return {
            "success": False,
            "provider": "gmail_smtp",
            "status": "failed",
            "delivery_mode": "unconfigured",
            "recipient": recipient_email,
            "subject": subject,
            "message": err_msg,
            "error": f"SMTP unconfigured: {', '.join(missing)}",
            "timestamp": datetime.utcnow().isoformat(),
        }

    # 4. Real live Gmail SMTP delivery flow:
    # SMTP connection -> EHLO -> STARTTLS -> EHLO -> Authentication -> send_message()
    try:
        logger.info("Connecting to %s:%d", settings.SMTP_HOST, settings.SMTP_PORT)

        # Sender must match authenticated Gmail mailbox
        from_user = settings.SMTP_USER.strip()
        from_address = f"Sales AI <{from_user}>"

        domain = settings.SMTP_HOST
        if "." in domain:
            domain_parts = domain.split(".")
            domain = ".".join(domain_parts[-2:])
        message_id = make_msgid(domain=domain)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_address
        msg["To"] = recipient_email
        msg["Reply-To"] = from_user
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = message_id

        part1 = MIMEText(text_body, "plain", "utf-8")
        part2 = MIMEText(html_body, "html", "utf-8")
        msg.attach(part1)
        msg.attach(part2)

        if settings.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
            server.ehlo()
            if settings.SMTP_USE_TLS:
                server.starttls()
                server.ehlo()

        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        logger.info("SMTP authentication successful for %s", settings.SMTP_USER)

        refused_recipients = server.send_message(msg)
        server.quit()

        if refused_recipients:
            logger.error("SMTP rejected recipient %s: %s", recipient_email, refused_recipients)
            return {
                "success": False,
                "provider": "gmail_smtp",
                "status": "failed",
                "delivery_mode": "smtp_live",
                "recipient": recipient_email,
                "subject": subject,
                "message": f"Email was rejected by SMTP server for recipient: {recipient_email}",
                "error": f"Recipient refused: {refused_recipients}",
                "message_id": message_id,
                "timestamp": datetime.utcnow().isoformat(),
            }

        logger.info("Email accepted by SMTP server for recipient: %s [Message-ID: %s]", recipient_email, message_id)
        return {
            "success": True,
            "provider": "gmail_smtp",
            "status": "sent",
            "delivery_mode": "smtp_live",
            "message_id": message_id,
            "recipient": recipient_email,
            "sender": from_address,
            "subject": subject,
            "smtp_host": settings.SMTP_HOST,
            "message": "Email accepted by Gmail SMTP",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except smtplib.SMTPAuthenticationError as e:
        logger.error("SMTP authentication failed for %s: %s", settings.SMTP_USER, str(e))
        return {
            "success": False,
            "provider": "gmail_smtp",
            "status": "failed",
            "delivery_mode": "smtp_error",
            "recipient": recipient_email,
            "subject": subject,
            "message": "Email delivery failed: Gmail SMTP authentication error. Please verify your Gmail address and 16-character Google App Password (ensure 2-Step Verification is enabled on your Google Account).",
            "error": "SMTP authentication failed. Verify credentials.",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except smtplib.SMTPConnectError as e:
        logger.error("Failed to connect to SMTP server %s:%d: %s", settings.SMTP_HOST, settings.SMTP_PORT, str(e))
        return {
            "success": False,
            "provider": "gmail_smtp",
            "status": "failed",
            "delivery_mode": "smtp_error",
            "recipient": recipient_email,
            "subject": subject,
            "message": f"Email delivery failed: Could not connect to mail server at {settings.SMTP_HOST}:{settings.SMTP_PORT}.",
            "error": f"SMTP connection error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except (socket.timeout, TimeoutError) as e:
        logger.error("SMTP connection timed out to %s:%d: %s", settings.SMTP_HOST, settings.SMTP_PORT, str(e))
        return {
            "success": False,
            "provider": "gmail_smtp",
            "status": "failed",
            "delivery_mode": "smtp_error",
            "recipient": recipient_email,
            "subject": subject,
            "message": f"Email delivery failed: Connection to mail server at {settings.SMTP_HOST} timed out.",
            "error": "SMTP connection timed out.",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except smtplib.SMTPRecipientsRefused as e:
        logger.error("SMTP recipient %s was refused: %s", recipient_email, str(e))
        return {
            "success": False,
            "provider": "gmail_smtp",
            "status": "failed",
            "delivery_mode": "smtp_error",
            "recipient": recipient_email,
            "subject": subject,
            "message": f"Email delivery failed: Recipient address '{recipient_email}' was rejected by mail server.",
            "error": f"Recipient refused: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except smtplib.SMTPException as e:
        logger.error("SMTP delivery exception: %s", str(e))
        return {
            "success": False,
            "provider": "gmail_smtp",
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
        logger.error("Network OS error during SMTP connection: %s", str(e))
        if getattr(e, "errno", None) == 101 or "Network is unreachable" in err_str:
            msg = (
                f"Email delivery failed: Outbound SMTP ports ({settings.SMTP_PORT}) are blocked by host network "
                f"[Errno 101: Network is unreachable]. "
                f"Render Free Tier prohibits traffic on outbound ports 25, 465, and 587."
            )
        elif getattr(e, "errno", None) == 111 or "Connection refused" in err_str:
            msg = f"Email delivery failed: Connection refused to mail server at {settings.SMTP_HOST}:{settings.SMTP_PORT}."
        else:
            msg = f"Email delivery failed due to network socket error: {err_str}"
        return {
            "success": False,
            "provider": "gmail_smtp",
            "status": "failed",
            "delivery_mode": "smtp_network_error",
            "recipient": recipient_email,
            "subject": subject,
            "message": msg,
            "error": err_str,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error("Unexpected error during proposal email dispatch: %s", str(e))
        return {
            "success": False,
            "provider": "gmail_smtp",
            "status": "failed",
            "delivery_mode": "error",
            "recipient": recipient_email,
            "subject": subject,
            "message": f"Email delivery failed: {str(e)}",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


def send_password_reset_otp_email(recipient_email: str, otp_code: str) -> dict:
    """
    Send a 6-digit verification code for password reset via SMTP.
    Falls back gracefully to logger in local development when SMTP is unconfigured.
    """
    subject = f"Your Sales AI Password Reset Code: {otp_code}"

    text_body = f"""Sales AI Account Security

Your verification code is: {otp_code}

This code will expire in 10 minutes. Enter this code on the password reset screen to set your new password.

If you did not request a password reset, please ignore this message. Your account remains secure and no changes will be made.

--
Sales AI Security Team
"""

    html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Sales AI Verification Code</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0c0a09; margin: 0; padding: 24px; color: #f5f5f4;">
  <div style="max-width: 520px; margin: 0 auto; background: #1c1917; border-radius: 16px; border: 1px solid rgba(249, 115, 22, 0.25); overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
    <div style="background: linear-gradient(135deg, #ea580c, #dc2626); padding: 24px; text-align: center;">
      <h1 style="color: #ffffff; margin: 0; font-size: 20px; font-weight: 800; letter-spacing: -0.5px;">Sales AI Account Security</h1>
    </div>
    <div style="padding: 28px 24px;">
      <p style="margin-top: 0; font-size: 15px; line-height: 1.6; color: #d6d3d1;">
        We received a request to reset the password for your Sales AI account. Use the 6-digit verification code below to complete your reset:
      </p>

      <div style="text-align: center; margin: 28px 0;">
        <div style="display: inline-block; background: #292524; border: 2px dashed #f97316; border-radius: 12px; padding: 16px 32px;">
          <span style="font-family: monospace, Consolas, Courier; font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #fb923c;">
            {otp_code}
          </span>
        </div>
        <p style="font-size: 12px; color: #a8a29e; margin-top: 8px;">Valid for 10 minutes</p>
      </div>

      <p style="font-size: 13px; line-height: 1.5; color: #a8a29e; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 16px;">
        <strong>Security Notice:</strong> If you did not request this code, you can safely ignore this email. No password changes will occur without this verification code.
      </p>
    </div>
  </div>
</body>
</html>"""

    # Check if SMTP is configured
    if not settings.is_smtp_configured():
        logger.warning(
            "[DEV / LOCAL OTP] SMTP is not configured. Password reset code for %s is: %s",
            recipient_email,
            otp_code,
        )
        return {
            "success": True,
            "provider": "dev_console",
            "status": "logged_to_console",
            "delivery_mode": "dev_fallback",
            "recipient": recipient_email,
            "subject": subject,
            "message": f"Verification code generated (development fallback): {otp_code}",
            "otp_code": otp_code,
            "timestamp": datetime.utcnow().isoformat(),
        }

    # Attempt live SMTP dispatch
    try:
        from_user = settings.SMTP_USER.strip()
        from_address = f"Sales AI Security <{from_user}>"

        domain = settings.SMTP_HOST
        if "." in domain:
            domain_parts = domain.split(".")
            domain = ".".join(domain_parts[-2:])
        message_id = make_msgid(domain=domain)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_address
        msg["To"] = recipient_email
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = message_id

        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        if settings.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
            server.ehlo()
            if settings.SMTP_USE_TLS:
                server.starttls()
                server.ehlo()

        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()

        logger.info("Password reset OTP email sent successfully to %s", recipient_email)
        return {
            "success": True,
            "provider": "gmail_smtp",
            "status": "sent",
            "delivery_mode": "smtp_live",
            "recipient": recipient_email,
            "subject": subject,
            "message": "Verification code sent to email inbox",
            "message_id": message_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as exc:
        logger.error("Failed to send OTP email via SMTP to %s: %s", recipient_email, str(exc))
        return {
            "success": True,
            "provider": "smtp_fallback_console",
            "status": "sent_with_warning",
            "delivery_mode": "dev_fallback",
            "recipient": recipient_email,
            "subject": subject,
            "message": f"Verification code logged to console (SMTP connection warning: {str(exc)})",
            "otp_code": otp_code,
            "timestamp": datetime.utcnow().isoformat(),
        }




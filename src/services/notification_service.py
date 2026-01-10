"""
Notification Service for sending emails and SMS.
Supports multiple notification channels.
"""
from typing import Dict, Any, Optional
from src.config.settings import settings
import structlog
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pytz import timezone
import httpx

logger = structlog.get_logger()

# India timezone
IST = timezone('Asia/Kolkata')


class NotificationService:
    """Service for sending notifications via email and SMS."""
    
    def __init__(self):
        """Initialize the notification service."""
        self.email_enabled = settings.enable_email_notifications
        # Default to Gmail SMTP if not specified
        self.smtp_config = {
            "host": settings.smtp_host or "smtp.gmail.com",
            "port": settings.smtp_port or 587,
            "user": settings.smtp_user,
            "password": settings.smtp_password,
        }
    
    def _format_name(self, name: str) -> str:
        """Format name with proper capitalization."""
        if not name:
            return "Citizen"
        # Capitalize first letter of each word
        return ' '.join(word.capitalize() for word in name.split())
    
    def _format_datetime(self, dt_string: str) -> str:
        """Format datetime string to readable format."""
        try:
            if isinstance(dt_string, str):
                # Parse ISO format datetime
                dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            else:
                dt = dt_string
            
            # Convert to IST
            if dt.tzinfo is None:
                dt = IST.localize(dt)
            else:
                dt = dt.astimezone(IST)
            
            # Format: "January 12, 2026 at 3:13 PM IST"
            return dt.strftime("%B %d, %Y at %I:%M %p IST")
        except Exception as e:
            logger.warning("Failed to format datetime", dt_string=dt_string, error=str(e))
            return str(dt_string)
    
    def _create_html_email(self, subject: str, body_plain: str, body_html: str = None) -> MIMEMultipart:
        """Create a professional HTML email with plain text fallback."""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        
        # Plain text version
        part1 = MIMEText(body_plain, 'plain', 'utf-8')
        msg.attach(part1)
        
        # HTML version
        if body_html:
            part2 = MIMEText(body_html, 'html', 'utf-8')
            msg.attach(part2)
        else:
            # Auto-convert plain text to HTML
            html_body = body_plain.replace('\n', '<br>\n')
            part2 = MIMEText(f"<html><body style='font-family: Arial, sans-serif; line-height: 1.6; color: #333;'>{html_body}</body></html>", 'html', 'utf-8')
            msg.attach(part2)
        
        return msg
    
    def send_complaint_submission_notification(
        self,
        complaint_id: str,
        citizen_email: str,
        citizen_name: str,
        department: str,
        sla_deadline: str
    ) -> Dict[str, Any]:
        """
        Send notification when complaint is submitted.
        
        Args:
            complaint_id: Complaint identifier
            citizen_email: Citizen email
            citizen_name: Citizen name
            department: Assigned department
            sla_deadline: SLA deadline
        
        Returns:
            Notification result
        """
        formatted_name = self._format_name(citizen_name)
        formatted_deadline = self._format_datetime(sla_deadline)
        complaint_short_id = complaint_id[:8].upper()
        
        subject = f"Complaint Registered - Reference #{complaint_short_id}"
        
        # Professional plain text version
        message_plain = f"""Dear {formatted_name},

Thank you for submitting your complaint through the Agentic Public Grievance Resolver system. Your complaint has been successfully registered and is now being processed.

COMPLAINT DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reference Number: {complaint_id}
Assigned Department: {department}
Expected Resolution Date: {formatted_deadline}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AUTOMATED PROCESSING COMPLETED:
Our AI-powered system has automatically:
  • Analyzed and categorized your complaint
  • Routed it to the appropriate department ({department})
  • Assigned a Service Level Agreement (SLA) deadline
  • Set up automated monitoring for timely resolution

NEXT STEPS:
You will receive email updates as your complaint progresses through the resolution process. You can also check the status of your complaint at any time using your Reference Number: {complaint_short_id}

If you have any questions or need assistance, please feel free to contact our support team.

We appreciate your patience and look forward to resolving your concern promptly.

Best regards,
Agentic Public Grievance Resolver
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated message. Please do not reply to this email.
For support, please visit our website or contact the helpdesk.
        """
        
        # Professional HTML version
        message_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border: 1px solid #e0e0e0; }}
        .details-box {{ background: white; border-left: 4px solid #667eea; padding: 20px; margin: 20px 0; border-radius: 4px; }}
        .detail-row {{ margin: 10px 0; padding: 8px 0; border-bottom: 1px solid #f0f0f0; }}
        .detail-label {{ font-weight: 600; color: #555; display: inline-block; width: 180px; }}
        .detail-value {{ color: #333; }}
        .steps {{ background: white; padding: 20px; margin: 20px 0; border-radius: 4px; }}
        .step-item {{ margin: 10px 0; padding-left: 25px; position: relative; }}
        .step-item:before {{ content: "✓"; position: absolute; left: 0; color: #4caf50; font-weight: bold; }}
        .footer {{ background: #f5f5f5; padding: 20px; text-align: center; font-size: 12px; color: #666; border-radius: 0 0 8px 8px; }}
        .complaint-id {{ font-family: 'Courier New', monospace; font-size: 14px; color: #667eea; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1 style="margin: 0; font-size: 24px;">Complaint Successfully Registered</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">Agentic Public Grievance Resolver</p>
    </div>
    
    <div class="content">
        <p>Dear <strong>{formatted_name}</strong>,</p>
        
        <p>Thank you for submitting your complaint through the Agentic Public Grievance Resolver system. Your complaint has been successfully registered and is now being processed.</p>
        
        <div class="details-box">
            <h3 style="margin-top: 0; color: #667eea;">Complaint Details</h3>
            <div class="detail-row">
                <span class="detail-label">Reference Number:</span>
                <span class="detail-value complaint-id">{complaint_id}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Assigned Department:</span>
                <span class="detail-value">{department}</span>
            </div>
            <div class="detail-row" style="border-bottom: none;">
                <span class="detail-label">Expected Resolution:</span>
                <span class="detail-value">{formatted_deadline}</span>
            </div>
        </div>
        
        <div class="steps">
            <h3 style="margin-top: 0; color: #667eea;">Automated Processing Completed</h3>
            <p>Our AI-powered system has automatically:</p>
            <div class="step-item">Analyzed and categorized your complaint</div>
            <div class="step-item">Routed it to the appropriate department ({department})</div>
            <div class="step-item">Assigned a Service Level Agreement (SLA) deadline</div>
            <div class="step-item">Set up automated monitoring for timely resolution</div>
        </div>
        
        <div style="background: #e3f2fd; padding: 15px; border-radius: 4px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #1976d2;">Next Steps</h3>
            <p style="margin-bottom: 0;">You will receive email updates as your complaint progresses through the resolution process. You can also check the status of your complaint at any time using your Reference Number: <strong class="complaint-id">{complaint_short_id}</strong></p>
        </div>
        
        <p>If you have any questions or need assistance, please feel free to contact our support team.</p>
        
        <p>We appreciate your patience and look forward to resolving your concern promptly.</p>
        
        <p>Best regards,<br>
        <strong>Agentic Public Grievance Resolver</strong><br>
         </p>
    </div>
    
    <div class="footer">
        <p style="margin: 0;">This is an automated message. Please do not reply to this email.</p>
        <p style="margin: 5px 0 0 0;">For support, please visit our website or contact the helpdesk.</p>
    </div>
</body>
</html>"""
        
        return self.send_email(citizen_email, subject, message_plain, message_html)
    
    def send_status_update_notification(
        self,
        complaint_id: str,
        citizen_email: str,
        citizen_name: str,
        status: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send status update notification.
        
        Args:
            complaint_id: Complaint identifier
            citizen_email: Citizen email
            citizen_name: Citizen name
            status: Current status
            message: Status message
        
        Returns:
            Notification result
        """
        formatted_name = self._format_name(citizen_name)
        complaint_short_id = complaint_id[:8].upper()
        status_display = status.replace('_', ' ').title()
        
        subject = f"Status Update - Complaint #{complaint_short_id}"
        
        message_plain = f"""Dear {formatted_name},

We have an update regarding your complaint.

COMPLAINT INFORMATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reference Number: {complaint_id}
Current Status: {status_display}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

UPDATE:
{message}

You can check the full status of your complaint at any time using your Reference Number: {complaint_short_id}

Thank you for your patience.

Best regards,
Agentic Public Grievance Resolver
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated message. Please do not reply to this email.
        """
        
        message_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border: 1px solid #e0e0e0; }}
        .details-box {{ background: white; border-left: 4px solid #667eea; padding: 20px; margin: 20px 0; border-radius: 4px; }}
        .update-box {{ background: #e3f2fd; padding: 20px; margin: 20px 0; border-radius: 4px; border-left: 4px solid #1976d2; }}
        .footer {{ background: #f5f5f5; padding: 20px; text-align: center; font-size: 12px; color: #666; border-radius: 0 0 8px 8px; }}
        .complaint-id {{ font-family: 'Courier New', monospace; font-size: 14px; color: #667eea; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1 style="margin: 0; font-size: 24px;">Complaint Status Update</h1>
    </div>
    
    <div class="content">
        <p>Dear <strong>{formatted_name}</strong>,</p>
        
        <p>We have an update regarding your complaint.</p>
        
        <div class="details-box">
            <h3 style="margin-top: 0; color: #667eea;">Complaint Information</h3>
            <p><strong>Reference Number:</strong> <span class="complaint-id">{complaint_id}</span></p>
            <p><strong>Current Status:</strong> {status_display}</p>
        </div>
        
        <div class="update-box">
            <h3 style="margin-top: 0; color: #1976d2;">Update</h3>
            <p style="white-space: pre-wrap;">{message}</p>
        </div>
        
        <p>You can check the full status of your complaint at any time using your Reference Number: <strong class="complaint-id">{complaint_short_id}</strong></p>
        
        <p>Thank you for your patience.</p>
        
        <p>Best regards,<br>
        <strong>Agentic Public Grievance Resolver</strong><br>
         </p>
    </div>
    
    <div class="footer">
        <p style="margin: 0;">This is an automated message. Please do not reply to this email.</p>
    </div>
</body>
</html>"""
        
        return self.send_email(citizen_email, subject, message_plain, message_html)
    
    def send_escalation_notification(
        self,
        complaint_id: str,
        citizen_email: str,
        citizen_name: str,
        escalation_level: str,
        escalated_to: str,
        reason: str
    ) -> Dict[str, Any]:
        """
        Send escalation notification.
        
        Args:
            complaint_id: Complaint identifier
            citizen_email: Citizen email
            citizen_name: Citizen name
            escalation_level: Escalation level
            escalated_to: Authority escalated to
            reason: Escalation reason
        
        Returns:
            Notification result
        """
        formatted_name = self._format_name(citizen_name)
        complaint_short_id = complaint_id[:8].upper()
        escalation_display = escalation_level.replace('_', ' ').title() if escalation_level else "High Priority"
        
        subject = f"URGENT: Complaint #{complaint_short_id} Escalated"
        
        message_plain = f"""Dear {formatted_name},

Your complaint has been escalated for immediate attention to ensure timely resolution.

COMPLAINT INFORMATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reference Number: {complaint_id}
Escalation Level: {escalation_display}
Escalated To: {escalated_to}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ESCALATION REASON:
{reason}

We are committed to resolving your issue promptly. You will receive updates as the matter progresses through the escalation process.

Thank you for your patience and understanding.

Best regards,
Agentic Public Grievance Resolver
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated message. Please do not reply to this email.
        """
        
        message_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border: 1px solid #e0e0e0; }}
        .details-box {{ background: white; border-left: 4px solid #f44336; padding: 20px; margin: 20px 0; border-radius: 4px; }}
        .reason-box {{ background: #ffebee; padding: 20px; margin: 20px 0; border-radius: 4px; border-left: 4px solid #f44336; }}
        .footer {{ background: #f5f5f5; padding: 20px; text-align: center; font-size: 12px; color: #666; border-radius: 0 0 8px 8px; }}
        .complaint-id {{ font-family: 'Courier New', monospace; font-size: 14px; color: #f44336; font-weight: bold; }}
        .urgent-badge {{ background: #f44336; color: white; padding: 5px 15px; border-radius: 20px; font-size: 12px; font-weight: bold; display: inline-block; margin-bottom: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <span class="urgent-badge">URGENT</span>
        <h1 style="margin: 0; font-size: 24px;">Complaint Escalated</h1>
    </div>
    
    <div class="content">
        <p>Dear <strong>{formatted_name}</strong>,</p>
        
        <p>Your complaint has been escalated for immediate attention to ensure timely resolution.</p>
        
        <div class="details-box">
            <h3 style="margin-top: 0; color: #f44336;">Complaint Information</h3>
            <p><strong>Reference Number:</strong> <span class="complaint-id">{complaint_id}</span></p>
            <p><strong>Escalation Level:</strong> {escalation_display}</p>
            <p><strong>Escalated To:</strong> {escalated_to}</p>
        </div>
        
        <div class="reason-box">
            <h3 style="margin-top: 0; color: #f44336;">Escalation Reason</h3>
            <p style="white-space: pre-wrap;">{reason}</p>
        </div>
        
        <p>We are committed to resolving your issue promptly. You will receive updates as the matter progresses through the escalation process.</p>
        
        <p>Thank you for your patience and understanding.</p>
        
        <p>Best regards,<br>
        <strong>Agentic Public Grievance Resolver</strong><br>
         </p>
    </div>
    
    <div class="footer">
        <p style="margin: 0;">This is an automated message. Please do not reply to this email.</p>
    </div>
</body>
</html>"""
        
        return self.send_email(citizen_email, subject, message_plain, message_html)
    
    def send_in_progress_notification(
        self,
        complaint_id: str,
        citizen_email: str,
        citizen_name: str,
        department: str,
        time_remaining: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send notification when complaint status changes to in_progress.
        
        Args:
            complaint_id: Complaint identifier
            citizen_email: Citizen email
            citizen_name: Citizen name
            department: Assigned department
            time_remaining: Time remaining until SLA deadline
        
        Returns:
            Notification result
        """
        formatted_name = self._format_name(citizen_name)
        complaint_short_id = complaint_id[:8].upper()
        
        subject = f"Complaint #{complaint_short_id} - Work In Progress"
        
        time_info = ""
        if time_remaining:
            time_info = f"Expected Resolution: {self._format_datetime(time_remaining) if isinstance(time_remaining, str) else time_remaining}"
        
        message_plain = f"""Dear {formatted_name},

Good news! Your complaint is now being actively worked on by the assigned department.

COMPLAINT INFORMATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reference Number: {complaint_id}
Status: In Progress
Assigned Department: {department}
{time_info}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Our team is working diligently to resolve your issue. You will be notified via email once it's resolved.

Thank you for your patience.

Best regards,
Agentic Public Grievance Resolver
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated message. Please do not reply to this email.
        """
        
        message_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border: 1px solid #e0e0e0; }}
        .details-box {{ background: white; border-left: 4px solid #4caf50; padding: 20px; margin: 20px 0; border-radius: 4px; }}
        .footer {{ background: #f5f5f5; padding: 20px; text-align: center; font-size: 12px; color: #666; border-radius: 0 0 8px 8px; }}
        .complaint-id {{ font-family: 'Courier New', monospace; font-size: 14px; color: #4caf50; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1 style="margin: 0; font-size: 24px;">Work In Progress</h1>
    </div>
    
    <div class="content">
        <p>Dear <strong>{formatted_name}</strong>,</p>
        
        <p>Good news! Your complaint is now being actively worked on by the assigned department.</p>
        
        <div class="details-box">
            <h3 style="margin-top: 0; color: #4caf50;">Complaint Information</h3>
            <p><strong>Reference Number:</strong> <span class="complaint-id">{complaint_id}</span></p>
            <p><strong>Status:</strong> In Progress</p>
            <p><strong>Assigned Department:</strong> {department}</p>
            {f'<p><strong>Expected Resolution:</strong> {self._format_datetime(time_remaining) if isinstance(time_remaining, str) else time_remaining}</p>' if time_remaining else ''}
        </div>
        
        <p>Our team is working diligently to resolve your issue. You will be notified via email once it's resolved.</p>
        
        <p>Thank you for your patience.</p>
        
        <p>Best regards,<br>
        <strong>Agentic Public Grievance Resolver</strong><br>
         </p>
    </div>
    
    <div class="footer">
        <p style="margin: 0;">This is an automated message. Please do not reply to this email.</p>
    </div>
</body>
</html>"""
        
        return self.send_email(citizen_email, subject, message_plain, message_html)
    
    def send_resolved_notification(
        self,
        complaint_id: str,
        citizen_email: str,
        citizen_name: str,
        department: str,
        resolution_details: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send notification when complaint is resolved.
        
        Args:
            complaint_id: Complaint identifier
            citizen_email: Citizen email
            citizen_name: Citizen name
            department: Department that resolved it
            resolution_details: Optional resolution details
        
        Returns:
            Notification result
        """
        formatted_name = self._format_name(citizen_name)
        complaint_short_id = complaint_id[:8].upper()
        
        subject = f"Complaint #{complaint_short_id} - Successfully Resolved"
        
        resolution_section = ""
        if resolution_details:
            resolution_section = f"""
RESOLUTION DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{resolution_details}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        message_plain = f"""Dear {formatted_name},

Great news! Your complaint has been successfully resolved.

COMPLAINT INFORMATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reference Number: {complaint_id}
Status: Resolved
Resolved By: {department}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{resolution_section}
We hope this resolves your concern. If you have any feedback or if the issue persists, please let us know by submitting a new complaint or contacting our support team.

Thank you for using our service and for your patience throughout the resolution process.

Best regards,
Agentic Public Grievance Resolver
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated message. Please do not reply to this email.
        """
        
        resolution_html = ""
        if resolution_details:
            resolution_html = f"""
        <div class="resolution-box">
            <h3 style="margin-top: 0; color: #4caf50;">Resolution Details</h3>
            <p style="white-space: pre-wrap;">{resolution_details}</p>
        </div>
"""
        
        message_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border: 1px solid #e0e0e0; }}
        .details-box {{ background: white; border-left: 4px solid #4caf50; padding: 20px; margin: 20px 0; border-radius: 4px; }}
        .resolution-box {{ background: #e8f5e9; padding: 20px; margin: 20px 0; border-radius: 4px; border-left: 4px solid #4caf50; }}
        .footer {{ background: #f5f5f5; padding: 20px; text-align: center; font-size: 12px; color: #666; border-radius: 0 0 8px 8px; }}
        .complaint-id {{ font-family: 'Courier New', monospace; font-size: 14px; color: #4caf50; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1 style="margin: 0; font-size: 24px;">✓ Complaint Resolved</h1>
    </div>
    
    <div class="content">
        <p>Dear <strong>{formatted_name}</strong>,</p>
        
        <p>Great news! Your complaint has been successfully resolved.</p>
        
        <div class="details-box">
            <h3 style="margin-top: 0; color: #4caf50;">Complaint Information</h3>
            <p><strong>Reference Number:</strong> <span class="complaint-id">{complaint_id}</span></p>
            <p><strong>Status:</strong> Resolved</p>
            <p><strong>Resolved By:</strong> {department}</p>
        </div>
{resolution_html}
        <p>We hope this resolves your concern. If you have any feedback or if the issue persists, please let us know by submitting a new complaint or contacting our support team.</p>
        
        <p>Thank you for using our service and for your patience throughout the resolution process.</p>
        
        <p>Best regards,<br>
        <strong>Agentic Public Grievance Resolver</strong><br>
         </p>
    </div>
    
    <div class="footer">
        <p style="margin: 0;">This is an automated message. Please do not reply to this email.</p>
    </div>
</body>
</html>"""
        
        return self.send_email(citizen_email, subject, message_plain, message_html)
    
    def send_sla_breach_notification(
        self,
        complaint_id: str,
        citizen_email: str,
        citizen_name: str,
        hours_overdue: float,
        department: str
    ) -> Dict[str, Any]:
        """
        Send notification when SLA is breached.
        
        Args:
            complaint_id: Complaint identifier
            citizen_email: Citizen email
            citizen_name: Citizen name
            hours_overdue: Hours past SLA deadline
            department: Assigned department
        
        Returns:
            Notification result
        """
        formatted_name = self._format_name(citizen_name)
        complaint_short_id = complaint_id[:8].upper()
        days_overdue = int(hours_overdue / 24)
        hours_remainder = int(hours_overdue % 24)
        
        time_overdue_str = f"{days_overdue} day(s)"
        if hours_remainder > 0 and days_overdue == 0:
            time_overdue_str = f"{hours_remainder} hour(s)"
        elif hours_remainder > 0:
            time_overdue_str = f"{days_overdue} day(s) and {hours_remainder} hour(s)"
        
        subject = f"URGENT: Complaint #{complaint_short_id} - SLA Breach Alert"
        
        message_plain = f"""Dear {formatted_name},

We want to inform you that your complaint has exceeded its expected resolution time.

COMPLAINT INFORMATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reference Number: {complaint_id}
Assigned Department: {department}
Time Overdue: {time_overdue_str}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

We sincerely apologize for the delay. Your complaint has been flagged for immediate attention and will be escalated to ensure prompt resolution.

We are working to resolve this as quickly as possible and will keep you updated on the progress.

Thank you for your patience and understanding.

Best regards,
Agentic Public Grievance Resolver
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated message. Please do not reply to this email.
        """
        
        message_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border: 1px solid #e0e0e0; }}
        .details-box {{ background: white; border-left: 4px solid #ff9800; padding: 20px; margin: 20px 0; border-radius: 4px; }}
        .alert-box {{ background: #fff3e0; padding: 20px; margin: 20px 0; border-radius: 4px; border-left: 4px solid #ff9800; }}
        .footer {{ background: #f5f5f5; padding: 20px; text-align: center; font-size: 12px; color: #666; border-radius: 0 0 8px 8px; }}
        .complaint-id {{ font-family: 'Courier New', monospace; font-size: 14px; color: #ff9800; font-weight: bold; }}
        .urgent-badge {{ background: #ff9800; color: white; padding: 5px 15px; border-radius: 20px; font-size: 12px; font-weight: bold; display: inline-block; margin-bottom: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <span class="urgent-badge">SLA BREACH ALERT</span>
        <h1 style="margin: 0; font-size: 24px;">Resolution Time Exceeded</h1>
    </div>
    
    <div class="content">
        <p>Dear <strong>{formatted_name}</strong>,</p>
        
        <p>We want to inform you that your complaint has exceeded its expected resolution time.</p>
        
        <div class="details-box">
            <h3 style="margin-top: 0; color: #ff9800;">Complaint Information</h3>
            <p><strong>Reference Number:</strong> <span class="complaint-id">{complaint_id}</span></p>
            <p><strong>Assigned Department:</strong> {department}</p>
            <p><strong>Time Overdue:</strong> {time_overdue_str}</p>
        </div>
        
        <div class="alert-box">
            <p style="margin: 0;"><strong>We sincerely apologize for the delay.</strong> Your complaint has been flagged for immediate attention and will be escalated to ensure prompt resolution.</p>
        </div>
        
        <p>We are working to resolve this as quickly as possible and will keep you updated on the progress.</p>
        
        <p>Thank you for your patience and understanding.</p>
        
        <p>Best regards,<br>
        <strong>Agentic Public Grievance Resolver</strong><br>
         </p>
    </div>
    
    <div class="footer">
        <p style="margin: 0;">This is an automated message. Please do not reply to this email.</p>
    </div>
</body>
</html>"""
        
        return self.send_email(citizen_email, subject, message_plain, message_html)
    
    def send_followup_notification(
        self,
        complaint_id: str,
        citizen_email: str,
        citizen_name: str,
        message: str,
        department: str
    ) -> Dict[str, Any]:
        """
        Send follow-up notification to citizen.
        
        Args:
            complaint_id: Complaint identifier
            citizen_email: Citizen email
            citizen_name: Citizen name
            message: Follow-up message
            department: Department name
        
        Returns:
            Notification result
        """
        formatted_name = self._format_name(citizen_name)
        complaint_short_id = complaint_id[:8].upper()
        
        subject = f"Follow-Up Update: Complaint #{complaint_short_id}"
        
        message_plain = f"""Dear {formatted_name},

We are providing you with an update on your complaint.

COMPLAINT INFORMATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reference Number: {complaint_id}
Assigned Department: {department}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FOLLOW-UP UPDATE:
{message}

We're actively monitoring your complaint and will keep you updated as soon as we receive a response from the department.

Thank you for your patience.

Best regards,
Agentic Public Grievance Resolver
 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated message. Please do not reply to this email.
        """
        
        message_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border: 1px solid #e0e0e0; }}
        .details-box {{ background: white; border-left: 4px solid #2196f3; padding: 20px; margin: 20px 0; border-radius: 4px; }}
        .update-box {{ background: #e3f2fd; padding: 20px; margin: 20px 0; border-radius: 4px; border-left: 4px solid #2196f3; }}
        .footer {{ background: #f5f5f5; padding: 20px; text-align: center; font-size: 12px; color: #666; border-radius: 0 0 8px 8px; }}
        .complaint-id {{ font-family: 'Courier New', monospace; font-size: 14px; color: #2196f3; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1 style="margin: 0; font-size: 24px;">Follow-Up Update</h1>
    </div>
    
    <div class="content">
        <p>Dear <strong>{formatted_name}</strong>,</p>
        
        <p>We are providing you with an update on your complaint.</p>
        
        <div class="details-box">
            <h3 style="margin-top: 0; color: #2196f3;">Complaint Information</h3>
            <p><strong>Reference Number:</strong> <span class="complaint-id">{complaint_id}</span></p>
            <p><strong>Assigned Department:</strong> {department}</p>
        </div>
        
        <div class="update-box">
            <h3 style="margin-top: 0; color: #1976d2;">Follow-Up Update</h3>
            <p style="white-space: pre-wrap;">{message}</p>
        </div>
        
        <p>We're actively monitoring your complaint and will keep you updated as soon as we receive a response from the department.</p>
        
        <p>Thank you for your patience.</p>
        
        <p>Best regards,<br>
        <strong>Agentic Public Grievance Resolver</strong><br>
         </p>
    </div>
    
    <div class="footer">
        <p style="margin: 0;">This is an automated message. Please do not reply to this email.</p>
    </div>
</body>
</html>"""
        
        return self.send_email(citizen_email, subject, message_plain, message_html)
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body_plain: str,
        body_html: str = None
    ) -> Dict[str, Any]:
        """
        Send email notification.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            body: Email body
        
        Returns:
            Notification result
        """
        if not self.email_enabled:
            logger.info("Email notifications disabled, skipping", to_email=to_email)
            return {
                "success": False,
                "method": "email",
                "message": "Email notifications are disabled"
            }
        
        if not self.smtp_config["user"] or not self.smtp_config["password"]:
            logger.warning("SMTP credentials missing, skipping email")
            return {
                "success": False,
                "method": "email",
                "message": "SMTP credentials missing"
            }
        
        try:
            # Create multipart message with HTML and plain text
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_config["user"]
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add plain text version
            part1 = MIMEText(body_plain, 'plain', 'utf-8')
            msg.attach(part1)
            
            # Add HTML version if provided
            if body_html:
                part2 = MIMEText(body_html, 'html', 'utf-8')
                msg.attach(part2)
            else:
                # Auto-convert plain text to basic HTML
                html_body = body_plain.replace('\n', '<br>\n')
                part2 = MIMEText(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
    </style>
</head>
<body>
{html_body}
</body>
</html>""", 'html', 'utf-8')
                msg.attach(part2)
            
            # Gmail SMTP configuration
            host = self.smtp_config["host"] or "smtp.gmail.com"
            port = self.smtp_config["port"] or 587
            
            # Use TLS for Gmail (port 587) or SSL for port 465
            if port == 465:
                server = smtplib.SMTP_SSL(host, port)
            else:
                server = smtplib.SMTP(host, port)
                server.starttls()
            
            server.login(self.smtp_config["user"], self.smtp_config["password"])
            server.send_message(msg)
            server.quit()
            
            logger.info("Email sent successfully", to_email=to_email, subject=subject)
            return {
                "success": True,
                "method": "email",
                "to": to_email,
                "message": "Email sent successfully"
            }
        except Exception as e:
            logger.error("Failed to send email", to_email=to_email, error=str(e))
            return {
                "success": False,
                "method": "email",
                "error": str(e)
            }
    
    def send_sms(
        self,
        phone_number: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send SMS notification (placeholder for SMS service integration).
        
        Args:
            phone_number: Recipient phone number
            message: SMS message
        
        Returns:
            Notification result
        """
        # TODO: Integrate with SMS service (Twilio, AWS SNS, etc.)
        logger.info("SMS notification requested", phone=phone_number, message_length=len(message))
        return {
            "success": False,
            "method": "sms",
            "message": "SMS service not yet implemented"
        }


# Global notification service instance
notification_service = NotificationService()


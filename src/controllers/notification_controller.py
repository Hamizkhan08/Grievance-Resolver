"""
Notification Controller.
Handles outbound communication to citizens.
"""
from typing import Optional
from src.agents.citizen_communication import CitizenCommunicationAgent
from src.models.database import db
from src.config.settings import settings
import structlog

logger = structlog.get_logger()


class NotificationController:
    """Controller for notification operations."""
    
    def __init__(self):
        """Initialize the notification controller."""
        self.communication_agent = CitizenCommunicationAgent()
    
    def send_status_update(self, complaint_id: str) -> dict:
        """
        Send a status update to the citizen.
        
        Args:
            complaint_id: Unique complaint identifier
        
        Returns:
            Notification result
        """
        try:
            complaint = db.get_complaint(complaint_id)
            if not complaint:
                return {"success": False, "error": "Complaint not found"}
            
            # Generate message
            message_data = self.communication_agent.process({
                "status": complaint.get("status"),
                "complaint_id": complaint_id,
                "department": complaint.get("responsible_department", "department"),
                "escalation_level": complaint.get("escalation_level"),
            })
            
            # Send notification (if email enabled)
            if settings.enable_email_notifications and complaint.get("citizen_email"):
                # TODO: Implement email sending
                logger.info("Email notification prepared", email=complaint["citizen_email"])
            
            return {
                "success": True,
                "message": message_data["message"],
                "subject": message_data["subject"],
                "sent": settings.enable_email_notifications,
            }
        
        except Exception as e:
            logger.error("Error sending notification", complaint_id=complaint_id, error=str(e))
            return {"success": False, "error": str(e)}


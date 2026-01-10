"""
Monitoring Agent.
Continuously checks complaint progress and SLA breaches.
Triggers escalation when needed.
"""
from typing import Dict, Any, List
from datetime import datetime
from src.agents.base import BaseAgent
from src.models.database import db
from src.models.schemas import ComplaintStatus
from src.services.notification_service import notification_service
import structlog

logger = structlog.get_logger()


class MonitoringAgent(BaseAgent):
    """Agent that monitors complaints and detects SLA breaches."""
    
    def __init__(self):
        """Initialize the monitoring agent."""
        super().__init__("MonitoringAgent")
    
    def process(self, input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Check for SLA breaches and complaints needing attention.
        
        Args:
            input_data: Optional input (not used, but required by interface)
        
        Returns:
            Dictionary with 'breaching_complaints' and 'action_required'
        """
        # Get all complaints breaching SLA
        breaching_complaints = db.get_complaints_breaching_sla()
        
        # Get complaints in progress for too long
        in_progress_complaints = db.get_complaints_by_status(ComplaintStatus.IN_PROGRESS)
        stale_complaints = self._find_stale_complaints(in_progress_complaints)
        
        result = {
            "breaching_complaints": [c.get("id") for c in breaching_complaints],
            "stale_complaints": [c.get("id") for c in stale_complaints],
            "action_required": len(breaching_complaints) + len(stale_complaints),
        }
        
        self.log_decision(result, {
            "breaching_count": len(breaching_complaints),
            "stale_count": len(stale_complaints)
        })
        
        return result
    
    def _find_stale_complaints(self, complaints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find complaints that have been in progress for too long.
        
        Args:
            complaints: List of complaint dictionaries
        
        Returns:
            List of stale complaints
        """
        stale = []
        now = datetime.utcnow()
        
        for complaint in complaints:
            updated_at_str = complaint.get("updated_at")
            if updated_at_str:
                try:
                    if isinstance(updated_at_str, str):
                        updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
                    else:
                        updated_at = updated_at_str
                    
                    # Consider stale if no update in 7 days
                    days_since_update = (now - updated_at.replace(tzinfo=None)).days
                    if days_since_update > 7:
                        stale.append(complaint)
                except Exception:
                    pass
        
        return stale
    
    def check_complaint_status(self, complaint_id: str) -> Dict[str, Any]:
        """
        Check status of a specific complaint.
        
        Args:
            complaint_id: Unique complaint identifier
        
        Returns:
            Status information dictionary
        """
        complaint = db.get_complaint(complaint_id)
        if not complaint:
            return {"error": "Complaint not found"}
        
        sla_deadline_str = complaint.get("sla_deadline")
        is_breaching = False
        hours_overdue = 0
        
        if sla_deadline_str:
            try:
                if isinstance(sla_deadline_str, str):
                    sla_deadline = datetime.fromisoformat(sla_deadline_str.replace("Z", "+00:00"))
                else:
                    sla_deadline = sla_deadline_str
                
                now = datetime.utcnow()
                if sla_deadline.tzinfo:
                    now = now.replace(tzinfo=sla_deadline.tzinfo)
                
                if now > sla_deadline:
                    is_breaching = True
                    delta = now - sla_deadline
                    hours_overdue = delta.total_seconds() / 3600.0
                    
                    # Send SLA breach notification if not already sent
                    if complaint.get("citizen_email") and complaint.get("status") not in [
                        ComplaintStatus.RESOLVED.value, ComplaintStatus.CLOSED.value
                    ]:
                        # Check if we've already notified (could add a flag to track this)
                        notification_service.send_sla_breach_notification(
                            complaint_id=complaint_id,
                            citizen_email=complaint["citizen_email"],
                            citizen_name=complaint.get("citizen_name", "Citizen"),
                            hours_overdue=hours_overdue,
                            department=complaint.get("responsible_department", "Department")
                        )
            except Exception as e:
                logger.warning("Error checking SLA", complaint_id=complaint_id, error=str(e))
        
        return {
            "complaint_id": complaint_id,
            "status": complaint.get("status"),
            "is_breaching_sla": is_breaching,
            "hours_overdue": round(hours_overdue, 2) if is_breaching else 0,
            "sla_deadline": sla_deadline_str,
        }


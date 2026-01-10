"""
View layer - API response formatters.
Formats internal data into user-friendly API responses.
No business logic or AI logic here.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from src.models.schemas import (
    Complaint, ComplaintStatus, EscalationLevel, ComplaintStatusResponse
)


class ComplaintSubmissionView:
    """Formats complaint submission responses."""
    
    @staticmethod
    def format(complaint: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a complaint submission response.
        
        Args:
            complaint: Complaint dictionary from database
        
        Returns:
            Formatted API response
        """
        return {
            "success": True,
            "message": "Complaint submitted successfully",
            "complaint": {
                "id": complaint.get("id"),
                "status": complaint.get("status"),
                "assigned_department": complaint.get("responsible_department"),
                "sla_deadline": complaint.get("sla_deadline"),
                "urgency": complaint.get("urgency"),
                "created_at": complaint.get("created_at"),
            }
        }


class ComplaintStatusView:
    """Formats complaint status responses."""
    
    @staticmethod
    def format(complaint: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a complaint status response.
        
        Args:
            complaint: Complaint dictionary from database
        
        Returns:
            Formatted API response
        """
        sla_deadline_str = complaint.get("sla_deadline")
        time_remaining_hours = None
        
        if sla_deadline_str:
            try:
                if isinstance(sla_deadline_str, str):
                    sla_deadline = datetime.fromisoformat(sla_deadline_str.replace("Z", "+00:00"))
                else:
                    sla_deadline = sla_deadline_str
                
                now = datetime.utcnow()
                if sla_deadline.tzinfo:
                    now = now.replace(tzinfo=sla_deadline.tzinfo)
                
                delta = sla_deadline - now
                time_remaining_hours = delta.total_seconds() / 3600.0
            except Exception:
                pass
        
        return {
            "success": True,
            "complaint": {
                "id": complaint.get("id"),
                "status": complaint.get("status"),
                "time_remaining_hours": round(time_remaining_hours, 2) if time_remaining_hours else None,
                "escalation_level": complaint.get("escalation_level", EscalationLevel.NONE.value),
                "last_update": complaint.get("updated_at"),
                "current_department": complaint.get("responsible_department"),
                "description": complaint.get("description"),
                "urgency": complaint.get("urgency"),
            }
        }


class AdminDashboardView:
    """Formats admin dashboard responses."""
    
    @staticmethod
    def format(metrics: Dict[str, Any], department_breakdown: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """
        Format admin dashboard metrics response.
        
        Args:
            metrics: Dictionary with complaint metrics
            department_breakdown: Optional breakdown by department
        
        Returns:
            Formatted API response
        """
        response = {
            "success": True,
            "metrics": {
                "total_complaints": metrics.get("total_complaints", 0),
                "by_status": {
                    "open": metrics.get("open", 0),
                    "in_progress": metrics.get("in_progress", 0),
                    "resolved": metrics.get("resolved", 0),
                    "escalated": metrics.get("escalated", 0),
                },
                "sla_breaches": metrics.get("sla_breaches", 0),
            }
        }
        
        if department_breakdown:
            response["metrics"]["by_department"] = department_breakdown
        
        return response


class ErrorView:
    """Formats error responses."""
    
    @staticmethod
    def format(message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Format an error response.
        
        Args:
            message: Error message
            error_code: Optional error code
            details: Optional additional error details
        
        Returns:
            Formatted error response
        """
        response = {
            "success": False,
            "error": message,
        }
        
        if error_code:
            response["error_code"] = error_code
        
        if details:
            response["details"] = details
        
        return response


class EscalationView:
    """Formats escalation responses."""
    
    @staticmethod
    def format(escalation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format an escalation response.
        
        Args:
            escalation: Escalation dictionary from database
        
        Returns:
            Formatted API response
        """
        return {
            "success": True,
            "escalation": {
                "id": escalation.get("id"),
                "complaint_id": escalation.get("complaint_id"),
                "level": escalation.get("escalation_level"),
                "reason": escalation.get("reason"),
                "escalated_to": escalation.get("escalated_to"),
                "created_at": escalation.get("created_at"),
            }
        }


"""
Follow-Up Controller.
Handles proactive follow-up actions for stale complaints.
"""
from typing import Dict, Any, List
from src.agents.followup import FollowUpAgent
from src.models.database import db
from src.views.responses import ErrorView
import structlog

logger = structlog.get_logger()


class FollowUpController:
    """Controller for follow-up operations."""
    
    def __init__(self):
        """Initialize the follow-up controller."""
        self.followup_agent = FollowUpAgent()
    
    def run_followups(self, days_without_update: int = 3) -> Dict[str, Any]:
        """
        Run follow-up process for stale complaints.
        
        Args:
            days_without_update: Number of days without update to trigger follow-up
        
        Returns:
            Dictionary with follow-up results
        """
        try:
            logger.info("Starting follow-up process", days=days_without_update)
            
            # Find stale complaints
            stale_complaints = self.followup_agent.find_stale_complaints(days_without_update)
            
            if not stale_complaints:
                return {
                    "success": True,
                    "message": "No stale complaints found",
                    "stale_count": 0,
                    "processed": 0
                }
            
            # Process each stale complaint
            results = []
            for complaint in stale_complaints:
                try:
                    result = self.followup_agent.process_followup(complaint)
                    results.append(result)
                except Exception as e:
                    logger.error("Error processing follow-up", 
                               complaint_id=complaint.get("id"), 
                               error=str(e))
                    results.append({
                        "success": False,
                        "complaint_id": complaint.get("id"),
                        "error": str(e)
                    })
            
            successful = sum(1 for r in results if r.get("success", False))
            
            return {
                "success": True,
                "message": f"Follow-up process completed",
                "stale_count": len(stale_complaints),
                "processed": len(results),
                "successful": successful,
                "results": results
            }
        except Exception as e:
            logger.error("Error in follow-up process", error=str(e))
            return ErrorView.format(f"Follow-up process failed: {str(e)}")
    
    def followup_single_complaint(self, complaint_id: str) -> Dict[str, Any]:
        """
        Run follow-up for a specific complaint.
        
        Args:
            complaint_id: Complaint identifier
        
        Returns:
            Dictionary with follow-up result
        """
        try:
            complaint = db.get_complaint(complaint_id)
            if not complaint:
                return ErrorView.format("Complaint not found")
            
            from src.models.schemas import ComplaintStatus
            if complaint.get("status") != ComplaintStatus.IN_PROGRESS.value:
                return ErrorView.format("Complaint is not in progress")
            
            result = self.followup_agent.process_followup(complaint)
            
            if result.get("success"):
                return {
                    "success": True,
                    "message": "Follow-up processed successfully",
                    "complaint_id": complaint_id,
                    "action_taken": result.get("action_taken"),
                    "citizen_notified": result.get("citizen_notified"),
                    "message": result.get("message")
                }
            else:
                return ErrorView.format(result.get("error", "Follow-up failed"))
        except Exception as e:
            logger.error("Error in single complaint follow-up", 
                        complaint_id=complaint_id, 
                        error=str(e))
            return ErrorView.format(f"Follow-up failed: {str(e)}")

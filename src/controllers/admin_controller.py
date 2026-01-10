"""
Admin Controller.
Handles admin dashboard and metrics.
"""
from typing import Optional, Dict, Any
from src.models.database import db
from src.views.responses import AdminDashboardView, ErrorView
from src.models.schemas import ComplaintStatus
import structlog

logger = structlog.get_logger()


class AdminController:
    """Controller for admin operations."""
    
    def get_all_complaints(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        department: Optional[str] = None
    ) -> dict:
        """
        Get all complaints with optional filters.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            status: Optional status filter
            department: Optional department filter
        
        Returns:
            Formatted API response with complaints list
        """
        try:
            complaints = db.get_all_complaints(
                limit=limit,
                offset=offset,
                status=status,
                department=department
            )
            
            return {
                "success": True,
                "complaints": complaints,
                "count": len(complaints)
            }
        except Exception as e:
            logger.error("Error fetching all complaints", error=str(e))
            return ErrorView.format(
                "Failed to fetch complaints",
                error_code="COMPLAINTS_FETCH_FAILED",
                details={"error": str(e)}
            )
    
    def update_complaint_status(
        self,
        complaint_id: str,
        new_status: str,
        notes: Optional[str] = None
    ) -> dict:
        """
        Update complaint status and send notification.
        
        Args:
            complaint_id: Complaint identifier
            new_status: New status value
            notes: Optional admin notes
        
        Returns:
            Formatted API response
        """
        try:
            # Validate status
            valid_statuses = [
                ComplaintStatus.OPEN.value,
                ComplaintStatus.IN_PROGRESS.value,
                ComplaintStatus.RESOLVED.value,
                ComplaintStatus.ESCALATED.value,
                ComplaintStatus.CLOSED.value
            ]
            
            if new_status not in valid_statuses:
                return ErrorView.format(
                    f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
                    error_code="INVALID_STATUS"
                )
            
            # Get current complaint
            current_complaint = db.get_complaint(complaint_id)
            if not current_complaint:
                return ErrorView.format(
                    "Complaint not found",
                    error_code="COMPLAINT_NOT_FOUND"
                )
            
            # Prepare updates
            updates = {
                "status": new_status,
                "updated_at": None  # Will be set by update_complaint
            }
            
            # Add notes to agent_metadata if provided
            if notes:
                metadata = current_complaint.get("agent_metadata", {})
                if not isinstance(metadata, dict):
                    metadata = {}
                if "admin_notes" not in metadata:
                    metadata["admin_notes"] = []
                metadata["admin_notes"].append({
                    "note": notes,
                    "status": new_status,
                    "timestamp": None  # Will be set by update_complaint
                })
                updates["agent_metadata"] = metadata
            
            # Update complaint (this will send notification automatically)
            updated_complaint = db.update_complaint(
                complaint_id=complaint_id,
                updates=updates,
                send_notification=True
            )
            
            if updated_complaint:
                logger.info(
                    "Complaint status updated",
                    complaint_id=complaint_id,
                    old_status=current_complaint.get("status"),
                    new_status=new_status
                )
                return {
                    "success": True,
                    "message": "Complaint status updated successfully",
                    "complaint": updated_complaint
                }
            else:
                return ErrorView.format(
                    "Failed to update complaint status",
                    error_code="UPDATE_FAILED"
                )
        except Exception as e:
            logger.error(
                "Error updating complaint status",
                complaint_id=complaint_id,
                error=str(e)
            )
            return ErrorView.format(
                "Failed to update complaint status",
                error_code="UPDATE_FAILED",
                details={"error": str(e)}
            )
    
    def get_dashboard_metrics(self) -> dict:
        """
        Get aggregated metrics for admin dashboard.
        
        Returns:
            Formatted API response
        """
        try:
            metrics = db.get_complaint_metrics()
            
            # Get department breakdown
            department_breakdown = self._get_department_breakdown()
            
            return AdminDashboardView.format(metrics, department_breakdown)
        
        except Exception as e:
            logger.error("Error fetching dashboard metrics", error=str(e))
            return ErrorView.format(
                "Failed to fetch dashboard metrics",
                error_code="METRICS_FETCH_FAILED",
                details={"error": str(e)}
            )
    
    def _get_department_breakdown(self) -> dict:
        """
        Get complaint counts by department.
        
        Returns:
            Dictionary mapping department names to counts
        """
        try:
            # Get all complaints
            all_complaints = db.get_complaints_by_status(ComplaintStatus.OPEN, limit=1000)
            all_complaints.extend(db.get_complaints_by_status(ComplaintStatus.IN_PROGRESS, limit=1000))
            all_complaints.extend(db.get_complaints_by_status(ComplaintStatus.ESCALATED, limit=1000))
            
            # Count by department
            department_counts = {}
            for complaint in all_complaints:
                dept = complaint.get("responsible_department", "unknown")
                department_counts[dept] = department_counts.get(dept, 0) + 1
            
            return department_counts
        except Exception as e:
            logger.warning("Error getting department breakdown", error=str(e))
            return {}


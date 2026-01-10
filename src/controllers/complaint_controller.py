"""
Complaint Controller.
Handles complaint creation and retrieval.
"""
from typing import Optional
from fastapi import HTTPException, BackgroundTasks
from src.models.schemas import ComplaintCreate
from src.models.database import db
from src.views.responses import ComplaintSubmissionView, ComplaintStatusView, ErrorView
from src.workflows.complaint_workflow import ComplaintWorkflow
from src.services.notification_service import notification_service
import structlog

logger = structlog.get_logger()


class ComplaintController:
    """Controller for complaint operations."""
    
    def __init__(self):
        """Initialize the complaint controller."""
        self.workflow = ComplaintWorkflow()
    
    def create_complaint(self, complaint_data: ComplaintCreate, background_tasks: BackgroundTasks = None) -> dict:
        """
        Create a new complaint and trigger agentic workflow.
        
        Args:
            complaint_data: Complaint creation schema
        
        Returns:
            Formatted API response
        """
        try:
            # Convert Pydantic model to dict
            workflow_input = {
                "description": complaint_data.description,
                "location": complaint_data.location.dict(),
                "citizen_name": complaint_data.citizen_name,
                "citizen_email": complaint_data.citizen_email,
                "citizen_phone": complaint_data.citizen_phone,
                "attachments": complaint_data.attachments or [],
            }
            
            # Execute workflow
            workflow_result = self.workflow.run(workflow_input)
            
            # Check for errors
            if workflow_result.get("errors"):
                logger.warning("Workflow completed with errors", errors=workflow_result["errors"])
            
            # Get created complaint from database
            complaint_id = workflow_result.get("complaint_id")
            if not complaint_id:
                raise HTTPException(status_code=500, detail="Failed to create complaint")
            
            complaint = db.get_complaint(complaint_id)
            if not complaint:
                raise HTTPException(status_code=404, detail="Complaint not found after creation")
            
            # Send notification in background
            if background_tasks and complaint.get("citizen_email"):
                background_tasks.add_task(
                    notification_service.send_complaint_submission_notification,
                    complaint_id=complaint_id,
                    citizen_email=complaint.get("citizen_email"),
                    citizen_name=complaint.get("citizen_name", "Citizen"),
                    department=complaint.get("responsible_department", "Department"),
                    sla_deadline=complaint.get("sla_deadline", "")
                )
            
            # Format response
            return ComplaintSubmissionView.format(complaint)
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error creating complaint", error=str(e))
            return ErrorView.format(
                "Failed to create complaint",
                error_code="COMPLAINT_CREATION_FAILED",
                details={"error": str(e)}
            )
    
    def get_complaint_status(self, complaint_id: str) -> dict:
        """
        Get the status of a complaint.
        
        Args:
            complaint_id: Unique complaint identifier
        
        Returns:
            Formatted API response
        """
        try:
            complaint = db.get_complaint(complaint_id)
            if not complaint:
                return ErrorView.format(
                    "Complaint not found",
                    error_code="COMPLAINT_NOT_FOUND"
                )
            
            return ComplaintStatusView.format(complaint)
        
        except Exception as e:
            logger.error("Error fetching complaint status", complaint_id=complaint_id, error=str(e))
            return ErrorView.format(
                "Failed to fetch complaint status",
                error_code="FETCH_FAILED",
                details={"error": str(e)}
            )


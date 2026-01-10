"""
Monitoring Controller.
Handles SLA monitoring and escalation triggers.
"""
from src.workflows.monitoring_workflow import MonitoringWorkflow
from src.models.database import db
import structlog

logger = structlog.get_logger()


class MonitoringController:
    """Controller for monitoring operations."""
    
    def __init__(self):
        """Initialize the monitoring controller."""
        self.workflow = MonitoringWorkflow()
    
    def run_monitoring_cycle(self) -> dict:
        """
        Run a monitoring cycle to check SLA breaches and trigger escalations.
        
        Returns:
            Monitoring results
        """
        try:
            workflow_result = self.workflow.run()
            
            return {
                "success": True,
                "breaching_complaints": len(workflow_result.get("breaching_complaints", [])),
                "stale_complaints": len(workflow_result.get("stale_complaints", [])),
                "escalated_complaints": len(workflow_result.get("escalated_complaints", [])),
                "notifications_sent": len(workflow_result.get("notifications_sent", [])),
                "errors": workflow_result.get("errors", []),
            }
        except Exception as e:
            logger.error("Error in monitoring cycle", error=str(e))
            return {
                "success": False,
                "error": str(e),
            }


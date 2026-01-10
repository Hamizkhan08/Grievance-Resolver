"""
Monitoring and Escalation Workflow using LangGraph.
Continuously monitors complaints and triggers escalations.
"""
from typing import TypedDict
from langgraph.graph import StateGraph, END
from src.agents.monitoring import MonitoringAgent
from src.agents.escalation import EscalationAgent
from src.agents.citizen_communication import CitizenCommunicationAgent
from src.agents.followup import FollowUpAgent
from src.models.database import db
from src.models.schemas import ComplaintStatus, EscalationLevel
from src.services.notification_service import notification_service
import structlog
import langchain

# Patch langchain.debug to avoid AttributeError in LangGraph
if not hasattr(langchain, 'debug'):
    langchain.debug = False

logger = structlog.get_logger()


class MonitoringState(TypedDict):
    """State for monitoring workflow."""
    breaching_complaints: list
    stale_complaints: list
    followup_results: list
    escalated_complaints: list
    notifications_sent: list
    errors: list


class MonitoringWorkflow:
    """LangGraph workflow for monitoring and escalation."""
    
    def __init__(self):
        """Initialize the workflow and agents."""
        self.monitoring_agent = MonitoringAgent()
        self.escalation_agent = EscalationAgent()
        self.communication_agent = CitizenCommunicationAgent()
        self.followup_agent = FollowUpAgent()
        
        # Build workflow graph
        self.workflow = self._build_workflow()
        # Compile without debug mode (langchain.debug doesn't exist in newer versions)
        self.app = self.workflow.compile(debug=False)
        logger.info("Monitoring workflow initialized")
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(MonitoringState)
        
        # Add nodes
        workflow.add_node("monitor", self._monitor_complaints)
        workflow.add_node("followup", self._followup_stale)
        workflow.add_node("check_escalation", self._check_escalations)
        workflow.add_node("escalate", self._escalate_complaints)
        workflow.add_node("notify", self._notify_citizens)
        
        # Define edges
        workflow.set_entry_point("monitor")
        workflow.add_edge("monitor", "followup")
        workflow.add_edge("followup", "check_escalation")
        workflow.add_edge("check_escalation", "escalate")
        workflow.add_edge("escalate", "notify")
        workflow.add_edge("notify", END)
        
        return workflow
    
    def _monitor_complaints(self, state: MonitoringState) -> MonitoringState:
        """Node: Monitor for SLA breaches."""
        try:
            result = self.monitoring_agent.process()
            state["breaching_complaints"] = result["breaching_complaints"]
            state["stale_complaints"] = result["stale_complaints"]
            logger.info("Monitoring completed", breaches=len(state["breaching_complaints"]))
        except Exception as e:
            logger.error("Error in monitoring", error=str(e))
            state.setdefault("errors", []).append(f"Monitoring failed: {str(e)}")
        
        return state
    
    def _followup_stale(self, state: MonitoringState) -> MonitoringState:
        """Node: Follow up on stale in-progress complaints."""
        state["followup_results"] = []
        
        # Find stale complaints (3 days without update)
        stale_complaints = self.followup_agent.find_stale_complaints(days_without_update=3)
        
        for complaint in stale_complaints:
            try:
                result = self.followup_agent.process_followup(complaint)
                state["followup_results"].append(result)
                logger.info("Follow-up processed", 
                          complaint_id=complaint.get("id"),
                          success=result.get("success"))
            except Exception as e:
                logger.error("Error in follow-up", 
                           complaint_id=complaint.get("id"), 
                           error=str(e))
                state.setdefault("errors", []).append(f"Follow-up failed for {complaint.get('id')}: {str(e)}")
        
        logger.info("Follow-up node completed", processed=len(state["followup_results"]))
        return state
    
    def _check_escalations(self, state: MonitoringState) -> MonitoringState:
        """Node: Check which complaints need escalation."""
        state["escalated_complaints"] = []
        
        all_complaints = state["breaching_complaints"] + state["stale_complaints"]
        
        for complaint_id in all_complaints:
            try:
                complaint = db.get_complaint(complaint_id)
                if not complaint:
                    continue
                
                # Check status
                status_info = self.monitoring_agent.check_complaint_status(complaint_id)
                
                if status_info.get("is_breaching_sla"):
                    escalation_result = self.escalation_agent.process({
                        "complaint_id": complaint_id,
                        "hours_overdue": status_info.get("hours_overdue", 0),
                        "urgency": complaint.get("urgency", "medium"),
                        "current_escalation_level": complaint.get("escalation_level", EscalationLevel.NONE.value),
                    })
                    
                    if escalation_result.get("escalation_needed"):
                        state["escalated_complaints"].append({
                            "complaint_id": complaint_id,
                            "escalation_data": escalation_result,
                        })
            except Exception as e:
                logger.error("Error checking escalation", complaint_id=complaint_id, error=str(e))
        
        return state
    
    def _escalate_complaints(self, state: MonitoringState) -> MonitoringState:
        """Node: Perform escalations."""
        for escalation_info in state["escalated_complaints"]:
            try:
                complaint_id = escalation_info["complaint_id"]
                escalation_data = escalation_info["escalation_data"]
                
                # Create escalation record
                escalation_record = {
                    "id": f"esc_{complaint_id}_{int(__import__('time').time())}",
                    "complaint_id": complaint_id,
                    "escalation_level": escalation_data["escalation_level"],
                    "reason": escalation_data["reason"],
                    "escalated_to": escalation_data["escalated_to"],
                }
                
                db.create_escalation(escalation_record)
                
                # Update complaint
                db.update_complaint(complaint_id, {
                    "status": ComplaintStatus.ESCALATED.value,
                    "escalation_level": escalation_data["escalation_level"],
                })
                
                logger.info("Complaint escalated", complaint_id=complaint_id, level=escalation_data["escalation_level"])
            except Exception as e:
                logger.error("Error escalating", complaint_id=complaint_id, error=str(e))
                state.setdefault("errors", []).append(f"Escalation failed for {complaint_id}: {str(e)}")
        
        return state
    
    def _notify_citizens(self, state: MonitoringState) -> MonitoringState:
        """Node: Notify citizens of escalations."""
        state["notifications_sent"] = []
        
        for escalation_info in state["escalated_complaints"]:
            try:
                complaint_id = escalation_info["complaint_id"]
                complaint = db.get_complaint(complaint_id)
                
                if complaint:
                    result = self.communication_agent.process({
                        "status": ComplaintStatus.ESCALATED.value,
                        "complaint_id": complaint_id,
                        "department": complaint.get("responsible_department", "department"),
                        "escalation_level": complaint.get("escalation_level", EscalationLevel.NONE.value),
                    })
                    
                    state["notifications_sent"].append({
                        "complaint_id": complaint_id,
                        "message": result["message"],
                        "subject": result["subject"],
                    })
                    
                    # Send email notification for escalation
                    if complaint.get("citizen_email"):
                        escalation_data = escalation_info["escalation_data"]
                        notification_service.send_escalation_notification(
                            complaint_id=complaint_id,
                            citizen_email=complaint["citizen_email"],
                            citizen_name=complaint.get("citizen_name", "Citizen"),
                            escalation_level=escalation_data.get("escalation_level", ""),
                            escalated_to=escalation_data.get("escalated_to", ""),
                            reason=escalation_data.get("reason", "")
                        )
                        
                        # Also send status update
                        notification_service.send_status_update_notification(
                            complaint_id=complaint_id,
                            citizen_email=complaint["citizen_email"],
                            citizen_name=complaint.get("citizen_name", "Citizen"),
                            status=ComplaintStatus.ESCALATED.value,
                            message=result["message"]
                        )
            except Exception as e:
                logger.error("Error notifying citizen", complaint_id=complaint_id, error=str(e))
        
        return state
    
    def run(self) -> dict:
        """
        Execute the monitoring workflow.
        
        Returns:
            Final workflow state
        """
        initial_state: MonitoringState = {
            "breaching_complaints": [],
            "stale_complaints": [],
            "followup_results": [],
            "escalated_complaints": [],
            "notifications_sent": [],
            "errors": [],
        }
        
        try:
            final_state = self.app.invoke(initial_state)
            return final_state
        except Exception as e:
            logger.error("Monitoring workflow execution failed", error=str(e))
            initial_state["errors"].append(f"Workflow failed: {str(e)}")
            return initial_state


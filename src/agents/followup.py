"""
Follow-Up Agent.
Autonomous agent that proactively follows up on in-progress complaints
that haven't been updated in a while.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from langchain_core.prompts import ChatPromptTemplate
from src.agents.base import BaseAgent
from src.agents.prompts import AgentPrompts
from src.agents.llm_factory import create_llm
from src.models.database import db
import structlog
import json
import re

logger = structlog.get_logger()


class FollowUpAgent(BaseAgent):
    """Agent that proactively follows up on stale in-progress complaints."""
    
    def __init__(self):
        """Initialize the follow-up agent."""
        super().__init__("FollowUpAgent")
        try:
            self.llm = create_llm(temperature=0.3)
            logger.info("LLM initialized for follow-up agent")
        except Exception as e:
            logger.error("Failed to initialize LLM for follow-up agent", error=str(e))
            raise RuntimeError("FollowUpAgent requires LLM to be configured") from e
    
    def process(self, input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process input data - required by BaseAgent.
        This method finds and processes stale complaints.
        
        Args:
            input_data: Optional input with 'days_without_update' key
        
        Returns:
            Dictionary with follow-up results
        """
        days_without_update = input_data.get("days_without_update", 3) if input_data else 3
        stale_complaints = self.find_stale_complaints(days_without_update)
        
        results = []
        for complaint in stale_complaints:
            result = self.process_followup(complaint)
            results.append(result)
        
        return {
            "stale_count": len(stale_complaints),
            "processed": len(results),
            "successful": sum(1 for r in results if r.get("success", False)),
            "results": results
        }
    
    def find_stale_complaints(self, days_without_update: int = 3) -> List[Dict[str, Any]]:
        """
        Find complaints that are in progress but haven't been updated recently.
        
        Args:
            days_without_update: Number of days without update to consider stale
        
        Returns:
            List of stale complaint records
        """
        try:
            from src.models.schemas import ComplaintStatus
            
            # Get all in-progress complaints
            in_progress = db.get_complaints_by_status(ComplaintStatus.IN_PROGRESS, limit=1000)
            
            stale_complaints = []
            cutoff_date = datetime.utcnow() - timedelta(days=days_without_update)
            
            for complaint in in_progress:
                updated_at_str = complaint.get("updated_at") or complaint.get("created_at")
                if not updated_at_str:
                    continue
                
                try:
                    # Parse ISO format datetime
                    updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
                    if updated_at.tzinfo:
                        updated_at = updated_at.replace(tzinfo=None)
                    
                    if updated_at < cutoff_date:
                        stale_complaints.append(complaint)
                except Exception as e:
                    logger.warning("Error parsing date", complaint_id=complaint.get("id"), error=str(e))
                    continue
            
            logger.info("Found stale complaints", count=len(stale_complaints), days=days_without_update)
            return stale_complaints
        except Exception as e:
            logger.error("Error finding stale complaints", error=str(e))
            return []
    
    def generate_followup_action(
        self,
        complaint: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a follow-up action for a stale complaint using AI.
        
        Args:
            complaint: Complaint record
        
        Returns:
            Dictionary with follow-up action details
        """
        try:
            description = complaint.get("description", "")
            department = complaint.get("responsible_department", "")
            department_name = complaint.get("current_department", "")
            complaint_id = complaint.get("id", "")
            status = complaint.get("status", "")
            updated_at = complaint.get("updated_at", complaint.get("created_at", ""))
            
            # Calculate days since last update
            days_since_update = 0
            if updated_at:
                try:
                    last_update = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                    if last_update.tzinfo:
                        last_update = last_update.replace(tzinfo=None)
                    days_since_update = (datetime.utcnow() - last_update).days
                except:
                    pass
            
            prompt = ChatPromptTemplate.from_template(AgentPrompts.FOLLOWUP_ACTION_PROMPT.template)
            formatted_prompt = prompt.format_messages(
                complaint_id=complaint_id[:8],
                description=description,
                department=department_name or department,
                status=status,
                days_since_update=days_since_update
            )
            
            logger.info("Generating follow-up action", complaint_id=complaint_id[:8])
            response = self.llm.invoke(formatted_prompt)
            
            if hasattr(response, 'content'):
                response = response.content
            
            # Parse JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if not json_match:
                raise ValueError(f"No JSON found in LLM response. Response: {response[:500]}")
            
            json_str = json_match.group()
            parsed = json.loads(json_str)
            
            action_type = parsed.get("action_type", "email")
            action_details = parsed.get("action_details", {})
            citizen_message = parsed.get("citizen_message", "")
            
            result = {
                "action_type": action_type,
                "action_details": action_details,
                "citizen_message": citizen_message,
                "reasoning": parsed.get("reasoning", ""),
                "priority": parsed.get("priority", "medium")
            }
            
            self.log_decision(result, {
                "complaint_id": complaint_id,
                "days_since_update": days_since_update,
                "method": "agentic_llm"
            })
            
            return result
        except Exception as e:
            logger.error("Error generating follow-up action", complaint_id=complaint.get("id"), error=str(e))
            # Fallback action
            return {
                "action_type": "email",
                "action_details": {
                    "recipient": department,
                    "subject": f"Follow-up on Complaint #{complaint.get('id', '')[:8]}",
                    "body": f"Please provide an update on complaint #{complaint.get('id', '')[:8]}"
                },
                "citizen_message": f"We've requested an update from {department}. You'll receive a response within 24 hours.",
                "reasoning": "Standard follow-up for stale complaint",
                "priority": "medium"
            }
    
    def process_followup(self, complaint: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a follow-up for a stale complaint.
        
        Args:
            complaint: Complaint record
        
        Returns:
            Dictionary with follow-up result
        """
        try:
            complaint_id = complaint.get("id")
            action = self.generate_followup_action(complaint)
            
            # Execute the action
            if action["action_type"] == "email":
                # Draft email to department (in real implementation, would send)
                logger.info("Drafting follow-up email", 
                          complaint_id=complaint_id,
                          department=action["action_details"].get("recipient"))
                # In production, this would send an email
                # For now, we'll just log it
            
            elif action["action_type"] == "api_call":
                # Call department API (if available)
                logger.info("Calling department API",
                          complaint_id=complaint_id,
                          api_url=action["action_details"].get("api_url"))
                # In production, this would make an API call
                # For now, we'll just log it
            
            # Update citizen with status
            citizen_email = complaint.get("citizen_email")
            citizen_name = complaint.get("citizen_name", "Citizen")
            
            if citizen_email and action.get("citizen_message"):
                from src.services.notification_service import notification_service
                
                notification_service.send_followup_notification(
                    complaint_id=complaint_id,
                    citizen_email=citizen_email,
                    citizen_name=citizen_name,
                    message=action["citizen_message"],
                    department=complaint.get("current_department", complaint.get("responsible_department", "Department"))
                )
            
            # Update complaint with follow-up timestamp (if fields exist in schema)
            # Note: These fields need to be added to the database schema
            try:
                db.update_complaint(
                    complaint_id,
                    {
                        "last_followup_at": datetime.utcnow().isoformat(),
                        "followup_count": (complaint.get("followup_count", 0) or 0) + 1
                    },
                    send_notification=False
                )
            except Exception as e:
                # If fields don't exist in schema, just log
                logger.warning("Could not update follow-up fields (may not exist in schema)", 
                             complaint_id=complaint_id, 
                             error=str(e))
            
            return {
                "success": True,
                "complaint_id": complaint_id,
                "action_taken": action["action_type"],
                "citizen_notified": bool(citizen_email),
                "message": action["citizen_message"]
            }
        except Exception as e:
            logger.error("Error processing follow-up", complaint_id=complaint.get("id"), error=str(e))
            return {
                "success": False,
                "complaint_id": complaint.get("id"),
                "error": str(e)
            }

"""
Escalation Agent.
Determines escalation level and authority using agentic LLM based on time overdue, severity, and past escalations.
"""
from typing import Dict, Any, List
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from src.agents.base import BaseAgent
from src.agents.prompts import AgentPrompts
from src.agents.llm_factory import create_llm
from src.models.database import db
from src.models.schemas import EscalationLevel
from src.config.india_data import INDIAN_DEPARTMENTS
import structlog
import json
import re

logger = structlog.get_logger()


class EscalationAgent(BaseAgent):
    """Agent that determines escalation levels and authorities."""
    
    def __init__(self):
        """Initialize the escalation agent."""
        super().__init__("EscalationAgent")
        try:
            self.llm = create_llm(temperature=0.3)  # Moderate temperature for escalation decisions
            logger.info("LLM initialized for escalation")
        except Exception as e:
            logger.error("Failed to initialize LLM - agentic system requires LLM", error=str(e))
            raise RuntimeError("EscalationAgent requires LLM to be configured") from e
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine escalation level and authority for a complaint.
        
        Args:
            input_data: Dictionary with 'complaint_id', 'hours_overdue', 'urgency', 'current_escalation_level'
        
        Returns:
            Dictionary with 'escalation_level', 'escalated_to', and 'reason'
        """
        complaint_id = input_data.get("complaint_id")
        hours_overdue = input_data.get("hours_overdue", 0)
        urgency = input_data.get("urgency", "medium")
        current_level = input_data.get("current_escalation_level", EscalationLevel.NONE.value)
        
        # Get complaint details
        complaint = db.get_complaint(complaint_id)
        if not complaint:
            return {"error": "Complaint not found"}
        
        department = complaint.get("responsible_department", "municipal")
        
        # Get past escalations
        past_escalations = db.get_escalations_for_complaint(complaint_id)
        
        # Use agentic LLM to determine escalation
        try:
            result = self._escalate_with_llm(
                complaint_id,
                hours_overdue,
                urgency,
                current_level,
                len(past_escalations),
                department,
                complaint
            )
            self.log_decision(result, {
                "complaint_id": complaint_id,
                "hours_overdue": hours_overdue,
                "urgency": urgency,
                "current_level": current_level,
                "method": "agentic_llm"
            })
            return result
        except Exception as e:
            logger.error("Agentic escalation failed", error=str(e))
            raise RuntimeError(f"Escalation agent failed: {str(e)}") from e
    
    def _escalate_with_llm(
        self,
        complaint_id: str,
        hours_overdue: float,
        urgency: str,
        current_level: str,
        past_escalation_count: int,
        department: str,
        complaint: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use agentic LLM to determine escalation decision.
        
        Args:
            complaint_id: Complaint identifier
            hours_overdue: Hours past SLA
            urgency: Urgency level
            current_level: Current escalation level
            past_escalation_count: Number of past escalations
            department: Department key
            complaint: Complaint data
        
        Returns:
            Escalation decision dictionary
        """
        complaint_details = json.dumps({
            "id": complaint_id,
            "category": complaint.get("structured_category", "other"),
            "description": complaint.get("description", "")[:200],  # Truncate for prompt
            "department": department,
        }, indent=2)
        
        prompt = ChatPromptTemplate.from_template(AgentPrompts.ESCALATION_DECISION_PROMPT.template)
        formatted_prompt = prompt.format_messages(
            complaint_details=complaint_details,
            hours_overdue=hours_overdue,
            urgency=urgency,
            past_escalations=str(past_escalation_count)
        )
        
        logger.info("Invoking agentic LLM for escalation decision", 
                  complaint_id=complaint_id, 
                  hours_overdue=hours_overdue)
        response = self.llm.invoke(formatted_prompt)
        
        # Extract content from AIMessage if needed
        if hasattr(response, 'content'):
            response = response.content
        
        # Parse JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if not json_match:
            raise ValueError(f"No JSON found in LLM response. Response: {response[:500]}")
        
        json_str = json_match.group()
        parsed = json.loads(json_str)
        
        escalation_needed = parsed.get("escalation_needed", False)
        escalation_level = parsed.get("escalation_level", EscalationLevel.NONE.value)
        
        if not escalation_needed or escalation_level == EscalationLevel.NONE.value or escalation_level == current_level:
            return {
                "escalation_needed": False,
                "current_level": current_level,
            }
        
        # Get authority name
        escalated_to = parsed.get("authority", self._get_escalation_authority(escalation_level, department))
        reason = parsed.get("reason", f"Complaint overdue by {hours_overdue:.1f} hours. Urgency: {urgency}.")
        
        result = {
            "escalation_needed": True,
            "escalation_level": escalation_level,
            "escalated_to": escalated_to,
            "reason": reason,
            "agent_metadata": {
                "priority_score": parsed.get("priority_score", 5),
            }
        }
        
        logger.info("Agentic escalation decision successful", 
                  escalation_level=escalation_level,
                  escalated_to=escalated_to)
        
        return result
    
    def _get_escalation_authority(self, level: str, department: str) -> str:
        """
        Get the authority name for an escalation level.
        
        Args:
            level: Escalation level
            department: Department key
        
        Returns:
            Authority name
        """
        dept_info = INDIAN_DEPARTMENTS.get(department, INDIAN_DEPARTMENTS["municipal"])
        
        authority_map = {
            EscalationLevel.LEVEL_1.value: f"{dept_info['name']} - Department Head",
            EscalationLevel.LEVEL_2.value: "State/City Commissioner",
            EscalationLevel.LEVEL_3.value: "Chief Secretary / Minister",
            EscalationLevel.LEVEL_4.value: "Chief Minister / Governor Office",
        }
        
        return authority_map.get(level, "Unknown Authority")
    


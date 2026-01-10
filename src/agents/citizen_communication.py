"""
Citizen Communication Agent.
Generates human-friendly updates for citizens.
May optionally use a small local LLM for tone refinement.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from src.agents.base import BaseAgent
from src.agents.prompts import AgentPrompts
from src.agents.llm_factory import create_llm
from src.models.schemas import ComplaintStatus, EscalationLevel
import structlog
import json
import re

logger = structlog.get_logger()


class CitizenCommunicationAgent(BaseAgent):
    """Agent that generates citizen-facing messages."""
    
    def __init__(self):
        """Initialize the citizen communication agent with agentic LLM."""
        super().__init__("CitizenCommunicationAgent")
        try:
            self.llm = create_llm(temperature=0.7)  # Slightly higher for more natural language
            logger.info("LLM initialized for citizen communication")
        except Exception as e:
            logger.error("Failed to initialize LLM - agentic system requires LLM", error=str(e))
            raise RuntimeError("CitizenCommunicationAgent requires LLM to be configured") from e
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a citizen-friendly status update message using agentic LLM.
        
        Args:
            input_data: Dictionary with 'status', 'complaint_id', 'department', 'escalation_level', etc.
        
        Returns:
            Dictionary with 'message' and 'subject'
        """
        status = input_data.get("status", ComplaintStatus.OPEN.value)
        complaint_id = input_data.get("complaint_id", "")
        department = input_data.get("department", "concerned department")
        escalation_level = input_data.get("escalation_level", EscalationLevel.NONE.value)
        time_remaining = input_data.get("time_remaining_hours")
        is_breaching = input_data.get("is_breaching_sla", False)
        policy_reference = input_data.get("policy_reference")
        policy_violation = input_data.get("policy_violation", False)
        suggested_action = input_data.get("suggested_action")
        
        # Always use agentic LLM for message generation
        try:
            result = self._generate_with_llm(
                complaint_id, status, department, escalation_level, time_remaining, is_breaching,
                policy_reference, policy_violation, suggested_action
            )
            if result:
                self.log_decision(result, {"status": status, "complaint_id": complaint_id, "method": "agentic_llm"})
                return result
            else:
                raise ValueError("LLM returned empty result")
        except Exception as e:
            logger.error("Agentic message generation failed", error=str(e))
            raise RuntimeError(f"Citizen communication agent failed: {str(e)}") from e
    
    def _generate_with_llm(
        self,
        complaint_id: str,
        status: str,
        department: str,
        escalation_level: str,
        time_remaining: Optional[float],
        is_breaching: bool,
        policy_reference: Optional[str] = None,
        policy_violation: bool = False,
        suggested_action: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate message using agentic LLM with prompts.
        
        Args:
            complaint_id: Complaint identifier
            status: Current status
            department: Department name
            escalation_level: Escalation level
            time_remaining: Hours remaining until SLA
            is_breaching: Whether SLA is breached
            policy_reference: Policy/Act/GR reference
            policy_violation: Whether policy is violated
            suggested_action: Suggested action based on policy
        
        Returns:
            Generated message dictionary
        """
        prompt = ChatPromptTemplate.from_template(AgentPrompts.CITIZEN_NOTIFICATION_PROMPT.template)
        formatted_prompt = prompt.format_messages(
            complaint_id=complaint_id[:8] if complaint_id else "N/A",
            status=status,
            department=department,
            escalation_level=escalation_level,
            time_remaining=round(time_remaining, 1) if time_remaining else "N/A",
            is_breaching=str(is_breaching).lower(),
            policy_reference=policy_reference or "N/A",
            policy_violation=str(policy_violation).lower(),
            suggested_action=suggested_action or "N/A"
        )
        
        logger.info("Invoking agentic LLM for citizen communication", complaint_id=complaint_id, status=status)
        response = self.llm.invoke(formatted_prompt)
        
        # Extract content from AIMessage if needed
        if hasattr(response, 'content'):
            response = response.content
        
        # Parse JSON from response - find the first complete JSON object
        # Try to find JSON object, handling cases with extra text before/after
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response)
        if not json_match:
            # Fallback: try to find any JSON-like structure
            json_match = re.search(r'\{.*?\}', response, re.DOTALL)
        
        if not json_match:
            raise ValueError(f"No JSON found in LLM response. Response: {response[:500]}")
        
        json_str = json_match.group()
        
        # Try to parse, with better error handling
        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError as e:
            # Try to extract just the JSON part more carefully
            # Find the first { and last } that form a valid JSON
            start_idx = response.find('{')
            if start_idx == -1:
                raise ValueError(f"No JSON object found in response: {response[:500]}")
            
            # Find matching closing brace
            brace_count = 0
            end_idx = start_idx
            for i in range(start_idx, len(response)):
                if response[i] == '{':
                    brace_count += 1
                elif response[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i
                        break
            
            if brace_count != 0:
                raise ValueError(f"Incomplete JSON in response: {response[:500]}")
            
            json_str = response[start_idx:end_idx + 1]
            parsed = json.loads(json_str)
        
        message = parsed.get("message", "")
        if not message:
            raise ValueError("LLM returned empty message")
        
        result = {
            "message": message,
            "subject": parsed.get("subject", f"Update on Your Complaint #{complaint_id[:8] if complaint_id else 'N/A'}"),
            "language": parsed.get("language", "en"),
            "tone": parsed.get("tone", "professional"),
        }
        
        logger.info("Agentic message generation successful", message_length=len(message))
        return result
    
    def _generate_open_message(self, complaint_id: str, department: str, time_remaining: float = None) -> str:
        """Generate message for open status."""
        base = f"Your complaint #{complaint_id[:8]} has been received and assigned to {department}."
        if time_remaining:
            days = int(time_remaining / 24)
            if days > 0:
                base += f" Expected resolution time: {days} days."
            else:
                hours = int(time_remaining)
                base += f" Expected resolution time: {hours} hours."
        base += " We will keep you updated on the progress."
        return base
    
    def _generate_in_progress_message(
        self,
        complaint_id: str,
        department: str,
        time_remaining: float = None,
        is_breaching: bool = False
    ) -> str:
        """Generate message for in-progress status."""
        base = f"Your complaint #{complaint_id[:8]} is being actively worked on by {department}."
        if is_breaching:
            base += " We apologize for the delay and are prioritizing your case."
        elif time_remaining:
            days = int(time_remaining / 24)
            if days > 0:
                base += f" Expected completion: {days} days."
        base += " Thank you for your patience."
        return base
    
    def _generate_escalated_message(self, complaint_id: str, department: str, escalation_level: str) -> str:
        """Generate message for escalated status."""
        level_names = {
            EscalationLevel.LEVEL_1.value: "department head",
            EscalationLevel.LEVEL_2.value: "commissioner's office",
            EscalationLevel.LEVEL_3.value: "chief secretary's office",
            EscalationLevel.LEVEL_4.value: "chief minister's office",
        }
        authority = level_names.get(escalation_level, "higher authority")
        
        return (
            f"Your complaint #{complaint_id[:8]} has been escalated to the {authority} "
            f"for immediate attention. We are committed to resolving your issue promptly."
        )
    
    def _generate_resolved_message(self, complaint_id: str, department: str) -> str:
        """Generate message for resolved status."""
        return (
            f"Great news! Your complaint #{complaint_id[:8]} has been resolved by {department}. "
            f"Thank you for bringing this to our attention. If you have any feedback, please let us know."
        )
    
    def _generate_default_message(self, complaint_id: str, department: str, status: str) -> str:
        """Generate default message for other statuses."""
        return (
            f"Update on your complaint #{complaint_id[:8]}: "
            f"Current status is {status}. Assigned to {department}."
        )


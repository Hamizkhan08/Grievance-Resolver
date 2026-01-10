"""
Policy Intelligence Agent.
Maps complaints to government rules, GRs, and regulations.
Provides policy-aware SLA and legal compliance information.
"""
from typing import Dict, Any
from src.agents.base import BaseAgent
from src.agents.llm_factory import create_llm
from src.agents.prompts import AgentPrompts
from src.agents.utils import extract_json_from_string
import structlog

logger = structlog.get_logger()


class PolicyIntelligenceAgent(BaseAgent):
    """Agent that maps complaints to government policies and regulations."""
    
    def __init__(self):
        """Initialize the Policy Intelligence Agent."""
        super().__init__("PolicyIntelligenceAgent")
        self.llm = create_llm(temperature=0.2)
        logger.info("Policy Intelligence Agent initialized")
    
    def process(
        self,
        description: str,
        category: str,
        department: str,
        urgency: str,
        location: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Map complaint to relevant government policies and regulations.
        
        Args:
            description: Complaint description
            category: Issue category
            department: Assigned department
            urgency: Urgency level
            location: Location information
        
        Returns:
            Policy intelligence data including:
            - applicable_policies: List of relevant policies/GRs
            - legal_sla: Legal SLA from policy
            - policy_violation: Whether department is violating policy
            - suggested_action: Lawful action based on policy
            - policy_reference: Specific act/section/GR reference
            - escalation_strategy: Detailed escalation strategy with steps, hierarchy, and templates
        """
        try:
            # Format location context
            location_context = self._format_location(location)
            
            # Get policy mapping from LLM
            policy_data = self._map_to_policy(
                description=description,
                category=category,
                department=department,
                urgency=urgency,
                location_context=location_context
            )
            
            self.log_decision(
                decision=policy_data,
                context={
                    "description_length": len(description),
                    "category": category,
                    "department": department,
                    "method": "agentic_llm"
                }
            )
            
            return policy_data
        
        except Exception as e:
            logger.error("Error in policy intelligence", error=str(e))
            # Return default policy data on error
            return {
                "applicable_policies": [],
                "legal_sla": None,
                "policy_violation": False,
                "suggested_action": "Standard complaint processing",
                "policy_reference": None,
                "reasoning": f"Error processing policy mapping: {str(e)}"
            }
    
    def _format_location(self, location: Dict[str, Any]) -> str:
        """Format location for context."""
        parts = []
        if location.get("state"):
            parts.append(f"State: {location['state']}")
        if location.get("city"):
            parts.append(f"City: {location['city']}")
        if location.get("district"):
            parts.append(f"District: {location['district']}")
        if location.get("pincode"):
            parts.append(f"PIN: {location['pincode']}")
        return ", ".join(parts) if parts else "Location not specified"
    
    def _map_to_policy(
        self,
        description: str,
        category: str,
        department: str,
        urgency: str,
        location_context: str
    ) -> Dict[str, Any]:
        """Use LLM to map complaint to government policies."""
        prompt = AgentPrompts.POLICY_INTELLIGENCE_PROMPT.format(
            description=description,
            category=category,
            department=department,
            urgency=urgency,
            location_context=location_context
        )
        
        response = self.llm.invoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Extract JSON from response
        policy_data = extract_json_from_string(response_text)
        
        # Validate required fields
        if not isinstance(policy_data, dict):
            raise ValueError("Invalid policy data format")
        
        # Ensure all required fields exist
        policy_data.setdefault("applicable_policies", [])
        policy_data.setdefault("legal_sla", None)
        policy_data.setdefault("policy_violation", False)
        policy_data.setdefault("suggested_action", "Standard complaint processing")
        policy_data.setdefault("policy_reference", None)
        policy_data.setdefault("escalation_strategy", None)
        policy_data.setdefault("escalation_authority", None)
        policy_data.setdefault("reasoning", "Policy mapping completed")
        
        logger.info(
            "Policy mapping successful",
            policies_count=len(policy_data.get("applicable_policies", [])),
            has_legal_sla=policy_data.get("legal_sla") is not None,
            violation_detected=policy_data.get("policy_violation", False)
        )
        
        return policy_data

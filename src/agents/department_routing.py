"""
Department Routing Agent.
Determines the responsible authority using agentic LLM prompts.
All routing decisions made by LLM.
"""
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from src.agents.base import BaseAgent
from src.agents.prompts import AgentPrompts
from src.agents.llm_factory import create_llm
from src.config.india_data import INDIAN_DEPARTMENTS
import structlog
import json
import re

logger = structlog.get_logger()


class DepartmentRoutingAgent(BaseAgent):
    """Agent that routes complaints to appropriate departments using agentic LLM."""
    
    def __init__(self):
        """Initialize the department routing agent."""
        super().__init__("DepartmentRoutingAgent")
        try:
            self.llm = create_llm(temperature=0.2)  # Lower temperature for consistent routing decisions
            logger.info("LLM initialized for department routing")
        except Exception as e:
            logger.error("Failed to initialize LLM - agentic system requires LLM", error=str(e))
            raise RuntimeError("DepartmentRoutingAgent requires LLM to be configured") from e
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine the responsible department for a complaint using agentic LLM.
        
        Args:
            input_data: Dictionary with 'category', 'location', and 'description'
        
        Returns:
            Dictionary with 'department' and 'department_name'
        """
        category = input_data.get("category", "other")
        location = input_data.get("location", {})
        description = input_data.get("description", "")
        
        # Use agentic LLM for routing decision
        try:
            result = self._route_with_llm(category, description, location)
            self.log_decision(result, {
                "category": category,
                "location": location,
                "method": "agentic_llm"
            })
            return result
        except Exception as e:
            logger.error("Agentic routing failed", error=str(e))
            raise RuntimeError(f"Department routing agent failed: {str(e)}") from e
    
    def _route_with_llm(self, category: str, description: str, location: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use agentic LLM to determine the appropriate department.
        
        Args:
            category: Issue category
            description: Complaint description
            location: Location information
        
        Returns:
            Dictionary with department information
        """
        # Build available departments context
        departments_context = json.dumps(INDIAN_DEPARTMENTS, indent=2)
        location_context = json.dumps(location, indent=2) if location else "No location provided"
        
        prompt = ChatPromptTemplate.from_template(AgentPrompts.DEPARTMENT_ROUTING_REFINEMENT_PROMPT.template)
        formatted_prompt = prompt.format_messages(
            category=category,
            description=description,
            location=location_context,
            suggested_department="municipal"  # Initial suggestion, LLM will refine
        )
        
        logger.info("Invoking agentic LLM for department routing", category=category)
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
        
        department_key = parsed.get("department", "municipal")
        department_name = parsed.get("department_name", "")
        jurisdiction = parsed.get("jurisdiction", "city")
        
        # Validate department exists
        if department_key not in INDIAN_DEPARTMENTS:
            logger.warning(f"Invalid department from LLM: {department_key}, using municipal")
            department_key = "municipal"
            department_info = INDIAN_DEPARTMENTS["municipal"]
        else:
            department_info = INDIAN_DEPARTMENTS[department_key]
        
        # Use LLM's department_name if provided, otherwise use from config
        if not department_name:
            department_name = department_info["name"]
        
        result = {
            "department": department_key,
            "department_name": department_name,
            "jurisdiction": jurisdiction,
            "agent_metadata": {
                "confidence": parsed.get("confidence", 0.0),
                "reasoning": parsed.get("reasoning", ""),
            }
        }
        
        logger.info("Agentic routing successful", 
                  department=department_key, 
                  jurisdiction=jurisdiction,
                  confidence=result["agent_metadata"]["confidence"])
        
        return result


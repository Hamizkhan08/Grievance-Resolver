"""
Complaint Understanding Agent.
Extracts structured information from free-text complaints using Ollama LLM.
"""
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from src.agents.base import BaseAgent
from src.agents.prompts import AgentPrompts
from src.agents.llm_factory import create_llm
import structlog
import re
import json

logger = structlog.get_logger()


class ComplaintUnderstandingAgent(BaseAgent):
    """Agent that understands and structures complaint text."""
    
    def __init__(self):
        """Initialize the complaint understanding agent."""
        super().__init__("ComplaintUnderstandingAgent")
        try:
            self.llm = create_llm(temperature=0.3)  # Lower temperature for more consistent extraction
            logger.info("LLM initialized for complaint understanding")
        except Exception as e:
            logger.error("Failed to initialize LLM - agentic system requires LLM", error=str(e))
            raise RuntimeError("ComplaintUnderstandingAgent requires LLM to be configured") from e
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured information from complaint description using agentic LLM.
        
        Args:
            input_data: Dictionary with 'description' and optional 'location'
        
        Returns:
            Dictionary with structured_category, urgency, and extracted_location
        """
        description = input_data.get("description", "")
        provided_location = input_data.get("location", {})
        
        if not description:
            raise ValueError("Complaint description is required")
        
        # Use LLM for agentic understanding
        try:
            result = self._understand_with_llm(description, provided_location)
            
            self.log_decision(result, {
                "description_length": len(description),
                "method": "agentic_llm"
            })
            return result
        except Exception as e:
            logger.error("Agentic understanding failed", error=str(e))
            raise RuntimeError(f"Complaint understanding agent failed: {str(e)}") from e
    
    def _understand_with_llm(
        self,
        description: str,
        provided_location: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use agentic LLM to understand and extract structured information from complaint.
        
        Args:
            description: Complaint description
            provided_location: Location data from input
        
        Returns:
            Dictionary with structured_category, urgency, and extracted_location
        """
        # Use the structured prompt from prompts.py
        location_context = json.dumps(provided_location, indent=2) if provided_location else "No location provided"
        
        # Convert PromptTemplate to ChatPromptTemplate for chat models
        prompt = ChatPromptTemplate.from_template(AgentPrompts.COMPLAINT_UNDERSTANDING_PROMPT.template)
        formatted_prompt = prompt.format_messages(
            description=description,
            location_context=location_context
        )
        
        logger.info("Invoking agentic LLM for complaint understanding", description_length=len(description))
        response = self.llm.invoke(formatted_prompt)
        
        # Extract content from AIMessage if needed
        if hasattr(response, 'content'):
            response = response.content
        
        # Parse JSON from response
        # Try to extract JSON block (handle markdown code blocks)
        json_match = re.search(r'\{[\s\S]*\}', response)
        if not json_match:
            raise ValueError(f"No JSON found in LLM response. Response: {response[:500]}")
        
        json_str = json_match.group()
        parsed = json.loads(json_str)
        
        # Merge provided location with extracted location
        extracted_location = provided_location.copy() if provided_location else {}
        if parsed.get("location"):
            extracted_location.update(parsed["location"])
        
        # Ensure country is set
        extracted_location["country"] = extracted_location.get("country", "India")
        
        # Validate category
        valid_categories = ["infrastructure", "utilities", "sanitation", "transport", 
                          "health", "education", "safety", "environment", "governance", "other"]
        category = parsed.get("category", "other")
        if category not in valid_categories:
            logger.warning(f"Invalid category from LLM: {category}, defaulting to 'other'")
            category = "other"
        
        # Validate urgency
        valid_urgencies = ["urgent", "high", "medium", "low"]
        urgency = parsed.get("urgency", "medium")
        if urgency not in valid_urgencies:
            logger.warning(f"Invalid urgency from LLM: {urgency}, defaulting to 'medium'")
            urgency = "medium"
        
        result = {
            "structured_category": category,
            "urgency": urgency,
            "extracted_location": extracted_location,
            "agent_metadata": {
                "reasoning": parsed.get("reasoning", ""),
                "key_details": parsed.get("key_details", {}),
            }
        }
        
        logger.info("Agentic understanding successful", 
                  category=category, 
                  urgency=urgency,
                  has_location=bool(extracted_location.get("state") or extracted_location.get("city")))
        
        return result


"""
SLA Assignment Agent.
Assigns resolution deadlines using agentic LLM based on issue type, urgency, and policy.
All decisions made by LLM.
"""
from typing import Dict, Any
from datetime import datetime, timedelta
from langchain_core.prompts import ChatPromptTemplate
from src.agents.base import BaseAgent
from src.agents.prompts import AgentPrompts
from src.agents.llm_factory import create_llm
import structlog
import json
import re

logger = structlog.get_logger()


class SLAAssignmentAgent(BaseAgent):
    """Agent that assigns SLA deadlines using agentic LLM."""
    
    def __init__(self):
        """Initialize the SLA assignment agent."""
        super().__init__("SLAAssignmentAgent")
        try:
            self.llm = create_llm(temperature=0.2)  # Lower temperature for consistent SLA decisions
            logger.info("LLM initialized for SLA assignment")
        except Exception as e:
            logger.error("Failed to initialize LLM - agentic system requires LLM", error=str(e))
            raise RuntimeError("SLAAssignmentAgent requires LLM to be configured") from e
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assign SLA deadline using agentic LLM based on urgency and category.
        
        Args:
            input_data: Dictionary with 'urgency', 'category', 'description', 'location'
        
        Returns:
            Dictionary with 'sla_deadline' (ISO format string) and 'sla_hours'
        """
        urgency = input_data.get("urgency", "medium")
        category = input_data.get("category", "other")
        description = input_data.get("description", "")
        location = input_data.get("location", {})
        department = input_data.get("department", "")
        
        try:
            result = self._assign_sla_with_llm(urgency, category, description, location, department)
            self.log_decision(result, {
                "urgency": urgency,
                "category": category,
                "method": "agentic_llm"
            })
            return result
        except Exception as e:
            logger.error("Agentic SLA assignment failed", error=str(e))
            raise RuntimeError(f"SLA assignment agent failed: {str(e)}") from e
    
    def _assign_sla_with_llm(
        self,
        urgency: str,
        category: str,
        description: str,
        location: Dict[str, Any],
        department: str = ""
    ) -> Dict[str, Any]:
        """
        Use agentic LLM to assign SLA deadline.
        
        Args:
            urgency: Urgency level
            category: Issue category
            description: Complaint description
            location: Location information
            department: Assigned department
        
        Returns:
            Dictionary with SLA information
        """
        location_str = json.dumps(location, indent=2) if location else "No location provided"
        
        prompt = ChatPromptTemplate.from_template(AgentPrompts.SLA_ASSIGNMENT_PROMPT.template)
        formatted_prompt = prompt.format_messages(
            urgency=urgency,
            category=category,
            description=description,
            location=location_str,
            department=department
        )
        
        logger.info("Invoking agentic LLM for SLA assignment", urgency=urgency, category=category, department=department)
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
        
        # Allow decimal hours for minutes (e.g., 0.5 = 30 minutes)
        # Use urgency-based defaults instead of fixed 168 hours
        default_sla = {
            "urgent": 0.5,  # 30 minutes default for urgent
            "high": 6.0,    # 6 hours default for high
            "medium": 72.0, # 3 days default for medium
            "low": 168.0    # 7 days default for low
        }
        default_hours = default_sla.get(urgency, 72.0)
        
        sla_hours_raw = parsed.get("sla_hours", default_hours)
        sla_hours = float(sla_hours_raw)  # Convert to float to support decimals
        
        # CRITICAL: Validate and force realistic SLA times for ALL emergencies and departments
        description_lower = description.lower()
        
        # ============================================
        # URGENT EMERGENCIES (All Departments)
        # ============================================
        if urgency == "urgent":
            # Fire emergencies: 15-30 minutes (0.25-0.5 hours)
            fire_keywords = ["fire", "burning", "blaze", "smoke", "flames", "on fire", "caught fire"]
            if any(keyword in description_lower for keyword in fire_keywords) or department == "fire":
                if sla_hours > 0.5:
                    logger.warning(f"🔥 Fire emergency: SLA was {sla_hours}h, forcing 0.5h (30 min)")
                    sla_hours = 0.5
                elif sla_hours < 0.25:
                    sla_hours = 0.25
            
            # Medical emergencies: 15-30 minutes
            medical_keywords = ["medical emergency", "heart attack", "stroke", "unconscious", "not breathing", "ambulance"]
            if any(keyword in description_lower for keyword in medical_keywords) or department == "maharashtra_health":
                if sla_hours > 0.5:
                    logger.warning(f"🚨 Medical emergency: SLA was {sla_hours}h, forcing 0.5h (30 min)")
                    sla_hours = 0.5
                elif sla_hours < 0.25:
                    sla_hours = 0.25
            
            # Accidents: 30-60 minutes
            accident_keywords = ["accident", "crash", "collision", "injured", "hurt", "bleeding", "trapped"]
            if any(keyword in description_lower for keyword in accident_keywords):
                if department in ["maharashtra_police", "mumbai_police"]:
                    if sla_hours > 1.0:
                        logger.warning(f"🚗 Accident: SLA was {sla_hours}h, forcing 1.0h (60 min)")
                        sla_hours = 1.0
                    elif sla_hours < 0.5:
                        sla_hours = 0.5
            
            # Gas leaks: 15-30 minutes
            gas_keywords = ["gas leak", "gas smell", "lpg leak", "explosion risk", "gas emergency"]
            if any(keyword in description_lower for keyword in gas_keywords):
                if sla_hours > 0.5:
                    logger.warning(f"💨 Gas leak: SLA was {sla_hours}h, forcing 0.5h (30 min)")
                    sla_hours = 0.5
                elif sla_hours < 0.25:
                    sla_hours = 0.25
            
            # Structural collapse: 30-60 minutes
            collapse_keywords = ["building collapse", "wall collapse", "structure falling", "unsafe building", "trapped"]
            if any(keyword in description_lower for keyword in collapse_keywords):
                if sla_hours > 1.0:
                    logger.warning(f"🏢 Structural danger: SLA was {sla_hours}h, forcing 1.0h (60 min)")
                    sla_hours = 1.0
                elif sla_hours < 0.5:
                    sla_hours = 0.5
            
            # Crime in progress: 15-30 minutes
            crime_keywords = ["robbery", "assault", "attack", "violence", "threat", "danger", "crime in progress"]
            if any(keyword in description_lower for keyword in crime_keywords):
                if department in ["maharashtra_police", "mumbai_police"]:
                    if sla_hours > 0.5:
                        logger.warning(f"🚔 Crime in progress: SLA was {sla_hours}h, forcing 0.5h (30 min)")
                        sla_hours = 0.5
                    elif sla_hours < 0.25:
                        sla_hours = 0.25
            
            # Electrical dangers: 15-30 minutes
            electrical_keywords = ["electrical fire", "power line down", "sparking wires", "live wire", "electrical hazard"]
            if any(keyword in description_lower for keyword in electrical_keywords):
                if department in ["fire", "mseb"]:
                    if sla_hours > 0.5:
                        logger.warning(f"⚡ Electrical danger: SLA was {sla_hours}h, forcing 0.5h (30 min)")
                        sla_hours = 0.5
                    elif sla_hours < 0.25:
                        sla_hours = 0.25
            
            # General urgent cap: Maximum 2 hours for any urgent complaint
            if sla_hours > 2.0:
                logger.warning(f"⚠️ Urgent complaint: SLA was {sla_hours}h, capping at 2.0h")
                sla_hours = 2.0
        
        # ============================================
        # HIGH PRIORITY (All Departments)
        # ============================================
        elif urgency == "high":
            # Health risks, contamination: 2-6 hours
            health_risk_keywords = ["contamination", "disease outbreak", "unsafe water", "food poisoning", "health risk"]
            if any(keyword in description_lower for keyword in health_risk_keywords):
                if sla_hours > 6.0:
                    logger.warning(f"🏥 Health risk: SLA was {sla_hours}h, forcing 6.0h max")
                    sla_hours = 6.0
                elif sla_hours < 2.0:
                    sla_hours = 2.0
            
            # Major infrastructure failure: 4-12 hours
            infrastructure_keywords = ["bridge collapse", "major road damage", "building structural", "infrastructure failure"]
            if any(keyword in description_lower for keyword in infrastructure_keywords):
                if department in ["maharashtra_pwd", "bmc", "pune_municipal", "municipal"]:
                    if sla_hours > 12.0:
                        logger.warning(f"🏗️ Infrastructure failure: SLA was {sla_hours}h, forcing 12.0h max")
                        sla_hours = 12.0
                    elif sla_hours < 4.0:
                        sla_hours = 4.0
            
            # Power outage (large area): 2-8 hours
            if "power outage" in description_lower or "power cut" in description_lower:
                if department == "mseb":
                    if sla_hours > 8.0:
                        logger.warning(f"⚡ Power outage: SLA was {sla_hours}h, forcing 8.0h max")
                        sla_hours = 8.0
                    elif sla_hours < 2.0:
                        sla_hours = 2.0
            
            # Water contamination: 2-6 hours
            if "water contamination" in description_lower or "contaminated water" in description_lower:
                if department in ["bmc", "pune_municipal", "municipal"]:
                    if sla_hours > 6.0:
                        logger.warning(f"💧 Water contamination: SLA was {sla_hours}h, forcing 6.0h max")
                        sla_hours = 6.0
                    elif sla_hours < 2.0:
                        sla_hours = 2.0
            
            # General high priority cap: Maximum 12 hours
            if sla_hours > 12.0:
                logger.warning(f"⚠️ High priority: SLA was {sla_hours}h, capping at 12.0h")
                sla_hours = 12.0
        
        # ============================================
        # MEDIUM PRIORITY (All Departments)
        # ============================================
        elif urgency == "medium":
            # Garbage collection: 1-3 days (24-72 hours)
            if "garbage" in description_lower or "waste" in description_lower:
                if department in ["bmc", "pune_municipal", "municipal"]:
                    if sla_hours > 72.0:
                        logger.warning(f"🗑️ Garbage issue: SLA was {sla_hours}h, forcing 72.0h max (3 days)")
                        sla_hours = 72.0
                    elif sla_hours < 24.0:
                        sla_hours = 24.0
            
            # Road repairs: 2-5 days (48-120 hours)
            if "road" in description_lower or "pothole" in description_lower:
                if department in ["bmc", "pune_municipal", "maharashtra_pwd", "municipal"]:
                    if sla_hours > 120.0:
                        logger.warning(f"🛣️ Road repair: SLA was {sla_hours}h, forcing 120.0h max (5 days)")
                        sla_hours = 120.0
                    elif sla_hours < 48.0:
                        sla_hours = 48.0
            
            # Water supply issues: 1-3 days (24-72 hours)
            if "water" in description_lower and "supply" in description_lower:
                if department in ["bmc", "pune_municipal", "municipal"]:
                    if sla_hours > 72.0:
                        logger.warning(f"💧 Water supply: SLA was {sla_hours}h, forcing 72.0h max (3 days)")
                        sla_hours = 72.0
                    elif sla_hours < 24.0:
                        sla_hours = 24.0
            
            # Electricity issues: 1-3 days (24-72 hours)
            if "electricity" in description_lower or "power" in description_lower:
                if department == "mseb":
                    if sla_hours > 72.0:
                        logger.warning(f"⚡ Electricity issue: SLA was {sla_hours}h, forcing 72.0h max (3 days)")
                        sla_hours = 72.0
                    elif sla_hours < 24.0:
                        sla_hours = 24.0
            
            # Drainage issues: 2-4 days (48-96 hours)
            if "drainage" in description_lower or "drain" in description_lower:
                if department in ["bmc", "pune_municipal", "municipal"]:
                    if sla_hours > 96.0:
                        logger.warning(f"🌊 Drainage issue: SLA was {sla_hours}h, forcing 96.0h max (4 days)")
                        sla_hours = 96.0
                    elif sla_hours < 48.0:
                        sla_hours = 48.0
            
            # Street lights: 2-5 days (48-120 hours)
            if "street light" in description_lower or "light" in description_lower:
                if department in ["bmc", "pune_municipal", "municipal"]:
                    if sla_hours > 120.0:
                        logger.warning(f"💡 Street light: SLA was {sla_hours}h, forcing 120.0h max (5 days)")
                        sla_hours = 120.0
                    elif sla_hours < 48.0:
                        sla_hours = 48.0
            
            # General medium priority: 1-7 days (24-168 hours)
            if sla_hours > 168.0:
                logger.warning(f"⚠️ Medium priority: SLA was {sla_hours}h, capping at 168.0h (7 days)")
                sla_hours = 168.0
            elif sla_hours < 24.0:
                sla_hours = 24.0
        
        # ============================================
        # LOW PRIORITY (All Departments)
        # ============================================
        elif urgency == "low":
            # Cosmetic issues: 7-14 days (168-336 hours)
            cosmetic_keywords = ["paint", "aesthetic", "cosmetic", "minor repair"]
            if any(keyword in description_lower for keyword in cosmetic_keywords):
                if sla_hours > 336.0:
                    logger.warning(f"🎨 Cosmetic issue: SLA was {sla_hours}h, forcing 336.0h max (14 days)")
                    sla_hours = 336.0
                elif sla_hours < 168.0:
                    sla_hours = 168.0
            
            # General low priority: 7-14 days (168-336 hours)
            if sla_hours > 336.0:
                logger.warning(f"⚠️ Low priority: SLA was {sla_hours}h, capping at 336.0h (14 days)")
                sla_hours = 336.0
            elif sla_hours < 168.0:
                sla_hours = 168.0
        
        # ============================================
        # FINAL VALIDATION
        # ============================================
        # Enforce absolute minimums and maximums
        if sla_hours < 0.25:  # Minimum 15 minutes
            sla_hours = 0.25
        if sla_hours > 336:  # Maximum 14 days
            sla_hours = 336
        
        # Calculate deadline
        now = datetime.utcnow()
        deadline = now + timedelta(hours=sla_hours)
        
        result = {
            "sla_deadline": deadline.isoformat(),
            "sla_hours": sla_hours,
            "agent_metadata": {
                "reasoning": parsed.get("reasoning", ""),
                "complexity_factor": parsed.get("complexity_factor", 1.0),
                "priority_score": parsed.get("priority_score", 5),
            }
        }
        
        logger.info("Agentic SLA assignment successful", 
                  sla_hours=sla_hours, 
                  deadline=deadline.isoformat())
        
        return result


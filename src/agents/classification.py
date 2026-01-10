"""
Classification Agent.
Unified agent that classifies both urgency and department routing together.
Ensures emergency situations (like fires) are properly classified and routed.
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


class ClassificationAgent(BaseAgent):
    """Unified agent that classifies urgency and routes to appropriate department."""
    
    def __init__(self):
        """Initialize the classification agent."""
        super().__init__("ClassificationAgent")
        try:
            self.llm = create_llm(temperature=0.2)  # Lower temperature for consistent classification
            logger.info("LLM initialized for classification")
        except Exception as e:
            logger.error("Failed to initialize LLM - agentic system requires LLM", error=str(e))
            raise RuntimeError("ClassificationAgent requires LLM to be configured") from e
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify complaint urgency and route to appropriate department using agentic LLM.
        
        Args:
            input_data: Dictionary with 'description' and optional 'location'
        
        Returns:
            Dictionary with urgency, category, department, and department_name
        """
        description = input_data.get("description", "")
        provided_location = input_data.get("location", {})
        
        if not description:
            raise ValueError("Complaint description is required")
        
        # Use LLM for unified classification
        try:
            result = self._classify_with_llm(description, provided_location)
            
            self.log_decision(result, {
                "description_length": len(description),
                "method": "agentic_llm_unified"
            })
            return result
        except Exception as e:
            logger.error("Agentic classification failed", error=str(e))
            raise RuntimeError(f"Classification agent failed: {str(e)}") from e
    
    def _classify_with_llm(
        self,
        description: str,
        provided_location: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use agentic LLM to classify urgency and route to department in one step.
        
        Args:
            description: Complaint description
            provided_location: Location data from input
        
        Returns:
            Dictionary with urgency, category, department, and department_name
        """
        description_lower = description.lower()
        
        # ============================================
        # KEYWORD-BASED ROUTING FIRST (BEFORE LLM)
        # This ensures correct routing even if LLM fails
        # ============================================
        department_key = None
        urgency = None
        category = None
        
        # EMERGENCIES (URGENT) - Check first
        fire_keywords = ["fire", "burning", "blaze", "smoke", "flames", "on fire", "caught fire", "fire broke out", "fire incident", "building on fire", "house on fire"]
        medical_keywords = ["medical emergency", "heart attack", "stroke", "unconscious", "not breathing", "ambulance needed", "ambulance", "emergency medical"]
        accident_keywords = ["accident", "crash", "collision", "injured", "hurt", "bleeding", "trapped", "road accident", "car accident"]
        gas_keywords = ["gas leak", "gas smell", "lpg leak", "explosion risk", "gas emergency", "gas", "lpg", "cng leak"]
        # Expanded police keywords - more comprehensive and context-aware
        police_keywords = [
            # Direct police references
            "police", "cop", "constable", "officer", "law enforcement", "police station", "police help", 
            "police complaint", "file fir", "fir", "first information report", "police intervention",
            "police action", "police report", "police case", "police investigation", "police department",
            # Crime-related
            "robbery", "assault", "attack", "violence", "threat", "crime", "theft", "fraud", "stolen", 
            "robbed", "mugging", "burglary", "break-in", "vandalism", "harassment", "molestation",
            "domestic violence", "abuse", "cybercrime", "scam", "cheating", "illegal", "criminal",
            "criminal activity", "law violation", "illegal activity",
            # Security and safety
            "security issue", "safety concern", "unsafe", "dangerous situation", "threatening",
            "intimidation", "extortion", "blackmail", "kidnapping", "missing person",
            # Traffic violations
            "traffic violation", "rash driving", "drunk driving", "hit and run", "traffic police",
            # Legal/law enforcement
            "legal action", "law and order", "public order", "disturbance", "riot", "commotion"
        ]
        
        if any(keyword in description_lower for keyword in fire_keywords):
            department_key = "fire"
            urgency = "urgent"
            category = "safety"
            logger.warning(f"🔥 FIRE detected - forcing fire department")
        elif any(keyword in description_lower for keyword in medical_keywords):
            department_key = "maharashtra_health"
            urgency = "urgent"
            category = "health"
            logger.warning(f"🚨 MEDICAL EMERGENCY detected - forcing health department")
        elif any(keyword in description_lower for keyword in accident_keywords):
            city = provided_location.get("city", "").lower() if provided_location else ""
            if "mumbai" in city:
                department_key = "mumbai_police"
            else:
                department_key = "maharashtra_police"
            urgency = "urgent"
            category = "safety"
            logger.warning(f"🚗 ACCIDENT detected - forcing police department")
        elif any(keyword in description_lower for keyword in gas_keywords):
            department_key = "fire"
            urgency = "urgent"
            category = "safety"
            logger.warning(f"💨 GAS LEAK detected - forcing fire department")
        elif any(keyword in description_lower for keyword in police_keywords):
            city = provided_location.get("city", "").lower() if provided_location else ""
            # Also check description for city names
            if not city and "mumbai" in description_lower:
                city = "mumbai"
            if "mumbai" in city:
                department_key = "mumbai_police"
            else:
                department_key = "maharashtra_police"
            if "in progress" in description_lower or "happening" in description_lower or "urgent" in description_lower:
                urgency = "urgent"
            else:
                urgency = "high"
            category = "safety"
            logger.warning(f"🚔 POLICE/CRIME issue detected - forcing police department (city: {city})")
        # NON-EMERGENCY ROUTING BY KEYWORDS
        elif any(kw in description_lower for kw in ["electricity", "power", "meter", "electric", "power cut", "load shedding", "blackout", "outage", "voltage", "transformer"]):
            department_key = "mseb"
            category = "utilities"
            logger.warning(f"⚡ ELECTRICITY issue detected - forcing MSEB")
        elif any(kw in description_lower for kw in ["garbage", "waste", "sewage", "trash", "dumping", "garbage collection", "solid waste", "refuse"]):
            city = provided_location.get("city", "").lower() if provided_location else ""
            if "mumbai" in city:
                department_key = "bmc"
            elif "pune" in city:
                department_key = "pune_municipal"
            elif "nagpur" in city:
                department_key = "nagpur_municipal"
            else:
                department_key = "municipal"
            category = "sanitation"
            logger.warning(f"🗑️ GARBAGE/SANITATION issue detected - routing to municipal")
        elif any(kw in description_lower for kw in ["water supply", "water shortage", "water pressure", "no water", "water problem", "water issue", "water cut", "water connection"]):
            city = provided_location.get("city", "").lower() if provided_location else ""
            if "mumbai" in city:
                department_key = "bmc"
            elif "pune" in city:
                department_key = "pune_municipal"
            elif "nagpur" in city:
                department_key = "nagpur_municipal"
            else:
                department_key = "municipal"
            category = "utilities"
            logger.warning(f"💧 WATER issue detected - routing to municipal")
        elif any(kw in description_lower for kw in ["road", "pothole", "bridge", "street", "highway", "pavement", "footpath", "sidewalk", "road repair", "road condition"]):
            city = provided_location.get("city", "").lower() if provided_location else ""
            if "mumbai" in city:
                department_key = "bmc"
            elif "pune" in city:
                department_key = "pune_municipal"
            elif "nagpur" in city:
                department_key = "nagpur_municipal"
            else:
                department_key = "municipal"
            category = "infrastructure"
            logger.warning(f"🛣️ ROAD/INFRASTRUCTURE issue detected - routing to municipal")
        elif any(kw in description_lower for kw in ["bus", "transport", "st bus", "state transport", "msrtc", "public transport"]):
            department_key = "msrtc"
            category = "transport"
            logger.warning(f"🚌 TRANSPORT issue detected - routing to MSRTC")
        elif any(kw in description_lower for kw in ["train", "railway", "railway station", "rail", "locomotive", "railway ticket"]):
            department_key = "central_railways"
            category = "transport"
            logger.warning(f"🚂 RAILWAY issue detected - routing to railways")
        elif any(kw in description_lower for kw in ["school", "education", "college", "teacher", "student", "tuition", "scholarship", "exam"]):
            department_key = "maharashtra_education"
            category = "education"
            logger.warning(f"📚 EDUCATION issue detected - routing to education department")
        elif any(kw in description_lower for kw in ["hospital", "health", "clinic", "doctor", "medicine", "treatment", "healthcare", "medical"]):
            department_key = "maharashtra_health"
            category = "health"
            logger.warning(f"🏥 HEALTH issue detected - routing to health department")
        elif any(kw in description_lower for kw in ["pollution", "environment", "air quality", "noise", "toxic", "contamination", "emission"]):
            department_key = "maharashtra_environment"
            category = "environment"
            logger.warning(f"🌍 ENVIRONMENT issue detected - routing to environment department")
        elif any(kw in description_lower for kw in ["post", "mail", "postal", "post office", "parcel", "letter"]):
            department_key = "central_post"
            category = "other"
            logger.warning(f"📮 POSTAL issue detected - routing to post")
        elif any(kw in description_lower for kw in ["internet", "telecom", "mobile", "phone", "network", "signal", "data", "broadband"]):
            department_key = "central_telecom"
            category = "utilities"
            logger.warning(f"📱 TELECOM issue detected - routing to telecom")
        elif any(kw in description_lower for kw in ["drainage", "sewer", "sewerage", "drain", "flooding", "water logging"]):
            city = provided_location.get("city", "").lower() if provided_location else ""
            if "mumbai" in city:
                department_key = "bmc"
            elif "pune" in city:
                department_key = "pune_municipal"
            elif "nagpur" in city:
                department_key = "nagpur_municipal"
            else:
                department_key = "municipal"
            category = "infrastructure"
            logger.warning(f"🌊 DRAINAGE issue detected - routing to municipal")
        elif any(kw in description_lower for kw in ["street light", "streetlight", "lamp post", "lighting", "dark street"]):
            city = provided_location.get("city", "").lower() if provided_location else ""
            if "mumbai" in city:
                department_key = "bmc"
            elif "pune" in city:
                department_key = "pune_municipal"
            elif "nagpur" in city:
                department_key = "nagpur_municipal"
            else:
                department_key = "municipal"
            category = "infrastructure"
            logger.warning(f"💡 STREET LIGHT issue detected - routing to municipal")
        
        # If keyword detection found a department, use it and skip LLM for department routing
        # But still use LLM for other fields if needed
        keyword_detected = department_key is not None
        
        location_context = json.dumps(provided_location, indent=2) if provided_location else "No location provided"
        
        # Build available departments context
        departments_context = json.dumps(INDIAN_DEPARTMENTS, indent=2)
        
        prompt = ChatPromptTemplate.from_template(AgentPrompts.CLASSIFICATION_PROMPT.template)
        formatted_prompt = prompt.format_messages(
            description=description,
            location_context=location_context,
            departments_context=departments_context
        )
        
        logger.info("Invoking agentic LLM for unified classification", description_length=len(description), keyword_detected=keyword_detected)
        response = self.llm.invoke(formatted_prompt)
        
        # Extract content from AIMessage if needed
        if hasattr(response, 'content'):
            response = response.content
        
        # Parse JSON from response using utility function
        from src.agents.utils import extract_json_from_string
        try:
            parsed = extract_json_from_string(response)
        except Exception as e:
            logger.error("Failed to parse JSON from classification response", error=str(e), response_preview=response[:500])
            raise ValueError(f"Failed to parse JSON from classification response: {str(e)}") from e
        
        # Extract and validate urgency (use keyword detection if available, otherwise LLM)
        valid_urgencies = ["urgent", "high", "medium", "low"]
        if urgency is None:
            urgency = parsed.get("urgency", "medium")
        if urgency not in valid_urgencies:
            logger.warning(f"Invalid urgency: {urgency}, defaulting to 'medium'")
            urgency = "medium"
        
        # Extract and validate category (use keyword detection if available, otherwise LLM)
        valid_categories = ["infrastructure", "utilities", "sanitation", "transport", 
                          "health", "education", "safety", "environment", "governance", "other"]
        if category is None:
            category = parsed.get("category", "other")
        if category not in valid_categories:
            logger.warning(f"Invalid category: {category}, defaulting to 'other'")
            category = "other"
        
        # Use keyword-detected department if available, otherwise use LLM
        if department_key is None:
            department_key = parsed.get("department", "municipal")
            # If LLM returned municipal, do a final keyword check to override if needed
            if department_key == "municipal":
                # CRITICAL: Check for police keywords FIRST (before other departments)
                if any(kw in description_lower for kw in police_keywords):
                    city = provided_location.get("city", "").lower() if provided_location else ""
                    if not city and "mumbai" in description_lower:
                        city = "mumbai"
                    if "mumbai" in city:
                        department_key = "mumbai_police"
                    else:
                        department_key = "maharashtra_police"
                    category = category or "safety"
                    urgency = urgency or "high"
                    logger.warning(f"🚔 POLICE keyword found - overriding municipal to police")
                # Check for any department-specific keywords one more time
                elif any(kw in description_lower for kw in ["electricity", "power", "meter", "electric", "power cut"]):
                    department_key = "mseb"
                    category = category or "utilities"
                    logger.warning(f"⚡ ELECTRICITY keyword found - overriding municipal to MSEB")
                elif any(kw in description_lower for kw in ["bus", "transport", "st bus", "state transport"]):
                    department_key = "msrtc"
                    category = category or "transport"
                    logger.warning(f"🚌 TRANSPORT keyword found - overriding municipal to MSRTC")
                elif any(kw in description_lower for kw in ["train", "railway", "railway station"]):
                    department_key = "central_railways"
                    category = category or "transport"
                    logger.warning(f"🚂 RAILWAY keyword found - overriding municipal to railways")
                elif any(kw in description_lower for kw in ["school", "education", "college", "teacher"]):
                    department_key = "maharashtra_education"
                    category = category or "education"
                    logger.warning(f"📚 EDUCATION keyword found - overriding municipal to education")
                elif any(kw in description_lower for kw in ["hospital", "health", "clinic", "doctor"]):
                    department_key = "maharashtra_health"
                    category = category or "health"
                    logger.warning(f"🏥 HEALTH keyword found - overriding municipal to health")
                elif any(kw in description_lower for kw in ["pollution", "environment", "air quality"]):
                    department_key = "maharashtra_environment"
                    category = category or "environment"
                    logger.warning(f"🌍 ENVIRONMENT keyword found - overriding municipal to environment")
        
        # CRITICAL SAFETY CHECK: Ensure police issues don't go to municipal (similar to fire check)
        if any(keyword in description_lower for keyword in police_keywords):
            if department_key in ["municipal", "bmc", "pune_municipal", "nagpur_municipal"]:
                city = provided_location.get("city", "").lower() if provided_location else ""
                if not city and "mumbai" in description_lower:
                    city = "mumbai"
                if "mumbai" in city:
                    department_key = "mumbai_police"
                else:
                    department_key = "maharashtra_police"
                category = "safety"
                if urgency not in ["urgent", "high"]:
                    urgency = "high"
                logger.error(f"🚔 CRITICAL: Police issue detected but routed to {parsed.get('department', 'municipal')}! Forcing police department.")
        
        # Final validation: If still municipal, check if it's valid based on location
        if department_key == "municipal":
            city = provided_location.get("city", "").lower() if provided_location else ""
            # Also check description for city names
            if not city:
                if "mumbai" in description_lower:
                    city = "mumbai"
                elif "pune" in description_lower:
                    city = "pune"
                elif "nagpur" in description_lower:
                    city = "nagpur"
            
            if "mumbai" in city:
                department_key = "bmc"
                logger.warning(f"📍 MUMBAI location detected - routing to BMC")
            elif "pune" in city:
                department_key = "pune_municipal"
                logger.warning(f"📍 PUNE location detected - routing to PMC")
            elif "nagpur" in city:
                department_key = "nagpur_municipal"
                logger.warning(f"📍 NAGPUR location detected - routing to NMC")
        
        if department_key not in INDIAN_DEPARTMENTS:
            logger.warning(f"Invalid department: {department_key}, using municipal")
            department_key = "municipal"
        
        department_info = INDIAN_DEPARTMENTS[department_key]
        department_name = parsed.get("department_name", department_info["name"])
        
        # Merge provided location with extracted location
        extracted_location = provided_location.copy() if provided_location else {}
        if parsed.get("location"):
            extracted_location.update(parsed["location"])
        
        # Ensure country is set
        extracted_location["country"] = extracted_location.get("country", "India")
        
        result = {
            "urgency": urgency,
            "structured_category": category,
            "department": department_key,
            "department_name": department_name,
            "extracted_location": extracted_location,
            "jurisdiction": parsed.get("jurisdiction", "city"),
            "agent_metadata": {
                "reasoning": parsed.get("reasoning", ""),
                "confidence": parsed.get("confidence", 0.0),
                "emergency_detected": parsed.get("emergency_detected", False),
                "key_details": parsed.get("key_details", {}),
            }
        }
        
        logger.info("Agentic classification successful", 
                  urgency=urgency,
                  category=category,
                  department=department_key,
                  emergency_detected=result["agent_metadata"]["emergency_detected"])
        
        return result


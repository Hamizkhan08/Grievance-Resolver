"""
Chatbot Agent.
AI agent that answers citizen questions about their complaints.
"""
from typing import Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from src.agents.base import BaseAgent
from src.agents.prompts import AgentPrompts
from src.agents.llm_factory import create_llm
from src.models.database import db
from datetime import datetime
import structlog
import json
import re

logger = structlog.get_logger()


class ChatbotAgent(BaseAgent):
    """Agent that answers citizen questions about complaints."""
    
    def __init__(self):
        """Initialize the chatbot agent."""
        super().__init__("ChatbotAgent")
        try:
            self.llm = create_llm(temperature=0.7)  # Higher temperature for conversational responses
            logger.info("LLM initialized for chatbot agent")
        except Exception as e:
            logger.error("Failed to initialize LLM for chatbot agent", error=str(e))
            raise RuntimeError("ChatbotAgent requires LLM to be configured") from e
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a chatbot query and return a response.
        
        Args:
            input_data: Dictionary with 'question', optional 'complaint_id', 'citizen_email', 'language'
        
        Returns:
            Dictionary with 'response', 'complaint_info', 'suggested_actions'
        """
        question = input_data.get("question", "")
        complaint_id = input_data.get("complaint_id")
        citizen_email = input_data.get("citizen_email")
        language = input_data.get("language", "en")  # Default to English
        
        # Validate language
        valid_languages = ["en", "english", "hi", "hindi", "mr", "marathi"]
        if language.lower() not in valid_languages:
            language = "en"  # Default to English if invalid
        
        # Normalize language code
        lang_map = {
            "english": "en",
            "hindi": "hi",
            "marathi": "mr"
        }
        language = lang_map.get(language.lower(), language.lower())
        
        # Extract complaint ID from question if it looks like a UUID
        # UUID pattern: 8-4-4-4-12 hex digits
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        uuid_match = re.search(uuid_pattern, question, re.IGNORECASE)
        if uuid_match and not complaint_id:
            # Found a UUID in the question - use it as complaint_id
            extracted_id = uuid_match.group()
            complaint_id = extracted_id
            logger.info("Extracted complaint ID from question", complaint_id=extracted_id)
            # Remove the UUID from question for cleaner context
            question = re.sub(uuid_pattern, '', question, flags=re.IGNORECASE).strip()
            # If question is now empty or just whitespace, make it a status query
            if not question or len(question) < 3:
                question = "What is the status of my complaint?"
        
        # Extract email from question if not provided
        if not citizen_email:
            # Email pattern: word characters, dots, hyphens, @, domain
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            email_match = re.search(email_pattern, question, re.IGNORECASE)
            if email_match:
                extracted_email = email_match.group()
                citizen_email = extracted_email
                logger.info("Extracted email from question", email=extracted_email)
                # Remove email from question for cleaner context (optional, keep it for now)
        
        if not question:
            greetings = {
                "en": "I'm here to help! Please ask me a question about your complaint.",
                "hi": "मैं यहाँ मदद के लिए हूँ! कृपया अपनी शिकायत के बारे में कोई प्रश्न पूछें।",
                "mr": "मी मदतीसाठी येथे आहे! कृपया तुमच्या तक्रारीबद्दल प्रश्न विचारा."
            }
            return {
                "response": greetings.get(language, greetings["en"]),
                "complaint_info": None,
                "suggested_actions": []
            }
        
        # Try to find complaint if ID or email provided
        complaint = None
        complaint_not_found_message = None
        
        if complaint_id:
            complaint = db.get_complaint(complaint_id)
            if not complaint:
                logger.warning("Complaint not found", complaint_id=complaint_id)
                # Provide helpful message if complaint ID was provided but not found
                complaint_not_found_message = {
                    "en": f"I couldn't find a complaint with ID {complaint_id[:8]}. Please verify the complaint ID or provide your email address.",
                    "hi": f"मुझे ID {complaint_id[:8]} के साथ कोई शिकायत नहीं मिली। कृपया शिकायत ID सत्यापित करें या अपना ईमेल पता प्रदान करें।",
                    "mr": f"मला ID {complaint_id[:8]} सह तक्रार सापडली नाही. कृपया तक्रार ID सत्यापित करा किंवा तुमचा ईमेल पत्ता प्रदान करा."
                }
        elif citizen_email:
            # Find complaints for this email - get all, then use most recent or match by question context
            try:
                logger.info("Searching for complaints by email", email=citizen_email)
                result = (
                    db.client.table("complaints")
                    .select("*")
                    .eq("citizen_email", citizen_email)
                    .order("created_at", desc=True)
                    .limit(10)  # Get up to 10 most recent complaints
                    .execute()
                )
                
                logger.info("Email query result", 
                           email=citizen_email, 
                           found_count=len(result.data) if result.data else 0)
                
                if result.data and len(result.data) > 0:
                    # If multiple complaints, try to match by question context
                    if len(result.data) > 1:
                        # Try to find complaint matching question keywords
                        question_lower = question.lower()
                        matched_complaint = None
                        for comp in result.data:
                            desc = comp.get("description", "").lower()
                            dept = comp.get("responsible_department", "").lower()
                            # Check if question mentions department or description keywords
                            if any(keyword in question_lower for keyword in [dept, desc[:50]]):
                                matched_complaint = comp
                                break
                        
                        # Use matched complaint or most recent
                        complaint = matched_complaint or result.data[0]
                        logger.info(
                            "Found multiple complaints by email",
                            email=citizen_email,
                            total_complaints=len(result.data),
                            using_complaint=complaint.get("id")[:8] if complaint else None
                        )
                    else:
                        complaint = result.data[0]
                    
                    # Use the found complaint's ID for context
                    complaint_id = complaint.get("id")
                    logger.info("Successfully found complaint by email", 
                               email=citizen_email, 
                               complaint_id=complaint_id[:8] if complaint_id else None,
                               status=complaint.get("status"))
                else:
                    logger.warning("No complaints found for email", email=citizen_email)
            except Exception as e:
                logger.error("Error finding complaint by email", email=citizen_email, error=str(e), error_type=type(e).__name__)
        
        # If complaint not found and ID was provided, return helpful message
        if complaint_not_found_message and not complaint:
            return {
                "response": complaint_not_found_message.get(language, complaint_not_found_message["en"]),
                "complaint_info": None,
                "suggested_actions": [
                    "Verify complaint ID",
                    "Provide email address",
                    "Contact support"
                ],
                "confidence": 1.0
            }
        
        # Generate response using LLM
        response = self._generate_response(question, complaint, language, complaint_id, citizen_email)
        
        self.log_decision(response, {
            "question_length": len(question),
            "complaint_found": complaint is not None,
            "language": language,
            "method": "agentic_llm"
        })
        
        return response
    
    def _generate_response(self, question: str, complaint: Optional[Dict[str, Any]] = None, language: str = "en", complaint_id: Optional[str] = None, citizen_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a conversational response to the question.
        
        Args:
            question: User's question
            complaint: Optional complaint data
            language: Language code (en, hi, mr)
            complaint_id: Optional complaint ID
            citizen_email: Optional citizen email (for context)
        
        Returns:
            Dictionary with response and metadata
        """
        complaint_context = ""
        time_remaining = None
        
        if complaint:
            complaint_id = complaint.get("id", complaint_id or "")
            status = complaint.get("status", "")
            department = complaint.get("current_department") or complaint.get("responsible_department", "")
            urgency = complaint.get("urgency", "")
            sla_deadline = complaint.get("sla_deadline", "")
            description = complaint.get("description", "")[:200]  # Truncate for context
            complaint_email = complaint.get("citizen_email", "")
            
            # Calculate time remaining
            if sla_deadline:
                try:
                    deadline = datetime.fromisoformat(sla_deadline.replace("Z", "+00:00"))
                    now = datetime.utcnow()
                    if deadline.tzinfo:
                        now = now.replace(tzinfo=deadline.tzinfo)
                    hours = (deadline - now).total_seconds() / 3600.0
                    if hours > 0:
                        days = int(hours / 24)
                        hours_remain = int(hours % 24)
                        time_remaining = f"{days} days, {hours_remain} hours"
                    else:
                        time_remaining = "OVERDUE"
                except:
                    pass
            
            # Get similar cases for context
            similar_count = self._get_similar_cases_count(department, status)
            
            # Build complaint context with email info if found via email
            complaint_email = complaint.get("citizen_email", "")
            found_via = "Complaint ID" if complaint_id and not citizen_email else "Email lookup"
            email_note = f" (Email: {complaint_email})" if complaint_email and citizen_email else ""
            
            complaint_context = f"""
COMPLAINT INFORMATION:
- Complaint ID: #{complaint_id[:8] if complaint_id else "N/A"}
- Status: {status}
- Department: {department}
- Urgency: {urgency}
- Description: {description}
- Time Remaining: {time_remaining or "N/A"}
- Similar Cases: {similar_count} similar cases in system
- Found via: {found_via}{email_note}
"""
        elif complaint_id:
            # Complaint ID provided but complaint not found - still provide context
            complaint_context = f"""
COMPLAINT INFORMATION:
- Complaint ID: #{complaint_id[:8]}
- Status: Not found (complaint may not exist or ID is incorrect)
"""
        
        prompt = ChatPromptTemplate.from_template(AgentPrompts.CHATBOT_PROMPT.template)
        formatted_prompt = prompt.format_messages(
            question=question,
            complaint_context=complaint_context or "No complaint information available. User may be asking general questions.",
            language=language
        )
        
        logger.info("Generating chatbot response", question_length=len(question), has_complaint=complaint is not None)
        response = self.llm.invoke(formatted_prompt)
        
        if hasattr(response, 'content'):
            response = response.content
        
        # Parse JSON from response using utility function
        from src.agents.utils import extract_json_from_string
        try:
            parsed = extract_json_from_string(response)
            return {
                "response": parsed.get("response", response),
                "complaint_info": {
                    "id": complaint.get("id") if complaint else complaint_id,
                    "status": complaint.get("status") if complaint else None,
                    "department": complaint.get("current_department") or (complaint.get("responsible_department") if complaint else None),
                    "time_remaining": time_remaining if complaint else None
                } if complaint else ({"id": complaint_id} if complaint_id else None),
                "suggested_actions": parsed.get("suggested_actions", []),
                "confidence": parsed.get("confidence", 0.8)
            }
        except Exception as e:
            logger.warning("Failed to parse JSON from chatbot response, using raw response", error=str(e))
            # Fallback: return raw response
        
        # Fallback: return raw response
        return {
            "response": response,
            "complaint_info": {
                "id": complaint.get("id") if complaint else None,
                "status": complaint.get("status") if complaint else None,
            } if complaint else None,
            "suggested_actions": [],
            "confidence": 0.7
        }
    
    def _get_similar_cases_count(self, department: str, status: str) -> int:
        """Get count of similar cases for context."""
        try:
            result = (
                db.client.table("complaints")
                .select("id", count="exact")
                .eq("responsible_department", department)
                .eq("status", status)
                .execute()
            )
            return result.count or 0
        except:
            return 0

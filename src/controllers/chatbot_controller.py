"""
Chatbot Controller.
Handles chatbot queries from citizens.
"""
from typing import Dict, Any
from src.agents.chatbot_agent import ChatbotAgent
from src.views.responses import ErrorView
import structlog

logger = structlog.get_logger()


class ChatbotController:
    """Controller for chatbot operations."""
    
    def __init__(self):
        """Initialize the chatbot controller."""
        self.chatbot_agent = ChatbotAgent()
    
    def handle_query(self, question: str, complaint_id: str = None, citizen_email: str = None, language: str = "en") -> Dict[str, Any]:
        """
        Handle a chatbot query.
        
        Args:
            question: User's question
            complaint_id: Optional complaint ID
            citizen_email: Optional citizen email
            language: Language code (en, hi, mr)
        
        Returns:
            Dictionary with chatbot response
        """
        try:
            if not question or not question.strip():
                return ErrorView.format("Question is required")
            
            result = self.chatbot_agent.process({
                "question": question.strip(),
                "complaint_id": complaint_id,
                "citizen_email": citizen_email,
                "language": language
            })
            
            return {
                "success": True,
                "response": result.get("response", "I'm here to help! Please ask me a question."),
                "complaint_info": result.get("complaint_info"),
                "suggested_actions": result.get("suggested_actions", []),
                "confidence": result.get("confidence", 0.8)
            }
        except Exception as e:
            logger.error("Error handling chatbot query", error=str(e))
            return ErrorView.format(f"Chatbot error: {str(e)}")

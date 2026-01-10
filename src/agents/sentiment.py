"""
Sentiment Analysis Agent.
Analyzes citizen complaints to detect frustration, anger, and emotional urgency.
Prioritizes emotionally charged complaints for faster response.
"""
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from src.agents.base import BaseAgent
from src.agents.prompts import AgentPrompts
from src.agents.llm_factory import create_llm
import structlog
import json
import re

logger = structlog.get_logger()


class SentimentAnalysisAgent(BaseAgent):
    """Agent that analyzes sentiment and emotional urgency in complaints."""
    
    def __init__(self):
        """Initialize the sentiment analysis agent."""
        super().__init__("SentimentAnalysisAgent")
        try:
            self.llm = create_llm(temperature=0.3)  # Lower temperature for consistent sentiment analysis
            logger.info("LLM initialized for sentiment analysis")
        except Exception as e:
            logger.error("Failed to initialize LLM for sentiment analysis", error=str(e))
            raise RuntimeError("SentimentAnalysisAgent requires LLM to be configured") from e
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze sentiment and emotional urgency of a complaint.
        
        Args:
            input_data: Dictionary with 'description', 'citizen_name', 'citizen_email', etc.
        
        Returns:
            Dictionary with sentiment analysis results including:
            - sentiment_score: float (-1.0 to 1.0, negative = negative sentiment)
            - emotion_level: str (calm, concerned, frustrated, angry, urgent)
            - frustration_indicators: list of detected frustration keywords/phrases
            - urgency_boost: float (0.0 to 1.0, additional urgency based on emotion)
            - priority_recommendation: str (normal, high, urgent)
        """
        description = input_data.get("description", "")
        citizen_name = input_data.get("citizen_name", "")
        citizen_email = input_data.get("citizen_email", "")
        
        if not description:
            return {
                "sentiment_score": 0.0,
                "emotion_level": "calm",
                "frustration_indicators": [],
                "urgency_boost": 0.0,
                "priority_recommendation": "normal"
            }
        
        try:
            result = self._analyze_sentiment_with_llm(description)
            
            # Apply keyword-based overrides for critical emotions
            result = self._apply_keyword_boosts(description, result)
            
            self.log_decision(result, {
                "description_length": len(description),
                "method": "agentic_llm"
            })
            
            return result
        except Exception as e:
            logger.error("Sentiment analysis failed", error=str(e))
            # Return neutral sentiment on error
            return {
                "sentiment_score": 0.0,
                "emotion_level": "calm",
                "frustration_indicators": [],
                "urgency_boost": 0.0,
                "priority_recommendation": "normal"
            }
    
    def _analyze_sentiment_with_llm(self, description: str) -> Dict[str, Any]:
        """
        Use agentic LLM to analyze sentiment and emotional state.
        
        Args:
            description: Complaint description text
        
        Returns:
            Dictionary with sentiment analysis results
        """
        prompt = ChatPromptTemplate.from_template(AgentPrompts.SENTIMENT_ANALYSIS_PROMPT.template)
        formatted_prompt = prompt.format_messages(description=description)
        
        logger.info("Invoking agentic LLM for sentiment analysis", description_length=len(description))
        response = self.llm.invoke(formatted_prompt)
        
        # Extract content from AIMessage if needed
        if hasattr(response, 'content'):
            response = response.content
        
        # Parse JSON from response
        parsed = self._parse_json_response(response)
        
        # Validate and normalize results
        sentiment_score = float(parsed.get("sentiment_score", 0.0))
        sentiment_score = max(-1.0, min(1.0, sentiment_score))  # Clamp to [-1, 1]
        
        emotion_level = parsed.get("emotion_level", "calm").lower()
        valid_emotions = ["calm", "concerned", "frustrated", "angry", "urgent"]
        if emotion_level not in valid_emotions:
            emotion_level = "calm"
        
        urgency_boost = float(parsed.get("urgency_boost", 0.0))
        urgency_boost = max(0.0, min(1.0, urgency_boost))  # Clamp to [0, 1]
        
        priority_recommendation = parsed.get("priority_recommendation", "normal").lower()
        valid_priorities = ["normal", "high", "urgent"]
        if priority_recommendation not in valid_priorities:
            priority_recommendation = "normal"
        
        result = {
            "sentiment_score": sentiment_score,
            "emotion_level": emotion_level,
            "frustration_indicators": parsed.get("frustration_indicators", []),
            "urgency_boost": urgency_boost,
            "priority_recommendation": priority_recommendation,
            "reasoning": parsed.get("reasoning", ""),
            "detected_emotions": parsed.get("detected_emotions", [])
        }
        
        logger.info("Sentiment analysis successful", 
                  sentiment_score=sentiment_score,
                  emotion_level=emotion_level,
                  urgency_boost=urgency_boost)
        
        return result
    
    def _apply_keyword_boosts(self, description: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply keyword-based sentiment boosts for critical emotional indicators.
        
        Args:
            description: Complaint description
            result: Current sentiment analysis result
        
        Returns:
            Updated result with keyword-based boosts
        """
        description_lower = description.lower()
        
        # Critical anger indicators
        critical_anger = [
            "very angry", "extremely angry", "furious", "outraged", "livid",
            "fed up", "had enough", "unacceptable", "disgusted", "appalled"
        ]
        if any(keyword in description_lower for keyword in critical_anger):
            result["emotion_level"] = "angry"
            result["sentiment_score"] = min(-0.8, result["sentiment_score"])
            result["urgency_boost"] = max(0.7, result["urgency_boost"])
            result["priority_recommendation"] = "urgent"
            if "critical_anger" not in result["frustration_indicators"]:
                result["frustration_indicators"].append("critical_anger_detected")
        
        # High frustration indicators
        high_frustration = [
            "frustrated", "annoyed", "irritated", "disappointed", "upset",
            "not happy", "dissatisfied", "complained before", "no response",
            "ignored", "neglected", "repeated complaint"
        ]
        if any(keyword in description_lower for keyword in high_frustration):
            if result["emotion_level"] not in ["angry", "urgent"]:
                result["emotion_level"] = "frustrated"
            result["sentiment_score"] = min(-0.5, result["sentiment_score"])
            result["urgency_boost"] = max(0.4, result["urgency_boost"])
            if result["priority_recommendation"] == "normal":
                result["priority_recommendation"] = "high"
        
        # Urgency language
        urgency_language = [
            "immediately", "urgent", "asap", "right now", "emergency",
            "critical", "life threatening", "dangerous", "unsafe"
        ]
        if any(keyword in description_lower for keyword in urgency_language):
            result["urgency_boost"] = max(0.5, result["urgency_boost"])
            if result["priority_recommendation"] != "urgent":
                result["priority_recommendation"] = "high"
        
        # Positive sentiment (gratitude, politeness)
        positive_indicators = [
            "thank you", "appreciate", "grateful", "please", "kindly",
            "respectfully", "hope", "would be great"
        ]
        if any(keyword in description_lower for keyword in positive_indicators):
            if result["sentiment_score"] < 0:
                result["sentiment_score"] = max(-0.3, result["sentiment_score"])
        
        return result
    
    def _parse_json_response(self, response: str) -> dict:
        """Parse JSON from LLM response, handling extra text."""
        # Find first { and matching }
        start_idx = response.find('{')
        if start_idx == -1:
            raise ValueError(f"No JSON found in response: {response[:500]}")
        
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
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {str(e)}. Response: {response[:500]}") from e

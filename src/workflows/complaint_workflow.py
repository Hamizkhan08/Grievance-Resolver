"""
Complaint Processing Workflow using LangGraph.
Orchestrates agents to process complaints end-to-end.
"""
from typing import TypedDict
from datetime import datetime
import uuid
from langgraph.graph import StateGraph, END
from src.agents.classification import ClassificationAgent
from src.agents.complaint_understanding import ComplaintUnderstandingAgent
from src.agents.department_routing import DepartmentRoutingAgent
from src.agents.sla_assignment import SLAAssignmentAgent
from src.agents.citizen_communication import CitizenCommunicationAgent
from src.agents.sentiment import SentimentAnalysisAgent
from src.agents.policy_intelligence import PolicyIntelligenceAgent
from src.models.database import db
from src.models.schemas import ComplaintStatus, EscalationLevel
import structlog
import langchain

# Patch langchain.debug to avoid AttributeError in LangGraph
if not hasattr(langchain, 'debug'):
    langchain.debug = False

logger = structlog.get_logger()


class ComplaintState(TypedDict):
    """State for complaint processing workflow."""
    complaint_id: str
    description: str
    location: dict
    citizen_name: str
    citizen_email: str
    citizen_phone: str
    attachments: list
    
    # Agent outputs
    structured_category: str
    urgency: str
    extracted_location: dict
    department: str
    department_name: str
    sla_deadline: str
    sla_hours: int
    
    # Sentiment analysis
    sentiment_score: float
    emotion_level: str
    urgency_boost: float
    priority_recommendation: str
    
    # Policy intelligence
    applicable_policies: list
    legal_sla: dict
    policy_violation: bool
    policy_reference: str
    suggested_action: str
    
    # Status
    status: str
    escalation_level: str
    
    # Communication
    citizen_message: str
    citizen_subject: str
    
    # Metadata
    errors: list
    agent_metadata: dict


class ComplaintWorkflow:
    """LangGraph workflow for processing complaints."""
    
    def __init__(self):
        """Initialize the workflow and agents."""
        # Use unified classification agent for better urgency and department routing
        self.classification_agent = ClassificationAgent()
        # Keep old agents as fallback
        self.understanding_agent = ComplaintUnderstandingAgent()
        self.routing_agent = DepartmentRoutingAgent()
        self.sla_agent = SLAAssignmentAgent()
        self.communication_agent = CitizenCommunicationAgent()
        self.sentiment_agent = SentimentAnalysisAgent()
        self.policy_agent = PolicyIntelligenceAgent()
        
        # Build workflow graph
        self.workflow = self._build_workflow()
        # Compile without debug mode (langchain.debug doesn't exist in newer versions)
        self.app = self.workflow.compile(debug=False)
        logger.info("Complaint workflow initialized with unified classification")
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(ComplaintState)
        
        # Add nodes
        workflow.add_node("classify", self._classify_complaint)  # Unified classification
        workflow.add_node("analyze_sentiment", self._analyze_sentiment)  # Sentiment analysis
        workflow.add_node("assign_sla", self._assign_sla)
        workflow.add_node("analyze_policy", self._analyze_policy)  # Policy intelligence
        workflow.add_node("persist", self._persist_complaint)
        workflow.add_node("notify", self._notify_citizen)
        
        # Define edges
        workflow.set_entry_point("classify")
        workflow.add_edge("classify", "analyze_sentiment")
        workflow.add_edge("analyze_sentiment", "assign_sla")
        workflow.add_edge("assign_sla", "analyze_policy")  # Policy analysis after SLA
        workflow.add_edge("analyze_policy", "persist")
        workflow.add_edge("persist", "notify")
        workflow.add_edge("notify", END)
        
        return workflow
    
    def _classify_complaint(self, state: ComplaintState) -> ComplaintState:
        """Node: Unified classification - urgency, category, and department routing."""
        try:
            # Use unified classification agent
            result = self.classification_agent.process({
                "description": state["description"],
                "location": state.get("location", {}),
            })
            
            # Extract all classification results
            state["structured_category"] = result["structured_category"]
            state["urgency"] = result["urgency"]
            state["department"] = result["department"]
            state["department_name"] = result["department_name"]
            state["extracted_location"] = result["extracted_location"]
            
            # CRITICAL: Double-check for fire emergencies in workflow (safety net)
            description_lower = state["description"].lower()
            fire_keywords = ["fire", "burning", "blaze", "smoke", "flames", "on fire", "caught fire", "fire broke out"]
            has_fire = any(keyword in description_lower for keyword in fire_keywords)
            
            if has_fire and state["department"] != "fire":
                logger.error(f"🔥 CRITICAL: Fire detected but routed to {state['department']}! Forcing fire department.")
                state["department"] = "fire"
                state["department_name"] = "Maharashtra Fire Department"
                state["urgency"] = "urgent"
                state["structured_category"] = "safety"
            
            if has_fire and state["urgency"] != "urgent":
                logger.error(f"🔥 CRITICAL: Fire detected but urgency is {state['urgency']}! Forcing urgent.")
                state["urgency"] = "urgent"
            
            # Merge extracted location with provided location
            if state.get("location"):
                state["location"].update(state["extracted_location"])
            else:
                state["location"] = state["extracted_location"]
            
            # Store classification metadata
            state["agent_metadata"] = result.get("agent_metadata", {})
            
            logger.info("Complaint classified", 
                       complaint_id=state.get("complaint_id"),
                       urgency=state["urgency"],
                       department=state["department"],
                       emergency_detected=has_fire or result.get("agent_metadata", {}).get("emergency_detected", False))
            
            # Initialize sentiment fields
            state["sentiment_score"] = 0.0
            state["emotion_level"] = "calm"
            state["urgency_boost"] = 0.0
            state["priority_recommendation"] = "normal"
        except Exception as e:
            logger.error("Error in classification", error=str(e))
            state.setdefault("errors", []).append(f"Classification failed: {str(e)}")
            # Fallback to separate agents if classification fails
            try:
                logger.info("Falling back to separate understanding and routing agents")
                # Try understanding agent
                understanding_result = self.understanding_agent.process({
                    "description": state["description"],
                    "location": state.get("location", {}),
                })
                state["structured_category"] = understanding_result["structured_category"]
                state["urgency"] = understanding_result["urgency"]
                state["extracted_location"] = understanding_result["extracted_location"]
                
                # Try routing agent
                routing_result = self.routing_agent.process({
                    "category": state["structured_category"],
                    "location": state["location"],
                    "description": state["description"],
                })
                state["department"] = routing_result["department"]
                state["department_name"] = routing_result["department_name"]
            except Exception as fallback_error:
                logger.error("Fallback agents also failed", error=str(fallback_error))
                # Ultimate fallback
                state["urgency"] = "medium"
                state["structured_category"] = "other"
                state["department"] = "municipal"
                state["department_name"] = "Municipal Corporation"
        
        return state
    
    def _analyze_sentiment(self, state: ComplaintState) -> ComplaintState:
        """Node: Analyze sentiment and adjust urgency based on emotional state."""
        try:
            sentiment_result = self.sentiment_agent.process({
                "description": state["description"],
                "citizen_name": state.get("citizen_name", ""),
                "citizen_email": state.get("citizen_email", ""),
            })
            
            # Store sentiment analysis results
            state["sentiment_score"] = sentiment_result.get("sentiment_score", 0.0)
            state["emotion_level"] = sentiment_result.get("emotion_level", "calm")
            state["urgency_boost"] = sentiment_result.get("urgency_boost", 0.0)
            state["priority_recommendation"] = sentiment_result.get("priority_recommendation", "normal")
            
            # Adjust urgency based on sentiment
            urgency_map = {"low": 1, "medium": 2, "high": 3, "urgent": 4}
            current_urgency_level = urgency_map.get(state["urgency"], 2)
            
            # Apply sentiment-based urgency boost
            if state["emotion_level"] in ["angry", "urgent"]:
                # Critical emotional state - boost to urgent if not already
                if current_urgency_level < 4:
                    logger.warning(f"😠 High emotion detected ({state['emotion_level']}): Boosting urgency from {state['urgency']} to urgent")
                    state["urgency"] = "urgent"
            elif state["emotion_level"] == "frustrated":
                # Frustration - boost by one level
                if current_urgency_level < 3:
                    if state["urgency"] == "low":
                        state["urgency"] = "medium"
                    elif state["urgency"] == "medium":
                        state["urgency"] = "high"
                    logger.info(f"😤 Frustration detected: Boosting urgency to {state['urgency']}")
            elif state["priority_recommendation"] == "high" and current_urgency_level < 3:
                # Sentiment agent recommends high priority
                if state["urgency"] == "low":
                    state["urgency"] = "medium"
                elif state["urgency"] == "medium":
                    state["urgency"] = "high"
            
            # Store sentiment metadata
            if "agent_metadata" not in state:
                state["agent_metadata"] = {}
            state["agent_metadata"]["sentiment"] = {
                "score": state["sentiment_score"],
                "emotion": state["emotion_level"],
                "urgency_boost": state["urgency_boost"],
                "frustration_indicators": sentiment_result.get("frustration_indicators", []),
                "detected_emotions": sentiment_result.get("detected_emotions", [])
            }
            
            logger.info("Sentiment analysis completed",
                       complaint_id=state.get("complaint_id"),
                       sentiment_score=state["sentiment_score"],
                       emotion_level=state["emotion_level"],
                       adjusted_urgency=state["urgency"])
        except Exception as e:
            logger.error("Error in sentiment analysis", error=str(e))
            state.setdefault("errors", []).append(f"Sentiment analysis failed: {str(e)}")
            # Continue with default values
            state["sentiment_score"] = 0.0
            state["emotion_level"] = "calm"
            state["urgency_boost"] = 0.0
            state["priority_recommendation"] = "normal"
        
        return state
    
    def _assign_sla(self, state: ComplaintState) -> ComplaintState:
        """Node: Assign SLA deadline."""
        try:
            result = self.sla_agent.process({
                "urgency": state["urgency"],
                "category": state["structured_category"],
                "description": state["description"],  # Pass description for context-aware SLA
                "location": state.get("location", {}),
                "department": state.get("department", ""),  # Pass department for context - critical for fire emergencies
            })
            
            state["sla_deadline"] = result["sla_deadline"]
            state["sla_hours"] = result["sla_hours"]
            
            logger.info("SLA assigned", 
                       sla_hours=result["sla_hours"],
                       urgency=state["urgency"],
                       department=state.get("department"))
        except Exception as e:
            logger.error("Error in SLA assignment", error=str(e))
            state.setdefault("errors", []).append(f"SLA assignment failed: {str(e)}")
            # Realistic fallback based on urgency and description keywords
            from datetime import timedelta
            urgency = state.get("urgency", "medium")
            description_lower = state.get("description", "").lower()
            department = state.get("department", "")
            
            # Check for emergency keywords even in fallback
            fire_keywords = ["fire", "burning", "blaze", "smoke", "flames"]
            if any(keyword in description_lower for keyword in fire_keywords) or department == "fire":
                deadline = datetime.utcnow() + timedelta(minutes=30)  # 30 minutes for fire
                sla_hours = 0.5
            elif urgency == "urgent":
                deadline = datetime.utcnow() + timedelta(hours=1)  # 1 hour for urgent
                sla_hours = 1
            elif urgency == "high":
                deadline = datetime.utcnow() + timedelta(hours=6)  # 6 hours for high
                sla_hours = 6
            elif urgency == "medium":
                deadline = datetime.utcnow() + timedelta(days=3)  # 3 days for medium
                sla_hours = 72
            else:
                deadline = datetime.utcnow() + timedelta(days=7)  # 7 days for low
                sla_hours = 168
            state["sla_deadline"] = deadline.isoformat()
            state["sla_hours"] = sla_hours
        
        return state
    
    def _analyze_policy(self, state: ComplaintState) -> ComplaintState:
        """Node: Analyze policy intelligence and map to government rules/GRs."""
        try:
            policy_result = self.policy_agent.process(
                description=state["description"],
                category=state["structured_category"],
                department=state.get("department", ""),
                urgency=state["urgency"],
                location=state.get("extracted_location", state.get("location", {}))
            )
            
            # Store policy intelligence results
            state["applicable_policies"] = policy_result.get("applicable_policies", [])
            state["legal_sla"] = policy_result.get("legal_sla", {})
            state["policy_violation"] = policy_result.get("policy_violation", False)
            state["policy_reference"] = policy_result.get("policy_reference")
            state["suggested_action"] = policy_result.get("suggested_action", "Standard complaint processing")
            state["escalation_strategy"] = policy_result.get("escalation_strategy", {})
            state["escalation_authority"] = policy_result.get("escalation_authority")
            
            # Compare legal SLA with assigned SLA
            legal_sla_hours = state["legal_sla"].get("hours") if state["legal_sla"] else None
            assigned_sla_hours = state.get("sla_hours")
            
            # Detect violation if assigned SLA exceeds legal SLA
            if legal_sla_hours and assigned_sla_hours:
                if assigned_sla_hours > legal_sla_hours:
                    state["policy_violation"] = True
                    logger.warning(
                        "Policy violation detected",
                        complaint_id=state.get("complaint_id"),
                        legal_sla_hours=legal_sla_hours,
                        assigned_sla_hours=assigned_sla_hours,
                        policy_reference=state["policy_reference"]
                    )
            
            # Store policy metadata
            if "agent_metadata" not in state:
                state["agent_metadata"] = {}
            state["agent_metadata"]["policy_intelligence"] = {
                "applicable_policies": state["applicable_policies"],
                "legal_sla": state["legal_sla"],
                "policy_violation": state["policy_violation"],
                "violation_details": policy_result.get("violation_details", {}),
                "escalation_authority": policy_result.get("escalation_authority"),
                "escalation_strategy": policy_result.get("escalation_strategy", {}),
                "primary_policy": policy_result.get("primary_policy", {}),
                "suggested_action": policy_result.get("suggested_action", ""),
                "policy_reference": policy_result.get("policy_reference")
            }
            
            logger.info("Policy analysis completed",
                       complaint_id=state.get("complaint_id"),
                       policies_count=len(state["applicable_policies"]),
                       policy_violation=state["policy_violation"],
                       policy_reference=state["policy_reference"])
        except Exception as e:
            logger.error("Error in policy analysis", error=str(e))
            state.setdefault("errors", []).append(f"Policy analysis failed: {str(e)}")
            # Continue with default values
            state["applicable_policies"] = []
            state["legal_sla"] = {}
            state["policy_violation"] = False
            state["policy_reference"] = None
            state["suggested_action"] = "Standard complaint processing"
        
        return state
    
    def _persist_complaint(self, state: ComplaintState) -> ComplaintState:
        """Node: Persist complaint to database."""
        try:
            complaint_id = state.get("complaint_id") or str(uuid.uuid4())
            state["complaint_id"] = complaint_id
            
            # Build complaint data - store sentiment fields in agent_metadata if columns don't exist
            complaint_data = {
                "id": complaint_id,
                "description": state["description"],
                "structured_category": state["structured_category"],
                "location": state["location"],
                "responsible_department": state["department"],
                "status": ComplaintStatus.OPEN.value,
                "urgency": state["urgency"],
                "sla_deadline": state["sla_deadline"],
                "escalation_level": EscalationLevel.NONE.value,
                "citizen_name": state.get("citizen_name"),
                "citizen_email": state.get("citizen_email"),
                "citizen_phone": state.get("citizen_phone"),
                "attachments": state.get("attachments", []),
                "agent_metadata": {
                    "department_name": state["department_name"],
                    "sla_hours": state["sla_hours"],
                    "workflow_errors": state.get("errors", []),
                    "sentiment": {
                        "sentiment_score": state.get("sentiment_score", 0.0),
                        "emotion_level": state.get("emotion_level", "calm"),
                        "urgency_boost": state.get("urgency_boost", 0.0),
                        **state.get("agent_metadata", {}).get("sentiment", {})
                    },
                    "policy_intelligence": state.get("agent_metadata", {}).get("policy_intelligence", {}),
                },
            }
            
            # Try to add sentiment columns if they exist in the database (for backward compatibility)
            # If columns don't exist, they'll be stored in agent_metadata above
            try:
                # Only add if we have values (let database handle defaults if columns exist)
                sentiment_score = state.get("sentiment_score")
                emotion_level = state.get("emotion_level")
                urgency_boost = state.get("urgency_boost")
                
                # Attempt to add these fields - if columns don't exist, Supabase will ignore them
                # We'll catch the error and retry without these fields if needed
                if sentiment_score is not None:
                    complaint_data["sentiment_score"] = sentiment_score
                if emotion_level:
                    complaint_data["emotion_level"] = emotion_level
                if urgency_boost is not None:
                    complaint_data["urgency_boost"] = urgency_boost
            except Exception:
                # If adding these fields fails, they're already in agent_metadata
                pass
            
            db.create_complaint(complaint_data)
            logger.info("Complaint persisted", complaint_id=complaint_id)
        except Exception as e:
            logger.error("Error persisting complaint", error=str(e))
            state.setdefault("errors", []).append(f"Persistence failed: {str(e)}")
        
        return state
    
    def _notify_citizen(self, state: ComplaintState) -> ComplaintState:
        """Node: Generate and prepare citizen notification."""
        try:
            result = self.communication_agent.process({
                "status": ComplaintStatus.OPEN.value,
                "complaint_id": state["complaint_id"],
                "department": state["department_name"],
                "escalation_level": EscalationLevel.NONE.value,
                "time_remaining_hours": state.get("sla_hours"),
                "policy_reference": state.get("policy_reference"),
                "policy_violation": state.get("policy_violation", False),
                "suggested_action": state.get("suggested_action"),
            })
            
            state["citizen_message"] = result["message"]
            state["citizen_subject"] = result["subject"]
            
            logger.info("Citizen notification prepared", complaint_id=state["complaint_id"])
        except Exception as e:
            logger.error("Error in notification", error=str(e))
            state.setdefault("errors", []).append(f"Notification failed: {str(e)}")
        
        return state
    
    def run(self, complaint_data: dict) -> dict:
        """
        Execute the complaint processing workflow.
        
        Args:
            complaint_data: Dictionary with complaint input
        
        Returns:
            Final workflow state
        """
        initial_state: ComplaintState = {
            "complaint_id": "",
            "description": complaint_data["description"],
            "location": complaint_data.get("location", {}),
            "citizen_name": complaint_data.get("citizen_name", ""),
            "citizen_email": complaint_data.get("citizen_email", ""),
            "citizen_phone": complaint_data.get("citizen_phone", ""),
            "attachments": complaint_data.get("attachments", []),
            "structured_category": "",
            "urgency": "",
            "extracted_location": {},
            "department": "",
            "department_name": "",
            "sla_deadline": "",
            "sla_hours": 0,
            "status": ComplaintStatus.OPEN.value,
            "escalation_level": EscalationLevel.NONE.value,
            "citizen_message": "",
            "citizen_subject": "",
            "errors": [],
            "agent_metadata": {},
        }
        
        try:
            final_state = self.app.invoke(initial_state)
            return final_state
        except Exception as e:
            logger.error("Workflow execution failed", error=str(e))
            initial_state["errors"].append(f"Workflow failed: {str(e)}")
            return initial_state


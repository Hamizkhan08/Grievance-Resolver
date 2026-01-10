"""
Base agent class for all specialized agents.
Provides common functionality and interface.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
import structlog

logger = structlog.get_logger()


class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(self, name: str):
        """
        Initialize the agent.
        
        Args:
            name: Agent name for logging
        """
        self.name = name
        logger.info("Agent initialized", agent=name)
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data and return results.
        
        Args:
            input_data: Input data dictionary
        
        Returns:
            Results dictionary
        """
        pass
    
    def log_decision(self, decision: Dict[str, Any], context: Dict[str, Any] = None):
        """
        Log agent decision for auditability.
        
        Args:
            decision: Decision made by agent
            context: Optional context information
        """
        logger.info(
            "Agent decision",
            agent=self.name,
            decision=decision,
            context=context or {}
        )


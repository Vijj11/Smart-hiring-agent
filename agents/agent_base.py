"""
Base agent interface and common functionality for all agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class AgentBase(ABC):
    """Base class for all agents in the Smart Hiring Suite."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"agent.{name}")
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method for the agent.
        
        Args:
            input_data: Input data dictionary
            
        Returns:
            Output data dictionary
        """
        pass
    
    def validate_input(self, input_data: Dict[str, Any], required_fields: List[str]) -> bool:
        """
        Validate that required fields are present in input.
        
        Args:
            input_data: Input data to validate
            required_fields: List of required field names
            
        Returns:
            True if valid, False otherwise
        """
        missing = [field for field in required_fields if field not in input_data]
        if missing:
            self.logger.error(f"Missing required fields: {missing}")
            return False
        return True
    
    def log_processing(self, input_data: Dict[str, Any], output_data: Dict[str, Any]):
        """Log processing results."""
        self.logger.info(f"Processed input: {len(str(input_data))} chars -> output: {len(str(output_data))} chars")


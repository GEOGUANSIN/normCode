"""Agent Mapping Service - Maps inferences to agents based on rules.

This module provides AgentMappingService which determines which agent
should handle a given inference based on:
1. Explicit assignments (flow_index → agent_id)
2. Pattern-based rules (regex matching on flow_index, concept_name, etc.)
3. Default agent fallback
"""

import re
import logging
from typing import Dict, Any, Optional, List

from .config import MappingRule

logger = logging.getLogger(__name__)


class AgentMappingService:
    """Maps inferences to agents based on rules.
    
    The resolution order is:
    1. Check explicit assignments (direct flow_index → agent_id mapping)
    2. Check rules in priority order (highest priority first)
    3. Fall back to default agent
    """
    
    def __init__(self):
        self.rules: List[MappingRule] = []
        self.explicit: Dict[str, str] = {}  # flow_index → agent_id
        self.default_agent: str = "default"
    
    def add_rule(self, rule: MappingRule) -> None:
        """Add a mapping rule, maintaining priority order."""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: -r.priority)
    
    def remove_rule(self, index: int) -> None:
        """Remove a rule by index."""
        if 0 <= index < len(self.rules):
            self.rules.pop(index)
    
    def clear_rules(self) -> None:
        """Clear all rules."""
        self.rules = []
    
    def set_explicit(self, flow_index: str, agent_id: str) -> None:
        """Set explicit agent assignment for an inference."""
        self.explicit[flow_index] = agent_id
    
    def clear_explicit(self, flow_index: str) -> None:
        """Remove explicit assignment."""
        self.explicit.pop(flow_index, None)
    
    def clear_all_explicit(self) -> None:
        """Clear all explicit assignments."""
        self.explicit = {}
    
    def get_agent_for_inference(
        self,
        flow_index: str,
        concept_name: Optional[str] = None,
        sequence_type: Optional[str] = None
    ) -> str:
        """Determine which agent should handle an inference."""
        
        # Check explicit assignment first
        if flow_index in self.explicit:
            return self.explicit[flow_index]
        
        # Check rules in priority order
        for rule in self.rules:
            if self._matches_rule(rule, flow_index, concept_name, sequence_type):
                return rule.agent_id
        
        return self.default_agent
    
    def _matches_rule(
        self,
        rule: MappingRule,
        flow_index: str,
        concept_name: Optional[str],
        sequence_type: Optional[str]
    ) -> bool:
        """Check if rule matches the inference."""
        value = {
            'flow_index': flow_index,
            'concept_name': concept_name or '',
            'sequence_type': sequence_type or ''
        }.get(rule.match_type, '')
        
        try:
            return bool(re.match(rule.pattern, value))
        except re.error:
            logger.warning(f"Invalid regex pattern in rule: {rule.pattern}")
            return False
    
    def get_state(self) -> Dict[str, Any]:
        """Get current mapping state for API/debugging."""
        return {
            "rules": [r.to_dict() for r in self.rules],
            "explicit": self.explicit.copy(),
            "default_agent": self.default_agent,
        }


# Global instance
agent_mapping = AgentMappingService()


"""Agent management API endpoints.

Provides endpoints for:
- Managing agent configurations (CRUD)
- Managing inference-agent mappings (rules and explicit)
- Accessing tool call history
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Union
from pathlib import Path
from pydantic import BaseModel

from services.agent_service import (
    AgentConfig, MappingRule, 
    agent_registry, agent_mapping
)
from core.events import event_emitter

router = APIRouter(prefix="/api/agents", tags=["agents"])


# ============================================================================
# Pydantic Models for API
# ============================================================================

class AgentConfigRequest(BaseModel):
    """Request body for creating/updating an agent."""
    id: str
    name: str
    description: str = ""
    llm_model: str = "qwen-plus"
    file_system_enabled: bool = True
    file_system_base_dir: Optional[str] = None
    python_interpreter_enabled: bool = True
    python_interpreter_timeout: int = 30
    user_input_enabled: bool = True
    user_input_mode: str = "blocking"
    paradigm_dir: Optional[str] = None


class AgentConfigResponse(BaseModel):
    """Response for agent configuration."""
    id: str
    name: str
    description: str
    llm_model: str
    file_system_enabled: bool
    file_system_base_dir: Optional[str]
    python_interpreter_enabled: bool
    python_interpreter_timeout: int
    user_input_enabled: bool
    user_input_mode: str
    paradigm_dir: Optional[str]


class MappingRuleRequest(BaseModel):
    """Request body for adding a mapping rule."""
    match_type: str  # 'flow_index', 'concept_name', 'sequence_type'
    pattern: str
    agent_id: str
    priority: int = 0


class ExplicitMappingRequest(BaseModel):
    """Request body for setting explicit mapping."""
    agent_id: str


class ToolCallResponse(BaseModel):
    """Response for a single tool call event."""
    id: str
    timestamp: str
    flow_index: str
    agent_id: str
    tool_name: str
    method: str
    inputs: dict
    outputs: Optional[dict] = None
    duration_ms: Optional[float] = None
    status: str
    error: Optional[str] = None


# ============================================================================
# Agent CRUD Endpoints
# ============================================================================

@router.get("/", response_model=List[AgentConfigResponse])
async def list_agents():
    """List all registered agents."""
    agents = agent_registry.list_agents()
    return [AgentConfigResponse(**a.to_dict()) for a in agents]


@router.get("/{agent_id}", response_model=AgentConfigResponse)
async def get_agent(agent_id: str):
    """Get a specific agent configuration."""
    config = agent_registry.get_config(agent_id)
    if config is None:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return AgentConfigResponse(**config.to_dict())


@router.post("/", response_model=AgentConfigResponse)
async def create_or_update_agent(request: AgentConfigRequest):
    """Create or update an agent configuration."""
    config = AgentConfig(
        id=request.id,
        name=request.name,
        description=request.description,
        llm_model=request.llm_model,
        file_system_enabled=request.file_system_enabled,
        file_system_base_dir=request.file_system_base_dir,
        python_interpreter_enabled=request.python_interpreter_enabled,
        python_interpreter_timeout=request.python_interpreter_timeout,
        user_input_enabled=request.user_input_enabled,
        user_input_mode=request.user_input_mode,
        paradigm_dir=request.paradigm_dir,
    )
    
    is_new = request.id not in agent_registry.configs
    agent_registry.register(config)
    
    # Emit event
    event_type = "agent:registered" if is_new else "agent:updated"
    await event_emitter.emit(event_type, config.to_dict())
    
    return AgentConfigResponse(**config.to_dict())


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent configuration."""
    if agent_id == "default":
        raise HTTPException(status_code=400, detail="Cannot delete default agent")
    
    if not agent_registry.unregister(agent_id):
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    
    # Also remove any explicit mappings to this agent
    flows_to_clear = [
        flow for flow, aid in agent_mapping.explicit.items() 
        if aid == agent_id
    ]
    for flow in flows_to_clear:
        agent_mapping.clear_explicit(flow)
    
    # Remove any rules pointing to this agent
    agent_mapping.rules = [r for r in agent_mapping.rules if r.agent_id != agent_id]
    
    await event_emitter.emit("agent:deleted", {"agent_id": agent_id})
    
    return {"success": True, "message": f"Agent '{agent_id}' deleted"}


# ============================================================================
# Mapping Endpoints
# ============================================================================

@router.get("/mappings/state")
async def get_mapping_state():
    """Get current agent mapping state (rules, explicit assignments, default)."""
    return agent_mapping.get_state()


@router.post("/mappings/rules")
async def add_mapping_rule(request: MappingRuleRequest):
    """Add a mapping rule."""
    # Validate agent exists
    if request.agent_id not in agent_registry.configs:
        raise HTTPException(status_code=400, detail=f"Agent '{request.agent_id}' not found")
    
    rule = MappingRule(
        match_type=request.match_type,
        pattern=request.pattern,
        agent_id=request.agent_id,
        priority=request.priority,
    )
    agent_mapping.add_rule(rule)
    
    await event_emitter.emit("mapping:rule_added", rule.to_dict())
    
    return {"success": True, "rule": rule.to_dict()}


@router.delete("/mappings/rules/{index}")
async def remove_mapping_rule(index: int):
    """Remove a mapping rule by index."""
    if index < 0 or index >= len(agent_mapping.rules):
        raise HTTPException(status_code=404, detail=f"Rule at index {index} not found")
    
    agent_mapping.remove_rule(index)
    
    await event_emitter.emit("mapping:rule_removed", {"index": index})
    
    return {"success": True, "message": f"Rule at index {index} removed"}


@router.delete("/mappings/rules")
async def clear_all_rules():
    """Clear all mapping rules."""
    agent_mapping.clear_rules()
    await event_emitter.emit("mapping:rules_cleared", {})
    return {"success": True, "message": "All rules cleared"}


@router.post("/mappings/explicit/{flow_index}")
async def set_explicit_mapping(flow_index: str, request: ExplicitMappingRequest):
    """Set explicit agent assignment for an inference."""
    # Validate agent exists
    if request.agent_id not in agent_registry.configs:
        raise HTTPException(status_code=400, detail=f"Agent '{request.agent_id}' not found")
    
    agent_mapping.set_explicit(flow_index, request.agent_id)
    
    await event_emitter.emit("mapping:explicit_set", {
        "flow_index": flow_index,
        "agent_id": request.agent_id,
    })
    
    return {
        "success": True, 
        "flow_index": flow_index, 
        "agent_id": request.agent_id
    }


@router.delete("/mappings/explicit/{flow_index}")
async def clear_explicit_mapping(flow_index: str):
    """Remove explicit agent assignment for an inference."""
    agent_mapping.clear_explicit(flow_index)
    
    await event_emitter.emit("mapping:explicit_cleared", {"flow_index": flow_index})
    
    return {"success": True, "flow_index": flow_index}


@router.delete("/mappings/explicit")
async def clear_all_explicit_mappings():
    """Clear all explicit agent assignments."""
    agent_mapping.clear_all_explicit()
    await event_emitter.emit("mapping:explicit_all_cleared", {})
    return {"success": True, "message": "All explicit mappings cleared"}


@router.get("/mappings/resolve/{flow_index}")
async def resolve_agent_for_inference(
    flow_index: str,
    concept_name: Optional[str] = Query(None),
    sequence_type: Optional[str] = Query(None)
):
    """Resolve which agent would handle a specific inference."""
    agent_id = agent_mapping.get_agent_for_inference(
        flow_index, concept_name, sequence_type
    )
    
    # Determine why this agent was selected
    reason = "default"
    if flow_index in agent_mapping.explicit:
        reason = "explicit"
    else:
        for i, rule in enumerate(agent_mapping.rules):
            if agent_mapping._matches_rule(rule, flow_index, concept_name, sequence_type):
                reason = f"rule:{i}"
                break
    
    return {
        "flow_index": flow_index,
        "agent_id": agent_id,
        "reason": reason,
    }


@router.put("/mappings/default")
async def set_default_agent(agent_id: str):
    """Set the default agent for unmapped inferences."""
    if agent_id not in agent_registry.configs:
        raise HTTPException(status_code=400, detail=f"Agent '{agent_id}' not found")
    
    agent_mapping.default_agent = agent_id
    
    await event_emitter.emit("mapping:default_changed", {"agent_id": agent_id})
    
    return {"success": True, "default_agent": agent_id}


# ============================================================================
# Tool Call History Endpoints
# ============================================================================

@router.get("/tool-calls", response_model=List[ToolCallResponse])
async def get_tool_calls(limit: int = Query(100, ge=1, le=1000)):
    """Get recent tool call events."""
    history = agent_registry.get_tool_call_history(limit)
    return [ToolCallResponse(**h) for h in history]


@router.delete("/tool-calls")
async def clear_tool_calls():
    """Clear tool call history."""
    agent_registry.clear_tool_call_history()
    await event_emitter.emit("tool_calls:cleared", {})
    return {"success": True, "message": "Tool call history cleared"}


# ============================================================================
# Agent Capabilities Endpoints
# ============================================================================

class ToolInfo(BaseModel):
    """Information about a tool."""
    name: str
    enabled: bool
    methods: List[str]
    description: str = ""


class ParadigmInfo(BaseModel):
    """Information about a paradigm."""
    name: str
    description: str = ""
    vertical_inputs: Union[dict, str] = {}  # Can be dict or string description
    horizontal_inputs: Union[dict, str] = {}  # Can be dict or string description
    is_custom: bool = False
    source: str = ""


class SequenceInfo(BaseModel):
    """Information about an inference sequence."""
    name: str
    description: str = ""
    category: str = ""  # e.g., "core", "python", "composition", "input"


class AgentCapabilitiesResponse(BaseModel):
    """Response for agent capabilities."""
    agent_id: str
    tools: List[ToolInfo]
    paradigms: List[ParadigmInfo]
    sequences: List[SequenceInfo]
    paradigm_dir: Optional[str]
    agent_frame_model: str = "demo"


def _get_tool_methods(tool_name: str) -> List[str]:
    """Get available methods for a tool type."""
    tool_methods = {
        "llm": ["query", "generate", "chat", "get_response"],
        "file_system": ["read", "write", "list_directory", "append", "delete", "exists"],
        "python_interpreter": ["execute", "function_execute", "create_function_executor"],
        "user_input": ["ask", "ask_for_confirmation", "ask_for_file_path"],
        "prompt_tool": ["retrieve", "get_template", "format"],
        "paradigm_tool": ["load", "list_manifest"],
        "composition_tool": ["compose"],
        "formatter_tool": ["get", "wrap", "collect_script_inputs"],
        "perception_router": ["strip_sign", "route"],
    }
    return tool_methods.get(tool_name, [])


def _get_available_sequences(agent_frame_model: str = "demo") -> List[dict]:
    """Get available inference sequences based on the AgentFrameModel.
    
    Based on infra/_agent/_agentframe.py
    """
    # All sequences with metadata
    all_sequences = {
        # Core sequences
        "simple": {
            "description": "Basic value passing without transformation",
            "category": "core",
        },
        "grouping": {
            "description": "Group multiple values together",
            "category": "core",
        },
        "quantifying": {
            "description": "Quantify or measure values",
            "category": "core",
        },
        "looping": {
            "description": "Iterate over collections",
            "category": "core",
        },
        "assigning": {
            "description": "Assign values to targets",
            "category": "core",
        },
        "timing": {
            "description": "Timing and scheduling operations",
            "category": "core",
        },
        
        # LLM-based sequences
        "imperative": {
            "description": "LLM generates structured output from prompt",
            "category": "llm",
        },
        "judgement": {
            "description": "LLM makes decisions/judgements",
            "category": "llm",
        },
        "imperative_direct": {
            "description": "Direct imperative without template",
            "category": "llm",
        },
        "judgement_direct": {
            "description": "Direct judgement without template",
            "category": "llm",
        },
        
        # Python execution sequences
        "imperative_python": {
            "description": "Execute Python script for imperative tasks",
            "category": "python",
        },
        "judgement_python": {
            "description": "Execute Python script for judgement tasks",
            "category": "python",
        },
        "imperative_python_indirect": {
            "description": "Indirect Python execution for imperative tasks",
            "category": "python",
        },
        "judgement_python_indirect": {
            "description": "Indirect Python execution for judgement tasks",
            "category": "python",
        },
        
        # Composition-based sequences
        "imperative_in_composition": {
            "description": "Imperative via composition tool with paradigms",
            "category": "composition",
        },
        "judgement_in_composition": {
            "description": "Judgement via composition tool with paradigms",
            "category": "composition",
        },
        
        # Input sequences
        "imperative_input": {
            "description": "Get user input for imperative tasks",
            "category": "input",
        },
    }
    
    # Which sequences are available for each model
    model_sequences = {
        "demo": [
            "simple", "imperative", "grouping", "quantifying", "looping", 
            "assigning", "timing", "judgement", "imperative_direct", 
            "imperative_input", "judgement_direct", "imperative_python",
            "judgement_python", "imperative_python_indirect", 
            "judgement_python_indirect", "imperative_in_composition",
            "judgement_in_composition"
        ],
        "composition": [
            "simple", "imperative", "judgement", "grouping", "quantifying",
            "looping", "assigning", "timing"
        ],
    }
    
    available = model_sequences.get(agent_frame_model, model_sequences["demo"])
    
    result = []
    for seq_name in available:
        seq_info = all_sequences.get(seq_name, {})
        result.append({
            "name": seq_name,
            "description": seq_info.get("description", ""),
            "category": seq_info.get("category", "other"),
        })
    
    return result


def _list_paradigms_from_dir(paradigm_dir: Optional[str]) -> List[dict]:
    """List paradigms from a directory.
    
    Prioritizes custom paradigm directory over default, showing custom paradigms first.
    """
    import os
    import json
    
    paradigms = []
    seen_names = set()
    
    # First scan custom paradigm directory (these take priority)
    if paradigm_dir:
        custom_path = Path(paradigm_dir)
        if custom_path.exists() and custom_path.is_dir():
            for filename in sorted(os.listdir(custom_path)):
                if not filename.endswith(".json"):
                    continue
                seen_names.add(filename)
                
                name = filename[:-5]  # Remove .json
                filepath = custom_path / filename
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    metadata = data.get("metadata", {})
                    paradigms.append({
                        "name": name,
                        "description": metadata.get("description", ""),
                        "vertical_inputs": metadata.get("inputs", {}).get("vertical", {}),
                        "horizontal_inputs": metadata.get("inputs", {}).get("horizontal", {}),
                        "is_custom": True,
                        "source": str(custom_path),
                    })
                except Exception as e:
                    paradigms.append({
                        "name": name,
                        "description": f"Error loading: {str(e)}",
                        "vertical_inputs": {},
                        "horizontal_inputs": {},
                        "is_custom": True,
                        "source": str(custom_path),
                    })
    
    # Then scan default paradigms directory (if not already seen)
    try:
        from infra._agent._models._paradigms import PARADIGMS_DIR
        if os.path.isdir(PARADIGMS_DIR):
            for filename in sorted(os.listdir(PARADIGMS_DIR)):
                if not filename.endswith(".json"):
                    continue
                if filename in seen_names:
                    continue  # Skip if custom version exists
                
                name = filename[:-5]
                filepath = os.path.join(PARADIGMS_DIR, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    metadata = data.get("metadata", {})
                    paradigms.append({
                        "name": name,
                        "description": metadata.get("description", ""),
                        "vertical_inputs": metadata.get("inputs", {}).get("vertical", {}),
                        "horizontal_inputs": metadata.get("inputs", {}).get("horizontal", {}),
                        "is_custom": False,
                        "source": str(PARADIGMS_DIR),
                    })
                except Exception as e:
                    paradigms.append({
                        "name": name,
                        "description": f"Error loading: {str(e)}",
                        "vertical_inputs": {},
                        "horizontal_inputs": {},
                        "is_custom": False,
                        "source": str(PARADIGMS_DIR),
                    })
    except ImportError:
        pass
    
    return paradigms


@router.get("/{agent_id}/capabilities", response_model=AgentCapabilitiesResponse)
async def get_agent_capabilities(agent_id: str):
    """Get the tools and paradigms available to an agent."""
    if agent_id not in agent_registry.configs:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    
    config = agent_registry.configs[agent_id]
    
    # Get effective paradigm_dir - check agent config first, then project config
    effective_paradigm_dir = config.paradigm_dir
    
    # If agent doesn't have a paradigm_dir, try to get from execution controller
    if not effective_paradigm_dir:
        try:
            from services.execution_service import execution_controller
            if execution_controller._load_config:
                project_paradigm_dir = execution_controller._load_config.get("paradigm_dir")
                project_base_dir = execution_controller._load_config.get("base_dir")
                if project_paradigm_dir:
                    # Resolve relative path
                    paradigm_path = Path(project_paradigm_dir)
                    if not paradigm_path.is_absolute() and project_base_dir:
                        paradigm_path = Path(project_base_dir) / project_paradigm_dir
                    if paradigm_path.exists():
                        effective_paradigm_dir = str(paradigm_path)
        except Exception:
            pass  # Fall back to just agent config
    
    # Build tools list based on config
    tools = []
    
    # LLM is always available
    tools.append(ToolInfo(
        name="llm",
        enabled=True,
        methods=_get_tool_methods("llm"),
        description=f"Language model ({config.llm_model})"
    ))
    
    # File system
    tools.append(ToolInfo(
        name="file_system",
        enabled=config.file_system_enabled,
        methods=_get_tool_methods("file_system"),
        description=f"File operations{f' (base: {config.file_system_base_dir})' if config.file_system_base_dir else ''}"
    ))
    
    # Python interpreter
    tools.append(ToolInfo(
        name="python_interpreter",
        enabled=config.python_interpreter_enabled,
        methods=_get_tool_methods("python_interpreter"),
        description=f"Execute Python code (timeout: {config.python_interpreter_timeout}s)"
    ))
    
    # User input
    tools.append(ToolInfo(
        name="user_input",
        enabled=config.user_input_enabled,
        methods=_get_tool_methods("user_input"),
        description=f"User prompts ({config.user_input_mode} mode)"
    ))
    
    # Internal tools (always available)
    tools.append(ToolInfo(
        name="prompt_tool",
        enabled=True,
        methods=_get_tool_methods("prompt_tool"),
        description="Prompt template retrieval"
    ))
    
    tools.append(ToolInfo(
        name="paradigm_tool",
        enabled=True,
        methods=_get_tool_methods("paradigm_tool"),
        description="Paradigm loading"
    ))
    
    tools.append(ToolInfo(
        name="composition_tool",
        enabled=True,
        methods=_get_tool_methods("composition_tool"),
        description="Function composition"
    ))
    
    tools.append(ToolInfo(
        name="formatter_tool",
        enabled=True,
        methods=_get_tool_methods("formatter_tool"),
        description="Data formatting utilities"
    ))
    
    tools.append(ToolInfo(
        name="perception_router",
        enabled=True,
        methods=_get_tool_methods("perception_router"),
        description="Perceptual sign routing"
    ))
    
    # Get paradigms from effective paradigm directory
    paradigms_data = _list_paradigms_from_dir(effective_paradigm_dir)
    paradigms = [ParadigmInfo(**p) for p in paradigms_data]
    
    # Determine AgentFrameModel - default to "demo", but check execution controller
    agent_frame_model = "demo"
    try:
        from services.execution_service import execution_controller
        if execution_controller.body and hasattr(execution_controller.body, 'agent_frame'):
            af = execution_controller.body.agent_frame
            if hasattr(af, 'AgentFrameModel'):
                agent_frame_model = af.AgentFrameModel
    except Exception:
        pass
    
    # Get available sequences
    sequences_data = _get_available_sequences(agent_frame_model)
    sequences = [SequenceInfo(**s) for s in sequences_data]
    
    return AgentCapabilitiesResponse(
        agent_id=agent_id,
        tools=tools,
        paradigms=paradigms,
        sequences=sequences,
        paradigm_dir=effective_paradigm_dir,
        agent_frame_model=agent_frame_model
    )


# ============================================================================
# Utility Endpoints
# ============================================================================

@router.post("/invalidate-bodies")
async def invalidate_all_bodies():
    """Invalidate all cached Body instances (force recreation on next use)."""
    agent_registry.invalidate_all_bodies()
    return {"success": True, "message": "All body instances invalidated"}


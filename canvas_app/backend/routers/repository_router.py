"""Repository management endpoints."""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from pydantic import BaseModel

from services.graph_service import graph_service
from services.execution_service import execution_controller, get_execution_controller
from schemas.execution_schemas import LoadRepositoryRequest

router = APIRouter()


class RepositoryInfo(BaseModel):
    """Information about a repository set."""
    name: str
    concepts_path: str
    inferences_path: str
    inputs_path: Optional[str] = None


class LoadResponse(BaseModel):
    """Response after loading repositories."""
    success: bool
    message: str
    run_id: Optional[str] = None
    total_inferences: int = 0
    concepts_count: int = 0


@router.post("/load", response_model=LoadResponse)
async def load_repositories(request: LoadRepositoryRequest):
    """Load concept and inference repository files."""
    try:
        # Validate paths exist
        concepts_path = Path(request.concepts_path)
        inferences_path = Path(request.inferences_path)
        
        if not concepts_path.exists():
            raise HTTPException(status_code=404, detail=f"Concepts file not found: {request.concepts_path}")
        if not inferences_path.exists():
            raise HTTPException(status_code=404, detail=f"Inferences file not found: {request.inferences_path}")
        
        if request.inputs_path:
            inputs_path = Path(request.inputs_path)
            if not inputs_path.exists():
                raise HTTPException(status_code=404, detail=f"Inputs file not found: {request.inputs_path}")
        
        # Load graph for visualization
        graph_service.load_from_files(
            str(concepts_path),
            str(inferences_path)
        )
        
        # Load into execution controller (agent-centric approach)
        result = await execution_controller.load_repositories(
            concepts_path=str(concepts_path),
            inferences_path=str(inferences_path),
            inputs_path=request.inputs_path,
            llm_model=request.llm_model,  # Backward compat
            base_dir=request.base_dir,
            max_cycles=request.max_cycles,
            db_path=request.db_path,
            paradigm_dir=request.paradigm_dir,
            agent_config=request.agent_config,
            project_dir=request.project_dir,
            project_name=request.project_name,
        )
        
        return LoadResponse(
            success=True,
            message="Repositories loaded successfully",
            run_id=result.get("run_id"),
            total_inferences=result.get("total_inferences", 0),
            concepts_count=result.get("concepts_count", 0),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/examples")
async def list_example_repositories():
    """List available example repository sets."""
    # Look for example repositories in the project
    project_root = Path(__file__).parent.parent.parent.parent
    examples_dir = project_root / "streamlit_app" / "repository_sets"
    
    examples = []
    if examples_dir.exists():
        for subdir in examples_dir.iterdir():
            if subdir.is_dir():
                concept_file = subdir / "concept_repo.json"
                inference_file = subdir / "inference_repo.json"
                if concept_file.exists() and inference_file.exists():
                    examples.append({
                        "name": subdir.name,
                        "concepts_path": str(concept_file),
                        "inferences_path": str(inference_file),
                    })
    
    return {"examples": examples}


# =============================================================================
# Repository Preview - Simple viewer for concept/inference JSON files
# =============================================================================

class RepoPreviewRequest(BaseModel):
    """Request to preview a repository file."""
    file_path: str


class ConceptPreview(BaseModel):
    """Preview data for a single concept."""
    id: str
    concept_name: str
    type: str
    flow_indices: List[str]
    description: Optional[str] = None
    natural_name: Optional[str] = None
    is_ground_concept: bool = False
    is_final_concept: bool = False
    is_invariant: bool = False
    reference_data: Optional[Any] = None
    reference_axis_names: List[str] = []


class InferencePreview(BaseModel):
    """Preview data for a single inference."""
    flow_index: str
    inference_sequence: str
    concept_to_infer: str
    function_concept: str
    value_concepts: List[str] = []
    context_concepts: List[str] = []
    working_interpretation: Optional[Dict[str, Any]] = None


class RepoPreviewResponse(BaseModel):
    """Response for repository preview."""
    success: bool
    file_path: str
    file_type: str  # 'concept' or 'inference'
    item_count: int
    concepts: Optional[List[ConceptPreview]] = None
    inferences: Optional[List[InferencePreview]] = None
    error: Optional[str] = None


def detect_repo_type(data: List[Dict[str, Any]]) -> str:
    """Detect whether the file is a concept or inference repository."""
    if not data:
        return "unknown"
    
    first_item = data[0]
    
    # Concept repos have concept_name and type fields
    if "concept_name" in first_item and "type" in first_item:
        return "concept"
    
    # Inference repos have flow_info and inference_sequence
    if "flow_info" in first_item or "inference_sequence" in first_item:
        return "inference"
    
    return "unknown"


def parse_concepts(data: List[Dict[str, Any]]) -> List[ConceptPreview]:
    """Parse concept repository data into preview format."""
    concepts = []
    for item in data:
        concepts.append(ConceptPreview(
            id=item.get("id", ""),
            concept_name=item.get("concept_name", ""),
            type=item.get("type", ""),
            flow_indices=item.get("flow_indices", []),
            description=item.get("description"),
            natural_name=item.get("natural_name"),
            is_ground_concept=item.get("is_ground_concept", False),
            is_final_concept=item.get("is_final_concept", False),
            is_invariant=item.get("is_invariant", False),
            reference_data=item.get("reference_data"),
            reference_axis_names=item.get("reference_axis_names", []),
        ))
    return concepts


def parse_inferences(data: List[Dict[str, Any]]) -> List[InferencePreview]:
    """Parse inference repository data into preview format."""
    inferences = []
    for item in data:
        # flow_index can be in flow_info dict or directly on item
        flow_info = item.get("flow_info", {})
        flow_index = flow_info.get("flow_index", "") if isinstance(flow_info, dict) else str(flow_info)
        
        inferences.append(InferencePreview(
            flow_index=flow_index,
            inference_sequence=item.get("inference_sequence", ""),
            concept_to_infer=item.get("concept_to_infer", ""),
            function_concept=item.get("function_concept", ""),
            value_concepts=item.get("value_concepts", []),
            context_concepts=item.get("context_concepts", []),
            working_interpretation=item.get("working_interpretation"),
        ))
    return inferences


@router.post("/preview", response_model=RepoPreviewResponse)
async def preview_repository(request: RepoPreviewRequest):
    """
    Preview a concept or inference repository file.
    
    Returns structured data for easy viewing without loading into execution.
    Automatically detects whether the file is a concept or inference repo.
    """
    try:
        file_path = Path(request.file_path)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")
        
        if not file_path.suffix.lower() == ".json":
            raise HTTPException(status_code=400, detail="Only JSON files are supported")
        
        # Load and parse the JSON file
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            raise HTTPException(status_code=400, detail="Repository file must contain a JSON array")
        
        # Detect file type
        file_type = detect_repo_type(data)
        
        if file_type == "concept":
            concepts = parse_concepts(data)
            return RepoPreviewResponse(
                success=True,
                file_path=str(file_path),
                file_type="concept",
                item_count=len(concepts),
                concepts=concepts,
            )
        elif file_type == "inference":
            inferences = parse_inferences(data)
            return RepoPreviewResponse(
                success=True,
                file_path=str(file_path),
                file_type="inference",
                item_count=len(inferences),
                inferences=inferences,
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail="Could not detect repository type. File must be a concept or inference repository."
            )
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Project Config Preview - Viewer for .normcode-canvas.json project files
# =============================================================================

class ProjectPreviewRequest(BaseModel):
    """Request to preview a project config file."""
    file_path: str


class RepositoriesConfig(BaseModel):
    """Repository paths in the project config."""
    concepts: Optional[str] = None
    inferences: Optional[str] = None
    inputs: Optional[str] = None


class ExecutionConfig(BaseModel):
    """Execution settings in the project config."""
    llm_model: Optional[str] = None
    max_cycles: Optional[int] = None
    db_path: Optional[str] = None
    base_dir: Optional[str] = None
    paradigm_dir: Optional[str] = None
    agent_config: Optional[str] = None


class ProjectPreview(BaseModel):
    """Preview data for a project config."""
    id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    repositories: RepositoriesConfig
    execution: ExecutionConfig
    breakpoints: List[str] = []
    ui_preferences: Dict[str, Any] = {}


class ProjectPreviewResponse(BaseModel):
    """Response for project config preview."""
    success: bool
    file_path: str
    project: Optional[ProjectPreview] = None
    error: Optional[str] = None


@router.post("/preview-project", response_model=ProjectPreviewResponse)
async def preview_project_config(request: ProjectPreviewRequest):
    """
    Preview a NormCode Canvas project configuration file.
    
    Returns structured data for easy viewing of project settings.
    """
    try:
        file_path = Path(request.file_path)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")
        
        if not file_path.suffix.lower() == ".json":
            raise HTTPException(status_code=400, detail="Only JSON files are supported")
        
        # Load and parse the JSON file
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, dict):
            raise HTTPException(status_code=400, detail="Project config must be a JSON object")
        
        # Validate this is a project config file
        if "repositories" not in data or "execution" not in data:
            raise HTTPException(
                status_code=400, 
                detail="Not a valid project config. Must contain 'repositories' and 'execution' fields."
            )
        
        # Parse repositories config
        repos_data = data.get("repositories", {})
        repositories = RepositoriesConfig(
            concepts=repos_data.get("concepts"),
            inferences=repos_data.get("inferences"),
            inputs=repos_data.get("inputs"),
        )
        
        # Parse execution config
        exec_data = data.get("execution", {})
        execution = ExecutionConfig(
            llm_model=exec_data.get("llm_model"),
            max_cycles=exec_data.get("max_cycles"),
            db_path=exec_data.get("db_path"),
            base_dir=exec_data.get("base_dir"),
            paradigm_dir=exec_data.get("paradigm_dir"),
            agent_config=exec_data.get("agent_config"),
        )
        
        # Build project preview
        project = ProjectPreview(
            id=data.get("id", ""),
            name=data.get("name", file_path.stem),
            description=data.get("description"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            repositories=repositories,
            execution=execution,
            breakpoints=data.get("breakpoints", []),
            ui_preferences=data.get("ui_preferences", {}),
        )
        
        return ProjectPreviewResponse(
            success=True,
            file_path=str(file_path),
            project=project,
        )
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Agent Config Preview - Viewer for .agent.json files
# =============================================================================

class AgentPreviewRequest(BaseModel):
    """Request to preview an agent config file."""
    file_path: str


class LLMToolConfig(BaseModel):
    """LLM tool configuration."""
    model: str = "demo"
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class ParadigmToolConfig(BaseModel):
    """Paradigm tool configuration."""
    dir: Optional[str] = None


class FileSystemToolConfig(BaseModel):
    """File system tool configuration."""
    enabled: bool = True
    base_dir: Optional[str] = None


class PythonInterpreterToolConfig(BaseModel):
    """Python interpreter tool configuration."""
    enabled: bool = True
    timeout: int = 30


class UserInputToolConfig(BaseModel):
    """User input tool configuration."""
    enabled: bool = True
    mode: str = "blocking"


class AgentToolsConfig(BaseModel):
    """Tools configuration for an agent."""
    llm: LLMToolConfig = LLMToolConfig()
    paradigm: ParadigmToolConfig = ParadigmToolConfig()
    file_system: FileSystemToolConfig = FileSystemToolConfig()
    python_interpreter: PythonInterpreterToolConfig = PythonInterpreterToolConfig()
    user_input: UserInputToolConfig = UserInputToolConfig()


class AgentDefinition(BaseModel):
    """Single agent definition - supports both new and legacy formats."""
    id: str
    name: str
    description: Optional[str] = None
    # New tool-centric format
    tools: Optional[AgentToolsConfig] = None
    # Legacy flat fields (for backwards compatibility)
    llm_model: Optional[str] = None
    file_system_enabled: bool = False
    file_system_base_dir: Optional[str] = None
    python_interpreter_enabled: bool = False
    python_interpreter_timeout: int = 30
    user_input_enabled: bool = False
    user_input_mode: str = "disabled"
    paradigm_dir: Optional[str] = None


class AgentMapping(BaseModel):
    """Agent routing rule."""
    match_type: str
    pattern: str
    agent_id: str
    priority: int = 0


class LLMProvider(BaseModel):
    """LLM provider configuration."""
    provider_name: str
    provider_type: str
    model: str
    api_key: Optional[str] = None


class AgentConfigPreview(BaseModel):
    """Preview data for an agent config."""
    description: Optional[str] = None
    default_agent: Optional[str] = None
    agents: List[AgentDefinition] = []
    mappings: List[AgentMapping] = []
    llm_providers: List[LLMProvider] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AgentPreviewResponse(BaseModel):
    """Response for agent config preview."""
    success: bool
    file_path: str
    config: Optional[AgentConfigPreview] = None
    error: Optional[str] = None


@router.post("/preview-agent", response_model=AgentPreviewResponse)
async def preview_agent_config(request: AgentPreviewRequest):
    """
    Preview an agent configuration file.
    
    Returns structured data for easy viewing of agent settings.
    """
    try:
        file_path = Path(request.file_path)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")
        
        if not file_path.suffix.lower() == ".json":
            raise HTTPException(status_code=400, detail="Only JSON files are supported")
        
        # Load and parse the JSON file
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, dict):
            raise HTTPException(status_code=400, detail="Agent config must be a JSON object")
        
        # Parse agents - support both new tool-centric and legacy format
        agents = []
        for agent_data in data.get("agents", []):
            tools_data = agent_data.get("tools")
            
            if tools_data:
                # New tool-centric format
                llm_data = tools_data.get("llm", {})
                paradigm_data = tools_data.get("paradigm", {})
                fs_data = tools_data.get("file_system", {})
                python_data = tools_data.get("python_interpreter", {})
                user_input_data = tools_data.get("user_input", {})
                
                tools_config = AgentToolsConfig(
                    llm=LLMToolConfig(
                        model=llm_data.get("model", "demo"),
                        temperature=llm_data.get("temperature"),
                        max_tokens=llm_data.get("max_tokens"),
                    ),
                    paradigm=ParadigmToolConfig(
                        dir=paradigm_data.get("dir"),
                    ),
                    file_system=FileSystemToolConfig(
                        enabled=fs_data.get("enabled", True),
                        base_dir=fs_data.get("base_dir"),
                    ),
                    python_interpreter=PythonInterpreterToolConfig(
                        enabled=python_data.get("enabled", True),
                        timeout=python_data.get("timeout", 30),
                    ),
                    user_input=UserInputToolConfig(
                        enabled=user_input_data.get("enabled", True),
                        mode=user_input_data.get("mode", "blocking"),
                    ),
                )
                
                agents.append(AgentDefinition(
                    id=agent_data.get("id", ""),
                    name=agent_data.get("name", ""),
                    description=agent_data.get("description"),
                    tools=tools_config,
                ))
            else:
                # Legacy flat format
                agents.append(AgentDefinition(
                    id=agent_data.get("id", ""),
                    name=agent_data.get("name", ""),
                    description=agent_data.get("description"),
                    llm_model=agent_data.get("llm_model"),
                    file_system_enabled=agent_data.get("file_system_enabled", False),
                    file_system_base_dir=agent_data.get("file_system_base_dir"),
                    python_interpreter_enabled=agent_data.get("python_interpreter_enabled", False),
                    python_interpreter_timeout=agent_data.get("python_interpreter_timeout", 30),
                    user_input_enabled=agent_data.get("user_input_enabled", False),
                    user_input_mode=agent_data.get("user_input_mode", "disabled"),
                    paradigm_dir=agent_data.get("paradigm_dir"),
                ))
        
        # Parse mappings
        mappings = []
        for mapping_data in data.get("mappings", []):
            mappings.append(AgentMapping(
                match_type=mapping_data.get("match_type", ""),
                pattern=mapping_data.get("pattern", ""),
                agent_id=mapping_data.get("agent_id", ""),
                priority=mapping_data.get("priority", 0),
            ))
        
        # Parse LLM providers
        llm_providers = []
        for provider_data in data.get("llm_providers", []):
            llm_providers.append(LLMProvider(
                provider_name=provider_data.get("provider_name", ""),
                provider_type=provider_data.get("provider_type", ""),
                model=provider_data.get("model", ""),
                api_key=provider_data.get("api_key"),
            ))
        
        # Build config preview
        config = AgentConfigPreview(
            description=data.get("description"),
            default_agent=data.get("default_agent"),
            agents=agents,
            mappings=mappings,
            llm_providers=llm_providers,
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
        
        return AgentPreviewResponse(
            success=True,
            file_path=str(file_path),
            config=config,
        )
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

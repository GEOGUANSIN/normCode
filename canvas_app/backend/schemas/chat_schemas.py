"""
Chat schemas for the compiler-driven chat interface.

These models define the structure for chat messages, input requests,
and compiler project state for the self-hosted NormCode compiler.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Chat Message Types
# ============================================================================

class MessageRole(str, Enum):
    """Roles for chat messages."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    COMPILER = "compiler"
    CONTROLLER = "controller"


class ChatMessage(BaseModel):
    """A single chat message."""
    id: str
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CodeBlock(BaseModel):
    """A code block embedded in chat."""
    id: str
    language: str
    code: str
    title: Optional[str] = None
    collapsible: bool = False


class ChatArtifact(BaseModel):
    """A structured artifact displayed in chat."""
    id: str
    type: str  # 'code', 'json', 'table', 'tree', 'graph-preview'
    data: Any
    title: Optional[str] = None


# ============================================================================
# Chat Input Requests (from compiler to user)
# ============================================================================

class ChatInputType(str, Enum):
    """Types of input the compiler can request."""
    TEXT = "text"
    CODE = "code"
    CONFIRM = "confirm"
    SELECT = "select"


class ChatInputRequest(BaseModel):
    """A request for user input from the compiler."""
    id: str
    prompt: str
    input_type: ChatInputType = ChatInputType.TEXT
    options: Optional[List[str]] = None  # For SELECT type
    placeholder: Optional[str] = None
    initial_value: Optional[str] = None  # For CODE type


class ChatInputResponse(BaseModel):
    """User's response to an input request."""
    request_id: str
    value: str


# ============================================================================
# Compiler Project State
# ============================================================================

class CompilerStatus(str, Enum):
    """Status of the compiler meta project."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RUNNING = "running"
    ERROR = "error"


class CompilerProjectInfo(BaseModel):
    """Information about the compiler meta project."""
    project_id: Optional[str] = None
    project_name: str = "NormCode Compiler"
    status: CompilerStatus = CompilerStatus.DISCONNECTED
    is_loaded: bool = False
    is_read_only: bool = True  # Meta project is always read-only
    current_step: Optional[str] = None
    error_message: Optional[str] = None


# ============================================================================
# API Request/Response Models
# ============================================================================

class SendMessageRequest(BaseModel):
    """Request to send a message to the compiler."""
    content: str
    metadata: Optional[Dict[str, Any]] = None


class SendMessageResponse(BaseModel):
    """Response after sending a message."""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class GetMessagesResponse(BaseModel):
    """Response containing chat history."""
    messages: List[ChatMessage]
    has_more: bool = False
    total_count: int = 0


class CompilerStateResponse(BaseModel):
    """Response containing compiler project state."""
    compiler: CompilerProjectInfo
    pending_input: Optional[ChatInputRequest] = None


class StartCompilerRequest(BaseModel):
    """Request to start/connect the compiler meta project."""
    auto_run: bool = True  # Whether to auto-start execution


class StartCompilerResponse(BaseModel):
    """Response after starting the compiler."""
    success: bool
    project_id: Optional[str] = None
    project_path: Optional[str] = None
    project_config_file: Optional[str] = None
    status: CompilerStatus = CompilerStatus.DISCONNECTED
    error: Optional[str] = None


# ============================================================================
# WebSocket Event Types
# ============================================================================

class ChatEventType(str, Enum):
    """Types of chat-related WebSocket events."""
    # Outgoing (backend -> frontend)
    MESSAGE = "chat:message"
    CODE_BLOCK = "chat:code_block"
    ARTIFACT = "chat:artifact"
    INPUT_REQUEST = "chat:input_request"
    COMPILER_STATUS = "chat:compiler_status"
    COMPILER_STEP = "chat:compiler_step"
    
    # Incoming (frontend -> backend)
    USER_INPUT = "chat:user_input"
    CANCEL_INPUT = "chat:cancel_input"


class ChatEvent(BaseModel):
    """A WebSocket event for chat."""
    type: ChatEventType
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


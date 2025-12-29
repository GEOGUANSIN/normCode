"""
Chat Router - REST API endpoints for the chat controller interface.

Provides endpoints for:
- Listing and selecting chat controllers
- Sending messages to the controller
- Getting chat history
- Managing controller execution state
- Responding to input requests
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.chat_controller_service import get_chat_controller_service, ControllerStatus
from schemas.chat_schemas import (
    ChatMessage,
    SendMessageRequest,
    SendMessageResponse,
    GetMessagesResponse,
    ChatInputRequest,
    ChatInputResponse,
    CompilerStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat")


# ============================================================================
# New Models for Controller Selection
# ============================================================================

class ControllerInfo(BaseModel):
    """Information about an available chat controller."""
    project_id: str
    name: str
    path: str
    config_file: Optional[str] = None
    description: Optional[str] = None
    is_builtin: bool = False


class ControllersListResponse(BaseModel):
    """Response containing available controllers."""
    controllers: List[ControllerInfo]
    current_controller_id: Optional[str] = None


class SelectControllerRequest(BaseModel):
    """Request to select a chat controller."""
    controller_id: str


class ControllerStateResponse(BaseModel):
    """Response containing current controller state."""
    controller_id: Optional[str] = None
    controller_name: Optional[str] = None
    controller_path: Optional[str] = None
    status: str = "disconnected"
    current_flow_index: Optional[str] = None
    error_message: Optional[str] = None
    pending_input: Optional[ChatInputRequest] = None
    is_execution_active: bool = False


class StartControllerRequest(BaseModel):
    """Request to start the controller."""
    auto_run: bool = True


class StartControllerResponse(BaseModel):
    """Response after starting the controller."""
    success: bool
    controller_id: Optional[str] = None
    controller_name: Optional[str] = None
    controller_path: Optional[str] = None
    status: str = "disconnected"
    error: Optional[str] = None


# ============================================================================
# Controller Management
# ============================================================================

@router.get("/controllers", response_model=ControllersListResponse)
async def list_controllers(refresh: bool = False):
    """
    List all available chat controller projects.
    
    Args:
        refresh: Force rescan of available controllers
        
    Returns:
        List of available controllers and current selection
    """
    service = get_chat_controller_service()
    controllers = service.get_available_controllers(refresh=refresh)
    
    return ControllersListResponse(
        controllers=[ControllerInfo(**c) for c in controllers],
        current_controller_id=service._controller_id,
    )


@router.post("/controllers/select", response_model=ControllerStateResponse)
async def select_controller(request: SelectControllerRequest):
    """
    Select a chat controller project.
    
    This connects to the specified controller and prepares it for execution.
    
    Args:
        request: Controller selection request
        
    Returns:
        New controller state
    """
    service = get_chat_controller_service()
    
    try:
        state = await service.select_controller(request.controller_id)
        return _state_to_response(state)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to select controller: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/controllers/register")
async def register_controller(
    project_id: str,
    name: str,
    path: str,
    config_file: Optional[str] = None,
    description: Optional[str] = None,
):
    """
    Register a new chat controller project.
    
    This allows dynamically adding chat-capable projects as controllers.
    """
    service = get_chat_controller_service()
    
    info = service.register_controller(
        project_id=project_id,
        name=name,
        path=path,
        config_file=config_file,
        description=description,
    )
    
    return {"success": True, "controller": info.to_dict()}


# ============================================================================
# Controller State & Lifecycle
# ============================================================================

@router.get("/state", response_model=ControllerStateResponse)
async def get_controller_state():
    """
    Get the current state of the chat controller.
    
    Returns:
        Controller info and any pending input request
    """
    service = get_chat_controller_service()
    state = service.get_state()
    return _state_to_response(state)


def _state_to_response(state: dict) -> ControllerStateResponse:
    """Convert service state dict to response model."""
    controller_info = state.get("controller_info") or {}
    pending = state.get("pending_input")
    
    pending_request = None
    if pending:
        pending_request = ChatInputRequest(
            id=pending.get("id"),
            prompt=pending.get("prompt"),
            input_type=pending.get("input_type", "text"),
            options=pending.get("options"),
            placeholder=pending.get("placeholder"),
        )
    
    return ControllerStateResponse(
        controller_id=state.get("controller_id"),
        controller_name=controller_info.get("name"),
        controller_path=controller_info.get("path"),
        status=state.get("status", "disconnected"),
        current_flow_index=state.get("current_flow_index"),
        error_message=state.get("error_message"),
        pending_input=pending_request,
        is_execution_active=state.get("is_execution_active", False),
    )


@router.post("/start", response_model=StartControllerResponse)
async def start_controller(request: StartControllerRequest = StartControllerRequest()):
    """
    Start/connect the chat controller.
    
    If no controller is selected, uses the default (compiler).
    
    Returns:
        Controller start result with status
    """
    service = get_chat_controller_service()
    
    try:
        state = await service.start()
        controller_info = state.get("controller_info") or {}
        
        return StartControllerResponse(
            success=True,
            controller_id=state.get("controller_id"),
            controller_name=controller_info.get("name"),
            controller_path=controller_info.get("path"),
            status=state.get("status", "connected"),
        )
        
    except Exception as e:
        logger.error(f"Failed to start controller: {e}")
        return StartControllerResponse(
            success=False,
            status="error",
            error=str(e),
        )


@router.post("/pause")
async def pause_controller():
    """Pause the controller execution."""
    service = get_chat_controller_service()
    await service.pause()
    return {"success": True, "status": "paused"}


@router.post("/resume")
async def resume_controller():
    """Resume paused controller execution."""
    service = get_chat_controller_service()
    await service.resume()
    return {"success": True, "status": "running"}


@router.post("/stop")
async def stop_controller():
    """
    Stop the controller execution (but keep it connected).
    
    Returns:
        Success status
    """
    service = get_chat_controller_service()
    await service.stop()
    return {"success": True, "status": "connected"}


@router.post("/disconnect")
async def disconnect_controller():
    """
    Disconnect the controller completely.
    
    Returns:
        Success status
    """
    service = get_chat_controller_service()
    await service.disconnect()
    return {"success": True, "status": "disconnected"}


# ============================================================================
# Messages
# ============================================================================

@router.get("/messages", response_model=GetMessagesResponse)
async def get_messages(limit: int = 100, offset: int = 0):
    """
    Get chat message history.
    
    Args:
        limit: Maximum number of messages to return
        offset: Offset for pagination
        
    Returns:
        List of chat messages
    """
    service = get_chat_controller_service()
    all_messages = service.get_messages()
    
    # Apply pagination
    total_count = len(all_messages)
    messages = all_messages[offset:offset + limit]
    
    # Convert to response models
    chat_messages = []
    for msg in messages:
        from datetime import datetime
        timestamp = msg.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif not isinstance(timestamp, datetime):
            timestamp = datetime.now()
            
        chat_messages.append(ChatMessage(
            id=msg.get("id", ""),
            role=msg.get("role", "system"),
            content=msg.get("content", ""),
            timestamp=timestamp,
            metadata=msg.get("metadata"),
        ))
    
    return GetMessagesResponse(
        messages=chat_messages,
        has_more=(offset + limit) < total_count,
        total_count=total_count,
    )


@router.post("/messages", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest):
    """
    Send a message to the controller.
    
    This is the main endpoint for user chat input. The message is:
    1. Added to history
    2. If there's a pending input request, it fulfills that request
    3. Otherwise, it's buffered for the controller to read
    
    Args:
        request: The message to send
        
    Returns:
        Success status and message ID
    """
    service = get_chat_controller_service()
    
    try:
        message = await service.send_message(
            content=request.content,
            metadata=request.metadata,
        )
        
        return SendMessageResponse(
            success=True,
            message_id=message.get("id"),
        )
        
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return SendMessageResponse(
            success=False,
            error=str(e),
        )


@router.delete("/messages")
async def clear_messages():
    """
    Clear all chat messages.
    
    Returns:
        Success status
    """
    service = get_chat_controller_service()
    service.clear_messages()
    return {"success": True}


# ============================================================================
# Input Handling
# ============================================================================

@router.post("/input/{request_id}")
async def submit_input_response(request_id: str, response: ChatInputResponse):
    """
    Submit a response to a pending input request.
    
    When the controller requests input from the user, this endpoint
    is used to submit the response.
    
    Args:
        request_id: The input request ID
        response: The user's response
        
    Returns:
        Success status
    """
    service = get_chat_controller_service()
    
    success = service.submit_input_response(request_id, response.value)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"No pending input request with ID: {request_id}"
        )
    
    return {"success": True}


@router.delete("/input/{request_id}")
async def cancel_input_request(request_id: str):
    """
    Cancel a pending input request.
    
    Args:
        request_id: The input request ID
        
    Returns:
        Success status
    """
    service = get_chat_controller_service()
    
    success = service.cancel_input_request(request_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"No pending input request with ID: {request_id}"
        )
    
    return {"success": True}


# ============================================================================
# WebSocket Integration
# ============================================================================

def setup_chat_websocket(emit_callback):
    """
    Set up the chat controller service with WebSocket emit callback.
    
    This should be called when the WebSocket connection is established.
    
    Args:
        emit_callback: Function to emit WebSocket events
    """
    service = get_chat_controller_service()
    service.set_emit_callback(emit_callback)


# ============================================================================
# Backward Compatibility Aliases
# ============================================================================

# These endpoints use the old "compiler" naming for backward compatibility

@router.get("/compiler/state")
async def get_compiler_state_compat():
    """Backward compatible endpoint."""
    return await get_controller_state()


@router.post("/compiler/start")
async def start_compiler_compat():
    """Backward compatible endpoint."""
    return await start_controller()


@router.post("/compiler/stop")
async def stop_compiler_compat():
    """Backward compatible endpoint."""
    return await stop_controller()

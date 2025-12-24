"""
Chat Router - REST API endpoints for the compiler chat interface.

Provides endpoints for:
- Sending messages to the compiler
- Getting chat history
- Getting compiler state
- Starting/stopping the compiler
- Responding to input requests
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.compiler_service import get_compiler_service
from schemas.chat_schemas import (
    ChatMessage,
    SendMessageRequest,
    SendMessageResponse,
    GetMessagesResponse,
    CompilerStateResponse,
    CompilerProjectInfo,
    CompilerStatus,
    StartCompilerRequest,
    StartCompilerResponse,
    ChatInputRequest,
    ChatInputResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat")


# ============================================================================
# Compiler State
# ============================================================================

@router.get("/state", response_model=CompilerStateResponse)
async def get_compiler_state():
    """
    Get the current state of the compiler meta project.
    
    Returns:
        Compiler project info and any pending input request
    """
    service = get_compiler_service()
    state = service.get_state()
    
    # Convert to response model
    compiler_info = CompilerProjectInfo(
        project_id=state.get("project_id"),
        project_name="NormCode Compiler",
        status=CompilerStatus(state.get("status", "disconnected")),
        is_loaded=state.get("is_loaded", False),
        is_read_only=True,
        current_step=state.get("current_step"),
        error_message=state.get("error_message"),
    )
    
    # Convert pending input if present
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
    
    return CompilerStateResponse(
        compiler=compiler_info,
        pending_input=pending_request,
    )


@router.post("/start", response_model=StartCompilerResponse)
async def start_compiler(request: StartCompilerRequest = StartCompilerRequest()):
    """
    Start/connect the compiler meta project.
    
    This initializes the compiler and makes it ready to receive
    user input through the chat. The compiler project is read-only.
    
    Args:
        request: Start configuration (auto_run, etc.)
        
    Returns:
        Compiler start result with status
    """
    service = get_compiler_service()
    
    try:
        state = await service.start()
        
        return StartCompilerResponse(
            success=True,
            project_id=state.get("project_id"),
            project_path=state.get("project_path"),
            project_config_file=state.get("project_config_file"),
            status=CompilerStatus(state.get("status", "connected")),
        )
        
    except Exception as e:
        logger.error(f"Failed to start compiler: {e}")
        return StartCompilerResponse(
            success=False,
            status=CompilerStatus.ERROR,
            error=str(e),
        )


@router.post("/stop")
async def stop_compiler():
    """
    Stop the compiler execution (but keep it connected).
    
    Returns:
        Success status
    """
    service = get_compiler_service()
    await service.stop()
    
    return {"success": True, "status": "connected"}


@router.post("/disconnect")
async def disconnect_compiler():
    """
    Disconnect the compiler completely.
    
    Returns:
        Success status
    """
    service = get_compiler_service()
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
    service = get_compiler_service()
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
    Send a message to the compiler.
    
    This is the main endpoint for user chat input. The message is:
    1. Added to history
    2. If there's a pending input request, it fulfills that request
    3. Otherwise, it triggers the compiler to process the message
    
    Args:
        request: The message to send
        
    Returns:
        Success status and message ID
    """
    service = get_compiler_service()
    
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
    service = get_compiler_service()
    service.clear_messages()
    
    return {"success": True}


# ============================================================================
# Input Handling
# ============================================================================

@router.post("/input/{request_id}")
async def submit_input_response(request_id: str, response: ChatInputResponse):
    """
    Submit a response to a pending input request.
    
    When the compiler requests input from the user, this endpoint
    is used to submit the response.
    
    Args:
        request_id: The input request ID
        response: The user's response
        
    Returns:
        Success status
    """
    service = get_compiler_service()
    
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
    service = get_compiler_service()
    
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
    Set up the compiler service with WebSocket emit callback.
    
    This should be called when the WebSocket connection is established.
    
    Args:
        emit_callback: Function to emit WebSocket events
    """
    service = get_compiler_service()
    service.set_emit_callback(emit_callback)


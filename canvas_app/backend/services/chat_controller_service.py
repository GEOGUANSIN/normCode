"""
Chat Controller Service - Manages which NormCode project controls the chat.

Unlike the previous CompilerService, this allows the user to select any
NormCode project to drive the chat conversation. The selected project
runs via ExecutionController and uses ChatTool for I/O.

Architecture:
    User selects a project → ChatControllerService loads it →
    ExecutionController runs the plan → ChatTool handles I/O

This makes the system transparent: users see exactly which plan is
running and can switch between different chat-capable projects.

The chat controller's canvas tool can also query the MAIN execution
controller (running user projects) to explain what's happening there.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from tools.chat_tool import CanvasChatTool
from tools.canvas_tool import CanvasDisplayTool

if TYPE_CHECKING:
    from services.execution.controller import ExecutionController

logger = logging.getLogger(__name__)


# =============================================================================
# Default Controller Projects
# =============================================================================

# Built-in compiler project (default controller)
COMPILER_PROJECT_DIR = Path(__file__).parent.parent.parent / "compiler"
COMPILER_CONFIG_FILE = COMPILER_PROJECT_DIR / "compiler.normcode-canvas.json"


class ControllerStatus:
    """Valid status values for the controller."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class ControllerInfo:
    """Information about an available chat controller project."""
    
    def __init__(
        self,
        project_id: str,
        name: str,
        path: str,
        config_file: Optional[str] = None,
        description: Optional[str] = None,
        is_builtin: bool = False,
    ):
        self.project_id = project_id
        self.name = name
        self.path = path
        self.config_file = config_file
        self.description = description
        self.is_builtin = is_builtin
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "path": self.path,
            "config_file": self.config_file,
            "description": self.description,
            "is_builtin": self.is_builtin,
        }


class ChatControllerService:
    """
    Service for managing chat controller projects.
    
    A chat controller is any NormCode project that:
    1. Has chat paradigms (c_ChatRead, h_Response-c_ChatWrite, etc.)
    2. Can be loaded and executed
    3. Drives the conversation via ChatTool
    
    Key Features:
    - List available controller projects
    - Select and load a controller
    - Run the controller with message routing
    - Show controller execution status
    """
    
    def __init__(self):
        """Initialize the chat controller service."""
        # Current controller state
        self._controller_id: Optional[str] = None
        self._controller_info: Optional[ControllerInfo] = None
        self._status: str = ControllerStatus.DISCONNECTED
        self._current_flow_index: Optional[str] = None
        self._error_message: Optional[str] = None
        
        # Execution controller for running the chat project
        self._execution_controller: Optional[Any] = None
        
        # Tools
        self._chat_tool: Optional[CanvasChatTool] = None
        self._canvas_tool: Optional[CanvasDisplayTool] = None
        self._emit_callback: Optional[Callable] = None
        
        # Message history
        self._messages: List[Dict[str, Any]] = []
        
        # Available controllers (cached)
        self._available_controllers: List[ControllerInfo] = []
        self._controllers_scanned = False
    
    # =========================================================================
    # Configuration
    # =========================================================================
    
    def set_emit_callback(self, callback: Callable[[str, Dict], None]):
        """
        Set the WebSocket emit callback.
        
        Called by websocket_router when a connection is established.
        """
        self._emit_callback = callback
        # Create tools with the callback
        self._chat_tool = CanvasChatTool(emit_callback=callback, source="controller")
        self._canvas_tool = CanvasDisplayTool(
            emit_callback=callback,
            execution_getter=self._get_main_execution_controller
        )
    
    def _get_main_execution_controller(self) -> Optional["ExecutionController"]:
        """
        Get the main ExecutionController for user projects.
        
        This allows the chat controller's canvas tool to query execution state
        of the user's project, enabling the chat to explain what's happening.
        
        We try multiple strategies:
        1. Get controller by current project ID from project_service
        2. Fall back to active controller from registry
        
        Returns:
            The main ExecutionController, or None if no project is loaded
        """
        try:
            from services.execution_service import execution_controller_registry, get_execution_controller
            from services.project_service import project_service
            
            # Strategy 1: Use current project from project_service
            if project_service.is_project_open and project_service.current_config:
                current_project_id = project_service.current_config.id
                controller = get_execution_controller(current_project_id)
                
                logger.debug(f"Checking controller for current project: {current_project_id}, "
                            f"has_controller={controller is not None}, "
                            f"concept_repo={controller.concept_repo is not None if controller else 'N/A'}, "
                            f"inference_repo={controller.inference_repo is not None if controller else 'N/A'}")
                
                if controller and controller.concept_repo is not None:
                    return controller
            
            # Strategy 2: Fall back to active controller from registry
            active_id = execution_controller_registry.get_active_project_id()
            controller = execution_controller_registry.get_active_controller()
            
            logger.debug(f"Checking active controller: active_id={active_id}, "
                        f"has_controller={controller is not None}, "
                        f"concept_repo={controller.concept_repo is not None if controller else 'N/A'}")
            
            if controller and controller.concept_repo is not None:
                return controller
            
            logger.debug(f"No loaded execution controller found. "
                        f"Project open: {project_service.is_project_open}, "
                        f"Active ID: {active_id}")
            return None
        except Exception as e:
            logger.warning(f"Could not get main execution controller: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    def _emit(self, event_type: str, data: Dict[str, Any]):
        """Emit a WebSocket event."""
        if self._emit_callback:
            try:
                self._emit_callback(event_type, data)
            except Exception as e:
                logger.error(f"Failed to emit event {event_type}: {e}")
    
    # =========================================================================
    # Available Controllers
    # =========================================================================
    
    def _scan_builtin_controllers(self) -> List[ControllerInfo]:
        """Scan for built-in controller projects."""
        controllers = []
        
        # Add the default compiler controller
        if COMPILER_CONFIG_FILE.exists():
            try:
                with open(COMPILER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                controllers.append(ControllerInfo(
                    project_id="compiler",
                    name=config.get("name", "NormCode Compiler"),
                    path=str(COMPILER_PROJECT_DIR),
                    config_file=COMPILER_CONFIG_FILE.name,
                    description=config.get("description", "Default chat-driven compiler"),
                    is_builtin=True,
                ))
            except Exception as e:
                logger.warning(f"Failed to load compiler config: {e}")
        
        return controllers
    
    def get_available_controllers(self, refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get list of available chat controller projects.
        
        Args:
            refresh: Force rescan of available controllers
            
        Returns:
            List of controller info dicts
        """
        if not self._controllers_scanned or refresh:
            self._available_controllers = self._scan_builtin_controllers()
            self._controllers_scanned = True
        
        return [c.to_dict() for c in self._available_controllers]
    
    def register_controller(
        self,
        project_id: str,
        name: str,
        path: str,
        config_file: Optional[str] = None,
        description: Optional[str] = None,
    ) -> ControllerInfo:
        """
        Register a new chat controller project.
        
        Args:
            project_id: Unique identifier for the controller
            name: Display name
            path: Path to the project directory
            config_file: Config file name (if any)
            description: Optional description
            
        Returns:
            The registered ControllerInfo
        """
        info = ControllerInfo(
            project_id=project_id,
            name=name,
            path=path,
            config_file=config_file,
            description=description,
            is_builtin=False,
        )
        
        # Remove existing with same ID
        self._available_controllers = [
            c for c in self._available_controllers 
            if c.project_id != project_id
        ]
        self._available_controllers.append(info)
        
        return info
    
    # =========================================================================
    # State Accessors
    # =========================================================================
    
    @property
    def is_connected(self) -> bool:
        """Check if a controller is connected."""
        return self._status in (
            ControllerStatus.CONNECTED,
            ControllerStatus.RUNNING,
            ControllerStatus.PAUSED,
        )
    
    @property
    def is_running(self) -> bool:
        """Check if controller is actively executing."""
        return self._status == ControllerStatus.RUNNING
    
    def get_state(self) -> Dict[str, Any]:
        """Get the current controller state."""
        return {
            "controller_id": self._controller_id,
            "controller_info": self._controller_info.to_dict() if self._controller_info else None,
            "status": self._status,
            "current_flow_index": self._current_flow_index,
            "error_message": self._error_message,
            "pending_input": self._chat_tool.get_pending_request() if self._chat_tool else None,
            "is_execution_active": self._chat_tool.is_execution_active() if self._chat_tool else False,
        }
    
    # =========================================================================
    # Message History
    # =========================================================================
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all chat messages."""
        return self._messages
    
    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict] = None,
        flow_index: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Add a message to history and emit to frontend.
        
        Args:
            role: Message role ('user', 'controller', 'system')
            content: Message content
            metadata: Optional metadata
            flow_index: Optional flow index that generated this message
        """
        import uuid
        from datetime import datetime
        
        msg_metadata = metadata or {}
        if flow_index:
            msg_metadata["flowIndex"] = flow_index
        
        message = {
            "id": str(uuid.uuid4())[:8],
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": msg_metadata,
        }
        self._messages.append(message)
        self._emit("chat:message", message)
        
        return message
    
    def clear_messages(self):
        """Clear all chat messages."""
        self._messages = []
    
    # =========================================================================
    # Controller Lifecycle
    # =========================================================================
    
    async def select_controller(self, controller_id: str) -> Dict[str, Any]:
        """
        Select and connect a chat controller.
        
        Args:
            controller_id: ID of the controller to select
            
        Returns:
            State after selection
        """
        # Find the controller
        controller = None
        for c in self._available_controllers:
            if c.project_id == controller_id:
                controller = c
                break
        
        if not controller:
            # Try to scan again
            self.get_available_controllers(refresh=True)
            for c in self._available_controllers:
                if c.project_id == controller_id:
                    controller = c
                    break
        
        if not controller:
            raise ValueError(f"Controller not found: {controller_id}")
        
        # Stop current controller if running
        if self._status != ControllerStatus.DISCONNECTED:
            await self.disconnect()
        
        # Connect to new controller
        return await self._connect_controller(controller)
    
    async def _connect_controller(self, controller: ControllerInfo) -> Dict[str, Any]:
        """
        Connect to a controller project.
        
        This loads the project and prepares it for execution.
        """
        try:
            self._status = ControllerStatus.CONNECTING
            self._controller_id = controller.project_id
            self._controller_info = controller
            self._emit("chat:controller_status", {
                "status": ControllerStatus.CONNECTING,
                "controller_id": controller.project_id,
            })
            
            # Validate project exists
            project_path = Path(controller.path)
            if not project_path.exists():
                raise FileNotFoundError(f"Controller project not found: {project_path}")
            
            # Load project config if available
            config = {}
            if controller.config_file:
                config_path = project_path / controller.config_file
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
            
            # Create execution controller with "controller" source to separate events from main execution
            from services.execution.controller import ExecutionController
            self._execution_controller = ExecutionController(
                project_id=f"chat-{controller.project_id}",
                event_source="controller"  # Events go to chat panel, not main control bar
            )
            
            # Load repositories
            repos = config.get("repositories", {})
            execution = config.get("execution", {})
            
            concepts_path = project_path / repos.get("concepts", "repos/chat.concept.json")
            inferences_path = project_path / repos.get("inferences", "repos/chat.inference.json")
            inputs_path = repos.get("inputs")
            if inputs_path:
                inputs_path = project_path / inputs_path
            
            await self._execution_controller.load_repositories(
                concepts_path=str(concepts_path),
                inferences_path=str(inferences_path),
                inputs_path=str(inputs_path) if inputs_path else None,
                llm_model=execution.get("llm_model", "demo"),
                base_dir=str(project_path),
                max_cycles=execution.get("max_cycles", 100),
                db_path=execution.get("db_path"),
                paradigm_dir=execution.get("paradigm_dir"),
            )
            
            # Wire up chat tool to the execution controller
            if self._execution_controller.chat_tool:
                # Use the execution controller's chat tool but update our reference
                self._chat_tool = self._execution_controller.chat_tool
                # Override the source so input requests go to /api/chat/input/ not /api/execution/chat-input/
                self._chat_tool._source = "controller"
            
            self._status = ControllerStatus.CONNECTED
            self._error_message = None
            self._emit("chat:controller_status", {
                "status": ControllerStatus.CONNECTED,
                "controller_id": controller.project_id,
                "controller_name": controller.name,
            })
            
            # Add welcome message
            self.add_message(
                role="controller",
                content=f"**{controller.name}** connected.\n\n"
                       f"{controller.description or 'Ready to chat.'}"
            )
            
            logger.info(f"Controller connected: {controller.project_id}")
            return self.get_state()
            
        except Exception as e:
            self._status = ControllerStatus.ERROR
            self._error_message = str(e)
            self._emit("chat:controller_status", {
                "status": ControllerStatus.ERROR,
                "error": str(e),
            })
            logger.error(f"Failed to connect controller: {e}")
            raise
    
    async def start(self) -> Dict[str, Any]:
        """
        Start the controller execution.
        
        This begins running the controller's NormCode plan.
        The plan will read messages from ChatTool.
        """
        if not self._execution_controller:
            # If no controller selected, use default
            if not self._available_controllers:
                self.get_available_controllers()
            
            if self._available_controllers:
                await self.select_controller(self._available_controllers[0].project_id)
            else:
                raise RuntimeError("No chat controllers available")
        
        if self._status == ControllerStatus.RUNNING:
            return self.get_state()
        
        try:
            self._status = ControllerStatus.RUNNING
            self._emit("chat:controller_status", {
                "status": ControllerStatus.RUNNING,
                "controller_id": self._controller_id,
            })
            
            # Start execution
            await self._execution_controller.start()
            
            logger.info(f"Controller started: {self._controller_id}")
            return self.get_state()
            
        except Exception as e:
            self._status = ControllerStatus.ERROR
            self._error_message = str(e)
            self._emit("chat:controller_status", {
                "status": ControllerStatus.ERROR,
                "error": str(e),
            })
            raise
    
    async def pause(self):
        """Pause the controller execution."""
        if self._execution_controller:
            await self._execution_controller.pause()
            self._status = ControllerStatus.PAUSED
            self._emit("chat:controller_status", {
                "status": ControllerStatus.PAUSED,
                "controller_id": self._controller_id,
            })
    
    async def resume(self):
        """Resume paused controller execution."""
        if self._execution_controller:
            await self._execution_controller.resume()
            self._status = ControllerStatus.RUNNING
            self._emit("chat:controller_status", {
                "status": ControllerStatus.RUNNING,
                "controller_id": self._controller_id,
            })
    
    async def stop(self):
        """Stop controller execution (stay connected)."""
        if self._execution_controller:
            await self._execution_controller.stop()
            self._status = ControllerStatus.CONNECTED
            self._emit("chat:controller_status", {
                "status": ControllerStatus.CONNECTED,
                "controller_id": self._controller_id,
            })
    
    async def disconnect(self):
        """Disconnect the controller completely."""
        if self._execution_controller:
            await self._execution_controller.stop()
            self._execution_controller = None
        
        self._controller_id = None
        self._controller_info = None
        self._status = ControllerStatus.DISCONNECTED
        self._current_flow_index = None
        self._emit("chat:controller_status", {"status": ControllerStatus.DISCONNECTED})
    
    # =========================================================================
    # Message Handling
    # =========================================================================
    
    async def send_message(self, content: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Handle a message from the user.
        
        The message is:
        1. Added to history
        2. If controller is running with pending input, message is delivered
        3. Otherwise, buffered for the controller to read
        """
        # Add user message to history
        message = self.add_message("user", content, metadata)
        
        # If there's a pending input request, fulfill it
        if self._chat_tool and self._chat_tool.has_pending_request():
            pending = self._chat_tool.get_pending_request()
            if pending:
                self._chat_tool.submit_response(pending["id"], content)
                logger.info(f"Fulfilled pending input request: {pending['id']}")
                return message
        
        # If controller is running, buffer the message
        if self._chat_tool and self._status == ControllerStatus.RUNNING:
            result = self._chat_tool.buffer_message(content)
            if result.get("success"):
                if result.get("delivered"):
                    logger.info("Message delivered to waiting controller")
                else:
                    logger.info("Message buffered for controller")
                return message
        
        # If controller is not running, start it
        if self._status == ControllerStatus.CONNECTED:
            await self.start()
            # Buffer the message for the newly started controller
            if self._chat_tool:
                self._chat_tool.buffer_message(content)
        
        return message
    
    def submit_input_response(self, request_id: str, value: str) -> bool:
        """Submit a response to a pending input request."""
        if not self._chat_tool:
            return False
        return self._chat_tool.submit_response(request_id, value)
    
    def cancel_input_request(self, request_id: str) -> bool:
        """Cancel a pending input request."""
        if not self._chat_tool:
            return False
        return self._chat_tool.cancel_request(request_id)
    
    # =========================================================================
    # Tool Access
    # =========================================================================
    
    @property
    def chat_tool(self) -> Optional[CanvasChatTool]:
        """Get the chat tool."""
        return self._chat_tool
    
    @property
    def canvas_tool(self) -> Optional[CanvasDisplayTool]:
        """Get the canvas tool."""
        return self._canvas_tool
    
    @property
    def execution_controller(self) -> Optional[Any]:
        """Get the execution controller running the chat project."""
        return self._execution_controller


# =============================================================================
# Singleton Instance
# =============================================================================

_chat_controller_service: Optional[ChatControllerService] = None


def get_chat_controller_service() -> ChatControllerService:
    """
    Get the global chat controller service instance.
    """
    global _chat_controller_service
    if _chat_controller_service is None:
        _chat_controller_service = ChatControllerService()
    return _chat_controller_service


# =============================================================================
# Backward Compatibility
# =============================================================================

# Alias for code that still uses "compiler_service" naming
def get_compiler_service():
    """Backward compatibility alias for get_chat_controller_service."""
    return get_chat_controller_service()


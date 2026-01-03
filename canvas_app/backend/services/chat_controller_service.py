"""
Chat Controller Service - Manages which NormCode project controls the chat.

Unlike the previous CompilerService, this allows the user to select any
NormCode project to drive the chat conversation. The selected project
runs via ExecutionController and uses ChatTool for I/O.

Architecture:
    User selects a project → ChatControllerService loads it →
    ExecutionController runs the plan → ChatTool handles I/O

This service is a facade that coordinates:
- ControllerRegistryService: Available controller discovery/registration
- ChatMessageService: Chat message history management
- ExecutionController: Running the selected controller project

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
from schemas.chat_schemas import ControllerStatus, ControllerInfo

# Import sub-services
from .chat.registry_service import ControllerRegistryService, BUILT_IN_PROJECTS_DIR
from .chat.message_service import ChatMessageService
from .chat.placeholder_service import PlaceholderService

if TYPE_CHECKING:
    from services.execution.controller import ExecutionController

logger = logging.getLogger(__name__)


class ChatControllerService:
    """
    Service for managing chat controller projects.
    
    A chat controller is any NormCode project that:
    1. Has chat paradigms (c_ChatRead, h_Response-c_ChatWrite, etc.)
    2. Can be loaded and executed
    3. Drives the conversation via ChatTool
    
    This is a facade that coordinates:
    - ControllerRegistryService: Controller discovery and registration
    - ChatMessageService: Message history management
    - ExecutionController: Running the controller project
    
    Key Features:
    - List available controller projects
    - Select and load a controller
    - Run the controller with message routing
    - Show controller execution status
    """
    
    def __init__(self):
        """Initialize the chat controller service."""
        # Sub-services
        self._registry_service = ControllerRegistryService()
        self._message_service = ChatMessageService()
        self._placeholder_service = PlaceholderService()
        
        # Current controller state
        self._controller_id: Optional[str] = None
        self._controller_info: Optional[ControllerInfo] = None
        self._status: ControllerStatus = ControllerStatus.DISCONNECTED
        self._current_flow_index: Optional[str] = None
        self._error_message: Optional[str] = None
        
        # Placeholder mode flag (use demo responses instead of real controller)
        self._placeholder_mode: bool = False
        
        # Execution controller for running the chat project
        self._execution_controller: Optional[Any] = None
        
        # Tools
        self._chat_tool: Optional[CanvasChatTool] = None
        self._canvas_tool: Optional[CanvasDisplayTool] = None
        self._emit_callback: Optional[Callable] = None
    
    # =========================================================================
    # Configuration
    # =========================================================================
    
    def set_emit_callback(self, callback: Callable[[str, Dict], None]):
        """
        Set the WebSocket emit callback.
        
        Called by websocket_router when a connection is established.
        """
        self._emit_callback = callback
        
        # Configure sub-services with callback
        self._message_service.set_emit_callback(callback)
        
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
        
        Strategy:
        1. Use WorkerRegistry's main panel binding (preferred - explicit binding)
        2. Fall back to WorkerManager's focused controller
        3. Fall back to active controller from legacy registry
        
        Returns:
            The main ExecutionController, or None if no project is loaded
        """
        try:
            # Strategy 1: Use WorkerRegistry's main panel binding (NEW)
            from services.execution.worker_registry import get_worker_registry, PanelType
            registry = get_worker_registry()
            
            # Get controller bound to main panel
            main_controller = registry.get_controller_for_panel("main_panel")
            if main_controller and main_controller.concept_repo is not None:
                logger.debug("Using controller bound to main_panel from WorkerRegistry")
                return main_controller
            
            # Strategy 2: Use WorkerManager's focused controller
            from services.execution.worker_manager import get_worker_manager
            wm = get_worker_manager()
            
            focused_controller = wm.get_focused_controller()
            if focused_controller and focused_controller.concept_repo is not None:
                logger.debug("Using focused controller from WorkerManager")
                return focused_controller
            
            # Strategy 3: Fall back to legacy registry for backward compatibility
            from services.execution_service import execution_controller_registry, get_execution_controller
            from services.project_service import project_service
            
            if project_service.is_project_open and project_service.current_config:
                current_project_id = project_service.current_config.id
                controller = get_execution_controller(current_project_id)
                
                if controller and controller.concept_repo is not None:
                    logger.debug(f"Using controller from legacy registry: {current_project_id}")
                    return controller
            
            # Strategy 4: Fall back to active controller from registry
            controller = execution_controller_registry.get_active_controller()
            if controller and controller.concept_repo is not None:
                logger.debug("Using active controller from legacy registry")
                return controller
            
            logger.debug("No loaded execution controller found")
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
                # Add controller info to status events for frontend to update state
                if event_type == "chat:controller_status":
                    if self._controller_info:
                        # Always include controller details so frontend stays in sync
                        data.setdefault("controller_id", self._controller_info.project_id)
                        data.setdefault("controller_name", self._controller_info.name)
                        data.setdefault("controller_path", self._controller_info.path)
                        data.setdefault("config_file", self._controller_info.config_file)
                    data.setdefault("placeholder_mode", self._placeholder_mode)
                self._emit_callback(event_type, data)
            except Exception as e:
                logger.error(f"Failed to emit event {event_type}: {e}")
    
    # =========================================================================
    # Registry Delegation
    # =========================================================================
    
    def get_available_controllers(self, refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get list of available chat controller projects.
        
        Args:
            refresh: Force rescan of available controllers
            
        Returns:
            List of controller info dicts
        """
        controllers = self._registry_service.get_available_controllers(refresh=refresh)
        return [c.model_dump() for c in controllers]
    
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
        return self._registry_service.register_controller(
            project_id=project_id,
            name=name,
            path=path,
            config_file=config_file,
            description=description,
        )
    
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
            "controller_info": self._controller_info.model_dump() if self._controller_info else None,
            "status": self._status.value,
            "current_flow_index": self._current_flow_index,
            "error_message": self._error_message,
            "pending_input": self._chat_tool.get_pending_request() if self._chat_tool else None,
            "is_execution_active": self._chat_tool.is_execution_active() if self._chat_tool else False,
            "placeholder_mode": self._placeholder_mode,
        }
    
    # =========================================================================
    # Message History Delegation
    # =========================================================================
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all chat messages."""
        return self._message_service.get_messages()
    
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
        return self._message_service.add_message(
            role=role,
            content=content,
            metadata=metadata,
            flow_index=flow_index,
        )
    
    def clear_messages(self):
        """Clear all chat messages."""
        self._message_service.clear_messages()
    
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
        # Stop current controller if running
        if self._status != ControllerStatus.DISCONNECTED:
            await self.disconnect()
        
        # Special case: placeholder controller (demo mode)
        if controller_id == "placeholder":
            return await self.start_placeholder_mode()
        
        # Find the controller
        controller = self._registry_service.get_controller(controller_id)
        
        if not controller:
            # Try to refresh and find again
            self._registry_service.get_available_controllers(refresh=True)
            controller = self._registry_service.get_controller(controller_id)
        
        if not controller:
            raise ValueError(f"Controller not found: {controller_id}")
        
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
                "status": ControllerStatus.CONNECTING.value,
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
            
            # Register with WorkerRegistry (primary)
            from services.execution.worker_registry import get_worker_registry, WorkerCategory, PanelType
            registry = get_worker_registry()
            worker_id = f"chat-{controller.project_id}"
            registry.register_worker(
                worker_id=worker_id,
                controller=self._execution_controller,
                category=WorkerCategory.ASSISTANT,
                name=controller.name,
                project_id=controller.project_id,
                metadata={"controller_info": controller.model_dump()},
            )
            
            # Bind chat panel to this worker
            registry.bind_panel(
                panel_id="chat_panel",
                panel_type=PanelType.CHAT,
                worker_id=worker_id,
            )
            
            # Also register with legacy WorkerManager for backward compat
            try:
                from services.execution.worker_manager import get_worker_manager, WorkerType
                wm = get_worker_manager()
                wm.register_worker(
                    worker_id=worker_id,
                    worker_type=WorkerType.CHAT_CONTROLLER,
                    controller=self._execution_controller,
                    project_id=controller.project_id,
                    project_name=controller.name,
                    metadata={"controller_info": controller.model_dump()},
                )
            except Exception as e:
                logger.debug(f"Legacy WorkerManager registration skipped: {e}")
            
            self._status = ControllerStatus.CONNECTED
            self._error_message = None
            self._emit("chat:controller_status", {
                "status": ControllerStatus.CONNECTED.value,
                "controller_id": controller.project_id,
                "controller_name": controller.name,
                "controller_path": controller.path,
                "config_file": controller.config_file,
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
                "status": ControllerStatus.ERROR.value,
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
            default_id = self._registry_service.get_default_controller_id()
            
            if default_id:
                await self.select_controller(default_id)
            else:
                raise RuntimeError("No chat controllers available")
        
        if self._status == ControllerStatus.RUNNING:
            return self.get_state()
        
        try:
            self._status = ControllerStatus.RUNNING
            self._emit("chat:controller_status", {
                "status": ControllerStatus.RUNNING.value,
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
                "status": ControllerStatus.ERROR.value,
                "error": str(e),
            })
            raise
    
    async def pause(self):
        """Pause the controller execution."""
        if self._execution_controller:
            await self._execution_controller.pause()
            self._status = ControllerStatus.PAUSED
            self._emit("chat:controller_status", {
                "status": ControllerStatus.PAUSED.value,
                "controller_id": self._controller_id,
            })
    
    async def resume(self):
        """Resume paused controller execution."""
        if self._execution_controller:
            await self._execution_controller.resume()
            self._status = ControllerStatus.RUNNING
            self._emit("chat:controller_status", {
                "status": ControllerStatus.RUNNING.value,
                "controller_id": self._controller_id,
            })
    
    async def stop(self):
        """Stop controller execution (stay connected)."""
        if self._execution_controller:
            await self._execution_controller.stop()
            self._status = ControllerStatus.CONNECTED
            self._emit("chat:controller_status", {
                "status": ControllerStatus.CONNECTED.value,
                "controller_id": self._controller_id,
            })
    
    async def disconnect(self):
        """Disconnect the controller completely."""
        if self._execution_controller:
            await self._execution_controller.stop()
            
            if self._controller_id:
                worker_id = f"chat-{self._controller_id}"
                
                # Unbind chat panel first
                try:
                    from services.execution.worker_registry import get_worker_registry
                    registry = get_worker_registry()
                    registry.unbind_panel("chat_panel")
                except Exception as e:
                    logger.debug(f"Failed to unbind chat panel: {e}")
                
                # Unregister from WorkerRegistry
                try:
                    from services.execution.worker_registry import get_worker_registry
                    registry = get_worker_registry()
                    registry.unregister_worker(worker_id)
                except Exception as e:
                    logger.warning(f"Failed to unregister from WorkerRegistry: {e}")
                
                # Unregister from legacy WorkerManager
                try:
                    from services.execution.worker_manager import get_worker_manager
                    wm = get_worker_manager()
                    wm.unregister_worker(worker_id)
                except Exception as e:
                    logger.debug(f"Legacy WorkerManager unregister skipped: {e}")
            
            self._execution_controller = None
        
        self._controller_id = None
        self._controller_info = None
        self._status = ControllerStatus.DISCONNECTED
        self._current_flow_index = None
        self._placeholder_mode = False
        self._emit("chat:controller_status", {"status": ControllerStatus.DISCONNECTED.value})
    
    # =========================================================================
    # Placeholder Mode
    # =========================================================================
    
    @property
    def is_placeholder_mode(self) -> bool:
        """Check if using placeholder/demo responses."""
        return self._placeholder_mode
    
    async def start_placeholder_mode(self) -> Dict[str, Any]:
        """
        Start placeholder mode for demo responses.
        
        Use this when no controller is available or for demos.
        """
        self._placeholder_mode = True
        self._status = ControllerStatus.CONNECTED
        self._controller_id = "placeholder"
        
        # Get placeholder controller info from registry
        placeholder_info = self._registry_service.get_controller("placeholder")
        if placeholder_info:
            self._controller_info = placeholder_info
        else:
            # Fallback if not in registry
            self._controller_info = ControllerInfo(
                project_id="placeholder",
                name="Demo Assistant",
                path="",
                description="Helpful demo responses about NormCode (no execution)",
                is_builtin=True,
            )
        
        self._emit("chat:controller_status", {
            "status": ControllerStatus.CONNECTED.value,
            "controller_id": "placeholder",
            "controller_name": self._controller_info.name,
            "controller_path": "",  # Placeholder has no path
            "placeholder_mode": True,
        })
        
        # Add welcome message
        self.add_message(
            role="controller",
            content=self._placeholder_service.get_welcome_message()
        )
        
        logger.info("Started placeholder mode")
        return self.get_state()
    
    def _handle_placeholder_response(self, content: str):
        """Generate and add a placeholder response."""
        response = self._placeholder_service.generate_response(content)
        self.add_message(role="controller", content=response)
    
    # =========================================================================
    # Message Handling
    # =========================================================================
    
    async def send_message(self, content: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Handle a message from the user.
        
        The message is:
        1. Added to history
        2. If in placeholder mode, generate demo response
        3. If controller is running with pending input, message is delivered
        4. Otherwise, buffered for the controller to read
        5. If disconnected, auto-start placeholder mode for graceful degradation
        """
        # Add user message to history
        message = self.add_message("user", content, metadata)
        
        # If in placeholder mode, generate demo response
        if self._placeholder_mode:
            self._handle_placeholder_response(content)
            return message
        
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
        
        # If controller is connected but not running, start it
        if self._status == ControllerStatus.CONNECTED:
            await self.start()
            # Buffer the message for the newly started controller
            if self._chat_tool:
                self._chat_tool.buffer_message(content)
            return message
        
        # If disconnected and no controller available, use placeholder mode
        if self._status == ControllerStatus.DISCONNECTED:
            default_id = self._registry_service.get_default_controller_id()
            if default_id:
                try:
                    await self.select_controller(default_id)
                    await self.start()
                    if self._chat_tool:
                        self._chat_tool.buffer_message(content)
                except Exception as e:
                    logger.warning(f"Failed to start default controller, using placeholder: {e}")
                    await self.start_placeholder_mode()
                    self._handle_placeholder_response(content)
            else:
                # No controllers available, use placeholder
                await self.start_placeholder_mode()
                self._handle_placeholder_response(content)
        
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

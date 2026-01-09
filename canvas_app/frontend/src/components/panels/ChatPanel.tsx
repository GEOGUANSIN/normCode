/**
 * Chat Panel Component
 * 
 * A controller-driven chat interface. The user can select which NormCode
 * project controls the chat, making it transparent what's running.
 * A controller-driven chat interface. The user can select which NormCode
 * project controls the chat, making it transparent what's running.
 * 
 * Key features:
 * - Controller selector dropdown
 * - Status indicator showing execution state
 * - Flow index badges on messages
 * - View controller project button
 * Key features:
 * - Controller selector dropdown
 * - Status indicator showing execution state
 * - Flow index badges on messages
 * - View controller project button
 */

import { useRef, useEffect, useState } from 'react';
import {
  X,
  Send,
  MessageSquare,
  Loader2,
  Trash2,
  Zap,
  Sparkles,
  Terminal,
  Link2,
  Eye,
  Code,
  ChevronRight,
  ChevronDown,
  ChevronDown,
  Play,
  Pause,
  Square,
  Bot,
} from 'lucide-react';
import { useChatStore, type ChatMessage } from '../../stores/chatStore';
import { useProjectStore } from '../../stores/projectStore';

// Message bubble component
function MessageBubble({ message }: { message: ChatMessage }) {
  // Reserved for future expandable content
  const [_isExpanded, _setIsExpanded] = useState(true);
  
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';
  const isController = message.role === 'controller' || message.role === 'compiler';
  const isController = message.role === 'controller' || message.role === 'compiler';
  
  // User messages - right aligned, blue
  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white ml-12 rounded-2xl rounded-br-md px-4 py-2.5 shadow-sm max-w-[85%]">
          <div className="whitespace-pre-wrap break-words text-sm leading-relaxed">
            {message.content}
          </div>
          <div className="text-xs mt-1.5 text-blue-200 text-right">
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>
      </div>
    );
  }
  
  // System messages - centered, subtle
  if (isSystem) {
    return (
      <div className="flex justify-center my-2">
        <div className="bg-slate-100 text-slate-500 text-xs italic px-3 py-1.5 rounded-full">
          {message.content}
        </div>
      </div>
    );
  }
  
  // Controller messages - left aligned with avatar and flow index
  // User messages - right aligned, blue
  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white ml-12 rounded-2xl rounded-br-md px-4 py-2.5 shadow-sm max-w-[85%]">
          <div className="whitespace-pre-wrap break-words text-sm leading-relaxed">
            {message.content}
          </div>
          <div className="text-xs mt-1.5 text-blue-200 text-right">
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>
      </div>
    );
  }
  
  // System messages - centered, subtle
  if (isSystem) {
    return (
      <div className="flex justify-center my-2">
        <div className="bg-slate-100 text-slate-500 text-xs italic px-3 py-1.5 rounded-full">
          {message.content}
        </div>
      </div>
    );
  }
  
  // Controller messages - left aligned with avatar and flow index
  return (
    <div className="flex gap-2 mr-8">
      {/* Avatar */}
      <div className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center ${
        isController ? 'bg-purple-100' : 'bg-slate-100'
      }`}>
        {isController ? (
          <Bot size={14} className="text-purple-600" />
        ) : (
          <MessageSquare size={14} className="text-slate-500" />
        )}
      </div>
      
      {/* Message content */}
      <div className="flex-1 min-w-0">
        {/* Role label with optional flow index */}
        <div className="flex items-center gap-2 mb-1">
          <span className={`text-xs font-medium ${isController ? 'text-purple-600' : 'text-slate-500'}`}>
            Controller
          </span>
          {message.metadata?.flowIndex && (
            <span className="text-[10px] font-mono bg-purple-100 text-purple-600 px-1.5 py-0.5 rounded">
              @{message.metadata.flowIndex}
            </span>
          )}
    <div className="flex gap-2 mr-8">
      {/* Avatar */}
      <div className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center ${
        isController ? 'bg-purple-100' : 'bg-slate-100'
      }`}>
        {isController ? (
          <Bot size={14} className="text-purple-600" />
        ) : (
          <MessageSquare size={14} className="text-slate-500" />
        )}
      </div>
      
      {/* Message content */}
      <div className="flex-1 min-w-0">
        {/* Role label with optional flow index */}
        <div className="flex items-center gap-2 mb-1">
          <span className={`text-xs font-medium ${isController ? 'text-purple-600' : 'text-slate-500'}`}>
            Controller
          </span>
          {message.metadata?.flowIndex && (
            <span className="text-[10px] font-mono bg-purple-100 text-purple-600 px-1.5 py-0.5 rounded">
              @{message.metadata.flowIndex}
            </span>
          )}
        </div>
        
        {/* Content bubble */}
        <div className={`rounded-2xl rounded-tl-md px-4 py-2.5 ${
          isController 
            ? 'bg-gradient-to-br from-purple-50 to-white border border-purple-100' 
            : 'bg-white border border-slate-200'
        }`}>
          <div className="whitespace-pre-wrap break-words text-sm text-slate-700 leading-relaxed">
            {message.content}
        {/* Content bubble */}
        <div className={`rounded-2xl rounded-tl-md px-4 py-2.5 ${
          isController 
            ? 'bg-gradient-to-br from-purple-50 to-white border border-purple-100' 
            : 'bg-white border border-slate-200'
        }`}>
          <div className="whitespace-pre-wrap break-words text-sm text-slate-700 leading-relaxed">
            {message.content}
          </div>
        </div>
        </div>
        
        {/* Timestamp */}
        <div className="text-[10px] text-slate-400 mt-1 ml-1">
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        <div className="text-[10px] text-slate-400 mt-1 ml-1">
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
}

// Controller selector dropdown
function ControllerSelector() {
  const [isOpen, setIsOpen] = useState(false);
  const {
    availableControllers,
    controllerId,
    controllerName,
    controllerStatus,
    currentFlowIndex,
    selectController,
    loadControllers,
  } = useChatStore();
  
  // Load controllers on mount
  useEffect(() => {
    loadControllers();
  }, [loadControllers]);
  
  const getStatusColor = () => {
    switch (controllerStatus) {
      case 'running': return 'bg-green-500 animate-pulse';
      case 'paused': return 'bg-yellow-500';
      case 'connected': return 'bg-blue-400';
      case 'connecting': return 'bg-yellow-500 animate-pulse';
      case 'error': return 'bg-red-500';
      default: return 'bg-slate-400';
    }
  };
  
  const getStatusText = () => {
    if (controllerStatus === 'running' && currentFlowIndex) {
      return `@${currentFlowIndex}`;
    }
    switch (controllerStatus) {
      case 'running': return 'Running in background';
      case 'paused': return 'Paused';
      case 'connected': return 'Ready';
      case 'connecting': return 'Connecting...';
      case 'error': return 'Error';
      default: return 'Disconnected';
    }
  };
  
  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-2 py-1 rounded-lg hover:bg-slate-100 transition-colors"
      >
        <span className={`w-2 h-2 rounded-full ${getStatusColor()}`} />
        <span className="text-sm font-medium text-slate-700 truncate max-w-[120px]">
          {controllerName || 'Select Controller'}
        </span>
        <ChevronDown size={14} className="text-slate-400" />
      </button>
      
      {/* Status text */}
      <div className="text-[10px] text-slate-500 mt-0.5 ml-4">
        {getStatusText()}
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-2 py-1 rounded-lg hover:bg-slate-100 transition-colors"
      >
        <span className={`w-2 h-2 rounded-full ${getStatusColor()}`} />
        <span className="text-sm font-medium text-slate-700 truncate max-w-[120px]">
          {controllerName || 'Select Controller'}
        </span>
        <ChevronDown size={14} className="text-slate-400" />
      </button>
      
      {/* Status text */}
      <div className="text-[10px] text-slate-500 mt-0.5 ml-4">
        {getStatusText()}
      </div>
      
      {/* Dropdown */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setIsOpen(false)} 
          />
          
          {/* Menu */}
          <div className="absolute top-full left-0 mt-1 w-64 bg-white rounded-lg shadow-lg border border-slate-200 z-20 overflow-hidden">
            <div className="p-2 border-b border-slate-100">
              <div className="text-xs font-medium text-slate-500 uppercase tracking-wide">
                Available Controllers
              </div>
            </div>
            
            <div className="max-h-64 overflow-y-auto">
              {availableControllers.length === 0 ? (
                <div className="p-3 text-sm text-slate-500 italic">
                  No controllers available
                </div>
              ) : (
                availableControllers.map((controller) => (
                  <button
                    key={controller.project_id}
                    onClick={() => {
                      selectController(controller.project_id);
                      setIsOpen(false);
                    }}
                    className={`w-full px-3 py-2 text-left hover:bg-slate-50 transition-colors flex items-start gap-2 ${
                      controller.project_id === controllerId ? 'bg-purple-50' : ''
                    }`}
                  >
                    <Bot size={16} className={`flex-shrink-0 mt-0.5 ${
                      controller.project_id === controllerId ? 'text-purple-600' : 'text-slate-400'
                    }`} />
                    <div className="flex-1 min-w-0">
                      <div className={`text-sm font-medium truncate ${
                        controller.project_id === controllerId ? 'text-purple-700' : 'text-slate-700'
                      }`}>
                        {controller.name}
                      </div>
                      {controller.description && (
                        <div className="text-xs text-slate-500 truncate">
                          {controller.description}
                        </div>
                      )}
                      {controller.is_builtin && (
                        <span className="inline-block mt-1 text-[10px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded">
                          Built-in
                        </span>
                      )}
                    </div>
                    {controller.project_id === controllerId && (
                      <span className="text-xs text-purple-600">✓</span>
                    )}
                  </button>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// Execution controls
function ExecutionControls() {
  const {
    controllerStatus,
    startController,
    pauseController,
    resumeController,
    stopController,
  } = useChatStore();
  
  const isRunning = controllerStatus === 'running';
  const isPaused = controllerStatus === 'paused';
  const isConnected = controllerStatus === 'connected';
  
  return (
    <div className="flex items-center gap-1">
      {isRunning && (
        <button
          onClick={pauseController}
          className="p-1 text-yellow-600 hover:bg-yellow-50 rounded transition-colors"
          title="Pause"
        >
          <Pause size={14} />
        </button>
      )}
      
      {isPaused && (
        <button
          onClick={resumeController}
          className="p-1 text-green-600 hover:bg-green-50 rounded transition-colors"
          title="Resume"
        >
          <Play size={14} />
        </button>
      )}
      
      {(isRunning || isPaused) && (
        <button
          onClick={stopController}
          className="p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
          title="Stop"
        >
          <Square size={14} />
        </button>
      )}
      
      {isConnected && (
        <button
          onClick={startController}
          className="p-1 text-green-600 hover:bg-green-50 rounded transition-colors"
          title="Start"
        >
          <Play size={14} />
        </button>
      {/* Dropdown */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setIsOpen(false)} 
          />
          
          {/* Menu */}
          <div className="absolute top-full left-0 mt-1 w-64 bg-white rounded-lg shadow-lg border border-slate-200 z-20 overflow-hidden">
            <div className="p-2 border-b border-slate-100">
              <div className="text-xs font-medium text-slate-500 uppercase tracking-wide">
                Available Controllers
              </div>
            </div>
            
            <div className="max-h-64 overflow-y-auto">
              {availableControllers.length === 0 ? (
                <div className="p-3 text-sm text-slate-500 italic">
                  No controllers available
                </div>
              ) : (
                availableControllers.map((controller) => (
                  <button
                    key={controller.project_id}
                    onClick={() => {
                      selectController(controller.project_id);
                      setIsOpen(false);
                    }}
                    className={`w-full px-3 py-2 text-left hover:bg-slate-50 transition-colors flex items-start gap-2 ${
                      controller.project_id === controllerId ? 'bg-purple-50' : ''
                    }`}
                  >
                    <Bot size={16} className={`flex-shrink-0 mt-0.5 ${
                      controller.project_id === controllerId ? 'text-purple-600' : 'text-slate-400'
                    }`} />
                    <div className="flex-1 min-w-0">
                      <div className={`text-sm font-medium truncate ${
                        controller.project_id === controllerId ? 'text-purple-700' : 'text-slate-700'
                      }`}>
                        {controller.name}
                      </div>
                      {controller.description && (
                        <div className="text-xs text-slate-500 truncate">
                          {controller.description}
                        </div>
                      )}
                      {controller.is_builtin && (
                        <span className="inline-block mt-1 text-[10px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded">
                          Built-in
                        </span>
                      )}
                    </div>
                    {controller.project_id === controllerId && (
                      <span className="text-xs text-purple-600">✓</span>
                    )}
                  </button>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// Execution controls
function ExecutionControls() {
  const {
    controllerStatus,
    startController,
    pauseController,
    resumeController,
    stopController,
  } = useChatStore();
  
  const isRunning = controllerStatus === 'running';
  const isPaused = controllerStatus === 'paused';
  const isConnected = controllerStatus === 'connected';
  
  return (
    <div className="flex items-center gap-1">
      {isRunning && (
        <button
          onClick={pauseController}
          className="p-1 text-yellow-600 hover:bg-yellow-50 rounded transition-colors"
          title="Pause"
        >
          <Pause size={14} />
        </button>
      )}
      
      {isPaused && (
        <button
          onClick={resumeController}
          className="p-1 text-green-600 hover:bg-green-50 rounded transition-colors"
          title="Resume"
        >
          <Play size={14} />
        </button>
      )}
      
      {(isRunning || isPaused) && (
        <button
          onClick={stopController}
          className="p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
          title="Stop"
        >
          <Square size={14} />
        </button>
      )}
      
      {isConnected && (
        <button
          onClick={startController}
          className="p-1 text-green-600 hover:bg-green-50 rounded transition-colors"
          title="Start"
        >
          <Play size={14} />
        </button>
      )}
    </div>
  );
}

// Main ChatPanel component
export function ChatPanel() {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  
  const {
    isOpen,
    messages,
    inputValue,
    isInputDisabled,
    isSending,
    pendingInputRequest,
    bufferedMessage,
    isExecutionActive,
    controllerStatus,
    controllerPath,
    isControllerProjectOpen,
    bufferedMessage,
    isExecutionActive,
    controllerStatus,
    controllerPath,
    isControllerProjectOpen,
    closePanel,
    clearMessages,
    setInputValue,
    submitInput,
    openControllerProject,
    syncControllerProjectState,
    refreshBufferStatus,
    openControllerProject,
    syncControllerProjectState,
    refreshBufferStatus,
  } = useChatStore();
  
  // Watch for tab changes
  // Watch for tab changes
  const openTabs = useProjectStore((s) => s.openTabs);
  
  useEffect(() => {
    syncControllerProjectState();
  }, [openTabs, syncControllerProjectState]);
  
  // Refresh buffer status periodically during execution
  useEffect(() => {
    if (isOpen && isExecutionActive) {
      const interval = setInterval(refreshBufferStatus, 1000);
      return () => clearInterval(interval);
    }
  }, [isOpen, isExecutionActive, refreshBufferStatus]);
  
  useEffect(() => {
    if (isOpen) {
      refreshBufferStatus();
    }
  }, [isOpen, refreshBufferStatus]);
  
  // Auto-scroll
    syncControllerProjectState();
  }, [openTabs, syncControllerProjectState]);
  
  // Refresh buffer status periodically during execution
  useEffect(() => {
    if (isOpen && isExecutionActive) {
      const interval = setInterval(refreshBufferStatus, 1000);
      return () => clearInterval(interval);
    }
  }, [isOpen, isExecutionActive, refreshBufferStatus]);
  
  useEffect(() => {
    if (isOpen) {
      refreshBufferStatus();
    }
  }, [isOpen, refreshBufferStatus]);
  
  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // Focus input
  // Focus input
  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
    }
  }, [isOpen]);
  
  const handleSubmit = async () => {
    const trimmedValue = inputValue.trim();
    if (trimmedValue && !isInputDisabled && !isSending) {
      await submitInput(trimmedValue);
    }
  };
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="w-80 h-full flex flex-col bg-slate-50 border-l border-slate-200 shadow-lg">
      {/* Header */}
      <div className="px-3 py-2 bg-white border-b border-slate-200">
        {/* Top row: Controller selector and controls */}
        <div className="flex items-center justify-between">
          <ControllerSelector />
          
          <div className="flex items-center gap-1">
            <ExecutionControls />
            
            {/* View Controller Project - opens as tab to see the plan's graph */}
            <button
              onClick={openControllerProject}
              disabled={controllerStatus === 'disconnected' || !controllerPath}
              className={`p-1.5 rounded transition-colors relative ${
                isControllerProjectOpen
                  ? 'text-purple-600 bg-purple-50 hover:bg-purple-100'
                  : 'text-slate-400 hover:text-slate-600 hover:bg-slate-100'
              } ${(controllerStatus === 'disconnected' || !controllerPath) ? 'opacity-50 cursor-not-allowed' : ''}`}
              title={!controllerPath 
                ? "Demo mode - no project to view"
                : isControllerProjectOpen 
                  ? "Switch to controller tab" 
                  : "Open controller as tab (runs in parallel)"
              }
            >
              <Eye size={14} />
              {/* Show indicator when controller is running but tab is not open */}
              {controllerStatus === 'running' && !isControllerProjectOpen && (
                <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              )}
            </button>
            
            {/* Clear messages */}
            <button
              onClick={clearMessages}
              className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded transition-colors"
              title="Clear messages"
            >
              <Trash2 size={14} />
            </button>
            
            {/* Close */}
            <button
              onClick={closePanel}
              className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded transition-colors"
              title="Close chat"
            >
              <X size={16} />
            </button>
          </div>
      <div className="px-3 py-2 bg-white border-b border-slate-200">
        {/* Top row: Controller selector and controls */}
        <div className="flex items-center justify-between">
          <ControllerSelector />
          
          <div className="flex items-center gap-1">
            <ExecutionControls />
            
            {/* View Controller Project - opens as tab to see the plan's graph */}
            <button
              onClick={openControllerProject}
              disabled={controllerStatus === 'disconnected' || !controllerPath}
              className={`p-1.5 rounded transition-colors relative ${
                isControllerProjectOpen
                  ? 'text-purple-600 bg-purple-50 hover:bg-purple-100'
                  : 'text-slate-400 hover:text-slate-600 hover:bg-slate-100'
              } ${(controllerStatus === 'disconnected' || !controllerPath) ? 'opacity-50 cursor-not-allowed' : ''}`}
              title={!controllerPath 
                ? "Demo mode - no project to view"
                : isControllerProjectOpen 
                  ? "Switch to controller tab" 
                  : "Open controller as tab (runs in parallel)"
              }
            >
              <Eye size={14} />
              {/* Show indicator when controller is running but tab is not open */}
              {controllerStatus === 'running' && !isControllerProjectOpen && (
                <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              )}
            </button>
            
            {/* Clear messages */}
            <button
              onClick={clearMessages}
              className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded transition-colors"
              title="Clear messages"
            >
              <Trash2 size={14} />
            </button>
            
            {/* Close */}
            <button
              onClick={closePanel}
              className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded transition-colors"
              title="Close chat"
            >
              <X size={16} />
            </button>
          </div>
        </div>
      </div>
      
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <div className="p-4 bg-purple-100 rounded-full mb-4">
              <Bot className="w-8 h-8 text-purple-600" />
              <Bot className="w-8 h-8 text-purple-600" />
            </div>
            <h4 className="font-medium text-slate-700 mb-2">Chat Controller</h4>
            <h4 className="font-medium text-slate-700 mb-2">Chat Controller</h4>
            <p className="text-sm text-slate-500 mb-4">
              Select a controller to drive this chat. The controller is a NormCode plan 
              that reads your messages and responds.
              Select a controller to drive this chat. The controller is a NormCode plan 
              that reads your messages and responds.
            </p>
            <div className="text-xs text-slate-400 space-y-1">
              <p>Try typing:</p>
              <p className="font-mono bg-slate-100 px-2 py-1 rounded">"Help me with NormCode"</p>
              <p className="font-mono bg-slate-100 px-2 py-1 rounded">"What can you do?"</p>
              <p className="font-mono bg-slate-100 px-2 py-1 rounded">"Help me with NormCode"</p>
              <p className="font-mono bg-slate-100 px-2 py-1 rounded">"What can you do?"</p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>
      
      {/* Buffered message indicator */}
      {bufferedMessage && (
        <div className="px-4 py-2 bg-amber-50 border-t border-amber-200">
          <div className="flex items-center gap-2 text-amber-700 text-xs mb-1">
            <Loader2 size={12} className="animate-spin" />
            <span className="font-medium">Message buffered, waiting for controller...</span>
          </div>
          <div className="text-sm text-amber-800 bg-amber-100 rounded px-2 py-1 truncate">
            "{bufferedMessage}"
          </div>
        </div>
      )}
      
      {/* Buffered message indicator */}
      {bufferedMessage && (
        <div className="px-4 py-2 bg-amber-50 border-t border-amber-200">
          <div className="flex items-center gap-2 text-amber-700 text-xs mb-1">
            <Loader2 size={12} className="animate-spin" />
            <span className="font-medium">Message buffered, waiting for controller...</span>
          </div>
          <div className="text-sm text-amber-800 bg-amber-100 rounded px-2 py-1 truncate">
            "{bufferedMessage}"
          </div>
        </div>
      )}
      
      {/* Input request indicator */}
      {pendingInputRequest && (
        <div className="px-4 py-2 bg-purple-50 border-t border-purple-200 text-sm text-purple-700">
          <div className="flex items-center gap-2">
            <Terminal size={14} />
            <span>{pendingInputRequest.prompt}</span>
          </div>
        </div>
      )}
      
      {/* Input area */}
      <div className="p-3 bg-white border-t border-slate-200">
        <div className="flex items-end gap-2">
          <textarea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              bufferedMessage 
                ? "Waiting for controller..." 
                : pendingInputRequest?.placeholder 
                  || "Type a message..."
            }
            disabled={isInputDisabled || !!bufferedMessage}
            placeholder={
              bufferedMessage 
                ? "Waiting for controller..." 
                : pendingInputRequest?.placeholder 
                  || "Type a message..."
            }
            disabled={isInputDisabled || !!bufferedMessage}
            rows={1}
            className="flex-1 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
            style={{
              minHeight: '38px',
              maxHeight: '120px',
            }}
          />
          <button
            onClick={handleSubmit}
            disabled={!inputValue.trim() || isInputDisabled || isSending}
            className="p-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Send message"
          >
            {isSending ? (
              <Loader2 size={18} className="animate-spin" />
            ) : (
              <Send size={18} />
            )}
          </button>
        </div>
        
        <div className="mt-2 text-xs text-slate-400 text-center">
          Press <kbd className="px-1 py-0.5 bg-slate-100 rounded text-slate-500">Enter</kbd> to send, 
          <kbd className="px-1 py-0.5 bg-slate-100 rounded text-slate-500 ml-1">Shift+Enter</kbd> for new line
        </div>
      </div>
    </div>
  );
}

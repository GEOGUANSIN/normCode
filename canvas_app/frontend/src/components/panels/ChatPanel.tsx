/**
 * Chat Panel Component
 * 
 * A compiler-driven chat interface that is independent of any project.
 * This panel appears on the right side and works across both Canvas and Editor views.
 * 
 * The chat is driven by a "compiler meta project" - a NormCode plan that orchestrates
 * the conversation, reads user input, and displays compilation results.
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
  ExternalLink,
} from 'lucide-react';
import { useChatStore, type ChatMessage } from '../../stores/chatStore';
import { useProjectStore } from '../../stores/projectStore';

// Message bubble component
function MessageBubble({ message }: { message: ChatMessage }) {
  const [isExpanded, setIsExpanded] = useState(true);
  
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';
  const isCompiler = message.role === 'compiler';
  
  // Determine styling based on role
  const bubbleStyles = isUser
    ? 'bg-blue-600 text-white ml-8'
    : isCompiler
    ? 'bg-purple-50 text-purple-900 border border-purple-200 mr-8'
    : isSystem
    ? 'bg-slate-100 text-slate-600 text-sm italic mx-4'
    : 'bg-white text-slate-800 border border-slate-200 mr-8';
  
  const roleLabel = isCompiler ? 'Compiler' : isSystem ? 'System' : isUser ? 'You' : 'Assistant';
  const roleColor = isCompiler ? 'text-purple-600' : isSystem ? 'text-slate-400' : isUser ? 'text-blue-400' : 'text-slate-500';
  
  return (
    <div className={`${isUser ? 'flex justify-end' : ''}`}>
      <div className={`rounded-lg p-3 max-w-full ${bubbleStyles}`}>
        {/* Role label for non-user messages */}
        {!isUser && (
          <div className={`text-xs font-medium mb-1 flex items-center gap-1 ${roleColor}`}>
            {isCompiler && <Zap size={12} />}
            {roleLabel}
          </div>
        )}
        
        {/* Message content */}
        <div className="whitespace-pre-wrap break-words text-sm">
          {message.content}
        </div>
        
        {/* Metadata/links */}
        {message.metadata?.flowIndex && (
          <div className="mt-2 flex items-center gap-1 text-xs opacity-70">
            <Link2 size={10} />
            <span>Node: {message.metadata.flowIndex}</span>
          </div>
        )}
        
        {/* Timestamp */}
        <div className={`text-xs mt-1 opacity-50 ${isUser ? 'text-right' : ''}`}>
          {message.timestamp.toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}

// Code block component for displaying code in chat
function CodeBlockDisplay({ code, language, title }: { code: string; language: string; title?: string }) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  
  return (
    <div className="bg-slate-900 rounded-lg overflow-hidden mr-8">
      {/* Header */}
      <div 
        className="flex items-center justify-between px-3 py-2 bg-slate-800 text-slate-300 text-xs cursor-pointer"
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        <div className="flex items-center gap-2">
          <Code size={12} />
          <span>{title || language}</span>
        </div>
        {isCollapsed ? <ChevronRight size={14} /> : <ChevronDown size={14} />}
      </div>
      
      {/* Code content */}
      {!isCollapsed && (
        <pre className="p-3 text-sm text-slate-100 overflow-x-auto">
          <code>{code}</code>
        </pre>
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
    compilerStatus,
    compilerProjectPath,
    isCompilerProjectOpen,
    closePanel,
    clearMessages,
    setInputValue,
    submitInput,
    openCompilerProject,
    syncCompilerProjectState,
  } = useChatStore();
  
  // Watch for tab changes to sync compiler project open state
  const openTabs = useProjectStore((s) => s.openTabs);
  
  useEffect(() => {
    // Sync state when tabs change (e.g., when compiler project tab is closed)
    syncCompilerProjectState();
  }, [openTabs, syncCompilerProjectState]);
  
  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // Focus input when panel opens
  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
    }
  }, [isOpen]);
  
  // Handle input submission
  const handleSubmit = async () => {
    const trimmedValue = inputValue.trim();
    if (trimmedValue && !isInputDisabled && !isSending) {
      await submitInput(trimmedValue);
    }
  };
  
  // Handle keyboard shortcuts
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
      <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-slate-200">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-purple-100 rounded-lg">
            <Sparkles className="w-4 h-4 text-purple-600" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-800 text-sm">NormCode Compiler</h3>
            <div className="flex items-center gap-1 text-xs">
              <span className={`w-1.5 h-1.5 rounded-full ${
                compilerStatus === 'connected' ? 'bg-green-500' :
                compilerStatus === 'running' ? 'bg-green-500 animate-pulse' :
                compilerStatus === 'connecting' ? 'bg-yellow-500' :
                'bg-slate-400'
              }`} />
              <span className="text-slate-500 capitalize">{compilerStatus}</span>
              {compilerProjectPath && (
                <>
                  <span className="text-slate-300">•</span>
                  <span className="text-slate-400 truncate max-w-[100px]" title={compilerProjectPath}>
                    {compilerProjectPath.split(/[/\\]/).pop()}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-1">
          {/* View Compiler Project Button */}
          <button
            onClick={openCompilerProject}
            disabled={compilerStatus === 'disconnected'}
            className={`p-1.5 rounded transition-colors flex items-center gap-1 ${
              isCompilerProjectOpen
                ? 'text-purple-600 bg-purple-50 hover:bg-purple-100'
                : 'text-slate-400 hover:text-slate-600 hover:bg-slate-100'
            } ${compilerStatus === 'disconnected' ? 'opacity-50 cursor-not-allowed' : ''}`}
            title={isCompilerProjectOpen ? 'Switch to Compiler Project' : 'View Compiler Plan'}
          >
            <Eye size={14} />
          </button>
          <button
            onClick={clearMessages}
            className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded transition-colors"
            title="Clear messages"
          >
            <Trash2 size={14} />
          </button>
          <button
            onClick={closePanel}
            className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded transition-colors"
            title="Close chat"
          >
            <X size={16} />
          </button>
        </div>
      </div>
      
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 ? (
          // Empty state
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <div className="p-4 bg-purple-100 rounded-full mb-4">
              <MessageSquare className="w-8 h-8 text-purple-600" />
            </div>
            <h4 className="font-medium text-slate-700 mb-2">Compiler Chat</h4>
            <p className="text-sm text-slate-500 mb-4">
              This chat is driven by the NormCode compiler. Start a conversation to compile plans, 
              get help, or interact with your projects.
            </p>
            <div className="text-xs text-slate-400 space-y-1">
              <p>Try typing:</p>
              <p className="font-mono bg-slate-100 px-2 py-1 rounded">"Compile my plan"</p>
              <p className="font-mono bg-slate-100 px-2 py-1 rounded">"Help me write a NormCode plan"</p>
            </div>
          </div>
        ) : (
          // Message list
          <>
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>
      
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
            placeholder={pendingInputRequest?.placeholder || "Type a message..."}
            disabled={isInputDisabled}
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


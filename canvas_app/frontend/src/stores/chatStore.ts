/**
 * Chat state management with Zustand
 * 
 * Manages the chat interface which can be driven by any NormCode project
 * that has chat capabilities (chat paradigms). The user can select which
 * "controller" project drives the chat.
 * 
 * Key concepts:
 * - Controller: A NormCode project that drives the chat conversation
 * - The controller runs via ExecutionController and uses ChatTool for I/O
 * - Messages show which flow_index generated them for transparency
 */

import { create } from 'zustand';
import { 
  chatApi, 
  type ChatMessage as ApiChatMessage, 
  type ChatBufferStatus,
  type ControllerInfo,
  type ControllerState,
} from '../services/api';
import { useProjectStore } from './projectStore';

// Message types for the chat
export type MessageRole = 'user' | 'assistant' | 'system' | 'compiler' | 'controller';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  // Optional metadata for linking to nodes/artifacts
  metadata?: {
    flowIndex?: string;
    artifactType?: string;
    codeLanguage?: string;
    nodeLink?: string;
  };
}

// Code block for displaying code in chat
export interface CodeBlock {
  id: string;
  language: string;
  code: string;
  title?: string;
  collapsible?: boolean;
}

// Artifact for structured data display
export interface ChatArtifact {
  id: string;
  type: 'code' | 'json' | 'table' | 'tree' | 'graph-preview';
  data: unknown;
  title?: string;
}

// Input request from the controller or execution
export interface ChatInputRequest {
  id: string;
  prompt: string;
  inputType: 'text' | 'code' | 'confirm' | 'select';
  options?: string[];
  placeholder?: string;
  source?: 'controller' | 'execution';
}

// Controller status types
export type ControllerStatusType = 
  | 'disconnected' 
  | 'connecting' 
  | 'connected' 
  | 'running' 
  | 'paused' 
  | 'error';

interface ChatState {
  // Panel visibility
  isOpen: boolean;
  
  // Messages
  messages: ChatMessage[];
  
  // Input state
  inputValue: string;
  isInputDisabled: boolean;
  isSending: boolean;
  pendingInputRequest: ChatInputRequest | null;
  
  // Message buffer state (for execution mode)
  bufferedMessage: string | null;
  isExecutionActive: boolean;
  
  // Controller state (NEW)
  availableControllers: ControllerInfo[];
  controllerId: string | null;
  controllerName: string | null;
  controllerPath: string | null;
  controllerStatus: ControllerStatusType;
  currentFlowIndex: string | null;
  isControllerProjectOpen: boolean;
  
  // Error state
  errorMessage: string | null;
  
  // Actions
  togglePanel: () => void;
  openPanel: () => void;
  closePanel: () => void;
  
  // Message actions
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  addMessageFromApi: (msg: ApiChatMessage) => void;
  clearMessages: () => void;
  
  // Input actions
  setInputValue: (value: string) => void;
  setInputDisabled: (disabled: boolean) => void;
  submitInput: (value: string) => Promise<void>;
  
  // Input request actions
  setInputRequest: (request: ChatInputRequest | null) => void;
  respondToInputRequest: (response: string) => Promise<void>;
  
  // Buffer actions
  updateBufferStatus: (status: ChatBufferStatus) => void;
  clearBuffer: () => void;
  
  // Controller actions (NEW)
  loadControllers: () => Promise<void>;
  selectController: (controllerId: string) => Promise<void>;
  setControllerStatus: (status: ControllerStatusType, flowIndex?: string) => void;
  
  // Lifecycle actions
  startController: () => Promise<void>;
  pauseController: () => Promise<void>;
  resumeController: () => Promise<void>;
  stopController: () => Promise<void>;
  loadMessages: () => Promise<void>;
  
  // Project view actions
  openControllerProject: () => Promise<void>;
  syncControllerProjectState: () => void;
  refreshBufferStatus: () => Promise<void>;
}

// Generate unique ID for messages
const generateId = () => `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

export const useChatStore = create<ChatState>((set, get) => ({
  // Initial state
  isOpen: false,
  messages: [],
  inputValue: '',
  isInputDisabled: false,
  isSending: false,
  pendingInputRequest: null,
  bufferedMessage: null,
  isExecutionActive: false,
  
  // Controller state
  availableControllers: [],
  controllerId: null,
  controllerName: null,
  controllerPath: null,
  controllerStatus: 'disconnected',
  currentFlowIndex: null,
  isControllerProjectOpen: false,
  errorMessage: null,
  
  // Panel visibility
  togglePanel: () => {
    const { isOpen } = get();
    if (!isOpen) {
      // Opening panel - start controller if not already started
      const { controllerStatus, startController, loadControllers } = get();
      loadControllers(); // Load available controllers
      if (controllerStatus === 'disconnected') {
        startController();
      }
    }
    set((state) => ({ isOpen: !state.isOpen }));
  },
  openPanel: () => {
    const { controllerStatus, startController, loadControllers } = get();
    loadControllers();
    if (controllerStatus === 'disconnected') {
      startController();
    }
    set({ isOpen: true });
  },
  closePanel: () => set({ isOpen: false }),
  
  // Message actions
  addMessage: (message) => set((state) => ({
    messages: [
      ...state.messages,
      {
        ...message,
        id: generateId(),
        timestamp: new Date(),
      },
    ],
  })),
  
  addMessageFromApi: (msg) => set((state) => {
    // Check if message already exists
    if (state.messages.some(m => m.id === msg.id)) {
      return state;
    }
    return {
      messages: [
        ...state.messages,
        {
          id: msg.id,
          role: msg.role as MessageRole,
          content: msg.content,
          timestamp: new Date(msg.timestamp),
          metadata: msg.metadata as ChatMessage['metadata'],
        },
      ],
    };
  }),
  
  clearMessages: async () => {
    try {
      await chatApi.clearMessages();
      set({ messages: [] });
    } catch (error) {
      console.error('Failed to clear messages:', error);
    }
  },
  
  // Input actions
  setInputValue: (value) => set({ inputValue: value }),
  setInputDisabled: (disabled) => set({ isInputDisabled: disabled }),
  
  submitInput: async (value) => {
    const { pendingInputRequest, isSending, bufferedMessage } = get();
    if (isSending) return;
    
    set({ isSending: true, isInputDisabled: true });
    
    try {
      // If there's a pending input request, respond to it
      if (pendingInputRequest) {
        get().addMessage({ role: 'user', content: value });
        
        if (pendingInputRequest.source === 'execution') {
          await chatApi.submitExecutionInput(pendingInputRequest.id, value);
        } else {
          await chatApi.submitInput(pendingInputRequest.id, value);
        }
        set({ pendingInputRequest: null });
      } else {
        // Check buffer status
        try {
          const bufferStatus = await chatApi.getBufferStatus();
          if (bufferStatus.execution_active) {
            if (bufferStatus.has_buffered_message) {
              console.warn('Buffer already full');
              set({ isSending: false, isInputDisabled: true });
              return;
            }
            
            const bufferResult = await chatApi.bufferMessage(value);
            if (bufferResult.success) {
              get().addMessage({ role: 'user', content: value });
              
              if (bufferResult.delivered) {
                set({ bufferedMessage: null });
              } else {
                set({ bufferedMessage: bufferResult.buffered_message || value });
              }
            } else if (bufferResult.buffer_full) {
              set({ 
                bufferedMessage: bufferResult.buffered_message || null,
                isSending: false, 
                isInputDisabled: true 
              });
              return;
            } else {
              await chatApi.sendMessage(value);
            }
          } else {
            await chatApi.sendMessage(value);
          }
        } catch (bufferError) {
          console.warn('Buffer check failed, sending regular message:', bufferError);
          await chatApi.sendMessage(value);
        }
      }
      
      set({ inputValue: '' });
    } catch (error) {
      console.error('Failed to submit input:', error);
    } finally {
      const { bufferedMessage: currentBuffer } = get();
      set({ 
        isSending: false, 
        isInputDisabled: currentBuffer !== null 
      });
    }
  },
  
  // Input request actions
  setInputRequest: (request) => set({ 
    pendingInputRequest: request,
    isInputDisabled: false,
  }),
  
  respondToInputRequest: async (response) => {
    const { pendingInputRequest } = get();
    
    if (pendingInputRequest) {
      set({ isSending: true, isInputDisabled: true });
      
      try {
        get().addMessage({ role: 'user', content: response });
        
        if (pendingInputRequest.source === 'execution') {
          await chatApi.submitExecutionInput(pendingInputRequest.id, response);
        } else {
          await chatApi.submitInput(pendingInputRequest.id, response);
        }
        set({ 
          pendingInputRequest: null,
          inputValue: '',
        });
      } catch (error) {
        console.error('Failed to respond to input request:', error);
      } finally {
        set({ isSending: false, isInputDisabled: false });
      }
    }
  },
  
  // Controller actions (NEW)
  loadControllers: async () => {
    try {
      const response = await chatApi.listControllers();
      set({ 
        availableControllers: response.controllers,
        controllerId: response.current_controller_id,
      });
      
      // If there's a connected controller, also load its full state (including path)
      if (response.current_controller_id) {
        const state = await chatApi.getControllerState();
        set({
          controllerName: state.controller_name || null,
          controllerPath: state.controller_path || null,
          controllerStatus: state.status as ControllerStatusType,
          currentFlowIndex: state.current_flow_index || null,
        });
      }
    } catch (error) {
      console.error('Failed to load controllers:', error);
    }
  },
  
  selectController: async (controllerId: string) => {
    set({ controllerStatus: 'connecting' });
    
    try {
      const state = await chatApi.selectController(controllerId);
      
      set({
        controllerId: state.controller_id,
        controllerName: state.controller_name,
        controllerPath: state.controller_path,
        controllerStatus: state.status as ControllerStatusType,
        currentFlowIndex: state.current_flow_index,
        errorMessage: state.error_message,
      });
      
      // Load messages for the new controller
      await get().loadMessages();
    } catch (error) {
      console.error('Failed to select controller:', error);
      set({ 
        controllerStatus: 'error',
        errorMessage: error instanceof Error ? error.message : String(error),
      });
    }
  },
  
  setControllerStatus: (status, flowIndex) => set({ 
    controllerStatus: status,
    currentFlowIndex: flowIndex ?? null,
    isExecutionActive: status === 'running',
  }),
  
  // Lifecycle actions
  startController: async () => {
    set({ controllerStatus: 'connecting' });
    
    try {
      const response = await chatApi.startController();
      
      if (response.success) {
        set({ 
          controllerId: response.controller_id || null,
          controllerName: response.controller_name || null,
          controllerPath: response.controller_path || null,
          controllerStatus: response.status as ControllerStatusType,
        });
        
        await get().loadMessages();
      } else {
        set({ 
          controllerStatus: 'error',
          errorMessage: response.error || 'Failed to start controller',
        });
        console.error('Failed to start controller:', response.error);
      }
    } catch (error) {
      set({ 
        controllerStatus: 'error',
        errorMessage: error instanceof Error ? error.message : String(error),
      });
      console.error('Failed to start controller:', error);
    }
  },
  
  pauseController: async () => {
    try {
      await chatApi.pauseController();
      set({ controllerStatus: 'paused' });
    } catch (error) {
      console.error('Failed to pause controller:', error);
    }
  },
  
  resumeController: async () => {
    try {
      await chatApi.resumeController();
      set({ controllerStatus: 'running' });
    } catch (error) {
      console.error('Failed to resume controller:', error);
    }
  },
  
  stopController: async () => {
    try {
      await chatApi.stopController();
      set({ controllerStatus: 'connected' });
    } catch (error) {
      console.error('Failed to stop controller:', error);
    }
  },
  
  loadMessages: async () => {
    try {
      const response = await chatApi.getMessages();
      
      const messages: ChatMessage[] = response.messages.map(msg => ({
        id: msg.id,
        role: msg.role as MessageRole,
        content: msg.content,
        timestamp: new Date(msg.timestamp),
        metadata: msg.metadata as ChatMessage['metadata'],
      }));
      
      set({ messages });
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  },
  
  openControllerProject: async () => {
    const { controllerPath, controllerName } = get();
    
    if (!controllerPath) {
      console.error('Cannot open controller project: no path available');
      return;
    }
    
    const projectStore = useProjectStore.getState();
    const normalizedPath = controllerPath.replace(/\\/g, '/').toLowerCase();
    const existingTab = projectStore.openTabs.find(t => 
      t.directory.replace(/\\/g, '/').toLowerCase() === normalizedPath
    );
    
    if (existingTab) {
      await projectStore.switchTab(existingTab.id);
      set({ isControllerProjectOpen: true });
      return;
    }
    
    try {
      const success = await projectStore.openProjectAsTab(
        controllerPath,
        undefined,
        undefined,
        true, // Make active
        true  // Read-only
      );
      
      if (success) {
        set({ isControllerProjectOpen: true });
      }
    } catch (error) {
      console.error('Failed to open controller project:', error);
    }
  },
  
  syncControllerProjectState: () => {
    const { controllerPath } = get();
    if (!controllerPath) {
      set({ isControllerProjectOpen: false });
      return;
    }
    
    const projectStore = useProjectStore.getState();
    const normalizedPath = controllerPath.replace(/\\/g, '/').toLowerCase();
    const isOpen = projectStore.openTabs.some(t => 
      t.directory.replace(/\\/g, '/').toLowerCase() === normalizedPath
    );
    
    set({ isControllerProjectOpen: isOpen });
  },
  
  // Buffer actions
  updateBufferStatus: (status) => {
    set({
      isExecutionActive: status.execution_active,
      bufferedMessage: status.buffered_message,
      isInputDisabled: status.has_buffered_message,
    });
  },
  
  clearBuffer: () => {
    set({ 
      bufferedMessage: null,
      isInputDisabled: false,
    });
  },
  
  refreshBufferStatus: async () => {
    try {
      const status = await chatApi.getBufferStatus();
      get().updateBufferStatus(status);
    } catch (error) {
      console.error('Failed to refresh buffer status:', error);
    }
  },
}));

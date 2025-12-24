/**
 * Chat state management with Zustand
 * 
 * Manages the compiler-driven chat interface that is independent of any project.
 * The chat panel can be opened/closed independently and is driven by a 
 * "compiler meta project" that orchestrates the conversation.
 */

import { create } from 'zustand';
import { chatApi, type ChatMessage as ApiChatMessage } from '../services/api';
import { useProjectStore } from './projectStore';

// Message types for the chat
export type MessageRole = 'user' | 'assistant' | 'system' | 'compiler';

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

// Input request from the compiler
export interface ChatInputRequest {
  id: string;
  prompt: string;
  inputType: 'text' | 'code' | 'confirm' | 'select';
  options?: string[];
  placeholder?: string;
}

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
  
  // Compiler connection state
  compilerProjectId: string | null;
  compilerProjectPath: string | null;
  compilerProjectConfigFile: string | null;
  isCompilerProjectOpen: boolean;
  compilerStatus: 'disconnected' | 'connecting' | 'connected' | 'running';
  
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
  
  // Input request actions (from compiler)
  setInputRequest: (request: ChatInputRequest | null) => void;
  respondToInputRequest: (response: string) => Promise<void>;
  
  // Compiler connection actions
  setCompilerProjectId: (id: string | null) => void;
  setCompilerProjectPath: (path: string | null) => void;
  setCompilerProjectConfigFile: (configFile: string | null) => void;
  setCompilerStatus: (status: ChatState['compilerStatus']) => void;
  
  // API actions
  startCompiler: () => Promise<void>;
  stopCompiler: () => Promise<void>;
  loadMessages: () => Promise<void>;
  openCompilerProject: () => Promise<void>;
  syncCompilerProjectState: () => void;
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
  compilerProjectId: null,
  compilerProjectPath: null,
  compilerProjectConfigFile: null,
  isCompilerProjectOpen: false,
  compilerStatus: 'disconnected',
  
  // Panel visibility
  togglePanel: () => {
    const { isOpen } = get();
    if (!isOpen) {
      // Opening panel - start compiler if not already started
      const { compilerStatus, startCompiler } = get();
      if (compilerStatus === 'disconnected') {
        startCompiler();
      }
    }
    set((state) => ({ isOpen: !state.isOpen }));
  },
  openPanel: () => {
    const { compilerStatus, startCompiler } = get();
    if (compilerStatus === 'disconnected') {
      startCompiler();
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
    const { pendingInputRequest, isSending } = get();
    if (isSending) return;
    
    set({ isSending: true, isInputDisabled: true });
    
    try {
      // If there's a pending input request, respond to it
      if (pendingInputRequest) {
        await chatApi.submitInput(pendingInputRequest.id, value);
        set({ pendingInputRequest: null });
      } else {
        // Otherwise, send as a new message
        await chatApi.sendMessage(value);
      }
      
      set({ inputValue: '' });
    } catch (error) {
      console.error('Failed to submit input:', error);
    } finally {
      set({ isSending: false, isInputDisabled: false });
    }
  },
  
  // Input request actions
  setInputRequest: (request) => set({ 
    pendingInputRequest: request,
    isInputDisabled: false, // Enable input when request comes in
  }),
  
  respondToInputRequest: async (response) => {
    const { pendingInputRequest } = get();
    
    if (pendingInputRequest) {
      set({ isSending: true, isInputDisabled: true });
      
      try {
        await chatApi.submitInput(pendingInputRequest.id, response);
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
  
  // Compiler connection actions
  setCompilerProjectId: (id) => set({ compilerProjectId: id }),
  setCompilerProjectPath: (path) => set({ compilerProjectPath: path }),
  setCompilerProjectConfigFile: (configFile) => set({ compilerProjectConfigFile: configFile }),
  setCompilerStatus: (status) => set({ compilerStatus: status }),
  
  // API actions
  startCompiler: async () => {
    set({ compilerStatus: 'connecting' });
    
    try {
      const response = await chatApi.startCompiler();
      
      if (response.success) {
        set({ 
          compilerProjectId: response.project_id || null,
          compilerProjectPath: response.project_path || null,
          compilerProjectConfigFile: response.project_config_file || null,
          compilerStatus: response.status as ChatState['compilerStatus'],
        });
        
        // Load existing messages
        await get().loadMessages();
      } else {
        set({ compilerStatus: 'disconnected' });
        console.error('Failed to start compiler:', response.error);
      }
    } catch (error) {
      set({ compilerStatus: 'disconnected' });
      console.error('Failed to start compiler:', error);
    }
  },
  
  stopCompiler: async () => {
    try {
      await chatApi.stopCompiler();
      set({ compilerStatus: 'connected' });
    } catch (error) {
      console.error('Failed to stop compiler:', error);
    }
  },
  
  loadMessages: async () => {
    try {
      const response = await chatApi.getMessages();
      
      // Convert API messages to local format
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
  
  openCompilerProject: async () => {
    const { compilerProjectPath, compilerProjectConfigFile } = get();
    
    // Validate we have enough info to open the project
    if (!compilerProjectPath) {
      console.error('Cannot open compiler project: no project_path available');
      return;
    }
    
    // Check if already open by matching path (normalize path for comparison)
    const projectStore = useProjectStore.getState();
    const normalizedPath = compilerProjectPath.replace(/\\/g, '/').toLowerCase();
    const existingTab = projectStore.openTabs.find(t => 
      t.directory.replace(/\\/g, '/').toLowerCase() === normalizedPath
    );
    
    if (existingTab) {
      // Already open, just switch to it (don't re-open, just switch)
      await projectStore.switchTab(existingTab.id);
      set({ isCompilerProjectOpen: true });
      return;
    }
    
    // Open the compiler project as a new tab
    // Note: We use project_path, not project_id, because "compiler-meta" is
    // not a registered project ID - it's just a static identifier
    // The compiler project is read-only (view and execute only)
    try {
      const success = await projectStore.openProjectAsTab(
        compilerProjectPath,
        compilerProjectConfigFile || undefined,
        undefined, // Don't use compilerProjectId - it's not a real registered ID
        true, // Make it active so user can see it
        true // Read-only mode - cannot modify the compiler project
      );
      
      if (success) {
        set({ isCompilerProjectOpen: true });
      }
    } catch (error) {
      console.error('Failed to open compiler project:', error);
    }
  },
  
  // Check if compiler project is currently open in tabs
  syncCompilerProjectState: () => {
    const { compilerProjectPath } = get();
    if (!compilerProjectPath) {
      set({ isCompilerProjectOpen: false });
      return;
    }
    
    const projectStore = useProjectStore.getState();
    const normalizedPath = compilerProjectPath.replace(/\\/g, '/').toLowerCase();
    const isOpen = projectStore.openTabs.some(t => 
      t.directory.replace(/\\/g, '/').toLowerCase() === normalizedPath
    );
    
    set({ isCompilerProjectOpen: isOpen });
  },
}));

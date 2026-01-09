/**
 * Canvas Command Store
 * 
 * Handles canvas commands received from the backend (via WebSocket)
 * and queues them for execution by the GraphCanvas component.
 */

import { create } from 'zustand';

export interface CanvasCommand {
  id: string;
  type: string;
  params: Record<string, unknown>;
  timestamp: number;
}

interface CanvasCommandStore {
  // Queue of pending commands
  pendingCommands: CanvasCommand[];
  
  // Last executed command (for debugging)
  lastExecutedCommand: CanvasCommand | null;
  
  // Add a new command to the queue
  addCommand: (type: string, params: Record<string, unknown>) => void;
  
  // Pop the next command from the queue
  popCommand: () => CanvasCommand | null;
  
  // Clear all pending commands
  clearCommands: () => void;
}

export const useCanvasCommandStore = create<CanvasCommandStore>((set, get) => ({
  pendingCommands: [],
  lastExecutedCommand: null,
  
  addCommand: (type, params) => {
    const command: CanvasCommand = {
      id: `cmd-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type,
      params,
      timestamp: Date.now(),
    };
    
    set((state) => ({
      pendingCommands: [...state.pendingCommands, command],
    }));
    
    console.log('[CanvasCommandStore] Command added:', command);
  },
  
  popCommand: () => {
    const { pendingCommands } = get();
    if (pendingCommands.length === 0) {
      return null;
    }
    
    const [command, ...rest] = pendingCommands;
    set({
      pendingCommands: rest,
      lastExecutedCommand: command,
    });
    
    return command;
  },
  
  clearCommands: () => {
    set({ pendingCommands: [] });
  },
}));


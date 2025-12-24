/**
 * Execution state management with Zustand
 */

import { create } from 'zustand';
import type { ExecutionStatus, NodeStatus, StepProgress } from '../types/execution';

interface LogEntry {
  flowIndex: string;
  level: string;
  message: string;
  timestamp: Date;
}

// User input request from backend
export interface UserInputRequest {
  request_id: string;
  prompt: string;
  interaction_type: 'text_input' | 'text_editor' | 'confirm' | 'select' | 'multi_file_input';
  options?: {
    initial_content?: string;
    initial_directory?: string;
    choices?: string[];
    [key: string]: unknown;
  };
  created_at?: number;
}

interface ExecutionState {
  // Status
  status: ExecutionStatus;
  currentInference: string | null;
  completedCount: number;
  totalCount: number;
  cycleCount: number;

  // Node statuses
  nodeStatuses: Record<string, NodeStatus>;

  // Breakpoints
  breakpoints: Set<string>;

  // Logs
  logs: LogEntry[];

  // Run info
  runId: string | null;

  // Step progress tracking (per flow_index)
  stepProgress: Record<string, StepProgress>;
  
  // Verbose logging mode
  verboseLogging: boolean;

  // User input requests (human-in-the-loop)
  userInputRequests: UserInputRequest[];

  // Actions
  setStatus: (status: ExecutionStatus) => void;
  setCurrentInference: (flowIndex: string | null) => void;
  setProgress: (completed: number, total: number, cycle?: number) => void;
  setNodeStatus: (nodeId: string, status: NodeStatus) => void;
  setNodeStatuses: (statuses: Record<string, NodeStatus>) => void;
  addBreakpoint: (flowIndex: string) => void;
  removeBreakpoint: (flowIndex: string) => void;
  toggleBreakpoint: (flowIndex: string) => void;
  addLog: (log: Omit<LogEntry, 'timestamp'>) => void;
  clearLogs: () => void;
  setRunId: (runId: string | null) => void;
  setStepProgress: (flowIndex: string, progress: StepProgress) => void;
  updateStepProgress: (flowIndex: string, update: Partial<StepProgress>) => void;
  clearStepProgress: (flowIndex?: string) => void;
  setVerboseLogging: (enabled: boolean) => void;
  // User input actions
  addUserInputRequest: (request: UserInputRequest) => void;
  removeUserInputRequest: (requestId: string) => void;
  clearUserInputRequests: () => void;
  reset: () => void;
}

export const useExecutionStore = create<ExecutionState>((set, get) => ({
  status: 'idle',
  currentInference: null,
  completedCount: 0,
  totalCount: 0,
  cycleCount: 0,
  nodeStatuses: {},
  breakpoints: new Set(),
  logs: [],
  runId: null,
  stepProgress: {},
  verboseLogging: false,
  userInputRequests: [],

  setStatus: (status) => set({ status }),

  setCurrentInference: (flowIndex) => set({ currentInference: flowIndex }),

  setProgress: (completed, total, cycle) => set({ 
    completedCount: completed, 
    totalCount: total,
    ...(cycle !== undefined && { cycleCount: cycle })
  }),

  setNodeStatus: (nodeId, status) =>
    set((state) => ({
      nodeStatuses: { ...state.nodeStatuses, [nodeId]: status },
    })),

  setNodeStatuses: (statuses) => set({ nodeStatuses: statuses }),

  addBreakpoint: (flowIndex) =>
    set((state) => ({
      breakpoints: new Set([...state.breakpoints, flowIndex]),
    })),

  removeBreakpoint: (flowIndex) =>
    set((state) => {
      const newBreakpoints = new Set(state.breakpoints);
      newBreakpoints.delete(flowIndex);
      return { breakpoints: newBreakpoints };
    }),

  toggleBreakpoint: (flowIndex) => {
    const { breakpoints, addBreakpoint, removeBreakpoint } = get();
    if (breakpoints.has(flowIndex)) {
      removeBreakpoint(flowIndex);
    } else {
      addBreakpoint(flowIndex);
    }
  },

  addLog: (log) =>
    set((state) => ({
      logs: [...state.logs, { ...log, timestamp: new Date() }],
    })),

  clearLogs: () => set({ logs: [] }),

  setRunId: (runId) => set({ runId }),

  setStepProgress: (flowIndex, progress) =>
    set((state) => ({
      stepProgress: { ...state.stepProgress, [flowIndex]: progress },
    })),

  updateStepProgress: (flowIndex, update) =>
    set((state) => {
      const current = state.stepProgress[flowIndex] || {
        flow_index: flowIndex,
        sequence_type: null,
        current_step: null,
        current_step_index: 0,
        total_steps: 0,
        steps: [],
        completed_steps: [],
      };
      return {
        stepProgress: {
          ...state.stepProgress,
          [flowIndex]: { ...current, ...update },
        },
      };
    }),

  clearStepProgress: (flowIndex) =>
    set((state) => {
      if (flowIndex) {
        const { [flowIndex]: _, ...rest } = state.stepProgress;
        return { stepProgress: rest };
      }
      return { stepProgress: {} };
    }),

  setVerboseLogging: (enabled) => set({ verboseLogging: enabled }),

  // User input actions
  addUserInputRequest: (request) =>
    set((state) => ({
      userInputRequests: [...state.userInputRequests, request],
    })),

  removeUserInputRequest: (requestId) =>
    set((state) => ({
      userInputRequests: state.userInputRequests.filter((r) => r.request_id !== requestId),
    })),

  clearUserInputRequests: () => set({ userInputRequests: [] }),

  reset: () =>
    set({
      status: 'idle',
      currentInference: null,
      completedCount: 0,
      totalCount: 0,
      cycleCount: 0,
      nodeStatuses: {},
      logs: [],
      runId: null,
      stepProgress: {},
      userInputRequests: [],
    }),
}));

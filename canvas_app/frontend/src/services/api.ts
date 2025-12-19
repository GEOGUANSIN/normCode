/**
 * REST API client for NormCode Canvas backend
 */

import type { GraphData, GraphNode, GraphStats } from '../types/graph';
import type { 
  ExecutionState, 
  LoadRepositoryRequest, 
  LoadResponse, 
  CommandResponse,
  RepositoryExample,
} from '../types/execution';

const API_BASE = '/api';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, error.detail || 'Request failed');
  }
  
  return response.json();
}

// Repository endpoints
export const repositoryApi = {
  load: (request: LoadRepositoryRequest): Promise<LoadResponse> =>
    fetchJson(`${API_BASE}/repositories/load`, {
      method: 'POST',
      body: JSON.stringify(request),
    }),
  
  getExamples: (): Promise<{ examples: RepositoryExample[] }> =>
    fetchJson(`${API_BASE}/repositories/examples`),
};

// Graph endpoints
export const graphApi = {
  get: (): Promise<GraphData> =>
    fetchJson(`${API_BASE}/graph`),
  
  getNode: (nodeId: string): Promise<GraphNode> =>
    fetchJson(`${API_BASE}/graph/node/${encodeURIComponent(nodeId)}`),
  
  getNodeData: (nodeId: string): Promise<{ node: GraphNode; concept: unknown }> =>
    fetchJson(`${API_BASE}/graph/node/${encodeURIComponent(nodeId)}/data`),
  
  getStats: (): Promise<GraphStats> =>
    fetchJson(`${API_BASE}/graph/stats`),
};

// Execution endpoints
export const executionApi = {
  getState: (): Promise<ExecutionState> =>
    fetchJson(`${API_BASE}/execution/state`),
  
  start: (): Promise<CommandResponse> =>
    fetchJson(`${API_BASE}/execution/start`, { method: 'POST' }),
  
  pause: (): Promise<CommandResponse> =>
    fetchJson(`${API_BASE}/execution/pause`, { method: 'POST' }),
  
  resume: (): Promise<CommandResponse> =>
    fetchJson(`${API_BASE}/execution/resume`, { method: 'POST' }),
  
  step: (): Promise<CommandResponse> =>
    fetchJson(`${API_BASE}/execution/step`, { method: 'POST' }),
  
  stop: (): Promise<CommandResponse> =>
    fetchJson(`${API_BASE}/execution/stop`, { method: 'POST' }),
  
  setBreakpoint: (flowIndex: string, enabled: boolean = true): Promise<CommandResponse> =>
    fetchJson(`${API_BASE}/execution/breakpoints`, {
      method: 'POST',
      body: JSON.stringify({ flow_index: flowIndex, enabled }),
    }),
  
  clearBreakpoint: (flowIndex: string): Promise<CommandResponse> =>
    fetchJson(`${API_BASE}/execution/breakpoints/${encodeURIComponent(flowIndex)}`, {
      method: 'DELETE',
    }),
  
  getBreakpoints: (): Promise<{ breakpoints: string[] }> =>
    fetchJson(`${API_BASE}/execution/breakpoints`),
};

export { ApiError };

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
  ExecutionConfig,
} from '../types/execution';
import type {
  ProjectResponse,
  RecentProjectsResponse,
  OpenProjectRequest,
  CreateProjectRequest,
  SaveProjectRequest,
  ExecutionSettings,
} from '../types/project';

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
  
  restart: (): Promise<CommandResponse> =>
    fetchJson(`${API_BASE}/execution/restart`, { method: 'POST' }),
  
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
  
  getConfig: (): Promise<ExecutionConfig> =>
    fetchJson(`${API_BASE}/execution/config`),
  
  getReference: (conceptName: string): Promise<ReferenceData> =>
    fetchJson(`${API_BASE}/execution/reference/${encodeURIComponent(conceptName)}`),
  
  getAllReferences: (): Promise<Record<string, ReferenceData>> =>
    fetchJson(`${API_BASE}/execution/references`),
};

// Reference data type
export interface ReferenceData {
  concept_name: string;
  has_reference: boolean;
  data: unknown;
  axes: string[];
  shape: number[];
}

// Project endpoints
export const projectApi = {
  getCurrent: (): Promise<ProjectResponse | null> =>
    fetchJson(`${API_BASE}/project/current`),
  
  open: (request: OpenProjectRequest): Promise<ProjectResponse> =>
    fetchJson(`${API_BASE}/project/open`, {
      method: 'POST',
      body: JSON.stringify(request),
    }),
  
  create: (request: CreateProjectRequest): Promise<ProjectResponse> =>
    fetchJson(`${API_BASE}/project/create`, {
      method: 'POST',
      body: JSON.stringify(request),
    }),
  
  save: (request: SaveProjectRequest): Promise<ProjectResponse> =>
    fetchJson(`${API_BASE}/project/save`, {
      method: 'POST',
      body: JSON.stringify(request),
    }),
  
  close: (): Promise<{ status: string }> =>
    fetchJson(`${API_BASE}/project/close`, { method: 'POST' }),
  
  getRecent: (): Promise<RecentProjectsResponse> =>
    fetchJson(`${API_BASE}/project/recent`),
  
  clearRecent: (): Promise<{ status: string }> =>
    fetchJson(`${API_BASE}/project/recent`, { method: 'DELETE' }),
  
  loadRepositories: (): Promise<{ status: string; concepts_path: string; inferences_path: string; breakpoints_restored: number }> =>
    fetchJson(`${API_BASE}/project/load-repositories`, { method: 'POST' }),
  
  getPaths: (): Promise<{ concepts: string; inferences: string; inputs?: string; base_dir: string }> =>
    fetchJson(`${API_BASE}/project/paths`),
  
  updateSettings: (settings: ExecutionSettings): Promise<ProjectResponse> =>
    fetchJson(`${API_BASE}/project/settings`, {
      method: 'PUT',
      body: JSON.stringify(settings),
    }),
};

export { ApiError };

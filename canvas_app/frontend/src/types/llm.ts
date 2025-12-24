/**
 * LLM configuration types for the Canvas app
 */

export type LLMProvider = 
  | 'openai'
  | 'anthropic'
  | 'azure'
  | 'dashscope'
  | 'ollama'
  | 'custom';

export interface LLMProviderConfig {
  id: string;
  name: string;
  provider: LLMProvider;
  api_key?: string;
  base_url?: string;
  model: string;
  temperature: number;
  max_tokens?: number;
  top_p?: number;
  is_default: boolean;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
  description?: string;
}

export interface LLMProviderPreset {
  provider: LLMProvider;
  name: string;
  base_url: string;
  default_model: string;
  available_models: string[];
  requires_api_key: boolean;
  description: string;
}

export interface LLMSettingsConfig {
  providers: LLMProviderConfig[];
  default_provider_id?: string;
  timeout_seconds: number;
  retry_count: number;
  updated_at: string;
}

// API Request types
export interface CreateProviderRequest {
  name: string;
  provider: LLMProvider;
  api_key?: string;
  base_url?: string;
  model: string;
  temperature?: number;
  max_tokens?: number;
  is_default?: boolean;
  description?: string;
}

export interface UpdateProviderRequest {
  name?: string;
  provider?: LLMProvider;
  api_key?: string;
  base_url?: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  is_default?: boolean;
  is_enabled?: boolean;
  description?: string;
}

export interface TestProviderRequest {
  provider_id?: string;
  provider?: LLMProvider;
  api_key?: string;
  base_url?: string;
  model?: string;
}

export interface TestProviderResponse {
  success: boolean;
  message: string;
  response_preview?: string;
  latency_ms?: number;
}

export interface ProviderListResponse {
  providers: LLMProviderConfig[];
  default_provider_id?: string;
}

export interface ProviderPresetsResponse {
  presets: Record<string, LLMProviderPreset>;
}

// Provider display info
export const PROVIDER_DISPLAY_INFO: Record<LLMProvider, { label: string; color: string; icon: string }> = {
  openai: { label: 'OpenAI', color: 'bg-green-100 text-green-700', icon: '🤖' },
  anthropic: { label: 'Anthropic', color: 'bg-orange-100 text-orange-700', icon: '🧠' },
  azure: { label: 'Azure', color: 'bg-blue-100 text-blue-700', icon: '☁️' },
  dashscope: { label: 'DashScope', color: 'bg-purple-100 text-purple-700', icon: '🚀' },
  ollama: { label: 'Ollama', color: 'bg-gray-100 text-gray-700', icon: '🦙' },
  custom: { label: 'Custom', color: 'bg-slate-100 text-slate-700', icon: '⚙️' },
};

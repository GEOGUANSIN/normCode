/**
 * LLM Settings Panel - Configure LLM providers and endpoints
 */

import { useEffect, useState } from 'react';
import {
  Bot,
  Plus,
  Trash2,
  Edit2,
  Check,
  X,
  Star,
  TestTube,
  Loader2,
  AlertCircle,
  ChevronDown,
  ChevronRight,
  Key,
  Globe,
  Zap,
  Download,
  Eye,
  EyeOff,
} from 'lucide-react';
import { useLLMStore } from '../../stores/llmStore';
import type {
  LLMProviderConfig,
  LLMProvider,
  CreateProviderRequest,
  LLMProviderPreset,
} from '../../types/llm';
import { PROVIDER_DISPLAY_INFO } from '../../types/llm';

interface LLMSettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export function LLMSettingsPanel({ isOpen, onClose }: LLMSettingsPanelProps) {
  const {
    providers,
    presets,
    defaultProviderId,
    isLoading,
    isTestingConnection,
    error,
    fetchProviders,
    fetchPresets,
    createProvider,
    updateProvider,
    deleteProvider,
    setDefaultProvider,
    testProvider,
    importFromYaml,
    clearError,
  } = useLLMStore();

  const [showAddForm, setShowAddForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, { success: boolean; message: string }>>({});
  const [expandedPresets, setExpandedPresets] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchProviders();
      fetchPresets();
    }
  }, [isOpen, fetchProviders, fetchPresets]);

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-gradient-to-r from-blue-50 to-purple-50">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-blue-600" />
            <h2 className="font-semibold text-slate-800">LLM Settings</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <X className="w-4 h-4 text-slate-500" />
          </button>
        </div>

        {/* Error display */}
        {error && (
          <div className="mx-6 mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm">{error}</span>
            <button onClick={clearError} className="ml-auto text-red-500 hover:text-red-700">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Quick Actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowAddForm(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add Provider
            </button>
            <button
              onClick={async () => {
                const count = await importFromYaml();
                if (count > 0) {
                  setTestResults({});
                }
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-slate-100 text-slate-700 rounded hover:bg-slate-200 transition-colors"
              title="Import providers from settings.yaml"
            >
              <Download className="w-4 h-4" />
              Import YAML
            </button>
          </div>

          {/* Presets section - collapsed by default */}
          <div className="border border-slate-200 rounded overflow-hidden">
            <button
              onClick={() => setExpandedPresets(!expandedPresets)}
              className="w-full flex items-center justify-between px-3 py-2 bg-slate-50 hover:bg-slate-100 transition-colors text-sm"
            >
              <div className="flex items-center gap-2 font-medium text-slate-700">
                <Zap className="w-3 h-3 text-amber-500" />
                Quick Setup from Presets
              </div>
              {expandedPresets ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
            </button>
            {expandedPresets && (
              <div className="p-3 flex flex-wrap gap-2">
                {Object.entries(presets).map(([key, preset]) => (
                  <PresetCard
                    key={key}
                    presetKey={key}
                    preset={preset}
                    onAdd={() => setShowAddForm(true)}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Providers list */}
          <div className="space-y-2">
            <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wide">Configured Providers</h3>
            
            {isLoading && providers.length === 0 ? (
              <div className="flex items-center justify-center py-6 text-slate-500 text-sm">
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                Loading...
              </div>
            ) : providers.length === 0 ? (
              <div className="text-center py-6 text-slate-500">
                <Bot className="w-10 h-10 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No providers configured</p>
                <p className="text-xs">Add a provider or import from YAML</p>
              </div>
            ) : (
              <div className="space-y-2">
                {providers.map((provider) => (
                  <ProviderCard
                    key={provider.id}
                    provider={provider}
                    isDefault={provider.id === defaultProviderId}
                    isEditing={editingId === provider.id}
                    testResult={testResults[provider.id]}
                    isTesting={isTestingConnection}
                    onEdit={() => setEditingId(provider.id)}
                    onCancelEdit={() => setEditingId(null)}
                    onSave={async (updates) => {
                      await updateProvider(provider.id, updates);
                      setEditingId(null);
                    }}
                    onDelete={() => deleteProvider(provider.id)}
                    onSetDefault={() => setDefaultProvider(provider.id)}
                    onTest={async () => {
                      const result = await testProvider(provider.id);
                      setTestResults(prev => ({ ...prev, [provider.id]: result }));
                    }}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Add Provider Modal */}
        {showAddForm && (
          <AddProviderModal
            presets={presets}
            onClose={() => setShowAddForm(false)}
            onCreate={async (request) => {
              await createProvider(request);
              setShowAddForm(false);
            }}
          />
        )}
      </div>
    </div>
  );
}

// Preset Card Component - Compact pill style
function PresetCard({
  presetKey,
  preset,
  onAdd,
}: {
  presetKey: string;
  preset: LLMProviderPreset;
  onAdd: () => void;
}) {
  const info = PROVIDER_DISPLAY_INFO[preset.provider] || PROVIDER_DISPLAY_INFO.custom;
  
  return (
    <button
      onClick={onAdd}
      className="flex items-center gap-1.5 px-2 py-1 text-xs border border-slate-200 rounded hover:border-blue-300 hover:bg-blue-50/50 transition-colors"
      title={`${preset.name} - ${preset.default_model}`}
    >
      <span>{info.icon}</span>
      <span className="font-medium text-slate-700 truncate max-w-[100px]">{preset.name}</span>
    </button>
  );
}

// Provider Card Component
function ProviderCard({
  provider,
  isDefault,
  isEditing,
  testResult,
  isTesting,
  onEdit,
  onCancelEdit,
  onSave,
  onDelete,
  onSetDefault,
  onTest,
}: {
  provider: LLMProviderConfig;
  isDefault: boolean;
  isEditing: boolean;
  testResult?: { success: boolean; message: string };
  isTesting: boolean;
  onEdit: () => void;
  onCancelEdit: () => void;
  onSave: (updates: Partial<LLMProviderConfig>) => Promise<void>;
  onDelete: () => void;
  onSetDefault: () => void;
  onTest: () => Promise<void>;
}) {
  const info = PROVIDER_DISPLAY_INFO[provider.provider] || PROVIDER_DISPLAY_INFO.custom;
  const [showApiKey, setShowApiKey] = useState(false);
  const [editForm, setEditForm] = useState({
    name: provider.name,
    api_key: provider.api_key || '',
    base_url: provider.base_url || '',
    model: provider.model,
    temperature: provider.temperature,
  });

  if (isEditing) {
    return (
      <div className="border border-blue-300 rounded p-3 bg-blue-50/50 space-y-2">
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-0.5">Name</label>
            <input
              type="text"
              value={editForm.name}
              onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
              className="w-full px-2 py-1.5 border border-slate-300 rounded text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-0.5">Model</label>
            <input
              type="text"
              value={editForm.model}
              onChange={(e) => setEditForm({ ...editForm, model: e.target.value })}
              className="w-full px-2 py-1.5 border border-slate-300 rounded text-sm font-mono"
            />
          </div>
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-0.5">API Key</label>
          <div className="relative">
            <input
              type={showApiKey ? 'text' : 'password'}
              value={editForm.api_key}
              onChange={(e) => setEditForm({ ...editForm, api_key: e.target.value })}
              placeholder="sk-..."
              className="w-full px-2 py-1.5 pr-8 border border-slate-300 rounded text-sm font-mono"
            />
            <button
              type="button"
              onClick={() => setShowApiKey(!showApiKey)}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            >
              {showApiKey ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
            </button>
          </div>
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-0.5">Base URL</label>
          <input
            type="text"
            value={editForm.base_url}
            onChange={(e) => setEditForm({ ...editForm, base_url: e.target.value })}
            placeholder="https://api.openai.com/v1"
            className="w-full px-2 py-1.5 border border-slate-300 rounded text-sm font-mono"
          />
        </div>
        <div className="flex items-center gap-2 pt-1">
          <button
            onClick={() => onSave(editForm)}
            className="flex items-center gap-1 px-2 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700"
          >
            <Check className="w-3 h-3" />
            Save
          </button>
          <button
            onClick={onCancelEdit}
            className="flex items-center gap-1 px-2 py-1 bg-slate-100 text-slate-700 rounded text-xs hover:bg-slate-200"
          >
            <X className="w-3 h-3" />
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`border rounded p-3 transition-colors ${
      isDefault ? 'border-blue-300 bg-blue-50/30' : 'border-slate-200 hover:border-slate-300'
    } ${!provider.is_enabled ? 'opacity-50' : ''}`}>
      <div className="flex items-center gap-2">
        {/* Icon */}
        <span className="text-lg">{info.icon}</span>
        
        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="font-medium text-sm text-slate-800">{provider.name}</span>
            {isDefault && (
              <span className="flex items-center gap-0.5 px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-[10px]">
                <Star className="w-2.5 h-2.5" />
                Default
              </span>
            )}
            <span className={`px-1.5 py-0.5 rounded text-[10px] ${info.color}`}>
              {info.label}
            </span>
          </div>
          <div className="text-xs text-slate-500 font-mono">{provider.model}</div>
        </div>
        
        {/* Compact info */}
        <div className="hidden sm:flex flex-col text-[10px] text-slate-400">
          {provider.base_url && (
            <div className="flex items-center gap-1 truncate max-w-[150px]" title={provider.base_url}>
              <Globe className="w-2.5 h-2.5" />
              {new URL(provider.base_url).hostname}
            </div>
          )}
          {provider.api_key && (
            <div className="flex items-center gap-1">
              <Key className="w-2.5 h-2.5" />
              {provider.api_key.slice(0, 6)}...
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-0.5">
          <button
            onClick={onTest}
            disabled={isTesting}
            className="p-1.5 hover:bg-slate-100 rounded transition-colors text-slate-400 hover:text-slate-600"
            title="Test connection"
          >
            {isTesting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <TestTube className="w-3.5 h-3.5" />}
          </button>
          {!isDefault && (
            <button
              onClick={onSetDefault}
              className="p-1.5 hover:bg-slate-100 rounded transition-colors text-slate-400 hover:text-amber-600"
              title="Set as default"
            >
              <Star className="w-3.5 h-3.5" />
            </button>
          )}
          <button
            onClick={onEdit}
            className="p-1.5 hover:bg-slate-100 rounded transition-colors text-slate-400 hover:text-blue-600"
            title="Edit"
          >
            <Edit2 className="w-3.5 h-3.5" />
          </button>
          {provider.id !== 'demo' && (
            <button
              onClick={onDelete}
              className="p-1.5 hover:bg-slate-100 rounded transition-colors text-slate-400 hover:text-red-600"
              title="Delete"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Test Result */}
      {testResult && (
        <div className={`mt-2 p-1.5 rounded text-xs ${
          testResult.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
        }`}>
          {testResult.success ? '✓' : '✗'} {testResult.message}
        </div>
      )}
    </div>
  );
}

// Add Provider Modal
function AddProviderModal({
  presets,
  onClose,
  onCreate,
}: {
  presets: Record<string, LLMProviderPreset>;
  onClose: () => void;
  onCreate: (request: CreateProviderRequest) => Promise<void>;
}) {
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [showApiKey, setShowApiKey] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [form, setForm] = useState<CreateProviderRequest>({
    name: '',
    provider: 'openai',
    api_key: '',
    base_url: '',
    model: '',
    temperature: 0,
  });

  const handlePresetSelect = (key: string) => {
    const preset = presets[key];
    if (preset) {
      setSelectedPreset(key);
      setForm({
        ...form,
        name: `${preset.name} - ${preset.default_model}`,
        provider: preset.provider,
        base_url: preset.base_url,
        model: preset.default_model,
      });
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      await onCreate(form);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black/50 z-[60] flex items-center justify-center p-4"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200">
          <h3 className="font-semibold text-slate-800">Add LLM Provider</h3>
          <button onClick={onClose} className="p-1 hover:bg-slate-100 rounded">
            <X className="w-4 h-4 text-slate-500" />
          </button>
        </div>

        <div className="p-4 space-y-3">
          {/* Compact Preset selection */}
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1.5">Quick Select</label>
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(presets).slice(0, 8).map(([key, preset]) => {
                const info = PROVIDER_DISPLAY_INFO[preset.provider] || PROVIDER_DISPLAY_INFO.custom;
                return (
                  <button
                    key={key}
                    onClick={() => handlePresetSelect(key)}
                    className={`px-2 py-1 text-xs border rounded transition-colors flex items-center gap-1 ${
                      selectedPreset === key
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-slate-200 hover:border-slate-300 text-slate-600'
                    }`}
                  >
                    <span>{info.icon}</span>
                    <span className="truncate max-w-[80px]">{preset.name}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Form fields */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Name</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="My GPT-4"
                className="w-full px-2 py-1.5 border border-slate-300 rounded text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Model</label>
              <input
                type="text"
                value={form.model}
                onChange={(e) => setForm({ ...form, model: e.target.value })}
                placeholder="gpt-4o"
                className="w-full px-2 py-1.5 border border-slate-300 rounded text-sm font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">API Key</label>
            <div className="relative">
              <input
                type={showApiKey ? 'text' : 'password'}
                value={form.api_key}
                onChange={(e) => setForm({ ...form, api_key: e.target.value })}
                placeholder="sk-..."
                className="w-full px-2 py-1.5 pr-8 border border-slate-300 rounded text-sm font-mono"
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                {showApiKey ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Base URL</label>
            <input
              type="text"
              value={form.base_url}
              onChange={(e) => setForm({ ...form, base_url: e.target.value })}
              placeholder="https://api.openai.com/v1"
              className="w-full px-2 py-1.5 border border-slate-300 rounded text-sm font-mono"
            />
          </div>

          <div className="flex items-center gap-3">
            <label className="text-xs font-medium text-slate-600 whitespace-nowrap">
              Temperature:
            </label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={form.temperature}
              onChange={(e) => setForm({ ...form, temperature: parseFloat(e.target.value) })}
              className="flex-1"
            />
            <span className="text-xs font-mono text-slate-600 w-6">{form.temperature}</span>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 px-4 py-3 border-t border-slate-200 bg-slate-50">
          <button
            onClick={onClose}
            className="px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100 rounded transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!form.name || !form.model || isSubmitting}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting && <Loader2 className="w-3 h-3 animate-spin" />}
            Add
          </button>
        </div>
      </div>
    </div>
  );
}

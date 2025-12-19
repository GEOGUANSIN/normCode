/**
 * Panel for loading repository files
 */

import { useState } from 'react';
import { FolderOpen, Play, AlertCircle, CheckCircle } from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { repositoryApi, graphApi } from '../../services/api';
import { useGraphStore } from '../../stores/graphStore';
import { useExecutionStore } from '../../stores/executionStore';
import type { LoadRepositoryRequest } from '../../types/execution';

interface LoadPanelProps {
  onClose: () => void;
}

export function LoadPanel({ onClose }: LoadPanelProps) {
  const [conceptsPath, setConceptsPath] = useState('');
  const [inferencesPath, setInferencesPath] = useState('');
  const [inputsPath, setInputsPath] = useState('');
  const [llmModel, setLlmModel] = useState('demo');

  const setGraphData = useGraphStore((s) => s.setGraphData);
  const setProgress = useExecutionStore((s) => s.setProgress);
  const setRunId = useExecutionStore((s) => s.setRunId);

  // Fetch example repositories
  const { data: examples } = useQuery({
    queryKey: ['repository-examples'],
    queryFn: repositoryApi.getExamples,
  });

  // Load mutation
  const loadMutation = useMutation({
    mutationFn: async (request: LoadRepositoryRequest) => {
      const loadResult = await repositoryApi.load(request);
      const graphData = await graphApi.get();
      return { loadResult, graphData };
    },
    onSuccess: ({ loadResult, graphData }) => {
      setGraphData(graphData);
      setProgress(0, loadResult.total_inferences);
      if (loadResult.run_id) {
        setRunId(loadResult.run_id);
      }
      onClose();
    },
  });

  const handleLoadExample = (example: { concepts_path: string; inferences_path: string }) => {
    setConceptsPath(example.concepts_path);
    setInferencesPath(example.inferences_path);
  };

  const handleLoad = () => {
    if (!conceptsPath || !inferencesPath) return;

    loadMutation.mutate({
      concepts_path: conceptsPath,
      inferences_path: inferencesPath,
      inputs_path: inputsPath || undefined,
      llm_model: llmModel,
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg m-4">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-200">
          <h2 className="text-lg font-semibold text-slate-800">Load Repository</h2>
          <button
            onClick={onClose}
            className="text-slate-500 hover:text-slate-700"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          {/* Example repositories */}
          {examples?.examples && examples.examples.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Quick Load Examples
              </label>
              <div className="flex flex-wrap gap-2">
                {examples.examples.map((ex) => (
                  <button
                    key={ex.name}
                    onClick={() => handleLoadExample(ex)}
                    className="px-3 py-1.5 text-sm bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                  >
                    {ex.name}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* File paths */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Concepts File (.concept.json) *
            </label>
            <input
              type="text"
              value={conceptsPath}
              onChange={(e) => setConceptsPath(e.target.value)}
              placeholder="/path/to/concept_repo.json"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Inferences File (.inference.json) *
            </label>
            <input
              type="text"
              value={inferencesPath}
              onChange={(e) => setInferencesPath(e.target.value)}
              placeholder="/path/to/inference_repo.json"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Inputs File (optional)
            </label>
            <input
              type="text"
              value={inputsPath}
              onChange={(e) => setInputsPath(e.target.value)}
              placeholder="/path/to/inputs.json"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              LLM Model
            </label>
            <select
              value={llmModel}
              onChange={(e) => setLlmModel(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            >
              <option value="demo">Demo (No LLM)</option>
              <option value="gpt-4">GPT-4</option>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
              <option value="claude-3-opus">Claude 3 Opus</option>
            </select>
          </div>

          {/* Error message */}
          {loadMutation.error && (
            <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
              <AlertCircle size={16} />
              <span>{(loadMutation.error as Error).message}</span>
            </div>
          )}

          {/* Success message */}
          {loadMutation.isSuccess && (
            <div className="flex items-center gap-2 p-3 bg-green-50 text-green-700 rounded-lg text-sm">
              <CheckCircle size={16} />
              <span>Repository loaded successfully!</span>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-4 border-t border-slate-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleLoad}
            disabled={!conceptsPath || !inferencesPath || loadMutation.isPending}
            className={`flex items-center gap-2 px-4 py-2 text-sm rounded-lg transition-colors ${
              !conceptsPath || !inferencesPath || loadMutation.isPending
                ? 'bg-slate-200 text-slate-500 cursor-not-allowed'
                : 'bg-blue-500 hover:bg-blue-600 text-white'
            }`}
          >
            <FolderOpen size={16} />
            {loadMutation.isPending ? 'Loading...' : 'Load'}
          </button>
        </div>
      </div>
    </div>
  );
}

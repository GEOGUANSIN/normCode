/**
 * Function Modify Modal - Phase 4.2
 * Allows users to modify working interpretation and retry function nodes.
 */

import { useState } from 'react';
import { X, Save, Play, AlertCircle, CheckCircle, FileText, Workflow } from 'lucide-react';
import { executionApi, FunctionModifyRequest } from '../../services/api';

interface WorkingInterpretation {
  paradigm?: string;
  prompt_location?: string;
  output_type?: string;
  value_order?: Record<string, number>;
  [key: string]: unknown;
}

interface FunctionModifyModalProps {
  flowIndex: string;
  conceptName: string;
  currentWI: WorkingInterpretation | null;
  onClose: () => void;
  onApply: (success: boolean) => void;
}

export function FunctionModifyModal({
  flowIndex,
  conceptName,
  currentWI,
  onClose,
  onApply,
}: FunctionModifyModalProps) {
  const [paradigm, setParadigm] = useState(currentWI?.paradigm || '');
  const [promptLocation, setPromptLocation] = useState(currentWI?.prompt_location || '');
  const [outputType, setOutputType] = useState(currentWI?.output_type || '');
  const [retryAfter, setRetryAfter] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);

  // Check if anything has changed
  const hasChanges = 
    paradigm !== (currentWI?.paradigm || '') ||
    promptLocation !== (currentWI?.prompt_location || '') ||
    outputType !== (currentWI?.output_type || '');

  const handleSubmit = async () => {
    if (!hasChanges && !retryAfter) {
      onClose();
      return;
    }

    setIsSubmitting(true);
    setResult(null);

    try {
      const modifications: FunctionModifyRequest = {
        retry: retryAfter,
      };
      
      if (paradigm !== (currentWI?.paradigm || '')) {
        modifications.paradigm = paradigm;
      }
      if (promptLocation !== (currentWI?.prompt_location || '')) {
        modifications.prompt_location = promptLocation;
      }
      if (outputType !== (currentWI?.output_type || '')) {
        modifications.output_type = outputType;
      }

      const response = await executionApi.modifyFunction(flowIndex, modifications);
      
      if (response.success) {
        setResult({
          success: true,
          message: `Modified: ${response.modified_fields.join(', ')}`
        });
        onApply(true);
        
        // Auto-close after success
        setTimeout(() => {
          onClose();
        }, 1500);
      } else {
        setResult({ success: false, message: 'Failed to modify function' });
      }
    } catch (e) {
      setResult({ success: false, message: (e as Error).message });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30" onClick={onClose}>
      <div 
        className="bg-white rounded-lg shadow-xl w-[550px] max-h-[80vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200">
          <div>
            <h3 className="font-semibold text-slate-800">Modify Function</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              <span className="font-mono">{flowIndex}</span>
              <span className="mx-1">•</span>
              <span>{conceptName}</span>
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded hover:bg-slate-100 text-slate-500"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Paradigm */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-slate-700 mb-1">
              <Workflow size={14} className="text-purple-600" />
              Paradigm
            </label>
            <input
              type="text"
              value={paradigm}
              onChange={(e) => setParadigm(e.target.value)}
              className="w-full px-3 py-2 font-mono text-sm border border-slate-300 rounded-lg focus:border-purple-500 focus:ring-purple-500"
              placeholder="e.g., h_PromptTemplate-c_GenerateJson-o_List"
            />
            <p className="mt-1 text-xs text-slate-500">
              The paradigm defines the execution pattern for this function
            </p>
          </div>

          {/* Prompt Location */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-slate-700 mb-1">
              <FileText size={14} className="text-green-600" />
              Prompt Location
            </label>
            <input
              type="text"
              value={promptLocation}
              onChange={(e) => setPromptLocation(e.target.value)}
              className="w-full px-3 py-2 font-mono text-sm border border-slate-300 rounded-lg focus:border-green-500 focus:ring-green-500"
              placeholder="e.g., provision/prompts/analyze.md"
            />
            <p className="mt-1 text-xs text-slate-500">
              Path to the prompt template file
            </p>
          </div>

          {/* Output Type */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-slate-700 mb-1">
              <span className="text-orange-600 font-bold text-xs">→</span>
              Output Type
            </label>
            <input
              type="text"
              value={outputType}
              onChange={(e) => setOutputType(e.target.value)}
              className="w-full px-3 py-2 font-mono text-sm border border-slate-300 rounded-lg focus:border-orange-500 focus:ring-orange-500"
              placeholder="e.g., list[dict], str, int"
            />
            <p className="mt-1 text-xs text-slate-500">
              Expected output type
            </p>
          </div>

          {/* Current Value Order (read-only) */}
          {currentWI?.value_order && Object.keys(currentWI.value_order).length > 0 && (
            <div className="bg-slate-50 rounded-lg p-3">
              <label className="text-xs font-medium text-slate-500 uppercase mb-2 block">
                Value Order (Read-only)
              </label>
              <div className="font-mono text-xs text-slate-600 space-y-1">
                {Object.entries(currentWI.value_order).map(([key, val]) => (
                  <div key={key} className="flex justify-between">
                    <span className="truncate max-w-[200px]" title={key}>{key}</span>
                    <span className="text-slate-800 font-medium">:{String(val)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Retry option */}
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={retryAfter}
              onChange={(e) => setRetryAfter(e.target.checked)}
              className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-slate-700">
              Run to this node after applying changes
            </span>
          </label>

          {/* Result message */}
          {result && (
            <div className={`rounded-lg p-3 flex items-center gap-2 ${
              result.success 
                ? 'bg-green-50 text-green-800 border border-green-200'
                : 'bg-red-50 text-red-800 border border-red-200'
            }`}>
              {result.success ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
              <span className="text-sm">{result.message}</span>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 px-4 py-3 border-t border-slate-200 bg-slate-50">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || (!hasChanges && !retryAfter)}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-purple-600 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Applying...
              </>
            ) : retryAfter ? (
              <>
                <Play size={16} />
                Apply & Run
              </>
            ) : (
              <>
                <Save size={16} />
                Apply
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

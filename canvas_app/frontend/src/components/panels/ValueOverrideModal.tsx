/**
 * Value Override Modal - Phase 4.1
 * Allows users to inject or modify values at any ground or computed node.
 */

import { useState, useEffect } from 'react';
import { X, Save, Play, AlertCircle, CheckCircle } from 'lucide-react';
import { executionApi, DependentsResponse } from '../../services/api';

interface ValueOverrideModalProps {
  conceptName: string;
  currentValue: unknown;
  axes: string[];
  shape: number[];
  isGround: boolean;
  onClose: () => void;
  onApply: (success: boolean) => void;
}

export function ValueOverrideModal({
  conceptName,
  currentValue,
  axes,
  shape,
  isGround,
  onClose,
  onApply,
}: ValueOverrideModalProps) {
  const [value, setValue] = useState<string>('');
  const [parseError, setParseError] = useState<string | null>(null);
  const [rerunDependents, setRerunDependents] = useState(false);
  const [dependents, setDependents] = useState<DependentsResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);

  // Initialize value from current value
  useEffect(() => {
    try {
      if (currentValue !== undefined && currentValue !== null) {
        setValue(JSON.stringify(currentValue, null, 2));
      } else {
        setValue('');
      }
    } catch {
      setValue(String(currentValue));
    }
  }, [currentValue]);

  // Fetch dependents on mount
  useEffect(() => {
    const fetchDependents = async () => {
      try {
        const deps = await executionApi.getDependents(conceptName);
        setDependents(deps);
      } catch (e) {
        console.error('Failed to fetch dependents:', e);
      }
    };
    fetchDependents();
  }, [conceptName]);

  // Validate JSON on change
  const handleValueChange = (newValue: string) => {
    setValue(newValue);
    setParseError(null);
    
    if (newValue.trim()) {
      try {
        JSON.parse(newValue);
      } catch (e) {
        setParseError((e as Error).message);
      }
    }
  };

  const handleSubmit = async () => {
    if (parseError) return;
    
    let parsedValue: unknown;
    try {
      parsedValue = value.trim() ? JSON.parse(value) : null;
    } catch (e) {
      setParseError((e as Error).message);
      return;
    }

    setIsSubmitting(true);
    setResult(null);

    try {
      const response = await executionApi.overrideValue(conceptName, parsedValue, rerunDependents);
      
      if (response.success) {
        setResult({
          success: true,
          message: `Value overridden. ${response.stale_nodes.length} nodes marked stale.`
        });
        onApply(true);
        
        // Auto-close after success
        setTimeout(() => {
          onClose();
        }, 1500);
      } else {
        setResult({ success: false, message: 'Failed to override value' });
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
        className="bg-white rounded-lg shadow-xl w-[600px] max-h-[80vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200">
          <div>
            <h3 className="font-semibold text-slate-800">Override Value</h3>
            <p className="text-xs text-slate-500 font-mono mt-0.5">{conceptName}</p>
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
          {/* Info badges */}
          <div className="flex items-center gap-2 flex-wrap text-xs">
            {isGround && (
              <span className="px-2 py-0.5 rounded bg-green-100 text-green-700">Ground Concept</span>
            )}
            {axes.length > 0 && (
              <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                Axes: [{axes.join(', ')}]
              </span>
            )}
            {shape.length > 0 && (
              <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                Shape: [{shape.join(', ')}]
              </span>
            )}
          </div>

          {/* Value Editor */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              New Value (JSON)
            </label>
            <textarea
              value={value}
              onChange={(e) => handleValueChange(e.target.value)}
              className={`w-full h-48 p-3 font-mono text-sm border rounded-lg resize-y ${
                parseError 
                  ? 'border-red-300 focus:border-red-500 focus:ring-red-500' 
                  : 'border-slate-300 focus:border-blue-500 focus:ring-blue-500'
              }`}
              placeholder="Enter value as JSON..."
            />
            {parseError && (
              <div className="mt-1 text-xs text-red-600 flex items-center gap-1">
                <AlertCircle size={12} />
                {parseError}
              </div>
            )}
          </div>

          {/* Dependents Info */}
          {dependents && dependents.count > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
              <div className="flex items-start gap-2">
                <AlertCircle size={16} className="text-amber-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-amber-800">
                    {dependents.count} dependent node{dependents.count !== 1 ? 's' : ''} will be marked stale
                  </p>
                  <p className="text-xs text-amber-600 mt-1">
                    {dependents.dependents.slice(0, 5).join(', ')}
                    {dependents.count > 5 && ` and ${dependents.count - 5} more...`}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Re-run option */}
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={rerunDependents}
              onChange={(e) => setRerunDependents(e.target.checked)}
              className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-slate-700">
              Re-run dependent nodes after override
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
            disabled={isSubmitting || !!parseError}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Applying...
              </>
            ) : rerunDependents ? (
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

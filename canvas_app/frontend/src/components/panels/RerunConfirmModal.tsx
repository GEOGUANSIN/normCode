/**
 * Rerun Confirm Modal - Phase 4.3
 * Shows confirmation with affected nodes before re-running from a node.
 */

import { useState, useEffect } from 'react';
import { X, RefreshCw, AlertTriangle, CheckCircle, AlertCircle } from 'lucide-react';
import { executionApi, DescendantsResponse } from '../../services/api';

interface RerunConfirmModalProps {
  flowIndex: string;
  conceptName: string;
  onClose: () => void;
  onConfirm: (success: boolean) => void;
}

export function RerunConfirmModal({
  flowIndex,
  conceptName,
  onClose,
  onConfirm,
}: RerunConfirmModalProps) {
  const [descendants, setDescendants] = useState<DescendantsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);

  // Fetch descendants on mount
  useEffect(() => {
    const fetchDescendants = async () => {
      setIsLoading(true);
      try {
        const deps = await executionApi.getDescendants(flowIndex);
        setDescendants(deps);
      } catch (e) {
        console.error('Failed to fetch descendants:', e);
      } finally {
        setIsLoading(false);
      }
    };
    fetchDescendants();
  }, [flowIndex]);

  const handleConfirm = async () => {
    setIsSubmitting(true);
    setResult(null);

    try {
      const response = await executionApi.rerunFrom(flowIndex);
      
      if (response.success) {
        setResult({
          success: true,
          message: `Reset ${response.reset_count} nodes. Execution started.`
        });
        onConfirm(true);
        
        // Auto-close after success
        setTimeout(() => {
          onClose();
        }, 1500);
      } else {
        setResult({ success: false, message: 'Failed to re-run' });
      }
    } catch (e) {
      setResult({ success: false, message: (e as Error).message });
    } finally {
      setIsSubmitting(false);
    }
  };

  const totalNodes = 1 + (descendants?.count || 0);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30" onClick={onClose}>
      <div 
        className="bg-white rounded-lg shadow-xl w-[500px] max-h-[80vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-amber-100 rounded-lg">
              <RefreshCw size={18} className="text-amber-600" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-800">Re-run from Node</h3>
              <p className="text-xs text-slate-500 font-mono">{flowIndex}</p>
            </div>
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
          {/* Warning */}
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
            <div className="flex items-start gap-2">
              <AlertTriangle size={18} className="text-amber-600 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-amber-800">
                  This will reset {totalNodes} node{totalNodes !== 1 ? 's' : ''}
                </p>
                <p className="text-xs text-amber-600 mt-1">
                  The selected node and all its downstream dependents will be reset to pending 
                  and re-executed from scratch.
                </p>
              </div>
            </div>
          </div>

          {/* Target node */}
          <div className="bg-slate-50 rounded-lg p-3">
            <label className="text-xs font-medium text-slate-500 uppercase mb-2 block">
              Starting Node
            </label>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-mono">
                {flowIndex}
              </span>
              <span className="text-sm text-slate-700 truncate">{conceptName}</span>
            </div>
          </div>

          {/* Descendants list */}
          {isLoading ? (
            <div className="flex items-center justify-center py-4 text-sm text-slate-500">
              <div className="w-4 h-4 border-2 border-slate-300 border-t-slate-600 rounded-full animate-spin mr-2" />
              Finding dependent nodes...
            </div>
          ) : descendants && descendants.count > 0 ? (
            <div className="bg-slate-50 rounded-lg p-3">
              <label className="text-xs font-medium text-slate-500 uppercase mb-2 block">
                Downstream Nodes ({descendants.count})
              </label>
              <div className="max-h-40 overflow-y-auto space-y-1">
                {descendants.descendants.map((fi) => (
                  <div key={fi} className="text-xs font-mono text-slate-600 px-2 py-1 bg-white rounded">
                    {fi}
                  </div>
                ))}
              </div>
            </div>
          ) : descendants && descendants.count === 0 ? (
            <div className="text-sm text-slate-500 text-center py-2">
              No downstream nodes - only this node will be reset
            </div>
          ) : null}

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
            onClick={handleConfirm}
            disabled={isSubmitting || isLoading}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-amber-600 rounded-lg hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Resetting...
              </>
            ) : (
              <>
                <RefreshCw size={16} />
                Reset & Re-run
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

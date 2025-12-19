/**
 * Log Panel for execution logs
 * Enhanced with per-node filtering based on selection
 */

import { useEffect, useRef, useState } from 'react';
import { Terminal, Filter, Trash2, ChevronDown, ChevronUp, AlertCircle, Info, AlertTriangle, Target } from 'lucide-react';
import { useExecutionStore } from '../../stores/executionStore';
import { useSelectionStore } from '../../stores/selectionStore';
import { useGraphStore } from '../../stores/graphStore';

type LogLevel = 'all' | 'info' | 'warning' | 'error';
type NodeFilter = 'all' | 'selected';

const levelIcons = {
  info: Info,
  warning: AlertTriangle,
  error: AlertCircle,
};

const levelColors = {
  info: 'text-blue-600',
  warning: 'text-yellow-600',
  error: 'text-red-600',
};

export function LogPanel() {
  const logs = useExecutionStore((s) => s.logs);
  const clearLogs = useExecutionStore((s) => s.clearLogs);
  const selectedNodeId = useSelectionStore((s) => s.selectedNodeId);
  const getNode = useGraphStore((s) => s.getNode);
  
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [levelFilter, setLevelFilter] = useState<LogLevel>('all');
  const [nodeFilter, setNodeFilter] = useState<NodeFilter>('all');
  const [autoScroll, setAutoScroll] = useState(true);
  const logEndRef = useRef<HTMLDivElement>(null);

  // Get selected node's flow_index for filtering
  const selectedNode = selectedNodeId ? getNode(selectedNodeId) : null;
  const selectedFlowIndex = selectedNode?.flow_index || null;

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  // Filter logs by level and node
  const filteredLogs = logs.filter((log) => {
    // Level filter
    if (levelFilter !== 'all' && log.level !== levelFilter) {
      return false;
    }
    
    // Node filter
    if (nodeFilter === 'selected' && selectedFlowIndex) {
      // Include logs for the selected node OR global logs (empty flowIndex)
      if (log.flowIndex !== selectedFlowIndex && log.flowIndex !== '') {
        return false;
      }
    }
    
    return true;
  });

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { 
      hour12: false, 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit' 
    });
  };

  if (isCollapsed) {
    return (
      <div className="border-t border-slate-200 bg-white">
        <button
          onClick={() => setIsCollapsed(false)}
          className="w-full px-4 py-2 flex items-center justify-between text-sm text-slate-600 hover:bg-slate-50"
        >
          <div className="flex items-center gap-2">
            <Terminal size={14} />
            <span>Logs ({logs.length})</span>
            {nodeFilter === 'selected' && selectedFlowIndex && (
              <span className="text-xs bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded">
                Node: {selectedFlowIndex}
              </span>
            )}
          </div>
          <ChevronUp size={14} />
        </button>
      </div>
    );
  }

  return (
    <div className="border-t border-slate-200 bg-white flex flex-col h-48">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-slate-100">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
            <Terminal size={14} />
            <span>Execution Logs</span>
            <span className="text-slate-400">({filteredLogs.length})</span>
          </div>

          {/* Level filter dropdown */}
          <div className="flex items-center gap-1">
            <Filter size={12} className="text-slate-400" />
            <select
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value as LogLevel)}
              className="text-xs border border-slate-200 rounded px-1 py-0.5 text-slate-600"
            >
              <option value="all">All Levels</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
            </select>
          </div>

          {/* Node filter toggle */}
          <button
            onClick={() => setNodeFilter(nodeFilter === 'all' ? 'selected' : 'all')}
            disabled={!selectedFlowIndex}
            className={`flex items-center gap-1 px-2 py-0.5 rounded text-xs transition-colors ${
              nodeFilter === 'selected' && selectedFlowIndex
                ? 'bg-purple-100 text-purple-700 border border-purple-200'
                : 'bg-slate-100 text-slate-600 border border-slate-200 hover:bg-slate-200'
            } ${!selectedFlowIndex ? 'opacity-50 cursor-not-allowed' : ''}`}
            title={selectedFlowIndex 
              ? `Filter logs for node ${selectedFlowIndex}` 
              : 'Select a node to filter logs'
            }
          >
            <Target size={12} />
            {nodeFilter === 'selected' && selectedFlowIndex
              ? `Node: ${selectedFlowIndex}`
              : 'Filter by Node'
            }
          </button>

          {/* Auto-scroll toggle */}
          <label className="flex items-center gap-1 text-xs text-slate-500">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              className="w-3 h-3"
            />
            Auto-scroll
          </label>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={clearLogs}
            className="p-1 text-slate-400 hover:text-slate-600 transition-colors"
            title="Clear logs"
          >
            <Trash2 size={14} />
          </button>
          <button
            onClick={() => setIsCollapsed(true)}
            className="p-1 text-slate-400 hover:text-slate-600 transition-colors"
            title="Collapse"
          >
            <ChevronDown size={14} />
          </button>
        </div>
      </div>

      {/* Log entries */}
      <div className="flex-1 overflow-y-auto font-mono text-xs bg-slate-50">
        {filteredLogs.length === 0 ? (
          <div className="flex items-center justify-center h-full text-slate-400">
            {logs.length === 0 
              ? 'No logs yet' 
              : `No logs matching current filters`
            }
          </div>
        ) : (
          <div className="p-2 space-y-0.5">
            {filteredLogs.map((log, index) => {
              const Icon = levelIcons[log.level as keyof typeof levelIcons] || Info;
              const colorClass = levelColors[log.level as keyof typeof levelColors] || 'text-slate-600';
              const isSelectedNode = selectedFlowIndex && log.flowIndex === selectedFlowIndex;
              
              return (
                <div
                  key={index}
                  className={`flex items-start gap-2 py-0.5 px-1 rounded ${
                    isSelectedNode 
                      ? 'bg-purple-50 hover:bg-purple-100' 
                      : 'hover:bg-white'
                  }`}
                >
                  <span className="text-slate-400 shrink-0">
                    {formatTime(log.timestamp)}
                  </span>
                  <Icon size={12} className={`${colorClass} shrink-0 mt-0.5`} />
                  {log.flowIndex && (
                    <span className={`shrink-0 ${
                      isSelectedNode ? 'text-purple-700 font-medium' : 'text-purple-600'
                    }`}>
                      [{log.flowIndex}]
                    </span>
                  )}
                  <span className="text-slate-700">{log.message}</span>
                </div>
              );
            })}
            <div ref={logEndRef} />
          </div>
        )}
      </div>
    </div>
  );
}

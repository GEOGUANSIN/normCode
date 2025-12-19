/**
 * Log Panel for execution logs
 */

import { useEffect, useRef, useState } from 'react';
import { Terminal, Filter, Trash2, ChevronDown, ChevronUp, AlertCircle, Info, AlertTriangle } from 'lucide-react';
import { useExecutionStore } from '../../stores/executionStore';

type LogLevel = 'all' | 'info' | 'warning' | 'error';

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
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [filter, setFilter] = useState<LogLevel>('all');
  const [autoScroll, setAutoScroll] = useState(true);
  const logEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  // Filter logs
  const filteredLogs = filter === 'all' 
    ? logs 
    : logs.filter((log) => log.level === filter);

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

          {/* Filter dropdown */}
          <div className="flex items-center gap-1">
            <Filter size={12} className="text-slate-400" />
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value as LogLevel)}
              className="text-xs border border-slate-200 rounded px-1 py-0.5 text-slate-600"
            >
              <option value="all">All</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
            </select>
          </div>

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
            No logs yet
          </div>
        ) : (
          <div className="p-2 space-y-0.5">
            {filteredLogs.map((log, index) => {
              const Icon = levelIcons[log.level as keyof typeof levelIcons] || Info;
              const colorClass = levelColors[log.level as keyof typeof levelColors] || 'text-slate-600';
              
              return (
                <div
                  key={index}
                  className="flex items-start gap-2 py-0.5 px-1 hover:bg-white rounded"
                >
                  <span className="text-slate-400 shrink-0">
                    {formatTime(log.timestamp)}
                  </span>
                  <Icon size={12} className={`${colorClass} shrink-0 mt-0.5`} />
                  {log.flowIndex && (
                    <span className="text-purple-600 shrink-0">
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


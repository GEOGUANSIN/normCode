/**
 * Main Application Component
 */

import { useState } from 'react';
import { FolderOpen, Settings, HelpCircle, Cpu, PanelRight, PanelRightClose, PanelBottom, PanelBottomClose } from 'lucide-react';
import { GraphCanvas } from './components/graph/GraphCanvas';
import { ControlPanel } from './components/panels/ControlPanel';
import { DetailPanel } from './components/panels/DetailPanel';
import { LoadPanel } from './components/panels/LoadPanel';
import { LogPanel } from './components/panels/LogPanel';
import { useWebSocket } from './hooks/useWebSocket';
import { useGraphStore } from './stores/graphStore';
import { useExecutionStore } from './stores/executionStore';

function App() {
  const [showLoadPanel, setShowLoadPanel] = useState(false);
  const [showDetailPanel, setShowDetailPanel] = useState(true);
  const [showLogPanel, setShowLogPanel] = useState(true);
  const graphData = useGraphStore((s) => s.graphData);
  const status = useExecutionStore((s) => s.status);
  const wsConnected = useWebSocket();

  return (
    <div className="h-screen w-screen flex flex-col bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Cpu className="w-6 h-6 text-purple-500" />
            <h1 className="text-lg font-semibold text-slate-800">NormCode Canvas</h1>
          </div>
          <span className="text-xs text-slate-500 bg-slate-100 px-2 py-0.5 rounded">v0.1.0</span>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowLoadPanel(true)}
            className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
          >
            <FolderOpen size={16} />
            Load Repository
          </button>
          
          {/* Panel toggles */}
          {graphData && (
            <div className="flex items-center gap-1 border-l border-slate-200 pl-2 ml-2">
              <button
                onClick={() => setShowDetailPanel(!showDetailPanel)}
                className={`p-2 rounded-lg transition-colors ${
                  showDetailPanel 
                    ? 'text-blue-600 bg-blue-50 hover:bg-blue-100' 
                    : 'text-slate-500 hover:text-slate-700 hover:bg-slate-100'
                }`}
                title={showDetailPanel ? 'Hide detail panel' : 'Show detail panel'}
              >
                {showDetailPanel ? <PanelRightClose size={18} /> : <PanelRight size={18} />}
              </button>
              <button
                onClick={() => setShowLogPanel(!showLogPanel)}
                className={`p-2 rounded-lg transition-colors ${
                  showLogPanel 
                    ? 'text-blue-600 bg-blue-50 hover:bg-blue-100' 
                    : 'text-slate-500 hover:text-slate-700 hover:bg-slate-100'
                }`}
                title={showLogPanel ? 'Hide log panel' : 'Show log panel'}
              >
                {showLogPanel ? <PanelBottomClose size={18} /> : <PanelBottom size={18} />}
              </button>
            </div>
          )}
          
          <button
            className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
            title="Settings"
          >
            <Settings size={18} />
          </button>
          <button
            className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
            title="Help"
          >
            <HelpCircle size={18} />
          </button>
        </div>
      </header>

      {/* Control Panel */}
      {graphData && <ControlPanel />}

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 flex overflow-hidden">
          {/* Graph Canvas */}
          <div className="flex-1 overflow-hidden">
            <GraphCanvas />
          </div>

          {/* Detail Panel */}
          {graphData && showDetailPanel && <DetailPanel />}
        </div>

        {/* Log Panel */}
        {graphData && showLogPanel && <LogPanel />}
      </main>

      {/* Load Panel Modal */}
      {showLoadPanel && (
        <LoadPanel onClose={() => setShowLoadPanel(false)} />
      )}

      {/* Status Bar */}
      <footer className="bg-white border-t border-slate-200 px-4 py-1 flex items-center justify-between text-xs text-slate-500">
        <div className="flex items-center gap-4">
          <span className={`flex items-center gap-1 ${
            status === 'running' ? 'text-green-600' :
            status === 'paused' ? 'text-yellow-600' :
            status === 'failed' ? 'text-red-600' :
            status === 'completed' ? 'text-green-600' :
            'text-slate-500'
          }`}>
            <span className={`w-2 h-2 rounded-full ${
              status === 'running' ? 'bg-green-500 animate-pulse' :
              status === 'paused' ? 'bg-yellow-500' :
              status === 'failed' ? 'bg-red-500' :
              status === 'completed' ? 'bg-green-500' :
              'bg-slate-400'
            }`} />
            {status === 'idle' ? 'Ready' : status.charAt(0).toUpperCase() + status.slice(1)}
          </span>
          {graphData && (
            <>
              <span>•</span>
              <span>{graphData.nodes.length} nodes</span>
              <span>•</span>
              <span>{graphData.edges.length} edges</span>
            </>
          )}
        </div>
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1">
            <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            WebSocket: {wsConnected ? 'Connected' : 'Disconnected'}
          </span>
          <span>NormCode Canvas Tool</span>
        </div>
      </footer>
    </div>
  );
}

export default App;

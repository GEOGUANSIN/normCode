/**
 * DeploymentPanel - Deploy projects to remote NormCode servers
 */

import { useEffect, useState } from 'react';
import {
  Server,
  Plus,
  Trash2,
  Edit2,
  Check,
  X,
  Rocket,
  Loader2,
  AlertCircle,
  ChevronDown,
  ChevronRight,
  Globe,
  CheckCircle,
  XCircle,
  RefreshCw,
  Play,
  Clock,
  Upload,
  Link,
  Star,
} from 'lucide-react';
import { useDeploymentStore } from '../../stores/deploymentStore';
import { useProjectStore } from '../../stores/projectStore';
import type { DeploymentServer, ServerHealth, RemotePlan } from '../../types/deployment';

interface DeploymentPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export function DeploymentPanel({ isOpen, onClose }: DeploymentPanelProps) {
  const {
    servers,
    selectedServerId,
    serverHealth,
    remotePlans,
    activeRuns,
    isLoading,
    isDeploying,
    error,
    activeTab,
    lastDeployResult,
    fetchServers,
    addServer,
    removeServer,
    updateServer,
    checkServerHealth,
    testConnection,
    deployCurrentProject,
    fetchRemotePlans,
    startRemoteRun,
    refreshRunStatus,
    setSelectedServerId,
    setActiveTab,
    setError,
  } = useDeploymentStore();

  const { currentProject } = useProjectStore();
  
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [expandedServer, setExpandedServer] = useState<string | null>(null);
  
  // New server form state
  const [newServerName, setNewServerName] = useState('');
  const [newServerUrl, setNewServerUrl] = useState('http://localhost:8080');
  const [newServerDesc, setNewServerDesc] = useState('');
  const [isTestingUrl, setIsTestingUrl] = useState(false);
  const [testResult, setTestResult] = useState<ServerHealth | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchServers();
    }
  }, [isOpen, fetchServers]);

  // Check health of all servers on load
  useEffect(() => {
    if (isOpen && servers.length > 0) {
      servers.forEach(s => {
        if (!serverHealth[s.id]) {
          checkServerHealth(s.id);
        }
      });
    }
  }, [isOpen, servers, serverHealth, checkServerHealth]);

  if (!isOpen) return null;

  const handleTestConnection = async () => {
    setIsTestingUrl(true);
    const result = await testConnection(newServerUrl);
    setTestResult(result);
    setIsTestingUrl(false);
  };

  const handleAddServer = async () => {
    if (!newServerName.trim() || !newServerUrl.trim()) return;
    
    const success = await addServer(newServerName, newServerUrl, newServerDesc);
    if (success) {
      setShowAddForm(false);
      setNewServerName('');
      setNewServerUrl('http://localhost:8080');
      setNewServerDesc('');
      setTestResult(null);
    }
  };

  const handleDeploy = async () => {
    if (!selectedServerId) return;
    await deployCurrentProject(selectedServerId);
  };

  const selectedServer = servers.find(s => s.id === selectedServerId);
  const selectedHealth = selectedServerId ? serverHealth[selectedServerId] : null;

  return (
    <div 
      className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[85vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-gradient-to-r from-emerald-50 to-teal-50">
          <div className="flex items-center gap-2">
            <Rocket className="w-5 h-5 text-emerald-600" />
            <h2 className="font-semibold text-slate-800">Deploy Project</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <X className="w-4 h-4 text-slate-500" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-slate-200 bg-slate-50">
          <button
            onClick={() => setActiveTab('servers')}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'servers'
                ? 'text-emerald-600 border-b-2 border-emerald-600 bg-white'
                : 'text-slate-600 hover:text-slate-800'
            }`}
          >
            <Server className="w-3.5 h-3.5 inline mr-1.5" />
            Servers
          </button>
          <button
            onClick={() => setActiveTab('deploy')}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'deploy'
                ? 'text-emerald-600 border-b-2 border-emerald-600 bg-white'
                : 'text-slate-600 hover:text-slate-800'
            }`}
          >
            <Upload className="w-3.5 h-3.5 inline mr-1.5" />
            Deploy
          </button>
          <button
            onClick={() => setActiveTab('runs')}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'runs'
                ? 'text-emerald-600 border-b-2 border-emerald-600 bg-white'
                : 'text-slate-600 hover:text-slate-800'
            }`}
          >
            <Play className="w-3.5 h-3.5 inline mr-1.5" />
            Remote Runs
            {activeRuns.length > 0 && (
              <span className="ml-1.5 px-1.5 py-0.5 text-xs bg-emerald-100 text-emerald-700 rounded-full">
                {activeRuns.length}
              </span>
            )}
          </button>
        </div>

        {/* Error display */}
        {error && (
          <div className="mx-4 mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm">{error}</span>
            <button onClick={() => setError(null)} className="ml-auto text-red-500 hover:text-red-700">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {activeTab === 'servers' && (
            <ServersTab
              servers={servers}
              serverHealth={serverHealth}
              selectedServerId={selectedServerId}
              showAddForm={showAddForm}
              setShowAddForm={setShowAddForm}
              editingId={editingId}
              setEditingId={setEditingId}
              expandedServer={expandedServer}
              setExpandedServer={setExpandedServer}
              newServerName={newServerName}
              setNewServerName={setNewServerName}
              newServerUrl={newServerUrl}
              setNewServerUrl={setNewServerUrl}
              newServerDesc={newServerDesc}
              setNewServerDesc={setNewServerDesc}
              isTestingUrl={isTestingUrl}
              testResult={testResult}
              isLoading={isLoading}
              onTestConnection={handleTestConnection}
              onAddServer={handleAddServer}
              onRemoveServer={removeServer}
              onSelectServer={setSelectedServerId}
              onCheckHealth={checkServerHealth}
              onUpdateServer={updateServer}
            />
          )}
          
          {activeTab === 'deploy' && (
            <DeployTab
              currentProject={currentProject}
              servers={servers}
              selectedServerId={selectedServerId}
              selectedServer={selectedServer}
              selectedHealth={selectedHealth}
              isDeploying={isDeploying}
              lastDeployResult={lastDeployResult}
              onSelectServer={setSelectedServerId}
              onDeploy={handleDeploy}
            />
          )}
          
          {activeTab === 'runs' && (
            <RunsTab
              servers={servers}
              selectedServerId={selectedServerId}
              remotePlans={remotePlans}
              activeRuns={activeRuns}
              serverHealth={serverHealth}
              isLoading={isLoading}
              onSelectServer={setSelectedServerId}
              onFetchPlans={fetchRemotePlans}
              onStartRun={startRemoteRun}
              onRefreshStatus={refreshRunStatus}
            />
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Servers Tab
// ============================================================================

interface ServersTabProps {
  servers: DeploymentServer[];
  serverHealth: Record<string, ServerHealth>;
  selectedServerId: string | null;
  showAddForm: boolean;
  setShowAddForm: (show: boolean) => void;
  editingId: string | null;
  setEditingId: (id: string | null) => void;
  expandedServer: string | null;
  setExpandedServer: (id: string | null) => void;
  newServerName: string;
  setNewServerName: (name: string) => void;
  newServerUrl: string;
  setNewServerUrl: (url: string) => void;
  newServerDesc: string;
  setNewServerDesc: (desc: string) => void;
  isTestingUrl: boolean;
  testResult: ServerHealth | null;
  isLoading: boolean;
  onTestConnection: () => Promise<void>;
  onAddServer: () => Promise<void>;
  onRemoveServer: (id: string) => Promise<void>;
  onSelectServer: (id: string | null) => void;
  onCheckHealth: (id: string) => Promise<ServerHealth | null>;
  onUpdateServer: (id: string, updates: { name?: string; url?: string; description?: string; is_default?: boolean }) => Promise<boolean>;
}

function ServersTab({
  servers,
  serverHealth,
  selectedServerId,
  showAddForm,
  setShowAddForm,
  newServerName,
  setNewServerName,
  newServerUrl,
  setNewServerUrl,
  newServerDesc,
  setNewServerDesc,
  isTestingUrl,
  testResult,
  isLoading,
  onTestConnection,
  onAddServer,
  onRemoveServer,
  onSelectServer,
  onCheckHealth,
  onUpdateServer,
}: ServersTabProps) {
  return (
    <div className="space-y-4">
      {/* Add Server Button */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-600">
          Manage deployment servers where you can deploy and run your plans.
        </p>
        {!showAddForm && (
          <button
            onClick={() => setShowAddForm(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-emerald-600 text-white rounded hover:bg-emerald-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Server
          </button>
        )}
      </div>

      {/* Add Server Form */}
      {showAddForm && (
        <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 space-y-3">
          <h3 className="font-medium text-slate-800">Add Deployment Server</h3>
          
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Server Name</label>
            <input
              type="text"
              value={newServerName}
              onChange={(e) => setNewServerName(e.target.value)}
              placeholder="e.g., Production Server"
              className="w-full px-3 py-1.5 text-sm border border-slate-300 rounded focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
            />
          </div>
          
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Server URL</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={newServerUrl}
                onChange={(e) => setNewServerUrl(e.target.value)}
                placeholder="http://localhost:8080"
                className="flex-1 px-3 py-1.5 text-sm border border-slate-300 rounded focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              />
              <button
                onClick={onTestConnection}
                disabled={isTestingUrl || !newServerUrl.trim()}
                className="px-3 py-1.5 text-sm bg-slate-100 text-slate-700 rounded hover:bg-slate-200 disabled:opacity-50 transition-colors flex items-center gap-1"
              >
                {isTestingUrl ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Link className="w-3.5 h-3.5" />}
                Test
              </button>
            </div>
            {testResult && (
              <div className={`mt-2 text-xs flex items-center gap-1.5 ${testResult.is_healthy ? 'text-green-600' : 'text-red-600'}`}>
                {testResult.is_healthy ? <CheckCircle className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
                {testResult.is_healthy 
                  ? `Connected! ${testResult.plans_count || 0} plans available.`
                  : testResult.error || 'Connection failed'}
              </div>
            )}
          </div>
          
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Description (optional)</label>
            <input
              type="text"
              value={newServerDesc}
              onChange={(e) => setNewServerDesc(e.target.value)}
              placeholder="e.g., Main production deployment server"
              className="w-full px-3 py-1.5 text-sm border border-slate-300 rounded focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
            />
          </div>
          
          <div className="flex justify-end gap-2 pt-2">
            <button
              onClick={() => {
                setShowAddForm(false);
                setNewServerName('');
                setNewServerUrl('http://localhost:8080');
                setNewServerDesc('');
              }}
              className="px-3 py-1.5 text-sm text-slate-600 hover:text-slate-800"
            >
              Cancel
            </button>
            <button
              onClick={onAddServer}
              disabled={!newServerName.trim() || !newServerUrl.trim() || isLoading}
              className="px-4 py-1.5 text-sm bg-emerald-600 text-white rounded hover:bg-emerald-700 disabled:opacity-50 transition-colors flex items-center gap-1.5"
            >
              {isLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
              Add Server
            </button>
          </div>
        </div>
      )}

      {/* Server List */}
      <div className="space-y-2">
        {servers.length === 0 ? (
          <div className="text-center py-8 text-slate-500">
            <Server className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No deployment servers configured.</p>
            <p className="text-xs">Add a server to get started with deployment.</p>
          </div>
        ) : (
          servers.map(server => (
            <ServerCard
              key={server.id}
              server={server}
              health={serverHealth[server.id]}
              isSelected={server.id === selectedServerId}
              onSelect={() => onSelectServer(server.id)}
              onRefresh={() => onCheckHealth(server.id)}
              onRemove={() => onRemoveServer(server.id)}
              onSetDefault={() => onUpdateServer(server.id, { is_default: true })}
            />
          ))
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Server Card
// ============================================================================

interface ServerCardProps {
  server: DeploymentServer;
  health?: ServerHealth;
  isSelected: boolean;
  onSelect: () => void;
  onRefresh: () => void;
  onRemove: () => void;
  onSetDefault: () => void;
}

function ServerCard({ server, health, isSelected, onSelect, onRefresh, onRemove, onSetDefault }: ServerCardProps) {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await onRefresh();
    setIsRefreshing(false);
  };

  return (
    <div
      onClick={onSelect}
      className={`p-3 border rounded-lg cursor-pointer transition-all ${
        isSelected
          ? 'border-emerald-500 bg-emerald-50 ring-1 ring-emerald-500'
          : 'border-slate-200 hover:border-slate-300 bg-white'
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          {/* Health indicator */}
          <div className={`w-2.5 h-2.5 rounded-full ${
            !health ? 'bg-slate-300' :
            health.is_healthy ? 'bg-green-500' :
            health.status === 'unreachable' ? 'bg-red-500' :
            'bg-amber-500'
          }`} />
          
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-medium text-slate-800">{server.name}</span>
              {server.is_default && (
                <Star className="w-3.5 h-3.5 text-amber-500 fill-amber-500" />
              )}
            </div>
            <div className="text-xs text-slate-500 flex items-center gap-1">
              <Globe className="w-3 h-3" />
              {server.url}
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-1" onClick={e => e.stopPropagation()}>
          <button
            onClick={handleRefresh}
            className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded transition-colors"
            title="Refresh health"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>
          {!server.is_default && (
            <button
              onClick={onSetDefault}
              className="p-1.5 text-slate-400 hover:text-amber-500 hover:bg-slate-100 rounded transition-colors"
              title="Set as default"
            >
              <Star className="w-3.5 h-3.5" />
            </button>
          )}
          <button
            onClick={onRemove}
            className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
            title="Remove server"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
      
      {/* Health details */}
      {health && (
        <div className="mt-2 pt-2 border-t border-slate-100 text-xs text-slate-500">
          {health.is_healthy ? (
            <span className="text-green-600">
              {health.plans_count || 0} plans · {health.active_runs || 0} active runs
              {health.available_models && health.available_models.length > 0 && (
                <> · {health.available_models.filter(m => !m.is_mock).length} LLM models</>
              )}
            </span>
          ) : (
            <span className="text-red-600">{health.error || 'Connection failed'}</span>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Deploy Tab
// ============================================================================

interface DeployTabProps {
  currentProject: import('../../types/project').ProjectConfig | null;
  servers: DeploymentServer[];
  selectedServerId: string | null;
  selectedServer: DeploymentServer | undefined;
  selectedHealth: ServerHealth | null | undefined;
  isDeploying: boolean;
  lastDeployResult: import('../../types/deployment').DeployResult | null;
  onSelectServer: (id: string | null) => void;
  onDeploy: () => Promise<void>;
}

function DeployTab({
  currentProject,
  servers,
  selectedServerId,
  selectedServer,
  selectedHealth,
  isDeploying,
  lastDeployResult,
  onSelectServer,
  onDeploy,
}: DeployTabProps) {
  if (!currentProject) {
    return (
      <div className="text-center py-12 text-slate-500">
        <Upload className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <h3 className="font-medium text-slate-700 mb-1">No Project Open</h3>
        <p className="text-sm">Open a project first to deploy it to a server.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Project Info */}
      <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
        <h3 className="text-sm font-medium text-slate-500 mb-2">Project to Deploy</h3>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
            <Rocket className="w-5 h-5 text-emerald-600" />
          </div>
          <div>
            <p className="font-medium text-slate-800">{currentProject.name}</p>
            {currentProject.description && (
              <p className="text-xs text-slate-500">{currentProject.description}</p>
            )}
          </div>
        </div>
      </div>

      {/* Target Server Selection */}
      <div>
        <h3 className="text-sm font-medium text-slate-700 mb-2">Target Server</h3>
        {servers.length === 0 ? (
          <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-700">
            <AlertCircle className="w-4 h-4 inline mr-1.5" />
            No deployment servers configured. Add a server in the Servers tab first.
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-2">
            {servers.map(server => (
              <button
                key={server.id}
                onClick={() => onSelectServer(server.id)}
                className={`p-3 text-left border rounded-lg transition-all ${
                  selectedServerId === server.id
                    ? 'border-emerald-500 bg-emerald-50 ring-1 ring-emerald-500'
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${
                    selectedServerId === server.id && selectedHealth?.is_healthy
                      ? 'bg-green-500'
                      : 'bg-slate-300'
                  }`} />
                  <span className="font-medium text-sm text-slate-800">{server.name}</span>
                  {server.is_default && (
                    <Star className="w-3 h-3 text-amber-500 fill-amber-500" />
                  )}
                </div>
                <p className="text-xs text-slate-500 mt-1 truncate">{server.url}</p>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Deploy Button */}
      <div className="flex items-center justify-between pt-4 border-t border-slate-200">
        <div className="text-sm text-slate-500">
          {selectedServer && selectedHealth?.is_healthy ? (
            <span className="text-green-600 flex items-center gap-1">
              <CheckCircle className="w-3.5 h-3.5" />
              Ready to deploy
            </span>
          ) : selectedServer ? (
            <span className="text-amber-600 flex items-center gap-1">
              <AlertCircle className="w-3.5 h-3.5" />
              Server may be unavailable
            </span>
          ) : (
            <span>Select a target server</span>
          )}
        </div>
        <button
          onClick={onDeploy}
          disabled={!selectedServerId || isDeploying}
          className="px-6 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          {isDeploying ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Deploying...
            </>
          ) : (
            <>
              <Rocket className="w-4 h-4" />
              Deploy
            </>
          )}
        </button>
      </div>

      {/* Last Deploy Result */}
      {lastDeployResult && (
        <div className={`p-4 rounded-lg border ${
          lastDeployResult.success
            ? 'bg-green-50 border-green-200'
            : 'bg-red-50 border-red-200'
        }`}>
          <div className="flex items-center gap-2">
            {lastDeployResult.success ? (
              <CheckCircle className="w-5 h-5 text-green-600" />
            ) : (
              <XCircle className="w-5 h-5 text-red-600" />
            )}
            <span className={`font-medium ${lastDeployResult.success ? 'text-green-800' : 'text-red-800'}`}>
              {lastDeployResult.success ? 'Deployment Successful' : 'Deployment Failed'}
            </span>
          </div>
          <p className={`mt-1 text-sm ${lastDeployResult.success ? 'text-green-700' : 'text-red-700'}`}>
            {lastDeployResult.message}
          </p>
          {lastDeployResult.deployed_at && (
            <p className="mt-1 text-xs text-slate-500 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {new Date(lastDeployResult.deployed_at).toLocaleString()}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Runs Tab
// ============================================================================

interface RunsTabProps {
  servers: DeploymentServer[];
  selectedServerId: string | null;
  remotePlans: RemotePlan[];
  activeRuns: import('../../types/deployment').RemoteRunStatus[];
  serverHealth: Record<string, ServerHealth>;
  isLoading: boolean;
  onSelectServer: (id: string | null) => void;
  onFetchPlans: (serverId: string) => Promise<void>;
  onStartRun: (serverId: string, planId: string, llmModel?: string) => Promise<import('../../types/deployment').RemoteRunStatus | null>;
  onRefreshStatus: (serverId: string, runId: string) => Promise<void>;
}

function RunsTab({
  servers,
  selectedServerId,
  remotePlans,
  activeRuns,
  serverHealth,
  isLoading,
  onSelectServer,
  onFetchPlans,
  onStartRun,
  onRefreshStatus,
}: RunsTabProps) {
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null);
  const [selectedLlmModel, setSelectedLlmModel] = useState<string>('demo');

  useEffect(() => {
    if (selectedServerId) {
      onFetchPlans(selectedServerId);
    }
  }, [selectedServerId, onFetchPlans]);

  const selectedHealth = selectedServerId ? serverHealth[selectedServerId] : null;
  const availableModels = selectedHealth?.available_models || [];

  return (
    <div className="space-y-4">
      {/* Server Selection */}
      <div>
        <label className="block text-xs font-medium text-slate-600 mb-1.5">Select Server</label>
        <select
          value={selectedServerId || ''}
          onChange={(e) => onSelectServer(e.target.value || null)}
          className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
        >
          <option value="">Select a server...</option>
          {servers.map(server => (
            <option key={server.id} value={server.id}>{server.name}</option>
          ))}
        </select>
      </div>

      {/* Remote Plans */}
      {selectedServerId && (
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-xs font-medium text-slate-600">Available Plans</label>
            <button
              onClick={() => onFetchPlans(selectedServerId)}
              className="text-xs text-slate-500 hover:text-slate-700 flex items-center gap-1"
            >
              <RefreshCw className={`w-3 h-3 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
          
          {remotePlans.length === 0 ? (
            <div className="p-4 text-center text-slate-500 bg-slate-50 rounded-lg">
              <p className="text-sm">No plans deployed on this server.</p>
            </div>
          ) : (
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {remotePlans.map(plan => (
                <div
                  key={plan.id}
                  onClick={() => setSelectedPlanId(plan.id)}
                  className={`p-2 border rounded cursor-pointer transition-all ${
                    selectedPlanId === plan.id
                      ? 'border-emerald-500 bg-emerald-50'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <span className="text-sm font-medium text-slate-800">{plan.name}</span>
                  {plan.description && (
                    <p className="text-xs text-slate-500">{plan.description}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* LLM Model Selection */}
      {selectedPlanId && availableModels.length > 0 && (
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1.5">LLM Model</label>
          <select
            value={selectedLlmModel}
            onChange={(e) => setSelectedLlmModel(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          >
            {availableModels.map(model => (
              <option key={model.id} value={model.id}>
                {model.name} {model.is_mock ? '(Mock)' : ''}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Start Run Button */}
      {selectedServerId && selectedPlanId && (
        <button
          onClick={() => onStartRun(selectedServerId, selectedPlanId, selectedLlmModel)}
          className="w-full px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors flex items-center justify-center gap-2"
        >
          <Play className="w-4 h-4" />
          Start Run
        </button>
      )}

      {/* Active Runs */}
      {activeRuns.length > 0 && (
        <div>
          <h3 className="text-xs font-medium text-slate-600 mb-1.5">Active Runs</h3>
          <div className="space-y-2">
            {activeRuns.map(run => (
              <div key={run.run_id} className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-sm font-medium text-slate-800">{run.plan_id}</span>
                    <p className="text-xs text-slate-500">{run.run_id.substring(0, 8)}...</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 text-xs rounded-full ${
                      run.status === 'completed' ? 'bg-green-100 text-green-700' :
                      run.status === 'running' ? 'bg-blue-100 text-blue-700' :
                      run.status === 'failed' ? 'bg-red-100 text-red-700' :
                      'bg-slate-100 text-slate-700'
                    }`}>
                      {run.status}
                    </span>
                    <button
                      onClick={() => onRefreshStatus(run.server_id, run.run_id)}
                      className="p-1 text-slate-400 hover:text-slate-600"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default DeploymentPanel;


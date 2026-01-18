/**
 * ProjectPreview - A clean viewer for .normcode-canvas.json project configuration files.
 * 
 * Displays project settings, repository paths, execution config, and breakpoints
 * in an easy-to-read format.
 */

import { useState, useEffect } from 'react';
import { 
  Settings,
  Database,
  GitBranch,
  Play,
  Clock,
  Calendar,
  Hash,
  FileJson,
  Cpu,
  RefreshCw,
  X,
  ChevronDown,
  ChevronRight,
  AlertCircle,
  FolderOpen,
  Layers,
  Pause,
  Sparkles,
} from 'lucide-react';

// =============================================================================
// Types
// =============================================================================

interface RepositoriesConfig {
  concepts: string | null;
  inferences: string | null;
  inputs: string | null;
}

interface ExecutionConfig {
  max_cycles: number | null;
  db_path: string | null;
  agent_config: string | null;
  // Deprecated fields - may exist in old config files
  llm_model?: string | null;
  base_dir?: string | null;
  paradigm_dir?: string | null;
}

interface ProjectData {
  id: string;
  name: string;
  description: string | null;
  created_at: string | null;
  updated_at: string | null;
  repositories: RepositoriesConfig;
  execution: ExecutionConfig;
  breakpoints: string[];
  ui_preferences: Record<string, unknown>;
}

interface ProjectPreviewData {
  success: boolean;
  file_path: string;
  project: ProjectData | null;
  error?: string;
}

interface ProjectPreviewProps {
  filePath: string;
  onClose?: () => void;
  onOpenFile?: (path: string) => void;
}

// =============================================================================
// API
// =============================================================================

async function fetchProjectPreview(filePath: string): Promise<ProjectPreviewData> {
  const response = await fetch('/api/repositories/preview-project', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_path: filePath }),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to load preview' }));
    throw new Error(error.detail || 'Failed to load preview');
  }
  
  return response.json();
}

// =============================================================================
// Section Components
// =============================================================================

interface SectionProps {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  defaultExpanded?: boolean;
}

function Section({ title, icon, children, defaultExpanded = true }: SectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 flex items-center gap-3 hover:bg-slate-50 transition-colors"
      >
        <div className="text-slate-400">
          {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        </div>
        <div className="flex items-center gap-2 text-slate-600">
          {icon}
          <span className="font-semibold">{title}</span>
        </div>
      </button>
      
      {isExpanded && (
        <div className="px-4 pb-4 border-t border-slate-100">
          {children}
        </div>
      )}
    </div>
  );
}

interface InfoRowProps {
  label: string;
  value: string | number | null | undefined;
  icon?: React.ReactNode;
  isPath?: boolean;
  onClickPath?: () => void;
}

function InfoRow({ label, value, icon, isPath, onClickPath }: InfoRowProps) {
  if (value === null || value === undefined) return null;
  
  return (
    <div className="flex items-start gap-3 py-2 border-b border-slate-50 last:border-0">
      {icon && <div className="text-slate-400 mt-0.5">{icon}</div>}
      <div className="flex-1 min-w-0">
        <div className="text-xs text-slate-500 mb-0.5">{label}</div>
        {isPath && onClickPath ? (
          <button
            onClick={onClickPath}
            className="text-sm text-blue-600 hover:text-blue-800 hover:underline font-mono truncate block max-w-full text-left"
            title={String(value)}
          >
            {String(value)}
          </button>
        ) : (
          <div 
            className={`text-sm text-slate-800 ${isPath ? 'font-mono truncate' : ''}`}
            title={isPath ? String(value) : undefined}
          >
            {String(value)}
          </div>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// Main ProjectPreview Component
// =============================================================================

export function ProjectPreview({ filePath, onClose, onOpenFile }: ProjectPreviewProps) {
  const [data, setData] = useState<ProjectPreviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load data on mount or path change
  useEffect(() => {
    loadPreview();
  }, [filePath]);

  const loadPreview = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchProjectPreview(filePath);
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load preview');
    } finally {
      setLoading(false);
    }
  };

  // Format date string
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return null;
    try {
      const date = new Date(dateStr);
      return date.toLocaleString();
    } catch {
      return dateStr;
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="flex items-center gap-3 text-slate-500">
          <RefreshCw size={20} className="animate-spin" />
          <span>Loading project config...</span>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="h-full flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="text-center p-8">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 flex items-center justify-center">
            <AlertCircle size={32} className="text-red-500" />
          </div>
          <h3 className="text-lg font-semibold text-slate-700 mb-2">Failed to Load</h3>
          <p className="text-slate-500 mb-4">{error}</p>
          <button
            onClick={loadPreview}
            className="px-4 py-2 bg-slate-800 text-white rounded-lg hover:bg-slate-700 transition-colors flex items-center gap-2 mx-auto"
          >
            <RefreshCw size={16} />
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data || !data.project) return null;

  const project = data.project;

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-50 to-slate-100 overflow-hidden">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 p-6 shadow-sm">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg">
              <Settings size={24} className="text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-800">{project.name}</h2>
              {project.description && (
                <p className="text-sm text-slate-500 mt-1 max-w-xl">{project.description}</p>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={loadPreview}
              className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
              title="Refresh"
            >
              <RefreshCw size={18} />
            </button>
            {onClose && (
              <button
                onClick={onClose}
                className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                title="Close"
              >
                <X size={18} />
              </button>
            )}
          </div>
        </div>
        
        {/* Quick info badges */}
        <div className="flex items-center gap-4 mt-4 text-xs text-slate-500">
          <div className="flex items-center gap-1.5">
            <Hash size={12} />
            <span className="font-mono">{project.id}</span>
          </div>
          {project.updated_at && (
            <div className="flex items-center gap-1.5">
              <Clock size={12} />
              <span>Updated {formatDate(project.updated_at)}</span>
            </div>
          )}
          {project.breakpoints.length > 0 && (
            <div className="flex items-center gap-1.5">
              <Pause size={12} />
              <span>{project.breakpoints.length} breakpoint{project.breakpoints.length !== 1 ? 's' : ''}</span>
            </div>
          )}
        </div>
      </div>
      
      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {/* Repositories Section */}
        <Section 
          title="Repositories" 
          icon={<Database size={18} />}
        >
          <div className="pt-3 space-y-1">
            <InfoRow
              label="Concepts Repository"
              value={project.repositories.concepts}
              icon={<Layers size={14} />}
              isPath
              onClickPath={project.repositories.concepts && onOpenFile ? () => onOpenFile(project.repositories.concepts!) : undefined}
            />
            <InfoRow
              label="Inferences Repository"
              value={project.repositories.inferences}
              icon={<GitBranch size={14} />}
              isPath
              onClickPath={project.repositories.inferences && onOpenFile ? () => onOpenFile(project.repositories.inferences!) : undefined}
            />
            <InfoRow
              label="Inputs Repository"
              value={project.repositories.inputs}
              icon={<FileJson size={14} />}
              isPath
              onClickPath={project.repositories.inputs && onOpenFile ? () => onOpenFile(project.repositories.inputs!) : undefined}
            />
          </div>
        </Section>
        
        {/* Execution Section */}
        <Section 
          title="Execution Settings" 
          icon={<Play size={18} />}
        >
          <div className="pt-3 space-y-1">
            {/* Agent Config - Primary (tool-centric approach) */}
            {project.execution.agent_config ? (
              <div className="p-3 bg-purple-50 rounded-lg border border-purple-200 mb-3">
                <div className="flex items-center gap-2 text-purple-700 font-medium text-sm mb-1">
                  <Settings size={14} />
                  Agent Configuration
                </div>
                <button
                  onClick={onOpenFile ? () => onOpenFile(project.execution.agent_config!) : undefined}
                  className="text-sm text-purple-600 hover:text-purple-800 hover:underline font-mono"
                >
                  {project.execution.agent_config}
                </button>
                <p className="text-xs text-purple-500 mt-1">
                  LLM model and paradigm settings are configured per-agent
                </p>
              </div>
            ) : (
              <div className="p-3 bg-amber-50 rounded-lg border border-amber-200 mb-3">
                <div className="flex items-center gap-2 text-amber-700 font-medium text-sm">
                  <AlertCircle size={14} />
                  No Agent Config
                </div>
                <p className="text-xs text-amber-600 mt-1">
                  This project uses legacy configuration. Consider updating to agent-centric settings.
                </p>
              </div>
            )}
            
            <InfoRow
              label="Max Cycles"
              value={project.execution.max_cycles}
              icon={<RefreshCw size={14} />}
            />
            <InfoRow
              label="Database Path"
              value={project.execution.db_path}
              icon={<Database size={14} />}
              isPath
            />
            
            {/* Deprecated fields - only show if present (legacy configs) */}
            {(project.execution.llm_model || project.execution.base_dir || project.execution.paradigm_dir) && (
              <div className="mt-3 pt-3 border-t border-slate-200">
                <div className="text-xs text-slate-400 mb-2 flex items-center gap-1">
                  <AlertCircle size={10} />
                  Legacy Settings (deprecated - use agent config instead)
                </div>
                <div className="opacity-60">
                  <InfoRow
                    label="LLM Model (deprecated)"
                    value={project.execution.llm_model}
                    icon={<Sparkles size={14} />}
                  />
                  <InfoRow
                    label="Base Directory (deprecated)"
                    value={project.execution.base_dir}
                    icon={<FolderOpen size={14} />}
                    isPath
                  />
                  <InfoRow
                    label="Paradigm Directory (deprecated)"
                    value={project.execution.paradigm_dir}
                    icon={<Cpu size={14} />}
                    isPath
                  />
                </div>
              </div>
            )}
          </div>
        </Section>
        
        {/* Breakpoints Section */}
        {project.breakpoints.length > 0 && (
          <Section 
            title={`Breakpoints (${project.breakpoints.length})`}
            icon={<Pause size={18} />}
          >
            <div className="pt-3 flex flex-wrap gap-2">
              {project.breakpoints.map((bp, idx) => (
                <code
                  key={idx}
                  className="px-3 py-1.5 bg-red-50 text-red-700 rounded-lg text-sm font-mono border border-red-200"
                >
                  {bp}
                </code>
              ))}
            </div>
          </Section>
        )}
        
        {/* Timestamps Section */}
        <Section 
          title="Metadata" 
          icon={<Calendar size={18} />}
          defaultExpanded={false}
        >
          <div className="pt-3 space-y-1">
            <InfoRow
              label="Created"
              value={formatDate(project.created_at)}
              icon={<Calendar size={14} />}
            />
            <InfoRow
              label="Last Updated"
              value={formatDate(project.updated_at)}
              icon={<Clock size={14} />}
            />
          </div>
        </Section>
        
        {/* UI Preferences (if any) */}
        {Object.keys(project.ui_preferences).length > 0 && (
          <Section 
            title="UI Preferences" 
            icon={<Settings size={18} />}
            defaultExpanded={false}
          >
            <div className="pt-3">
              <pre className="bg-slate-50 p-3 rounded-lg text-xs font-mono overflow-x-auto text-slate-700">
                {JSON.stringify(project.ui_preferences, null, 2)}
              </pre>
            </div>
          </Section>
        )}
      </div>
    </div>
  );
}

export default ProjectPreview;


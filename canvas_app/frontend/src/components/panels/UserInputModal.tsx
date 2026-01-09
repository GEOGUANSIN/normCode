/**
 * UserInputModal - Modal for human-in-the-loop user input during execution
 * 
 * This component displays when the orchestrator needs user input to proceed.
 * It supports multiple interaction types:
 * - text_input: Simple single-line text input
 * - text_editor: Multi-line text editor with initial content
 * - confirm: Yes/No confirmation dialog
 * - select: Selection from a list of choices
 * - multi_file_input: File browser for selecting multiple files
 */

import { useState, useEffect, useCallback } from 'react';
import {
  MessageCircle,
  Send,
  X,
  Check,
  XCircle,
  AlertCircle,
  Edit3,
  List,
  RefreshCw,
  FolderOpen,
  File,
  Folder,
  Plus,
  Trash2,
  ArrowUp,
} from 'lucide-react';
import { useExecutionStore, type UserInputRequest } from '../../stores/executionStore';
import { executionApi } from '../../services/api';

interface UserInputModalProps {
  request: UserInputRequest;
  onComplete: () => void;
}

// File browser component for multi_file_input
interface FileEntry {
  name: string;
  path: string;
  is_dir: boolean;
  size?: number;
}

function FileBrowser({ 
  initialDirectory, 
  selectedFiles, 
  onFilesChange 
}: { 
  initialDirectory: string;
  selectedFiles: string[];
  onFilesChange: (files: string[]) => void;
}) {
  const [currentDir, setCurrentDir] = useState(initialDirectory || '');
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [_expandedDirs, _setExpandedDirs] = useState<Set<string>>(new Set());
  const [manualPath, setManualPath] = useState('');

  const loadDirectory = useCallback(async (dir: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/editor/list', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          directory: dir, 
          extensions: null,  // Show all files
          recursive: false 
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to load directory');
      }
      
      const data = await response.json();
      
      // Sort: directories first, then files
      const entries: FileEntry[] = data.files.map((f: { path: string; name: string; size: number; is_dir?: boolean }) => ({
        name: f.name,
        path: f.path,
        is_dir: f.is_dir ?? (f.path.endsWith('/') || f.path.endsWith('\\')),
        size: f.size,
      }));
      
      entries.sort((a, b) => {
        if (a.is_dir && !b.is_dir) return -1;
        if (!a.is_dir && b.is_dir) return 1;
        return a.name.localeCompare(b.name);
      });
      
      setFiles(entries);
      setCurrentDir(dir);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load files');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (initialDirectory) {
      loadDirectory(initialDirectory);
    }
  }, [initialDirectory, loadDirectory]);

  const toggleFile = (filePath: string) => {
    if (selectedFiles.includes(filePath)) {
      onFilesChange(selectedFiles.filter(f => f !== filePath));
    } else {
      onFilesChange([...selectedFiles, filePath]);
    }
  };

  const addManualPath = () => {
    if (manualPath.trim() && !selectedFiles.includes(manualPath.trim())) {
      onFilesChange([...selectedFiles, manualPath.trim()]);
      setManualPath('');
    }
  };

  const navigateUp = () => {
    // Go to parent directory
    const parts = currentDir.replace(/[\\/]+$/, '').split(/[\\/]/);
    if (parts.length > 1) {
      parts.pop();
      const parentDir = parts.join('/') || '/';
      loadDirectory(parentDir);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addManualPath();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Current directory & navigation */}
      <div className="flex items-center gap-2 mb-2 p-2 bg-slate-100 rounded">
        <button
          onClick={navigateUp}
          className="p-1 hover:bg-slate-200 rounded"
          title="Go to parent directory"
        >
          <ArrowUp size={16} />
        </button>
        <div className="flex-1 text-xs text-slate-600 truncate" title={currentDir}>
          {currentDir}
        </div>
        <button
          onClick={() => loadDirectory(currentDir)}
          disabled={loading}
          className="p-1 hover:bg-slate-200 rounded"
          title="Refresh"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* File list */}
      <div className="flex-1 overflow-auto border border-slate-200 rounded mb-2">
        {error && (
          <div className="p-2 text-sm text-red-600">{error}</div>
        )}
        {loading ? (
          <div className="p-4 text-center text-slate-500">
            <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2" />
            Loading...
          </div>
        ) : files.length === 0 ? (
          <div className="p-4 text-center text-slate-400 text-sm">
            No files in this directory
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {files.map((file) => (
              <div
                key={file.path}
                className={`flex items-center gap-2 px-2 py-1.5 hover:bg-slate-50 cursor-pointer ${
                  selectedFiles.includes(file.path) ? 'bg-blue-50' : ''
                }`}
                onClick={() => {
                  if (file.is_dir) {
                    loadDirectory(file.path);
                  } else {
                    toggleFile(file.path);
                  }
                }}
              >
                {file.is_dir ? (
                  <Folder className="w-4 h-4 text-yellow-500 flex-shrink-0" />
                ) : (
                  <File className="w-4 h-4 text-slate-400 flex-shrink-0" />
                )}
                <span className="flex-1 text-sm truncate">{file.name}</span>
                {!file.is_dir && selectedFiles.includes(file.path) && (
                  <Check className="w-4 h-4 text-blue-500 flex-shrink-0" />
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Manual path input */}
      <div className="flex items-center gap-2 mb-2">
        <input
          type="text"
          value={manualPath}
          onChange={(e) => setManualPath(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Or enter file path manually..."
          className="flex-1 px-2 py-1 text-sm border border-slate-300 rounded"
        />
        <button
          onClick={addManualPath}
          disabled={!manualPath.trim()}
          className="p-1.5 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
        >
          <Plus size={14} />
        </button>
      </div>

      {/* Selected files */}
      {selectedFiles.length > 0 && (
        <div className="border border-slate-200 rounded p-2 bg-slate-50">
          <div className="text-xs font-medium text-slate-600 mb-1">
            Selected files ({selectedFiles.length}):
          </div>
          <div className="max-h-24 overflow-auto space-y-1">
            {selectedFiles.map((file) => (
              <div
                key={file}
                className="flex items-center gap-2 text-xs bg-white rounded px-2 py-1"
              >
                <File className="w-3 h-3 text-slate-400 flex-shrink-0" />
                <span className="flex-1 truncate" title={file}>{file}</span>
                <button
                  onClick={() => onFilesChange(selectedFiles.filter(f => f !== file))}
                  className="text-red-400 hover:text-red-600"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function SingleInputModal({ request, onComplete }: UserInputModalProps) {
  const [value, setValue] = useState<string | string[]>('');
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const removeUserInputRequest = useExecutionStore((s) => s.removeUserInputRequest);

  const handleSubmit = async () => {
    let submitValue: unknown = value;
    
    if (request.interaction_type === 'multi_file_input') {
      submitValue = selectedFiles;
      if (selectedFiles.length === 0) {
        // Allow empty submission for multi_file_input
        submitValue = [];
      }
    } else if (!String(value).trim() && request.interaction_type !== 'confirm') {
      setError('Please enter a value');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await executionApi.submitUserInput(request.request_id, submitValue);
      removeUserInputRequest(request.request_id);
      onComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = async () => {
    setSubmitting(true);
    try {
      await executionApi.cancelUserInput(request.request_id);
      removeUserInputRequest(request.request_id);
      onComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel');
    } finally {
      setSubmitting(false);
    }
  };

  const handleConfirm = async (confirmed: boolean) => {
    setSubmitting(true);
    setError(null);

    try {
      await executionApi.submitUserInput(request.request_id, confirmed ? 'yes' : 'no');
      removeUserInputRequest(request.request_id);
      onComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit');
    } finally {
      setSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey && request.interaction_type === 'text_input') {
      e.preventDefault();
      handleSubmit();
    }
  };

  // Set initial content for text_editor
  useEffect(() => {
    if (request.interaction_type === 'text_editor' && request.options?.initial_content) {
      setValue(request.options.initial_content as string);
    }
  }, [request]);

  const getIcon = () => {
    switch (request.interaction_type) {
      case 'text_editor':
        return <Edit3 className="w-5 h-5 text-blue-500" />;
      case 'confirm':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      case 'select':
        return <List className="w-5 h-5 text-purple-500" />;
      case 'multi_file_input':
        return <FolderOpen className="w-5 h-5 text-amber-500" />;
      default:
        return <MessageCircle className="w-5 h-5 text-green-500" />;
    }
  };

  const getSubtitle = () => {
    switch (request.interaction_type) {
      case 'text_input':
        return 'Enter your response';
      case 'text_editor':
        return 'Edit the content below';
      case 'confirm':
        return 'Confirm or deny';
      case 'select':
        return 'Select an option';
      case 'multi_file_input':
        return 'Browse and select files';
      default:
        return '';
    }
  };

  const isMultiFileInput = request.interaction_type === 'multi_file_input';
  const modalWidth = isMultiFileInput ? 'max-w-3xl' : 'max-w-2xl';
  const modalHeight = isMultiFileInput ? 'h-[80vh]' : 'max-h-[80vh]';

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div 
        className={`bg-white rounded-lg shadow-xl w-full ${modalWidth} mx-4 ${modalHeight} flex flex-col`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-200">
          <div className="flex items-center gap-3">
            {getIcon()}
            <div>
              <h2 className="text-lg font-semibold text-slate-800">User Input Required</h2>
              <p className="text-xs text-slate-500">{getSubtitle()}</p>
            </div>
          </div>
          <button
            onClick={handleCancel}
            disabled={submitting}
            className="text-slate-400 hover:text-slate-600 transition-colors disabled:opacity-50"
            title="Cancel and skip"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 flex-1 overflow-auto flex flex-col">
          {/* Prompt */}
          <div className="mb-4 p-3 bg-slate-50 rounded-lg border border-slate-200">
            <p className="text-sm text-slate-700 whitespace-pre-wrap">{request.prompt}</p>
          </div>

          {/* Input based on type */}
          {request.interaction_type === 'text_input' && (
            <input
              type="text"
              value={value as string}
              onChange={(e) => setValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your response..."
              autoFocus
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          )}

          {request.interaction_type === 'text_editor' && (
            <textarea
              value={value as string}
              onChange={(e) => setValue(e.target.value)}
              placeholder="Enter or edit content..."
              autoFocus
              rows={12}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm resize-y"
            />
          )}

          {request.interaction_type === 'select' && request.options?.choices && (
            <div className="space-y-2">
              {(request.options.choices as string[]).map((choice, index) => (
                <button
                  key={index}
                  onClick={() => setValue(choice)}
                  className={`w-full px-4 py-3 text-left rounded-lg border transition-colors ${
                    value === choice
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                  }`}
                >
                  {choice}
                </button>
              ))}
            </div>
          )}

          {request.interaction_type === 'multi_file_input' && (
            <div className="flex-1 min-h-0">
              <FileBrowser
                initialDirectory={request.options?.initial_directory || ''}
                selectedFiles={selectedFiles}
                onFilesChange={setSelectedFiles}
              />
            </div>
          )}

          {/* Error message */}
          {error && (
            <p className="mt-2 text-sm text-red-600 flex items-center gap-1">
              <XCircle size={14} />
              {error}
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 p-4 border-t border-slate-200 bg-slate-50 rounded-b-lg">
          {request.interaction_type === 'confirm' ? (
            <>
              <button
                onClick={() => handleConfirm(false)}
                disabled={submitting}
                className="px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg flex items-center gap-2 transition-colors disabled:opacity-50"
              >
                {submitting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <XCircle className="w-4 h-4" />}
                No
              </button>
              <button
                onClick={() => handleConfirm(true)}
                disabled={submitting}
                className="px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2 transition-colors disabled:opacity-50"
              >
                {submitting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                Yes
              </button>
            </>
          ) : (
            <>
              <button
                onClick={handleCancel}
                disabled={submitting}
                className="px-4 py-2 text-sm text-slate-600 hover:text-slate-800 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={submitting}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
              >
                {submitting ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
                {isMultiFileInput ? `Submit (${selectedFiles.length} files)` : 'Submit'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Main UserInputModal component that shows when there are pending requests
 */
export function UserInputModal() {
  const userInputRequests = useExecutionStore((s) => s.userInputRequests);
  const [currentIndex, setCurrentIndex] = useState(0);

  // Reset index when requests change
  useEffect(() => {
    if (currentIndex >= userInputRequests.length) {
      setCurrentIndex(Math.max(0, userInputRequests.length - 1));
    }
  }, [userInputRequests.length, currentIndex]);

  // No pending requests
  if (userInputRequests.length === 0) {
    return null;
  }

  const currentRequest = userInputRequests[currentIndex];
  if (!currentRequest) {
    return null;
  }

  return (
    <SingleInputModal
      key={currentRequest.request_id}
      request={currentRequest}
      onComplete={() => {
        // Move to next request if available
        if (currentIndex < userInputRequests.length - 1) {
          setCurrentIndex(currentIndex);
        }
      }}
    />
  );
}

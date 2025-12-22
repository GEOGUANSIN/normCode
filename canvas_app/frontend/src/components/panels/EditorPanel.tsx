/**
 * EditorPanel - NormCode file editor component
 * 
 * Allows loading, editing, and saving .ncd, .ncn, .ncdn, .py, .md files
 * with a tree-based file browser preserving folder structure
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  FileText,
  FolderOpen,
  Folder,
  FolderClosed,
  Save,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  File,
  Search,
  X,
  Code,
  FileCode,
  Loader2,
  ChevronRight,
  ChevronDown,
  FileJson,
  FileType,
  Hash,
  Database,
} from 'lucide-react';
import { useProjectStore } from '../../stores/projectStore';

// Types
interface FileInfo {
  name: string;
  path: string;
  format: string;
  size: number;
  modified: number;
}

interface TreeNode {
  name: string;
  path: string;
  type: 'file' | 'folder';
  format?: string;
  size?: number;
  modified?: number;
  children?: TreeNode[];
}

interface FileContent {
  path: string;
  content: string;
  format: string;
}

interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  format: string;
}

interface ParsedLine {
  flow_index: string | null;
  type: 'main' | 'comment' | 'inline_comment';
  depth: number;
  nc_main?: string;
  nc_comment?: string;
  ncn_content?: string;
}

interface ParseResponse {
  lines: ParsedLine[];
  parser_available: boolean;
}

interface PreviewResponse {
  parser_available: boolean;
  previews: {
    ncd?: string;
    ncn?: string;
    ncdn?: string;
    json?: string;
    nci?: string;
  };
}

// Editor view mode
type EditorViewMode = 'raw' | 'parsed' | 'preview';

// API functions
const editorApi = {
  async readFile(path: string): Promise<FileContent> {
    const response = await fetch(`/api/editor/file?path=${encodeURIComponent(path)}`);
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to read file');
    }
    return response.json();
  },

  async saveFile(path: string, content: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch('/api/editor/file', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, content }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to save file');
    }
    return response.json();
  },

  async listFiles(directory: string, recursive: boolean = false): Promise<{ files: FileInfo[] }> {
    const endpoint = recursive ? '/api/editor/list-recursive' : '/api/editor/list';
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        directory,
        extensions: [
          '.ncd', '.ncn', '.ncdn', '.nc.json', '.nci.json', '.json',
          '.py', '.md', '.txt', '.yaml', '.yml', '.toml',
          '.concept.json', '.inference.json'
        ],
      }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to list files');
    }
    return response.json();
  },

  async listFilesTree(directory: string): Promise<{ tree: TreeNode[]; total_files: number }> {
    const response = await fetch('/api/editor/list-tree', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        directory,
        extensions: [
          '.ncd', '.ncn', '.ncdn', '.nc.json', '.nci.json', '.json',
          '.py', '.md', '.txt', '.yaml', '.yml', '.toml',
          '.concept.json', '.inference.json'
        ],
      }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to list files');
    }
    return response.json();
  },

  async validateFile(path: string): Promise<ValidationResult> {
    const response = await fetch(`/api/editor/validate?path=${encodeURIComponent(path)}`);
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to validate file');
    }
    return response.json();
  },

  async parseContent(content: string, format: string): Promise<ParseResponse> {
    const response = await fetch('/api/editor/parse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, format }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to parse content');
    }
    return response.json();
  },

  async getPreviews(content: string, format: string): Promise<PreviewResponse> {
    const response = await fetch('/api/editor/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, format }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get previews');
    }
    return response.json();
  },

  async getParserStatus(): Promise<{ available: boolean; message: string }> {
    const response = await fetch('/api/editor/parser-status');
    if (!response.ok) {
      return { available: false, message: 'Failed to check parser status' };
    }
    return response.json();
  },
};

// Format icon mapping
const formatIcons: Record<string, React.ReactNode> = {
  // NormCode formats
  ncd: <FileCode className="w-4 h-4 text-blue-500" />,
  ncn: <FileText className="w-4 h-4 text-green-500" />,
  ncdn: <Code className="w-4 h-4 text-purple-500" />,
  nci: <FileJson className="w-4 h-4 text-red-500" />,
  'nc-json': <FileJson className="w-4 h-4 text-orange-500" />,
  concept: <Database className="w-4 h-4 text-cyan-500" />,
  inference: <Hash className="w-4 h-4 text-pink-500" />,
  // Common formats
  json: <FileJson className="w-4 h-4 text-yellow-500" />,
  python: <FileType className="w-4 h-4 text-blue-400" />,
  markdown: <FileText className="w-4 h-4 text-gray-600" />,
  yaml: <File className="w-4 h-4 text-amber-500" />,
  toml: <File className="w-4 h-4 text-orange-400" />,
  text: <FileText className="w-4 h-4 text-gray-400" />,
};

export function EditorPanel() {
  // Get project path from store
  const projectPath = useProjectStore((s) => s.projectPath);
  
  // State - initialize directoryPath with projectPath
  const [directoryPath, setDirectoryPath] = useState<string>(projectPath || '');
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [fileTree, setFileTree] = useState<TreeNode[]>([]);
  const [totalFiles, setTotalFiles] = useState(0);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [originalContent, setOriginalContent] = useState<string>('');
  const [fileFormat, setFileFormat] = useState<string>('');
  const [isModified, setIsModified] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [showFileBrowser, setShowFileBrowser] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [useTreeView, setUseTreeView] = useState(true);
  
  // Parser and preview state
  const [editorViewMode, setEditorViewMode] = useState<EditorViewMode>('raw');
  const [parsedLines, setParsedLines] = useState<ParsedLine[]>([]);
  const [previews, setPreviews] = useState<PreviewResponse['previews']>({});
  const [previewTab, setPreviewTab] = useState<string>('ncd');
  const [parserAvailable, setParserAvailable] = useState<boolean>(true);
  const [isParsing, setIsParsing] = useState(false);
  
  // Track if we've done initial load
  const initialLoadDone = useRef(false);

  // Clear messages after timeout
  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => setSuccessMessage(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [successMessage]);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  // Track modifications
  useEffect(() => {
    setIsModified(fileContent !== originalContent);
  }, [fileContent, originalContent]);

  // Load files from directory (both tree and flat list)
  const loadFiles = useCallback(async (dir?: string) => {
    const targetDir = dir || directoryPath;
    if (!targetDir.trim()) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      // Load both tree and flat list
      const [treeResult, flatResult] = await Promise.all([
        editorApi.listFilesTree(targetDir),
        editorApi.listFiles(targetDir, true)
      ]);
      setFileTree(treeResult.tree);
      setTotalFiles(treeResult.total_files);
      setFiles(flatResult.files);
      if (dir) setDirectoryPath(dir);
      
      // Auto-expand first level folders
      const firstLevelFolders = treeResult.tree
        .filter(n => n.type === 'folder')
        .map(n => n.path);
      setExpandedFolders(new Set(firstLevelFolders));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load files');
      setFiles([]);
      setFileTree([]);
    } finally {
      setIsLoading(false);
    }
  }, [directoryPath]);
  
  // Auto-load files from project directory on mount
  useEffect(() => {
    if (projectPath && !initialLoadDone.current) {
      initialLoadDone.current = true;
      setDirectoryPath(projectPath);
      loadFiles(projectPath);
    }
  }, [projectPath, loadFiles]);

  // Load a specific file
  const loadFile = useCallback(async (path: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await editorApi.readFile(path);
      setSelectedFile(result.path);
      setFileContent(result.content);
      setOriginalContent(result.content);
      setFileFormat(result.format);
      setValidation(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load file');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Save current file
  const saveFile = useCallback(async () => {
    if (!selectedFile) return;
    
    setIsSaving(true);
    setError(null);
    
    try {
      const result = await editorApi.saveFile(selectedFile, fileContent);
      if (result.success) {
        setOriginalContent(fileContent);
        setIsModified(false);
        setSuccessMessage('File saved successfully');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save file');
    } finally {
      setIsSaving(false);
    }
  }, [selectedFile, fileContent]);

  // Validate current file
  const validateFile = useCallback(async () => {
    if (!selectedFile) return;
    
    try {
      const result = await editorApi.validateFile(selectedFile);
      setValidation(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to validate file');
    }
  }, [selectedFile]);

  // Parse content for structured view
  const parseContent = useCallback(async () => {
    if (!fileContent) return;
    
    setIsParsing(true);
    try {
      const result = await editorApi.parseContent(fileContent, fileFormat);
      setParsedLines(result.lines);
      setParserAvailable(result.parser_available);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to parse content');
      setParsedLines([]);
    } finally {
      setIsParsing(false);
    }
  }, [fileContent, fileFormat]);

  // Get previews in all formats
  const loadPreviews = useCallback(async () => {
    if (!fileContent) return;
    
    setIsParsing(true);
    try {
      const result = await editorApi.getPreviews(fileContent, fileFormat);
      setPreviews(result.previews);
      setParserAvailable(result.parser_available);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load previews');
      setPreviews({});
    } finally {
      setIsParsing(false);
    }
  }, [fileContent, fileFormat]);

  // Load parsed/preview when switching view mode
  useEffect(() => {
    if (editorViewMode === 'parsed' && fileContent) {
      parseContent();
    } else if (editorViewMode === 'preview' && fileContent) {
      loadPreviews();
    }
  }, [editorViewMode, parseContent, loadPreviews, fileContent]);

  // Reload current file
  const reloadFile = useCallback(async () => {
    if (!selectedFile) return;
    
    if (isModified) {
      const confirm = window.confirm('You have unsaved changes. Discard them and reload?');
      if (!confirm) return;
    }
    
    await loadFile(selectedFile);
  }, [selectedFile, isModified, loadFile]);

  // Filter files by search query
  const filteredFiles = files.filter(f => 
    f.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Toggle folder expansion
  const toggleFolder = useCallback((folderPath: string) => {
    setExpandedFolders(prev => {
      const next = new Set(prev);
      if (next.has(folderPath)) {
        next.delete(folderPath);
      } else {
        next.add(folderPath);
      }
      return next;
    });
  }, []);

  // Filter tree nodes by search query
  const filterTreeNodes = useCallback((nodes: TreeNode[], query: string): TreeNode[] => {
    if (!query) return nodes;
    
    return nodes.reduce<TreeNode[]>((acc, node) => {
      if (node.type === 'folder') {
        const filteredChildren = filterTreeNodes(node.children || [], query);
        if (filteredChildren.length > 0) {
          acc.push({ ...node, children: filteredChildren });
        }
      } else {
        if (node.name.toLowerCase().includes(query.toLowerCase())) {
          acc.push(node);
        }
      }
      return acc;
    }, []);
  }, []);

  const filteredTree = filterTreeNodes(fileTree, searchQuery);

  // Render a tree node recursively
  const renderTreeNode = useCallback((node: TreeNode, depth: number = 0) => {
    const isFolder = node.type === 'folder';
    const isExpanded = expandedFolders.has(node.path);
    const isSelected = selectedFile === node.path;
    
    return (
      <div key={node.path}>
        <button
          onClick={() => isFolder ? toggleFolder(node.path) : loadFile(node.path)}
          className={`w-full text-left flex items-center gap-1.5 py-1 px-2 hover:bg-gray-100 text-sm
            ${isSelected ? 'bg-blue-50 border-l-2 border-blue-500' : ''}`}
          style={{ paddingLeft: `${8 + depth * 16}px` }}
        >
          {isFolder ? (
            <>
              {isExpanded ? (
                <ChevronDown className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
              ) : (
                <ChevronRight className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
              )}
              {isExpanded ? (
                <FolderOpen className="w-4 h-4 text-amber-500 flex-shrink-0" />
              ) : (
                <FolderClosed className="w-4 h-4 text-amber-500 flex-shrink-0" />
              )}
            </>
          ) : (
            <>
              <span className="w-3.5 flex-shrink-0" /> {/* Spacer for alignment */}
              {formatIcons[node.format || 'text'] || formatIcons.text}
            </>
          )}
          <span className="truncate flex-1" title={node.name}>
            {node.name}
          </span>
          {!isFolder && node.size !== undefined && (
            <span className="text-xs text-gray-400 flex-shrink-0">
              {node.size < 1024 
                ? `${node.size}B`
                : `${(node.size / 1024).toFixed(1)}KB`
              }
            </span>
          )}
        </button>
        {isFolder && isExpanded && node.children && (
          <div>
            {node.children.map(child => renderTreeNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  }, [expandedFolders, selectedFile, toggleFolder, loadFile]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey) {
        if (e.key === 's') {
          e.preventDefault();
          saveFile();
        }
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [saveFile]);

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Compact Toolbar - no title since main header has tabs */}
      <div className="bg-white border-b px-3 py-1.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Toggle file browser */}
          <button
            onClick={() => setShowFileBrowser(!showFileBrowser)}
            className={`p-1.5 rounded transition-colors ${
              showFileBrowser 
                ? 'bg-blue-50 text-blue-600' 
                : 'hover:bg-gray-100 text-gray-500'
            }`}
            title={showFileBrowser ? 'Hide file browser' : 'Show file browser'}
          >
            <FolderOpen className="w-4 h-4" />
          </button>
          
          {/* Current file info */}
          {selectedFile ? (
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-700 font-medium truncate max-w-md">
                {selectedFile.split(/[/\\]/).pop()}
              </span>
              {isModified && (
                <span className="text-orange-500" title="Unsaved changes">●</span>
              )}
            </div>
          ) : (
            <span className="text-sm text-gray-400">No file selected</span>
          )}
        </div>
        
        <div className="flex items-center gap-1">
          {/* Reload button */}
          <button
            onClick={reloadFile}
            disabled={!selectedFile || isLoading}
            className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-50 text-gray-500"
            title="Reload file"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          
          {/* Save button */}
          <button
            onClick={saveFile}
            disabled={!selectedFile || !isModified || isSaving}
            className={`px-2.5 py-1 rounded text-xs font-medium flex items-center gap-1 
              ${isModified 
                ? 'bg-blue-600 text-white hover:bg-blue-700' 
                : 'bg-gray-100 text-gray-400'
              } disabled:opacity-50`}
            title="Save file (Ctrl+S)"
          >
            {isSaving ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <Save className="w-3 h-3" />
            )}
            Save
          </button>
        </div>
      </div>

      {/* Messages */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-2 flex items-center gap-2 text-red-700 text-sm">
          <AlertCircle className="w-4 h-4" />
          {error}
          <button onClick={() => setError(null)} className="ml-auto">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
      
      {successMessage && (
        <div className="bg-green-50 border-b border-green-200 px-4 py-2 flex items-center gap-2 text-green-700 text-sm">
          <CheckCircle className="w-4 h-4" />
          {successMessage}
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 flex min-h-0">
        {/* File browser sidebar */}
        {showFileBrowser && (
          <div className="w-72 bg-white border-r flex flex-col">
            {/* Directory input */}
            <div className="p-3 border-b space-y-2">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={directoryPath}
                  onChange={(e) => setDirectoryPath(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && loadFiles()}
                  placeholder="Enter directory path..."
                  className="flex-1 px-3 py-1.5 text-sm border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={() => loadFiles()}
                  disabled={isLoading || !directoryPath.trim()}
                  className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50"
                >
                  Load
                </button>
              </div>
              
              {/* View toggle and search */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setUseTreeView(!useTreeView)}
                  className={`px-2 py-1 text-xs rounded border ${
                    useTreeView 
                      ? 'bg-blue-50 border-blue-300 text-blue-600'
                      : 'border-gray-300 text-gray-600 hover:bg-gray-50'
                  }`}
                  title={useTreeView ? 'Tree view' : 'Flat list view'}
                >
                  {useTreeView ? <FolderOpen className="w-3 h-3" /> : <FileText className="w-3 h-3" />}
                </button>
                <div className="relative flex-1">
                  <Search className="w-4 h-4 absolute left-2 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Filter files..."
                    className="w-full pl-8 pr-3 py-1.5 text-sm border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  {searchQuery && (
                    <button 
                      onClick={() => setSearchQuery('')}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  )}
                </div>
              </div>
            </div>
            
            {/* File browser - Tree or Flat view */}
            <div className="flex-1 overflow-y-auto">
              {isLoading && fileTree.length === 0 ? (
                <div className="p-4 text-center text-gray-500">
                  <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
                  Loading files...
                </div>
              ) : useTreeView ? (
                /* Tree View */
                filteredTree.length === 0 ? (
                  <div className="p-4 text-center text-gray-500 text-sm">
                    {fileTree.length === 0 
                      ? 'Enter a directory path and click Load'
                      : 'No matching files found'
                    }
                  </div>
                ) : (
                  <div className="py-1">
                    {filteredTree.map(node => renderTreeNode(node, 0))}
                  </div>
                )
              ) : (
                /* Flat List View */
                filteredFiles.length === 0 ? (
                  <div className="p-4 text-center text-gray-500 text-sm">
                    {files.length === 0 
                      ? 'Enter a directory path and click Load'
                      : 'No matching files found'
                    }
                  </div>
                ) : (
                  <div className="py-1">
                    {filteredFiles.map((file) => (
                      <button
                        key={file.path}
                        onClick={() => loadFile(file.path)}
                        className={`w-full px-3 py-1.5 text-left flex items-center gap-2 hover:bg-gray-100 text-sm
                          ${selectedFile === file.path ? 'bg-blue-50 border-l-2 border-blue-500' : ''}`}
                      >
                        {formatIcons[file.format] || formatIcons.text}
                        <span className="truncate flex-1 text-xs" title={file.name}>
                          {file.name}
                        </span>
                        <span className="text-xs text-gray-400 flex-shrink-0">
                          {(file.size / 1024).toFixed(1)}KB
                        </span>
                      </button>
                    ))}
                  </div>
                )
              )}
            </div>
            
            {/* File count */}
            {totalFiles > 0 && (
              <div className="p-2 border-t text-xs text-gray-500 text-center flex items-center justify-center gap-2">
                <span>{searchQuery ? filteredFiles.length + ' matching /' : ''} {totalFiles} files</span>
                {useTreeView && (
                  <button
                    onClick={() => setExpandedFolders(new Set())}
                    className="text-blue-500 hover:underline"
                    title="Collapse all folders"
                  >
                    collapse
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {/* Editor area */}
        <div className="flex-1 flex flex-col min-w-0">
          {selectedFile ? (
            <>
              {/* Editor toolbar */}
              <div className="bg-gray-100 px-4 py-2 flex items-center justify-between border-b">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-medium px-2 py-0.5 rounded bg-gray-200 text-gray-700 uppercase">
                    {fileFormat}
                  </span>
                  
                  {/* View mode toggle */}
                  <div className="flex items-center bg-white rounded border">
                    <button
                      onClick={() => setEditorViewMode('raw')}
                      className={`px-2 py-1 text-xs rounded-l ${
                        editorViewMode === 'raw' 
                          ? 'bg-blue-600 text-white' 
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      Raw
                    </button>
                    <button
                      onClick={() => setEditorViewMode('parsed')}
                      className={`px-2 py-1 text-xs border-x ${
                        editorViewMode === 'parsed' 
                          ? 'bg-blue-600 text-white' 
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      Parsed
                    </button>
                    <button
                      onClick={() => setEditorViewMode('preview')}
                      className={`px-2 py-1 text-xs rounded-r ${
                        editorViewMode === 'preview' 
                          ? 'bg-blue-600 text-white' 
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      Preview
                    </button>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  {isParsing && <Loader2 className="w-4 h-4 animate-spin text-gray-400" />}
                  <button
                    onClick={validateFile}
                    className="text-xs px-2 py-1 rounded border hover:bg-white"
                  >
                    Validate
                  </button>
                </div>
              </div>
              
              {/* Validation messages */}
              {validation && (
                <div className={`px-4 py-2 text-sm border-b ${
                  validation.valid ? 'bg-green-50' : 'bg-yellow-50'
                }`}>
                  <div className="flex items-center gap-2">
                    {validation.valid ? (
                      <>
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span className="text-green-700">File is valid</span>
                      </>
                    ) : (
                      <>
                        <AlertCircle className="w-4 h-4 text-yellow-600" />
                        <span className="text-yellow-700">
                          {validation.errors.length} error(s), {validation.warnings.length} warning(s)
                        </span>
                      </>
                    )}
                  </div>
                  {validation.errors.length > 0 && (
                    <ul className="mt-1 ml-6 text-xs text-red-600">
                      {validation.errors.map((e, i) => <li key={i}>{e}</li>)}
                    </ul>
                  )}
                  {validation.warnings.length > 0 && (
                    <ul className="mt-1 ml-6 text-xs text-yellow-600">
                      {validation.warnings.map((w, i) => <li key={i}>{w}</li>)}
                    </ul>
                  )}
                </div>
              )}
              
              {/* Editor content area - switches based on view mode */}
              <div className="flex-1 min-h-0 overflow-hidden">
                {editorViewMode === 'raw' && (
                  /* Raw text editor */
                  <textarea
                    value={fileContent}
                    onChange={(e) => setFileContent(e.target.value)}
                    className="w-full h-full p-4 font-mono text-sm resize-none focus:outline-none"
                    style={{
                      tabSize: 4,
                      lineHeight: '1.5',
                    }}
                    spellCheck={false}
                    placeholder="File content will appear here..."
                  />
                )}
                
                {editorViewMode === 'parsed' && (
                  /* Parsed view with flow indices */
                  <div className="h-full overflow-auto bg-white">
                    {!parserAvailable ? (
                      <div className="p-4 text-center text-gray-500">
                        <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
                        <p className="text-sm">Parser not available</p>
                        <p className="text-xs mt-1">The unified_parser module is not loaded</p>
                      </div>
                    ) : isParsing ? (
                      <div className="p-4 text-center text-gray-500">
                        <Loader2 className="w-6 h-6 animate-spin mx-auto" />
                        <p className="text-sm mt-2">Parsing...</p>
                      </div>
                    ) : parsedLines.length === 0 ? (
                      <div className="p-4 text-center text-gray-500">
                        <p className="text-sm">No parsed content</p>
                      </div>
                    ) : (
                      <table className="w-full text-sm font-mono">
                        <thead className="bg-gray-50 sticky top-0">
                          <tr className="text-left text-xs text-gray-500">
                            <th className="px-3 py-2 w-24 border-b">Flow Index</th>
                            <th className="px-3 py-2 w-16 border-b">Type</th>
                            <th className="px-3 py-2 border-b">Content</th>
                          </tr>
                        </thead>
                        <tbody>
                          {parsedLines.map((line, idx) => (
                            <tr key={idx} className="hover:bg-gray-50 border-b border-gray-100">
                              <td className="px-3 py-1.5 text-blue-600 font-medium">
                                {line.flow_index || ''}
                              </td>
                              <td className="px-3 py-1.5">
                                <span className={`text-xs px-1.5 py-0.5 rounded ${
                                  line.type === 'main' 
                                    ? 'bg-blue-100 text-blue-700' 
                                    : line.type === 'comment'
                                    ? 'bg-gray-100 text-gray-600'
                                    : 'bg-yellow-100 text-yellow-700'
                                }`}>
                                  {line.type}
                                </span>
                              </td>
                              <td className="px-3 py-1.5" style={{ paddingLeft: `${12 + line.depth * 20}px` }}>
                                <span className="text-gray-800">
                                  {line.nc_main || line.nc_comment || ''}
                                </span>
                                {line.ncn_content && (
                                  <span className="text-green-600 ml-2 text-xs">
                                    → {line.ncn_content}
                                  </span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                )}
                
                {editorViewMode === 'preview' && (
                  /* Preview tabs for different formats */
                  <div className="h-full flex flex-col">
                    {/* Preview format tabs */}
                    <div className="bg-gray-50 border-b px-4 py-1 flex gap-1">
                      {['ncd', 'ncn', 'ncdn', 'json', 'nci'].map(fmt => (
                        <button
                          key={fmt}
                          onClick={() => setPreviewTab(fmt)}
                          className={`px-3 py-1 text-xs rounded-t ${
                            previewTab === fmt
                              ? 'bg-white border-t border-x -mb-px text-blue-600 font-medium'
                              : 'text-gray-500 hover:text-gray-700'
                          }`}
                        >
                          {fmt.toUpperCase()}
                        </button>
                      ))}
                    </div>
                    
                    {/* Preview content */}
                    <div className="flex-1 overflow-auto bg-white">
                      {!parserAvailable ? (
                        <div className="p-4 text-center text-gray-500">
                          <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
                          <p className="text-sm">Parser not available</p>
                        </div>
                      ) : isParsing ? (
                        <div className="p-4 text-center text-gray-500">
                          <Loader2 className="w-6 h-6 animate-spin mx-auto" />
                        </div>
                      ) : (
                        <pre className="p-4 font-mono text-sm whitespace-pre-wrap text-gray-800">
                          {previews[previewTab as keyof typeof previews] || `No ${previewTab} preview available`}
                        </pre>
                      )}
                    </div>
                  </div>
                )}
              </div>
              
              {/* Status bar */}
              <div className="bg-gray-100 px-4 py-1 border-t flex items-center justify-between text-xs text-gray-500">
                <div>
                  Lines: {fileContent.split('\n').length} | 
                  Characters: {fileContent.length}
                </div>
                <div>
                  {isModified ? 'Modified' : 'Saved'}
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center bg-gray-50">
              <div className="text-center text-gray-500">
                <FileText className="w-16 h-16 mx-auto mb-4 opacity-30" />
                <p className="text-lg font-medium">No file selected</p>
                <p className="text-sm mt-1">
                  Select a file from the browser or enter a directory path
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default EditorPanel;

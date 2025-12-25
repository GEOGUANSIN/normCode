/**
 * EditorPanel - NormCode file editor component
 * 
 * Features:
 * - Line-by-line editing with flow indices
 * - View mode toggle (NCD/NCN) per line
 * - Filter controls (show/hide comments, collapse sections)
 * - Pure text editing mode with flow index prefixes
 * - Add/delete line controls
 * - Tab handling for indentation
 */

import React, { useState, useEffect, useCallback, useRef, KeyboardEvent } from 'react';
import {
  FileText,
  FolderOpen,
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
  Plus,
  Trash2,
  Eye,
  EyeOff,
  Filter,
  Minus,
  RotateCw,
  MessageSquare,
  Settings2,
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

// Editor modes
type EditorMode = 'line_by_line' | 'pure_text';
type ViewMode = 'ncd' | 'ncn';
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
          '.concept.json', '.inference.json', '.ncds'
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
          '.concept.json', '.inference.json', '.ncds'
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

  async serializeLines(lines: ParsedLine[], format: string): Promise<{ success: boolean; content: string }> {
    const response = await fetch('/api/editor/lines/serialize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lines, format }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to serialize');
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
  ncd: <FileCode className="w-4 h-4 text-blue-500" />,
  ncn: <FileText className="w-4 h-4 text-green-500" />,
  ncdn: <Code className="w-4 h-4 text-purple-500" />,
  ncds: <Code className="w-4 h-4 text-indigo-500" />,
  nci: <FileJson className="w-4 h-4 text-red-500" />,
  'nc-json': <FileJson className="w-4 h-4 text-orange-500" />,
  concept: <Database className="w-4 h-4 text-cyan-500" />,
  inference: <Hash className="w-4 h-4 text-pink-500" />,
  json: <FileJson className="w-4 h-4 text-yellow-500" />,
  python: <FileType className="w-4 h-4 text-blue-400" />,
  markdown: <FileText className="w-4 h-4 text-gray-600" />,
  yaml: <File className="w-4 h-4 text-amber-500" />,
  toml: <File className="w-4 h-4 text-orange-400" />,
  text: <FileText className="w-4 h-4 text-gray-400" />,
};

// Type indicator icons
const typeIcons: Record<string, { icon: React.ReactNode; label: string }> = {
  main: { icon: <Code className="w-3 h-3 text-blue-500" />, label: 'Main' },
  comment: { icon: <MessageSquare className="w-3 h-3 text-gray-400" />, label: 'Comment' },
  inline_comment: { icon: <MessageSquare className="w-3 h-3 text-yellow-500" />, label: 'Inline' },
};

export function EditorPanel() {
  // Get project path from store
  const projectPath = useProjectStore((s) => s.projectPath);
  
  // File browser state
  const [directoryPath, setDirectoryPath] = useState<string>(projectPath || '');
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [fileTree, setFileTree] = useState<TreeNode[]>([]);
  const [totalFiles, setTotalFiles] = useState(0);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [showFileBrowser, setShowFileBrowser] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [useTreeView, setUseTreeView] = useState(true);
  
  // File content state
  const [fileContent, setFileContent] = useState<string>('');
  const [originalContent, setOriginalContent] = useState<string>('');
  const [fileFormat, setFileFormat] = useState<string>('');
  const [isModified, setIsModified] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  
  // Parsed content state
  const [parsedLines, setParsedLines] = useState<ParsedLine[]>([]);
  const [parserAvailable, setParserAvailable] = useState<boolean>(true);
  const [isParsing, setIsParsing] = useState(false);
  
  // Editor mode state
  const [editorMode, setEditorMode] = useState<EditorMode>('line_by_line');
  const [editorViewMode, setEditorViewMode] = useState<EditorViewMode>('raw');
  const [defaultViewMode, setDefaultViewMode] = useState<ViewMode>('ncd');
  const [lineViewModes, setLineViewModes] = useState<Record<number, ViewMode>>({});
  
  // Filter state
  const [showComments, setShowComments] = useState(true);
  const [showNaturalLanguage, setShowNaturalLanguage] = useState(true);
  const [collapsedIndices, setCollapsedIndices] = useState<Set<string>>(new Set());
  
  // Delete confirmation state
  const [deleteConfirmations, setDeleteConfirmations] = useState<Set<number>>(new Set());
  
  // Preview state
  const [previews, setPreviews] = useState<PreviewResponse['previews']>({});
  const [previewTab, setPreviewTab] = useState<string>('ncd');
  
  // Text editor state
  const [textEditorKey, setTextEditorKey] = useState(0);
  const [pendingText, setPendingText] = useState<string | null>(null);
  
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

  // Load files from directory
  const loadFiles = useCallback(async (dir?: string) => {
    const targetDir = dir || directoryPath;
    if (!targetDir.trim()) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const [treeResult, flatResult] = await Promise.all([
        editorApi.listFilesTree(targetDir),
        editorApi.listFiles(targetDir, true)
      ]);
      setFileTree(treeResult.tree);
      setTotalFiles(treeResult.total_files);
      setFiles(flatResult.files);
      if (dir) setDirectoryPath(dir);
      
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
      setParsedLines([]);
      setLineViewModes({});
      setCollapsedIndices(new Set());
      setTextEditorKey(prev => prev + 1);
      
      // Auto-parse for NormCode files
      if (['ncd', 'ncn', 'ncdn', 'ncds'].includes(result.format)) {
        const parseResult = await editorApi.parseContent(result.content, result.format);
        setParsedLines(parseResult.lines);
        setParserAvailable(parseResult.parser_available);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load file');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Parse current content
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

  // Save current file
  const saveFile = useCallback(async () => {
    if (!selectedFile) return;
    
    setIsSaving(true);
    setError(null);
    
    try {
      // If we have parsed lines, serialize them back to the correct format
      if (parsedLines.length > 0 && ['ncd', 'ncdn', 'ncds'].includes(fileFormat)) {
        const serialized = await editorApi.serializeLines(parsedLines, fileFormat);
        if (serialized.success) {
          const result = await editorApi.saveFile(selectedFile, serialized.content);
          if (result.success) {
            setOriginalContent(serialized.content);
            setFileContent(serialized.content);
            setIsModified(false);
            setSuccessMessage('File saved successfully');
          }
        }
      } else {
        const result = await editorApi.saveFile(selectedFile, fileContent);
        if (result.success) {
          setOriginalContent(fileContent);
          setIsModified(false);
          setSuccessMessage('File saved successfully');
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save file');
    } finally {
      setIsSaving(false);
    }
  }, [selectedFile, fileContent, parsedLines, fileFormat]);

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

  // Load previews
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
    if (editorViewMode === 'parsed' && fileContent && parsedLines.length === 0) {
      parseContent();
    } else if (editorViewMode === 'preview' && fileContent) {
      loadPreviews();
    }
  }, [editorViewMode, parseContent, loadPreviews, fileContent, parsedLines.length]);

  // Reload current file
  const reloadFile = useCallback(async () => {
    if (!selectedFile) return;
    
    if (isModified) {
      const confirm = window.confirm('You have unsaved changes. Discard them and reload?');
      if (!confirm) return;
    }
    
    await loadFile(selectedFile);
  }, [selectedFile, isModified, loadFile]);

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
  const filteredFiles = files.filter(f => 
    f.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Line operations
  const updateLine = useCallback((lineIndex: number, field: string, value: string) => {
    setParsedLines(prev => {
      const updated = [...prev];
      updated[lineIndex] = { ...updated[lineIndex], [field]: value };
      return updated;
    });
    setIsModified(true);
  }, []);

  const addLineAfter = useCallback((afterIndex: number, lineType: 'main' | 'comment' = 'main') => {
    setParsedLines(prev => {
      const updated = [...prev];
      const insertIndex = afterIndex + 1;
      
      // Get context from reference line
      const refLine = afterIndex >= 0 ? prev[afterIndex] : prev[prev.length - 1] || { depth: 0, flow_index: '0' };
      const refDepth = refLine.depth || 0;
      const refFlow = refLine.flow_index || '1';
      
      // Calculate new flow index
      let newFlow = '1';
      if (refFlow) {
        const parts = refFlow.split('.');
        parts[parts.length - 1] = String(parseInt(parts[parts.length - 1] || '0', 10) + 1);
        newFlow = parts.join('.');
      }
      
      const newLine: ParsedLine = {
        flow_index: newFlow,
        type: lineType,
        depth: refDepth,
        nc_main: lineType === 'main' ? '' : undefined,
        nc_comment: lineType !== 'main' ? '' : undefined,
        ncn_content: lineType === 'main' ? '' : undefined,
      };
      
      updated.splice(insertIndex, 0, newLine);
      return updated;
    });
    setIsModified(true);
  }, []);

  const deleteLine = useCallback((lineIndex: number) => {
    setParsedLines(prev => {
      const updated = [...prev];
      updated.splice(lineIndex, 1);
      return updated;
    });
    setDeleteConfirmations(prev => {
      const next = new Set(prev);
      next.delete(lineIndex);
      return next;
    });
    setIsModified(true);
  }, []);

  // Toggle line view mode
  const toggleLineViewMode = useCallback((lineIndex: number) => {
    setLineViewModes(prev => ({
      ...prev,
      [lineIndex]: prev[lineIndex] === 'ncn' ? 'ncd' : 'ncn'
    }));
  }, []);

  // Toggle collapse for a flow index
  const toggleCollapse = useCallback((flowIndex: string) => {
    setCollapsedIndices(prev => {
      const next = new Set(prev);
      if (next.has(flowIndex)) {
        next.delete(flowIndex);
      } else {
        next.add(flowIndex);
      }
      return next;
    });
  }, []);

  // Check if line is collapsed
  const isLineCollapsed = useCallback((flowIndex: string | null): boolean => {
    if (!flowIndex) return false;
    for (const collapsed of collapsedIndices) {
      if (flowIndex.startsWith(collapsed + '.')) {
        return true;
      }
    }
    return false;
  }, [collapsedIndices]);

  // Check if line has children
  const hasChildren = useCallback((flowIndex: string | null): boolean => {
    if (!flowIndex) return false;
    return parsedLines.some(line => 
      line.flow_index && line.flow_index.startsWith(flowIndex + '.') && line.type === 'main'
    );
  }, [parsedLines]);

  // Handle Tab key in text areas
  const handleTextAreaKeyDown = useCallback((e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key !== 'Tab') return;
    
    e.preventDefault();
    const target = e.target as HTMLTextAreaElement;
    const start = target.selectionStart;
    const end = target.selectionEnd;
    const value = target.value;
    
    if (e.shiftKey) {
      // Shift+Tab: Unindent
      const beforeSel = value.substring(0, start);
      const lineStart = beforeSel.lastIndexOf('\n') + 1;
      const lineEnd = value.indexOf('\n', end);
      const actualEnd = lineEnd === -1 ? value.length : lineEnd;
      const selectedText = value.substring(lineStart, actualEnd);
      const lines = selectedText.split('\n');
      
      let totalChange = 0;
      let firstLineChange = 0;
      
      const newLines = lines.map((line, idx) => {
        let change = 0;
        if (line.startsWith('    ')) { line = line.substring(4); change = 4; }
        else if (line.startsWith('\t')) { line = line.substring(1); change = 1; }
        else if (line.startsWith('   ')) { line = line.substring(3); change = 3; }
        else if (line.startsWith('  ')) { line = line.substring(2); change = 2; }
        else if (line.startsWith(' ')) { line = line.substring(1); change = 1; }
        
        if (idx === 0) firstLineChange = change;
        totalChange += change;
        return line;
      });
      
      const newValue = value.substring(0, lineStart) + newLines.join('\n') + value.substring(actualEnd);
      target.value = newValue;
      target.selectionStart = Math.max(lineStart, start - firstLineChange);
      target.selectionEnd = Math.max(target.selectionStart, end - totalChange);
    } else {
      // Tab: Indent
      if (start === end) {
        // No selection - insert spaces at cursor
        target.value = value.substring(0, start) + '    ' + value.substring(end);
        target.selectionStart = target.selectionEnd = start + 4;
      } else {
        // Selection - indent each line
        const beforeSel = value.substring(0, start);
        const lineStart = beforeSel.lastIndexOf('\n') + 1;
        const lineEnd = value.indexOf('\n', end);
        const actualEnd = lineEnd === -1 ? value.length : lineEnd;
        const selectedText = value.substring(lineStart, actualEnd);
        const lines = selectedText.split('\n');
        
        const newLines = lines.map(line => '    ' + line);
        target.value = value.substring(0, lineStart) + newLines.join('\n') + value.substring(actualEnd);
        target.selectionStart = start + 4;
        target.selectionEnd = end + (lines.length * 4);
      }
    }
    
    // Trigger React change
    const event = new Event('input', { bubbles: true });
    target.dispatchEvent(event);
  }, []);

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
              <span className="w-3.5 flex-shrink-0" />
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
    const handleKeyDown = (e: globalThis.KeyboardEvent) => {
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

  // Check if file is a NormCode format
  const isNormCodeFormat = ['ncd', 'ncn', 'ncdn', 'ncds'].includes(fileFormat);

  // Get visible lines count
  const getVisibleLinesCount = useCallback(() => {
    let count = 0;
    for (const line of parsedLines) {
      if (!showComments && (line.type === 'comment' || line.type === 'inline_comment')) continue;
      if (isLineCollapsed(line.flow_index)) continue;
      count++;
    }
    return count;
  }, [parsedLines, showComments, isLineCollapsed]);

  // Generate pure text with flow prefixes
  const generatePureText = useCallback(() => {
    const lines: string[] = [];
    const maxFlowLen = Math.max(
      ...parsedLines.map(l => (l.flow_index || '').length),
      6
    );
    
    for (const line of parsedLines) {
      if (!showComments && (line.type === 'comment' || line.type === 'inline_comment')) continue;
      if (isLineCollapsed(line.flow_index)) continue;
      
      const indent = '    '.repeat(line.depth);
      const flowPrefix = (line.flow_index || '').padStart(maxFlowLen);
      
      if (line.type === 'main') {
        const content = line.nc_main || '';
        lines.push(`${flowPrefix} │ ${indent}${content}`);
        
        if (showNaturalLanguage && line.ncn_content) {
          lines.push(`${''.padStart(maxFlowLen)} │ ${indent}    |?{natural language}: ${line.ncn_content}`);
        }
      } else if (line.type === 'comment') {
        const content = line.nc_comment || '';
        lines.push(`${''.padStart(maxFlowLen)} │ ${indent}${content}`);
      }
    }
    
    return lines.join('\n');
  }, [parsedLines, showComments, showNaturalLanguage, isLineCollapsed]);

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Compact Toolbar */}
      <div className="bg-white border-b px-3 py-1.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
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
          <button
            onClick={reloadFile}
            disabled={!selectedFile || isLoading}
            className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-50 text-gray-500"
            title="Reload file"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          
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
            
            <div className="flex-1 overflow-y-auto">
              {isLoading && fileTree.length === 0 ? (
                <div className="p-4 text-center text-gray-500">
                  <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
                  Loading files...
                </div>
              ) : useTreeView ? (
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
                  
                  {/* Editor mode toggle for NormCode files */}
                  {isNormCodeFormat && (
                    <div className="flex items-center bg-white rounded border">
                      <button
                        onClick={() => setEditorMode('line_by_line')}
                        className={`px-2 py-1 text-xs rounded-l ${
                          editorMode === 'line_by_line' 
                            ? 'bg-blue-600 text-white' 
                            : 'text-gray-600 hover:bg-gray-100'
                        }`}
                        title="Line-by-line editing"
                      >
                        Lines
                      </button>
                      <button
                        onClick={() => setEditorMode('pure_text')}
                        className={`px-2 py-1 text-xs rounded-r border-l ${
                          editorMode === 'pure_text' 
                            ? 'bg-blue-600 text-white' 
                            : 'text-gray-600 hover:bg-gray-100'
                        }`}
                        title="Pure text editing"
                      >
                        Text
                      </button>
                    </div>
                  )}
                  
                  {/* View mode toggle */}
                  {!isNormCodeFormat && (
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
                        onClick={() => setEditorViewMode('preview')}
                        className={`px-2 py-1 text-xs rounded-r border-l ${
                          editorViewMode === 'preview' 
                            ? 'bg-blue-600 text-white' 
                            : 'text-gray-600 hover:bg-gray-100'
                        }`}
                      >
                        Preview
                      </button>
                    </div>
                  )}
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
              
              {/* Filter controls for NormCode files */}
              {isNormCodeFormat && parsedLines.length > 0 && (
                <div className="bg-gray-50 border-b px-4 py-2 flex items-center gap-4">
                  {/* Stats */}
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <span>{parsedLines.length} lines</span>
                    <span>•</span>
                    <span>{getVisibleLinesCount()} visible</span>
                  </div>
                  
                  <div className="flex-1" />
                  
                  {/* Filter toggles */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setShowComments(!showComments)}
                      className={`flex items-center gap-1 px-2 py-1 text-xs rounded border ${
                        showComments 
                          ? 'bg-white border-gray-300' 
                          : 'bg-gray-200 border-gray-400 text-gray-500'
                      }`}
                      title={showComments ? 'Hide comments' : 'Show comments'}
                    >
                      <MessageSquare className="w-3 h-3" />
                      Comments
                    </button>
                    
                    <button
                      onClick={() => setShowNaturalLanguage(!showNaturalLanguage)}
                      className={`flex items-center gap-1 px-2 py-1 text-xs rounded border ${
                        showNaturalLanguage 
                          ? 'bg-white border-gray-300' 
                          : 'bg-gray-200 border-gray-400 text-gray-500'
                      }`}
                      title={showNaturalLanguage ? 'Hide NCN annotations' : 'Show NCN annotations'}
                    >
                      <Eye className="w-3 h-3" />
                      NCN
                    </button>
                    
                    {collapsedIndices.size > 0 && (
                      <button
                        onClick={() => setCollapsedIndices(new Set())}
                        className="flex items-center gap-1 px-2 py-1 text-xs rounded border bg-yellow-50 border-yellow-300 text-yellow-700"
                        title="Expand all collapsed sections"
                      >
                        <RotateCw className="w-3 h-3" />
                        {collapsedIndices.size} collapsed
                      </button>
                    )}
                  </div>
                  
                  {/* Default view mode */}
                  {editorMode === 'line_by_line' && (
                    <div className="flex items-center gap-1 ml-2">
                      <span className="text-xs text-gray-500">Default:</span>
                      <button
                        onClick={() => setDefaultViewMode(defaultViewMode === 'ncd' ? 'ncn' : 'ncd')}
                        className={`px-2 py-0.5 text-xs rounded ${
                          defaultViewMode === 'ncd'
                            ? 'bg-blue-100 text-blue-700'
                            : 'bg-green-100 text-green-700'
                        }`}
                      >
                        {defaultViewMode.toUpperCase()}
                      </button>
                    </div>
                  )}
                </div>
              )}
              
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
                </div>
              )}
              
              {/* Editor content area */}
              <div className="flex-1 min-h-0 overflow-hidden">
                {isNormCodeFormat && parsedLines.length > 0 ? (
                  editorMode === 'line_by_line' ? (
                    /* Line-by-line editor */
                    <div className="h-full overflow-auto bg-white">
                      {/* Add line at top button */}
                      <div className="sticky top-0 bg-gray-50 border-b px-3 py-1">
                        <button
                          onClick={() => addLineAfter(-1)}
                          className="flex items-center gap-1 px-2 py-1 text-xs rounded border hover:bg-white text-gray-600"
                        >
                          <Plus className="w-3 h-3" />
                          Add line at top
                        </button>
                      </div>
                      
                      <table className="w-full text-sm font-mono">
                        <thead className="bg-gray-50 sticky top-8">
                          <tr className="text-left text-xs text-gray-500">
                            <th className="px-2 py-2 w-20 border-b">Flow</th>
                            <th className="px-2 py-2 w-12 border-b">Type</th>
                            <th className="px-2 py-2 w-16 border-b">Actions</th>
                            <th className="px-2 py-2 border-b">Content</th>
                          </tr>
                        </thead>
                        <tbody>
                          {parsedLines.map((line, idx) => {
                            // Apply filters
                            if (!showComments && (line.type === 'comment' || line.type === 'inline_comment')) {
                              return null;
                            }
                            if (isLineCollapsed(line.flow_index)) {
                              return null;
                            }
                            
                            const lineViewMode = lineViewModes[idx] || defaultViewMode;
                            const lineHasChildren = hasChildren(line.flow_index);
                            const isCollapsed = line.flow_index ? collapsedIndices.has(line.flow_index) : false;
                            
                            return (
                              <tr key={idx} className="hover:bg-gray-50 border-b border-gray-100 group">
                                {/* Flow index */}
                                <td className="px-2 py-1">
                                  <input
                                    type="text"
                                    value={line.flow_index || ''}
                                    onChange={(e) => updateLine(idx, 'flow_index', e.target.value)}
                                    className="w-full px-1 py-0.5 text-xs text-blue-600 font-medium bg-transparent border border-transparent hover:border-gray-300 focus:border-blue-500 focus:outline-none rounded"
                                  />
                                </td>
                                
                                {/* Type indicator */}
                                <td className="px-2 py-1">
                                  <div className="flex items-center gap-1">
                                    {typeIcons[line.type]?.icon}
                                    <span className="text-[10px] text-gray-400">
                                      {line.type === 'main' ? '' : line.type.charAt(0).toUpperCase()}
                                    </span>
                                  </div>
                                </td>
                                
                                {/* Actions */}
                                <td className="px-2 py-1">
                                  <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                                    {line.type === 'main' && (
                                      <button
                                        onClick={() => toggleLineViewMode(idx)}
                                        className={`p-0.5 rounded text-[10px] ${
                                          lineViewMode === 'ncd' 
                                            ? 'bg-blue-100 text-blue-600' 
                                            : 'bg-green-100 text-green-600'
                                        }`}
                                        title={`Switch to ${lineViewMode === 'ncd' ? 'NCN' : 'NCD'}`}
                                      >
                                        {lineViewMode.toUpperCase()}
                                      </button>
                                    )}
                                    {lineHasChildren && (
                                      <button
                                        onClick={() => line.flow_index && toggleCollapse(line.flow_index)}
                                        className="p-0.5 rounded hover:bg-gray-200"
                                        title={isCollapsed ? 'Expand' : 'Collapse'}
                                      >
                                        {isCollapsed ? (
                                          <Plus className="w-3 h-3 text-gray-500" />
                                        ) : (
                                          <Minus className="w-3 h-3 text-gray-500" />
                                        )}
                                      </button>
                                    )}
                                    <button
                                      onClick={() => addLineAfter(idx)}
                                      className="p-0.5 rounded hover:bg-gray-200"
                                      title="Add line after"
                                    >
                                      <Plus className="w-3 h-3 text-green-600" />
                                    </button>
                                    {deleteConfirmations.has(idx) ? (
                                      <button
                                        onClick={() => deleteLine(idx)}
                                        className="p-0.5 rounded bg-red-100 text-red-600"
                                        title="Click again to confirm delete"
                                      >
                                        <AlertCircle className="w-3 h-3" />
                                      </button>
                                    ) : (
                                      <button
                                        onClick={() => setDeleteConfirmations(prev => new Set(prev).add(idx))}
                                        className="p-0.5 rounded hover:bg-red-100"
                                        title="Delete line"
                                      >
                                        <Trash2 className="w-3 h-3 text-red-500" />
                                      </button>
                                    )}
                                  </div>
                                </td>
                                
                                {/* Content */}
                                <td className="px-2 py-1" style={{ paddingLeft: `${8 + line.depth * 16}px` }}>
                                  {line.type === 'main' ? (
                                    lineViewMode === 'ncd' ? (
                                      <div className="space-y-1">
                                        <input
                                          type="text"
                                          value={line.nc_main || ''}
                                          onChange={(e) => updateLine(idx, 'nc_main', e.target.value)}
                                          className="w-full px-2 py-1 text-xs bg-transparent border border-transparent hover:border-gray-300 focus:border-blue-500 focus:outline-none rounded"
                                          placeholder="(empty)"
                                        />
                                        {showNaturalLanguage && line.ncn_content && (
                                          <div className="text-[10px] text-green-600 pl-4 italic">
                                            → {line.ncn_content}
                                          </div>
                                        )}
                                      </div>
                                    ) : (
                                      <input
                                        type="text"
                                        value={line.ncn_content || ''}
                                        onChange={(e) => updateLine(idx, 'ncn_content', e.target.value)}
                                        className="w-full px-2 py-1 text-xs text-green-700 bg-green-50 border border-transparent hover:border-green-300 focus:border-green-500 focus:outline-none rounded"
                                        placeholder="(no natural language)"
                                      />
                                    )
                                  ) : (
                                    <input
                                      type="text"
                                      value={line.nc_comment || ''}
                                      onChange={(e) => updateLine(idx, 'nc_comment', e.target.value)}
                                      className="w-full px-2 py-1 text-xs text-gray-500 bg-gray-50 border border-transparent hover:border-gray-300 focus:border-gray-400 focus:outline-none rounded italic"
                                      placeholder="(comment)"
                                    />
                                  )}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    /* Pure text editor */
                    <div className="h-full flex flex-col">
                      <textarea
                        key={textEditorKey}
                        value={pendingText ?? generatePureText()}
                        onChange={(e) => setPendingText(e.target.value)}
                        onKeyDown={handleTextAreaKeyDown}
                        className="flex-1 p-4 font-mono text-sm resize-none focus:outline-none"
                        style={{ tabSize: 4, lineHeight: '1.6' }}
                        spellCheck={false}
                      />
                      <div className="bg-gray-50 border-t px-4 py-2 flex items-center gap-4">
                        <button
                          onClick={() => {
                            setPendingText(null);
                            setTextEditorKey(prev => prev + 1);
                          }}
                          className="px-3 py-1 text-xs rounded border hover:bg-white"
                        >
                          Refresh
                        </button>
                        <button
                          onClick={async () => {
                            if (pendingText) {
                              // Re-parse the text
                              try {
                                const result = await editorApi.parseContent(pendingText, 'ncdn');
                                setParsedLines(result.lines);
                                setPendingText(null);
                                setTextEditorKey(prev => prev + 1);
                                setIsModified(true);
                              } catch (e) {
                                setError('Failed to parse text: ' + (e instanceof Error ? e.message : 'Unknown error'));
                              }
                            }
                          }}
                          disabled={!pendingText}
                          className={`px-3 py-1 text-xs rounded ${
                            pendingText 
                              ? 'bg-blue-600 text-white hover:bg-blue-700' 
                              : 'bg-gray-200 text-gray-400'
                          }`}
                        >
                          Apply Changes
                        </button>
                        <span className="text-xs text-gray-500">
                          Flow indices shown as reference. Edit freely, then Apply to update.
                        </span>
                      </div>
                    </div>
                  )
                ) : editorViewMode === 'raw' ? (
                  /* Raw text editor */
                  <textarea
                    value={fileContent}
                    onChange={(e) => setFileContent(e.target.value)}
                    onKeyDown={handleTextAreaKeyDown}
                    className="w-full h-full p-4 font-mono text-sm resize-none focus:outline-none"
                    style={{ tabSize: 4, lineHeight: '1.5' }}
                    spellCheck={false}
                    placeholder="File content will appear here..."
                  />
                ) : (
                  /* Preview tabs for different formats */
                  <div className="h-full flex flex-col">
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
                  {parsedLines.length > 0 ? (
                    <>
                      Parsed: {parsedLines.length} lines | 
                      Main: {parsedLines.filter(l => l.type === 'main').length} | 
                      Comments: {parsedLines.filter(l => l.type === 'comment' || l.type === 'inline_comment').length}
                    </>
                  ) : (
                    <>Lines: {fileContent.split('\n').length} | Characters: {fileContent.length}</>
                  )}
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

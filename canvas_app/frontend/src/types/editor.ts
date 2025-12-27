/**
 * Type definitions for the editor system.
 */

// =============================================================================
// File Types
// =============================================================================

export interface FileInfo {
  name: string;
  path: string;
  format: string;
  size: number;
  modified: number;
  is_dir?: boolean;
}

export interface TreeNode {
  name: string;
  path: string;
  type: 'file' | 'folder';
  format?: string;
  size?: number;
  modified?: number;
  children?: TreeNode[];
}

export interface FileContent {
  path: string;
  content: string;
  format: string;
}

// =============================================================================
// Validation
// =============================================================================

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  format: string;
}

// =============================================================================
// Parsed Content (NormCode)
// =============================================================================

export interface ParsedLine {
  flow_index: string | null;
  type: 'main' | 'comment' | 'inline_comment';
  depth: number;
  nc_main?: string;
  nc_comment?: string;
  ncn_content?: string;
  // Concept type info
  inference_marker?: string;  // '<-', '<=', '<*', ':<:', ':>:'
  concept_type?: string;      // 'object', 'proposition', 'relation', 'subject', 'imperative', 'judgement', 'operator', 'informal'
  operator_type?: string;     // For operators: 'assigning', 'grouping', 'timing', 'looping'
  concept_name?: string;      // Extracted concept name
  warnings?: string[];        // Potential issues detected
}

export interface ParseResponse {
  lines: ParsedLine[];
  parser_available: boolean;
}

export interface PreviewResponse {
  parser_available: boolean;
  previews: {
    ncd?: string;
    ncn?: string;
    ncdn?: string;
    json?: string;
    nci?: string;
  };
}

export interface SerializeResponse {
  success: boolean;
  content: string;
}

// =============================================================================
// Editor Modes
// =============================================================================

export type EditorMode = 'line_by_line' | 'pure_text';
export type ViewMode = 'ncd' | 'ncn';
export type EditorViewMode = 'raw' | 'parsed' | 'preview';

// =============================================================================
// Editor State
// =============================================================================

export interface EditorState {
  // File browser
  directoryPath: string;
  files: FileInfo[];
  fileTree: TreeNode[];
  totalFiles: number;
  expandedFolders: Set<string>;
  selectedFile: string | null;
  showFileBrowser: boolean;
  searchQuery: string;
  useTreeView: boolean;
  
  // File content
  fileContent: string;
  originalContent: string;
  fileFormat: string;
  isModified: boolean;
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;
  successMessage: string | null;
  validation: ValidationResult | null;
  
  // Parsed content
  parsedLines: ParsedLine[];
  parserAvailable: boolean;
  isParsing: boolean;
  
  // Editor mode
  editorMode: EditorMode;
  editorViewMode: EditorViewMode;
  defaultViewMode: ViewMode;
  lineViewModes: Record<number, ViewMode>;
  
  // Filters
  showComments: boolean;
  showNaturalLanguage: boolean;
  collapsedIndices: Set<string>;
  
  // Delete confirmations
  deleteConfirmations: Set<number>;
  
  // Previews
  previews: PreviewResponse['previews'];
  previewTab: string;
  
  // Text editor
  textEditorKey: number;
  pendingText: string | null;
}

// =============================================================================
// Editor Actions
// =============================================================================

export interface EditorActions {
  // File browser
  setDirectoryPath: (path: string) => void;
  loadFiles: (dir?: string) => Promise<void>;
  loadFile: (path: string) => Promise<void>;
  toggleFolder: (path: string) => void;
  setSearchQuery: (query: string) => void;
  setUseTreeView: (use: boolean) => void;
  setShowFileBrowser: (show: boolean) => void;
  
  // File operations
  saveFile: () => Promise<void>;
  reloadFile: () => Promise<void>;
  parseContent: () => Promise<void>;
  validateFile: () => Promise<void>;
  
  // Editor mode
  setEditorMode: (mode: EditorMode) => void;
  setEditorViewMode: (mode: EditorViewMode) => void;
  setDefaultViewMode: (mode: ViewMode) => void;
  toggleLineViewMode: (lineIndex: number) => void;
  
  // Line operations
  updateLine: (lineIndex: number, field: string, value: string) => void;
  addLineAfter: (afterIndex: number, lineType?: 'main' | 'comment') => void;
  deleteLine: (lineIndex: number) => void;
  
  // Filters
  setShowComments: (show: boolean) => void;
  setShowNaturalLanguage: (show: boolean) => void;
  toggleCollapse: (flowIndex: string) => void;
  
  // Messages
  setError: (error: string | null) => void;
  setSuccessMessage: (message: string | null) => void;
}


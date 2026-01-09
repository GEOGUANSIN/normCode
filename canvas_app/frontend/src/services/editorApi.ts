/**
 * Editor API service.
 * 
 * Provides functions for interacting with the editor backend endpoints.
 */

import type {
  FileInfo,
  TreeNode,
  FileContent,
  ValidationResult,
  ParseResponse,
  PreviewResponse,
  SerializeResponse,
  ParsedLine,
} from '../types/editor';
import type { ParsedParadigm } from '../types/paradigm';

// =============================================================================
// API Functions
// =============================================================================

export const editorApi = {
  /**
   * Read a file's content.
   */
  async readFile(path: string): Promise<FileContent> {
    const response = await fetch(`/api/editor/file?path=${encodeURIComponent(path)}`);
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to read file');
    }
    return response.json();
  },

  /**
   * Save a file's content.
   */
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

  /**
   * List files in a directory.
   */
  async listFiles(directory: string, recursive: boolean = false): Promise<{ files: FileInfo[] }> {
    const endpoint = recursive ? '/api/editor/list-recursive' : '/api/editor/list';
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        directory,
        // Extensions are now handled by backend config
        extensions: null,
      }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to list files');
    }
    return response.json();
  },

  /**
   * List files as a tree structure.
   */
  async listFilesTree(directory: string): Promise<{ tree: TreeNode[]; total_files: number }> {
    const response = await fetch('/api/editor/list-tree', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        directory,
        // Extensions are now handled by backend config
        extensions: null,
      }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to list files');
    }
    return response.json();
  },

  /**
   * Validate a file.
   */
  async validateFile(path: string): Promise<ValidationResult> {
    const response = await fetch(`/api/editor/validate?path=${encodeURIComponent(path)}`);
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to validate file');
    }
    return response.json();
  },

  /**
   * Parse content into structured lines.
   */
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

  /**
   * Get content previews in all formats.
   */
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

  /**
   * Serialize parsed lines to a specific format.
   */
  async serializeLines(lines: ParsedLine[], format: string): Promise<SerializeResponse> {
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

  /**
   * Check if the parser is available.
   */
  async getParserStatus(): Promise<{ available: boolean; message: string }> {
    const response = await fetch('/api/editor/parser-status');
    if (!response.ok) {
      return { available: false, message: 'Failed to check parser status' };
    }
    return response.json();
  },

  // =========================================================================
  // Paradigm API Methods
  // =========================================================================

  /**
   * Parse paradigm JSON content into structured format.
   */
  async parseParadigm(content: string): Promise<{
    success: boolean;
    lines: Array<Record<string, unknown>>;
    metadata: Record<string, unknown>;
    errors: string[];
    warnings: string[];
  }> {
    const response = await fetch('/api/editor/paradigm/parse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to parse paradigm');
    }
    return response.json();
  },

  /**
   * Serialize paradigm data back to JSON.
   */
  async serializeParadigm(
    lines: Array<Record<string, unknown>>,
    metadata: Record<string, unknown>
  ): Promise<{
    success: boolean;
    content: string;
    errors: string[];
  }> {
    const response = await fetch('/api/editor/paradigm/serialize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lines, metadata }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to serialize paradigm');
    }
    return response.json();
  },

  /**
   * Validate paradigm JSON content.
   */
  async validateParadigm(content: string): Promise<{
    valid: boolean;
    errors: string[];
    warnings: string[];
    format: string;
  }> {
    const response = await fetch('/api/editor/paradigm/validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to validate paradigm');
    }
    return response.json();
  },

  /**
   * Check if content looks like a paradigm file.
   */
  isParadigmContent(content: string): boolean {
    try {
      const data = JSON.parse(content);
      const requiredKeys = ['metadata', 'env_spec', 'sequence_spec'];
      return requiredKeys.every(key => key in data);
    } catch {
      return false;
    }
  },

  /**
   * Check if a filename matches paradigm naming pattern.
   */
  isParadigmFilename(filename: string): boolean {
    const basename = filename.split(/[/\\]/).pop() || '';
    return /^[hv]_.*-c_.*-o_.*\.json$/.test(basename);
  },
};

export default editorApi;


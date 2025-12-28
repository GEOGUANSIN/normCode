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

import { useState, useEffect, useCallback, useRef, KeyboardEvent } from 'react';
import {
  FileText,
  FolderOpen,
  Save,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  X,
  Loader2,
  Eye,
  RotateCw,
  MessageSquare,
} from 'lucide-react';
import { useProjectStore } from '../../stores/projectStore';

// Types
import type {
  FileInfo,
  TreeNode,
  ValidationResult,
  ParsedLine,
  PreviewResponse,
  EditorMode,
  ViewMode,
  EditorViewMode,
} from '../../types/editor';

// API
import { editorApi } from '../../services/editorApi';

// Config
import { isNormCodeFormat as checkNormCodeFormat } from '../../config/fileTypes';

// Components
import { FileBrowser, NormCodeLineEditor, ExportPanel, ParadigmEditor, RepoPreview, ProjectPreview, AgentConfigPreview } from '../editor';

// Paradigm types
import type { Paradigm, ParsedParadigm } from '../../types/paradigm';

// =============================================================================
// EditorPanel Component
// =============================================================================

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
  
  // Preview state
  const [previews, setPreviews] = useState<PreviewResponse['previews']>({});
  const [previewTab, setPreviewTab] = useState<string>('ncd');
  
  // Text editor state
  const [textEditorKey, setTextEditorKey] = useState(0);
  const [pendingText, setPendingText] = useState<string | null>(null);
  
  // Paradigm editor state
  const [isParadigmFile, setIsParadigmFile] = useState(false);
  const [paradigm, setParadigm] = useState<Paradigm | null>(null);
  const [parsedParadigm, setParsedParadigm] = useState<ParsedParadigm | null>(null);
  
  // Repository preview state
  const [isRepoFile, setIsRepoFile] = useState(false);
  
  // Project config preview state
  const [isProjectFile, setIsProjectFile] = useState(false);
  
  // Agent config preview state
  const [isAgentFile, setIsAgentFile] = useState(false);
  
  const initialLoadDone = useRef(false);
  
  // Helper to detect if a file is a concept/inference repository
  const isRepoFilename = (path: string): boolean => {
    const filename = path.split(/[/\\]/).pop()?.toLowerCase() || '';
    // Match patterns like: *.concept.json, *.inference.json, concept_repo.json, etc.
    return (
      filename.endsWith('.concept.json') ||
      filename.endsWith('.inference.json') ||
      (filename.includes('concept') && filename.endsWith('.json')) ||
      (filename.includes('inference') && filename.endsWith('.json'))
    );
  };
  
  // Helper to detect if a file is a project config file
  const isProjectFilename = (path: string): boolean => {
    const filename = path.split(/[/\\]/).pop()?.toLowerCase() || '';
    return filename.endsWith('.normcode-canvas.json');
  };
  
  // Helper to detect if a file is an agent config file
  const isAgentFilename = (path: string): boolean => {
    const filename = path.split(/[/\\]/).pop()?.toLowerCase() || '';
    return filename.endsWith('.agent.json');
  };

  // Check if current file is NormCode format
  const isNormCodeFormat = checkNormCodeFormat(fileFormat);

  // ==========================================================================
  // Message handling
  // ==========================================================================
  
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

  // ==========================================================================
  // File browser operations
  // ==========================================================================

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

  // ==========================================================================
  // File operations
  // ==========================================================================

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
      
      // Reset paradigm, repo, project, and agent state
      setIsParadigmFile(false);
      setParadigm(null);
      setParsedParadigm(null);
      setIsRepoFile(false);
      setIsProjectFile(false);
      setIsAgentFile(false);
      
      // Check if this is a project config file (.normcode-canvas.json)
      if (isProjectFilename(path)) {
        setIsProjectFile(true);
        setIsLoading(false);
        return;
      }
      
      // Check if this is an agent config file (.agent.json)
      if (isAgentFilename(path)) {
        setIsAgentFile(true);
        setIsLoading(false);
        return;
      }
      
      // Check if this is a repository file (concept/inference JSON)
      // The API returns format 'concept' or 'inference' for these files
      if (result.format === 'concept' || result.format === 'inference' || 
          (isRepoFilename(path) && result.format === 'json')) {
        setIsRepoFile(true);
        // Don't parse further - RepoPreview will handle loading
        setIsLoading(false);
        return;
      }
      
      // Check if this is a paradigm file
      const isParadigm = editorApi.isParadigmFilename(path) || editorApi.isParadigmContent(result.content);
      
      if (isParadigm && result.format === 'json') {
        setIsParadigmFile(true);
        
        try {
          // Parse as paradigm
          const paradigmData = JSON.parse(result.content) as Paradigm;
          setParadigm(paradigmData);
          
          // Get parsed structure for editor
          const parseResult = await editorApi.parseParadigm(result.content);
          if (parseResult.success) {
            // Build parsed paradigm structure from metadata
            const meta = parseResult.metadata as {
              description?: string;
              inputs?: Array<{ name: string; description: string; type: 'vertical' | 'horizontal' }>;
              output_type?: string;
              output_description?: string;
              tools?: Array<{
                index: number;
                tool_name: string;
                affordances: Array<{
                  index: number;
                  tool_name: string;
                  affordance_name: string;
                  call_code: string;
                  full_id: string;
                }>;
              }>;
              all_affordances?: Array<{
                index: number;
                tool_name: string;
                affordance_name: string;
                call_code: string;
                full_id: string;
              }>;
              steps?: Array<{
                index: number;
                step_index: number;
                affordance: string;
                tool_name: string;
                affordance_name: string;
                params: Record<string, unknown>;
                result_key: string;
                has_composition_plan: boolean;
                composition_steps: Array<{
                  index: number;
                  output_key: string;
                  function_ref: string;
                  params: Array<{ name: string; value: string; is_literal: boolean }>;
                }>;
              }>;
              composition_step_index?: number | null;
            };
            
            setParsedParadigm({
              description: meta.description || '',
              inputs: meta.inputs || [],
              output_type: meta.output_type || '',
              output_description: meta.output_description || '',
              tools: meta.tools || [],
              all_affordances: meta.all_affordances || [],
              steps: meta.steps || [],
              composition_step_index: meta.composition_step_index ?? null,
              errors: parseResult.errors,
              warnings: parseResult.warnings,
            });
          }
        } catch (e) {
          console.error('Failed to parse paradigm:', e);
          setIsParadigmFile(false);
        }
      } else if (['ncd', 'ncn', 'ncdn', 'ncds'].includes(result.format)) {
        // Auto-parse for NormCode files
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

  const reloadFile = useCallback(async () => {
    if (!selectedFile) return;
    
    if (isModified) {
      const confirm = window.confirm('You have unsaved changes. Discard them and reload?');
      if (!confirm) return;
    }
    
    await loadFile(selectedFile);
  }, [selectedFile, isModified, loadFile]);

  const validateFile = useCallback(async () => {
    if (!selectedFile) return;
    
    try {
      const result = await editorApi.validateFile(selectedFile);
      setValidation(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to validate file');
    }
  }, [selectedFile]);

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

  // ==========================================================================
  // Line operations
  // ==========================================================================

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
    setIsModified(true);
  }, []);

  const toggleLineViewMode = useCallback((lineIndex: number) => {
    setLineViewModes(prev => ({
      ...prev,
      [lineIndex]: prev[lineIndex] === 'ncn' ? 'ncd' : 'ncn'
    }));
  }, []);

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

  // ==========================================================================
  // Paradigm operations
  // ==========================================================================

  const handleParadigmUpdate = useCallback((updatedParadigm: Paradigm) => {
    setParadigm(updatedParadigm);
    setFileContent(JSON.stringify(updatedParadigm, null, 2));
    setIsModified(true);
  }, []);

  const handleParsedParadigmUpdate = useCallback((updatedParsed: ParsedParadigm) => {
    setParsedParadigm(updatedParsed);
    setIsModified(true);
    
    // Reconstruct paradigm from parsed data
    if (paradigm) {
      const newParadigm: Paradigm = {
        metadata: {
          description: updatedParsed.description,
          inputs: {
            vertical: Object.fromEntries(
              updatedParsed.inputs
                .filter(i => i.type === 'vertical')
                .map(i => [i.name, i.description])
            ),
            horizontal: Object.fromEntries(
              updatedParsed.inputs
                .filter(i => i.type === 'horizontal')
                .map(i => [i.name, i.description])
            ),
          },
          outputs: {
            type: updatedParsed.output_type,
            description: updatedParsed.output_description,
          },
        },
        env_spec: {
          tools: updatedParsed.tools.map(t => ({
            tool_name: t.tool_name,
            affordances: t.affordances.map(a => ({
              affordance_name: a.affordance_name,
              call_code: a.call_code,
            })),
          })),
        },
        sequence_spec: {
          steps: updatedParsed.steps.map(s => {
            const step: Record<string, unknown> = {
              step_index: s.step_index,
              affordance: s.affordance,
              params: { ...s.params },
              result_key: s.result_key,
            };
            
            // Rebuild composition plan if present
            if (s.has_composition_plan && s.composition_steps.length > 0) {
              const plan = s.composition_steps.map(cs => {
                const planStep: Record<string, unknown> = {
                  output_key: cs.output_key,
                  function: { __type__: 'MetaValue', key: cs.function_ref },
                  params: {},
                };
                
                const literalParams: Record<string, unknown> = {};
                
                for (const param of cs.params) {
                  if (param.is_literal) {
                    try {
                      literalParams[param.name] = JSON.parse(param.value);
                    } catch {
                      literalParams[param.name] = param.value;
                    }
                  } else {
                    (planStep.params as Record<string, string>)[param.name] = param.value;
                  }
                }
                
                if (Object.keys(literalParams).length > 0) {
                  planStep.literal_params = literalParams;
                }
                
                return planStep;
              });
              
              (step.params as Record<string, unknown>).plan = plan;
              (step.params as Record<string, unknown>).return_key = s.params.return_key || 'result';
            }
            
            return step;
          }),
        },
      };
      
      setParadigm(newParadigm as Paradigm);
      setFileContent(JSON.stringify(newParadigm, null, 2));
    }
  }, [paradigm]);

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

  // ==========================================================================
  // Text editor helpers
  // ==========================================================================

  // Handle Tab key in text areas
  const handleTextAreaKeyDown = useCallback((e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key !== 'Tab') return;
    
    e.preventDefault();
    e.stopPropagation();
    
    const target = e.target as HTMLTextAreaElement;
    const start = target.selectionStart;
    const end = target.selectionEnd;
    const value = target.value;
    
    const SEP = ' │ ';
    
    const beforeSel = value.substring(0, start);
    const lineStart = beforeSel.lastIndexOf('\n') + 1;
    const lineEnd = value.indexOf('\n', end);
    const actualEnd = lineEnd === -1 ? value.length : lineEnd;
    const selectedText = value.substring(lineStart, actualEnd);
    const lines = selectedText.split('\n');
    
    let totalChange = 0;
    let firstLineChange = 0;
    
    if (e.shiftKey) {
      // Unindent
      const newLines = lines.map((line, idx) => {
        let change = 0;
        const sepIdx = line.indexOf(SEP);
        
        if (sepIdx >= 0) {
          const prefix = line.substring(0, sepIdx + SEP.length);
          let content = line.substring(sepIdx + SEP.length);
          
          if (content.startsWith('    ')) { content = content.substring(4); change = 4; }
          else if (content.startsWith('\t')) { content = content.substring(1); change = 1; }
          else if (content.startsWith('   ')) { content = content.substring(3); change = 3; }
          else if (content.startsWith('  ')) { content = content.substring(2); change = 2; }
          else if (content.startsWith(' ')) { content = content.substring(1); change = 1; }
          
          line = prefix + content;
        } else {
          if (line.startsWith('    ')) { line = line.substring(4); change = 4; }
          else if (line.startsWith('\t')) { line = line.substring(1); change = 1; }
          else if (line.startsWith('   ')) { line = line.substring(3); change = 3; }
          else if (line.startsWith('  ')) { line = line.substring(2); change = 2; }
          else if (line.startsWith(' ')) { line = line.substring(1); change = 1; }
        }
        
        if (idx === 0) firstLineChange = change;
        totalChange += change;
        return line;
      });
      
      const newValue = value.substring(0, lineStart) + newLines.join('\n') + value.substring(actualEnd);
      target.value = newValue;
      target.selectionStart = Math.max(lineStart, start - firstLineChange);
      target.selectionEnd = Math.max(target.selectionStart, end - totalChange);
    } else {
      // Indent
      if (start === end) {
        target.value = value.substring(0, start) + '    ' + value.substring(end);
        target.selectionStart = target.selectionEnd = start + 4;
      } else {
        const newLines = lines.map((line) => {
          const sepIdx = line.indexOf(SEP);
          
          if (sepIdx >= 0) {
            const prefix = line.substring(0, sepIdx + SEP.length);
            const content = line.substring(sepIdx + SEP.length);
            return prefix + '    ' + content;
          } else {
            return '    ' + line;
          }
        });
        
        target.value = value.substring(0, lineStart) + newLines.join('\n') + value.substring(actualEnd);
        target.selectionStart = start + 4;
        target.selectionEnd = end + (lines.length * 4);
      }
    }
    
    // Trigger React change
    const event = new Event('input', { bubbles: true });
    target.dispatchEvent(event);
  }, []);

  // Strip flow index prefixes from pure text
  const stripFlowPrefixes = useCallback((text: string): string => {
    const SEP = ' │ ';
    const lines = text.split('\n');
    
    const strippedLines = lines.map(line => {
      const sepIdx = line.indexOf(SEP);
      if (sepIdx >= 0) {
        return line.substring(sepIdx + SEP.length);
      }
      return line;
    });
    
    return strippedLines.join('\n');
  }, []);

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

  // ==========================================================================
  // Keyboard shortcuts
  // ==========================================================================

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

  // ==========================================================================
  // Render
  // ==========================================================================

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
          <FileBrowser
            directoryPath={directoryPath}
            onDirectoryChange={setDirectoryPath}
            onLoadFiles={() => loadFiles()}
            fileTree={fileTree}
            files={files}
            totalFiles={totalFiles}
            expandedFolders={expandedFolders}
            onToggleFolder={toggleFolder}
            selectedFile={selectedFile}
            onSelectFile={loadFile}
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            useTreeView={useTreeView}
            onToggleTreeView={() => setUseTreeView(!useTreeView)}
            isLoading={isLoading}
          />
        )}

        {/* Editor area */}
        <div className="flex-1 flex flex-col min-w-0">
          {selectedFile ? (
            <>
              {/* Editor toolbar */}
              <div className="bg-gray-100 px-4 py-2 flex items-center justify-between border-b">
                <div className="flex items-center gap-3">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded uppercase ${
                    isProjectFile
                      ? 'bg-indigo-100 text-indigo-700'
                      : isAgentFile
                      ? 'bg-violet-100 text-violet-700'
                      : isRepoFile
                      ? 'bg-blue-100 text-blue-700'
                      : isParadigmFile 
                      ? 'bg-purple-100 text-purple-700' 
                      : 'bg-gray-200 text-gray-700'
                  }`}>
                    {isProjectFile ? 'project' : isAgentFile ? 'agent' : isRepoFile ? 'repository' : isParadigmFile ? 'paradigm' : fileFormat}
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
                {/* Project Config Preview (.normcode-canvas.json) */}
                {isProjectFile && selectedFile ? (
                  <ProjectPreview 
                    filePath={selectedFile}
                    onClose={() => setIsProjectFile(false)}
                    onOpenFile={(relPath) => {
                      // Handle relative paths from project config
                      const projectDir = selectedFile.split(/[/\\]/).slice(0, -1).join('/');
                      const fullPath = relPath.startsWith('.') || !relPath.includes(':')
                        ? `${projectDir}/${relPath}`
                        : relPath;
                      loadFile(fullPath);
                    }}
                  />
                ) : isAgentFile && selectedFile ? (
                  /* Agent Config Preview (.agent.json) */
                  <AgentConfigPreview 
                    filePath={selectedFile}
                    onClose={() => setIsAgentFile(false)}
                  />
                ) : isRepoFile && selectedFile ? (
                  /* Repository Preview (concept/inference files) */
                  <RepoPreview 
                    filePath={selectedFile}
                    onClose={() => setIsRepoFile(false)}
                  />
                ) : isParadigmFile && paradigm && parsedParadigm ? (
                  /* Paradigm Editor */
                  <ParadigmEditor
                    paradigm={paradigm}
                    parsed={parsedParadigm}
                    onUpdate={handleParadigmUpdate}
                    onParsedUpdate={handleParsedParadigmUpdate}
                  />
                ) : isNormCodeFormat && parsedLines.length > 0 ? (
                  editorMode === 'line_by_line' ? (
                    /* Line-by-line editor */
                    <NormCodeLineEditor
                      parsedLines={parsedLines}
                      defaultViewMode={defaultViewMode}
                      lineViewModes={lineViewModes}
                      showComments={showComments}
                      showNaturalLanguage={showNaturalLanguage}
                      collapsedIndices={collapsedIndices}
                      onUpdateLine={updateLine}
                      onAddLine={addLineAfter}
                      onDeleteLine={deleteLine}
                      onToggleLineViewMode={toggleLineViewMode}
                      onToggleCollapse={toggleCollapse}
                    />
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
                              const contentOnly = stripFlowPrefixes(pendingText);
                              
                              try {
                                const result = await editorApi.parseContent(contentOnly, 'ncdn');
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
              
              {/* Export Panel - collapsible */}
              {isNormCodeFormat && parsedLines.length > 0 && (
                <ExportPanel 
                  parsedLines={parsedLines}
                  selectedFile={selectedFile}
                  onError={setError}
                  onSuccess={setSuccessMessage}
                />
              )}
              
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

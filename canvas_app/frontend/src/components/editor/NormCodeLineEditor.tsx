/**
 * NormCodeLineEditor - Line-by-line editor for NormCode files.
 */

import { useState, useCallback } from 'react';
import {
  MessageSquare,
  Plus,
  Minus,
  Trash2,
  AlertCircle,
} from 'lucide-react';
import type { ParsedLine, ViewMode } from '../../types/editor';
import { CONCEPT_TYPE_BADGES, INFERENCE_MARKER_BADGES, TYPE_ICONS } from '../../config/fileTypes';

// =============================================================================
// Types
// =============================================================================

interface NormCodeLineEditorProps {
  parsedLines: ParsedLine[];
  defaultViewMode: ViewMode;
  lineViewModes: Record<number, ViewMode>;
  showComments: boolean;
  showNaturalLanguage: boolean;
  collapsedIndices: Set<string>;
  onUpdateLine: (lineIndex: number, field: string, value: string) => void;
  onAddLine: (afterIndex: number, lineType?: 'main' | 'comment') => void;
  onDeleteLine: (lineIndex: number) => void;
  onToggleLineViewMode: (lineIndex: number) => void;
  onToggleCollapse: (flowIndex: string) => void;
}

// =============================================================================
// Helper Functions
// =============================================================================

function isLineCollapsed(flowIndex: string | null, collapsedIndices: Set<string>): boolean {
  if (!flowIndex) return false;
  for (const collapsed of collapsedIndices) {
    if (flowIndex.startsWith(collapsed + '.')) {
      return true;
    }
  }
  return false;
}

function hasChildren(flowIndex: string | null, parsedLines: ParsedLine[]): boolean {
  if (!flowIndex) return false;
  return parsedLines.some(line => 
    line.flow_index && line.flow_index.startsWith(flowIndex + '.') && line.type === 'main'
  );
}

// =============================================================================
// Component
// =============================================================================

export function NormCodeLineEditor({
  parsedLines,
  defaultViewMode,
  lineViewModes,
  showComments,
  showNaturalLanguage,
  collapsedIndices,
  onUpdateLine,
  onAddLine,
  onDeleteLine,
  onToggleLineViewMode,
  onToggleCollapse,
}: NormCodeLineEditorProps) {
  // Delete confirmation state
  const [deleteConfirmations, setDeleteConfirmations] = useState<Set<number>>(new Set());

  const handleDeleteClick = useCallback((idx: number) => {
    if (deleteConfirmations.has(idx)) {
      onDeleteLine(idx);
      setDeleteConfirmations(prev => {
        const next = new Set(prev);
        next.delete(idx);
        return next;
      });
    } else {
      setDeleteConfirmations(prev => new Set(prev).add(idx));
    }
  }, [deleteConfirmations, onDeleteLine]);

  return (
    <div className="h-full overflow-auto bg-white">
      {/* Add line at top button */}
      <div className="sticky top-0 bg-gray-50 border-b px-3 py-1 z-10">
        <button
          onClick={() => onAddLine(-1)}
          className="flex items-center gap-1 px-2 py-1 text-xs rounded border hover:bg-white text-gray-600"
        >
          <Plus className="w-3 h-3" />
          Add line at top
        </button>
      </div>
      
      <table className="w-full text-sm font-mono">
        <thead className="bg-gray-50 sticky top-8 z-10">
          <tr className="text-left text-xs text-gray-500">
            <th className="px-2 py-2 w-20 border-b">Flow</th>
            <th className="px-2 py-2 w-24 border-b">Concept</th>
            <th className="px-2 py-2 w-20 border-b">Actions</th>
            <th className="px-2 py-2 border-b">Content</th>
          </tr>
        </thead>
        <tbody>
          {parsedLines.map((line, idx) => {
            // Apply filters
            if (!showComments && (line.type === 'comment' || line.type === 'inline_comment')) {
              return null;
            }
            if (isLineCollapsed(line.flow_index, collapsedIndices)) {
              return null;
            }
            
            const lineViewMode = lineViewModes[idx] || defaultViewMode;
            const lineHasChildren = hasChildren(line.flow_index, parsedLines);
            const isCollapsed = line.flow_index ? collapsedIndices.has(line.flow_index) : false;
            const conceptBadge = line.concept_type ? CONCEPT_TYPE_BADGES[line.concept_type] : null;
            const markerBadge = line.inference_marker ? INFERENCE_MARKER_BADGES[line.inference_marker] : null;
            
            return (
              <tr key={idx} className="hover:bg-gray-50 border-b border-gray-100 group">
                {/* Flow index */}
                <td className="px-2 py-1">
                  <input
                    type="text"
                    value={line.flow_index || ''}
                    onChange={(e) => onUpdateLine(idx, 'flow_index', e.target.value)}
                    className="w-full px-1 py-0.5 text-xs text-blue-600 font-medium bg-transparent border border-transparent hover:border-gray-300 focus:border-blue-500 focus:outline-none rounded"
                  />
                </td>
                
                {/* Type indicator with concept type badge */}
                <td className="px-2 py-1">
                  <div className="flex items-center gap-1 flex-wrap">
                    {/* Inference marker badge */}
                    {markerBadge && (
                      <span className={`px-1 py-0.5 rounded text-[9px] font-mono ${markerBadge.bg} ${markerBadge.text}`}>
                        {line.inference_marker}
                      </span>
                    )}
                    {/* Concept type badge */}
                    {conceptBadge && (
                      <span 
                        className={`px-1 py-0.5 rounded text-[9px] font-medium ${conceptBadge.bg} ${conceptBadge.text}`}
                        title={`${line.concept_type}${line.operator_type ? ` (${line.operator_type})` : ''}${line.concept_name ? `: ${line.concept_name}` : ''}`}
                      >
                        {conceptBadge.label}
                      </span>
                    )}
                    {/* Warning indicator */}
                    {line.warnings && line.warnings.length > 0 && (
                      <span 
                        className="text-yellow-600" 
                        title={line.warnings.join('\n')}
                      >
                        <AlertCircle className="w-3 h-3" />
                      </span>
                    )}
                    {/* Fallback type icon for non-main lines */}
                    {!line.concept_type && line.type !== 'main' && TYPE_ICONS[line.type] && (
                      <span className={line.type === 'comment' ? 'text-gray-400' : 'text-yellow-500'}>
                        <MessageSquare className="w-3 h-3" />
                      </span>
                    )}
                  </div>
                </td>
                
                {/* Actions */}
                <td className="px-2 py-1">
                  <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                    {line.type === 'main' && (
                      <button
                        onClick={() => onToggleLineViewMode(idx)}
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
                        onClick={() => line.flow_index && onToggleCollapse(line.flow_index)}
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
                      onClick={() => onAddLine(idx)}
                      className="p-0.5 rounded hover:bg-gray-200"
                      title="Add line after"
                    >
                      <Plus className="w-3 h-3 text-green-600" />
                    </button>
                    {deleteConfirmations.has(idx) ? (
                      <button
                        onClick={() => handleDeleteClick(idx)}
                        className="p-0.5 rounded bg-red-100 text-red-600"
                        title="Click again to confirm delete"
                      >
                        <AlertCircle className="w-3 h-3" />
                      </button>
                    ) : (
                      <button
                        onClick={() => handleDeleteClick(idx)}
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
                          onChange={(e) => onUpdateLine(idx, 'nc_main', e.target.value)}
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
                        onChange={(e) => onUpdateLine(idx, 'ncn_content', e.target.value)}
                        className="w-full px-2 py-1 text-xs text-green-700 bg-green-50 border border-transparent hover:border-green-300 focus:border-green-500 focus:outline-none rounded"
                        placeholder="(no natural language)"
                      />
                    )
                  ) : (
                    <input
                      type="text"
                      value={line.nc_comment || ''}
                      onChange={(e) => onUpdateLine(idx, 'nc_comment', e.target.value)}
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
  );
}

export default NormCodeLineEditor;


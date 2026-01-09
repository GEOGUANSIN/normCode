/**
 * RepoPreview - A clean viewer for concept and inference repository JSON files.
 * 
 * Simpler than the full canvas view - just displays the structured data
 * in an easy-to-read format for investigation and debugging.
 */

import { useState, useEffect, useMemo } from 'react';
import { 
  Database, 
  GitBranch, 
  Layers, 
  ChevronDown, 
  ChevronRight, 
  Search,
  FileJson,
  Circle,
  ArrowRight,
  RefreshCw,
  X,
  Filter,
  Hash,
  Tag,
  Workflow,
  Sparkles,
  Box,
  Settings2,
} from 'lucide-react';

// =============================================================================
// Types
// =============================================================================

interface ConceptPreview {
  id: string;
  concept_name: string;
  type: string;
  flow_indices: string[];
  description?: string;
  natural_name?: string;
  is_ground_concept: boolean;
  is_final_concept: boolean;
  is_invariant: boolean;
  reference_data?: unknown;
  reference_axis_names: string[];
}

interface InferencePreview {
  flow_index: string;
  inference_sequence: string;
  concept_to_infer: string;
  function_concept: string;
  value_concepts: string[];
  context_concepts: string[];
  working_interpretation?: Record<string, unknown>;
}

interface RepoPreviewData {
  success: boolean;
  file_path: string;
  file_type: 'concept' | 'inference';
  item_count: number;
  concepts?: ConceptPreview[];
  inferences?: InferencePreview[];
  error?: string;
}

interface RepoPreviewProps {
  filePath: string;
  onClose?: () => void;
}

// =============================================================================
// API
// =============================================================================

async function fetchRepoPreview(filePath: string): Promise<RepoPreviewData> {
  const response = await fetch('/api/repositories/preview', {
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
// Concept Card Component
// =============================================================================

interface ConceptCardProps {
  concept: ConceptPreview;
  isExpanded: boolean;
  onToggle: () => void;
  searchQuery: string;
}

function ConceptCard({ concept, isExpanded, onToggle, searchQuery }: ConceptCardProps) {
  // Type badge colors
  const typeColors: Record<string, string> = {
    '{}': 'bg-blue-100 text-blue-700 border-blue-200',
    '[]': 'bg-purple-100 text-purple-700 border-purple-200',
    '<>': 'bg-amber-100 text-amber-700 border-amber-200',
    '$.': 'bg-emerald-100 text-emerald-700 border-emerald-200',
    '$%': 'bg-teal-100 text-teal-700 border-teal-200',
    '*.': 'bg-rose-100 text-rose-700 border-rose-200',
    '&[{}]': 'bg-indigo-100 text-indigo-700 border-indigo-200',
    '::': 'bg-orange-100 text-orange-700 border-orange-200',
    ':>:': 'bg-cyan-100 text-cyan-700 border-cyan-200',
    '@:!': 'bg-pink-100 text-pink-700 border-pink-200',
    '$+': 'bg-lime-100 text-lime-700 border-lime-200',
    '<{}>': 'bg-fuchsia-100 text-fuchsia-700 border-fuchsia-200',
  };
  
  const typeColor = typeColors[concept.type] || 'bg-slate-100 text-slate-700 border-slate-200';
  
  // Highlight search matches
  const highlightMatch = (text: string) => {
    if (!searchQuery) return text;
    const regex = new RegExp(`(${searchQuery})`, 'gi');
    const parts = text.split(regex);
    return parts.map((part, i) => 
      regex.test(part) ? <mark key={i} className="bg-yellow-200 px-0.5 rounded">{part}</mark> : part
    );
  };

  return (
    <div className="border border-slate-200 rounded-lg bg-white hover:border-slate-300 transition-colors">
      {/* Header - always visible */}
      <button
        onClick={onToggle}
        className="w-full p-3 flex items-start gap-3 text-left hover:bg-slate-50 transition-colors rounded-lg"
      >
        {/* Expand/collapse icon */}
        <div className="mt-0.5 text-slate-400">
          {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        </div>
        
        {/* Type badge */}
        <span className={`px-2 py-0.5 rounded text-xs font-mono border ${typeColor} shrink-0`}>
          {concept.type}
        </span>
        
        {/* Name and description */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-sm text-slate-800 break-all">
              {highlightMatch(concept.concept_name)}
            </span>
            {concept.natural_name && (
              <span className="text-xs text-slate-500 italic truncate max-w-xs">
                ({highlightMatch(concept.natural_name)})
              </span>
            )}
          </div>
          {concept.description && (
            <p className="text-xs text-slate-500 mt-1 line-clamp-1">
              {highlightMatch(concept.description)}
            </p>
          )}
        </div>
        
        {/* Status badges */}
        <div className="flex items-center gap-1 shrink-0">
          {concept.is_ground_concept && (
            <span className="px-1.5 py-0.5 rounded text-[10px] bg-green-100 text-green-700 font-medium">
              Ground
            </span>
          )}
          {concept.is_final_concept && (
            <span className="px-1.5 py-0.5 rounded text-[10px] bg-red-100 text-red-700 font-medium">
              Final
            </span>
          )}
          {concept.is_invariant && (
            <span className="px-1.5 py-0.5 rounded text-[10px] bg-purple-100 text-purple-700 font-medium">
              Invariant
            </span>
          )}
        </div>
      </button>
      
      {/* Expanded details */}
      {isExpanded && (
        <div className="px-4 pb-4 pt-2 border-t border-slate-100 space-y-3">
          {/* ID */}
          <div className="flex items-center gap-2 text-xs">
            <Hash size={12} className="text-slate-400" />
            <span className="text-slate-500">ID:</span>
            <code className="bg-slate-100 px-1.5 py-0.5 rounded text-slate-700">{concept.id}</code>
          </div>
          
          {/* Flow Indices */}
          <div className="flex items-start gap-2 text-xs">
            <Workflow size={12} className="text-slate-400 mt-0.5" />
            <span className="text-slate-500">Flows:</span>
            <div className="flex flex-wrap gap-1">
              {concept.flow_indices.map((fi, idx) => (
                <code key={idx} className="bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded">
                  {fi}
                </code>
              ))}
            </div>
          </div>
          
          {/* Axes */}
          {concept.reference_axis_names.length > 0 && (
            <div className="flex items-start gap-2 text-xs">
              <Layers size={12} className="text-slate-400 mt-0.5" />
              <span className="text-slate-500">Axes:</span>
              <div className="flex flex-wrap gap-1">
                {concept.reference_axis_names.map((axis, idx) => (
                  <code key={idx} className="bg-purple-50 text-purple-700 px-1.5 py-0.5 rounded">
                    {axis}
                  </code>
                ))}
              </div>
            </div>
          )}
          
          {/* Reference Data */}
          {concept.reference_data !== null && concept.reference_data !== undefined && (
            <div className="text-xs">
              <div className="flex items-center gap-2 mb-1">
                <Database size={12} className="text-slate-400" />
                <span className="text-slate-500">Reference Data:</span>
              </div>
              <pre className="bg-slate-50 p-2 rounded text-[11px] overflow-x-auto max-h-40 text-slate-700">
                {JSON.stringify(concept.reference_data, null, 2)}
              </pre>
            </div>
          )}
          
          {/* Full description */}
          {concept.description && (
            <div className="text-xs">
              <div className="flex items-center gap-2 mb-1">
                <Tag size={12} className="text-slate-400" />
                <span className="text-slate-500">Description:</span>
              </div>
              <p className="text-slate-600 bg-slate-50 p-2 rounded">{concept.description}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Inference Card Component
// =============================================================================

interface InferenceCardProps {
  inference: InferencePreview;
  isExpanded: boolean;
  onToggle: () => void;
  searchQuery: string;
}

function InferenceCard({ inference, isExpanded, onToggle, searchQuery }: InferenceCardProps) {
  // Sequence type colors
  const sequenceColors: Record<string, string> = {
    'assigning': 'bg-blue-100 text-blue-700 border-blue-200',
    'looping': 'bg-purple-100 text-purple-700 border-purple-200',
    'grouping': 'bg-amber-100 text-amber-700 border-amber-200',
    'timing': 'bg-pink-100 text-pink-700 border-pink-200',
    'imperative_in_composition': 'bg-emerald-100 text-emerald-700 border-emerald-200',
    'judgement_in_composition': 'bg-rose-100 text-rose-700 border-rose-200',
  };
  
  const seqColor = sequenceColors[inference.inference_sequence] || 'bg-slate-100 text-slate-700 border-slate-200';
  
  // Highlight search matches
  const highlightMatch = (text: string) => {
    if (!searchQuery) return text;
    const regex = new RegExp(`(${searchQuery})`, 'gi');
    const parts = text.split(regex);
    return parts.map((part, i) => 
      regex.test(part) ? <mark key={i} className="bg-yellow-200 px-0.5 rounded">{part}</mark> : part
    );
  };
  
  // Extract key info from working interpretation
  const wi = inference.working_interpretation || {};
  const paradigm = wi.paradigm as string | undefined;
  const bodyFaculty = wi.body_faculty as string | undefined;
  const promptLocation = wi.v_input_provision as string | undefined;

  return (
    <div className="border border-slate-200 rounded-lg bg-white hover:border-slate-300 transition-colors">
      {/* Header - always visible */}
      <button
        onClick={onToggle}
        className="w-full p-3 flex items-start gap-3 text-left hover:bg-slate-50 transition-colors rounded-lg"
      >
        {/* Expand/collapse icon */}
        <div className="mt-0.5 text-slate-400">
          {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        </div>
        
        {/* Flow index badge */}
        <code className="px-2 py-0.5 rounded text-xs bg-slate-800 text-white font-mono shrink-0">
          {inference.flow_index}
        </code>
        
        {/* Sequence type */}
        <span className={`px-2 py-0.5 rounded text-[10px] font-medium border ${seqColor} shrink-0`}>
          {inference.inference_sequence}
        </span>
        
        {/* Concept to infer */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <ArrowRight size={12} className="text-slate-400 shrink-0" />
            <span className="font-mono text-sm text-slate-800 break-all">
              {highlightMatch(inference.concept_to_infer)}
            </span>
          </div>
          {/* Function concept preview */}
          <p className="text-xs text-slate-500 mt-1 font-mono truncate">
            {highlightMatch(inference.function_concept)}
          </p>
        </div>
        
        {/* Faculty badge if present */}
        {bodyFaculty && (
          <span className="px-1.5 py-0.5 rounded text-[10px] bg-orange-100 text-orange-700 font-medium shrink-0">
            {bodyFaculty}
          </span>
        )}
      </button>
      
      {/* Expanded details */}
      {isExpanded && (
        <div className="px-4 pb-4 pt-2 border-t border-slate-100 space-y-3">
          {/* Function Concept */}
          <div className="text-xs">
            <div className="flex items-center gap-2 mb-1">
              <Settings2 size={12} className="text-slate-400" />
              <span className="text-slate-500">Function:</span>
            </div>
            <code className="block bg-slate-50 p-2 rounded text-slate-700 break-all">
              {inference.function_concept}
            </code>
          </div>
          
          {/* Value Concepts */}
          {inference.value_concepts.length > 0 && (
            <div className="text-xs">
              <div className="flex items-center gap-2 mb-1">
                <Box size={12} className="text-blue-500" />
                <span className="text-slate-500">Value Inputs ({inference.value_concepts.length}):</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {inference.value_concepts.map((vc, idx) => (
                  <code key={idx} className="bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded">
                    {vc}
                  </code>
                ))}
              </div>
            </div>
          )}
          
          {/* Context Concepts */}
          {inference.context_concepts.length > 0 && (
            <div className="text-xs">
              <div className="flex items-center gap-2 mb-1">
                <Circle size={12} className="text-purple-500" />
                <span className="text-slate-500">Context ({inference.context_concepts.length}):</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {inference.context_concepts.map((cc, idx) => (
                  <code key={idx} className="bg-purple-50 text-purple-700 px-1.5 py-0.5 rounded">
                    {cc}
                  </code>
                ))}
              </div>
            </div>
          )}
          
          {/* Paradigm */}
          {paradigm && (
            <div className="flex items-center gap-2 text-xs">
              <Sparkles size={12} className="text-amber-500" />
              <span className="text-slate-500">Paradigm:</span>
              <code className="bg-amber-50 text-amber-700 px-1.5 py-0.5 rounded">
                {paradigm}
              </code>
            </div>
          )}
          
          {/* Prompt Location */}
          {promptLocation && (
            <div className="flex items-center gap-2 text-xs">
              <FileJson size={12} className="text-emerald-500" />
              <span className="text-slate-500">Prompt:</span>
              <code className="bg-emerald-50 text-emerald-700 px-1.5 py-0.5 rounded text-[11px]">
                {promptLocation}
              </code>
            </div>
          )}
          
          {/* Full Working Interpretation */}
          {inference.working_interpretation && Object.keys(inference.working_interpretation).length > 0 && (
            <details className="text-xs">
              <summary className="flex items-center gap-2 cursor-pointer text-slate-500 hover:text-slate-700">
                <Settings2 size={12} />
                <span>Working Interpretation (full)</span>
              </summary>
              <pre className="bg-slate-50 p-2 rounded text-[11px] overflow-x-auto max-h-60 mt-2 text-slate-700">
                {JSON.stringify(inference.working_interpretation, null, 2)}
              </pre>
            </details>
          )}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Main RepoPreview Component
// =============================================================================

export function RepoPreview({ filePath, onClose }: RepoPreviewProps) {
  const [data, setData] = useState<RepoPreviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [sequenceFilter, setSequenceFilter] = useState<string>('all');

  // Load data on mount or path change
  useEffect(() => {
    loadPreview();
  }, [filePath]);

  const loadPreview = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchRepoPreview(filePath);
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load preview');
    } finally {
      setLoading(false);
    }
  };

  // Toggle item expansion
  const toggleItem = (id: string) => {
    setExpandedItems(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  // Expand/collapse all
  const expandAll = () => {
    if (data?.concepts) {
      setExpandedItems(new Set(data.concepts.map(c => c.id)));
    } else if (data?.inferences) {
      setExpandedItems(new Set(data.inferences.map(i => i.flow_index)));
    }
  };

  const collapseAll = () => {
    setExpandedItems(new Set());
  };

  // Get unique types/sequences for filters
  const availableTypes = useMemo(() => {
    if (!data?.concepts) return [];
    return [...new Set(data.concepts.map(c => c.type))].sort();
  }, [data?.concepts]);

  const availableSequences = useMemo(() => {
    if (!data?.inferences) return [];
    return [...new Set(data.inferences.map(i => i.inference_sequence))].sort();
  }, [data?.inferences]);

  // Filter and search
  const filteredConcepts = useMemo(() => {
    if (!data?.concepts) return [];
    
    return data.concepts.filter(concept => {
      // Type filter
      if (typeFilter !== 'all' && concept.type !== typeFilter) return false;
      
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        return (
          concept.concept_name.toLowerCase().includes(query) ||
          concept.id.toLowerCase().includes(query) ||
          concept.natural_name?.toLowerCase().includes(query) ||
          concept.description?.toLowerCase().includes(query) ||
          concept.flow_indices.some(fi => fi.toLowerCase().includes(query))
        );
      }
      
      return true;
    });
  }, [data?.concepts, searchQuery, typeFilter]);

  const filteredInferences = useMemo(() => {
    if (!data?.inferences) return [];
    
    return data.inferences.filter(inference => {
      // Sequence filter
      if (sequenceFilter !== 'all' && inference.inference_sequence !== sequenceFilter) return false;
      
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        return (
          inference.flow_index.toLowerCase().includes(query) ||
          inference.concept_to_infer.toLowerCase().includes(query) ||
          inference.function_concept.toLowerCase().includes(query) ||
          inference.value_concepts.some(vc => vc.toLowerCase().includes(query)) ||
          inference.context_concepts.some(cc => cc.toLowerCase().includes(query))
        );
      }
      
      return true;
    });
  }, [data?.inferences, searchQuery, sequenceFilter]);

  // Loading state
  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-50">
        <div className="flex items-center gap-3 text-slate-500">
          <RefreshCw size={20} className="animate-spin" />
          <span>Loading preview...</span>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-50">
        <div className="text-center p-8">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 flex items-center justify-center">
            <X size={32} className="text-red-500" />
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

  if (!data) return null;

  const isConcepts = data.file_type === 'concept';
  const items = isConcepts ? filteredConcepts : filteredInferences;
  const totalItems = isConcepts ? data.concepts?.length : data.inferences?.length;

  return (
    <div className="h-full flex flex-col bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            {isConcepts ? (
              <Database size={20} className="text-blue-600" />
            ) : (
              <GitBranch size={20} className="text-purple-600" />
            )}
            <div>
              <h2 className="font-semibold text-slate-800">
                {isConcepts ? 'Concept Repository' : 'Inference Repository'}
              </h2>
              <p className="text-xs text-slate-500 font-mono truncate max-w-md" title={data.file_path}>
                {data.file_path.split(/[/\\]/).pop()}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-500">
              {items.length} / {totalItems} items
            </span>
            <button
              onClick={loadPreview}
              className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded transition-colors"
              title="Refresh"
            >
              <RefreshCw size={16} />
            </button>
            {onClose && (
              <button
                onClick={onClose}
                className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded transition-colors"
                title="Close"
              >
                <X size={16} />
              </button>
            )}
          </div>
        </div>
        
        {/* Search and filters */}
        <div className="flex items-center gap-3">
          {/* Search */}
          <div className="relative flex-1">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={isConcepts ? "Search concepts..." : "Search inferences..."}
              className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          {/* Type/Sequence filter */}
          <div className="flex items-center gap-2">
            <Filter size={14} className="text-slate-400" />
            {isConcepts ? (
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Types</option>
                {availableTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            ) : (
              <select
                value={sequenceFilter}
                onChange={(e) => setSequenceFilter(e.target.value)}
                className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Sequences</option>
                {availableSequences.map(seq => (
                  <option key={seq} value={seq}>{seq}</option>
                ))}
              </select>
            )}
          </div>
          
          {/* Expand/collapse buttons */}
          <div className="flex items-center gap-1 border-l border-slate-200 pl-3">
            <button
              onClick={expandAll}
              className="px-2 py-1 text-xs text-slate-600 hover:bg-slate-100 rounded transition-colors"
            >
              Expand All
            </button>
            <button
              onClick={collapseAll}
              className="px-2 py-1 text-xs text-slate-600 hover:bg-slate-100 rounded transition-colors"
            >
              Collapse
            </button>
          </div>
        </div>
      </div>
      
      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {items.length === 0 ? (
          <div className="text-center py-12 text-slate-500">
            <Search size={32} className="mx-auto mb-3 opacity-50" />
            <p>No items match your search</p>
          </div>
        ) : (
          <div className="space-y-2">
            {isConcepts ? (
              filteredConcepts.map(concept => (
                <ConceptCard
                  key={concept.id}
                  concept={concept}
                  isExpanded={expandedItems.has(concept.id)}
                  onToggle={() => toggleItem(concept.id)}
                  searchQuery={searchQuery}
                />
              ))
            ) : (
              filteredInferences.map(inference => (
                <InferenceCard
                  key={inference.flow_index}
                  inference={inference}
                  isExpanded={expandedItems.has(inference.flow_index)}
                  onToggle={() => toggleItem(inference.flow_index)}
                  searchQuery={searchQuery}
                />
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default RepoPreview;


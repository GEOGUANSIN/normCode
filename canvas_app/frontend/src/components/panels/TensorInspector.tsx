/**
 * TensorInspector - Interactive N-D tensor viewer
 * Ported from streamlit_app/tabs/execute/preview/tensor_display.py
 * Enhanced with expandable individual items
 */

import { useState, useMemo } from 'react';
import { Layers, Grid3X3, List, Code, ChevronDown, ChevronUp, ChevronRight, X, Copy, Check, Maximize2 } from 'lucide-react';
import {
  TensorData,
  getTensorShape,
  getShapeString,
  formatCellValue,
  sliceTensor,
  getSliceDescription,
  createInitialSliceState,
  ensureAxisNames,
  detectElementType,
  SliceState,
} from '../../utils/tensorUtils';

interface TensorInspectorProps {
  data: TensorData;
  axes?: string[];
  shape?: number[];  // Backend-provided shape (authoritative)
  conceptName?: string;
  isGround?: boolean;
  isCompact?: boolean;
}

export function TensorInspector({
  data,
  axes: providedAxes,
  shape: providedShape,
  conceptName,
  isGround,
  isCompact = false,
}: TensorInspectorProps) {
  // Use backend-provided shape if available, otherwise compute from data
  // The backend shape is authoritative as it knows the logical tensor structure
  const computedShape = useMemo(() => getTensorShape(data), [data]);
  const shape = providedShape && providedShape.length > 0 ? providedShape : computedShape;
  const dims = shape.length;
  // Use provided axes directly - the backend knows the correct axis count
  const axes = useMemo(() => ensureAxisNames(providedAxes, dims), [providedAxes, dims]);
  const elementType = useMemo(() => detectElementType(data), [data]);
  
  const [sliceState, setSliceState] = useState<SliceState>(() => 
    createInitialSliceState(dims)
  );
  const [isExpanded, setIsExpanded] = useState(!isCompact);

  // Slice the data for display
  const displayData = useMemo(() => {
    if (dims <= 2) return data;
    return sliceTensor(data, sliceState.displayAxes, sliceState.sliceIndices, dims);
  }, [data, dims, sliceState]);

  // Compact header-only view
  if (!isExpanded) {
    return (
      <div className="border border-slate-200 rounded-lg bg-slate-50">
        <button
          onClick={() => setIsExpanded(true)}
          className="w-full px-3 py-2 flex items-center justify-between text-sm hover:bg-slate-100 transition-colors"
        >
          <div className="flex items-center gap-2">
            <Layers size={14} className="text-slate-500" />
            <span className="text-slate-700">
              {dims === 0 ? 'Scalar' : `${getShapeString(shape)} tensor`}
            </span>
            {isGround && (
              <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded">
                Ground
              </span>
            )}
          </div>
          <ChevronDown size={14} className="text-slate-400" />
        </button>
      </div>
    );
  }

  return (
    <div className="border border-slate-200 rounded-lg bg-white overflow-hidden">
      {/* Header */}
      <div className="px-3 py-2 bg-slate-50 border-b border-slate-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers size={14} className="text-slate-500" />
            <span className="text-sm font-medium text-slate-700">
              {conceptName ? `Reference Data` : 'Tensor Data'}
            </span>
            {isGround && (
              <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded">
                Ground
              </span>
            )}
          </div>
          {isCompact && (
            <button
              onClick={() => setIsExpanded(false)}
              className="p-1 hover:bg-slate-200 rounded transition-colors"
            >
              <ChevronUp size={14} className="text-slate-400" />
            </button>
          )}
        </div>
        
        {/* Shape info */}
        <div className="mt-1 flex flex-wrap gap-2 text-xs text-slate-500">
          <span className="bg-white px-2 py-0.5 rounded border border-slate-200">
            Shape: {getShapeString(shape)}
          </span>
          <span className="bg-white px-2 py-0.5 rounded border border-slate-200">
            Type: {elementType}
          </span>
          {dims > 0 && (
            <span className="bg-white px-2 py-0.5 rounded border border-slate-200">
              Axes: [{axes.join(', ')}]
            </span>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-3">
        {dims === 0 && <ScalarView data={data} />}
        {dims === 1 && <OneDView data={data as unknown[]} axisName={axes[0]} />}
        {dims === 2 && <TwoDView data={data as unknown[][]} axes={axes} />}
        {dims > 2 && (
          <NDView
            data={data}
            displayData={displayData}
            shape={shape}
            axes={axes}
            sliceState={sliceState}
            setSliceState={setSliceState}
          />
        )}
      </div>
    </div>
  );
}

// =============================================================================
// SCALAR VIEW
// =============================================================================

function ScalarView({ data }: { data: TensorData }) {
  return (
    <div className="text-center py-4">
      <div className="text-xs text-slate-500 mb-1">Value</div>
      <div className="text-lg font-mono text-slate-800">
        {formatCellValue(data)}
      </div>
    </div>
  );
}

// =============================================================================
// EXPANDABLE ITEM - For complex data items (objects, arrays, long strings)
// =============================================================================

interface ExpandableItemProps {
  index: number;
  axisName: string;
  item: unknown;
  onExpand: (index: number, item: unknown) => void;
}

function ExpandableItem({ index, axisName, item, onExpand }: ExpandableItemProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [copied, setCopied] = useState(false);
  
  const isComplex = typeof item === 'object' && item !== null;
  const formattedValue = formatCellValue(item);
  
  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const textToCopy = isComplex ? JSON.stringify(item, null, 2) : String(item);
      await navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };
  
  // Get the full content for expanded view
  const fullContent = isComplex ? JSON.stringify(item, null, 2) : String(item);
  
  return (
    <div className="border border-slate-200 rounded-lg mb-2 overflow-hidden bg-white hover:border-slate-300 transition-colors">
      {/* Header - clickable to expand */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center gap-2 px-3 py-2.5 hover:bg-slate-50 transition-colors text-left group"
      >
        <span className="text-slate-400 flex-shrink-0">
          {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </span>
        <span className="text-xs text-blue-600 font-mono min-w-[70px] flex-shrink-0">{axisName}[{index}]</span>
        <span className="text-sm font-mono text-slate-700 flex-1 truncate">
          {formattedValue.length > 50 ? formattedValue.substring(0, 47) + '...' : formattedValue}
        </span>
        <div className="flex items-center gap-1 flex-shrink-0">
          <button
            onClick={handleCopy}
            className="p-1.5 hover:bg-slate-200 rounded transition-colors"
            title="Copy to clipboard"
          >
            {copied ? <Check size={12} className="text-green-500" /> : <Copy size={12} className="text-slate-400" />}
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); onExpand(index, item); }}
            className="p-1.5 hover:bg-slate-200 rounded transition-colors"
            title="View fullscreen"
          >
            <Maximize2 size={12} className="text-slate-400" />
          </button>
        </div>
      </button>
      
      {/* Expanded content */}
      {isExpanded && (
        <div className="border-t border-slate-200 bg-slate-50 p-3">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs text-slate-500">
              {isComplex ? (Array.isArray(item) ? 'Array' : 'Object') : typeof item}
              {fullContent.length > 100 && ` • ${fullContent.length} chars`}
            </span>
            <div className="flex gap-1">
              <button
                onClick={handleCopy}
                className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700 px-2 py-1 rounded hover:bg-slate-200 transition-colors"
              >
                {copied ? <Check size={12} className="text-green-500" /> : <Copy size={12} />}
                {copied ? 'Copied!' : 'Copy'}
              </button>
              <button
                onClick={() => onExpand(index, item)}
                className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 px-2 py-1 rounded hover:bg-blue-50 transition-colors"
              >
                <Maximize2 size={12} />
                Fullscreen
              </button>
            </div>
          </div>
          <pre className="text-xs font-mono text-slate-700 whitespace-pre-wrap break-words max-h-64 overflow-auto bg-white p-3 rounded border border-slate-200">
            {fullContent}
          </pre>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// ITEM MODAL - Fullscreen view for a single item
// =============================================================================

interface ItemModalProps {
  index: number;
  axisName: string;
  item: unknown;
  onClose: () => void;
}

function ItemModal({ index, axisName, item, onClose }: ItemModalProps) {
  const [copied, setCopied] = useState(false);
  const isComplex = typeof item === 'object' && item !== null;
  const content = isComplex ? JSON.stringify(item, null, 2) : String(item);
  
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };
  
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50" onClick={onClose}>
      <div 
        className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] flex flex-col m-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-slate-50 rounded-t-lg">
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm text-slate-600">{axisName}[{index}]</span>
            <span className="text-xs bg-slate-200 text-slate-600 px-2 py-0.5 rounded">
              {isComplex ? (Array.isArray(item) ? 'Array' : 'Object') : typeof item}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 text-sm text-slate-600 hover:text-slate-800 px-3 py-1.5 rounded hover:bg-slate-200 transition-colors"
            >
              {copied ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
              {copied ? 'Copied!' : 'Copy'}
            </button>
            <button
              onClick={onClose}
              className="p-1.5 hover:bg-slate-200 rounded transition-colors text-slate-500"
            >
              <X size={18} />
            </button>
          </div>
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-auto p-4">
          <pre className="text-sm font-mono text-slate-700 whitespace-pre-wrap break-words">
            {content}
          </pre>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// 1D VIEW - Always uses expandable items for better inspection
// =============================================================================

function OneDView({ data, axisName }: { data: unknown[]; axisName: string }) {
  const [modalItem, setModalItem] = useState<{ index: number; item: unknown } | null>(null);
  
  const handleExpand = (index: number, item: unknown) => {
    setModalItem({ index, item });
  };
  
  // Always use expandable items layout for better inspection capability
  return (
    <>
      <div className="max-h-[400px] overflow-y-auto space-y-1">
        {data.map((item, i) => (
          <ExpandableItem
            key={i}
            index={i}
            axisName={axisName}
            item={item}
            onExpand={handleExpand}
          />
        ))}
      </div>
      
      {/* Modal for fullscreen view */}
      {modalItem && (
        <ItemModal
          index={modalItem.index}
          axisName={axisName}
          item={modalItem.item}
          onClose={() => setModalItem(null)}
        />
      )}
    </>
  );
}

// =============================================================================
// 2D VIEW - Enhanced with clickable cells for complex data
// =============================================================================

function TwoDView({ data, axes }: { data: unknown[][]; axes: string[] }) {
  const [modalCell, setModalCell] = useState<{ row: number; col: number; item: unknown } | null>(null);
  
  const rowAxis = axes[0] || 'row';
  const colAxis = axes[1] || 'col';
  const maxCols = Math.max(...data.map((row) => (Array.isArray(row) ? row.length : 0)), 0);
  
  if (data.length === 0) {
    return <div className="text-sm text-slate-400 text-center py-4">Empty tensor</div>;
  }
  
  const handleCellClick = (row: number, col: number, cell: unknown) => {
    const isComplex = typeof cell === 'object' && cell !== null;
    const formatted = formatCellValue(cell);
    if (isComplex || formatted.length > 30) {
      setModalCell({ row, col, item: cell });
    }
  };
  
  return (
    <>
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-slate-50">
              <th className="px-2 py-1.5 border border-slate-200 text-slate-400 text-xs font-normal">
                {/* Corner cell */}
              </th>
              {Array.from({ length: maxCols }, (_, j) => (
                <th
                  key={j}
                  className="px-2 py-1.5 border border-slate-200 text-slate-500 text-xs font-medium"
                >
                  {colAxis}[{j}]
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, i) => (
              <tr key={i}>
                <td className="px-2 py-1.5 border border-slate-200 bg-slate-50 text-slate-500 text-xs font-medium">
                  {rowAxis}[{i}]
                </td>
                {Array.from({ length: maxCols }, (_, j) => {
                  const cell = Array.isArray(row) && j < row.length ? row[j] : null;
                  const isComplex = typeof cell === 'object' && cell !== null;
                  const formatted = formatCellValue(cell);
                  const isClickable = isComplex || formatted.length > 30;
                  
                  return (
                    <td
                      key={j}
                      onClick={() => isClickable && handleCellClick(i, j, cell)}
                      className={`
                        px-2 py-1.5 border border-slate-200 font-mono text-slate-700 max-w-[150px]
                        ${isClickable ? 'cursor-pointer hover:bg-blue-50 hover:border-blue-300 transition-colors' : 'text-center'}
                      `}
                      title={isClickable ? 'Click to expand' : undefined}
                    >
                      <div className="truncate">
                        {formatted.length > 30 ? formatted.substring(0, 27) + '...' : formatted}
                      </div>
                      {isClickable && (
                        <div className="text-[9px] text-blue-500 mt-0.5">click to expand</div>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {/* Modal for cell expansion */}
      {modalCell && (
        <ItemModal
          index={modalCell.row}
          axisName={`${rowAxis}[${modalCell.row}], ${colAxis}[${modalCell.col}]`}
          item={modalCell.item}
          onClose={() => setModalCell(null)}
        />
      )}
    </>
  );
}

// =============================================================================
// N-D VIEW (3D+)
// =============================================================================

interface NDViewProps {
  data: TensorData;
  displayData: TensorData;
  shape: number[];
  axes: string[];
  sliceState: SliceState;
  setSliceState: React.Dispatch<React.SetStateAction<SliceState>>;
}

function NDView({
  data,
  displayData,
  shape,
  axes,
  sliceState,
  setSliceState,
}: NDViewProps) {
  const dims = shape.length;
  const { displayAxes, sliceIndices, viewMode } = sliceState;
  
  // Get non-displayed axes that need sliders
  const sliceAxes = Array.from({ length: dims }, (_, i) => i)
    .filter((i) => !displayAxes.includes(i) && shape[i] > 1);
  
  return (
    <div className="space-y-3">
      {/* Axis selectors */}
      <div className="flex flex-wrap gap-3 items-end">
        {/* Row axis */}
        <div>
          <label className="text-xs text-slate-500 block mb-1">Row Axis</label>
          <select
            value={displayAxes[0]}
            onChange={(e) => {
              const newRow = Number(e.target.value);
              setSliceState((s) => ({
                ...s,
                displayAxes: [newRow, displayAxes[1] === newRow ? displayAxes[0] : displayAxes[1]],
              }));
            }}
            className="text-xs border border-slate-200 rounded px-2 py-1"
          >
            {Array.from({ length: dims }, (_, i) => (
              <option key={i} value={i}>
                {axes[i]} ({shape[i]})
              </option>
            ))}
          </select>
        </div>
        
        {/* Column axis */}
        <div>
          <label className="text-xs text-slate-500 block mb-1">Col Axis</label>
          <select
            value={displayAxes[1]}
            onChange={(e) => {
              const newCol = Number(e.target.value);
              setSliceState((s) => ({
                ...s,
                displayAxes: [displayAxes[0] === newCol ? displayAxes[1] : displayAxes[0], newCol],
              }));
            }}
            className="text-xs border border-slate-200 rounded px-2 py-1"
          >
            {Array.from({ length: dims }, (_, i) => (
              <option key={i} value={i} disabled={i === displayAxes[0]}>
                {axes[i]} ({shape[i]})
              </option>
            ))}
          </select>
        </div>
        
        {/* View mode */}
        <div className="flex border border-slate-200 rounded overflow-hidden">
          <button
            onClick={() => setSliceState((s) => ({ ...s, viewMode: 'table' }))}
            className={`p-1.5 ${viewMode === 'table' ? 'bg-slate-100' : 'hover:bg-slate-50'}`}
            title="Table view"
          >
            <Grid3X3 size={14} />
          </button>
          <button
            onClick={() => setSliceState((s) => ({ ...s, viewMode: 'list' }))}
            className={`p-1.5 ${viewMode === 'list' ? 'bg-slate-100' : 'hover:bg-slate-50'}`}
            title="List view"
          >
            <List size={14} />
          </button>
          <button
            onClick={() => setSliceState((s) => ({ ...s, viewMode: 'json' }))}
            className={`p-1.5 ${viewMode === 'json' ? 'bg-slate-100' : 'hover:bg-slate-50'}`}
            title="JSON view"
          >
            <Code size={14} />
          </button>
        </div>
      </div>
      
      {/* Slice sliders */}
      {sliceAxes.length > 0 && (
        <div className="space-y-2">
          <div className="text-xs text-slate-500">Slice indices:</div>
          {sliceAxes.map((axisIdx) => (
            <div key={axisIdx} className="flex items-center gap-2">
              <label className="text-xs text-slate-600 min-w-[60px]">
                {axes[axisIdx]}:
              </label>
              <input
                type="range"
                min={0}
                max={shape[axisIdx] - 1}
                value={sliceIndices[axisIdx] ?? 0}
                onChange={(e) => {
                  const val = Number(e.target.value);
                  setSliceState((s) => ({
                    ...s,
                    sliceIndices: { ...s.sliceIndices, [axisIdx]: val },
                  }));
                }}
                className="flex-1"
              />
              <span className="text-xs text-slate-500 min-w-[30px] text-right">
                [{sliceIndices[axisIdx] ?? 0}]
              </span>
            </div>
          ))}
        </div>
      )}
      
      {/* Slice description */}
      <div className="text-xs text-slate-500 bg-slate-50 px-2 py-1 rounded">
        📍 Viewing: {getSliceDescription(axes, shape, displayAxes, sliceIndices)}
      </div>
      
      {/* Display sliced data */}
      {viewMode === 'json' ? (
        <pre className="text-xs bg-slate-50 p-2 rounded overflow-x-auto max-h-48">
          {JSON.stringify(displayData, null, 2)}
        </pre>
      ) : viewMode === 'list' ? (
        Array.isArray(displayData) ? (
          <OneDView data={displayData as unknown[]} axisName={axes[displayAxes[0]]} />
        ) : (
          <ScalarView data={displayData} />
        )
      ) : (
        // Table view
        Array.isArray(displayData) && 
        displayData.length > 0 && 
        Array.isArray(displayData[0]) ? (
          <TwoDView
            data={displayData as unknown[][]}
            axes={[axes[displayAxes[0]], axes[displayAxes[1]]]}
          />
        ) : Array.isArray(displayData) ? (
          <OneDView data={displayData as unknown[]} axisName={axes[displayAxes[0]]} />
        ) : (
          <ScalarView data={displayData} />
        )
      )}
    </div>
  );
}

export default TensorInspector;

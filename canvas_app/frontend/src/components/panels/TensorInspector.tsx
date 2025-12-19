/**
 * TensorInspector - Interactive N-D tensor viewer
 * Ported from streamlit_app/tabs/execute/preview/tensor_display.py
 */

import { useState, useMemo } from 'react';
import { Layers, Grid3X3, List, Code, ChevronDown, ChevronUp } from 'lucide-react';
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
  conceptName?: string;
  isGround?: boolean;
  isCompact?: boolean;
}

export function TensorInspector({
  data,
  axes: providedAxes,
  conceptName,
  isGround,
  isCompact = false,
}: TensorInspectorProps) {
  const shape = useMemo(() => getTensorShape(data), [data]);
  const dims = shape.length;
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
// 1D VIEW
// =============================================================================

function OneDView({ data, axisName }: { data: unknown[]; axisName: string }) {
  const isShort = data.length <= 6;
  
  if (isShort) {
    return (
      <div className="flex gap-2 flex-wrap">
        {data.map((item, i) => (
          <div
            key={i}
            className="flex flex-col items-center bg-slate-50 border border-slate-200 rounded px-3 py-2 min-w-[60px]"
          >
            <div className="text-[10px] text-slate-400">{axisName}[{i}]</div>
            <div className="text-sm font-mono text-slate-700">
              {formatCellValue(item)}
            </div>
          </div>
        ))}
      </div>
    );
  }
  
  return (
    <div className="max-h-48 overflow-y-auto">
      {data.map((item, i) => (
        <div
          key={i}
          className="flex gap-3 py-1.5 border-b border-slate-100 last:border-b-0"
        >
          <span className="text-xs text-slate-400 min-w-[50px]">[{i}]</span>
          <span className="text-sm font-mono text-slate-700">
            {formatCellValue(item)}
          </span>
        </div>
      ))}
    </div>
  );
}

// =============================================================================
// 2D VIEW
// =============================================================================

function TwoDView({ data, axes }: { data: unknown[][]; axes: string[] }) {
  const rowAxis = axes[0] || 'row';
  const colAxis = axes[1] || 'col';
  const maxCols = Math.max(...data.map((row) => (Array.isArray(row) ? row.length : 0)), 0);
  
  if (data.length === 0) {
    return <div className="text-sm text-slate-400 text-center py-4">Empty tensor</div>;
  }
  
  return (
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
                return (
                  <td
                    key={j}
                    className="px-2 py-1.5 border border-slate-200 text-center font-mono text-slate-700"
                  >
                    {formatCellValue(cell)}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
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

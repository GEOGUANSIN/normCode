/**
 * Tensor utilities for shape calculation, slicing, and formatting.
 * Ported from streamlit_app/tabs/execute/preview/utils.py
 */

// =============================================================================
// TYPES
// =============================================================================

export type TensorData = unknown;
export type TensorShape = number[];

export interface SliceState {
  displayAxes: number[];      // Which axes to display (up to 2)
  sliceIndices: Record<number, number>;  // Index for non-displayed axes
  viewMode: 'table' | 'list' | 'json';
}

// =============================================================================
// TENSOR SHAPE UTILITIES
// =============================================================================

/**
 * Get the shape of tensor data as an array.
 * Handles nested arrays of any depth.
 */
export function getTensorShape(data: TensorData): TensorShape {
  if (!Array.isArray(data)) {
    return [];  // Scalar
  }
  
  const shape: number[] = [];
  let current: unknown = data;
  
  while (Array.isArray(current)) {
    shape.push(current.length);
    if (current.length > 0) {
      current = current[0];
    } else {
      break;
    }
  }
  
  return shape;
}

/**
 * Get a string representation of tensor shape.
 */
export function getShapeString(shape: TensorShape): string {
  if (shape.length === 0) {
    return 'scalar';
  }
  return shape.join('×');
}

/**
 * Get dimensions count.
 */
export function getDimensions(data: TensorData): number {
  return getTensorShape(data).length;
}

// =============================================================================
// VALUE FORMATTING
// =============================================================================

/**
 * Format a cell value for display.
 * Handles special syntax like %(value).
 */
export function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) {
    return '∅';
  }
  
  if (typeof value === 'string') {
    // Check for special %(value) syntax
    if (value.startsWith('%(') && value.endsWith(')')) {
      const inner = value.slice(2, -1);
      return `📌 ${inner}`;
    }
    // Truncate long strings
    if (value.length > 50) {
      return value.slice(0, 47) + '...';
    }
    return value;
  }
  
  if (typeof value === 'number') {
    // Format numbers nicely
    if (Number.isInteger(value)) {
      return value.toString();
    }
    return value.toFixed(4).replace(/\.?0+$/, '');
  }
  
  if (typeof value === 'boolean') {
    return value ? '✓' : '✗';
  }
  
  if (Array.isArray(value)) {
    return `[${value.length} items]`;
  }
  
  if (typeof value === 'object') {
    return `{${Object.keys(value).length} keys}`;
  }
  
  return String(value);
}

/**
 * Format a cell value for JSON display (untruncated).
 */
export function formatCellValueFull(value: unknown): string {
  if (value === null || value === undefined) {
    return 'null';
  }
  
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2);
  }
  
  return String(value);
}

// =============================================================================
// TENSOR SLICING
// =============================================================================

/**
 * Slice a tensor to extract a 2D (or lower) view.
 * 
 * @param data - The full tensor data
 * @param displayAxes - Which axes to keep (display)
 * @param sliceIndices - Index values for axes not in displayAxes
 * @param totalDims - Total number of dimensions
 * @returns Sliced data (2D or lower)
 */
export function sliceTensor(
  data: TensorData,
  displayAxes: number[],
  sliceIndices: Record<number, number>,
  totalDims: number
): TensorData {
  if (totalDims <= 2) {
    return data;
  }
  
  function extractSlice(d: unknown, dim: number): unknown {
    if (dim >= totalDims) {
      return d;
    }
    
    if (!Array.isArray(d)) {
      return d;
    }
    
    if (displayAxes.includes(dim)) {
      // Keep this dimension - recurse into each element
      return d.map((item) => extractSlice(item, dim + 1));
    } else {
      // Slice this dimension - take single index
      const idx = sliceIndices[dim] ?? 0;
      if (idx < d.length) {
        return extractSlice(d[idx], dim + 1);
      }
      return null;
    }
  }
  
  return extractSlice(data, 0);
}

/**
 * Generate a human-readable description of the current slice.
 */
export function getSliceDescription(
  axes: string[],
  shape: TensorShape,
  displayAxes: number[],
  sliceIndices: Record<number, number>
): string {
  const parts: string[] = [];
  
  for (let i = 0; i < shape.length; i++) {
    if (displayAxes.includes(i)) {
      parts.push(`${axes[i] || `axis_${i}`}[:]`);
    } else {
      const idx = sliceIndices[i] ?? 0;
      parts.push(`${axes[i] || `axis_${i}`}[${idx}]`);
    }
  }
  
  return parts.join(' × ');
}

// =============================================================================
// INITIAL STATE HELPERS
// =============================================================================

/**
 * Create initial slice state for a tensor.
 */
export function createInitialSliceState(dims: number): SliceState {
  return {
    displayAxes: dims >= 2 ? [0, 1] : dims === 1 ? [0] : [],
    sliceIndices: Object.fromEntries(
      Array.from({ length: dims }, (_, i) => [i, 0])
    ),
    viewMode: dims >= 2 ? 'table' : 'list',
  };
}

/**
 * Generate default axis names if not provided.
 */
export function ensureAxisNames(axes: string[] | undefined, dims: number): string[] {
  const result = [...(axes || [])];
  while (result.length < dims) {
    result.push(`axis_${result.length}`);
  }
  return result;
}

// =============================================================================
// DATA TYPE DETECTION
// =============================================================================

/**
 * Detect the element type of tensor data.
 */
export function detectElementType(data: TensorData): string {
  // Navigate to a leaf element
  let current: unknown = data;
  while (Array.isArray(current) && current.length > 0) {
    current = current[0];
  }
  
  if (current === null || current === undefined) {
    return 'null';
  }
  
  const type = typeof current;
  
  if (type === 'object') {
    if (Array.isArray(current)) {
      return 'array';
    }
    // Check for common object structures
    const keys = Object.keys(current as object);
    if (keys.length <= 3) {
      return `{${keys.join(', ')}}`;
    }
    return `object(${keys.length} keys)`;
  }
  
  return type;
}

/**
 * Check if data is a valid tensor (has reference format).
 */
export function isReferenceData(data: unknown): data is { data: TensorData; axes?: string[] } {
  return (
    data !== null &&
    typeof data === 'object' &&
    'data' in data &&
    (data as Record<string, unknown>).data !== undefined
  );
}

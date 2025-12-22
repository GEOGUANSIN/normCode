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
 * 
 * IMPORTANT: When the tensor contains complex values (objects, nested arrays)
 * as cell values, those should NOT be counted as additional dimensions.
 * Use the `maxDims` parameter to limit shape calculation to the known
 * number of axes from the backend.
 * 
 * @param data - The tensor data (nested arrays)
 * @param maxDims - Optional maximum dimensions to calculate (from axes count).
 *                  If provided, stops descending once this depth is reached.
 *                  This prevents treating list VALUES as extra dimensions.
 */
export function getTensorShape(data: TensorData, maxDims?: number): TensorShape {
  if (!Array.isArray(data)) {
    return [];  // Scalar
  }
  
  const shape: number[] = [];
  let current: unknown = data;
  
  while (Array.isArray(current)) {
    // Stop if we've reached the maximum dimensions (based on axes count)
    if (maxDims !== undefined && shape.length >= maxDims) {
      break;
    }
    
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
 * 
 * @param data - The tensor data
 * @param maxDims - Optional maximum dimensions (from axes count)
 */
export function getDimensions(data: TensorData, maxDims?: number): number {
  return getTensorShape(data, maxDims).length;
}

// =============================================================================
// PERCEPTUAL SIGN PARSING
// =============================================================================

/**
 * Regex to detect perceptual sign format: %xxx(...) or %(...) 
 * Examples: %c2a({...}), %(some_value), %abc123(...)
 */
const PERCEPTUAL_SIGN_REGEX = /^%([a-zA-Z0-9]*)\((.+)\)$/s;

/**
 * Check if a string is a perceptual sign format.
 */
export function isPerceptualSign(value: unknown): value is string {
  if (typeof value !== 'string') return false;
  return PERCEPTUAL_SIGN_REGEX.test(value);
}

/**
 * Extract the content from a perceptual sign string.
 * Returns { id: string, content: string } or null if not a perceptual sign.
 */
export function extractPerceptualSign(value: string): { id: string; content: string } | null {
  const match = value.match(PERCEPTUAL_SIGN_REGEX);
  if (!match) return null;
  return { id: match[1] || '', content: match[2] };
}

/**
 * Try to parse Python dict-like syntax into a JavaScript object.
 * Handles: single quotes, True/False/None, and nested structures.
 */
export function parsePythonDict(content: string): unknown {
  try {
    // Convert Python syntax to JSON:
    // 1. Replace single quotes with double quotes (but handle escaped quotes)
    // 2. Replace True/False/None with JSON equivalents
    // 3. Handle multiline strings
    
    let jsonStr = content;
    
    // Replace Python booleans and None (word boundary to avoid replacing inside strings)
    // We need to be careful here - only replace outside of strings
    // Simple approach: replace known patterns
    jsonStr = jsonStr
      .replace(/:\s*True\b/g, ': true')
      .replace(/:\s*False\b/g, ': false')
      .replace(/:\s*None\b/g, ': null')
      .replace(/,\s*True\b/g, ', true')
      .replace(/,\s*False\b/g, ', false')
      .replace(/,\s*None\b/g, ', null')
      .replace(/\[\s*True\b/g, '[true')
      .replace(/\[\s*False\b/g, '[false')
      .replace(/\[\s*None\b/g, '[null');
    
    // Replace single quotes with double quotes
    // This is tricky because we need to handle:
    // - 'key': 'value' -> "key": "value"
    // - Don't break apostrophes inside strings like "don't"
    // Simple approach: replace ' with " for dict keys and simple values
    jsonStr = jsonStr.replace(/'/g, '"');
    
    // Try to parse as JSON
    return JSON.parse(jsonStr);
  } catch {
    // If parsing fails, return null
    return null;
  }
}

/**
 * Parse a perceptual sign value, returning the parsed object if possible.
 * Returns { id, parsed, raw } where parsed is the JS object (or null if unparseable).
 */
export interface ParsedPerceptualSign {
  id: string;
  parsed: unknown;
  raw: string;
}

export function parsePerceptualSignValue(value: string): ParsedPerceptualSign | null {
  const extracted = extractPerceptualSign(value);
  if (!extracted) return null;
  
  const parsed = parsePythonDict(extracted.content);
  return {
    id: extracted.id,
    parsed,
    raw: extracted.content,
  };
}

// =============================================================================
// VALUE FORMATTING
// =============================================================================

/**
 * Format a cell value for display.
 * Handles special syntax like %(value) and %xxx({...}).
 */
export function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) {
    return '∅';
  }
  
  if (typeof value === 'string') {
    // Check for perceptual sign format: %xxx(...) or %(...)
    const psResult = parsePerceptualSignValue(value);
    if (psResult) {
      if (psResult.parsed && typeof psResult.parsed === 'object' && !Array.isArray(psResult.parsed)) {
        const keys = Object.keys(psResult.parsed as object);
        const idPrefix = psResult.id ? `%${psResult.id}` : '%';
        if (keys.length <= 3) {
          return `${idPrefix}{${keys.join(', ')}}`;
        }
        return `${idPrefix}{${keys.length} keys}`;
      }
      // Fallback: show as pinned value
      const inner = psResult.raw.length > 40 ? psResult.raw.slice(0, 37) + '...' : psResult.raw;
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
 * 
 * @param data - The tensor data
 * @param axesCount - Optional number of axes. If provided, descends only that many
 *                    levels to find the element type. This prevents treating
 *                    nested list VALUES as tensor structure.
 */
export function detectElementType(data: TensorData, axesCount?: number): string {
  // Navigate to a leaf element, but only descend as far as the axes allow
  let current: unknown = data;
  let depth = 0;
  
  while (Array.isArray(current) && current.length > 0) {
    // Stop if we've descended through all axes
    if (axesCount !== undefined && depth >= axesCount) {
      break;
    }
    current = current[0];
    depth++;
  }
  
  if (current === null || current === undefined) {
    return 'null';
  }
  
  const type = typeof current;
  
  // Check for perceptual sign strings first
  if (type === 'string' && isPerceptualSign(current)) {
    const psResult = parsePerceptualSignValue(current as string);
    if (psResult?.parsed && typeof psResult.parsed === 'object' && !Array.isArray(psResult.parsed)) {
      const keys = Object.keys(psResult.parsed as object);
      const idPrefix = psResult.id ? `%${psResult.id}` : '%';
      if (keys.length <= 4) {
        return `${idPrefix}{${keys.join(', ')}}`;
      }
      return `${idPrefix}{object, ${keys.length} keys}`;
    }
    // Unparseable perceptual sign
    return psResult?.id ? `%${psResult.id}(...)` : '%(...)';
  }
  
  if (type === 'object') {
    if (Array.isArray(current)) {
      const arr = current as unknown[];
      if (arr.length === 0) {
        return 'array (empty)';
      }
      // Check if first element is a perceptual sign
      if (typeof arr[0] === 'string' && isPerceptualSign(arr[0])) {
        const psResult = parsePerceptualSignValue(arr[0]);
        if (psResult?.parsed && typeof psResult.parsed === 'object') {
          const keys = Object.keys(psResult.parsed as object);
          const idPrefix = psResult.id ? `%${psResult.id}` : '%';
          if (keys.length <= 3) {
            return `list[${idPrefix}{${keys.join(', ')}}]`;
          }
          return `list[${idPrefix}{...}] (${arr.length} items)`;
        }
      }
      // Show first element type for array values
      const firstType = typeof arr[0];
      if (firstType === 'object' && arr[0] !== null) {
        const keys = Object.keys(arr[0] as object);
        if (keys.length <= 3) {
          return `list[{${keys.join(', ')}}]`;
        }
        return `list[object] (${arr.length} items)`;
      }
      return `list[${firstType}] (${arr.length} items)`;
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

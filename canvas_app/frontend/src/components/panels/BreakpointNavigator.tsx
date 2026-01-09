/**
 * Breakpoint Navigator component
 * Allows navigating through breakpoints with prev/next and dropdown
 */

import { useState, useMemo, useCallback, useRef, useEffect } from 'react';
import { Circle, ChevronLeft, ChevronRight, ChevronDown, X } from 'lucide-react';
import { useExecutionStore } from '../../stores/executionStore';
import { useCanvasCommandStore } from '../../stores/canvasCommandStore';
import { executionApi } from '../../services/api';

// Utility to sort flow indices numerically (e.g., "1.2.3" comes before "1.10")
function sortFlowIndices(indices: string[]): string[] {
  return [...indices].sort((a, b) => {
    const partsA = a.split('.').map(Number);
    const partsB = b.split('.').map(Number);
    const maxLen = Math.max(partsA.length, partsB.length);
    for (let i = 0; i < maxLen; i++) {
      const numA = partsA[i] ?? 0;
      const numB = partsB[i] ?? 0;
      if (numA !== numB) return numA - numB;
    }
    return 0;
  });
}

export function BreakpointNavigator() {
  const breakpoints = useExecutionStore((s) => s.breakpoints);
  const removeBreakpoint = useExecutionStore((s) => s.removeBreakpoint);
  const addCommand = useCanvasCommandStore((s) => s.addCommand);
  
  const [isOpen, setIsOpen] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  // Sort breakpoints by flow index
  const sortedBreakpoints = useMemo(() => {
    return sortFlowIndices(Array.from(breakpoints));
  }, [breakpoints]);
  
  const count = sortedBreakpoints.length;
  
  // Clamp current index when breakpoints change
  useEffect(() => {
    if (currentIndex >= count) {
      setCurrentIndex(Math.max(0, count - 1));
    }
  }, [count, currentIndex]);
  
  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);
  
  // Navigate to a breakpoint
  const navigateTo = useCallback((flowIndex: string) => {
    addCommand('focus_node', { flow_index: flowIndex });
  }, [addCommand]);
  
  // Go to previous breakpoint
  const goPrev = useCallback(() => {
    if (count === 0) return;
    const newIndex = (currentIndex - 1 + count) % count;
    setCurrentIndex(newIndex);
    navigateTo(sortedBreakpoints[newIndex]);
  }, [count, currentIndex, sortedBreakpoints, navigateTo]);
  
  // Go to next breakpoint
  const goNext = useCallback(() => {
    if (count === 0) return;
    const newIndex = (currentIndex + 1) % count;
    setCurrentIndex(newIndex);
    navigateTo(sortedBreakpoints[newIndex]);
  }, [count, currentIndex, sortedBreakpoints, navigateTo]);
  
  // Handle clicking a specific breakpoint in dropdown
  const handleBreakpointClick = useCallback((flowIndex: string, index: number) => {
    setCurrentIndex(index);
    navigateTo(flowIndex);
    setIsOpen(false);
  }, [navigateTo]);
  
  // Handle removing a breakpoint
  const handleRemoveBreakpoint = useCallback(async (e: React.MouseEvent, flowIndex: string) => {
    e.stopPropagation();
    try {
      await executionApi.clearBreakpoint(flowIndex);
      removeBreakpoint(flowIndex);
    } catch (err) {
      console.error('Failed to remove breakpoint:', err);
    }
  }, [removeBreakpoint]);
  
  if (count === 0) {
    return (
      <div className="flex items-center gap-1 text-sm text-slate-400">
        <Circle size={12} className="text-slate-300" />
        <span>No BP</span>
      </div>
    );
  }
  
  return (
    <div className="relative" ref={dropdownRef}>
      <div className="flex items-center gap-0.5">
        {/* Previous button */}
        <button
          onClick={goPrev}
          className="p-1 rounded hover:bg-slate-100 text-slate-500 hover:text-slate-700 transition-colors"
          title="Previous breakpoint"
        >
          <ChevronLeft size={14} />
        </button>
        
        {/* Breakpoint count dropdown trigger */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-1 px-1.5 py-0.5 rounded hover:bg-red-50 text-sm text-slate-600 transition-colors"
          title="Click to see all breakpoints"
        >
          <Circle size={12} className="text-red-500 fill-red-500" />
          <span className="font-medium">{count} BP</span>
          <ChevronDown size={12} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>
        
        {/* Next button */}
        <button
          onClick={goNext}
          className="p-1 rounded hover:bg-slate-100 text-slate-500 hover:text-slate-700 transition-colors"
          title="Next breakpoint"
        >
          <ChevronRight size={14} />
        </button>
      </div>
      
      {/* Dropdown */}
      {isOpen && (
        <div className="absolute top-full right-0 mt-1 w-56 bg-white rounded-lg shadow-lg border border-slate-200 py-1 z-50 max-h-64 overflow-y-auto">
          <div className="px-3 py-1.5 text-xs text-slate-400 uppercase font-medium border-b border-slate-100">
            Breakpoints ({count})
          </div>
          {sortedBreakpoints.map((flowIndex, index) => (
            <div
              key={flowIndex}
              className={`flex items-center justify-between px-3 py-1.5 cursor-pointer transition-colors group ${
                index === currentIndex
                  ? 'bg-red-50 text-red-700'
                  : 'hover:bg-slate-50 text-slate-700'
              }`}
              onClick={() => handleBreakpointClick(flowIndex, index)}
            >
              <div className="flex items-center gap-2">
                <Circle size={10} className={`${
                  index === currentIndex ? 'text-red-500 fill-red-500' : 'text-red-400 fill-red-400'
                }`} />
                <span className="font-mono text-sm">{flowIndex}</span>
              </div>
              <button
                onClick={(e) => handleRemoveBreakpoint(e, flowIndex)}
                className="p-0.5 rounded opacity-0 group-hover:opacity-100 hover:bg-red-100 text-slate-400 hover:text-red-600 transition-all"
                title="Remove breakpoint"
              >
                <X size={12} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


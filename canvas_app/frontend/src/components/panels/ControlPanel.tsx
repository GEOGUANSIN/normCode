/**
 * Control Panel for execution commands
 */

import { Play, Pause, Square, SkipForward, RotateCcw, Circle, RefreshCw } from 'lucide-react';
import { useExecutionStore } from '../../stores/executionStore';
import { executionApi } from '../../services/api';

export function ControlPanel() {
  const status = useExecutionStore((s) => s.status);
  const completedCount = useExecutionStore((s) => s.completedCount);
  const totalCount = useExecutionStore((s) => s.totalCount);
  const cycleCount = useExecutionStore((s) => s.cycleCount);
  const currentInference = useExecutionStore((s) => s.currentInference);
  const breakpointsCount = useExecutionStore((s) => s.breakpoints.size);
  const setStatus = useExecutionStore((s) => s.setStatus);

  const isRunning = status === 'running';
  const isPaused = status === 'paused';
  const isIdle = status === 'idle';
  const isCompleted = status === 'completed';
  const isFailed = status === 'failed';

  const progressPercent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  const handleStart = async () => {
    try {
      await executionApi.start();
      setStatus('running');
    } catch (e) {
      console.error('Failed to start:', e);
    }
  };

  const handlePause = async () => {
    try {
      await executionApi.pause();
      setStatus('paused');
    } catch (e) {
      console.error('Failed to pause:', e);
    }
  };

  const handleResume = async () => {
    try {
      await executionApi.resume();
      setStatus('running');
    } catch (e) {
      console.error('Failed to resume:', e);
    }
  };

  const handleStep = async () => {
    try {
      await executionApi.step();
      setStatus('stepping');
    } catch (e) {
      console.error('Failed to step:', e);
    }
  };

  const handleStop = async () => {
    try {
      await executionApi.stop();
      setStatus('idle');
    } catch (e) {
      console.error('Failed to stop:', e);
    }
  };

  return (
    <div className="bg-white border-b border-slate-200 px-4 py-2 relative z-10">
      <div className="flex items-center gap-4">
        {/* Execution controls */}
        <div className="flex items-center gap-1">
          {/* Play/Resume button */}
          {(isIdle || isPaused || isCompleted || isFailed) && (
            <button
              onClick={isPaused ? handleResume : handleStart}
              className="p-2 rounded-lg bg-green-500 hover:bg-green-600 text-white transition-colors"
              title={isPaused ? 'Resume' : 'Run'}
            >
              <Play size={18} />
            </button>
          )}

          {/* Pause button */}
          {isRunning && (
            <button
              onClick={handlePause}
              className="p-2 rounded-lg bg-yellow-500 hover:bg-yellow-600 text-white transition-colors"
              title="Pause"
            >
              <Pause size={18} />
            </button>
          )}

          {/* Stop button */}
          <button
            onClick={handleStop}
            disabled={isIdle}
            className={`p-2 rounded-lg transition-colors ${
              isIdle
                ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                : 'bg-red-500 hover:bg-red-600 text-white'
            }`}
            title="Stop"
          >
            <Square size={18} />
          </button>

          {/* Step button */}
          <button
            onClick={handleStep}
            disabled={isRunning}
            className={`p-2 rounded-lg transition-colors ${
              isRunning
                ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                : 'bg-blue-500 hover:bg-blue-600 text-white'
            }`}
            title="Step"
          >
            <SkipForward size={18} />
          </button>

          {/* Reset button */}
          <button
            onClick={handleStop}
            className="p-2 rounded-lg bg-slate-200 hover:bg-slate-300 text-slate-700 transition-colors"
            title="Reset"
          >
            <RotateCcw size={18} />
          </button>
        </div>

        {/* Divider */}
        <div className="w-px h-8 bg-slate-200" />

        {/* Status */}
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${
              isRunning
                ? 'bg-green-500 animate-pulse'
                : isPaused
                ? 'bg-yellow-500'
                : isCompleted
                ? 'bg-green-500'
                : isFailed
                ? 'bg-red-500'
                : 'bg-slate-400'
            }`}
          />
          <span className="text-sm font-medium text-slate-700 capitalize">
            {status}
          </span>
        </div>

        {/* Progress */}
        <div className="flex items-center gap-2 flex-1">
          <div className="flex-1 max-w-xs">
            <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 transition-all duration-300"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>
          <span className="text-sm text-slate-600">
            {completedCount}/{totalCount}
          </span>
        </div>

        {/* Current inference */}
        {currentInference && (
          <>
            <div className="w-px h-8 bg-slate-200" />
            <div className="flex items-center gap-1 text-sm text-slate-600">
              <RefreshCw size={12} className={isRunning ? 'animate-spin text-blue-500' : 'text-slate-400'} />
              <span className="font-mono text-xs truncate max-w-[150px]" title={currentInference}>
                {currentInference}
              </span>
            </div>
          </>
        )}

        {/* Cycle count */}
        {cycleCount > 0 && (
          <div className="text-sm text-slate-500">
            Cycle {cycleCount}
          </div>
        )}

        {/* Breakpoints count */}
        <div className="flex items-center gap-1 text-sm text-slate-600">
          <Circle size={12} className="text-red-500 fill-red-500" />
          <span>{breakpointsCount} breakpoints</span>
        </div>
      </div>
    </div>
  );
}

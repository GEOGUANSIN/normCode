/**
 * Control Panel for execution commands
 */

import { useState } from 'react';
import { Play, Pause, Square, SkipForward, RotateCcw, Circle, RefreshCw, Bug, Database, Rabbit, Turtle } from 'lucide-react';
import { useExecutionStore } from '../../stores/executionStore';
import { executionApi } from '../../services/api';
import { STEP_FULL_NAMES } from '../../types/execution';

interface ControlPanelProps {
  onCheckpointToggle?: () => void;
  checkpointPanelOpen?: boolean;
}

export function ControlPanel({ onCheckpointToggle, checkpointPanelOpen }: ControlPanelProps = {}) {
  const status = useExecutionStore((s) => s.status);
  const completedCount = useExecutionStore((s) => s.completedCount);
  const totalCount = useExecutionStore((s) => s.totalCount);
  const cycleCount = useExecutionStore((s) => s.cycleCount);
  const currentInference = useExecutionStore((s) => s.currentInference);
  const breakpointsCount = useExecutionStore((s) => s.breakpoints.size);
  const setStatus = useExecutionStore((s) => s.setStatus);
  const reset = useExecutionStore((s) => s.reset);
  const verboseLogging = useExecutionStore((s) => s.verboseLogging);
  const setVerboseLogging = useExecutionStore((s) => s.setVerboseLogging);
  const stepProgress = useExecutionStore((s) => s.stepProgress);
  const runId = useExecutionStore((s) => s.runId);
  const runMode = useExecutionStore((s) => s.runMode);
  const setRunMode = useExecutionStore((s) => s.setRunMode);
  
  const [isTogglingVerbose, setIsTogglingVerbose] = useState(false);
  const [isTogglingRunMode, setIsTogglingRunMode] = useState(false);
  
  // Get current step progress for the running inference
  const currentStepProgress = currentInference ? stepProgress[currentInference] : null;

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

  const handleRestart = async () => {
    try {
      await executionApi.restart();
      // Reset local state as well - the WebSocket will also send updates
      reset();
    } catch (e) {
      console.error('Failed to restart:', e);
    }
  };

  const handleToggleVerbose = async () => {
    setIsTogglingVerbose(true);
    try {
      const newState = !verboseLogging;
      await executionApi.setVerboseLogging(newState);
      setVerboseLogging(newState);
    } catch (e) {
      console.error('Failed to toggle verbose logging:', e);
    } finally {
      setIsTogglingVerbose(false);
    }
  };

  const handleToggleRunMode = async () => {
    setIsTogglingRunMode(true);
    try {
      const newMode = runMode === 'slow' ? 'fast' : 'slow';
      await executionApi.setRunMode(newMode);
      setRunMode(newMode);
    } catch (e) {
      console.error('Failed to toggle run mode:', e);
    } finally {
      setIsTogglingRunMode(false);
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

          {/* Reset/Restart button - available after completion or when not idle */}
          <button
            onClick={handleRestart}
            disabled={isIdle && !isCompleted && !isFailed}
            className={`p-2 rounded-lg transition-colors ${
              (isCompleted || isFailed)
                ? 'bg-orange-500 hover:bg-orange-600 text-white'
                : isIdle
                ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                : 'bg-slate-200 hover:bg-slate-300 text-slate-700'
            }`}
            title={isCompleted || isFailed ? "Reset & Run Again" : "Reset"}
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

        {/* Current inference and step */}
        {currentInference && (
          <>
            <div className="w-px h-8 bg-slate-200" />
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <RefreshCw size={12} className={isRunning ? 'animate-spin text-blue-500' : 'text-slate-400'} />
              <span className="font-mono text-xs truncate max-w-[100px]" title={currentInference}>
                {currentInference}
              </span>
              {/* Show current step if available */}
              {currentStepProgress?.current_step && (
                <span 
                  className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-[10px] font-mono font-medium animate-pulse"
                  title={STEP_FULL_NAMES[currentStepProgress.current_step] || currentStepProgress.current_step}
                >
                  {currentStepProgress.current_step}
                  {currentStepProgress.total_steps > 0 && (
                    <span className="text-blue-500 ml-1">
                      {(currentStepProgress.current_step_index || 0) + 1}/{currentStepProgress.total_steps}
                    </span>
                  )}
                </span>
              )}
            </div>
          </>
        )}

        {/* Cycle count */}
        {cycleCount > 0 && (
          <div className="text-sm text-slate-500">
            Cycle {cycleCount}
          </div>
        )}

        {/* Run ID */}
        {runId && (
          <div 
            className="text-xs text-slate-400 font-mono truncate max-w-[120px]" 
            title={`Run: ${runId}`}
          >
            Run: {runId.length > 12 ? `${runId.slice(0, 12)}...` : runId}
          </div>
        )}

        {/* Breakpoints count */}
        <div className="flex items-center gap-1 text-sm text-slate-600">
          <Circle size={12} className="text-red-500 fill-red-500" />
          <span>{breakpointsCount} BP</span>
        </div>

        {/* Run mode toggle (Slow/Fast) */}
        <button
          onClick={handleToggleRunMode}
          disabled={isTogglingRunMode || isRunning}
          className={`flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors ${
            runMode === 'fast'
              ? 'bg-amber-100 text-amber-700 border border-amber-200'
              : 'bg-teal-100 text-teal-700 border border-teal-200'
          } disabled:opacity-50`}
          title={runMode === 'slow' 
            ? 'Slow mode: One inference at a time (easier to follow)' 
            : 'Fast mode: All ready inferences per cycle (faster execution)'}
        >
          {runMode === 'slow' ? (
            <Turtle size={12} className="text-teal-500" />
          ) : (
            <Rabbit size={12} className="text-amber-500" />
          )}
          <span>{runMode === 'slow' ? 'Slow' : 'Fast'}</span>
        </button>

        {/* Verbose logging toggle */}
        <button
          onClick={handleToggleVerbose}
          disabled={isTogglingVerbose}
          className={`flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors ${
            verboseLogging
              ? 'bg-purple-100 text-purple-700 border border-purple-200'
              : 'bg-slate-100 text-slate-600 border border-slate-200 hover:bg-slate-200'
          } disabled:opacity-50`}
          title={verboseLogging ? 'Verbose logging enabled (DEBUG level)' : 'Enable verbose logging'}
        >
          <Bug size={12} className={verboseLogging ? 'text-purple-500' : 'text-slate-400'} />
          <span>Verbose</span>
        </button>

        {/* Checkpoint panel toggle */}
        {onCheckpointToggle && (
          <button
            onClick={onCheckpointToggle}
            className={`flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors ${
              checkpointPanelOpen
                ? 'bg-indigo-100 text-indigo-700 border border-indigo-200'
                : 'bg-slate-100 text-slate-600 border border-slate-200 hover:bg-slate-200'
            }`}
            title="Resume or fork from checkpoint"
          >
            <Database size={12} className={checkpointPanelOpen ? 'text-indigo-500' : 'text-slate-400'} />
            <span>Checkpoints</span>
          </button>
        )}
      </div>
    </div>
  );
}

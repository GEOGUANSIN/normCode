/**
 * Control Panel for execution commands
 * Supports both local and remote execution control.
 */

import { useState } from 'react';
import { Play, Pause, Square, SkipForward, RotateCcw, RefreshCw, Bug, Database, Rabbit, Turtle, Globe } from 'lucide-react';
import { BreakpointNavigator } from './BreakpointNavigator';
import { useExecutionStore } from '../../stores/executionStore';
import { useProjectStore } from '../../stores/projectStore';
import { useDeploymentStore } from '../../stores/deploymentStore';
import { executionApi, deploymentApi } from '../../services/api';
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
  const setStatus = useExecutionStore((s) => s.setStatus);
  const reset = useExecutionStore((s) => s.reset);
  const verboseLogging = useExecutionStore((s) => s.verboseLogging);
  const setVerboseLogging = useExecutionStore((s) => s.setVerboseLogging);
  const stepProgress = useExecutionStore((s) => s.stepProgress);
  const runId = useExecutionStore((s) => s.runId);
  const runMode = useExecutionStore((s) => s.runMode);
  const setRunMode = useExecutionStore((s) => s.setRunMode);
  
  // Check if we're on a remote tab
  const activeRemoteTabId = useProjectStore((s) => s.activeRemoteTabId);
  const remoteProjectTabs = useProjectStore((s) => s.remoteProjectTabs);
  const boundRemoteRuns = useDeploymentStore((s) => s.boundRemoteRuns);
  
  const [isTogglingVerbose, setIsTogglingVerbose] = useState(false);
  const [isTogglingRunMode, setIsTogglingRunMode] = useState(false);
  
  // Determine if we're controlling a remote run
  const activeRemoteTab = activeRemoteTabId 
    ? remoteProjectTabs.find(t => t.id === activeRemoteTabId) 
    : null;
  
  // Check if this remote tab has a bound run_id directly (new approach)
  // or fallback to searching in boundRemoteRuns list (legacy)
  const boundRun = activeRemoteTab?.run_id
    ? boundRemoteRuns.find(r => r.run_id === activeRemoteTab.run_id)
    : activeRemoteTab
      ? boundRemoteRuns.find(r => 
          r.server_id === activeRemoteTab.server_id && 
          (r.plan_id === activeRemoteTab.plan_id || r.run_id.includes(activeRemoteTab.plan_id))
        )
      : null;
  
  // Remote tab is controllable if it has a run_id (bound or from tab)
  const isRemote = !!activeRemoteTabId && (!!boundRun || !!activeRemoteTab?.run_id);
  const remoteServerId = boundRun?.server_id || activeRemoteTab?.server_id;
  const remoteRunId = boundRun?.run_id || activeRemoteTab?.run_id;
  
  // Get current step progress for the running inference
  const currentStepProgress = currentInference ? stepProgress[currentInference] : null;

  const isRunning = status === 'running';
  const isPaused = status === 'paused';
  const isStepping = status === 'stepping';
  const isIdle = status === 'idle';
  const isCompleted = status === 'completed';
  const isFailed = status === 'failed';

  const progressPercent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  const handleStart = async () => {
    try {
      if (isRemote && remoteServerId && remoteRunId) {
        // For remote runs, "start" means "continue" from paused
        await deploymentApi.continueRemoteRun(remoteServerId, remoteRunId);
        setStatus('running');
      } else {
        await executionApi.start();
        setStatus('running');
      }
    } catch (e) {
      console.error('Failed to start:', e);
    }
  };

  const handlePause = async () => {
    try {
      if (isRemote && remoteServerId && remoteRunId) {
        await deploymentApi.pauseRemoteRun(remoteServerId, remoteRunId);
        setStatus('paused');
      } else {
        await executionApi.pause();
        setStatus('paused');
      }
    } catch (e) {
      console.error('Failed to pause:', e);
    }
  };

  const handleResume = async () => {
    try {
      if (isRemote && remoteServerId && remoteRunId) {
        await deploymentApi.continueRemoteRun(remoteServerId, remoteRunId);
        setStatus('running');
      } else {
        await executionApi.resume();
        setStatus('running');
      }
    } catch (e) {
      console.error('Failed to resume:', e);
    }
  };

  const handleStep = async () => {
    try {
      if (isRemote && remoteServerId && remoteRunId) {
        await deploymentApi.stepRemoteRun(remoteServerId, remoteRunId);
        setStatus('stepping');
      } else {
        await executionApi.step();
        setStatus('stepping');
      }
    } catch (e) {
      console.error('Failed to step:', e);
    }
  };

  const handleStop = async () => {
    try {
      if (isRemote && remoteServerId && remoteRunId) {
        await deploymentApi.stopRemoteRun(remoteServerId, remoteRunId);
        setStatus('idle');
      } else {
        await executionApi.stop();
        setStatus('idle');
      }
    } catch (e) {
      console.error('Failed to stop:', e);
    }
  };

  const handleRestart = async () => {
    try {
      if (isRemote) {
        // For remote runs, restart isn't directly supported - would need to start a new run
        console.log('Restart not supported for remote runs - start a new run instead');
        return;
      }
      await executionApi.restart();
      // Reset local state as well - the WebSocket will also send updates
      reset();
    } catch (e) {
      console.error('Failed to restart:', e);
    }
  };

  const handleToggleVerbose = async () => {
    if (isRemote) return; // Not supported for remote runs
    
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
    if (isRemote) return; // Not supported for remote runs
    
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
    <div className={`border-b px-4 py-2 relative z-10 ${isRemote ? 'bg-gradient-to-r from-cyan-50 to-white border-cyan-200' : 'bg-white border-slate-200'}`}>
      <div className="flex items-center gap-4">
        {/* Remote indicator */}
        {isRemote && (
          <>
            <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-cyan-100 text-cyan-700 border border-cyan-200">
              <Globe size={14} className="text-cyan-600" />
              <span className="text-xs font-medium">Remote</span>
            </div>
            <div className="w-px h-8 bg-cyan-200" />
          </>
        )}
        
        {/* Execution controls */}
        <div className="flex items-center gap-1">
          {/* Play/Resume button */}
          {(isIdle || isPaused || isStepping || isCompleted || isFailed) && (
            <button
              onClick={isPaused || isStepping ? handleResume : handleStart}
              className={`p-2 rounded-lg text-white transition-colors ${
                isRemote 
                  ? 'bg-cyan-500 hover:bg-cyan-600' 
                  : 'bg-green-500 hover:bg-green-600'
              }`}
              title={isPaused || isStepping ? 'Resume' : 'Run'}
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

          {/* Reset/Restart button - available after completion or when not idle, hidden for remote */}
          {!isRemote && (
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
          )}
        </div>

        {/* Divider */}
        <div className={`w-px h-8 ${isRemote ? 'bg-cyan-200' : 'bg-slate-200'}`} />

        {/* Status */}
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${
              isRunning
                ? 'bg-green-500 animate-pulse'
                : isPaused
                ? 'bg-yellow-500'
                : isStepping
                ? 'bg-blue-500 animate-pulse'
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

        {/* Breakpoints navigator */}
        <BreakpointNavigator />

        {/* Run mode toggle (Slow/Fast) - only for local execution */}
        {!isRemote && (
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
        )}

        {/* Verbose logging toggle - only for local execution */}
        {!isRemote && (
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
        )}

        {/* Checkpoint panel toggle - only for local execution */}
        {!isRemote && onCheckpointToggle && (
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
        
        {/* Remote run info */}
        {isRemote && remoteRunId && (
          <div 
            className="text-xs text-cyan-600 font-mono truncate max-w-[150px]" 
            title={`Remote Run: ${remoteRunId}`}
          >
            {remoteRunId.length > 12 ? `${remoteRunId.slice(0, 12)}...` : remoteRunId}
          </div>
        )}
      </div>
    </div>
  );
}

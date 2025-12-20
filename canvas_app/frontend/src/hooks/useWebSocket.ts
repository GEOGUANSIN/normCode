/**
 * Hook for WebSocket connection and event handling
 */

import { useEffect, useCallback, useState } from 'react';
import { wsClient } from '../services/websocket';
import { useExecutionStore } from '../stores/executionStore';
import type { WebSocketEvent, StepProgress } from '../types/execution';
import type { NodeStatus } from '../types/execution';

export function useWebSocket() {
  const setStatus = useExecutionStore((s) => s.setStatus);
  const setNodeStatus = useExecutionStore((s) => s.setNodeStatus);
  const setCurrentInference = useExecutionStore((s) => s.setCurrentInference);
  const setProgress = useExecutionStore((s) => s.setProgress);
  const addLog = useExecutionStore((s) => s.addLog);
  const addBreakpoint = useExecutionStore((s) => s.addBreakpoint);
  const removeBreakpoint = useExecutionStore((s) => s.removeBreakpoint);
  const setRunId = useExecutionStore((s) => s.setRunId);
  const setNodeStatuses = useExecutionStore((s) => s.setNodeStatuses);
  const reset = useExecutionStore((s) => s.reset);
  const setStepProgress = useExecutionStore((s) => s.setStepProgress);
  const updateStepProgress = useExecutionStore((s) => s.updateStepProgress);
  const clearStepProgress = useExecutionStore((s) => s.clearStepProgress);

  const handleEvent = useCallback(
    (event: WebSocketEvent) => {
      const { type, data } = event;

      switch (type) {
        case 'connection:established':
          console.log('WebSocket connected:', data.message);
          break;

        case 'execution:loaded':
          if (data.run_id) {
            setRunId(data.run_id as string);
          }
          if (data.total_inferences !== undefined) {
            setProgress(0, data.total_inferences as number);
          }
          break;

        case 'execution:started':
          setStatus('running');
          break;

        case 'execution:paused':
          setStatus('paused');
          if (data.inference) {
            setCurrentInference(data.inference as string);
          }
          break;

        case 'execution:resumed':
          setStatus('running');
          break;

        case 'execution:completed':
          setStatus('completed');
          setCurrentInference(null);
          if (data.completed_count !== undefined && data.total_count !== undefined) {
            setProgress(data.completed_count as number, data.total_count as number);
          }
          break;

        case 'execution:error':
          setStatus('failed');
          addLog({
            flowIndex: '',
            level: 'error',
            message: data.error as string,
          });
          break;

        case 'execution:stopped':
          setStatus('idle');
          setCurrentInference(null);
          break;

        case 'execution:reset':
          setStatus('idle');
          setCurrentInference(null);
          if (data.node_statuses) {
            setNodeStatuses(data.node_statuses as Record<string, NodeStatus>);
          }
          if (data.completed_count !== undefined && data.total_count !== undefined) {
            setProgress(data.completed_count as number, data.total_count as number);
          }
          addLog({
            flowIndex: '',
            level: 'info',
            message: 'Execution reset - ready to run again',
          });
          break;

        case 'execution:stepping':
          setStatus('stepping');
          break;

        case 'execution:progress':
          if (data.completed_count !== undefined && data.total_count !== undefined) {
            setProgress(data.completed_count as number, data.total_count as number);
          }
          if (data.current_inference) {
            setCurrentInference(data.current_inference as string);
          }
          break;

        case 'inference:started':
          if (data.flow_index) {
            setNodeStatus(data.flow_index as string, 'running');
            setCurrentInference(data.flow_index as string);
          }
          break;

        case 'inference:completed':
          if (data.flow_index) {
            setNodeStatus(data.flow_index as string, 'completed');
          }
          break;

        case 'inference:failed':
          if (data.flow_index) {
            setNodeStatus(data.flow_index as string, 'failed');
            addLog({
              flowIndex: data.flow_index as string,
              level: 'error',
              message: (data.error as string) || 'Inference failed',
            });
          }
          break;

        case 'inference:retry':
          if (data.flow_index) {
            setNodeStatus(data.flow_index as string, 'pending');
            addLog({
              flowIndex: data.flow_index as string,
              level: 'warning',
              message: `Retry scheduled: ${data.status || 'unknown status'}`,
            });
          }
          break;

        case 'inference:updated':
          if (data.flow_index && data.status) {
            setNodeStatus(data.flow_index as string, data.status as NodeStatus);
          }
          break;

        case 'breakpoint:hit':
          setStatus('paused');
          if (data.flow_index) {
            setCurrentInference(data.flow_index as string);
            addLog({
              flowIndex: data.flow_index as string,
              level: 'info',
              message: `Breakpoint hit at ${data.flow_index}`,
            });
          }
          break;

        case 'breakpoint:set':
          if (data.flow_index) {
            addBreakpoint(data.flow_index as string);
          }
          break;

        case 'breakpoint:cleared':
          if (data.flow_index) {
            removeBreakpoint(data.flow_index as string);
          }
          break;

        case 'log:entry':
          addLog({
            flowIndex: (data.flow_index as string) || '',
            level: (data.level as string) || 'info',
            message: (data.message as string) || '',
          });
          break;

        // Step progress events
        case 'step:started':
          if (data.flow_index) {
            const flowIndex = data.flow_index as string;
            const stepProgress: StepProgress = {
              flow_index: flowIndex,
              sequence_type: (data.sequence_type as string) || null,
              current_step: (data.step_name as string) || null,
              current_step_index: (data.step_index as number) || 0,
              total_steps: (data.total_steps as number) || 0,
              steps: (data.steps as string[]) || [],
              completed_steps: [], // Will be updated as steps complete
              paradigm: (data.paradigm as string) || null,
            };
            
            // Mark previous step as completed if updating existing progress
            updateStepProgress(flowIndex, {
              current_step: stepProgress.current_step,
              current_step_index: stepProgress.current_step_index,
              sequence_type: stepProgress.sequence_type,
              total_steps: stepProgress.total_steps,
              steps: stepProgress.steps,
              paradigm: stepProgress.paradigm,
            });
          }
          break;

        case 'step:completed':
          if (data.flow_index && data.step_name) {
            const flowIndex = data.flow_index as string;
            const stepName = data.step_name as string;
            updateStepProgress(flowIndex, {
              completed_steps: [...(useExecutionStore.getState().stepProgress[flowIndex]?.completed_steps || []), stepName],
            });
          }
          break;

        case 'sequence:started':
          if (data.flow_index) {
            const flowIndex = data.flow_index as string;
            setStepProgress(flowIndex, {
              flow_index: flowIndex,
              sequence_type: (data.sequence_type as string) || null,
              current_step: null,
              current_step_index: 0,
              total_steps: (data.total_steps as number) || 0,
              steps: (data.steps as string[]) || [],
              completed_steps: [],
            });
          }
          break;

        case 'sequence:completed':
          if (data.flow_index) {
            const flowIndex = data.flow_index as string;
            // Mark all steps as completed
            const progress = useExecutionStore.getState().stepProgress[flowIndex];
            if (progress) {
              updateStepProgress(flowIndex, {
                current_step: null,
                completed_steps: progress.steps,
              });
            }
          }
          break;

        default:
          console.log('Unknown WebSocket event:', type, data);
      }
    },
    [setStatus, setNodeStatus, setNodeStatuses, setCurrentInference, setProgress, addLog, addBreakpoint, removeBreakpoint, setRunId, reset, setStepProgress, updateStepProgress, clearStepProgress]
  );

  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Connect to WebSocket
    wsClient.connect();

    // Subscribe to events
    const unsubscribe = wsClient.subscribe((event) => {
      handleEvent(event);
      // Update connection state on any received message
      setIsConnected(true);
    });

    // Check connection state periodically
    const intervalId = setInterval(() => {
      setIsConnected(wsClient.isConnected);
    }, 1000);

    // Cleanup on unmount
    return () => {
      unsubscribe();
      clearInterval(intervalId);
      wsClient.disconnect();
    };
  }, [handleEvent]);

  return isConnected;
}

/**
 * Hook for WebSocket connection and event handling
 */

import { useEffect, useCallback, useState } from 'react';
import { wsClient } from '../services/websocket';
import { useExecutionStore } from '../stores/executionStore';
import type { WebSocketEvent } from '../types/execution';
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

        default:
          console.log('Unknown WebSocket event:', type, data);
      }
    },
    [setStatus, setNodeStatus, setCurrentInference, setProgress, addLog, addBreakpoint, removeBreakpoint, setRunId]
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

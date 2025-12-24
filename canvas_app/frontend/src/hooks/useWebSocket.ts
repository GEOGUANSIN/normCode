/**
 * Hook for WebSocket connection and event handling
 */

import { useEffect, useCallback, useState } from 'react';
import { wsClient } from '../services/websocket';
import { useExecutionStore, type UserInputRequest } from '../stores/executionStore';
import { useAgentStore } from '../stores/agentStore';
import type { WebSocketEvent, StepProgress } from '../types/execution';
import type { NodeStatus } from '../types/execution';
import type { ToolCallEvent, AgentConfig } from '../stores/agentStore';

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

  // Agent store actions
  const addToolCall = useAgentStore((s) => s.addToolCall);
  const updateToolCall = useAgentStore((s) => s.updateToolCall);
  const addAgent = useAgentStore((s) => s.addAgent);
  const updateAgent = useAgentStore((s) => s.updateAgent);
  const deleteAgent = useAgentStore((s) => s.deleteAgent);

  // User input actions
  const addUserInputRequest = useExecutionStore((s) => s.addUserInputRequest);
  const removeUserInputRequest = useExecutionStore((s) => s.removeUserInputRequest);

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
          // Update run_id if a new orchestrator was created
          if (data.run_id) {
            setRunId(data.run_id as string);
          }
          if (data.node_statuses) {
            setNodeStatuses(data.node_statuses as Record<string, NodeStatus>);
          }
          if (data.completed_count !== undefined && data.total_count !== undefined) {
            setProgress(data.completed_count as number, data.total_count as number);
          }
          // Clear step progress for fresh start
          clearStepProgress();
          addLog({
            flowIndex: '',
            level: 'info',
            message: data.run_id 
              ? `Execution reset with new run: ${data.run_id}` 
              : 'Execution reset - ready to run again',
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

        // Agent and tool call events
        case 'tool:call_started':
          addToolCall(data as unknown as ToolCallEvent);
          break;

        case 'tool:call_completed':
          // Update existing tool call or add as new
          if (data.id) {
            updateToolCall(data.id as string, data as unknown as Partial<ToolCallEvent>);
          } else {
            addToolCall(data as unknown as ToolCallEvent);
          }
          break;

        case 'tool:call_failed':
          if (data.id) {
            updateToolCall(data.id as string, data as unknown as Partial<ToolCallEvent>);
          } else {
            addToolCall(data as unknown as ToolCallEvent);
          }
          break;

        case 'agent:registered':
        case 'agent:updated':
          addAgent(data as unknown as AgentConfig);
          break;

        case 'agent:deleted':
          if (data.agent_id) {
            deleteAgent(data.agent_id as string);
          }
          break;

        // Phase 4: Modification events
        case 'value:overridden':
          if (data.concept_name && data.stale_nodes) {
            addLog({
              flowIndex: '',
              level: 'info',
              message: `Value overridden: ${data.concept_name}. ${(data.stale_nodes as string[]).length} nodes marked stale.`,
            });
            // Mark stale nodes as pending
            for (const fi of (data.stale_nodes as string[])) {
              setNodeStatus(fi, 'pending');
            }
          }
          break;

        case 'function:modified':
          if (data.flow_index && data.modified_fields) {
            addLog({
              flowIndex: data.flow_index as string,
              level: 'info',
              message: `Function modified: ${(data.modified_fields as string[]).join(', ')}`,
            });
            setNodeStatus(data.flow_index as string, 'pending');
          }
          break;

        case 'execution:partial_reset':
          if (data.reset_nodes) {
            addLog({
              flowIndex: (data.from_flow_index as string) || '',
              level: 'info',
              message: `Partial reset: ${(data.reset_nodes as string[]).length} nodes reset from ${data.from_flow_index}`,
            });
            // Mark reset nodes as pending
            for (const fi of (data.reset_nodes as string[])) {
              setNodeStatus(fi, 'pending');
            }
          }
          break;

        // User input events (human-in-the-loop)
        case 'user_input:request':
          if (data.request_id) {
            const request: UserInputRequest = {
              request_id: data.request_id as string,
              prompt: (data.prompt as string) || 'Please provide input:',
              interaction_type: (data.interaction_type as UserInputRequest['interaction_type']) || 'text_input',
              options: data.options as UserInputRequest['options'],
              created_at: data.created_at as number,
            };
            addUserInputRequest(request);
            addLog({
              flowIndex: '',
              level: 'info',
              message: `User input requested: ${request.prompt.substring(0, 50)}${request.prompt.length > 50 ? '...' : ''}`,
            });
          }
          break;

        case 'user_input:completed':
          if (data.request_id) {
            removeUserInputRequest(data.request_id as string);
            addLog({
              flowIndex: '',
              level: 'info',
              message: `User input completed: ${data.request_id}`,
            });
          }
          break;

        case 'user_input:cancelled':
          if (data.request_id) {
            removeUserInputRequest(data.request_id as string);
            addLog({
              flowIndex: '',
              level: 'warning',
              message: `User input cancelled: ${data.request_id}`,
            });
          }
          break;

        default:
          console.log('Unknown WebSocket event:', type, data);
      }
    },
    [setStatus, setNodeStatus, setNodeStatuses, setCurrentInference, setProgress, addLog, addBreakpoint, removeBreakpoint, setRunId, reset, setStepProgress, updateStepProgress, clearStepProgress, addToolCall, updateToolCall, addAgent, updateAgent, deleteAgent, addUserInputRequest, removeUserInputRequest]
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

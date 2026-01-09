/**
 * StepPipeline - Visual representation of sequence step progress
 * 
 * Shows the pipeline of steps for an inference execution with:
 * - Step abbreviations (IWI, IR, MFP, MVP, TVA, TIP, MIA, OR, OWI)
 * - Status indicators (pending, running, completed)
 * - Current step highlighting
 * - Paradigm display
 */

import { memo } from 'react';
import { CheckCircle, Circle, Loader2, Zap } from 'lucide-react';
import type { StepProgress } from '../../types/execution';
import { STEP_FULL_NAMES, STEP_DESCRIPTIONS } from '../../types/execution';

interface StepPipelineProps {
  progress: StepProgress | null;
  compact?: boolean;
}

type StepStatus = 'pending' | 'running' | 'completed';

function getStepStatus(
  stepName: string,
  currentStep: string | null,
  completedSteps: string[],
  _steps: string[]
): StepStatus {
  if (completedSteps.includes(stepName)) {
    return 'completed';
  }
  if (stepName === currentStep) {
    return 'running';
  }
  return 'pending';
}

const StepBox = memo(({ 
  stepName, 
  status, 
  isLLMStep,
  compact 
}: { 
  stepName: string; 
  status: StepStatus; 
  isLLMStep: boolean;
  compact: boolean;
}) => {
  const fullName = STEP_FULL_NAMES[stepName] || stepName;
  const description = STEP_DESCRIPTIONS[stepName] || '';
  
  const baseClasses = compact
    ? 'px-1.5 py-0.5 text-xs rounded'
    : 'px-2 py-1 text-xs rounded-md';
  
  const statusClasses = {
    pending: 'bg-slate-100 text-slate-400 border border-slate-200',
    running: 'bg-blue-100 text-blue-700 border border-blue-300 ring-2 ring-blue-200 animate-pulse',
    completed: 'bg-green-100 text-green-700 border border-green-300',
  };
  
  const StatusIcon = {
    pending: Circle,
    running: Loader2,
    completed: CheckCircle,
  }[status];
  
  return (
    <div
      className={`${baseClasses} ${statusClasses[status]} flex items-center gap-1 transition-all duration-200`}
      title={`${fullName}\n${description}`}
    >
      <StatusIcon 
        size={compact ? 10 : 12} 
        className={status === 'running' ? 'animate-spin' : ''} 
      />
      <span className="font-mono font-medium">{stepName}</span>
      {isLLMStep && status === 'running' && (
        <Zap size={10} className="text-yellow-500" />
      )}
    </div>
  );
});

StepBox.displayName = 'StepBox';

const Arrow = memo(({ compact }: { compact: boolean }) => (
  <div className={`text-slate-300 ${compact ? 'text-xs' : 'text-sm'}`}>→</div>
));

Arrow.displayName = 'Arrow';

export const StepPipeline = memo(({ progress, compact = false }: StepPipelineProps) => {
  if (!progress || !progress.steps || progress.steps.length === 0) {
    return (
      <div className="text-xs text-slate-400 italic">
        No step information available
      </div>
    );
  }
  
  const { steps, current_step, completed_steps, sequence_type, paradigm } = progress;
  
  // Steps that typically involve LLM calls
  const llmSteps = ['TVA', 'MFP'];
  
  return (
    <div className={`${compact ? 'space-y-1' : 'space-y-2'}`}>
      {/* Sequence type and paradigm header */}
      {!compact && (
        <div className="flex items-center gap-2 text-xs">
          {sequence_type && (
            <span className="bg-purple-100 text-purple-700 px-2 py-0.5 rounded font-medium">
              {sequence_type}
            </span>
          )}
          {paradigm && (
            <span className="bg-orange-100 text-orange-700 px-2 py-0.5 rounded font-mono text-[10px] truncate max-w-[200px]" title={paradigm}>
              {paradigm}
            </span>
          )}
        </div>
      )}
      
      {/* Step pipeline */}
      <div className={`flex items-center ${compact ? 'gap-1' : 'gap-1.5'} flex-wrap`}>
        {steps.map((stepName, index) => {
          const status = getStepStatus(stepName, current_step, completed_steps, steps);
          const isLLMStep = llmSteps.includes(stepName);
          
          return (
            <div key={stepName} className="flex items-center gap-1">
              <StepBox 
                stepName={stepName} 
                status={status} 
                isLLMStep={isLLMStep}
                compact={compact}
              />
              {index < steps.length - 1 && <Arrow compact={compact} />}
            </div>
          );
        })}
      </div>
      
      {/* Progress summary */}
      {!compact && (
        <div className="text-xs text-slate-500">
          Step {(progress.current_step_index || 0) + 1} of {steps.length}
          {current_step && (
            <span className="ml-2 text-slate-600">
              — {STEP_FULL_NAMES[current_step] || current_step}
            </span>
          )}
        </div>
      )}
    </div>
  );
});

StepPipeline.displayName = 'StepPipeline';

/**
 * Compact step indicator for use in log entries or inline display
 */
export const StepIndicator = memo(({ 
  stepName, 
  status = 'running' 
}: { 
  stepName: string; 
  status?: StepStatus;
}) => {
  const statusClasses = {
    pending: 'bg-slate-100 text-slate-500',
    running: 'bg-blue-100 text-blue-700',
    completed: 'bg-green-100 text-green-700',
  };
  
  return (
    <span 
      className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono font-medium ${statusClasses[status]}`}
      title={STEP_FULL_NAMES[stepName] || stepName}
    >
      {stepName}
    </span>
  );
});

StepIndicator.displayName = 'StepIndicator';

export default StepPipeline;

/**
 * ParadigmEditor - Visual editor for paradigm JSON files.
 * 
 * Features:
 * - Metadata editing (description, inputs, outputs)
 * - Tools & affordances management
 * - Vertical steps (sequence) editing
 * - Horizontal composition (data flow) editing
 * - Visual flow diagram
 */

import { useState, useCallback, useMemo } from 'react';
import {
  ChevronDown,
  ChevronRight,
  Plus,
  Trash2,
  AlertCircle,
  Settings,
  Code,
  ArrowRight,
  ArrowDown,
  Check,
  X,
  Box,
  Zap,
  FileJson,
  Layout,
  Layers,
} from 'lucide-react';
import type {
  Paradigm,
  ParsedParadigm,
  ParsedTool,
  ParsedAffordance,
  ParsedSequenceStep,
  ParsedCompositionStep,
  ParsedInput,
  ParadigmViewMode,
  ParadigmSection,
} from '../../types/paradigm';

// =============================================================================
// Types
// =============================================================================

interface ParadigmEditorProps {
  paradigm: Paradigm;
  parsed: ParsedParadigm;
  onUpdate: (paradigm: Paradigm) => void;
  onParsedUpdate: (parsed: ParsedParadigm) => void;
}

// =============================================================================
// Section Components
// =============================================================================

/**
 * Collapsible section wrapper
 */
function Section({
  title,
  icon: Icon,
  expanded,
  onToggle,
  badge,
  children,
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  expanded: boolean;
  onToggle: () => void;
  badge?: string | number;
  children: React.ReactNode;
}) {
  return (
    <div className="border rounded-lg bg-white overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center gap-3 bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        {expanded ? (
          <ChevronDown className="w-4 h-4 text-gray-500" />
        ) : (
          <ChevronRight className="w-4 h-4 text-gray-500" />
        )}
        <Icon className="w-4 h-4 text-gray-600" />
        <span className="font-medium text-gray-800">{title}</span>
        {badge !== undefined && (
          <span className="ml-auto px-2 py-0.5 text-xs bg-gray-200 text-gray-600 rounded-full">
            {badge}
          </span>
        )}
      </button>
      {expanded && <div className="p-4 border-t">{children}</div>}
    </div>
  );
}

/**
 * Editable text field with inline editing
 */
function EditableField({
  value,
  onChange,
  placeholder,
  multiline = false,
  className = '',
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  multiline?: boolean;
  className?: string;
}) {
  const [editing, setEditing] = useState(false);
  const [localValue, setLocalValue] = useState(value);

  const handleSave = () => {
    onChange(localValue);
    setEditing(false);
  };

  const handleCancel = () => {
    setLocalValue(value);
    setEditing(false);
  };

  if (editing) {
    return (
      <div className="flex items-start gap-2">
        {multiline ? (
          <textarea
            value={localValue}
            onChange={(e) => setLocalValue(e.target.value)}
            className={`flex-1 px-2 py-1 border rounded text-sm focus:outline-none focus:border-blue-500 ${className}`}
            rows={3}
            autoFocus
          />
        ) : (
          <input
            type="text"
            value={localValue}
            onChange={(e) => setLocalValue(e.target.value)}
            className={`flex-1 px-2 py-1 border rounded text-sm focus:outline-none focus:border-blue-500 ${className}`}
            autoFocus
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSave();
              if (e.key === 'Escape') handleCancel();
            }}
          />
        )}
        <button onClick={handleSave} className="p-1 text-green-600 hover:bg-green-50 rounded">
          <Check className="w-4 h-4" />
        </button>
        <button onClick={handleCancel} className="p-1 text-gray-500 hover:bg-gray-100 rounded">
          <X className="w-4 h-4" />
        </button>
      </div>
    );
  }

  return (
    <div
      onClick={() => {
        setLocalValue(value);
        setEditing(true);
      }}
      className={`px-2 py-1 rounded cursor-pointer hover:bg-gray-100 ${className} ${
        !value ? 'text-gray-400 italic' : ''
      }`}
    >
      {value || placeholder || 'Click to edit'}
    </div>
  );
}

// =============================================================================
// Metadata Section
// =============================================================================

function MetadataSection({
  parsed,
  onUpdate,
}: {
  parsed: ParsedParadigm;
  onUpdate: (updates: Partial<ParsedParadigm>) => void;
}) {
  const handleInputUpdate = useCallback((index: number, field: keyof ParsedInput, value: string) => {
    const newInputs = [...parsed.inputs];
    newInputs[index] = { ...newInputs[index], [field]: value };
    onUpdate({ inputs: newInputs });
  }, [parsed.inputs, onUpdate]);

  const handleAddInput = useCallback((type: 'vertical' | 'horizontal') => {
    const newInputs = [
      ...parsed.inputs,
      { name: `new_${type}_input`, description: '', type }
    ];
    onUpdate({ inputs: newInputs });
  }, [parsed.inputs, onUpdate]);

  const handleDeleteInput = useCallback((index: number) => {
    const newInputs = parsed.inputs.filter((_, i) => i !== index);
    onUpdate({ inputs: newInputs });
  }, [parsed.inputs, onUpdate]);

  const verticalInputs = parsed.inputs.filter(i => i.type === 'vertical');
  const horizontalInputs = parsed.inputs.filter(i => i.type === 'horizontal');

  return (
    <div className="space-y-4">
      {/* Description */}
      <div>
        <label className="text-xs font-medium text-gray-500 uppercase">Description</label>
        <EditableField
          value={parsed.description}
          onChange={(v) => onUpdate({ description: v })}
          placeholder="Enter paradigm description..."
          multiline
          className="text-sm text-gray-700"
        />
      </div>

      {/* Vertical Inputs */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <label className="text-xs font-medium text-gray-500 uppercase">
            Vertical Inputs (v_)
          </label>
          <span className="text-[10px] text-gray-400">Composition-time inputs from agent state</span>
          <button
            onClick={() => handleAddInput('vertical')}
            className="ml-auto p-1 text-blue-600 hover:bg-blue-50 rounded"
          >
            <Plus className="w-3 h-3" />
          </button>
        </div>
        {verticalInputs.length === 0 ? (
          <div className="text-xs text-gray-400 italic px-2">No vertical inputs</div>
        ) : (
          <div className="space-y-1">
            {verticalInputs.map((inp, idx) => {
              const globalIdx = parsed.inputs.findIndex(i => i === inp);
              return (
                <div key={idx} className="flex items-center gap-2 group">
                  <span className="text-blue-600 text-xs font-mono">v_</span>
                  <EditableField
                    value={inp.name}
                    onChange={(v) => handleInputUpdate(globalIdx, 'name', v)}
                    className="flex-1 font-mono text-sm"
                  />
                  <EditableField
                    value={inp.description}
                    onChange={(v) => handleInputUpdate(globalIdx, 'description', v)}
                    placeholder="Description..."
                    className="flex-[2] text-sm text-gray-600"
                  />
                  <button
                    onClick={() => handleDeleteInput(globalIdx)}
                    className="p-1 text-red-500 opacity-0 group-hover:opacity-100 hover:bg-red-50 rounded"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Horizontal Inputs */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <label className="text-xs font-medium text-gray-500 uppercase">
            Horizontal Inputs (h_)
          </label>
          <span className="text-[10px] text-gray-400">Runtime inputs passed at invocation</span>
          <button
            onClick={() => handleAddInput('horizontal')}
            className="ml-auto p-1 text-green-600 hover:bg-green-50 rounded"
          >
            <Plus className="w-3 h-3" />
          </button>
        </div>
        {horizontalInputs.length === 0 ? (
          <div className="text-xs text-gray-400 italic px-2">No horizontal inputs</div>
        ) : (
          <div className="space-y-1">
            {horizontalInputs.map((inp, idx) => {
              const globalIdx = parsed.inputs.findIndex(i => i === inp);
              return (
                <div key={idx} className="flex items-center gap-2 group">
                  <span className="text-green-600 text-xs font-mono">h_</span>
                  <EditableField
                    value={inp.name}
                    onChange={(v) => handleInputUpdate(globalIdx, 'name', v)}
                    className="flex-1 font-mono text-sm"
                  />
                  <EditableField
                    value={inp.description}
                    onChange={(v) => handleInputUpdate(globalIdx, 'description', v)}
                    placeholder="Description..."
                    className="flex-[2] text-sm text-gray-600"
                  />
                  <button
                    onClick={() => handleDeleteInput(globalIdx)}
                    className="p-1 text-red-500 opacity-0 group-hover:opacity-100 hover:bg-red-50 rounded"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Output */}
      <div>
        <label className="text-xs font-medium text-gray-500 uppercase">Output (o_)</label>
        <div className="flex items-center gap-2">
          <span className="text-purple-600 text-xs font-mono">o_</span>
          <EditableField
            value={parsed.output_type}
            onChange={(v) => onUpdate({ output_type: v })}
            placeholder="Output type..."
            className="flex-1 font-mono text-sm"
          />
          <EditableField
            value={parsed.output_description}
            onChange={(v) => onUpdate({ output_description: v })}
            placeholder="Description..."
            className="flex-[2] text-sm text-gray-600"
          />
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Tools Section
// =============================================================================

function ToolsSection({
  tools,
  onUpdate,
}: {
  tools: ParsedTool[];
  onUpdate: (tools: ParsedTool[]) => void;
}) {
  const [expandedTools, setExpandedTools] = useState<Set<number>>(new Set([0]));

  const toggleTool = useCallback((idx: number) => {
    setExpandedTools(prev => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  }, []);

  const handleAddTool = useCallback(() => {
    const newTool: ParsedTool = {
      index: tools.length,
      tool_name: 'new_tool',
      affordances: [],
    };
    onUpdate([...tools, newTool]);
    setExpandedTools(prev => new Set(prev).add(tools.length));
  }, [tools, onUpdate]);

  const handleDeleteTool = useCallback((idx: number) => {
    onUpdate(tools.filter((_, i) => i !== idx).map((t, i) => ({ ...t, index: i })));
  }, [tools, onUpdate]);

  const handleToolNameChange = useCallback((idx: number, name: string) => {
    const newTools = [...tools];
    newTools[idx] = { ...newTools[idx], tool_name: name };
    // Update affordances with new tool name
    newTools[idx].affordances = newTools[idx].affordances.map(a => ({
      ...a,
      tool_name: name,
      full_id: `${name}.${a.affordance_name}`,
    }));
    onUpdate(newTools);
  }, [tools, onUpdate]);

  const handleAddAffordance = useCallback((toolIdx: number) => {
    const tool = tools[toolIdx];
    const newAff: ParsedAffordance = {
      index: tool.affordances.length,
      tool_name: tool.tool_name,
      affordance_name: 'new_affordance',
      call_code: 'result = tool.method()',
      full_id: `${tool.tool_name}.new_affordance`,
    };
    const newTools = [...tools];
    newTools[toolIdx] = {
      ...tool,
      affordances: [...tool.affordances, newAff],
    };
    onUpdate(newTools);
  }, [tools, onUpdate]);

  const handleDeleteAffordance = useCallback((toolIdx: number, affIdx: number) => {
    const newTools = [...tools];
    newTools[toolIdx] = {
      ...newTools[toolIdx],
      affordances: newTools[toolIdx].affordances.filter((_, i) => i !== affIdx),
    };
    onUpdate(newTools);
  }, [tools, onUpdate]);

  const handleAffordanceUpdate = useCallback(
    (toolIdx: number, affIdx: number, field: keyof ParsedAffordance, value: string) => {
      const newTools = [...tools];
      const tool = newTools[toolIdx];
      const newAffs = [...tool.affordances];
      newAffs[affIdx] = {
        ...newAffs[affIdx],
        [field]: value,
        full_id: field === 'affordance_name'
          ? `${tool.tool_name}.${value}`
          : newAffs[affIdx].full_id,
      };
      newTools[toolIdx] = { ...tool, affordances: newAffs };
      onUpdate(newTools);
    },
    [tools, onUpdate]
  );

  return (
    <div className="space-y-2">
      {tools.map((tool, toolIdx) => (
        <div key={toolIdx} className="border rounded">
          {/* Tool header */}
          <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 group">
            <button onClick={() => toggleTool(toolIdx)} className="p-0.5">
              {expandedTools.has(toolIdx) ? (
                <ChevronDown className="w-4 h-4 text-gray-500" />
              ) : (
                <ChevronRight className="w-4 h-4 text-gray-500" />
              )}
            </button>
            <Box className="w-4 h-4 text-blue-500" />
            <EditableField
              value={tool.tool_name}
              onChange={(v) => handleToolNameChange(toolIdx, v)}
              className="font-mono text-sm font-medium"
            />
            <span className="text-xs text-gray-400">
              {tool.affordances.length} affordance{tool.affordances.length !== 1 ? 's' : ''}
            </span>
            <button
              onClick={() => handleAddAffordance(toolIdx)}
              className="ml-auto p-1 text-green-600 hover:bg-green-50 rounded opacity-0 group-hover:opacity-100"
              title="Add affordance"
            >
              <Plus className="w-3 h-3" />
            </button>
            <button
              onClick={() => handleDeleteTool(toolIdx)}
              className="p-1 text-red-500 hover:bg-red-50 rounded opacity-0 group-hover:opacity-100"
              title="Delete tool"
            >
              <Trash2 className="w-3 h-3" />
            </button>
          </div>
          
          {/* Affordances */}
          {expandedTools.has(toolIdx) && (
            <div className="px-3 py-2 space-y-2 border-t bg-white">
              {tool.affordances.length === 0 ? (
                <div className="text-xs text-gray-400 italic">No affordances defined</div>
              ) : (
                tool.affordances.map((aff, affIdx) => (
                  <div key={affIdx} className="flex items-start gap-2 group pl-4">
                    <Zap className="w-3 h-3 text-amber-500 mt-1 flex-shrink-0" />
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center gap-2">
                        <EditableField
                          value={aff.affordance_name}
                          onChange={(v) => handleAffordanceUpdate(toolIdx, affIdx, 'affordance_name', v)}
                          className="font-mono text-sm"
                        />
                        <span className="text-xs text-gray-400 font-mono">{aff.full_id}</span>
                      </div>
                      <EditableField
                        value={aff.call_code}
                        onChange={(v) => handleAffordanceUpdate(toolIdx, affIdx, 'call_code', v)}
                        className="font-mono text-xs text-gray-600 bg-gray-50"
                        placeholder="result = tool.method()"
                      />
                    </div>
                    <button
                      onClick={() => handleDeleteAffordance(toolIdx, affIdx)}
                      className="p-1 text-red-500 hover:bg-red-50 rounded opacity-0 group-hover:opacity-100"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      ))}

      <button
        onClick={handleAddTool}
        className="w-full py-2 border-2 border-dashed rounded text-sm text-gray-500 hover:text-blue-600 hover:border-blue-300 transition-colors flex items-center justify-center gap-2"
      >
        <Plus className="w-4 h-4" />
        Add Tool
      </button>
    </div>
  );
}

// =============================================================================
// Sequence Steps Section (Vertical)
// =============================================================================

function SequenceStepsSection({
  steps,
  allAffordances,
  onUpdate,
  onSelectStep,
  selectedStepIndex,
}: {
  steps: ParsedSequenceStep[];
  allAffordances: ParsedAffordance[];
  onUpdate: (steps: ParsedSequenceStep[]) => void;
  onSelectStep: (index: number | null) => void;
  selectedStepIndex: number | null;
}) {
  const handleAddStep = useCallback(() => {
    const newStep: ParsedSequenceStep = {
      index: steps.length,
      step_index: steps.length + 1,
      affordance: allAffordances[0]?.full_id || '',
      tool_name: allAffordances[0]?.tool_name || '',
      affordance_name: allAffordances[0]?.affordance_name || '',
      params: {},
      result_key: `result_${steps.length + 1}`,
      has_composition_plan: false,
      composition_steps: [],
    };
    onUpdate([...steps, newStep]);
  }, [steps, allAffordances, onUpdate]);

  const handleDeleteStep = useCallback((idx: number) => {
    onUpdate(
      steps
        .filter((_, i) => i !== idx)
        .map((s, i) => ({ ...s, index: i, step_index: i + 1 }))
    );
  }, [steps, onUpdate]);

  const handleStepUpdate = useCallback(
    (idx: number, field: keyof ParsedSequenceStep, value: unknown) => {
      const newSteps = [...steps];
      newSteps[idx] = { ...newSteps[idx], [field]: value };
      
      // If affordance changed, update tool_name and affordance_name
      if (field === 'affordance' && typeof value === 'string') {
        const parts = value.split('.');
        newSteps[idx].tool_name = parts[0] || '';
        newSteps[idx].affordance_name = parts[1] || '';
      }
      
      onUpdate(newSteps);
    },
    [steps, onUpdate]
  );

  return (
    <div className="space-y-2">
      {steps.map((step, idx) => (
        <div
          key={idx}
          onClick={() => onSelectStep(idx)}
          className={`border rounded p-3 cursor-pointer transition-colors ${
            selectedStepIndex === idx
              ? 'border-blue-500 bg-blue-50'
              : 'hover:border-gray-300'
          }`}
        >
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-6 h-6 rounded-full bg-gray-200 text-xs font-medium">
              {step.step_index}
            </div>
            
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <select
                  value={step.affordance}
                  onChange={(e) => handleStepUpdate(idx, 'affordance', e.target.value)}
                  onClick={(e) => e.stopPropagation()}
                  className="px-2 py-1 text-sm font-mono border rounded bg-white"
                >
                  {allAffordances.map((aff) => (
                    <option key={aff.full_id} value={aff.full_id}>
                      {aff.full_id}
                    </option>
                  ))}
                </select>
                
                <ArrowRight className="w-4 h-4 text-gray-400" />
                
                <EditableField
                  value={step.result_key}
                  onChange={(v) => handleStepUpdate(idx, 'result_key', v)}
                  className="font-mono text-sm text-blue-600"
                />
              </div>
              
              {step.has_composition_plan && (
                <div className="mt-2 flex items-center gap-1 text-xs text-purple-600">
                  <Layers className="w-3 h-3" />
                  Contains composition plan with {step.composition_steps.length} steps
                </div>
              )}
            </div>
            
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleDeleteStep(idx);
              }}
              className="p-1 text-red-500 hover:bg-red-50 rounded opacity-0 group-hover:opacity-100"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      ))}

      <button
        onClick={handleAddStep}
        className="w-full py-2 border-2 border-dashed rounded text-sm text-gray-500 hover:text-blue-600 hover:border-blue-300 transition-colors flex items-center justify-center gap-2"
      >
        <Plus className="w-4 h-4" />
        Add Step
      </button>
    </div>
  );
}

// =============================================================================
// Composition Steps Section (Horizontal)
// =============================================================================

function CompositionStepsSection({
  steps,
  parentStep,
  resultKeys,
  onUpdate,
}: {
  steps: ParsedCompositionStep[];
  parentStep: ParsedSequenceStep | null;
  resultKeys: string[];
  onUpdate: (steps: ParsedCompositionStep[]) => void;
}) {
  const handleAddStep = useCallback(() => {
    const newStep: ParsedCompositionStep = {
      index: steps.length,
      output_key: `output_${steps.length + 1}`,
      function_ref: resultKeys[0] || '',
      params: [],
    };
    onUpdate([...steps, newStep]);
  }, [steps, resultKeys, onUpdate]);

  const handleDeleteStep = useCallback((idx: number) => {
    onUpdate(steps.filter((_, i) => i !== idx).map((s, i) => ({ ...s, index: i })));
  }, [steps, onUpdate]);

  const handleStepUpdate = useCallback(
    (idx: number, field: keyof ParsedCompositionStep, value: unknown) => {
      const newSteps = [...steps];
      newSteps[idx] = { ...newSteps[idx], [field]: value };
      onUpdate(newSteps);
    },
    [steps, onUpdate]
  );

  const handleAddParam = useCallback((stepIdx: number) => {
    const newSteps = [...steps];
    newSteps[stepIdx] = {
      ...newSteps[stepIdx],
      params: [...newSteps[stepIdx].params, { name: 'param', value: '', is_literal: false }],
    };
    onUpdate(newSteps);
  }, [steps, onUpdate]);

  const handleParamUpdate = useCallback(
    (stepIdx: number, paramIdx: number, field: string, value: string | boolean) => {
      const newSteps = [...steps];
      const newParams = [...newSteps[stepIdx].params];
      newParams[paramIdx] = { ...newParams[paramIdx], [field]: value };
      newSteps[stepIdx] = { ...newSteps[stepIdx], params: newParams };
      onUpdate(newSteps);
    },
    [steps, onUpdate]
  );

  const handleDeleteParam = useCallback((stepIdx: number, paramIdx: number) => {
    const newSteps = [...steps];
    newSteps[stepIdx] = {
      ...newSteps[stepIdx],
      params: newSteps[stepIdx].params.filter((_, i) => i !== paramIdx),
    };
    onUpdate(newSteps);
  }, [steps, onUpdate]);

  if (!parentStep) {
    return (
      <div className="text-center py-8 text-gray-500">
        <Layers className="w-12 h-12 mx-auto mb-3 opacity-30" />
        <p>Select a step with a composition plan to edit</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="text-xs text-gray-500 mb-2">
        Composition plan for step {parentStep.step_index} ({parentStep.affordance})
      </div>

      {steps.map((step, idx) => (
        <div key={idx} className="border rounded p-3 bg-white group">
          <div className="flex items-start gap-3">
            {/* Step number */}
            <div className="flex items-center justify-center w-5 h-5 rounded bg-purple-100 text-purple-700 text-xs font-medium flex-shrink-0 mt-1">
              {idx + 1}
            </div>

            <div className="flex-1 space-y-2">
              {/* Function and output */}
              <div className="flex items-center gap-2 flex-wrap">
                <select
                  value={step.function_ref}
                  onChange={(e) => handleStepUpdate(idx, 'function_ref', e.target.value)}
                  className="px-2 py-1 text-sm font-mono border rounded bg-gray-50"
                >
                  <option value="__initial_input__">__initial_input__</option>
                  {resultKeys.map((key) => (
                    <option key={key} value={key}>{key}</option>
                  ))}
                </select>
                <span className="text-gray-400">(</span>
                <span className="text-gray-400">...)</span>
                <ArrowRight className="w-4 h-4 text-gray-400" />
                <EditableField
                  value={step.output_key}
                  onChange={(v) => handleStepUpdate(idx, 'output_key', v)}
                  className="font-mono text-sm text-purple-600 font-medium"
                />
              </div>

              {/* Parameters */}
              <div className="pl-4 space-y-1">
                {step.params.map((param, pIdx) => (
                  <div key={pIdx} className="flex items-center gap-2 text-sm">
                    <EditableField
                      value={param.name}
                      onChange={(v) => handleParamUpdate(idx, pIdx, 'name', v)}
                      className="font-mono text-gray-600"
                    />
                    <span className="text-gray-400">=</span>
                    {param.is_literal ? (
                      <EditableField
                        value={param.value}
                        onChange={(v) => handleParamUpdate(idx, pIdx, 'value', v)}
                        className="font-mono text-amber-600"
                      />
                    ) : (
                      <select
                        value={param.value}
                        onChange={(e) => handleParamUpdate(idx, pIdx, 'value', e.target.value)}
                        className="px-2 py-0.5 text-xs font-mono border rounded bg-white"
                      >
                        <option value="__initial_input__">__initial_input__</option>
                        <option value="__positional__">__positional__</option>
                        {steps.slice(0, idx).map((s) => (
                          <option key={s.output_key} value={s.output_key}>{s.output_key}</option>
                        ))}
                      </select>
                    )}
                    <button
                      onClick={() => handleParamUpdate(idx, pIdx, 'is_literal', !param.is_literal)}
                      className={`px-1.5 py-0.5 text-[10px] rounded ${
                        param.is_literal
                          ? 'bg-amber-100 text-amber-700'
                          : 'bg-gray-100 text-gray-600'
                      }`}
                      title={param.is_literal ? 'Literal value' : 'Variable reference'}
                    >
                      {param.is_literal ? 'LIT' : 'VAR'}
                    </button>
                    <button
                      onClick={() => handleDeleteParam(idx, pIdx)}
                      className="p-0.5 text-red-500 hover:bg-red-50 rounded opacity-0 group-hover:opacity-100"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
                <button
                  onClick={() => handleAddParam(idx)}
                  className="text-xs text-gray-500 hover:text-blue-600 flex items-center gap-1"
                >
                  <Plus className="w-3 h-3" />
                  Add parameter
                </button>
              </div>
            </div>

            <button
              onClick={() => handleDeleteStep(idx)}
              className="p-1 text-red-500 hover:bg-red-50 rounded opacity-0 group-hover:opacity-100"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      ))}

      <button
        onClick={handleAddStep}
        className="w-full py-2 border-2 border-dashed rounded text-sm text-gray-500 hover:text-purple-600 hover:border-purple-300 transition-colors flex items-center justify-center gap-2"
      >
        <Plus className="w-4 h-4" />
        Add Composition Step
      </button>
    </div>
  );
}

// =============================================================================
// Flow Diagram View
// =============================================================================

function FlowDiagramView({ parsed }: { parsed: ParsedParadigm }) {
  return (
    <div className="p-4 overflow-auto">
      <div className="inline-block min-w-full">
        {/* Vertical Steps */}
        <div className="flex flex-col items-center gap-2">
          {parsed.steps.map((step, idx) => (
            <div key={idx} className="flex flex-col items-center">
              {/* Step box */}
              <div className={`px-4 py-2 rounded-lg border-2 ${
                step.has_composition_plan
                  ? 'border-purple-500 bg-purple-50'
                  : 'border-blue-500 bg-blue-50'
              }`}>
                <div className="text-xs text-gray-500">Step {step.step_index}</div>
                <div className="font-mono text-sm">{step.affordance}</div>
                <div className="text-xs text-blue-600 font-mono">→ {step.result_key}</div>
              </div>
              
              {/* Arrow to next step */}
              {idx < parsed.steps.length - 1 && (
                <ArrowDown className="w-5 h-5 text-gray-400 my-1" />
              )}
              
              {/* Composition plan (inline) */}
              {step.has_composition_plan && step.composition_steps.length > 0 && (
                <div className="ml-8 mt-2 mb-2 border-l-2 border-purple-300 pl-4">
                  <div className="text-xs text-purple-600 font-medium mb-2">Composition Plan:</div>
                  <div className="flex flex-wrap gap-2">
                    {step.composition_steps.map((comp, cIdx) => (
                      <div
                        key={cIdx}
                        className="px-3 py-1.5 bg-white border border-purple-200 rounded shadow-sm"
                      >
                        <div className="text-[10px] text-gray-500">{comp.function_ref}(...)</div>
                        <div className="text-sm font-mono text-purple-700">{comp.output_key}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export function ParadigmEditor({
  paradigm,
  parsed,
  onUpdate: _onUpdate,
  onParsedUpdate,
}: ParadigmEditorProps) {
  const [viewMode, setViewMode] = useState<ParadigmViewMode>('visual');
  const [expandedSections, setExpandedSections] = useState<Set<ParadigmSection>>(
    new Set(['metadata', 'steps'])
  );
  const [selectedStepIndex, setSelectedStepIndex] = useState<number | null>(null);

  const toggleSection = useCallback((section: ParadigmSection) => {
    setExpandedSections(prev => {
      const next = new Set(prev);
      if (next.has(section)) next.delete(section);
      else next.add(section);
      return next;
    });
  }, []);

  // Handle parsed updates
  const handleParsedUpdate = useCallback((updates: Partial<ParsedParadigm>) => {
    onParsedUpdate({ ...parsed, ...updates });
  }, [parsed, onParsedUpdate]);

  // Get result keys for composition step references
  const resultKeys = useMemo(() => {
    return parsed.steps.map(s => s.result_key);
  }, [parsed.steps]);

  // Get selected step for composition editing
  const selectedStep = useMemo(() => {
    if (selectedStepIndex === null) return null;
    return parsed.steps[selectedStepIndex] || null;
  }, [parsed.steps, selectedStepIndex]);

  // Handle composition steps update
  const handleCompositionUpdate = useCallback((compSteps: ParsedCompositionStep[]) => {
    if (selectedStepIndex === null) return;
    
    const newSteps = [...parsed.steps];
    newSteps[selectedStepIndex] = {
      ...newSteps[selectedStepIndex],
      composition_steps: compSteps,
      has_composition_plan: compSteps.length > 0,
    };
    handleParsedUpdate({ steps: newSteps });
  }, [parsed.steps, selectedStepIndex, handleParsedUpdate]);

  return (
    <div className="h-full flex flex-col bg-gray-100">
      {/* Toolbar */}
      <div className="bg-white border-b px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileJson className="w-5 h-5 text-purple-600" />
          <span className="font-medium">Paradigm Editor</span>
        </div>
        
        <div className="flex items-center bg-gray-100 rounded p-1">
          <button
            onClick={() => setViewMode('visual')}
            className={`px-3 py-1 text-sm rounded ${
              viewMode === 'visual'
                ? 'bg-white shadow text-blue-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            <Layout className="w-4 h-4 inline mr-1" />
            Visual
          </button>
          <button
            onClick={() => setViewMode('flow')}
            className={`px-3 py-1 text-sm rounded ${
              viewMode === 'flow'
                ? 'bg-white shadow text-blue-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            <Layers className="w-4 h-4 inline mr-1" />
            Flow
          </button>
          <button
            onClick={() => setViewMode('json')}
            className={`px-3 py-1 text-sm rounded ${
              viewMode === 'json'
                ? 'bg-white shadow text-blue-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            <Code className="w-4 h-4 inline mr-1" />
            JSON
          </button>
        </div>
      </div>

      {/* Validation Messages */}
      {(parsed.errors.length > 0 || parsed.warnings.length > 0) && (
        <div className="px-4 py-2 bg-yellow-50 border-b border-yellow-200">
          {parsed.errors.map((err, i) => (
            <div key={i} className="flex items-center gap-2 text-sm text-red-600">
              <AlertCircle className="w-4 h-4" />
              {err}
            </div>
          ))}
          {parsed.warnings.map((warn, i) => (
            <div key={i} className="flex items-center gap-2 text-sm text-yellow-700">
              <AlertCircle className="w-4 h-4" />
              {warn}
            </div>
          ))}
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {viewMode === 'visual' && (
          <div className="p-4 space-y-3">
            {/* Metadata Section */}
            <Section
              title="Metadata"
              icon={Settings}
              expanded={expandedSections.has('metadata')}
              onToggle={() => toggleSection('metadata')}
              badge={parsed.inputs.length}
            >
              <MetadataSection parsed={parsed} onUpdate={handleParsedUpdate} />
            </Section>

            {/* Tools Section */}
            <Section
              title="Tools & Affordances"
              icon={Box}
              expanded={expandedSections.has('tools')}
              onToggle={() => toggleSection('tools')}
              badge={parsed.tools.length}
            >
              <ToolsSection
                tools={parsed.tools}
                onUpdate={(tools) => handleParsedUpdate({ tools, all_affordances: tools.flatMap(t => t.affordances) })}
              />
            </Section>

            {/* Sequence Steps Section */}
            <Section
              title="Sequence Steps (Vertical)"
              icon={ArrowDown}
              expanded={expandedSections.has('steps')}
              onToggle={() => toggleSection('steps')}
              badge={parsed.steps.length}
            >
              <SequenceStepsSection
                steps={parsed.steps}
                allAffordances={parsed.all_affordances}
                onUpdate={(steps) => handleParsedUpdate({ steps })}
                onSelectStep={setSelectedStepIndex}
                selectedStepIndex={selectedStepIndex}
              />
            </Section>

            {/* Composition Steps Section */}
            <Section
              title="Composition Plan (Horizontal)"
              icon={ArrowRight}
              expanded={expandedSections.has('composition')}
              onToggle={() => toggleSection('composition')}
              badge={selectedStep?.composition_steps.length}
            >
              <CompositionStepsSection
                steps={selectedStep?.composition_steps || []}
                parentStep={selectedStep}
                resultKeys={resultKeys}
                onUpdate={handleCompositionUpdate}
              />
            </Section>
          </div>
        )}

        {viewMode === 'flow' && <FlowDiagramView parsed={parsed} />}

        {viewMode === 'json' && (
          <div className="p-4">
            <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-auto text-sm font-mono">
              {JSON.stringify(paradigm, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

export default ParadigmEditor;


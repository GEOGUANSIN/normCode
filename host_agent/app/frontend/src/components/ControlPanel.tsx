import React from 'react';
import styled from 'styled-components';
import { nodeColors } from '../config';
import { ControlPanelProps } from '../types';

const Panel = styled.div`
  position: absolute;
  top: 20px;
  left: 20px;
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  z-index: 5;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 300px;
`;

const Title = styled.h2`
  margin: 0;
  font-size: 18px;
  color: #2c3e50;
`;

const InputGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

const Label = styled.label`
  font-size: 14px;
  color: #34495e;
  font-weight: 500;
`;

const Input = styled.input`
  padding: 8px 12px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;

  &:focus {
    outline: none;
    border-color: #3498db;
  }
`;

const Select = styled.select`
  padding: 8px 12px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;
  cursor: pointer;

  &:focus {
    outline: none;
    border-color: #3498db;
  }
`;

const ColorOption = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
`;

const ColorDot = styled.div<{ color: string }>`
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: ${props => props.color};
  border: 1px solid rgba(0, 0, 0, 0.1);
`;

const Button = styled.button<{ $primary?: boolean }>`
  padding: 10px 16px;
  background: ${props => props.$primary ? '#3498db' : '#e0e0e0'};
  color: ${props => props.$primary ? 'white' : '#2c3e50'};
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    background: ${props => props.$primary ? '#2980b9' : '#d0d0d0'};
    transform: translateY(-1px);
  }

  &:active {
    transform: translateY(0);
  }
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 8px;
`;

const SaveStatus = styled.div<{ hasUnsavedChanges: boolean; isSaving: boolean }>`
  font-size: 14px;
  color: ${props => {
    if (props.isSaving) return '#3498db';
    return props.hasUnsavedChanges ? '#e74c3c' : '#27ae60';
  }};
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
`;

const StatusDot = styled.div<{ hasUnsavedChanges: boolean; isSaving: boolean }>`
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: ${props => {
    if (props.isSaving) return '#3498db';
    return props.hasUnsavedChanges ? '#e74c3c' : '#27ae60';
  }};
`;

const ToggleSwitch = styled.label`
  position: relative;
  display: inline-block;
  width: 50px;
  height: 24px;
  margin-left: 8px;
`;

const ToggleInput = styled.input`
  opacity: 0;
  width: 0;
  height: 0;

  &:checked + span {
    background-color: #3498db;
  }

  &:checked + span:before {
    transform: translateX(26px);
  }
`;

const ToggleSlider = styled.span`
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: .4s;
  border-radius: 24px;

  &:before {
    position: absolute;
    content: "";
    height: 16px;
    width: 16px;
    left: 4px;
    bottom: 4px;
    background-color: white;
    transition: .4s;
    border-radius: 50%;
  }
`;

const ToggleContainer = styled.div`
  display: flex;
  align-items: center;
  margin-top: 8px;
`;

const ControlPanel: React.FC<ControlPanelProps> = ({
  newNodeType,
  setNewNodeType,
  newNodeLabel,
  setNewNodeLabel,
  addNewNode,
  saveGraph,
  loadGraph,
  hasUnsavedChanges,
  autoSave,
  setAutoSave,
  edgeStyleType,
  setEdgeStyleType,
  isSaving
}) => {
  const handleSave = async () => {
    await saveGraph();
  };

  return (
    <Panel>
      <Title>Flow Graph Controls</Title>
      <InputGroup>
        <Label>Node Label</Label>
        <Input
          type="text"
          value={newNodeLabel}
          onChange={(e) => setNewNodeLabel(e.target.value)}
          placeholder="Enter node label"
        />
      </InputGroup>
      <InputGroup>
        <Label>Node Type</Label>
        <Select value={newNodeType} onChange={(e) => setNewNodeType(e.target.value)}>
          {Object.keys(nodeColors).map((type) => (
            <option key={type} value={type}>
              {type.charAt(0).toUpperCase() + type.slice(1)} Node
            </option>
          ))}
        </Select>
        <div style={{ marginTop: '8px', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {Object.entries(nodeColors).map(([type, color]) => (
            <ColorOption key={type}>
              <ColorDot color={color} />
              <span style={{ fontSize: '12px', color: '#34495e' }}>
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </span>
            </ColorOption>
          ))}
        </div>
      </InputGroup>
      <InputGroup>
        <Label>Edge Type</Label>
        <Select value={edgeStyleType} onChange={(e) => setEdgeStyleType(e.target.value as 'solid' | 'dashed')}>
          <option value="solid">Solid Line</option>
          <option value="dashed">Dashed Line</option>
        </Select>
      </InputGroup>
      <ButtonGroup>
        <Button onClick={addNewNode} $primary>Add Node</Button>
        <Button onClick={handleSave} $primary disabled={isSaving}>
          {isSaving ? 'Saving...' : 'Save'}
        </Button>
        <Button onClick={loadGraph}>Load</Button>
      </ButtonGroup>
      <SaveStatus hasUnsavedChanges={hasUnsavedChanges} isSaving={isSaving}>
        <StatusDot hasUnsavedChanges={hasUnsavedChanges} isSaving={isSaving} />
        {isSaving ? 'Saving changes...' : hasUnsavedChanges ? 'Unsaved changes' : 'All changes saved'}
      </SaveStatus>
      <ToggleContainer>
        <Label>Auto-save</Label>
        <ToggleSwitch>
          <ToggleInput
            type="checkbox"
            checked={autoSave}
            onChange={(e) => setAutoSave(e.target.checked)}
          />
          <ToggleSlider />
        </ToggleSwitch>
      </ToggleContainer>
    </Panel>
  );
};

export default ControlPanel; 
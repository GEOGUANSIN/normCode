import React, { useState, useContext } from 'react';
import { Handle, Position } from 'reactflow';
import { NodeContext } from '../../context/NodeContext';
import { API_BASE_URL } from '../../config';
import {
  NodeContainer,
  NodeWrapper,
  NodeInput,
  EditButton,
  DeleteButton
} from './NodeStyles';

const CustomNode = React.memo(({ data, color, id }) => {
  const { nodes, setNodes, setEdges } = useContext(NodeContext);
  const [isEditing, setIsEditing] = useState(false);
  const [inputValue, setInputValue] = useState(data.label);

  const startEditing = (e) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    setIsEditing(true);
  };

  const handleInputChange = (e) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    setInputValue(e.target.value);
  };

  const saveChanges = async () => {
    if (inputValue.trim() === '') {
      setInputValue(data.label);
      setIsEditing(false);
      return;
    }

    const updatedNode = {
      ...nodes.find(n => n.id === id),
      data: {
        ...data,
        label: inputValue,
      },
    };

    try {
      const response = await fetch(`${API_BASE_URL}/nodes/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updatedNode),
      });

      if (response.ok) {
        setNodes((nds) =>
          nds.map((node) => {
            if (node.id === id) {
              return updatedNode;
            }
            return node;
          })
        );
        setIsEditing(false);
      }
    } catch (error) {
      console.error('Error updating node:', error);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      saveChanges();
    } else if (e.key === 'Escape') {
      setInputValue(data.label);
      setIsEditing(false);
    }
  };

  const handleBlur = () => {
    saveChanges();
  };

  const deleteNode = async (e) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    
    try {
      await fetch(`${API_BASE_URL}/nodes/${id}`, {
        method: 'DELETE',
      });
      
      setNodes((nds) => nds.filter((node) => node.id !== id));
      setEdges((eds) => eds.filter((edge) => edge.source !== id && edge.target !== id));
    } catch (error) {
      console.error('Error deleting node:', error);
    }
  };

  return (
    <div style={{ position: 'relative' }}>
      <Handle 
        type="target" 
        position={Position.Top} 
        id={`${id}-top`}
        size={30}
        style={{ 
          background: '#555',
          border: '3px solid #333',
          width: '30px',
          height: '30px',
          borderRadius: '50%',
          cursor: 'crosshair'
        }}
      />
      <Handle 
        type="source" 
        position={Position.Bottom} 
        id={`${id}-bottom`}
        size={30}
        style={{ 
          background: '#555',
          border: '3px solid #333',
          width: '30px',
          height: '30px',
          borderRadius: '50%',
          cursor: 'crosshair'
        }}
      />
      <NodeWrapper>
        <NodeContainer 
          color={color}
          onClick={startEditing}
        >
          {isEditing ? (
            <NodeInput
              type="text"
              value={inputValue}
              onChange={handleInputChange}
              onBlur={handleBlur}
              onKeyDown={handleKeyDown}
              autoFocus
            />
          ) : (
            <>
              {data.label}
              <EditButton 
                onClick={(e) => {
                  e.stopPropagation();
                  startEditing(e);
                }}
              >
                ✎
              </EditButton>
              <DeleteButton 
                onClick={(e) => {
                  e.stopPropagation();
                  deleteNode(e);
                }}
              >
                ×
              </DeleteButton>
            </>
          )}
        </NodeContainer>
      </NodeWrapper>
    </div>
  );
});

export default CustomNode; 
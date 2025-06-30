import React, { useState, useContext } from 'react';
import { getBezierPath } from 'reactflow';
import { NodeContext } from '../../context/NodeContext';
import { API_BASE_URL } from '../../config';
import { CustomEdgeProps } from '../../types';
import styled from 'styled-components';

const DeleteButton = styled.button`
  background: #e74c3c;
  color: white;
  border: none;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  opacity: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);

  &:hover {
    background: #c0392b;
    opacity: 1;
    transform: translate(-50%, -50%) scale(1.1);
  }

  &:active {
    transform: translate(-50%, -50%) scale(0.95);
  }
`;

const EdgePath = styled.path`
  stroke: #34495e;
  stroke-width: 1.5;
  fill: none;
  transition: all 0.3s ease;

  &:hover {
    stroke: #2c3e50;
    stroke-width: 2;
  }
`;

const CustomEdge: React.FC<CustomEdgeProps> = ({ 
  id, 
  sourceX, 
  sourceY, 
  targetX, 
  targetY, 
  sourcePosition, 
  targetPosition, 
  style = {}, 
  markerEnd, 
  data 
}) => {
  const context = useContext(NodeContext);
  if (!context) {
    throw new Error('CustomEdge must be used within a NodeContext.Provider');
  }
  
  const { setEdges } = context;
  const [isDeleting, setIsDeleting] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  const deleteEdge = async (e?: React.MouseEvent) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    
    if (isDeleting) return;
    setIsDeleting(true);
    
    try {
      const response = await fetch(`${API_BASE_URL}/edges/${id}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error('Failed to delete edge');
      }
      
      setEdges((eds) => eds.filter((edge) => edge.id !== id));
    } catch (error) {
      console.error('Error deleting edge:', error);
      alert('Failed to delete edge. Please try again.');
    } finally {
      setIsDeleting(false);
    }
  };

  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
    curvature: 0.25,
  });

  const edgeCenter = {
    x: (sourceX + targetX) / 2,
    y: (sourceY + targetY) / 2,
  };

  // Apply the base style and hover effects
  const edgeStyle: React.CSSProperties = {
    ...style,
    strokeDasharray: data?.styleType === 'dashed' ? '10,5' : 'none',
    strokeWidth: isHovered ? 2 : 1.5,
    stroke: isHovered ? '#2c3e50' : '#34495e',
    transition: 'all 0.3s ease'
  };

  return (
    <>
      <EdgePath
        id={id}
        className="react-flow__edge-path"
        d={edgePath}
        markerEnd="url(#arrowhead)"
        style={edgeStyle}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      />
      <foreignObject
        width={40}
        height={40}
        x={edgeCenter.x - 20}
        y={edgeCenter.y - 20}
        style={{ overflow: 'visible' }}
        requiredExtensions="http://www.w3.org/1999/xhtml"
      >
        <div
          style={{
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <DeleteButton
            onClick={deleteEdge}
            disabled={isDeleting}
            onMouseEnter={(e) => e.currentTarget.style.opacity = '0.8'}
            onMouseLeave={(e) => e.currentTarget.style.opacity = '0'}
          >
            ×
          </DeleteButton>
        </div>
      </foreignObject>
    </>
  );
};

export default CustomEdge; 
import styled from 'styled-components';

export const NodeContainer = styled.div`
  padding: 16px 24px;
  border-radius: 12px;
  background: ${props => props.color};
  color: #fff;
  border: none;
  min-width: 120px;
  text-align: center;
  font-weight: 600;
  font-size: 14px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  cursor: pointer;
  position: relative;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(4px);
  letter-spacing: 0.5px;

  &:hover {
    box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    transform: translateY(-2px) scale(1.02);
  }
`;

export const EditButton = styled.button`
  position: absolute;
  top: -8px;
  right: -8px;
  background: #2c3e50;
  color: white;
  border: none;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  opacity: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 10;
  pointer-events: auto;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);

  &:hover {
    background: #34495e;
    opacity: 1;
    transform: scale(1.1);
  }
`;

export const DeleteButton = styled.button`
  position: absolute;
  top: -8px;
  left: -8px;
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
  z-index: 10;
  pointer-events: auto;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);

  &:hover {
    background: #c0392b;
    opacity: 1;
    transform: scale(1.1);
  }
`;

export const NodeWrapper = styled.div`
  position: relative;
  display: inline-block;

  &:hover ${EditButton}, &:hover ${DeleteButton} {
    opacity: 0.8;
  }
`;

export const NodeInput = styled.input`
  width: 100%;
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid rgba(255, 255, 255, 0.2);
  color: #fff;
  text-align: center;
  outline: none;
  font-size: inherit;
  font-weight: inherit;
  padding: 4px 8px;
  margin: 0;
  cursor: text;
  border-radius: 6px;
  transition: all 0.3s ease;

  &:focus {
    background: rgba(255, 255, 255, 0.15);
    border-color: rgba(255, 255, 255, 0.3);
  }

  &::placeholder {
    color: rgba(255, 255, 255, 0.6);
  }
`; 
import { createContext } from 'react';
import { NodeContextType } from '../types';

export const NodeContext = createContext<NodeContextType | null>(null); 
import { useState, useCallback } from 'react';
import { apiService } from '../services/api';
import { MessageType } from './useMessage';

export const useRepositoryRunner = (showMessage: (type: MessageType, text: string) => void) => {
  const [logs, setLogs] = useState<string>('');
  const [isRunning, setIsRunning] = useState<boolean>(false);

  const runRepository = useCallback(async (repoName: string) => {
    if (!repoName) {
      showMessage('error', 'Select a repository first');
      return;
    }

    try {
      setIsRunning(true);
      setLogs(`Running ${repoName}...\n`);
      const logFile = await apiService.runRepositorySet(repoName);
      
      const pollInterval = setInterval(async () => {
        try {
          const content = await apiService.getLogContent(logFile);
          setLogs(content);
          
          if (content.includes('--- Normcode Execution Completed ---') || content.includes('--- Normcode Execution Failed ---')) {
            clearInterval(pollInterval);
            setIsRunning(false);
          }
        } catch {
          clearInterval(pollInterval);
          setIsRunning(false);
        }
      }, 1000);
    } catch (error) {
      setIsRunning(false);
      showMessage('error', 'Failed to run repository');
    }
  }, [showMessage]);

  return {
    logs,
    isRunning,
    runRepository,
  };
};


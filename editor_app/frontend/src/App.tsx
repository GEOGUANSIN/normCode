import React, { useState, useEffect, useCallback } from 'react';
import { RepositorySet } from './types';
import { apiService } from './services/api';
import Sidebar from './components/Sidebar';
import JsonEditorComponent from './components/JsonEditor';
import LogViewer from './components/LogViewer';
import './App.css';

const App: React.FC = () => {
  const [repositorySets, setRepositorySets] = useState<string[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<string | null>(null);
  const [currentRepoData, setCurrentRepoData] = useState<RepositorySet | null>(null);
  const [logContent, setLogContent] = useState<string>('');
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [currentLogFilename, setCurrentLogFilename] = useState<string | null>(null);

  // Polling interval for logs
  const logPollingInterval = React.useRef<number | null>(null);

  // Fetch repository sets on component mount
  useEffect(() => {
    fetchRepositorySets();
  }, []);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (logPollingInterval.current) {
        clearInterval(logPollingInterval.current);
      }
    };
  }, []);

  const fetchRepositorySets = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const sets = await apiService.fetchRepositorySets();
      setRepositorySets(sets);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch repository sets');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRepoSelect = (repoName: string) => {
    setSelectedRepo(repoName);
  };

  const handleNewRepo = () => {
    const newRepo: RepositorySet = {
      name: "new_repository_set",
      concepts: [],
      inferences: []
    };
    setCurrentRepoData(newRepo);
    setSelectedRepo(null);
    setLogContent("Create a new repository set. Remember to save it!");
    stopLogPolling();
  };

  const handleLoadRepo = async () => {
    if (!selectedRepo) return;

    try {
      setIsLoading(true);
      setError(null);
      const repoData = await apiService.loadRepositorySet(selectedRepo);
      setCurrentRepoData(repoData);
      setLogContent(`Loaded repository set: ${selectedRepo}.`);
      stopLogPolling();
      setCurrentLogFilename(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load repository set');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveRepo = async () => {
    if (!currentRepoData) {
      setError("No repository data to save");
      return;
    }

    if (!currentRepoData.name) {
      setError("Repository Set must have a 'name' field.");
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      const savedRepo = await apiService.saveRepositorySet(currentRepoData);
      setSuccess(`Repository set '${savedRepo.name}' saved!`);
      setSelectedRepo(savedRepo.name);
      await fetchRepositorySets(); // Refresh the list
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save repository set');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteRepo = async () => {
    if (!selectedRepo) return;

    if (!confirm(`Are you sure you want to delete repository set '${selectedRepo}'?`)) {
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      await apiService.deleteRepositorySet(selectedRepo);
      setSuccess(`Repository set '${selectedRepo}' deleted!`);
      await fetchRepositorySets();
      
      if (currentRepoData?.name === selectedRepo) {
        setCurrentRepoData(null);
        setSelectedRepo(null);
        setLogContent("");
        stopLogPolling();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete repository set');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunRepo = async () => {
    if (isRunning) {
      stopLogPolling();
      setIsRunning(false);
      setLogContent(prev => prev + "\n--- Execution stopped by user ---");
      return;
    }

    const repoName = selectedRepo || currentRepoData?.name;
    if (!repoName) {
      setError("Please load or select a repository set to run.");
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      setLogContent(`Running repository set: ${repoName}...\n`);
      stopLogPolling();

      const logFilename = await apiService.runRepositorySet(repoName);
      setCurrentLogFilename(logFilename);
      setIsRunning(true);
      startLogPolling(logFilename);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run repository set');
      setLogContent(prev => prev + `Error: ${err instanceof Error ? err.message : 'Unknown error'}\n`);
    } finally {
      setIsLoading(false);
    }
  };

  const startLogPolling = (logFilename: string) => {
    if (logPollingInterval.current) {
      clearInterval(logPollingInterval.current);
    }
    
    if (logFilename) {
      logPollingInterval.current = setInterval(async () => {
        try {
          const content = await apiService.getLogContent(logFilename);
          setLogContent(content);
          
          // Check if execution has completed
          if (content.includes("--- Normcode Execution Completed ---") ||
              content.includes("--- Normcode Execution Failed:")) {
            stopLogPolling();
            setIsRunning(false);
          }
        } catch (error) {
          console.error('Error fetching log content:', error);
          stopLogPolling();
          setIsRunning(false);
        }
      }, 2000);
    }
  };

  const stopLogPolling = () => {
    if (logPollingInterval.current) {
      clearInterval(logPollingInterval.current);
      logPollingInterval.current = null;
    }
  };

  const handleDataChange = useCallback((data: RepositorySet) => {
    setCurrentRepoData(data);
  }, []);

  const handleEditorError = useCallback((error: string) => {
    setError(`JSON Editor Error: ${error}`);
  }, []);

  // Clear messages after 5 seconds
  useEffect(() => {
    if (error || success) {
      const timer = setTimeout(() => {
        setError(null);
        setSuccess(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, success]);

  return (
    <div className="container">
      <Sidebar
        repositorySets={repositorySets}
        selectedRepo={selectedRepo}
        onRepoSelect={handleRepoSelect}
        onNewRepo={handleNewRepo}
        onLoadRepo={handleLoadRepo}
        onSaveRepo={handleSaveRepo}
        onDeleteRepo={handleDeleteRepo}
        onRunRepo={handleRunRepo}
        isRunning={isRunning}
        disabled={isLoading}
      />
      
      <div className="main-content">
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}
        
        <JsonEditorComponent
          data={currentRepoData}
          onDataChange={handleDataChange}
          onError={handleEditorError}
        />
      </div>
      
      <LogViewer
        logContent={logContent}
        isRunning={isRunning}
      />
    </div>
  );
};

export default App;

import React, { useEffect, useRef } from 'react';

interface LogViewerProps {
  logContent: string;
  isRunning: boolean;
}

const LogViewer: React.FC<LogViewerProps> = ({ logContent, isRunning }) => {
  const logOutputRef = useRef<HTMLPreElement>(null);

  useEffect(() => {
    if (logOutputRef.current) {
      logOutputRef.current.scrollTop = logOutputRef.current.scrollHeight;
    }
  }, [logContent]);

  return (
    <div className="log-viewer-tab">
      <div className="log-viewer-header">
        <h3>
          <span className={`status-indicator ${isRunning ? 'running' : 'stopped'}`}></span>
          Execution Logs
        </h3>
        <span className="log-viewer-status">
          {isRunning ? '🔄 Running...' : '✓ Ready'}
        </span>
      </div>
      <pre ref={logOutputRef} className="log-viewer-output">
        {logContent || 'No logs yet. Click "Run" to execute the repository and see logs here.'}
      </pre>
    </div>
  );
};

export default LogViewer;

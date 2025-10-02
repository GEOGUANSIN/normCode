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
    <div className="log-viewer">
      <h2>
        <span className={`status-indicator ${isRunning ? 'running' : 'stopped'}`}></span>
        Logs
      </h2>
      <pre ref={logOutputRef} className="log-output">
        {logContent || 'Select a repository set and click "Run" to see logs.'}
      </pre>
    </div>
  );
};

export default LogViewer;

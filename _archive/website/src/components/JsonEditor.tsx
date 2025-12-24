import React, { useEffect, useRef } from 'react';
import JSONEditor from 'jsoneditor';
import 'jsoneditor/dist/jsoneditor.css';
import type { RepositorySetData } from '../types';

interface JsonEditorProps {
  data: RepositorySetData | null;
  onDataChange: (data: RepositorySetData) => void;
  onError: (error: string) => void;
}

const JsonEditorComponent: React.FC<JsonEditorProps> = ({ data, onDataChange, onError }) => {
  const editorRef = useRef<HTMLDivElement>(null);
  const jsonEditorRef = useRef<JSONEditor | null>(null);
  const isInternalChangeRef = useRef<boolean>(false);
  const lastDataRef = useRef<RepositorySetData | null>(null);

  // Initialize the editor once
  useEffect(() => {
    if (editorRef.current && !jsonEditorRef.current) {
      const options = {
        mode: 'tree' as const,
        modes: ['code', 'tree', 'form', 'view'] as const,
        onError: (err: any) => {
          console.error('JSONEditor error:', err);
          if (err && err.toString) {
            onError(err.toString());
          }
        },
        onModeChange: (newMode: string, oldMode: string) => {
          console.log('Mode switched from', oldMode, 'to', newMode);
        },
        onChange: () => {
          // Only propagate changes that come from user interaction
          isInternalChangeRef.current = true;
          try {
            if (jsonEditorRef.current) {
              const editorData = jsonEditorRef.current.get();
              lastDataRef.current = editorData;
              onDataChange(editorData);
            }
          } catch (error) {
            console.error('Error getting data from editor:', error);
          }
        }
      };

      jsonEditorRef.current = new JSONEditor(editorRef.current, options as any);
      
      // Set initial data if available
      if (data) {
        jsonEditorRef.current.set(data);
        lastDataRef.current = data;
      }
    }

    // Cleanup on unmount only
    return () => {
      if (jsonEditorRef.current) {
        jsonEditorRef.current.destroy();
        jsonEditorRef.current = null;
      }
    };
  }, []); // Empty dependency array - only run once

  // Update editor when data changes externally (not from user edits)
  useEffect(() => {
    if (jsonEditorRef.current && data) {
      // Only update if this is an external change and data actually changed
      if (!isInternalChangeRef.current && JSON.stringify(lastDataRef.current) !== JSON.stringify(data)) {
        try {
          jsonEditorRef.current.set(data);
          lastDataRef.current = data;
        } catch (error) {
          console.error('Error setting data in editor:', error);
          onError('Invalid JSON data');
        }
      }
      // Reset the flag after processing
      isInternalChangeRef.current = false;
    }
  }, [data, onError]);

  return <div ref={editorRef} className="json-editor-container" />;
};

export default JsonEditorComponent;

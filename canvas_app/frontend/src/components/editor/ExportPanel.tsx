/**
 * ExportPanel - Format conversion and export component for NormCode files.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  ChevronDown,
  Loader2,
  Copy,
  Download,
  Save,
  FileOutput,
} from 'lucide-react';
import type { ParsedLine } from '../../types/editor';
import { editorApi } from '../../services/editorApi';

// =============================================================================
// Types
// =============================================================================

interface ExportPanelProps {
  parsedLines: ParsedLine[];
  selectedFile: string | null;
  onError: (error: string | null) => void;
  onSuccess: (message: string | null) => void;
}

// =============================================================================
// Component
// =============================================================================

export function ExportPanel({ 
  parsedLines, 
  selectedFile, 
  onError, 
  onSuccess 
}: ExportPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState<string>('ncd');
  const [previewContent, setPreviewContent] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [exportPath, setExportPath] = useState('');
  
  const formats = ['ncd', 'ncn', 'ncdn', 'json', 'nci'];
  
  // Generate previews when expanded or tab changes
  useEffect(() => {
    if (!isExpanded || parsedLines.length === 0) return;
    
    const generatePreview = async () => {
      setIsLoading(true);
      try {
        const result = await editorApi.serializeLines(parsedLines, activeTab);
        if (result.success) {
          setPreviewContent(prev => ({ ...prev, [activeTab]: result.content }));
        }
      } catch (e) {
        console.error('Failed to generate preview:', e);
      } finally {
        setIsLoading(false);
      }
    };
    
    if (!previewContent[activeTab]) {
      generatePreview();
    }
  }, [isExpanded, activeTab, parsedLines, previewContent]);
  
  // Reset previews when parsedLines change
  useEffect(() => {
    setPreviewContent({});
  }, [parsedLines]);
  
  // Initialize export path from selected file
  useEffect(() => {
    if (selectedFile && !exportPath) {
      // Replace extension with new format
      const basePath = selectedFile.replace(/\.[^/.]+$/, '');
      setExportPath(basePath);
    }
  }, [selectedFile, exportPath]);
  
  // Copy to clipboard
  const copyToClipboard = useCallback(async () => {
    const content = previewContent[activeTab];
    if (content) {
      try {
        await navigator.clipboard.writeText(content);
        onSuccess(`Copied ${activeTab.toUpperCase()} to clipboard`);
      } catch {
        onError('Failed to copy to clipboard');
      }
    }
  }, [activeTab, previewContent, onSuccess, onError]);
  
  // Download as file
  const downloadFile = useCallback(() => {
    const content = previewContent[activeTab];
    if (!content) return;
    
    const extensions: Record<string, string> = {
      ncd: '.ncd',
      ncn: '.ncn',
      ncdn: '.ncdn',
      json: '.nc.json',
      nci: '.nci.json',
    };
    
    const fileName = selectedFile 
      ? selectedFile.split(/[/\\]/).pop()?.replace(/\.[^/.]+$/, '') + extensions[activeTab]
      : `export${extensions[activeTab]}`;
    
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    a.click();
    URL.revokeObjectURL(url);
    onSuccess(`Downloaded ${fileName}`);
  }, [activeTab, previewContent, selectedFile, onSuccess]);
  
  // Save to server
  const saveToServer = useCallback(async () => {
    const content = previewContent[activeTab];
    if (!content || !exportPath) return;
    
    const extensions: Record<string, string> = {
      ncd: '.ncd',
      ncn: '.ncn',
      ncdn: '.ncdn',
      json: '.nc.json',
      nci: '.nci.json',
    };
    
    const fullPath = exportPath + extensions[activeTab];
    
    try {
      const result = await editorApi.saveFile(fullPath, content);
      if (result.success) {
        onSuccess(`Saved to ${fullPath}`);
      }
    } catch (e) {
      onError(`Failed to save: ${e instanceof Error ? e.message : 'Unknown error'}`);
    }
  }, [activeTab, previewContent, exportPath, onSuccess, onError]);
  
  // Generate all previews
  const generateAllPreviews = useCallback(async () => {
    for (const fmt of formats) {
      try {
        const result = await editorApi.serializeLines(parsedLines, fmt);
        if (result.success) {
          setPreviewContent(prev => ({ ...prev, [fmt]: result.content }));
        }
      } catch (e) {
        console.error(`Failed to generate ${fmt}:`, e);
      }
    }
    onSuccess('Generated all format previews');
  }, [parsedLines, formats, onSuccess]);
  
  // Download all available formats
  const downloadAllFormats = useCallback(() => {
    let downloaded = 0;
    const extensions: Record<string, string> = {
      ncd: '.ncd', ncn: '.ncn', ncdn: '.ncdn', json: '.nc.json', nci: '.nci.json',
    };
    
    for (const [fmt, content] of Object.entries(previewContent)) {
      if (content) {
        const fileName = selectedFile 
          ? selectedFile.split(/[/\\]/).pop()?.replace(/\.[^/.]+$/, '') + extensions[fmt]
          : `export${extensions[fmt]}`;
        
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        a.click();
        URL.revokeObjectURL(url);
        downloaded++;
      }
    }
    if (downloaded > 0) {
      onSuccess(`Downloaded ${downloaded} file(s)`);
    }
  }, [previewContent, selectedFile, onSuccess]);

  return (
    <div className="border-t bg-gray-50">
      {/* Header - always visible */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-2 flex items-center justify-between text-sm font-medium text-gray-700 hover:bg-gray-100"
      >
        <div className="flex items-center gap-2">
          <FileOutput className="w-4 h-4" />
          Export & Format Conversion
        </div>
        <ChevronDown className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
      </button>
      
      {/* Expanded content */}
      {isExpanded && (
        <div className="px-4 pb-4 space-y-3">
          {/* Format tabs */}
          <div className="flex items-center gap-1 border-b">
            {formats.map(fmt => (
              <button
                key={fmt}
                onClick={() => setActiveTab(fmt)}
                className={`px-3 py-1.5 text-xs font-medium rounded-t border-t border-x -mb-px transition-colors ${
                  activeTab === fmt
                    ? 'bg-white border-gray-300 text-blue-600'
                    : 'bg-gray-100 border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {fmt.toUpperCase()}
              </button>
            ))}
          </div>
          
          {/* Preview area */}
          <div className="bg-white border rounded-lg">
            <div className="flex items-center justify-between px-3 py-1.5 bg-gray-50 border-b text-xs text-gray-500 rounded-t-lg">
              <span>{activeTab.toUpperCase()} Preview</span>
              <div className="flex items-center gap-1">
                {isLoading && <Loader2 className="w-3 h-3 animate-spin" />}
                <button
                  onClick={copyToClipboard}
                  disabled={!previewContent[activeTab]}
                  className="p-1 rounded hover:bg-gray-200 disabled:opacity-50"
                  title="Copy to clipboard"
                >
                  <Copy className="w-3 h-3" />
                </button>
                <button
                  onClick={downloadFile}
                  disabled={!previewContent[activeTab]}
                  className="p-1 rounded hover:bg-gray-200 disabled:opacity-50"
                  title="Download file"
                >
                  <Download className="w-3 h-3" />
                </button>
              </div>
            </div>
            <div className="max-h-64 overflow-y-auto overflow-x-auto">
              <pre className="p-3 font-mono text-xs text-gray-800 whitespace-pre min-w-max">
                {previewContent[activeTab] || (isLoading ? 'Generating preview...' : 'Click to generate preview')}
              </pre>
            </div>
          </div>
          
          {/* Export path and save button */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500 whitespace-nowrap">Save as:</span>
            <input
              type="text"
              value={exportPath}
              onChange={(e) => setExportPath(e.target.value)}
              placeholder="path/to/file (without extension)"
              className="flex-1 px-2 py-1 text-xs border rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <span className="text-xs text-gray-400">
              {activeTab === 'json' ? '.nc.json' : activeTab === 'nci' ? '.nci.json' : `.${activeTab}`}
            </span>
            <button
              onClick={saveToServer}
              disabled={!previewContent[activeTab] || !exportPath}
              className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
            >
              <Save className="w-3 h-3" />
              Save
            </button>
          </div>
          
          {/* Quick export all formats */}
          <div className="flex items-center justify-between pt-2 border-t">
            <span className="text-xs text-gray-500">Quick actions:</span>
            <div className="flex items-center gap-2">
              <button
                onClick={generateAllPreviews}
                className="px-2 py-1 text-xs border rounded hover:bg-white text-gray-600"
              >
                Generate All
              </button>
              <button
                onClick={downloadAllFormats}
                disabled={Object.keys(previewContent).length === 0}
                className="px-2 py-1 text-xs border rounded hover:bg-white text-gray-600 disabled:opacity-50"
              >
                Download All
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ExportPanel;


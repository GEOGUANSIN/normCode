/**
 * FileBrowser - File tree browser component for the editor.
 */

import { useCallback } from 'react';
import {
  FolderOpen,
  FolderClosed,
  FileText,
  Search,
  X,
  Loader2,
  ChevronRight,
  ChevronDown,
} from 'lucide-react';
import type { FileInfo, TreeNode } from '../../types/editor';
import { getFormatIcon } from '../../config/fileTypes';

// =============================================================================
// Types
// =============================================================================

interface FileBrowserProps {
  directoryPath: string;
  onDirectoryChange: (path: string) => void;
  onLoadFiles: () => void;
  fileTree: TreeNode[];
  files: FileInfo[];
  totalFiles: number;
  expandedFolders: Set<string>;
  onToggleFolder: (path: string) => void;
  selectedFile: string | null;
  onSelectFile: (path: string) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  useTreeView: boolean;
  onToggleTreeView: () => void;
  isLoading: boolean;
}

// =============================================================================
// Component
// =============================================================================

export function FileBrowser({
  directoryPath,
  onDirectoryChange,
  onLoadFiles,
  fileTree,
  files,
  totalFiles,
  expandedFolders,
  onToggleFolder,
  selectedFile,
  onSelectFile,
  searchQuery,
  onSearchChange,
  useTreeView,
  onToggleTreeView,
  isLoading,
}: FileBrowserProps) {
  // Filter tree nodes by search query
  const filterTreeNodes = useCallback((nodes: TreeNode[], query: string): TreeNode[] => {
    if (!query) return nodes;
    
    return nodes.reduce<TreeNode[]>((acc, node) => {
      if (node.type === 'folder') {
        const filteredChildren = filterTreeNodes(node.children || [], query);
        if (filteredChildren.length > 0) {
          acc.push({ ...node, children: filteredChildren });
        }
      } else {
        if (node.name.toLowerCase().includes(query.toLowerCase())) {
          acc.push(node);
        }
      }
      return acc;
    }, []);
  }, []);

  const filteredTree = filterTreeNodes(fileTree, searchQuery);
  const filteredFiles = files.filter(f => 
    f.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Render a tree node recursively
  const renderTreeNode = useCallback((node: TreeNode, depth: number = 0) => {
    const isFolder = node.type === 'folder';
    const isExpanded = expandedFolders.has(node.path);
    const isSelected = selectedFile === node.path;
    
    return (
      <div key={node.path}>
        <button
          onClick={() => isFolder ? onToggleFolder(node.path) : onSelectFile(node.path)}
          className={`w-full text-left flex items-center gap-1.5 py-1 px-2 hover:bg-gray-100 text-sm
            ${isSelected ? 'bg-blue-50 border-l-2 border-blue-500' : ''}`}
          style={{ paddingLeft: `${8 + depth * 16}px` }}
        >
          {isFolder ? (
            <>
              {isExpanded ? (
                <ChevronDown className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
              ) : (
                <ChevronRight className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
              )}
              {isExpanded ? (
                <FolderOpen className="w-4 h-4 text-amber-500 flex-shrink-0" />
              ) : (
                <FolderClosed className="w-4 h-4 text-amber-500 flex-shrink-0" />
              )}
            </>
          ) : (
            <>
              <span className="w-3.5 flex-shrink-0" />
              {getFormatIcon(node.format || 'text')}
            </>
          )}
          <span className="truncate flex-1" title={node.name}>
            {node.name}
          </span>
          {!isFolder && node.size !== undefined && (
            <span className="text-xs text-gray-400 flex-shrink-0">
              {node.size < 1024 
                ? `${node.size}B`
                : `${(node.size / 1024).toFixed(1)}KB`
              }
            </span>
          )}
        </button>
        {isFolder && isExpanded && node.children && (
          <div>
            {node.children.map(child => renderTreeNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  }, [expandedFolders, selectedFile, onToggleFolder, onSelectFile]);

  return (
    <div className="w-72 bg-white border-r flex flex-col">
      {/* Header with directory input */}
      <div className="p-3 border-b space-y-2">
        <div className="flex gap-2">
          <input
            type="text"
            value={directoryPath}
            onChange={(e) => onDirectoryChange(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && onLoadFiles()}
            placeholder="Enter directory path..."
            className="flex-1 px-3 py-1.5 text-sm border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={onLoadFiles}
            disabled={isLoading || !directoryPath.trim()}
            className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            Load
          </button>
        </div>
        
        {/* View toggle and search */}
        <div className="flex items-center gap-2">
          <button
            onClick={onToggleTreeView}
            className={`px-2 py-1 text-xs rounded border ${
              useTreeView 
                ? 'bg-blue-50 border-blue-300 text-blue-600'
                : 'border-gray-300 text-gray-600 hover:bg-gray-50'
            }`}
            title={useTreeView ? 'Tree view' : 'Flat list view'}
          >
            {useTreeView ? <FolderOpen className="w-3 h-3" /> : <FileText className="w-3 h-3" />}
          </button>
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-2 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder="Filter files..."
              className="w-full pl-8 pr-3 py-1.5 text-sm border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {searchQuery && (
              <button 
                onClick={() => onSearchChange('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
        </div>
      </div>
      
      {/* File list */}
      <div className="flex-1 overflow-y-auto">
        {isLoading && fileTree.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
            Loading files...
          </div>
        ) : useTreeView ? (
          filteredTree.length === 0 ? (
            <div className="p-4 text-center text-gray-500 text-sm">
              {fileTree.length === 0 
                ? 'Enter a directory path and click Load'
                : 'No matching files found'
              }
            </div>
          ) : (
            <div className="py-1">
              {filteredTree.map(node => renderTreeNode(node, 0))}
            </div>
          )
        ) : (
          filteredFiles.length === 0 ? (
            <div className="p-4 text-center text-gray-500 text-sm">
              {files.length === 0 
                ? 'Enter a directory path and click Load'
                : 'No matching files found'
              }
            </div>
          ) : (
            <div className="py-1">
              {filteredFiles.map((file) => (
                <button
                  key={file.path}
                  onClick={() => onSelectFile(file.path)}
                  className={`w-full px-3 py-1.5 text-left flex items-center gap-2 hover:bg-gray-100 text-sm
                    ${selectedFile === file.path ? 'bg-blue-50 border-l-2 border-blue-500' : ''}`}
                >
                  {getFormatIcon(file.format)}
                  <span className="truncate flex-1 text-xs" title={file.name}>
                    {file.name}
                  </span>
                  <span className="text-xs text-gray-400 flex-shrink-0">
                    {(file.size / 1024).toFixed(1)}KB
                  </span>
                </button>
              ))}
            </div>
          )
        )}
      </div>
      
      {/* Footer with file count */}
      {totalFiles > 0 && (
        <div className="p-2 border-t text-xs text-gray-500 text-center flex items-center justify-center gap-2">
          <span>{searchQuery ? filteredFiles.length + ' matching /' : ''} {totalFiles} files</span>
          {useTreeView && (
            <button
              onClick={() => {/* TODO: collapse all */}}
              className="text-blue-500 hover:underline"
              title="Collapse all folders"
            >
              collapse
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default FileBrowser;


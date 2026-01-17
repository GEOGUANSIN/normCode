/**
 * Portable project state management with Zustand
 * 
 * Handles export/import of portable project archives.
 */
import { create } from 'zustand';
import type {
  ExportOptions,
  ImportOptions,
  ExportResult,
  ImportResult,
  PortableProjectInfo,
  RunInfoForExport,
  ExportListItem,
} from '../types/portable';
import { portableApi } from '../services/api';
import { useNotificationStore } from './notificationStore';

interface PortableState {
  // Export state
  isExporting: boolean;
  lastExportResult: ExportResult | null;
  availableRuns: RunInfoForExport[];
  availableExports: ExportListItem[];
  
  // Import state
  isImporting: boolean;
  isPreviewing: boolean;
  lastImportResult: ImportResult | null;
  previewInfo: PortableProjectInfo | null;
  
  // UI state
  isDialogOpen: boolean;
  dialogMode: 'export' | 'import' | null;
  error: string | null;
  
  // Actions
  setDialogOpen: (open: boolean, mode?: 'export' | 'import') => void;
  setError: (error: string | null) => void;
  
  // Export actions
  exportProject: (projectId?: string, options?: ExportOptions) => Promise<ExportResult | null>;
  quickExport: (projectId?: string, includeDatabase?: boolean) => Promise<ExportResult | null>;
  fetchRunsForExport: (projectId?: string) => Promise<void>;
  fetchAvailableExports: () => Promise<void>;
  
  // Import actions
  previewArchive: (archivePath: string) => Promise<PortableProjectInfo | null>;
  importProject: (archivePath: string, options: ImportOptions) => Promise<ImportResult | null>;
  quickImport: (archivePath: string, targetDirectory: string, overwrite?: boolean) => Promise<ImportResult | null>;
  clearPreview: () => void;
  
  // Reset
  reset: () => void;
}

export const usePortableStore = create<PortableState>((set, get) => ({
  // Initial state
  isExporting: false,
  lastExportResult: null,
  availableRuns: [],
  availableExports: [],
  
  isImporting: false,
  isPreviewing: false,
  lastImportResult: null,
  previewInfo: null,
  
  isDialogOpen: false,
  dialogMode: null,
  error: null,
  
  // Simple setters
  setDialogOpen: (open, mode) => set({ 
    isDialogOpen: open, 
    dialogMode: mode ?? null,
    // Clear states when closing
    ...(open ? {} : { error: null, previewInfo: null }),
  }),
  
  setError: (error) => set({ error }),
  
  // Export a project
  exportProject: async (projectId, options) => {
    set({ isExporting: true, error: null, lastExportResult: null });
    
    try {
      const result = await portableApi.exportProject(projectId, options);
      set({ isExporting: false, lastExportResult: result });
      
      if (result.success) {
        useNotificationStore.getState().showSuccess(
          'Project Exported',
          `Exported to ${result.output_path}`,
          5000
        );
      } else {
        useNotificationStore.getState().showError(
          'Export Failed',
          result.message
        );
      }
      
      // Refresh exports list
      get().fetchAvailableExports();
      
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Export failed';
      set({ isExporting: false, error: message });
      useNotificationStore.getState().showError('Export Failed', message);
      return null;
    }
  },
  
  // Quick export with defaults
  quickExport: async (projectId, includeDatabase = true) => {
    set({ isExporting: true, error: null, lastExportResult: null });
    
    try {
      const result = await portableApi.quickExport({
        project_id: projectId,
        include_database: includeDatabase,
      });
      set({ isExporting: false, lastExportResult: result });
      
      if (result.success) {
        useNotificationStore.getState().showSuccess(
          'Project Exported',
          `Exported ${result.files_count} files to ${result.output_path}`,
          5000
        );
      } else {
        useNotificationStore.getState().showError(
          'Export Failed',
          result.message
        );
      }
      
      // Refresh exports list
      get().fetchAvailableExports();
      
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Export failed';
      set({ isExporting: false, error: message });
      useNotificationStore.getState().showError('Export Failed', message);
      return null;
    }
  },
  
  // Fetch runs for selective export
  fetchRunsForExport: async (projectId) => {
    try {
      const runs = await portableApi.listRunsForExport(projectId);
      set({ availableRuns: runs });
    } catch (err) {
      console.error('Failed to fetch runs for export:', err);
      set({ availableRuns: [] });
    }
  },
  
  // Fetch available exports
  fetchAvailableExports: async () => {
    try {
      const response = await portableApi.listExports();
      set({ availableExports: response.exports });
    } catch (err) {
      console.error('Failed to fetch exports:', err);
      set({ availableExports: [] });
    }
  },
  
  // Preview an archive before importing
  previewArchive: async (archivePath) => {
    set({ isPreviewing: true, error: null, previewInfo: null });
    
    try {
      const info = await portableApi.previewImport(archivePath);
      set({ isPreviewing: false, previewInfo: info });
      return info;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Preview failed';
      set({ isPreviewing: false, error: message });
      useNotificationStore.getState().showError('Preview Failed', message);
      return null;
    }
  },
  
  // Import a project
  importProject: async (archivePath, options) => {
    set({ isImporting: true, error: null, lastImportResult: null });
    
    try {
      const result = await portableApi.importProject(archivePath, options);
      set({ isImporting: false, lastImportResult: result });
      
      if (result.success) {
        let message = `Imported ${result.files_imported} files`;
        if (result.runs_imported > 0) {
          message += ` and ${result.runs_imported} runs`;
        }
        
        useNotificationStore.getState().showSuccess(
          'Project Imported',
          message,
          5000
        );
        
        // Show warnings if any
        if (result.warnings.length > 0) {
          for (const warning of result.warnings.slice(0, 3)) {
            useNotificationStore.getState().showWarning(
              'Import Warning',
              warning,
              6000
            );
          }
        }
      } else {
        useNotificationStore.getState().showError(
          'Import Failed',
          result.message
        );
      }
      
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Import failed';
      set({ isImporting: false, error: message });
      useNotificationStore.getState().showError('Import Failed', message);
      return null;
    }
  },
  
  // Quick import with defaults
  quickImport: async (archivePath, targetDirectory, overwrite = false) => {
    set({ isImporting: true, error: null, lastImportResult: null });
    
    try {
      const result = await portableApi.quickImport({
        archive_path: archivePath,
        target_directory: targetDirectory,
        overwrite,
      });
      set({ isImporting: false, lastImportResult: result });
      
      if (result.success) {
        useNotificationStore.getState().showSuccess(
          'Project Imported',
          `Imported "${result.project_name}" to ${result.project_path}`,
          5000
        );
      } else {
        useNotificationStore.getState().showError(
          'Import Failed',
          result.message
        );
      }
      
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Import failed';
      set({ isImporting: false, error: message });
      useNotificationStore.getState().showError('Import Failed', message);
      return null;
    }
  },
  
  // Clear preview state
  clearPreview: () => set({ previewInfo: null }),
  
  // Reset store
  reset: () => set({
    isExporting: false,
    lastExportResult: null,
    availableRuns: [],
    availableExports: [],
    isImporting: false,
    isPreviewing: false,
    lastImportResult: null,
    previewInfo: null,
    isDialogOpen: false,
    dialogMode: null,
    error: null,
  }),
}));


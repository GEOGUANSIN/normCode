/**
 * Portable project types for export/import functionality.
 */

export type ExportScope = 'full' | 'project' | 'selected';

export interface PortableManifest {
  format_version: string;
  exported_at: string;
  export_scope: ExportScope;
  source_path: string | null;
  project_id: string;
  project_name: string;
  project_description: string | null;
  config_file: string;
  files: string[];
  has_database: boolean;
  database_file: string | null;
  runs_count: number;
  runs_included: string[];
  provisions_included: Record<string, string>;
  agent_config_included: boolean;
}

export interface ExportOptions {
  scope?: ExportScope;
  selected_run_ids?: string[];
  include_database?: boolean;
  include_logs?: boolean;
  include_provisions?: boolean;
  include_agent_config?: boolean;
  output_dir?: string;
  output_filename?: string;
  create_zip?: boolean;
}

export interface ImportOptions {
  target_directory: string;
  new_project_name?: string;
  overwrite_existing?: boolean;
  import_database?: boolean;
  import_runs?: boolean;
  merge_with_existing?: boolean;
}

export interface ExportResult {
  success: boolean;
  message: string;
  output_path: string | null;
  archive_size: number | null;
  manifest: PortableManifest | null;
  files_count: number;
  runs_exported: number;
}

export interface ImportResult {
  success: boolean;
  message: string;
  project_id: string | null;
  project_name: string | null;
  project_path: string | null;
  config_file: string | null;
  files_imported: number;
  runs_imported: number;
  warnings: string[];
}

export interface PortableProjectInfo {
  format_version: string;
  exported_at: string;
  export_scope: ExportScope;
  source_path: string | null;
  project_id: string;
  project_name: string;
  project_description: string | null;
  repositories: Record<string, string | null>;  // e.g., {concepts: "concepts.json", inputs: "inputs.json"}
  files_count: number;
  has_database: boolean;
  runs_count: number;
  provisions: Record<string, string>;
  archive_path: string;
  archive_size: number;
}

export interface RunInfoForExport {
  run_id: string;
  started_at: string | null;
  completed_at: string | null;
  status: string;
  execution_count: number;
  max_cycle: number;
  has_checkpoints: boolean;
}

export interface ExportListItem {
  path: string;
  filename: string;
  project_name?: string;
  exported_at?: string;
  size?: number;
  runs_count?: number;
  error?: string;
}

// Request types
export interface ExportProjectRequest {
  project_id?: string;
  options: ExportOptions;
}

export interface ImportProjectRequest {
  archive_path: string;
  options: ImportOptions;
}

export interface PreviewImportRequest {
  archive_path: string;
}

export interface ListRunsForExportRequest {
  project_id?: string;
}

export interface QuickExportRequest {
  project_id?: string;
  include_database?: boolean;
  output_dir?: string;
}

export interface QuickImportRequest {
  archive_path: string;
  target_directory: string;
  overwrite?: boolean;
}


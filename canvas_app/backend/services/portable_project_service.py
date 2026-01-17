"""
Portable Project Service - Export/Import projects with databases.

This service enables exporting projects as self-contained portable archives
that can be imported on different machines, preserving:
- Project configuration
- Repository files (concepts, inferences, inputs)
- Provisions (paradigms, prompts, scripts, data)
- Execution databases (orchestration.db)
- Run history and checkpoints
- Log files
"""
import json
import logging
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from schemas.portable_schemas import (
    ExportScope,
    PortableManifest,
    ExportOptions,
    ImportOptions,
    ExportResult,
    ImportResult,
    PortableProjectInfo,
    RunInfo,
)
from schemas.project_schemas import (
    ProjectConfig,
    generate_project_id,
    PROJECT_CONFIG_SUFFIX,
)
from services.project_service import project_service, get_app_data_dir

logger = logging.getLogger(__name__)

# Archive format constants
PORTABLE_ARCHIVE_EXTENSION = ".normcode-portable.zip"
MANIFEST_FILENAME = "portable-manifest.json"
PROJECT_SUBDIR = "project"  # Project files go here
DATABASE_SUBDIR = "database"  # Database and logs go here


class PortableProjectService:
    """
    Service for exporting and importing portable project archives.
    
    A portable project archive contains everything needed to fully restore
    a project including its run history and databases.
    """
    
    def __init__(self):
        self._exports_dir: Optional[Path] = None
    
    def _get_exports_dir(self) -> Path:
        """Get the default exports directory."""
        if self._exports_dir is None:
            app_data = get_app_data_dir()
            self._exports_dir = app_data / "exports"
            self._exports_dir.mkdir(parents=True, exist_ok=True)
        return self._exports_dir
    
    # =========================================================================
    # Export
    # =========================================================================
    
    def export_project(
        self,
        project_id: Optional[str] = None,
        options: Optional[ExportOptions] = None,
    ) -> ExportResult:
        """
        Export a project as a portable archive.
        
        Args:
            project_id: Project ID to export (uses current if None)
            options: Export options
            
        Returns:
            ExportResult with success status and output path
        """
        if options is None:
            options = ExportOptions()
        
        try:
            # Get project info
            if project_id:
                registered = project_service.get_project_by_id(project_id)
                if not registered:
                    return ExportResult(
                        success=False,
                        message=f"Project not found: {project_id}"
                    )
                project_dir = Path(registered.directory)
                config_file = registered.config_file
                config, _ = project_service._config_service.open_project(project_dir, config_file)
            else:
                if not project_service.is_project_open:
                    return ExportResult(
                        success=False,
                        message="No project is currently open"
                    )
                project_dir = project_service.current_project_path
                config = project_service.current_config
                config_file = project_service.current_config_file
            
            # Create temp directory for staging
            temp_dir = Path(tempfile.mkdtemp(prefix="normcode_export_"))
            staging_dir = temp_dir / "staging"
            staging_dir.mkdir()
            
            try:
                # Track all files
                all_files: List[str] = []
                
                # 1. Create project subdirectory and copy project files
                project_export_dir = staging_dir / PROJECT_SUBDIR
                project_export_dir.mkdir()
                
                # Copy project config
                config_src = project_dir / config_file
                if config_src.exists():
                    shutil.copy2(config_src, project_export_dir / config_file)
                    all_files.append(f"{PROJECT_SUBDIR}/{config_file}")
                
                # Copy repository files
                repos = config.repositories
                repositories_included: Dict[str, Optional[str]] = {}
                for repo_name, repo_path in [
                    ("concepts", repos.concepts),
                    ("inferences", repos.inferences),
                    ("inputs", repos.inputs),
                ]:
                    if repo_path:
                        src_path = project_dir / repo_path
                        if src_path.exists():
                            # Preserve directory structure
                            dest_path = project_export_dir / repo_path
                            dest_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(src_path, dest_path)
                            all_files.append(f"{PROJECT_SUBDIR}/{repo_path}")
                            repositories_included[repo_name] = repo_path
                            logger.info(f"Exported {repo_name}: {repo_path}")
                        else:
                            logger.warning(f"{repo_name} file not found: {repo_path}")
                            repositories_included[repo_name] = None
                    else:
                        repositories_included[repo_name] = None
                
                # 2. Copy provisions
                provisions_included: Dict[str, str] = {}
                if options.include_provisions:
                    provisions_included = self._copy_provisions(
                        project_dir, config, project_export_dir, all_files
                    )
                
                # 3. Copy agent config if exists
                agent_config_included = False
                if options.include_agent_config and config.execution.agent_config:
                    agent_src = project_dir / config.execution.agent_config
                    if agent_src.exists():
                        dest_path = project_export_dir / config.execution.agent_config
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(agent_src, dest_path)
                        all_files.append(f"{PROJECT_SUBDIR}/{config.execution.agent_config}")
                        agent_config_included = True
                
                # 4. Handle database and runs
                has_database = False
                runs_included: List[str] = []
                runs_count = 0
                
                if options.include_database:
                    db_result = self._copy_database(
                        project_dir, config, staging_dir, options, all_files
                    )
                    has_database = db_result["has_database"]
                    runs_included = db_result["runs_included"]
                    runs_count = db_result["runs_count"]
                
                # 5. Create manifest
                manifest = PortableManifest(
                    format_version="1.0.0",
                    exported_at=datetime.now(),
                    export_scope=options.scope,
                    source_path=str(project_dir.absolute()),
                    project_id=config.id,
                    project_name=config.name,
                    project_description=config.description,
                    config_file=config_file,
                    repositories=repositories_included,
                    files=all_files,
                    has_database=has_database,
                    database_file=f"{DATABASE_SUBDIR}/orchestration.db" if has_database else None,
                    runs_count=runs_count,
                    runs_included=runs_included,
                    provisions_included=provisions_included,
                    agent_config_included=agent_config_included,
                )
                
                # Save manifest
                manifest_path = staging_dir / MANIFEST_FILENAME
                with open(manifest_path, 'w', encoding='utf-8') as f:
                    json.dump(manifest.model_dump(mode='json'), f, indent=2, default=str)
                
                # 6. Determine output path
                # Default to project directory, or custom location if specified
                if options.output_dir:
                    output_dir = Path(options.output_dir)
                else:
                    # Default to project directory
                    output_dir = project_dir
                output_dir.mkdir(parents=True, exist_ok=True)
                
                # Generate filename
                if options.output_filename:
                    base_filename = options.output_filename
                else:
                    # Use project name + timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_name = config.name.replace(" ", "-").lower()
                    safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '-')
                    base_filename = f"{safe_name}_{timestamp}"
                
                # 7. Create output (zip or folder)
                if options.create_zip:
                    output_path = output_dir / f"{base_filename}{PORTABLE_ARCHIVE_EXTENSION}"
                    self._create_zip_archive(staging_dir, output_path)
                    archive_size = output_path.stat().st_size
                else:
                    output_path = output_dir / base_filename
                    if output_path.exists():
                        shutil.rmtree(output_path)
                    shutil.copytree(staging_dir, output_path)
                    archive_size = sum(f.stat().st_size for f in output_path.rglob('*') if f.is_file())
                
                logger.info(f"Exported project '{config.name}' to {output_path}")
                
                return ExportResult(
                    success=True,
                    message=f"Project exported successfully to {output_path}",
                    output_path=str(output_path),
                    archive_size=archive_size,
                    manifest=manifest,
                    files_count=len(all_files),
                    runs_exported=runs_count,
                )
                
            finally:
                # Cleanup temp directory
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            logger.exception(f"Export failed: {e}")
            return ExportResult(
                success=False,
                message=f"Export failed: {str(e)}"
            )
    
    def _copy_provisions(
        self,
        project_dir: Path,
        config: ProjectConfig,
        dest_dir: Path,
        all_files: List[str],
    ) -> Dict[str, str]:
        """Copy provision directories (paradigms, prompts, etc.)."""
        provisions_included: Dict[str, str] = {}
        
        # Find provisions root from paradigm_dir
        provisions_root = None
        if config.execution.paradigm_dir:
            paradigm_path = project_dir / config.execution.paradigm_dir
            if paradigm_path.exists():
                provisions_root = paradigm_path.parent
        
        # Common provision directory names
        provision_dirs = ["paradigm", "paradigms", "prompts", "scripts", "data", "schemas"]
        
        if provisions_root and provisions_root.exists() and provisions_root != project_dir:
            # Copy from provisions root
            for item in provisions_root.iterdir():
                if item.is_dir() and not item.name.startswith('__'):
                    rel_path = item.relative_to(project_dir)
                    dest_path = dest_dir / rel_path
                    shutil.copytree(
                        item, dest_path,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo')
                    )
                    provisions_included[item.name] = str(rel_path)
                    # Track files
                    for f in dest_path.rglob('*'):
                        if f.is_file():
                            all_files.append(f"{PROJECT_SUBDIR}/{f.relative_to(dest_dir)}")
        else:
            # Look for common provision directories at project level
            for subdir_name in provision_dirs:
                src_path = project_dir / subdir_name
                if src_path.exists() and src_path.is_dir():
                    dest_path = dest_dir / subdir_name
                    shutil.copytree(
                        src_path, dest_path,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo')
                    )
                    provisions_included[subdir_name] = subdir_name
                    for f in dest_path.rglob('*'):
                        if f.is_file():
                            all_files.append(f"{PROJECT_SUBDIR}/{f.relative_to(dest_dir)}")
            
            # Also check for "provision" or "provisions" parent directory
            for parent_name in ["provision", "provisions"]:
                parent_path = project_dir / parent_name
                if parent_path.exists() and parent_path.is_dir():
                    for item in parent_path.iterdir():
                        if item.is_dir() and not item.name.startswith('__'):
                            rel_path = item.relative_to(project_dir)
                            dest_path = dest_dir / rel_path
                            if not dest_path.exists():
                                shutil.copytree(
                                    item, dest_path,
                                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo')
                                )
                                provisions_included[item.name] = str(rel_path)
                                for f in dest_path.rglob('*'):
                                    if f.is_file():
                                        all_files.append(f"{PROJECT_SUBDIR}/{f.relative_to(dest_dir)}")
        
        return provisions_included
    
    def _copy_database(
        self,
        project_dir: Path,
        config: ProjectConfig,
        staging_dir: Path,
        options: ExportOptions,
        all_files: List[str],
    ) -> Dict[str, Any]:
        """Copy database and related files."""
        result = {
            "has_database": False,
            "runs_included": [],
            "runs_count": 0,
        }
        
        # Find database path
        db_path = project_dir / config.execution.db_path
        if not db_path.exists():
            return result
        
        # Create database subdirectory
        db_export_dir = staging_dir / DATABASE_SUBDIR
        db_export_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine which runs to include
        runs_to_include: Optional[List[str]] = None
        if options.scope == ExportScope.SELECTED_RUNS:
            runs_to_include = options.selected_run_ids
        elif options.scope == ExportScope.PROJECT_ONLY:
            # Skip database entirely for project-only export
            return result
        
        # Copy the database
        if runs_to_include is not None and len(runs_to_include) > 0:
            # Selective export - need to create a filtered database
            result = self._create_filtered_database(
                db_path, db_export_dir, runs_to_include, all_files
            )
        else:
            # Full export - copy the entire database
            dest_db_path = db_export_dir / "orchestration.db"
            shutil.copy2(db_path, dest_db_path)
            all_files.append(f"{DATABASE_SUBDIR}/orchestration.db")
            result["has_database"] = True
            
            # Get run count
            try:
                from infra._orchest._db import OrchestratorDB
                db = OrchestratorDB(str(db_path))
                runs = db.list_runs()
                result["runs_count"] = len(runs)
                result["runs_included"] = [r.get("run_id", "") for r in runs]
            except Exception as e:
                logger.warning(f"Could not count runs: {e}")
        
        # Copy log files if requested
        if options.include_logs:
            db_dir = db_path.parent
            logs_dir = db_dir / "logs"
            
            # Look for logs in both the logs/ subdirectory (new) and db directory (legacy)
            log_sources = []
            if logs_dir.exists():
                log_sources.extend(logs_dir.glob("run_*.log"))
            log_sources.extend(db_dir.glob("run_*.log"))  # Legacy location
            
            for log_file in log_sources:
                # Check if this log belongs to an included run
                if runs_to_include is not None:
                    # Extract run_id from log filename (run_XXXXXXXX_YYYYMMDD_HHMMSS.log)
                    parts = log_file.stem.split("_")
                    if len(parts) >= 2:
                        log_run_id = parts[1]
                        if not any(log_run_id in run_id for run_id in runs_to_include):
                            continue
                
                dest_log = db_export_dir / log_file.name
                shutil.copy2(log_file, dest_log)
                all_files.append(f"{DATABASE_SUBDIR}/{log_file.name}")
        
        return result
    
    def _create_filtered_database(
        self,
        source_db: Path,
        dest_dir: Path,
        run_ids: List[str],
        all_files: List[str],
    ) -> Dict[str, Any]:
        """Create a database containing only selected runs."""
        result = {
            "has_database": False,
            "runs_included": [],
            "runs_count": 0,
        }
        
        try:
            import sqlite3
            
            dest_db = dest_dir / "orchestration.db"
            
            # Copy the entire database first
            shutil.copy2(source_db, dest_db)
            
            # Then remove unwanted runs
            conn = sqlite3.connect(str(dest_db))
            cursor = conn.cursor()
            
            try:
                # Get all run IDs in the database
                cursor.execute("SELECT DISTINCT run_id FROM run_metadata")
                all_run_ids = [row[0] for row in cursor.fetchall()]
                
                # Determine which runs to delete
                runs_to_keep = set(run_ids)
                runs_to_delete = [r for r in all_run_ids if r not in runs_to_keep]
                
                # Delete unwanted runs
                for run_id in runs_to_delete:
                    cursor.execute("DELETE FROM checkpoints WHERE run_id = ?", (run_id,))
                    cursor.execute("DELETE FROM run_metadata WHERE run_id = ?", (run_id,))
                    cursor.execute("DELETE FROM executions WHERE run_id = ?", (run_id,))
                
                # Vacuum to reclaim space
                conn.execute("VACUUM")
                conn.commit()
                
                result["has_database"] = True
                result["runs_included"] = list(runs_to_keep & set(all_run_ids))
                result["runs_count"] = len(result["runs_included"])
                
            finally:
                conn.close()
            
            all_files.append(f"{DATABASE_SUBDIR}/orchestration.db")
            
        except Exception as e:
            logger.error(f"Failed to create filtered database: {e}")
        
        return result
    
    def _create_zip_archive(self, source_dir: Path, output_path: Path):
        """Create a zip archive from a directory."""
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in source_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_dir)
                    zf.write(file_path, arcname)
    
    # =========================================================================
    # Import
    # =========================================================================
    
    def preview_import(self, archive_path: str) -> PortableProjectInfo:
        """
        Preview a portable project archive before importing.
        
        Args:
            archive_path: Path to the archive (.zip or folder)
            
        Returns:
            PortableProjectInfo with archive contents
            
        Raises:
            FileNotFoundError: If archive doesn't exist
            ValueError: If archive is invalid
        """
        path = Path(archive_path)
        if not path.exists():
            raise FileNotFoundError(f"Archive not found: {archive_path}")
        
        # Determine if it's a zip or folder
        is_zip = path.suffix == ".zip" or path.name.endswith(PORTABLE_ARCHIVE_EXTENSION)
        
        if is_zip:
            # Read manifest from zip
            with zipfile.ZipFile(path, 'r') as zf:
                if MANIFEST_FILENAME not in zf.namelist():
                    raise ValueError(f"Invalid archive: missing {MANIFEST_FILENAME}")
                
                with zf.open(MANIFEST_FILENAME) as f:
                    manifest_data = json.load(f)
                
                files_count = len([n for n in zf.namelist() if not n.endswith('/')])
            
            archive_size = path.stat().st_size
        else:
            # Read manifest from folder
            manifest_path = path / MANIFEST_FILENAME
            if not manifest_path.exists():
                raise ValueError(f"Invalid archive: missing {MANIFEST_FILENAME}")
            
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)
            
            files_count = len([f for f in path.rglob('*') if f.is_file()])
            archive_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        
        manifest = PortableManifest(**manifest_data)
        
        return PortableProjectInfo(
            format_version=manifest.format_version,
            exported_at=manifest.exported_at,
            export_scope=manifest.export_scope,
            source_path=manifest.source_path,
            project_id=manifest.project_id,
            project_name=manifest.project_name,
            project_description=manifest.project_description,
            repositories=manifest.repositories,
            files_count=files_count,
            has_database=manifest.has_database,
            runs_count=manifest.runs_count,
            provisions=manifest.provisions_included,
            archive_path=str(path.absolute()),
            archive_size=archive_size,
        )
    
    def import_project(
        self,
        archive_path: str,
        options: ImportOptions,
    ) -> ImportResult:
        """
        Import a portable project archive.
        
        Args:
            archive_path: Path to the archive (.zip or folder)
            options: Import options
            
        Returns:
            ImportResult with success status and project info
        """
        path = Path(archive_path)
        if not path.exists():
            return ImportResult(
                success=False,
                message=f"Archive not found: {archive_path}"
            )
        
        try:
            # Create temp extraction directory
            temp_dir = Path(tempfile.mkdtemp(prefix="normcode_import_"))
            
            try:
                # Extract or copy to temp
                is_zip = path.suffix == ".zip" or path.name.endswith(PORTABLE_ARCHIVE_EXTENSION)
                
                if is_zip:
                    with zipfile.ZipFile(path, 'r') as zf:
                        zf.extractall(temp_dir)
                    extract_dir = temp_dir
                else:
                    extract_dir = path
                
                # Read manifest
                manifest_path = extract_dir / MANIFEST_FILENAME
                if not manifest_path.exists():
                    return ImportResult(
                        success=False,
                        message=f"Invalid archive: missing {MANIFEST_FILENAME}"
                    )
                
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest_data = json.load(f)
                manifest = PortableManifest(**manifest_data)
                
                # Prepare target directory
                target_dir = Path(options.target_directory)
                target_dir.mkdir(parents=True, exist_ok=True)
                
                # Check for existing project
                warnings: List[str] = []
                existing_config = None
                for f in target_dir.iterdir():
                    if f.name.endswith(PROJECT_CONFIG_SUFFIX) or f.name == "normcode-canvas.json":
                        if not options.overwrite_existing and not options.merge_with_existing:
                            return ImportResult(
                                success=False,
                                message=f"Project already exists in {target_dir}. "
                                        "Use overwrite_existing or merge_with_existing option."
                            )
                        existing_config = f.name
                        break
                
                # Determine project name and config file
                if options.new_project_name:
                    project_name = options.new_project_name
                    # Generate new config filename
                    slug = project_name.lower().replace(' ', '-')
                    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
                    config_file = f"{slug}{PROJECT_CONFIG_SUFFIX}"
                else:
                    project_name = manifest.project_name
                    config_file = manifest.config_file
                
                # Copy project files
                project_src = extract_dir / PROJECT_SUBDIR
                if project_src.exists():
                    files_imported = self._copy_project_files(
                        project_src, target_dir, manifest, config_file, options, warnings
                    )
                else:
                    files_imported = 0
                    warnings.append("No project files found in archive")
                
                # Handle database
                runs_imported = 0
                if options.import_database and manifest.has_database:
                    db_src = extract_dir / DATABASE_SUBDIR
                    if db_src.exists():
                        runs_imported = self._import_database(
                            db_src, target_dir, manifest, options, warnings
                        )
                
                # Update/create project config
                new_project_id = self._update_project_config(
                    target_dir, config_file, project_name, manifest, options
                )
                
                # Register the project
                try:
                    project_service._registry_service.register_project(
                        target_dir, config_file, 
                        project_service._config_service.open_project(target_dir, config_file)[0]
                    )
                except Exception as e:
                    warnings.append(f"Could not register project: {e}")
                
                logger.info(f"Imported project '{project_name}' to {target_dir}")
                
                return ImportResult(
                    success=True,
                    message=f"Project imported successfully to {target_dir}",
                    project_id=new_project_id,
                    project_name=project_name,
                    project_path=str(target_dir.absolute()),
                    config_file=config_file,
                    files_imported=files_imported,
                    runs_imported=runs_imported,
                    warnings=warnings,
                )
                
            finally:
                # Cleanup temp directory (only if we extracted a zip)
                if is_zip:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    
        except Exception as e:
            logger.exception(f"Import failed: {e}")
            return ImportResult(
                success=False,
                message=f"Import failed: {str(e)}"
            )
    
    def _copy_project_files(
        self,
        src_dir: Path,
        dest_dir: Path,
        manifest: PortableManifest,
        config_file: str,
        options: ImportOptions,
        warnings: List[str],
    ) -> int:
        """Copy project files to target directory."""
        files_copied = 0
        
        for item in src_dir.iterdir():
            dest_path = dest_dir / item.name
            
            # Handle config file specially (may need renaming)
            if item.name == manifest.config_file and item.name != config_file:
                dest_path = dest_dir / config_file
            
            if item.is_file():
                if dest_path.exists() and not options.overwrite_existing:
                    warnings.append(f"Skipped existing file: {item.name}")
                    continue
                shutil.copy2(item, dest_path)
                files_copied += 1
            elif item.is_dir():
                if dest_path.exists():
                    if options.overwrite_existing:
                        shutil.rmtree(dest_path)
                    else:
                        warnings.append(f"Skipped existing directory: {item.name}")
                        continue
                shutil.copytree(item, dest_path)
                files_copied += len([f for f in dest_path.rglob('*') if f.is_file()])
        
        return files_copied
    
    def _import_database(
        self,
        db_src_dir: Path,
        target_dir: Path,
        manifest: PortableManifest,
        options: ImportOptions,
        warnings: List[str],
    ) -> int:
        """Import database and log files."""
        runs_imported = 0
        
        src_db = db_src_dir / "orchestration.db"
        if not src_db.exists():
            warnings.append("Database file not found in archive")
            return 0
        
        dest_db = target_dir / "orchestration.db"
        
        if dest_db.exists() and options.merge_with_existing:
            # Merge databases
            runs_imported = self._merge_databases(src_db, dest_db, manifest, warnings)
        else:
            if dest_db.exists() and not options.overwrite_existing:
                warnings.append("Skipped existing database")
                return 0
            
            shutil.copy2(src_db, dest_db)
            runs_imported = manifest.runs_count
        
        # Copy log files to logs/ subdirectory
        logs_dest_dir = target_dir / "logs"
        logs_dest_dir.mkdir(parents=True, exist_ok=True)
        for log_file in db_src_dir.glob("run_*.log"):
            dest_log = logs_dest_dir / log_file.name
            if not dest_log.exists() or options.overwrite_existing:
                shutil.copy2(log_file, dest_log)
        
        return runs_imported
    
    def _merge_databases(
        self,
        src_db: Path,
        dest_db: Path,
        manifest: PortableManifest,
        warnings: List[str],
    ) -> int:
        """Merge source database runs into destination database."""
        runs_imported = 0
        
        try:
            import sqlite3
            
            src_conn = sqlite3.connect(str(src_db))
            dest_conn = sqlite3.connect(str(dest_db))
            
            try:
                src_cursor = src_conn.cursor()
                dest_cursor = dest_conn.cursor()
                
                # Get existing run IDs in destination
                dest_cursor.execute("SELECT run_id FROM run_metadata")
                existing_runs = set(row[0] for row in dest_cursor.fetchall())
                
                # Get runs to import from source
                src_cursor.execute("SELECT run_id FROM run_metadata")
                src_runs = [row[0] for row in src_cursor.fetchall()]
                
                for run_id in src_runs:
                    if run_id in existing_runs:
                        warnings.append(f"Skipped existing run: {run_id[:8]}...")
                        continue
                    
                    # Import run_metadata
                    src_cursor.execute("SELECT * FROM run_metadata WHERE run_id = ?", (run_id,))
                    row = src_cursor.fetchone()
                    if row:
                        placeholders = ','.join(['?' for _ in row])
                        dest_cursor.execute(f"INSERT INTO run_metadata VALUES ({placeholders})", row)
                    
                    # Import executions
                    src_cursor.execute("SELECT * FROM executions WHERE run_id = ?", (run_id,))
                    for row in src_cursor.fetchall():
                        placeholders = ','.join(['?' for _ in row])
                        dest_cursor.execute(f"INSERT INTO executions VALUES ({placeholders})", row)
                    
                    # Import checkpoints
                    src_cursor.execute("SELECT * FROM checkpoints WHERE run_id = ?", (run_id,))
                    for row in src_cursor.fetchall():
                        placeholders = ','.join(['?' for _ in row])
                        dest_cursor.execute(f"INSERT INTO checkpoints VALUES ({placeholders})", row)
                    
                    runs_imported += 1
                
                dest_conn.commit()
                
            finally:
                src_conn.close()
                dest_conn.close()
                
        except Exception as e:
            warnings.append(f"Database merge error: {e}")
        
        return runs_imported
    
    def _update_project_config(
        self,
        target_dir: Path,
        config_file: str,
        project_name: str,
        manifest: PortableManifest,
        options: ImportOptions,
    ) -> str:
        """Update or create project configuration."""
        config_path = target_dir / config_file
        
        if config_path.exists():
            # Load and update existing config
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            if options.new_project_name:
                config_data['name'] = project_name
            
            # Generate new ID if this is a fresh import
            if not options.merge_with_existing:
                config_data['id'] = generate_project_id()
            
            config_data['updated_at'] = datetime.now().isoformat()
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, default=str)
            
            return config_data['id']
        else:
            # This shouldn't happen as we copied project files
            return manifest.project_id
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def list_runs_for_export(
        self,
        project_id: Optional[str] = None,
    ) -> List[RunInfo]:
        """
        List available runs for selective export.
        
        Args:
            project_id: Project ID (uses current if None)
            
        Returns:
            List of RunInfo objects
        """
        try:
            # Get project info
            if project_id:
                registered = project_service.get_project_by_id(project_id)
                if not registered:
                    return []
                project_dir = Path(registered.directory)
                config, _ = project_service._config_service.open_project(
                    project_dir, registered.config_file
                )
            else:
                if not project_service.is_project_open:
                    return []
                project_dir = project_service.current_project_path
                config = project_service.current_config
            
            # Find database
            db_path = project_dir / config.execution.db_path
            if not db_path.exists():
                return []
            
            # Get runs from database
            from infra._orchest._db import OrchestratorDB
            db = OrchestratorDB(str(db_path))
            runs = db.list_runs(include_metadata=True)
            
            result = []
            for run in runs:
                result.append(RunInfo(
                    run_id=run.get('run_id', ''),
                    started_at=run.get('first_execution'),
                    completed_at=run.get('last_execution'),
                    status=run.get('status', 'unknown'),
                    execution_count=run.get('execution_count', 0),
                    max_cycle=run.get('max_cycle', 0),
                    has_checkpoints=run.get('max_cycle', 0) > 0,
                ))
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list runs: {e}")
            return []
    
    def list_exports(self) -> List[Dict[str, Any]]:
        """List available exported archives in the default exports directory."""
        exports_dir = self._get_exports_dir()
        result = []
        
        for item in exports_dir.iterdir():
            if item.name.endswith(PORTABLE_ARCHIVE_EXTENSION):
                try:
                    info = self.preview_import(str(item))
                    result.append({
                        "path": str(item),
                        "filename": item.name,
                        "project_name": info.project_name,
                        "exported_at": info.exported_at.isoformat(),
                        "size": info.archive_size,
                        "runs_count": info.runs_count,
                    })
                except Exception as e:
                    result.append({
                        "path": str(item),
                        "filename": item.name,
                        "error": str(e),
                    })
        
        return sorted(result, key=lambda x: x.get('exported_at', ''), reverse=True)


# Global singleton
portable_project_service = PortableProjectService()


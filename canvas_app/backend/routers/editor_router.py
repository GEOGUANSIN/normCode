"""
Editor Router - File editing endpoints for NormCode files
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import os
import json

router = APIRouter()


class FileContent(BaseModel):
    """File content for reading/writing"""
    path: str
    content: str
    format: str = "ncd"  # ncd, ncn, ncdn, json


class FileInfo(BaseModel):
    """File information"""
    name: str
    path: str
    format: str
    size: int
    modified: float
    is_dir: bool = False  # True if this is a directory


class FileSaveRequest(BaseModel):
    """Request to save a file"""
    path: str
    content: str


class FileListRequest(BaseModel):
    """Request to list files in a directory"""
    directory: str
    extensions: Optional[List[str]] = [
        ".ncd", ".ncn", ".ncdn", ".nc.json", ".nci.json", ".json",
        ".py", ".md", ".txt", ".yaml", ".yml", ".toml",
        ".concept.json", ".inference.json"
    ]
    recursive: bool = False  # Whether to list recursively


class FileListResponse(BaseModel):
    """Response with list of files"""
    directory: str
    files: List[FileInfo]


def get_file_format(filename: str) -> str:
    """Determine file format from extension"""
    # NormCode specific formats (check longer extensions first)
    if filename.endswith('.concept.json'):
        return 'concept'
    elif filename.endswith('.inference.json'):
        return 'inference'
    elif filename.endswith('.nci.json'):
        return 'nci'
    elif filename.endswith('.nc.json'):
        return 'nc-json'
    elif filename.endswith('.ncdn'):
        return 'ncdn'
    elif filename.endswith('.ncn'):
        return 'ncn'
    elif filename.endswith('.ncd'):
        return 'ncd'
    elif filename.endswith('.json'):
        return 'json'
    # Common code formats
    elif filename.endswith('.py'):
        return 'python'
    elif filename.endswith('.md'):
        return 'markdown'
    elif filename.endswith('.txt'):
        return 'text'
    elif filename.endswith('.yaml') or filename.endswith('.yml'):
        return 'yaml'
    elif filename.endswith('.toml'):
        return 'toml'
    else:
        return 'text'


@router.get("/file")
async def read_file(path: str) -> FileContent:
    """Read a file's content"""
    try:
        file_path = Path(path)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {path}")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail=f"Not a file: {path}")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_format = get_file_format(file_path.name)
        
        return FileContent(
            path=str(file_path.absolute()),
            content=content,
            format=file_format
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


@router.post("/file")
async def save_file(request: FileSaveRequest) -> dict:
    """Save content to a file"""
    try:
        file_path = Path(request.path)
        
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(request.content)
        
        return {
            "success": True,
            "path": str(file_path.absolute()),
            "message": f"File saved successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")


@router.post("/list")
async def list_files(request: FileListRequest) -> FileListResponse:
    """List files and directories in a directory matching extensions.
    
    If extensions is None or empty, returns all files and all directories.
    Otherwise, only returns files matching the extensions and all directories.
    """
    try:
        dir_path = Path(request.directory)
        
        if not dir_path.exists():
            raise HTTPException(status_code=404, detail=f"Directory not found: {request.directory}")
        
        if not dir_path.is_dir():
            raise HTTPException(status_code=400, detail=f"Not a directory: {request.directory}")
        
        files = []
        
        # Skip hidden directories
        skip_patterns = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', '.conda', '.idea'}
        
        # Walk through directory (non-recursive for now)
        for item in dir_path.iterdir():
            # Skip hidden files/directories
            if item.name.startswith('.') or item.name in skip_patterns:
                continue
                
            if item.is_dir():
                # Always include directories for navigation
                stat = item.stat()
                files.append(FileInfo(
                    name=item.name,
                    path=str(item.absolute()),
                    format='directory',
                    size=0,
                    modified=stat.st_mtime,
                    is_dir=True
                ))
            elif item.is_file():
                # Check if extension matches (if extensions provided)
                if request.extensions:
                    matches = any(item.name.endswith(ext) for ext in request.extensions)
                    if not matches:
                        continue
                
                stat = item.stat()
                files.append(FileInfo(
                    name=item.name,
                    path=str(item.absolute()),
                    format=get_file_format(item.name),
                    size=stat.st_size,
                    modified=stat.st_mtime,
                    is_dir=False
                ))
        
        # Sort: directories first, then by name
        files.sort(key=lambda f: (not f.is_dir, f.name.lower()))
        
        return FileListResponse(
            directory=str(dir_path.absolute()),
            files=files
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")


@router.post("/list-recursive")
async def list_files_recursive(request: FileListRequest) -> FileListResponse:
    """List files in a directory recursively"""
    try:
        dir_path = Path(request.directory)
        
        if not dir_path.exists():
            raise HTTPException(status_code=404, detail=f"Directory not found: {request.directory}")
        
        if not dir_path.is_dir():
            raise HTTPException(status_code=400, detail=f"Not a directory: {request.directory}")
        
        files = []
        
        # Walk through directory recursively
        for root, dirs, filenames in os.walk(dir_path):
            # Skip hidden directories and common excludes
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', '.conda']]
            
            for filename in filenames:
                # Check if extension matches
                matches = any(filename.endswith(ext) for ext in request.extensions)
                if matches:
                    file_path = Path(root) / filename
                    stat = file_path.stat()
                    
                    # Use relative path from base directory
                    rel_path = file_path.relative_to(dir_path)
                    
                    files.append(FileInfo(
                        name=str(rel_path),
                        path=str(file_path.absolute()),
                        format=get_file_format(filename),
                        size=stat.st_size,
                        modified=stat.st_mtime
                    ))
        
        # Sort by name
        files.sort(key=lambda f: f.name)
        
        return FileListResponse(
            directory=str(dir_path.absolute()),
            files=files
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")


class TreeNode(BaseModel):
    """A node in the file tree"""
    name: str
    path: str
    type: str  # 'file' or 'folder'
    format: Optional[str] = None
    size: Optional[int] = None
    modified: Optional[float] = None
    children: List["TreeNode"] = []


# Required for recursive model
TreeNode.model_rebuild()


class FileTreeResponse(BaseModel):
    """Response with file tree structure"""
    directory: str
    tree: List[TreeNode]
    total_files: int


@router.post("/list-tree")
async def list_files_tree(request: FileListRequest) -> FileTreeResponse:
    """List files in a directory as a tree structure"""
    try:
        dir_path = Path(request.directory)
        
        if not dir_path.exists():
            raise HTTPException(status_code=404, detail=f"Directory not found: {request.directory}")
        
        if not dir_path.is_dir():
            raise HTTPException(status_code=400, detail=f"Not a directory: {request.directory}")
        
        # Build tree structure
        tree_dict: dict = {}
        total_files = 0
        
        # Walk through directory recursively
        for root, dirs, filenames in os.walk(dir_path):
            # Skip hidden directories and common excludes
            dirs[:] = sorted([d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', '.conda', '.git']])
            
            for filename in sorted(filenames):
                # Skip hidden files
                if filename.startswith('.'):
                    continue
                    
                # Check if extension matches
                matches = any(filename.endswith(ext) for ext in request.extensions)
                if matches:
                    file_path = Path(root) / filename
                    try:
                        stat = file_path.stat()
                    except (OSError, PermissionError):
                        continue
                    
                    # Get relative path parts
                    rel_path = file_path.relative_to(dir_path)
                    parts = rel_path.parts
                    
                    # Navigate/create the tree structure
                    current = tree_dict
                    for i, part in enumerate(parts[:-1]):  # All except the filename
                        if part not in current:
                            current[part] = {"__is_folder__": True, "__children__": {}}
                        current = current[part]["__children__"]
                    
                    # Add the file
                    filename_part = parts[-1]
                    current[filename_part] = {
                        "__is_folder__": False,
                        "path": str(file_path.absolute()),
                        "format": get_file_format(filename),
                        "size": stat.st_size,
                        "modified": stat.st_mtime
                    }
                    total_files += 1
        
        def dict_to_tree_nodes(d: dict, parent_path: str = "") -> List[TreeNode]:
            """Convert nested dict to TreeNode list"""
            nodes = []
            
            # Sort: folders first, then files, both alphabetically
            items = sorted(d.items(), key=lambda x: (not x[1].get("__is_folder__", False), x[0].lower()))
            
            for name, info in items:
                if info.get("__is_folder__"):
                    # It's a folder
                    folder_path = os.path.join(parent_path, name) if parent_path else name
                    children = dict_to_tree_nodes(info.get("__children__", {}), folder_path)
                    nodes.append(TreeNode(
                        name=name,
                        path=folder_path,
                        type="folder",
                        children=children
                    ))
                else:
                    # It's a file
                    nodes.append(TreeNode(
                        name=name,
                        path=info["path"],
                        type="file",
                        format=info.get("format"),
                        size=info.get("size"),
                        modified=info.get("modified")
                    ))
            
            return nodes
        
        tree = dict_to_tree_nodes(tree_dict)
        
        return FileTreeResponse(
            directory=str(dir_path.absolute()),
            tree=tree,
            total_files=total_files
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")


@router.get("/validate")
async def validate_file(path: str) -> dict:
    """Validate a NormCode file's syntax"""
    try:
        file_path = Path(path)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_format = get_file_format(file_path.name)
        errors = []
        warnings = []
        
        # Basic validation based on format
        if file_format in ['json', 'nc-json', 'nci']:
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                errors.append(f"JSON syntax error at line {e.lineno}: {e.msg}")
        
        elif file_format in ['ncd', 'ncn', 'ncdn']:
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if not stripped:
                    continue
                
                # Check for basic NormCode structure markers
                if file_format in ['ncd', 'ncdn']:
                    # Check for common issues
                    if '<-' in line and '<=' in line:
                        warnings.append(f"Line {i}: Mixed <- and <= on same line")
                    
                    # Check indentation consistency
                    indent = len(line) - len(line.lstrip())
                    if indent % 4 != 0 and indent % 2 != 0:
                        warnings.append(f"Line {i}: Unusual indentation ({indent} spaces)")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "format": file_format
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating file: {str(e)}")


# ============================================================================
# Parser Endpoints - For structured editing and format conversion
# ============================================================================

class ParseRequest(BaseModel):
    """Request to parse file content"""
    content: str
    format: str = "ncd"  # ncd, ncdn
    ncn_content: Optional[str] = None  # Optional NCN content for NCD files


class ConvertRequest(BaseModel):
    """Request to convert between formats"""
    content: str
    from_format: str  # ncd, ncn, ncdn
    to_format: str    # ncd, ncn, ncdn, json, nci


class ParsedLine(BaseModel):
    """A parsed line with flow index"""
    flow_index: Optional[str]
    type: str  # main, comment, inline_comment
    depth: int
    nc_main: Optional[str] = None
    nc_comment: Optional[str] = None
    ncn_content: Optional[str] = None


class ParseResponse(BaseModel):
    """Response with parsed lines"""
    lines: List[dict]
    parser_available: bool


@router.post("/parse")
async def parse_content(request: ParseRequest) -> ParseResponse:
    """Parse NormCode content into structured JSON with flow indices"""
    try:
        from services.parser_service import get_parser_service
        
        parser = get_parser_service()
        
        if not parser.is_available:
            return ParseResponse(
                lines=[],
                parser_available=False
            )
        
        if request.format == "ncdn":
            parsed = parser.parse_ncdn(request.content)
        else:
            ncn = request.ncn_content or ""
            parsed = parser.parse_ncd(request.content, ncn)
        
        return ParseResponse(
            lines=parsed.get('lines', []),
            parser_available=True
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing content: {str(e)}")


@router.post("/convert")
async def convert_format(request: ConvertRequest) -> dict:
    """Convert content between NormCode formats"""
    try:
        from services.parser_service import get_parser_service
        
        parser = get_parser_service()
        
        if not parser.is_available:
            raise HTTPException(status_code=503, detail="Parser not available")
        
        result = parser.convert_format(
            request.content,
            request.from_format,
            request.to_format
        )
        
        return {
            "content": result,
            "from_format": request.from_format,
            "to_format": request.to_format
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error converting format: {str(e)}")


@router.post("/preview")
async def get_previews(request: ParseRequest) -> dict:
    """Get content previewed in all formats (NCD, NCN, NCDN, JSON, NCI)"""
    try:
        from services.parser_service import get_parser_service
        
        parser = get_parser_service()
        
        if not parser.is_available:
            return {
                "parser_available": False,
                "previews": {}
            }
        
        # Parse the content first
        if request.format == "ncdn":
            parsed = parser.parse_ncdn(request.content)
        else:
            ncn = request.ncn_content or ""
            parsed = parser.parse_ncd(request.content, ncn)
        
        # Generate all previews
        ncd_ncn = parser.serialize_to_ncd_ncn(parsed)
        
        previews = {
            "ncd": ncd_ncn.get('ncd', ''),
            "ncn": ncd_ncn.get('ncn', ''),
            "ncdn": parser.serialize_to_ncdn(parsed),
            "json": json.dumps(parsed, indent=2, ensure_ascii=False),
        }
        
        # Try to generate NCI (may fail for incomplete content)
        try:
            nci = parser.to_nci(parsed)
            previews["nci"] = json.dumps(nci, indent=2, ensure_ascii=False)
        except Exception:
            previews["nci"] = "// NCI generation requires complete inference structure"
        
        return {
            "parser_available": True,
            "previews": previews
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating previews: {str(e)}")


@router.get("/parser-status")
async def get_parser_status() -> dict:
    """Check if the parser is available"""
    try:
        from services.parser_service import get_parser_service
        
        parser = get_parser_service()
        
        return {
            "available": parser.is_available,
            "message": "Parser ready" if parser.is_available else "Parser not available - unified_parser.py not found"
        }
    
    except Exception as e:
        return {
            "available": False,
            "message": f"Error loading parser: {str(e)}"
        }

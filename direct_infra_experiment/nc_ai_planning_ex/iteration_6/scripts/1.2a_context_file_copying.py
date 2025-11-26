from pathlib import Path
import json


def main(input_1, body):
    """
    Copy files from source paths to target paths in context_store.
    
    This function leverages the Body infrastructure for file operations:
    - FileSystemTool for consistent file operations (handles base_dir automatically via body.file_system)
    - Other tools (formatter, composition, etc.) available if needed
    
    Args:
        file_mapping: Dictionary mapping source file paths to target paths
                     Example: {"prompt.md": "./context_store/raw--prompt.md"}
        body: Body instance providing access to infrastructure tools.
              Uses body.file_system for all file operations:
              - body.file_system.read(source_path) - reads relative to body.file_system.base_dir
              - body.file_system.save(content, target_path) - saves relative to body.file_system.base_dir
              - body.file_system.exists(path) - checks relative to body.file_system.base_dir
    
    Returns:
        Dictionary with:
        - "copied_files": List of dicts with source_path, target_path, status, error_message
        - "context_store_directory": Path to context_store directory
    """

    file_mapping = input_1
    # Allow file_mapping to be provided as JSON string or dict
    if isinstance(file_mapping, str):
        try:
            file_mapping = json.loads(file_mapping)
        except json.JSONDecodeError:
            return {
                "copied_files": [],
                "context_store_directory": "./context_store",
                "error": "Invalid JSON in file_mapping",
            }
    copied_files = []
    context_store_dir = None
    
    # Process each file in the mapping
    for source_path, target_path in file_mapping.items():
        try:
            # Set context_store directory from first target
            if context_store_dir is None:
                # Extract directory from target_path (handle both relative and absolute)
                target_dir = Path(target_path).parent
                context_store_dir = str(target_dir)
            
            # Read source file using FileSystemTool
            read_result = body.file_system.read(source_path)
            if read_result.get("status") != "success":
                copied_files.append({
                    "source_path": source_path,
                    "target_path": target_path,
                    "status": "error",
                    "error_message": read_result.get("message", "Failed to read source file")
                })
                continue
            content = read_result.get("content")
            
            # Save to target using FileSystemTool (handles directory creation automatically)
            save_result = body.file_system.save(content, target_path)
            if save_result.get("status") != "success":
                copied_files.append({
                    "source_path": source_path,
                    "target_path": target_path,
                    "status": "error",
                    "error_message": save_result.get("message", "Unknown error saving file")
                })
                continue
            
            # Verify copy was successful
            target_exists = body.file_system.exists(target_path)
            
            if not target_exists:
                copied_files.append({
                    "source_path": source_path,
                    "target_path": target_path,
                    "status": "error",
                    "error_message": "File copy completed but target file not found"
                })
                continue
            
            copied_files.append({
                "source_path": source_path,
                "target_path": target_path,
                "status": "success",
                "error_message": None
            })
            
        except PermissionError as e:
            copied_files.append({
                "source_path": source_path,
                "target_path": target_path,
                "status": "error",
                "error_message": f"Permission denied: {str(e)}"
            })
        except OSError as e:
            copied_files.append({
                "source_path": source_path,
                "target_path": target_path,
                "status": "error",
                "error_message": f"OS error: {str(e)}"
            })
        except Exception as e:
            copied_files.append({
                "source_path": source_path,
                "target_path": target_path,
                "status": "error",
                "error_message": f"Unexpected error: {str(e)}"
            })
    
    return {
        "copied_files": copied_files,
        "context_store_directory": context_store_dir or "./context_store"
    }


if __name__ == "__main__":
    # Example usage for testing
    test_mapping = {
        "prompt.md": "./context_store/raw--prompt.md",
        "test_file.txt": "./context_store/raw--test_file.txt"
    }
    
    # Test with Body (required)
    try:
        from infra._agent._body import Body
        body = Body(base_dir=".")
        result = main(test_mapping, body=body)
        print("Result:", result)
    except ImportError:
        print("Body not available for testing")


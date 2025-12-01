"""
Streamlit-native file system tool for NormCode orchestration.

This tool replicates the functionality of the core FileSystemTool but resides
within the Streamlit app structure to allow for future UI integrations
(e.g., showing file operations in the UI, toast notifications, etc.).
"""

import os
import logging
import json
import streamlit as st
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class StreamlitFileSystemTool:
    def __init__(self, base_dir: str | None = None):
        """
        Initializes the StreamlitFileSystemTool.

        Args:
            base_dir (str | None): An optional designated directory path to use as the
                                   base for all file operations.
        """
        self.base_dir = base_dir
    
    def _log_operation(self, operation_type: str, location: str, status: str, details: str = ""):
        """Log a file operation to session state for monitoring."""
        # Check if session state exists and has the log
        if hasattr(st, 'session_state') and 'file_operations_log' in st.session_state:
            st.session_state.file_operations_log.append({
                'timestamp': datetime.now().isoformat(),
                'operation': operation_type,
                'location': location,
                'status': status,
                'details': details
            })

    def _get_base_dir(self) -> Path:
        """Determines the base directory for file operations."""
        if self.base_dir:
            return Path(self.base_dir)
        else:
            # Fallback to a sensible default if no base_dir is provided
            # In the Streamlit app context, this might default to a temp dir or the app dir
            return Path(os.getcwd())

    def _get_memorized_file_path(self) -> Path:
        """Gets the full path to the default memorized.json file."""
        return self._get_base_dir() / 'memorized.json'

    def save(self, content: str | None, location: str) -> dict:
        """
        Saves content to a specified file location.

        Args:
            content (str): The content to be saved.
            location (str): The file path where the content will be saved. Can be
                            absolute, or relative to the base_dir.

        Returns:
            dict: A dictionary with the status of the operation.
        """
        if content is None:
            err_msg = f"Content cannot be None. Failed to save to {location}."
            logger.error(err_msg)
            self._log_operation('SAVE', location, 'ERROR', err_msg)
            return {"status": "error", "message": err_msg}

        try:
            file_path = Path(location) if Path(location).is_absolute() else self._get_base_dir() / location
            # Ensure the directory exists
            dir_path = file_path.parent
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")

            # Write the content to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Successfully saved content to {file_path}")
            
            # Log the operation
            self._log_operation('SAVE', str(file_path), 'SUCCESS', f'{len(content)} chars')
                
            return {"status": "success", "location": str(file_path)}
        except Exception as e:
            logger.error(f"Failed to save file at {location}: {e}")
            self._log_operation('SAVE', location, 'ERROR', str(e))
            return {"status": "error", "message": str(e)}

    def save_from_dict(self, content_dict: dict, directory: str) -> dict:
        """
        Saves the contents of a dictionary to multiple files in a specified directory.

        Each key in the dictionary is used as a filename, and the corresponding value
        is saved as the content of that file.

        Args:
            content_dict (dict): The dictionary containing filename-content pairs.
            directory (str): The directory where the files will be saved. Can be
                             absolute, or relative to the base_dir.

        Returns:
            dict: A dictionary with the status and a list of saved file locations.
        """
        if not isinstance(content_dict, dict):
            return {"status": "error", "message": "content_dict must be a dictionary."}

        saved_locations = []
        try:
            base_save_path = Path(directory) if Path(directory).is_absolute() else self._get_base_dir() / directory
            
            for filename, content in content_dict.items():
                if not isinstance(content, str):
                    logger.warning(f"Skipping non-string content for filename '{filename}'.")
                    continue
                
                # Use the save method to handle directory creation and writing
                result = self.save(content, str(base_save_path / filename))
                if result["status"] == "success":
                    saved_locations.append(result["location"])
                else:
                    # If any file fails to save, return an error immediately
                    return {"status": "error", "message": f"Failed to save {filename}: {result['message']}", "saved_locations": saved_locations}

            return {"status": "success", "saved_locations": saved_locations, "saved_location": saved_locations[0] if saved_locations else None}
        except Exception as e:
            logger.error(f"An error occurred in save_from_dict: {e}")
            return {"status": "error", "message": str(e)}

    def read(self, location: str) -> dict:
        """
        Reads content from a specified file location.

        Args:
            location (str): The file path to read from. Can be absolute, or relative
                            to the base_dir.

        Returns:
            dict: A dictionary with the status and content of the file.
        """
        try:
            file_path = Path(location) if Path(location).is_absolute() else self._get_base_dir() / location
            if not file_path.exists():
                logger.warning(f"File not found at {file_path}")
                self._log_operation('READ', str(file_path), 'ERROR', 'File not found')
                return {"status": "error", "message": f"File not found at {file_path}"}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.info(f"Successfully read content from {file_path}")
            self._log_operation('READ', str(file_path), 'SUCCESS', f'{len(content)} chars')
            return {"status": "success", "content": content}
        except Exception as e:
            logger.error(f"Failed to read file at {location}: {e}")
            self._log_operation('READ', location, 'ERROR', str(e))
            return {"status": "error", "message": str(e)}

    def exists(self, location: str) -> bool:
        """
        Checks if a file exists at the specified location.

        Args:
            location (str): The file path to check. Can be absolute, or relative
                            to the base_dir.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        try:
            file_path = Path(location) if Path(location).is_absolute() else self._get_base_dir() / location
            exists = file_path.exists()
            self._log_operation('EXISTS', str(file_path), 'SUCCESS', f'exists={exists}')
            return exists
        except Exception as e:
            logger.error(f"Error checking for file existence at {location}: {e}")
            self._log_operation('EXISTS', location, 'ERROR', str(e))
            return False

    def read_memorized_value(self, content: str) -> dict:
        """
        Reads a value from a JSON-based memory file.

        The `content` can be a simple key, or a JSON string specifying both
        a `key` and an alternate `location` for the memory file.

        Args:
            content (str): The key or JSON string to resolve.

        Returns:
            dict: A dictionary with the status and the retrieved value.
        """
        file_path = self._get_memorized_file_path()
        lookup_key = content
        try:
            params = json.loads(content)
            if isinstance(params, dict) and "key" in params:
                lookup_key = params["key"]
                if "location" in params:
                    location = params["location"]
                    # If location is relative, it's relative to the base dir
                    file_path = Path(location) if Path(location).is_absolute() else self._get_base_dir() / location
        except (json.JSONDecodeError, TypeError):
            pass  # Not JSON, treat content as key
        except Exception as e:
            logger.error(f"Error processing memorized parameter content '{content}': {e}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            value = data.get(lookup_key)
            if value is not None:
                self._log_operation('MEMORIZED_READ', str(file_path), 'SUCCESS', f'key={lookup_key}')
                return {"status": "success", "content": value}
            else:
                self._log_operation('MEMORIZED_READ', str(file_path), 'ERROR', f'Key not found: {lookup_key}')
                return {"status": "error", "message": f"Key '{lookup_key}' not found in {file_path}"}

        except FileNotFoundError:
            self._log_operation('MEMORIZED_READ', str(file_path), 'ERROR', 'File not found')
            return {"status": "error", "message": f"Memorized parameters file not found at {file_path}"}
        except json.JSONDecodeError:
            self._log_operation('MEMORIZED_READ', str(file_path), 'ERROR', 'Invalid JSON')
            return {"status": "error", "message": f"Failed to decode JSON from {file_path}"}
        except Exception as e:
            self._log_operation('MEMORIZED_READ', str(file_path), 'ERROR', str(e))
            return {"status": "error", "message": f"Failed to read memorized parameter: {e}"}

    def save_memorized_value(self, content: str) -> dict:
        """
        Saves a key-value pair to a JSON-based memory file.

        The `content` is a JSON string that must contain a `key` and `value`,
        and can optionally include a `location` for the memory file.

        Args:
            content (str): The JSON string with the data to save.

        Returns:
            dict: A dictionary with the status of the operation.
        """
        file_path = self._get_memorized_file_path()
        try:
            params = json.loads(content)
            if not isinstance(params, dict) or "key" not in params or "value" not in params:
                return {"status": "error", "message": "Content must be a JSON object with 'key' and 'value'."}
            
            key = params["key"]
            value = params["value"]
            if "location" in params:
                location = params["location"]
                file_path = Path(location) if Path(location).is_absolute() else self._get_base_dir() / location

        except (json.JSONDecodeError, TypeError):
            return {"status": "error", "message": "Invalid JSON content provided."}
        
        try:
            data = {}
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        # File is corrupted or not JSON, will be overwritten
                        logger.warning(f"Could not decode JSON from {file_path}. The file will be overwritten.")
                        pass
            
            data[key] = value

            dir_path = os.path.dirname(file_path)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            
            self._log_operation('MEMORIZED_SAVE', str(file_path), 'SUCCESS', f'key={key}')
            return {"status": "success", "message": f"Successfully saved key '{key}' to {file_path}"}
        
        except Exception as e:
            self._log_operation('MEMORIZED_SAVE', str(file_path), 'ERROR', str(e))
            return {"status": "error", "message": f"Failed to save memorized value: {e}"}


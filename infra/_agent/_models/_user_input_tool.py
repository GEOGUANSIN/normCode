import sys
import logging
import os
import subprocess
from typing import Callable, Any, Dict

# Attempt to import tkinter for simple GUI dialogs (non-iterative)
try:
    import tkinter as tk
    from tkinter import messagebox, simpledialog
    _TKINTER_AVAILABLE = True
except ImportError:
    _TKINTER_AVAILABLE = False

logger = logging.getLogger(__name__)


def _is_gui_available() -> bool:
    """Checks if a GUI can be created."""
    if not _TKINTER_AVAILABLE:
        return False
    # On Windows, PowerShell is a better check for advanced UI
    if sys.platform == "win32":
        return True
    try:
        # Fallback for non-Windows
        root = tk.Tk()
        root.withdraw()
        root.destroy()
        return True
    except Exception:
        return False


class UserInputTool:
    _gui_checked = False
    _can_use_gui = False

    def _check_gui(self):
        """Checks for GUI availability once and caches the result."""
        if not UserInputTool._gui_checked:
            UserInputTool._can_use_gui = _is_gui_available()
            UserInputTool._gui_checked = True
            logger.debug(f"GUI available: {UserInputTool._can_use_gui}")

    def create_input_function(self, prompt_key: str = "prompt_text") -> Callable:
        config = {"interaction_type": "simple_text", "prompt_key": prompt_key}
        return self.create_interaction(**config)

    def create_interaction(self, **config: Any) -> Callable:
        self._check_gui()

        def interaction_fn(**kwargs: Any) -> Any:
            prompt_key = config.get("prompt_key", "prompt_text")
            prompt_text = kwargs.get(prompt_key, "Enter input: ")
            interaction_type = config.get("interaction_type", "simple_text")

            is_interactive = sys.stdin.isatty() or UserInputTool._can_use_gui
            if not is_interactive:
                logging.warning("Non-interactive session detected. Returning default.")
                return config.get("non_interactive_default", "Default response")

            if UserInputTool._can_use_gui:
                return self._handle_gui_interaction(prompt_text, interaction_type, config)
            else:
                return self._handle_cli_interaction(prompt_text, interaction_type, config)

        return interaction_fn

    def _handle_gui_interaction(self, prompt: str, interaction_type: str, config: Dict) -> Any:
        logger.debug(f"Handling GUI interaction: {interaction_type}")
        title = config.get("title", "User Input Required")

        if interaction_type == "multi_file_input" and sys.platform == "win32":
            return self._handle_powershell_multi_file_input(prompt)

        # Fallback to tkinter for simple dialogs
        try:
            root = tk.Tk()
            root.withdraw()
            if interaction_type == "confirm":
                return messagebox.askyesno(title, prompt)
            return simpledialog.askstring(title, prompt)
        finally:
            if 'root' in locals() and root.winfo_exists():
                root.destroy()

    def _handle_powershell_multi_file_input(self, prompt: str) -> list[str]:
        """
        Uses a PowerShell script to launch a native Windows multi-file selection dialog.
        This is more robust than a custom tkinter implementation.
        """
        logger.debug("Using PowerShell for multi-file selection.")
        script = f"""
        Add-Type -AssemblyName System.Windows.Forms
        $openFileDialog = New-Object System.Windows.Forms.OpenFileDialog
        $openFileDialog.Title = "{prompt}"
        $openFileDialog.Multiselect = $true
        if ($openFileDialog.ShowDialog() -eq 'OK') {{
            $openFileDialog.FileNames
        }}
        """
        try:
            process = subprocess.run(
                ["powershell", "-Command", script],
                capture_output=True,
                text=True,
                check=True
            )
            # The output is a string with newlines, so we split it
            files = process.stdout.strip().split('\\r\\n')
            return [f for f in files if f]  # Filter out empty strings
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"PowerShell script failed: {e}")
            logger.warning("Falling back to CLI for multi-file input.")
            return self._handle_cli_multi_file_input(prompt, {})

    def _handle_cli_interaction(self, prompt: str, interaction_type: str, config: Dict) -> Any:
        logger.debug(f"Handling CLI interaction: {interaction_type}")
        if interaction_type == "confirm":
            return self._handle_cli_confirm(prompt, config)
        elif interaction_type == "validated_text":
            return self._handle_cli_validated_text(prompt, config)
        elif interaction_type == "multi_file_input":
            return self._handle_cli_multi_file_input(prompt, config)
        else:
            return input(prompt + ": ")

    def _handle_cli_confirm(self, prompt: str, config: Dict) -> bool:
        default = config.get("default")
        suffix = " (Y/n)" if default else " (y/N)" if default is False else " (y/n)"
        while True:
            response = input(prompt + suffix + " ").strip().lower()
            if response in ["y", "yes"]: return True
            if response in ["n", "no"]: return False
            if response == "" and default is not None: return default
            print("Please answer with 'y' or 'n'.")

    def _handle_cli_multi_file_input(self, prompt: str, config: Dict) -> list[str]:
        print(prompt)
        print("Enter file paths one per line. Press Enter on an empty line to finish.")
        paths = []
        while True:
            path = input("> ").strip()
            if not path: break
            if os.path.exists(path):
                paths.append(path)
            else:
                print(f"Warning: File not found at '{path}'. It will be skipped.")
        return paths

    def _handle_cli_validated_text(self, prompt: str, config: Dict) -> str:
        validation_config = config.get("validation", {})
        validation_type = validation_config.get("type")
        error_message = validation_config.get("error_message", "Invalid input.")
        default = config.get("default")
        prompt_with_default = f"{prompt} [{default}]" if default else prompt
        prompt_with_default += ": "
        while True:
            response = input(prompt_with_default).strip() or default
            if not validation_type: return response
            if validation_type == "file_exists" and os.path.exists(response): return response
            print(error_message)

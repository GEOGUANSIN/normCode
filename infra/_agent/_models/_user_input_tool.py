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
    
    def create_text_editor_function(self, prompt_key: str = "prompt_text", initial_text_key: str = "initial_text") -> Callable:
        """
        Creates a function that opens a text editor for the user to modify text.
        
        Args:
            prompt_key: The key in kwargs that contains the prompt to display
            initial_text_key: The key in kwargs that contains the initial text to edit
        
        Returns:
            A callable that opens a text editor and returns the modified text
        """
        config = {
            "interaction_type": "text_editor",
            "prompt_key": prompt_key,
            "initial_text_key": initial_text_key
        }
        return self.create_interaction(**config)

    def create_interaction(self, **config: Any) -> Callable:
        self._check_gui()

        def interaction_fn(**kwargs: Any) -> Any:
            prompt_key = config.get("prompt_key", "prompt_text")
            prompt_text = kwargs.get(prompt_key, "Enter input: ")
            interaction_type = config.get("interaction_type", "simple_text")
            
            # For text_editor type, get the initial text
            if interaction_type == "text_editor":
                initial_text_key = config.get("initial_text_key", "initial_text")
                initial_text = kwargs.get(initial_text_key, "")
                # Add initial_text to config for handlers
                config_with_text = {**config, "initial_text": initial_text}
            else:
                config_with_text = config

            is_interactive = sys.stdin.isatty() or UserInputTool._can_use_gui
            if not is_interactive:
                logging.warning("Non-interactive session detected. Returning default.")
                return config.get("non_interactive_default", "Default response")

            if UserInputTool._can_use_gui:
                return self._handle_gui_interaction(prompt_text, interaction_type, config_with_text)
            else:
                return self._handle_cli_interaction(prompt_text, interaction_type, config_with_text)

        return interaction_fn

    def _handle_gui_interaction(self, prompt: str, interaction_type: str, config: Dict) -> Any:
        logger.debug(f"Handling GUI interaction: {interaction_type}")
        title = config.get("title", "User Input Required")

        if interaction_type == "multi_file_input" and sys.platform == "win32":
            return self._handle_powershell_multi_file_input(prompt)
        
        if interaction_type == "text_editor":
            initial_text = config.get("initial_text", "")
            return self._handle_text_editor_interaction(initial_text, prompt)

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
        Uses a PowerShell script to launch a native Windows multi-file selection dialog
        with a persistent GUI window showing accumulated files.
        """
        logger.debug("Using PowerShell for multi-file selection with GUI buffer.")
        
        try:
            import tkinter as tk
            from tkinter import Listbox, Scrollbar, Button, Label, VERTICAL, END, MULTIPLE
        except ImportError:
            logger.warning("Tkinter not available, falling back to CLI.")
            return self._handle_cli_multi_file_input(prompt, {})
        
        selected_files = []
        file_set = set()  # To prevent duplicates
        
        def add_files():
            """Open PowerShell file dialog and add selected files to the list."""
            script = f"""
            Add-Type -AssemblyName System.Windows.Forms
            $openFileDialog = New-Object System.Windows.Forms.OpenFileDialog
            $openFileDialog.Title = "Select files to add"
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
                new_files = process.stdout.strip().splitlines()
                
                for file_path in new_files:
                    if file_path and file_path not in file_set:
                        selected_files.append(file_path)
                        file_set.add(file_path)
                        listbox.insert(END, file_path)
                
                count_label.config(text=f"Files selected: {len(selected_files)}")
                logger.debug(f"Added {len(new_files)} new files. Total: {len(selected_files)}")
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                logger.error(f"PowerShell script failed: {e}")
        
        def remove_files():
            """Remove selected files from the list."""
            selection = listbox.curselection()
            if not selection:
                return
            
            # Remove in reverse order to maintain correct indices
            for index in reversed(selection):
                file_path = listbox.get(index)
                listbox.delete(index)
                selected_files.remove(file_path)
                file_set.discard(file_path)
            
            count_label.config(text=f"Files selected: {len(selected_files)}")
            logger.debug(f"Removed {len(selection)} files. Remaining: {len(selected_files)}")
        
        def confirm_selection():
            """Close the window and return the selected files."""
            root.quit()
            root.destroy()
        
        # Create the GUI window
        root = tk.Tk()
        root.title("File Selection")
        root.geometry("700x500")
        
        # Prompt label
        prompt_label = Label(root, text=prompt, font=("Arial", 10), wraplength=680, justify="left")
        prompt_label.pack(pady=10)
        
        # Count label
        count_label = Label(root, text="Files selected: 0", font=("Arial", 9, "bold"))
        count_label.pack(pady=5)
        
        # Listbox with scrollbar
        frame = tk.Frame(root)
        frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        scrollbar = Scrollbar(frame, orient=VERTICAL)
        listbox = Listbox(frame, yscrollcommand=scrollbar.set, selectmode=MULTIPLE, width=80, height=15)
        scrollbar.config(command=listbox.yview)
        scrollbar.pack(side="right", fill="y")
        listbox.pack(side="left", fill="both", expand=True)
        
        # Buttons
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)
        
        add_button = Button(button_frame, text="Add Files", command=add_files, width=15, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
        add_button.pack(side="left", padx=5)
        
        remove_button = Button(button_frame, text="Remove Selected", command=remove_files, width=15, bg="#f44336", fg="white", font=("Arial", 10, "bold"))
        remove_button.pack(side="left", padx=5)
        
        confirm_button = Button(button_frame, text="Confirm", command=confirm_selection, width=15, bg="#2196F3", fg="white", font=("Arial", 10, "bold"))
        confirm_button.pack(side="left", padx=5)
        
        # Run the GUI
        root.mainloop()
        
        logger.debug(f"Final file selection: {selected_files}")
        return selected_files

    def _handle_text_editor_interaction(self, initial_text: str, prompt: str = "Edit the text below:") -> str:
        """
        Opens a text editor window where the user can view and modify text content.
        Returns the modified text when the user clicks Save.
        """
        logger.debug("Opening text editor for user modification.")
        
        try:
            import tkinter as tk
            from tkinter import Text, Button, Label, Scrollbar, VERTICAL, END
        except ImportError:
            logger.warning("Tkinter not available, falling back to CLI.")
            return self._handle_cli_text_editor(initial_text, prompt)
        
        result_text = [initial_text]  # Using list to avoid closure issues
        
        def save_and_close():
            """Save the current text and close the window."""
            result_text[0] = text_widget.get("1.0", END).rstrip('\n')
            logger.debug(f"User saved text ({len(result_text[0])} characters)")
            root.quit()
            root.destroy()
        
        def cancel():
            """Close without saving (returns original text)."""
            logger.debug("User cancelled text editing")
            root.quit()
            root.destroy()
        
        # Create the GUI window
        root = tk.Tk()
        root.title("Text Editor")
        root.geometry("800x600")
        
        # Prompt label
        prompt_label = Label(root, text=prompt, font=("Arial", 10, "bold"), wraplength=780, justify="left")
        prompt_label.pack(pady=10)
        
        # Text editor with scrollbar
        editor_frame = tk.Frame(root)
        editor_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        scrollbar = Scrollbar(editor_frame, orient=VERTICAL)
        text_widget = Text(
            editor_frame, 
            yscrollcommand=scrollbar.set, 
            wrap="word",
            font=("Consolas", 10),
            padx=10,
            pady=10
        )
        scrollbar.config(command=text_widget.yview)
        scrollbar.pack(side="right", fill="y")
        text_widget.pack(side="left", fill="both", expand=True)
        
        # Insert initial text
        text_widget.insert("1.0", initial_text)
        
        # Character count label
        char_count_label = Label(root, text=f"Characters: {len(initial_text)}", font=("Arial", 9))
        char_count_label.pack(pady=5)
        
        def update_char_count(event=None):
            """Update character count as user types."""
            current_text = text_widget.get("1.0", END).rstrip('\n')
            char_count_label.config(text=f"Characters: {len(current_text)}")
        
        text_widget.bind("<KeyRelease>", update_char_count)
        
        # Buttons
        button_frame = tk.Frame(root)
        button_frame.pack(pady=15)
        
        save_button = Button(
            button_frame, 
            text="Save", 
            command=save_and_close, 
            width=15, 
            bg="#4CAF50", 
            fg="white", 
            font=("Arial", 11, "bold")
        )
        save_button.pack(side="left", padx=10)
        
        cancel_button = Button(
            button_frame, 
            text="Cancel", 
            command=cancel, 
            width=15, 
            bg="#9E9E9E", 
            fg="white", 
            font=("Arial", 11, "bold")
        )
        cancel_button.pack(side="left", padx=10)
        
        # Run the GUI
        root.mainloop()
        
        return result_text[0]
    
    def _handle_cli_text_editor(self, initial_text: str, prompt: str) -> str:
        """
        CLI fallback for text editing. Allows multi-line input with a special terminator.
        """
        print(prompt)
        print("\n--- Current Text ---")
        print(initial_text)
        print("--- End of Current Text ---\n")
        print("Enter your modified text below. Type '###DONE###' on a new line to finish:")
        
        lines = []
        while True:
            line = input()
            if line.strip() == "###DONE###":
                break
            lines.append(line)
        
        return "\n".join(lines)

    def _handle_cli_interaction(self, prompt: str, interaction_type: str, config: Dict) -> Any:
        logger.debug(f"Handling CLI interaction: {interaction_type}")
        if interaction_type == "confirm":
            return self._handle_cli_confirm(prompt, config)
        elif interaction_type == "validated_text":
            return self._handle_cli_validated_text(prompt, config)
        elif interaction_type == "multi_file_input":
            return self._handle_cli_multi_file_input(prompt, config)
        elif interaction_type == "text_editor":
            initial_text = config.get("initial_text", "")
            return self._handle_cli_text_editor(initial_text, prompt)
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

import re
import uuid
import logging
from typing import Any, NamedTuple, Optional, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from infra._agent._body import Body

logger = logging.getLogger(__name__)

class PerceptualSign(NamedTuple):
    norm: Optional[str]  # The Norm of Perception (e.g., 'file_location')
    id: str              # Unique identifier
    signifier: str       # The content/name (e.g., the file path)

class PerceptionRouter:
    """
    Manages the Agent's faculties of perception.
    
    It defines how 'Signs' (formatted strings) are transmuted into 'Objects' (data)
    by applying a 'Norm' which selects the appropriate Faculty of the Body.
    """
    
    # Regex: %{Norm}ID(Signifier)
    # Matches:
    # 1. Optional Norm: {type_name} (Group 2 is inner name)
    # 2. ID: alphanumeric (Group 3)
    # 3. Signifier: content inside () (Group 4)
    _PATTERN = re.compile(r"^%(\{([a-zA-Z0-9_]+)\})?([a-zA-Z0-9]*)\((.*)\)$", re.DOTALL)

    # Specialized output markers produced by perception
    SPECIAL_KEYS = {
        "prompt_template": "{%{prompt_template}: ",
        "prompt_location": "{%{prompt_location}: ",
        "script_location": "{%{script_location}: ",
        "save_path": "{%{save_path}: ",
        "save_dir": "{%{save_dir}: ",
    }

    def encode_sign(self, content: Any, norm: str | None = None) -> str:
        """
        Creates a Perceptual Sign.
        Turns an object/name into a reference string that dictates how it should be perceived later.
        """
        unique_id = uuid.uuid4().hex[:3]
        str_content = str(content)
        
        if norm:
            return f"%{{{norm}}}{unique_id}({str_content})"
        else:
            return f"%{unique_id}({str_content})"

    def decode_sign(self, token: str) -> PerceptualSign | None:
        """Parses a string to see if it is a Perceptual Sign."""
        if not isinstance(token, str) or not token.startswith("%"):
            return None
            
        match = self._PATTERN.match(token)
        if not match:
            return None
        
        norm = match.group(2) # Inner group of {norm}
        unique_id = match.group(3)
        signifier = match.group(4)
        
        return PerceptualSign(norm=norm, id=unique_id, signifier=signifier)

    def strip_sign(self, token: Any) -> Any:
        """
        Decodes a sign and returns its raw signifier (payload).
        If the payload looks like a Python literal, it attempts to evaluate it.
        If the input is not a sign, returns the input as-is.
        """
        decoded = self.decode_sign(token)
        if decoded:
            # Try to literal eval if it looks like python structure
            import ast
            try:
                return ast.literal_eval(decoded.signifier)
            except (ValueError, SyntaxError):
                return decoded.signifier
        return token

    def transform(self, token: Any, config: Dict[str, Any], body: "Body") -> Any:
        """
        Applies a sequence of perception transformations based on a configuration:
        1. Stripping (optional): Removes existing wrappers.
        2. Branching (optional): Splits value into multiple perceived variants.
        3. Re-wrapping (optional): Wraps value in a new Norm.
        """
        strip_wrapper = config.get("strip_wrapper", False)
        new_wrapper = config.get("new_wrapper")
        branch = config.get("branch")

        current_val = token

        # 1. Pre-process: Strip if requested
        if strip_wrapper:
            current_val = self.strip_sign(current_val)

        # 2. Branching
        if branch and isinstance(branch, dict):
            branch_result = {}
            for branch_key, wrapper_name in branch.items():
                # Branching usually assumes working with the raw value
                raw_val = self.strip_sign(current_val)
                
                if wrapper_name == "NULL":
                    branch_result[branch_key] = raw_val
                else:
                    encoded = self.encode_sign(raw_val, wrapper_name)
                    branch_result[branch_key] = self.perceive(encoded, body)
            return branch_result

        # 3. Post-process: New Wrapper
        if new_wrapper and current_val is not None:
            # Re-wrapping implies wrapping the raw content
            raw_val = self.strip_sign(current_val)
            return self.encode_sign(raw_val, new_wrapper)
            
        return current_val

    def perceive(self, token: Any, body: "Body") -> Any:
        """
        The Act of Perception.
        
        1. Decodes the token into a Sign.
        2. Identifies the Norm.
        3. Uses the Norm to select a Faculty (Tool) from the Body.
        4. Transmutes the Signifier into the Object.
        """
        sign = self.decode_sign(token)
        if not sign:
            return token # Not a sign, return raw reality

        norm = sign.norm
        content = sign.signifier

        logger.debug(f"Perceiving: Norm='{norm}', Content='{content}'")

        # --- The Norms of Perception ---

        # Norm: File Location -> Faculty: FileSystem
        if norm == "file_location":
            logger.info(f"[PerceptionRouter] file_location norm: content='{content}'")
            logger.info(f"[PerceptionRouter] body.file_system = {body.file_system}")
            logger.info(f"[PerceptionRouter] file_system type = {type(body.file_system)}")
            
            if not hasattr(body, "file_system") or not body.file_system:
                logger.error(f"[PerceptionRouter] Body lacks file_system!")
                return f"ERROR: Body lacks faculty 'file_system' required for norm '{norm}'"
            try:
                logger.info(f"[PerceptionRouter] Calling body.file_system.read('{content}')")
                result = body.file_system.read(content)
                logger.info(f"[PerceptionRouter] read() returned: type={type(result)}, value={str(result)[:200]}")
                
                # Handle both dict and string return types
                if isinstance(result, dict):
                    if result.get("status") == "success":
                        content_preview = result.get("content", "")[:100] if result.get("content") else ""
                        logger.info(f"[PerceptionRouter] SUCCESS! Content preview: {content_preview}...")
                        return result.get("content", "")
                    else:
                        logger.warning(f"[PerceptionRouter] File read FAILED for '{content}': {result.get('message')}")
                        return result.get("message", f"ERROR: Failed to read {content}")
                elif isinstance(result, str):
                    logger.info(f"[PerceptionRouter] Got string result, length={len(result)}")
                    return result
                return str(result)
            except Exception as e:
                logger.error(f"[PerceptionRouter] Exception reading file '{content}': {e}", exc_info=True)
                return f"ERROR: Failed to read file {content}: {e}"

        # Norm: Prompt Location -> Faculty: PromptTool
        elif norm == "prompt_location":
            if not hasattr(body, "prompt_tool") or not body.prompt_tool:
                return f"ERROR: Body lacks faculty 'prompt_tool' required for norm '{norm}'"
            try:
                # We return a formatted instruction for the next step (templating)
                prompt_obj = body.prompt_tool.read(content)
                return f"{{%{{prompt_template}}: {prompt_obj.template}}}"
            except Exception as e:
                return f"ERROR: Failed to perceive prompt '{content}': {e}"

        # Norm: Prompt Template (Direct) -> Faculty: FileSystem (if content is path) or Direct
        elif norm == "prompt":
            # If content looks like a path, we might need FileSystem, otherwise it's raw text
            if hasattr(body, "file_system") and body.file_system:
                try:
                    file_exists = body.file_system.exists(content)
                    # Handle both bool and dict return types for compatibility
                    if isinstance(file_exists, dict):
                        file_exists = file_exists.get("exists", False)
                    if file_exists:
                        result = body.file_system.read(content)
                        if isinstance(result, dict):
                            content = result.get("content", content)
                        elif isinstance(result, str):
                            content = result
                except Exception as e:
                    logger.debug(f"Could not read prompt file '{content}': {e}")
            return f"{{%{{prompt_template}}: {content}}}"

        # Norm: Memorized Parameter -> Faculty: FileSystem (Memory Storage)
        elif norm == "memorized_parameter":
             if not hasattr(body, "file_system") or not body.file_system:
                return f"ERROR: Body lacks faculty 'file_system'"
             result = body.file_system.read_memorized_value(content)
             return result.get("content") if result.get("status") == "success" else result.get("message")

        # Norm: Deferred/Instructional Norms
        # These are not fully realized into objects yet, but reformatted for specific downstream consumers
        elif norm in ["script_location", "generated_script_path"]:
            return f"{{%{{script_location}}: {content}}}"
        elif norm == "save_path":
            return f"{{%{{save_path}}: {content}}}"
        elif norm == "save_dir":
            return f"{{%{{save_dir}}: {content}}}"

        # Fallback: Unknown Norm -> Return Signifier as is
        return content

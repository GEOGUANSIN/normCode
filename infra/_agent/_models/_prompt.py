from __future__ import annotations
import os
from typing import Dict, Optional, Any
from string import Template
from pathlib import Path

try:
	from infra._constants import CURRENT_DIR  # type: ignore
except Exception:
	import sys, pathlib
	here = pathlib.Path(__file__).parent
	parent = here.parent
	if str(parent) not in sys.path:
		sys.path.insert(0, str(parent))
	from _constants import CURRENT_DIR


class PromptTool:
	"""Prompt tool exposing affordances to read and render templates.

	Affordances (methods):
	- read(template_name: str) -> Template
	  Loads a template from the prompts directory and caches it by name.
	- substitute(template_name: str, variables: Dict[str, Any]) -> Template
	  Applies safe_substitute to the cached template content, creates a new Template
	  from the result, updates the cache, and returns the updated Template.
	- render(template_name: str, variables: Dict[str, Any]) -> str
	  Renders the current cached template with variables and returns a string without
	  mutating the cache.
	"""

	def __init__(self, base_dir: Optional[str] = None, encoding: str = "utf-8") -> None:
		self.base_dir = base_dir
		self.encoding = encoding
		self._cache: Dict[str, Template] = {}
		# Default inline templates as fallback when files are not present
		self._defaults: Dict[str, str] = {
			"translation": "Translate concept to natural name: ${output}",
			"instruction_with_buffer_record": "Use record '${record}' to act on imperative: ${impmerative}",
		}

	def _get_base_dir(self) -> Path:
		"""Determines the base directory for prompt operations."""
		if self.base_dir:
			return Path(self.base_dir)
		else:
			# Fallback to the 'prompts' directory relative to this file's parent
			this_dir = Path(__file__).parent
			return this_dir / "prompts"

	def read(self, template_name: str) -> Template:
		"""Load a template by name and cache it. Returns a string.Template."""
		base_path = self._get_base_dir()
		file_path = Path(template_name) if Path(template_name).is_absolute() else base_path / template_name

		if file_path.exists():
			with open(file_path, "r", encoding=self.encoding) as f:
				content = f.read()
			tmpl = Template(content)
			self._cache[template_name] = tmpl
			return tmpl
		
		# Fallback to default inline template if available
		default_content = self._defaults.get(template_name)
		if default_content is not None:
			tmpl = Template(default_content)
			self._cache[template_name] = tmpl
			return tmpl

		raise FileNotFoundError(
			f"Template file '{template_name}' not found at path: {file_path}"
		)

	def substitute(self, template_name: str, variables: Dict[str, Any]) -> Template:
		"""Apply variables and persist the updated Template back to cache.

		If not cached, loads the template first. Returns the updated Template.
		"""
		tmpl = self._cache.get(template_name)
		if tmpl is None:
			tmpl = self.read(template_name)
		rendered = tmpl.safe_substitute(variables)
		updated = Template(rendered)
		self._cache[template_name] = updated
		return updated

	# render returns a string, without mutating cache
	def render(self, template_name: str, variables: Dict[str, Any]) -> str:
		tmpl = self._cache.get(template_name)
		if tmpl is None:
			tmpl = self.read(template_name)
		return str(tmpl.safe_substitute(variables))

	# Optional: manage cache
	def clear_cache(self) -> None:
		self._cache.clear()

	def drop(self, template_name: str) -> None:
		self._cache.pop(template_name, None) 
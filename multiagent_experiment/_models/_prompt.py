from __future__ import annotations
import os
from typing import Dict, Optional, Any
from string import Template

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

	def __init__(self, prompts_dir: Optional[str] = None, encoding: str = "utf-8") -> None:
		this_dir = os.path.dirname(os.path.abspath(__file__))
		candidate_dirs = [
			os.path.join(this_dir, "prompts"),              # core/_new_infra/_syntax/prompts
			os.path.join(CURRENT_DIR, "prompts"),          # core/_new_infra/prompts
		]
		resolved_dir = prompts_dir
		if not resolved_dir:
			for d in candidate_dirs:
				if os.path.isdir(d):
					resolved_dir = d
					break
			if not resolved_dir:
				resolved_dir = candidate_dirs[0]

		self.prompts_dir = resolved_dir
		self.encoding = encoding
		self._cache: Dict[str, Template] = {}
		# Default inline templates as fallback when files are not present
		self._defaults: Dict[str, str] = {
			"translation": "Translate concept to natural name: ${output}",
			"instruction_with_buffer_record": "Use record '${record}' to act on imperative: ${impmerative}",
		}

	def _template_path(self, template_name: str) -> str:
		return os.path.join(self.prompts_dir, f"{template_name}.txt")

	def read(self, template_name: str) -> Template:
		"""Load a template by name and cache it. Returns a string.Template."""
		# Try primary directory
		path = self._template_path(template_name)
		if os.path.exists(path):
			with open(path, "r", encoding=self.encoding) as f:
				content = f.read()
			tmpl = Template(content)
			self._cache[template_name] = tmpl
			return tmpl
		# Try secondary directory if primary was the parent
		this_dir = os.path.dirname(os.path.abspath(__file__))
		alt_path = os.path.join(this_dir, "prompts", f"{template_name}.txt")
		if alt_path != path and os.path.exists(alt_path):
			with open(alt_path, "r", encoding=self.encoding) as f:
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
			f"Template file '{template_name}.txt' not found in prompts directory: {self.prompts_dir}"
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
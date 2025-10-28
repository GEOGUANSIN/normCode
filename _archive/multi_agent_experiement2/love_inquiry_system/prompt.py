
class Prompt:
    """A simple class to load and format a prompt template."""
    def __init__(self, template_path: str):
        with open(template_path, 'r', encoding='utf-8') as f:
            self.template = f.read()
        self.formatted_text = ""

    def format(self, **kwargs):
        """Formats the template with the given key-value pairs."""
        self.formatted_text = self.template.format(**kwargs)

    def __str__(self):
        return self.formatted_text

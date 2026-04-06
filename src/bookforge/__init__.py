"""BookForge - Pipeline CLI Markdown vers PDF/EPUB conforme KDP."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("bookforge")
except PackageNotFoundError:
    __version__ = "0.0.0"

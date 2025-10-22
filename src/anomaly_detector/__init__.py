"""Anomaly Detector core package."""

from importlib.metadata import version

__all__ = ["__version__"]


def __getattr__(name: str) -> str:
    if name == "__version__":
        try:
            return version("anomaly-detector")
        except Exception:  # fallback when package metadata not installed
            return "0.1.0"
    raise AttributeError(name)

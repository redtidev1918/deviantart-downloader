"""Compatibility shim for tools that still invoke ``setup.py`` directly.

All package metadata lives in ``pyproject.toml``.
"""

from setuptools import setup


setup()

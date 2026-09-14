"""Sphinx documentation configuration file for jedrezito."""

import os
import sys

# Path setup: add repository root to sys.path
sys.path.insert(0, os.path.abspath(".."))

# Project information
project = "jedrezito"
copyright = "2026, Ahmed-Amine HOMMAN"
author = "Ahmed-Amine HOMMAN"
release = "0.1.0"

# General configuration
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

templates_path = []
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

language = "fr"

# HTML output options
html_theme = "furo"
html_static_path = []

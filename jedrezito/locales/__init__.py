"""Localization utilities for Jedrezito.

This package manages translations and text dictionaries for the GUI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]


def load_locale(
    language: str = "fr",
) -> dict[str, Any]:
    """Load the translation dictionary for the specified language.

    Parameters
    ----------
    language : str, optional
        Two-letter ISO language code or locale identifier, by default "fr".

    Returns
    -------
    dict of str to Any
        Parsed dictionary containing localized UI strings.

    Raises
    ------
    FileNotFoundError
        If the translation file corresponding to the language is not found.
    """
    locales_dir: Path = Path(__file__).parent
    locale_file: Path = locales_dir / f"{language}.toml"

    if not locale_file.is_file():
        raise FileNotFoundError(
            f"Locale '{language}' is not supported. "
            f"File not found: {locale_file}"
        )

    with locale_file.open("rb") as f:
        return tomllib.load(f)

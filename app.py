"""Jedrezito main desktop GUI application entry point.

This module provides the command-line interface and bootstrap logic
for launching the PySide6 desktop GUI allowing players to play
Generalized Chess Games (JEG) with customizable variants and locales.
"""

from __future__ import annotations

import argparse
import sys
from typing import (
    Any,
)

from PySide6.QtCore import (
    QTimer,
)
from PySide6.QtWidgets import (
    QApplication,
)

from jedrezito.config import (
    load_variant_config,
)
from jedrezito.gui import (
    MainWindow,
)
from jedrezito.locales import (
    load_locale,
)
from jedrezito.models import (
    GameConfig,
)


def main(
) -> None:
    """Launch the Jedrezito PySide6 desktop GUI application."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Jedrezito - Generalized Chess Games (JEG) Desktop GUI",
    )
    parser.add_argument(
        "--game",
        type=str,
        default="chess",
        help="Name of the chess variant to load (default: chess)",
    )
    parser.add_argument(
        "--language",
        type=str,
        default="fr",
        help="Interface language code (default: fr)",
    )
    parser.add_argument(
        "--maximize",
        action="store_true",
        help="Launch the application in maximized window mode",
    )
    args: argparse.Namespace = parser.parse_args()

    config: GameConfig = load_variant_config(args.game)
    locale: dict[str, Any] = load_locale(args.language)

    app: QApplication = QApplication(sys.argv)
    window: MainWindow = MainWindow(
        config=config,
        locale=locale,
        initial_variant=args.game,
        start_maximized=args.maximize,
    )
    if args.maximize:
        window.showMaximized()
        QTimer.singleShot(50, window.showMaximized)
    else:
        window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

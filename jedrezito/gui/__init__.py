"""Jedrezito PySide6 Graphical User Interface package.

This package exposes GUI components, dialogs, widgets, and the main window
for playing generalized chess variants with human or AI participants.
"""

from __future__ import annotations

from jedrezito.gui.board import (
    ChessBoardWidget,
    ChessSquareButton,
    ResponsiveBoardContainer,
)
from jedrezito.gui.dialogs import (
    PIECE_SYMBOLS,
    GameSetupDialog,
    PlayerKind,
    PlayerSettings,
    PromotionDialog,
)
from jedrezito.gui.widgets import (
    GameSelectorWidget,
)
from jedrezito.gui.window import (
    MainWindow,
)

__all__: list[str] = [
    "ChessBoardWidget",
    "ChessSquareButton",
    "GameSelectorWidget",
    "GameSetupDialog",
    "MainWindow",
    "PIECE_SYMBOLS",
    "PlayerKind",
    "PlayerSettings",
    "PromotionDialog",
    "ResponsiveBoardContainer",
]

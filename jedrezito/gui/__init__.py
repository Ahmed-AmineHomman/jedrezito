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
    ArmyHistoryPlotWidget,
    CapturedPiecesWidget,
    PlayerCardWidget,
    TurnStatusWidget,
)
from jedrezito.gui.window import (
    MainWindow,
)

__all__: list[str] = [
    "ArmyHistoryPlotWidget",
    "CapturedPiecesWidget",
    "ChessBoardWidget",
    "ChessSquareButton",
    "GameSetupDialog",
    "MainWindow",
    "PIECE_SYMBOLS",
    "PlayerCardWidget",
    "PlayerKind",
    "PlayerSettings",
    "PromotionDialog",
    "ResponsiveBoardContainer",
    "TurnStatusWidget",
]

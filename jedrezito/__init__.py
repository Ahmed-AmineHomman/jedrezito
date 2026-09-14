"""Jedrezito: Generalized Chess Games (JEG) library and engine.

This package provides data structures, variant configuration parsers, and a
complete game engine to execute Generalized Chess Games.
"""

from __future__ import annotations

from jedrezito.config import (
    load_config,
    load_config_from_dict,
    load_default_chess_config,
    validate_config,
)
from jedrezito.engine import GameEngine
from jedrezito.models import (
    GameConfig,
    GameStatus,
    JumpMovement,
    Move,
    MovementRule,
    Piece,
    PieceCategory,
    PieceType,
    Player,
    RayFamily,
    RayMovement,
)

__all__ = [
    "GameConfig",
    "GameEngine",
    "GameStatus",
    "JumpMovement",
    "Move",
    "MovementRule",
    "Piece",
    "PieceCategory",
    "PieceType",
    "Player",
    "RayFamily",
    "RayMovement",
    "load_config",
    "load_config_from_dict",
    "load_default_chess_config",
    "validate_config",
]

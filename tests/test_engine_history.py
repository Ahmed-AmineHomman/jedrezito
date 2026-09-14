"""Unit tests for GameEngine army history and captured pieces tracking."""

from __future__ import annotations

import pytest

from jedrezito.config import (
    load_default_chess_config,
)
from jedrezito.engine import (
    GameEngine,
)
from jedrezito.models import (
    GameConfig,
    Move,
    Piece,
    Player,
)


@pytest.fixture
def standard_engine() -> GameEngine:
    """Create a standard chess GameEngine."""
    config: GameConfig = load_default_chess_config()
    return GameEngine(config)


def test_initial_army_history(standard_engine: GameEngine) -> None:
    """Validate initial army history contains exactly the initial state."""
    engine = standard_engine
    history = engine.get_army_history()
    assert len(history) == 1
    light_val = engine.get_army_value(Player.LIGHT)
    dark_val = engine.get_army_value(Player.DARK)
    assert history[0] == (light_val, dark_val)
    # Standard chess army without King: Queen(9) + 2*Rook(5) + 2*Bishop(3) + 2*Knight(3) + 8*Pawn(1) = 39
    assert light_val == 39
    assert dark_val == 39


def test_army_history_appends_on_move(standard_engine: GameEngine) -> None:
    """Validate each move appends a new state to army history."""
    engine = standard_engine
    # Light pawn moves 1 step forward in JEG (1, 4) -> (2, 4)
    move1 = Move(from_pos=(1, 4), to_pos=(2, 4))
    assert engine.make_move(move1) is True

    history = engine.get_army_history()
    assert len(history) == 2
    assert history[1] == (39, 39)

    # Dark pawn moves 1 step forward in JEG (6, 3) -> (5, 3)
    move2 = Move(from_pos=(6, 3), to_pos=(5, 3))
    assert engine.make_move(move2) is True

    history = engine.get_army_history()
    assert len(history) == 3
    assert history[2] == (39, 39)


def test_captured_pieces_and_history_decrease(standard_engine: GameEngine) -> None:
    """Validate captures update both captured_pieces and army_history."""
    engine = standard_engine
    # Setup custom scenario on empty board
    engine.board = [[None for _ in range(8)] for _ in range(8)]
    engine.board[0][0] = Piece("King", Player.LIGHT)
    engine.board[7][7] = Piece("King", Player.DARK)
    engine.board[3][3] = Piece("Queen", Player.LIGHT)
    engine.board[3][4] = Piece("Bishop", Player.DARK)  # value 3
    engine.board[6][6] = Piece("Rook", Player.DARK)    # value 5
    engine.army_history = [
        (engine.get_army_value(Player.LIGHT), engine.get_army_value(Player.DARK))
    ]

    assert engine.get_army_value(Player.LIGHT) == 9
    assert engine.get_army_value(Player.DARK) == 8
    assert engine.get_captured_pieces(Player.LIGHT) == []
    assert engine.get_captured_pieces(Player.DARK) == []

    # Light Queen captures Dark Bishop at (3, 4)
    cap_move = Move(from_pos=(3, 3), to_pos=(3, 4))
    assert engine.make_move(cap_move) is True

    # Check captures
    light_captures = engine.get_captured_pieces(Player.LIGHT)
    assert len(light_captures) == 1
    assert light_captures[0].piece_type == "Bishop"
    assert light_captures[0].player == Player.DARK
    assert engine.get_captured_pieces(Player.DARK) == []

    # Check army history
    history = engine.get_army_history()
    assert len(history) == 2
    assert history[1] == (9, 5)  # Dark lost 3 points


def test_undo_restores_army_history_and_captures(standard_engine: GameEngine) -> None:
    """Validate undoing a move restores army history and removes captured piece."""
    engine = standard_engine
    engine.board = [[None for _ in range(8)] for _ in range(8)]
    engine.board[0][0] = Piece("King", Player.LIGHT)
    engine.board[7][7] = Piece("King", Player.DARK)
    engine.board[3][3] = Piece("Queen", Player.LIGHT)
    engine.board[3][4] = Piece("Bishop", Player.DARK)
    engine.army_history = [
        (engine.get_army_value(Player.LIGHT), engine.get_army_value(Player.DARK))
    ]

    cap_move = Move(from_pos=(3, 3), to_pos=(3, 4))
    engine.make_move(cap_move)
    assert len(engine.get_captured_pieces(Player.LIGHT)) == 1
    assert len(engine.get_army_history()) == 2

    # Revert move
    assert engine.undo_move() is True
    assert len(engine.get_captured_pieces(Player.LIGHT)) == 0
    assert len(engine.get_army_history()) == 1
    assert engine.get_army_history()[0] == (9, 3)
    # Piece is back on board
    piece_at_target = engine.get_piece(3, 4)
    assert piece_at_target is not None
    assert piece_at_target.piece_type == "Bishop"


def test_reset_clears_history_and_captures(standard_engine: GameEngine) -> None:
    """Validate reset reinitializes army history and clears captures."""
    engine = standard_engine
    move1 = Move(from_pos=(1, 4), to_pos=(2, 4))
    assert engine.make_move(move1) is True
    assert len(engine.get_army_history()) == 2

    engine.reset()
    assert len(engine.get_army_history()) == 1
    assert engine.get_captured_pieces(Player.LIGHT) == []
    assert engine.get_captured_pieces(Player.DARK) == []

"""Unit tests for the Scaredycat AI agent."""

from __future__ import annotations

import pytest

from jedrezito.ai import (
    create_ai,
    list_available_ais,
)
from jedrezito.ai.scaredycat import (
    ScaredycatAI,
)
from jedrezito.config import (
    load_default_chess_config,
    load_variant_config,
)
from jedrezito.engine import (
    GameEngine,
)
from jedrezito.locales import (
    load_locale,
)
from jedrezito.models import (
    GameConfig,
    GameStatus,
    Move,
    Piece,
    Player,
)


@pytest.fixture
def empty_engine() -> GameEngine:
    """Create a GameEngine with an empty board for controlled scenario tests."""
    config: GameConfig = load_default_chess_config()
    engine: GameEngine = GameEngine(config)
    engine.board = [[None for _ in range(config.cols)] for _ in range(config.rows)]
    engine.current_player = Player.LIGHT
    engine.status = GameStatus.ONGOING
    return engine


def test_scaredycat_default_name() -> None:
    """Verify Scaredycat agent default identifier is 'scaredycat'."""
    assert ScaredycatAI().name == "scaredycat"


def test_scaredycat_custom_name() -> None:
    """Verify Scaredycat agent accepts a custom identifier."""
    assert ScaredycatAI(name="custom_scaredycat").name == "custom_scaredycat"


def test_scaredycat_in_available_ais() -> None:
    """Verify 'scaredycat' is in the registered AI list."""
    assert "scaredycat" in list_available_ais()


def test_create_ai_returns_scaredycat_instance() -> None:
    """Verify create_ai factory instantiates ScaredycatAI."""
    assert isinstance(create_ai("scaredycat"), ScaredycatAI)


def test_locale_includes_scaredycat() -> None:
    """Verify French locale includes scaredycat localization."""
    loc = load_locale("fr")
    assert "scaredycat" in loc.get("ais", {})


def test_scaredycat_returns_none_when_no_legal_moves(
    empty_engine: GameEngine,
) -> None:
    """Verify Scaredycat returns None when active player has no legal moves."""
    scaredycat = ScaredycatAI()
    assert scaredycat.select_move(empty_engine) is None


def test_scaredycat_deterministic_with_seed() -> None:
    """Verify identical random seeds yield identical move selection."""
    config = load_default_chess_config()
    engine = GameEngine(config)

    move_1 = ScaredycatAI(seed=42).select_move(engine)
    move_2 = ScaredycatAI(seed=42).select_move(engine)

    assert move_1 == move_2


def test_unprotected_heads_empty_when_all_protected(
    empty_engine: GameEngine,
) -> None:
    """Verify _get_unprotected_heads returns empty list when all heads are guarded."""
    engine = empty_engine
    engine.board[0][0] = Piece("King", Player.LIGHT)
    engine.board[1][1] = Piece("Knight", Player.LIGHT)

    ai = ScaredycatAI()
    assert ai._get_unprotected_heads(engine, Player.LIGHT) == []


def test_unprotected_heads_detects_unprotected_head(
    empty_engine: GameEngine,
) -> None:
    """Verify _get_unprotected_heads detects an isolated, unguarded head."""
    engine = empty_engine
    engine.board[0][0] = Piece("King", Player.LIGHT)
    engine.board[5][5] = Piece("Queen", Player.LIGHT)

    ai = ScaredycatAI()
    assert len(ai._get_unprotected_heads(engine, Player.LIGHT)) == 1


def test_unprotected_heads_ignores_pawns_and_king(
    empty_engine: GameEngine,
) -> None:
    """Verify _get_unprotected_heads ignores unguarded pawns and the King."""
    engine = empty_engine
    engine.board[0][0] = Piece("King", Player.LIGHT)
    engine.board[5][5] = Piece("Pawn", Player.LIGHT)

    ai = ScaredycatAI()
    assert ai._get_unprotected_heads(engine, Player.LIGHT) == []


def test_scaredycat_bully_capture_prioritized_when_protected(
    empty_engine: GameEngine,
) -> None:
    """Verify Scaredycat executes a Bully capture when full protection is preserved."""
    engine = empty_engine
    engine.board[0][0] = Piece("King", Player.LIGHT)
    engine.board[7][7] = Piece("King", Player.DARK)

    # Friendly Knight at (1, 1) protected by friendly King at (0, 0)
    engine.board[1][1] = Piece("Knight", Player.LIGHT)
    # Friendly Pawn at (2, 1) protects square (3, 2)
    engine.board[2][1] = Piece("Pawn", Player.LIGHT)
    # Dark Queen is at (3, 2)
    engine.board[3][2] = Piece("Queen", Player.DARK)

    ai = ScaredycatAI(seed=42)
    chosen_move = ai.select_move(engine)

    # Pawn (rank 1) captures Queen (rank 9) instead of Knight (rank 3) as per Bully logic
    assert chosen_move == Move(from_pos=(2, 1), to_pos=(3, 2))


def test_scaredycat_preserves_head_protection(
    empty_engine: GameEngine,
) -> None:
    """Verify Scaredycat avoids moves that break protection of its heads."""
    engine = empty_engine
    engine.board[0][0] = Piece("King", Player.LIGHT)
    engine.board[7][7] = Piece("King", Player.DARK)

    # Queen at (0, 7) protected along row 0 by Rook at (0, 3)
    engine.board[0][7] = Piece("Queen", Player.LIGHT)
    engine.board[0][3] = Piece("Rook", Player.LIGHT)

    ai = ScaredycatAI(seed=42)
    chosen_move = ai.select_move(engine)

    # Moving Rook off row 0 would break Queen protection; chosen move must keep Queen protected
    assert chosen_move is not None and chosen_move.to_pos[0] == 0


def test_scaredycat_minimax_sacrifices_least_valuable_head(
    empty_engine: GameEngine,
) -> None:
    """Verify Scaredycat prioritizes protecting higher-ranking heads when forced."""
    engine = empty_engine
    engine.board[7][7] = Piece("King", Player.DARK)
    engine.board[0][0] = Piece("King", Player.LIGHT)

    # Light Queen at (7, 0) has no legal moves
    engine.board[7][0] = Piece("Queen", Player.LIGHT)
    engine.board[6][0] = Piece("Pawn", Player.LIGHT)
    engine.board[7][1] = Piece("Pawn", Player.LIGHT)
    engine.board[6][1] = Piece("Pawn", Player.LIGHT)

    # Light Knight at (7, 2) has no legal moves
    engine.board[7][2] = Piece("Knight", Player.LIGHT)
    engine.board[5][1] = Piece("Pawn", Player.LIGHT)
    engine.board[5][3] = Piece("Pawn", Player.LIGHT)
    engine.board[6][4] = Piece("Pawn", Player.LIGHT)

    # Rook at (2, 0) protects Queen (7, 0) along col 0; moving to col 2 would protect Knight (7, 2)
    engine.board[2][0] = Piece("Rook", Player.LIGHT)

    ai = ScaredycatAI(seed=42)
    chosen_move = ai.select_move(engine)

    # Minimax must keep Queen (9) protected and leave Knight (3) unprotected
    assert chosen_move is not None and (
        chosen_move.from_pos == (2, 0) and chosen_move.to_pos[1] == 0
    )


def test_scaredycat_endgame_advances_pawn(
    empty_engine: GameEngine,
) -> None:
    """Verify Scaredycat advances a pawn when no friendly heads remain."""
    engine = empty_engine
    engine.board[0][0] = Piece("King", Player.LIGHT)
    engine.board[7][7] = Piece("King", Player.DARK)
    engine.board[1][3] = Piece("Pawn", Player.LIGHT)

    ai = ScaredycatAI(seed=42)
    chosen_move = ai.select_move(engine)

    assert chosen_move == Move(from_pos=(1, 3), to_pos=(2, 3))


def test_scaredycat_endgame_pawn_capture_preferred(
    empty_engine: GameEngine,
) -> None:
    """Verify Scaredycat prioritizes capturing pawn moves in the endgame."""
    engine = empty_engine
    engine.board[0][0] = Piece("King", Player.LIGHT)
    engine.board[7][7] = Piece("King", Player.DARK)
    engine.board[2][2] = Piece("Pawn", Player.LIGHT)
    engine.board[3][3] = Piece("Knight", Player.DARK)

    ai = ScaredycatAI(seed=42)
    chosen_move = ai.select_move(engine)

    assert chosen_move == Move(from_pos=(2, 2), to_pos=(3, 3))


def test_scaredycat_endgame_fallback_when_pawns_blocked(
    empty_engine: GameEngine,
) -> None:
    """Verify Scaredycat falls back to legal King move when pawns cannot advance."""
    engine = empty_engine
    engine.board[0][0] = Piece("King", Player.LIGHT)
    engine.board[7][7] = Piece("King", Player.DARK)
    # Pawn is completely blocked
    engine.board[1][0] = Piece("Pawn", Player.LIGHT)
    engine.board[2][0] = Piece("Pawn", Player.DARK)

    ai = ScaredycatAI(seed=42)
    chosen_move = ai.select_move(engine)

    assert chosen_move in engine.get_legal_moves(Player.LIGHT)


def test_scaredycat_mini_chess_variant_selects_legal_move() -> None:
    """Verify Scaredycat AI selects a legal move on mini-chess variant."""
    config = load_variant_config("mini_chess")
    engine = GameEngine(config)

    scaredycat = ScaredycatAI(seed=7)
    move = scaredycat.select_move(engine)

    assert move in engine.get_legal_moves(Player.LIGHT)

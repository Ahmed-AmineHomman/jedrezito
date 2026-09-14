"""Unit tests for the Bully AI agent."""

from __future__ import annotations

import pytest

from jedrezito.ai import (
    create_ai,
    list_available_ais,
)
from jedrezito.ai.bully import (
    BullyAI,
    get_piece_rank,
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


def test_piece_rank_king(empty_engine: GameEngine) -> None:
    """Validate King rank evaluates to infinity."""
    king = Piece("King", Player.LIGHT)
    assert get_piece_rank(king, empty_engine.config) == float("inf")


def test_piece_rank_queen(empty_engine: GameEngine) -> None:
    """Validate Queen rank evaluates to 9.0."""
    queen = Piece("Queen", Player.LIGHT)
    assert get_piece_rank(queen, empty_engine.config) == 9.0


def test_piece_rank_rook(empty_engine: GameEngine) -> None:
    """Validate Rook rank evaluates to 5.0."""
    rook = Piece("Rook", Player.LIGHT)
    assert get_piece_rank(rook, empty_engine.config) == 5.0


def test_piece_rank_bishop(empty_engine: GameEngine) -> None:
    """Validate Bishop rank evaluates to 3.0."""
    bishop = Piece("Bishop", Player.LIGHT)
    assert get_piece_rank(bishop, empty_engine.config) == 3.0


def test_piece_rank_knight(empty_engine: GameEngine) -> None:
    """Validate Knight rank evaluates to 3.0."""
    knight = Piece("Knight", Player.LIGHT)
    assert get_piece_rank(knight, empty_engine.config) == 3.0


def test_piece_rank_pawn(empty_engine: GameEngine) -> None:
    """Validate Pawn rank evaluates to 1.0."""
    pawn = Piece("Pawn", Player.LIGHT)
    assert get_piece_rank(pawn, empty_engine.config) == 1.0


def test_bully_targets_highest_ranking_opponent_piece(
    empty_engine: GameEngine,
) -> None:
    """Bully must prioritize capturing Queen (9) over Rook (5) or Pawn (1)."""
    engine = empty_engine
    engine.board[0][0] = Piece("King", Player.LIGHT)
    engine.board[5][7] = Piece("King", Player.DARK)

    # Light Queen at (3, 3) can capture Dark Queen (3, 7), Rook (3, 1), or Pawn (7, 3)
    engine.board[3][3] = Piece("Queen", Player.LIGHT)
    engine.board[3][7] = Piece("Queen", Player.DARK)
    engine.board[3][1] = Piece("Rook", Player.DARK)
    engine.board[7][3] = Piece("Pawn", Player.DARK)

    bully = BullyAI(seed=42)
    chosen_move = bully.select_move(engine)

    assert chosen_move == Move(from_pos=(3, 3), to_pos=(3, 7))


def test_bully_uses_lowest_ranking_piece_to_capture(
    empty_engine: GameEngine,
) -> None:
    """When multiple pieces can capture the target, Bully uses the lowest-ranking piece."""
    engine = empty_engine
    engine.board[0][0] = Piece("King", Player.LIGHT)
    engine.board[7][7] = Piece("King", Player.DARK)

    # Dark Queen is at (4, 4)
    engine.board[4][4] = Piece("Queen", Player.DARK)

    # Light has Rook at (4, 0) and Pawn at (3, 3) - both can capture at (4, 4)
    engine.board[4][0] = Piece("Rook", Player.LIGHT)
    engine.board[3][3] = Piece("Pawn", Player.LIGHT)

    bully = BullyAI(seed=42)
    chosen_move = bully.select_move(engine)

    # Pawn (rank 1) must be used instead of Rook (rank 5)
    assert chosen_move == Move(from_pos=(3, 3), to_pos=(4, 4))


def test_bully_prefers_regular_piece_over_king_attacker(
    empty_engine: GameEngine,
) -> None:
    """Bully prefers a regular piece (even Queen) over King when capturing."""
    engine = empty_engine
    engine.board[3][3] = Piece("King", Player.LIGHT)
    engine.board[3][5] = Piece("Queen", Player.LIGHT)
    engine.board[7][7] = Piece("King", Player.DARK)

    # Dark Bishop at (3, 4)
    engine.board[3][4] = Piece("Bishop", Player.DARK)

    bully = BullyAI(seed=42)
    chosen_move = bully.select_move(engine)

    # Queen (rank 9) must be preferred over King (rank inf)
    assert chosen_move == Move(from_pos=(3, 5), to_pos=(3, 4))


def test_bully_sacrifices_piece_regardless_of_danger(
    empty_engine: GameEngine,
) -> None:
    """Bully relentlessly captures highest ranking piece even if square is guarded."""
    engine = empty_engine
    engine.board[0][0] = Piece("King", Player.LIGHT)
    engine.board[7][7] = Piece("King", Player.DARK)

    # Dark Queen is at (4, 4), guarded by Dark Rook at (7, 4)
    engine.board[4][4] = Piece("Queen", Player.DARK)
    engine.board[7][4] = Piece("Rook", Player.DARK)

    # Light Queen at (4, 0) can take Dark Queen; Knight at (2, 2) can take Pawn at (3, 0)
    engine.board[4][0] = Piece("Queen", Player.LIGHT)
    engine.board[2][2] = Piece("Knight", Player.LIGHT)
    engine.board[3][0] = Piece("Pawn", Player.DARK)

    bully = BullyAI(seed=42)
    chosen = bully.select_move(engine)

    assert chosen == Move(from_pos=(4, 0), to_pos=(4, 4))


def test_bully_mini_chess_variant_selects_legal_move() -> None:
    """Verify Bully AI selects a legal move on mini-chess variant."""
    config = load_variant_config("mini_chess")
    engine = GameEngine(config)

    bully = BullyAI(seed=7)
    move = bully.select_move(engine)
    assert move in engine.get_legal_moves(Player.LIGHT)


def test_bully_falls_back_to_legal_move_when_no_captures() -> None:
    """In starting position where no captures exist, Bully selects a legal move."""
    config = load_default_chess_config()
    engine = GameEngine(config)

    bully = BullyAI(seed=123)
    move = bully.select_move(engine)

    assert move in engine.get_legal_moves(Player.LIGHT)


def test_bully_fallback_move_is_non_capturing_when_no_captures() -> None:
    """Fallback move in non-capture position lands on an empty square."""
    config = load_default_chess_config()
    engine = GameEngine(config)

    bully = BullyAI(seed=123)
    move = bully.select_move(engine)
    assert (
        move is not None
        and engine.get_piece(move.to_pos[0], move.to_pos[1]) is None
    )


def test_bully_returns_none_when_no_legal_moves(
    empty_engine: GameEngine,
) -> None:
    """Bully returns None when active player has no legal moves."""
    bully = BullyAI()
    assert bully.select_move(empty_engine) is None


def test_bully_deterministic_with_seed() -> None:
    """Verify identical random seeds yield identical move selection."""
    config = load_default_chess_config()
    engine = GameEngine(config)

    move_1 = BullyAI(seed=42).select_move(engine)
    move_2 = BullyAI(seed=42).select_move(engine)

    assert move_1 == move_2


def test_bully_default_name() -> None:
    """Verify Bully agent identifier is 'bully'."""
    assert BullyAI().name == "bully"


def test_bully_in_available_ais() -> None:
    """Verify 'bully' is in the registered AI list."""
    assert "bully" in list_available_ais()


def test_create_ai_returns_bully_instance() -> None:
    """Verify create_ai factory instantiates BullyAI."""
    assert isinstance(create_ai("bully"), BullyAI)


def test_locale_includes_bully() -> None:
    """Verify French locale includes bully localization."""
    loc = load_locale("fr")
    assert "bully" in loc.get("ais", {})

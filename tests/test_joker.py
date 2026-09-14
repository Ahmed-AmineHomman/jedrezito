"""Unit tests for the Joker AI agent."""

from __future__ import annotations

from unittest.mock import (
    MagicMock,
)

import pytest

from jedrezito.ai import (
    create_ai,
    list_available_ais,
)
from jedrezito.ai.joker import (
    JokerAI,
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


@pytest.fixture
def mock_engine() -> MagicMock:
    """Create a mock GameEngine for isolated Joker AI unit tests."""
    engine = MagicMock(spec=GameEngine)
    engine.current_player = Player.LIGHT
    engine.get_legal_moves.return_value = []
    return engine


def test_joker_default_name() -> None:
    """Verify Joker agent default identifier is 'joker'."""
    assert JokerAI().name == "joker"


def test_joker_custom_name() -> None:
    """Verify Joker agent accepts a custom identifier."""
    assert JokerAI(name="custom_joker").name == "custom_joker"


def test_joker_in_available_ais() -> None:
    """Verify 'joker' is in the registered AI list."""
    assert "joker" in list_available_ais()


def test_create_ai_returns_joker_instance() -> None:
    """Verify create_ai factory instantiates JokerAI."""
    assert isinstance(create_ai("joker"), JokerAI)


def test_locale_includes_joker() -> None:
    """Verify French locale includes joker localization."""
    loc = load_locale("fr")
    assert "joker" in loc.get("ais", {})


def test_joker_returns_none_when_no_legal_moves(
    empty_engine: GameEngine,
) -> None:
    """Verify Joker returns None when active player has no legal moves."""
    joker = JokerAI()
    assert joker.select_move(empty_engine) is None


def test_joker_returns_none_when_legal_moves_is_empty(
    mock_engine: MagicMock,
) -> None:
    """Verify Joker returns None when engine returns an empty legal moves list."""
    mock_engine.get_legal_moves.return_value = []
    joker = JokerAI()
    assert joker.select_move(mock_engine) is None


def test_joker_queries_current_player_legal_moves(
    mock_engine: MagicMock,
) -> None:
    """Verify Joker requests legal moves for the engine's active player."""
    mock_engine.current_player = Player.DARK
    mock_engine.get_legal_moves.return_value = []

    JokerAI().select_move(mock_engine)

    mock_engine.get_legal_moves.assert_called_once_with(Player.DARK)


def test_joker_selects_sole_available_move(
    mock_engine: MagicMock,
) -> None:
    """Verify Joker deterministically returns the only legal move provided."""
    sole_move = Move(from_pos=(1, 2), to_pos=(3, 4))
    mock_engine.get_legal_moves.return_value = [sole_move]

    joker = JokerAI()
    chosen_move = joker.select_move(mock_engine)

    assert chosen_move == sole_move


def test_joker_selects_move_from_available_moves(
    mock_engine: MagicMock,
) -> None:
    """Verify Joker selects a move belonging to the supplied candidate moves."""
    candidate_moves = [
        Move(from_pos=(0, 0), to_pos=(1, 0)),
        Move(from_pos=(0, 1), to_pos=(2, 1)),
        Move(from_pos=(0, 2), to_pos=(3, 2)),
    ]
    mock_engine.get_legal_moves.return_value = candidate_moves

    joker = JokerAI(seed=42)
    chosen_move = joker.select_move(mock_engine)

    assert chosen_move in candidate_moves


def test_joker_deterministic_selection_with_seed(
    mock_engine: MagicMock,
) -> None:
    """Verify identical random seeds yield identical move selection from candidates."""
    candidate_moves = [
        Move(from_pos=(0, 0), to_pos=(1, 0)),
        Move(from_pos=(0, 1), to_pos=(2, 1)),
        Move(from_pos=(0, 2), to_pos=(3, 2)),
    ]
    mock_engine.get_legal_moves.return_value = candidate_moves

    move_1 = JokerAI(seed=42).select_move(mock_engine)
    move_2 = JokerAI(seed=42).select_move(mock_engine)

    assert move_1 == move_2


def test_joker_consecutive_selections_reproducible_with_seed(
    mock_engine: MagicMock,
) -> None:
    """Verify seeded Joker AI produces reproducible consecutive move choices."""
    candidate_moves = [
        Move(from_pos=(0, 0), to_pos=(1, 0)),
        Move(from_pos=(0, 1), to_pos=(2, 1)),
        Move(from_pos=(0, 2), to_pos=(3, 2)),
    ]
    mock_engine.get_legal_moves.return_value = candidate_moves

    joker_1 = JokerAI(seed=99)
    joker_2 = JokerAI(seed=99)
    joker_1.select_move(mock_engine)
    joker_2.select_move(mock_engine)

    assert joker_1.select_move(mock_engine) == joker_2.select_move(mock_engine)


def test_create_ai_deterministic_with_seed(
    mock_engine: MagicMock,
) -> None:
    """Verify create_ai factory instantiates reproducible JokerAI with seed."""
    candidate_moves = [
        Move(from_pos=(0, 0), to_pos=(1, 0)),
        Move(from_pos=(0, 1), to_pos=(2, 1)),
    ]
    mock_engine.get_legal_moves.return_value = candidate_moves

    move_1 = create_ai("joker", seed=42).select_move(mock_engine)
    move_2 = create_ai("joker", seed=42).select_move(mock_engine)

    assert move_1 == move_2


def test_joker_deterministic_with_seed_on_real_engine() -> None:
    """Verify identical random seeds yield identical move selection on GameEngine."""
    config = load_default_chess_config()
    engine = GameEngine(config)

    move_1 = JokerAI(seed=42).select_move(engine)
    move_2 = JokerAI(seed=42).select_move(engine)

    assert move_1 == move_2


def test_joker_selects_legal_move_on_default_board() -> None:
    """Verify Joker AI selects a legal move in initial chess position."""
    config = load_default_chess_config()
    engine = GameEngine(config)

    joker = JokerAI(seed=123)
    move = joker.select_move(engine)

    assert move in engine.get_legal_moves(Player.LIGHT)


def test_joker_mini_chess_variant_selects_legal_move() -> None:
    """Verify Joker AI selects a legal move on mini-chess variant."""
    config = load_variant_config("mini_chess")
    engine = GameEngine(config)

    joker = JokerAI(seed=7)
    move = joker.select_move(engine)

    assert move in engine.get_legal_moves(Player.LIGHT)

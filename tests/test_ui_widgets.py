"""Unit tests for Jedrezito GUI widgets, player cards, plots, and layout."""

from __future__ import annotations

import os
import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtCore import (
    QPointF,
    Qt,
)
from PySide6.QtGui import (
    QMouseEvent,
)
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
)

from jedrezito.config import (
    load_default_chess_config,
)
from jedrezito.gui.dialogs import (
    GameSetupDialog,
    PlayerKind,
    PlayerSettings,
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


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    """Ensure a singleton QApplication exists for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def locale() -> dict:
    """Load French localization dictionary."""
    return load_locale("fr")


@pytest.fixture
def config() -> GameConfig:
    """Load default chess configuration."""
    return load_default_chess_config()


def test_captured_pieces_widget_empty(qapp: QApplication, locale: dict) -> None:
    """Test CapturedPiecesWidget in initial empty state."""
    widget = CapturedPiecesWidget(locale)
    assert widget.empty_label.text() == "Aucune capture"


def test_captured_pieces_widget_with_pieces(
    qapp: QApplication,
    locale: dict,
    config: GameConfig,
) -> None:
    """Test CapturedPiecesWidget displaying captured pieces."""
    widget = CapturedPiecesWidget(locale)
    captured = [
        Piece("Pawn", Player.DARK),
        Piece("Pawn", Player.DARK),
        Piece("Knight", Player.DARK),
    ]
    widget.update_pieces(captured, config.piece_types)
    # The empty label should have been removed and badges created
    assert widget.main_layout.count() > 1


def test_player_card_widget_human(qapp: QApplication, locale: dict, config: GameConfig) -> None:
    """Test PlayerCardWidget configured for a human player."""
    card = PlayerCardWidget(Player.LIGHT, locale)
    settings = PlayerSettings(kind=PlayerKind.HUMAN)

    card.update_card(
        settings=settings,
        is_current_turn=True,
        is_in_check=False,
        army_value=39,
        opponent_army_value=36,
        captured_pieces=[Piece("Bishop", Player.DARK)],
        piece_types=config.piece_types,
    )

    assert "Humain" in card.lbl_controller.text()
    assert "AU TRAIT" in card.lbl_turn_badge.text()
    assert card.lbl_score.text() == "39 pts"
    assert card.lbl_diff.text() == "+3"
    assert not card.lbl_diff.isHidden()


def test_player_card_widget_ai_bully(qapp: QApplication, locale: dict, config: GameConfig) -> None:
    """Test PlayerCardWidget configured for Bully AI."""
    card = PlayerCardWidget(Player.DARK, locale)
    settings = PlayerSettings(kind=PlayerKind.AI, ai_name="bully")

    card.update_card(
        settings=settings,
        is_current_turn=False,
        is_in_check=False,
        army_value=30,
        opponent_army_value=35,
        captured_pieces=[],
        piece_types=config.piece_types,
    )

    assert "Bully" in card.lbl_controller.text()
    assert "En attente" in card.lbl_turn_badge.text()
    assert card.lbl_score.text() == "30 pts"
    assert card.lbl_diff.text() == "-5"


def test_player_card_widget_in_check(qapp: QApplication, locale: dict, config: GameConfig) -> None:
    """Test PlayerCardWidget displaying King in check alert."""
    card = PlayerCardWidget(Player.LIGHT, locale)
    settings = PlayerSettings(kind=PlayerKind.HUMAN)

    card.update_card(
        settings=settings,
        is_current_turn=True,
        is_in_check=True,
        army_value=39,
        opponent_army_value=39,
        captured_pieces=[],
        piece_types=config.piece_types,
    )

    assert "ÉCHEC" in card.lbl_turn_badge.text()


def test_army_history_plot_widget(qapp: QApplication, locale: dict) -> None:
    """Test ArmyHistoryPlotWidget data update and rendering."""
    plot = ArmyHistoryPlotWidget(locale)
    plot.resize(350, 180)

    # Empty history
    plot.set_history([])
    plot.repaint()

    # Populated history
    history = [(39, 39), (39, 39), (39, 36), (36, 36), (36, 27)]
    plot.set_history(history)
    plot.repaint()
    assert len(plot._history) == 5

    # Mouse hover interaction
    pos = QPointF(100.0, 50.0)
    event = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        pos,
        pos,
        Qt.MouseButton.NoButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    plot.mouseMoveEvent(event)
    assert plot._hover_idx is not None

    plot.leaveEvent(None)
    assert plot._hover_idx is None


def test_turn_status_widget(qapp: QApplication, locale: dict) -> None:
    """Test TurnStatusWidget updates for ongoing, check, and game over states."""
    widget = TurnStatusWidget(locale)

    # Ongoing turn - focused on match status without redundant player details
    widget.update_status(
        current_player=Player.LIGHT,
        player_settings=PlayerSettings(PlayerKind.HUMAN),
        is_check=False,
        status=GameStatus.ONGOING,
        winner=None,
        turns_played={Player.LIGHT: 0, Player.DARK: 0},
        turn_limit=None,
    )
    assert "Partie en cours" in widget.lbl_main_status.text()
    assert "Coup 1" in widget.lbl_move_counter.text()

    # In check
    widget.update_status(
        current_player=Player.LIGHT,
        player_settings=PlayerSettings(PlayerKind.HUMAN),
        is_check=True,
        status=GameStatus.ONGOING,
        winner=None,
        turns_played={Player.LIGHT: 2, Player.DARK: 2},
        turn_limit=None,
    )
    assert "Échec au Roi" in widget.lbl_main_status.text() or "ÉCHEC" in widget.lbl_main_status.text()

    # Checkmate
    widget.update_status(
        current_player=Player.DARK,
        player_settings=PlayerSettings(PlayerKind.HUMAN),
        is_check=True,
        status=GameStatus.CHECKMATE,
        winner=Player.LIGHT,
        turns_played={Player.LIGHT: 10, Player.DARK: 9},
        turn_limit=None,
    )
    assert "Échec et mat" in widget.lbl_main_status.text()
    assert "Blancs" in widget.lbl_main_status.text()
    assert "Terminée" in widget.lbl_move_counter.text()


def test_main_window_setup_and_panels(qapp: QApplication, config: GameConfig, locale: dict) -> None:
    """Test MainWindow initialization with 16:9 desktop dimensions and widgets."""
    window = MainWindow(config=config, locale=locale)

    # 16:9 desktop dimensions
    assert window.minimumWidth() == 960
    assert window.minimumHeight() == 540
    assert window.width() == 1280
    assert window.height() == 720

    # Ensure required panels exist and old selector panel is removed
    assert window.turn_status_widget is not None
    assert window.dark_player_card is not None
    assert window.light_player_card is not None
    assert window.army_plot_widget is not None
    assert window.board_widget is not None
    assert not hasattr(window, "selector_widget")

    # Initial turn indications:
    # Light has active turn in player card; status widget shows match progression
    assert "AU TRAIT" in window.light_player_card.lbl_turn_badge.text()
    assert "En attente" in window.dark_player_card.lbl_turn_badge.text()
    assert "Partie en cours" in window.turn_status_widget.lbl_main_status.text()

    # Verify initial army history in plot
    assert len(window.army_plot_widget._history) == 1
    assert window.army_plot_widget._history[0] == (39, 39)

    # Execute a move via engine and update (1 step forward for JEG pawn: (1, 4) -> (2, 4))
    move = Move(from_pos=(1, 4), to_pos=(2, 4))
    assert window.engine.make_move(move) is True
    window._update_all()

    # Verify plot updated
    assert len(window.army_plot_widget._history) == 2
    # Turn now belongs to Dark in the dark player card
    assert window.engine.current_player == Player.DARK
    assert "AU TRAIT" in window.dark_player_card.lbl_turn_badge.text()
    assert "En attente" in window.light_player_card.lbl_turn_badge.text()
    assert "Partie en cours" in window.turn_status_widget.lbl_main_status.text()
    assert "Coup 2" in window.turn_status_widget.lbl_move_counter.text()


def test_left_panel_no_cropping(qapp: QApplication, config: GameConfig, locale: dict) -> None:
    """Verify that left panel contents fit completely within the scroll area width."""
    window = MainWindow(config=config, locale=locale)
    window.show()
    qapp.processEvents()

    left_scroll = window.centralWidget().layout().itemAt(0).widget()
    left_panel = left_scroll.widget()
    scroll_w = left_scroll.width()
    panel_w = left_panel.width()
    assert panel_w <= scroll_w

    # Check that all visible widgets inside left_panel fit inside the scroll width
    for child in left_panel.findChildren(QWidget):
        if child.isVisible() and child is not left_panel:
            assert child.geometry().right() <= scroll_w


def test_game_setup_dialog_and_start(qapp: QApplication, config: GameConfig, locale: dict) -> None:
    """Test GameSetupDialog preview and starting a configured game in MainWindow."""
    window = MainWindow(config=config, locale=locale)

    dialog = GameSetupDialog(
        current_variant="chess",
        light_settings=PlayerSettings(PlayerKind.HUMAN),
        dark_settings=PlayerSettings(PlayerKind.AI, ai_name="joker"),
        locale=locale,
    )
    assert dialog.combo_variant.count() >= 2
    assert "8 × 8" in dialog.lbl_variant_info.text()

    # Change to mini_chess
    for i in range(dialog.combo_variant.count()):
        if dialog.combo_variant.itemData(i) == "mini_chess":
            dialog.combo_variant.setCurrentIndex(i)
            break
    assert "6 × 6" in dialog.lbl_variant_info.text()
    assert "40" in dialog.lbl_variant_info.text()

    dialog._on_start_clicked()
    assert dialog.selected_variant == "mini_chess"

    window._start_configured_game(
        variant_name=dialog.selected_variant,
        light_settings=dialog.selected_light_settings,
        dark_settings=dialog.selected_dark_settings,
    )
    assert window.current_variant == "mini_chess"
    assert window.config.rows == 6
    assert window.config.cols == 6
    assert window.player_configs[Player.DARK].kind == PlayerKind.AI
    assert window.player_configs[Player.DARK].ai_name == "joker"
    assert window.ai_agents[Player.DARK] is not None

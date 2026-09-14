"""Main desktop application window for the Jedrezito GUI.

This module provides the central 16:9 desktop application window connecting:
- Left sidebar: game configuration and match controls
- Center viewport: responsive, auto-scaling chessboard grid
- Right dashboard: active turn banner, player cards (Human/AI details),
  captured pieces trays, and real-time army points history line plot.
"""

from __future__ import annotations

from typing import (
    Any,
    Optional,
)

from PySide6.QtCore import (
    Qt,
    QTimer,
)
from PySide6.QtGui import (
    QShowEvent,
)
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from jedrezito.ai import (
    BaseAI,
    create_ai,
)
from jedrezito.config import (
    load_variant_config,
)
from jedrezito.engine import (
    GameEngine,
)
from jedrezito.gui.board import (
    ChessBoardWidget,
    ResponsiveBoardContainer,
)
from jedrezito.gui.dialogs import (
    GameSetupDialog,
    PlayerKind,
    PlayerSettings,
    PromotionDialog,
)
from jedrezito.gui.widgets import (
    ArmyHistoryPlotWidget,
    PlayerCardWidget,
    TurnStatusWidget,
)
from jedrezito.models import (
    GameConfig,
    GameStatus,
    Move,
    Piece,
    Player,
)


class MainWindow(QMainWindow):
    """Main desktop application window for Jedrezito chess games.

    Parameters
    ----------
    config : GameConfig
        Active JEG game configuration.
    locale : dict of str to Any
        Localization dictionary containing UI strings.
    initial_variant : str, optional
        Identifier of the initially loaded variant, by default "chess".
    start_maximized : bool, optional
        Whether to launch the window maximized, by default False.
    parent : QWidget or None, optional
        Parent widget, by default None.

    Attributes
    ----------
    config : GameConfig
        Active variant configuration.
    locale : dict of str to Any
        Active localized UI strings.
    current_variant : str
        Currently active chess variant identifier.
    start_maximized : bool
        Whether the window was started in maximized mode.
    player_configs : dict of Player to PlayerSettings
        Controller settings for Light and Dark players.
    ai_agents : dict of Player to BaseAI or None
        Active AI agent instances for each player camp.
    engine : GameEngine
        Active JEG game engine instance.
    selected_square : tuple of int or None
        Coordinates (row, col) of currently selected square.
    board_container : ResponsiveBoardContainer
        Container holding the chessboard grid.
    board_container_layout : QVBoxLayout
        Layout managing dynamic board widget replacement.
    board_widget : ChessBoardWidget
        Active chessboard grid widget.
    turn_status_widget : TurnStatusWidget
        Prominent active turn banner and check alert widget.
    dark_player_card : PlayerCardWidget
        Dark player information card.
    light_player_card : PlayerCardWidget
        Light player information card.
    army_plot_widget : ArmyHistoryPlotWidget
        Interactive line plot showing army points history.
    btn_next_move : QPushButton
        Button triggering next AI action in AI-vs-AI matches.
    btn_revert_move : QPushButton
        Button reverting the most recently executed move.
    btn_new_game : QPushButton
        Reset button to start a fresh match with active variant.
    """

    def __init__(
        self,
        config: GameConfig,
        locale: dict[str, Any],
        initial_variant: str = "chess",
        start_maximized: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.config: GameConfig = config
        self.locale: dict[str, Any] = locale
        self.current_variant: str = initial_variant
        self.start_maximized: bool = start_maximized

        self.player_configs: dict[Player, PlayerSettings] = {
            Player.LIGHT: PlayerSettings(PlayerKind.HUMAN),
            Player.DARK: PlayerSettings(PlayerKind.HUMAN),
        }
        self.ai_agents: dict[Player, Optional[BaseAI]] = {
            Player.LIGHT: None,
            Player.DARK: None,
        }
        self._ai_timer: QTimer = QTimer(self)
        self._ai_timer.setSingleShot(True)
        self._ai_timer.timeout.connect(self._perform_ai_move)

        app_locale: dict[str, Any] = self.locale.get("app", {})
        self.setWindowTitle(
            app_locale.get(
                "window_title",
                "Jedrezito — Jeux d'Échecs Généralisés",
            )
        )

        # 16:9 desktop window dimensions (1280x720 default, 960x540 min)
        self.setMinimumSize(960, 540)
        if self.start_maximized:
            self.setWindowState(Qt.WindowState.WindowMaximized)
        else:
            self.resize(1280, 720)

        self.engine: GameEngine = GameEngine(self.config)
        self.selected_square: Optional[tuple[int, int]] = None

        self._setup_ui()
        self._update_all()

    def showEvent(
        self,
        event: QShowEvent,
    ) -> None:
        """Ensure maximized window state is enforced when the window is shown.

        Parameters
        ----------
        event : QShowEvent
            Window show event.
        """
        super().showEvent(event)
        if self.start_maximized:
            self.showMaximized()

    def _setup_ui(
        self,
    ) -> None:
        """Initialize central 3-column layout optimized for 16:9 desktop displays."""
        central_widget: QWidget = QWidget(self)
        central_widget.setStyleSheet("background-color: #1a1816;")
        self.setCentralWidget(central_widget)

        main_layout: QHBoxLayout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(14)

        app_locale: dict[str, Any] = self.locale.get("app", {})
        controls_locale: dict[str, Any] = self.locale.get("controls", {})

        # =========================================================================
        # LEFT COLUMN: Match controls & actions (Width ~280px)
        # =========================================================================
        left_panel: QFrame = QFrame(self)
        left_panel.setStyleSheet(
            "QFrame {"
            "  background-color: #242220;"
            "  border-radius: 8px;"
            "}"
        )
        left_layout: QVBoxLayout = QVBoxLayout(left_panel)
        left_layout.setSpacing(12)
        left_layout.setContentsMargins(10, 10, 10, 10)

        # App title and subtitle
        lbl_app_title: QLabel = QLabel(
            app_locale.get("sidebar_title", "Jeux d'Échecs Généralisés"),
            self,
        )
        lbl_app_title.setStyleSheet(
            "color: #f5f5f5; font-size: 16px; font-weight: bold; background: transparent;"
        )
        left_layout.addWidget(lbl_app_title)

        lbl_app_sub: QLabel = QLabel(
            app_locale.get(
                "sidebar_description",
                "Affrontement local au tour par tour (mode hotseat)",
            ),
            self,
        )
        lbl_app_sub.setWordWrap(True)
        lbl_app_sub.setStyleSheet(
            "color: #a8a096; font-size: 12px; background: transparent;"
        )
        left_layout.addWidget(lbl_app_sub)

        # Spacer to push action controls down
        left_layout.addSpacerItem(
            QSpacerItem(
                20,
                20,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            )
        )

        # Action Buttons Group
        actions_group: QFrame = QFrame(self)
        actions_group.setStyleSheet("background: transparent; border: none;")
        actions_layout: QVBoxLayout = QVBoxLayout(actions_group)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        # Reset / Configure New Game Button
        self.btn_new_game: QPushButton = QPushButton(
            app_locale.get("btn_new_game", "Nouvelle partie"),
            self,
        )
        self.btn_new_game.setStyleSheet(
            "QPushButton {"
            "  background-color: #4a752c;"
            "  color: #ffffff;"
            "  font-size: 14px;"
            "  font-weight: bold;"
            "  padding: 10px;"
            "  border: none;"
            "  border-radius: 6px;"
            "}"
            "QPushButton:hover {"
            "  background-color: #5d9337;"
            "}"
            "QPushButton:pressed {"
            "  background-color: #3b5e23;"
            "}"
        )
        self.btn_new_game.clicked.connect(self._handle_new_game)
        actions_layout.addWidget(self.btn_new_game)

        # Next move (AI pacing) button
        self.btn_next_move: QPushButton = QPushButton(
            controls_locale.get("btn_next_move", "Coup suivant"),
            self,
        )
        self.btn_next_move.setStyleSheet(
            "QPushButton {"
            "  background-color: #385e26;"
            "  color: #ffffff;"
            "  font-size: 13px;"
            "  font-weight: bold;"
            "  padding: 9px;"
            "  border: none;"
            "  border-radius: 6px;"
            "}"
            "QPushButton:hover {"
            "  background-color: #4a752c;"
            "}"
            "QPushButton:pressed {"
            "  background-color: #2b451c;"
            "}"
            "QPushButton:disabled {"
            "  background-color: #262422;"
            "  color: #59534c;"
            "}"
        )
        self.btn_next_move.clicked.connect(self._handle_next_move)
        actions_layout.addWidget(self.btn_next_move)

        # Revert move button
        self.btn_revert_move: QPushButton = QPushButton(
            controls_locale.get("btn_revert_move", "Annuler le coup"),
            self,
        )
        self.btn_revert_move.setStyleSheet(
            "QPushButton {"
            "  background-color: #332f2b;"
            "  color: #f0eae1;"
            "  font-size: 13px;"
            "  font-weight: bold;"
            "  padding: 9px;"
            "  border: 1px solid #4a443e;"
            "  border-radius: 6px;"
            "}"
            "QPushButton:hover {"
            "  background-color: #4a443e;"
            "  border-color: #5d564f;"
            "}"
            "QPushButton:pressed {"
            "  background-color: #242220;"
            "}"
            "QPushButton:disabled {"
            "  background-color: #201e1d;"
            "  color: #55504a;"
            "  border-color: #2b2724;"
            "}"
        )
        self.btn_revert_move.clicked.connect(self._handle_revert_move)
        actions_layout.addWidget(self.btn_revert_move)

        left_layout.addWidget(actions_group)

        # Wrap left panel in scroll area for safety on small displays
        left_scroll: QScrollArea = QScrollArea(self)
        left_scroll.setFixedWidth(280)
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        left_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        left_scroll.setWidget(left_panel)
        main_layout.addWidget(left_scroll, stretch=0)

        # =========================================================================
        # CENTER COLUMN: Responsive Chessboard Container (Stretch = 1)
        # =========================================================================
        self.board_container: ResponsiveBoardContainer = (
            ResponsiveBoardContainer(self)
        )
        self.board_container.resized.connect(self._on_board_container_resized)
        self.board_container_layout: QVBoxLayout = QVBoxLayout(
            self.board_container
        )
        self.board_container_layout.setContentsMargins(0, 0, 0, 0)

        self.board_widget: ChessBoardWidget = ChessBoardWidget(
            self.engine.config,
            self,
        )
        self.board_widget.square_clicked.connect(self._handle_square_click)
        self.board_container_layout.addWidget(
            self.board_widget,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )
        main_layout.addWidget(
            self.board_container,
            stretch=1,
        )

        # =========================================================================
        # RIGHT COLUMN: Dashboard & Information Panels (Width ~330px)
        # =========================================================================
        right_panel: QFrame = QFrame(self)
        right_panel.setStyleSheet(
            "QFrame {"
            "  background-color: #242220;"
            "  border-radius: 8px;"
            "}"
        )
        right_layout: QVBoxLayout = QVBoxLayout(right_panel)
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(10, 10, 10, 10)

        # 1. Turn / Match Status Banner (no player identity repetition)
        self.turn_status_widget: TurnStatusWidget = TurnStatusWidget(
            self.locale,
            self,
        )
        right_layout.addWidget(self.turn_status_widget)

        # 2. Dark Player Card (Top participant)
        self.dark_player_card: PlayerCardWidget = PlayerCardWidget(
            Player.DARK,
            self.locale,
            self,
        )
        right_layout.addWidget(self.dark_player_card)

        # 3. Light Player Card (Bottom participant)
        self.light_player_card: PlayerCardWidget = PlayerCardWidget(
            Player.LIGHT,
            self.locale,
            self,
        )
        right_layout.addWidget(self.light_player_card)

        # 4. Army Material Points History Line Plot
        self.army_plot_widget: ArmyHistoryPlotWidget = ArmyHistoryPlotWidget(
            self.locale,
            self,
        )
        right_layout.addWidget(self.army_plot_widget)

        # Wrap right panel in scroll area
        right_scroll: QScrollArea = QScrollArea(self)
        right_scroll.setFixedWidth(330)
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QFrame.Shape.NoFrame)
        right_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        right_scroll.setWidget(right_panel)
        main_layout.addWidget(right_scroll, stretch=0)

    def _on_board_container_resized(
        self,
        width: int,
        height: int,
    ) -> None:
        """Handle container resize by updating board tile sizes.

        Parameters
        ----------
        width : int
            New container width in pixels.
        height : int
            New container height in pixels.
        """
        if self.board_widget is not None:
            self.board_widget.resize_to_fit(width, height)

    @property
    def is_ai_vs_ai(
        self,
    ) -> bool:
        """Check whether both players are controlled by AI agents.

        Returns
        ------
        bool
            True if both players are AI agents, False otherwise.
        """
        return (
            self.player_configs[Player.LIGHT].kind == PlayerKind.AI
            and self.player_configs[Player.DARK].kind == PlayerKind.AI
        )

    @property
    def is_human_vs_ai(
        self,
    ) -> bool:
        """Check whether the match pits a human player against an AI agent.

        Returns
        ------
        bool
            True if one player is AI and the other is human, False otherwise.
        """
        kinds: set[PlayerKind] = {
            self.player_configs[Player.LIGHT].kind,
            self.player_configs[Player.DARK].kind,
        }
        return kinds == {PlayerKind.HUMAN, PlayerKind.AI}

    @property
    def is_human_vs_human(
        self,
    ) -> bool:
        """Check whether both players are human players.

        Returns
        ------
        bool
            True if both players are human players, False otherwise.
        """
        return (
            self.player_configs[Player.LIGHT].kind == PlayerKind.HUMAN
            and self.player_configs[Player.DARK].kind == PlayerKind.HUMAN
        )

    def _handle_next_move(
        self,
    ) -> None:
        """Trigger the next AI move in an AI-vs-AI match upon button click."""
        if self.engine.status != GameStatus.ONGOING:
            return
        if not self.is_ai_vs_ai:
            return

        self._perform_ai_move()

    def _handle_revert_move(
        self,
    ) -> None:
        """Revert the most recently executed move upon button click."""
        self._ai_timer.stop()
        if self.engine.can_undo():
            self.engine.undo_move()
            self.selected_square = None
            self._update_all()

    def _update_all(
        self,
    ) -> None:
        """Refresh board tiles, status widgets, player cards, and history plot."""
        self.board_widget.refresh_board(self.engine, self.selected_square)

        cur_player: Player = self.engine.current_player
        cur_settings: PlayerSettings = self.player_configs.get(
            cur_player,
            PlayerSettings(PlayerKind.HUMAN),
        )
        is_check: bool = self.engine.is_in_check(cur_player)
        selected_piece: Optional[Piece] = (
            self.engine.get_piece(*self.selected_square)
            if self.selected_square is not None
            else None
        )

        # 1. Update Turn / Match Status banner
        self.turn_status_widget.update_status(
            current_player=cur_player,
            player_settings=cur_settings,
            is_check=is_check,
            status=self.engine.status,
            winner=self.engine.winner,
            turns_played=self.engine.turns_played,
            turn_limit=self.config.turn_limit,
            selected_coords=self.selected_square,
            selected_piece=selected_piece,
            board_rows=self.config.rows,
        )

        # 2. Army values & captured pieces
        light_val: int = self.engine.get_army_value(Player.LIGHT)
        dark_val: int = self.engine.get_army_value(Player.DARK)
        light_captured: list[Piece] = self.engine.get_captured_pieces(
            Player.LIGHT
        )
        dark_captured: list[Piece] = self.engine.get_captured_pieces(Player.DARK)

        # 3. Update Dark Player Card
        self.dark_player_card.update_card(
            settings=self.player_configs[Player.DARK],
            is_current_turn=(
                cur_player == Player.DARK
                and self.engine.status == GameStatus.ONGOING
            ),
            is_in_check=(
                cur_player == Player.DARK
                and is_check
                and self.engine.status == GameStatus.ONGOING
            ),
            army_value=dark_val,
            opponent_army_value=light_val,
            captured_pieces=dark_captured,
            piece_types=self.config.piece_types,
        )

        # 4. Update Light Player Card
        self.light_player_card.update_card(
            settings=self.player_configs[Player.LIGHT],
            is_current_turn=(
                cur_player == Player.LIGHT
                and self.engine.status == GameStatus.ONGOING
            ),
            is_in_check=(
                cur_player == Player.LIGHT
                and is_check
                and self.engine.status == GameStatus.ONGOING
            ),
            army_value=light_val,
            opponent_army_value=dark_val,
            captured_pieces=light_captured,
            piece_types=self.config.piece_types,
        )

        # 5. Update Army Points History Line Plot
        self.army_plot_widget.set_history(self.engine.get_army_history())

        # 6. Update action buttons state based on match mode
        if self.is_ai_vs_ai:
            self.btn_next_move.setVisible(True)
            self.btn_next_move.setEnabled(
                self.engine.status == GameStatus.ONGOING
            )
            self.btn_revert_move.setVisible(True)
            self.btn_revert_move.setEnabled(self.engine.can_undo())
        elif self.is_human_vs_ai:
            self.btn_next_move.setVisible(False)
            self.btn_revert_move.setVisible(True)
            self.btn_revert_move.setEnabled(self.engine.can_undo())
        else:
            self.btn_next_move.setVisible(False)
            self.btn_revert_move.setVisible(False)

        self._check_ai_turn()

    def _check_ai_turn(
        self,
    ) -> None:
        """Schedule an AI move if active player is AI in Human-vs-AI mode."""
        if self.engine.status != GameStatus.ONGOING:
            return

        # AI-vs-AI pacing is manually triggered via btn_next_move
        if not self.is_human_vs_ai:
            return

        current: Player = self.engine.current_player
        settings: PlayerSettings = self.player_configs.get(
            current,
            PlayerSettings(PlayerKind.HUMAN),
        )
        if settings.kind == PlayerKind.AI:
            if not self._ai_timer.isActive():
                self._ai_timer.start(300)

    def _perform_ai_move(
        self,
    ) -> None:
        """Execute a move computed by the active AI agent."""
        if self.engine.status != GameStatus.ONGOING:
            return

        current: Player = self.engine.current_player
        settings: PlayerSettings = self.player_configs.get(
            current,
            PlayerSettings(PlayerKind.HUMAN),
        )
        if settings.kind != PlayerKind.AI:
            return

        ai: Optional[BaseAI] = self.ai_agents.get(current)
        if ai is None:
            return

        move: Optional[Move] = ai.select_move(self.engine)
        if move is not None:
            self.engine.make_move(move)

        self.selected_square = None
        self._update_all()

    def _handle_square_click(
        self,
        row: int,
        col: int,
    ) -> None:
        """Process click events from the chessboard.

        Parameters
        ----------
        row : int
            Row coordinate of clicked square.
        col : int
            Column coordinate of clicked square.
        """
        if self.engine.status != GameStatus.ONGOING:
            return

        # Block user interaction during AI turn
        if (
            self.player_configs[self.engine.current_player].kind
            == PlayerKind.AI
        ):
            return

        if self.selected_square is None:
            piece: Optional[Piece] = self.engine.get_piece(row, col)
            if piece is not None and piece.player == self.engine.current_player:
                self.selected_square = (row, col)
        else:
            sel_r, sel_c = self.selected_square
            if (row, col) == (sel_r, sel_c):
                self.selected_square = None
            else:
                piece = self.engine.get_piece(row, col)
                if (
                    piece is not None
                    and piece.player == self.engine.current_player
                ):
                    self.selected_square = (row, col)
                else:
                    legal_moves: list[Move] = self.engine.get_legal_moves_from(
                        sel_r,
                        sel_c,
                    )
                    matching_moves: list[Move] = [
                        m for m in legal_moves if m.to_pos == (row, col)
                    ]

                    if not matching_moves:
                        self.selected_square = None
                    else:
                        is_promo: bool = any(
                            m.promotion_type is not None
                            for m in matching_moves
                        )
                        if is_promo:
                            promo_options: list[str] = [
                                m.promotion_type
                                for m in matching_moves
                                if m.promotion_type is not None
                            ]
                            chosen_promo: Optional[str] = None
                            if len(promo_options) == 1:
                                chosen_promo = promo_options[0]
                            else:
                                dialog: PromotionDialog = PromotionDialog(
                                    player=self.engine.current_player,
                                    promotions=promo_options,
                                    locale=self.locale,
                                    parent=self,
                                )
                                if dialog.exec() == QDialog.DialogCode.Accepted:
                                    chosen_promo = dialog.selected_piece_type

                            if chosen_promo is not None:
                                candidate_move: Move = Move(
                                    from_pos=(sel_r, sel_c),
                                    to_pos=(row, col),
                                    promotion_type=chosen_promo,
                                )
                                self.engine.make_move(candidate_move)
                        else:
                            candidate_move = Move(
                                from_pos=(sel_r, sel_c),
                                to_pos=(row, col),
                                promotion_type=None,
                            )
                            self.engine.make_move(candidate_move)

                        self.selected_square = None

        self._update_all()

    def _handle_new_game(
        self,
    ) -> None:
        """Open the game configuration dialog and initialize a new match."""
        dialog: GameSetupDialog = GameSetupDialog(
            current_variant=self.current_variant,
            light_settings=self.player_configs[Player.LIGHT],
            dark_settings=self.player_configs[Player.DARK],
            locale=self.locale,
            parent=self,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._start_configured_game(
                variant_name=dialog.selected_variant,
                light_settings=dialog.selected_light_settings,
                dark_settings=dialog.selected_dark_settings,
            )

    def _start_configured_game(
        self,
        variant_name: str,
        light_settings: PlayerSettings,
        dark_settings: PlayerSettings,
    ) -> None:
        """Initialize a new game with chosen variant and player configurations.

        Parameters
        ----------
        variant_name : str
            Variant identifier to load.
        light_settings : PlayerSettings
            Controller configuration for Light player.
        dark_settings : PlayerSettings
            Controller configuration for Dark player.
        """
        self._ai_timer.stop()
        self.player_configs = {
            Player.LIGHT: light_settings,
            Player.DARK: dark_settings,
        }
        self.ai_agents = {
            Player.LIGHT: (
                create_ai(light_settings.ai_name)
                if light_settings.kind == PlayerKind.AI and light_settings.ai_name
                else None
            ),
            Player.DARK: (
                create_ai(dark_settings.ai_name)
                if dark_settings.kind == PlayerKind.AI and dark_settings.ai_name
                else None
            ),
        }

        if variant_name != self.current_variant:
            self._load_game_variant(variant_name)
        else:
            self.engine.reset()
            self.selected_square = None
            self._update_all()

    def _load_game_variant(
        self,
        variant_name: str,
    ) -> None:
        """Re-initialize game engine and board widget with the chosen variant.

        Parameters
        ----------
        variant_name : str
            Identifier of the variant to load.
        """
        self._ai_timer.stop()
        new_config: GameConfig = load_variant_config(variant_name)
        self.config = new_config
        self.current_variant = variant_name
        self.engine = GameEngine(self.config)
        self.selected_square = None

        self.board_container_layout.removeWidget(self.board_widget)
        self.board_widget.deleteLater()

        self.board_widget = ChessBoardWidget(
            self.config,
            self,
        )
        self.board_widget.square_clicked.connect(self._handle_square_click)
        self.board_container_layout.addWidget(
            self.board_widget,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        if self.board_container.width() > 0 and self.board_container.height() > 0:
            self.board_widget.resize_to_fit(
                self.board_container.width(),
                self.board_container.height(),
            )

        self._update_all()

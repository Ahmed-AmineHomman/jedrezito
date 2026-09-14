"""Main desktop application window for the Jedrezito GUI.

This module provides the central application window connecting the responsive chessboard,
game engine, game configuration dialogs, and controls sidebar.
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
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
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
    PIECE_SYMBOLS,
    GameSetupDialog,
    PlayerKind,
    PlayerSettings,
    PromotionDialog,
)
from jedrezito.gui.widgets import (
    GameSelectorWidget,
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
    selector_widget : GameSelectorWidget
        Sidebar widget for variant selection and switching.
    status_box : QLabel
        Banner displaying active player, status, or game result.
    score_light_label : QLabel
        Army value display for light player.
    score_dark_label : QLabel
        Army value display for dark player.
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

        self.setMinimumSize(760, 520)
        if self.start_maximized:
            self.setWindowState(Qt.WindowState.WindowMaximized)
        else:
            self.resize(1020, 700)

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
        """Initialize central layout, controls sidebar, and responsive board widget."""
        central_widget: QWidget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout: QHBoxLayout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(20)

        # Responsive chessboard container on the left
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

        # Control sidebar on the right enclosed in a scroll area for small screens
        sidebar_frame: QFrame = QFrame(self)
        sidebar_frame.setStyleSheet(
            "QFrame {"
            "  background-color: #242220;"
            "  border-radius: 8px;"
            "  padding: 12px;"
            "}"
        )
        sidebar_layout: QVBoxLayout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setSpacing(14)

        app_locale: dict[str, Any] = self.locale.get("app", {})

        # Header Title
        title_label: QLabel = QLabel(
            app_locale.get("sidebar_title", "Jeux d'Échecs Généralisés"),
            self,
        )
        title_label.setStyleSheet(
            "color: #f5f5f5;"
            "font-size: 18px;"
            "font-weight: bold;"
        )
        subtitle_label: QLabel = QLabel(
            app_locale.get(
                "sidebar_description",
                "Affrontement local au tour par tour (mode hotseat)",
            ),
            self,
        )
        subtitle_label.setWordWrap(True)
        subtitle_label.setStyleSheet(
            "color: #a8a096;"
            "font-size: 13px;"
        )
        sidebar_layout.addWidget(title_label)
        sidebar_layout.addWidget(subtitle_label)

        # Game Selector Group
        self.selector_widget: GameSelectorWidget = GameSelectorWidget(
            current_variant=self.current_variant,
            locale=self.locale,
            parent=self,
        )
        self.selector_widget.variant_selected.connect(
            self._handle_variant_selected
        )
        sidebar_layout.addWidget(self.selector_widget)

        # Status Banner Box
        self.status_box: QLabel = QLabel(self)
        self.status_box.setWordWrap(True)
        self.status_box.setStyleSheet(
            "QLabel {"
            "  background-color: #1a1816;"
            "  color: #e0d8cf;"
            "  border: 1px solid #3c3834;"
            "  border-radius: 6px;"
            "  padding: 10px;"
            "  font-size: 14px;"
            "}"
        )
        sidebar_layout.addWidget(self.status_box)

        # Army Scores Group
        scores_locale: dict[str, Any] = self.locale.get("scores", {})
        scores_group: QGroupBox = QGroupBox(
            scores_locale.get("group_title", "Valeur des armées"),
            self,
        )
        scores_group.setStyleSheet(
            "QGroupBox {"
            "  color: #d6cfc7;"
            "  font-weight: bold;"
            "  border: 1px solid #3c3834;"
            "  border-radius: 6px;"
            "  margin-top: 10px;"
            "  padding-top: 12px;"
            "}"
            "QGroupBox::title {"
            "  subcontrol-origin: margin;"
            "  left: 10px;"
            "  padding: 0 4px;"
            "}"
        )
        scores_layout: QHBoxLayout = QHBoxLayout(scores_group)

        self.score_light_label: QLabel = QLabel("", self)
        self.score_light_label.setStyleSheet(
            "background-color: #332f2b;"
            "color: #ffffff;"
            "font-size: 14px;"
            "font-weight: bold;"
            "padding: 8px;"
            "border-radius: 4px;"
            "qproperty-alignment: AlignCenter;"
        )
        scores_layout.addWidget(self.score_light_label)

        self.score_dark_label: QLabel = QLabel("", self)
        self.score_dark_label.setStyleSheet(
            "background-color: #1a1715;"
            "color: #cccccc;"
            "font-size: 14px;"
            "font-weight: bold;"
            "padding: 8px;"
            "border-radius: 4px;"
            "qproperty-alignment: AlignCenter;"
        )
        scores_layout.addWidget(self.score_dark_label)
        sidebar_layout.addWidget(scores_group)

        # Spacer to push action buttons down
        sidebar_layout.addSpacerItem(
            QSpacerItem(
                20,
                20,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            )
        )

        controls_locale: dict[str, Any] = self.locale.get("controls", {})

        # Next move (AI pacing) button
        self.btn_next_move: QPushButton = QPushButton(
            controls_locale.get("btn_next_move", "Coup suivant"),
            self,
        )
        self.btn_next_move.setStyleSheet(
            "QPushButton {"
            "  background-color: #385e26;"
            "  color: #ffffff;"
            "  font-size: 14px;"
            "  font-weight: bold;"
            "  padding: 10px;"
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
        sidebar_layout.addWidget(self.btn_next_move)

        # Revert move button
        self.btn_revert_move: QPushButton = QPushButton(
            controls_locale.get("btn_revert_move", "Annuler le coup"),
            self,
        )
        self.btn_revert_move.setStyleSheet(
            "QPushButton {"
            "  background-color: #332f2b;"
            "  color: #f0eae1;"
            "  font-size: 14px;"
            "  font-weight: bold;"
            "  padding: 10px;"
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
        sidebar_layout.addWidget(self.btn_revert_move)

        # Reset / Configure Game Button
        self.btn_new_game: QPushButton = QPushButton(
            app_locale.get("btn_new_game", "Nouvelle partie"),
            self,
        )
        self.btn_new_game.setStyleSheet(
            "QPushButton {"
            "  background-color: #4a752c;"
            "  color: #ffffff;"
            "  font-size: 15px;"
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
        sidebar_layout.addWidget(self.btn_new_game)

        sidebar_scroll: QScrollArea = QScrollArea(self)
        sidebar_scroll.setFixedWidth(350)
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setFrameShape(QFrame.Shape.NoFrame)
        sidebar_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        sidebar_scroll.setWidget(sidebar_frame)

        main_layout.addWidget(sidebar_scroll, stretch=0)

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

    def _format_status_message(
        self,
    ) -> str:
        """Format the localized status message based on current engine state.

        Returns
        -------
        str
            Status string for display.
        """
        status_locale: dict[str, Any] = self.locale.get("status", {})
        players_locale: dict[str, Any] = self.locale.get("players", {})
        pieces_locale: dict[str, Any] = self.locale.get("pieces", {})

        light_name: str = players_locale.get("light", "Blancs")
        dark_name: str = players_locale.get("dark", "Noirs")

        if self.engine.status == GameStatus.CHECKMATE:
            winner_str: str = (
                light_name if self.engine.winner == Player.LIGHT else dark_name
            )
            template: str = status_locale.get(
                "checkmate",
                "🏆 Échec et mat !\nVictoire des {winner}.",
            )
            return template.format(winner=winner_str)

        if self.engine.status == GameStatus.STALEMATE:
            return status_locale.get(
                "stalemate",
                "🤝 Pat !\nLa partie se termine par un match nul.",
            )

        if self.engine.status == GameStatus.TURN_EXHAUSTED:
            if self.engine.winner is not None:
                winner_str = (
                    light_name
                    if self.engine.winner == Player.LIGHT
                    else dark_name
                )
                template = status_locale.get(
                    "turn_exhausted_win",
                    "⌛ Épuisement des tours !\nVictoire des {winner} au matériel.",
                )
                return template.format(winner=winner_str)
            return status_locale.get(
                "turn_exhausted_draw",
                "⌛ Épuisement des tours !\nÉgalité matérielle parfaite.",
            )

        player_camp: Player = self.engine.current_player
        player_str: str = (
            light_name if player_camp == Player.LIGHT else dark_name
        )

        ctrl_settings: PlayerSettings = self.player_configs.get(
            player_camp,
            PlayerSettings(PlayerKind.HUMAN),
        )
        if ctrl_settings.kind == PlayerKind.AI:
            ai_name_str: str = ctrl_settings.ai_name or "joker"
            ai_name_disp: str = self.locale.get("ais", {}).get(
                ai_name_str,
                ai_name_str.capitalize(),
            )
            controller_label: str = (
                f"{players_locale.get('ai', 'IA')} {ai_name_disp}"
            )
        else:
            controller_label = players_locale.get("human", "Humain")

        turn_template: str = status_locale.get(
            "turn",
            "Tour : {player}",
        )
        base_status: str = (
            f"{turn_template.format(player=player_str)} ({controller_label})"
        )

        check_note: str = ""
        if self.engine.is_in_check(self.engine.current_player):
            check_note = status_locale.get(
                "check_warning",
                "\n⚠️ Échec au Roi !",
            )

        selection_note: str = ""
        if self.selected_square is not None:
            r, c = self.selected_square
            piece: Optional[Piece] = self.engine.get_piece(r, c)
            if piece is not None:
                symbol: str = PIECE_SYMBOLS.get(
                    (piece.piece_type, piece.player),
                    piece.piece_type,
                )
                coord_str: str = f"{chr(ord('a') + c)}{r + 1}"
                local_type: str = pieces_locale.get(
                    piece.piece_type,
                    piece.piece_type,
                )
                selection_template: str = status_locale.get(
                    "selection_pattern",
                    "\nSélection : {symbol} {piece_name} ({coords})",
                )
                selection_note = selection_template.format(
                    symbol=symbol,
                    piece_name=local_type,
                    coords=coord_str,
                )

        return f"{base_status}{check_note}{selection_note}"

    @property
    def is_ai_vs_ai(
        self,
    ) -> bool:
        """Check whether both players are controlled by AI agents.

        Returns
        -------
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
        -------
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
        -------
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
        """Refresh board tiles, status text, army scores, and action controls."""
        self.board_widget.refresh_board(self.engine, self.selected_square)
        self.status_box.setText(self._format_status_message())

        scores_locale: dict[str, Any] = self.locale.get("scores", {})
        light_template: str = scores_locale.get(
            "score_light",
            "Blancs : {score}",
        )
        dark_template: str = scores_locale.get(
            "score_dark",
            "Noirs : {score}",
        )

        light_val: float = self.engine.get_army_value(Player.LIGHT)
        dark_val: float = self.engine.get_army_value(Player.DARK)

        self.score_light_label.setText(
            light_template.format(score=f"{light_val:g}")
        )
        self.score_dark_label.setText(
            dark_template.format(score=f"{dark_val:g}")
        )

        # Update action buttons state based on match mode
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

    def _handle_variant_selected(
        self,
        variant_name: str,
    ) -> None:
        """Process variant selection request and prompt if a match is in progress.

        Parameters
        ----------
        variant_name : str
            Identifier of the variant to load.
        """
        total_moves: int = sum(self.engine.turns_played.values())
        if self.engine.status == GameStatus.ONGOING and total_moves > 0:
            selector_locale: dict[str, Any] = self.locale.get("selector", {})
            title: str = selector_locale.get(
                "confirm_switch_title",
                "Changer de variante",
            )
            message: str = selector_locale.get(
                "confirm_switch_message",
                "Une partie est en cours. Voulez-vous vraiment charger cette variante et réinitialiser la partie ?",
            )
            reply = QMessageBox.question(
                self,
                title,
                message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                self.selector_widget.set_current_variant(self.current_variant)
                return

        self._start_configured_game(
            variant_name=variant_name,
            light_settings=self.player_configs[Player.LIGHT],
            dark_settings=self.player_configs[Player.DARK],
        )

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

        self.selector_widget.set_current_variant(variant_name)
        self._update_all()

"""Jedrezito main desktop GUI application.

This module exposes a PySide6 graphical user interface allowing two human players
to play Generalized Chess Games (JEG) in hotseat mode with customizable variants and locales.
"""

from __future__ import annotations

import argparse
import sys
from typing import (
    Any,
    Optional,
)

from PySide6.QtCore import (
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QFont,
)
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from jedrezito.config import (
    get_variant_metadata,
    list_available_variants,
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

PIECE_SYMBOLS: dict[tuple[str, Player], str] = {
    ("King", Player.LIGHT): "♔",
    ("Queen", Player.LIGHT): "♕",
    ("Rook", Player.LIGHT): "♖",
    ("Bishop", Player.LIGHT): "♗",
    ("Knight", Player.LIGHT): "♘",
    ("Pawn", Player.LIGHT): "♙",
    ("King", Player.DARK): "♚",
    ("Queen", Player.DARK): "♛",
    ("Rook", Player.DARK): "♜",
    ("Bishop", Player.DARK): "♝",
    ("Knight", Player.DARK): "♞",
    ("Pawn", Player.DARK): "♟",
}


class PromotionDialog(QDialog):
    """Modal dialog prompting the active player to choose a promotion head piece.

    Parameters
    ----------
    player : Player
        The active player executing the promotion.
    promotions : list of str
        Names of allowed piece types eligible for promotion.
    locale : dict of str to Any
        Localized GUI strings dictionary.
    parent : QWidget or None, optional
        Parent widget, by default None.

    Attributes
    ----------
    selected_piece_type : str or None
        The piece type chosen by the player, or None if dismissed.
    locale : dict of str to Any
        Active localization dictionary.
    """

    def __init__(
        self,
        player: Player,
        promotions: list[str],
        locale: dict[str, Any],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.locale: dict[str, Any] = locale
        self.selected_piece_type: Optional[str] = None

        promo_locale: dict[str, Any] = self.locale.get(
            "dialogs", {}
        ).get("promotion", {})

        self.setWindowTitle(
            promo_locale.get("window_title", "Promotion du pion")
        )
        self.setModal(True)
        self.setStyleSheet(
            "QDialog {"
            "  background-color: #242220;"
            "  border: 2px solid #3c3834;"
            "  border-radius: 8px;"
            "}"
        )

        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        prompt_label: QLabel = QLabel(
            promo_locale.get(
                "prompt",
                "Choisissez une pièce pour la promotion :",
            ),
            self,
        )
        prompt_label.setStyleSheet(
            "color: #f0eae1;"
            "font-size: 14px;"
            "font-weight: bold;"
            "qproperty-alignment: AlignCenter;"
        )
        layout.addWidget(prompt_label)

        button_layout: QHBoxLayout = QHBoxLayout()
        button_layout.setSpacing(10)

        piece_names: dict[str, str] = self.locale.get("pieces", {})

        for promo_name in promotions:
            piece_label: str = piece_names.get(promo_name, promo_name)
            symbol: str = PIECE_SYMBOLS.get((promo_name, player), promo_name)
            btn: QPushButton = QPushButton(f"{symbol}  {piece_label}", self)
            btn.setStyleSheet(
                "QPushButton {"
                "  background-color: #332f2b;"
                "  color: #f0eae1;"
                "  font-size: 15px;"
                "  font-weight: bold;"
                "  padding: 10px 14px;"
                "  border: 1px solid #4a443e;"
                "  border-radius: 6px;"
                "}"
                "QPushButton:hover {"
                "  background-color: #4a752c;"
                "  color: #ffffff;"
                "  border-color: #5d9337;"
                "}"
                "QPushButton:pressed {"
                "  background-color: #3b5e23;"
                "}"
            )
            btn.clicked.connect(
                lambda checked=False, p=promo_name: self._choose_piece(p)
            )
            button_layout.addWidget(btn)

        layout.addLayout(button_layout)

    def _choose_piece(
        self,
        piece_type: str,
    ) -> None:
        """Record chosen piece type and accept dialog.

        Parameters
        ----------
        piece_type : str
            Name of chosen piece type.
        """
        self.selected_piece_type = piece_type
        self.accept()


class ChessSquareButton(QPushButton):
    """Square button representing an individual tile on the chessboard.

    Parameters
    ----------
    row : int
        Row index of the square (0 corresponds to rank 1).
    col : int
        Column index of the square (0 corresponds to file a).
    parent : QWidget or None, optional
        Parent widget, by default None.

    Attributes
    ----------
    row : int
        Row index of the square.
    col : int
        Column index of the square.
    is_light : bool
        Whether this is a light-colored checkered tile.
    """

    clicked_square: Signal = Signal(int, int)

    def __init__(
        self,
        row: int,
        col: int,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.row: int = row
        self.col: int = col
        self.is_light: bool = (row + col) % 2 == 1

        self.setFixedSize(QSize(62, 62))
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        font: QFont = self.font()
        font.setPointSize(26)
        font.setBold(True)
        self.setFont(font)

        self.clicked.connect(self._on_clicked)

    def _on_clicked(
        self,
    ) -> None:
        """Forward the button click signal with square coordinates."""
        self.clicked_square.emit(self.row, self.col)

    def update_tile(
        self,
        piece: Optional[Piece],
        is_selected: bool,
        is_legal_dest: bool,
        is_capture_dest: bool,
        is_king_check: bool,
    ) -> None:
        """Update square visual state, symbol, and stylesheet.

        Parameters
        ----------
        piece : Piece or None
            Piece currently occupying the square, if any.
        is_selected : bool
            Whether the square is currently selected by the active player.
        is_legal_dest : bool
            Whether the square is a legal destination for the selected piece.
        is_capture_dest : bool
            Whether the destination square involves capturing an opposing piece.
        is_king_check : bool
            Whether this square holds a king currently in check.
        """
        base_color: str = "#f0d9b5" if self.is_light else "#b58863"
        border_style: str = "border: 1px solid rgba(0, 0, 0, 0.15);"
        text_color: str = "#1e1c1a"

        if piece is not None:
            symbol: str = PIECE_SYMBOLS.get(
                (piece.piece_type, piece.player),
                piece.piece_type,
            )
            self.setText(symbol)
            if piece.player == Player.LIGHT:
                text_color = "#ffffff"
            else:
                text_color = "#181614"
        else:
            self.setText("")

        if is_selected:
            bg_color: str = "#829769"
            border_style = "border: 3px solid #f6f669;"
        elif is_king_check:
            bg_color = "#e53935"
            border_style = "border: 3px solid #b71c1c;"
        elif is_capture_dest:
            bg_color = "#e57373"
            border_style = "border: 3px solid #c62828;"
        elif is_legal_dest:
            bg_color = "#a9b870"
            border_style = "border: 2px dashed #4b6b28;"
            if piece is None:
                self.setText("●")
                text_color = "#455325"
        else:
            bg_color = base_color

        self.setStyleSheet(
            f"QPushButton {{"
            f"  background-color: {bg_color};"
            f"  color: {text_color};"
            f"  {border_style}"
            f"  border-radius: 4px;"
            f"}}"
        )


class ChessBoardWidget(QFrame):
    """Chessboard grid widget with rank and file coordinate indicators.

    Parameters
    ----------
    config : GameConfig
        Board configuration containing dimension parameters.
    parent : QWidget or None, optional
        Parent widget, by default None.

    Attributes
    ----------
    config : GameConfig
        Active variant board configuration.
    square_buttons : dict of tuple of int to ChessSquareButton
        Map of (row, col) coordinates to square button instances.
    """

    square_clicked: Signal = Signal(int, int)

    def __init__(
        self,
        config: GameConfig,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.config: GameConfig = config
        self.square_buttons: dict[tuple[int, int], ChessSquareButton] = {}

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            "ChessBoardWidget {"
            "  background-color: #2b2724;"
            "  border: 2px solid #1a1715;"
            "  border-radius: 8px;"
            "  padding: 8px;"
            "}"
        )

        self._build_grid()

    def _build_grid(
        self,
    ) -> None:
        """Construct the inner grid layout with coordinate markers and squares."""
        grid: QGridLayout = QGridLayout(self)
        grid.setSpacing(1)
        grid.setContentsMargins(6, 6, 6, 6)

        label_style: str = (
            "color: #b0a89f;"
            "font-size: 13px;"
            "font-weight: bold;"
            "qproperty-alignment: AlignCenter;"
        )

        # File headers (top and bottom)
        for c in range(self.config.cols):
            file_char: str = chr(ord("a") + c)
            lbl_top: QLabel = QLabel(file_char)
            lbl_top.setStyleSheet(label_style)
            lbl_top.setFixedHeight(22)
            grid.addWidget(lbl_top, 0, c + 1)

            lbl_bottom: QLabel = QLabel(file_char)
            lbl_bottom.setStyleSheet(label_style)
            lbl_bottom.setFixedHeight(22)
            grid.addWidget(lbl_bottom, self.config.rows + 1, c + 1)

        # Rank headers (left and right) and interactive squares
        for r in range(self.config.rows):
            grid_row: int = self.config.rows - r
            rank_str: str = str(r + 1)

            lbl_left: QLabel = QLabel(rank_str)
            lbl_left.setStyleSheet(label_style)
            lbl_left.setFixedWidth(22)
            grid.addWidget(lbl_left, grid_row, 0)

            lbl_right: QLabel = QLabel(rank_str)
            lbl_right.setStyleSheet(label_style)
            lbl_right.setFixedWidth(22)
            grid.addWidget(lbl_right, grid_row, self.config.cols + 1)

            for c in range(self.config.cols):
                btn: ChessSquareButton = ChessSquareButton(r, c, self)
                btn.clicked_square.connect(self._on_square_clicked)
                self.square_buttons[(r, c)] = btn
                grid.addWidget(btn, grid_row, c + 1)

    def _on_square_clicked(
        self,
        row: int,
        col: int,
    ) -> None:
        """Bubble up square click events.

        Parameters
        ----------
        row : int
            Row coordinate of clicked square.
        col : int
            Column coordinate of clicked square.
        """
        self.square_clicked.emit(row, col)

    def refresh_board(
        self,
        engine: GameEngine,
        selected_square: Optional[tuple[int, int]],
    ) -> None:
        """Render all tiles according to active game engine state.

        Parameters
        ----------
        engine : GameEngine
            Active game engine instance.
        selected_square : tuple of int or None
            Coordinates of currently selected square, if any.
        """
        legal_destinations: set[tuple[int, int]] = set()
        if selected_square is not None:
            sr, sc = selected_square
            moves = engine.get_legal_moves_from(sr, sc)
            for m in moves:
                legal_destinations.add(m.to_pos)

        is_in_check: bool = engine.is_in_check(engine.current_player)
        king_pos: Optional[tuple[int, int]] = (
            engine.find_king(engine.current_player) if is_in_check else None
        )

        for (r, c), btn in self.square_buttons.items():
            piece: Optional[Piece] = engine.get_piece(r, c)
            is_selected: bool = selected_square == (r, c)
            is_dest: bool = (r, c) in legal_destinations
            is_capture: bool = is_dest and (piece is not None)
            is_check: bool = king_pos == (r, c)

            btn.update_tile(
                piece=piece,
                is_selected=is_selected,
                is_legal_dest=is_dest,
                is_capture_dest=is_capture,
                is_king_check=is_check,
            )


class GameSelectorWidget(QGroupBox):
    """Sidebar widget facilitating in-app game variant selection and engine re-initialization.

    Parameters
    ----------
    current_variant : str
        Identifier of the currently loaded variant.
    locale : dict of str to Any
        Localized GUI strings dictionary.
    parent : QWidget or None, optional
        Parent widget, by default None.

    Attributes
    ----------
    variant_selected : Signal
        Signal emitted with the selected variant identifier when confirmed.
    locale : dict of str to Any
        Active localization strings dictionary.
    combo_variants : QComboBox
        Dropdown selector of available game variants.
    lbl_dimensions : QLabel
        Label displaying board dimensions of the selected variant.
    lbl_turn_limit : QLabel
        Label displaying turn limit of the selected variant.
    btn_load : QPushButton
        Button triggering variant loading into the engine.
    """

    variant_selected: Signal = Signal(str)

    def __init__(
        self,
        current_variant: str,
        locale: dict[str, Any],
        parent: Optional[QWidget] = None,
    ) -> None:
        selector_locale: dict[str, Any] = locale.get("selector", {})
        title: str = selector_locale.get("group_title", "Variante de jeu")
        super().__init__(title, parent)
        self.locale: dict[str, Any] = locale
        self._current_variant: str = current_variant

        self.setStyleSheet(
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

        self._setup_ui()
        self.set_current_variant(current_variant)

    def _setup_ui(
        self,
    ) -> None:
        """Initialize child widgets and layout for variant selection."""
        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)

        selector_locale: dict[str, Any] = self.locale.get("selector", {})

        # Dropdown for available variants
        self.combo_variants: QComboBox = QComboBox(self)
        self.combo_variants.setStyleSheet(
            "QComboBox {"
            "  background-color: #332f2b;"
            "  color: #f0eae1;"
            "  border: 1px solid #4a443e;"
            "  border-radius: 6px;"
            "  padding: 6px 10px;"
            "  font-size: 13px;"
            "}"
            "QComboBox:hover {"
            "  border-color: #5d9337;"
            "}"
            "QComboBox::drop-down {"
            "  border: none;"
            "  width: 20px;"
            "}"
            "QComboBox QAbstractItemView {"
            "  background-color: #242220;"
            "  color: #f0eae1;"
            "  selection-background-color: #4a752c;"
            "  selection-color: #ffffff;"
            "  border: 1px solid #4a443e;"
            "  outline: none;"
            "}"
        )

        variants: list[str] = list_available_variants()
        for v in variants:
            try:
                meta: dict[str, Any] = get_variant_metadata(v)
                disp_name: str = meta.get("name", v)
            except Exception:
                disp_name = v
            self.combo_variants.addItem(f"{disp_name} ({v})", v)

        self.combo_variants.currentIndexChanged.connect(self._on_combo_changed)
        layout.addWidget(self.combo_variants)

        # Metadata preview container
        meta_frame: QFrame = QFrame(self)
        meta_frame.setStyleSheet(
            "QFrame {"
            "  background-color: #1a1816;"
            "  border: 1px solid #332f2b;"
            "  border-radius: 4px;"
            "  padding: 6px;"
            "}"
        )
        meta_layout: QVBoxLayout = QVBoxLayout(meta_frame)
        meta_layout.setContentsMargins(6, 6, 6, 6)
        meta_layout.setSpacing(4)

        self.lbl_dimensions: QLabel = QLabel(self)
        self.lbl_dimensions.setStyleSheet("color: #b0a89f; font-size: 12px;")
        meta_layout.addWidget(self.lbl_dimensions)

        self.lbl_turn_limit: QLabel = QLabel(self)
        self.lbl_turn_limit.setStyleSheet("color: #b0a89f; font-size: 12px;")
        meta_layout.addWidget(self.lbl_turn_limit)

        layout.addWidget(meta_frame)

        # Load button
        self.btn_load: QPushButton = QPushButton(
            selector_locale.get("btn_load", "Charger la variante"),
            self,
        )
        self.btn_load.setStyleSheet(
            "QPushButton {"
            "  background-color: #385e26;"
            "  color: #ffffff;"
            "  font-size: 13px;"
            "  font-weight: bold;"
            "  padding: 8px;"
            "  border: none;"
            "  border-radius: 5px;"
            "}"
            "QPushButton:hover {"
            "  background-color: #4a752c;"
            "}"
            "QPushButton:pressed {"
            "  background-color: #2b451c;"
            "}"
        )
        self.btn_load.clicked.connect(self._on_load_clicked)
        layout.addWidget(self.btn_load)

    def _on_combo_changed(
        self,
        index: int,
    ) -> None:
        """Update metadata summary display when combo selection changes.

        Parameters
        ----------
        index : int
            Current index in the variant combo box.
        """
        variant_id: Optional[str] = self.combo_variants.itemData(index)
        if variant_id is not None:
            self._update_preview(variant_id)

    def _update_preview(
        self,
        variant_id: str,
    ) -> None:
        """Refresh dimension and turn limit display labels.

        Parameters
        ----------
        variant_id : str
            Identifier of the variant.
        """
        selector_locale: dict[str, Any] = self.locale.get("selector", {})
        try:
            meta: dict[str, Any] = get_variant_metadata(variant_id)
            dim_template: str = selector_locale.get(
                "dimensions_label",
                "Plateau : {rows} × {cols}",
            )
            self.lbl_dimensions.setText(
                dim_template.format(rows=meta["rows"], cols=meta["cols"])
            )

            turn_limit: Optional[int] = meta.get("turn_limit")
            limit_str: str = (
                str(turn_limit)
                if turn_limit is not None
                else selector_locale.get("turn_limit_none", "Illimité")
            )
            turn_template: str = selector_locale.get(
                "turn_limit_label",
                "Limite de tours : {limit}",
            )
            self.lbl_turn_limit.setText(turn_template.format(limit=limit_str))
        except Exception:
            self.lbl_dimensions.setText("")
            self.lbl_turn_limit.setText("")

    def _on_load_clicked(
        self,
    ) -> None:
        """Emit variant selection signal when user confirms load."""
        idx: int = self.combo_variants.currentIndex()
        if idx >= 0:
            variant_id: Optional[str] = self.combo_variants.itemData(idx)
            if variant_id is not None:
                self.variant_selected.emit(variant_id)

    def set_current_variant(
        self,
        variant_name: str,
    ) -> None:
        """Synchronize dropdown selection and preview with current variant.

        Parameters
        ----------
        variant_name : str
            Variant identifier to select.
        """
        self._current_variant = variant_name
        for i in range(self.combo_variants.count()):
            if self.combo_variants.itemData(i) == variant_name:
                self.combo_variants.setCurrentIndex(i)
                self._update_preview(variant_name)
                break


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
    parent : QWidget or None, optional
        Parent widget, by default None.

    Attributes
    ----------
    config : GameConfig
        Active JEG game configuration.
    locale : dict of str to Any
        Active localization strings dictionary.
    current_variant : str
        Identifier of the active game variant.
    engine : GameEngine
        Active JEG game engine instance.
    selected_square : tuple of int or None
        Coordinates (row, col) of currently selected square.
    board_container : QWidget
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
    btn_new_game : QPushButton
        Reset button to start a fresh match with active variant.
    """

    def __init__(
        self,
        config: GameConfig,
        locale: dict[str, Any],
        initial_variant: str = "chess",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.config: GameConfig = config
        self.locale: dict[str, Any] = locale
        self.current_variant: str = initial_variant

        app_locale: dict[str, Any] = self.locale.get("app", {})
        self.setWindowTitle(
            app_locale.get(
                "window_title",
                "Jedrezito — Jeux d'Échecs Généralisés",
            )
        )

        self.engine: GameEngine = GameEngine(self.config)
        self.selected_square: Optional[tuple[int, int]] = None

        self._setup_ui()
        self._update_all()

    def _setup_ui(
        self,
    ) -> None:
        """Initialize central layout, controls sidebar, and board widget."""
        central_widget: QWidget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout: QHBoxLayout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(20)

        # Chessboard container on the left
        self.board_container: QWidget = QWidget(self)
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
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        # Control sidebar on the right
        sidebar_frame: QFrame = QFrame(self)
        sidebar_frame.setFixedWidth(340)
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

        # Reset Game Button
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

        main_layout.addWidget(sidebar_frame)

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
                    light_name if self.engine.winner == Player.LIGHT else dark_name
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

        player_str: str = (
            light_name if self.engine.current_player == Player.LIGHT else dark_name
        )
        turn_template: str = status_locale.get(
            "turn",
            "Tour : {player}",
        )
        base_status: str = turn_template.format(player=player_str)

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

    def _update_all(
        self,
    ) -> None:
        """Refresh board tiles, status text, and army scores."""
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
        """Reset the match and restore the initial game state."""
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

        self._load_game_variant(variant_name)

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

        self.selector_widget.set_current_variant(variant_name)
        self._update_all()
        self.adjustSize()


def main(
) -> None:
    """Launch the Jedrezito PySide6 desktop GUI application."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Jedrezito - Generalized Chess Games (JEG) Desktop GUI",
    )
    parser.add_argument(
        "--game",
        type=str,
        default="chess",
        help="Name of the chess variant to load (default: chess)",
    )
    parser.add_argument(
        "--language",
        type=str,
        default="fr",
        help="Interface language code (default: fr)",
    )
    args: argparse.Namespace = parser.parse_args()

    config: GameConfig = load_variant_config(args.game)
    locale: dict[str, Any] = load_locale(args.language)

    app: QApplication = QApplication(sys.argv)
    window: MainWindow = MainWindow(
        config=config,
        locale=locale,
        initial_variant=args.game,
    )
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

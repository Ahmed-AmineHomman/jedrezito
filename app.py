"""Jedrezito main desktop GUI application.

This module exposes a PySide6 graphical user interface allowing two human players
to play Generalized Chess Games (JEG) in hotseat mode on the default chess variant.
"""

from __future__ import annotations

import sys
from typing import Optional

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
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from jedrezito.config import load_default_chess_config
from jedrezito.engine import GameEngine
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

FRENCH_PROMOTION_MAP: dict[str, str] = {
    "Reine": "Queen",
    "Tour": "Rook",
    "Fou": "Bishop",
    "Cavalier": "Knight",
}


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

        shadow_style: str = ""
        if piece is not None and piece.player == Player.LIGHT:
            shadow_style = (
                "color: #ffffff; "
                "-webkit-text-stroke: 1px #111111; "
            )

        self.setStyleSheet(
            f"QPushButton {{"
            f"  background-color: {bg_color};"
            f"  color: {text_color};"
            f"  {border_style}"
            f"  border-radius: 4px;"
            f"  {shadow_style}"
            f"}}"
            f"QPushButton:hover {{"
            f"  filter: brightness(1.1);"
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


class MainWindow(QMainWindow):
    """Main desktop application window for Jedrezito chess games.

    Parameters
    ----------
    parent : QWidget or None, optional
        Parent widget, by default None.

    Attributes
    ----------
    engine : GameEngine
        Active JEG game engine instance.
    selected_square : tuple of int or None
        Coordinates (row, col) of currently selected square.
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Jedrezito - Jeux d'Échecs Généralisés")

        config: GameConfig = load_default_chess_config()
        self.engine: GameEngine = GameEngine(config)
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

        # Chessboard on the left
        self.board_widget: ChessBoardWidget = ChessBoardWidget(
            self.engine.config,
            self,
        )
        self.board_widget.square_clicked.connect(self._handle_square_click)
        main_layout.addWidget(
            self.board_widget,
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

        # Header Title
        title_label: QLabel = QLabel("Jeux d'Échecs Généralisés", self)
        title_label.setStyleSheet(
            "color: #f5f5f5;"
            "font-size: 18px;"
            "font-weight: bold;"
        )
        subtitle_label: QLabel = QLabel(
            "Mode hotseat (2 joueurs humains)",
            self,
        )
        subtitle_label.setStyleSheet(
            "color: #a8a096;"
            "font-size: 13px;"
        )
        sidebar_layout.addWidget(title_label)
        sidebar_layout.addWidget(subtitle_label)

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
        scores_group: QGroupBox = QGroupBox("Valeur des armées", self)
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

        self.score_light_label: QLabel = QLabel("Blancs : 0", self)
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

        self.score_dark_label: QLabel = QLabel("Noirs : 0", self)
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

        # Promotion selector
        promo_group: QGroupBox = QGroupBox("Promotion du pion", self)
        promo_group.setStyleSheet(
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
        promo_layout: QVBoxLayout = QVBoxLayout(promo_group)
        self.promo_combo: QComboBox = QComboBox(self)
        self.promo_combo.addItems(["Reine", "Tour", "Fou", "Cavalier"])
        self.promo_combo.setStyleSheet(
            "QComboBox {"
            "  background-color: #332f2b;"
            "  color: #f0eae1;"
            "  border: 1px solid #4a443e;"
            "  border-radius: 4px;"
            "  padding: 6px;"
            "  font-size: 13px;"
            "}"
            "QComboBox::drop-down {"
            "  border: none;"
            "}"
            "QComboBox QAbstractItemView {"
            "  background-color: #2b2724;"
            "  color: #f0eae1;"
            "  selection-background-color: #829769;"
            "}"
        )
        promo_layout.addWidget(self.promo_combo)
        sidebar_layout.addWidget(promo_group)

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
        self.btn_new_game: QPushButton = QPushButton("Nouvelle partie", self)
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
        """Format the French status message based on current engine state.

        Returns
        -------
        str
            Status string for display.
        """
        if self.engine.status == GameStatus.CHECKMATE:
            if self.engine.winner == Player.LIGHT:
                return "🏆 Échec et mat !\nLes Blancs remportent la partie."
            return "🏆 Échec et mat !\nLes Noirs remportent la partie."

        if self.engine.status == GameStatus.STALEMATE:
            return "🤝 Pat !\nLa partie se termine par un match nul."

        if self.engine.status == GameStatus.TURN_EXHAUSTED:
            if self.engine.winner == Player.LIGHT:
                return "⌛ Épuisement des tours !\nVictoire des Blancs au matériel."
            if self.engine.winner == Player.DARK:
                return "⌛ Épuisement des tours !\nVictoire des Noirs au matériel."
            return "⌛ Épuisement des tours !\nÉgalité matérielle."

        player_str: str = (
            "Blancs" if self.engine.current_player == Player.LIGHT else "Noirs"
        )
        check_note: str = (
            "\n⚠️ Échec au Roi !"
            if self.engine.is_in_check(self.engine.current_player)
            else ""
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
                selection_note = f"\nSélection : {symbol} {piece.piece_type} ({coord_str})"

        return f"Tour : {player_str}{check_note}{selection_note}"

    def _update_all(
        self,
    ) -> None:
        """Refresh board tiles, status text, and army scores."""
        self.board_widget.refresh_board(self.engine, self.selected_square)
        self.status_box.setText(self._format_status_message())

        light_val: float = self.engine.get_army_value(Player.LIGHT)
        dark_val: float = self.engine.get_army_value(Player.DARK)
        self.score_light_label.setText(f"Blancs : {light_val:g}")
        self.score_dark_label.setText(f"Noirs : {dark_val:g}")

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
                if piece is not None and piece.player == self.engine.current_player:
                    self.selected_square = (row, col)
                else:
                    promo_choice: str = self.promo_combo.currentText()
                    promo_type: str = FRENCH_PROMOTION_MAP.get(
                        promo_choice,
                        "Queen",
                    )
                    candidate_move: Move = Move(
                        from_pos=(sel_r, sel_c),
                        to_pos=(row, col),
                        promotion_type=promo_type,
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


def main(
) -> None:
    """Launch the Jedrezito PySide6 desktop GUI application."""
    app: QApplication = QApplication(sys.argv)
    window: MainWindow = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

"""Chessboard grid widgets and responsive scaling components for Jedrezito GUI.

This module implements square buttons, coordinate labels, the main chessboard grid frame,
and a responsive container dynamically adapting the board geometry to any screen format.
"""

from __future__ import annotations

from typing import (
    Optional,
)

from PySide6.QtCore import (
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QFont,
    QResizeEvent,
)
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QWidget,
)

from jedrezito.engine import (
    GameEngine,
)
from jedrezito.gui.dialogs import (
    PIECE_SYMBOLS,
)
from jedrezito.models import (
    GameConfig,
    Piece,
    Player,
)


class ChessSquareButton(QPushButton):
    """Square button representing an individual tile on the chessboard.

    Parameters
    ----------
    row : int
        Row index of the square (0 corresponds to rank 1).
    col : int
        Column index of the square (0 corresponds to file a).
    initial_size : int, optional
        Initial width and height of the tile in pixels, by default 62.
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
        initial_size: int = 62,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.row: int = row
        self.col: int = col
        self.is_light: bool = (row + col) % 2 == 1
        self._tile_size: int = initial_size
        self._font_size: int = max(10, int(initial_size * 0.42))

        # Cached tile state for styling updates
        self._last_piece: Optional[Piece] = None
        self._last_is_selected: bool = False
        self._last_is_legal_dest: bool = False
        self._last_is_capture_dest: bool = False
        self._last_is_king_check: bool = False

        self.setFixedSize(QSize(initial_size, initial_size))
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        font: QFont = self.font()
        font.setPointSize(self._font_size)
        font.setBold(True)
        self.setFont(font)

        self.clicked.connect(self._on_clicked)

    def _on_clicked(
        self,
    ) -> None:
        """Forward the button click signal with square coordinates."""
        self.clicked_square.emit(self.row, self.col)

    def set_tile_size(
        self,
        size: int,
    ) -> None:
        """Update tile dimensions and font size to maintain proportional scaling.

        Parameters
        ----------
        size : int
            Width and height in pixels for the square button.
        """
        if size == self._tile_size:
            return

        self._tile_size = size
        self._font_size = max(10, int(size * 0.42))
        self.setFixedSize(QSize(size, size))

        font: QFont = self.font()
        font.setPointSize(self._font_size)
        font.setBold(True)
        self.setFont(font)

        self.update_tile(
            piece=self._last_piece,
            is_selected=self._last_is_selected,
            is_legal_dest=self._last_is_legal_dest,
            is_capture_dest=self._last_is_capture_dest,
            is_king_check=self._last_is_king_check,
        )

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
        self._last_piece = piece
        self._last_is_selected = is_selected
        self._last_is_legal_dest = is_legal_dest
        self._last_is_capture_dest = is_capture_dest
        self._last_is_king_check = is_king_check

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

        border_radius: int = max(2, int(self._tile_size * 0.06))
        self.setStyleSheet(
            f"QPushButton {{"
            f"  background-color: {bg_color};"
            f"  color: {text_color};"
            f"  font-size: {self._font_size}pt;"
            f"  font-weight: bold;"
            f"  {border_style}"
            f"  border-radius: {border_radius}px;"
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
        self._rank_labels: list[QLabel] = []
        self._file_labels: list[QLabel] = []
        self._current_tile_size: int = 62

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
            lbl_top: QLabel = QLabel(file_char, self)
            lbl_top.setStyleSheet(label_style)
            lbl_top.setFixedHeight(22)
            grid.addWidget(lbl_top, 0, c + 1)
            self._file_labels.append(lbl_top)

            lbl_bottom: QLabel = QLabel(file_char, self)
            lbl_bottom.setStyleSheet(label_style)
            lbl_bottom.setFixedHeight(22)
            grid.addWidget(lbl_bottom, self.config.rows + 1, c + 1)
            self._file_labels.append(lbl_bottom)

        # Rank headers (left and right) and interactive squares
        for r in range(self.config.rows):
            grid_row: int = self.config.rows - r
            rank_str: str = str(r + 1)

            lbl_left: QLabel = QLabel(rank_str, self)
            lbl_left.setStyleSheet(label_style)
            lbl_left.setFixedWidth(22)
            grid.addWidget(lbl_left, grid_row, 0)
            self._rank_labels.append(lbl_left)

            lbl_right: QLabel = QLabel(rank_str, self)
            lbl_right.setStyleSheet(label_style)
            lbl_right.setFixedWidth(22)
            grid.addWidget(lbl_right, grid_row, self.config.cols + 1)
            self._rank_labels.append(lbl_right)

            for c in range(self.config.cols):
                btn: ChessSquareButton = ChessSquareButton(
                    row=r,
                    col=c,
                    initial_size=self._current_tile_size,
                    parent=self,
                )
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

    def resize_to_fit(
        self,
        available_width: int,
        available_height: int,
    ) -> None:
        """Resize board tiles and labels to optimally fit within the available space.

        Parameters
        ----------
        available_width : int
            Available container width in pixels.
        available_height : int
            Available container height in pixels.
        """
        if available_width <= 0 or available_height <= 0:
            return

        label_size: int = 22
        grid_margin: int = 12
        frame_padding: int = 20
        h_spacing: int = (self.config.cols + 1) * 1
        v_spacing: int = (self.config.rows + 1) * 1

        h_overhead: int = (
            grid_margin + frame_padding + (2 * label_size) + h_spacing + 10
        )
        v_overhead: int = (
            grid_margin + frame_padding + (2 * label_size) + v_spacing + 10
        )

        usable_w: int = max(0, available_width - h_overhead)
        usable_h: int = max(0, available_height - v_overhead)

        max_tile_w: int = usable_w // self.config.cols if self.config.cols else 62
        max_tile_h: int = usable_h // self.config.rows if self.config.rows else 62
        tile_size: int = max(28, min(140, min(max_tile_w, max_tile_h)))

        if tile_size == self._current_tile_size:
            return

        self._current_tile_size = tile_size

        for btn in self.square_buttons.values():
            btn.set_tile_size(tile_size)

        label_font_size: int = max(9, min(13, int(tile_size * 0.22)))
        label_style: str = (
            f"color: #b0a89f;"
            f"font-size: {label_font_size}px;"
            f"font-weight: bold;"
            f"qproperty-alignment: AlignCenter;"
        )

        for lbl in self._file_labels:
            lbl.setStyleSheet(label_style)
            lbl.setFixedHeight(label_size)

        for lbl in self._rank_labels:
            lbl.setStyleSheet(label_style)
            lbl.setFixedWidth(label_size)

        self.adjustSize()

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


class ResponsiveBoardContainer(QWidget):
    """Container widget that expands and notifies when its dimensions change.

    Parameters
    ----------
    parent : QWidget or None, optional
        Parent widget, by default None.

    Attributes
    ----------
    resized : Signal
        Signal emitted with (width, height) when the container is resized.
    """

    resized: Signal = Signal(int, int)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

    def resizeEvent(
        self,
        event: QResizeEvent,
    ) -> None:
        """Forward resize dimensions when container size changes.

        Parameters
        ----------
        event : QResizeEvent
            Resize event containing old and new sizes.
        """
        super().resizeEvent(event)
        self.resized.emit(event.size().width(), event.size().height())

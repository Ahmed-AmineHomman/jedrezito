"""Sidebar controls and dashboard helper widgets for Jedrezito GUI.

This module provides selection, configuration, and real-time visualization widgets:
- CapturedPiecesWidget: Visual tray of captured opponent pieces
- PlayerCardWidget: Detailed player status, AI agent badge, army points, and captures
- ArmyHistoryPlotWidget: Interactive line plot of material score history
- TurnStatusWidget: Match progress banner, check alert, and game outcome display
"""

from __future__ import annotations

from collections import Counter
from typing import (
    Any,
    Optional,
)

from PySide6.QtCore import (
    QPointF,
    QRectF,
    Qt,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from jedrezito.gui.dialogs import (
    PIECE_SYMBOLS,
    PlayerKind,
    PlayerSettings,
)
from jedrezito.models import (
    GameStatus,
    Piece,
    PieceType,
    Player,
)


class CapturedPiecesWidget(QWidget):
    """Compact visual tray displaying pieces captured from the opponent.

    Pieces are grouped by type, sorted by descending material value, and shown
    with unicode chess glyphs and count multipliers.
    """

    def __init__(
        self,
        locale: dict[str, Any],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.locale: dict[str, Any] = locale
        self._setup_ui()

    def _setup_ui(
        self,
    ) -> None:
        """Initialize the layout for captured piece badges."""
        self.main_layout: QHBoxLayout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(6)

        self.empty_label: QLabel = QLabel(
            self.locale.get("cards", {}).get("no_captures", "Aucune capture"),
            self,
        )
        self.empty_label.setStyleSheet(
            "color: #736b63; font-style: italic; font-size: 11px;"
        )
        self.main_layout.addWidget(self.empty_label)
        self.main_layout.addStretch()

    def update_pieces(
        self,
        captured_pieces: list[Piece],
        piece_types: dict[str, PieceType],
    ) -> None:
        """Refresh the tray with the given list of captured pieces.

        Parameters
        ----------
        captured_pieces : list of Piece
            Pieces captured by the owning player (hence belonging to opponent).
        piece_types : dict of str to PieceType
            Variant piece definitions for material values.
        """
        # Clear previous items
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not captured_pieces:
            self.empty_label = QLabel(
                self.locale.get("cards", {}).get("no_captures", "Aucune capture"),
                self,
            )
            self.empty_label.setStyleSheet(
                "color: #736b63; font-style: italic; font-size: 11px;"
            )
            self.main_layout.addWidget(self.empty_label)
            self.main_layout.addStretch()
            return

        # Group by piece type and sort by material value descending
        counts: Counter[str] = Counter(p.piece_type for p in captured_pieces)
        opponent_player: Player = captured_pieces[0].player

        def get_value(pt_name: str) -> int:
            pt: PieceType | None = piece_types.get(pt_name)
            return pt.material_value if (pt and pt.material_value is not None) else 0

        sorted_types = sorted(
            counts.keys(),
            key=lambda t: get_value(t),
            reverse=True,
        )

        piece_locale: dict[str, Any] = self.locale.get("pieces", {})

        for pt_name in sorted_types:
            count: int = counts[pt_name]
            symbol: str = PIECE_SYMBOLS.get(
                (pt_name, opponent_player),
                pt_name[:1],
            )
            french_name: str = piece_locale.get(pt_name, pt_name)
            val: int = get_value(pt_name)

            badge: QFrame = QFrame(self)
            badge.setStyleSheet(
                "QFrame {"
                "  background-color: #1a1816;"
                "  border: 1px solid #3c3834;"
                "  border-radius: 4px;"
                "  padding: 1px 4px;"
                "}"
                "QFrame:hover {"
                "  border-color: #5d9337;"
                "}"
            )
            tip_val = f"{val} pt{'s' if val > 1 else ''}"
            badge.setToolTip(f"{french_name} ({tip_val})")

            badge_layout: QHBoxLayout = QHBoxLayout(badge)
            badge_layout.setContentsMargins(3, 1, 3, 1)
            badge_layout.setSpacing(3)

            lbl_sym: QLabel = QLabel(symbol, badge)
            glyph_color = "#f0d9b5" if opponent_player == Player.LIGHT else "#d49b6a"
            lbl_sym.setStyleSheet(
                f"color: {glyph_color}; font-size: 16px; font-weight: bold; background: transparent;"
            )
            badge_layout.addWidget(lbl_sym)

            if count > 1:
                lbl_cnt: QLabel = QLabel(f"×{count}", badge)
                lbl_cnt.setStyleSheet(
                    "color: #b0a89f; font-size: 11px; font-weight: bold; background: transparent;"
                )
                badge_layout.addWidget(lbl_cnt)

            self.main_layout.addWidget(badge)

        self.main_layout.addStretch()


class PlayerCardWidget(QFrame):
    """Dedicated information card for a match participant (Light or Dark).

    Displays player camp badge, controller status (Human vs AI and AI agent name),
    active turn indicator, check alert, current army material score, material
    advantage indicator, and captured opponent pieces tray.
    """

    def __init__(
        self,
        player: Player,
        locale: dict[str, Any],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.player: Player = player
        self.locale: dict[str, Any] = locale
        self._setup_ui()

    def _setup_ui(
        self,
    ) -> None:
        """Construct child labels, badges, and the captures tray."""
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        cards_locale: dict[str, Any] = self.locale.get("cards", {})

        # Top row: Camp badge + active turn / check status
        top_row: QHBoxLayout = QHBoxLayout()
        top_row.setSpacing(6)

        camp_icon = "⚪" if self.player == Player.LIGHT else "⚫"
        default_camp_title = (
            "Blancs" if self.player == Player.LIGHT else "Noirs"
        )
        camp_title = cards_locale.get(
            "light_title" if self.player == Player.LIGHT else "dark_title",
            default_camp_title,
        )

        self.lbl_camp: QLabel = QLabel(f"{camp_icon}  {camp_title}", self)
        camp_color = "#f5f5f5" if self.player == Player.LIGHT else "#d4a373"
        self.lbl_camp.setStyleSheet(
            f"color: {camp_color}; font-size: 14px; font-weight: bold; background: transparent;"
        )
        top_row.addWidget(self.lbl_camp)
        top_row.addStretch()

        self.lbl_turn_badge: QLabel = QLabel("", self)
        self.lbl_turn_badge.setStyleSheet("font-size: 11px; font-weight: bold;")
        top_row.addWidget(self.lbl_turn_badge)

        layout.addLayout(top_row)

        # Middle row: Controller info (Human / AI: name) and Material Score
        mid_row: QHBoxLayout = QHBoxLayout()
        mid_row.setSpacing(8)

        self.lbl_controller: QLabel = QLabel("", self)
        self.lbl_controller.setStyleSheet(
            "background-color: #2b2724;"
            "color: #d6cfc7;"
            "border: 1px solid #443f39;"
            "border-radius: 4px;"
            "padding: 2px 8px;"
            "font-size: 11px;"
        )
        mid_row.addWidget(self.lbl_controller)
        mid_row.addStretch()

        self.lbl_score: QLabel = QLabel("0 pts", self)
        self.lbl_score.setStyleSheet(
            "color: #ffffff; font-size: 15px; font-weight: bold; background: transparent;"
        )
        mid_row.addWidget(self.lbl_score)

        self.lbl_diff: QLabel = QLabel("", self)
        self.lbl_diff.setStyleSheet("font-size: 11px; font-weight: bold;")
        self.lbl_diff.setVisible(False)
        mid_row.addWidget(self.lbl_diff)

        layout.addLayout(mid_row)

        # Bottom section: Captured pieces tray
        cap_header: QLabel = QLabel(
            cards_locale.get("captured_title", "Pièces capturées :"),
            self,
        )
        cap_header.setStyleSheet("color: #a8a096; font-size: 11px; margin-top: 2px;")
        layout.addWidget(cap_header)

        self.captured_tray: CapturedPiecesWidget = CapturedPiecesWidget(
            self.locale,
            self,
        )
        layout.addWidget(self.captured_tray)

    def update_card(
        self,
        settings: PlayerSettings,
        is_current_turn: bool,
        is_in_check: bool,
        army_value: int,
        opponent_army_value: int,
        captured_pieces: list[Piece],
        piece_types: dict[str, PieceType],
    ) -> None:
        """Update the player card with current game state.

        Parameters
        ----------
        settings : PlayerSettings
            Human or AI configuration.
        is_current_turn : bool
            Whether this player has the active turn.
        is_in_check : bool
            Whether this player's King is under threat.
        army_value : int
            Current material score for this player.
        opponent_army_value : int
            Current material score for the opponent.
        captured_pieces : list of Piece
            Opponent pieces captured by this player.
        piece_types : dict of str to PieceType
            Variant piece rules.
        """
        cards_locale: dict[str, Any] = self.locale.get("cards", {})
        ais_locale: dict[str, Any] = self.locale.get("ais", {})

        # Controller badge text and styling
        if settings.kind == PlayerKind.HUMAN:
            self.lbl_controller.setText("👤 Humain")
            self.lbl_controller.setStyleSheet(
                "background-color: #2c2824;"
                "color: #d6cfc7;"
                "border: 1px solid #443f39;"
                "border-radius: 4px;"
                "padding: 2px 7px;"
                "font-size: 11px;"
            )
        else:
            raw_ai = settings.ai_name or "AI"
            ai_disp = ais_locale.get(raw_ai, raw_ai.capitalize())
            self.lbl_controller.setText(f"🤖 IA : {ai_disp}")
            self.lbl_controller.setStyleSheet(
                "background-color: #1a2e19;"
                "color: #8fe07d;"
                "border: 1px solid #385e26;"
                "border-radius: 4px;"
                "padding: 2px 7px;"
                "font-size: 11px;"
                "font-weight: bold;"
            )

        # Turn and Check state
        if is_in_check:
            self.lbl_turn_badge.setText(
                cards_locale.get("check_badge", "⚠️ ÉCHEC AU ROI")
            )
            self.lbl_turn_badge.setStyleSheet(
                "background-color: #4a1515;"
                "color: #ff8a80;"
                "border: 1px solid #d32f2f;"
                "border-radius: 4px;"
                "padding: 2px 6px;"
                "font-size: 11px;"
                "font-weight: bold;"
            )
            self.setStyleSheet(
                "PlayerCardWidget {"
                "  background-color: #2b1d1d;"
                "  border: 2px solid #e53935;"
                "  border-radius: 8px;"
                "}"
            )
        elif is_current_turn:
            self.lbl_turn_badge.setText(
                cards_locale.get("turn_active", "🟢 AU TRAIT")
            )
            self.lbl_turn_badge.setStyleSheet(
                "background-color: #1e3a1b;"
                "color: #82e865;"
                "border: 1px solid #4a752c;"
                "border-radius: 4px;"
                "padding: 2px 6px;"
                "font-size: 11px;"
                "font-weight: bold;"
            )
            self.setStyleSheet(
                "PlayerCardWidget {"
                "  background-color: #282522;"
                "  border: 2px solid #5d9337;"
                "  border-radius: 8px;"
                "}"
            )
        else:
            self.lbl_turn_badge.setText(
                cards_locale.get("turn_waiting", "En attente")
            )
            self.lbl_turn_badge.setStyleSheet(
                "color: #7a7269; background: transparent; font-size: 11px; padding: 2px 4px;"
            )
            self.setStyleSheet(
                "PlayerCardWidget {"
                "  background-color: #201e1c;"
                "  border: 1px solid #3c3834;"
                "  border-radius: 8px;"
                "}"
            )

        # Scores
        self.lbl_score.setText(f"{army_value} pts")
        diff = army_value - opponent_army_value
        if diff > 0:
            self.lbl_diff.setText(f"+{diff}")
            self.lbl_diff.setStyleSheet(
                "background-color: #1e3a1b;"
                "color: #82e865;"
                "border: 1px solid #3d6e2e;"
                "border-radius: 4px;"
                "padding: 1px 5px;"
                "font-size: 11px;"
                "font-weight: bold;"
            )
            self.lbl_diff.setVisible(True)
        elif diff < 0:
            self.lbl_diff.setText(f"{diff}")
            self.lbl_diff.setStyleSheet(
                "background-color: #2d2724;"
                "color: #a8a096;"
                "border: 1px solid #443f39;"
                "border-radius: 4px;"
                "padding: 1px 5px;"
                "font-size: 11px;"
                "font-weight: bold;"
            )
            self.lbl_diff.setVisible(True)
        else:
            self.lbl_diff.setVisible(False)

        # Captures tray
        self.captured_tray.update_pieces(captured_pieces, piece_types)


class ArmyHistoryPlotWidget(QFrame):
    """Interactive line plot visualizing the history of army material points for both players.

    Uses QPainter with antialiasing for zero-latency, responsive, theme-consistent
    rendering on desktop displays.
    """

    def __init__(
        self,
        locale: dict[str, Any],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.locale: dict[str, Any] = locale
        self._history: list[tuple[int, int]] = []
        self._hover_idx: int | None = None
        self.setMouseTracking(True)
        self.setMinimumHeight(175)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setStyleSheet(
            "ArmyHistoryPlotWidget {"
            "  background-color: #191816;"
            "  border: 1px solid #383430;"
            "  border-radius: 8px;"
            "}"
        )

    def set_history(
        self,
        history: list[tuple[int, int]],
    ) -> None:
        """Update the plot data with army points history.

        Parameters
        ----------
        history : list of tuple of int
            Chronological list of (light_score, dark_score) recorded at each turn/ply.
        """
        self._history = list(history)
        self.update()

    def mouseMoveEvent(
        self,
        event: QMouseEvent,
    ) -> None:
        """Track mouse movement to display hover guidelines and score tooltips."""
        if len(self._history) <= 1:
            self._hover_idx = None
            self.update()
            return

        left_m = 36.0
        right_m = 16.0
        pw = max(1.0, float(self.rect().width()) - left_m - right_m)
        x_max = float(len(self._history) - 1)

        mouse_x = event.position().x()
        if left_m <= mouse_x <= self.rect().width() - right_m:
            rel = (mouse_x - left_m) / pw
            idx = int(round(rel * x_max))
            idx = max(0, min(len(self._history) - 1, idx))
            if idx != self._hover_idx:
                self._hover_idx = idx
                self.update()
        else:
            if self._hover_idx is not None:
                self._hover_idx = None
                self.update()

    def leaveEvent(
        self,
        event: Any,
    ) -> None:
        """Clear hover guidelines when mouse leaves widget."""
        if self._hover_idx is not None:
            self._hover_idx = None
            self.update()

    def paintEvent(
        self,
        event: Any,
    ) -> None:
        """Render the axes, grid lines, series curves, markers, and legend."""
        painter: QPainter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        w = rect.width()
        h = rect.height()

        plot_locale: dict[str, Any] = self.locale.get("plot", {})

        # 1. Legend at top
        cur_l = self._history[-1][0] if self._history else 0
        cur_d = self._history[-1][1] if self._history else 0

        title_font = QFont()
        title_font.setPointSize(9)
        title_font.setBold(True)
        painter.setFont(title_font)

        # Plot title
        painter.setPen(QColor("#d6cfc7"))
        painter.drawText(
            12,
            20,
            plot_locale.get("group_title", "Évolution des armées"),
        )

        legend_font = QFont()
        legend_font.setPointSize(8)
        painter.setFont(legend_font)

        # Light legend: ● Blancs: X pts
        painter.setPen(QColor("#f0d9b5"))
        painter.setBrush(QBrush(QColor("#f0d9b5")))
        painter.drawEllipse(QPointF(w - 180, 16), 3.5, 3.5)
        painter.drawText(w - 172, 20, f"Blancs : {cur_l}")

        # Dark legend: ■ Noirs: Y pts
        painter.setPen(QColor("#c4915f"))
        painter.setBrush(QBrush(QColor("#c4915f")))
        painter.drawRect(QRectF(w - 85, 12.5, 7, 7))
        painter.drawText(w - 72, 20, f"Noirs : {cur_d}")

        # Plot geometry
        left_m = 36.0
        right_m = 16.0
        top_m = 36.0
        bottom_m = 24.0

        pw = float(w) - left_m - right_m
        ph = float(h) - top_m - bottom_m

        if pw <= 10 or ph <= 10:
            return

        if not self._history:
            painter.setPen(QColor("#736b63"))
            painter.drawText(
                QRectF(0, top_m, w, ph),
                Qt.AlignmentFlag.AlignCenter,
                plot_locale.get("empty_hint", "En attente du premier coup..."),
            )
            return

        # Y scale calculation
        all_vals = [v for pt in self._history for v in pt]
        min_v = min(all_vals)
        max_v = max(all_vals)
        if max_v - min_v < 6:
            y_min = max(0, min_v - 3)
            y_max = max_v + 3
        else:
            y_min = max(0, min_v - 2)
            y_max = max_v + 2
        y_range = max(1.0, float(y_max - y_min))

        # Horizontal grid lines
        grid_pen = QPen(QColor(55, 51, 47), 1, Qt.PenStyle.DashLine)
        label_pen = QColor("#80776d")
        tick_font = QFont()
        tick_font.setPointSize(7)
        painter.setFont(tick_font)

        num_grid_lines = 4
        for g in range(num_grid_lines):
            frac = g / float(num_grid_lines - 1)
            val = int(round(y_min + frac * y_range))
            y_pos = top_m + ph - (frac * ph)

            painter.setPen(grid_pen)
            painter.drawLine(QPointF(left_m, y_pos), QPointF(left_m + pw, y_pos))

            painter.setPen(label_pen)
            painter.drawText(
                QRectF(4, y_pos - 8, left_m - 8, 16),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                str(val),
            )

        # Coordinate mappings
        n_pts = len(self._history)
        x_max = max(1.0, float(n_pts - 1))

        def to_x(idx: int) -> float:
            return left_m + (float(idx) / x_max) * pw

        def to_y(val: int) -> float:
            return top_m + ph - ((float(val) - float(y_min)) / y_range) * ph

        # X axis ticks and labels
        step = 1 if n_pts <= 10 else 5 if n_pts <= 30 else 10 if n_pts <= 60 else 20
        painter.setPen(label_pen)
        for i in range(0, n_pts, step):
            px = to_x(i)
            painter.drawText(
                QRectF(px - 15, top_m + ph + 4, 30, 16),
                Qt.AlignmentFlag.AlignCenter,
                str(i),
            )
        # Always label last point if not already labeled
        if (n_pts - 1) % step != 0:
            px = to_x(n_pts - 1)
            painter.drawText(
                QRectF(px - 15, top_m + ph + 4, 30, 16),
                Qt.AlignmentFlag.AlignCenter,
                str(n_pts - 1),
            )

        # 2. Draw Light curve (Ivory `#f0d9b5`, Solid)
        light_path = QPainterPath()
        light_path.moveTo(to_x(0), to_y(self._history[0][0]))
        for i in range(1, n_pts):
            light_path.lineTo(to_x(i), to_y(self._history[i][0]))

        light_pen = QPen(
            QColor("#f0d9b5"),
            2.4,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
        painter.setPen(light_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(light_path)

        # 3. Draw Dark curve (Wood `#c4915f`, Dashed)
        dark_path = QPainterPath()
        dark_path.moveTo(to_x(0), to_y(self._history[0][1]))
        for i in range(1, n_pts):
            dark_path.lineTo(to_x(i), to_y(self._history[i][1]))

        dark_pen = QPen(
            QColor("#c4915f"),
            2.2,
            Qt.PenStyle.DashLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
        painter.setPen(dark_pen)
        painter.drawPath(dark_path)

        # 4. Markers
        for i in range(n_pts):
            lx, ly = to_x(i), to_y(self._history[i][0])
            dx, dy = to_x(i), to_y(self._history[i][1])

            # Light marker: Circle
            is_latest = i == n_pts - 1
            l_radius = 4.5 if is_latest else 3.0
            painter.setPen(QPen(QColor("#242220"), 1.2))
            painter.setBrush(QBrush(QColor("#f0d9b5")))
            painter.drawEllipse(QPointF(lx, ly), l_radius, l_radius)

            # Dark marker: Square
            d_size = 7.0 if is_latest else 5.0
            painter.setPen(QPen(QColor("#242220"), 1.2))
            painter.setBrush(QBrush(QColor("#c4915f")))
            painter.drawRect(
                QRectF(dx - d_size / 2, dy - d_size / 2, d_size, d_size)
            )

        # 5. Hover indicator
        if self._hover_idx is not None and 0 <= self._hover_idx < n_pts:
            hx = to_x(self._hover_idx)
            hl, hd = self._history[self._hover_idx]

            guide_pen = QPen(QColor(255, 255, 255, 90), 1, Qt.PenStyle.DotLine)
            painter.setPen(guide_pen)
            painter.drawLine(QPointF(hx, top_m), QPointF(hx, top_m + ph))

            # Tooltip badge
            tip_txt = f"Coup {self._hover_idx} : ⚪ {hl} | ⚫ {hd}"
            tip_font = QFont()
            tip_font.setPointSize(8)
            tip_font.setBold(True)
            painter.setFont(tip_font)

            badge_w = 140.0
            badge_h = 22.0
            badge_x = min(hx + 8, w - right_m - badge_w)
            if badge_x < left_m:
                badge_x = left_m
            badge_y = top_m + 6

            painter.setPen(QPen(QColor("#5d9337"), 1))
            painter.setBrush(QBrush(QColor(36, 32, 28, 230)))
            painter.drawRoundedRect(
                QRectF(badge_x, badge_y, badge_w, badge_h),
                4.0,
                4.0,
            )

            painter.setPen(QColor("#f0eae1"))
            painter.drawText(
                QRectF(badge_x, badge_y, badge_w, badge_h),
                Qt.AlignmentFlag.AlignCenter,
                tip_txt,
            )


class TurnStatusWidget(QFrame):
    """Match status banner displaying game progression, check alerts, and outcomes.

    Focuses strictly on match state, move/ply progression, and selection feedback.
    Player-specific details (Human vs AI, controller identity, turn badges) are
    displayed exclusively in the dedicated PlayerCardWidgets to prevent repetition.
    """

    def __init__(
        self,
        locale: dict[str, Any],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.locale: dict[str, Any] = locale
        self._setup_ui()

    def _setup_ui(
        self,
    ) -> None:
        """Construct status banner components."""
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        # Primary row: Status / outcome title + move counter
        header_row: QHBoxLayout = QHBoxLayout()
        header_row.setSpacing(8)

        self.lbl_main_status: QLabel = QLabel("Partie en cours", self)
        self.lbl_main_status.setStyleSheet(
            "color: #ffffff; font-size: 14px; font-weight: bold; background: transparent;"
        )
        header_row.addWidget(self.lbl_main_status)
        header_row.addStretch()

        self.lbl_move_counter: QLabel = QLabel("Coup 1", self)
        self.lbl_move_counter.setStyleSheet(
            "color: #8fe07d; font-size: 11px; font-weight: bold; background: transparent;"
        )
        header_row.addWidget(self.lbl_move_counter)

        layout.addLayout(header_row)

        # Selection hint label (shown when a square is selected)
        self.lbl_selection: QLabel = QLabel("", self)
        self.lbl_selection.setStyleSheet(
            "color: #f0d9b5; font-size: 11px; font-style: italic; background: transparent;"
        )
        self.lbl_selection.setVisible(False)
        layout.addWidget(self.lbl_selection)

    def update_status(
        self,
        current_player: Player,
        player_settings: Optional[PlayerSettings] = None,
        is_check: bool = False,
        status: GameStatus = GameStatus.ONGOING,
        winner: Player | None = None,
        turns_played: Optional[dict[Player, int]] = None,
        turn_limit: int | None = None,
        selected_coords: tuple[int, int] | None = None,
        selected_piece: Piece | None = None,
        board_rows: int = 8,
    ) -> None:
        """Refresh status banner state based on current game engine progress.

        Parameters
        ----------
        current_player : Player
            Active player.
        player_settings : PlayerSettings or None, optional
            Controller settings for current player (kept for API compatibility).
        is_check : bool, optional
            Whether active player's King is in check.
        status : GameStatus, optional
            Game lifecycle status.
        winner : Player or None, optional
            Match winner if concluded.
        turns_played : dict of Player to int or None, optional
            Turns taken by each player.
        turn_limit : int or None, optional
            Turn limit if variant imposes one.
        selected_coords : tuple of int or None, optional
            Currently selected board coordinates.
        selected_piece : Piece or None, optional
            Piece on selected square.
        board_rows : int, optional
            Number of rows for chess coordinate formatting.
        """
        panel_locale: dict[str, Any] = self.locale.get("status_panel", {})
        players_locale: dict[str, Any] = self.locale.get("players", {})

        if turns_played is None:
            turns_played = {Player.LIGHT: 0, Player.DARK: 0}

        total_plies = turns_played[Player.LIGHT] + turns_played[Player.DARK]
        current_turn = max(turns_played[Player.LIGHT], turns_played[Player.DARK]) + (
            1 if status == GameStatus.ONGOING else 0
        )

        # Move / Turn counter display
        if status == GameStatus.ONGOING:
            if turn_limit is not None:
                self.lbl_move_counter.setText(f"Tour {current_turn} / {turn_limit}")
            else:
                self.lbl_move_counter.setText(f"Coup {total_plies + 1} — Tour {current_turn}")
        else:
            self.lbl_move_counter.setText("Terminée")

        # Game outcome or ongoing turn state
        if status == GameStatus.ONGOING:
            if is_check:
                self.lbl_main_status.setText(
                    panel_locale.get("check_alert", "⚠️ ÉCHEC AU ROI !")
                )
                self.setStyleSheet(
                    "TurnStatusWidget {"
                    "  background-color: #3b1616;"
                    "  border: 2px solid #e53935;"
                    "  border-radius: 8px;"
                    "}"
                )
            else:
                self.lbl_main_status.setText(
                    panel_locale.get("ongoing", "Partie en cours")
                )
                self.setStyleSheet(
                    "TurnStatusWidget {"
                    "  background-color: #242220;"
                    "  border: 1px solid #3c3834;"
                    "  border-radius: 8px;"
                    "}"
                )

        elif status == GameStatus.CHECKMATE:
            win_name = (
                players_locale.get("light", "Blancs")
                if winner == Player.LIGHT
                else players_locale.get("dark", "Noirs")
            )
            self.lbl_main_status.setText(f"🏆 Échec et mat ! Victoire des {win_name}")
            self.setStyleSheet(
                "TurnStatusWidget {"
                "  background-color: #1e381b;"
                "  border: 2px solid #5d9337;"
                "  border-radius: 8px;"
                "}"
            )
        elif status == GameStatus.STALEMATE:
            self.lbl_main_status.setText("🤝 Match nul par pat !")
            self.setStyleSheet(
                "TurnStatusWidget {"
                "  background-color: #2b251d;"
                "  border: 2px solid #d49b4b;"
                "  border-radius: 8px;"
                "}"
            )
        elif status == GameStatus.TURN_EXHAUSTED:
            if winner is not None:
                win_name = (
                    players_locale.get("light", "Blancs")
                    if winner == Player.LIGHT
                    else players_locale.get("dark", "Noirs")
                )
                self.lbl_main_status.setText(
                    f"⌛ Limite de tours ! Victoire des {win_name}"
                )
                self.setStyleSheet(
                    "TurnStatusWidget {"
                    "  background-color: #1e381b;"
                    "  border: 2px solid #5d9337;"
                    "  border-radius: 8px;"
                    "}"
                )
            else:
                self.lbl_main_status.setText("⌛ Limite de tours ! Match nul")
                self.setStyleSheet(
                    "TurnStatusWidget {"
                    "  background-color: #2b251d;"
                    "  border: 2px solid #d49b4b;"
                    "  border-radius: 8px;"
                    "}"
                )

        # Selected square feedback
        if selected_coords is not None and selected_piece is not None:
            r, c = selected_coords
            col_letter = chr(ord("a") + c)
            row_number = board_rows - r
            piece_locale: dict[str, Any] = self.locale.get("pieces", {})
            p_name = piece_locale.get(
                selected_piece.piece_type,
                selected_piece.piece_type,
            )
            sym = PIECE_SYMBOLS.get(
                (selected_piece.piece_type, selected_piece.player),
                "",
            )
            self.lbl_selection.setText(
                f"Sélection : {sym} {p_name} ({col_letter}{row_number})"
            )
            self.lbl_selection.setVisible(True)
        else:
            self.lbl_selection.setVisible(False)

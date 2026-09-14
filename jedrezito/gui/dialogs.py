"""Dialog components and player controller models for Jedrezito GUI.

This module provides setup dialogs, pawn promotion prompts, and player configuration
data structures used across the GUI application.
"""

from __future__ import annotations

from dataclasses import (
    dataclass,
)
from enum import (
    Enum,
)
from typing import (
    Any,
    Optional,
)

from PySide6.QtCore import (
    Qt,
)
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from jedrezito.ai import (
    list_available_ais,
)
from jedrezito.config import (
    get_variant_metadata,
    list_available_variants,
)
from jedrezito.models import (
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


class PlayerKind(str, Enum):
    """Kind of player controller.

    Attributes
    ----------
    HUMAN : str
        Human player interacting with the GUI.
    AI : str
        Autonomous AI agent choosing moves programmatically.
    """

    HUMAN = "human"
    AI = "ai"


@dataclass
class PlayerSettings:
    """Settings defining a player's controller.

    Parameters
    ----------
    kind : PlayerKind
        Controller kind (Human or AI).
    ai_name : str or None, optional
        Registered AI identifier if kind is AI, by default None.

    Attributes
    ----------
    kind : PlayerKind
        Controller kind.
    ai_name : str or None
        AI agent identifier.
    """

    kind: PlayerKind
    ai_name: Optional[str] = None


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


class GameSetupDialog(QDialog):
    """Modal dialog allowing users to configure game variant and players before starting.

    Parameters
    ----------
    current_variant : str
        Currently active variant name.
    light_settings : PlayerSettings
        Current player settings for Light.
    dark_settings : PlayerSettings
        Current player settings for Dark.
    locale : dict of str to Any
        Localized UI strings dictionary.
    parent : QWidget or None, optional
        Parent widget, by default None.

    Attributes
    ----------
    selected_variant : str
        The chosen variant identifier upon dialog confirmation.
    selected_light_settings : PlayerSettings
        The chosen player settings for Light upon confirmation.
    selected_dark_settings : PlayerSettings
        The chosen player settings for Dark upon confirmation.
    locale : dict of str to Any
        Active localization strings dictionary.
    """

    def __init__(
        self,
        current_variant: str,
        light_settings: PlayerSettings,
        dark_settings: PlayerSettings,
        locale: dict[str, Any],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.locale: dict[str, Any] = locale
        self.selected_variant: str = current_variant
        self.selected_light_settings: PlayerSettings = light_settings
        self.selected_dark_settings: PlayerSettings = dark_settings

        setup_locale: dict[str, Any] = (
            self.locale.get("dialogs", {}).get("setup", {})
        )
        self.setWindowTitle(
            setup_locale.get("window_title", "Configuration de la partie")
        )
        self.setModal(True)
        self.setMinimumWidth(440)
        self.setStyleSheet(
            "QDialog {"
            "  background-color: #242220;"
            "  border: 2px solid #3c3834;"
            "  border-radius: 8px;"
            "}"
            "QLabel {"
            "  color: #f0eae1;"
            "}"
            "QGroupBox {"
            "  color: #d6cfc7;"
            "  font-weight: bold;"
            "  border: 1px solid #3c3834;"
            "  border-radius: 6px;"
            "  margin-top: 10px;"
            "  padding-top: 14px;"
            "}"
            "QGroupBox::title {"
            "  subcontrol-origin: margin;"
            "  left: 10px;"
            "  padding: 0 4px;"
            "}"
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
            "QComboBox QAbstractItemView {"
            "  background-color: #242220;"
            "  color: #f0eae1;"
            "  selection-background-color: #4a752c;"
            "  selection-color: #ffffff;"
            "  border: 1px solid #4a443e;"
            "  outline: none;"
            "}"
        )

        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Title
        title_label: QLabel = QLabel(
            setup_locale.get("dialog_title", "Configurer une nouvelle partie"),
            self,
        )
        title_label.setStyleSheet(
            "color: #f5f5f5;"
            "font-size: 16px;"
            "font-weight: bold;"
            "qproperty-alignment: AlignCenter;"
        )
        layout.addWidget(title_label)

        # 1. Variant selection group
        variant_group: QGroupBox = QGroupBox(
            setup_locale.get("variant_group", "Variante de jeu"),
            self,
        )
        var_layout: QVBoxLayout = QVBoxLayout(variant_group)
        var_layout.setSpacing(8)

        self.combo_variant: QComboBox = QComboBox(self)
        variants: list[str] = list_available_variants()
        for v in variants:
            try:
                meta: dict[str, Any] = get_variant_metadata(v)
                disp_name: str = meta.get("name", v)
            except Exception:
                disp_name = v
            self.combo_variant.addItem(f"{disp_name} ({v})", v)

        # Pre-select current variant
        for i in range(self.combo_variant.count()):
            if self.combo_variant.itemData(i) == current_variant:
                self.combo_variant.setCurrentIndex(i)
                break

        var_layout.addWidget(self.combo_variant)

        self.lbl_variant_info: QLabel = QLabel(self)
        self.lbl_variant_info.setStyleSheet("color: #b0a89f; font-size: 12px;")
        var_layout.addWidget(self.lbl_variant_info)
        self.combo_variant.currentIndexChanged.connect(
            self._update_variant_preview
        )
        self._update_variant_preview()
        layout.addWidget(variant_group)

        # 2. Players selection group
        players_group: QGroupBox = QGroupBox(
            setup_locale.get("players_group", "Configuration des joueurs"),
            self,
        )
        players_layout: QVBoxLayout = QVBoxLayout(players_group)
        players_layout.setSpacing(12)

        players_locale: dict[str, Any] = self.locale.get("players", {})
        ais_locale: dict[str, Any] = self.locale.get("ais", {})
        available_ais: list[str] = list_available_ais()

        self.combo_light_type, self.combo_light_ai, row_light = (
            self._create_player_row(
                label_text=setup_locale.get(
                    "light_player_label",
                    "Joueur Blancs :",
                ),
                default_settings=light_settings,
                players_locale=players_locale,
                ais_locale=ais_locale,
                available_ais=available_ais,
            )
        )
        players_layout.addWidget(row_light)

        self.combo_dark_type, self.combo_dark_ai, row_dark = (
            self._create_player_row(
                label_text=setup_locale.get(
                    "dark_player_label",
                    "Joueur Noirs :",
                ),
                default_settings=dark_settings,
                players_locale=players_locale,
                ais_locale=ais_locale,
                available_ais=available_ais,
            )
        )
        players_layout.addWidget(row_dark)
        layout.addWidget(players_group)

        # 3. Buttons layout
        btn_layout: QHBoxLayout = QHBoxLayout()
        btn_layout.setSpacing(12)

        btn_cancel: QPushButton = QPushButton(
            setup_locale.get("btn_cancel", "Annuler"),
            self,
        )
        btn_cancel.setStyleSheet(
            "QPushButton {"
            "  background-color: #332f2b;"
            "  color: #f0eae1;"
            "  font-size: 14px;"
            "  padding: 8px 16px;"
            "  border: 1px solid #4a443e;"
            "  border-radius: 6px;"
            "}"
            "QPushButton:hover {"
            "  background-color: #4a443e;"
            "}"
        )
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_start: QPushButton = QPushButton(
            setup_locale.get("btn_start", "Démarrer la partie"),
            self,
        )
        btn_start.setStyleSheet(
            "QPushButton {"
            "  background-color: #4a752c;"
            "  color: #ffffff;"
            "  font-size: 14px;"
            "  font-weight: bold;"
            "  padding: 8px 16px;"
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
        btn_start.clicked.connect(self._on_start_clicked)
        btn_layout.addWidget(btn_start)

        layout.addLayout(btn_layout)

    def _create_player_row(
        self,
        label_text: str,
        default_settings: PlayerSettings,
        players_locale: dict[str, Any],
        ais_locale: dict[str, Any],
        available_ais: list[str],
    ) -> tuple[QComboBox, QComboBox, QWidget]:
        """Create a row containing player type and AI model selectors.

        Parameters
        ----------
        label_text : str
            Display label identifying the player color.
        default_settings : PlayerSettings
            Initial player settings to populate.
        players_locale : dict of str to Any
            Localized player labels.
        ais_locale : dict of str to Any
            Localized AI names.
        available_ais : list of str
            Identifiers of registered AI agents.

        Returns
        -------
        tuple of QComboBox, QComboBox, QWidget
            Tuple of (type combo, AI combo, container row widget).
        """
        row_widget: QWidget = QWidget(self)
        row_layout: QHBoxLayout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(10)

        lbl: QLabel = QLabel(label_text, row_widget)
        lbl.setFixedWidth(115)
        lbl.setStyleSheet("font-weight: bold;")
        row_layout.addWidget(lbl)

        combo_type: QComboBox = QComboBox(row_widget)
        combo_type.addItem(
            players_locale.get("human", "Humain"),
            PlayerKind.HUMAN,
        )
        combo_type.addItem(
            players_locale.get("ai", "IA"),
            PlayerKind.AI,
        )
        row_layout.addWidget(combo_type)

        combo_ai: QComboBox = QComboBox(row_widget)
        for ai_id in available_ais:
            ai_display: str = ais_locale.get(ai_id, ai_id.capitalize())
            combo_ai.addItem(ai_display, ai_id)
        row_layout.addWidget(combo_ai)

        if default_settings.kind == PlayerKind.AI:
            combo_type.setCurrentIndex(1)
            if default_settings.ai_name is not None:
                for i in range(combo_ai.count()):
                    if combo_ai.itemData(i) == default_settings.ai_name:
                        combo_ai.setCurrentIndex(i)
                        break
            combo_ai.setVisible(True)
        else:
            combo_type.setCurrentIndex(0)
            combo_ai.setVisible(False)

        combo_type.currentIndexChanged.connect(
            lambda idx, c_ai=combo_ai, c_type=combo_type: c_ai.setVisible(
                c_type.itemData(idx) == PlayerKind.AI
            )
        )

        return combo_type, combo_ai, row_widget

    def _update_variant_preview(
        self,
    ) -> None:
        """Update metadata preview for the chosen variant."""
        variant_id: Optional[str] = self.combo_variant.currentData()
        if variant_id is None:
            self.lbl_variant_info.setText("")
            return

        selector_locale: dict[str, Any] = self.locale.get("selector", {})
        try:
            meta: dict[str, Any] = get_variant_metadata(variant_id)
            dim_template: str = selector_locale.get(
                "dimensions_label",
                "Plateau : {rows} × {cols}",
            )
            dims: str = dim_template.format(
                rows=meta["rows"],
                cols=meta["cols"],
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
            turns: str = turn_template.format(limit=limit_str)
            self.lbl_variant_info.setText(f"{dims}  |  {turns}")
        except Exception:
            self.lbl_variant_info.setText("")

    def _on_start_clicked(
        self,
    ) -> None:
        """Store configured parameters and accept the dialog."""
        var_id: Optional[str] = self.combo_variant.currentData()
        if var_id:
            self.selected_variant = var_id

        light_kind: PlayerKind = self.combo_light_type.currentData()
        light_ai: Optional[str] = (
            self.combo_light_ai.currentData()
            if light_kind == PlayerKind.AI
            else None
        )
        self.selected_light_settings = PlayerSettings(
            kind=light_kind,
            ai_name=light_ai,
        )

        dark_kind: PlayerKind = self.combo_dark_type.currentData()
        dark_ai: Optional[str] = (
            self.combo_dark_ai.currentData()
            if dark_kind == PlayerKind.AI
            else None
        )
        self.selected_dark_settings = PlayerSettings(
            kind=dark_kind,
            ai_name=dark_ai,
        )

        self.accept()

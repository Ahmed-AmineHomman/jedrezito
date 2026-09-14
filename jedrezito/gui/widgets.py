"""Sidebar controls and helper widgets for Jedrezito GUI.

This module provides selection and configuration widgets such as the
variant picker sidebar widget.
"""

from __future__ import annotations

from typing import (
    Any,
    Optional,
)

from PySide6.QtCore import (
    Signal,
)
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGroupBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from jedrezito.config import (
    get_variant_metadata,
    list_available_variants,
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

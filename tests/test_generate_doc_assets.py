"""Unit tests for the documentation asset generation script."""

from __future__ import annotations

from pathlib import Path
import sys
import pytest

_REPO_ROOT: Path = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from jedrezito.config import (
    load_variant_config,
)
from jedrezito.engine import (
    GameEngine,
)
from jedrezito.models import (
    GameConfig,
)
from scripts.generate_doc_assets import (
    generate_all_variant_assets,
    generate_variant_asset,
    render_board_to_svg,
)


@pytest.fixture
def chess_engine() -> GameEngine:
    """Create a GameEngine initialized with classical chess variant.

    Returns
    -------
    GameEngine
        GameEngine for classical chess.
    """
    config: GameConfig = load_variant_config("chess")
    return GameEngine(config)


def test_render_board_to_svg_starts_with_svg_tag(
    chess_engine: GameEngine,
) -> None:
    """Validate render_board_to_svg output starts with opening svg tag."""
    svg_output: str = render_board_to_svg(chess_engine)
    assert svg_output.startswith("<svg xmlns=")


def test_render_board_to_svg_ends_with_closing_tag(
    chess_engine: GameEngine,
) -> None:
    """Validate render_board_to_svg output ends with closing svg tag."""
    svg_output: str = render_board_to_svg(chess_engine)
    assert svg_output.strip().endswith("</svg>")


def test_render_board_to_svg_contains_king_symbol(
    chess_engine: GameEngine,
) -> None:
    """Validate render_board_to_svg contains chess king piece symbol."""
    svg_output: str = render_board_to_svg(chess_engine)
    assert "♔" in svg_output


def test_generate_variant_asset_creates_file(
    tmp_path: Path,
) -> None:
    """Validate generate_variant_asset writes an SVG file to the target path."""
    output_file: Path = generate_variant_asset(
        variant_name="chess",
        output_dir=tmp_path,
    )
    assert output_file.is_file()


def test_generate_all_variant_assets_count(
    tmp_path: Path,
) -> None:
    """Validate generate_all_variant_assets produces assets for all variants."""
    paths: list[Path] = generate_all_variant_assets(output_dir=tmp_path)
    assert len(paths) >= 2

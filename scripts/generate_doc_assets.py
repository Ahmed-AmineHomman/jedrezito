"""Helper script generating visual documentation assets for Jedrezito variants.

This script scans all available JEG variants in the repository, constructs their
initial game board states, and renders them into vector SVG images saved in the
documentation assets directory.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import (
    Optional,
)

# Ensure jedrezito package is importable when running script directly
_REPO_ROOT: Path = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from jedrezito.config import (
    list_available_variants,
    load_variant_config,
)
from jedrezito.engine import (
    GameEngine,
)
from jedrezito.models import (
    GameConfig,
    Piece,
    Player,
)

DEFAULT_OUTPUT_DIR: Path = _REPO_ROOT / "docs" / "assets" / "games"
DEFAULT_TILE_SIZE: int = 60
DEFAULT_MARGIN: int = 30

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


def render_board_to_svg(
    engine: GameEngine,
    tile_size: int = DEFAULT_TILE_SIZE,
    margin: int = DEFAULT_MARGIN,
) -> str:
    """Render the current engine board state to an SVG XML string.

    Parameters
    ----------
    engine : GameEngine
        The active game engine instance containing board state and dimensions.
    tile_size : int, optional
        Width and height of each chessboard tile in pixels, by default 60.
    margin : int, optional
        Margin in pixels around the board for rank and file labels, by default 30.

    Returns
    -------
    str
        Complete SVG markup representing the chessboard.
    """
    rows: int = engine.config.rows
    cols: int = engine.config.cols

    board_width: int = cols * tile_size
    board_height: int = rows * tile_size
    total_width: int = board_width + 2 * margin
    total_height: int = board_height + 2 * margin

    svg_parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {total_width} {total_height}" '
        f'width="{total_width}" height="{total_height}">',
        f'  <!-- Outer board container -->',
        f'  <rect x="0" y="0" width="{total_width}" height="{total_height}" '
        f'fill="#2b2724" rx="8" ry="8"/>',
        f'  <!-- Chessboard inner frame -->',
        f'  <rect x="{margin}" y="{margin}" width="{board_width}" height="{board_height}" '
        f'fill="#1a1715" stroke="#1a1715" stroke-width="2"/>',
    ]

    # Render squares
    for r in range(rows):
        # r = 0 is rank 1 (Light side at the bottom), r = rows - 1 is rank N (Dark side at top)
        y_pos: int = margin + (rows - 1 - r) * tile_size
        for c in range(cols):
            x_pos: int = margin + c * tile_size
            is_light: bool = (r + c) % 2 == 1
            square_color: str = "#f0d9b5" if is_light else "#b58863"
            svg_parts.append(
                f'  <rect x="{x_pos}" y="{y_pos}" width="{tile_size}" height="{tile_size}" '
                f'fill="{square_color}"/>'
            )

    # Render coordinate labels
    label_style: str = (
        'fill="#b0a89f" font-family="-apple-system, BlinkMacSystemFont, '
        '\'Segoe UI\', Roboto, Helvetica, Arial, sans-serif" '
        'font-size="13" font-weight="bold" text-anchor="middle" dominant-baseline="central"'
    )

    # File labels (columns: a, b, c, ...) on top and bottom
    for c in range(cols):
        col_letter: str = chr(ord("a") + c)
        x_center: float = margin + c * tile_size + tile_size / 2.0
        y_top: float = margin / 2.0
        y_bottom: float = total_height - margin / 2.0
        svg_parts.append(
            f'  <text x="{x_center}" y="{y_top}" {label_style}>{col_letter}</text>'
        )
        svg_parts.append(
            f'  <text x="{x_center}" y="{y_bottom}" {label_style}>{col_letter}</text>'
        )

    # Rank labels (rows: 1, 2, 3, ...) on left and right
    for r in range(rows):
        rank_num: str = str(r + 1)
        y_center: float = margin + (rows - 1 - r) * tile_size + tile_size / 2.0
        x_left: float = margin / 2.0
        x_right: float = total_width - margin / 2.0
        svg_parts.append(
            f'  <text x="{x_left}" y="{y_center}" {label_style}>{rank_num}</text>'
        )
        svg_parts.append(
            f'  <text x="{x_right}" y="{y_center}" {label_style}>{rank_num}</text>'
        )

    # Render pieces
    font_size: int = int(tile_size * 0.72)
    for r in range(rows):
        y_center = margin + (rows - 1 - r) * tile_size + tile_size / 2.0
        for c in range(cols):
            piece: Optional[Piece] = engine.board[r][c]
            if piece is None:
                continue

            x_center = margin + c * tile_size + tile_size / 2.0

            # Determine piece symbol
            symbol: str = PIECE_SYMBOLS.get(
                (piece.piece_type, piece.player),
                piece.piece_type[:2],
            )

            # Styling depending on player side
            if piece.player == Player.LIGHT:
                fill_color: str = "#ffffff"
                stroke_color: str = "#181614"
                stroke_width: str = "1.2"
            else:
                fill_color: str = "#181614"
                stroke_color: str = "#ffffff"
                stroke_width: str = "0.6"

            piece_element: str = (
                f'  <text x="{x_center}" y="{y_center}" '
                f'font-family="DejaVu Sans, \'Segoe UI Symbol\', \'Noto Sans Symbols\', Arial Unicode MS, sans-serif" '
                f'font-size="{font_size}" font-weight="bold" '
                f'text-anchor="middle" dominant-baseline="central" '
                f'fill="{fill_color}" stroke="{stroke_color}" stroke-width="{stroke_width}" '
                f'paint-order="stroke fill">{symbol}</text>'
            )
            svg_parts.append(piece_element)

    svg_parts.append("</svg>\n")
    return "\n".join(svg_parts)


def generate_variant_asset(
    variant_name: str,
    output_dir: Path,
    tile_size: int = DEFAULT_TILE_SIZE,
    margin: int = DEFAULT_MARGIN,
) -> Path:
    """Generate and save an SVG asset for the initial layout of a variant.

    Parameters
    ----------
    variant_name : str
        Name identifier of the variant.
    output_dir : Path
        Directory where the SVG asset should be written.
    tile_size : int, optional
        Tile size in pixels, by default 60.
    margin : int, optional
        Board margin in pixels, by default 30.

    Returns
    -------
    Path
        Destination path of the created SVG file.
    """
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )
    config: GameConfig = load_variant_config(variant_name)
    engine: GameEngine = GameEngine(config)
    svg_content: str = render_board_to_svg(
        engine=engine,
        tile_size=tile_size,
        margin=margin,
    )

    output_path: Path = output_dir / f"{variant_name}.svg"
    output_path.write_text(
        svg_content,
        encoding="utf-8",
    )
    return output_path


def generate_all_variant_assets(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    tile_size: int = DEFAULT_TILE_SIZE,
    margin: int = DEFAULT_MARGIN,
) -> list[Path]:
    """Discover all variants and generate their initial layout SVG assets.

    Parameters
    ----------
    output_dir : Path, optional
        Target directory for the SVG files, by default DEFAULT_OUTPUT_DIR.
    tile_size : int, optional
        Tile size in pixels, by default 60.
    margin : int, optional
        Board margin in pixels, by default 30.

    Returns
    -------
    list of Path
        List of generated SVG file paths.
    """
    variants: list[str] = list_available_variants()
    generated_paths: list[Path] = []

    for variant in variants:
        target_file: Path = generate_variant_asset(
            variant_name=variant,
            output_dir=output_dir,
            tile_size=tile_size,
            margin=margin,
        )
        generated_paths.append(target_file)

    return generated_paths


def main() -> None:
    """CLI entrypoint for doc asset generation."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Generate initial board layout SVG assets for Jedrezito variants.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Destination directory for SVG files (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--tile-size",
        type=int,
        default=DEFAULT_TILE_SIZE,
        help=f"Tile dimension in pixels (default: {DEFAULT_TILE_SIZE})",
    )
    parser.add_argument(
        "--margin",
        type=int,
        default=DEFAULT_MARGIN,
        help=f"Board margin in pixels (default: {DEFAULT_MARGIN})",
    )
    parser.add_argument(
        "--variant",
        type=str,
        default=None,
        help="Optional specific variant name to generate (generates all if omitted)",
    )

    args: argparse.Namespace = parser.parse_args()

    if args.variant:
        path: Path = generate_variant_asset(
            variant_name=args.variant,
            output_dir=args.output_dir,
            tile_size=args.tile_size,
            margin=args.margin,
        )
        print(f"Generated asset for '{args.variant}': {path}")
    else:
        paths: list[Path] = generate_all_variant_assets(
            output_dir=args.output_dir,
            tile_size=args.tile_size,
            margin=args.margin,
        )
        print(f"Generated {len(paths)} asset(s) in {args.output_dir}:")
        for p in paths:
            print(f"  - {p.name}")


if __name__ == "__main__":
    main()

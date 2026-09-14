"""Configuration loader and validator for Generalized Chess Games (JEG).

This module parses JSON configuration files defining JEG variants, enforces
fundamental JEG rules and constraints, and produces structured GameConfig objects.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jedrezito.models import (
    GameConfig,
    JumpMovement,
    MovementRule,
    PieceCategory,
    PieceType,
    RayFamily,
    RayMovement,
)


def _parse_movement_rule(
    raw_data: dict[str, Any],
) -> MovementRule:
    """Parse a raw dictionary into a MovementRule instance.

    Parameters
    ----------
    raw_data : dict of str to Any
        Dictionary containing rays, jumps, and forward_only fields.

    Returns
    -------
    MovementRule
        Parsed movement or capture rule.
    """
    rays: list[RayMovement] = []
    for ray_dict in raw_data.get("rays", []):
        family = RayFamily(ray_dict["family"])
        range_limit = ray_dict.get("range_limit")
        if range_limit is not None:
            range_limit = int(range_limit)
        rays.append(
            RayMovement(
                family=family,
                range_limit=range_limit,
            )
        )

    jumps: list[JumpMovement] = []
    for jump_dict in raw_data.get("jumps", []):
        jumps.append(
            JumpMovement(
                row_offset=int(jump_dict["row_offset"]),
                col_offset=int(jump_dict["col_offset"]),
            )
        )

    forward_only = bool(raw_data.get("forward_only", False))
    return MovementRule(
        rays=rays,
        jumps=jumps,
        forward_only=forward_only,
    )


def validate_config(
    config: GameConfig,
) -> None:
    """Validate that a GameConfig conforms to the JEG specification.

    Parameters
    ----------
    config : GameConfig
        The game configuration to validate.

    Raises
    ------
    ValueError
        If any JEG constraint is violated.
    """
    if config.rows % 2 != 0 or config.cols % 2 != 0:
        raise ValueError(
            f"Board dimensions must be even numbers: got {config.rows}x{config.cols}"
        )

    if config.rows < 4:
        raise ValueError(
            f"Board must have at least 4 rows: got {config.rows}"
        )

    if len(config.initial_back_rank) != config.cols:
        raise ValueError(
            f"Initial back rank length ({len(config.initial_back_rank)}) "
            f"must match number of columns ({config.cols})"
        )

    if len(config.initial_pawn_rank) != config.cols:
        raise ValueError(
            f"Initial pawn rank length ({len(config.initial_pawn_rank)}) "
            f"must match number of columns ({config.cols})"
        )

    # Validate piece types in ranks
    king_count = 0
    head_count = 0
    pawn_count = 0

    for name in config.initial_back_rank:
        if name is None:
            continue
        if name not in config.piece_types:
            raise ValueError(f"Unknown piece '{name}' in initial back rank")
        piece_type = config.piece_types[name]
        if piece_type.category == PieceCategory.KING:
            king_count += 1
        elif piece_type.category == PieceCategory.HEAD:
            head_count += 1
        elif piece_type.category == PieceCategory.PAWN:
            raise ValueError(
                f"Pawn '{name}' cannot be placed on the back rank (row 0)"
            )

    for name in config.initial_pawn_rank:
        if name is None:
            continue
        if name not in config.piece_types:
            raise ValueError(f"Unknown piece '{name}' in initial pawn rank")
        piece_type = config.piece_types[name]
        if piece_type.category != PieceCategory.PAWN:
            raise ValueError(
                f"Piece '{name}' on row 1 must be a pawn, got {piece_type.category}"
            )
        pawn_count += 1

    if king_count != 1:
        raise ValueError(f"Army must have exactly 1 King, got {king_count}")

    if head_count <= 0 or head_count % 2 == 0:
        raise ValueError(
            f"Army must have a strictly positive odd number of heads, got {head_count}"
        )

    if pawn_count <= 0 or pawn_count % 2 != 0:
        raise ValueError(
            f"Army must have a strictly positive even number of pawns, got {pawn_count}"
        )

    # Validate piece values and promotions
    for name, ptype in config.piece_types.items():
        if ptype.category == PieceCategory.KING:
            if ptype.material_value is not None:
                raise ValueError(
                    f"King '{name}' must not have a finite material value"
                )
        else:
            if ptype.material_value is None or ptype.material_value <= 0:
                raise ValueError(
                    f"Piece '{name}' must have a strictly positive integer material value"
                )

        if ptype.category == PieceCategory.PAWN:
            if not ptype.promotions:
                raise ValueError(
                    f"Pawn '{name}' must define at least one valid promotion head type"
                )
            for promo in ptype.promotions:
                if promo not in config.piece_types:
                    raise ValueError(
                        f"Pawn '{name}' defines unknown promotion piece '{promo}'"
                    )
                if config.piece_types[promo].category != PieceCategory.HEAD:
                    raise ValueError(
                        f"Promotion target '{promo}' must be a head piece"
                    )


def load_config_from_dict(
    data: dict[str, Any],
) -> GameConfig:
    """Create and validate a GameConfig from a dictionary.

    Parameters
    ----------
    data : dict of str to Any
        Dictionary loaded from configuration JSON.

    Returns
    -------
    GameConfig
        Validated game configuration instance.
    """
    piece_types: dict[str, PieceType] = {}
    for name, raw_type in data.get("piece_types", {}).items():
        category = PieceCategory(raw_type["category"])
        material_value = raw_type.get("material_value")
        if material_value is not None:
            material_value = int(material_value)

        move_rules = _parse_movement_rule(raw_type.get("move_rules", {}))
        capture_rules = _parse_movement_rule(raw_type.get("capture_rules", {}))
        promotions = list(raw_type.get("promotions", []))

        piece_types[name] = PieceType(
            name=name,
            category=category,
            material_value=material_value,
            move_rules=move_rules,
            capture_rules=capture_rules,
            promotions=promotions,
        )

    turn_limit = data.get("turn_limit")
    if turn_limit is not None:
        turn_limit = int(turn_limit)

    config = GameConfig(
        name=str(data.get("name", "JEG Variant")),
        rows=int(data["rows"]),
        cols=int(data["cols"]),
        piece_types=piece_types,
        initial_back_rank=list(data["initial_back_rank"]),
        initial_pawn_rank=list(data["initial_pawn_rank"]),
        turn_limit=turn_limit,
    )

    validate_config(config)
    return config


def load_config(
    file_path: str | Path,
) -> GameConfig:
    """Load and validate a GameConfig from a JSON file.

    Parameters
    ----------
    file_path : str or Path
        Path to the JSON configuration file.

    Returns
    -------
    GameConfig
        Validated game configuration.
    """
    path = Path(file_path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return load_config_from_dict(data)


def load_variant_config(
    variant_name: str = "chess",
) -> GameConfig:
    """Load a specific JEG variant configuration by name.

    Parameters
    ----------
    variant_name : str, optional
        Name of the variant corresponding to a JSON file in the variants directory,
        by default "chess".

    Returns
    -------
    GameConfig
        The parsed and validated variant configuration.

    Raises
    ------
    FileNotFoundError
        If the variant configuration file does not exist.
    """
    variant_path: Path = Path(__file__).parent / "variants" / f"{variant_name}.json"
    if not variant_path.is_file():
        raise FileNotFoundError(
            f"Variant '{variant_name}' not found at {variant_path}"
        )
    return load_config(variant_path)


def load_default_chess_config(
) -> GameConfig:
    """Load the built-in classical chess JEG variant.

    Returns
    -------
    GameConfig
        The classical chess variant configuration.
    """
    return load_variant_config("chess")


def list_available_variants(
) -> list[str]:
    """Discover and list all available JEG variants in the variants directory.

    Returns
    -------
    list of str
        Sorted list of variant identifier names without file extensions.
    """
    variants_dir: Path = Path(__file__).parent / "variants"
    if not variants_dir.is_dir():
        return []
    return sorted(
        f.stem
        for f in variants_dir.glob("*.json")
        if f.is_file()
    )


def get_variant_metadata(
    variant_name: str,
) -> dict[str, Any]:
    """Retrieve metadata summary for a given JEG variant.

    Parameters
    ----------
    variant_name : str
        Name of the variant corresponding to a JSON file.

    Returns
    -------
    dict of str to Any
        Dictionary containing variant metadata including id, name, rows, cols,
        and turn_limit.

    Raises
    ------
    FileNotFoundError
        If the variant configuration file does not exist.
    """
    variant_path: Path = Path(__file__).parent / "variants" / f"{variant_name}.json"
    if not variant_path.is_file():
        raise FileNotFoundError(
            f"Variant '{variant_name}' not found at {variant_path}"
        )
    with variant_path.open("r", encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    return {
        "id": variant_name,
        "name": data.get("name", variant_name),
        "rows": int(data.get("rows", 0)),
        "cols": int(data.get("cols", 0)),
        "turn_limit": data.get("turn_limit"),
    }

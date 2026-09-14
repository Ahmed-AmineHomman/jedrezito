"""Data models for Generalized Chess Games (JEG).

This module defines all core enumerations, dataclasses, and records representing
players, piece categories, movements, game state, and variant configurations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Player(str, Enum):
    """Enumeration of players in a JEG match.

    Attributes
    ----------
    LIGHT : str
        The player controlling light pieces, moving first.
    DARK : str
        The player controlling dark pieces, moving second.
    """

    LIGHT = "light"
    DARK = "dark"

    @property
    def opponent(
        self,
    ) -> Player:
        """Return the opposing player.

        Returns
        -------
        Player
            The other player.
        """
        if self == Player.LIGHT:
            return Player.DARK
        return Player.LIGHT

    @property
    def forward_direction(
        self,
    ) -> int:
        """Return the forward direction along the row axis.

        Returns
        -------
        int
            +1 for LIGHT, -1 for DARK.
        """
        if self == Player.LIGHT:
            return 1
        return -1


class PieceCategory(str, Enum):
    """Enumeration of piece categories in JEG.

    Attributes
    ----------
    KING : str
        The unique king of each army.
    HEAD : str
        Major/minor specialized pieces.
    PAWN : str
        Pawns subject to promotion upon reaching the opponent's back rank.
    """

    KING = "king"
    HEAD = "head"
    PAWN = "pawn"


class RayFamily(str, Enum):
    """Ray family defining movement along rectilinear or diagonal lines.

    Attributes
    ----------
    LINE : str
        Ray parallel to board rows (forward/backward).
    COLUMN : str
        Ray parallel to board columns (left/right).
    DIAGONAL : str
        Ray along the four diagonal directions.
    """

    LINE = "line"
    COLUMN = "column"
    DIAGONAL = "diagonal"


@dataclass(frozen=True)
class RayMovement:
    """Ray movement specification.

    Parameters
    ----------
    family : RayFamily
        The ray direction family.
    range_limit : int or None, optional
        Maximum number of squares that can be traversed, or None for infinite.
    """

    family: RayFamily
    range_limit: int | None = None


@dataclass(frozen=True)
class JumpMovement:
    """Jump movement specification.

    Parameters
    ----------
    row_offset : int
        Distance along the row axis.
    col_offset : int
        Distance along the column axis.
    """

    row_offset: int
    col_offset: int


@dataclass
class MovementRule:
    """Movement or capture rule for a piece type.

    Parameters
    ----------
    rays : list of RayMovement, optional
        List of ray movements available to the piece.
    jumps : list of JumpMovement, optional
        List of jump movements available to the piece.
    forward_only : bool, optional
        Whether movements are strictly restricted to the forward direction.
    """

    rays: list[RayMovement] = field(default_factory=list)
    jumps: list[JumpMovement] = field(default_factory=list)
    forward_only: bool = False


@dataclass
class PieceType:
    """Configuration for a specific piece type.

    Parameters
    ----------
    name : str
        Human-readable name of the piece type.
    category : PieceCategory
        Category of the piece (king, head, or pawn).
    material_value : int or None
        Material value (strictly positive integer for heads and pawns, None for King).
    move_rules : MovementRule
        Rules governing non-capturing displacement.
    capture_rules : MovementRule
        Rules governing captures.
    promotions : list of str, optional
        Allowed head type names when this pawn is promoted.
    """

    name: str
    category: PieceCategory
    material_value: int | None
    move_rules: MovementRule
    capture_rules: MovementRule
    promotions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Piece:
    """Instance of a piece placed on the board.

    Parameters
    ----------
    piece_type : str
        Name of the piece type.
    player : Player
        Camp owning this piece.
    """

    piece_type: str
    player: Player


@dataclass(frozen=True)
class Move:
    """Representation of a player move.

    Parameters
    ----------
    from_pos : tuple of int
        Starting coordinate (row, col).
    to_pos : tuple of int
        Target destination coordinate (row, col).
    promotion_type : str or None, optional
        Name of head piece type chosen if move triggers a promotion.
    """

    from_pos: tuple[int, int]
    to_pos: tuple[int, int]
    promotion_type: str | None = None


class GameStatus(str, Enum):
    """Status of the game.

    Attributes
    ----------
    ONGOING : str
        The game is currently in progress.
    CHECKMATE : str
        The active player has been checkmated.
    STALEMATE : str
        The active player is stalemated (draw).
    TURN_EXHAUSTED : str
        Maximum turn limit reached under turn exhaustion variant.
    """

    ONGOING = "ongoing"
    CHECKMATE = "checkmate"
    STALEMATE = "stalemate"
    TURN_EXHAUSTED = "turn_exhausted"


@dataclass
class GameConfig:
    """Full configuration for a JEG variant.

    Parameters
    ----------
    name : str
        Name of the variant.
    rows : int
        Number of board rows (must be even, >= 4).
    cols : int
        Number of board columns (must be even).
    piece_types : dict of str to PieceType
        Dictionary of piece type specifications keyed by name.
    initial_back_rank : list of str or None
        Piece type names (or None for empty) on Light's back row (row 0).
    initial_pawn_rank : list of str or None
        Piece type names (or None for empty) on Light's pawn row (row 1).
    turn_limit : int or None, optional
        Maximum turns per player before ending the game, or None if disabled.
    """

    name: str
    rows: int
    cols: int
    piece_types: dict[str, PieceType]
    initial_back_rank: list[str | None]
    initial_pawn_rank: list[str | None]
    turn_limit: int | None = None

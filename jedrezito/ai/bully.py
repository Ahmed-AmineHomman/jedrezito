"""Bully AI agent for Generalized Chess Games (JEG).

This module implements an aggressive agent that prioritizes capturing the
highest-ranking opponent piece using its lowest-ranking piece, falling back
to random moves if no captures are available.
"""

from __future__ import annotations

import random
from typing import (
    Optional,
)

from jedrezito.ai.base import (
    BaseAI,
)
from jedrezito.engine import (
    GameEngine,
)
from jedrezito.models import (
    GameConfig,
    Move,
    Piece,
    PieceCategory,
)


def get_piece_rank(
    piece: Piece,
    config: GameConfig,
) -> float:
    """Compute the numerical ranking or importance of a piece.

    The King has infinite rank, while heads and pawns are ranked according
    to their strictly positive material value.

    Parameters
    ----------
    piece : Piece
        The piece instance to evaluate.
    config : GameConfig
        Game configuration containing piece specifications.

    Returns
    -------
    float
        The rank of the piece (higher indicates greater importance/value).
    """
    piece_type = config.piece_types[piece.piece_type]
    if piece_type.category == PieceCategory.KING or piece_type.material_value is None:
        return float("inf")
    return float(piece_type.material_value)


class BullyAI(BaseAI):
    """Aggressive AI agent targeting the opponent's highest-ranking pieces.

    The Bully AI relentlessly attempts to capture the highest-ranking opponent piece
    available. When multiple captures are possible, it prioritizes attacking the most
    valuable enemy piece and using its own lowest-ranking piece to execute the capture.
    If no capture is legally available, it selects uniformly at random among all legal moves.

    Parameters
    ----------
    name : str, optional
        Unique identifier of the agent, by default "bully".
    seed : int or None, optional
        Optional random seed for deterministic reproduction, by default None.

    Attributes
    ----------
    name : str
        Name of the agent.
    """

    def __init__(
        self,
        name: str = "bully",
        seed: Optional[int] = None,
    ) -> None:
        super().__init__(name=name)
        self._rng: random.Random = random.Random(seed)

    def select_move(
        self,
        engine: GameEngine,
    ) -> Optional[Move]:
        """Select a move following the Bully strategy.

        Prioritizes capturing the highest-ranking opponent piece with the lowest-ranking
        own piece. Falls back to a random legal move if no capture is available.

        Parameters
        ----------
        engine : GameEngine
            The active game engine instance.

        Returns
        -------
        Move or None
            The chosen legal move, or None if no legal moves exist.
        """
        legal_moves: list[Move] = engine.get_legal_moves(engine.current_player)
        if not legal_moves:
            return None

        # Filter capturing moves and associate with priority score:
        # (captured_piece_rank, -attacker_piece_rank)
        capture_candidates: list[tuple[tuple[float, float], Move]] = []
        for move in legal_moves:
            target_piece: Optional[Piece] = engine.get_piece(
                move.to_pos[0],
                move.to_pos[1],
            )
            if target_piece is not None:
                attacker_piece: Optional[Piece] = engine.get_piece(
                    move.from_pos[0],
                    move.from_pos[1],
                )
                if attacker_piece is not None:
                    captured_rank: float = get_piece_rank(
                        target_piece,
                        engine.config,
                    )
                    attacker_rank: float = get_piece_rank(
                        attacker_piece,
                        engine.config,
                    )
                    # Priority: Maximize captured rank, minimize attacker rank
                    score: tuple[float, float] = (
                        captured_rank,
                        -attacker_rank,
                    )
                    capture_candidates.append((score, move))

        # If no capture moves are available, fall back to random choice
        if not capture_candidates:
            return self._rng.choice(legal_moves)

        # Select among the highest scoring capture moves
        max_score: tuple[float, float] = max(
            score for score, _ in capture_candidates
        )
        best_moves: list[Move] = [
            move for score, move in capture_candidates if score == max_score
        ]

        return self._rng.choice(best_moves)

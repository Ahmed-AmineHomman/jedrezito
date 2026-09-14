"""Joker AI agent for Generalized Chess Games (JEG).

This module implements a random agent that selects uniformly among all
currently available legal moves.
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
    Move,
)


class JokerAI(BaseAI):
    """Random AI agent selecting moves uniformly at random.

    Parameters
    ----------
    name : str, optional
        Unique identifier of the agent, by default "joker".
    seed : int or None, optional
        Optional random seed for deterministic reproduction, by default None.

    Attributes
    ----------
    name : str
        Name of the agent.
    """

    def __init__(
        self,
        name: str = "joker",
        seed: Optional[int] = None,
    ) -> None:
        super().__init__(name=name)
        self._rng: random.Random = random.Random(seed)

    def select_move(
        self,
        engine: GameEngine,
    ) -> Optional[Move]:
        """Select a legal move uniformly at random.

        Parameters
        ----------
        engine : GameEngine
            The active game engine instance.

        Returns
        -------
        Move or None
            A randomly chosen legal move, or None if no legal moves exist.
        """
        legal_moves: list[Move] = engine.get_legal_moves(engine.current_player)
        if not legal_moves:
            return None
        return self._rng.choice(legal_moves)

"""Base class definition for Generalized Chess Games (JEG) artificial intelligence agents.

This module provides the abstract interface that all AI agents playing JEG
must implement to participate in games and tournaments.
"""

from __future__ import annotations

from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    Optional,
)

from jedrezito.engine import (
    GameEngine,
)
from jedrezito.models import (
    Move,
)


class BaseAI(ABC):
    """Abstract base class for all JEG artificial intelligence agents.

    Parameters
    ----------
    name : str
        Unique identifier or display name of the AI agent.

    Attributes
    ----------
    name : str
        Name of the AI agent.
    """

    def __init__(
        self,
        name: str,
    ) -> None:
        self.name: str = name

    @abstractmethod
    def select_move(
        self,
        engine: GameEngine,
    ) -> Optional[Move]:
        """Select a legal move given the current game engine state.

        Parameters
        ----------
        engine : GameEngine
            The active game engine instance providing board state and legal moves.

        Returns
        -------
        Move or None
            The chosen legal move, or None if no legal moves are available.
        """
        raise NotImplementedError

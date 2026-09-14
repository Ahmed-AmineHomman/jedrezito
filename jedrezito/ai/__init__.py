"""Artificial Intelligence agents package for Generalized Chess Games (JEG).

This package provides AI agent implementations, base interfaces, and factory
functions to register and instantiate agents for games and tournaments.
"""

from __future__ import annotations

from typing import (
    Any,
    Callable,
    Optional,
)

from jedrezito.ai.base import (
    BaseAI,
)
from jedrezito.ai.joker import (
    JokerAI,
)

AI_REGISTRY: dict[str, Callable[..., BaseAI]] = {
    "joker": JokerAI,
}


def list_available_ais(
) -> list[str]:
    """Retrieve the sorted list of registered AI agent identifiers.

    Returns
    -------
    list of str
        Identifiers of all available AI agents.
    """
    return sorted(AI_REGISTRY.keys())


def create_ai(
    name: str,
    **kwargs: Any,
) -> BaseAI:
    """Instantiate a registered AI agent by identifier.

    Parameters
    ----------
    name : str
        Identifier of the registered AI agent.
    **kwargs : Any
        Optional keyword arguments forwarded to the AI constructor.

    Returns
    -------
    BaseAI
        Configured AI agent instance.

    Raises
    ------
    ValueError
        If no AI agent is registered under the given identifier.
    """
    if name not in AI_REGISTRY:
        raise ValueError(
            f"Unknown AI agent '{name}'. Available agents: {list_available_ais()}"
        )
    factory: Callable[..., BaseAI] = AI_REGISTRY[name]
    return factory(**kwargs)


__all__: list[str] = [
    "BaseAI",
    "JokerAI",
    "create_ai",
    "list_available_ais",
]

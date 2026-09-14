"""Scaredycat AI agent for Generalized Chess Games (JEG).

This module implements a cautious agent that prioritizes protecting all its
heads (major and minor pieces), attacking according to the Bully strategy only
when all heads are defended, and minimizing risk to its most valuable pieces
otherwise.
"""

from __future__ import annotations

import random
from typing import (
    Optional,
)

from jedrezito.ai.base import (
    BaseAI,
)
from jedrezito.ai.bully import (
    get_piece_rank,
)
from jedrezito.engine import (
    GameEngine,
)
from jedrezito.models import (
    Move,
    Piece,
    PieceCategory,
    Player,
)


class ScaredycatAI(BaseAI):
    """Cautious AI agent prioritizing head piece defense.

    The Scaredycat AI ensures all its heads are defended before considering
    aggressive actions. When all heads are protected, it mimics the Bully AI
    within the safe move subset (or moves randomly if no capture exists). If full
    protection cannot be achieved or maintained, it chooses a move minimizing the
    maximum value among unprotected heads. In the endgame with no remaining heads,
    it seeks to advance its pawns, capturing when possible.

    Parameters
    ----------
    name : str, optional
        Unique identifier of the agent, by default "scaredycat".
    seed : int or None, optional
        Optional random seed for deterministic reproduction, by default None.

    Attributes
    ----------
    name : str
        Name of the agent.
    """

    def __init__(
        self,
        name: str = "scaredycat",
        seed: Optional[int] = None,
    ) -> None:
        super().__init__(name=name)
        self._rng: random.Random = random.Random(seed)

    def _get_unprotected_heads(
        self,
        engine: GameEngine,
        player: Player,
    ) -> list[Piece]:
        """Collect all friendly heads that are not protected by another friendly piece.

        Parameters
        ----------
        engine : GameEngine
            The game engine with the current board state.
        player : Player
            The player whose heads are evaluated.

        Returns
        -------
        list of Piece
            List of unprotected friendly head pieces.
        """
        unprotected: list[Piece] = []
        for r in range(engine.config.rows):
            for c in range(engine.config.cols):
                piece = engine.board[r][c]
                if piece is not None and piece.player == player:
                    piece_type = engine.config.piece_types[piece.piece_type]
                    if piece_type.category == PieceCategory.HEAD:
                        if not engine.is_square_threatened(r, c, player):
                            unprotected.append(piece)
        return unprotected

    def _select_endgame_move(
        self,
        engine: GameEngine,
        legal_moves: list[Move],
    ) -> Move:
        """Select a move in the endgame when no friendly heads remain.

        Tries to advance pawns forward, capturing if possible. Falls back to a
        random legal move if no pawn advancement is possible.

        Parameters
        ----------
        engine : GameEngine
            The active game engine.
        legal_moves : list of Move
            All available legal moves.

        Returns
        -------
        Move
            The chosen legal move.
        """
        player = engine.current_player
        forward_dir = player.forward_direction
        pawn_advances: list[Move] = []
        pawn_captures: list[Move] = []

        for move in legal_moves:
            piece = engine.board[move.from_pos[0]][move.from_pos[1]]
            if piece is not None and piece.player == player:
                piece_type = engine.config.piece_types[piece.piece_type]
                if piece_type.category == PieceCategory.PAWN:
                    row_diff = move.to_pos[0] - move.from_pos[0]
                    if row_diff * forward_dir > 0:
                        pawn_advances.append(move)
                        target = engine.board[move.to_pos[0]][move.to_pos[1]]
                        if target is not None and target.player != player:
                            pawn_captures.append(move)

        if pawn_captures:
            return self._rng.choice(pawn_captures)
        if pawn_advances:
            return self._rng.choice(pawn_advances)
        return self._rng.choice(legal_moves)

    def select_move(
        self,
        engine: GameEngine,
    ) -> Optional[Move]:
        """Select a move following the Scaredycat strategy.

        Parameters
        ----------
        engine : GameEngine
            The active game engine instance.

        Returns
        -------
        Move or None
            The chosen legal move, or None if no legal moves exist.
        """
        player = engine.current_player
        legal_moves: list[Move] = engine.get_legal_moves(player)
        if not legal_moves:
            return None

        # Check if friendly heads remain on the board
        has_heads = False
        for r in range(engine.config.rows):
            for c in range(engine.config.cols):
                piece = engine.board[r][c]
                if piece is not None and piece.player == player:
                    piece_type = engine.config.piece_types[piece.piece_type]
                    if piece_type.category == PieceCategory.HEAD:
                        has_heads = True
                        break
            if has_heads:
                break

        # Endgame: No friendly heads remain
        if not has_heads:
            return self._select_endgame_move(
                engine=engine,
                legal_moves=legal_moves,
            )

        # Evaluate protection status resulting from each candidate move
        safe_moves: list[Move] = []
        unsafe_moves: list[tuple[float, Move]] = []

        for move in legal_moves:
            fr, fc = move.from_pos
            tr, tc = move.to_pos
            moving_piece = engine.board[fr][fc]
            captured_piece = engine.board[tr][tc]

            if move.promotion_type is not None:
                assert moving_piece is not None
                placed_piece: Optional[Piece] = Piece(
                    piece_type=move.promotion_type,
                    player=moving_piece.player,
                )
            else:
                placed_piece = moving_piece

            engine.board[fr][fc] = None
            engine.board[tr][tc] = placed_piece

            try:
                unprotected = self._get_unprotected_heads(
                    engine=engine,
                    player=player,
                )
                if not unprotected:
                    safe_moves.append(move)
                else:
                    max_unprotected_rank = max(
                        get_piece_rank(p, engine.config) for p in unprotected
                    )
                    unsafe_moves.append((max_unprotected_rank, move))
            finally:
                engine.board[fr][fc] = moving_piece
                engine.board[tr][tc] = captured_piece

        # Case A: At least one move keeps or establishes full head protection
        if safe_moves:
            safe_captures: list[tuple[tuple[float, float], Move]] = []
            for move in safe_moves:
                target_piece = engine.board[move.to_pos[0]][move.to_pos[1]]
                if target_piece is not None and target_piece.player != player:
                    attacker_piece = engine.board[move.from_pos[0]][move.from_pos[1]]
                    if attacker_piece is not None:
                        captured_rank = get_piece_rank(
                            piece=target_piece,
                            config=engine.config,
                        )
                        attacker_rank = get_piece_rank(
                            piece=attacker_piece,
                            config=engine.config,
                        )
                        score = (captured_rank, -attacker_rank)
                        safe_captures.append((score, move))

            if safe_captures:
                max_score = max(score for score, _ in safe_captures)
                best_safe_captures = [
                    move for score, move in safe_captures if score == max_score
                ]
                return self._rng.choice(best_safe_captures)

            return self._rng.choice(safe_moves)

        # Case B: No move maintains full protection. Minimax rank selection.
        min_penalty = min(penalty for penalty, _ in unsafe_moves)
        best_unsafe_moves = [
            move for penalty, move in unsafe_moves if penalty == min_penalty
        ]
        return self._rng.choice(best_unsafe_moves)

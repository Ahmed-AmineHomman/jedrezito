"""Core game engine for Generalized Chess Games (JEG).

This module implements the complete game loop, board state management, move
generation, threat/check evaluation, and win/draw condition detection according
to the JEG specification.
"""

from __future__ import annotations

import copy
from typing import Iterator

from jedrezito.models import (
    GameConfig,
    GameStatus,
    Move,
    Piece,
    PieceCategory,
    Player,
    RayFamily,
)


class GameEngine:
    """Game engine managing a Generalized Chess Game match.

    Parameters
    ----------
    config : GameConfig
        The configuration defining the rules and army composition.

    Attributes
    ----------
    config : GameConfig
        Configuration of the active JEG variant.
    board : list of list of Piece or None
        2D grid representing the board state (rows x cols).
    current_player : Player
        The player whose turn it is to move.
    status : GameStatus
        Current status of the match.
    winner : Player or None
        The winning player, or None if ongoing or drawn.
    turns_played : dict of Player to int
        Number of moves completed by each player.
    """

    def __init__(
        self,
        config: GameConfig,
    ) -> None:
        self.config: GameConfig = config
        self.board: list[list[Piece | None]] = []
        self.current_player: Player = Player.LIGHT
        self.status: GameStatus = GameStatus.ONGOING
        self.winner: Player | None = None
        self.turns_played: dict[Player, int] = {
            Player.LIGHT: 0,
            Player.DARK: 0,
        }
        self.reset()

    def reset(
        self,
    ) -> None:
        """Reset the game state to the initial setup."""
        rows = self.config.rows
        cols = self.config.cols
        self.board = [[None for _ in range(cols)] for _ in range(rows)]
        self.current_player = Player.LIGHT
        self.status = GameStatus.ONGOING
        self.winner = None
        self.turns_played = {
            Player.LIGHT: 0,
            Player.DARK: 0,
        }

        # Setup Light pieces
        for col_idx, piece_name in enumerate(self.config.initial_back_rank):
            if piece_name is not None:
                self.board[0][col_idx] = Piece(
                    piece_type=piece_name,
                    player=Player.LIGHT,
                )

        for col_idx, piece_name in enumerate(self.config.initial_pawn_rank):
            if piece_name is not None:
                self.board[1][col_idx] = Piece(
                    piece_type=piece_name,
                    player=Player.LIGHT,
                )

        # Setup Dark pieces by 180° rotation symmetry: (r, c) -> (rows - 1 - r, cols - 1 - c)
        for col_idx, piece_name in enumerate(self.config.initial_back_rank):
            if piece_name is not None:
                target_r = rows - 1
                target_c = cols - 1 - col_idx
                self.board[target_r][target_c] = Piece(
                    piece_type=piece_name,
                    player=Player.DARK,
                )

        for col_idx, piece_name in enumerate(self.config.initial_pawn_rank):
            if piece_name is not None:
                target_r = rows - 2
                target_c = cols - 1 - col_idx
                self.board[target_r][target_c] = Piece(
                    piece_type=piece_name,
                    player=Player.DARK,
                )

    def is_in_bounds(
        self,
        row: int,
        col: int,
    ) -> bool:
        """Check whether coordinates lie within the board boundaries.

        Parameters
        ----------
        row : int
            Row coordinate.
        col : int
            Column coordinate.

        Returns
        -------
        bool
            True if the coordinates are on the board, False otherwise.
        """
        return 0 <= row < self.config.rows and 0 <= col < self.config.cols

    def get_piece(
        self,
        row: int,
        col: int,
    ) -> Piece | None:
        """Retrieve the piece at the specified square.

        Parameters
        ----------
        row : int
            Row coordinate.
        col : int
            Column coordinate.

        Returns
        -------
        Piece or None
            The piece occupying the square, or None if empty or out of bounds.
        """
        if not self.is_in_bounds(row, col):
            return None
        return self.board[row][col]

    def get_army_value(
        self,
        player: Player,
    ) -> int:
        """Calculate the total material value of an army.

        The King is excluded from this calculation as per JEG specification.

        Parameters
        ----------
        player : Player
            The player whose army value is to be computed.

        Returns
        -------
        int
            Total material value of currently present pieces.
        """
        total = 0
        for r in range(self.config.rows):
            for c in range(self.config.cols):
                piece = self.board[r][c]
                if piece is not None and piece.player == player:
                    piece_type = self.config.piece_types[piece.piece_type]
                    if piece_type.material_value is not None:
                        total += piece_type.material_value
        return total

    def find_king(
        self,
        player: Player,
    ) -> tuple[int, int] | None:
        """Find the coordinates of the King for a given player.

        Parameters
        ----------
        player : Player
            Player whose King is searched.

        Returns
        -------
        tuple of int or None
            (row, col) coordinates of the King, or None if not found.
        """
        for r in range(self.config.rows):
            for c in range(self.config.cols):
                piece = self.board[r][c]
                if piece is not None and piece.player == player:
                    piece_type = self.config.piece_types[piece.piece_type]
                    if piece_type.category == PieceCategory.KING:
                        return (r, c)
        return None

    def _generate_ray_destinations(
        self,
        row: int,
        col: int,
        player: Player,
        family: RayFamily,
        range_limit: int | None,
        forward_only: bool,
    ) -> Iterator[tuple[int, int]]:
        """Yield valid ray squares originating from a given position.

        Parameters
        ----------
        row : int
            Origin row.
        col : int
            Origin column.
        player : Player
            Owner player for orientation.
        family : RayFamily
            Ray direction family.
        range_limit : int or None
            Max distance, or None for infinite.
        forward_only : bool
            Whether movement is restricted towards the opposing rank.

        Yields
        ------
        tuple of int
            (target_row, target_col) coordinates along ray paths.
        """
        forward_dir = player.forward_direction
        directions: list[tuple[int, int]] = []

        if family == RayFamily.LINE:
            if forward_only:
                directions.append((forward_dir, 0))
            else:
                directions.extend([(1, 0), (-1, 0)])
        elif family == RayFamily.COLUMN:
            if not forward_only:
                directions.extend([(0, 1), (0, -1)])
        elif family == RayFamily.DIAGONAL:
            if forward_only:
                directions.extend([
                    (forward_dir, 1),
                    (forward_dir, -1),
                ])
            else:
                directions.extend([
                    (1, 1),
                    (1, -1),
                    (-1, 1),
                    (-1, -1),
                ])

        max_steps = (
            range_limit
            if range_limit is not None
            else max(self.config.rows, self.config.cols)
        )

        for dr, dc in directions:
            for step in range(1, max_steps + 1):
                nr = row + dr * step
                nc = col + dc * step
                if not self.is_in_bounds(nr, nc):
                    break
                yield (nr, nc)
                # If a piece is encountered, ray stops traversing beyond
                if self.board[nr][nc] is not None:
                    break

    def _generate_jump_destinations(
        self,
        row: int,
        col: int,
        player: Player,
        row_offset: int,
        col_offset: int,
        forward_only: bool,
    ) -> Iterator[tuple[int, int]]:
        """Yield destination squares for a jump movement.

        Parameters
        ----------
        row : int
            Origin row.
        col : int
            Origin column.
        player : Player
            Owner player for orientation.
        row_offset : int
            Distance along the row axis.
        col_offset : int
            Distance along the column axis.
        forward_only : bool
            Whether jump is restricted forward.

        Yields
        ------
        tuple of int
            (target_row, target_col) coordinates.
        """
        forward_dir = player.forward_direction
        row_sign_candidates = [1] if forward_only else [1, -1]
        col_sign_candidates = [1, -1]

        visited: set[tuple[int, int]] = set()

        for r_sign in row_sign_candidates:
            for c_sign in col_sign_candidates:
                relative_row = r_sign * row_offset
                relative_col = c_sign * col_offset

                if forward_only and relative_row <= 0:
                    continue

                nr = row + relative_row * forward_dir
                nc = col + relative_col

                if self.is_in_bounds(nr, nc):
                    pos = (nr, nc)
                    if pos not in visited:
                        visited.add(pos)
                        yield pos

    def is_square_threatened(
        self,
        target_row: int,
        target_col: int,
        by_player: Player,
    ) -> bool:
        """Check whether a square is threatened by a given player.

        Parameters
        ----------
        target_row : int
            Target square row.
        target_col : int
            Target square column.
        by_player : Player
            Player whose pieces may threaten the square.

        Returns
        -------
        bool
            True if any piece of by_player threatens the target square.
        """
        for r in range(self.config.rows):
            for c in range(self.config.cols):
                piece = self.board[r][c]
                if piece is None or piece.player != by_player:
                    continue

                piece_type = self.config.piece_types[piece.piece_type]
                capture_rules = piece_type.capture_rules

                # Check rays
                for ray in capture_rules.rays:
                    for dest_r, dest_c in self._generate_ray_destinations(
                        r,
                        c,
                        piece.player,
                        ray.family,
                        ray.range_limit,
                        capture_rules.forward_only,
                    ):
                        if dest_r == target_row and dest_c == target_col:
                            return True

                # Check jumps
                for jump in capture_rules.jumps:
                    for dest_r, dest_c in self._generate_jump_destinations(
                        r,
                        c,
                        piece.player,
                        jump.row_offset,
                        jump.col_offset,
                        capture_rules.forward_only,
                    ):
                        if dest_r == target_row and dest_c == target_col:
                            return True

        return False

    def is_in_check(
        self,
        player: Player,
    ) -> bool:
        """Check whether the given player's King is currently in check.

        Parameters
        ----------
        player : Player
            The player whose King is evaluated.

        Returns
        -------
        bool
            True if the King is threatened by an opponent piece.
        """
        king_pos = self.find_king(player)
        if king_pos is None:
            return False
        return self.is_square_threatened(
            king_pos[0],
            king_pos[1],
            player.opponent,
        )

    def _is_pawn_promotion_rank(
        self,
        row: int,
        player: Player,
    ) -> bool:
        """Check whether a row corresponds to the promotion rank for a player.

        Parameters
        ----------
        row : int
            Row coordinate.
        player : Player
            Player moving the pawn.

        Returns
        -------
        bool
            True if row is the opponent's back rank.
        """
        if player == Player.LIGHT:
            return row == self.config.rows - 1
        return row == 0

    def generate_pseudo_legal_moves(
        self,
        row: int,
        col: int,
    ) -> list[Move]:
        """Generate all pseudo-legal moves for a piece on a given square.

        Pseudo-legal moves follow geometric movement and capture rules,
        without checking King safety.

        Parameters
        ----------
        row : int
            Row coordinate of the piece.
        col : int
            Column coordinate of the piece.

        Returns
        -------
        list of Move
            List of pseudo-legal moves.
        """
        piece = self.get_piece(row, col)
        if piece is None:
            return []

        piece_type = self.config.piece_types[piece.piece_type]
        player = piece.player
        moves: list[Move] = []

        def add_move(
            dest_r: int,
            dest_c: int,
        ) -> None:
            if (
                piece_type.category == PieceCategory.PAWN
                and self._is_pawn_promotion_rank(dest_r, player)
            ):
                for promo in piece_type.promotions:
                    moves.append(
                        Move(
                            from_pos=(row, col),
                            to_pos=(dest_r, dest_c),
                            promotion_type=promo,
                        )
                    )
            else:
                moves.append(
                    Move(
                        from_pos=(row, col),
                        to_pos=(dest_r, dest_c),
                        promotion_type=None,
                    )
                )

        # 1. Non-capturing movements
        # Rays
        for ray in piece_type.move_rules.rays:
            for dest_r, dest_c in self._generate_ray_destinations(
                row,
                col,
                player,
                ray.family,
                ray.range_limit,
                piece_type.move_rules.forward_only,
            ):
                if self.board[dest_r][dest_c] is None:
                    add_move(dest_r, dest_c)

        # Jumps
        for jump in piece_type.move_rules.jumps:
            for dest_r, dest_c in self._generate_jump_destinations(
                row,
                col,
                player,
                jump.row_offset,
                jump.col_offset,
                piece_type.move_rules.forward_only,
            ):
                if self.board[dest_r][dest_c] is None:
                    add_move(dest_r, dest_c)

        # 2. Capturing movements
        # Rays
        for ray in piece_type.capture_rules.rays:
            for dest_r, dest_c in self._generate_ray_destinations(
                row,
                col,
                player,
                ray.family,
                ray.range_limit,
                piece_type.capture_rules.forward_only,
            ):
                target = self.board[dest_r][dest_c]
                if target is not None and target.player != player:
                    add_move(dest_r, dest_c)

        # Jumps
        for jump in piece_type.capture_rules.jumps:
            for dest_r, dest_c in self._generate_jump_destinations(
                row,
                col,
                player,
                jump.row_offset,
                jump.col_offset,
                piece_type.capture_rules.forward_only,
            ):
                target = self.board[dest_r][dest_c]
                if target is not None and target.player != player:
                    add_move(dest_r, dest_c)

        return moves

    def _simulate_move(
        self,
        move: Move,
    ) -> bool:
        """Simulate a move and determine if it leaves the player's King safe.

        Parameters
        ----------
        move : Move
            The move to simulate.

        Returns
        -------
        bool
            True if King remains safe after the move.
        """
        fr, fc = move.from_pos
        tr, tc = move.to_pos
        moving_piece = self.board[fr][fc]
        if moving_piece is None:
            return False

        captured_piece = self.board[tr][tc]

        # Apply temporary move
        if move.promotion_type is not None:
            placed_piece = Piece(
                piece_type=move.promotion_type,
                player=moving_piece.player,
            )
        else:
            placed_piece = moving_piece

        self.board[fr][fc] = None
        self.board[tr][tc] = placed_piece

        safe = not self.is_in_check(moving_piece.player)

        # Revert move
        self.board[fr][fc] = moving_piece
        self.board[tr][tc] = captured_piece

        return safe

    def get_legal_moves_from(
        self,
        row: int,
        col: int,
    ) -> list[Move]:
        """Get all legal moves available for a piece at the specified square.

        Parameters
        ----------
        row : int
            Row coordinate.
        col : int
            Column coordinate.

        Returns
        -------
        list of Move
            List of validated legal moves.
        """
        piece = self.get_piece(row, col)
        if piece is None or piece.player != self.current_player:
            return []

        pseudo_moves = self.generate_pseudo_legal_moves(row, col)
        return [m for m in pseudo_moves if self._simulate_move(m)]

    def get_legal_moves(
        self,
        player: Player | None = None,
    ) -> list[Move]:
        """Get all legal moves for the given player.

        Parameters
        ----------
        player : Player or None, optional
            Player whose legal moves are requested. Defaults to current_player.

        Returns
        -------
        list of Move
            All legal moves available to the player.
        """
        active = self.current_player if player is None else player
        all_legal: list[Move] = []

        for r in range(self.config.rows):
            for c in range(self.config.cols):
                piece = self.board[r][c]
                if piece is not None and piece.player == active:
                    pseudo = self.generate_pseudo_legal_moves(r, c)
                    for m in pseudo:
                        if self._simulate_move(m):
                            all_legal.append(m)

        return all_legal

    def make_move(
        self,
        move: Move,
    ) -> bool:
        """Execute a move on the board if legal.

        Parameters
        ----------
        move : Move
            The move to execute.

        Returns
        -------
        bool
            True if the move was legal and executed, False otherwise.
        """
        if self.status != GameStatus.ONGOING:
            return False

        fr, fc = move.from_pos
        piece = self.get_piece(fr, fc)
        if piece is None or piece.player != self.current_player:
            return False

        legal_moves = self.get_legal_moves_from(fr, fc)
        matched_move: Move | None = None
        for cand in legal_moves:
            if cand.to_pos == move.to_pos:
                if cand.promotion_type is not None:
                    if (
                        move.promotion_type is None
                        or cand.promotion_type == move.promotion_type
                    ):
                        matched_move = cand
                        break
                else:
                    matched_move = cand
                    break

        if matched_move is None:
            return False

        # Execute the move
        tr, tc = matched_move.to_pos
        self.board[fr][fc] = None

        if matched_move.promotion_type is not None:
            self.board[tr][tc] = Piece(
                piece_type=matched_move.promotion_type,
                player=self.current_player,
            )
        else:
            self.board[tr][tc] = piece

        self.turns_played[self.current_player] += 1
        self.current_player = self.current_player.opponent
        self._evaluate_game_status()
        return True

    def _evaluate_game_status(
        self,
    ) -> None:
        """Update game status following a move."""
        # 1. Turn exhaustion check (if configured)
        if self.config.turn_limit is not None:
            limit = self.config.turn_limit
            if (
                self.turns_played[Player.LIGHT] >= limit
                and self.turns_played[Player.DARK] >= limit
            ):
                val_light = self.get_army_value(Player.LIGHT)
                val_dark = self.get_army_value(Player.DARK)
                self.status = GameStatus.TURN_EXHAUSTED
                if val_light > val_dark:
                    self.winner = Player.LIGHT
                elif val_dark > val_light:
                    self.winner = Player.DARK
                else:
                    self.winner = None
                return

        # 2. Checkmate and Stalemate check
        legal_moves = self.get_legal_moves(self.current_player)
        if not legal_moves:
            if self.is_in_check(self.current_player):
                self.status = GameStatus.CHECKMATE
                self.winner = self.current_player.opponent
            else:
                self.status = GameStatus.STALEMATE
                self.winner = None

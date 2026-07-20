"""
BlockRepository — data access layer for the Block aggregate.

Architecture:
    - Receives an AsyncSession via constructor injection.
    - The only layer permitted to write SQLAlchemy queries for Block.
    - Returns ORM model instances or primitives — never raises HTTP exceptions.
    - Business logic lives in BlockService, not here.
"""

import logging
import uuid
from typing import Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.block import Block
from app.models.user import User

logger = logging.getLogger(__name__)


class BlockRepository:
    """
    Data access object for the `blocks` table.

    All queries for Block records go through this class.
    Instantiate with an active AsyncSession obtained from get_db().
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Args:
            session: An active SQLAlchemy AsyncSession.
        """
        self._session = session

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    async def get_block(
        self,
        blocker_id: uuid.UUID,
        blocked_id: uuid.UUID,
    ) -> Optional[Block]:
        """
        Fetch a specific block record by participant IDs.

        Args:
            blocker_id: UUID of the user who placed the block.
            blocked_id: UUID of the user who is blocked.

        Returns:
            Block instance or None if the block does not exist.
        """
        stmt = select(Block).where(
            Block.blocker_id == blocker_id,
            Block.blocked_id == blocked_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def is_blocked(
        self,
        blocker_id: uuid.UUID,
        blocked_id: uuid.UUID,
    ) -> bool:
        """
        Return True if `blocker_id` has blocked `blocked_id`.

        Args:
            blocker_id: UUID of the potential blocker.
            blocked_id: UUID of the potentially blocked user.

        Returns:
            True if the block exists, False otherwise.
        """
        block = await self.get_block(blocker_id, blocked_id)
        return block is not None

    async def is_mutually_blocked(
        self,
        user_a_id: uuid.UUID,
        user_b_id: uuid.UUID,
    ) -> bool:
        """
        Return True if either user has blocked the other.

        Useful as a quick "can these users interact?" guard across services.

        Args:
            user_a_id: UUID of the first user.
            user_b_id: UUID of the second user.

        Returns:
            True if any block exists in either direction.
        """
        stmt = select(func.count()).where(
            (
                (Block.blocker_id == user_a_id) & (Block.blocked_id == user_b_id)
            )
            | (
                (Block.blocker_id == user_b_id) & (Block.blocked_id == user_a_id)
            )
        )
        result = await self._session.execute(stmt)
        return (result.scalar_one() or 0) > 0

    async def blocked_count(self, blocker_id: uuid.UUID) -> int:
        """
        Return the total number of users that `blocker_id` has blocked.

        Args:
            blocker_id: UUID of the user whose block list is counted.

        Returns:
            Integer count.
        """
        stmt = (
            select(func.count())
            .select_from(Block)
            .where(Block.blocker_id == blocker_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def blocked_users(
        self,
        blocker_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> list[tuple[User, Block]]:
        """
        Return (User, Block) tuples for accounts that `blocker_id` has blocked.

        Only returns records where the blocked user still exists (not hard-deleted).
        Results are ordered newest-block-first.

        Args:
            blocker_id: UUID of the user whose block list is fetched.
            skip:       Number of records to skip (for pagination).
            limit:      Maximum number of records to return.

        Returns:
            List of (User, Block) tuples (may be empty).
        """
        safe_limit = min(max(1, limit), 100)
        stmt = (
            select(User, Block)
            .join(Block, Block.blocked_id == User.id)
            .where(Block.blocker_id == blocker_id)
            .order_by(Block.created_at.desc())
            .offset(skip)
            .limit(safe_limit)
        )
        result = await self._session.execute(stmt)
        return [(row.User, row.Block) for row in result]

    async def blocked_by_users(
        self,
        blocked_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> list[tuple[User, Block]]:
        """
        Return (User, Block) tuples for accounts that have blocked `blocked_id`.

        Only returns records where the blocker user still exists (not hard-deleted).
        Results are ordered newest-block-first.

        Args:
            blocked_id: UUID of the user to check who has blocked them.
            skip:       Number of records to skip (for pagination).
            limit:      Maximum number of records to return.

        Returns:
            List of (User, Block) tuples (may be empty).
        """
        safe_limit = min(max(1, limit), 100)
        stmt = (
            select(User, Block)
            .join(Block, Block.blocker_id == User.id)
            .where(Block.blocked_id == blocked_id)
            .order_by(Block.created_at.desc())
            .offset(skip)
            .limit(safe_limit)
        )
        result = await self._session.execute(stmt)
        return [(row.User, row.Block) for row in result]

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    async def block_user(
        self,
        blocker_id: uuid.UUID,
        blocked_id: uuid.UUID,
    ) -> Block:
        """
        Persist a new block record.

        Pre-conditions (enforced by BlockService before this call):
            - blocker_id != blocked_id
            - the block does not already exist
            - target user is active and not deleted

        Args:
            blocker_id: UUID of the user placing the block.
            blocked_id: UUID of the user being blocked.

        Returns:
            The newly created Block instance with server-generated fields.
        """
        new_block = Block(blocker_id=blocker_id, blocked_id=blocked_id)
        self._session.add(new_block)
        await self._session.flush()
        await self._session.refresh(new_block)
        logger.info(
            "block_repo.blocked blocker_id=%s blocked_id=%s",
            str(blocker_id),
            str(blocked_id),
        )
        return new_block

    async def unblock_user(
        self,
        blocker_id: uuid.UUID,
        blocked_id: uuid.UUID,
    ) -> bool:
        """
        Remove a block record.

        Args:
            blocker_id: UUID of the user removing the block.
            blocked_id: UUID of the user being unblocked.

        Returns:
            True if a row was deleted; False if the block did not exist.
        """
        stmt = delete(Block).where(
            Block.blocker_id == blocker_id,
            Block.blocked_id == blocked_id,
        )
        result = await self._session.execute(stmt)
        removed = result.rowcount > 0
        if removed:
            logger.info(
                "block_repo.unblocked blocker_id=%s blocked_id=%s",
                str(blocker_id),
                str(blocked_id),
            )
        return removed

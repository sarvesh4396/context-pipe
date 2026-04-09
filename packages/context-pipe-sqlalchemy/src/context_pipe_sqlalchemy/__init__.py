# packages/context-pipe-sqlalchemy/src/context_pipe_sqlalchemy/__init__.py

import asyncio
import json
from datetime import datetime
from typing import Optional, Union

from sqlalchemy import JSON, Column, DateTime, Integer, String, create_engine, Engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from context_pipe import AbstractBackend
from context_pipe.schemas import (
    Conversation,
    Message,
    Role,
    Summary,
    WipeMode,
)

Base = declarative_base()


class ConversationORM(Base):
    """SQLAlchemy ORM model for conversations."""

    __tablename__ = "conversations"

    id = Column(String, primary_key=True)
    messages_json = Column(JSON, default=[])
    summaries_json = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class SQLAlchemyBackend(AbstractBackend):
    """SQLAlchemy backend for storing conversations in SQL databases.

    Supports any SQLAlchemy-compatible database (PostgreSQL, SQLite, MySQL, etc.)
    with both async and sync support.
    """

    def __init__(
        self,
        engine: AsyncEngine,
        session_factory: sessionmaker | None = None,
        sync_engine: Engine | None = None,
        sync_session_factory: sessionmaker | None = None,
    ) -> None:
        """Initialize the SQLAlchemy backend.

        Args:
            engine: The SQLAlchemy AsyncEngine instance (for async operations).
            session_factory: Optional custom async session factory.
            sync_engine: Optional sync Engine for sync operations.
            sync_session_factory: Optional custom sync session factory.
        """
        self.engine = engine
        self.async_session_factory = session_factory or sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        self.sync_engine = sync_engine
        self.sync_session_factory = sync_session_factory or (
            sessionmaker(bind=sync_engine, expire_on_commit=False)
            if sync_engine
            else None
        )

    async def _init_db(self) -> None:
        """Initialize the database schema (async).

        This should be called once before using the backend.
        """
        async with self.engine.begin() as conn:  # type: ignore
            await conn.run_sync(Base.metadata.create_all)  # type: ignore

    def _init_db_sync(self) -> None:
        """Initialize the database schema (sync).

        This should be called once before using the backend with sync operations.
        """
        if self.sync_engine is None:
            raise RuntimeError("Sync engine not configured")
        Base.metadata.create_all(self.sync_engine)  # type: ignore

    @staticmethod
    def _serialize_messages(messages: list[Message]) -> list[dict[str, object]]:
        """Serialize messages for storage."""
        return [
            {
                "role": msg.role.value,
                "content": msg.content,
                "token_count": msg.token_count,
                "metadata": msg.metadata,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in messages
        ]

    @staticmethod
    def _serialize_summaries(summaries: list[Summary]) -> list[dict[str, object]]:
        """Serialize summaries for storage."""
        return [
            {
                "text": s.text,
                "span_start": s.span_start,
                "span_end": s.span_end,
                "compacted_at": s.compacted_at.isoformat(),
            }
            for s in summaries
        ]

    @staticmethod
    def _deserialize_conversation(
        orm_obj: object, conversation_id: int
    ) -> Conversation:
        """Deserialize an ORM object to a Conversation."""
        # Type ignore needed for dynamic ORM object
        orm_messages_json = getattr(orm_obj, "messages_json", [])
        orm_summaries_json = getattr(orm_obj, "summaries_json", [])

        # Deserialize messages
        messages = [
            Message(
                role=Role(msg["role"]),
                content=msg["content"],
                token_count=msg.get("token_count", 0),
                metadata=msg.get("metadata", {}),
                created_at=datetime.fromisoformat(msg["created_at"]),
            )
            for msg in orm_messages_json
        ]

        # Deserialize summaries
        summaries = [
            Summary(
                text=s["text"],
                span_start=s["span_start"],
                span_end=s["span_end"],
                compacted_at=datetime.fromisoformat(s["compacted_at"]),
            )
            for s in orm_summaries_json
        ]

        return Conversation(
            id=conversation_id,
            messages=messages,
            summaries=summaries,
        )

    # Sync versions
    def save(self, conversation: Conversation) -> None:
        """Save a conversation to the database (sync).

        Args:
            conversation: The conversation to save.
        """
        if self.sync_session_factory is None:
            asyncio.run(self.asave(conversation))
        else:
            with self.sync_session_factory() as session:
                from sqlalchemy import select

                messages_data = self._serialize_messages(conversation.messages)
                summaries_data = self._serialize_summaries(conversation.summaries)

                # Upsert
                stmt = (
                    ConversationORM.__table__.update()
                    .where(ConversationORM.id == conversation.id)
                    .values(
                        messages_json=messages_data,
                        summaries_json=summaries_data,
                        updated_at=datetime.now(),
                    )
                )

                result = session.execute(stmt)

                # If no rows were updated, insert
                if result.rowcount == 0:
                    orm_obj = ConversationORM(
                        id=conversation.id,
                        messages_json=messages_data,
                        summaries_json=summaries_data,
                    )
                    session.add(orm_obj)

                session.commit()

    def load(self, conversation_id: int) -> Conversation:
        """Load a conversation from the database (sync).

        Args:
            conversation_id: The ID of the conversation to load.

        Returns:
            The loaded conversation.

        Raises:
            KeyError: If the conversation does not exist.
        """
        if self.sync_session_factory is None:
            return asyncio.run(self.aload(conversation_id))
        else:
            with self.sync_session_factory() as session:
                from sqlalchemy import select

                stmt = select(ConversationORM).where(
                    ConversationORM.id == conversation_id
                )
                orm_obj = session.execute(stmt).scalar_one_or_none()

                if orm_obj is None:
                    raise KeyError(f"Conversation '{conversation_id}' not found")

                return self._deserialize_conversation(orm_obj, conversation_id)

    def delete(self, conversation_id: int) -> None:
        """Delete a conversation from the database (sync).

        Args:
            conversation_id: The ID of the conversation to delete.
        """
        if self.sync_session_factory is None:
            asyncio.run(self.adelete(conversation_id))
        else:
            with self.sync_session_factory() as session:
                from sqlalchemy import select

                stmt = select(ConversationORM).where(
                    ConversationORM.id == conversation_id
                )
                orm_obj = session.execute(stmt).scalar_one_or_none()

                if orm_obj:
                    session.delete(orm_obj)
                    session.commit()

    def exists(self, conversation_id: int) -> bool:
        """Check if a conversation exists in the database (sync).

        Args:
            conversation_id: The ID of the conversation to check.

        Returns:
            True if the conversation exists, False otherwise.
        """
        if self.sync_session_factory is None:
            return asyncio.run(self.aexists(conversation_id))
        else:
            with self.sync_session_factory() as session:
                from sqlalchemy import select

                stmt = (
                    select(ConversationORM)
                    .where(ConversationORM.id == conversation_id)
                    .limit(1)
                )
                result = session.execute(stmt)
                return result.scalar_one_or_none() is not None

    # Async versions
    async def asave(self, conversation: Conversation) -> None:
        """Save a conversation to the database (async).

        Args:
            conversation: The conversation to save.
        """
        async with self.async_session_factory() as session:
            messages_data = self._serialize_messages(conversation.messages)
            summaries_data = self._serialize_summaries(conversation.summaries)

            # Upsert
            stmt = (
                ConversationORM.__table__.update()
                .where(ConversationORM.id == conversation.id)
                .values(
                    messages_json=messages_data,
                    summaries_json=summaries_data,
                    updated_at=datetime.now(),
                )
            )

            result = await session.execute(stmt)

            # If no rows were updated, insert
            if result.rowcount == 0:
                orm_obj = ConversationORM(
                    id=conversation.id,
                    messages_json=messages_data,
                    summaries_json=summaries_data,
                )
                session.add(orm_obj)

            await session.commit()

    async def aload(self, conversation_id: int) -> Conversation:
        """Load a conversation from the database (async).

        Args:
            conversation_id: The ID of the conversation to load.

        Returns:
            The loaded conversation.

        Raises:
            KeyError: If the conversation does not exist.
        """
        async with self.async_session_factory() as session:
            from sqlalchemy import select

            stmt = select(ConversationORM).where(ConversationORM.id == conversation_id)
            result = await session.execute(stmt)
            orm_obj = result.scalar_one_or_none()

            if orm_obj is None:
                raise KeyError(f"Conversation '{conversation_id}' not found")

            return self._deserialize_conversation(orm_obj, conversation_id)

    async def adelete(self, conversation_id: int) -> None:
        """Delete a conversation from the database (async).

        Args:
            conversation_id: The ID of the conversation to delete.
        """
        async with self.async_session_factory() as session:
            from sqlalchemy import select

            stmt = select(ConversationORM).where(ConversationORM.id == conversation_id)
            result = await session.execute(stmt)
            orm_obj = result.scalar_one_or_none()

            if orm_obj:
                await session.delete(orm_obj)
                await session.commit()

    async def aexists(self, conversation_id: int) -> bool:
        """Check if a conversation exists in the database (async).

        Args:
            conversation_id: The ID of the conversation to check.

        Returns:
            True if the conversation exists, False otherwise.
        """
        async with self.async_session_factory() as session:
            from sqlalchemy import select

            stmt = (
                select(ConversationORM)
                .where(ConversationORM.id == conversation_id)
                .limit(1)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None


__all__ = ["SQLAlchemyBackend", "ConversationORM", "Base"]

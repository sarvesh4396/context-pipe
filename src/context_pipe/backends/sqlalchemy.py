from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Engine, String
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

from context_pipe import AbstractBackend
from context_pipe.schemas import (
    Conversation,
    Message,
    Role,
    Summary,
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
    """SQLAlchemy backend for storing conversations in SQL databases."""

    def __init__(
        self,
        engine: AsyncEngine,
        session_factory: sessionmaker | None = None,
        sync_engine: Engine | None = None,
        sync_session_factory: sessionmaker | None = None,
        conversation_id: int | None = None,
    ) -> None:
        super().__init__(conversation_id)
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
        """Initialize the database schema (async)."""
        async with self.engine.begin() as conn:  # type: ignore
            await conn.run_sync(Base.metadata.create_all)  # type: ignore

    def _init_db_sync(self) -> None:
        """Initialize the database schema (sync)."""
        if self.sync_engine is None:
            raise RuntimeError("Sync engine not configured")
        Base.metadata.create_all(self.sync_engine)  # type: ignore

    @staticmethod
    def _serialize_messages(messages: list[Message]) -> list[dict[str, object]]:
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
        orm_messages_json = getattr(orm_obj, "messages_json", [])
        orm_summaries_json = getattr(orm_obj, "summaries_json", [])

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

    def create(self) -> Conversation:
        pass

    def save(self, conversation: Conversation) -> Conversation:
        pass

    def load(self, conversation_id: int | None = None) -> Conversation:
        pass

    def delete(self, conversation_id: int | None = None) -> None:
        pass

    def exists(self, conversation_id: int | None = None) -> bool:
        pass

    def update_token_counts(self, conversation_id: int | None = None) -> None:
        pass

    def add_message(
        self, message: Message, conversation_id: int | None = None
    ) -> Message:
        pass

    def get_messages(self, conversation_id: int | None = None) -> list[Message]:
        pass

    def add_summary(
        self, summary: Summary, conversation_id: int | None = None
    ) -> Summary:
        pass

    def get_summaries(self, conversation_id: int | None = None) -> list[Summary]:
        pass

    async def acreate(self) -> Conversation:
        pass

    async def asave(self, conversation: Conversation) -> Conversation:
        pass

    async def aload(self, conversation_id: int | None = None) -> Conversation:
        pass

    async def adelete(self, conversation_id: int | None = None) -> None:
        pass

    async def aexists(self, conversation_id: int | None = None) -> bool:
        pass

    async def aupdate_token_counts(self, conversation_id: int | None = None) -> None:
        pass

    async def aadd_message(
        self, message: Message, conversation_id: int | None = None
    ) -> Message:
        pass

    async def aget_messages(self, conversation_id: int | None = None) -> list[Message]:
        pass

    async def aadd_summary(
        self, summary: Summary, conversation_id: int | None = None
    ) -> Summary:
        pass

    async def aget_summaries(self, conversation_id: int | None = None) -> list[Summary]:
        pass


__all__ = ["SQLAlchemyBackend", "ConversationORM", "Base"]

from sqlalchemy import UUID as SqlUUID, DateTime, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID, uuid4
import datetime

from star.models import Base
from star.transcribe.state import VideoState

LANGUAGE_LENGTH = 8
NAME_LENGTH = 256
PATH_LENGTH = 96


class Video(Base):
    __tablename__ = 'videos'

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[UUID] = mapped_column(SqlUUID(), nullable=False, unique=True, default=uuid4)
    created: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=False), nullable=False, default=datetime.datetime.now)
    title: Mapped[str] = mapped_column(String(NAME_LENGTH), nullable=False)
    state: Mapped[VideoState] = mapped_column(nullable=False, default=VideoState.PENDING)
    transcript: Mapped[int | None] = mapped_column(ForeignKey('transcriptions.id'), nullable=True)


class Transcription(Base):
    __tablename__ = 'transcriptions'

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[UUID] = mapped_column(SqlUUID(), nullable=False, unique=True, default=uuid4)
    created: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=False), nullable=False, default=datetime.datetime.now)
    video_id: Mapped[int] = mapped_column(ForeignKey('videos.id'), nullable=False)
    language: Mapped[str] = mapped_column(String(LANGUAGE_LENGTH), nullable=False)
    path: Mapped[str] = mapped_column(String(PATH_LENGTH), nullable=False)

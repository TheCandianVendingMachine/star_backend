from sqlalchemy import UUID as SqlUUID, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID, uuid4
import datetime

from star.models import Base
from star.transcribe.state import VideoState

NAME_LENGTH = 256
PATH_LENGTH = 96


class Video(Base):
    __tablename__ = 'videos'

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[UUID] = mapped_column(SqlUUID(), nullable=False, unique=True, default=uuid4())
    title: Mapped[str] = mapped_column(String(NAME_LENGTH), nullable=False)
    state: Mapped[VideoState] = mapped_column(nullable=False, default=VideoState.PENDING)
    date_transcribed: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=False), nullable=True)
    transcription_path: Mapped[str] = mapped_column(String(PATH_LENGTH), nullable=True)

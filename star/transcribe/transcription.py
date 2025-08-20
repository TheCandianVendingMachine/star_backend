from sqlalchemy.exc import SQLAlchemyError
from pathlib import Path
import logging

from star.state import State
from star.models.transcribe import Video, Transcription
from star.error import DbError
from star.transcribe.language import Language

logger = logging.getLogger(__name__)


class TranscriptionStore:
    def create_transcript(self, state: State, video: Video, language: Language, subtitle_path: Path):
        try:
            logger.info(f'Creating transcription for video "{video.title}" in language "{language}"')
            with state.Session.begin() as session:
                transcription = Transcription(video_id=video.id, language=language, path=str(subtitle_path))
                session.add(transcription)
                session.commit()
                session.expunge(transcription)
            return transcription
        except SQLAlchemyError as e:
            logger.error(f'Failed to create transcription for video "{video.title}" in language "{language}"')
            raise DbError() from e

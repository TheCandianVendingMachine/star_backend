from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from pathlib import Path
from uuid import UUID
import logging

from star.state import State
from star.models.transcribe import Video, Transcription
from star.error import DbError, TranscriptNotFoundError
from star.transcribe.language import Language

logger = logging.getLogger('star.video')


class TranscriptionStore:
    def create_transcript(self, state: State, video: Video, language: Language, subtitle_path: Path):
        try:
            logger.info(f'Creating transcription for video "{video.title}" in language "{language}"')
            with state.Session.begin() as session:
                transcription = Transcription(language=language, path=str(subtitle_path))
                session.add(transcription)
                session.commit()
                session.expunge(transcription)
            return transcription
        except SQLAlchemyError as e:
            logger.error(f'Failed to create transcription for video "{video.title}" in language "{language}"')
            raise DbError() from e
    
    def get_transcript_by_uuid(self, state: State, uuid: UUID) -> Transcription:
        with state.Session.begin() as session:
            logger.info(f'Fetching transcription with UUID "{uuid}"')
            query = select(Transcription).where(Transcription.uuid == uuid)
            transcription = session.scalar(query)
            if transcription is None:
                raise TranscriptNotFoundError(uuid)
            session.expunge(transcription)
            return transcription

from sqlalchemy import update, select
from sqlalchemy.exc import SQLAlchemyError
from pathlib import Path
import logging
from uuid import UUID

from star.state import State
from star.models.transcribe import Video, Transcription
from star.transcribe.state import VideoState
from star.transcribe.metadata import VideoMetadata
from star.error import DbError, VideoNotFoundError

logger = logging.getLogger(__name__)


class VideoStore:
    def create_video(self, state: State, video_metadata: VideoMetadata) -> Video:
        try:
            logger.info(f'Creating video with title "{video_metadata.title}"')
            with state.Session.begin() as session:
                video = Video(title=video_metadata.title, state=VideoState.PENDING)
                session.add(video)
                session.commit()
                session.expunge(video)
            return video
        except SQLAlchemyError as e:
            logger.error(f'Failed to create video with title "{video_metadata.title}"')
            raise DbError() from e

    def update_video_state(self, state: State, video: Video, video_state: VideoState):
        with state.Session.begin() as session:
            logger.info(f'Updating video state for video "{video.title}" to "{video_state}"')
            try:
                session.execute(update(Video).where(Video.id == video.id).values(state=video_state))
                session.commit()
            except SQLAlchemyError as e:
                logger.error(f'Failed to update video state for video "{video.title}" to "{video_state}"')
                raise DbError() from e

    def link_transcription(self, state: State, video: Video, transcript: Transcription, transcription_path: Path):
        with state.Session.begin() as session:
            logger.info(f'Linking transcription path "{transcription_path}" to video "{video.title}"')
            try:
                session.execute(update(Video).where(Video.id == video.id).values(transcript=transcript.id))
                session.commit()
            except SQLAlchemyError as e:
                logger.error(f'Failed to link transcription path "{transcription_path}" to video "{video.title}"')
                raise DbError() from e

    def get_video_from_uuid(self, state: State, uuid: UUID) -> Video:
        with state.Session.begin() as session:
            logger.info(f'Fetching video with UUID "{uuid}"')
            video = session.scalar(select(Video).where(Video.uuid == uuid))
            if not video:
                logger.error(f'Video with UUID "{uuid}" not found')
                raise VideoNotFoundError(uuid)
            session.expunge(video)
        return video

    def get_all_videos(
        self, state: State, count: int, offset_id: int, filter: list[VideoState] = []
    ) -> list[tuple[Video, Transcription | None]]:
        count = max(1, min(100, count))  # Ensure count is at least 1
        offset = max(0, offset_id)
        with state.Session.begin() as session:
            logger.info(f'Fetching all videos and their transcripts, if applicable. (Count: {count}. Offset: {offset})')
            query = select(Video, Transcription | None).join(Transcription, Transcription.id == Video.transcript, isouter=True)
            if filter:
                query = query.where(Video.state.in_(filter))
            videos = session.scalars(query.order_by(Video.id).offset(offset).limit(count)).fetchall()
            videos = list(videos)
            session.expunge_all()
        return list(videos)

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
from star.events import ServerEvent

logger = logging.getLogger('star.video')


class VideoStore:
    def create_video(self, state: State, video_metadata: VideoMetadata) -> Video:
        try:
            logger.info(f'Creating video with title "{video_metadata.title}"')
            with state.Session.begin() as session:
                video = Video(title=video_metadata.title, state=VideoState.PENDING)
                session.add(video)
                session.flush()
                session.expunge(video)
            return video
        except SQLAlchemyError as e:
            logger.error(f'Failed to create video with title "{video_metadata.title}"')
            raise DbError() from e

    def update_video_state(self, state: State, video: Video, video_state: VideoState):
        video_title = video.title
        with state.Session.begin() as session:
            logger.info(f'Updating video state for video "{video_title}" to "{video_state}"')
            try:
                session.add(video)
                video.state = video_state
                session.flush()
            except SQLAlchemyError as e:
                logger.error(f'Failed to update video state for video "{video_title}" to "{video_state}"')
                raise DbError() from e
            finally:
                session.expunge(video)

        state.broker.publish(ServerEvent.VIDEO_STATE_CHANGE, {'uuid': video.uuid, 'state': video_state})

    def link_transcription(self, state: State, video: Video, transcript: Transcription, transcription_path: Path):
        with state.Session.begin() as session:
            logger.info(f'Linking transcription path "{transcription_path}" to video "{video.title}"')
            try:
                session.add(video)
                session.add(transcript)
                video.transcript = transcript.id
                session.flush()
            except SQLAlchemyError as e:
                logger.error(f'Failed to link transcription path "{transcription_path}" to video "{video.title}"')
                raise DbError() from e
            finally:
                session.expunge(video)
                session.expunge(transcript)

    def get_video_from_uuid(self, state: State, uuid: UUID) -> tuple[Video, Transcription | None]:
        with state.Session.begin() as session:
            logger.info(f'Fetching video with UUID "{uuid}"')
            query = select(Video, Transcription).join(Transcription, Transcription.id == Video.transcript, isouter=True)
            video, transcript = session.execute(query.where(Video.uuid == uuid)).all()[0]
            if not video:
                logger.error(f'Video with UUID "{uuid}" not found')
                raise VideoNotFoundError(uuid)
            session.expunge_all()
        return video, transcript

    def get_all_videos(
        self, state: State, count: int, offset_id: int, filter: list[VideoState] = []
    ) -> list[tuple[Video, Transcription | None]]:
        count = max(1, min(100, count))  # Ensure count is at least 1
        offset = max(0, offset_id)
        with state.Session.begin() as session:
            logger.info(f'Fetching all videos and their transcripts, if applicable. (Count: {count}. Offset: {offset})')
            query = select(Video, Transcription).join(Transcription, Transcription.id == Video.transcript, isouter=True)
            if filter:
                query = query.where(Video.state.in_(filter))
            videos = list(session.execute(query.order_by(Video.id.desc())).all())
            session.expunge_all()
        return list(videos)

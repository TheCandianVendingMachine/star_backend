from star.response import WebResponse, Created, JsonResponse
from star.web_utils import define_async_api
from star.subprocess.ffprobe import ffprobe
from star.subprocess.ffmpeg import ffmpeg
from star.subprocess.transcribe import transcribe
from star.transcribe.video import VideoStore
from star.transcribe.metadata import VideoMetadata
from star.transcribe.state import VideoState
from star.transcribe.transcription import TranscriptionStore
from star.transcribe.language import Language
from star.models.transcribe import Video
from star.error import ServerError, InvalidFileFormat
from star.state import State
from star.environment import ENVIRONMENT
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import logging
import dataclasses

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class TranscriptReturn:
    uuid: str
    create_date: str
    language: str


@dataclasses.dataclass
class VideoReturn:
    uuid: str
    create_date: str
    title: str
    state: str
    transcription: TranscriptReturn | None = None


class VideoApi:
    async def _transcribe(self, state: State, video: Video, audio_file: Path, processing_directory: TemporaryDirectory):
        try:
            logger.info(f'Starting transcription for video "{video.title}" with audio file "{audio_file}"')
            VideoStore().update_video_state(state, video, VideoState.PROCESSING)
            await transcribe.acall(audio_file)
            logger.info(f'Transcription for video "{video.title}" completed')
            transcript = Path(processing_directory.name) / audio_file.with_suffix('.srt').name
            transcript.rename(ENVIRONMENT.transcript_folder() / transcript.name)

            logger.info(f'Linking transcription for video "{video.title}" to database')
            db_transcript = TranscriptionStore().create_transcript(state, video, Language.ENGLISH, transcript)

            VideoStore().link_transcription(state, video, db_transcript, transcript)
            VideoStore().update_video_state(state, video, VideoState.COMPLETED)
            logger.info(f'Video "{video.title}" transcription linked to DB')
        except ServerError as e:
            VideoStore().update_video_state(state, video, VideoState.FAILED)
            logger.error(f'Failed to transcribe video "{video.title}": {e}')

    @define_async_api
    async def upload_video(self, state: State, video_file: Path) -> WebResponse:
        logger.info(f'Uploading video file: {video_file} to server')
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Move the uploaded file to a temporary directory for processing
            temp_video_file = temp_path / video_file.name
            video_file.rename(temp_video_file)

            # Generate ffprobe metadata
            json_file = temp_video_file.with_suffix('.ffprobe.json')
            logger.info(f'Generating metadata to {json_file}')
            await ffprobe.acall(video_file, show_format=True, show_error=True, output_format='json', o=json_file)

            # If there was an error with ffprobe, ffmpeg has no chance
            metadata = json.loads(json_file.read_text())
            if 'error' in metadata:
                raise InvalidFileFormat()

            audio_file = video_file.with_suffix('.mp3')
            logger.info(f'Extracting audio from {video_file} to {audio_file}')
            await ffmpeg.acall(
                audio_file,
                i=video_file,
                vn=True,
                acodec='copy',
            )

            metadata = VideoMetadata(title=video_file.stem)
            video = VideoStore().create_video(state, metadata)

            processing_directory = TemporaryDirectory()
            audio_file = audio_file.rename(processing_directory / audio_file.name)
            from star.server import app

            app.add_background_task(VideoApi._transcribe, self, state, video, audio_file, processing_directory)
        return Created(str(video.uuid))

    @define_async_api
    async def get_videos(self, state: State, count: int, offset: int) -> JsonResponse:
        videos = VideoStore().get_all_videos(state, count, offset)

        video_responses = []
        for video, transcript in videos:
            video_responses.append(
                VideoReturn(
                    uuid=str(video.uuid),
                    create_date=str(video.created),
                    title=video.title,
                    state=video.state,
                    transcription=TranscriptReturn(
                        uuid=str(transcript.uuid), create_date=str(transcript.created), language=transcript.language
                    )
                    if transcript
                    else None,
                )
            )
        return JsonResponse({'videos': video_responses})

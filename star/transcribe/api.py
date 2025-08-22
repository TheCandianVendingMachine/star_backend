from star.response import WebResponse, Created, JsonResponse, SeeOther, Ok
from star.web_utils import define_async_api, define_sse_api
from star.subprocess.ffprobe import ffprobe
from star.subprocess.ffmpeg import ffmpeg
from star.subprocess.transcribe import transcribe
from star.transcribe.video import VideoStore
from star.transcribe.metadata import VideoMetadata
from star.transcribe.state import VideoState
from star.transcribe.transcription import TranscriptionStore
from star.transcribe.language import Language
from star.models.transcribe import Video
from star.error import ServerError, InvalidFileFormat, TranscriptNotFoundError
from star.state import State
from star.environment import ENVIRONMENT
from star.web_event import BaseEvent
from star.events import ServerEvent
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID
from collections.abc import AsyncIterator
from werkzeug.utils import secure_filename
import json
import logging
import dataclasses
import asyncio
import shutil
import re

logger = logging.getLogger('star.video')


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


class VideoEvent(BaseEvent):
    def __init__(self, data: VideoReturn):
        self.event = 'update'
        self.namespace = 'video'
        self._data = data
        self.id = data.uuid
        super().__init__()
    
    def data(self):
        return json.dumps(dataclasses.asdict(self._data))

class VideoEventEnd(VideoEvent):
    def __init__(self, data: VideoReturn):
        super().__init__(data)
        self.event = 'update-end'


class VideoApi:
    async def _transcribe(self, state: State, video_file: Path, video: Video):
        try:
            # Generate ffprobe metadata
            json_file = video_file.with_suffix('.ffprobe.json')
            logger.info(f'Generating metadata to {json_file}')
            await ffprobe.acall(str(video_file), show_format=True, show_error=True, output_format='json', o=str(json_file), loglevel='error')

            # If there was an error with ffprobe, ffmpeg has no chance
            logger.info(f'Reading metadata from {json_file}')
            metadata = json.loads(json_file.read_text())
            if 'error' in metadata:
                raise InvalidFileFormat()


            with TemporaryDirectory(dir=str(ENVIRONMENT.data_folder())) as processing_directory:
                audio_file = Path(processing_directory) / video_file.with_suffix('.aac').name
                logger.info(f'Extracting audio from {video_file} to {audio_file}')
                await ffmpeg.acall(
                    str(audio_file),
                    i=str(video_file),
                    vn=True,
                    acodec='copy',
                    loglevel='error'
                )

                logger.info(f'Starting transcription for video "{video.title}" with audio file "{audio_file}"')
                VideoStore().update_video_state(state, video, VideoState.PROCESSING)
                await transcribe.acall(str(audio_file))
                logger.info(f'Transcription for video "{video.title}" completed')
                transcript = Path(processing_directory) / audio_file.with_suffix('.srt').name
            
                idx = 0
                while True:
                    test_path = ENVIRONMENT.transcript_folder() / transcript.name
                    if idx > 0:
                        test_path = ENVIRONMENT.transcript_folder() / f'{transcript.stem}_{idx}.srt'

                    if not test_path.exists():
                        transcript = transcript.rename(test_path)
                        break

                    idx = idx + 1

            logger.info(f'Linking transcription for video "{video.title}" to database')
            db_transcript = TranscriptionStore().create_transcript(state, video, Language.ENGLISH, transcript)

            VideoStore().link_transcription(state, video, db_transcript, transcript)
            VideoStore().update_video_state(state, video, VideoState.COMPLETED)
            logger.info(f'Video "{video.title}" transcription linked to DB')
            logger.info(f'Removing temporary video file: {video_file}')
            video_file.unlink()
            logger.info(f'Video transcript complete and ready')
            state.broker.publish(
                ServerEvent.VIDEO_TRANSCRIPT_COMPLETED, {'uuid': video.uuid, 'transcript': db_transcript.uuid, 'title': video.title}
            )
        except ServerError as e:
            VideoStore().update_video_state(state, video, VideoState.FAILED)
            logger.error(f'Failed to transcribe video "{video.title}":\n{e}')
        except Exception as e:
            VideoStore().update_video_state(state, video, VideoState.FAILED)
            logger.error(f'Failed to transcribe video "{video.title}":\n{e}')
            raise e

    @define_async_api
    async def upload_video(self, state: State, video_file: Path) -> WebResponse:
        logger.info(f'Uploading video file: {video_file} to server')

        metadata = VideoMetadata(title=video_file.stem)
        video = VideoStore().create_video(state, metadata)

        logger.info(f'Created video entry in database with UUID: {video.uuid}')
        from star.server import app
        app.add_background_task(VideoApi._transcribe, self, state, video_file, video)

        logger.info(f'Video file {video_file} is being processed in the background...')
        state.broker.publish(ServerEvent.VIDEO_UPLOADED, {'uuid': video.uuid, 'title': video.title})
        return SeeOther(f'/video/{video.uuid}')

    @define_async_api
    async def upload_chunk(self, state: State, file_data: bytes, filename: str, chunk_index: int, total_chunks: int, chunk_uuid: str) -> WebResponse:
        try:
            # Create a unique filename for this upload session
            upload_folder = ENVIRONMENT.upload_folder()
            safe_filename = secure_filename(filename)
            chunk_folder = upload_folder / f"chunks_{chunk_uuid}"
            chunk_folder.mkdir(exist_ok=True)
            
            # Write the chunk to disk
            chunk_file = chunk_folder / f"chunk_{chunk_index:06d}"
            chunk_file.write_bytes(file_data)
            
            logger.info(f'Written chunk {chunk_index + 1}/{total_chunks} for file {safe_filename}')
            
            # Check if all chunks have been received
            received_chunks = len(list(chunk_folder.glob("chunk_*")))
            
            if received_chunks == total_chunks:
                # All chunks received, combine them
                final_file_path = upload_folder / safe_filename
                
                # Handle duplicate filenames
                counter = 1
                while final_file_path.exists():
                    name_parts = safe_filename.rsplit('.', 1)
                    if len(name_parts) == 2:
                        final_file_path = upload_folder / f"{name_parts[0]}_{counter}.{name_parts[1]}"
                    else:
                        final_file_path = upload_folder / f"{safe_filename}_{counter}"
                    counter += 1
                
                # Combine chunks in order
                with open(final_file_path, 'wb') as final_file:
                    for i in range(total_chunks):
                        chunk_file = chunk_folder / f"chunk_{i:06d}"
                        if chunk_file.exists():
                            final_file.write(chunk_file.read_bytes())
                        else:
                            raise ServerError(f"Missing chunk {i} for file {safe_filename}")
                
                # Clean up chunk files
                shutil.rmtree(chunk_folder)
                
                logger.info(f'Successfully assembled file {final_file_path} from {total_chunks} chunks')
                
                # Process the complete file
                return await self.upload_video(state, final_file_path)
            else:
                # More chunks expected
                return Ok(f'Chunk {chunk_index + 1}/{total_chunks} received')
        except Exception as e:
            logger.error(f'Failed to process chunk {chunk_index} for file {filename}: {e}')
            return WebResponse(status=500, response=f'Failed to process chunk {chunk_index + 1}')

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
        return JsonResponse({'videos': [dataclasses.asdict(response) for response in video_responses]})

    @define_sse_api
    async def stream_video(self, state: State, uuid: UUID) -> AsyncIterator[VideoEvent]:
        while True:
            video, transcript = VideoStore().get_video_from_uuid(state, uuid)
            video_metadata = VideoReturn(
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

            yield VideoEvent(video_metadata)

            if video.state in [VideoState.COMPLETED, VideoState.FAILED]:
                break
            await asyncio.sleep(5)
        yield VideoEventEnd(video_metadata)
        StopAsyncIteration

    @define_async_api
    async def get_transcript_file(self, state: State, *, transcript_id: UUID | None = None, video_id: UUID | None = None) -> bytes:
        if transcript_id:
            logger.info(f'Attempting to fetch transcript via its UUID: {transcript_id}')
            transcript = TranscriptionStore().get_transcript_by_uuid(state, transcript_id)
            transcript_path = Path(transcript.path)
            with open(transcript_path, 'rb') as f:
                return WebResponse(
                    status=200,
                    headers={
                        'Content-Type': 'text/plain',
                        'Content-Disposition': f'attachment; filename="{transcript_path.name}"'
                    },
                    response=f.read()
                )
        elif video_id:
            logger.info(f'Attempting to fetch transcript via a video UUID: {video_id}')
            _, transcript = VideoStore().get_video_from_uuid(state, video_id)
            if transcript is None:
                raise TranscriptNotFoundError(f'Video ID: {video_id}')
            transcript_path = Path(transcript.path)
            with open(transcript_path, 'rb') as f:
                return WebResponse(
                    status=200,
                    headers={
                        'Content-Type': 'text/plain',
                        'Content-Disposition': f'attachment; filename="{transcript_path.name}"'
                    },
                    response=f.read()
                )
        else:
            raise TranscriptNotFoundError('No transcript or video ID provided')

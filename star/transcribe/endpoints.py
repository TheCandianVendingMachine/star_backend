import logging
from uuid import UUID
from quart import Blueprint, request, render_template_string
from typing import AsyncIterator
from werkzeug.utils import secure_filename

from star.environment import ENVIRONMENT
from star.web_utils import url_endpoint, html_endpoint, sse_endpoint
from star.response import WebResponse, HtmlResponse, ServerSentEventResponse
from star.state import State
from star.transcribe.api import VideoApi
from star.error import UploadError
from star.events import ServerEvent


logger = logging.getLogger('star.video')


def define_transcribe(api: Blueprint, sse: Blueprint, app: Blueprint):
    @api.post('/video')
    @url_endpoint
    async def upload_video() -> WebResponse:
        logger.info('Received video upload request')
        files = await request.files
        logger.info('File downloaded')

        if 'file' not in files:
            logger.error('No file part in the request')
            return UploadError('No file part in the request').as_response_code()

        file = files['file']
        filename = secure_filename(file.filename)
        save_path = ENVIRONMENT.upload_folder() / filename
        logger.info(f'Uploading video file to {save_path}')
        await file.save(save_path)
        return await VideoApi().upload_video(State.state, save_path)

    @sse.get('/video/<uuid:uuid>')
    @sse_endpoint
    async def stream_video(uuid: UUID) -> AsyncIterator[ServerSentEventResponse]:
        async for event in VideoApi().stream_video(State.state, uuid):
            yield event

    @api.get('/transcript/<uuid:transcript_uuid>')
    @url_endpoint
    async def download_transcript(transcript_uuid: UUID) -> WebResponse:
        logger.info(f'Requested download of transcript with UUID: {transcript_uuid}')
        return await VideoApi().get_transcript_file(State.state, transcript_id=transcript_uuid)

    @app.get('/video')
    @html_endpoint(template_path='videos/home.html', title='Videos', expire_event=ServerEvent.VIDEO_STATE_CHANGE)
    async def video_homepage(html: str) -> HtmlResponse:
        return await render_template_string(
            html
        )

    @app.get('/video/upload')
    @html_endpoint(template_path='videos/upload.html', title='Video Upload')
    async def video_upload(html: str) -> HtmlResponse:
        return await render_template_string(
            html
        )

    @app.get('/video/<uuid>')
    @html_endpoint(template_path='videos/video.html', title='Video', expire_event=ServerEvent.VIDEO_STATE_CHANGE)
    async def show_video_info(html:str, uuid: str) -> HtmlResponse:
        return await render_template_string(
            html,
            video={
                'uuid': uuid
            }
        )

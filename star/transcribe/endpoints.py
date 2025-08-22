import logging
import datetime
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
        logger.info('Received chunked video upload request')
        form = await request.form
        files = await request.files
        
        if 'file' not in files:
            logger.error('No file part in the request')
            return UploadError('No file part in the request').as_response_code()
        
        file = files['file']
        filename = form.get('filename', file.filename)
        chunk_index = int(form.get('dzchunkindex', 0))
        total_chunks = int(form.get('dztotalchunkcount', 1))
        chunk_uuid = form.get('dzuuid', '')
        
        file_data = file.read()
        
        logger.info(f'Received chunk {chunk_index + 1}/{total_chunks} for file {filename}')
        return await VideoApi().upload_chunk(
            State.state, 
            file_data, 
            filename, 
            chunk_index, 
            total_chunks, 
            chunk_uuid
        )

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
        all_videos = (await VideoApi().get_videos(State.state, count=100, offset=0)).contained_json
        for video in all_videos['videos']:
            date_string = video['create_date'].split('.')[0]
            video['create_date'] = str(datetime.datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S'))
        return await render_template_string(
            html,
            videos=all_videos['videos']
        )

    @app.get('/video/upload')
    @html_endpoint(template_path='videos/upload.html', title='Video Upload')
    async def video_upload(html: str) -> HtmlResponse:
        return await render_template_string(
            html
        )

    @app.get('/video/<uuid>')
    @html_endpoint(template_path='videos/video.html', title='Video', cache=False)
    async def show_video_info(html:str, uuid: str) -> HtmlResponse:
        return await render_template_string(
            html,
            video={
                'uuid': uuid
            }
        )

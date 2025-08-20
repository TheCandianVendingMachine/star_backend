import logging
from quart import Blueprint, request
from werkzeug.utils import secure_filename

from star.environment import ENVIRONMENT
from star.web_utils import url_endpoint
from star.response import WebResponse
from star.state import State
from star.transcribe.api import VideoApi
from star.error import UploadError


logger = logging.getLogger(__name__)


def define_transcribe(api: Blueprint):
    @api.post('/')
    @url_endpoint
    async def upload_video() -> WebResponse:
        files = await request.files

        if 'file' not in files:
            logger.error('No file part in the request')
            return UploadError('No file part in the request').as_response_code()

        file = files['file']
        filename = secure_filename(file.filename)
        save_path = ENVIRONMENT.upload_folder() / filename
        logger.info(f'Uploading video file to {save_path}')
        await file.save(save_path)
        return await VideoApi().upload_video(State.state, save_path)

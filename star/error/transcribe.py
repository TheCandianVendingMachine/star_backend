from star.error.base import ServerError
from typing import Any


class TranscribeError(ServerError):
    def __init__(self, message: str):
        super().__init__(f'Failed to transcribe video: {message}')


class UploadError(TranscribeError):
    def __init__(self):
        super().__init__('Could not upload')


class VideoNotFoundError(TranscribeError):
    def status(self) -> int:
        return 404

    def __init__(self, idx: Any):
        super().__init__(f'Could not find video with "{idx}"')

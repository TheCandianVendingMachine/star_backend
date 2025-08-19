from star.response import WebResponse, Created, Ok
from pathlib import Path


class VideoApi:
    def upload_video(self, video_file: Path) -> WebResponse:
        return Created()

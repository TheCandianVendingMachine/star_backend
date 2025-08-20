from enum import StrEnum


class VideoState(StrEnum):
    PENDING = 'Pending Processing'
    PROCESSING = 'Processing Transcript'
    COMPLETED = 'Completed!'
    FAILED = 'Failed'

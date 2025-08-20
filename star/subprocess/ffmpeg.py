from star.subprocess.command import Command, define_process
import logging

logger = logging.getLogger('star.command.ffprobe')


class Ffmpeg(Command):
    COMMAND = 'ffmpeg'

    KEYWORD_PREFIX = '-'
    KEYWORD_ARGUMENTS = {
        'i': str,
        'vn': None,
        'acodec': str,
        'loglevel': str
    }
    POSITIONAL_ARGUMENTS = (str,)

    def _map_stderr(result: str):
        logger.error(f'ffmpeg stderr: {result}')

    def _map_stdout(result: str):
        logger.info(f'ffmpeg stdout: {result}')


ffmpeg = define_process(Ffmpeg)

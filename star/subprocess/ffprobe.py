from star.subprocess.command import Command, define_process
import logging

logger = logging.getLogger('star.command.ffprobe')


class Ffprobe(Command):
    COMMAND = 'ffprobe'

    KEYWORD_PREFIX = '-'
    KEYWORD_ARGUMENTS = {
        'show_format': None,
        'show_error': None,
        'output_format': str,
        'o': str,
        'loglevel': str
    }
    POSITIONAL_ARGUMENTS = (str,)

    def _map_stderr(result: str):
        logger.error(f'ffprobe stderr: {result}')

    def _map_stdout(result: str):
        logger.info(f'ffprobe stdout: {result}')

ffprobe = define_process(Ffprobe)

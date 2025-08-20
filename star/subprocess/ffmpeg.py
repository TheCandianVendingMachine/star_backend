from star.subprocess.command import Command, define_process


class Ffmpeg(Command):
    COMMAND = 'ffmpeg'

    KEYWORD_PREFIX = '-'
    KEYWORD_ARGUMENTS = {
        'i': str,
        'vn': None,
        'acodec': str,
    }
    POSITIONAL_ARGUMENTS = (str,)


ffmpeg = define_process(Ffmpeg)

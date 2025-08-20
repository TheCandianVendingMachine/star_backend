from star.subprocess.command import Command, define_process


class Ffprobe(Command):
    COMMAND = 'ffprobe'

    KEYWORD_PREFIX = '-'
    KEYWORD_ARGUMENTS = {
        'show_format': None,
        'show_error': None,
        'output_format': str,
        'o': str,
    }
    POSITIONAL_ARGUMENTS = (str,)


ffprobe = define_process(Ffprobe)

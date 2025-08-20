from pathlib import Path
from star.subprocess.command import Command, define_process


class Transcribe(Command):
    RUNNER = 'uv run python'
    COMMAND_PATHS = [Path('./scripts')]
    COMMAND = 'transcribe.py'

    POSITIONAL_ARGUMENTS = (str,)


transcribe = define_process(Transcribe)

import shutil
import os


def can_call_as_command(program: str, paths: list[str] | None = None) -> str:
    paths_to_check = None
    if paths:
        paths_to_check = f'{os.pathsep}'.join(paths)

    path = shutil.which(program, path=paths_to_check)
    if path:
        return path
    return ''

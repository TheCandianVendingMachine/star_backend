from star.error.base import ServerError


class CacheMiss(ServerError):
    def status(self) -> int:
        return 404


class L1CacheMiss(CacheMiss):
    def __init__(self, key: str):
        super().__init__(f'L1 Cache miss for key: {key}')

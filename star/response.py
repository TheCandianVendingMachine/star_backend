from quart import Response
from werkzeug.datastructures.headers import Headers
from dataclasses import dataclass
from typing import Self
from collections.abc import AsyncGenerator
import json


class WebResponse(Response):
    def content_type(self) -> str:
        return 'text/plain'

    def headers(self) -> dict[str, str]:
        return {}

    def raise_if_unsuccessful(self) -> Self:
        if self.status_code >= 400:
            if self.exception is not None:
                raise self.exception
            else:
                from star.error import BwServerError

                raise BwServerError(status=self.status_code, message='An error occurred for unknown reasons.')
        return self

    def __init__(self, status: int, headers: dict = {}, response='', from_exception: Exception | None = None, **kwargs):  # ty: ignore[invalid-type-form]
        self.exception = from_exception
        headers.update(self.headers())
        lower_headers = {key.lower(): value for key, value in headers.items()}
        if 'content-type' not in lower_headers:
            lower_headers['content-type'] = self.content_type()

        super().__init__(
            response=response,
            status=status,
            headers=Headers([(k, v) for k, v in lower_headers.items()]),
            mimetype=self.content_type(),
            **kwargs,
        )


class Ok(WebResponse):
    def __init__(self, data: str = ''):
        super().__init__(200, response=data)


class Created(WebResponse):
    def __init__(self, data: str = ''):
        super().__init__(201, response=data)


class Exists(WebResponse):
    def __bool__(self):
        return self.exists

    def __init__(self, exists: bool = True):
        super().__init__(status=200 if exists else 409, response='Exists' if exists else 'Does not exist')
        self.exists = exists


class DoesNotExist(Exists):
    def __init__(self):
        super().__init__(False)


class JsonResponse(WebResponse):
    def content_type(self) -> str:
        return 'application/json'

    def __init__(self, json_payload: dict, headers: dict = {}, status=200):
        contained_status = json_payload.pop('status', None)
        if contained_status is None:
            contained_status = status
        self.contained_json = json_payload
        super().__init__(status=contained_status, headers=headers, response=json.dumps(json_payload))


class HtmlResponse(WebResponse):
    def content_type(self) -> str:
        return 'text/html'

    def __init__(self, html: str, headers: dict = {}):
        super().__init__(status=200, headers=headers, response=html)


@dataclass(kw_only=True)
class WebEvent:
    event: str
    data: str | dict = ''
    id: str | None = None
    retry: int | None = None

    def encode(self) -> bytes:
        data = f'event: {self.event}\ndata: {json.dumps(self.data)}\n'
        if self.id is not None:
            data += f'id: {self.id}\n'
        if self.retry is not None:
            data += f'retry: {self.retry}\n'
        data += '\n'
        return data.encode('utf-8')


class ServerSentEventResponse(WebResponse):
    def content_type(self) -> str:
        return 'text/event-stream'

    def headers(self) -> dict[str, str]:
        return {
            'Cache-Control': 'no-cache',
            'Transfer-Encoding': 'chunked',
        }

    @classmethod
    async def from_async_generator(cls, async_generator: AsyncGenerator[WebEvent]) -> AsyncGenerator[Self]:
        async def async_generator_wrapper() -> AsyncGenerator[bytes]:
            async for event in async_generator:
                yield event.encode()

        response = cls(status=200, response=async_generator_wrapper())
        response.timeout = None  # Disable timeout for SSE
        return response

from enum import StrEnum
from typing import Any
from collections.abc import Callable


class ServerEvent(StrEnum):
    TEST_EVENT = 'test_event'
    VIDEO_UPLOADED = 'upload'
    VIDEO_STATE_CHANGE = 'video state changed'
    VIDEO_TRANSCRIPT_COMPLETED = 'video transcript completed'


class Broker:
    def __init__(self):
        self.subscribers = {}
        self.global_subscribers = []

    def subscribe_all(self, callback: Callable[[ServerEvent, Any], None]):
        self.global_subscribers.append(callback)

    def subscribe(self, event: ServerEvent, callback: Callable[[ServerEvent, Any], None]):
        if event not in self.subscribers:
            self.subscribers[event] = []
        self.subscribers[event].append(callback)

    def publish(self, event: ServerEvent, data=None):
        if event in self.subscribers:
            for callback in self.subscribers[event]:
                callback(event, data)

        for callback in self.global_subscribers:
            callback(event, data)

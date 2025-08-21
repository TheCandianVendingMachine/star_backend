from star.settings import GLOBAL_CONFIGURATION
from star.environment import ENVIRONMENT, Local

import os
import logging
from typing import Any

PRODUCTION_LOG_CONFIG = {
    'root': 'INFO',
    'quart.app': 'INFO',
    'star': 'INFO',
    'star.cache': 'INFO',
    'star.video': 'INFO',
    'star.command.ffmpeg': 'INFO',
    'star.command.ffprobe': 'INFO',
}


class NoHealthcheckFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        allow = record.getMessage().find('/healthcheck') == -1
        return allow


def config() -> dict[str, Any]:
    if not os.path.exists('./logs'):
        os.makedirs('./logs')
    return {
        'version': 1,
        'filters': {
            'no_healthcheck': {
                '()': NoHealthcheckFilter,
            }
        },
        'formatters': {
            'default': {'format': '[%(asctime)s] [%(module)s] %(levelname)s: %(message)s', 'datefmt': '%Y-%m-%d %H:%M:%S'}
        },
        'handlers': {
            'wsgi': {
                'class': 'logging.StreamHandler',
                'stream': 'ext://flask.logging.wsgi_errors_stream',
                'formatter': 'default',
                'filters': ['no_healthcheck']
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': 'logs/server.log',
                'backupCount': int(GLOBAL_CONFIGURATION.get('log_backup_count', 3)),
                'maxBytes': int(GLOBAL_CONFIGURATION.get('single_log_size', 1 * 1024 * 1024)),
                'filters': ['no_healthcheck']
            },
            'ffmpeg': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': 'logs/ffmpeg.log',
                'backupCount': int(GLOBAL_CONFIGURATION.get('log_backup_count', 3)),
                'maxBytes': int(GLOBAL_CONFIGURATION.get('single_log_size', 1 * 1024 * 1024)),
            },
            'ffprobe': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': 'logs/ffprobe.log',
                'backupCount': int(GLOBAL_CONFIGURATION.get('log_backup_count', 3)),
                'maxBytes': int(GLOBAL_CONFIGURATION.get('single_log_size', 1 * 1024 * 1024)),
            },
        },
        'root': {
            'level': 'DEBUG' if isinstance(ENVIRONMENT, Local) else PRODUCTION_LOG_CONFIG['root'],
            'handlers': ['wsgi', 'file'],
        },
        'loggers': {
            'uvicorn.access': {
                'level': 'DEBUG' if isinstance(ENVIRONMENT, Local) else PRODUCTION_LOG_CONFIG['quart.app'],
                'handlers': ['wsgi', 'file'],
            },
            'quart.app': {
                'level': 'DEBUG' if isinstance(ENVIRONMENT, Local) else PRODUCTION_LOG_CONFIG['quart.app'],
                'handlers': ['wsgi', 'file'],
            },
            'star': {
                'level': 'DEBUG' if isinstance(ENVIRONMENT, Local) else PRODUCTION_LOG_CONFIG['star'],
                'handlers': ['wsgi', 'file'],
            },
            'star.cache': {
                'level': 'DEBUG' if isinstance(ENVIRONMENT, Local) else PRODUCTION_LOG_CONFIG['star.cache'],
                'handlers': ['wsgi', 'file'],
            },
            'star.video': {
                'level': 'DEBUG' if isinstance(ENVIRONMENT, Local) else PRODUCTION_LOG_CONFIG['star.video'],
                'handlers': ['wsgi', 'file'],
            },
            'star.command.ffmpeg': {
                'level': 'DEBUG' if isinstance(ENVIRONMENT, Local) else PRODUCTION_LOG_CONFIG['star.command.ffmpeg'],
                'handlers': ['wsgi', 'ffmpeg'],
            },
            'star.command.ffprobe': {
                'level': 'DEBUG' if isinstance(ENVIRONMENT, Local) else PRODUCTION_LOG_CONFIG['star.command.ffprobe'],
                'handlers': ['wsgi', 'ffprobe'],
            },
        },
    }

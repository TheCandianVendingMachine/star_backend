from star.settings import GLOBAL_CONFIGURATION
from star.environment import ENVIRONMENT, Local

import os
from typing import Any

PRODUCTION_LOG_CONFIG = {'root': 'INFO', 'quart.app': 'INFO', 'star.cache': 'INFO'}


def config() -> dict[str, Any]:
    if not os.path.exists('./logs'):
        os.makedirs('./logs')
    return {
        'version': 1,
        'formatters': {
            'default': {'format': '[%(asctime)s] [%(module)s] %(levelname)s: %(message)s', 'datefmt': '%Y-%m-%d %H:%M:%S'}
        },
        'handlers': {
            'wsgi': {
                'class': 'logging.StreamHandler',
                'stream': 'ext://flask.logging.wsgi_errors_stream',
                'formatter': 'default',
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': 'logs/server.log',
                'backupCount': int(GLOBAL_CONFIGURATION.get('log_backup_count', 3)),
                'maxBytes': int(GLOBAL_CONFIGURATION.get('single_log_size', 1 * 1024 * 1024)),
            },
        },
        'root': {
            'level': 'DEBUG' if isinstance(ENVIRONMENT, Local) else PRODUCTION_LOG_CONFIG['root'],
            'handlers': ['wsgi', 'file'],
        },
        'loggers': {
            'quart.app': {
                'level': 'DEBUG' if isinstance(ENVIRONMENT, Local) else PRODUCTION_LOG_CONFIG['quart.app'],
                'handlers': ['wsgi', 'file'],
            },
        },
    }

from quart import Quart
from logging.config import dictConfig

from star.log import config as log_config
from star.settings import GLOBAL_CONFIGURATION
from star.environment import ENVIRONMENT
from star.state import State
from star.endpoints import define as define_endpoints
import star.response  # noqa: F401

dictConfig(log_config())

app = Quart(__name__)
app.config.update(
    TESTING=False,
    PROPAGATE_EXCEPTIONS=False,
    MAX_CONTENT_LENGTH=50 * 1024 * 1024 * 1024,
)
state = State()
define_endpoints(app)


def run():
    if ENVIRONMENT.use_ssl():
        app.logger.info('using ssl...')
        ssl_ca_certs_path, ssl_certfile_path, ssl_keyfile_path = GLOBAL_CONFIGURATION.require(
            'ssl_ca_certs_path', 'ssl_certfile_path', 'ssl_keyfile_path'
        ).get()
    else:
        app.logger.info('ignoring ssl [STAGING/LOCAL ONLY]')
        ssl_ca_certs_path = None
        ssl_certfile_path = None
        ssl_keyfile_path = None

    app.logger.info('starting BW backend')
    app.logger.info('-' * 50)
    app.run(
        host='0.0.0.0',
        port=ENVIRONMENT.port(),
        ca_certs=ssl_ca_certs_path,
        certfile=ssl_certfile_path,
        keyfile=ssl_keyfile_path,
    )
    app.logger.info("that's all, folks")

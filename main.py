import star.server  # noqa: F401
from star.server import run
from star.environment import ENVIRONMENT
from star.log import config as log_config


def production():
    from star.settings import GLOBAL_CONFIGURATION
    import uvicorn

    if ENVIRONMENT.use_ssl():
        print('Starting production server with SSL')
        GLOBAL_CONFIGURATION.require('ssl_ca_certs_path', 'ssl_certfile_path', 'ssl_keyfile_path')
        ssl_ca_certs_path = GLOBAL_CONFIGURATION['ssl_ca_certs_path']
        ssl_certfile_path = GLOBAL_CONFIGURATION['ssl_certfile_path']
        ssl_keyfile_path = GLOBAL_CONFIGURATION['ssl_keyfile_path']
    else:
        print('Starting ASGI server !!WITHOUT!! SSL')
        ssl_ca_certs_path = None
        ssl_certfile_path = None
        ssl_keyfile_path = None

    uvicorn.run(
        'star.server:app',
        host='0.0.0.0',
        port=ENVIRONMENT.port(),
        ssl_keyfile=ssl_keyfile_path,
        ssl_certfile=ssl_certfile_path,
        ssl_ca_certs=ssl_ca_certs_path,
        log_config=log_config(),
        log_level='info',
    )
    print('thats all, folks')


def main():
    if ENVIRONMENT.deploy_asgi():
        production()
    else:
        run()


if __name__ == '__main__':
    main()

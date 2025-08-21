from star.settings import GLOBAL_CONFIGURATION as GC
from pathlib import Path


class Environment:
    def port(self) -> int:
        raise NotImplementedError()

    def use_ssl(self) -> bool:
        raise NotImplementedError()

    def db_connection(self) -> str:
        db_driver = GC.require('db_driver').get()
        if db_driver.split('+')[0] == 'sqlite':
            db_filepath = GC.require('db_filepath').get()
            return f'{db_driver}:///{db_filepath}'
        else:
            db_username, db_password, db_address = GC.require(
                'db_username', 'db_password', 'db_address'
            ).get()
            return f'{db_driver}://{db_username}:{db_password}@{db_address}'

    def deploy_asgi(self) -> bool:
        raise NotImplementedError()

    def use_subprocess(self) -> bool:
        raise NotImplementedError()

    def upload_folder(self) -> Path:
        return Path(GC.require('upload_folder').get())

    def model_folder(self) -> Path:
        return Path(GC.require('model_folder').get())

    def transcript_folder(self) -> Path:
        return Path(GC.require('transcript_output_dir').get())


class Local(Environment):
    def port(self) -> int:
        return 8080

    def use_ssl(self) -> bool:
        return False

    def deploy_asgi(self) -> bool:
        return False

    def use_subprocess(self) -> bool:
        return True


class Test(Environment):
    def port(self) -> int:
        return 8080

    def use_ssl(self) -> bool:
        return False

    def deploy_asgi(self) -> bool:
        return False

    def use_subprocess(self) -> bool:
        return False


class Staging(Environment):
    def port(self) -> int:
        return 8500

    def use_ssl(self) -> bool:
        return False

    def deploy_asgi(self) -> bool:
        return True

    def use_subprocess(self) -> bool:
        return True


class Production(Environment):
    def port(self) -> int:
        return 12239

    def use_ssl(self) -> bool:
        return False

    def deploy_asgi(self) -> bool:
        return True

    def use_subprocess(self) -> bool:
        return True


if GC.get('environment', 'local') == 'prod':
    ENVIRONMENT = Production()
elif GC.get('environment', 'local') == 'test':
    ENVIRONMENT = Test()
elif GC.get('environment', 'local') == 'staging':
    ENVIRONMENT = Staging()
else:
    ENVIRONMENT = Local()

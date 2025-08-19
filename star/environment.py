from star.settings import GLOBAL_CONFIGURATION as GC


class Environment:
    def port(self) -> int:
        raise NotImplementedError()

    def use_ssl(self) -> bool:
        raise NotImplementedError()

    def db_connection(self) -> str:
        GC.require('db_driver', 'db_username', 'db_password', 'db_address', 'db_name')
        return f'{GC["db_driver"]}://{GC["db_username"]}:{GC["db_password"]}@{GC["db_address"]}'

    def deploy_asgi(self) -> bool:
        raise NotImplementedError()

    def use_subprocess(self) -> bool:
        raise NotImplementedError()


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
        return True

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

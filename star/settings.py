from star.configuration import Configuration

GLOBAL_CONFIGURATION = None
if GLOBAL_CONFIGURATION is None:
    GLOBAL_CONFIGURATION = Configuration.load('settings.env')

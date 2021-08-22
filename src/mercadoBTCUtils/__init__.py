from os import getenv, path
from configparser import ConfigParser
from logging import getLogger, basicConfig, DEBUG, INFO, WARNING, ERROR, CRITICAL

# Reading the configuration file
config = ConfigParser()
configFilePath = getenv('MERCADOBTC_CFG_FILE')
if configFilePath is None:
    configFilePath = path.join(path.abspath(path.curdir), 'mercadoBTC.ini')
config.read(configFilePath)
if ('MercadoBitcoin' in config) is False:
    config['MercadoBitcoin'] = {
        'BaseUrl': 'https://www.mercadobitcoin.net',
        'TapiID': 'None',
        'TapiSecret': 'None'
    }
if ('Log' in config) is False:
    config['Log'] = {
        'FileStream': 'logs/mercadoBTC.log',
        'Level': 'INFO'
    }

# Initialize a default logger
log = getLogger(__name__)
logLevel = INFO
if config['Log']['Level'].upper() == 'DEBUG':
    logLevel = DEBUG
elif config['Log']['Level'].upper() == 'INFO':
    logLevel = INFO
elif config['Log']['Level'].upper() == 'WARNING':
    logLevel = WARNING
elif config['Log']['Level'].upper() == 'ERROR':
    logLevel = ERROR
elif config['Log']['Level'].upper() == 'CRITICAL':
    logLevel = CRITICAL

basicConfig(filename=config['Log']['FileStream'], level=logLevel, format='[%(asctime)s %(levelname)s - %(name)s-%(module)s %(filename)s-%(funcName)s (%(lineno)d)] %(message)s')

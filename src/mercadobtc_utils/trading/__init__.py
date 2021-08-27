from logging import getLogger, WARNING
getLogger("urllib3").setLevel(WARNING)
log = getLogger(__name__)

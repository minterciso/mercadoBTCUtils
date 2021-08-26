from urllib.parse import urlencode
from hashlib import sha512
from hmac import new

from mercadoBTCUtils import config
from mercadoBTCUtils.trading import log


class Operations:
    def __init__(self):
        pass

    def create_tapi_hmac(self, request_path: str, request_params: dict):
        """
        Creates a TAPI HMAC to be used on any communications.

        Parameters
        ----------
        request_path: str
            The requested Path to encode in the TAPI-HMAC

        request_params: dict
            A valid dictionary of parameters to encode on the TAPI-HMAC Url

        Returns
        -------
        The Hex digest of the TAPI-HMAC
        """
        log.info('Creating a TAPI-HMAC security code')
        log.debug('Using:')
        log.debug(f'- Request Path: {request_path}')
        log.debug(f'- Parameters  : {request_params}')
        encoded_parameters = urlencode(request_params)
        params_string = f'{request_path}?{encoded_parameters}'
        hmac_secret = new(config["MercadoBitcoin"]["TapiSecret"].encode(), digestmod=sha512)
        hmac_secret.update(params_string.encode())
        log.info('Done')
        return hmac_secret.hexdigest()



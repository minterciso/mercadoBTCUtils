from urllib.parse import urlencode
# from hashlib import sha512
# from hmac import new
import hmac
import hashlib
import datetime as dt
from requests import post

from mercadobtc_utils import config
from mercadobtc_utils.trading import log


class Operations:
    def __init__(self):
        pass

    @property
    def tapi_nonce(self):
        """
        Create a unique number to be used only once on each API request. For now, we are basically returning the current timestamp.

        Returns
        -------
        An integer to be used only once on each API call
        """
        return int(dt.datetime.now().timestamp())

    def __build_header(self, request_path: str, request_params: dict):
        """
        Creates a header based on the path and parameters passed

        Parameters
        ----------
        request_path: str
            The requested Path to encode in the TAPI-HMAC

        request_params: dict
            A valid dictionary of parameters to encode on the TAPI-HMAC Url

        Returns
        -------
        A Dictionary with a valid header to be used on all requests
        """
        log.info('Creating a TAPI-HMAC security code')
        log.debug('Using:')
        log.debug(f'- Request Path: {request_path}')
        log.debug(f'- Parameters  : {request_params}')
        encoded_parameters = urlencode(request_params)
        params_string = f'{request_path}?{encoded_parameters}'
        tapi_id = config['MercadoBitcoin']['TapiID']
        tapi_secret = config["MercadoBitcoin"]["TapiSecret"]
        hmac_secret = hmac.new(bytes(tapi_secret, encoding='utf-8'), digestmod=hashlib.sha512)
        hmac_secret.update(params_string.encode('utf-8'))
        tapi_mac = hmac_secret.hexdigest()
        log.info('Done')
        return {
            'Content-Type': 'application/x-www-form-urlencoded',
            'TAPI-ID': tapi_id,
            'TAPI-MAC': tapi_mac
        }

    def get_account_info(self, assets: list = None):
        """
        Query the TAPI and return the current account information

        Parameters
        ----------
        assets : list, default: None
            A list of assets to query, for instance ['brl', 'btc'] to retrieve only data related to Bitcoin and your own R$ Ballance. Please use the actually return value as the list parameters.

        Returns
        -------
        A dictionary with the account information as depicted on https://www.mercadobitcoin.com.br/trade-api/#get_account_info

        Notes
        -----
        It seems there's a bug on the Mercado BitCoin API when you send the assets as a parameter, due to this, we are making the asset filtering manually.
        """
        log.info('Requesting account information...')
        params = {
            'tapi_method': 'get_account_info',
            'tapi_nonce': self.tapi_nonce,
        }
        log.debug('Creating POST request...')
        endpoint = '/tapi/v3/'
        headers = self.__build_header(request_path=endpoint, request_params=params)
        url = f'{config["MercadoBitcoin"]["BaseUrl"]}{endpoint}'
        response = post(url=url, headers=headers, data=urlencode(params))
        if response.status_code != 200:
            log.error(f'Unable to get account information: {response.reason}')
            return None
        response_data = response.json()
        if response_data['status_code'] != 100:
            log.error(f'Unable to execute TAPI: {response_data["error_message"]}')
            return None
        response_data = response_data['response_data']
        return_data = None
        if assets:
            return_data = {key: value for key, value in response_data['balance'].items() if key in assets}
        else:
            return_data = response_data['balance']
        log.info('Done')
        return return_data



from urllib.parse import urlencode
import hmac
import hashlib
import datetime as dt
from requests import post
from json import dumps

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

    def __execute_tapi(self, params: dict):
        """
        Execute a TAPI transaction (anything on the endpoint /tapi/v3), and return the result.

        Parameters
        ----------
        params : dict
            The dictionary parameters

        Returns
        -------
        The dictionary with the results, or None if there's an error, and the error is logged on the logger.
        """
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
        log.info('Done')
        return response_data['response_data']

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
        response_data = self.__execute_tapi(params=params)
        return_data = None
        if assets:
            return_data = {key: value for key, value in response_data['balance'].items() if key in assets}
        else:
            return_data = response_data['balance']
        log.info('Done')
        return return_data

    def list_orders(self, coin_pair: str = 'BRLBTC', order_type: int = None, status_list: list = None, has_fills: bool = None, from_id: int = None, to_id: int = None, from_timestamp: int = None, to_timestamp: int = None):
        """
        Retrieve the owner of the TAPI ID orders list.

        Parameters
        ----------
        coin_pair : str, default: BRLBTC
            Retrieve only related the the passed coin pair, you can find the list of valid coin pairs on https://www.mercadobitcoin.com.br/trade-api/#list_orders

        order_type: int, optional
            Retrieve only the type of: 1-buy, 2-sell

        status_list: list of ints, optional
            Retrieve only orders in the status: 1-pending, 2-open, 3-canceled, 4-filled

        has_fills: bool, optional
            Retrieves only orders that has one or more executions

        from_id: int, optional
            Retrieves only orders starting from passed id

        to_id: int, optional
            Retrieves only orders up until passed id

        from_timestamp: int, optional
            Retrieves only orders starting from passed UNIX timestamp

        to_timestamp: int, optional
            Retrieves only orders ending from passed UNIX timestamp

        Returns
        -------
        A dictionary with a list of orders found, based on the filters passed.
        """
        log.info('Requesting all users orders')
        params = {
            'tapi_method': 'list_orders',
            'tapi_nonce': self.tapi_nonce,
            'coin_pair': coin_pair
        }
        log.debug('Sanitizing optional parameters...')
        if order_type is not None:
            params['order_type'] = order_type
        if status_list is not None:
            params['status_list'] = dumps(status_list)
        if has_fills is not None:
            params['has_fills'] = has_fills
        if from_id is not None:
            params['from_id'] = from_id
        if to_id is not None:
            params['to_id'] = to_id
        if from_timestamp is not None:
            params['from_timestamp'] = f'{from_timestamp}'
        if to_timestamp is not None:
            params['to_timestamp'] = f'{to_timestamp}'

        response_data = self.__execute_tapi(params=params)
        log.info('Done')
        return response_data

    def get_order(self, coin_pair: str, order_id: int):
        """
        Query the TAPI and return the order information composed by the pair coin_pair and order_id.

        Parameters
        ----------
        coin_pair: str
            The coin pair to find the order information, valid values can be found in https://www.mercadobitcoin.com.br/trade-api/#get_order

        order_id: int
            The order unique identifier for the specific coin.

        Returns
        -------
        The information of the order, if found.
        """
        log.info('Requesting information on a specific order')
        log.debug(f'- coin : {coin_pair}')
        log.debug(f'- order: {order_id}')
        params = {
            'tapi_method': 'get_order',
            'tapi_nonce': self.tapi_nonce,
            'coin_pair': coin_pair,
            'order_id': order_id
        }
        response_data = self.__execute_tapi(params=params)
        log.info('Done')
        return response_data

    def list_order_book(self, coin_pair: str, full: bool = False):
        """
        Returns (open) information from the order book regarding the specific coin pair.

        Parameters
        ----------
        coin_pair: str
            The coin to get the order book from

        full: bool, default: False
            If set to True, it'll return the last 500 orders for that coin, if set to False it'll return the last 20

        Returns
        -------
        The last order book orders for the specific coins. You can find better information in https://www.mercadobitcoin.com.br/trade-api/#list_orderbook.
        """
        log.info('Getting detailed information regarding the last orders')
        log.debug(f'- Coin: {coin_pair}')
        log.debug(f'- Full: {full}')
        params = {
            'tapi_method': 'list_orderbook',
            'tapi_nonce': self.tapi_nonce,
            'coin_pair': coin_pair,
            'full': 'true' if full else 'false'
        }
        response_data = self.__execute_tapi(params=params)
        log.info('Done')
        return response_data

    def place_buy_sell_order(self, buy: bool, coin_pair: str, quantity: float, limit_price: float, wait: bool = True):
        """
        Create a buy/sell order on the order book, with passed parameters.

        Parameters
        ----------
        buy: bool
            If set to True, we want to buy some coin, if set to False we want to sell.

        coin_pair: str
            The coin to buy.

        quantity: float
            The amount of the coin to buy.

        limit_price: float
            The value of the coin you want to buy from.

        wait: bool, default: True
            If set to True, wait for the order to be placed on the order book and return after this. Otherwise return asap.

        Returns
        -------
        A dictionary with the placed order parameter, as shown in https://www.mercadobitcoin.com.br/trade-api/#place_buy_order.
        """
        log.info('Placing a \'buy\' order.')
        log.debug(f'- Type : {"buy" if buy else "sell"}')
        log.debug(f'- Coin : {coin_pair}')
        log.debug(f'- Qtd  : {quantity}')
        log.debug(f'- Price: R$ {limit_price}')
        log.debug(f'- Wait : {wait}')
        method = 'place_buy_order' if buy else 'place_sell_order'
        params = {
            'tapi_method': method,
            'tapi_nonce': self.tapi_nonce,
            'coin_pair': coin_pair,
            'quantity': quantity,
            'limit_price': limit_price,
            'async': 'true' if wait else 'false'
        }
        response_data = self.__execute_tapi(params=params)
        log.info('Done')
        return response_data

    def cancel_order(self, coin_pair: str, order_id: int, wait: bool = False):
        """
        Cancel an open order on the order book, with passed parameters.

        Parameters
        ----------
        coin_pair: str
            The coin to buy.

        order_id: int
            The order # to cancel

        wait: bool, default: False
            If set to True, it'll wait for the return. Since this is a cancel method, we default this to False.

        Returns
        -------
        The order that was canceled. You can see more information on https://www.mercadobitcoin.com.br/trade-api/#cancel_order
        """
        log.info('Canceling an open order...')
        log.debug(f'- Coin   : {coin_pair}')
        log.debug(f'- Order #: {order_id}')
        log.debug(f'- Wait   : {wait}')
        params = {
            'tapi_method': 'cancel_order',
            'tapi_nonce': self.tapi_nonce,
            'coin_pair': coin_pair,
            'order_id': order_id,
            'async': 'true' if wait else 'false'
        }
        response_data = self.__execute_tapi(params=params)
        log.info('Done')
        return response_data

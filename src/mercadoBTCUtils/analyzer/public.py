import requests.exceptions
from requests import get
from pandas import DataFrame
from numpy import sqrt
import datetime as dt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error

from mercadoBTCUtils import config
from mercadoBTCUtils.analyzer import log


class BasicAnalysis:
    """
    This class is responsible for making the basic analysis of the public available information on MercadoBitcoin public
    APIs.

    Attributes
    ----------
    initialSummaryDate : Datetime
        The initial start date to download and analyze data

    endSummaryDate : Datetime
        The end start date (non inclusive) to download and analyze data

    summaryData : DataFrame
        The downloaded daily summary data, as a Pandas DataFrame
    """
    initialSummaryDate = None
    endSummaryDate = None
    __summaryData = None

    @property
    def summaryData(self):
        return self.__summaryData

    def __init__(self):
        pass

    def downloadSummaryData(self):
        """
        Downloads the data from the Mercado Bitcoin API Day Summary endpoint (api/BTC/day-summary).

        Notes
        -----
        This method uses a synchronized way of downloading the actual data, so it may take some time to complete. If there's
        a known error, it'll try for 3 times (and log the errors as they appear), on the 4th error it'll raise the Exception
        causing the error.
        """
        log.info('Downloading daily summary data')
        if self.initialSummaryDate is None:
            log.warning('Initial date is \'None\', configuring it as last 90 days data.')
            self.initialSummaryDate = (dt.datetime.now() - dt.timedelta(days=90)).date()
        if self.endSummaryDate is None:
            log.warning('End date is \'None\', configuring as yesterday.')
            self.endSummaryDate = (dt.datetime.now() - dt.timedelta(days=1)).date()
        log.debug(f'Initial Date: {self.initialSummaryDate}')
        log.debug(f'End Date    : {self.endSummaryDate}')
        numDays = (self.endSummaryDate-self.initialSummaryDate).days
        baseUrl = f'{config["MercadoBitcoin"]["BaseUrl"]}/api/BTC/day-summary/'
        data = []
        log.info(f'Getting last {numDays+1} summary data...')
        numTries = 0
        for i in range(numDays+1):
            queryDate = self.initialSummaryDate+dt.timedelta(days=i)
            try:
                log.debug(f'{queryDate.strftime("%Y-%m-%d")}...')
                url = f'{baseUrl}{queryDate.strftime("%Y/%m/%d/")}'
                response = get(url)
                if response.status_code != 200:
                    log.error(f'There was an error with the actual request: {response.reason}')
                    log.error('Aborting!')
                    raise
                else:
                    data.append((response.json()))
                numTries = 0
            except requests.exceptions.ConnectionError:
                if numTries < 3:
                    log.warning(f'We got a Connection Error for the {numTries+1} time, trying again...')
                else:
                    log.error('Too many Connection Errors, aborting.')
                    raise
        log.debug('Download complete, creating DataFrame...')
        self.__summaryData = DataFrame(data)
        log.info('Done')

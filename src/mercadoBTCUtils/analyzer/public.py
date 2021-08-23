import requests.exceptions
from requests import get
from pandas import DataFrame
from numpy import sqrt
from os import path
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
    initialSummaryDate : Date
                         The initial start date to download and analyze data. If not configured, it'll always be today - 90 days

    endSummaryDate : Date
                     The end start date (non inclusive) to download and analyze data. If not configured, it'll always be today - 1 day

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
        self.initialSummaryDate = (dt.datetime.now() - dt.timedelta(days=90)).date()
        self.endSummaryDate = (dt.datetime.now() - dt.timedelta(days=1)).date()

    def summaryToCSV(self, filePath: str):
        """
        Save the full summary data to the file pointed by filePath. If the file does not ends in .csv, this method will add it. If the summary is empty, it won't save the file and the method will return False.
        Any other error it'll raise the error

        Parameters
        ----------
        filePath : str
                   The file path location to save the summary data.

        Returns
        -------
        bool
             If there is something on the summary data, and the file is save successfully, it'll return True. If the summary data is empty or None, it'll return False. Any other error it'll raise the proper Exception.

        Notes
        -----
        The directory of the passed filePath should at least exists. This method does not create the directories.
        """
        log.info('Saving the summary data to a CSV file.')
        normalizedFilePath = path.normpath(filePath)
        if ('csv' in normalizedFilePath.lower().split('.')[-1]) is False:
            normalizedFilePath += '.csv'
        log.debug(f'File Path: {normalizedFilePath}')
        if self.summaryData is None:
            log.warning('Summary is None, maybe it wasn\'t run yet?')
            return False
        if len(self.summaryData) == 0:
            log.warning('No summary found.')
            return False
        self.__summaryData.to_csv(path_or_buf=normalizedFilePath, index=False)
        log.info('Done')

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
        log.debug(f'Initial Date: {self.initialSummaryDate}')
        log.debug(f'End Date    : {self.endSummaryDate}')
        numDays = (self.endSummaryDate-self.initialSummaryDate).days
        baseUrl = f'{config["MercadoBitcoin"]["BaseUrl"]}/api/BTC/day-summary/'
        data = []
        log.info(f'Getting last {numDays+1} days of summary data...')
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

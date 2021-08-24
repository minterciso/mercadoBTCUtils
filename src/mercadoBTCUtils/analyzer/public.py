import pandas as pd
import requests.exceptions
from requests import get
from pandas import DataFrame, to_datetime
from numpy import sqrt
from os import path
import datetime as dt
import seaborn as sns
import matplotlib.pyplot as plt

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

    summaryModel : sklearn summary model
                The trained summary model

    summaryDirection : bool
                If the average price is rising, this will return True, otherwise it'll return False
    """
    initialSummaryDate = None
    endSummaryDate = None
    __summaryData = None
    __summaryLRM = None

    @property
    def summaryData(self):
        return self.__summaryData

    @property
    def summaryModel(self):
        return self.__summaryLRM

    @property
    def summaryDirection(self):
        return True if self.__summaryData['avg_price'].iloc[-3:].diff().mean() > 0 else False

    def __init__(self):
        self.initialSummaryDate = (dt.datetime.now() - dt.timedelta(days=90)).date()
        self.endSummaryDate = dt.datetime.now().date()

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

    def downloadSummaryData(self, concatenate: bool = False):
        """
        Downloads the data from the Mercado Bitcoin API Day Summary endpoint (api/BTC/day-summary).

        Parameters
        ----------
        concatenate : bool, default: False
                      If this is set to True, then we'll concatenate the downloaded data with whatever was already downloaded/read.
                      The default if False, then it'll override with whatever already exists there

        Notes
        -----
        This method uses a synchronized way of downloading the actual data, so it may take some time to complete. If there's
        a known error, it'll try for 3 times (and log the errors as they appear), on the 4th error it'll raise the Exception
        causing the error.
        If the data was already downloaded or read using the readSummaryCSVData() method, it'll append the data on the existing
        summary.
        """
        log.info('Downloading daily summary data')
        log.debug(f'Initial Date: {self.initialSummaryDate}')
        log.debug(f'End Date    : {self.endSummaryDate}')
        numDays = (self.endSummaryDate-self.initialSummaryDate).days
        baseUrl = f'{config["MercadoBitcoin"]["BaseUrl"]}/api/BTC/day-summary/'
        data = []
        log.info(f'Getting last {numDays+1} days of summary data...')
        numTries = 0
        for i in range(numDays):
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
        df = DataFrame(data)
        log.debug('Calculating dates timestamp')
        df['tstamp'] = to_datetime(df['date'], format='%Y-%m-%d').apply(lambda x: x.timestamp())
        if concatenate is False:
            self.__summaryData = df.copy(True)
        else:
            if self.__summaryData is not None:
                self.__summaryData = pd.concat([self.__summaryData, df]).reset_index(drop=True)
            else:
                self.__summaryData = df.copy(deep=True)
        log.info('Done')

    def readSummaryCSVData(self, filePath: str):
        """
        Instead of downloading the data, you can read the data from a CSV file, that was created before with the method summaryToCSV().

        Parameters
        ----------
        filePath : str
                   Where the file is located
        """
        log.info('Reading a CSV file as a Daily Summary data')
        normalizedFilePath = path.normpath(filePath)
        log.debug(f'File: {normalizedFilePath}')
        self.__summaryData = pd.read_csv(normalizedFilePath)
        log.info('Done')

    def getBasicSummaryAnalysisPlots(self, calculatePairPlot: bool = False):
        """
        Create some basic analysis plots (average price, average volume, pair plot) and a described DataFrame from the summary data

        Parameters
        ----------
        calculatePairPlot : bool
                            If set to True, calculate the pair plot of the full summary dataset

        Returns
        -------
        A tuple with (average price plot figure, average volume plot figure, pair plot figure, describe DataFrame)
        """
        log.info('Creating some standard analysis plot, and DataFrame.')
        log.debug('Average Price')
        avgPriceLmPlot = sns.lmplot(data=self.__summaryData.reset_index(), x='index', y='avg_price', height=5, aspect=2)
        avgPriceLmPlot.set_xlabels('Measure')
        avgPriceLmPlot.set_ylabels('Average Price R$')
        avgPriceLmPlot.set(title='Average Price X Measure')
        avgPriceLmPlot.tight_layout()
        log.debug('Average Volume')
        avgVolumeLmPlot = sns.lmplot(data=self.__summaryData.reset_index(), x='index', y='volume', height=5, aspect=2)
        avgVolumeLmPlot.set_xlabels('Measure')
        avgVolumeLmPlot.set_ylabels('Average Price R$')
        avgVolumeLmPlot.set(title='Average Volume X Measure')
        avgVolumeLmPlot.tight_layout()
        pairPlot = None
        if calculatePairPlot:
            log.debug('Pair Plot')
            pairPlot = sns.pairplot(self.__summaryData)
            pairPlot.fig.suptitle('Summary Pair Plot', y=1)
            pairPlot.tight_layout()
        log.debug('Described DataFrame')
        describedSummaryData = self.__summaryData.describe()
        log.info('Done')
        return avgPriceLmPlot.fig, avgVolumeLmPlot.fig, pairPlot.fig if pairPlot is not None else None, describedSummaryData

    def trainSummary(self, testSize: float = 0.3, resultComparison: bool = False):
        """
        This method parses the read summary data and create a simple Linear Regression model to predict the average daily values.

        Parameters
        ----------
        testSize : float, default: 0.3
                   The % to keep from the data for testing the ML model

        resultComparison : bool, default: False
                   If this is set to True, then it'll create both a Comparison DataFrame, as well as 2 comparison graphs (one with realXpredicted value, another with %difference from real value)

        Returns
        -------
        A tuple with:
            model results: A dictionary with mae, mse, rmse, score and coefficient dataframe
            comparison dataframe: A DataFrame with the real and predicted values
            comparison plot: A plot with the real and predicted values
            difference plot: A plot with the % difference from the real values
        """
        log.info('Training a Linear Regression module to try to predict the average price, on a daily basis.')
        log.debug('Cleaning data...')
        X = self.__summaryData.drop(['date', 'avg_price', 'closing', 'lowest', 'highest', 'volume', 'amount', 'quantity', 'tstamp'], axis=1)
        y = self.__summaryData['avg_price']
        log.debug(f'Splitting with {testSize*100}% as a test base amount')
        XTrain, XTest, yTrain, yTest = train_test_split(X, y, test_size=testSize)
        log.debug('Creating Linear Regression model and fitting it...')
        self.__summaryLRM = LinearRegression()
        self.__summaryLRM.fit(XTrain, yTrain)
        log.debug('Testing against our test data')
        predictedTests = self.__summaryLRM.predict(XTest)
        predictedResults = {
            'mae': mean_absolute_error(yTest, predictedTests),
            'mse': mean_squared_error(yTest, predictedTests),
            'rmse': sqrt(mean_squared_error(yTest, predictedTests)),
            'score': self.__summaryLRM.score(XTest, yTest),
            'coeff': pd.DataFrame(self.__summaryLRM.coef_, X.columns, columns=['Coeff'])
        }
        log.info('Test results:')
        log.info(f'MAE:  {predictedResults["mae"]}')
        log.info(f'MSE:  {predictedResults["mse"]}')
        log.info(f'RMSE:  {predictedResults["rmse"]}')
        log.info(f'Score:  {predictedResults["score"]}')
        log.info(f'Coefficient DataFrame:\n{predictedResults["coeff"]}')
        df = None
        comparisonPlot = None
        pctDiffPlot = None
        if resultComparison:
            log.debug('Result comparison is set to true, creating a result comparison graph...')
            df = XTest.copy()
            df['real'] = yTest
            df['predicted'] = predictedTests
            df['diff'] = df['real'] - df['predicted']
            df['pctChange'] = df[['real', 'predicted']].pct_change(axis='columns')['predicted']
            comparisonPlot, ax = plt.subplots()
            ax.scatter(df.index, df['real'], label='real')
            ax.scatter(df.index, df['predicted'], label='predicted')
            plt.xlabel('Measure')
            plt.ylabel('Price R$')
            plt.title('Predicted Vs Real values')
            plt.legend()
            plt.tight_layout()
            plt.close(comparisonPlot)
            pctDiffPlot, ax = plt.subplots()
            ax.plot(df.sort_index().index, df.sort_index()['pctChange'], label='% Difference', marker='o')
            plt.grid()
            plt.xlabel('Measure')
            plt.ylabel('% Change')
            plt.ylim(-1.0, 1.0)
            plt.title('Difference % between real and predicted')
            plt.legend()
            plt.tight_layout()
            plt.close(pctDiffPlot)
        return predictedResults, df, comparisonPlot, pctDiffPlot

    def predictSummary(self, numDays: int = 1, useStd: bool = False, pctStdUsage: float = 0.1):
        """
        Use the trained summary model (based on the opening values) to predict the next numDays of average price.

        Notes
        -----
        Since we train the model based on the opening value, and we don't (yet maybe?) have a way to predict this, we are using the
        predicted average value as the starting point for the next day. That means that the precision will fall drastically for anything
        greater than 1 day. We try to improve this by adding 10% of the standard deviation of the opening parameter on the average value,
        but this is by far nothing mathematically proven to improve this. I'm actually doing this for kicks and wondering if this can improve
        or not.

        Parameters
        ----------
        numDays : int, default: 1
                    The amount of days to predict. 1 day is pretty precise, anything more than 3-4 days can loose a lot of precision.

        useStd : bool, default: False
                    If this is set to True, it'll try to add (or remove) 10% of the Standard Deviation of the opening value. This improves a little of
                    the precision for up until 3-4 days. Anything more then this, we need a better module. The decision to add or remove is based on the
                    direction of the last 2 average summary measures
        pctStdUsage : float, default: 0.1
                    The % of the STD to use when useStd is set to True.

        Returns
        -------
        A DataFrame with the predicted values
        """
        log.info(f'Trying to predict for {numDays} days from the last downloaded day.')
        if numDays > 1:
            log.warning('Using anything greater then 1 extra day can lead to very wrong predicted values.')
        lastKnownValues = self.summaryData[['date', 'opening']].iloc[-1]
        df = pd.DataFrame({'date': [lastKnownValues['date']], 'Average Price': [lastKnownValues['opening']]})
        startDate = dt.datetime.strptime(lastKnownValues['date'], '%Y-%m-%d').date()
        openingStd = self.summaryData.describe()['closing']['std']
        for i in range(1, numDays):
            predictDate = startDate + dt.timedelta(days=i)
            log.debug(f'Predicting for {predictDate.strftime("%Y-%m-%d")}...')
            avgPrice = df.iloc[-1]['Average Price']
            predictAvgPrice = self.__summaryLRM.predict(pd.DataFrame([avgPrice]))[0]
            if i > 0 and useStd:
                if self.summaryDirection:
                    predictAvgPrice += (openingStd * pctStdUsage)
                else:
                    predictAvgPrice -= (openingStd * pctStdUsage)
            df = df.append({'date': predictDate, 'Average Price': predictAvgPrice}, ignore_index=True).reset_index(drop=True)
        log.info('Done')
        return df

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

from mercadobtc_utils import config
from mercadobtc_utils.analyzer import log


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
    initial_summary_date = None
    end_summary_date = None
    __summary_data = None
    __summary_lrm = None

    @property
    def summary_data(self):
        return self.__summary_data

    @property
    def summary_model(self):
        return self.__summary_lrm

    @property
    def summary_direction(self):
        return True if self.__summary_data['avg_price'].iloc[-3:].diff().mean() > 0 else False

    def __init__(self):
        self.initial_summary_date = (dt.datetime.now() - dt.timedelta(days=90)).date()
        self.end_summary_date = dt.datetime.now().date()

    def summary_to_csv(self, file_path: str):
        """
        Save the full summary data to the file pointed by filePath. If the file does not ends in .csv, this method will add it. If the summary is empty, it won't save the file and the method will return False.
        Any other error it'll raise the error

        Parameters
        ----------
        file_path : str
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
        normalized_file_path = path.normpath(file_path)
        if ('csv' in normalized_file_path.lower().split('.')[-1]) is False:
            normalized_file_path += '.csv'
        log.debug(f'File Path: {normalized_file_path}')
        if self.summary_data is None:
            log.warning('Summary is None, maybe it wasn\'t run yet?')
            return False
        if len(self.summary_data) == 0:
            log.warning('No summary found.')
            return False
        self.__summary_data.to_csv(path_or_buf=normalized_file_path, index=False)
        log.info('Done')

    def download_summary_data(self, concatenate: bool = False):
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
        log.debug(f'Initial Date: {self.initial_summary_date}')
        log.debug(f'End Date    : {self.end_summary_date}')
        num_days = (self.end_summary_date - self.initial_summary_date).days
        base_url = f'{config["MercadoBitcoin"]["BaseUrl"]}/api/BTC/day-summary/'
        data = []
        log.info(f'Getting last {num_days+1} days of summary data...')
        num_tries = 0
        for i in range(num_days):
            query_date = self.initial_summary_date + dt.timedelta(days=i)
            try:
                log.debug(f'{query_date.strftime("%Y-%m-%d")}...')
                url = f'{base_url}{query_date.strftime("%Y/%m/%d/")}'
                response = get(url)
                if response.status_code != 200:
                    log.error(f'There was an error with the actual request: {response.reason}')
                    log.error('Aborting!')
                    raise
                else:
                    data.append((response.json()))
                num_tries = 0
            except requests.exceptions.ConnectionError:
                if num_tries < 3:
                    log.warning(f'We got a Connection Error for the {num_tries+1} time, trying again...')
                else:
                    log.error('Too many Connection Errors, aborting.')
                    raise
        log.debug('Download complete, creating DataFrame...')
        df = DataFrame(data)
        log.debug('Calculating dates timestamp')
        df['tstamp'] = to_datetime(df['date'], format='%Y-%m-%d').apply(lambda x: x.timestamp())
        if concatenate is False:
            self.__summary_data = df.copy(True)
        else:
            if self.__summary_data is not None:
                self.__summary_data = pd.concat([self.__summary_data, df]).reset_index(drop=True)
            else:
                self.__summary_data = df.copy(deep=True)
        log.info('Done')

    def read_summary_csv_data(self, filePath: str):
        """
        Instead of downloading the data, you can read the data from a CSV file, that was created before with the method summaryToCSV().

        Parameters
        ----------
        filePath : str
                   Where the file is located
        """
        log.info('Reading a CSV file as a Daily Summary data')
        normalized_file_path = path.normpath(filePath)
        log.debug(f'File: {normalized_file_path}')
        self.__summary_data = pd.read_csv(normalized_file_path)
        log.info('Done')

    def get_basic_summary_analysis_plots(self, calculate_pair_plot: bool = False):
        """
        Create some basic analysis plots (average price, average volume, pair plot) and a described DataFrame from the summary data

        Parameters
        ----------
        calculate_pair_plot : bool
                            If set to True, calculate the pair plot of the full summary dataset

        Returns
        -------
        A tuple with (average price plot figure, average volume plot figure, pair plot figure, describe DataFrame)
        """
        log.info('Creating some standard analysis plot, and DataFrame.')
        log.debug('Average Price')
        avg_price_lm_plot = sns.lmplot(data=self.__summary_data.reset_index(), x='index', y='avg_price', height=5, aspect=2)
        avg_price_lm_plot.set_xlabels('Measure')
        avg_price_lm_plot.set_ylabels('Average Price R$')
        avg_price_lm_plot.set(title='Average Price X Measure')
        avg_price_lm_plot.tight_layout()
        log.debug('Average Volume')
        avg_volume_lm_plot = sns.lmplot(data=self.__summary_data.reset_index(), x='index', y='volume', height=5, aspect=2)
        avg_volume_lm_plot.set_xlabels('Measure')
        avg_volume_lm_plot.set_ylabels('Average Price R$')
        avg_volume_lm_plot.set(title='Average Volume X Measure')
        avg_volume_lm_plot.tight_layout()
        pair_plot = None
        if calculate_pair_plot:
            log.debug('Pair Plot')
            pair_plot = sns.pairplot(self.__summary_data)
            pair_plot.fig.suptitle('Summary Pair Plot', y=1)
            pair_plot.tight_layout()
        log.debug('Described DataFrame')
        described_summary_data = self.__summary_data.describe()
        log.info('Done')
        return avg_price_lm_plot.fig, avg_volume_lm_plot.fig, pair_plot.fig if pair_plot is not None else None, described_summary_data

    def train_summary(self, test_size: float = 0.3, result_comparison: bool = False):
        """
        This method parses the read summary data and create a simple Linear Regression model to predict the average daily values.

        Parameters
        ----------
        test_size : float, default: 0.3
                   The % to keep from the data for testing the ML model

        result_comparison : bool, default: False
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
        X = self.__summary_data.drop(['date', 'avg_price', 'closing', 'lowest', 'highest', 'volume', 'amount', 'quantity', 'tstamp'], axis=1)
        y = self.__summary_data['avg_price']
        log.debug(f'Splitting with {test_size * 100}% as a test base amount')
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size)
        log.debug('Creating Linear Regression model and fitting it...')
        self.__summary_lrm = LinearRegression()
        self.__summary_lrm.fit(X_train, y_train)
        log.debug('Testing against our test data')
        predicted_tests = self.__summary_lrm.predict(X_test)
        predicted_results = {
            'mae': mean_absolute_error(y_test, predicted_tests),
            'mse': mean_squared_error(y_test, predicted_tests),
            'rmse': sqrt(mean_squared_error(y_test, predicted_tests)),
            'score': self.__summary_lrm.score(X_test, y_test),
            'coeff': pd.DataFrame(self.__summary_lrm.coef_, X.columns, columns=['Coeff'])
        }
        log.info('Test results:')
        log.info(f'MAE:  {predicted_results["mae"]}')
        log.info(f'MSE:  {predicted_results["mse"]}')
        log.info(f'RMSE:  {predicted_results["rmse"]}')
        log.info(f'Score:  {predicted_results["score"]}')
        log.info(f'Coefficient DataFrame:\n{predicted_results["coeff"]}')
        df = None
        comparison_plot = None
        pct_diff_plot = None
        if result_comparison:
            log.debug('Result comparison is set to true, creating a result comparison graph...')
            df = X_test.copy()
            df['real'] = y_test
            df['predicted'] = predicted_tests
            df['diff'] = df['real'] - df['predicted']
            df['pctChange'] = df[['real', 'predicted']].pct_change(axis='columns')['predicted']
            comparison_plot, ax = plt.subplots()
            ax.scatter(df.index, df['real'], label='real')
            ax.scatter(df.index, df['predicted'], label='predicted')
            plt.xlabel('Measure')
            plt.ylabel('Price R$')
            plt.title('Predicted Vs Real values')
            plt.legend()
            plt.tight_layout()
            plt.close(comparison_plot)
            pct_diff_plot, ax = plt.subplots()
            ax.plot(df.sort_index().index, df.sort_index()['pctChange'], label='% Difference', marker='o')
            plt.grid()
            plt.xlabel('Measure')
            plt.ylabel('% Change')
            plt.ylim(-1.0, 1.0)
            plt.title('Difference % between real and predicted')
            plt.legend()
            plt.tight_layout()
            plt.close(pct_diff_plot)
        return predicted_results, df, comparison_plot, pct_diff_plot

    def predict_summary(self, num_days: int = 1, use_std: bool = False, pct_std_usage: float = 0.1):
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
        num_days : int, default: 1
                    The amount of days to predict. 1 day is pretty precise, anything more than 3-4 days can loose a lot of precision.

        use_std : bool, default: False
                    If this is set to True, it'll try to add (or remove) 10% of the Standard Deviation of the opening value. This improves a little of
                    the precision for up until 3-4 days. Anything more then this, we need a better module. The decision to add or remove is based on the
                    direction of the last 2 average summary measures
        pct_std_usage : float, default: 0.1
                    The % of the STD to use when useStd is set to True.

        Returns
        -------
        A DataFrame with the predicted values
        """
        log.info(f'Trying to predict for {num_days} days from the last downloaded day.')
        if num_days > 1:
            log.warning('Using anything greater then 1 extra day can lead to very wrong predicted values.')
        last_known_values = self.summary_data[['date', 'opening']].iloc[-1]
        df = pd.DataFrame({'date': [last_known_values['date']], 'Average Price': [last_known_values['opening']]})
        start_date = dt.datetime.strptime(last_known_values['date'], '%Y-%m-%d').date()
        opening_std = self.summary_data.describe()['closing']['std']
        for i in range(1, num_days):
            predict_date = start_date + dt.timedelta(days=i)
            log.debug(f'Predicting for {predict_date.strftime("%Y-%m-%d")}...')
            avg_price = df.iloc[-1]['Average Price']
            predict_avg_price = self.__summary_lrm.predict(pd.DataFrame([avg_price]))[0]
            if i > 0 and use_std:
                if self.summary_direction:
                    predict_avg_price += (opening_std * pct_std_usage)
                else:
                    predict_avg_price -= (opening_std * pct_std_usage)
            df = df.append({'date': predict_date, 'Average Price': predict_avg_price}, ignore_index=True).reset_index(drop=True)
        log.info('Done')
        return df

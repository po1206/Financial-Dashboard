import pandas as pd
import requests
from datetime import datetime
import datetime as dt
import numpy as np
import asyncio
import websockets

class FinnhubConnector:

    def __init__(self, api_key, base_api_url='https://finnhub.io/api/v1/'):
        self.api_key = api_key
        self.base_api_url = base_api_url

    def get_north_american_stocks(self) -> pd.DataFrame:

        # call the API with appropriate parameters (free tier only gives access to North American stocks)
        df = pd.DataFrame(requests.get(f'{self.base_api_url}stock/symbol?exchange=US&token={self.api_key}').json())

        # sort alphabetically by symbol
        df = df.sort_values(['displaySymbol']).reset_index(drop=True)

        # tidy up the df and drop unnecessary columns and test rows
        df.drop(['symbol', 'symbol2', 'shareClassFIGI', 'isin'], axis=1, inplace=True)
        df.rename(columns={'currency': 'Currency', 'description': 'Description',
                           'displaySymbol': 'Symbol', 'figi': 'FIGI', 'mic': 'MIC', 'type': 'Type'}, inplace=True)
        df = df[df.Description != 'Test'].reset_index(drop=True)
        return df

    def look_up_stock(self, search_query: str) -> pd.DataFrame:

        # Query text can be symbol, name, isin, or cusip.
        search_results = pd.DataFrame(
            requests.get(f'{self.base_api_url}search?q={search_query}&token={self.api_key}').json())

        if len(search_results) == 0:
            raise ValueError(f'NOTHING FOUND FOR QUERY-> {search_query}')

        # make the dictionary values into a pandas df, drop unnecessary columns and tidy up the df
        search_results = search_results['result'].apply(pd.Series)
        search_results.drop('symbol', axis=1, inplace=True)
        search_results.rename(columns={'description': 'Description', 'displaySymbol': 'Symbol', 'type': 'Type'},
                              inplace=True)
        search_results.index.rename('Search results', inplace=True)
        return search_results

    def get_company_news(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        # start/end date format: yyyy-mm-dd -free tier only gives 1 year of records so the end date cannot
        # be more that one year behind current date, also the API call returns a df that goes back no more than
        # 240 records records away from the end date, so it is highly preferable to enter dates that
        # are only a few days apart
        # symbol: company symbol i.e 'AAPL'

        # make the API call with proper parameters and create a data frame
        df = pd.DataFrame(requests.get(
            f'{self.base_api_url}company-news?symbol={symbol}&from={start_date}&to={end_date}&token={self.api_key}').json())

        # return value error if the API call returns an empty data frame
        try:
            df.set_index(df['datetime'].apply(lambda x: datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M')),
                         inplace=True)
        except:
            raise ValueError(f'THERE IS NO DATA FOR-> {symbol} FROM {start_date} TO {start_date}')

        # rename the columns and sort by ascending date
        df.rename(columns={'category': 'Category', 'headline': 'Headline',
                           'id': 'ID', 'image': 'Image',
                           'related': 'Related to (symbol)',
                           'source': 'Source', 'summary': 'Summary', 'url': 'URL'}, inplace=True)
        df.drop(['datetime'], axis=1, inplace=True)
        df.index.rename('Datetime', inplace=True)
        df.sort_index(ascending=True, inplace=True)
        return df

    def get_basic_financials(self, symbol: str) -> pd.DataFrame:
        past_year = pd.DataFrame(
            requests.get(f'{self.base_api_url}stock/metric?symbol={symbol}&metric=all&token={self.api_key}').json())

        # create a dictionary that will later be updated with 3 different dataframes
        basic_financials = {}

        # create two dictionaries for annual and quarterly returns that are within cells of the
        # original df created from calling json()
        for fiscal in ['annual', 'quarterly']:
            try:
                fiscal_period = past_year['series'][fiscal]
            except:
                raise ValueError(f'THERE IS NO DATA FOR-> {symbol}')

            # drop the two rows from the original df as they will no longer be needed
            past_year.drop([fiscal], inplace=True)

            # created dfs out of the given dictionaries
            fiscal_df = pd.DataFrame({key: pd.Series(value) for key, value in fiscal_period.items()})

            #Create datetime list to set index for our data frame
            periods = []
            for i in fiscal_period.values():
                if len(i) == len(fiscal_df):
                    for d in i:
                        periods.append(d['period'])
                    break 
                        
            # clean up data cells to only leave dict values
            for col in fiscal_df.columns:
                fiscal_df[col] = fiscal_df[col].apply(lambda x: x.get('v') if type(x) == dict else np.nan)

            #Set index of the df as the earlier defined datetime periods
            fiscal_df.set_index([periods], inplace=True)

            # sort the dfs by ascending dates, rename index and update the empty dict with annual
            # quarterly dfs
            fiscal_df.index.rename('Datetime', inplace=True)
            fiscal_df.sort_index(ascending=True, inplace=True)
            basic_financials.update({fiscal: fiscal_df})

        # update the dict with original df outside of the loop
        basic_financials.update({'past_year': past_year})
        return basic_financials

    def get_earnings_surprises(self, symbol: str) -> pd.DataFrame:

        # make the API call with proper parameters and create a data frame
        df = pd.DataFrame(
            requests.get(f'{self.base_api_url}stock/earnings?symbol={symbol}&token={self.api_key}').json())

        try:
            df.set_index(df['period'], inplace=True)
        except:
            raise ValueError(f'THERE IS NO DATA FOR-> {symbol}')

        # rename columns, set datetime as index and sort by datetime
        df.rename(columns={'actual': 'Actual', 'estimate': 'Estimate', 'quarter': 'Quarter',
                           'surprise': 'Surprise', 'surprisePercent': 'Surprise percent', 'symbol': 'Symbol',
                           'year': 'Year'}, inplace=True)
        df.index.rename('Period', inplace=True)
        df.drop(['period'], axis=1, inplace=True)
        df.sort_index(ascending=True, inplace=True)
        return df

    def get_current_quote(self, symbol: str) -> pd.DataFrame:
        df = pd.DataFrame(requests.get(f'{self.base_api_url}quote?symbol={symbol}&token={self.api_key}').json(),
                          index=['Value'])

        # handles the case when the response is a dataframe with null values (no data)
        if df['t']['Value'] == 0:
            raise ValueError(f'THERE IS NO DATA FOR-> {symbol}')

        # convert date and time into readable format and tidy up the data frame
        df['t'] = datetime.utcfromtimestamp(df['t']['Value']).strftime('%Y-%m-%d %H:%M')
        df.rename(columns={'c': 'Current price', 'd': 'Change', 'dp': 'Percent change', 'h': 'High price of the day',
                           'l': 'Low price of the day', 'o': 'Open price of the day', 'pc': 'Previous close price',
                           't': 'Time'}, inplace=True)
        return df

    # static-method helper function that will be used more than once within
    # the class to convert date and time into UNIX format
    @staticmethod
    def convert_to_unix(date, time) -> int:
        given_date = f"{date}, {time}"
        formated_date = dt.datetime.strptime(given_date, "%Y-%m-%d, %H:%M:%S")
        return int(dt.datetime.timestamp(formated_date))

    # Supported resolution includes [1, 5, 15, 30, 60, D, W, M]. Some timeframes might not be available
    # depending on the exchange. Please specify the date in the following format: yyyy-mm-dd
    # time is an optional argument set to default 00:00:00
    def get_stock_candles(self, symbol: str, resolution: str, date_from: str, date_to: str, time_from='00:00:00',
                          time_to='00:00:00') -> pd.DataFrame:

        # make the API call with proper parameters and create a data frame
        try:
            df = pd.DataFrame(requests.get(
                f'{self.base_api_url}stock/candle?symbol={symbol}&resolution={resolution}&from={self.convert_to_unix(date_from, time_from)}&to={self.convert_to_unix(date_to, time_to)}&token={self.api_key}').json())
        except:
            raise ValueError(f"THERE IS NO DATA FOR-> {symbol} FROM {date_from} {time_from} TO {date_to} {time_to}")

        # convert date and time from UNIX back into readable format and tidy up the df
        df.set_index(df['t'].apply(lambda x: datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S')), inplace=True)
        df.rename(columns={'c': 'Close', 'h': 'High', 'l': 'Low', 'o': 'Open', 's': 'Status',
                           'v': 'Volume'}, inplace=True)
        df.index.rename('Datetime', inplace=True)
        df.drop(['t'], axis=1, inplace=True)
        return df

    def get_crypto_symbols(self, exchange: str) -> pd.DataFrame:
        # List of crypto exchanges for function input: ["FXPIG","KUCOIN","GEMINI","BITTREX","POLONIEX",
        # "HUOBI","BINANCEUS","COINBASE","BITFINEX","KRAKEN","HITBTC","OKEX","BITMEX","BINANCE"]
        crypto_symbols = pd.DataFrame(
            requests.get(f'{self.base_api_url}crypto/symbol?exchange={exchange}&token={self.api_key}').json())

        if len(crypto_symbols) == 0:
            raise ValueError(f'{exchange} IS NOT A VALID EXCHANGE')

        crypto_symbols.rename(
            columns={'description': 'Description', 'displaySymbol': 'Display symbol', 'symbol': 'Symbol'}, inplace=True)
        return crypto_symbols

    def get_crypto_candles(self, symbol: str, resolution: str, date_from: str, date_to: str, time_from='00:00:00',
                           time_to='00:00:00') -> pd.DataFrame:
        # Make sure that the symbol input is in the following format: 'EXCHANGE:SYMBOL' i.e 'BINANCE:BTCUSDT'
        # The list of symbols can be generated by calling get_crypto_symbols and would be in the 'Symbols'
        # column of the returned data frame

        # make the API call with proper parameters and create a data frame
        try:
            df = pd.DataFrame(requests.get(
                f'{self.base_api_url}crypto/candle?symbol={symbol}&resolution={resolution}&from={self.convert_to_unix(date_from, time_from)}&to={self.convert_to_unix(date_to, time_to)}&token={self.api_key}').json())
        except:
            raise ValueError(f"THERE IS NO DATA FOR-> {symbol} FROM {date_from} {time_from} TO {date_to} {time_to}")

        # convert date and time from UNIX back into readable format and tidy up the df
        df.set_index(df['t'].apply(lambda x: datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S')), inplace=True)
        df.rename(columns={'c': 'Close', 'h': 'High', 'l': 'Low', 'o': 'Open', 's': 'Status',
                           'v': 'Volume'}, inplace=True)
        df.index.rename('Datetime', inplace=True)
        df.drop(['t'], axis=1, inplace=True)
        return df

    def stream_websocket(self, symbol: str) -> pd.DataFrame:

        # Run the two lines of code below if you are using Jupyter Notebooks and/or get
        # the 'RuntimeError: This event loop is already running' error.

        # import nest_asyncio
        # nest_asyncio.apply()

        # Define an asynchronous function with websocket URL
        async def fetch_live():
            url = f'wss://ws.finnhub.io?token={self.api_key}'

            # Establish the websocket connection, send the live stock subscription  credentials
            # And wait for the response from the server
            async with websockets.connect(url) as ws:
                await ws.send('{"type":"subscribe","symbol":"' + symbol + '"}')

                # Puts the function in an infinite fetch loop in order to stream output. The live data frames
                # are stopped by pressing the 'interrupt kernel' button.
                while True:
                    # Wait for the response from the server and print the message
                    msg = await ws.recv()
                    print(msg)
                    print('')

        # Print 'connection closed' instead of throwing an error when the stream is interrupted
        try:
            asyncio.run(fetch_live())
        except KeyboardInterrupt:
            print('####### CONNECTION CLOSED #######')

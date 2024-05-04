import requests
from cryptography.hazmat.primitives.asymmetric import ed25519
from urllib.parse import urlparse, urlencode
import urllib
import json
import pandas as pd
import numpy as np
import datetime as dt
from forex_python.converter import CurrencyRates
import time
from enum import Enum
from Strategy import BollingerBandStrategy  # Import BollingerBandStrategy class from Strategy module

# These secret_key and api key are valid for Coinswitch only
secret_key_outer = 'd69afdb11286262561794897baccb253881b6896bfde71203fadfd78d5d004c4'
api_key = 'c17d863c6132e9726f0f377fd1ffbeb1ebbf5f75ea34c175c36cc373130c9772'

class OrderType(Enum):
    MARKET = 'market'
    LIMIT = 'limit'
    STOP_LOSS = 'stop_loss'
    STOP_LIMIT = 'stop_limit'

class AssetType(Enum):
    CRYPTO = 0
    STOCK = 1
    OPTIONS = 2

class CryptoTrading:
    '''
    Initializes the class with ticker to be traded
    and strategy to be applied
    '''
    def __init__(self, ticker):
        self.ticker = ticker
        self.position = 0
        self.entry_price = 0
        self.main_balance = 0
        self.total_quantity = 0
        # Create an empty DataFrame to store the tickers
        self.ticker_data = pd.DataFrame(columns=['timestamp', 'close', 'ma', 'stddev', 'lowerBand', 'upperBand', 'gain', 'loss', 'RSI', 'MAR', 'signal'])
        self.strategy = BollingerBandStrategy()

    def getValidKeys(self):
        params = {}

        endpoint = "/trade/api/v2/validate/keys"
        method = "GET"
        payload = {}

        unquote_endpoint = endpoint
        if method == "GET" and len(params) != 0:
            endpoint += ('&', '?')[urlparse(endpoint).query == ''] + urlencode(params)
            unquote_endpoint = urllib.parse.unquote_plus(endpoint)

        signature_msg = method + unquote_endpoint + json.dumps(payload, separators=(',', ':'), sort_keys=True)

        request_string = bytes(signature_msg, 'utf-8')
        secret_key_bytes = bytes.fromhex(secret_key_outer)
        secret_key = ed25519.Ed25519PrivateKey.from_private_bytes(secret_key_bytes)
        signature_bytes = secret_key.sign(request_string)
        signature = signature_bytes.hex()

        url = "https://coinswitch.co" + endpoint

        headers = {
            'Content-Type': 'application/json',
            'X-AUTH-SIGNATURE': signature,
            'X-AUTH-APIKEY': api_key
        }

        response = requests.request("GET", url, headers=headers, json=payload)
        print(response.json())

    '''
    Creates order - sell/buy, number of coins to buy, price at which order has to be placed, type of order 
    '''
    def createOrder(self, side, totalQuantity, price, orderType = OrderType.LIMIT):
        print("*****TICKER*****", self.ticker)
        print("*****SIDE*****", side)
        print("*****QUANTITY*****", totalQuantity)
        print("*****PRICE*****", price)
        print("*****ORDER*****", orderType)
        endpoint = "/trade/api/v2/order"
        method = "POST"
        payload = {
            "side": side,
            "symbol": self.ticker,
            "type": "limit",
            "price":price,
            "quantity": totalQuantity,
            "exchange": "c2c1"
        }
        print(payload)
        unquote_endpoint = endpoint
        if method == "GET" and len({}) != 0:
            endpoint += ('&', '?')[urlparse(endpoint).query == ''] + urlencode({})
            unquote_endpoint = urllib.parse.unquote_plus(endpoint)

        signature_msg = method + unquote_endpoint + json.dumps(payload, separators=(',', ':'), sort_keys=True)

        request_string = bytes(signature_msg, 'utf-8')
        secret_key_bytes = bytes.fromhex(secret_key_outer)
        secret_key = ed25519.Ed25519PrivateKey.from_private_bytes(secret_key_bytes)
        signature_bytes = secret_key.sign(request_string)
        signature = signature_bytes.hex()

        url = "https://coinswitch.co" + endpoint

        headers = {
            'Content-Type': 'application/json',
            'X-AUTH-SIGNATURE': signature,
            'X-AUTH-APIKEY': api_key
        }

        self.getValidKeys()
        response = requests.request("POST", url, headers=headers, json=payload)
        # response.raise_for_status()
        print(response.json(), "Placing order ============================")
        if response.status_code == 200:
            print("Request successful")
            print(response.json())  # Print response data
            return True
        else:
            print("Request failed with status code:", response.status_code)
            return False
        # try:
        #     # Make the API request
        #     response = requests.request("POST", url, headers=headers, json=payload)
        #     response.raise_for_status()  # Raise an exception for bad responses (status code >= 400)
        #     print(response.json(), "============================PLACING ORDER============================")
        #     return True, response.json()  # Return success status and response data
        # except requests.exceptions.RequestException as e:
        #     # Handle request exceptions (e.g., network errors, timeout)
        #     print("Request failed:", e)
        #     return False, None  # Return failure status and None for response data
        # except Exception as e:
        #     # Handle any other unexpected exceptions
        #     print("An unexpected error occurred:", e)
        #     return False, None  # Return failure status and None for response data

    '''
    Gets Ticker Data 
    '''
    def get_ticker_data(self):
        endpoint = "/trade/api/v2/24hr/ticker"
        method = "GET"
        payload = {}
        params = {
            "symbol": self.ticker,
            "exchange": "c2c1"
        }

        unquote_endpoint = endpoint
        if method == "GET" and len(params) != 0:
            endpoint += ('&', '?')[urlparse(endpoint).query == ''] + urlencode(params)
            unquote_endpoint = urllib.parse.unquote_plus(endpoint)

        signature_msg = method + unquote_endpoint + json.dumps(payload, separators=(',', ':'), sort_keys=True)

        request_string = bytes(signature_msg, 'utf-8')
        secret_key_bytes = bytes.fromhex(secret_key_outer)
        secret_key = ed25519.Ed25519PrivateKey.from_private_bytes(secret_key_bytes)
        signature_bytes = secret_key.sign(request_string)
        signature = signature_bytes.hex()

        url = "https://coinswitch.co" + endpoint

        headers = {
            'Content-Type': 'application/json',
            'X-AUTH-SIGNATURE': signature,
            'X-AUTH-APIKEY': api_key
        }

        response = requests.request("GET", url, headers=headers, json=payload)

        # Check if 'data' key exists in the response JSON
        data = response.json().get('data', [])

        # Convert the list of dictionaries to a Pandas DataFrame
        original_data = pd.DataFrame(data)
        return original_data

    '''
    Generates buy/sell signals
    '''
    def generate_signal(self, data):
        self.strategy.generate_signals(data)
        self.ticker_data = data
        self.ticker_data.dropna()

    def generate_position(self, data):
        self.strategy.generate_position(data)

    '''
    Gets User Portfoio
    '''
    def get_portfolio(self, coin_symbol):
        endpoint = "/trade/api/v2/user/portfolio"
        method = "GET"
        payload = {}

        unquote_endpoint = endpoint
        if method == "GET" and len({}) != 0:
            endpoint += ('&', '?')[urlparse(endpoint).query == ''] + urlencode({})
            unquote_endpoint = urllib.parse.unquote_plus(endpoint)

        signature_msg = method + unquote_endpoint + json.dumps(payload, separators=(',', ':'), sort_keys=True)

        request_string = bytes(signature_msg, 'utf-8')
        secret_key_bytes = bytes.fromhex(secret_key_outer)
        secret_key = ed25519.Ed25519PrivateKey.from_private_bytes(secret_key_bytes)
        signature_bytes = secret_key.sign(request_string)
        signature = signature_bytes.hex()

        url = "https://coinswitch.co" + endpoint

        headers = {
            'Content-Type': 'application/json',
            'X-AUTH-SIGNATURE': signature,
            'X-AUTH-APIKEY': api_key
        }

        try:
            response = requests.get(url, headers=headers, json=payload)
            response.raise_for_status()  # Raise an exception for bad responses (status code >= 400)
            data = response.json()["data"]

            # Convert JSON data to DataFrame
            df = pd.DataFrame(data)


            # Filter DataFrame based on coin symbol
            coin_data = df[df['currency'] == coin_symbol]
            print(coin_data)
            if not coin_data.empty:
                return coin_data.iloc[0].to_dict()  # Return dictionary of coin data
            else:
                return None  # Return None if coin data not found
        except requests.exceptions.RequestException as e:
            print("Request failed:", e)
            return None  # Return None for failure


    '''
    Responsible for live trading
    '''
    def trade(self, price, tp = None):
        if self.position in [0, -1] and self.ticker_data['signal'].iloc[-1] == 1:
            # go long
            # Placing buy order
            quantity_of_asset = int(self.main_balance/price)
            quantity_of_asset = 80
            success = self.createOrder("buy", quantity_of_asset, price)

            if success== True:
                self.position = 1
                self.entry_price = price
                self.total_quantity += quantity_of_asset
                self.main_balance -= (quantity_of_asset *  self.entry_price)
                print("*****position*****", self.position)
                print("*****entry_price*****", self.entry_price)
                print("*****total_quantity*****", self.total_quantity )
                print("*****main_balance*****", self.main_balance)
                print("***************************************************************************************************************************************************************************************************Buy Order placed successfully********************************************************************************************************************************************")
            else:
                print("***************************************************************************************************************************************************************************************************Failed to place buy order********************************************************************************************************************************************")
            print(55 * '=')
        elif self.position in [0, 1] and (self.entry_price != 0) and self.ticker_data['signal'].iloc[-1] == -1:
            # go short
            # Placing sell order
            price_diff = (price - self.entry_price)/price
            if tp is not None and price_diff >= tp:
                success, responsedata = self.createOrder("sell", self.total_quantity, price)
                if success == True:
                    self.position = -1
                    self.entry_price = price
                    self.main_balance += (self.total_quantity *  self.entry_price)
                    self.total_quantity = 0
                    print("*****position*****", self.position)
                    print("*****entry_price*****", self.entry_price)
                    print("*****total_quantity*****", self.total_quantity )
                    print("*****main_balance*****", self.main_balance)
                    print("***************************************************************************************************************************************************************************************************Sell Order placed successfully********************************************************************************************************************************************")
                else:
                    print("***************************************************************************************************************************************************************************************************Failed to place sell order********************************************************************************************************************************************")
            print(55 * '=')


    def check_for_stop_loss(self, price, sl = None):
        status = False
        if sl is not None and self.position != 0:
            rc = (price - self.entry_price) / self.entry_price
            if self.position == 1 and rc < -sl:
                print(f'STOP LOSS HIT | LONG')
                # Placing sell order
                success, responsedata = self.createOrder("sell", self.total_quantity, price)
                if success == True:
                    self.position = 0
                    self.entry_price = price
                    self.main_balance += (self.total_quantity * self.entry_price)
                    self.total_quantity  = 0
                    print("*****position*****", self.position)
                    print("*****entry_price*****", self.entry_price)
                    print("*****total_quantity*****", self.total_quantity)
                    print("*****main_balance*****", self.main_balance)
                    print("***************************************************************************************************************************************************************************************************Sell Order placed successfully with Stop loss********************************************************************************************************************************************")
                    status = True
                else:
                    print("***************************************************************************************************************************************************************************************************Failed to place sell order********************************************************************************************************************************************")
            elif self.position == -1 and rc > sl:
                print(f'STOP LOSS HIT | SHORT')
                # Placing buy order
                #quantity_of_asset = int(self.main_balance / price)
                quantity_of_asset = 82
                success, responsedata = self.createOrder("buy", quantity_of_asset, price)
                if success == True:
                    self.position = 0
                    self.entry_price = price
                    self.total_quantity += quantity_of_asset
                    self.main_balance -= (quantity_of_asset * self.entry_price)
                    print("*****position*****", self.position)
                    print("*****entry_price*****", self.entry_price)
                    print("*****total_quantity*****", self.total_quantity)
                    print("*****main_balance*****", self.main_balance)
                    print("***************************************************************************************************************************************************************************************************Buy Order placed successfully with Stop loss********************************************************************************************************************************************")
                    status = True
                else:
                    print("***************************************************************************************************************************************************************************************************Failed to place sell order********************************************************************************************************************************************")
        return status

    '''
    Converting INR to USDT
    '''
    def INR_to_USDT_conversion(self, price):
        # Create a CurrencyRates object
        c = CurrencyRates()
        # Specify the source and target currencies
        source_currency = 'INR'
        target_currency = 'USD'
        print("here")
        # Gets the exchange rate
        exchange_rate = c.get_rate(source_currency, target_currency)
        print("here2")
        # Performs the conversion from INR to USD
        price_in_usd = c.convert(source_currency, target_currency, pd.to_numeric(price))
        return price_in_usd

    # This API converts the ticker data into proper usable format
    def fetch_and_convert_to_dataframe(self, data):
        selected_data = {
            'timestamp': (dt.datetime.fromtimestamp(data['C2C1']['at'] / 1000)).strftime('%Y-%m-%d %H:%M:%S.%f'),
            'close': pd.to_numeric(data['C2C1']['lastPrice'])}
        selected_df = pd.DataFrame([selected_data], columns=['timestamp', 'close'])
        self.ticker_data = pd.concat([self.ticker_data, selected_df], ignore_index=True)
        self.ticker_data['timestamp'] = pd.to_datetime(self.ticker_data['timestamp'])


    def get_exchange_precision(self):
        endpoint = "https://coinswitch.co/trade/api/v2/exchangePrecision"
        method = "POST"
        payload = {
            "exchange": "coinswitchx",
            "symbol": "BTC/INR"
        }
        print(payload)
        unquote_endpoint = endpoint
        if method == "GET" and len({}) != 0:
            endpoint += ('&', '?')[urlparse(endpoint).query == ''] + urlencode({})
            unquote_endpoint = urllib.parse.unquote_plus(endpoint)

        signature_msg = method + unquote_endpoint + json.dumps(payload, separators=(',', ':'), sort_keys=True)

        request_string = bytes(signature_msg, 'utf-8')
        secret_key_bytes = bytes.fromhex(secret_key_outer)
        secret_key = ed25519.Ed25519PrivateKey.from_private_bytes(secret_key_bytes)
        signature_bytes = secret_key.sign(request_string)
        signature = signature_bytes.hex()

        url = "https://coinswitch.co/trade/api/v2/exchangePrecision"


        headers = {
            'Content-Type': 'application/json',
            'X-AUTH-SIGNATURE': signature,
            'X-AUTH-APIKEY': api_key
        }

        self.getValidKeys()
        response = requests.request("POST", url, headers=headers, json=payload)
        # response.raise_for_status()
        print(response.json(), "Placing order ============================")


'''
===================================STARTING MAIN APPLICATION======================================= 
'''

cryptoTrading = CryptoTrading("JASMY/USDT")
ticker_data = cryptoTrading.get_ticker_data()
cryptoTrading.fetch_and_convert_to_dataframe(ticker_data)
#cryptoTrading.createOrder("sell", 297, 0.0262)
#cryptoTrading.get_exchange_precision()


print("Ticker data is", cryptoTrading.get_ticker_data())
percentage_of_balance_to_invest = float(0.0045)


# Get USDT portfolio
usdt_portfolio = cryptoTrading.get_portfolio('USDT')
if usdt_portfolio is not None and 'main_balance' in usdt_portfolio:
    main_balance = usdt_portfolio['main_balance']
    cryptoTrading.main_balance = percentage_of_balance_to_invest * float(main_balance)
    print('main balance available for investment', cryptoTrading.main_balance)
else:
    print("Error: Unable to retrieve or parse USDT portfolio data")


average_buy_price_INR = 0
if cryptoTrading.get_portfolio("JASMY") is not None:
    average_buy_price_INR = cryptoTrading.get_portfolio('JASMY')['buy_average_price']

cryptoTrading.entry_price = cryptoTrading.INR_to_USDT_conversion(average_buy_price_INR)
print("Initial price which is already there", cryptoTrading.entry_price)
'''
while True:
    ticker_data = cryptoTrading.get_ticker_data()
    cryptoTrading.fetch_and_convert_to_dataframe(ticker_data)
    #print(cryptoTrading.ticker_data)
    #cryptoTrading.ticker_data[['close', 'ma', 'stddev', 'lowerBand', 'upperBand']].tail(50)
    cryptoTrading.generate_signal(cryptoTrading.ticker_data)
    print(cryptoTrading.ticker_data)
    price = cryptoTrading.ticker_data['close'].iloc[-1]
    print("price is", price)
    if cryptoTrading.check_for_stop_loss(price, sl = 0.05) == False:
        cryptoTrading.trade(price,tp = 0.001)
'''






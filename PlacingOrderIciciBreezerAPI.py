import pandas as pd
from breeze_connect import BreezeConnect
from datetime import datetime
import urllib
import time

#Enter your keys
your_api_key = ""
your_secret_key = ""
your_api_session = ""

class OptionsTrading:
    def __init__(self, user_code, user_right, user_strike_price, user_quantity, user_expiry_date):
        self.trailing_stoploss = 0
        self.take_profit = 0
        self.level = 0
        self.breeze = BreezeConnect(api_key=your_api_key)
        self.user_code = user_code
        self.user_right = user_right
        self.user_strike_price = user_strike_price
        self.user_quantity = user_quantity
        self.user_expiry_date = user_expiry_date
        # Obtain your session key from https://api.icicidirect.com/apiuser/login?api_key=YOUR_API_KEY
        # Incase your api-key has special characters(like +,=,!) then encode the api key before using in the url as shown below.
        print("https://api.icicidirect.com/apiuser/login?api_key=" + urllib.parse.quote_plus(your_api_key))
        # Generate Session
        self.breeze.generate_session(api_secret=your_secret_key,
                                session_token=your_api_session)

# This API is used to place the order
    def place_order(self):
        today = datetime.now().strftime('%Y-%m-%dT06:00:00.000Z')
        print(f"\n buying {self.user_right} order for {self.user_code} at {self.user_strike_price}")
        try:
            #Place order
            placed_order = self.breeze.place_order(stock_code=self.user_code,
                                              exchange_code="NFO",
                                              product="options",
                                              action="buy",
                                              order_type="market",
                                              stoploss="",
                                              quantity=self.user_quantity,
                                              price="",
                                              validity="day",
                                              validity_date= today,
                                              expiry_date=self.user_expiry_date,
                                              disclosed_quantity="0",
                                              right=self.user_right,
                                              strike_price=self.user_strike_price)

            if(placed_order['Status'] == 200):
                order_id = placed_order['Success']['order_id']
                print(f"Successfully placed market order !\nOrder ID is {order_id}")
                return order_id
            else:
                print("\n Failed to place an order !\n", placed_order["Error"])
                return False

        except Exception as error:
            print("Place Order API Error !", error)
            return False


    def on_ticks(self,ticks):
        if( 'last' in ticks.keys()):
            ltp = ticks['last']
            print(f"LTP: {round(ltp, 1)} | Level: {round(self.level, 1)} | SL:{round(self.trailing_stoploss, 1)}")

            # increase level & SL if price crosses threshold:
            if(ltp > self.level* 1.05):
                print(f"************ revising SL **************")
                self.level = ltp
                self.trailing_stoploss = self.level*0.90

            if (ltp < self.trailing_stoploss):
                #square off now
                print(f">>>>>>>>>>>>>>>ALERT-SQUARE OFF NOW <<<<<<<<<<<<<<<<<<<<<<")
                self.close()

            if (ltp > self.take_profit):
                #square off now
                print(f">>>>>>>>>>>>>>>BOOK-PROFIT<<<<<<<<<<<<<<<<<<<<<<")
                self.close()


#This API connects the websocket
    def web_socket_connect(self):
        print("entered 1")
        self.breeze.ws_connect()
        def on_ticks(ticks):
            print("entered")
            if ('last' in ticks.keys()):
                ltp = ticks['last']
                print(f"LTP: {round(ltp, 1)} | Level: {round(self.level, 1)} | SL:{round(self.trailing_stoploss, 1)}")

                # increase level & SL if price crosses threshold:
                if (ltp > self.level * 1.05):
                    print(f"************ revising SL **************")
                    self.level = ltp
                    self.trailing_stoploss = self.level * 0.8


                if (ltp < self.trailing_stoploss):
                    # square off now
                    print(f">>>>>>>>>>>>>>>ALERT-SQUARE OFF NOW <<<<<<<<<<<<<<<<<<<<<<")
                    self.close()

                #if (ltp > self.take_profit):
                    # square off now
                    #print(f">>>>>>>>>>>>>>>BOOK-PROFIT<<<<<<<<<<<<<<<<<<<<<<")
                    #self.close()

        # Assign the callbacks.
        self.breeze.on_ticks = on_ticks
        # subscribe stocks feeds
        self.breeze.subscribe_feeds(get_order_notification= True)


# This API returns the average of cost of the order placed
    def get_cost(self, order_id):
        try:
            detail = self.breeze.get_trade_detail("NFO", order_id)
            if(detail['Status'] == 200):
                cost = float(detail['Success'][0]['execution_price'])
                status = detail['Status']
                print(f"Order Status : {status}")
                return cost
            else:
                print("detail")

        except:
            print("API Failed!")

# This API disconnects the web socket & further, squares off the position.
    def close(self):
        self.breeze.ws_disconnect()
        print("-------------Squaring off now--------------")
        today = datetime.now().strftime('%Y-%m-%dT06:00:00.000Z')
        try:
            #Squaring off order
            sq_off_order = self.breeze.square_off(exchange_code="NFO",
                                                  product="options",
                                                  stock_code=self.user_code,
                                                   expiry_date=self.user_expiry_date,
                                                   right=self.user_right,
                                                   strike_price=self.user_strike_price,
                                                   action="sell",
                                                   order_type="market",
                                                   validity="day",
                                                   stoploss="0",
                                                   quantity=self.user_quantity,
                                                   price="0",
                                                   validity_date=today,
                                                   trade_password="",
                                                   disclosed_quantity="0")
            if (sq_off_order['Status'] == 200):
                order_id = sq_off_order['Success']['order_id']
                msg = sq_off_order['Success']['message']
                print(f"{msg} : {order_id}")
                return order_id

            else:
                print(f"Failed to square off!\n", sq_off_order['Error'])
                return False

        except Exception as error:
            print("Place order API Error!", error)
            return False


if __name__ == "__main__":
    print("Starting Execution \n")
    optionsTrading = OptionsTrading("NIFTY", "call", "23600", 25, "2024-05-30T06:00:00.000Z")
    optionsTrading.web_socket_connect()
    order_id = optionsTrading.place_order()
    if (order_id != False):
        time.sleep(5)
        cost = optionsTrading.get_cost(order_id)
        optionsTrading.level = cost
        if cost is not None:
            optionsTrading.take_profit = round(cost * 4.0, 1)
            optionsTrading.trailing_stoploss = round(cost * 0.8,1)
            print(f"Entry Cost:", {cost})
            print(f"Take Profit", {optionsTrading.take_profit})
            print(f"Trailing Stoploss", {optionsTrading.trailing_stoploss })
import pandas as pd
import numpy as np
import asyncio
from binance.client import Client
from binance.enums import *

# Define API keys here
api_key = "api_key"
api_secret = "api_secret"

# create binance client
client = Client(api_key, api_secret)
# client = Client(api_key, api_secret, testnet=True) #For Binance Testnet

symbols = ['BTCUSDT', 'ETHUSDT', 'MATICUSDT']  # Example: BTC/USDT
interval = '15m'  # minutes interval
limit = 50  # Limit the number of fetched data
delay_between_symbols = 3 * 60  # in seconds


async def process_symbol(symbol):

    while True:
        try:
            klines = client.futures_klines(
                symbol=symbol, interval=interval, limit=limit)
            klines_data = []

            for kline in klines:
                klines_data.append({
                    'timestamp': kline[0],
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5])
                })

            df = pd.DataFrame(klines_data)
            '''
            # Process the DataFrame or perform operations here...
            ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
            '''
            # print(df)

            '''
            Indicators
            ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
            '''
            def ema(period):
                ema = df['close'].ewm(
                    span=period, adjust=False).mean().iloc[-1]
                return ema

            def ATR(period):  # Average True Range

                df['high_low'] = df['high'] - df['low']
                df['high_prev_close'] = abs(df['high'] - df['close'].shift(1))
                df['low_prev_close'] = abs(df['low'] - df['close'].shift(1))
                df['true_range'] = df[['high_low',
                                      'high_prev_close', 'low_prev_close']].max(axis=1)

                # Calculate the Average True Range (ATR)
                df['atr'] = df['true_range'].rolling(window=period).mean()
                ATR = df['atr'][-2:-1].to_numpy()
                return ATR

            ema_20 = ema(20)
            ema_50 = ema(50)

            atr_14 = ATR(14)
            print('Average True Range:', atr_14)

            '''
            Functions
            ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
            '''
            def get_balance():
                futures_info = client.futures_account()
                futures_balances = {}
                for asset in futures_info['assets']:
                    asset_name = asset['asset']
                    # Converting balance to a float
                    asset_balance = float(asset['walletBalance'])
                    futures_balances[asset_name] = asset_balance
                usdt = futures_balances['USDT']
                print('USDT Balance:', usdt)
                return usdt

            def check_for_position():
                positions = client.futures_position_information(symbol=symbol)
                has_position = any(
                    float(pos['positionAmt']) != 0 for pos in positions)
                return has_position

            def cancel_oders_if_no_position():
                has_position = check_for_position()
                if not has_position:
                    # Retrieve open orders for the symbol
                    open_orders = client.futures_get_open_orders(symbol=symbol)

                    if open_orders:
                        # Cancel open orders
                        for order in open_orders:
                            order_id = order['orderId']
                            result = client.futures_cancel_order(
                                symbol=symbol, orderId=order_id)
                            if result:
                                print(
                                    f"Order {order_id} canceled successfully.")
                            else:
                                print(f"Failed to cancel order {order_id}.")
                    else:
                        print("No open orders for", symbol)
                else:
                    print("There is an open position for", symbol)

            def get_risk_reward_ratio():
                ratio = 2  # 1:2 ratio
                sl = atr_14  # assuming you will use ATR as stop loss
                tp = atr_14 * ratio
                return sl, tp

            def get_position_size():
                sl, tp = get_risk_reward_ratio()
                balance = get_balance()
                risk_amount = balance * 0.05
                lot_size = risk_amount / sl.item()  # contract size/position size
                # rounded lot_size varies, please check Binance allowed contract size for each pair
                if (symbol == 'BTCUSDT'):
                    lot_size = round(lot_size, 3)
                elif (symbol == 'ETHUSDT'):
                    lot_size = round(lot_size, 2)
                elif (symbol == 'MATICUSDT'):
                    lot_size = round(lot_size)
                return lot_size

            def get_buy_stop_loss(entry_price):
                sl, tp = get_risk_reward_ratio()
                stop = entry_price - sl.item()
                # rounded price depends on coin decimals
                if (symbol == 'BTCUSDT'):
                    stop_loss = round(stop, 1)
                elif (symbol == 'ETHUSDT'):
                    stop_loss = round(stop, 2)
                elif (symbol == 'MATICUSDT'):
                    stop_loss = round(stop, 4)
                return stop_loss

            def get_buy_take_profit(entry_price):
                sl, tp = get_risk_reward_ratio()
                profit = entry_price + tp.item()
                if (symbol == 'BTCUSDT'):
                    take_profit = round(profit, 1)
                elif (symbol == 'ETHUSDT'):
                    take_profit = round(profit, 2)
                elif (symbol == 'MATICUSDT'):
                    take_profit = round(profit, 4)
                return take_profit

            def get_sell_stop_loss(entry_price):
                sl, tp = get_risk_reward_ratio()
                stop = entry_price + sl.item()
                if (symbol == 'BTCUSDT'):
                    stop_loss = round(stop, 1)
                elif (symbol == 'ETHUSDT'):
                    stop_loss = round(stop, 2)
                elif (symbol == 'MATICUSDT'):
                    stop_loss = round(stop, 4)
                return stop_loss

            def get_sell_take_profit(entry_price):
                sl, tp = get_risk_reward_ratio()
                profit = entry_price - tp.item()
                if (symbol == 'BTCUSDT'):
                    take_profit = round(profit, 1)
                elif (symbol == 'ETHUSDT'):
                    take_profit = round(profit, 2)
                elif (symbol == 'MATICUSDT'):
                    take_profit = round(profit, 4)
                return take_profit

            def place_buy_order(symbol, lot_size):
                has_position = has_position()
                if not has_position:
                    # No open position, place a market order
                    order = client.futures_create_order(
                        symbol=symbol,
                        side='BUY',  # 'BUY' or 'SELL'
                        type='MARKET',  # Type of order: 'MARKET'
                        quantity=lot_size  # Amount to buy or sell
                    )
                    if (order):
                        print("Entry order placed:", order)

                    positions = client.futures_position_information(
                        symbol=symbol)
                    # Check if there's an open position for the symbol
                    open_positions = [pos for pos in positions if pos['symbol'] == symbol and float(
                        pos['positionAmt']) != 0]

                    if open_positions:
                        entry_price = float(
                            open_positions[0]['entryPrice'])
                        print(f"Entry price for {symbol}: {entry_price}")

                        stop_loss = get_buy_stop_loss(entry_price)
                        take_profit = get_buy_take_profit(entry_price)

                        # Place stop loss order
                        stop_loss_order = client.futures_create_order(
                            symbol=symbol,
                            side='SELL',  # Opposite side for stop loss
                            type='STOP_MARKET',  # Type of order: 'STOP_MARKET' for stop loss
                            quantity=0.01,
                            stopPrice=stop_loss,  # Price at which stop loss triggers
                            closePosition=True,  # Close the position when stop loss is triggered
                        )
                        if stop_loss_order:
                            print("Stop loss order placed:", stop_loss_order)

                        # Place take profit order
                        take_profit_order = client.futures_create_order(
                            symbol=symbol,
                            side='SELL',  # Opposite side for take profit
                            type='TAKE_PROFIT_MARKET',  # Type of order: 'TAKE_PROFIT_MARKET' for take profit
                            quantity=lot_size,
                            stopPrice=take_profit,  # Price at which take profit triggers
                            closePosition=True,  # Close the position when take profit is triggered
                        )
                        if take_profit_order:
                            print("Take profit order placed:",
                                  take_profit_order)
                        else:
                            print("Failed to place take profit order")
                else:
                    print("There is already an open position for", symbol)

            def place_sell_order(symbol, lot_size):
                has_position = has_position()
                if not has_position:
                    # No open position, place a market order
                    order = client.futures_create_order(
                        symbol=symbol,
                        side='SELL',  # 'BUY' or 'SELL'
                        type='MARKET',  # Type of order: 'MARKET'
                        quantity=lot_size,  # Amount to buy or sell
                    )
                    if (order):
                        print("Entry order placed:", order)

                        # Get position information for the symbol
                        positions = client.futures_position_information(
                            symbol=symbol)
                        # Check if there's an open position for the symbol
                        open_positions = [pos for pos in positions if pos['symbol'] == symbol and float(
                            pos['positionAmt']) != 0]

                        if open_positions:
                            entry_price = float(
                                open_positions[0]['entryPrice'])
                            print(f"Entry price for {symbol}: {entry_price}")

                        stop_loss = get_sell_stop_loss(entry_price)
                        take_profit = get_sell_take_profit(entry_price)

                        # Place stop loss order
                        stop_loss_order = client.futures_create_order(
                            symbol=symbol,
                            side='BUY',  # Opposite side for stop loss when selling
                            type='STOP_MARKET',  # Type of order: 'STOP_MARKET' for stop loss
                            quantity=lot_size,
                            stopPrice=stop_loss,  # Price at which stop loss triggers
                            closePosition=True,  # Close the position when stop loss is triggered
                        )
                        if stop_loss_order:
                            print("Stop loss order placed:", stop_loss_order)

                        # Place take profit order
                        take_profit_order = client.futures_create_order(
                            symbol=symbol,
                            side='BUY',  # Opposite side for take profit when selling
                            type='TAKE_PROFIT_MARKET',  # Type of order: 'TAKE_PROFIT_MARKET' for take profit
                            quantity=lot_size,
                            stopPrice=take_profit,  # Price at which take profit triggers
                            closePosition=True,  # Close the position when take profit is triggered
                        )
                        if take_profit_order:
                            print("Take profit order placed:",
                                  take_profit_order)
                        else:
                            print("Failed to place take profit order")

                else:
                    print("There is already an open position for", symbol)

            '''
            Logic here
            ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
            '''

            lot_size = get_position_size()
            # print('lot_size:', lot_size)

            long_condition = ema_20 > ema_50
            short_condition = ema_20 < ema_50

            if long_condition:
                return place_buy_order(symbol, lot_size)
            if short_condition:
                return place_sell_order(symbol, lot_size)

            # cancel orders if there is no position open
            cancel_order = cancel_oders_if_no_position()
            print('///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////')

            await asyncio.sleep(0)  # seconds delay before next iteration

        except Exception as e:
            print(f"Error fetching data: {e}")

        # Synchronous sleep in executor
        await asyncio.sleep(delay_between_symbols)


async def main():
    tasks = [process_symbol(symbol) for symbol in symbols]
    await asyncio.gather(*tasks)  # Await the list of tasks

asyncio.run(main())

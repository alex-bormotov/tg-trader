import json
import time
import ccxt
import requests
from time import sleep
from functools import wraps
from datetime import datetime, timedelta
from telegram.ext import Updater, CommandHandler


open_orders = []
account_name = ''
monitoring_state = 'OFF'
chat_id_for_orders_notifications = None


def get_config():
    with open("config.json", "r") as read_file:
        config = json.load(read_file)
        return config


def write_config(config):
    with open("config.json", "w") as write_file:
        json.dump(config, write_file, indent=1)


def get_telegram_config():
    telegram_chat_id = get_config()["telegram_chat_id"]
    telegram_bot_key = get_config()["telegram_bot_key"]
    return telegram_chat_id, telegram_bot_key


def get_api_config(account_name):
    for i in get_config()["exchange_api_data"]:
        if i["name"] == account_name:
            key = i["key"]
            secret = i["secret"]
            return key, secret


def restricted(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        chat_id = int(get_telegram_config()[0])
        if user_id != chat_id:
            # print("Unauthorized access denied for {}.".format(user_id))
            context.bot.send_message(
                chat_id=chat_id,
                text=("Unauthorized access denied for {}.".format(user_id)),
            )
            return
        return func(update, context, *args, **kwargs)

    return wrapped


def exchange(account_name):
    try:
        key = get_api_config(account_name)[0]
        secret = get_api_config(account_name)[1]
        exchange = ccxt.binance(
            {"apiKey": key, "secret": secret, "enableRateLimit": True}
        )
        return exchange

    except ccxt.NetworkError as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))
    except ccxt.ExchangeError as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))
    except Exception as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))


def usd_price(coin, amount, account_name):
    price = exchange(account_name).fetch_ticker(f"{coin.upper()}/USDT")["last"]
    return price * amount


def number_for_human(number):
    x_str = str(number)
    if "e-0" in x_str:
        return "%.08f" % number  # str
    else:
        return str(number)[:9]  # str


def order_for_human(order):
    return f'Order {order["id"]}, {order["type"]} {order["side"]} {order["amount"]} {order["symbol"]} at price {order["price"]} is {order["status"]}'


@restricted
def start(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="For showing all commands type /help",
    )


@restricted
def help(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="/balance\n\n/accounts\n\n/price\n\n/trade\n\n/orders\n\n/cancel_order\n\n/monitoring_orders",
    )


@restricted
def show_all_accounts_names(update, context):
    for i in get_config()["exchange_api_data"]:
        context.bot.send_message(chat_id=update.effective_chat.id,text=i["name"])


@restricted
def fetch_balance(update, context):
    try:
        if len(" ".join(context.args)) == 0:
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="/balance <account_name> <coin> or <all>\n\nAn example (Balance XRP on account 1): \n/balance account_1 xrp(or all for all not zero balances)",
                    )
        else:
            account_name = context.args[0]
            coin = context.args[1]

            if coin == 'all':
                balances = exchange(account_name).fetch_balance()['info']['balances']
                balances = [f'{b["asset"]} {b["free"]}, in order {b["locked"]}' for b in balances for k, v in b.items() if k == 'free' and float(v) > 0]
                for b in balances:
                    if 'VTHO' not in b:
                        context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=b
                        )
            else:
                b = exchange(account_name).fetch_balance()
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f'{coin.upper()} total {b[coin.upper()]["total"]}, free {b[coin.upper()]["free"]}, in order {b[coin.upper()]["used"]} ~ {round(usd_price(coin, b[coin.upper()]["total"], account_name))} USDT'
                )

    except ccxt.NetworkError as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))
    except ccxt.ExchangeError as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))
    except Exception as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))


@restricted
def get_price(update, context):
    try:
        if len(" ".join(context.args)) == 0:
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="/price <account_name> <coin_1> <coin_2>\n\nAn example (Price XRP/BTC): \n/price account_1 xrp btc",
                    )
        else:
            account_name = context.args[0]
            coin_1 = context.args[1].upper()
            coin_2 = context.args[2].upper()
            price = exchange(account_name).fetch_ticker(f"{coin_1}/{coin_2}")["last"]
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"{number_for_human(price)}",
            )

    except ccxt.NetworkError as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))
    except ccxt.ExchangeError as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))
    except Exception as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))


@restricted
def trade(update, context):
    try:
        if len(" ".join(context.args)) == 0:
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="/trade <account_name> <buy/sell> <coin_1> <coin_2> <amount> <price>\n\nAn example (Sell XRP/BTC): \n/trade account_1 sell xrp btc 100 0.00003154",
                    )
        else:
            account_name = context.args[0]
            side = context.args[1]  # "buy" or "sell"
            coin_1 = context.args[2].upper()
            coin_2 = context.args[3].upper()
            amount = float(context.args[4])
            price = float(context.args[5])
            symbol = f"{coin_1}/{coin_2}"
            type = "limit"  # "market" or "limit"
            params = {}
            order = (symbol, type, side, amount, price, params)
            order = exchange(account_name).create_order(symbol, type, side, amount, price, params)

            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=order_for_human(order),
            )

    except ccxt.NetworkError as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))
    except ccxt.ExchangeError as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))
    except Exception as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))


@restricted
def show_orders(update, context):
    try:
        if len(" ".join(context.args)) == 0:
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="/orders <account_name> <coin_1> <coin_2>\n\nAn example (Open orders XRP/BTC): \n/orders account_1 xrp btc\n\nOr\n/orders <account_name> all",
                    )
        else:
            if context.args[1] == 'all':
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text='Wait, please ...',
                )

                account_name = context.args[0]

                all_markets = exchange(account_name).fetch_markets()
                markets = [i['symbol'] for i in all_markets]
                balances = exchange(account_name).fetch_balance()['total']
                coins_1 = [k for k, v in balances.items() if v > 0 and k != 'VTHO']
                coin_pairs = [t for i in coins_1 for t in markets if i == (t.split('/')[0])]
                open_orders = [x for h in coin_pairs for x in exchange(account_name).fetch_open_orders(h) if len(x) > 0]
                for order in open_orders:
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=order_for_human(order),
                    )

            else:
                account_name = context.args[0]
                coin_1 = context.args[1].upper()
                coin_2 = context.args[2].upper()
                orders = exchange(account_name).fetch_open_orders(f"{coin_1}/{coin_2}")
                for order in orders:
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=order_for_human(order),
                    )


    except ccxt.NetworkError as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))
    except ccxt.ExchangeError as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))
    except Exception as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))


@restricted
def cancel_order(update, context):
    try:
        if len(" ".join(context.args)) == 0:
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="/cancel_order <account_name> <order_id> <coin_1> <coin_2>\n\nAn example: \n/cancel_order account_1 257880697 xrp btc",
                    )
        else:
            account_name = context.args[0]
            order_id = int(context.args[1])
            coin_1 = context.args[2].upper()
            coin_2 = context.args[3].upper()
            order = exchange(account_name).cancel_order(order_id, f"{coin_1}/{coin_2}")
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=order_for_human(order),
            )


    except ccxt.NetworkError as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))
    except ccxt.ExchangeError as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))
    except Exception as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))


@restricted
def monitoring_orders(update, context):

    global account_name
    global monitoring_state
    global chat_id_for_orders_notifications


    if len(" ".join(context.args)) == 0:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="/monitoring_orders <account_name> on/off\n\n/monitoring_orders <account_name> status",
                )

    if context.args[1].upper() == "STATUS":
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Orders monitoring is {monitoring_state}",
        )

    if context.args[1].upper() == "ON" and monitoring_state == "ON":
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Orders monitoring is already {monitoring_state}, turn OFF it before new start",
        )

    if context.args[1].upper() == "OFF":
        chat_id_for_orders_notifications = None
        account_name = ''
        monitoring_state = context.args[1].upper()
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Orders monitoring is {monitoring_state}",
        )

    if context.args[1].upper() == "ON" and monitoring_state == "OFF":
        chat_id_for_orders_notifications = update.effective_chat.id
        account_name = context.args[0]
        monitoring_state = context.args[1].upper()
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Orders monitoring is {monitoring_state}",
        )


def orders_monitoring():
    global open_orders

    def order_status_is_open(order_id, coin_pair):
        order = exchange(account_name).fetch_order(order_id, coin_pair)
        return order, order['status']

    try:
        while True:
            if monitoring_state == 'ON':
                all_markets = exchange(account_name).fetch_markets()
                markets = [i['symbol'] for i in all_markets]
                balances = exchange(account_name).fetch_balance()['total']
                coins_1 = [k for k, v in balances.items() if v > 0 and k != 'VTHO']
                coin_pairs = [t for i in coins_1 for t in markets if i == (t.split('/')[0])]

                open_orders_new = [(i['id'], i['symbol']) for i in [x for h in coin_pairs for x in exchange(account_name).fetch_open_orders(h) if len(x) > 0]]
                if len(open_orders) == 0:
                    if len(open_orders_new) != 0:
                        open_orders = open_orders_new

                for c, v in open_orders_new:
                    if c not in [x for x, v in open_orders]:
                        open_orders.append((c, v))

                for c, v in open_orders:
                    order_status_is_open_data = order_status_is_open(c, v)
                    if order_status_is_open_data[1] != 'open':
                        pop = open_orders.pop([index for index, k in enumerate(open_orders) if (c, v) == k][0])
                        updater.bot.send_message(
                            chat_id=chat_id_for_orders_notifications,
                            text=order_for_human(order_status_is_open_data[0]),
                        )
                        
                time.sleep(5)
                continue
            else:
                time.sleep(5)
                continue

    except Exception as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))


if __name__ == "__main__":

    updater = Updater(get_telegram_config()[1], use_context=True)
    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("help", help))
    updater.dispatcher.add_handler(CommandHandler("balance", fetch_balance))
    updater.dispatcher.add_handler(CommandHandler("accounts", show_all_accounts_names))
    updater.dispatcher.add_handler(CommandHandler("price", get_price))
    updater.dispatcher.add_handler(CommandHandler("trade", trade))
    updater.dispatcher.add_handler(CommandHandler("orders", show_orders))
    updater.dispatcher.add_handler(CommandHandler("cancel_order", cancel_order))
    updater.dispatcher.add_handler(CommandHandler("monitoring_orders", monitoring_orders))

    updater.start_polling()

    orders_monitoring()

    updater.idle()

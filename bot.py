import json
import time
import ccxt
import requests
from time import sleep
from functools import wraps
from datetime import datetime, timedelta
from telegram.ext import Updater, CommandHandler



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



admin_chat_id = get_telegram_config()[0]
open_orders = []
monitoring_state_name_chat_id = [('acc name', 'OFF', '000001')]



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
                balances = [f'{b["asset"]} {number_for_human(b["free"])}, in order {number_for_human(b["locked"])}' for b in balances for k, v in b.items() if k == 'free' and float(v) > 0]
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
                    text=f'{coin.upper()} total {number_for_human(b[coin.upper()]["total"])}, free {number_for_human(b[coin.upper()]["free"])}, in order {b[coin.upper()]["used"]} ~ {round(usd_price(coin, b[coin.upper()]["total"], account_name))} USDT'
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
                account_name = context.args[0]

                if len(open_orders) != 0 and 'ON' in [c for n, c, v in monitoring_state_name_chat_id if account_name == n]:
                    for order in open_orders:
                        if order[0] == account_name:
                            context.bot.send_message(
                                chat_id=update.effective_chat.id,
                                text=f'Account {account_name}\n\n{order_for_human(exchange(account_name).fetch_order(order[1], order[2]))}',
                            )

                if len(open_orders) == 0 and 'ON' in [c for n, c, v in monitoring_state_name_chat_id if account_name == n]:
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text='Orders not found',
                    )

                if 'ON' not in [c for n, c, v in monitoring_state_name_chat_id if account_name == n]:
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text='For see all orders you need to enable /monitoring_orders',
                    )

            else:
                account_name = context.args[0]
                coin_1 = context.args[1].upper()
                coin_2 = context.args[2].upper()
                orders = exchange(account_name).fetch_open_orders(f"{coin_1}/{coin_2}")
                if len(orders) != 0:
                    for order in orders:
                        context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=f'Account {account_name}\n\n{order_for_human(order)}',
                        )
                else:
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text='Order not found',
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

    global monitoring_state_name_chat_id


    if len(" ".join(context.args)) == 0:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="/monitoring_orders <account_name> <on/off>\n\n\nCoinPairs or ALL(a long wait for an update - up to six minutes, binance's restriction) must be set in config file\n\n/monitoring_orders <account_name> status\n\n\n",
                )
    else:
        account_name = context.args[0]

        if context.args[1].upper() == "STATUS":
            status = [c for n, c, v in monitoring_state_name_chat_id if account_name == n]
            if len(status) == 0:
                status = ['OFF']
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Orders monitoring is {status[0]}",
            )


        if context.args[1].upper() == "OFF":
            for account_name, c, v in monitoring_state_name_chat_id:
                x = [(index, k) for index, k in enumerate(monitoring_state_name_chat_id) if account_name == k[0]]
                if account_name == x[0][1][0]:
                    pop = monitoring_state_name_chat_id.pop(x[0][0] + 1)
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"Orders monitoring for account {pop[0]} is OFF",
                    )

        if context.args[1].upper() == "ON":
            for n, c, v in monitoring_state_name_chat_id:
                if account_name != n and account_name not in [z for z, x, v in monitoring_state_name_chat_id]:
                    state = context.args[1].upper()
                    chat_id = update.effective_chat.id
                    monitoring_state_name_chat_id.append((account_name, state, chat_id))
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"Orders monitoring for account {account_name} is {state}",
                    )


def orders_monitoring():

    global open_orders

    def order_status_is_open(order_id, coin_pair):
        order = exchange(account_name).fetch_order(order_id, coin_pair)
        return order, order['status']

    def get_new_open_orders(account_name):
        if get_config()['coin_pairs'][0] == 'ALL':
            all_markets = exchange(account_name).fetch_markets()
            markets = [i['symbol'] for i in all_markets]
            balances = exchange(account_name).fetch_balance()['total']
            coins_1 = [k for k, v in balances.items() if v > 0 and k != 'VTHO']
            coin_pairs = [t for i in coins_1 for t in markets if i == (t.split('/')[1])]
        else:
            coin_pairs = get_config()['coin_pairs']
        return [(account_name, i['id'], i['symbol']) for i in [x for h in coin_pairs for x in exchange(account_name).fetch_open_orders(h) if len(x) > 0]]


    try:
        while True:
            for account_name in [k for index, k in enumerate([i["name"] for i in get_config()["exchange_api_data"]])]:
                t = [n for n, c, v in monitoring_state_name_chat_id if n == account_name and c == 'ON']
                if len(t) != 0:
                    open_orders_new = get_new_open_orders(account_name)

                    if len(open_orders) == 0:
                        open_orders = open_orders_new

                    for n, c, v in open_orders_new:
                        if c not in [x for z, x, v in open_orders]:
                            open_orders.append((n, c, v))

                    for i in monitoring_state_name_chat_id:
                        if i[1] == 'ON':
                            for account_name, c, v in open_orders:
                                order_status_is_open_data = order_status_is_open(c, v)
                                if order_status_is_open_data[1] != 'open':
                                    x = [(index, k) for index, k in enumerate(open_orders) if account_name == k[0]]
                                    if account_name == x[0][1][0]:
                                        pop = open_orders.pop(x[0][0])
                                        updater.bot.send_message(
                                            chat_id=i[2],
                                            text=f'Account {account_name}\n\n{order_for_human(order_status_is_open_data[0])}',
                                        )
            time.sleep(10)
            continue

    except Exception as e:
        updater.bot.send_message(chat_id=admin_chat_id, text=str(e))



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

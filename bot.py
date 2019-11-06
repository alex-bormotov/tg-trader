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



def restricted(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in LIST_OF_ADMINS:
            # print("Unauthorized access denied for {}.".format(user_id))
            context.bot.send_message(
                chat_id=LIST_OF_ADMINS[0],
                text=("Unauthorized access denied for {}.".format(user_id)),
            )
            return
        return func(update, context, *args, **kwargs)

    return wrapped

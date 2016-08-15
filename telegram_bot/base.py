import json

import telebot
from telebot import types

from telegram_bot.crypt import decrypt
from telegram_bot.plugins.admin import AdminPlugin
from telegram_bot.types.keyboard import get_button_function
from telegram_bot.types.message import message_wrapper
from .config import Config
from .utils.telegram import securize_message


class BotBase(object):
    commands = (AdminPlugin,)

    def __init__(self, config_path):
        self.config = Config(config_path)
        self.init()

    def init(self):
        self.bot = telebot.TeleBot(self.config['api_token'])
        self.set_handlers()
        self.set_command_handlers()
        # 'sqlite:///db.sqlite3'
        # self.engine = self.get_engine(self.config['db_url'])
        # self.sessionmaker = self.get_sessionmaker()

    def set_command_handlers(self):
        for command in self.commands:
            cmd = command(self)
            cmd.set_handlers()

    def set_message_handler(self, fn, *args, **kwargs):
        return self.bot.message_handler(*args, **kwargs)(securize_message(message_wrapper(self, fn)))

    def set_handlers(self):
        self.bot.callback_query_handler(self.process_query)(self.process_query)

    def process_query(self, query):
        """Process callback_data to send message to correct callback function.
        :return:
        """
        key = self.config['api_token'].split(':')[1][:16].encode('utf-8')
        data = decrypt(query.data, key)
        try:
            query.data = json.loads(data.decode('utf-8'))
        except json.decoder.JSONDecodeError:
            pass
        if isinstance(query.data, dict) and 'fn' in query.data:
            fn = get_button_function(query.data['fn'])
            fn(**query.data['kw'] or {})


    def poll(self):
        self.bot.polling(none_stop=True, interval=0)

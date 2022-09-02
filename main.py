import json
import logging
from enum import Enum

import telebot
from telebot import types

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logger.info('Bot starts')


class Button(Enum):
    reload = 'Обновить данные'
    search = 'Найти контакт'
    close = 'Закрыть панель'


class ReplyAction(Enum):
    want_to_search = 'Введите имя желаемого контакта'


class Settings:
    token: str
    data: list[dict]

    def __init__(self) -> None:
        self.reload()

    def reload(self) -> None:
        with open('data.json', 'r') as file:
            info = json.load(file)
            self.token = info.get('token')
            self.data = info.get('data')

    def default(self) -> None:
        self.token = ''
        self.data = []


def main() -> telebot.TeleBot:
    settings = Settings()
    bot = telebot.TeleBot(settings.token)

    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        answer = 'Привет! Используй команды, которые бот может тебе предложить. Не бойся, они рабочие.'
        bot.reply_to(message, answer)
        logger.info(f'Send to "{message.chat.username}" message - "{answer}"')
        send_buttons(message.chat.id)

    @bot.message_handler(commands=['open'])
    def open_panel(message):
        send_buttons(message.chat.id)
        logger.info(f'User "{message.chat.username}" open button panel')

    @bot.message_handler(commands=['сlose', 'end'])
    def close_panel(message):
        bot.reply_to(message, 'Скрыл панель с кнопками.', reply_markup=types.ReplyKeyboardRemove())
        logger.info(f'User "{message.chat.username}" close button panel')

    @bot.message_handler(commands=[Button.search.name])
    def send_search_info(message):
        logger.info(f'User "{message.chat.username}" choose "{Button.search.name}".')
        bot.send_message(message.chat.id, ReplyAction.want_to_search.value, reply_markup=types.ForceReply())

    @bot.message_handler(func=lambda message: True)
    def echo_all(message):
        if message.text == Button.reload.value:
            logger.info(f'User "{message.chat.username}" choose "{Button.reload.name}".')
            send_reload_result(message)
        elif message.text == Button.search.value:
            send_search_info(message)
        elif message.text == Button.close.value:
            close_panel(message)
        elif message.reply_to_message is not None and message.reply_to_message.text == ReplyAction.want_to_search.value:
            logger.info(f'User "{message.chat.username}" trying to search persons by name "{message.text}".')
            send_found_user(message)
        else:
            logger.info(f'User "{message.chat.username}" send message "{message.text}".')
            bot.reply_to(message, 'Мне твои непонятные команды непонятны :|')

    @bot.message_handler(commands=['reload'])
    def send_reload_result(message):
        try:
            settings.reload()
            answer = 'Данные обновлены.'
            logger.info(f'User "{message.chat.username}" updated settings.')
        except Exception:
            answer = 'Данные не удалось обновить.'
            logger.warning(f'User "{message.chat.username}" trying to update setting, it fails.')
        bot.send_message(message.chat.id, answer)
        send_buttons(message.chat.id)

    def send_buttons(chat_id: id) -> [types.ReplyKeyboardMarkup, str]:
        markup = types.ReplyKeyboardMarkup(row_width=3)
        search_btn = types.KeyboardButton(Button.search.value)
        reload_btn = types.KeyboardButton(Button.reload.value)
        close_btn = types.KeyboardButton(Button.close.value)
        markup.add(search_btn, reload_btn, close_btn)
        bot.send_message(chat_id, 'Выбери одну из опций:', reply_markup=markup)

    def send_found_user(message):
        search_person = message.text.lower()
        people = [item for item in settings.data if search_person in item['name'].lower()]
        if people:
            answer = [f'Контакт:\t{person["name"]}\nНомер:\t[{person["phone_number"]}](tel:{person["phone_number"]})' for person in people]
            bot.reply_to(message, '\n\n'.join(answer), parse_mode='Markdown')
            logger.info(f'User "{message.chat.username}" found users: {len(people)}.')
        else:
            bot.reply_to(message, 'С такими именами тебе только в цирк.')
            logger.info(f'User "{message.chat.username}" cannot found anything.')
        send_buttons(message.chat.id)

    return bot


if __name__ == '__main__':
    bot = main()
    bot.infinity_polling()

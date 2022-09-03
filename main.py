import json
import logging
from enum import Enum

import telebot
from telebot import types
from telebot.custom_filters import TextContainsFilter, SimpleCustomFilter

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


class ReplyFilter(SimpleCustomFilter):
    key = 'is_search_reply'

    @staticmethod
    def check(message: types.Message, **kwargs) -> bool:
        return (message.reply_to_message is not None and
                message.reply_to_message.text == ReplyAction.want_to_search.value)


def main() -> telebot.TeleBot:
    settings = Settings()
    bot = telebot.TeleBot(settings.token)
    bot.add_custom_filter(TextContainsFilter())
    bot.add_custom_filter(ReplyFilter())

    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message: types.Message) -> None:
        answer = 'Привет! Используй команды, которые бот может тебе предложить. Не бойся, они рабочие.'
        bot.reply_to(message, answer)
        logger.info(f'Send to "{message.chat.username}" message - "{answer}"')
        send_buttons(message.chat.id)

    @bot.message_handler(commands=['open'])
    def open_panel(message: types.Message) -> None:
        send_buttons(message.chat.id)
        logger.info(f'User "{message.chat.username}" open button panel')

    @bot.message_handler(commands=[Button.close.name, 'end'])
    @bot.message_handler(text_contains=[Button.close.value])
    def close_panel(message: types.Message) -> None:
        bot.reply_to(message, 'Скрыл панель с кнопками.', reply_markup=types.ReplyKeyboardRemove())
        logger.info(f'User "{message.chat.username}" close button panel')

    @bot.message_handler(commands=[Button.search.name])
    @bot.message_handler(text_contains=[Button.search.value])
    def send_search_info(message: types.Message) -> None:
        logger.info(f'User "{message.chat.username}" choose "{Button.search.name}".')
        bot.send_message(message.chat.id, ReplyAction.want_to_search.value, reply_markup=types.ForceReply())

    @bot.message_handler(commands=[Button.reload.name])
    @bot.message_handler(text_contains=[Button.reload.value])
    def send_reload_result(message: types.Message) -> None:
        logger.info(f'User "{message.chat.username}" choose "{Button.reload.name}".')
        try:
            settings.reload()
            answer = 'Данные обновлены.'
            logger.info(f'User "{message.chat.username}" updated settings.')
        except Exception:
            answer = 'Данные не удалось обновить.'
            logger.warning(f'User "{message.chat.username}" trying to update setting, it fails.')
        bot.send_message(message.chat.id, answer)
        send_buttons(message.chat.id)

    def send_buttons(chat_id: int) -> None:
        markup = types.ReplyKeyboardMarkup(row_width=3)
        search_btn = types.KeyboardButton(Button.search.value)
        reload_btn = types.KeyboardButton(Button.reload.value)
        close_btn = types.KeyboardButton(Button.close.value)
        markup.add(search_btn, reload_btn, close_btn)
        bot.send_message(chat_id, 'Выбери одну из опций:', reply_markup=markup)

    @bot.message_handler(is_search_reply=True)
    def send_found_user(message: types.Message) -> None:
        logger.info(f'User "{message.chat.username}" trying to search persons by name "{message.text}".')
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

    @bot.message_handler(func=lambda message: True)
    def echo_all(message: types.Message) -> None:
        logger.info(f'User "{message.chat.username}" send message "{message.text}".')
        bot.reply_to(message, 'Мне твои непонятные команды непонятны :|')

    return bot


if __name__ == '__main__':
    bot = main()
    bot.infinity_polling(skip_pending=True)

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# создаем кнопки и клаиватуру
get_call_stat_button = InlineKeyboardButton('Получить статистику', callback_data='get_call_stat')
create_creds_button = InlineKeyboardButton('Подключить кабинет', callback_data='create_creds')
remove_creds_button = InlineKeyboardButton('Отключить кабинет', callback_data='remove_creds')
show_creds_button = InlineKeyboardButton('Список моих кабинетов', callback_data='show_creds')

main_keyboard = InlineKeyboardMarkup(resize_keyboard=True)
main_keyboard.add(get_call_stat_button)
main_keyboard.add(show_creds_button)
main_keyboard.add(create_creds_button)
main_keyboard.add(remove_creds_button)


# кнопки и клавиатура для статистики CallTouch
get_today_stat_button = InlineKeyboardButton('Статистика за сегодня', callback_data='get_today_stat')
get_yesterday_stat_button = InlineKeyboardButton('Статистика за вчера', callback_data='get_yesterday_stat')
get_back_button = InlineKeyboardButton('Вернуться назад', callback_data='get_back')

calltouch_keyboard = InlineKeyboardMarkup(resize_keyboard=True)
calltouch_keyboard.add(get_today_stat_button)
calltouch_keyboard.add(get_yesterday_stat_button)
calltouch_keyboard.add(get_back_button)

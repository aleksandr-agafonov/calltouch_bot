from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from states import Actions
from aiogram.dispatcher import FSMContext

# ипортируем клавиатуру
from tg_keyboard import main_keyboard, calltouch_keyboard

# импортируем внутренни функции
from calltouch_functions_async import CallTouchFunctions
from db_functions_async import DbFunctions

# импорт других библиотек
from datetime import datetime
import itertools
import asyncio
import nest_asyncio


token = '1974255060:AAFosMbvKycoKRydyPdi4yjflv8031SW4mE' # боевой
#token = '1938283222:AAEe7C80RbtpAjW7BVBzt6qISW8VnzIpg0A'  # тестовый
bot = Bot(token=token)
dp = Dispatcher(bot, storage=MemoryStorage())
nest_asyncio.apply()  # для добавления задач в ассинхрон

# глобальные переменные
ct_creds = dict()  # сюда кладем крденшалы для сохранения колтача


# Приветственный блок
@dp.message_handler(commands=['start'], state='*')  # приветствуем и показываем клавиатуру
async def start_message(message: types.Message, state: FSMContext):
    await state.reset_state()
    message_text = 'Привет!\n' \
                   'Я вышлю Вам статистику из CallTouch в любое время!\n'\
                   'Выберете нужный пункт меню'
    await bot.send_message(message.from_user.id, message_text, reply_markup=main_keyboard)


# блок создания CT
@dp.callback_query_handler(lambda c: c.data == 'create_creds')
async def create_creds_get_id(callback_query: types.CallbackQuery):
    message_text = 'Все данные для подключения, можно найти в личном кабинете Calltouch:\n'\
                   'Интеграция => API и Webhooks\n' \
                   'Что бы завести кабинет, вам понадобится:\n'\
                   '1. ID своего кабинета Calltouch,\n'\
                   '2. Ссылку на сервер,\n'\
                   '3. Токен доступа\n' \
                   'Или /start что бы вернуться назад\n'
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, message_text)
    await bot.send_message(callback_query.from_user.id, 'Введите ID кабинета CallTouch')
    await Actions.create_ct_get_id.set()


# получение ID кабинета calltouch
@dp.message_handler(state=Actions.create_ct_get_id)
async def get_ct_id(message: types.Message, state: FSMContext):
    # сохраняем ID введенного кабинета
    async with state.proxy() as data:
        data['cabinet_id'] = message.text

    await Actions.create_ct_get_server.set()
    await bot.send_message(message.from_user.id, 'Введите ссылку на сервер')


# получение ноды calltouch
@dp.message_handler(state=Actions.create_ct_get_server)
async def get_ct_server(message: types.Message, state: FSMContext):
    # сохраняем ноду введенного кабинета
    async with state.proxy() as data:
        data['server'] = message.text
    await Actions.create_ct_get_token.set()
    await bot.send_message(message.from_user.id, 'Введите токен')


# получение токена calltouch, валидация и запись данных в БД
@dp.message_handler(state=Actions.create_ct_get_token)
async def get_ct_token(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        data['token'] = message.text
        data['create_date'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        data['user_id'] = message.from_user.id

    try:
        async with state.proxy() as data:
            data['user_name'] = message.from_user.first_name
    except ValueError:
        async with state.proxy() as data:
            data['user_name'] = 'unknown'

    try:
        async with state.proxy() as data:
            data['user_surname'] = message.from_user.last_name
    except ValueError:
        async with state.proxy() as data:
            data['user_surname'] = 'unknown'

    # добавляем задачу ассинхронно
    loop = asyncio.get_running_loop()
    run_func = loop.create_task(CallTouchFunctions.validate_creds(data['cabinet_id'], data['server'], data['token']))
    loop.run_until_complete(run_func)
    result = run_func.result()

    if result != 'ok':
        # очищаем креды колтача в случае ошибки
        async with state.proxy() as data:
            data.clear()
        message_text = 'Введенные данные некорректны.\n'\
                       'Попробуйте еще раз'
        await bot.send_message(message.from_user.id, message_text, reply_markup=main_keyboard)
        await state.reset_state()
    else:
        # добавляем задачу ассинхронно
        loop = asyncio.get_running_loop()
        run_func = loop.create_task(DbFunctions.create_new_ct(data))
        loop.run_until_complete(run_func)
        result = run_func.result()

        if result == 'already exists':
            message_text = 'Данный кабинет уже подключен'
            await bot.send_message(message.from_user.id, message_text, reply_markup=main_keyboard)
            await state.finish()

        else:
            message_text = 'Данные успешно сохранены!\n'\
                           'Теперь вы можете получать статистику'
            await bot.send_message(message.from_user.id, message_text, reply_markup=main_keyboard)
            await state.finish()


# запрашиваем список аккаунтов CT для удаления
@dp.callback_query_handler(lambda c: c.data == 'remove_creds')
async def show_creds_to_remove(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)

    # добавляем задачу ассинхронно
    loop = asyncio.get_running_loop()
    run_func = loop.create_task(DbFunctions.list_of_accounts(callback_query.from_user.id))
    loop.run_until_complete(run_func)
    calltouch_accounts = run_func.result()

    if len(calltouch_accounts) == 0:
        message_text = 'У вас нет аккаунтов CallTouch\n' \
                       'Нажмите /start что бы вернуться в меню'
        await bot.send_message(callback_query.from_user.id, message_text)
        await state.reset_state()
    else:
        message_text = 'Введите ID кабинета который необходимо удалить\n' \
                       'или нажмите /start что бы вернуться назад\n' \
                       'ID ваших аккаунтов:\n'

        for account in calltouch_accounts:
            message_text += account[0] + '\n'

        await bot.send_message(callback_query.from_user.id, message_text)
        await Actions.remove_ct_creds.set()


# удаляем список
@dp.message_handler(state=Actions.remove_ct_creds)
async def remove_ct_creds(message: types.Message, state: FSMContext):

    # добавляем задачу ассинхронно
    loop = asyncio.get_running_loop()
    run_func = loop.create_task(DbFunctions.list_of_accounts(message.from_user.id))
    loop.run_until_complete(run_func)
    calltouch_accounts = list(itertools.chain.from_iterable(run_func.result()))  # делаем плоский список

    if message.text not in calltouch_accounts:
        message_text = 'Такого аккаунта нет в списке.\n'\
                       'Введите аккаунт из списка выше или нажмите /start что бы вернуться назад'
        await bot.send_message(message.from_user.id, message_text)
    else:
        # добавляем задачу ассинхронно
        loop = asyncio.get_running_loop()
        run_func = loop.create_task(DbFunctions.remove_account(message.from_user.id, message.text))
        loop.run_until_complete(run_func)

        message_text = f'Аккаунт {message.text} удален!\n' \
                       f'Нажмите /start что бы вернуться в меню'
        await bot.send_message(message.from_user.id, message_text)
        await state.finish()


# выводим список креденшалов
@dp.callback_query_handler(lambda c: c.data == 'show_creds')
async def show_my_creds(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    # добавляем задачу ассинхронно
    loop = asyncio.get_running_loop()
    run_func = loop.create_task(DbFunctions.list_of_accounts(callback_query.from_user.id))
    loop.run_until_complete(run_func)
    calltouch_accounts = list(itertools.chain.from_iterable(run_func.result()))

    if len(calltouch_accounts) == 0:
        message_text = 'У вас нет аккаунтов CallTouch\n' \
                       'Нажмите /start что бы вернуться в меню'
        await bot.send_message(callback_query.from_user.id, message_text)
    else:
        message_text = 'ID ваших кабинетов:\n'

        for account in calltouch_accounts:
            message_text += account + '\n'

        message_text += 'Нажмите /start что бы вернуться назад'
        await bot.send_message(callback_query.from_user.id, message_text)


# выводим список кабинетов при запросе статистики
@dp.callback_query_handler(lambda c: c.data == 'get_call_stat')
async def show_my_creds(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)

    # добавляем задачу ассинхронно
    loop = asyncio.get_running_loop()
    run_func = loop.create_task(DbFunctions.list_of_accounts(callback_query.from_user.id))
    loop.run_until_complete(run_func)
    calltouch_accounts = list(itertools.chain.from_iterable(run_func.result()))

    if len(calltouch_accounts) == 0:
        message_text = 'У вас нет аккаунтов CallTouch\n' \
                       'Нажмите /start что бы вернуться в меню'
        await bot.send_message(callback_query.from_user.id, message_text)

    elif len(calltouch_accounts) == 1:
        async with state.proxy() as data:
            data['cabinet_id'] = calltouch_accounts[0]
        message_text = 'Выберете пункт меню:'
        await bot.send_message(callback_query.from_user.id, message_text, reply_markup=calltouch_keyboard)
        await Actions.get_statistic.set()
    else:
        message_text = 'Введите ID кабинета по которому хотели бы получать статистику:\n'

        for account in calltouch_accounts:
            message_text += account + '\n'

        message_text += 'Или нажмите /start что бы вернуться назад'
        await bot.send_message(callback_query.from_user.id, message_text)
        await Actions.choose_cabinet_id.set()


# выбор кабинета если их больше одного
@dp.message_handler(state=Actions.choose_cabinet_id)
async def choose_cabinet_id(message: types.Message, state: FSMContext):
    cabinet_id = message.text

    # добавляем задачу ассинхронно
    loop = asyncio.get_running_loop()
    run_func = loop.create_task(DbFunctions.validate_cabinet_id(message.from_user.id, cabinet_id))
    loop.run_until_complete(run_func)
    account_list = list(itertools.chain.from_iterable(run_func.result()))

    if cabinet_id not in account_list:
        message_text = 'Аккаунтов CallTouch с таким ID не найдено.\n' \
                       'Нажмите /start что бы вернуться назад'
        await bot.send_message(message.from_user.id, message_text)
    else:
        async with state.proxy() as data:
            data['cabinet_id'] = cabinet_id

        message_text = 'Выберете пункт меню:'
        await bot.send_message(message.from_user.id, message_text, reply_markup=calltouch_keyboard)
        await Actions.get_statistic.set()


# Статистика за сегодня по выбранному ЛК
@dp.callback_query_handler(lambda c: c.data == 'get_today_stat', state=Actions.get_statistic)
async def get_today_calls(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)

    async with state.proxy() as data:
        data['days_ago'] = 0

    # добавляем задачу ассинхронно
    loop = asyncio.get_running_loop()
    run_func = loop.create_task(
        CallTouchFunctions.get_n_days_ago_data(callback_query.from_user.id, data['cabinet_id'], data['days_ago']))
    loop.run_until_complete(run_func)  # ошибка но почему - хер знает
    result = run_func.result()

    if result == 'error':
        message_text = f'Возникла ошибка.\nПопробуйте удалить кабинет {data["cabinet_id"]} и попробуйте снова'
        await bot.send_message(callback_query.from_user.id, message_text, reply_markup=calltouch_keyboard)
    else:
        message_text = f'Статистика за {result["date"]}:\n' \
                       f'Всего звонков: {result["total_calls"]}\n' \
                       f'Уникальных звонков: {result["unique_calls"]}\n' \
                       f'Целевых звонков: {result["target_calls"]}\n' \
                       f'Уникально-целевых звонков: {result["unique_target_calls"]}'

        await bot.send_message(callback_query.from_user.id, message_text, reply_markup=calltouch_keyboard)


# Статистика за вчера по выбранному ЛК
@dp.callback_query_handler(lambda c: c.data == 'get_yesterday_stat', state=Actions.get_statistic)
async def get_today_calls(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)

    async with state.proxy() as data:
        data['days_ago'] = 1

    # добавляем задачу ассинхронно
    loop = asyncio.get_running_loop()
    run_func = loop.create_task(
        CallTouchFunctions.get_n_days_ago_data(callback_query.from_user.id, data['cabinet_id'], data['days_ago']))
    loop.run_until_complete(run_func)  # ошибка но почему - хер знает
    result = run_func.result()

    if result == 'error':
        message_text = f'Возникла ошибка.\nПопробуйте удалить кабинет {data["cabinet_id"]} и попробуйте снова'
        await bot.send_message(callback_query.from_user.id, message_text, reply_markup=calltouch_keyboard)
    else:
        message_text = f'Статистика за {result["date"]}:\n' \
                       f'Всего звонков: {result["total_calls"]}\n' \
                       f'Уникальных звонков: {result["unique_calls"]}\n' \
                       f'Целевых звонков: {result["target_calls"]}\n' \
                       f'Уникально-целевых звонков: {result["unique_target_calls"]}'

        await bot.send_message(callback_query.from_user.id, message_text, reply_markup=calltouch_keyboard)


# функция возврата в главное меню
@dp.callback_query_handler(lambda c: c.data == 'get_back', state='*')
async def get_back_to_upper_menu(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    message_text = 'Выберете нужный пункт меню:'
    await bot.send_message(callback_query.from_user.id, message_text, reply_markup=main_keyboard)
    await state.reset_state()


# выгрузка БД для "своих"
@dp.message_handler(commands=['list'], state='*')
async def start_message(message: types.Message, state: FSMContext):
    message_text = 'Формирую CSV-файл'
    await bot.send_message(message.from_user.id, message_text)

    # добавляем задачу ассинхронно
    loop = asyncio.get_running_loop()
    run_func = loop.create_task(DbFunctions.download_db(message.from_user.id))
    loop.run_until_complete(run_func)
    result = run_func.result()

    if result != 'ok':
        pass
    else:
        file_name = open('db_file.csv', 'rb')
        await bot.send_document(message.from_user.id, file_name)


executor.start_polling(dp, skip_updates=True)
# збс, все четенько переведено в ассинхрон
# при добавлении ЛК надо првоерять нет ли такого уже в БД

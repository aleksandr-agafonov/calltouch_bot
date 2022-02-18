from aiogram.dispatcher.filters.state import StatesGroup, State


class Actions(StatesGroup):
    # состояния для создания ct
    create_ct_get_id = State()
    create_ct_get_server = State()
    create_ct_get_token = State()

    # состояния для удаления
    remove_ct_creds = State()

    # состояние запроса статистика
    get_statistic = State()
    choose_cabinet_id = State()

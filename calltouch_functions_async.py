import aiohttp
import aiosqlite
from datetime import datetime, timedelta


db = 'ct_database.db'
table_name = 'ct_creds'


class CallTouchFunctions:
    # функция принимает на вход значения и взвращает их или ноль
    async def get_values_or_zero(argument):
        try:
            return argument
        except:
            return 0

    # валидация креденшелов calltouch
    async def validate_creds(site_id, server, token):
        get_date = datetime.now()
        get_date = get_date.strftime('%d/%m/%Y')
        url = f'{server}calls-service/RestAPI/{site_id}/calls-diary/calls'

        params = {
            'clientApiId': token,
            'dateFrom': get_date,
            'dateTo': get_date
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200 and len(await response.json()) >= 0:
                        return 'ok'
                    else:
                        return 'no data'
            except Exception as e:
                print('Ошибка в CallTouchFunctions => validate_creds => request\n', e)
                return 'error'

    # сбор статистики за n дней назад
    async def get_n_days_ago_data(user_id, cabinet_id, days_back):
        result_dict = dict()
        async with aiosqlite.connect(db) as connection:
            cursor = await connection.cursor()
            query = f'''SELECT token, server FROM {table_name} WHERE user_id = (?) and cabinet_id = (?)'''
            values = (user_id, cabinet_id)
            await cursor.execute(query, values)
            result = await cursor.fetchone()

            token = result[0]
            server = result[1]
            get_date = datetime.now() - timedelta(days=days_back)
            get_date = get_date.strftime('%d/%m/%Y')
            url = f'{server}calls-service/RestAPI/{cabinet_id}/calls-diary/calls'

            params = {
                'clientApiId': token,
                'dateFrom': get_date,
                'dateTo': get_date
            }

            # ототправляем запрос в CallTouch и возвращем словарь с результатами
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        print('Ошибка в CallTouchFunctions => get_n_days_ago_data => request')
                        print(await response.json())
                        return 'error'
                    else:
                        result = await response.json()
                        result_dict['date'] = get_date
                        result_dict['unique_calls'] = sum(result.get('uniqueCall') for result in result)
                        result_dict['target_calls'] = sum(result.get('targetCall') for result in result)
                        result_dict['unique_target_calls'] = sum(result.get('uniqTargetCall') for result in result)
                        result_dict['total_calls'] = len(result)

                    return result_dict

# тест
# import asyncio
# loop = asyncio.get_event_loop()
# a = loop.run_until_complete(CallTouchFunctions.get_n_days_ago_data(1673451611, 45840, 0))
# print(a)

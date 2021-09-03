import requests
from datetime import datetime, timedelta
import sqlite3
import pandas as pd


db = 'ct_database.db'
table_name = 'ct_creds'


# функция принимает на вход значения ии взвращает их или none
def get_values_or_zero(argument):
    try:
        return argument
    except:
        return 0


# валидация креденшелов calltouch
def validate_creds(site_id, server, token):
    get_date = datetime.now()
    get_date = get_date.strftime('%d/%m/%Y')

    params = {
        'clientApiId': token,
        'dateFrom': get_date,
        'dateTo': get_date
    }

    url = f'{server}calls-service/RestAPI/{site_id}/calls-diary/calls'
    try:
        req = requests.get(url, params=params)
        if req.status_code == 200 and len(req.json()) >= 0:
            return 'Данные проверены!'
        else:
            return 'error'
    except:
        return 'error'


# сбор статистики за days_back дней назад
def get_today_data(user_id, cabinet_id, days_back):

    result_dict = dict()

    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    query = f'''
    SELECT 
        token, server
    FROM {table_name} 
    WHERE user_id = (?)
        and cabinet_id = (?)
    '''

    values = (user_id, cabinet_id)

    cursor.execute(query, values).fetchone()

    token = cursor.execute(query, values).fetchone()[0]
    server = cursor.execute(query, values).fetchone()[1]
    get_date = datetime.now() - timedelta(days=days_back)
    get_date = get_date.strftime('%d/%m/%Y')

    params = {
        'clientApiId': token,
        'dateFrom': get_date,
        'dateTo': get_date
    }

    url = f'{server}calls-service/RestAPI/{cabinet_id}/calls-diary/calls'

    req = requests.get(url, params=params)

    df = pd.DataFrame(req.json())

    if df.empty:
        result_dict['date'] = get_date
        result_dict['total_calls'] = 0
        result_dict['unique_calls'] = 0
        result_dict['target_calls'] = 0
        result_dict['unique_target_calls'] = 0

    else:
        total_calls = get_values_or_zero(df['callId'].nunique())  # всего звонков
        unique_calls = get_values_or_zero(df[df['uniqueCall'] == True]['callId'].nunique())  # уникальные звонки
        target_calls = get_values_or_zero(df[df['targetCall'] == True]['callId'].nunique())  # целевые звонки
        unique_target_calls = get_values_or_zero(
            df[(df['uniqueCall'] == True) & (df['targetCall'] == True)]['callId'].nunique())  # уникально-целевые звонки

        result_dict['date'] = get_date
        result_dict['total_calls'] = total_calls
        result_dict['unique_calls'] = unique_calls
        result_dict['target_calls'] = target_calls
        result_dict['unique_target_calls'] = unique_target_calls

    return result_dict


# a = get_today_data(1673451611, '45840', 1)
# print(a)
# id = 45105
# server = 'https://api.calltouch.ru/'
# token = 'iOT/yJ8iucx0PvB8S0sJvRdjusF75/jewx21muGauttSs'
# print(validate_creds(45840, 'https://api.calltouch.ru/', '2lF3SN/aMOVRBaEyiEmCeQDvJTARWSOunh05Ar/KX1rr2'))

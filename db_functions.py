import sqlite3


db = 'ct_database.db'
table_name = 'ct_creds'


# создает аккаунт CT
def create_new_ct(ct_dict):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    query = f'''
    INSERT INTO {table_name} VALUES (?, ?, ?, ?, ?, ?, ?)
    '''
    values = (
        ct_dict['create_date'],
        ct_dict['token'],
        ct_dict['cabinet_id'],
        ct_dict['server'],
        ct_dict['user_id'],
        ct_dict['user_name'],
        ct_dict['user_surname']
    )

    cursor.execute(query, values)
    conn.commit()
    conn.close()


# выдает список аккаунтов пользователя
def list_of_accounts(user_id):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    query = f'''
    SELECT cabinet_id 
    FROM {table_name} 
    WHERE user_id = {user_id}
    '''

    result = cursor.execute(query).fetchall()
    conn.close()
    return result


# удаляет аккаунт CT
def remove_account(user_id, cabinet_id):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    query = f'''
    DELETE FROM {table_name} 
    WHERE user_id = ?
        and cabinet_id = ?
    '''

    values = (user_id, cabinet_id)

    cursor.execute(query, values)
    conn.commit()
    conn.close()
    return 'success'


# проверяет есть ли введенный кибент в БД и принаджелит ли этому пользователю
def validate_cabinet_id(user_id, cabinet_id):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    query = f'''
    SELECT cabinet_id 
    FROM {table_name}
    WHERE user_id = ?
        and cabinet_id = ?
    '''
    values = (user_id, cabinet_id)

    result = cursor.execute(query, values).fetchall()
    conn.close()
    return result


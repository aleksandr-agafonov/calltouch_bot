import aiosqlite
import csv


# креденшалы для БД
db = 'ct_database.db'
table_name = 'ct_creds'
table_rows = ('create_date', 'token', 'cabinet_id', 'server', 'user_id', 'user_name', 'user_surname')
allowed_user_list = [1673451611]


class DbFunctions:

    # Добавить аккаунт CallTouch в БД
    async def create_new_ct(ct_dict):
        async with aiosqlite.connect(db) as connection:
            cursor = await connection.cursor()

            # проверяем есть ли данные кабинет у данного пользователя уже в БД
            check_query = f'''SELECT * FROM {table_name} WHERE user_id = ? and cabinet_id = ? '''
            check_values = (ct_dict['user_id'], ct_dict['cabinet_id'])
            await cursor.execute(check_query, check_values)
            result = await cursor.fetchone()

            if result is not None:
                return 'already exists'
            else:
                query = f'''INSERT INTO {table_name} VALUES (?, ?, ?, ?, ?, ?, ?)'''
                values = (
                    ct_dict['create_date'],
                    ct_dict['token'],
                    ct_dict['cabinet_id'],
                    ct_dict['server'],
                    ct_dict['user_id'],
                    ct_dict['user_name'],
                    ct_dict['user_surname']
                )
                await cursor.execute(query, values)
                await connection.commit()
            return 'ok'

    # выдает список аккаунтов пользователя
    async def list_of_accounts(user_id):
        async with aiosqlite.connect(db) as connection:
            cursor = await connection.cursor()
            query = f'''SELECT cabinet_id FROM {table_name} WHERE user_id = {user_id}'''
            await cursor.execute(query)
            result = await cursor.fetchall()
        return result

    # удаляет аккаунт CT
    async def remove_account(user_id, cabinet_id):
        async with aiosqlite.connect(db) as connection:
            cursor = await connection.cursor()
            query = f'''DELETE FROM {table_name} WHERE user_id = ? and cabinet_id = ?'''
            values = (user_id, cabinet_id)
            await cursor.execute(query, values)
            await connection.commit()
        return 'ok'

    # проверяет есть ли введенный кибент в БД и принаджелит ли этому пользователю
    async def validate_cabinet_id(user_id, cabinet_id):
        async with aiosqlite.connect(db) as connection:
            cursor = await connection.cursor()
            query = f'''SELECT cabinet_id FROM {table_name} WHERE user_id = ? and cabinet_id = ?'''
            values = (user_id, cabinet_id)
            await cursor.execute(query, values)
            result = await cursor.fetchall()
        return result

    # выгрузка БД для "своих"
    async def download_db(user_id):
        if user_id not in allowed_user_list:
            return 'permission denied'
        else:
            async with aiosqlite.connect(db) as connection:
                cursor = await connection.cursor()
                query = f'''SELECT * FROM {table_name}'''
                await cursor.execute(query)
                result = await cursor.fetchall()

                open_file = open('db_file.csv', 'w', newline='\n')
                open_file = csv.writer(open_file)
                open_file.writerow(table_rows)  # записывае шапку таблицы
                open_file.writerows(result)  # пишем результат из БД

            return 'ok'

# тест
# import asyncio
# loop = asyncio.get_event_loop()
# a = loop.run_until_complete(DbFunctions.download_db(1673451611))
# print(a)

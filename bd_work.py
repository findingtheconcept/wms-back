import mysql.connector
from mysql.connector import Error

def insert_user_data(name,category, measure, description, position, minimum_to_warn):
    try:
        # Подключение к базе данных
        connection = mysql.connector.connect(
            host='localhost',
            database='warehouse',
            user='root',
            password='0000'
        ) 
        
        if connection.is_connected():
            cursor = connection.cursor()
            # SQL-запрос на вставку данных
            insert_query = """
            INSERT INTO products (name, category, measure, description, position, minimum_to_warn)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            data = (name, category, measure, description, position, minimum_to_warn)
            cursor.execute(insert_query, data)
            connection.commit()
            print("Данные успешно добавлены.")

    except Error as e:
        print(f"Ошибка при работе с MySQL: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

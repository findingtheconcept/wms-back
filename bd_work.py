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

            cursor.execute("SELECT * FROM categories WHERE name = %s", (category,))
            result = cursor.fetchone()

            
            if not result:
                print("Категории не существует!")
                return
            # SQL-запрос на вставку данных
            insert_query = """
            INSERT INTO products (name, category, measure, description, position, minimum_to_warn)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            data = (name, category, measure, description, position, minimum_to_warn)
            cursor.execute(insert_query, data)
            cursor.execute("UPDATE categories SET num = num + 1 WHERE name = %s", (category,))
            connection.commit()
            print("Данные успешно добавлены.")

    except Error as e:
        print(f"Ошибка при работе с MySQL: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def insert_user_category(name, description): # добавить
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
            INSERT INTO categories (name, description, num)
            VALUES (%s, %s, %s)
            """
            data = (name, description, 0)
            cursor.execute(insert_query, data)
            connection.commit()
            print("Данные успешно добавлены.")

    except Error as e:
        print(f"Ошибка при работе с MySQL: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def delete_user_category(name, description): # 
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
            # SQL-запрос на удаление данных
            cursor.execute("SELECT COUNT(*) FROM products WHERE category = %s", (name,))
            product_count = cursor.fetchone()[0]
            if product_count > 0:
                print("Нельзя удалить категорию — существуют связанные товары.")
                return
            delete_query = "DELETE FROM categories WHERE name = %s"
            cursor.execute(delete_query, (name,))
            data = (name)
            cursor.execute(delete_query, data)
            connection.commit()
            print("Данные успешно удалены.")

    except Error as e:
        print(f"Ошибка при работе с MySQL: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()



def redact_user_category(old_name, name, description):
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
            cursor.execute("SELECT * FROM categories WHERE name = %s", (old_name,))
            result = cursor.fetchone()
            if not result:
                print(f"Категория с именем '{old_name}' не найдена.")
                return
            redact_query = """
            UPDATE categories
            SET name = %s, description=%s 
            WHERE name = %s 
            """
            data = (name, description, old_name)
            cursor.execute(redact_query, data)
            connection.commit()
            print("Данные успешно обновлены.")

    except Error as e:
        print(f"Ошибка при работе с MySQL: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
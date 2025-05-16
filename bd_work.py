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
            cursor.execute("SELECT * FROM categories WHERE name = %s", (name,))
            existing = cursor.fetchone()
            if existing:
                print(f"Категория с именем '{name}' уже существует.")
                return
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

def delete_user_category(name): # 
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


def register_product_arrival(productname, quantity, date, invoice_number, provider, comment=None):
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='warehouse',
            user='root',
            password='0000'
        )

        if connection.is_connected():
            cursor = connection.cursor()

            # Проверка существования продукта
            cursor.execute("SELECT id FROM products WHERE name = %s", (productname,))
            result = cursor.fetchone()
            if not result:
                print("Продукт не найден!")
                return
            product_id = result[0]

            # Вставка в таблицу поступлений
            insert_query = """
            INSERT INTO product_incoming (product_id, quantity, date, invoice_number, provider, comment)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            data = (product_id, quantity, date, invoice_number, provider, comment)
            cursor.execute(insert_query, data)
            connection.commit()
            print("Поступление успешно зарегистрировано.")

    except Error as e:
        print(f"Ошибка при работе с MySQL: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
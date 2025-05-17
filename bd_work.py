import mysql.connector
from mysql.connector import Error

def insert_user_data(name,category, measure, description, position, minimum_to_warn):
    try:    
        message = ''                                                                            
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
                message = "Категории не существует!"
                return message
            insert_query = """
            INSERT INTO products (name, category, measure, description, position, minimum_to_warn, stock)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            data = (name, category, measure, description, position, minimum_to_warn, 0)
            cursor.execute(insert_query, data)
            cursor.execute("UPDATE categories SET num = num + 1 WHERE name = %s", (category,))
            connection.commit()
            message = "Данные успешно добавлены."

    except Error as e:
        message = "Ошибка при работе с MySQL: " + e
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
        return message

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

def register_movement_by_name(product_name, quantity, date, doc_number, partner, operation, comment=None):
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

            # Получение ID и текущего остатка по имени товара
            cursor.execute("SELECT id, stock FROM products WHERE name = %s", (product_name,))
            result = cursor.fetchone()

            if not result:
                return f"Товар с именем '{product_name}' не найден."

            product_id, current_stock = result

            # Проверка на доступность при отгрузке
            if operation == 'out':
                if quantity > current_stock:
                    return f"Недостаточно товара на складе. Текущий остаток: {current_stock}."

            # Вычисление нового остатка
            new_stock = current_stock + quantity if operation == 'in' else current_stock - quantity

            # Обновление остатка
            cursor.execute("UPDATE products SET stock = %s WHERE id = %s", (new_stock, product_id))

            # Запись движения
            cursor.execute("""
                INSERT INTO movements (product_id, quantity, movement_date, doc_number, partner, operation, comment)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                product_id,
                quantity,
                date,
                doc_number,
                partner,
                operation,
                comment
            ))

            connection.commit()
            return f"Операция '{'Поступление' if operation == 'in' else 'Отгрузка'}' выполнена. Текущий остаток: {new_stock}"

    except Error as e:
        if connection and connection.is_connected():
            connection.rollback()
        return f"Ошибка при выполнении операции: {e}"

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

''' ТЕСТ БЛОК, СНЕСИТЕ ЕСЛИ НУЖНО
insert_user_category(
    name="Электроника",
    description="Товары электронного назначения"
)

insert_user_data(
    name="Блок питания 12V",
    category="Электроника",
    measure="шт",
    description="Импульсный блок питания 12V 2A",
    position="Склад A, ряд 3",
    minimum_to_warn=10
)


register_movement_by_name("Блок питания 12V",100,"2025-05-15",
    doc_number="НАКЛ-007",
    partner="ООО ЭлектроПлюс",
    operation="in",
    comment="Допоставка по контракту"
)

register_movement_by_name(
    product_name="Блок питания 12V",
    quantity=30,
    date="2025-05-17",
    doc_number="НАКЛ-005",
    partner="ООО КАК",
    operation="out",
    comment="Отправка на склад"
)

'''
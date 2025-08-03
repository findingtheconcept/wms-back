import mysql.connector
from mysql.connector import Error

def drop_all_tables(database_name):
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='adminka228',
            database=database_name
        )
        if connection.is_connected():
                print("Успешное подключение к базе данных")
        cursor = connection.cursor()
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        for (table_name,) in tables:
            drop_sql = f"DROP TABLE IF EXISTS `{table_name}`"
            cursor.execute(drop_sql)
            print(f"Таблица {table_name} удалена.")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        connection.commit()
    except mysql.connector.Error as e:
        print(f"Ошибка: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def create_tables():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='warehouse',
            user='root',
            password='#######'
        )
        if connection.is_connected():
            cursor = connection.cursor()

            # Создание таблицы categories
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                num INT DEFAULT 0 COMMENT 'Количество товаров в категории, если нужно'
            )
            """)

            # Создание таблицы products
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                category_id INT NOT NULL COMMENT 'Внешний ключ к categories.id',
                unit VARCHAR(50) COMMENT 'Единица измерения',
                description TEXT,
                location VARCHAR(100) COMMENT 'Место хранения',
                min_stock INT DEFAULT 0 COMMENT 'Минимальный остаток',
                current_stock INT DEFAULT 0 COMMENT 'Текущий остаток',
                FOREIGN KEY (category_id) REFERENCES categories(id)
                    ON UPDATE CASCADE
                    ON DELETE RESTRICT 
            )
            """)
            # ON DELETE RESTRICT - не даст удалить категорию, если есть товары
            # Можно заменить на ON DELETE SET NULL (если category_id может быть NULL) 

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS operations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                date DATETIME NOT NULL,
                type ENUM('Поступление', 'Отгрузка') NOT NULL,
                product_id INT NOT NULL,
                quantity INT NOT NULL,
                invoice_number VARCHAR(100),
                party VARCHAR(255) COMMENT 'Поставщик или получатель',
                comment TEXT,
                FOREIGN KEY (product_id) REFERENCES products(id)
                    ON UPDATE CASCADE
                    ON DELETE RESTRICT 
            )
            """)
            # ON DELETE RESTRICT для product_id - не даст удалить товар, если есть операции.

            connection.commit()
            print("Все таблицы успешно созданы/проверены.")

    except Error as e:
        print(f"Ошибка при работе с MySQL: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    drop_all_tables('warehouse') 
    create_tables()            
    print("Таблицы пересозданы по обновленной схеме.")
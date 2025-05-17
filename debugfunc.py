import mysql.connector

def drop_all_tables(database_name): #удаляет все таблицы из бд
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='0000',
            database=database_name
        )
        cursor = connection.cursor()

        # Отключаем проверку внешних ключей
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

        # Получаем список всех таблиц
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        for (table_name,) in tables:
            drop_sql = f"DROP TABLE IF EXISTS `{table_name}`"
            cursor.execute(drop_sql)
            print(f"Таблица {table_name} удалена.")

        # Включаем проверку внешних ключей обратно
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

        connection.commit()
    except mysql.connector.Error as e:
        print(f"Ошибка: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

#АККУРАТНО, ОПАСНАЯ ФУНКЦИЯ
#drop_all_tables('warehouse')


def create_tables():
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

            # Создание таблицы categories
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                num INT DEFAULT 0
            )
            """)

            # Создание таблицы products
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                category VARCHAR(100) NOT NULL,
                measure VARCHAR(50),
                description TEXT,
                position VARCHAR(100),
                minimum_to_warn INT DEFAULT 0,
                stock INT DEFAULT 0,
                FOREIGN KEY (category) REFERENCES categories(name)
                    ON UPDATE CASCADE
                    ON DELETE RESTRICT
            )
            """)

            # Создание таблицы movements
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS movements (
                id INT AUTO_INCREMENT PRIMARY KEY,
                product_id INT NOT NULL,
                quantity INT NOT NULL,
                operation ENUM('in', 'out') NOT NULL,
                doc_number VARCHAR(50),
                partner VARCHAR(100),
                comment TEXT,
                movement_date DATETIME NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(id)
                    ON UPDATE CASCADE
                    ON DELETE RESTRICT
            )
            """)

            connection.commit()
            print("Все таблицы успешно созданы.")

    except Error as e:
        print(f"Ошибка при работе с MySQL: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


#create_tables()
import mysql.connector
from mysql.connector import Error
import datetime

# --- Database Connection Utility ---
def get_db_connection():
    """Устанавливает соединение с базой данных MySQL."""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='warehouse',
            user='root',
            password='#######' # Убедись, что пароль верный
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# --- Категории ---
def db_add_category(name, description=""):
    """Добавляет новую категорию в базу данных."""
    conn = get_db_connection()
    if conn is None:
        return None, "Database connection failed"
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM categories WHERE name = %s", (name,))
        if cursor.fetchone():
            return None, "Категория с таким названием уже существует"

        insert_query = "INSERT INTO categories (name, description, num) VALUES (%s, %s, %s)"
        cursor.execute(insert_query, (name.strip(), description.strip(), 0))
        conn.commit()
        new_category_id = cursor.lastrowid
        cursor.execute("SELECT id, name, description, num FROM categories WHERE id = %s", (new_category_id,))
        new_category = cursor.fetchone()
        return new_category, "Категория успешно добавлена"
    except Error as e:
        conn.rollback()
        print(f"Error adding category: {e}")
        return None, f"Ошибка при добавлении категории: {e}"
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def db_add_category(name, description=""):
    """Добавляет новую категорию в базу данных."""
    conn = get_db_connection()
    if conn is None:
        return None, "Database connection failed"
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM categories WHERE name = %s", (name,))
        if cursor.fetchone():
            return None, "Категория с таким названием уже существует"

        insert_query = "INSERT INTO categories (name, description, num) VALUES (%s, %s, %s)"
        cursor.execute(insert_query, (name.strip(), description, 0))
        conn.commit()
        new_category_id = cursor.lastrowid
        cursor.execute("SELECT id, name, description, num FROM categories WHERE id = %s", (new_category_id,))
        new_category = cursor.fetchone()
        return new_category, "Категория успешно добавлена"
    except Error as e:
        conn.rollback()
        print(f"Error adding category: {e}")
        return None, f"Ошибка при добавлении категории: {e}"
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def db_get_all_categories():
    """Получает все категории из базы данных."""
    conn = get_db_connection()
    if conn is None:
        return [], "Database connection failed"
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, name, description, num FROM categories ORDER BY name")
        categories = cursor.fetchall()
        return categories, "Категории успешно загружены"
    except Error as e:
        print(f"Error fetching categories: {e}")
        return [], f"Ошибка при загрузке категорий: {e}"
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def db_update_category(category_id, name, description):
    """Обновляет существующую категорию."""
    conn = get_db_connection()
    if conn is None:
        return None, "Database connection failed"
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM categories WHERE name = %s AND id != %s", (name.strip(), category_id))
        if cursor.fetchone():
            return None, "Категория с таким названием уже существует"

        update_query = "UPDATE categories SET name = %s, description = %s WHERE id = %s"
        cursor.execute(update_query, (name.strip(), description, category_id))
        conn.commit()
        if cursor.rowcount == 0:
            return None, "Категория не найдена или данные не изменились"
        
        cursor.execute("SELECT id, name, description, num FROM categories WHERE id = %s", (category_id,))
        updated_category = cursor.fetchone()
        return updated_category, "Категория успешно обновлена"
    except Error as e:
        conn.rollback()
        print(f"Error updating category: {e}")
        return None, f"Ошибка при обновлении категории: {e}"
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def db_delete_category(category_id):
    """Удаляет категорию, если она не используется товарами."""
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed"
    cursor = conn.cursor()
    try:
        # Проверка на связанные товары
        cursor.execute("SELECT COUNT(*) FROM products WHERE category_id = %s", (category_id,))
        product_count = cursor.fetchone()[0]
        if product_count > 0:
            return False, "Нельзя удалить категорию, так как она используется товарами"

        delete_query = "DELETE FROM categories WHERE id = %s"
        cursor.execute(delete_query, (category_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return False, "Категория не найдена"
        return True, "Категория успешно удалена"
    except Error as e:
        conn.rollback()
        print(f"Error deleting category: {e}")
        return False, f"Ошибка при удалении категории: {e}"
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# --- Товары ---
def db_get_all_products():
    """Получает все товары с информацией о категории."""
    conn = get_db_connection()
    if conn is None:
        return [], "Database connection failed"
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT 
                p.id, p.name, p.category_id, c.name as category_name, 
                p.unit, p.location, p.min_stock, p.current_stock, p.description
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            ORDER BY p.name
        """
        cursor.execute(query)
        products = cursor.fetchall()
        return products, "Товары успешно загружены"
    except Error as e:
        print(f"Error fetching products: {e}")
        return [], f"Ошибка при загрузке товаров: {e}"
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def db_get_product_by_id(product_id):
    """Получает товар по ID."""
    conn = get_db_connection()
    if conn is None:
        return None, "Database connection failed"
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT 
                p.id, p.name, p.category_id, c.name as category_name,
                p.unit, p.location, p.min_stock, p.current_stock, p.description
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id = %s
        """
        cursor.execute(query, (product_id,))
        product = cursor.fetchone()
        if product:
            return product, "Товар найден"
        else:
            return None, "Товар не найден"
    except Error as e:
        print(f"Error fetching product: {e}")
        return None, f"Ошибка при загрузке товара: {e}"
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def db_add_product(name, category_id, unit, description, location, min_stock, current_stock=0):
    """Добавляет новый товар в базу данных."""
    conn = get_db_connection()
    if conn is None:
        return None, "Database connection failed"
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM categories WHERE id = %s", (category_id,))
        if not cursor.fetchone():
            return None, "Указанная категория не найдена"
        
        cursor.execute("SELECT id FROM products WHERE name = %s", (name.strip(),))
        if cursor.fetchone():
            return None, "Товар с таким названием уже существует"

        insert_query = """
            INSERT INTO products (name, category_id, unit, description, location, min_stock, current_stock)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        data = (name.strip(), category_id, unit.strip(), description.strip(), location.strip(), min_stock, current_stock)
        cursor.execute(insert_query, data)
        
        conn.commit()
        
        new_product_id = cursor.lastrowid
        product, msg = db_get_product_by_id(new_product_id)
        return product, "Товар успешно добавлен"

    except Error as e:
        conn.rollback()
        print(f"Error adding product: {e}")
        return None, f"Ошибка при добавлении товара: {e}"
    except ValueError:
        return None, "Неверный формат числового поля для товара"
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def db_update_product(product_id, name, category_id, unit, description, location, min_stock):
    """Обновляет существующий товар."""
    conn = get_db_connection()
    if conn is None:
        return None, "Database connection failed"
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM categories WHERE id = %s", (category_id,))
        if not cursor.fetchone():
            return None, "Указанная категория не найдена"

        # Проверка на дубликат имени (если имя меняется)
        cursor.execute("SELECT id FROM products WHERE name = %s AND id != %s", (name.strip(), product_id))
        if cursor.fetchone():
            return None, "Товар с таким названием уже существует"

        update_query = """
            UPDATE products 
            SET name = %s, category_id = %s, unit = %s, description = %s, 
                location = %s, min_stock = %s
            WHERE id = %s
        """
        data = (name.strip(), category_id, unit.strip(), description.strip(), 
                location.strip(), min_stock, product_id)
        cursor.execute(update_query, data)
        conn.commit()

        if cursor.rowcount == 0:
            return None, "Товар не найден или данные не изменились"

        updated_product, msg = db_get_product_by_id(product_id)
        return updated_product, "Товар успешно обновлен"
    except Error as e:
        conn.rollback()
        print(f"Error updating product: {e}")
        return None, f"Ошибка при обновлении товара: {e}"
    except ValueError:
        return None, "Неверный формат числового поля для товара"
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def db_delete_product(product_id):
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed"
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COUNT(*) as count FROM operations WHERE product_id = %s", (product_id,))
        result = cursor.fetchone()
        if result and result['count'] > 0:
            return False, f"Нельзя удалить товар (ID: {product_id}), так как с ним связано {result['count']} операций в журнале. Сначала удалите эти операции или рассмотрите возможность архивации товара."

        cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return False, "Товар не найден"
        return True, "Товар успешно удален"
    except Error as e:
        conn.rollback()
        error_code = e.errno if hasattr(e, 'errno') else 'N/A'
        print(f"Error deleting product: {e} (Code: {error_code})")
        if error_code == 1451:
             return False, f"Ошибка при удалении товара: на товар ссылаются другие записи (например, операции). Код: {error_code}"
        return False, f"Ошибка при удалении товара: {e}"
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# --- Операции (Поступления/Отгрузки) ---
def db_get_all_operations():
    """Получает все операции с именами товаров, отсортированные по дате."""
    conn = get_db_connection()
    if conn is None:
        return [], "Database connection failed"
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT
                o.id, o.date, o.type, o.product_id, p.name as product_name,
                o.quantity, o.invoice_number, o.party, o.comment
            FROM operations o
            LEFT JOIN products p ON o.product_id = p.id
            ORDER BY o.date DESC
        """
        cursor.execute(query)
        operations = cursor.fetchall()
        return operations, "Операции успешно загружены"
    except Error as e:
        print(f"Error fetching operations: {e}")
        return [], f"Ошибка при загрузке операций: {e}"
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def db_register_operation(op_type, product_id, quantity, op_date_str, invoice_number, party, comment):
    """Регистрирует операцию (поступление/отгрузка) и обновляет остатки товара."""
    conn = get_db_connection()
    if conn is None:
        return None, "Database connection failed"
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, name, current_stock FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()
        if not product:
            return None, "Товар не найден"

        current_stock = product["current_stock"]
        if op_type == "Отгрузка" and current_stock < quantity:
            return None, f"Недостаточно товара '{product['name']}' на складе. В наличии: {current_stock}"

        op_date = datetime.datetime.now()
        if op_date_str:
            try:
                op_date = datetime.datetime.strptime(op_date_str, "%Y-%m-%dT%H:%M") # Формат из datetime-local
            except ValueError:
                 try:
                    op_date = datetime.datetime.strptime(op_date_str, "%Y-%m-%d %H:%M:%S")
                 except ValueError:
                    return None, "Неверный формат даты операции"
        
        op_date_formatted = op_date.strftime("%Y-%m-%d %H:%M:%S")


        # Вставка операции
        insert_operation_query = """
            INSERT INTO operations (date, type, product_id, quantity, invoice_number, party, comment)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        operation_data = (
            op_date_formatted, op_type, product_id, quantity,
            invoice_number.strip(), party.strip(), comment.strip()
        )
        cursor.execute(insert_operation_query, operation_data)
        new_operation_id = cursor.lastrowid

        # Обновление остатка товара
        new_stock = current_stock + quantity if op_type == "Поступление" else current_stock - quantity
        update_stock_query = "UPDATE products SET current_stock = %s WHERE id = %s"
        cursor.execute(update_stock_query, (new_stock, product_id))
        conn.commit()

        # Получение созданной операции с именем товара
        cursor.execute("""
            SELECT
                o.id, o.date, o.type, o.product_id, p.name as product_name,
                o.quantity, o.invoice_number, o.party, o.comment
            FROM operations o
            LEFT JOIN products p ON o.product_id = p.id
            WHERE o.id = %s
        """, (new_operation_id,))
        new_operation_details = cursor.fetchone()
        return new_operation_details, "Операция успешно зарегистрирована"

    except Error as e:
        conn.rollback()
        print(f"Error registering operation: {e}")
        return None, f"Ошибка при регистрации операции: {e}"
    except ValueError:
         return None, "Количество товара должно быть числом"
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# --- Отчеты ---

def db_report_current_stock_all():
    conn = get_db_connection()
    if conn is None: return [], [], "Database connection failed"
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                p.name as Наименование, c.name as Категория, p.unit as `Ед. изм.`,
                p.location as `Место хранения`, p.min_stock as `Мин. остаток`,
                p.current_stock as `Текущий остаток`
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            ORDER BY p.name
        """)
        data = cursor.fetchall()
        columns = list(data[0].keys()) if data else [
            "Наименование", "Категория", "Ед. изм.", "Место хранения", "Мин. остаток", "Текущий остаток"
        ]
        return data, columns, "Отчет 'Текущие остатки всех товаров' сформирован"
    except Error as e:
        print(f"Error in report_current_stock_all: {e}")
        return [], [], f"Ошибка отчета: {e}"
    finally:
        if conn.is_connected(): cursor.close(); conn.close()


def db_report_low_stock():
    conn = get_db_connection()
    if conn is None: return [], [], "Database connection failed"
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                p.name as Наименование, c.name as Категория,
                p.min_stock as `Мин. остаток`, p.current_stock as `Текущий остаток`,
                (p.min_stock - p.current_stock) as `Требуется закупка`
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.current_stock < p.min_stock
            ORDER BY p.name
        """)
        data = cursor.fetchall()
        columns = list(data[0].keys()) if data else [
            "Наименование", "Категория", "Мин. остаток", "Текущий остаток", "Требуется закупка"
        ]
        return data, columns, "Отчет 'Товары с остатком ниже минимального' сформирован"
    except Error as e:
        print(f"Error in report_low_stock: {e}")
        return [], [], f"Ошибка отчета: {e}"
    finally:
        if conn.is_connected(): cursor.close(); conn.close()

def db_report_operations_period(start_date_str, end_date_str):
    conn = get_db_connection()
    if conn is None: return [], [], "Database connection failed"
    cursor = conn.cursor(dictionary=True)
    try:
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").strftime("%Y-%m-%d 00:00:00")
        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").strftime("%Y-%m-%d 23:59:59")
        
        cursor.execute("""
            SELECT
                o.date as Дата, o.type as Тип, p.name as Товар,
                o.quantity as Количество, o.invoice_number as `Номер накладной`,
                o.party as `Поставщик/Получатель`, o.comment as Комментарий
            FROM operations o
            LEFT JOIN products p ON o.product_id = p.id
            WHERE o.date BETWEEN %s AND %s
            ORDER BY o.date DESC
        """, (start_date, end_date))
        data = cursor.fetchall()
        columns = list(data[0].keys()) if data else [
            "Дата", "Тип", "Товар", "Количество", "Номер накладной", "Поставщик/Получатель", "Комментарий"
        ]
        return data, columns, f"Отчет 'Операции за период с {start_date_str} по {end_date_str}' сформирован"
    except ValueError:
        return [], [], "Неверный формат даты. Используйте ГГГГ-ММ-ДД."
    except Error as e:
        print(f"Error in report_operations_period: {e}")
        return [], [], f"Ошибка отчета: {e}"
    finally:
        if conn.is_connected(): cursor.close(); conn.close()

def db_report_product_movement_period(product_id, start_date_str, end_date_str):
    conn = get_db_connection()
    if conn is None: return [], [], "", "Database connection failed" # product_name, message
    cursor = conn.cursor(dictionary=True)
    try:
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").strftime("%Y-%m-%d 00:00:00")
        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").strftime("%Y-%m-%d 23:59:59")

        cursor.execute("SELECT name FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()
        if not product:
            return [], [], "", "Товар не найден"
        product_name = product['name']

        cursor.execute("""
            SELECT
                o.date as Дата, o.type as Тип, o.quantity as Количество,
                o.invoice_number as `Номер накладной`, o.party as `Поставщик/Получатель`, o.comment as Комментарий
            FROM operations o
            WHERE o.product_id = %s AND o.date BETWEEN %s AND %s
            ORDER BY o.date DESC
        """, (product_id, start_date, end_date))
        data = cursor.fetchall()
        columns = list(data[0].keys()) if data else [
             "Дата", "Тип", "Количество", "Номер накладной", "Поставщик/Получатель", "Комментарий"
        ]
        return data, columns, product_name, f"Отчет 'Движение товара {product_name}' сформирован"
    except ValueError:
        return [], [], "", "Неверный формат даты. Используйте ГГГГ-ММ-ДД."
    except Error as e:
        print(f"Error in report_product_movement_period: {e}")
        return [], [], "", f"Ошибка отчета: {e}"
    finally:
        if conn.is_connected(): cursor.close(); conn.close()
def db_clear_operations_log():
    """Очищает всю таблицу операций и сбрасывает текущие остатки товаров на 0."""
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed"
    cursor = conn.cursor()
    try:
        # Шаг 1: Удаление всех операций
        cursor.execute("DELETE FROM operations")
        deleted_operations_count = cursor.rowcount

        # Шаг 2: Сброс текущих остатков всех товаров на 0
        # Это важно, так как остатки зависят от операций.
        cursor.execute("UPDATE products SET current_stock = 0")
        updated_products_count = cursor.rowcount

        conn.commit()
        return True, f"Журнал операций успешно очищен ({deleted_operations_count} записей удалено). Остатки {updated_products_count} товаров сброшены на 0."
    except Error as e:
        conn.rollback()
        print(f"Error clearing operations log: {e}")
        return False, f"Ошибка при очистке журнала операций: {e}"
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
